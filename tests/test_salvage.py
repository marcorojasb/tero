"""Salvage: si el modelo escribe la propuesta como texto, el host la arma igual.

Solo se rescata una ficha con titulares markdown que calcen con el esqueleto de
algún tipo de material, o una llamada `proponer_crear(...)`/`proponer_editar(...)`
filtrada como texto. Una respuesta conversacional larga NO se convierte en
propuesta.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tero.artifacts import missing_section_headings
from tero.gate import write_approved
from tero.salvage import salvage_draft_from_text, salvage_propuesta_from_text
from tero.types import ArtifactType
from tero.workspace import Workspace
from tests.fake_models import TextModel
from tests.support import artifact_paths, open_session

CONVERSACION = (
    "## Qué puedo hacer\n\n"
    "Puedo preparar una planificación con inicio, desarrollo, cierre y evaluación, "
    "o una guía con actividades. También puedo adaptar material para NEE.\n"
    "Cuéntame qué necesitas y lo vemos juntos, sin apuro.\n" + "x" * 300
)

FICHA_CON_TITULARES = (
    "## Inicio\nPregunta del patio.\n\n"
    "## Desarrollo\nLectura del cuento con evidencia.\n\n"
    "## Cierre\nTicket de salida.\n\n"
    "## Evaluación\nFormativa con pauta.\n\n"
    "## Objetivo\nLeer con evidencia.\n\n"
    "## OA\nLEN-4B-OA04\n" + "y" * 200
)

GUIA_EN_PROSA = """
### Guía de autoaprendizaje: Fotosíntesis en la hoja

**Propósito:** Relacionar cloroplasto, luz y gas que sale de la hoja, con evidencia de la carpeta.

## Instrucciones
- Lee solo las fuentes de la carpeta.
- Trabaja en 45 minutos, sin laboratorio.
- Cierra con un ticket de salida de dos líneas.

## Desarrollo
Dibuja la hoja con tres flechas y nombra el proceso de cada una usando el vocabulario.

## Cierre
Escribe dónde ocurre la fotosíntesis en la célula, con evidencia del texto.
"""

EVALUACION_EN_PROSA = """
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


def test_salvage_de_una_llamada_proponer_crear_escrita_como_texto():
    blob = """
Plan registrado. No redactes aún.proponer_crear(
  titulo="Prueba corta: Comprensión lectora - \\"El cóndor y el huemul\\"",
  tipo="evaluacion",
  resumen="Evaluación breve del cuento.",
  vista_previa_markdown=\"\"\"
# Prueba corta
## Selección múltiple
1. ¿Quién preguntó?
a) El huemul
b) El río
\"\"\"
)
"""
    propuesta = salvage_propuesta_from_text(blob)
    assert propuesta is not None
    assert propuesta.accion == "crear"
    assert propuesta.draft.tipo == ArtifactType.EVALUACION
    assert propuesta.draft.titulo
    assert "Selección múltiple" in propuesta.draft.cuerpo_markdown
    assert "huemul" in propuesta.draft.cuerpo_markdown.lower()


def test_salvage_de_una_llamada_proponer_editar_respeta_accion_y_origen(workspace: Workspace):
    origen = workspace.write_artifact(
        "derivados/existente.md", "---\ntitulo: Guía base\n---\n\n# Guía base\n"
    )
    blob = (
        "Voy a adaptar el material.\n"
        'proponer_editar(\n  ruta_origen="derivados/existente.md",\n  accion="adaptar",\n'
        '  tipo="guia",\n  titulo="Guía adaptada",\n  resumen="Con apoyos visuales",\n'
        '  vista_previa_markdown="## Propósito\\nLeer.\\n## Instrucciones\\nx\\n'
        '## Actividades\\ny\\n## Cierre\\nz\\n",\n'
        '  cambios="Apoyos visuales\\nTiempo extra",\n'
        '  notas_nee="Enunciados leídos en voz alta",\n)\n'
    )
    propuesta = salvage_propuesta_from_text(blob)
    assert propuesta is not None
    assert propuesta.accion == "adaptar"
    assert propuesta.origen == "derivados/existente.md"
    assert propuesta.cambios == ["Apoyos visuales", "Tiempo extra"]
    assert propuesta.notas_nee == ["Enunciados leídos en voz alta"]
    assert origen.exists()


def test_una_llamada_sin_accion_pero_con_origen_se_trata_como_edicion(workspace: Workspace):
    workspace.write_artifact("derivados/existente.md", "# Guía base\n")
    blob = (
        'proponer_editar(\n  ruta_origen="derivados/existente.md",\n  tipo="guia",\n'
        '  titulo="Guía nueva",\n  vista_previa_markdown="## Propósito\\nLeer.\\n'
        '## Instrucciones\\nx\\n## Actividades\\ny\\n## Cierre\\nz\\n",\n)\n'
    )
    propuesta = salvage_propuesta_from_text(blob)
    assert propuesta is not None
    assert propuesta.accion == "editar"
    assert propuesta.origen == "derivados/existente.md"


def test_una_respuesta_conversacional_larga_no_se_rescata(workspace: Workspace):
    session = open_session(workspace)
    with patch("tero.session.make_model", return_value=TextModel(CONVERSACION)):
        turn = session.start_turn("Hola, ¿qué puedes hacer?")

    assert session.phase == "idle"
    assert turn.propuesta is None
    assert turn.respuesta.strip()
    assert session.pending_propuesta is None
    assert artifact_paths(workspace) == []
    assert salvage_propuesta_from_text(CONVERSACION) is None


def test_una_ficha_con_titulares_si_se_rescata(workspace: Workspace):
    session = open_session(workspace)
    with patch("tero.session.make_model", return_value=TextModel(FICHA_CON_TITULARES)):
        turn = session.start_turn("Prepara una planificación del cuento.")

    assert session.phase == "esperando_aprobacion"
    assert turn.propuesta is not None
    assert turn.propuesta.draft.tipo is ArtifactType.PLANIFICACION
    assert artifact_paths(workspace) == []
    resultado = session.aprobar()
    assert resultado.path is not None


def test_el_salvage_avisa_con_propuesta_salvaged(workspace: Workspace):
    session = open_session(workspace)
    events: list[dict] = []
    session._downstream = events.append
    blob = (
        'proponer_crear(\n  tipo="guia",\n  titulo="Guía filtrada",\n  resumen="r",\n'
        '  vista_previa_markdown="## Propósito\\nLeer.\\n## Instrucciones\\nx\\n'
        '## Actividades\\ny\\n## Cierre\\nz\\n",\n)\n'
    )
    with patch("tero.session.make_model", return_value=TextModel(blob)):
        turn = session.start_turn("Prepara una guía del cuento.")

    assert turn.propuesta is not None
    codigos = [event["warning"]["code"] for event in events if event["type"] == "warning"]
    assert "propuesta_salvaged" in codigos


def test_missing_section_headings_no_se_deja_enganar_por_prosa():
    prosa = "Puedo armar una planificación con inicio, desarrollo, cierre y evaluación."
    for tipo in ArtifactType:
        assert missing_section_headings(tipo, prosa) == list(missing_section_headings(tipo, ""))
    assert missing_section_headings(ArtifactType.PLANIFICACION, FICHA_CON_TITULARES) == []
    assert missing_section_headings(ArtifactType.GUIA, "# Guía\n\n## Propósito\nLeer.\n")


@pytest.mark.xfail(
    strict=False,
    reason=(
        "BUG host: el salvage de prosa exige titulares para TODAS las secciones (tolera 1). "
        "Una ficha real escrita con `## Ítem 1:` / `**Propósito:**` deja 2–3 secciones sin "
        "titular, así que el host la trata como charla y no la rescata."
    ),
)
@pytest.mark.parametrize(
    ("blob", "tipo"),
    [
        (GUIA_EN_PROSA, ArtifactType.GUIA),
        (EVALUACION_EN_PROSA, ArtifactType.EVALUACION),
    ],
)
def test_las_fichas_reales_escritas_en_prosa_siguen_rescatandose(blob: str, tipo: ArtifactType):
    propuesta = salvage_propuesta_from_text(blob, fallback_tipo=tipo)
    assert propuesta is not None
    assert propuesta.draft.tipo is tipo


@pytest.mark.xfail(
    strict=False,
    reason=(
        "BUG host: `salvage_propuesta_from_text` no valida `ruta_origen`, así que una edición "
        "filtrada como texto puede aprobarse con un `origen:` que no existe en la carpeta "
        "(la tool `proponer_editar` sí lo valida y devuelve origen_no_encontrado)."
    ),
)
def test_una_edicion_rescatada_con_origen_inexistente_no_deberia_escribirse(workspace: Workspace):
    blob = (
        'proponer_editar(\n  ruta_origen="derivados/inventado.md",\n  accion="editar",\n'
        '  tipo="guia",\n  titulo="Guía fantasma",\n  resumen="r",\n'
        '  vista_previa_markdown="## Propósito\\nLeer.\\n## Instrucciones\\nx\\n'
        '## Actividades\\ny\\n## Cierre\\nz\\n",\n)\n'
    )
    propuesta = salvage_propuesta_from_text(blob)
    assert propuesta is not None
    resultado = write_approved(
        workspace=workspace, encargo=open_session(workspace).encargo, propuesta=propuesta
    )
    assert resultado.path is not None
    assert (workspace.root / propuesta.origen).is_file()


def test_salvage_ignora_prosa_sin_forma_de_ficha():
    assert salvage_draft_from_text("Solo un comentario sin herramienta.") is None


def test_salvage_usa_el_blob_json_cuando_la_llamada_esta_incompleta():
    """Qwen imprime `proponer_crear(..., cuerpo_markdown=markdown)` y luego el JSON."""
    blob = """
### Evaluación corta: El cóndor y el huemul

**Instrucciones:** Lee el cuento y responde. Tiempo: 45 minutos.

#### Ítem 1: Selección múltiple (2 puntos)
¿Por qué se ríe el cóndor?
a) Porque el huemul no vuela
b) Porque el río se secó

proponer_crear(tipo="evaluacion", titulo="Evaluación corta", cuerpo_markdown=markdown, payload_json=payload_json)
{
  "titulo": "Evaluación corta: El cóndor y el huemul",
  "tipo": "evaluacion",
  "cuerpo_markdown": "# Evaluación corta\\n\\n## Instrucciones\\nLee el cuento.\\n\\n## Ítems\\n¿Por qué se ríe el cóndor?\\n\\n## Criterios\\nCita el texto.\\n\\n## Puntaje\\n10 puntos.",
  "payload_json": "{\\"items\\": [{\\"tipo_item\\": \\"sm\\", \\"enunciado\\": \\"¿Por qué se ríe el cóndor?\\", \\"opciones\\": [\\"No vuela\\", \\"El río se secó\\"]}]}"
}
"""
    draft = salvage_draft_from_text(blob, fallback_tipo=ArtifactType.EVALUACION)
    assert draft is not None
    assert draft.tipo == ArtifactType.EVALUACION
    assert "cóndor" in draft.titulo.lower()
    assert draft.payload is not None
    items = draft.payload.get("items") or []
    assert items, "payload_json items should survive salvage"
    assert "cóndor" in str(items[0].get("enunciado") or "").lower()


def test_salvage_cae_al_markdown_cuando_no_hay_json():
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

proponer_crear(tipo="evaluacion", titulo="Evaluación corta: Sistemas 2x2", cuerpo_markdown=markdown, payload_json=payload_json)
"""
    draft = salvage_draft_from_text(blob, fallback_tipo=ArtifactType.EVALUACION)
    assert draft is not None
    assert draft.tipo == ArtifactType.EVALUACION
    assert "Sistemas" in draft.titulo
    assert "Selección múltiple" in draft.cuerpo_markdown
    assert "sustitución" in draft.cuerpo_markdown.lower()


def test_salvage_de_un_blob_json_sin_llamada():
    blob = """
Plan registrado. No redactes aún.
{
  "titulo": "Evaluación — Comprensión lectora del cuento",
  "tipo": "evaluacion",
  "cuerpo_markdown": "## Evaluación — Comprensión lectora\\n\\n### Instrucciones\\nLee el cuento.\\n\\n### Ítems\\n**1. Selección múltiple**\\n¿Por qué se ríe el cóndor?\\n\\n### Criterios\\nCita el texto."
}
"""
    draft = salvage_draft_from_text(blob)
    assert draft is not None
    assert draft.tipo == ArtifactType.EVALUACION
    assert "comprensión lectora" in draft.titulo.lower()


def test_salvage_conserva_el_payload_json():
    blob = """
proponer_crear(
  tipo="guia",
  titulo="Ficha",
  vista_previa_markdown="## Propósito\\nLeer.",
  payload_json="{\\"tipo\\": \\"guia\\", \\"titulo\\": \\"Ficha\\", \\"proposito\\": \\"Leer con cita\\"}"
)
"""
    draft = salvage_draft_from_text(blob)
    assert draft is not None
    assert draft.payload is not None
    assert "cita" in draft.payload.get("proposito", "").lower()
