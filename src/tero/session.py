"""Sesión docente: un agente Strands que conversa. El modelo nunca escribe archivos.

El agente entiende el primer mensaje (responder / crear / editar-adaptar), pregunta en
lenguaje natural si le falta algo, y propone material **en memoria**. El host escribe
en `derivados/` solo cuando la persona aprueba.
"""

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
from tero.gate import WriteResult, write_approved
from tero.offline import OfflineModel
from tero.prompts import system_prompt
from tero.salvage import salvage_propuesta_from_text
from tero.tools import DRAFT_AGENT_TURNS, DRAFT_TOOL_BUDGET, TurnContext, build_tools
from tero.transcript import TranscriptLog
from tero.types import Encargo, Propuesta, ProtocolPhase, Turn
from tero.workspace import Workspace

_DELTA_FLUSH = 80
_MAX_PROMPT = 8000
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
    """Bedrock ConverseStream ToolUse / modelStreamErrorException flakiness."""
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
        self.last_prompt: str = ""
        self.last_artifact: Path | None = None
        self.pending_propuesta: Propuesta | None = None
        self._stream_buf: list[str] = []
        self._delta_buf: str = ""
        self._last_tool_activity: tuple[str, str] | None = None

    # ------------------------------------------------------------------ plumbing

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

    def _agent_for(self) -> Agent:
        self.ctx.emit = self.emit
        model = make_model(self.settings, self.encargo)
        return Agent(
            model=model,
            system_prompt=system_prompt(self.encargo),
            tools=build_tools(self.ctx),
            callback_handler=self._callback,
        )

    def _flush_delta(self) -> None:
        text = self._delta_buf
        if not text:
            return
        self._delta_buf = ""
        self.emit({"type": "delta", "text": text})

    def _callback(self, **kwargs: Any) -> None:
        if "data" in kwargs and kwargs["data"]:
            chunk = str(kwargs["data"])
            self._stream_buf.append(chunk)
            self._delta_buf += chunk
            if len(self._delta_buf) >= _DELTA_FLUSH or "\n" in chunk:
                self._flush_delta()
        tool = kwargs.get("current_tool_use") or {}
        name = str(tool.get("name") or "").strip()
        if not name:
            return
        self._flush_delta()
        tool_id = str(tool.get("toolUseId") or tool.get("tool_use_id") or "")
        key = (name, tool_id)
        if key == self._last_tool_activity:
            return
        self._last_tool_activity = key
        self.emit({"type": "activity", "tool": name, "state": "start", "detail": name})

    # --------------------------------------------------------------------- turno

    def start_turn(self, prompt: str) -> Turn:
        """Un mensaje de la persona. El agente decide si responde, crea o edita."""
        cleaned = (prompt or "").strip()
        if not cleaned:
            raise TeroError(
                "Escribe un mensaje: tero conversa, no adivina con la línea vacía.",
                code="empty_prompt",
            )
        if len(cleaned) > _MAX_PROMPT:
            cleaned = cleaned[:_MAX_PROMPT] + "…"
            self._warn("long_paste", "Pegado muy largo: se truncó a 8000 caracteres.")

        synced = sync_encargo_from_prompt(self.encargo, cleaned)
        if synced != self.encargo:
            self.set_encargo(synced)
            self.emit({"type": "encargo", "encargo": self.encargo.as_dict()})

        mismatch = source_domain_warning(self.workspace, cleaned, self.encargo)
        if mismatch:
            self._warn("domain_mismatch", mismatch)

        self.last_prompt = cleaned
        turn = Turn(id=uuid.uuid4().hex[:10], prompt=cleaned, phase="pensando")
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
        self.ctx.pending_propuesta = None
        self.ctx.evidence = []
        self.pending_propuesta = None
        self.workspace.ensure_index()
        try:
            self._run_turn(turn, self._user_payload(cleaned))
        except Exception as exc:  # noqa: BLE001 — se muestra humanizado en la TUI
            self._fail(exc)
        return turn

    def retry_last(self) -> Turn | None:
        if not self.last_prompt:
            raise TeroError("No hay un mensaje previo para reintentar.", code="no_retry")
        return self.start_turn(self.last_prompt)

    def _run_turn(self, turn: Turn, prompt: str) -> None:
        self._set_phase("pensando")
        self.emit({"type": "status", "phase": "pensando", "detail": "pensando", "step": "turn"})
        text = self._call_model(prompt)
        propuesta = self.ctx.pending_propuesta
        if propuesta is None:
            propuesta = salvage_propuesta_from_text(
                text,
                fallback_tipo=self.encargo.tipo,
                evidencias=list(self.ctx.evidence),
            )
            if propuesta is not None:
                self._warn(
                    "propuesta_salvaged",
                    "El modelo escribió la propuesta como texto. tero la armó igual "
                    "para que puedas revisarla.",
                )
        if propuesta is not None:
            turn.propuesta = propuesta
            self.pending_propuesta = propuesta
            self._finish_with_proposal(turn, propuesta)
            return
        if not text:
            raise TeroError(
                "El agente no respondió nada. Pulsa r para reintentar.", code="no_response"
            )
        turn.respuesta = text
        turn.phase = "idle"
        self._set_phase("idle")
        self.emit({"type": "respuesta", "id": turn.id, "texto": text})

    def _call_model(self, prompt: str) -> str:
        """Corre el agente una vez; reintenta solo si Bedrock corta el stream."""
        self._stream_buf = []
        self._delta_buf = ""
        self._last_tool_activity = None
        self.ctx.reset_tool_budget(DRAFT_TOOL_BUDGET)
        agent = self._agent_for()
        try:
            agent(prompt, limits={"turns": DRAFT_AGENT_TURNS})
        except Exception as exc:  # noqa: BLE001 — Bedrock stream/ToolUse flakiness
            self._flush_delta()
            if not _is_retryable_stream_error(exc):
                raise
            self.emit(
                {
                    "type": "status",
                    "phase": "pensando",
                    "detail": "reintento: error de stream de Bedrock",
                    "step": "stream_retry",
                }
            )
            self._stream_buf = []
            self._delta_buf = ""
            self._last_tool_activity = None
            self.ctx.reset_tool_budget(DRAFT_TOOL_BUDGET)
            agent = self._agent_for()
            agent(prompt, limits={"turns": DRAFT_AGENT_TURNS})
        self._flush_delta()
        return "".join(self._stream_buf).strip()

    def _finish_with_proposal(self, turn: Turn, propuesta: Propuesta) -> None:
        propuesta.draft.warnings = collect_warnings(
            workspace=self.workspace,
            encargo=self.encargo,
            draft=propuesta.draft,
            prompt=turn.prompt,
        )
        if self.ctx.budget_exhausted:
            self._warn(
                "tool_budget_exhausted",
                "Se cortó el loop de herramientas "
                f"(tope {DRAFT_TOOL_BUDGET}). Revisa si el material quedó corto.",
            )
        turn.phase = "esperando_aprobacion"
        self._set_phase("esperando_aprobacion")
        self.emit({"type": "propuesta", "id": turn.id, "propuesta": propuesta.as_dict()})

    # ------------------------------------------------------------------ decisión

    def aprobar(self, note: str = "") -> WriteResult:
        """Única vía de escritura: la persona aprobó lo que vio."""
        turn = self._current_turn()
        propuesta = self.pending_propuesta
        if propuesta is None:
            raise TeroError("No hay una propuesta pendiente que aprobar.", code="no_propuesta")
        self.record(
            {
                "type": "host_action",
                "action": "aprobar",
                "id": turn.id if turn else "",
                "note": note,
            }
        )
        before = self.workspace.fingerprint_sources()
        result = write_approved(
            workspace=self.workspace,
            encargo=self.encargo,
            propuesta=propuesta,
            note=note,
        )
        after = self.workspace.fingerprint_sources()
        if turn is not None:
            turn.aprobada = True
            turn.phase = "listo"
            turn.artifact_path = str(result.path) if result.path else None
        if result.path is not None:
            self.last_artifact = result.path
        self.pending_propuesta = None
        self.ctx.pending_propuesta = None
        self.emit(
            {
                "type": "aprobacion",
                "id": turn.id if turn else "",
                "decision": "aprobar",
                "note": note,
            }
        )
        self.emit(
            {
                "type": "escrito",
                "id": turn.id if turn else "",
                "path": str(result.path) if result.path else None,
                "accion": propuesta.accion,
            }
        )
        if after != before:
            self._warn(
                "source_changed",
                "Un original cambió durante la escritura. tero no escribe en fuentes/: "
                "revisa la carpeta.",
            )
        self._set_phase("listo")
        return result

    def descartar(self, note: str = "") -> Turn | None:
        turn = self._current_turn()
        if self.pending_propuesta is None:
            raise TeroError("No hay una propuesta pendiente.", code="no_propuesta")
        self.record(
            {
                "type": "host_action",
                "action": "descartar",
                "id": turn.id if turn else "",
                "note": note,
            }
        )
        self.pending_propuesta = None
        self.ctx.pending_propuesta = None
        if turn is not None:
            turn.phase = "idle"
        self.emit(
            {
                "type": "aprobacion",
                "id": turn.id if turn else "",
                "decision": "descartar",
                "note": note,
            }
        )
        self._set_phase("idle")
        return turn

    def pedir_cambio(self, note: str) -> Turn:
        """La persona pide cambios sobre la propuesta pendiente: el agente la revisa."""
        turn = self._current_turn()
        propuesta = self.pending_propuesta
        if propuesta is None:
            raise TeroError("No hay una propuesta pendiente que corregir.", code="no_propuesta")
        pedido = (note or "").strip() or "Hazla más usable en aula: más evidencia, menos adorno."
        if turn is not None:
            turn.peticiones.append(pedido)
        self.record(
            {
                "type": "host_action",
                "action": "pedir_cambio",
                "id": turn.id if turn else "",
                "note": pedido,
            }
        )
        self.emit(
            {
                "type": "aprobacion",
                "id": turn.id if turn else "",
                "decision": "cambiar",
                "note": pedido,
            }
        )
        follow = (
            f"La persona revisó tu propuesta y pide cambios: {pedido}\n"
            f"ACCIÓN ESPERADA: {propuesta.accion}\n\n"
            f"Propuesta anterior ({propuesta.tipo.label} · {propuesta.titulo}):\n"
            f"{propuesta.vista_previa[:6000]}\n\n"
            "Entrega la versión corregida con proponer_crear o proponer_editar. "
            "Mantén la evidencia y no escribas archivos."
        )
        # La propuesta anterior sigue viva hasta que llegue una nueva: si la
        # revisión falla, la persona no pierde lo que ya tenía a la vista.
        self.ctx.pending_propuesta = None
        nuevo = Turn(id=uuid.uuid4().hex[:10], prompt=pedido, phase="pensando")
        self.turns.append(nuevo)
        try:
            self._run_turn(nuevo, self._user_payload(follow))
        except Exception as exc:  # noqa: BLE001
            self._fail(exc)
        return nuevo

    # ------------------------------------------------------------------- helpers

    def exportable_path(self) -> Path | None:
        for turn in reversed(self.turns):
            if turn.artifact_path:
                path = Path(turn.artifact_path)
                if path.exists():
                    return path
        if self.last_artifact and self.last_artifact.exists():
            return self.last_artifact
        return None

    def _current_turn(self) -> Turn | None:
        return self.turns[-1] if self.turns else None

    def _user_payload(self, prompt: str) -> str:
        context = self.encargo.context_line()
        return f"Contexto: {context}\n\n{prompt}"

    def _warn(self, code: str, message: str) -> None:
        self.emit(
            {
                "type": "warning",
                "warning": {"code": code, "message": message, "blocking": False},
            }
        )

    def _fail(self, exc: BaseException) -> None:
        code, message = humanize_exception(exc)
        self._set_phase("error")
        self.emit({"type": "error", "message": message, "code": code, "retryable": True})
