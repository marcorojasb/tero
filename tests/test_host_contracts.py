"""Contratos del host: payload_json, catálogo, avisos, presupuesto y materialización."""

from __future__ import annotations

import json

from tero.artifacts import materialize_markdown
from tero.evidence import collect_warnings
from tero.export import export_latex
from tero.latex.schemas import extract_payload_from_markdown, parse_payload_json
from tero.salvage import salvage_draft_from_text
from tero.tools import DRAFT_TOOL_BUDGET, TurnContext, build_tools
from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence, Propuesta
from tero.workspace import Workspace

GUIA_CUERPO = (
    "# Guía\n\n## Propósito\nLeer.\n\n## Instrucciones\nSigue los pasos.\n\n"
    "## Actividades\nUna.\n\n## Cierre\nTicket.\n"
)


def _tools(workspace: Workspace, encargo: Encargo | None = None) -> tuple[TurnContext, dict]:
    ctx = TurnContext(workspace=workspace, encargo=encargo or Encargo(oa="OA 4"))
    return ctx, {tool.tool_name: tool for tool in build_tools(ctx)}


def _propuesta(draft: ArtifactDraft, *, accion: str = "crear", origen: str = "") -> Propuesta:
    return Propuesta(accion=accion, draft=draft, resumen="Prueba", origen=origen)


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


def test_proponer_crear_payload_json_preferred_on_export(workspace: Workspace, tmp_path):
    ctx, tools = _tools(workspace)
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
        tools["proponer_crear"](
            tipo="evaluacion",
            titulo="Prueba huemul",
            resumen="Evaluación breve.",
            vista_previa_markdown="# Corta\n\nSin headings de ítems.\n",
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
    )
    assert result["ok"] is True
    assert result["payload"] is True
    propuesta = ctx.pending_propuesta
    assert propuesta is not None
    assert propuesta.draft.payload is not None
    assert propuesta.draft.payload["items"]

    md = materialize_markdown(Encargo(curso="4° básico"), propuesta)
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
    _ctx, tools = _tools(
        workspace,
        Encargo(curso="1° medio", asignatura="Matemática", oa="sistemas 2x2"),
    )
    listed = json.loads(tools["list_oa"]())
    assert listed["catalog_covers"] is False
    assert listed["oas"] == []
    searched = json.loads(tools["search_oa"]("fracciones"))
    assert searched["catalog_covers"] is False
    assert searched["oas"] == []


def test_proponer_crear_keeps_encargo_chips_over_payload(workspace: Workspace):
    ctx, tools = _tools(
        workspace,
        Encargo(curso="8° básico", asignatura="Ciencias Naturales", oa="conservación de la masa"),
    )
    result = json.loads(
        tools["proponer_crear"](
            tipo="pauta",
            titulo="Pauta lab",
            resumen="Pauta de laboratorio.",
            vista_previa_markdown="# Pauta\n\n## Criterios\n- Evidencia\n## Niveles\n- Logrado\n"
            + "x" * 200,
            payload_json=(
                '{"tipo":"pauta","titulo":"Pauta lab",'
                '"asignatura":"Lenguaje y Comunicación","curso":"4° básico",'
                '"criterios":[{"nombre":"Evidencia"}]}'
            ),
        )
    )
    assert result["ok"] is True
    propuesta = ctx.pending_propuesta
    assert propuesta is not None
    assert propuesta.draft.payload is not None
    assert propuesta.draft.payload["asignatura"] == "Ciencias Naturales"
    assert propuesta.draft.payload["curso"] == "8° básico"


def test_tipo_desviado_avisa_sin_bloquear(workspace: Workspace):
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
        encargo=Encargo(tipo=ArtifactType.EVALUACION, oa="LEN-4B-OA04"),
        draft=draft,
    )
    assert "tipo_desviado" in {item.code for item in warnings}
    assert all(item.blocking is False for item in warnings)


def test_el_presupuesto_bloquea_y_luego_deja_proponer(workspace: Workspace):
    ctx, tools = _tools(workspace)
    ctx.reset_tool_budget(DRAFT_TOOL_BUDGET)
    last_ok = None
    for _ in range(DRAFT_TOOL_BUDGET + 3):
        last_ok = json.loads(tools["list_sources"]())
    assert last_ok is not None
    assert last_ok.get("error") == "presupuesto_herramientas_agotado"
    assert ctx.budget_exhausted is True
    creada = json.loads(
        tools["proponer_crear"](
            tipo="guia",
            titulo="Sigue",
            resumen="r",
            vista_previa_markdown=GUIA_CUERPO,
        )
    )
    assert creada["ok"] is True
    assert ctx.pending_propuesta is not None


def test_la_ultima_oportunidad_de_proponer_es_una_sola_vez(workspace: Workspace):
    ctx, tools = _tools(workspace)
    ctx.reset_tool_budget(DRAFT_TOOL_BUDGET)
    for _ in range(DRAFT_TOOL_BUDGET + 2):
        json.loads(tools["list_sources"]())
    vacia = json.loads(
        tools["proponer_crear"](tipo="", titulo="x", resumen="", vista_previa_markdown="# x\n")
    )
    assert vacia.get("error") == "presupuesto_herramientas_agotado"
    creada = json.loads(
        tools["proponer_crear"](
            tipo="guia", titulo="Sigue", resumen="r", vista_previa_markdown=GUIA_CUERPO
        )
    )
    assert creada["ok"] is True
    otra = json.loads(
        tools["proponer_crear"](
            tipo="guia", titulo="Dos", resumen="r", vista_previa_markdown=GUIA_CUERPO
        )
    )
    assert otra.get("already") is True


def test_proponer_crear_fills_empty_eval_items_from_markdown(workspace: Workspace):
    ctx, tools = _tools(workspace)
    cuerpo = """# Prueba

## Verdadero o falso
- El huemul preguntó por qué el valle tenía sed.

## Ítems de desarrollo
¿Qué se infiere del final del cuento?
"""
    result = json.loads(
        tools["proponer_crear"](
            tipo="evaluacion",
            titulo="Prueba huemul",
            resumen="r",
            vista_previa_markdown=cuerpo,
            payload_json=json.dumps(
                {"tipo": "evaluacion", "titulo": "Prueba huemul", "items": []},
                ensure_ascii=False,
            ),
        )
    )
    assert result["ok"] is True
    propuesta = ctx.pending_propuesta
    assert propuesta is not None
    items = (propuesta.draft.payload or {}).get("items") or []
    assert items
    blob = " ".join(str(row.get("enunciado") or "") for row in items).lower()
    assert "huemul" in blob or "infiere" in blob
    md = materialize_markdown(Encargo(curso="4° básico"), propuesta)
    extracted = extract_payload_from_markdown(md, tipo="evaluacion")
    assert extracted["items"]
    fence = md[md.index("```json") : md.index("```", md.index("```json") + 7)]
    assert '"enunciado"' in fence


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


def test_salvage_fills_empty_eval_items_from_markdown():
    blob = r"""
draft_artifact(
  tipo="evaluacion",
  titulo="Prueba",
  cuerpo_markdown="## Verdadero o falso\n- El cóndor se rió del huemul.\n## Ítems de desarrollo\n¿Por qué el valle tenía sed?\n",
  payload_json="{\"tipo\": \"evaluacion\", \"titulo\": \"Prueba\", \"items\": []}"
)
"""
    draft = salvage_draft_from_text(blob)
    assert draft is not None
    items = (draft.payload or {}).get("items") or []
    assert items
    blob_txt = " ".join(str(row.get("enunciado") or "") for row in items).lower()
    assert "cóndor" in blob_txt or "condor" in blob_txt or "valle" in blob_txt


def test_materialize_fills_empty_plan_moments():
    draft = ArtifactDraft(
        tipo=ArtifactType.PLANIFICACION,
        titulo="Agua",
        cuerpo_markdown=(
            "## Objetivo\nExplicar la distribución del agua.\n\n"
            "## Inicio\nPregunta del patio sobre la lluvia.\n\n"
            "## Desarrollo\nLectura de la carpeta y globo terráqueo.\n\n"
            "## Cierre\nTicket de salida sin laboratorio.\n"
        ),
        payload={
            "tipo": "planificacion",
            "titulo": "Agua",
            "objetivo": "Explicar la distribución del agua.",
            "inicio": "",
            "desarrollo": "",
            "cierre": "",
        },
    )
    propuesta = _propuesta(draft)
    md = materialize_markdown(Encargo(curso="5° básico"), propuesta)
    assert draft.payload is not None
    assert "patio" in draft.payload["inicio"].lower()
    assert "globo" in draft.payload["desarrollo"].lower()
    assert "ticket" in draft.payload["cierre"].lower()
    fence = md[md.index("```json") :]
    assert "patio" in fence.lower()


def test_materialize_deja_el_origen_en_el_front_matter():
    draft = ArtifactDraft(
        tipo=ArtifactType.GUIA,
        titulo="Guía adaptada",
        cuerpo_markdown=GUIA_CUERPO,
    )
    propuesta = _propuesta(draft, accion="adaptar", origen="derivados/base.md")
    md = materialize_markdown(Encargo(curso="4° básico"), propuesta)
    assert "accion: adaptar" in md
    assert "origen: derivados/base.md" in md
