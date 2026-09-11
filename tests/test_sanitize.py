"""Leaked tool traces must not land on the photocopied ficha."""

from __future__ import annotations

import json

import pytest

from tero.artifacts import materialize_markdown
from tero.export import export_latex
from tero.latex.schemas import repair_payload
from tero.salvage import salvage_draft_from_text
from tero.sanitize import strip_tool_traces, strip_tool_traces_value
from tero.tools import TurnContext, build_tools
from tero.types import ArtifactType, Encargo, Propuesta
from tero.workspace import Workspace

QWEN_LINE = (
    'Leer el fragmento del OA 12: "Describir la distribución del agua dulce." '
    "(cite_evidence: fuentes/01-oa-curriculo.md)"
)


def test_strip_paren_and_bare_cite_evidence():
    cleaned = strip_tool_traces(QWEN_LINE)
    assert "cite_evidence" not in cleaned
    assert "fuentes/01-oa-curriculo.md" not in cleaned
    assert "Describir la distribución del agua dulce." in cleaned
    bare = strip_tool_traces(
        "Sequías recurrentes cite_evidence: fuentes/03-contexto-chile.md en el centro."
    )
    assert "cite_evidence" not in bare
    assert "Sequías recurrentes" in bare
    assert "en el centro." in bare


def test_strip_keeps_classroom_spanish():
    prose = "Cita evidencia del cuento. El huemul preguntó al cóndor."
    assert strip_tool_traces(prose) == prose


def test_strip_walks_payload_desarrollo():
    payload = {
        "tipo": "planificacion",
        "desarrollo": QWEN_LINE,
        "actividades": [{"desarrollo": QWEN_LINE}],
    }
    cleaned = strip_tool_traces_value(payload)
    assert "cite_evidence" not in json.dumps(cleaned)
    assert "agua dulce" in cleaned["desarrollo"]


def test_repair_payload_strips_plan_prose():
    repaired = repair_payload(
        "planificacion",
        {"titulo": "Agua", "desarrollo": QWEN_LINE, "objetivo": "Explicar el agua."},
    )
    assert "cite_evidence" not in json.dumps(repaired, ensure_ascii=False)
    assert "agua dulce" in repaired["desarrollo"]


def test_proponer_crear_limpia_el_payload_y_el_archivo_escrito(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {t.tool_name: t for t in build_tools(ctx)}
    tools["proponer_crear"](
        tipo="planificacion",
        titulo="Agua",
        resumen="Plan de clase.",
        vista_previa_markdown="# Plan\n\n## Objetivo\nx\n## Desarrollo\n" + QWEN_LINE + "\n",
        payload_json=json.dumps(
            {"tipo": "planificacion", "desarrollo": QWEN_LINE},
            ensure_ascii=False,
        ),
    )
    propuesta = ctx.pending_propuesta
    assert propuesta is not None
    assert propuesta.draft.payload is not None
    assert "cite_evidence" not in json.dumps(propuesta.draft.payload, ensure_ascii=False)
    md = materialize_markdown(Encargo(curso="5° básico"), propuesta)
    assert "cite_evidence" not in md


@pytest.mark.xfail(
    strict=False,
    reason=(
        "BUG host: `proponer_crear`/`proponer_editar` guardan la vista previa sin pasar por "
        "`scrub_ficha_text`, así que el evento `propuesta` (y `as_dict()['vista_previa']`) "
        "muestra rastros de tools en pantalla. El salvage sí limpia y el archivo escrito "
        "también (materialize_markdown scrubea), pero la vista previa no."
    ),
)
def test_la_vista_previa_no_muestra_rastros_de_tools(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {t.tool_name: t for t in build_tools(ctx)}
    tools["proponer_crear"](
        tipo="planificacion",
        titulo="Agua",
        resumen="Plan de clase.",
        vista_previa_markdown="# Plan\n\n## Objetivo\nx\n## Desarrollo\n" + QWEN_LINE + "\n",
    )
    propuesta = ctx.pending_propuesta
    assert propuesta is not None
    assert "cite_evidence" not in propuesta.draft.cuerpo_markdown
    assert "cite_evidence" not in propuesta.as_dict()["vista_previa"]


def test_salvage_and_export_drop_traces(tmp_path, workspace: Workspace):
    blob = (
        "# Planificación\n\n## Objetivo\nCuidar el agua.\n\n## Inicio\nPreguntar.\n\n"
        "## Desarrollo\n"
        + QWEN_LINE
        + "\n\n## Cierre\nTicket.\n\n## Evaluación\nFormativa.\n"
        + "x" * 200
    )
    draft = salvage_draft_from_text(blob, fallback_tipo=ArtifactType.PLANIFICACION)
    assert draft is not None
    assert "cite_evidence" not in draft.cuerpo_markdown
    propuesta = Propuesta(accion="crear", draft=draft, resumen="Plan de clase.")
    md = materialize_markdown(Encargo(curso="5° básico"), propuesta)
    source = tmp_path / "plan.md"
    dest = tmp_path / "plan.tex"
    source.write_text(md, encoding="utf-8")
    export_latex(source, dest, tipo="planificacion")
    tex = dest.read_text(encoding="utf-8")
    assert "cite_evidence" not in tex
    assert "cite\\_evidence" not in tex


QWEN_OPTION = r"\\( \\begin{cases} 2x + y = 4 \\\\ x - y = 2 \\end{cases} \\)"


def test_flatten_cases_tex_in_opciones():
    from tero.sanitize import flatten_tex_leaks, scrub_ficha_text

    flat = flatten_tex_leaks(QWEN_OPTION)
    assert "begin{cases}" not in flat
    assert "2x + y = 4" in flat
    assert "x - y = 2" in flat
    repaired = repair_payload(
        "evaluacion",
        {
            "titulo": "Sistemas",
            "items": [
                {
                    "tipo_item": "sm",
                    "enunciado": "¿Cuál NO tiene solución única?",
                    "opciones": [QWEN_OPTION, "(2, 3)"],
                }
            ],
        },
    )
    blob = json.dumps(repaired, ensure_ascii=False)
    assert "begin{cases}" not in blob
    assert "2x + y = 4" in blob
    leftover = "¿Cuál es la solución del sistema: ; [ \\ x + y = 5; x - y = 1 \\ ; ]"
    cleaned = flatten_tex_leaks(leftover)
    assert "[" not in cleaned
    assert "x + y = 5" in cleaned
    assert "cite_evidence" not in scrub_ficha_text(QWEN_LINE + " " + QWEN_OPTION)
