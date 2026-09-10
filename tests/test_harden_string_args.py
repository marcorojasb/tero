"""Regression: Nova Lite list-shaped tool args + full plan.as_dict() on plan.decide."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

from tero.bridge import Bridge, _flat_plan_edits
from tero.coerce import as_text
from tero.config import Settings
from tero.errors import humanize_exception
from tero.evidence import snippet_in_text
from tero.plan import apply_plan_edits, build_plan
from tero.session import TeacherSession, _is_retryable_stream_error
from tero.tools import TurnContext, build_tools
from tero.types import ArtifactType, Encargo
from tero.workspace import Workspace


def test_as_text_joins_lists():
    assert as_text(["a", "b"]) == "a\nb"
    assert as_text(["a", "b"], joiner=" ") == "a b"
    assert as_text(None) == ""
    assert as_text("ya") == "ya"


def test_artifact_type_parse_accepts_list():
    assert ArtifactType.parse(["planificacion"]) is ArtifactType.PLANIFICACION
    assert ArtifactType.parse(["guía"]) is ArtifactType.GUIA


def test_build_plan_and_snippet_accept_list_shaped_args():
    plan = build_plan(
        objetivo=["Extraer info", "del cuento"],
        tipo=["planificacion"],
        oa=["OA", "4"],
        titulo=["Plan", "lectura"],
        encargo=Encargo(curso="4° básico"),
    )
    assert "Extraer info" in plan.objetivo
    assert plan.tipo is ArtifactType.PLANIFICACION
    assert plan.oa == "OA 4"
    assert snippet_in_text("hola mundo largo", ["hola", "mundo"])


def test_apply_plan_edits_with_full_as_dict_is_noop():
    plan = build_plan(
        objetivo="Leer con evidencia",
        tipo="planificación",
        oa="OA 4",
        encargo=Encargo(oa="OA 4"),
    )
    payload = plan.as_dict()
    assert isinstance(payload["supuestos"], list)
    assert isinstance(payload["decisiones"], dict)
    same = apply_plan_edits(plan, payload)  # type: ignore[arg-type]
    assert same is plan
    assert same.objetivo == plan.objetivo


def test_flat_plan_edits_rejects_full_plan_keeps_patches():
    plan = build_plan(objetivo="x", tipo="guia")
    assert _flat_plan_edits(plan.as_dict()) is None
    assert _flat_plan_edits({"oa": "OA 6", "duracion": "90 min"}) == {
        "oa": "OA 6",
        "duracion": "90 min",
    }


def test_bridge_plan_decide_with_full_plan_dict(workspace: Workspace):
    settings = Settings(offline=True, carpeta=workspace.root)
    session = TeacherSession(
        workspace,
        settings,
        encargo=Encargo(oa="OA 4", tipo=ArtifactType.PLANIFICACION),
        emit=lambda _e: None,
    )
    session.start_turn("planificación del cuento")
    while session.phase == "esperando_clarificacion":
        session.answer_plan_question(option_id="1")
    assert session.phase == "esperando_plan"
    assert session.turns[-1].plan is not None
    full = session.turns[-1].plan.as_dict()

    stdin = io.StringIO(
        json.dumps({"type": "plan.decide", "decision": "approve", "plan": full})
        + "\n"
        + json.dumps({"type": "shutdown"})
        + "\n"
    )
    stdout = io.StringIO()
    bridge = Bridge(settings, stdin=stdin, stdout=stdout, auto_yes=False)
    bridge.session = session
    bridge.workspace = workspace
    assert bridge.serve() == 0
    out = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    errors = [e for e in out if e.get("type") == "error"]
    assert not any("strip" in str(e.get("message", "")).lower() for e in errors)
    assert session.phase == "esperando_criterio"
    assert session.turns[-1].draft is not None


def test_draft_artifact_accepts_list_titulo(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {t.tool_name: t for t in build_tools(ctx, phase="draft")}
    draft = tools["draft_artifact"]
    result = json.loads(
        draft(
            tipo=["actividad"],
            titulo=["Preguntar", "como el huemul"],
            cuerpo_markdown=[
                "# Actividad",
                "## Objetivo",
                "x",
                "## Materiales",
                "y",
                "## Pasos",
                "z",
            ],
        )
    )
    assert result["ok"] is True
    assert ctx.pending_draft is not None
    assert "Preguntar" in ctx.pending_draft.titulo
    assert ctx.pending_draft.tipo is ArtifactType.ACTIVIDAD


def test_stream_tooluse_error_retries_once(workspace: Workspace):
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

    class FlakyStream:
        def __init__(self, real):
            self._real = real

        def __call__(self, prompt: str):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("modelStreamErrorException: invalid ToolUse sequence")
            return self._real(prompt)

    def agent_for(phase: str):
        agent = real_agent_for(phase)
        if phase == "draft":
            return FlakyStream(agent)
        return agent

    with patch.object(session, "_agent_for", side_effect=agent_for):
        session.decide_plan("approve")

    assert calls["n"] == 2
    assert session.phase == "esperando_criterio"
    assert session.turns[-1].draft is not None
    assert any(e.get("step") == "draft_stream_retry" for e in events if e.get("type") == "status")


def test_humanize_stream_tooluse():
    assert _is_retryable_stream_error(RuntimeError("modelStreamErrorException ToolUse"))
    assert _is_retryable_stream_error(RuntimeError("EventStreamError | event loop cycle failed"))
    code, message = humanize_exception(RuntimeError("modelStreamErrorException: bad ToolUse"))
    assert code == "bedrock_stream"
    assert "reintenta" in message.lower() or "retry" in message.lower()
