"""JSONL host: stdin commands, stdout events. Logs go to stderr only."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, TextIO

from tero.config import Settings
from tero.curriculum.catalog import catalog_summary, list_oa, resolve_oa
from tero.encargo_sync import apply_rumbo
from tero.errors import ProtocolError, TeroError, humanize_exception
from tero.export import export_docx, export_latex, export_markdown
from tero.offline import model_label
from tero.protocol import decode, encode
from tero.session import TeacherSession
from tero.transcript import public_inbound
from tero.types import Encargo
from tero.workspace import Workspace

_FULL_PLAN_KEYS = (
    "supuestos",
    "como_abordare",
    "questions",
    "entregables",
    "resultado_previsto",
    "decisiones",
)


def _flat_plan_edits(payload: object) -> dict[str, str] | None:
    """Accept only flat string patches; full plan.as_dict() → None (approve as-is)."""
    if not isinstance(payload, dict) or not payload:
        return None
    if isinstance(payload.get("decisiones"), dict):
        return None
    if any(isinstance(payload.get(key), (list, tuple)) for key in _FULL_PLAN_KEYS):
        return None
    out: dict[str, str] = {}
    for key, value in payload.items():
        if value is None or isinstance(value, (list, tuple, dict)):
            continue
        text = str(value).strip()
        if text:
            out[str(key)] = text
    return out or None


class Bridge:
    def __init__(
        self,
        settings: Settings,
        *,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
        auto_yes: bool = False,
    ) -> None:
        self.settings = settings
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.auto_yes = auto_yes
        self.workspace = Workspace(settings.carpeta)
        self.session = TeacherSession(self.workspace, settings, emit=self._client_emit)

    def _client_emit(self, event: dict[str, Any]) -> None:
        self.stdout.write(encode(event) + "\n")
        self.stdout.flush()
        if self.auto_yes:
            self._maybe_autogate(event)

    def emit(self, event: dict[str, Any]) -> None:
        """Stdout (+ autogate). Transcript even if tests swap `session`."""
        self.session.record(event)
        self._client_emit(event)

    def _maybe_autogate(self, event: dict[str, Any]) -> None:
        kind = event.get("type")
        if kind == "plan_question":
            # Prefer suggested option for offline/demo autogate
            question = event.get("question") or {}
            options = question.get("options") or []
            suggested = next((opt for opt in options if opt.get("suggested")), None)
            option_id = (suggested or (options[0] if options else {})).get("id") or "1"
            self.session.answer_plan_question(option_id=str(option_id))
        elif kind == "plan_ready":
            self.session.decide_plan("approve")
        elif kind == "plan":
            plan = event.get("plan") or {}
            # Plans with clarification questions wait for plan_ready.
            if plan.get("questions"):
                return
            if plan.get("status") == "clarificando":
                return
            self.session.decide_plan("approve")
        elif kind == "proposal":
            self.session.decide_gate("s")

    def serve(self) -> int:
        self.emit(
            {
                "type": "ready",
                "mode": "offline" if self.settings.offline else "bedrock",
                "model": model_label(self.settings.offline, self.settings.model_id),
                "carpeta": str(self.workspace.root),
                "transcript": str(self.session.transcript.path),
            }
        )
        for line in self.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = decode(line)
            except ProtocolError as exc:
                self.emit({"type": "error", "message": exc.message, "code": exc.code})
                continue
            kind = message["type"]
            if kind == "shutdown":
                self.emit({"type": "bye"})
                return 0
            try:
                self._handle(message)
            except TeroError as exc:
                self.emit(
                    {
                        "type": "error",
                        "message": exc.message,
                        "code": exc.code,
                        "retryable": exc.code
                        in {
                            "bedrock_auth",
                            "bedrock_throttle",
                            "bedrock_model",
                            "network",
                            "no_plan",
                            "no_draft",
                            "host_error",
                        },
                    }
                )
            except Exception as exc:  # noqa: BLE001 — surface to TUI, keep host alive
                code, message = humanize_exception(exc)
                self.emit(
                    {
                        "type": "error",
                        "message": message,
                        "code": code,
                        "retryable": True,
                    }
                )
        return 0

    def _handle(self, message: dict[str, Any]) -> None:
        kind = message["type"]
        if kind == "hello":
            if message.get("encargo"):
                self.session.set_encargo(Encargo.from_dict(message["encargo"]))
            carpeta = message.get("carpeta")
            if carpeta:
                self.workspace = Workspace(Path(carpeta))
                self.session = TeacherSession(
                    self.workspace,
                    self.settings,
                    encargo=self.session.encargo,
                    emit=self._client_emit,
                )
            self.session.record({"type": "inbound", "command": public_inbound(message)})
            sources = self.workspace.list_sources()
            self.emit(
                {
                    "type": "hello_ok",
                    "carpeta": str(self.workspace.root),
                    "encargo": self.session.encargo.as_dict(),
                    "fuentes": len(sources),
                    "changed": sum(1 for item in sources if item.changed),
                    "sessions": _recent_sessions(self.workspace),
                    "curriculum": catalog_summary(),
                    "transcript": str(self.session.transcript.path),
                }
            )
            _emit_oa_options(self, self.session.encargo)
            return
        self.session.record({"type": "inbound", "command": public_inbound(message)})
        if kind == "encargo.update":
            encargo = Encargo.from_dict(message.get("encargo") or {})
            # Validate /oa against catalog when possible; keep chip but warn if unknown.
            if encargo.oa:
                resolved = resolve_oa(
                    encargo.oa, curso=encargo.curso, asignatura=encargo.asignatura
                )
                if resolved:
                    encargo = Encargo(
                        curso=encargo.curso,
                        asignatura=encargo.asignatura,
                        oa=resolved.chip(),
                        duracion=encargo.duracion,
                        tipo=encargo.tipo,
                        notas=encargo.notas,
                        rumbo=encargo.rumbo,
                        tema=encargo.tema,
                    )
                else:
                    self.emit(
                        {
                            "type": "warning",
                            "warning": {
                                "code": "oa_unknown",
                                "message": (
                                    f"OA «{encargo.oa}» no está en el catálogo Chile. "
                                    "Usa /curso + /asignatura y elige un id de la lista, "
                                    "o list_oa en el agente."
                                ),
                                "blocking": False,
                            },
                        }
                    )
            self.session.set_encargo(encargo)
            self.emit({"type": "encargo", "encargo": self.session.encargo.as_dict()})
            _emit_oa_options(self, self.session.encargo)
            # Changing tipo/curso/oa mid-flight MUST clear stale proposal (not just warn).
            if self.session.phase in {
                "esperando_criterio",
                "esperando_plan",
                "esperando_clarificacion",
                "escribiendo",
                "proponiendo_plan",
            }:
                turn = self.session.turns[-1] if self.session.turns else None
                if turn is not None:
                    turn.draft = None
                self.session.ctx.pending_draft = None
                self.emit({"type": "proposal_cleared", "reason": "encargo_cambiado"})
                self.emit(
                    {
                        "type": "warning",
                        "warning": {
                            "code": "encargo_changed",
                            "message": (
                                "Encargo actualizado — propuesta anterior archivada. "
                                "Envía un nuevo prompt para regenerar el plan (evita contexto mezclado)."
                            ),
                            "blocking": False,
                        },
                    }
                )
            return
        if kind == "curriculum.list":
            curso = str(message.get("curso") or self.session.encargo.curso or "")
            asignatura = str(message.get("asignatura") or self.session.encargo.asignatura or "")
            rows = [item.as_dict() for item in list_oa(curso, asignatura)]
            self.emit(
                {
                    "type": "oa_options",
                    "oas": rows,
                    "curso": curso,
                    "asignatura": asignatura,
                }
            )
            return
        if kind == "rumbo":
            rumbo = str(message.get("rumbo") or "")
            self.session.set_encargo(apply_rumbo(self.session.encargo, rumbo))
            self.emit({"type": "encargo", "encargo": self.session.encargo.as_dict()})
            self.emit({"type": "rumbo", "rumbo": self.session.encargo.rumbo})
            _emit_oa_options(self, self.session.encargo)
            return
        if kind == "prompt":
            text = str(message.get("text") or "").strip()
            if not text:
                raise ProtocolError("prompt vacío — escribe un encargo o elige un rumbo")
            turn = self.session.start_turn(text)
            self.emit({"type": "turn", "turn": turn.as_dict()})
            return
        if kind == "retry":
            turn = self.session.retry_last()
            if turn:
                self.emit({"type": "turn", "turn": turn.as_dict()})
            return
        if kind == "plan.decide":
            decision = str(message.get("decision") or "approve")
            edits = _flat_plan_edits(message.get("plan"))
            self.session.decide_plan(decision, edits)
            return
        if kind == "plan.answer":
            self.session.answer_plan_question(
                option_id=str(message["option_id"])
                if message.get("option_id") is not None
                else None,
                free_text=str(message["text"]) if message.get("text") is not None else None,
                question_id=str(message["question_id"])
                if message.get("question_id") is not None
                else None,
            )
            return
        if kind == "plan.edit_assumption":
            assumption_id = str(message.get("id") or message.get("assumption_id") or "s1")
            text = str(message.get("text") or "").strip()
            if not text:
                raise ProtocolError("supuesto vacío")
            self.session.edit_plan_assumption(assumption_id, text)
            return
        if kind == "gate":
            decision = str(message.get("decision") or "")
            if decision not in {"s", "n", "b", "c"}:
                raise ProtocolError("gate debe ser s, n, b o c")
            self.session.decide_gate(decision, str(message.get("note") or ""))  # type: ignore[arg-type]
            return
        if kind == "export":
            source = self.session.exportable_path()
            if source is None:
                raise ProtocolError(
                    "No hay artefacto para exportar. Acepta con `s` (derivados/) "
                    "o guarda borrador con `b` (borradores/) primero. "
                    "Después: /export md|latex"
                )
            kind_src = (
                "borrador"
                if "borrador" in source.parts or "borradores" in source.parts
                else "derivado"
            )
            fmt = str(message.get("format") or "md").lower()
            dest_raw = message.get("path")
            pdf_path = None
            if fmt == "docx":
                dest = Path(dest_raw) if dest_raw else source.with_suffix(".docx")
                path = export_docx(source, dest)
            elif fmt in {"latex", "tex"}:
                dest = Path(dest_raw) if dest_raw else source.with_suffix(".tex")
                try_pdf = bool(message.get("pdf"))
                path = export_latex(source, dest, try_pdf=try_pdf)
                maybe_pdf = path.with_suffix(".pdf")
                if maybe_pdf.exists():
                    pdf_path = str(maybe_pdf)
                fmt = "tex"
            else:
                dest = Path(dest_raw) if dest_raw else source.with_name(source.stem + ".export.md")
                path = export_markdown(source, dest)
            # Also offer a feedback sidecar summarizing session critiques
            feedback = _write_feedback(self.workspace, self.session)
            event = {
                "type": "exported",
                "path": str(path),
                "format": fmt,
                "source_kind": kind_src,
                "source_path": str(source),
                "feedback": str(feedback) if feedback else None,
            }
            if pdf_path:
                event["pdf"] = pdf_path
            self.emit(event)
            return
        raise ProtocolError(f"no implementado: {kind}")


def _emit_oa_options(bridge: Bridge, encargo: Encargo) -> None:
    if not (encargo.curso or encargo.asignatura):
        return
    rows = [item.as_dict() for item in list_oa(encargo.curso, encargo.asignatura)]
    bridge.emit(
        {
            "type": "oa_options",
            "oas": rows,
            "curso": encargo.curso,
            "asignatura": encargo.asignatura,
        }
    )


def _recent_sessions(workspace: Workspace) -> list[dict[str, str]]:
    """Lightweight recent artifact list for the home screen."""
    items: list[dict[str, str]] = []
    for folder in ("derivados", "borradores"):
        root = workspace.root / folder
        if not root.exists():
            continue
        for path in sorted(root.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:6]:
            kind = "derivado" if folder == "derivados" else "borrador"
            items.append({"label": path.stem[:42], "path": f"{folder}/{path.name}", "kind": kind})
    return items[:8]


def _write_feedback(workspace: Workspace, session: TeacherSession) -> Path | None:
    notes: list[str] = []
    for turn in session.turns:
        for note in turn.critique_notes:
            notes.append(f"- turn `{turn.id}`: {note}")
    if not notes:
        return None
    from datetime import UTC, datetime

    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    relative = f".tero/feedback-{stamp}.md"
    body = "# Feedback exportado desde tero\n\n" + "\n".join(notes) + "\n"
    return workspace.write_artifact(relative, body, overwrite=True)
