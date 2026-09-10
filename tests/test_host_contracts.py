"""Host contracts: payload_json, catalog_covers, tipo_desviado, draft tool budget."""

from __future__ import annotations

import json

from tero.artifacts import materialize_markdown
from tero.evidence import collect_warnings
from tero.export import export_latex
from tero.latex.schemas import extract_payload_from_markdown, parse_payload_json
from tero.plan import build_plan
from tero.salvage import salvage_draft_from_text
from tero.tools import DRAFT_TOOL_BUDGET, PLAN_TOOL_BUDGET, TurnContext, build_tools
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


def test_last_chance_draft_is_once(workspace: Workspace):
    ctx, tools = _draft_tools(workspace)
    ctx.reset_tool_budget(DRAFT_TOOL_BUDGET)
    for _ in range(DRAFT_TOOL_BUDGET + 2):
        json.loads(tools["list_sources"]())
    empty = json.loads(tools["draft_artifact"](tipo="", titulo="x", cuerpo_markdown="# x\n"))
    assert empty.get("error") == "presupuesto_herramientas_agotado"
    drafted = json.loads(
        tools["draft_artifact"](
            tipo="guia",
            titulo="Sigue",
            cuerpo_markdown="# Guía\n\n## Propósito\nx\n## Instrucciones\ny\n## Actividades\nz\n## Cierre\nw\n",
        )
    )
    assert drafted["ok"] is True
    assert ctx.pending_draft is not None
    again = json.loads(
        tools["draft_artifact"](
            tipo="guia",
            titulo="Dos",
            cuerpo_markdown="# Guía\n\n## Propósito\nx\n## Instrucciones\ny\n## Actividades\nz\n## Cierre\nw\n",
        )
    )
    assert again.get("already") is True


def test_plan_stubs_consume_budget(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {t.tool_name: t for t in build_tools(ctx, phase="plan")}
    ctx.reset_tool_budget(PLAN_TOOL_BUDGET)
    errors: list[str] = []
    for _ in range(PLAN_TOOL_BUDGET + 8):
        row = json.loads(
            tools["draft_artifact"](
                tipo="evaluacion",
                titulo="Temprano",
                cuerpo_markdown="# No aún",
            )
        )
        errors.append(str(row.get("error") or ""))
    assert "fase_plan" in errors
    assert errors.count("presupuesto_herramientas_agotado") >= 3
    assert ctx.budget_exhausted is True
    cite = json.loads(tools["cite_evidence"](path="fuentes/x.md", snippet="agua"))
    assert cite.get("error") == "presupuesto_herramientas_agotado"
    planned = json.loads(
        tools["propose_plan"](
            objetivo="Planificar el agua dulce",
            tipo="planificacion",
            oa="CIE-5B-OA06",
        )
    )
    assert planned.get("ok") is True
    assert ctx.pending_plan is not None


def test_second_draft_artifact_is_noop(workspace: Workspace):
    ctx, tools = _draft_tools(workspace)
    ctx.reset_tool_budget(DRAFT_TOOL_BUDGET)
    first = json.loads(
        tools["draft_artifact"](
            tipo="guia",
            titulo="Uno",
            cuerpo_markdown="# Guía\n\n## Propósito\nx\n## Instrucciones\ny\n## Actividades\nz\n## Cierre\nw\n",
        )
    )
    assert first["ok"] is True
    second = json.loads(
        tools["draft_artifact"](
            tipo="pauta",
            titulo="Dos",
            cuerpo_markdown="# Otra",
        )
    )
    assert second.get("already") is True
    assert ctx.pending_draft is not None
    assert ctx.pending_draft.titulo == "Uno"


def test_plan_phase_exposes_draft_stub(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {t.tool_name: t for t in build_tools(ctx, phase="plan")}
    assert "draft_artifact" in tools
    assert "propose_plan" in tools
    refused = json.loads(
        tools["draft_artifact"](
            tipo="evaluacion",
            titulo="Temprano",
            cuerpo_markdown="# No aún",
        )
    )
    assert refused["ok"] is False
    assert refused["error"] == "fase_plan"


def test_criterios_objects_render_as_prose():
    from tero.latex.schemas import repair_payload

    payload = repair_payload(
        "evaluacion",
        {
            "titulo": "Prueba",
            "criterios": [
                {
                    "id": "c1",
                    "nombre": "Evidencia",
                    "descripcion": "Ancla la inferencia a una cita.",
                }
            ],
        },
    )
    assert payload["criterios"]
    assert "Evidencia" in payload["criterios"][0]
    assert "{" not in payload["criterios"][0]


def test_export_payload_fills_curso_from_front_matter(tmp_path):
    source = tmp_path / "eval.md"
    source.write_text(
        """---
generado_por: tero
tipo: evaluacion
titulo: Prueba
curso: 4° básico
asignatura: Lenguaje
oa: LEN-4B-OA04
---

# Prueba
""",
        encoding="utf-8",
    )
    dest = tmp_path / "eval.tex"
    export_latex(
        source,
        dest,
        tipo="evaluacion",
        payload={"tipo": "evaluacion", "titulo": "Prueba", "items": []},
    )
    tex = dest.read_text(encoding="utf-8")
    assert "4° básico" in tex or "4\\textdegree" in tex or "básico" in tex


def test_parse_payload_json_garbage_is_none():
    assert parse_payload_json("guia", "") is None
    assert parse_payload_json("guia", "no-json") is None
    parsed = parse_payload_json("guia", '{"titulo": "Ficha", "proposito": "Leer"}')
    assert parsed is not None
    assert parsed["titulo"] == "Ficha"


def test_parse_payload_json_rejects_plan_card_dump():
    card = {
        "tipo": "planificacion",
        "titulo": "Plan agua",
        "objetivo": "Describir el agua",
        "inicio": "",
        "desarrollo": "",
        "cierre": "",
        "meta": "Plan de trabajo",
        "resultado_previsto": ["Planificación"],
        "decisiones": {"curso": "5° básico"},
        "como_abordare": [{"titulo": "Inicio", "detalle": "Activación"}],
        "supuestos": [{"id": "s1", "text": "Solo la carpeta"}],
    }
    assert parse_payload_json("planificacion", card) is None
    assert parse_payload_json("evaluacion", card) is None
    eval_ok = parse_payload_json(
        "evaluacion",
        {
            "tipo": "evaluacion",
            "titulo": "Prueba",
            "items": [{"tipo_item": "sm", "enunciado": "¿x+y?", "opciones": ["1", "2"]}],
        },
    )
    assert eval_ok is not None
    assert eval_ok["items"]


def test_repair_evaluacion_lifts_sm_items_and_plain_math():
    from tero.latex.schemas import repair_payload

    payload = repair_payload(
        "evaluacion",
        {
            "tipo": "evaluacion",
            "titulo": "Prueba",
            "items": [],
            "sm_items": [
                {
                    "enunciado": r"sistema \begin{cases} x + y = 7 \\ x - y = 1 \end{cases}",
                    "opciones": [{"id": "A", "texto": "(4, 3)"}, {"id": "B", "texto": "(1, 6)"}],
                }
            ],
            "vf_items": [{"enunciado": "Un sistema 2x2 puede no tener solución."}],
        },
    )
    kinds = [row["tipo_item"] for row in payload["items"]]
    assert "sm" in kinds
    assert "vf" in kinds
    sm = next(row for row in payload["items"] if row["tipo_item"] == "sm")
    assert "begin{cases}" not in sm["enunciado"]
    assert "(4, 3)" in sm["opciones"]


def test_repair_evaluacion_lifts_desarrollo_items_beside_sm():
    from tero.latex.schemas import repair_payload

    payload = repair_payload(
        "evaluacion",
        {
            "tipo": "evaluacion",
            "titulo": "Prueba",
            "items": [
                {"tipo_item": "sm", "enunciado": "¿Quién preguntó?", "opciones": ["El huemul"]}
            ],
            "desarrollo_items": [
                {
                    "enunciado": r"Resuelve \begin{cases} 2x + y = 8 \\ x - y = 2 \end{cases}",
                    "puntos": 6,
                }
            ],
            "vf_items": [
                {
                    "enunciado": "El huemul preguntó al cóndor por qué el valle tenía sed.",
                    "correcta": True,
                }
            ],
            "desarrollo_prompts": [],
        },
    )
    kinds = [row["tipo_item"] for row in payload["items"]]
    assert kinds.count("sm") == 1
    assert "vf" in kinds
    assert "desarrollo" in kinds
    dev = next(row for row in payload["items"] if row["tipo_item"] == "desarrollo")
    assert "begin{cases}" not in dev["enunciado"]
    assert "2x" in dev["enunciado"]
    assert dev["puntaje"] == "6"
    vf = next(row for row in payload["items"] if row["tipo_item"] == "vf")
    assert vf["clave"] == "V"


def test_canonical_tipo_item_seleccion_multiple_and_vf():
    from tero.latex.schemas import repair_payload

    payload = repair_payload(
        "evaluacion",
        {
            "titulo": "Prueba",
            "items": [
                {
                    "tipo_item": "seleccion_multiple",
                    "enunciado": "¿Qué observaba el cóndor?",
                    "opciones": ["El mar", "El río"],
                },
                {
                    "tipo_item": "verdadero_falso",
                    "enunciado": "El huemul no corrió.",
                },
                {"tipo_item": "desarrollo", "enunciado": "Infiere con cita."},
            ],
            "criterios": ["1", "3", "Ancla la inferencia a una cita."],
        },
    )
    kinds = [row["tipo_item"] for row in payload["items"]]
    assert kinds == ["sm", "vf", "desarrollo"]
    assert payload["criterios"] == ["Ancla la inferencia a una cita."]


def test_instrucciones_python_dict_repr():
    from tero.latex.schemas import repair_payload

    payload = repair_payload(
        "evaluacion",
        {
            "titulo": "Prueba",
            "instrucciones": [
                "{'tiempo': '45 minutos', 'materiales': 'lápiz y papel', 'puntaje': '50 puntos'}"
            ],
        },
    )
    joined = " ".join(payload["instrucciones"])
    assert "{" not in joined
    assert "45 minutos" in joined
    assert "lápiz" in joined


def test_catalog_essay_oa_is_dropped():
    from tero.latex.schemas import repair_payload

    payload = repair_payload(
        "evaluacion",
        {
            "titulo": "Prueba",
            "oa": (
                "No disponible en el catálogo Chile para 1° medio; se basa en "
                "fuentes locales (bases curriculares, ejemplos resueltos, vocabulario)."
            ),
        },
    )
    assert payload["oa"] == ""


def test_propose_plan_does_not_echo_card(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=Encargo(oa="OA 4"))
    tools = {t.tool_name: t for t in build_tools(ctx, phase="plan")}
    result = json.loads(
        tools["propose_plan"](
            objetivo="Evaluar sistemas 2x2",
            tipo="evaluacion",
            oa="sistemas 2x2",
            duracion="45 min",
        )
    )
    assert result["ok"] is True
    assert "como_abordare" not in result
    assert result.get("plan") is None or "como_abordare" not in (result.get("plan") or {})
    assert ctx.pending_plan is not None
    assert ctx.pending_plan.objetivo.startswith("Evaluar")


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
