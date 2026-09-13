"""Suite de pruebas para el trío de modelos documentados de Bedrock y Strands SDK.

Verifica de forma determinista y sin red:
1. amazon.nova-lite-v1:0: filtrado de tags <thinking>, citas Begonia y ModelRouter fallback.
2. zai.glm-4.7-flash: orquestación acelerada de herramientas y contrato Decreto 83 NEE.
3. minimax.minimax-m2.5: marcado especial (negritas, números romanos, emojis) y rúbricas.
4. Strands GraphBuilder: compilación y ejecución del grafo multi-agente.
5. StrandsTelemetry: inicialización y observabilidad.
"""

from __future__ import annotations

from unittest.mock import patch

from strands.models import ModelRouter

from tero.config import Settings
from tero.graph import build_tero_graph, run_tero_graph
from tero.latex.schemas import extract_payload_from_markdown, repair_payload
from tero.sanitize import strip_thinking_tags
from tero.session import make_model
from tero.telemetry import get_or_create_telemetry, is_telemetry_active
from tero.types import ArtifactType, Encargo
from tero.workspace import Workspace
from tests.fake_models import TextModel, ToolModel
from tests.support import open_session


# ------------------------------------------------------------------ 1. Nova Lite
def test_nova_lite_thinking_tags_filtered(workspace: Workspace):
    """Nova Lite suele emitir razonamiento interno en <thinking>; debe limpiarse."""
    raw = (
        "<thinking>Analizando fuentes para comprensión lectora 4° básico...</thinking>\n"
        "Hola. Veo el cuento en la carpeta y puedo preparar la guía."
    )
    cleaned = strip_thinking_tags(raw)
    assert "<thinking>" not in cleaned
    assert "</thinking>" not in cleaned
    assert "Hola. Veo el cuento" in cleaned


def test_nova_lite_model_router_fallback():
    """make_model para Nova Lite envuelve en ModelRouter con fallback cross-region."""
    settings = Settings(offline=False, model_id="amazon.nova-lite-v1:0")
    encargo = Encargo(curso="4° básico")
    with patch("strands.models.BedrockModel") as mock_bedrock:
        mock_bedrock.side_effect = lambda model_id, **kw: TextModel(f"model-{model_id}")
        model = make_model(settings, encargo)

    assert isinstance(model, ModelRouter)
    candidates = model._candidates
    assert len(candidates) == 2
    assert getattr(candidates[0].model, "text", "") == "model-amazon.nova-lite-v1:0"
    assert getattr(candidates[1].model, "text", "") == "model-us.amazon.nova-lite-v1:0"


# ------------------------------------------------------------------ 2. GLM 4.7 Flash
def test_glm_flash_decreto_83_nee_compliance(workspace: Workspace):
    """GLM 4.7 Flash produce notas_nee con la taxonomía exacta del Decreto 83/2015."""
    ctx_encargo = Encargo(curso="4° básico", tipo=ArtifactType.GUIA)
    session = open_session(workspace, encargo=ctx_encargo)

    notas_nee_payload = [
        "acceso · tiempo: extensión de 45 a 60 minutos con pausas guiadas",
        "acceso · presentación de la información: tamaño de fuente 14pt y pictogramas de apoyo",
        "acceso · formas de respuesta: permite señalar o respuesta oral con mediador",
    ]

    model = ToolModel(
        "proponer_editar",
        {
            "ruta_origen": "derivados/guia-base.md",
            "accion": "adaptar",
            "tipo": "guia",
            "titulo": "Guía adaptada NEE",
            "resumen": "Adaptación curricular según Decreto 83.",
            "vista_previa_markdown": (
                "# Guía adaptada\n\n## Propósito\nLeer con apoyo.\n\n"
                "## Instrucciones\nSigue los pasos.\n\n## Actividades\nUna.\n\n## Cierre\nTicket."
            ),
            "notas_nee": "\n".join(notas_nee_payload),
        },
    )

    workspace.write_artifact("derivados/guia-base.md", "# Guía base\n")

    with patch("tero.session.make_model", return_value=model):
        turn = session.start_turn("Adapta la guía para NEE con apoyos visuales.")

    assert turn.propuesta is not None
    assert turn.propuesta.accion == "adaptar"
    assert len(turn.propuesta.notas_nee) >= 3
    assert any("tiempo" in nota for nota in turn.propuesta.notas_nee)
    assert any("presentación" in nota for nota in turn.propuesta.notas_nee)


# ------------------------------------------------------------------ 3. MiniMax M2.5
def test_minimax_heading_idiosyncrasies_and_rubrics():
    """MiniMax emite ítems con **1.** en negrita, números romanos y emojis en titulares."""
    markdown = """# Evaluación de Comprensión Lectora

## 📌 Propósito
Evaluar la comprensión inferencial del cuento según Decreto 67.

## Instrucciones
Lee atentamente cada pregunta antes de responder.

### I. Selección Múltiple (4 puntos)
**1.** ¿Qué motivó al queltehue a dar la alarma en el valle?
A) La llegada del zorro
B) La sequía del estero
C) El canto del zorzal

**2.** Según el relato, el huemul se refugia cuando:
A) Hay viento fuerte
B) Siente pasos en el matorral

### II. Desarrollo y Rúbrica Analítica (6 puntos)
Explica la actitud del cóndor frente a la petición del río, citando el texto.

## Criterios de Evaluación
- Nivel Inicial: Menciona al cóndor sin justificación textual.
- Nivel Intermedio: Explica la actitud pero no incluye citas del texto.
- Nivel Avanzado: Analiza la actitud del cóndor e incluye cita textual explícita.
"""
    payload = extract_payload_from_markdown(markdown, tipo="evaluacion")
    assert payload is not None
    assert payload.get("titulo")
    # Los ítems SM deben ser rescatados correctamente en items
    items = payload.get("items") or []
    sm_items = [it for it in items if it.get("tipo_item") == "sm"]
    assert len(sm_items) >= 2
    assert "queltehue" in sm_items[0].get("enunciado", "").lower()
    assert len(sm_items[0].get("opciones", [])) >= 2


def test_minimax_repair_payload_nested_dicts():
    """MiniMax a veces emite diccionarios anidados en criterios; deben convertirse a prosa."""
    raw_payload = {
        "titulo": "Rúbrica de aula",
        "criterios": [
            {
                "criterio": "Inferencia",
                "descripcion": "Deduce causas y consecuencias.",
                "ponderacion": "50%",
            },
            {
                "criterio": "Evidencia",
                "descripcion": "Cita el texto de la carpeta.",
                "ponderacion": "50%",
            },
        ],
    }
    repaired = repair_payload("evaluacion", raw_payload)
    for crit in repaired.get("criterios", []):
        assert isinstance(crit, str)
        assert "{" not in crit
        assert "Inferencia" in crit or "Evidencia" in crit


# ------------------------------------------------------------------ 4. Strands Graph
def test_strands_graph_builder_and_execution(workspace: Workspace):
    """El grafo formal de Strands se construye y ejecuta con éxito."""
    settings = Settings(offline=True)
    encargo = Encargo(curso="4° básico", tipo=ArtifactType.PLANIFICACION)

    graph = build_tero_graph(workspace, settings, encargo, max_node_executions=4)
    assert graph is not None
    assert "pedagogical_drafter" in graph.nodes
    assert "quality_gate_auditor" in graph.nodes

    result, ok = run_tero_graph("Prepara una clase de 45 minutos.", workspace, settings, encargo)
    assert ok is True
    assert result is not None


# ------------------------------------------------------------------ 5. Telemetry
def test_strands_telemetry_initialization():
    """La telemetría de Strands se inicializa sin errores."""
    telemetry = get_or_create_telemetry()
    assert telemetry is not None
    assert is_telemetry_active() is True
