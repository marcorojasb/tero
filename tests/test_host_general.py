"""Host contracts on shapes that are not the demo cuento / loop trio."""

from __future__ import annotations

from tero.latex.schemas import (
    enrich_payload_from_markdown,
    extract_payload_from_markdown,
    repair_payload,
)
from tero.rumbos import domain_mismatch, domain_of_text, infer_asignatura
from tero.salvage import salvage_draft_from_text
from tero.types import ArtifactType


def test_story_animals_are_not_a_lenguaje_domain_cue():
    assert domain_of_text("el huemul del bosque andino") is None
    assert domain_of_text("el cóndor sobre la cornisa") is None
    assert domain_of_text("lectura de un poema en 6° básico") == "lenguaje"
    warn = domain_mismatch(
        "fracciones equivalentes 6° básico matemática",
        "fuentes/bases-oa-lenguaje-4b.md cuento de la carpeta",
    )
    assert warn is not None


def test_domain_cues_are_disciplines_not_fixture_nouns():
    assert domain_of_text("el agua del río en el valle") is None
    assert domain_of_text("laboratorio de fotosíntesis 8° básico") == "ciencias"
    assert domain_of_text("noticia de la semana en 6° básico") == "lenguaje"
    assert domain_of_text("historia de la independencia en 2° medio") == "historia"
    assert infer_asignatura("informe de laboratorio de química") == "Ciencias Naturales"
    assert infer_asignatura("el agua del patio") == ""


def test_extract_plan_momentos_historia():
    md = """# Independencia de Chile — 2° medio

## Objetivo
Relacionar causas internas y externas del proceso independentista.

## Momento inicial (12 min)
Activar con un mapa mudo de 1810. En parejas, marcan puertos y capital.

## Momento central (50 min)
Leen dos fragmentos de la carpeta (cabildo y prensa). Contrastan actores y evidencias.

## Momento de cierre (18 min)
Ticket: una causa interna y una externa, cada una con cita de la fuente local.
"""
    payload = extract_payload_from_markdown(md, tipo="planificacion")
    assert "independentista" in payload["objetivo"].lower()
    assert "mapa mudo" in payload["inicio"].lower()
    assert "cabildo" in payload["desarrollo"].lower()
    assert "Ticket" in payload["cierre"] or "ticket" in payload["cierre"].lower()


def test_extract_plan_apertura_sintesis_ingles():
    md = """# Simple past — 6° básico

## Objetivo
Usar simple past en un relato oral de tres oraciones.

## Apertura (8 min)
Escuchan un audio corto de la carpeta. Anotan tres verbos.

## Desarrollo (30 min)
En parejas arman un mini relato con evidencia del audio, no de la memoria.

## Síntesis (7 min)
Cada pareja lee una oración. El curso marca el verbo en pasado.
"""
    payload = extract_payload_from_markdown(md, tipo="planificacion")
    assert "audio corto" in payload["inicio"].lower()
    assert "mini relato" in payload["desarrollo"].lower()
    assert "verbo en pasado" in payload["cierre"].lower()


def test_repair_plan_momentos_list():
    payload = repair_payload(
        "planificacion",
        {
            "title": "Cabildo de 1810",
            "objective": "Contrastar actores del cabildo con la prensa de la carpeta.",
            "momentos": [
                {
                    "nombre": "Momento inicial",
                    "texto": "Mapa mudo de Santiago en 1810.",
                },
                {
                    "titulo": "Momento central",
                    "detalle": "Leen el acta y marcan quién habla.",
                },
                {
                    "fase": "Cierre",
                    "prosa": "Ticket: un actor y una evidencia.",
                },
            ],
        },
    )
    assert "Cabildo" in payload["titulo"]
    assert "acta" in payload["desarrollo"].lower()
    assert "Mapa mudo" in payload["inicio"]
    assert "Ticket" in payload["cierre"]


def test_repair_eval_english_json_keys():
    payload = repair_payload(
        "evaluacion",
        {
            "tipo": "evaluacion",
            "titulo": "Fracciones equivalentes",
            "items": [
                {
                    "type": "sm",
                    "stem": "¿Cuál fracción es equivalente a 1/2?",
                    "options": [
                        {"label": "A", "text": "2/4"},
                        {"label": "B", "text": "1/3"},
                        {"label": "C", "text": "3/5"},
                    ],
                    "correct": 0,
                    "points": 2,
                },
                {
                    "type": "true_false",
                    "question": "Toda fracción con denominador par es equivalente a 1/2.",
                    "correct": False,
                },
                {
                    "type": "development",
                    "prompt": "Explica con un dibujo por qué 2/4 = 1/2.",
                    "points": 4,
                },
            ],
        },
    )
    assert payload is not None
    kinds = [row["tipo_item"] for row in payload["items"]]
    assert kinds == ["sm", "vf", "desarrollo"]
    sm = payload["items"][0]
    assert "1/2" in sm["enunciado"]
    assert sm["opciones"] == ["2/4", "1/3", "3/5"]
    assert payload["items"][1]["clave"] == "F"


def test_repair_eval_questions_alias_and_nested_payload():
    payload = repair_payload(
        "quiz",
        {
            "data": {
                "title": "Simple past",
                "questions": [
                    {
                        "kind": "mcq",
                        "prompt": "Which sentence is in the simple past?",
                        "choices": ["She walks.", "She walked.", "She walking."],
                        "answer": 1,
                    }
                ],
            }
        },
    )
    assert payload["titulo"] == "Simple past"
    assert payload["items"][0]["tipo_item"] == "sm"
    assert "walked" in payload["items"][0]["opciones"][1]
    assert payload["items"][0]["clave"] == "B"


def test_repair_pauta_and_beamer_aliases():
    pauta = repair_payload(
        "rubric",
        {
            "title": "Informe de laboratorio",
            "levels": ["Inicial", "En proceso", "Logrado"],
            "criteria": [
                {
                    "name": "Evidencia",
                    "descriptors": ["Cita la fuente local.", "Mezcla dato e inferencia."],
                }
            ],
        },
    )
    assert pauta["titulo"] == "Informe de laboratorio"
    assert pauta["criterios"][0]["nombre"] == "Evidencia"
    assert "fuente local" in pauta["criterios"][0]["descriptores"][0]

    slides = repair_payload(
        "slides",
        {
            "title": "Causas internas",
            "slides": [
                {"title": "Cabildo", "points": ["Quién convoca", "Quién registra"]},
            ],
        },
    )
    assert slides["slides"][0]["titulo"] == "Cabildo"
    assert "Quién convoca" in slides["slides"][0]["bullets"]


def test_repair_actividad_activities_alias():
    payload = repair_payload(
        "actividad",
        {
            "title": "Role-play de prensa",
            "purpose": "Contrastar dos voces de la carpeta.",
            "activities": [
                {
                    "title": "Lectura en pares",
                    "start": "Reparte fichas A y B.",
                    "development": "Cada voz lee su fragmento y marca una evidencia.",
                    "close": "Comparten una cita, no un resumen.",
                }
            ],
        },
    )
    assert payload["proposito"].startswith("Contrastar")
    assert payload["actividades"][0]["titulo"] == "Lectura en pares"
    assert "fichas" in payload["actividades"][0]["inicio"]


def test_enrich_fills_empty_opciones_from_markdown():
    md = """# Prueba corta — Fotosíntesis

## Preguntas
1. ¿Dónde ocurre la fotosíntesis en la célula vegetal?
a) En los cloroplastos
b) En la mitocondria
c) En el núcleo solamente

2. ¿Qué gas libera la planta durante el día?
a) Nitrógeno
b) Oxígeno
c) Metano
"""
    payload = enrich_payload_from_markdown(
        "evaluacion",
        {
            "tipo": "evaluacion",
            "titulo": "Fotosíntesis",
            "items": [
                {
                    "tipo_item": "sm",
                    "enunciado": "¿Dónde ocurre la fotosíntesis en la célula vegetal?",
                    "opciones": [],
                },
                {
                    "tipo_item": "sm",
                    "enunciado": "¿Qué gas libera la planta durante el día?",
                    "opciones": [],
                },
            ],
        },
        md,
    )
    assert payload is not None
    assert payload["items"][0]["opciones"]
    assert any("cloroplastos" in opt.lower() for opt in payload["items"][0]["opciones"])
    assert any(
        "oxígeno" in opt.lower() or "oxigeno" in opt.lower()
        for opt in payload["items"][1]["opciones"]
    )


def test_extract_skips_answer_key_block_not_the_prompt():
    md = """# Evaluación — Reacciones químicas

## Ítems
### 1. Selección múltiple
¿Qué se conserva en una reacción química?
a) El color
b) La masa
c) El olor

**Respuesta:**
La masa se conserva. El docente no imprime esto en la hoja del estudiante.

### 2. Desarrollo
¿Por qué conviene registrar los estados de los reactantes?

**Respuesta:** Porque el gas puede escapar del vaso de precipitado.
"""
    payload = extract_payload_from_markdown(md, tipo="evaluacion")
    blob = " ".join(str(row.get("enunciado") or "") for row in payload["items"]).lower()
    assert "conserva" in blob or "reactantes" in blob
    assert "vaso de precipitado" not in blob
    assert "no imprime" not in blob


def test_extract_keeps_short_clave_drops_teacher_prose():
    md = """# Control — Porcentajes 6° básico

## Preguntas
1. ¿Cuánto es el 25% de 80?
a) 10
b) 20
c) 40
Clave: B

2. Explica con un dibujo por qué 50% de 80 es 40.
**Respuesta:** Parte el rectángulo en dos y pinta una mitad.
"""
    payload = extract_payload_from_markdown(md, tipo="evaluacion")
    sm = [row for row in payload["items"] if row.get("tipo_item") == "sm"]
    assert sm
    assert sm[0]["clave"].upper().startswith("B")
    blob = " ".join(str(row.get("enunciado") or "") for row in payload["items"]).lower()
    assert "rectángulo" not in blob and "rectangulo" not in blob


def test_salvage_guia_ciencias_markdown_without_tool_call():
    blob = """
### Guía de autoaprendizaje: Fotosíntesis en la hoja

**Propósito:** Relacionar cloroplasto, luz y gas que sale de la hoja, con evidencia de la carpeta.

## Instrucciones
- Lee solo las fuentes de la carpeta.
- Trabaja en 45 minutos, sin laboratorio.
- Cierra con un ticket de salida de dos líneas.

## Desarrollo
Dibuja la hoja con tres flechas y nombra el proceso de cada una usando el vocabulario de la fuente.

## Cierre
Escribe dónde ocurre la fotosíntesis en la célula, con evidencia del texto.
"""
    draft = salvage_draft_from_text(blob, fallback_tipo=ArtifactType.GUIA)
    assert draft is not None
    assert draft.tipo == ArtifactType.GUIA
    assert "fotosíntesis" in draft.titulo.lower() or "Guía" in draft.titulo
    assert "cloroplasto" in draft.cuerpo_markdown.lower()
    assert "ticket" in draft.cuerpo_markdown.lower()


def test_salvage_pauta_markdown_is_not_swallowed_as_chat():
    blob = """
# Pauta de corrección — Informe de laboratorio

## Criterios
- Usa evidencia de la fuente local (no Wikipedia).
- Distingue dato medido de inferencia.
- Escribe en español de aula, sin relleno.

## Niveles
- Inicial
- En proceso
- Logrado

El docente decide si acepta el borrador. Puntaje orientativo: 12 puntos.
La pauta no reemplaza la hoja del estudiante. Cada criterio pide una cita breve.
"""
    draft = salvage_draft_from_text(blob, fallback_tipo=ArtifactType.PAUTA)
    assert draft is not None
    assert "criterios" in draft.cuerpo_markdown.lower()
    assert "inferencia" in draft.cuerpo_markdown.lower()


def test_repair_guia_nested_cierre_and_items():
    payload = repair_payload(
        "guia",
        {
            "title": "Cabildo",
            "purpose": "Contrastar dos voces de la carpeta.",
            "cierre": {
                "tipo": "ticket_salida",
                "descripcion": "Una cita del acta y una de la prensa.",
            },
            "items": [
                {
                    "type": "sm",
                    "pregunta": "¿Quién queda en el patio?",
                    "opciones": [
                        {"id": "a", "texto": "El vecino"},
                        {"id": "b", "texto": "El escribano"},
                    ],
                    "respuesta_correcta": "a",
                }
            ],
        },
    )
    assert "{" not in payload["cierre"]
    assert "cita del acta" in payload["cierre"].lower()
    assert payload["sm_items"]
    assert "patio" in payload["sm_items"][0]["enunciado"].lower()
    assert "El vecino" in payload["sm_items"][0]["opciones"]


def test_repair_pauta_coalesces_chopped_markdown_lines():
    payload = repair_payload(
        "pauta",
        {
            "title": "Informe",
            "criterios": [
                {"nombre": "Se observan tres dimensiones:"},
                {"nombre": "**Evidencia de la carpeta**"},
                {"nombre": "El informe cita el registro de la carpeta."},
                {"nombre": "*Ejemplo:* el vaso abierto baja."},
                {"nombre": "**Dato vs. inferencia**"},
                {"nombre": "Distingue dato medido de inferencia."},
            ],
        },
    )
    names = [row["nombre"] for row in payload["criterios"]]
    assert names == ["Evidencia de la carpeta", "Dato vs. inferencia"]
    assert "cita el registro" in " ".join(payload["criterios"][0]["descriptores"]).lower()
    blob = " ".join(names).lower()
    assert "ejemplo" not in blob
    assert "**" not in "".join(names)


def test_extract_guia_skips_markdown_table_as_instrucciones():
    md = """# Guía — Simple past

## Propósito
Usar simple past con evidencia del audio de la carpeta.

## Instrucciones
1. Escucha el audio.
2. Completa la tabla:

| Elemento | Acta | Prensa |
|----------|------|--------|
| Lenguaje | | |

3. Entrega el ticket con una cita.
"""
    payload = extract_payload_from_markdown(md, tipo="guia")
    joined = " ".join(payload["instrucciones"]).lower()
    assert "escucha el audio" in joined
    assert "elemento" not in joined
    assert "|" not in joined
