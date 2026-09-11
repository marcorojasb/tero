"""Resiliencia del host: reintentos, errores traducidos y estado que no se pierde."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

from tero import session as session_module
from tero.bridge import Bridge
from tero.config import Settings
from tero.errors import TeroError, humanize_exception
from tero.session import _is_retryable_stream_error
from tero.tools import DRAFT_TOOL_BUDGET
from tests.fake_models import BoomModel, ToolModel
from tests.support import PEDIDO_GUIA, artifact_paths, open_session


def test_un_error_de_stream_reintenta_una_vez_y_termina_bien(workspace):
    session = open_session(workspace)
    events: list[dict] = []
    session._downstream = events.append
    calls = {"n": 0}
    real_agent_for = session._agent_for

    class FlakyStream:
        def __init__(self, real):
            self._real = real

        def __call__(self, prompt: str, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("modelStreamErrorException: invalid ToolUse sequence")
            return self._real(prompt, **kwargs)

    def agent_for():
        return FlakyStream(real_agent_for())

    with patch.object(session, "_agent_for", side_effect=agent_for):
        turn = session.start_turn(PEDIDO_GUIA)

    assert calls["n"] == 2
    assert session.phase == "esperando_aprobacion"
    assert turn.propuesta is not None
    assert any(
        event.get("step") == "stream_retry" for event in events if event.get("type") == "status"
    )
    assert artifact_paths(workspace) == []


def test_un_error_irrecuperable_deja_la_fase_en_error_sin_escribir(workspace):
    session = open_session(workspace)
    events: list[dict] = []
    session._downstream = events.append
    with patch("tero.session.make_model", return_value=BoomModel()):
        turn = session.start_turn(PEDIDO_GUIA)

    assert session.phase == "error"
    assert turn.respuesta == ""
    assert turn.propuesta is None
    error = next(event for event in events if event["type"] == "error")
    assert error["code"]
    assert error["message"]
    assert artifact_paths(workspace) == []


def test_si_falla_la_revision_la_propuesta_anterior_sigue_viva(workspace):
    session = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    anterior = session.pending_propuesta
    assert anterior is not None

    with patch("tero.session.make_model", return_value=BoomModel()):
        session.pedir_cambio("Hazla más corta, por favor.")

    assert session.pending_propuesta is anterior
    assert session.phase == "error"

    resultado = session.aprobar("la de antes estaba bien")
    assert resultado.path is not None
    assert resultado.path.exists()


def test_el_presupuesto_agotado_avisa_pero_deja_aprobar(workspace):
    session = open_session(workspace)
    events: list[dict] = []
    session._downstream = events.append
    model = ToolModel(
        "proponer_crear",
        {
            "tipo": "guia",
            "titulo": "Guía al límite",
            "resumen": "Sin presupuesto.",
            "vista_previa_markdown": (
                "# Guía\n\n## Propósito\nLeer.\n\n## Instrucciones\nSigue.\n\n"
                "## Actividades\nUna.\n\n## Cierre\nTicket.\n"
            ),
        },
    )
    with (
        patch("tero.session.make_model", return_value=model),
        patch.object(session_module, "DRAFT_TOOL_BUDGET", 0),
    ):
        session.start_turn(PEDIDO_GUIA)

    assert session.phase == "esperando_aprobacion"
    assert session.pending_propuesta is not None
    codigos = [event["warning"]["code"] for event in events if event["type"] == "warning"]
    assert "tool_budget_exhausted" in codigos
    resultado = session.aprobar()
    assert resultado.path is not None


def test_encargo_update_conserva_la_propuesta_pendiente(workspace):
    session = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    propuesta = session.pending_propuesta
    assert propuesta is not None

    stdin = io.StringIO(
        json.dumps(
            {
                "type": "encargo.update",
                "encargo": {"curso": "6° básico", "asignatura": "Matemática"},
            }
        )
        + "\n"
        + json.dumps({"type": "shutdown"})
        + "\n"
    )
    stdout = io.StringIO()
    bridge = Bridge(Settings(offline=True, carpeta=workspace.root), stdin=stdin, stdout=stdout)
    bridge.session = session
    bridge.workspace = workspace
    assert bridge.serve() == 0

    events = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    avisos = [event["warning"]["code"] for event in events if event["type"] == "warning"]
    assert "encargo_changed" in avisos
    assert session.pending_propuesta is propuesta
    assert session.encargo.curso == "6° básico"
    assert artifact_paths(workspace) == []


def test_pedir_cambio_sin_propuesta_pendiente_levanta_error(workspace):
    session = open_session(workspace)
    with pytest.raises(TeroError) as caught:
        session.pedir_cambio("cámbiala")
    assert caught.value.code == "no_propuesta"


def test_retry_repite_el_ultimo_mensaje(workspace):
    session = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    turn = session.retry_last()
    assert turn is not None
    assert turn.prompt == PEDIDO_GUIA
    assert session.phase == "esperando_aprobacion"


def test_retry_sin_mensaje_previo_levanta_error(workspace):
    session = open_session(workspace)
    with pytest.raises(TeroError) as caught:
        session.retry_last()
    assert caught.value.code == "no_retry"


def test_los_errores_de_bedrock_se_traducen_a_espanol():
    assert _is_retryable_stream_error(RuntimeError("modelStreamErrorException ToolUse"))
    assert not _is_retryable_stream_error(RuntimeError("todo bien"))

    code, message = humanize_exception(RuntimeError("modelStreamErrorException: bad ToolUse"))
    assert code == "bedrock_stream"
    assert "reintenta" in message.lower() or "retry" in message.lower()

    class Fake(Exception):
        pass

    code, message = humanize_exception(Fake("ThrottlingException: Rate exceeded"))
    assert code == "bedrock_throttle"
    assert "reintenta" in message.lower()

    code, _ = humanize_exception(
        Fake("AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel")
    )
    assert code == "bedrock_auth"

    code, message = humanize_exception(
        Fake("AccessDeniedException: You don't have access to the model with the specified id.")
    )
    assert code == "bedrock_model"
    assert "TERO_MODEL" in message

    code, _ = humanize_exception(RuntimeError("boom de prueba"))
    assert code == "host_error"


def test_el_presupuesto_por_defecto_sigue_siendo_el_del_guion():
    assert DRAFT_TOOL_BUDGET >= 4
