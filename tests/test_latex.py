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


def test_export_latex_reads_h4_sections_from_nova_markdown(tmp_path):
    """Nova Lite drafts use #### for body sections; parser must not drop them."""
    source = tmp_path / "plan.md"
    source.write_text(
        """---
generado_por: tero
tipo: planificacion
titulo: Planificación del Cuento
curso: 4° básico
asignatura: Lenguaje y Comunicación
oa: OA 4 (LEN-4B-OA04)
duracion: 45 min
---

# Planificación del Cuento

### Planificación del Cuento

#### Objetivo
Los estudiantes planificarán un cuento breve utilizando la comprensión lectora.

#### Inicio
- Activación y foco del OA en pocos minutos.

#### Desarrollo
- Lectura / práctica con evidencia de la carpeta.

#### Cierre
- Síntesis y chequeo formativo breve.

#### Evaluación
- Los estudiantes presentarán su planificación del cuento.
""",
        encoding="utf-8",
    )
    payload = extract_payload_from_markdown(
        source.read_text(encoding="utf-8"), tipo="planificacion"
    )
    assert "cuento breve" in payload["objetivo"]
    assert "Activación" in payload["inicio"]
    assert "Lectura" in payload["desarrollo"]
    dest = tmp_path / "plan.tex"
    text = export_latex(source, dest).read_text(encoding="utf-8")
    assert "cuento breve" in text
    assert "Activación" in text
    assert r"\section*{Objetivo}" in text


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
