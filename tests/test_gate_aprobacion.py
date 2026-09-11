"""La puerta de aprobación: sin `aprobar()` no se escribe nada, y nunca se sobrescribe."""

from __future__ import annotations

import pytest

from tero.errors import TeroError
from tero.hashutil import sha256_file
from tero.types import Encargo
from tero.workspace import Workspace
from tests.support import (
    PEDIDO_GUIA,
    PEDIDO_PLANIFICACION,
    artifact_paths,
    open_session,
)


def _arbol(workspace: Workspace) -> dict[str, str]:
    """Hash del material de la carpeta: fuentes, derivados y borradores.

    Deja fuera `.tero/` (índice y transcripción), que es bookkeeping del host y
    cambia en cada turno por diseño.
    """
    out: dict[str, str] = {}
    for folder in ("fuentes", "derivados", "borradores"):
        root = workspace.root / folder
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                out[path.relative_to(workspace.root).as_posix()] = sha256_file(path)
    return out


def test_sin_aprobar_no_se_escribe_nada(workspace: Workspace):
    antes = _arbol(workspace)
    session = open_session(workspace)
    session.start_turn(PEDIDO_PLANIFICACION)

    assert session.pending_propuesta is not None
    assert session.phase == "esperando_aprobacion"
    assert _arbol(workspace) == antes


def test_descartar_no_escribe_y_vuelve_a_idle(workspace: Workspace):
    antes = _arbol(workspace)
    session = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    turn = session.descartar("no por ahora")

    assert session.phase == "idle"
    assert session.pending_propuesta is None
    assert turn is not None and turn.phase == "idle"
    assert _arbol(workspace) == antes
    assert artifact_paths(workspace) == []


def test_descartar_sin_propuesta_pendiente_levanta_error(workspace: Workspace):
    session = open_session(workspace)
    with pytest.raises(TeroError) as caught:
        session.descartar()
    assert caught.value.code == "no_propuesta"


def test_aprobar_sin_propuesta_pendiente_levanta_error(workspace: Workspace):
    session = open_session(workspace)
    with pytest.raises(TeroError) as caught:
        session.aprobar()
    assert caught.value.code == "no_propuesta"


def test_aprobar_dos_veces_no_sobrescribe_ni_duplica(workspace: Workspace):
    session = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    primero = session.aprobar()
    assert primero.path is not None
    contenido = primero.path.read_text(encoding="utf-8")

    with pytest.raises(TeroError) as caught:
        session.aprobar()
    assert caught.value.code == "no_propuesta"

    assert artifact_paths(workspace) == [primero.path]
    assert primero.path.read_text(encoding="utf-8") == contenido


def test_dos_creaciones_del_mismo_material_escriben_archivos_distintos(workspace: Workspace):
    session = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    primero = session.aprobar()
    session.start_turn(PEDIDO_GUIA)
    segundo = session.aprobar()

    assert primero.path is not None and segundo.path is not None
    assert primero.path != segundo.path
    assert primero.path.exists() and segundo.path.exists()
    assert len(artifact_paths(workspace)) == 2


def test_editar_un_archivo_existente_no_lo_sobrescribe(workspace: Workspace):
    session = open_session(workspace)
    session.start_turn(PEDIDO_PLANIFICACION)
    origen = session.aprobar()
    assert origen.path is not None
    digest = sha256_file(origen.path)
    ruta = origen.path.relative_to(workspace.root).as_posix()

    otra = open_session(workspace)
    otra.start_turn(f"Edita {ruta} y acorta el cierre.")
    resultado = otra.aprobar()

    assert resultado.path is not None and resultado.path != origen.path
    assert sha256_file(origen.path) == digest
    assert len(artifact_paths(workspace)) == 2


def test_fuentes_intactas_tras_aprobar(workspace: Workspace):
    antes = workspace.fingerprint_sources()
    session = open_session(workspace)
    session.start_turn(PEDIDO_PLANIFICACION)
    # El agente lee las fuentes antes de proponer: eso tampoco las toca.
    assert workspace.fingerprint_sources() == antes

    session.aprobar()
    assert workspace.fingerprint_sources() == antes


def test_borradores_es_legado_y_no_recibe_escrituras(workspace: Workspace):
    session = open_session(workspace)
    session.start_turn(PEDIDO_GUIA)
    session.aprobar()

    assert artifact_paths(workspace, "derivados")
    assert artifact_paths(workspace, "borradores") == []


def test_avisos_no_bloquean_la_aprobacion(workspace: Workspace):
    """thin_evidence / unverified_citation se muestran, pero la persona decide igual."""
    from unittest.mock import patch

    from tests.fake_models import ToolModel

    model = ToolModel(
        "proponer_crear",
        {
            "tipo": "evaluacion",
            "titulo": "Prueba corta",
            "resumen": "Evaluación breve del cuento.",
            "vista_previa_markdown": "# Prueba\n\n## Instrucciones\nResponde.\n",
            "evidencias_json": (
                '[{"path": "fuentes/cuento-el-condor-y-el-huemul.md", '
                '"snippet": "Los pingüinos votaron en el valle."}]'
            ),
        },
    )
    session = open_session(workspace)
    with patch("tero.session.make_model", return_value=model):
        session.start_turn("Prepara una evaluación corta del cuento.")

    propuesta = session.pending_propuesta
    assert propuesta is not None
    codigos = {item.code for item in propuesta.draft.warnings}
    assert "thin_evidence" in codigos
    assert "unverified_citation" in codigos
    assert all(item.blocking is False for item in propuesta.draft.warnings)

    resultado = session.aprobar()
    assert resultado.path is not None
    assert resultado.path.exists()


def test_el_contexto_no_bloquea_una_propuesta_de_otro_tipo(workspace: Workspace):
    """El tipo del encargo es contexto, no una puerta: si el material llega distinto, se aprueba."""
    from unittest.mock import patch

    from tero.types import ArtifactType
    from tests.fake_models import ToolModel

    encargo = Encargo(
        curso="4° básico",
        asignatura="Lenguaje y Comunicación",
        oa="LEN-4B-OA04",
        tipo=ArtifactType.PLANIFICACION,
    )
    model = ToolModel(
        "proponer_crear",
        {
            "tipo": "pauta",
            "titulo": "Pauta de cierre",
            "resumen": "Pauta para el ticket de salida.",
            "vista_previa_markdown": (
                "# Pauta\n\n## Criterios\nEvidencia\n\n## Niveles\nLogrado\n\n"
                "## Descriptores\nCita el cuento.\n"
            ),
        },
        then_text="Listo.",
    )
    session = open_session(workspace, encargo)
    with patch("tero.session.make_model", return_value=model):
        session.start_turn("Prepara una pauta de cierre para la clase.")

    propuesta = session.pending_propuesta
    assert propuesta is not None
    assert propuesta.draft.tipo is ArtifactType.PAUTA
    assert all(item.blocking is False for item in propuesta.draft.warnings)

    resultado = session.aprobar()
    assert resultado.path is not None
    assert resultado.path.exists()
