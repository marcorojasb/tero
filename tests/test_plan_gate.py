from __future__ import annotations

from tero.config import Settings
from tero.gate import apply_gate
from tero.plan import apply_plan_edits, build_plan
from tero.session import TeacherSession
from tero.types import ArtifactDraft, ArtifactType, Encargo
from tero.workspace import Workspace


def test_plan_typed_and_editable():
    plan = build_plan(
        objetivo="Leer con evidencia",
        tipo="planificación",
        oa="OA 4",
        duracion="45 min",
        encargo=Encargo(oa="OA 6"),
    )
    assert plan.tipo is ArtifactType.PLANIFICACION
    assert plan.oa == "OA 4"
    edited = apply_plan_edits(plan, {"oa": "OA 6", "duracion": "90 min"})
    assert edited.oa == "OA 6"
    assert edited.duracion == "90 min"


def test_gate_s_writes_derivados_n_does_not(workspace: Workspace):
    encargo = Encargo(curso="4°", oa="OA 4")
    draft = ArtifactDraft(
        tipo=ArtifactType.ACTIVIDAD,
        titulo="Preguntar como el huemul",
        cuerpo_markdown="# Actividad\n\n## Objetivo\n...\n## Materiales\n...\n## Pasos\n...",
    )
    accepted = apply_gate(
        workspace=workspace, encargo=encargo, plan=None, draft=draft, decision="s"
    )
    assert accepted.path is not None
    assert "derivados" in accepted.path.parts
    discarded = apply_gate(
        workspace=workspace, encargo=encargo, plan=None, draft=draft, decision="n"
    )
    assert discarded.path is None
    drafted = apply_gate(workspace=workspace, encargo=encargo, plan=None, draft=draft, decision="b")
    assert drafted.path is not None
    assert "borradores" in drafted.path.parts


def test_repeat_accept_does_not_collide(workspace: Workspace):
    encargo = Encargo(curso="4°", oa="OA 4")
    draft = ArtifactDraft(
        tipo=ArtifactType.ACTIVIDAD,
        titulo="Misma hora",
        cuerpo_markdown="# Actividad\n\n## Objetivo\n...\n## Materiales\n...\n## Pasos\n...",
    )
    first = apply_gate(workspace=workspace, encargo=encargo, plan=None, draft=draft, decision="s")
    second = apply_gate(workspace=workspace, encargo=encargo, plan=None, draft=draft, decision="s")
    assert first.path is not None and second.path is not None
    assert first.path != second.path
    assert first.path.exists() and second.path.exists()


def test_approve_plan_applies_host_edits(workspace: Workspace):
    session = TeacherSession(
        workspace,
        Settings(offline=True, carpeta=workspace.root),
        encargo=Encargo(oa="OA 4", tipo=None),
    )
    session.start_turn("planificación del cuento")
    assert session.turns[-1].plan is not None
    session.decide_plan("approve", {"oa": "OA 6", "duracion": "90 min"})
    assert session.turns[-1].plan is not None
    assert session.turns[-1].plan.oa == "OA 6"
    assert session.turns[-1].plan.duracion == "90 min"
