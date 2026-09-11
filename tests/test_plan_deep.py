from __future__ import annotations

from tero.config import Settings
from tero.errors import humanize_exception
from tero.session import TeacherSession
from tero.types import Encargo
from tero.workspace import Workspace


def test_offline_answers_clarification_then_draft(workspace: Workspace):
    settings = Settings(offline=True, carpeta=workspace.root)
    session = TeacherSession(
        workspace,
        settings,
        encargo=Encargo(oa="OA 4", tipo=None),
        emit=lambda _e: None,
    )
    session.start_turn("Prepara una planificación sobre el cuento.")
    assert session.phase == "esperando_clarificacion"
    pending = session.turns[-1].plan.pending_question()
    assert pending is not None
    session.answer_plan_question(option_id="1")
    assert session.phase == "esperando_plan"
    session.decide_plan("approve")
    assert session.phase == "esperando_criterio"


def test_plan_cancel_clears_to_idle(workspace: Workspace):
    events: list[dict] = []
    session = TeacherSession(
        workspace,
        Settings(offline=True, carpeta=workspace.root),
        encargo=Encargo(oa="OA 4"),
        emit=events.append,
    )
    session.start_turn("planificación del cuento")
    while session.phase == "esperando_clarificacion":
        session.answer_plan_question(option_id="1")
    session.decide_plan("cancel")
    assert session.phase == "idle"
    types = [e.get("type") for e in events]
    assert "plan_cancelled" in types
    assert "proposal_cleared" in types


def test_critique_persisted(workspace: Workspace):
    session = TeacherSession(
        workspace,
        Settings(offline=True, carpeta=workspace.root),
        encargo=Encargo(oa="OA 4"),
        emit=lambda _e: None,
    )
    session.start_turn("planificación del cuento")
    while session.phase == "esperando_clarificacion":
        session.answer_plan_question(option_id="1")
    session.decide_plan("approve")
    session.decide_gate("c", "Más citas del cuento, menos adorno.")
    crit_dir = workspace.root / ".tero" / "criticas"
    assert crit_dir.exists()
    assert list(crit_dir.glob("*.md"))
    assert session.turns[-1].critique_notes


def test_export_after_draft_b(workspace: Workspace):
    from tero.export import export_markdown

    session = TeacherSession(
        workspace,
        Settings(offline=True, carpeta=workspace.root),
        encargo=Encargo(oa="OA 4"),
        emit=lambda _e: None,
    )
    session.start_turn("planificación del cuento")
    while session.phase == "esperando_clarificacion":
        session.answer_plan_question(option_id="1")
    session.decide_plan("approve")
    result = session.decide_gate("b")
    assert result.path is not None
    path = session.exportable_path()
    assert path is not None
    out = export_markdown(path, workspace.root / "borradores" / "export-test.md")
    assert out.exists()


def test_humanize_bedrock_auth():
    class Fake(Exception):
        pass

    code, msg = humanize_exception(Fake("UnrecognizedClientException: credentials"))
    assert code == "bedrock_auth"
    assert "credenciales" in msg.lower()


def test_humanize_bedrock_model_and_throttle():
    class Fake(Exception):
        pass

    code, msg = humanize_exception(
        Fake(
            "AccessDeniedException: You don't have access to the model with the specified model ID."
        )
    )
    assert code == "bedrock_model"
    assert "Nova Lite" in msg or "TERO_MODEL" in msg
    assert "Model access habilita" not in msg
    assert "primer invoke" in msg or "invocarlo" in msg

    code, msg = humanize_exception(Fake("ThrottlingException: Rate exceeded"))
    assert code == "bedrock_throttle"

    # IAM invoke denial must stay auth, not model (InvokeModel contains "model")
    code, msg = humanize_exception(
        Fake("AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel")
    )
    assert code == "bedrock_auth"


def test_settings_accepts_tero_model_id(monkeypatch):
    monkeypatch.setenv("TERO_MODEL_ID", "amazon.nova-micro-v1:0")
    monkeypatch.delenv("TERO_MODEL", raising=False)
    settings = Settings.from_env(offline=True)
    assert settings.model_id == "amazon.nova-micro-v1:0"
