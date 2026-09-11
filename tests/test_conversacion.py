"""Intenciones del agente conversacional: a) responder, b) crear, c) editar/adaptar.

Todo corre con el modelo scripted `tero-offline`: sin red ni AWS. El host es el
único que escribe, y solo después de `aprobar()`.
"""

from __future__ import annotations

import pytest

from tero.session import TeacherSession
from tero.types import ArtifactType, Encargo
from tero.workspace import Workspace
from tests.support import (
    PEDIDO_GUIA,
    PEDIDO_PLANIFICACION,
    PEDIDO_PREGUNTA,
    artifact_paths,
    crear_y_aprobar,
    open_session,
    rel,
)


def test_intencion_a_pregunta_responde_y_no_escribe_nada(workspace: Workspace):
    events: list[dict] = []
    session = open_session(workspace, events=events)
    turn = session.start_turn("Hola, ¿qué puedes hacer por mí?")

    assert session.phase == "idle"
    assert turn.phase == "idle"
    assert turn.respuesta.strip()
    assert turn.propuesta is None
    assert session.pending_propuesta is None
    assert artifact_paths(workspace) == []
    tipos = [event["type"] for event in events]
    assert "respuesta" in tipos
    assert "propuesta" not in tipos


def test_intencion_a_con_contexto_cargado_el_contexto_no_secuestra_la_intencion(
    workspace: Workspace,
):
    """El encabezado "Contexto: …" no debe convertir una pregunta en un pedido."""
    encargo = Encargo(
        curso="4° básico",
        asignatura="Lenguaje y Comunicación",
        oa="LEN-4B-OA04",
        tipo=ArtifactType.PLANIFICACION,
    )
    session = open_session(workspace, encargo)
    turn = session.start_turn(PEDIDO_PREGUNTA)

    assert session.phase == "idle"
    assert turn.propuesta is None
    assert turn.respuesta.strip()
    assert artifact_paths(workspace) == []


def test_intencion_b_pedido_de_material_propone_y_no_escribe_hasta_aprobar(
    workspace: Workspace,
):
    events: list[dict] = []
    session = open_session(workspace, events=events)
    turn = session.start_turn(PEDIDO_PLANIFICACION)

    assert session.phase == "esperando_aprobacion"
    assert turn.propuesta is not None
    assert turn.propuesta.accion == "crear"
    assert turn.propuesta.origen == ""
    assert turn.propuesta.vista_previa.strip()
    assert turn.propuesta.tipo is ArtifactType.PLANIFICACION
    assert session.pending_propuesta is turn.propuesta
    assert artifact_paths(workspace) == []
    assert "propuesta" in [event["type"] for event in events]

    result = session.aprobar()
    assert result.path is not None
    assert result.path.parent.name == "derivados"
    assert result.path.exists()
    escrito = result.path.read_text(encoding="utf-8")
    assert "generado_por: tero" in escrito
    assert "accion: crear" in escrito
    assert session.phase == "listo"
    assert session.pending_propuesta is None


def test_intencion_c_editar_escribe_version_nueva_y_deja_el_origen_intacto(
    workspace: Workspace,
):
    origen = crear_y_aprobar(workspace)
    original = origen.read_text(encoding="utf-8")
    ruta = rel(workspace, origen)

    session = open_session(workspace)
    turn = session.start_turn(f"Edita {ruta} y acorta el inicio de la clase.")

    assert session.phase == "esperando_aprobacion"
    assert turn.propuesta is not None
    assert turn.propuesta.accion == "editar"
    assert turn.propuesta.origen == ruta
    assert (workspace.root / turn.propuesta.origen).is_file()
    assert artifact_paths(workspace) == [origen]

    result = session.aprobar()
    assert result.path is not None
    assert result.path != origen
    assert result.path.exists()
    assert origen.read_text(encoding="utf-8") == original

    escrito = result.path.read_text(encoding="utf-8")
    assert f"origen: {ruta}" in escrito
    assert "accion: editar" in escrito


def test_intencion_c_adaptar_para_nee_propone_con_origen_y_notas(workspace: Workspace):
    origen = crear_y_aprobar(workspace)
    original = origen.read_text(encoding="utf-8")
    ruta = rel(workspace, origen)

    session = open_session(workspace)
    turn = session.start_turn(f"Adapta {ruta} para NEE: apoyos visuales y más tiempo.")

    assert session.phase == "esperando_aprobacion"
    assert turn.propuesta is not None
    assert turn.propuesta.accion == "adaptar"
    assert turn.propuesta.origen == ruta
    assert turn.propuesta.notas_nee
    codigos = {item.code for item in turn.propuesta.draft.warnings}
    assert "paci_no_oficial" in codigos
    assert all(item.blocking is False for item in turn.propuesta.draft.warnings)

    result = session.aprobar()
    assert result.path is not None and result.path != origen
    assert origen.read_text(encoding="utf-8") == original
    escrito = result.path.read_text(encoding="utf-8")
    assert f"origen: {ruta}" in escrito
    assert "accion: adaptar" in escrito


def test_pregunta_con_propuesta_pendiente_responde_y_la_mantiene_viva(workspace: Workspace):
    """El caso que estaba roto: conversar no debe tirar la propuesta a la basura."""
    session = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    propuesta = session.pending_propuesta
    assert propuesta is not None

    turn = session.start_turn(PEDIDO_PREGUNTA)

    assert session.phase == "idle"
    assert turn.respuesta.strip()
    assert turn.propuesta is None
    assert session.pending_propuesta is propuesta
    assert artifact_paths(workspace) == []

    result = session.aprobar("dale")
    assert result.path is not None
    assert result.path.exists()
    assert result.path.read_text(encoding="utf-8").startswith("---")


def test_una_propuesta_nueva_reemplaza_a_la_anterior(workspace: Workspace):
    session = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    primera = session.pending_propuesta
    session.start_turn("Mejor prepara una evaluación corta del cuento.")
    segunda = session.pending_propuesta

    assert primera is not None and segunda is not None
    assert segunda is not primera
    assert artifact_paths(workspace) == []
    result = session.aprobar()
    assert result.path is not None
    assert len(artifact_paths(workspace)) == 1


def test_revision_de_una_creacion_conserva_la_accion_y_no_inventa_origen(workspace: Workspace):
    session = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    assert session.pending_propuesta is not None

    session.pedir_cambio("Hazla más corta y con menos adorno.")

    propuesta = session.pending_propuesta
    assert propuesta is not None
    assert propuesta.accion == "crear"
    assert propuesta.origen == ""
    assert session.phase == "esperando_aprobacion"
    assert artifact_paths(workspace) == []


def test_revision_de_una_edicion_mantiene_el_origen(workspace: Workspace):
    origen = crear_y_aprobar(workspace)
    ruta = rel(workspace, origen)
    session = open_session(workspace)
    session.start_turn(f"Edita {ruta} y acorta el inicio.")
    assert session.pending_propuesta is not None
    assert session.pending_propuesta.accion == "editar"

    session.pedir_cambio("Agrega tiempos por momento de clase.")

    propuesta = session.pending_propuesta
    assert propuesta is not None
    assert propuesta.accion == "editar"
    assert propuesta.origen == ruta


@pytest.mark.xfail(
    strict=False,
    reason=(
        "BUG host: `pedir_cambio` sobre una propuesta `adaptar` la convierte en `crear` "
        "sin origen. `offline._next_action` solo ramifica para intent == 'editar'; "
        "`_intent` sí devuelve 'adaptar', así que la revisión NEE pierde acción y origen."
    ),
)
def test_revision_de_una_adaptacion_conserva_la_accion(workspace: Workspace):
    origen = crear_y_aprobar(workspace)
    ruta = rel(workspace, origen)
    session = open_session(workspace)
    session.start_turn(f"Adapta {ruta} para NEE con apoyos visuales.")
    assert session.pending_propuesta is not None
    assert session.pending_propuesta.accion == "adaptar"

    session.pedir_cambio("Agrega apoyo visual a la secuencia.")

    propuesta = session.pending_propuesta
    assert propuesta is not None
    assert propuesta.accion == "adaptar"
    assert propuesta.origen == ruta


def test_prompt_vacio_levanta_error_sin_tocar_la_carpeta(workspace: Workspace):
    from tero.errors import TeroError

    session = open_session(workspace)
    with pytest.raises(TeroError) as caught:
        session.start_turn("   ")
    assert caught.value.code == "empty_prompt"
    assert session.turns == []
    assert artifact_paths(workspace) == []


def test_el_loop_offline_corre_las_tools_y_cita_evidencia_verificada(workspace: Workspace):
    """El agente offline es un Strands Model real: lee, cita y recién ahí propone."""
    events: list[dict] = []
    session = open_session(workspace, events=events)
    turn = session.start_turn(PEDIDO_PLANIFICACION)

    assert turn.propuesta is not None
    tools = [event.get("tool") for event in events if event.get("type") == "activity"]
    assert "list_sources" in tools
    assert "read_source" in tools
    assert "proponer_crear" in tools
    assert "proponer_editar" not in tools

    evidencias = turn.propuesta.draft.evidencias
    assert len(evidencias) >= 2
    assert all(item.verified for item in evidencias)
    assert all(item.path.startswith("fuentes/") for item in evidencias)


def test_callback_emits_one_activity_per_tool_use(workspace: Workspace):
    events: list[dict] = []
    session = open_session(workspace, events=events)
    session._callback(current_tool_use={"name": "proponer_crear", "toolUseId": "u1", "input": "{"})
    session._callback(
        current_tool_use={"name": "proponer_crear", "toolUseId": "u1", "input": '{"tipo"'}
    )
    session._callback(
        current_tool_use={"name": "proponer_crear", "toolUseId": "u1", "input": '{"tipo":"guia"}'}
    )
    session._callback(current_tool_use={"name": "cite_evidence", "toolUseId": "u2", "input": "{}"})
    activities = [row for row in events if row.get("type") == "activity"]
    assert [row["tool"] for row in activities] == ["proponer_crear", "cite_evidence"]
    assert all(row.get("state") == "start" for row in activities)


def test_delta_events_coalesce_before_flush(workspace: Workspace):
    events: list[dict] = []
    session = open_session(workspace, events=events)
    session._callback(data="aaaa")
    session._callback(data="bbbb")
    assert [row for row in events if row.get("type") == "delta"] == []
    session._callback(data="c" * 80)
    deltas = [row["text"] for row in events if row.get("type") == "delta"]
    assert len(deltas) == 1
    assert deltas[0] == "aaaa" + "bbbb" + ("c" * 80)
    events.clear()
    session._callback(data="hola\n")
    assert [row["text"] for row in events if row.get("type") == "delta"] == ["hola\n"]
    events.clear()
    session._callback(data="xyz")
    session._callback(current_tool_use={"name": "list_sources", "toolUseId": "t1", "input": "{}"})
    assert [row["text"] for row in events if row.get("type") == "delta"] == ["xyz"]


def test_session_registra_el_turno_en_el_transcript(workspace: Workspace):
    session: TeacherSession = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    session.aprobar()
    texto = session.transcript.path.read_text(encoding="utf-8")
    assert PEDIDO_GUIA in texto
