"""Teacher session: Strands Agent + HITL pauses. The model never writes derivados/."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from strands import Agent

from tero.config import Settings
from tero.evidence import collect_warnings
from tero.gate import GateResult, apply_gate
from tero.offline import OfflineModel
from tero.plan import apply_plan_edits
from tero.prompts import system_prompt
from tero.tools import TurnContext, build_tools
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
        temperature=0.3,
    )


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
        self.emit = emit or (lambda _event: None)
        self.turns: list[Turn] = []
        self.phase: ProtocolPhase = "idle"
        self.ctx = TurnContext(workspace=workspace, encargo=self.encargo, emit=self.emit)
        self._agent: Agent | None = None

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
            self.emit({"type": "delta", "text": str(kwargs["data"])})
        tool = kwargs.get("current_tool_use") or {}
        if tool.get("name"):
            self.emit({"type": "activity", "tool": tool["name"], "state": "delta"})

    def start_turn(self, prompt: str) -> Turn:
        turn = Turn(id=uuid.uuid4().hex[:10], prompt=prompt, phase="leyendo")
        self.turns.append(turn)
        self.ctx.pending_plan = None
        self.ctx.pending_draft = None
        self.ctx.evidence = []
        self.workspace.ensure_index()
        if self.settings.skip_plan:
            self._draft_phase(turn, prompt, phase="draft")
        else:
            self._plan_phase(turn, prompt)
        return turn

    def _plan_phase(self, turn: Turn, prompt: str) -> None:
        self._set_phase("leyendo")
        agent = self._agent_for("plan")
        self._set_phase("proponiendo_plan")
        agent(self._user_payload(prompt))
        if self.ctx.pending_plan is None:
            self._set_phase("error")
            self.emit(
                {
                    "type": "error",
                    "message": "El agente no propuso un plan. Prueba de nuevo o usa --skip-plan.",
                }
            )
            return
        turn.plan = self.ctx.pending_plan
        turn.phase = "esperando_plan"
        self._set_phase("esperando_plan")
        self.emit({"type": "plan", "id": turn.id, "plan": turn.plan.as_dict()})

    def decide_plan(self, decision: str, edits: dict[str, str] | None = None) -> Turn:
        turn = self._current_turn()
        if turn is None or turn.plan is None:
            raise RuntimeError("No hay plan pendiente.")
        if decision == "cancel":
            turn.phase = "listo"
            self._set_phase("idle")
            self.emit({"type": "plan_cancelled", "id": turn.id})
            return turn
        if decision == "edit" and edits:
            turn.plan = apply_plan_edits(turn.plan, edits)
        assert turn.plan is not None
        self.ctx.pending_plan = turn.plan
        self.emit({"type": "plan_approved", "id": turn.id, "plan": turn.plan.as_dict()})
        follow = (
            f"El docente aprobó el plan:\n{turn.plan.as_dict()}\n"
            f"Encargo original: {turn.prompt}\n"
            "Redacta ahora el artefacto con cite_evidence y draft_artifact."
        )
        self._draft_phase(turn, follow, phase="draft")
        return turn

    def _draft_phase(self, turn: Turn, prompt: str, *, phase: str) -> None:
        self._set_phase("escribiendo")
        agent = self._agent_for(phase)
        agent(self._user_payload(prompt))
        if self.ctx.pending_draft is None:
            self._set_phase("error")
            self.emit({"type": "error", "message": "El agente no entregó un borrador."})
            return
        draft = self.ctx.pending_draft
        draft.warnings = collect_warnings(
            workspace=self.workspace,
            encargo=self.encargo,
            plan=turn.plan,
            draft=draft,
        )
        turn.draft = draft
        turn.phase = "esperando_criterio"
        self._set_phase("esperando_criterio")
        self.emit({"type": "proposal", "id": turn.id, "artifact": draft.as_dict()})

    def decide_gate(self, decision: GateDecision, note: str = "") -> GateResult:
        turn = self._current_turn()
        if turn is None or turn.draft is None:
            raise RuntimeError("No hay propuesta pendiente.")
        result = apply_gate(
            workspace=self.workspace,
            encargo=self.encargo,
            plan=turn.plan,
            draft=turn.draft,
            decision=decision,
            note=note,
        )
        turn.gate = decision
        if decision == "c":
            critique = note.strip() or "Hazlo más usable en aula: más evidencia, menos adorno."
            follow = (
                f"CORRECCIÓN DOCENTE: {critique}\n"
                f"Reescribe el artefacto tipo {turn.draft.tipo.value} titulado {turn.draft.titulo}."
            )
            self.ctx.pending_draft = None
            self._draft_phase(turn, follow, phase="correct")
            return result
        if result.path is not None:
            turn.artifact_path = str(result.path)
            event_type = "accepted" if decision == "s" else "draft_saved"
            self.emit({"type": event_type, "id": turn.id, "path": str(result.path)})
        elif decision == "n":
            self.emit({"type": "discarded", "id": turn.id})
        turn.phase = "listo"
        self._set_phase("listo")
        return result

    def _current_turn(self) -> Turn | None:
        return self.turns[-1] if self.turns else None

    def _user_payload(self, prompt: str) -> str:
        chips = ", ".join(self.encargo.chips())
        header = f"Encargo: {chips}\n" if chips else ""
        return header + prompt
