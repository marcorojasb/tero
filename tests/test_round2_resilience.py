from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

from tero.bridge import Bridge
from tero.config import Settings
from tero.session import TeacherSession
from tero.types import Encargo
from tero.workspace import Workspace


def test_encargo_update_clears_stale_proposal(workspace: Workspace):
    events: list[dict] = []
    settings = Settings(offline=True, carpeta=workspace.root)
    session = TeacherSession(
        workspace,
        settings,
        encargo=Encargo(curso="4° básico", asignatura="Lenguaje", oa="OA 4"),
        emit=events.append,
    )
    session.start_turn("planificación del cuento")
    while session.phase == "esperando_clarificacion":
        session.answer_plan_question(option_id="1")
    session.decide_plan("approve")
    assert session.phase == "esperando_criterio"
    assert session.turns[-1].draft is not None

    stdin = io.StringIO(
        json.dumps(
            {
                "type": "encargo.update",
                "encargo": {
                    "curso": "6° básico",
                    "asignatura": "Matemática",
                    "oa": "OA 4",
                    "tipo": "guia",
                },
            }
        )
        + "\n"
        + json.dumps({"type": "shutdown"})
        + "\n"
    )
    stdout = io.StringIO()
    bridge = Bridge(settings, stdin=stdin, stdout=stdout, auto_yes=False)
    # reuse the live session with a pending draft
    bridge.session = session
    bridge.workspace = workspace
    bridge.serve()
    out = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    types = [e["type"] for e in out]
    assert "proposal_cleared" in types
    assert session.turns[-1].draft is None


def test_export_after_draft_includes_source_kind(workspace: Workspace, tmp_path: Path):
    settings = Settings(offline=True, carpeta=workspace.root)
    session = TeacherSession(
        workspace,
        settings,
        encargo=Encargo(oa="OA 4"),
        emit=lambda _e: None,
    )
    session.start_turn("planificación del cuento")
    while session.phase == "esperando_clarificacion":
        session.answer_plan_question(option_id="1")
    session.decide_plan("approve")
    session.decide_gate("b")
    assert session.exportable_path() is not None

    stdin = io.StringIO(
        json.dumps({"type": "export", "format": "md"})
        + "\n"
        + json.dumps({"type": "shutdown"})
        + "\n"
    )
    stdout = io.StringIO()
    bridge = Bridge(settings, stdin=stdin, stdout=stdout)
    bridge.session = session
    bridge.workspace = workspace
    assert bridge.serve() == 0
    events = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    exported = next(e for e in events if e["type"] == "exported")
    assert exported["source_kind"] == "borrador"
    assert Path(exported["path"]).exists()


def test_empty_draft_retries_once(workspace: Workspace):
    """If the model skips draft_artifact, session retries once before error."""
    settings = Settings(offline=True, carpeta=workspace.root)
    events: list[dict] = []
    session = TeacherSession(
        workspace,
        settings,
        encargo=Encargo(oa="OA 4"),
        emit=events.append,
    )
    session.start_turn("planificación del cuento")
    while session.phase == "esperando_clarificacion":
        session.answer_plan_question(option_id="1")

    calls = {"n": 0}
    real_agent_for = session._agent_for

    class FlakyDraft:
        def __init__(self, real):
            self._real = real

        def __call__(self, prompt: str, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                session.ctx.pending_draft = None
                return "ok (sin tool)"
            return self._real(prompt, **kwargs)

    def agent_for(phase: str):
        agent = real_agent_for(phase)
        if phase == "draft":
            return FlakyDraft(agent)
        return agent

    with patch.object(session, "_agent_for", side_effect=agent_for):
        session.decide_plan("approve")

    assert calls["n"] == 2
    assert session.phase == "esperando_criterio"
    assert session.turns[-1].draft is not None
    details = [
        e.get("detail")
        for e in events
        if e.get("type") == "status" and e.get("phase") == "escribiendo"
    ]
    assert any(d and "reintento" in str(d) for d in details)
