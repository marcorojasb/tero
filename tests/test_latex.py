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
    assert r"\begin{tabular" in tex
    assert r"\fbox{" in tex
    assert "clave docente:" not in tex.lower()
    assert "Clave docente" in tex
    assert r"\write18" not in tex or r"\textbackslash{}" in tex
    # Model must not inject raw TeX commands via fields — they get escaped
    evil = repair_payload("guia", {**raw, "proposito": r"\write18{rm -rf /}"})
    safe = render_latex(evil)
    assert r"\write18" not in safe or r"\textbackslash{}" in safe


def test_guia_omits_empty_sections_and_keeps_student_header():
    tex = render_latex(
        {
            "tipo": "guia",
            "titulo": "Ficha corta",
            "curso": "4° básico",
            "asignatura": "Lenguaje",
            "oa": "LEN-4B-OA04",
            "proposito": "Marcar pistas.",
            "sm_items": [
                {
                    "enunciado": "¿Quién preguntó?",
                    "opciones": ["El cóndor", "El huemul", "El río"],
                    "clave": "B",
                }
            ],
            "vf_items": [{"enunciado": "El valle tenía sed.", "clave": "V"}],
            "desarrollo_prompts": ["Escribe una inferencia con cita del cuento."],
        }
    )
    assert "Nombre:" in tex
    assert "Fecha:" in tex
    assert "Selección múltiple" in tex
    assert "Verdadero o falso" in tex
    assert r"\fbox{\strut V}" in tex
    assert "Materiales" not in tex
    assert "sin ítems" not in tex
    assert "(sin " not in tex
    assert tex.count(r"\rule{\textwidth}") >= 2
    # many short fragments collapse (worksheet, not one blank line per markdown line)
    bloated = render_latex(
        {
            "tipo": "guia",
            "titulo": "Ficha",
            "proposito": "Practicar.",
            "desarrollo_prompts": [
                "Resuelve el sistema.",
                "x+y=5",
                "x-y=1",
                "verifica el par",
                "otra pista corta",
                "más texto corto",
                "y otro",
                "Escribe el procedimiento completo con verificación del par ordenado.",
            ],
        }
    )
    assert bloated.count(r"\item ") <= 4


def test_planificacion_omits_empty_evaluacion_section():
    tex = render_latex(
        {
            "tipo": "planificacion",
            "titulo": "Plan valle",
            "curso": "4° básico",
            "objetivo": "Leer el cuento.",
            "inicio": "Activar saberes.",
            "desarrollo": "Lectura compartida.",
            "cierre": "Ticket.",
        }
    )
    assert r"\section*{Objetivo}" in tex
    assert r"\section*{Evaluación}" not in tex
    assert r"\section*{Recursos}" not in tex


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

#### Evaluación ####
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
    assert "Puntaje" in body
    assert "50" not in body  # payload says 5
    # Label is a paragraph, not a left-side caption that shoves the table.
    assert r"el docente decide}\par" in body
    idx_label = body.index("el docente decide")
    idx_table = body.index(r"\begin{tabularx}")
    assert idx_label < idx_table
    assert r"\par" in body[idx_label:idx_table]


def test_ficha_header_table_is_full_width(tmp_path):
    payload = {
        "tipo": "evaluacion",
        "titulo": "Prueba de comprensión lectora: El cóndor y el huemul",
        "curso": "4° básico",
        "asignatura": "Lenguaje y Comunicación",
        "oa": "OA 4 (LEN-4B-OA04)",
        "puntaje_total": "20",
        "items": [
            {
                "tipo_item": "sm",
                "enunciado": "¿Qué observaba el cóndor?",
                "opciones": ["El mar", "El río"],
            }
        ],
    }
    dest = tmp_path / "header.tex"
    export_latex(tmp_path / "missing.md", dest, payload=payload, try_pdf=True)
    body = dest.read_text(encoding="utf-8")
    assert r"el docente decide}\par" in body
    assert r"\noindent\begin{tabularx}{\textwidth}" in body
    assert "Lenguaje y Comunicaci" in body
    pdf = dest.with_suffix(".pdf")
    assert pdf.exists()


def test_evaluacion_header_prefers_puntaje_over_duration(tmp_path):
    payload = {
        "tipo": "evaluacion",
        "titulo": "Sistemas",
        "curso": "1° medio",
        "asignatura": "Matemática",
        "oa": "sistemas 2x2",
        "tiempo": "45 min",
        "duracion": "45 min",
        "puntaje_total": "50",
        "items": [{"tipo_item": "sm", "enunciado": "¿x?", "opciones": ["1", "2"]}],
    }
    dest = tmp_path / "sistemas.tex"
    export_latex(tmp_path / "missing.md", dest, payload=payload)
    body = dest.read_text(encoding="utf-8")
    assert "Puntaje" in body
    assert "50" in body
    # duration must not replace the score in the puntaje slot
    assert "Puntaje}{45" not in body.replace(" ", "")


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
    table = prose_latex(
        "| Término | Definición |\n|---------|------------|\n| Incógnita | Valor x |"
    )
    assert r"\begin{tabular" in table
    assert "Incógnita" in table
    assert "Definición" in table
    assert r"\write18" not in body
    evil = prose_latex(r"\write18{rm -rf /}")
    assert r"\write18" not in evil
    assert r"\textbackslash{}" in evil


def test_extract_guia_emoji_and_roman_item_headings():
    md = """# Guía

## 📌 Propósito
Trabajar sistemas 2×2 solo.

## Actividades

### I. Selección Múltiple
1. ¿Qué es un sistema 2×2?
a) Una ecuación
b) Dos ecuaciones lineales
c) Un gráfico

### II. Verdadero o Falso
- El par (2, 1) siempre sirve.

### III. Desarrollo
- Resuelve y verifica: x+y=5, x-y=1.

## Cierre
Autochequeo del par ordenado.
"""
    payload = extract_payload_from_markdown(md, tipo="guia")
    assert "sistemas 2" in payload["proposito"]
    assert payload["sm_items"]
    assert "sistema 2" in payload["sm_items"][0]["enunciado"].lower()
    vf = [row for row in payload["actividades"] if "falso" in row["titulo"].lower()]
    assert vf
    assert any("verifica" in p.lower() for p in payload["desarrollo_prompts"])
    assert "Autochequeo" in payload["cierre"]
    md_bold = """# Guía
## Propósito
Practicar.
## Selección múltiple
**1.** ¿Qué es un sistema 2×2?
A) Una ecuación
B) Dos ecuaciones lineales
C) Un gráfico
"""
    sm = extract_payload_from_markdown(md_bold, tipo="guia")["sm_items"]
    assert sm
    assert "sistema 2" in sm[0]["enunciado"].lower()
    assert len(sm[0]["opciones"]) == 3


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


def test_plan_payload_empty_fields_fill_from_markdown():
    md = """---
tipo: planificacion
titulo: Agua
curso: 5° básico
---
# Plan

## Objetivo
Explicar la distribución del agua.

## Inicio
Pregunta del patio sobre la lluvia.

## Desarrollo
Lectura de la carpeta y globo terráqueo.

## Cierre
Ticket de salida sin laboratorio.

```json
{"tipo": "planificacion", "titulo": "Agua", "objetivo": "Explicar la distribución del agua.", "inicio": "", "desarrollo": "", "cierre": ""}
```
"""
    payload = extract_payload_from_markdown(md, tipo="planificacion")
    assert "patio" in payload["inicio"].lower()
    assert "globo" in payload["desarrollo"].lower()
    assert "ticket" in payload["cierre"].lower()


def test_plan_nested_dict_becomes_prose():
    from tero.latex.schemas import repair_payload

    payload = repair_payload(
        "planificacion",
        {
            "titulo": "Agua",
            "inicio": {
                "titulo": "Activación",
                "duracion": "15 minutos",
                "actividades": ["Pregunta de apertura", "Foco del OA"],
            },
        },
    )
    assert "Activación" in payload["inicio"]
    assert "{" not in payload["inicio"]
    assert "Pregunta de apertura" in payload["inicio"]


def test_extract_evaluacion_item_i_sm_heading():
    md = """# Evaluación

## Instrucciones
- Lee cada ítem.

## Ítem I: Selección múltiple (10 puntos)
### 1. (3 puntos)
Sistema: x+y=7
A) (3, 4)
B) (4, 3)

## Ítem II: Verdadero o falso
- El sistema 2x+2y=10, x+y=5 tiene infinitas soluciones.
"""
    payload = extract_payload_from_markdown(md, tipo="evaluacion")
    sm = [row for row in payload["items"] if row.get("tipo_item") == "sm"]
    assert sm
    assert any("(3, 4)" in str(row.get("opciones")) for row in sm)
    vf = [row for row in payload["items"] if row.get("tipo_item") == "vf"]
    assert vf


def test_extract_qwen_eval_heading_kinds_without_dumping_evidence():
    md = """---
tipo: evaluacion
titulo: Evaluación cuento
curso: 4° básico
---
# Evaluación

**Instrucciones generales:**

Lee el cuento.

## Ítems de evaluación

### 1. Selección múltiple (2 puntos)

¿Por qué el cóndor le dice al huemul que corra?

a) Porque quiere ayudarlo a encontrar agua.
b) Porque cree que el valle se está secando y ya no es seguro.
c) Porque el huemul lo está molestando con preguntas.
d) Porque el río ha crecido y hay peligro de inundación.

**Respuesta correcta:**

### 2. Verdadero o Falso (2 puntos)

El huemul cree que el río se secó por culpa de alguien.

☐ Verdadero
☐ Falso

**Justifica tu respuesta con una frase del texto:**

### 3. Desarrollo (6 puntos)

¿Qué nos dice el cuento sobre la diferencia entre el cóndor y el huemul?

**Respuesta:**

## Evidencia (fuentes usadas)

- `fuentes/cuento-el-condor-y-el-huemul.md` — sección *Ítem 1 (SM)* · verificada
  > El cóndor, desde una cornisa, se rió.
"""
    payload = extract_payload_from_markdown(md, tipo="evaluacion")
    sm = [row for row in payload["items"] if row.get("tipo_item") == "sm"]
    vf = [row for row in payload["items"] if row.get("tipo_item") == "vf"]
    des = [row for row in payload["items"] if row.get("tipo_item") == "desarrollo"]
    assert sm
    assert "cóndor" in sm[0]["enunciado"].lower() or "corra" in sm[0]["enunciado"].lower()
    assert len(sm[0]["opciones"]) == 4
    assert vf
    assert "huemul" in vf[0]["enunciado"].lower()
    assert "justifica" not in vf[0]["enunciado"].lower()
    assert des
    assert "diferencia" in des[0]["enunciado"].lower()
    blob = " ".join(row["enunciado"] for row in payload["items"]).lower()
    assert "fuentes/" not in blob
    assert "verificada" not in blob


def test_extract_evaluacion_skips_vf_table_and_item_desarrollo_heading():
    md = """# Prueba

## Verdadero o falso
| # | Oración | V o F |
|---|---------|-------|
| 1 | El cóndor se rió del huemul con un tono burlón. | |

## Ítem III: Desarrollo (5 puntos)
¿Por qué el narrador dice que el huemul tenía menos miedo?

## Puntuación
| Ítem | Puntos |
| Desarrollo | 5 puntos |
"""
    payload = extract_payload_from_markdown(md, tipo="evaluacion")
    vf = [row for row in payload["items"] if row.get("tipo_item") == "vf"]
    des = [row for row in payload["items"] if row.get("tipo_item") == "desarrollo"]
    assert vf
    assert any("rió" in row["enunciado"] or "rio" in row["enunciado"].lower() for row in vf)
    blob = " ".join(row["enunciado"] for row in payload["items"]).lower()
    assert "|" not in blob
    assert "puntos" not in blob or des
    assert des
    assert "miedo" in des[0]["enunciado"].lower()


def test_extract_evaluacion_numbered_heading_without_item_i():
    md = """# Prueba

## Instrucciones
- Lee en silencio.

### 1. (3 puntos)
¿Cuál es la solución de x+y=7, x-y=1?
A) (4, 3)
B) (3, 4)

## Verdadero o falso
- Un sistema 2x2 siempre tiene solución única.
"""
    payload = extract_payload_from_markdown(md, tipo="evaluacion")
    sm = [row for row in payload["items"] if row.get("tipo_item") == "sm"]
    assert sm
    assert any("x+y=7" in row.get("enunciado", "") for row in sm)


def test_worksheet_guia_compiles_with_pdflatex(tmp_path):
    from tero.latex.render import compile_pdf, export_latex

    source = tmp_path / "ficha.md"
    source.write_text(
        """---
generado_por: tero
tipo: guia
titulo: Ficha huemul
curso: 4° básico
asignatura: Lenguaje
oa: LEN-4B-OA04
---

# Guía

## Propósito
Practicar inferencias.

## Selección múltiple
1. ¿Quién preguntó al cóndor?
a) El huemul
b) El río
c) La nieve
Clave: A

## Verdadero o falso
- El valle tenía sed.

## Ítems de desarrollo
- Escribe una inferencia con cita.
""",
        encoding="utf-8",
    )
    dest = tmp_path / "ficha.tex"
    export_latex(source, dest, try_pdf=True)
    pdf = dest.with_suffix(".pdf")
    compiled = compile_pdf(dest)
    assert dest.exists()
    text = dest.read_text(encoding="utf-8")
    assert "Nombre:" in text
    assert "sin ítems" not in text
    if compiled is None and not pdf.exists():
        import shutil

        if shutil.which("latexmk"):
            raise AssertionError("latexmk está instalado pero la ficha no compiló")
        return
    assert pdf.exists()


def test_escape_latex_drops_narrow_nbsp_for_pdflatex():
    from tero.latex.render import escape_latex, render_latex

    escaped = escape_latex("Lectura guiada (15\u202fmin)")
    assert "\u202f" not in escaped
    assert "15 min" in escaped
    assert "x-y" in escape_latex("x\u2212y")
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
