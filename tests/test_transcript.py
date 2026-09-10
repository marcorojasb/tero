"""Session JSONL transcripts live in the carpeta (.tero/transcripciones/)."""

from __future__ import annotations

import json

from tero.config import Settings
from tero.session import TeacherSession
from tero.transcript import TRANSCRIPT_DIR, latest_transcript, sanitize_event
from tero.types import Encargo
from tero.workspace import Workspace


def test_offline_session_writes_full_transcript(workspace: Workspace):
    settings = Settings(offline=True, carpeta=workspace.root)
    events: list[dict] = []
    session = TeacherSession(
        workspace,
        settings,
        encargo=Encargo(oa="OA 4", tipo=None),
        emit=events.append,
    )
    session.start_turn("Prepara una planificación sobre el cuento.")
    while session.phase == "esperando_clarificacion":
        session.answer_plan_question(option_id="1")
    session.decide_plan("approve")
    session.decide_gate("s")

    path = session.transcript.path
    assert path.is_file()
    assert TRANSCRIPT_DIR in path.as_posix()
    lines = [
        json.loads(row) for row in path.read_text(encoding="utf-8").splitlines() if row.strip()
    ]
    types = [row.get("type") for row in lines]
    assert "session_start" in types
    assert "host_action" in types
    assert "plan" in types
    assert "proposal" in types
    assert "accepted" in types
    start = next(row for row in lines if row.get("type") == "session_start")
    assert start["model"] == "tero-offline"
    assert start["offline"] is True
    prompts = [
        row.get("prompt")
        for row in lines
        if row.get("type") == "host_action" and row.get("action") == "start_turn"
    ]
    assert any("cuento" in str(p).lower() for p in prompts)
    # TUI still receives the live events (minus transcript-only host_action/session_start)
    assert any(event.get("type") == "proposal" for event in events)
    assert latest_transcript(workspace) == path


def test_sanitize_redacts_credential_keys():
    cleaned = sanitize_event(
        {
            "type": "debug",
            "aws_secret_access_key": "should-not-leak",
            "nested": {"Authorization": "Bearer xyz", "text": "ok"},
        }
    )
    assert cleaned["aws_secret_access_key"] == "***"
    assert cleaned["nested"]["Authorization"] == "***"
    assert cleaned["nested"]["text"] == "ok"
