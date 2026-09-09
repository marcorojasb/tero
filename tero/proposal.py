"""Deterministic proposal used by the scripted (offline) model."""

from __future__ import annotations

import re
from collections.abc import Mapping

OA_RE = re.compile(r"\bCN\d{2}\s*OA\s*\d+\b", re.IGNORECASE)


def compose_proposal(sources: Mapping[str, str], task: str) -> tuple[str, str, str]:
    """Build a Chilean-flavored lesson proposal from source texts.

    Returns (filename, markdown, citations_str).
    """
    citations = list(sources.keys())
    oa_hits: list[str] = []
    for body in sources.values():
        for match in OA_RE.findall(body):
            compact = re.sub(r"\s+", " ", match).upper()
            if compact not in oa_hits:
                oa_hits.append(compact)

    oa_line = ", ".join(oa_hits) if oa_hits else "No se encontró un código OA explícito en las fuentes."

    snippets = []
    for path, body in sources.items():
        excerpt = " ".join(body.split())[:280]
        snippets.append(f"- `{path}`: {excerpt}…")

    markdown = f"""# Planificación de clase — El agua en Chile

> Propuesta generada por tero. El o la docente decide si se aplica.

## Identificación
- **Asignatura:** Ciencias Naturales
- **Curso:** 5° básico
- **Duración:** 90 minutos
- **Unidad (según fuentes):** El agua y los océanos
- **OA citados en las fuentes:** {oa_line}

## Encargo del o de la docente
{task.strip()}

## Objetivo de la clase
Que las y los estudiantes describan la distribución de agua dulce y salada, reconozcan la escasez relativa de agua dulce y la vinculen con ejemplos de Chile (glaciares, ríos, zona norte y zona austral), usando solo lo que aparece en las fuentes de esta carpeta.

## Secuencia didáctica

### Inicio (15 min)
Activación: ¿dónde hay agua en Chile? Recoger ideas sobre océano, nieve, grifo y desierto.
Anclar con el OA y con el apunte local del o de la docente.

### Desarrollo (55 min)
1. Lectura guiada de la distribución de agua dulce / salada (fuente curricular).
2. Mapa mental Chile: Norte Grande, zona central, glaciares del sur (fuente de contexto local).
3. Mini guía: tres preguntas de evidencia + una acción de cuidado del agua.

### Cierre (20 min)
Ticket de salida: una idea que cambió y una pregunta que queda. El o la docente valida con su criterio, no el agente.

## Evaluación formativa
- Explica con un ejemplo chileno por qué el agua dulce es relativamente escasa.
- Cita un proceso del ciclo del agua nombrado en las fuentes.

## Mini guía de trabajo (estudiantes)
1. Completa: la mayor parte del agua de la Tierra es ______; el agua dulce disponible es ______.
2. Nombra dos reservas de agua dulce presentes en Chile según las fuentes.
3. Propón una acción concreta de cuidado del agua en tu escuela o casa.
4. (Desafío) Relaciona un glaciar o río mencionado en las fuentes con el ciclo del agua.

## Fuentes citadas
Estas secciones se apoyan de forma explícita en los archivos originales. Nada de esto reemplaza tu juicio profesional.

{chr(10).join(snippets)}
"""
    filename = "planificacion-agua-5basico.md"
    citations_str = "; ".join(citations)
    return filename, markdown, citations_str
