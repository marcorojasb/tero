from __future__ import annotations

import io
import json
from pathlib import Path

from tero.bridge import Bridge
from tero.config import Settings
from tero.protocol import decode, encode


def test_protocol_roundtrip():
    line = encode({"type": "prompt", "text": "hola"})
    data = decode(line)
    assert data["type"] == "prompt"
    assert data["v"] == 1


def test_bridge_jsonl_offline_yes(demo_carpeta: Path):
    settings = Settings(offline=True, carpeta=demo_carpeta)
    stdin = io.StringIO(
        json.dumps({"type": "hello", "encargo": {"oa": "OA 4", "tipo": "planificacion"}})
        + "\n"
        + json.dumps({"type": "prompt", "text": "Prepara la planificación del cuento."})
        + "\n"
        + json.dumps({"type": "shutdown"})
        + "\n"
    )
    stdout = io.StringIO()
    bridge = Bridge(settings, stdin=stdin, stdout=stdout, auto_yes=True)
    assert bridge.serve() == 0
    events = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    types = [event["type"] for event in events]
    assert "ready" in types
    assert "plan" in types
    assert "proposal" in types
    assert "accepted" in types
    accepted = next(event for event in events if event["type"] == "accepted")
    assert accepted["path"].endswith(".md")
