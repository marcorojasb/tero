"""JSONL host: stdin commands, stdout events. Logs go to stderr only."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, TextIO

from tero.approval import classify_approval
from tero.config import Settings
from tero.curriculum.catalog import catalog_summary, list_oa, resolve_oa
from tero.errors import ProtocolError, TeroError, humanize_exception
from tero.export import export_docx, export_latex, export_markdown
from tero.offline import model_label
from tero.protocol import decode, encode
from tero.session import TeacherSession
from tero.transcript import public_inbound
from tero.types import Encargo
from tero.workspace import Workspace

_RETRYABLE = {
    "bedrock_auth",
    "bedrock_throttle",
    "bedrock_model",
    "network",
    "no_propuesta",
    "no_response",
    "host_error",
}


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
        """`--yes` (demo/tests): aprueba la propuesta sin teclado."""
        if event.get("type") == "propuesta":
            self.session.aprobar("autogate --yes")

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
                        "retryable": exc.code in _RETRYABLE,
                    }
                )
            except Exception as exc:  # noqa: BLE001 — surface to TUI, keep host alive
                code, message = humanize_exception(exc)
                self.emit({"type": "error", "message": message, "code": code, "retryable": True})
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
            self._update_encargo(message)
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
        if kind == "prompt":
            text = str(message.get("text") or "").strip()
            if not text:
                raise ProtocolError("mensaje vacío — escribe qué necesitas")
            self._prompt(text)
            return
        if kind == "retry":
            turn = self.session.retry_last()
            if turn:
                self.emit({"type": "turn", "turn": turn.as_dict()})
            return
        if kind == "aprobar":
            decision = str(message.get("decision") or "aprobar")
            note = str(message.get("note") or "")
            if decision == "descartar":
                self.session.descartar(note)
            elif decision == "aprobar":
                self.session.aprobar(note)
            else:
                raise ProtocolError("decisión inválida: usa aprobar o descartar")
            return
        if kind == "export":
            self._export(message)
            return
        raise ProtocolError(f"no implementado: {kind}")

    def _prompt(self, text: str) -> None:
        """Si hay propuesta pendiente, la respuesta se clasifica antes de conversar."""
        if self.session.pending_propuesta is not None:
            decision = classify_approval(text)
            if decision.kind == "aprobar":
                self.session.aprobar(decision.note or text)
                return
            if decision.kind == "descartar":
                self.session.descartar(decision.note or text)
                return
            if decision.kind == "cambiar":
                self.session.pedir_cambio(decision.note or text)
                return
        turn = self.session.start_turn(text)
        self.emit({"type": "turn", "turn": turn.as_dict()})

    def _update_encargo(self, message: dict[str, Any]) -> None:
        encargo = Encargo.from_dict(message.get("encargo") or {})
        # Validate /oa against catalog when possible; keep chip but warn if unknown.
        if encargo.oa:
            resolved = resolve_oa(encargo.oa, curso=encargo.curso, asignatura=encargo.asignatura)
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
        if self.session.pending_propuesta is not None:
            self.emit(
                {
                    "type": "warning",
                    "warning": {
                        "code": "encargo_changed",
                        "message": (
                            "Contexto actualizado. La propuesta pendiente sigue ahí: "
                            "apruébala, pide cambios o descártala."
                        ),
                        "blocking": False,
                    },
                }
            )

    def _export(self, message: dict[str, Any]) -> None:
        source = self.session.exportable_path()
        if source is None:
            raise ProtocolError(
                "No hay material escrito para exportar. Aprueba una propuesta primero. "
                "Después: /export md|latex"
            )
        kind_src = "derivado" if "derivados" in source.parts else "legado"
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
            kind = "derivado" if folder == "derivados" else "legado"
            items.append({"label": path.stem[:42], "path": f"{folder}/{path.name}", "kind": kind})
    return items[:8]


def _write_feedback(workspace: Workspace, session: TeacherSession) -> Path | None:
    notes: list[str] = []
    for turn in session.turns:
        for note in turn.peticiones:
            notes.append(f"- turn `{turn.id}`: {note}")
    if not notes:
        return None
    from datetime import UTC, datetime

    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    relative = f".tero/feedback-{stamp}.md"
    body = "# Cambios pedidos durante la sesión\n\n" + "\n".join(notes) + "\n"
    return workspace.write_artifact(relative, body, overwrite=True)
