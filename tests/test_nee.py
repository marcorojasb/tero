"""Decreto 83/2015: el contrato NEE de una propuesta de adaptación.

Los apoyos de una adaptación se declaran con `acceso · <criterio>: …` u
`objetivos · <criterio>: …`, y todos los avisos son informativos: nunca bloquean
la aprobación.
"""

from __future__ import annotations

import json

from tero.evidence import (
    NEE_CRITERIOS_ACCESO,
    NEE_CRITERIOS_OBJETIVOS,
    propuesta_warnings,
)
from tero.salvage import _split_kw_items
from tero.tools import TurnContext, build_tools
from tero.types import ArtifactDraft, ArtifactType, Encargo, Propuesta
from tero.workspace import Workspace
from tests.support import crear_y_aprobar, open_session, rel

GUIA = (
    "# Guía adaptada\n\n## Propósito\nLeer.\n\n## Instrucciones\nSigue los pasos.\n\n"
    "## Actividades\nUna lectura guiada.\n\n## Cierre\nTicket de salida.\n"
)


def _propuesta(accion: str = "adaptar", notas: list[str] | None = None) -> Propuesta:
    draft = ArtifactDraft(tipo=ArtifactType.GUIA, titulo="Guía adaptada", cuerpo_markdown=GUIA)
    return Propuesta(
        accion=accion,  # type: ignore[arg-type]
        draft=draft,
        resumen="Versión adaptada.",
        origen="derivados/base.md",
        cambios=["Inicio: tiempos por momento de clase"],
        notas_nee=list(notas or []),
    )


def _codigos(propuesta: Propuesta) -> set[str]:
    return {item.code for item in propuesta_warnings(propuesta)}


def test_el_vocabulario_del_decreto_esta_cerrado():
    assert NEE_CRITERIOS_ACCESO == (
        "presentación de la información",
        "formas de respuesta",
        "entorno",
        "tiempo",
    )
    assert NEE_CRITERIOS_OBJETIVOS == (
        "graduación",
        "priorización",
        "temporalización",
        "enriquecimiento",
        "eliminación",
    )


def test_adaptar_siempre_avisa_que_no_es_un_paci():
    warnings = propuesta_warnings(_propuesta())
    assert [item.code for item in warnings] == ["paci_no_oficial"]
    assert warnings[0].blocking is False
    assert "PACI" in warnings[0].message


def test_objetivos_sin_apoyos_de_acceso_avisa():
    warnings = propuesta_warnings(
        _propuesta(notas=["objetivos · priorización: foco en el OA de comprensión."])
    )
    assert "paci_no_oficial" in {item.code for item in warnings}
    assert "nee_sin_apoyos_de_acceso" in {item.code for item in warnings}
    assert all(item.blocking is False for item in warnings)


def test_con_apoyos_de_acceso_no_avisa_por_objetivos():
    codigos = _codigos(
        _propuesta(
            notas=[
                "acceso · tiempo: tiempo extra para completar la guía",
                "objetivos · priorización: foco en el OA de comprensión",
            ]
        )
    )
    assert "paci_no_oficial" in codigos
    assert "nee_sin_apoyos_de_acceso" not in codigos


def test_eliminacion_avisa_porque_el_decreto_la_limita():
    warnings = propuesta_warnings(
        _propuesta(
            notas=[
                "acceso · tiempo: tiempo extra",
                "objetivos · eliminación: se excluye el ítem de producción escrita",
            ]
        )
    )
    assert "nee_eliminacion" in {item.code for item in warnings}
    assert all(item.blocking is False for item in warnings)


def test_crear_y_editar_no_agregan_avisos_nee():
    for accion in ("crear", "editar"):
        assert propuesta_warnings(_propuesta(accion)) == []


def test_los_criterios_de_acceso_no_se_parten_al_guardarlos(workspace: Workspace):
    workspace.write_artifact("derivados/base.md", "# Base\n")
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    result = json.loads(
        tools["proponer_editar"](
            ruta_origen="derivados/base.md",
            accion="adaptar",
            tipo="guia",
            titulo="Guía adaptada",
            resumen="Versión adaptada.",
            vista_previa_markdown=GUIA,
            cambios="Inicio: tiempos por momento de clase\nDesarrollo: enunciados más cortos",
            notas_nee=(
                "acceso · tiempo: tiempo extra para completar la guía\n"
                "acceso · entorno: puesto cerca del pizarrón"
            ),
        )
    )
    assert result["ok"] is True
    propuesta = ctx.pending_propuesta
    assert propuesta is not None
    assert propuesta.cambios == [
        "Inicio: tiempos por momento de clase",
        "Desarrollo: enunciados más cortos",
    ]
    assert propuesta.notas_nee == [
        "acceso · tiempo: tiempo extra para completar la guía",
        "acceso · entorno: puesto cerca del pizarrón",
    ]
    assert [item.code for item in propuesta_warnings(propuesta)] == ["paci_no_oficial"]


def test_el_salvage_tampoco_parte_por_el_separador_del_criterio():
    assert _split_kw_items("acceso · tiempo: extra\nacceso · entorno: cerca del pizarrón") == [
        "acceso · tiempo: extra",
        "acceso · entorno: cerca del pizarrón",
    ]


def test_una_adaptacion_del_flujo_completo_trae_el_aviso_paci(workspace: Workspace):
    origen = crear_y_aprobar(workspace)
    ruta = rel(workspace, origen)
    session = open_session(workspace)
    turn = session.start_turn(f"Adapta {ruta} para NEE con apoyos visuales y más tiempo.")

    assert turn.propuesta is not None
    assert turn.propuesta.accion == "adaptar"
    codigos = {item.code for item in turn.propuesta.draft.warnings}
    assert "paci_no_oficial" in codigos
    assert all(item.blocking is False for item in turn.propuesta.draft.warnings)
    assert all(nota.startswith(("acceso · ", "objetivos · ")) for nota in turn.propuesta.notas_nee)

    resultado = session.aprobar()
    assert resultado.path is not None
    assert resultado.path.exists()


def test_el_guion_offline_nombra_la_seccion_en_los_cambios(workspace: Workspace):
    origen = crear_y_aprobar(workspace)
    ruta = rel(workspace, origen)
    session = open_session(workspace)
    turn = session.start_turn(f"Edita {ruta} y ajusta los tiempos de la clase.")

    assert turn.propuesta is not None
    assert turn.propuesta.cambios
    assert all(":" in cambio for cambio in turn.propuesta.cambios)


def test_el_host_etiqueta_los_apoyos_que_vienen_sin_criterio():
    """Contrato blando: si el modelo escribe el apoyo en texto libre, se etiqueta."""
    from tero.evidence import normalizar_notas_nee

    notas, etiquetadas = normalizar_notas_nee(
        [
            "Tiempo extra para terminar",
            "Letra más grande y apoyos visuales",
            "Puede responder de forma oral o con dibujo",
            "acceso · entorno: puesto cerca del pizarrón",
            "Se prioriza el OA de comprensión",
        ]
    )
    assert etiquetadas == 3
    assert notas[0] == "acceso · tiempo: Tiempo extra para terminar"
    assert notas[1].startswith("acceso · presentación de la información:")
    assert notas[2].startswith("acceso · formas de respuesta:")
    # Lo que ya traía criterio se respeta tal cual, y una nota sin palabra
    # inequívoca no se inventa: queda como estaba y se avisa más abajo.
    assert notas[3] == "acceso · entorno: puesto cerca del pizarrón"
    assert notas[4] == "Se prioriza el OA de comprensión"


def test_una_adaptacion_sin_criterios_avisa_sin_bloquear():
    from tero.evidence import propuesta_warnings

    warnings = propuesta_warnings(_propuesta(notas=["Apoyo general para la clase"]))
    codigos = {item.code for item in warnings}
    assert "nee_sin_criterios" in codigos
    assert all(item.blocking is False for item in warnings)


def test_adaptar_sin_notas_pide_una_vez_y_no_bloquea(workspace: Workspace):
    """El contrato blando pide los apoyos una vez; la segunda llamada pasa."""
    import json

    from tero.tools import TurnContext, build_tools

    workspace.write_artifact("derivados/base.md", "# Base\n")
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    argumentos = dict(
        ruta_origen="derivados/base.md",
        accion="adaptar",
        tipo="guia",
        titulo="Guía adaptada",
        resumen="Versión adaptada.",
        vista_previa_markdown=GUIA,
    )
    primera = json.loads(tools["proponer_editar"](**argumentos))
    assert primera["ok"] is False
    assert primera["error"] == "nee_sin_notas"
    assert "acceso ·" in primera["hint"]
    assert ctx.pending_propuesta is None

    segunda = json.loads(tools["proponer_editar"](**argumentos))
    assert segunda["ok"] is True  # no bloquea: se acepta igual
    assert ctx.pending_propuesta is not None
    assert ctx.pending_propuesta.notas_nee == []
