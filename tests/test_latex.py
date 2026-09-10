"""LaTeX: schema repair + deterministic templates (no free-form TeX from the model)."""

from __future__ import annotations

import json

from tero.export import export_latex, render_latex
from tero.latex.schemas import extract_payload_from_markdown, repair_payload, validate_payload


def test_repair_and_render_guia_schema():
    raw = {
        "tipo": "guia",
        "titulo": "Guía de inferencias",
        "curso": "4° básico",
        "asignatura": "Lenguaje",
        "oa": "LEN-4B-OA04",
        "oa_texto": "Extraer información explícita e implícita.",
        "proposito": "Practicar inferencias con evidencia.",
        "materiales": ["cuento", "lápiz"],
        "instrucciones": ["Lee el cuento", "Marca pistas"],
        "sm_items": [
            {
                "enunciado": "¿Por qué el valle tenía sed?",
                "opciones": ["Lluvia", "El huemul preguntó", "Nieve"],
                "clave": "B",
            }
        ],
        "desarrollo_prompts": ["Escribe una inferencia con cita."],
        "actividades": [
            {
                "titulo": "Lectura compartida",
                "inicio": "Activar saberes",
                "desarrollo": "Leer en voz alta",
                "cierre": "Compartir pistas",
            }
        ],
        "cierre": "Ticket de salida",
        "tiempo": "45 min",
    }
    payload = repair_payload("guia", raw)
    assert validate_payload("guia", payload) == []
    tex = render_latex(payload)
    assert r"\documentclass" in tex
    assert "Guía de inferencias" in tex
    assert "LEN-4B-OA04" in tex
    assert r"\begin{tabular}" in tex
    # Model must not inject raw TeX commands via fields — they get escaped
    evil = repair_payload("guia", {**raw, "proposito": r"\write18{rm -rf /}"})
    safe = render_latex(evil)
    assert r"\write18" not in safe or r"\textbackslash{}" in safe


def test_export_latex_from_markdown(tmp_path):
    source = tmp_path / "plan.md"
    source.write_text(
        """---
generado_por: tero
tipo: planificacion
titulo: Plan cuento
curso: 4° básico
asignatura: Lenguaje
oa: LEN-4B-OA04
duracion: 45 min
---

# Planificación

## Objetivo
Leer y distinguir explícito de implícito.

## Inicio
Activar saberes del valle.

## Desarrollo
Lectura compartida y pistas.

## Cierre
Ticket de salida.

## Evaluación
Observación formativa.
""",
        encoding="utf-8",
    )
    dest = tmp_path / "plan.tex"
    path = export_latex(source, dest)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Planificación" in text or "Plan cuento" in text
    assert r"\section*{Objetivo}" in text
    # Regression: grade 4° must not pick up the "5" from "45 min".
    assert "4° básico" in text
    assert "45° básico" not in text


def test_grado_4_survives_markdown_and_schema_to_latex():
    """4° básico + duracion 45 min must not become 45° básico in LaTeX."""
    md = """---
generado_por: tero
tipo: planificacion
titulo: Plan valle
curso: 4° básico
asignatura: Lenguaje
oa: LEN-4B-OA04
duracion: 45 min
---

# Planificación

## Objetivo
Que las y los estudiantes de 4° básico lean el cuento.

## Inicio (45 min)
Activar saberes.
"""
    payload = extract_payload_from_markdown(md, tipo="planificacion")
    assert payload["curso"] == "4° básico"
    assert payload.get("duracion") == "45 min"
    assert "45°" not in payload["curso"]
    assert "Activar saberes" in payload["inicio"]

    filled = repair_payload(
        "planificacion",
        {
            "tipo": "planificacion",
            "titulo": "Plan valle",
            "curso": "4° básico",
            "asignatura": "Lenguaje",
            "oa": "LEN-4B-OA04",
            "duracion": "45 min",
            "objetivo": "Leer",
            "inicio": "Inicio",
            "desarrollo": "Desarrollo",
            "cierre": "Cierre",
        },
    )
    tex = render_latex(filled)
    assert r"\textbf{Curso} & 4° básico" in tex
    assert "45° básico" not in tex


def test_export_latex_from_json_payload(tmp_path):
    payload = {
        "tipo": "evaluacion",
        "titulo": "Prueba corta",
        "curso": "5° básico",
        "asignatura": "Matemática",
        "oa": "MAT-5B-OA04",
        "instrucciones": ["Lee con calma", "Justifica"],
        "items": [
            {"tipo_item": "sm", "enunciado": "1/2 de 8", "puntaje": 2, "opciones": ["2", "4", "8"]},
            {"tipo_item": "desarrollo", "enunciado": "Explica con dibujo", "puntaje": 3},
        ],
        "criterios": ["Procedimiento", "Respuesta"],
        "puntaje_total": 5,
    }
    dest = tmp_path / "eval.tex"
    # source may be missing when payload is provided
    path = export_latex(tmp_path / "missing.md", dest, payload=payload)
    assert path.exists()
    body = path.read_text(encoding="utf-8")
    assert "Prueba corta" in body
    assert "MAT-5B-OA04" in body


def test_extract_json_fence_from_markdown():
    md = """# Borrador

```json
{"tipo": "pauta", "titulo": "Rúbrica inferencia", "criterios": [{"nombre": "Evidencia", "descriptores": ["Cita", "Parafrasea"]}]}
```
"""
    payload = extract_payload_from_markdown(md, tipo="pauta")
    assert payload["tipo"] == "pauta"
    assert payload["titulo"] == "Rúbrica inferencia"
    assert payload["criterios"][0]["nombre"] == "Evidencia"


def test_cli_export_latex_smoke(tmp_path):
    from tero.cli import main

    payload_path = tmp_path / "guia.json"
    payload_path.write_text(
        json.dumps(
            {
                "tipo": "guia",
                "titulo": "Smoke guía",
                "proposito": "Probar JSON→LaTeX",
                "actividades": [{"titulo": "Uno", "desarrollo": "Hacer"}],
                "instrucciones": ["Paso 1"],
                "oa": "LEN-4B-OA04",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out.tex"
    code = main(
        [
            "export",
            str(tmp_path / "noop.md"),
            "--format",
            "latex",
            "--payload",
            str(payload_path),
            "--out",
            str(out),
        ]
    )
    assert code == 0
    assert out.exists()
    assert "Smoke" in out.read_text(encoding="utf-8")


def test_extract_planificacion_heading_aliases_and_h4():
    md = """# Plan

#### Objetivo de aprendizaje
Distinguir explícito de implícito.

## Estructura de la clase

### 1. Inicio (8-10 min)
Preguntar por el cóndor.

### Activación
Parejas de 30 segundos.

### 2. Desarrollo — 25 min
Lectura en voz alta del cuento.

### 3. Cierre (10 min)
Ticket de salida.

## Evaluación formativa
Observación en parejas.

## Materiales
- Copias del cuento
"""
    payload = extract_payload_from_markdown(md, tipo="planificacion")
    assert "Distinguir explícito" in payload["objetivo"]
    assert "cóndor" in payload["inicio"]
    assert "Parejas de 30 segundos" in payload["inicio"]
    assert "Lectura en voz alta" in payload["desarrollo"]
    assert "Ticket de salida" in payload["cierre"]
    assert "Observación" in payload["evaluacion"]
    assert any("cuento" in item.lower() for item in payload["recursos"])


def test_prose_latex_lists_are_host_itemize_not_raw_tex():
    from tero.latex.render import prose_latex

    body = prose_latex("- Copias del cuento\n- Lápices\n\nSíntesis.")
    assert r"\begin{itemize}" in body
    assert r"\item Copias del cuento" in body
    assert r"\write18" not in body
    evil = prose_latex(r"\write18{rm -rf /}")
    assert r"\write18" not in evil
    assert r"\textbackslash{}" in evil


def test_extract_guia_sm_vf_and_desarrollo_sections():
    md = """# Guía de sistemas

## Propósito
Introducir sistemas 2×2 en autoaprendizaje.

## Instrucciones
- Lee el ejemplo resuelto.
- Resuelve sin calculadora.

## Selección múltiple
1. El par (2, 1) es solución de x+y=3, x-y=1.
a) Sí
b) No
c) No se puede saber
Clave: A

## Verdadero o falso
- Un sistema 2×2 siempre tiene una única solución.

## Ítems de desarrollo
- Resuelve por sustitución: x+y=5, x-y=1.

## Cierre
Compara tu par ordenado con el ejemplo de la carpeta.
"""
    payload = extract_payload_from_markdown(md, tipo="guia")
    assert "sistemas 2" in payload["proposito"]
    assert payload["sm_items"]
    assert "solución" in payload["sm_items"][0]["enunciado"].lower()
    assert len(payload["sm_items"][0]["opciones"]) == 3
    vf = [row for row in payload["actividades"] if "falso" in row["titulo"].lower()]
    assert vf
    assert any("sustitución" in p or "sustitucion" in p for p in payload["desarrollo_prompts"])
    assert "par ordenado" in payload["cierre"]


def test_escape_latex_drops_narrow_nbsp_for_pdflatex():
    from tero.latex.render import escape_latex, render_latex

    escaped = escape_latex("Lectura guiada (15\u202fmin)")
    assert "\u202f" not in escaped
    assert "15 min" in escaped
    tex = render_latex(
        {
            "tipo": "planificacion",
            "titulo": "Plan",
            "objetivo": "Leer",
            "inicio": "15\u202fmin",
            "desarrollo": "Práctica",
            "cierre": "Ticket",
        }
    )
    assert "\u202f" not in tex
    assert "15 min" in tex
