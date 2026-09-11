"""Regresión: Nova Lite manda argumentos como listas; el host los coerciona."""

from __future__ import annotations

import json

from tero.coerce import as_text
from tero.evidence import snippet_in_text
from tero.tools import TurnContext, build_tools
from tero.types import ArtifactType, Encargo
from tero.workspace import Workspace

CUERPO_LISTA = [
    "# Actividad",
    "",
    "## Objetivo",
    "Preguntar como el huemul.",
    "",
    "## Materiales",
    "Cuento y lápiz.",
    "",
    "## Pasos",
    "Uno, dos, tres.",
]


def test_as_text_joins_lists():
    assert as_text(["a", "b"]) == "a\nb"
    assert as_text(["a", "b"], joiner=" ") == "a b"
    assert as_text(None) == ""
    assert as_text("ya") == "ya"


def test_artifact_type_parse_accepts_list():
    assert ArtifactType.parse(["planificacion"]) is ArtifactType.PLANIFICACION
    assert ArtifactType.parse(["guía"]) is ArtifactType.GUIA


def test_snippet_in_text_accepts_list():
    assert snippet_in_text("hola mundo largo", ["hola", "mundo"])
    assert not snippet_in_text("hola mundo largo", ["adios"])


def test_proponer_crear_acepta_argumentos_en_lista(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    result = json.loads(
        tools["proponer_crear"](
            tipo=["actividad"],
            titulo=["Preguntar", "como el huemul"],
            resumen=["Actividad", "breve"],
            vista_previa_markdown=CUERPO_LISTA,
        )
    )
    assert result["ok"] is True
    propuesta = ctx.pending_propuesta
    assert propuesta is not None
    assert "Preguntar" in propuesta.titulo
    assert propuesta.tipo is ArtifactType.ACTIVIDAD
    assert "## Pasos" in propuesta.vista_previa


def test_proponer_editar_acepta_listas_en_cambios_y_notas(workspace: Workspace):
    workspace.write_artifact("derivados/base.md", "# Base\n")
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    result = json.loads(
        tools["proponer_editar"](
            ruta_origen=["derivados/base.md"],
            accion=["adaptar"],
            tipo=["actividad"],
            titulo=["Preguntar", "como el huemul"],
            resumen=["Versión", "adaptada"],
            vista_previa_markdown=CUERPO_LISTA,
            cambios=["Tiempos por momento", "Enunciados cortos"],
            notas_nee=["Lectura en voz alta", "Tiempo extra"],
        )
    )
    assert result["ok"] is True
    propuesta = ctx.pending_propuesta
    assert propuesta is not None
    assert propuesta.accion == "adaptar"
    assert propuesta.origen == "derivados/base.md"
    assert propuesta.cambios == ["Tiempos por momento", "Enunciados cortos"]
    assert propuesta.notas_nee == ["Lectura en voz alta", "Tiempo extra"]
