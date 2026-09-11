"""Tools del agente: leen la carpeta o proponen en memoria. Ninguna escribe."""

from __future__ import annotations

import json

import pytest

from tero.errors import WorkspaceError
from tero.hashutil import sha256_file
from tero.tools import DRAFT_TOOL_BUDGET, TurnContext, build_tools
from tero.types import ArtifactType, Encargo
from tero.workspace import Workspace

ENCARGO = Encargo(
    curso="4° básico",
    asignatura="Lenguaje y Comunicación",
    oa="LEN-4B-OA04",
    duracion="45 min",
)
GUIA = "# Guía\n\n## Propósito\nLeer.\n\n## Instrucciones\nSigue los pasos.\n"
CUENTO = "fuentes/cuento-el-condor-y-el-huemul.md"


def _tools(workspace: Workspace, encargo: Encargo | None = None) -> dict:
    ctx = TurnContext(workspace=workspace, encargo=encargo or ENCARGO)
    return {tool.tool_name: tool for tool in build_tools(ctx)}


def _hash_tree(root) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_ninguna_tool_escribe_en_la_carpeta(workspace: Workspace):
    workspace.ensure_index()
    workspace.write_artifact("derivados/probe.md", "# Material previo\n")
    antes = _hash_tree(workspace.root)

    ctx = TurnContext(workspace=workspace, encargo=ENCARGO)
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    llamadas = {
        "list_sources": {},
        "list_artifacts": {},
        "read_artifact": {"path": "derivados/probe.md"},
        "search_sources": {"query": "huemul"},
        "read_source": {"path": CUENTO},
        "list_oa": {},
        "get_oa": {"id": "LEN-4B-OA04"},
        "search_oa": {"q": "comprensión"},
        "cite_evidence": {"path": CUENTO, "snippet": "El huemul no corrió", "seccion": "inicio"},
        "proponer_crear": {
            "tipo": "guia",
            "titulo": "Guía del cuento",
            "resumen": "Guía breve.",
            "vista_previa_markdown": GUIA,
        },
        "proponer_editar": {
            "ruta_origen": "derivados/probe.md",
            "accion": "editar",
            "tipo": "guia",
            "titulo": "Guía del cuento",
            "resumen": "Versión nueva.",
            "vista_previa_markdown": GUIA,
        },
    }
    for name, kwargs in llamadas.items():
        result = tools[name](**kwargs)
        assert result, name

    assert _hash_tree(workspace.root) == antes
    assert ctx.pending_propuesta is not None
    assert ctx.pending_propuesta.accion == "editar"
    assert ctx.pending_propuesta.origen == "derivados/probe.md"


def test_read_artifact_lee_derivados(workspace: Workspace):
    workspace.write_artifact("derivados/probe.md", "# Material derivado\n\nHola.\n")
    tools = _tools(workspace)
    payload = json.loads(tools["read_artifact"](path="derivados/probe.md"))
    assert payload["path"] == "derivados/probe.md"
    assert "Material derivado" in payload["texto"]


def test_read_source_no_deja_leer_derivados(workspace: Workspace):
    workspace.write_artifact("derivados/probe.md", "# Material derivado\n")
    tools = _tools(workspace)
    with pytest.raises(WorkspaceError) as caught:
        tools["read_source"](path="derivados/probe.md")
    assert "no es una fuente original" in str(caught.value)


@pytest.mark.xfail(
    strict=False,
    reason=(
        "BUG host: `Workspace.resolve_source` decide con `target.parts` de la ruta ABSOLUTA, "
        "así que basta que un directorio padre se llame `fuentes` para que el guard de "
        "derivados/ se desactive y `read_source` devuelva material derivado como fuente."
    ),
)
def test_read_source_no_deja_leer_derivados_si_un_padre_se_llama_fuentes(tmp_path):
    import shutil

    from tero.config import EXAMPLE_CARPETA

    root = tmp_path / "fuentes" / "carpeta"
    shutil.copytree(
        EXAMPLE_CARPETA,
        root,
        ignore=shutil.ignore_patterns("derivados", "borradores", ".tero"),
    )
    workspace = Workspace(root)
    workspace.write_artifact("derivados/probe.md", "# Material derivado\n")
    tools = _tools(workspace)
    with pytest.raises(WorkspaceError):
        tools["read_source"](path="derivados/probe.md")


def test_proponer_editar_con_ruta_inexistente_no_crea_propuesta(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=ENCARGO)
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    payload = json.loads(
        tools["proponer_editar"](
            ruta_origen="derivados/no-existe.md",
            accion="editar",
            tipo="guia",
            titulo="Guía fantasma",
            resumen="No debería existir.",
            vista_previa_markdown=GUIA,
        )
    )
    assert payload["ok"] is False
    assert payload["error"] == "origen_no_encontrado"
    assert ctx.pending_propuesta is None
    assert (workspace.root / "derivados").glob("*.md")
    assert list((workspace.root / "derivados").glob("*.md")) == []


def test_proponer_editar_rechaza_rutas_fuera_de_la_carpeta(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=ENCARGO)
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    payload = json.loads(
        tools["proponer_editar"](
            ruta_origen="../secreto.md",
            accion="editar",
            tipo="guia",
            titulo="Fuera",
            resumen="No.",
            vista_previa_markdown=GUIA,
        )
    )
    assert payload["ok"] is False
    assert ctx.pending_propuesta is None


def test_proponer_crear_con_tipo_desconocido_no_crea_propuesta(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=ENCARGO)
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    payload = json.loads(
        tools["proponer_crear"](
            tipo="ensalada",
            titulo="Nada",
            resumen="No.",
            vista_previa_markdown=GUIA,
        )
    )
    assert payload["ok"] is False
    assert ctx.pending_propuesta is None


def test_proponer_crear_arma_la_propuesta_en_memoria(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=ENCARGO)
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    payload = json.loads(
        tools["proponer_crear"](
            tipo="guia",
            titulo="Guía del cuento",
            resumen="Guía breve.",
            vista_previa_markdown=GUIA,
            evidencias_json=json.dumps([{"path": CUENTO, "snippet": "El huemul no corrió"}]),
        )
    )
    assert payload["ok"] is True
    assert payload["accion"] == "crear"
    propuesta = ctx.pending_propuesta
    assert propuesta is not None
    assert propuesta.tipo is ArtifactType.GUIA
    assert propuesta.titulo == "Guía del cuento"
    assert propuesta.draft.evidencias[0].verified is True


def test_la_segunda_propuesta_del_turno_no_reemplaza_a_la_primera(workspace: Workspace):
    # El turno real siempre fija el presupuesto antes de correr al agente
    # (`TeacherSession._call_model`); sin presupuesto no hay guard de propuesta.
    ctx = TurnContext(workspace=workspace, encargo=ENCARGO)
    ctx.reset_tool_budget(DRAFT_TOOL_BUDGET)
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    tools["proponer_crear"](tipo="guia", titulo="Uno", resumen="r", vista_previa_markdown=GUIA)
    segunda = json.loads(
        tools["proponer_crear"](
            tipo="pauta", titulo="Dos", resumen="r", vista_previa_markdown="# Otra\n"
        )
    )
    assert segunda["already"] is True
    assert ctx.pending_propuesta is not None
    assert ctx.pending_propuesta.titulo == "Uno"


def test_el_presupuesto_de_tools_deja_una_ultima_propuesta(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=ENCARGO)
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    ctx.reset_tool_budget(DRAFT_TOOL_BUDGET)
    ultimo = None
    for _ in range(DRAFT_TOOL_BUDGET + 3):
        ultimo = json.loads(tools["list_sources"]())
    assert ultimo is not None
    assert ultimo["error"] == "presupuesto_herramientas_agotado"
    assert ctx.budget_exhausted is True
    # Una tool que no propone queda bloqueada…
    assert json.loads(tools["cite_evidence"](path=CUENTO, snippet="huemul"))["error"] == (
        "presupuesto_herramientas_agotado"
    )
    # …y la propuesta todavía tiene su última oportunidad.
    creada = json.loads(
        tools["proponer_crear"](
            tipo="guia", titulo="Al límite", resumen="r", vista_previa_markdown=GUIA
        )
    )
    assert creada["ok"] is True
    assert ctx.pending_propuesta is not None


def test_workspace_list_artifacts_ordena_por_fecha_y_respeta_limit(workspace: Workspace):
    import os
    import time

    viejo = workspace.write_artifact(
        "derivados/viejo.md", "---\ntitulo: Guía vieja\n---\n\n# Vieja\n"
    )
    time.sleep(0.01)
    nuevo = workspace.write_artifact("derivados/nuevo.md", "# Sin front matter\n")
    os.utime(viejo, (1_600_000_000, 1_600_000_000))
    os.utime(nuevo, (1_700_000_000, 1_700_000_000))

    items = workspace.list_artifacts()
    assert [item["path"] for item in items] == ["derivados/nuevo.md", "derivados/viejo.md"]
    assert items[0]["titulo"] == "nuevo"  # sin front matter: cae al stem
    assert items[0]["carpeta"] == "derivados"
    assert items[1]["titulo"] == "Guía vieja"
    assert len(workspace.list_artifacts(limit=1)) == 1


def test_workspace_list_artifacts_incluye_borradores_legado(workspace: Workspace):
    workspace.write_artifact("borradores/legado.md", "---\ntitulo: Legado\n---\n\n# Legado\n")
    items = workspace.list_artifacts()
    assert [item["carpeta"] for item in items] == ["borradores"]


def test_la_tool_list_artifacts_expone_path_titulo_y_carpeta(workspace: Workspace):
    workspace.write_artifact("derivados/uno.md", "---\ntitulo: Guía uno\n---\n\n# Guía\n")
    tools = _tools(workspace)
    payload = json.loads(tools["list_artifacts"]())
    materiales = payload["materiales"]
    assert materiales
    assert materiales[0]["path"] == "derivados/uno.md"
    assert materiales[0]["titulo"] == "Guía uno"
    assert materiales[0]["carpeta"] == "derivados"
    assert set(materiales[0]) == {"path", "titulo", "carpeta"}


def test_cite_evidence_marca_lo_que_no_esta_textual(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=ENCARGO)
    tools = {tool.tool_name: tool for tool in build_tools(ctx)}
    real = json.loads(tools["cite_evidence"](path=CUENTO, snippet="El huemul no corrió"))
    assert real["verified"] is True
    falso = json.loads(tools["cite_evidence"](path=CUENTO, snippet="Los pingüinos votaron"))
    assert falso["verified"] is False
    assert len(ctx.evidence) == 2
