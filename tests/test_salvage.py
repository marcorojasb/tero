"""Recover drafts when the model prints draft_artifact(...) as prose."""

from __future__ import annotations

from tero.salvage import salvage_draft_from_text
from tero.types import ArtifactType


def test_salvage_python_style_tool_call():
    blob = '''
Plan registrado. No redactes aún.draft_artifact(
  titulo="Prueba corta: Comprensión lectora - \\"El cóndor y el huemul\\"",
  tipo="evaluacion",
  cuerpo_markdown="""
# Prueba corta
## Selección múltiple
1. ¿Quién preguntó?
a) El huemul
b) El río
"""
)
'''
    draft = salvage_draft_from_text(blob)
    assert draft is not None
    assert draft.tipo == ArtifactType.EVALUACION
    assert "cóndor" in draft.titulo.lower() or "Prueba corta" in draft.titulo
    assert "Selección múltiple" in draft.cuerpo_markdown
    assert "huemul" in draft.cuerpo_markdown.lower()


def test_salvage_ignores_plain_prose():
    assert salvage_draft_from_text("Solo un comentario sin herramienta.") is None


def test_salvage_propose_plan_python_style():
    from tero.salvage import salvage_plan_from_text
    from tero.types import Encargo

    blob = """
Voy a planificar. propose_plan(
  objetivo="Relacionar la distribución del agua dulce y salada con el entorno",
  tipo="planificacion",
  oa="CIE-5B-OA06",
  duracion="90 min",
  titulo="Agua en la Tierra",
  curso="5° básico",
  asignatura="Ciencias Naturales"
)
"""
    plan = salvage_plan_from_text(
        blob,
        encargo=Encargo(curso="5° básico", tipo=ArtifactType.PLANIFICACION),
    )
    assert plan is not None
    assert plan.tipo == ArtifactType.PLANIFICACION
    assert "agua dulce" in plan.objetivo.lower()
    assert "CIE-5B-OA06" in plan.oa


def test_salvage_identifier_call_uses_json_blob():
    """Qwen prints draft_artifact(..., cuerpo_markdown=markdown) then a JSON object."""
    blob = """
### Evaluación corta: El cóndor y el huemul

**Instrucciones:** Lee el cuento y responde. Tiempo: 45 minutos.
No uses otras fuentes. En desarrollo, cita el texto.

#### Ítem 1: Selección múltiple (2 puntos)
¿Por qué se ríe el cóndor?
a) Porque el huemul no vuela
b) Porque el río se secó

#### Ítem 2: Verdadero o falso (2 puntos)
La niña anota que el huemul tiene menos miedo. ☐ V  ☐ F

#### Ítem 3: Desarrollo (4 puntos)
Cita el cuento para explicar la pregunta del huemul.

draft_artifact(tipo="evaluacion", titulo="Evaluación corta: El cóndor y el huemul", cuerpo_markdown=markdown, payload_json=payload_json, evidencias_json=[...])
{
  "titulo": "Evaluación corta: El cóndor y el huemul",
  "tipo": "evaluacion",
  "cuerpo_markdown": "# Evaluación corta: El cóndor y el huemul\\n\\n## Instrucciones\\nLee el cuento.\\n\\n## Ítem 1: Selección múltiple\\n¿Por qué se ríe el cóndor?\\na) No vuela\\nb) El río se secó\\n\\n## Ítem 2: Verdadero o falso\\nLa niña anota el miedo del huemul.\\n\\n## Ítem 3: Desarrollo\\nCita el cuento.",
  "payload_json": "{\\"items\\": [{\\"tipo_item\\": \\"sm\\", \\"enunciado\\": \\"¿Por qué se ríe el cóndor?\\", \\"opciones\\": [\\"No vuela\\", \\"El río se secó\\"]}]}"
}
"""
    draft = salvage_draft_from_text(blob, fallback_tipo=ArtifactType.EVALUACION)
    assert draft is not None
    assert draft.tipo == ArtifactType.EVALUACION
    assert "cóndor" in draft.titulo.lower()
    assert (
        "Selección múltiple" in draft.cuerpo_markdown
        or "selección múltiple" in draft.cuerpo_markdown.lower()
    )
    assert draft.payload is not None
    items = draft.payload.get("items") or []
    assert items, "payload_json items should survive salvage"
    assert "cóndor" in str(items[0].get("enunciado") or "").lower()


def test_salvage_identifier_call_falls_back_to_markdown():
    """If the JSON blob is missing, take the ficha printed before the call."""
    blob = """
### Evaluación corta: Sistemas 2x2

**Instrucciones generales:**
- Tiempo: 45 minutos.
- En desarrollo, muestra los pasos y verifica ambas ecuaciones.

#### Ítem 1: Selección múltiple (2 puntos)
¿Cuál es la solución del sistema 2x+y=8, x-y=1?
A) (2, 4)
B) (3, 2)

#### Ítem 2: Verdadero o Falso (2 puntos)
Dos rectas paralelas siempre tienen infinitas soluciones.
☐ V  ☐ F

#### Ítem 3: Desarrollo (6 puntos)
Resuelve por sustitución y verifica.

draft_artifact(tipo="evaluacion", titulo="Evaluación corta: Sistemas 2x2", cuerpo_markdown=markdown, payload_json=payload_json)
"""
    draft = salvage_draft_from_text(blob, fallback_tipo=ArtifactType.EVALUACION)
    assert draft is not None
    assert draft.tipo == ArtifactType.EVALUACION
    assert "Sistemas" in draft.titulo
    assert "Selección múltiple" in draft.cuerpo_markdown
    assert "sustitución" in draft.cuerpo_markdown.lower()


def test_salvage_json_blob_without_tool_call():
    blob = """
Plan registrado. No redactes aún.
{
  "titulo": "Evaluación — Comprensión lectora del cuento",
  "tipo": "evaluacion",
  "cuerpo_markdown": "## Evaluación — Comprensión lectora\\n\\n### Instrucciones\\nLee el cuento y responde con evidencia.\\n\\n### Ítems\\n**1. Selección múltiple**\\n¿Por qué se ríe el cóndor?\\na) No vuela\\nb) El río\\n\\n**2. Verdadero o falso**\\nLa niña cree que el huemul es valiente.\\n\\n**3. Desarrollo**\\nCita el cuento."
}
"""
    draft = salvage_draft_from_text(blob)
    assert draft is not None
    assert draft.tipo == ArtifactType.EVALUACION
    assert "comprensión lectora" in draft.titulo.lower()
    assert (
        "Selección múltiple" in draft.cuerpo_markdown
        or "selección múltiple" in draft.cuerpo_markdown.lower()
    )


def test_salvage_plain_markdown_ficha_without_tool():
    blob = """
### Evaluación corta: El cóndor y el huemul

**Instrucciones:** Lee el cuento de la carpeta. Tiempo 45 minutos.
Usa solo evidencia del texto. No inventes datos.

## Ítem 1: Selección múltiple (2 puntos)
¿Qué anotó la niña detrás del maitén?
a) Que el río estaba bajo
b) Que el cóndor tenía hambre

## Ítem 2: Verdadero o falso (2 puntos)
El huemul pregunta por qué el valle tiene sed. ☐ V  ☐ F

## Ítem 3: Desarrollo (4 puntos)
Cita el cuento para explicar la inferencia del miedo del huemul.
"""
    draft = salvage_draft_from_text(blob, fallback_tipo=ArtifactType.EVALUACION)
    assert draft is not None
    assert draft.tipo == ArtifactType.EVALUACION
    assert "cóndor" in draft.titulo.lower() or "Evaluación" in draft.titulo
    assert "Selección múltiple" in draft.cuerpo_markdown
    assert "maitén" in draft.cuerpo_markdown or "maiten" in draft.cuerpo_markdown.lower()


def test_salvage_propose_plan_json_blob():
    from tero.salvage import salvage_plan_from_text
    from tero.types import Encargo

    blob = """
{
  "objetivo": "Evaluar la capacidad de resolver sistemas de ecuaciones lineales 2x2",
  "tipo": "evaluacion",
  "curso": "1° medio",
  "asignatura": "Matemática",
  "tema": "Sistemas de ecuaciones lineales 2x2",
  "duracion": "45 min",
  "oa": "sistemas 2x2",
  "notas": "catalog_covers=false"
}
"""
    plan = salvage_plan_from_text(
        blob,
        encargo=Encargo(curso="1° medio", tipo=ArtifactType.EVALUACION),
    )
    assert plan is not None
    assert plan.tipo == ArtifactType.EVALUACION
    assert "sistemas" in plan.objetivo.lower()
    assert "45" in plan.duracion
