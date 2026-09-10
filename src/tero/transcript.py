"""Full-session JSONL transcript under the carpeta (.tero/transcripciones/).

The carpeta is the system of record. This log is for later analysis of the
teacher loop (prompts, tools, plan, gate, export) — never AWS secrets.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tero import __version__
from tero.config import Settings
from tero.offline import model_label
from tero.workspace import Workspace

TRANSCRIPT_DIR = ".tero/transcripciones"
_SECRET_KEY = re.compile(
    r"(secret|password|token|authorization|api[_-]?key|aws_access|aws_secret|private_key)",
    re.IGNORECASE,
)
_INBOUND_KEEP = (
    "type",
    "text",
    "decision",
    "rumbo",
    "option_id",
    "question_id",
    "note",
    "format",
    "pdf",
    "id",
    "assumption_id",
    "path",
    "encargo",
    "plan",
    "carpeta",
)


class TranscriptLog:
    """Append-only JSONL. One file per TeacherSession (TUI/bridge/demo process)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0
        self._fh = self.path.open("a", encoding="utf-8")

    @classmethod
    def open(cls, workspace: Workspace, settings: Settings) -> TranscriptLog:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        name = f"{stamp}-{uuid.uuid4().hex[:8]}.jsonl"
        path = workspace.root / TRANSCRIPT_DIR / name
        log = cls(path)
        log.append(
            {
                "type": "session_start",
                "model": model_label(settings.offline, settings.model_id),
                "offline": bool(settings.offline),
                "carpeta": str(workspace.root),
                "tero": __version__,
                "region": settings.region if not settings.offline else "",
            }
        )
        return log

    def append(self, event: dict[str, Any]) -> None:
        self._seq += 1
        record = {"ts": datetime.now(UTC).isoformat(), "seq": self._seq}
        record.update(sanitize_event(event))
        self._fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        self._fh.flush()

    def close(self) -> None:
        try:
            self._fh.close()
        except OSError:
            pass


def sanitize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Copy an event, redacting credential-like keys. Keep full text/deltas."""
    cleaned = _sanitize_value(event)
    return cleaned if isinstance(cleaned, dict) else {"type": "opaque"}


def public_inbound(message: dict[str, Any]) -> dict[str, Any]:
    """Inbound bridge command, without unknown blob fields."""
    out: dict[str, Any] = {}
    for key in _INBOUND_KEEP:
        if key in message:
            out[key] = message[key]
    return sanitize_event(out)


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, inner in value.items():
            if _SECRET_KEY.search(str(key)):
                out[str(key)] = "***"
            else:
                out[str(key)] = _sanitize_value(inner)
        return out
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def latest_transcript(workspace: Workspace) -> Path | None:
    folder = workspace.root / TRANSCRIPT_DIR
    if not folder.is_dir():
        return None
    files = sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None
