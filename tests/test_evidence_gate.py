"""Gate evidence policy + stream retry token coverage."""

from __future__ import annotations

import pytest

from tero.config import Settings
from tero.errors import TeroError
from tero.evidence import accept_blockers, collect_warnings
from tero.session import TeacherSession, _is_retryable_stream_error
from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence, WarningItem
from tero.workspace import Workspace


def test_eventstreamerror_is_retryable():
    assert _is_retryable_stream_error(RuntimeError("EventStreamError | event loop cycle failed"))

    class EventStreamError(Exception):
        pass

    assert _is_retryable_stream_error(EventStreamError("boom"))


def test_accept_blockers_thin_and_unknown(workspace: Workspace):
    draft = ArtifactDraft(
        tipo=ArtifactType.PLANIFICACION,
        titulo="Sin citas",
        cuerpo_markdown="# Plan\n\n## Objetivo\n…\n",
        evidencias=[],
        warnings=[],
    )
    draft.warnings = collect_warnings(
        workspace=workspace,
        encargo=Encargo(oa="OA 4"),
        plan=None,
        draft=draft,
        prompt="planifica",
    )
    blockers = accept_blockers(draft)
    assert any(w.code == "thin_evidence" for w in blockers)
    assert all(w.blocking for w in blockers if w.code == "thin_evidence")


def test_decide_gate_s_blocks_thin_evidence(workspace: Workspace):
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
    # Force a thin/unknown draft at the gate.
    turn = session.turns[-1]
    assert turn.draft is not None
    turn.draft.evidencias = [
        Evidence(path="OA 4 (LEN-4B-OA04)", snippet="falso", seccion="", verified=False)
    ]
    turn.draft.warnings = [
        WarningItem(code="thin_evidence", message="pobre", blocking=True),
        WarningItem(code="unknown_source", message="ruta falsa", blocking=True),
    ]
    with pytest.raises(TeroError) as exc:
        session.decide_gate("s")
    assert exc.value.code == "evidence_blocked"
    assert session.phase == "esperando_criterio"
    # Explicit override still writes.
    result = session.decide_gate("s", "forzar evidencia delgada para prueba")
    assert result.path is not None
    assert "derivados" in result.path.parts


def test_decide_gate_b_allows_thin(workspace: Workspace):
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
    turn = session.turns[-1]
    assert turn.draft is not None
    turn.draft.warnings = [WarningItem(code="thin_evidence", message="pobre", blocking=True)]
    result = session.decide_gate("b")
    assert result.path is not None
    assert "borradores" in result.path.parts
