"""JSONL host: stdin commands, stdout events. Logs go to stderr only."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, TextIO

from tero.config import Settings
from tero.errors import ProtocolError, TeroError
from tero.export import export_docx, export_markdown
from tero.offline import model_label
from tero.protocol import decode, encode
from tero.session import TeacherSession
from tero.types import Encargo
from tero.workspace import Workspace


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
        self.session = TeacherSession(self.workspace, settings, emit=self.emit)

    def emit(self, event: dict[str, Any]) -> None:
        self.stdout.write(encode(event) + "\n")
        self.stdout.flush()
        if self.auto_yes:
            self._maybe_autogate(event)

    def _maybe_autogate(self, event: dict[str, Any]) -> None:
        kind = event.get("type")
        if kind == "plan":
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
            }
        )
        for line in self.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = decode(line)
            except ProtocolError as exc:
                self.emit({"type": "error", "message": exc.message})
                continue
            kind = message["type"]
            if kind == "shutdown":
                self.emit({"type": "bye"})
                return 0
            try:
                self._handle(message)
            except TeroError as exc:
                self.emit({"type": "error", "message": exc.message, "code": exc.code})
            except Exception as exc:  # noqa: BLE001 — surface to TUI, keep host alive
                self.emit({"type": "error", "message": str(exc)})
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
                    emit=self.emit,
                )
            sources = self.workspace.list_sources()
            self.emit(
                {
                    "type": "hello_ok",
                    "carpeta": str(self.workspace.root),
                    "encargo": self.session.encargo.as_dict(),
                    "fuentes": len(sources),
                    "changed": sum(1 for item in sources if item.changed),
                }
            )
            return
        if kind == "encargo.update":
            self.session.set_encargo(Encargo.from_dict(message.get("encargo") or {}))
            self.emit({"type": "encargo", "encargo": self.session.encargo.as_dict()})
            return
        if kind == "prompt":
            text = str(message.get("text") or "").strip()
            if not text:
                raise ProtocolError("prompt vacío")
            turn = self.session.start_turn(text)
            self.emit({"type": "turn", "turn": turn.as_dict()})
            return
        if kind == "plan.decide":
            self.session.decide_plan(str(message.get("decision") or "approve"), message.get("plan"))
            return
        if kind == "gate":
            decision = str(message.get("decision") or "")
            if decision not in {"s", "n", "b", "c"}:
                raise ProtocolError("gate debe ser s, n, b o c")
            self.session.decide_gate(decision, str(message.get("note") or ""))  # type: ignore[arg-type]
            return
        if kind == "export":
            turn = self.session.turns[-1] if self.session.turns else None
            if not turn or not turn.artifact_path:
                raise ProtocolError("no hay artefacto aceptado para exportar")
            source = Path(turn.artifact_path)
            fmt = str(message.get("format") or "md")
            dest_raw = message.get("path")
            if fmt == "docx":
                dest = Path(dest_raw) if dest_raw else source.with_suffix(".docx")
                path = export_docx(source, dest)
            else:
                dest = Path(dest_raw) if dest_raw else source.with_name(source.stem + ".export.md")
                path = export_markdown(source, dest)
            self.emit({"type": "exported", "path": str(path), "format": fmt})
            return
        raise ProtocolError(f"no implementado: {kind}")
