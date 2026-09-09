"""JSONL protocol between the Python Strands host and the OpenTUI client."""

from __future__ import annotations

import json
from typing import Any

from tero import PROTOCOL_VERSION
from tero.errors import ProtocolError

ALLOWED_IN = {
    "hello",
    "prompt",
    "encargo.update",
    "plan.decide",
    "gate",
    "export",
    "shutdown",
}


def encode(event: dict[str, Any]) -> str:
    payload = {"v": PROTOCOL_VERSION, **event}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def decode(line: str) -> dict[str, Any]:
    raw = line.strip()
    if not raw:
        raise ProtocolError("línea vacía")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"JSON inválido: {exc}") from exc
    if not isinstance(data, dict):
        raise ProtocolError("cada línea debe ser un objeto")
    kind = data.get("type")
    if kind not in ALLOWED_IN:
        raise ProtocolError(f"tipo no permitido: {kind}")
    return data
