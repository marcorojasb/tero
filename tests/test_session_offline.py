from __future__ import annotations

import pytest

from tero.config import Settings
from tero.errors import TeroError
from tero.session import TeacherSession
from tero.types import Encargo
from tero.workspace import Workspace


def test_offline_strands_loop_plan_draft_accept(workspace: Workspace):
    settings = Settings(offline=True, carpeta=workspace.root)
    encargo = Encargo(
        curso="4° básico",
        asignatura="Lenguaje",
        oa="OA 4",
        duracion="45 min",
        tipo=None,
    )
    events: list[dict] = []
    session = TeacherSession(workspace, settings, encargo=encargo, emit=events.append)
    session.start_turn("Prepara una planificación sobre el cuento.")
    assert session.phase in {"esperando_plan", "esperando_clarificacion"}
    while session.phase == "esperando_clarificacion":
        session.answer_plan_question(option_id="1")
    assert session.phase == "esperando_plan"
    assert session.turns[-1].plan is not None
    session.decide_plan("approve")
    assert session.phase == "esperando_criterio"
    draft = session.turns[-1].draft
    assert draft is not None
    assert len(draft.evidencias) >= 2
    assert all(item.verified for item in draft.evidencias)
    assert "Objetivo" in draft.cuerpo_markdown or "objetivo" in draft.cuerpo_markdown.lower()
    result = session.decide_gate("s")
    assert result.path is not None
    assert result.path.exists()
    text = result.path.read_text(encoding="utf-8")
    assert "generado_por: tero" in text
    assert "Evidencia" in text
    tools = [event.get("tool") for event in events if event.get("type") == "activity"]
    assert "list_sources" in tools
    assert "read_source" in tools
    assert "plan" in tools
    assert "draft" in tools


def test_gate_c_runs_another_pass(workspace: Workspace):
    settings = Settings(offline=True, carpeta=workspace.root)
    session = TeacherSession(
        workspace,
        settings,
        encargo=Encargo(oa="OA 4", tipo=None),
        emit=lambda _e: None,
    )
    session.start_turn("planificación del cuento")
    while session.phase == "esperando_clarificacion":
        session.answer_plan_question(option_id="1")
    session.decide_plan("approve")
    first = session.turns[-1].draft
    assert first is not None
    session.decide_gate("c", "Quita adorno y cita más el cuento.")
    second = session.turns[-1].draft
    assert second is not None
    assert "Corrección docente" in second.cuerpo_markdown


def test_hola_does_not_launch_plan(workspace: Workspace):
    settings = Settings(offline=True, carpeta=workspace.root)
    events: list[dict] = []
    session = TeacherSession(workspace, settings, emit=events.append)
    with pytest.raises(TeroError) as caught:
        session.start_turn("hola")
    assert caught.value.code == "no_encargo"
    assert session.phase == "idle"
    assert session.turns == []
    assert not any(event.get("type") == "plan" for event in events)


def test_hola_profe_is_still_phatic(workspace: Workspace):
    settings = Settings(offline=True, carpeta=workspace.root)
    session = TeacherSession(workspace, settings)
    with pytest.raises(TeroError) as caught:
        session.start_turn("hola profe")
    assert caught.value.code == "no_encargo"


def test_guia_short_encargo_still_starts(workspace: Workspace):
    settings = Settings(offline=True, carpeta=workspace.root)
    session = TeacherSession(workspace, settings, encargo=Encargo(oa="OA 4"))
    session.start_turn("guía del cuento")
    assert session.phase in {"esperando_plan", "esperando_clarificacion", "error"}
    assert session.turns
