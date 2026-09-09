"""Deterministic Spanish classroom content for the offline / Devpost path."""

from __future__ import annotations

from tero.types import ArtifactType, Encargo


def infer_tipo(prompt: str, encargo: Encargo) -> ArtifactType:
    if encargo.tipo:
        return encargo.tipo
    return ArtifactType.parse(prompt) or ArtifactType.PLANIFICACION


def demo_plan(encargo: Encargo, tipo: ArtifactType) -> dict[str, str]:
    oa = encargo.oa or "OA 4"
    duracion = encargo.duracion or "45 min"
    objetivos = {
        ArtifactType.PLANIFICACION: "Leer el cuento y distinguir lo explícito de lo implícito en el valle.",
        ArtifactType.GUIA: "Guiar una lectura compartida del cóndor y el huemul con pistas de inferencia.",
        ArtifactType.EVALUACION: "Evaluar comprensión lectora del cuento con ítems mixtos y puntaje claro.",
        ArtifactType.PAUTA: "Pautar niveles de inferencia y evidencia textual para la misma lectura.",
        ArtifactType.ACTIVIDAD: "Jugar a ser huemul: preguntar antes de huir, con evidencia del cuento.",
    }
    return {
        "objetivo": objetivos[tipo],
        "tipo": tipo.value,
        "oa": oa,
        "duracion": duracion,
        "notas": "Material de aula, no de vitrina. Fuentes de la carpeta, no de internet.",
    }


def demo_draft_markdown(encargo: Encargo, tipo: ArtifactType, *, critique: str = "") -> str:
    curso = encargo.curso or "4° básico"
    asignatura = encargo.asignatura or "Lenguaje"
    oa = encargo.oa or "OA 4"
    duracion = encargo.duracion or "45 min"
    note = ""
    if critique:
        note = "\n> Corrección docente incorporada: se refuerza evidencia textual y se baja el tono ornamental.\n"
    builders = {
        ArtifactType.PLANIFICACION: _planificacion,
        ArtifactType.GUIA: _guia,
        ArtifactType.EVALUACION: _evaluacion,
        ArtifactType.PAUTA: _pauta,
        ArtifactType.ACTIVIDAD: _actividad,
    }
    return builders[tipo](curso, asignatura, oa, duracion, note)


def _planificacion(curso: str, asignatura: str, oa: str, duracion: str, note: str) -> str:
    return f"""# Planificación — El cóndor y el huemul
{note}
## Objetivo
Que las y los estudiantes de {curso} extraigan información explícita e implícita del cuento, usando el diálogo del huemul como evidencia — no como adorno.

## OA
{oa} ({asignatura}). Se trabaja comprensión lectora: lo que el texto dice y lo que el texto deja pensar.

## Inicio ({duracion.split()[0] if duracion else "8"} min)
- Mostrar dos imágenes mudas: un cóndor alto y un huemul junto al río seco.
- Pregunta abierta: «¿Quién sabe más del valle? ¿El que vuela o el que pregunta?»
- Anotar en la pizarra: *explícito* / *implícito*.

## Desarrollo
1. Lectura en voz alta del cuento de la carpeta (`fuentes/cuento-el-condor-y-el-huemul.md`).
2. Primera pasada: subrayar lo que **está escrito** (el río bajo, el cóndor que se burla).
3. Segunda pasada: marcar lo que **se infiere** (el valle tiene sed; preguntar es una forma de valentía).
4. En parejas: «El huemul no corrió: preguntó…» — ¿qué habría pasado si corre?

## Cierre
- Tres oraciones en el cuaderno: 1 explícita, 1 implícita, 1 opinión con evidencia.
- Recoger dos oraciones al azar y decidir juntas si son explícitas o implícitas.

## Evaluación
- Formativa: lista de cotejo (participa, cita el cuento, distingue implícito).
- No hay nota numérica hoy. Si se necesita pauta, pedir a tero una pauta/rúbrica aparte.
- Duración total: {duracion}.
"""


def _guia(curso: str, asignatura: str, oa: str, duracion: str, note: str) -> str:
    return f"""# Guía de lectura — El cóndor y el huemul
{note}
## Propósito
{curso}, {asignatura}. Leer con lupa: {oa}. Separar lo que el cuento dice de lo que nosotros completamos.

## Instrucciones
1. Lee el cuento completo en silencio (8 min).
2. No copies internet. Solo la fuente de la carpeta.
3. Responde con oraciones, no con una sola palabra.
4. Tiempo total: {duracion}.

## Actividades
1. **Explícito.** Copia una frase que demuestre que el río está bajo.
2. **Implícito.** ¿Por qué el huemul pregunta en vez de huir? Apoya con una cita.
3. **Vocabulario.** Explica *burlón* y *sed del valle* con tus palabras.
4. **Diálogo.** Reescribe la burla del cóndor en tono respetuoso. ¿Cambia el final?

## Cierre
Comparte con tu pareja una inferencia que **no** esté escrita. Si no puedes señalar el cuento, no vale.
"""


def _evaluacion(curso: str, asignatura: str, oa: str, duracion: str, note: str) -> str:
    return f"""# Evaluación — Comprensión lectora del cuento
{note}
## Instrucciones
{curso} · {asignatura} · {oa} · {duracion}.
Lee el cuento. No uses otras fuentes. Responde en el mismo cuadernillo.

## Ítems
1. (2 pts, selección) El río está bajo. Eso es: a) implícito b) explícito c) opinión.
2. (3 pts) Cita una frase que muestre la burla del cóndor.
3. (3 pts) Infiere: ¿qué habría pasado si el huemul corre? Usa evidencia.
4. (2 pts) Explica con tus palabras la «sed del valle».

## Puntaje
Total: 10 puntos. 6 = suficiente; 8 = destacado.

## Criterios
- Cita textual cuando se pide evidencia.
- Distingue explícito / implícito.
- No inventa hechos que el cuento no sostiene.
- (Pauta breve) 2 = cita + inferencia coherente; 1 = idea sin evidencia; 0 = no aborda.
"""


def _pauta(curso: str, asignatura: str, oa: str, duracion: str, note: str) -> str:
    return f"""# Pauta / rúbrica — Inferencia con evidencia
{note}
Curso {curso}, {asignatura}, {oa}. Uso en {duracion} o en una corrección posterior.

## Criterios
1. Evidencia textual.
2. Inferencia (implícito).
3. Claridad de la respuesta.

## Niveles
- Destacado (3)
- Suficiente (2)
- En desarrollo (1)
- No observado (0)

## Descriptores
| Criterio | 3 | 2 | 1 | 0 |
| --- | --- | --- | --- | --- |
| Evidencia | Cita precisa del cuento | Parafrasea con anclaje | Menciona el cuento sin cita | No hay anclaje |
| Inferencia | Implícito plausible y ligado a la cita | Implícito plausible, vínculo débil | Opinión disfrazada | No infiere |
| Claridad | Oraciones completas, sin adorno vacío | Comprensible | Fragmentario | Ilegible / vacío |
"""


def _actividad(curso: str, asignatura: str, oa: str, duracion: str, note: str) -> str:
    return f"""# Actividad — Preguntar como el huemul
{note}
## Objetivo
{curso}, {asignatura}, {oa}: ensayar la pregunta antes de la huida, con evidencia del cuento. Duración {duracion}.

## Materiales
- Cuento de la carpeta (una copia o lectura en voz alta).
- Tres tarjetas: *explícito*, *implícito*, *opinión*.
- Pizarra.

## Pasos
1. El docente lee el diálogo del cóndor y el huemul.
2. En tríos, un estudiante es cóndor, otro huemul, otro juez de evidencia.
3. El huemul debe responder con una pregunta que el cuento sostenga.
4. El juez levanta la tarjeta correcta.
5. Rotar roles.
6. Cierre: una pregunta nueva que el cuento **no** responde — y por eso no se usa como evidencia.
"""
