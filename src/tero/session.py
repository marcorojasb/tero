"""Teacher session: Strands Agent + HITL pauses. The model never writes derivados/."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from strands import Agent

from tero.config import Settings
from tero.encargo_sync import source_domain_warning, sync_encargo_from_prompt
from tero.errors import TeroError, humanize_exception
from tero.evidence import collect_warnings
from tero.gate import GateResult, apply_gate, persist_critique
from tero.offline import OfflineModel
from tero.plan import answer_question, apply_plan_edits, edit_assumption
from tero.prompts import system_prompt
from tero.salvage import salvage_draft_from_text
from tero.tools import (
    DRAFT_AGENT_TURNS,
    DRAFT_TOOL_BUDGET,
    PLAN_AGENT_TURNS,
    PLAN_TOOL_BUDGET,
    TurnContext,
    build_tools,
)
from tero.transcript import TranscriptLog
from tero.types import Encargo, GateDecision, ProtocolPhase, Turn
from tero.workspace import Workspace

EmitFn = Callable[[dict[str, Any]], None]


def make_model(settings: Settings, encargo: Encargo):
    if settings.offline:
        return OfflineModel(encargo, model_id="tero-offline")
    from strands.models import BedrockModel

    return BedrockModel(
        model_id=settings.model_id,
        region_name=settings.region,
        temperature=settings.temperature,
    )


def _is_retryable_stream_error(exc: BaseException) -> bool:
    """Nova Lite ConverseStream ToolUse / modelStreamErrorException flakiness."""
    blob = f"{type(exc).__name__} {exc}".lower()
    tokens = (
        "modelstreamerrorexception",
        "modelstreamerror",
        "tooluse",
        "tool use",
        "tool_use",
        "invalid tool",
        "unexpected tool",
        "toolcall",
        "conversationstream",
        "event stream error",
        "internalserverexception",
    )
    return any(token in blob for token in tokens)


class TeacherSession:
    def __init__(
        self,
        workspace: Workspace,
        settings: Settings,
        encargo: Encargo | None = None,
        emit: EmitFn | None = None,
    ) -> None:
        self.workspace = workspace
        self.settings = settings
        self.encargo = encargo or Encargo()
        self._downstream: EmitFn = emit or (lambda _event: None)
        self.transcript = TranscriptLog.open(workspace, settings)
        self.emit: EmitFn = self._emit
        self.turns: list[Turn] = []
        self.phase: ProtocolPhase = "idle"
        self.ctx = TurnContext(workspace=workspace, encargo=self.encargo, emit=self.emit)
        self._agent: Agent | None = None
        self.last_prompt: str = ""
        self._stream_buf: list[str] = []

    def _emit(self, event: dict[str, Any]) -> None:
        self.transcript.append(event)
        self._downstream(event)

    def record(self, event: dict[str, Any]) -> None:
        """Transcript-only (inbound commands / host actions). Not sent to the TUI."""
        self.transcript.append(event)

    def set_encargo(self, encargo: Encargo) -> None:
        self.encargo = encargo
        self.ctx.encargo = encargo

    def _set_phase(self, phase: ProtocolPhase) -> None:
        self.phase = phase
        self.emit({"type": "status", "phase": phase})

    def _agent_for(self, phase: str) -> Agent:
        self.ctx.emit = self.emit
        model = make_model(self.settings, self.encargo)
        return Agent(
            model=model,
            system_prompt=system_prompt(self.encargo, phase=phase),
            tools=build_tools(self.ctx, phase=phase),
            callback_handler=self._callback,
        )

    def _callback(self, **kwargs: Any) -> None:
        if "data" in kwargs and kwargs["data"]:
            chunk = str(kwargs["data"])
            self._stream_buf.append(chunk)
            self.emit({"type": "delta", "text": chunk})
        tool = kwargs.get("current_tool_use") or {}
        if tool.get("name"):
            self.emit(
                {
                    "type": "activity",
                    "tool": tool["name"],
                    "state": "delta",
                    "detail": str(tool.get("name") or ""),
                }
            )

    def start_turn(self, prompt: str) -> Turn:
        cleaned = (prompt or "").strip()
        if not cleaned:
            raise TeroError(
                "Escribe un encargo (o elige un rumbo). Enter vacío no lanza al agente.",
                code="empty_prompt",
            )
        if len(cleaned) > 8000:
            cleaned = cleaned[:8000] + "…"
            self.emit(
                {
                    "type": "warning",
                    "warning": {
                        "code": "long_paste",
                        "message": "Pegado muy largo: se truncó a 8000 caracteres.",
                        "blocking": False,
                    },
                }
            )
        if _looks_garbage(cleaned):
            raise TeroError(
                "Ese texto no parece un encargo usable. Describe el material en una frase.",
                code="garbage_prompt",
            )

        # Sync chips from prompt (fixes encargo vs chips desync)
        synced = sync_encargo_from_prompt(self.encargo, cleaned)
        if synced != self.encargo:
            self.set_encargo(synced)
            self.emit({"type": "encargo", "encargo": self.encargo.as_dict()})

        mismatch = source_domain_warning(self.workspace, cleaned, self.encargo)
        if mismatch:
            self.emit(
                {
                    "type": "warning",
                    "warning": {
                        "code": "domain_mismatch",
                        "message": mismatch,
                        "blocking": False,
                    },
                }
            )

        # Clear previous proposal visually for the client
        self.emit({"type": "proposal_cleared", "reason": "nuevo_encargo"})

        self.last_prompt = cleaned
        turn = Turn(id=uuid.uuid4().hex[:10], prompt=cleaned, phase="leyendo")
        self.turns.append(turn)
        self.record(
            {
                "type": "host_action",
                "action": "start_turn",
                "id": turn.id,
                "prompt": cleaned,
                "encargo": self.encargo.as_dict(),
            }
        )
        self.ctx.pending_plan = None
        self.ctx.pending_draft = None
        self.ctx.evidence = []
        self.workspace.ensure_index()
        try:
            if self.settings.skip_plan:
                self._draft_phase(turn, cleaned, phase="draft")
            else:
                self._plan_phase(turn, cleaned)
        except Exception as exc:  # noqa: BLE001
            code, message = humanize_exception(exc)
            self._set_phase("error")
            self.emit({"type": "error", "message": message, "code": code, "retryable": True})
        return turn

    def retry_last(self) -> Turn | None:
        if not self.last_prompt:
            raise TeroError("No hay un encargo previo para reintentar.", code="no_retry")
        return self.start_turn(self.last_prompt)

    def _plan_phase(self, turn: Turn, prompt: str) -> None:
        self._set_phase("leyendo")
        self.emit(
            {
                "type": "status",
                "phase": "leyendo",
                "detail": "leyendo fuentes de la carpeta",
                "step": "read",
                "progress": "1/2",
            }
        )
        agent = self._agent_for("plan")
        self.ctx.reset_tool_budget(PLAN_TOOL_BUDGET)
        self._set_phase("proponiendo_plan")
        self.emit(
            {
                "type": "status",
                "phase": "proponiendo_plan",
                "detail": "armando plan tipado",
                "step": "plan",
                "progress": "1/2",
            }
        )
        agent(self._user_payload(prompt), limits={"turns": PLAN_AGENT_TURNS})
        if self.ctx.pending_plan is None:
            self._set_phase("error")
            self.emit(
                {
                    "type": "error",
                    "message": "El agente no propuso un plan. Prueba de nuevo o usa --skip-plan.",
                    "code": "no_plan",
                    "retryable": True,
                }
            )
            return
        turn.plan = self.ctx.pending_plan
        pending_q = turn.plan.pending_question()
        if pending_q is not None:
            turn.phase = "esperando_clarificacion"
            self._set_phase("esperando_clarificacion")
            self.emit({"type": "plan", "id": turn.id, "plan": turn.plan.as_dict()})
            self.emit(
                {
                    "type": "plan_question",
                    "id": turn.id,
                    "question": pending_q.as_dict(),
                    "plan": turn.plan.as_dict(),
                }
            )
            return
        turn.phase = "esperando_plan"
        self._set_phase("esperando_plan")
        self.emit({"type": "plan", "id": turn.id, "plan": turn.plan.as_dict()})

    def answer_plan_question(
        self,
        *,
        option_id: str | None = None,
        free_text: str | None = None,
        question_id: str | None = None,
    ) -> Turn:
        turn = self._current_turn()
        if turn is None or turn.plan is None:
            raise RuntimeError("No hay plan pendiente.")
        turn.plan = answer_question(
            turn.plan,
            question_id=question_id,
            option_id=option_id,
            free_text=free_text,
        )
        self.ctx.pending_plan = turn.plan
        pending = turn.plan.pending_question()
        self.emit({"type": "plan", "id": turn.id, "plan": turn.plan.as_dict()})
        if pending is not None:
            turn.phase = "esperando_clarificacion"
            self._set_phase("esperando_clarificacion")
            self.emit(
                {
                    "type": "plan_question",
                    "id": turn.id,
                    "question": pending.as_dict(),
                    "plan": turn.plan.as_dict(),
                }
            )
        else:
            turn.phase = "esperando_plan"
            self._set_phase("esperando_plan")
            self.emit({"type": "plan_ready", "id": turn.id, "plan": turn.plan.as_dict()})
        return turn

    def edit_plan_assumption(self, assumption_id: str, text: str) -> Turn:
        turn = self._current_turn()
        if turn is None or turn.plan is None:
            raise RuntimeError("No hay plan pendiente.")
        turn.plan = edit_assumption(turn.plan, assumption_id, text)
        self.ctx.pending_plan = turn.plan
        self.emit({"type": "plan", "id": turn.id, "plan": turn.plan.as_dict()})
        return turn

    def decide_plan(self, decision: str, edits: dict[str, str] | None = None) -> Turn:
        turn = self._current_turn()
        if turn is None or turn.plan is None:
            raise RuntimeError("No hay plan pendiente.")
        self.record(
            {
                "type": "host_action",
                "action": "decide_plan",
                "id": turn.id,
                "decision": decision,
                "edits": edits or {},
            }
        )
        if decision == "cancel":
            turn.phase = "listo"
            turn.plan.status = "cancelado"
            self.ctx.pending_plan = None
            self.ctx.pending_draft = None
            self._set_phase("idle")
            self.emit({"type": "plan_cancelled", "id": turn.id})
            self.emit({"type": "proposal_cleared", "reason": "plan_cancelado"})
            self.emit(
                {
                    "type": "status",
                    "phase": "idle",
                    "detail": "Plan cancelado. Elige un rumbo o escribe un nuevo encargo.",
                }
            )
            return turn
        if edits:
            turn.plan = apply_plan_edits(turn.plan, edits)
        assert turn.plan is not None
        # Sync encargo chips from confirmed decisiones
        d = turn.plan.decisiones
        self.set_encargo(
            Encargo(
                curso=d.curso or self.encargo.curso,
                asignatura=d.asignatura or self.encargo.asignatura,
                oa=turn.plan.oa or self.encargo.oa,
                duracion=turn.plan.duracion or self.encargo.duracion,
                tipo=turn.plan.tipo,
                notas=self.encargo.notas,
                rumbo=self.encargo.rumbo,
                tema=d.tema or self.encargo.tema,
            )
        )
        self.emit({"type": "encargo", "encargo": self.encargo.as_dict()})
        turn.plan.status = "listo"
        self.ctx.pending_plan = turn.plan
        self.emit({"type": "plan_approved", "id": turn.id, "plan": turn.plan.as_dict()})
        follow = (
            f"El docente aprobó el plan:\n{turn.plan.as_dict()}\n"
            f"Encargo original: {turn.prompt}\n"
            "Redacta ahora el artefacto con cite_evidence y draft_artifact. "
            "Respeta el tipo del plan aprobado. "
            "Si list_oa trae catalog_covers=false, no uses un OA de otro curso. "
            "Si puedes, pasa payload_json con el schema del tipo (ítems SM/V-F, propósito, etc.)."
        )
        try:
            self._draft_phase(turn, follow, phase="draft")
        except Exception as exc:  # noqa: BLE001
            code, message = humanize_exception(exc)
            self._set_phase("error")
            self.emit({"type": "error", "message": message, "code": code, "retryable": True})
        return turn

    def _draft_phase(self, turn: Turn, prompt: str, *, phase: str) -> None:
        self._set_phase("escribiendo")
        self.emit(
            {
                "type": "status",
                "phase": "escribiendo",
                "detail": "redactando borrador",
                "step": "draft",
                "progress": "2/2",
            }
        )
        # Bedrock sometimes returns tools/text without draft_artifact — retry once.
        for attempt in (1, 2):
            self.ctx.pending_draft = None
            self._stream_buf = []
            self.ctx.reset_tool_budget(DRAFT_TOOL_BUDGET)
            if attempt == 2:
                self.emit(
                    {
                        "type": "status",
                        "phase": "escribiendo",
                        "detail": "reintento: el modelo no entregó borrador",
                        "step": "draft_retry",
                        "progress": "2/2",
                    }
                )
                self.emit(
                    {
                        "type": "activity",
                        "tool": "draft",
                        "state": "start",
                        "detail": "reintento automático",
                    }
                )
            agent = self._agent_for(phase)
            nudge = prompt
            if attempt == 2:
                nudge = (
                    prompt
                    + "\n\nIMPORTANTE: Debes llamar a draft_artifact ahora con el markdown completo. "
                    "No te detengas solo en texto."
                )
            try:
                agent(
                    self._user_payload(nudge),
                    limits={"turns": DRAFT_AGENT_TURNS},
                )
            except Exception as exc:  # noqa: BLE001 — Bedrock stream/ToolUse flakiness
                if attempt == 1 and _is_retryable_stream_error(exc):
                    self.emit(
                        {
                            "type": "status",
                            "phase": "escribiendo",
                            "detail": "reintento: error de stream/ToolUse de Bedrock",
                            "step": "draft_stream_retry",
                            "progress": "2/2",
                        }
                    )
                    continue
                raise
            if self.ctx.pending_draft is not None:
                break
            salvaged = salvage_draft_from_text(
                "".join(self._stream_buf),
                fallback_tipo=self.encargo.tipo or (turn.plan.tipo if turn.plan else None),
                evidencias=list(self.ctx.evidence),
            )
            if salvaged is not None:
                self.ctx.pending_draft = salvaged
                self.emit(
                    {
                        "type": "warning",
                        "warning": {
                            "code": "draft_salvaged",
                            "message": (
                                "El modelo escribió draft_artifact como texto. "
                                "tero armó el borrador igual para que puedas decidir s/n/b/c."
                            ),
                            "blocking": False,
                        },
                    }
                )
                self.emit(
                    {
                        "type": "activity",
                        "tool": "draft",
                        "state": "end",
                        "detail": "recuperado desde texto",
                    }
                )
                break
        if self.ctx.pending_draft is None:
            self._set_phase("error")
            self.emit(
                {
                    "type": "error",
                    "message": (
                        "El agente no entregó un borrador (ni en el reintento). "
                        "Pulsa r o /retry para volver a intentar."
                    ),
                    "code": "no_draft",
                    "retryable": True,
                }
            )
            return
        draft = self.ctx.pending_draft
        expected = (turn.plan.tipo if turn.plan is not None else None) or self.encargo.tipo
        if expected is not None and draft.tipo != expected:
            # Keep plan.tipo / encargo.tipo. The draft tipo is what the model delivered.
            self.emit(
                {
                    "type": "warning",
                    "warning": {
                        "code": "tipo_desviado",
                        "message": (
                            f"El plan pedía {expected.label} y el borrador llegó como "
                            f"{draft.tipo.label}. No cambié el tipo del plan: decide s, "
                            "o c si quieres el otro entregable."
                        ),
                        "blocking": False,
                    },
                }
            )
        if self.ctx.budget_exhausted:
            self.emit(
                {
                    "type": "warning",
                    "warning": {
                        "code": "tool_budget_exhausted",
                        "message": (
                            "Se cortó el loop de herramientas en el borrador "
                            f"(tope {DRAFT_TOOL_BUDGET}). Revisa si el material quedó corto."
                        ),
                        "blocking": False,
                    },
                }
            )
        draft.warnings = collect_warnings(
            workspace=self.workspace,
            encargo=self.encargo,
            plan=turn.plan,
            draft=draft,
            prompt=turn.prompt,
        )
        turn.draft = draft
        turn.phase = "esperando_criterio"
        self._set_phase("esperando_criterio")
        self.emit({"type": "proposal", "id": turn.id, "artifact": draft.as_dict()})

    def decide_gate(self, decision: GateDecision, note: str = "") -> GateResult:
        turn = self._current_turn()
        if turn is None or turn.draft is None:
            raise RuntimeError("No hay propuesta pendiente.")
        self.record(
            {
                "type": "host_action",
                "action": "decide_gate",
                "id": turn.id,
                "decision": decision,
                "note": note,
            }
        )
        if decision == "c" and note.strip():
            turn.critique_notes.append(note.strip())
            persist_critique(self.workspace, turn.id, note.strip())
            self.emit(
                {
                    "type": "critique_saved",
                    "id": turn.id,
                    "note": note.strip(),
                    "n": len(turn.critique_notes),
                }
            )
        result = apply_gate(
            workspace=self.workspace,
            encargo=self.encargo,
            plan=turn.plan,
            draft=turn.draft,
            decision=decision,
            note=note,
            critique_notes=turn.critique_notes,
        )
        turn.gate = decision
        if decision == "c":
            critique = note.strip() or "Hazlo más usable en aula: más evidencia, menos adorno."
            follow = (
                f"CORRECCIÓN DOCENTE: {critique}\n"
                f"Reescribe el artefacto tipo {turn.draft.tipo.value} titulado {turn.draft.titulo}."
            )
            self.ctx.pending_draft = None
            try:
                self._draft_phase(turn, follow, phase="correct")
            except Exception as exc:  # noqa: BLE001
                code, message = humanize_exception(exc)
                self._set_phase("error")
                self.emit({"type": "error", "message": message, "code": code, "retryable": True})
            return result
        if result.path is not None:
            turn.artifact_path = str(result.path)
            event_type = "accepted" if decision == "s" else "draft_saved"
            self.emit({"type": event_type, "id": turn.id, "path": str(result.path)})
        elif decision == "n":
            self.emit({"type": "discarded", "id": turn.id})
            self.emit({"type": "proposal_cleared", "reason": "descartado"})
        turn.phase = "listo"
        self._set_phase("listo")
        return result

    def exportable_path(self) -> Path | None:
        """Last accepted *or* draft artifact path for /export."""
        for turn in reversed(self.turns):
            if turn.artifact_path:
                path = Path(turn.artifact_path)
                if path.exists():
                    return path
        return None

    def _current_turn(self) -> Turn | None:
        return self.turns[-1] if self.turns else None

    def _user_payload(self, prompt: str) -> str:
        chips = ", ".join(self.encargo.chips())
        header = f"Encargo: {chips}\n" if chips else ""
        return header + prompt


def _looks_garbage(text: str) -> bool:
    compact = "".join(text.split())
    if len(compact) < 2:
        return True
    # mostly punctuation / keyboard smash
    alpha = sum(1 for ch in compact if ch.isalpha())
    if alpha < 2 and len(compact) >= 2:
        return True
    if len(set(compact)) == 1 and len(compact) >= 3:
        return True
    return False
