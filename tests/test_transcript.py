"""Transcripción de la sesión: JSONL en la carpeta (.tero/transcripciones/)."""

from __future__ import annotations

import json

from tero.transcript import TRANSCRIPT_DIR, latest_transcript, sanitize_event
from tero.workspace import Workspace
from tests.support import PEDIDO_GUIA, PEDIDO_PREGUNTA, open_session


def test_el_turno_completo_queda_en_la_transcripcion(workspace: Workspace):
    events: list[dict] = []
    session = open_session(workspace, events=events)
    session.start_turn(PEDIDO_GUIA)
    session.start_turn(PEDIDO_PREGUNTA)
    session.aprobar("dale")

    path = session.transcript.path
    assert path.is_file()
    assert TRANSCRIPT_DIR in path.as_posix()
    rows = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines() if row.strip()]
    tipos = [row.get("type") for row in rows]

    assert "session_start" in tipos
    assert "host_action" in tipos
    assert "propuesta" in tipos
    assert "respuesta" in tipos
    assert "aprobacion" in tipos
    assert "escrito" in tipos

    start = next(row for row in rows if row.get("type") == "session_start")
    assert start["model"] == "tero-offline"
    assert start["offline"] is True

    acciones = [row.get("action") for row in rows if row.get("type") == "host_action"]
    assert "start_turn" in acciones
    assert "aprobar" in acciones
    prompts = [
        row.get("prompt")
        for row in rows
        if row.get("type") == "host_action" and row.get("action") == "start_turn"
    ]
    assert any("cuento" in str(prompt).lower() for prompt in prompts)

    propuesta = next(row for row in rows if row.get("type") == "propuesta")
    assert propuesta["propuesta"]["accion"] == "crear"
    assert propuesta["propuesta"]["vista_previa"].strip()

    escrito = next(row for row in rows if row.get("type") == "escrito")
    assert str(escrito["path"]).endswith(".md")

    # La TUI recibe los eventos en vivo (menos los que son solo de transcripción).
    assert any(event.get("type") == "propuesta" for event in events)
    assert any(event.get("type") == "respuesta" for event in events)
    assert latest_transcript(workspace) == path


def test_cada_sesion_escribe_su_propio_jsonl(workspace: Workspace):
    primera = open_session(workspace)
    primera.start_turn(PEDIDO_GUIA)
    segunda = open_session(workspace)
    segunda.start_turn(PEDIDO_GUIA)

    assert primera.transcript.path != segunda.transcript.path
    assert primera.transcript.path.is_file()
    assert segunda.transcript.path.is_file()


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
