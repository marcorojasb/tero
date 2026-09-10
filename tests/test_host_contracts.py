"""Host contracts: payload_json, catalog_covers, tipo_desviado, draft tool budget."""

from __future__ import annotations

import json

from tero.artifacts import materialize_markdown
from tero.evidence import collect_warnings
from tero.export import export_latex
from tero.latex.schemas import extract_payload_from_markdown, parse_payload_json
from tero.plan import build_plan
from tero.salvage import salvage_draft_from_text
from tero.tools import DRAFT_TOOL_BUDGET, TurnContext, build_tools
from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence
from tero.workspace import Workspace


def _draft_tools(workspace: Workspace, encargo: Encargo | None = None) -> tuple[TurnContext, dict]:
    ctx = TurnContext(workspace=workspace, encargo=encargo or Encargo(oa="OA 4"))
    tools = {t.tool_name: t for t in build_tools(ctx, phase="draft")}
    return ctx, tools


def test_draft_artifact_payload_json_preferred_on_export(workspace: Workspace, tmp_path):
    ctx, tools = _draft_tools(workspace)
    payload = {
        "tipo": "evaluacion",
        "titulo": "Prueba huemul",
        "instrucciones": ["Lee el cuento."],
        "items": [
            {
                "tipo_item": "sm",
                "enunciado": "¿Quién preguntó?",
                "opciones": ["El huemul", "El río"],
                "clave": "A",
            }
        ],
        "criterios": ["Cita del cuento"],
        "puntaje_total": "10",
    }
    result = json.loads(
        tools["draft_artifact"](
            tipo="evaluacion",
            titulo="Prueba huemul",
            cuerpo_markdown="# Corta\n\nSin headings de ítems.\n",
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
    )
    assert result["ok"] is True
    assert result["payload"] is True
    assert ctx.pending_draft is not None
    assert ctx.pending_draft.payload is not None
    assert ctx.pending_draft.payload["items"]

    md = materialize_markdown(Encargo(curso="4° básico"), None, ctx.pending_draft)
    assert "```json" in md
    extracted = extract_payload_from_markdown(md, tipo="evaluacion")
    sm = [row for row in extracted["items"] if row.get("tipo_item") == "sm"]
    assert sm
    assert "preguntó" in sm[0]["enunciado"].lower()
    assert any("huemul" in str(opt).lower() for opt in sm[0].get("opciones") or [])

    dest = tmp_path / "from-payload.tex"
    source = tmp_path / "from-payload.md"
    source.write_text(md, encoding="utf-8")
    export_latex(source, dest, tipo="evaluacion")
    tex = dest.read_text(encoding="utf-8")
    assert "Quién preguntó" in tex or "Qui\\'en preguntó" in tex or "huemul" in tex.lower()


def test_list_oa_media_catalog_covers_false(workspace: Workspace):
    ctx, tools = _draft_tools(
        workspace,
        Encargo(curso="1° medio", asignatura="Matemática", oa="sistemas 2x2"),
    )
    listed = json.loads(tools["list_oa"]())
    assert listed["catalog_covers"] is False
    assert listed["oas"] == []
    searched = json.loads(tools["search_oa"]("fracciones"))
    assert searched["catalog_covers"] is False
    assert searched["oas"] == []


def test_tipo_desviado_keeps_plan_tipo(workspace: Workspace):
    plan = build_plan(
        objetivo="Evaluar comprensión lectora",
        tipo="evaluacion",
        encargo=Encargo(tipo=ArtifactType.EVALUACION, rumbo="evaluar"),
    )
    assert plan.tipo is ArtifactType.EVALUACION
    draft = ArtifactDraft(
        tipo=ArtifactType.PAUTA,
        titulo="Rúbrica",
        cuerpo_markdown="# Pauta\n\n## Criterios\nx\n## Niveles\ny\n## Descriptores\nz\n"
        + "w" * 800,
        evidencias=[
            Evidence(path="fuentes/cuento-el-condor-y-el-huemul.md", snippet="huemul"),
            Evidence(path="fuentes/notas-curso.md", snippet="OA"),
        ],
    )
    warnings = collect_warnings(
        workspace=workspace,
        encargo=Encargo(tipo=ArtifactType.EVALUACION, rumbo="evaluar", oa="LEN-4B-OA04"),
        plan=plan,
        draft=draft,
    )
    assert "tipo_desviado" in {item.code for item in warnings}
    assert plan.tipo is ArtifactType.EVALUACION


def test_draft_tool_budget_blocks_then_allows_draft(workspace: Workspace):
    ctx, tools = _draft_tools(workspace)
    ctx.reset_tool_budget(DRAFT_TOOL_BUDGET)
    last_ok = None
    for i in range(DRAFT_TOOL_BUDGET + 3):
        last_ok = json.loads(tools["list_sources"]())
    assert last_ok is not None
    assert last_ok.get("error") == "presupuesto_herramientas_agotado"
    assert ctx.budget_exhausted is True
    drafted = json.loads(
        tools["draft_artifact"](
            tipo="guia",
            titulo="Sigue",
            cuerpo_markdown="# Guía\n\n## Propósito\nx\n## Instrucciones\ny\n## Actividades\nz\n## Cierre\nw\n",
        )
    )
    assert drafted["ok"] is True
    assert ctx.pending_draft is not None


def test_parse_payload_json_garbage_is_none():
    assert parse_payload_json("guia", "") is None
    assert parse_payload_json("guia", "no-json") is None
    parsed = parse_payload_json("guia", '{"titulo": "Ficha", "proposito": "Leer"}')
    assert parsed is not None
    assert parsed["titulo"] == "Ficha"


def test_salvage_payload_json():
    blob = """
draft_artifact(
  tipo="guia",
  titulo="Ficha",
  cuerpo_markdown="## Propósito\\nLeer.",
  payload_json="{\\"tipo\\": \\"guia\\", \\"titulo\\": \\"Ficha\\", \\"proposito\\": \\"Leer con cita\\"}"
)
"""
    draft = salvage_draft_from_text(blob)
    assert draft is not None
    assert draft.payload is not None
    assert "cita" in draft.payload.get("proposito", "").lower()
