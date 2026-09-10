"""Leaked tool traces must not land on the photocopied ficha."""

from __future__ import annotations

import json

from tero.artifacts import materialize_markdown
from tero.export import export_latex
from tero.latex.schemas import repair_payload
from tero.salvage import salvage_draft_from_text
from tero.sanitize import strip_tool_traces, strip_tool_traces_value
from tero.tools import TurnContext, build_tools
from tero.types import ArtifactType, Encargo
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


def test_draft_artifact_strips_traces(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {t.tool_name: t for t in build_tools(ctx, phase="draft")}
    tools["draft_artifact"](
        tipo="planificacion",
        titulo="Agua",
        cuerpo_markdown="# Plan\n\n## Objetivo\nx\n## Desarrollo\n" + QWEN_LINE + "\n",
        payload_json=json.dumps(
            {"tipo": "planificacion", "desarrollo": QWEN_LINE},
            ensure_ascii=False,
        ),
    )
    assert ctx.pending_draft is not None
    assert "cite_evidence" not in ctx.pending_draft.cuerpo_markdown
    assert ctx.pending_draft.payload is not None
    assert "cite_evidence" not in json.dumps(ctx.pending_draft.payload, ensure_ascii=False)
    md = materialize_markdown(Encargo(curso="5° básico"), None, ctx.pending_draft)
    assert "cite_evidence" not in md


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
    md = materialize_markdown(Encargo(curso="5° básico"), None, draft)
    source = tmp_path / "plan.md"
    dest = tmp_path / "plan.tex"
    source.write_text(md, encoding="utf-8")
    export_latex(source, dest, tipo="planificacion")
    tex = dest.read_text(encoding="utf-8")
    assert "cite_evidence" not in tex
    assert "cite\\_evidence" not in tex
