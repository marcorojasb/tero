"""Deterministic LaTeX render from repaired JSON payloads. Optional latexmk PDF."""

from __future__ import annotations

import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

from tero.artifacts import slugify
from tero.config import PACKAGE_ROOT
from tero.errors import TeroError
from tero.latex.schemas import (
    _vf_from_section,
    extract_payload_from_markdown,
    repair_payload,
    validate_payload,
)
from tero.types import ArtifactType

TEMPLATES_ROOT = PACKAGE_ROOT / "templates" / "latex"

_LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(text: str) -> str:
    out: list[str] = []
    for ch in _pdflatex_safe(text):
        out.append(_LATEX_SPECIALS.get(ch, ch))
    return "".join(out)


def _pdflatex_safe(text: str) -> str:
    """NFKC + drop chars pdflatex/inputenc utf8 cannot ingest (e.g. U+202F)."""
    normalized = unicodedata.normalize("NFKC", text or "")
    punct = str.maketrans(
        {
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2013": "-",
            "\u2014": "-",
            "\u2212": "-",
            "\u00d7": "x",
            "\u2026": "...",
        }
    )
    normalized = normalized.translate(punct)
    chars: list[str] = []
    for ch in normalized:
        code = ord(ch)
        if ch in "\n\t" or code == 32:
            chars.append(ch)
        elif code < 32:
            continue
        elif code < 127:
            chars.append(ch)
        elif 0xA1 <= code <= 0xFF:
            chars.append(ch)
        else:
            chars.append(" ")
    return "".join(chars)


def _strip_md_inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def prose_latex(text: str) -> str:
    """Escape model markdown for a template body: paragraphs, lists, quotes. No raw TeX."""
    if not (text or "").strip():
        return ""
    parts: list[str] = []
    in_list = False
    table_rows: list[str] = []

    def flush_table() -> None:
        if table_rows:
            parts.append(_md_table_latex(table_rows))
            table_rows.clear()

    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped in {"---", "***", "___"}:
            continue
        if _looks_md_table_row(stripped):
            if in_list:
                parts.append(r"\end{itemize}")
                in_list = False
            table_rows.append(stripped)
            continue
        flush_table()
        is_bullet = bool(re.match(r"^[-*•]\s+", stripped))
        is_numbered = bool(re.match(r"^\d+[.)]\s+", stripped))
        if is_bullet or is_numbered:
            if not in_list:
                parts.append(r"\begin{itemize}")
                in_list = True
            item = re.sub(r"^[-*•]\s+", "", stripped)
            item = re.sub(r"^\d+[.)]\s+", "", item)
            parts.append(rf"\item {escape_latex(_strip_md_inline(item))}")
            continue
        if in_list:
            parts.append(r"\end{itemize}")
            in_list = False
        if not stripped:
            parts.append(r"\par")
            continue
        if stripped.startswith(">"):
            quote = stripped.lstrip("> ").strip()
            parts.append(r"\begin{quote}")
            parts.append(escape_latex(_strip_md_inline(quote)))
            parts.append(r"\end{quote}")
            continue
        if stripped.startswith("#"):
            title = re.sub(r"^#+\s*", "", stripped)
            parts.append(rf"\textbf{{{escape_latex(_strip_md_inline(title))}}}\par")
            continue
        parts.append(escape_latex(_strip_md_inline(stripped)))
        parts.append(r"\par")
    flush_table()
    if in_list:
        parts.append(r"\end{itemize}")
    return "\n".join(parts)


def _looks_md_table_row(line: str) -> bool:
    if not line.startswith("|") or line.count("|") < 2:
        return False
    return True


def _md_table_latex(rows: list[str]) -> str:
    parsed: list[list[str]] = []
    for row in rows:
        if re.match(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", row):
            continue
        cells = [c.strip() for c in row.strip("|").split("|")]
        if cells:
            parsed.append(cells)
    if not parsed:
        return ""
    width = max(len(r) for r in parsed)
    col = r">{\raggedright\arraybackslash}X"
    spec = "|" + f"{col}|" * width
    lines = [rf"\begin{{tabularx}}{{\textwidth}}{{{spec}}}", r"\hline"]
    for row in parsed:
        padded = row + [""] * (width - len(row))
        lines.append(" & ".join(escape_latex(_strip_md_inline(c)) for c in padded) + r" \\")
        lines.append(r"\hline")
    lines.append(r"\end{tabularx}")
    lines.append(r"\par")
    return "\n".join(lines)


def _fill(template: str, mapping: dict[str, str]) -> str:
    result = template
    # longer keys first so {{oa_texto}} wins over {{oa}}
    for key in sorted(mapping.keys(), key=len, reverse=True):
        result = result.replace("{{" + key + "}}", mapping[key])
    # remove any leftover placeholders
    return re.sub(r"\{\{[a-z0-9_]+\}\}", "", result)


def _real_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        stripped = str(line).strip()
        if not stripped or stripped in {"-", "—", "–", "*", "·"}:
            continue
        out.append(stripped)
    return out


def _itemize(lines: list[str]) -> str:
    cleaned = _real_lines(lines)
    if not cleaned:
        return ""
    return "\n".join(rf"\item {escape_latex(_strip_md_inline(line))}" for line in cleaned)


def _enumerate(lines: list[str]) -> str:
    cleaned = _real_lines(lines)
    if not cleaned:
        return ""
    return "\n".join(rf"\item {escape_latex(_strip_md_inline(line))}" for line in cleaned)


def _tcolor(title: str | None, body: str) -> str:
    if not (body or "").strip():
        return ""
    opts = (
        r"breakable,colback=black!3,colframe=black!45,boxrule=0.5pt,arc=0pt,"
        r"left=8pt,right=8pt,top=5pt,bottom=5pt"
    )
    if title:
        opts += r",fonttitle=\bfseries\small,title=" + escape_latex(title)
    return "\n".join([rf"\begin{{tcolorbox}}[{opts}]", body, r"\end{tcolorbox}"])


def _prose_section(title: str, text: str, *, boxed: bool = False) -> str:
    body = prose_latex(text)
    if not body.strip():
        return ""
    heading = rf"\needspace{{7\baselineskip}}\section*{{{escape_latex(title)}}}"
    if boxed:
        return heading + "\n" + _tcolor(None, body)
    return heading + "\n" + body


def _itemize_section(title: str, lines: list[str]) -> str:
    inner_items = _itemize(lines)
    if not inner_items:
        return ""
    inner = "\n".join([r"\begin{itemize}", inner_items, r"\end{itemize}"])
    return rf"\needspace{{6\baselineskip}}\section*{{{escape_latex(title)}}}" + "\n" + inner


def _enumerate_section(title: str, lines: list[str]) -> str:
    inner_items = _enumerate(lines)
    if not inner_items:
        return ""
    inner = "\n".join([r"\begin{enumerate}", inner_items, r"\end{enumerate}"])
    return rf"\needspace{{6\baselineskip}}\section*{{{escape_latex(title)}}}" + "\n" + inner


def _oa_texto_line(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    return r"{\small\textit{" + escape_latex(cleaned) + r"}}\par"


def _ficha_header(data: dict[str, Any], *, kind: str) -> str:
    """Student ID strip — photocopied-ficha look, not a title page."""
    label = {
        "guia": "guía de trabajo",
        "actividad": "actividad de aula",
        "evaluacion": "prueba / evaluación",
    }.get(kind, "material de aula")
    curso = escape_latex(str(data.get("curso") or "—"))
    asignatura = escape_latex(str(data.get("asignatura") or "—"))
    oa = escape_latex(str(data.get("oa") or "—"))
    tiempo = escape_latex(
        str(data.get("tiempo") or data.get("duracion") or data.get("puntaje_total") or "—")
    )
    tiempo_label = "Puntaje" if kind == "evaluacion" else "Tiempo"
    return "\n".join(
        [
            rf"{{\footnotesize tero · {escape_latex(label)} · el docente decide}}",
            r"\vspace{0.45em}",
            r"\begin{tabularx}{\textwidth}{|X|X|}",
            r"\hline",
            r"\rule{0pt}{3.1ex}Nombre: \hrulefill & Fecha: \hrulefill \\",
            rf"Curso: {curso} & Asignatura: {asignatura} \\",
            rf"OA: {oa} & {escape_latex(tiempo_label)}: {tiempo} \\",
            r"\hline",
            r"\end{tabularx}",
        ]
    )


def _answer_rules(n: int = 3) -> str:
    count = max(1, min(n, 4))
    return "\n".join([r"\par\vspace{0.45em}\noindent\rule{\textwidth}{0.4pt}"] * count)


def _choice_list(opciones: list[str]) -> str:
    if not opciones:
        return r"\hfill\textit{Marco:}\,\fbox{\phantom{XX}}"
    parts = [r"\begin{itemize}[leftmargin=2.2em,itemsep=0.18em,topsep=0.2em]"]
    for idx, opt in enumerate(opciones):
        letter = chr(ord("A") + idx) if idx < 26 else str(idx + 1)
        parts.append(
            rf"\item[\fbox{{\makebox[0.9em]{{\strut {letter}}}}}] "
            + escape_latex(_strip_md_inline(str(opt)))
        )
    parts.append(r"\end{itemize}")
    parts.append(r"\hfill\textit{Marco:}\,\fbox{\phantom{XX}}")
    return "\n".join(parts)


def render_latex(payload: dict[str, Any] | str, *, tipo: str | None = None) -> str:
    """Render a schema payload to LaTeX source (never trusts free-form TeX from the model)."""
    if isinstance(payload, str):
        repaired = repair_payload(tipo or "guia", payload)
    else:
        inferred = str((payload or {}).get("tipo") or tipo or "guia")
        repaired = repair_payload(inferred, payload)
    key = str(repaired.get("tipo") or "guia")
    template_name = {
        "guia": "guia.tex",
        "evaluacion": "evaluacion.tex",
        "planificacion": "planificacion.tex",
        "pauta": "pauta.tex",
        "beamer": "beamer.tex",
        "actividad": "guia.tex",
    }.get(key, "guia.tex")
    path = TEMPLATES_ROOT / template_name
    if not path.exists():
        raise TeroError(f"Plantilla LaTeX ausente: {path}", code="latex_template")
    template = path.read_text(encoding="utf-8")
    errors = validate_payload(key, repaired)
    # soft: still render with placeholders filled; caller may warn
    mapping = _mapping_for(key, repaired)
    if errors:
        mapping["nota_docente"] = escape_latex(
            (repaired.get("nota_docente") or "")
            + (" · " if repaired.get("nota_docente") else "")
            + "aviso host: "
            + "; ".join(errors)
        )
    return _fill(template, mapping)


def _mapping_for(key: str, data: dict[str, Any]) -> dict[str, str]:
    materiales = [str(x) for x in (data.get("materiales") or []) if str(x).strip()]
    instrucciones = [str(x) for x in (data.get("instrucciones") or []) if str(x).strip()]
    sm_items = list(data.get("sm_items") or [])
    vf_items = list(data.get("vf_items") or [])
    desarrollo = _group_desarrollo_prompts(list(data.get("desarrollo_prompts") or []))
    proposito = str(data.get("proposito") or "")
    acts = _usable_actividades(
        list(data.get("actividades") or []),
        proposito=proposito,
        vf_items=vf_items,
    )
    eval_items = list(data.get("items") or [])
    criterios_eval = (
        [
            str(x) if not isinstance(x, dict) else str(x.get("nombre") or x)
            for x in (data.get("criterios") or [])
        ]
        if key == "evaluacion"
        else []
    )
    recursos = [str(x) for x in (data.get("recursos") or []) if str(x).strip()]
    nota_docente = str(data.get("nota_docente") or "")
    lineamientos = str(data.get("lineamientos_nota") or "")
    ficha_kind = "guia" if key == "actividad" else key
    base = {
        "titulo": escape_latex(str(data.get("titulo") or "")),
        "curso": escape_latex(str(data.get("curso") or "—")),
        "asignatura": escape_latex(str(data.get("asignatura") or "—")),
        "oa": escape_latex(str(data.get("oa") or "—")),
        "oa_texto": escape_latex(str(data.get("oa_texto") or "")),
        "oa_texto_line": _oa_texto_line(str(data.get("oa_texto") or "")),
        "tiempo": escape_latex(str(data.get("tiempo") or data.get("duracion") or "—")),
        "duracion": escape_latex(str(data.get("duracion") or data.get("tiempo") or "—")),
        "proposito": prose_latex(proposito),
        "proposito_block": _tcolor("Propósito", prose_latex(proposito)),
        "cierre": prose_latex(str(data.get("cierre") or "")),
        "objetivo": prose_latex(str(data.get("objetivo") or "")),
        "inicio": prose_latex(str(data.get("inicio") or "")),
        "desarrollo": prose_latex(str(data.get("desarrollo") or "")),
        "evaluacion": prose_latex(str(data.get("evaluacion") or "")),
        "puntaje_total": escape_latex(str(data.get("puntaje_total") or "—")),
        "nota_docente": escape_latex(nota_docente),
        "lineamientos_nota": escape_latex(lineamientos),
        "subtitulo": escape_latex(str(data.get("subtitulo") or "")),
        "autor": escape_latex(str(data.get("autor") or "tero")),
        "ficha_header": _ficha_header(data, kind=ficha_kind)
        if ficha_kind in {"guia", "evaluacion", "actividad"}
        else "",
        "materiales_items": _itemize(materiales),
        "instrucciones_items": _enumerate(instrucciones),
        "criterios_items": _itemize(criterios_eval),
        "recursos_items": _itemize(recursos),
        "materiales_section": _itemize_section("Materiales", materiales),
        "instrucciones_section": _enumerate_section("Instrucciones", instrucciones),
        "sm_section": _sm_section(sm_items),
        "vf_section": _vf_section(vf_items),
        "desarrollo_section": _desarrollo_section(desarrollo),
        "actividades_section": _actividades_section(acts),
        "cierre_section": _prose_section("Cierre", str(data.get("cierre") or "")),
        "clave_section": _clave_section(sm_items, vf_items, eval_items),
        "objetivo_section": _prose_section("Objetivo", str(data.get("objetivo") or ""), boxed=True),
        "inicio_section": _prose_section("Inicio", str(data.get("inicio") or "")),
        "desarrollo_plan_section": _prose_section("Desarrollo", str(data.get("desarrollo") or "")),
        "cierre_plan_section": _prose_section("Cierre", str(data.get("cierre") or "")),
        "evaluacion_section": _prose_section("Evaluación", str(data.get("evaluacion") or "")),
        "recursos_section": _itemize_section("Recursos", recursos),
        "items_section": _eval_items_section(eval_items),
        "criterios_section": _itemize_section("Criterios", criterios_eval),
        "nota_docente_section": _prose_section("Nota al docente", nota_docente),
        "sm_block": _sm_block(sm_items),
        "desarrollo_block": _desarrollo_block(desarrollo),
        "actividades_block": _actividades_block(acts),
        "items_block": _eval_items_block(eval_items),
        "niveles_line": escape_latex(" · ".join(str(x) for x in (data.get("niveles") or []))),
        "criterios_block": _pauta_block(list(data.get("criterios") or []))
        if key == "pauta"
        else "",
        "slides_block": _slides_block(list(data.get("slides") or [])),
    }
    return base


def _group_desarrollo_prompts(prompts: list[str]) -> list[str]:
    """Collapse markdown fragments into a few student-facing items."""
    skip = {
        "desarrollo",
        "items de desarrollo",
        "ítems de desarrollo",
        "actividad",
        "actividades",
    }
    cleaned: list[str] = []
    for raw in prompts:
        text = re.sub(r"\s+", " ", str(raw or "")).strip()
        if not text:
            continue
        if text.lower().strip(".:") in skip:
            continue
        cleaned.append(text)
    if len(cleaned) <= 5:
        return cleaned
    grouped: list[str] = []
    buf = ""
    verb = re.compile(
        r"^(resuelve|explica|escribe|justifica|calcula|grafica|verifica|plantea|"
        r"analiza|redacta|completa|compara|interpreta|demuestra)\b",
        re.IGNORECASE,
    )
    for text in cleaned:
        looks_new = text.endswith("?") or len(text) >= 55 or bool(verb.match(text))
        if looks_new:
            if buf:
                grouped.append(buf)
            buf = text
        else:
            buf = f"{buf} {text}".strip() if buf else text
    if buf:
        grouped.append(buf)
    return grouped or cleaned


def _usable_actividades(
    acts: list[dict[str, Any]],
    *,
    proposito: str,
    vf_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    proposito_s = (proposito or "").strip()
    out: list[dict[str, Any]] = []
    for act in acts:
        title = str(act.get("titulo") or "").strip()
        low = title.lower()
        if vf_items and ("falso" in low or "verdadero" in low):
            continue
        inicio = str(act.get("inicio") or "").strip()
        desarrollo = str(act.get("desarrollo") or "").strip()
        cierre = str(act.get("cierre") or "").strip()
        if not (inicio or desarrollo or cierre):
            continue
        if title == "Actividad principal" and desarrollo == proposito_s:
            continue
        if title.lower() == "secuencia" and desarrollo == proposito_s:
            continue
        out.append(act)
    return out


def _sm_section(items: list[dict[str, Any]]) -> str:
    body = _sm_block(items)
    if not body:
        return ""
    return r"\needspace{8\baselineskip}\section*{Selección múltiple}" + "\n" + body


def _vf_section(items: list[dict[str, Any]]) -> str:
    body = _vf_block(items)
    if not body:
        return ""
    return r"\needspace{8\baselineskip}\section*{Verdadero o falso}" + "\n" + body


def _desarrollo_section(prompts: list[str]) -> str:
    body = _desarrollo_block(prompts)
    if not body:
        return ""
    return r"\needspace{8\baselineskip}\section*{Desarrollo}" + "\n" + body


def _actividades_section(acts: list[dict[str, Any]]) -> str:
    body = _actividades_block(acts)
    if not body:
        return ""
    return r"\needspace{8\baselineskip}\section*{Actividades}" + "\n" + body


def _eval_items_section(items: list[dict[str, Any]]) -> str:
    body = _eval_items_block(items)
    if not body:
        return ""
    return r"\needspace{8\baselineskip}\section*{Ítems}" + "\n" + body


def _clave_section(
    sm_items: list[dict[str, Any]],
    vf_items: list[dict[str, Any]],
    eval_items: list[dict[str, Any]] | None = None,
) -> str:
    lines: list[str] = []
    for idx, item in enumerate(sm_items, start=1):
        clave = str(item.get("clave") or "").strip()
        if clave:
            lines.append(f"SM {idx}: {clave}")
    for idx, item in enumerate(vf_items, start=1):
        clave = str(item.get("clave") or "").strip()
        if clave:
            lines.append(f"V/F {idx}: {clave}")
    for idx, item in enumerate(eval_items or [], start=1):
        clave = str(item.get("clave") or "").strip()
        if clave:
            kind = str(item.get("tipo_item") or "ítem")
            lines.append(f"{kind} {idx}: {clave}")
    if not lines:
        return ""
    inner = r"\begin{itemize}" + "\n" + _itemize(lines) + "\n" + r"\end{itemize}"
    return "\n".join(
        [
            r"\newpage",
            r"\needspace{8\baselineskip}",
            _tcolor("Clave docente (no fotocopiar al curso)", inner),
        ]
    )


def _sm_block(items: list[dict[str, Any]]) -> str:
    if not items:
        return ""
    parts: list[str] = [r"\begin{enumerate}"]
    for item in items:
        parts.append(rf"\item {escape_latex(_strip_md_inline(str(item.get('enunciado') or '')))}")
        parts.append(_choice_list(list(item.get("opciones") or [])))
    parts.append(r"\end{enumerate}")
    return "\n".join(parts)


def _vf_block(items: list[dict[str, Any]]) -> str:
    if not items:
        return ""
    parts: list[str] = [r"\begin{enumerate}"]
    for item in items:
        parts.append(rf"\item {escape_latex(_strip_md_inline(str(item.get('enunciado') or '')))}")
        parts.append(r"\hfill \fbox{\strut V}\;\fbox{\strut F}")
    parts.append(r"\end{enumerate}")
    return "\n".join(parts)


def _desarrollo_block(prompts: list[str]) -> str:
    if not prompts:
        return ""
    parts = [r"\begin{enumerate}"]
    for prompt in prompts:
        n_rules = 3 if len(prompt) >= 80 else 2
        parts.append(rf"\item {escape_latex(_strip_md_inline(prompt))}")
        parts.append(_answer_rules(n_rules))
    parts.append(r"\end{enumerate}")
    return "\n".join(parts)


def _actividades_block(acts: list[dict[str, Any]]) -> str:
    if not acts:
        return ""
    parts: list[str] = []
    for act in acts:
        title = str(act.get("titulo") or "Actividad")
        low = title.lower()
        parts.append(rf"\subsection*{{{escape_latex(title)}}}")
        if "falso" in low or "verdadero" in low:
            vf = _vf_from_section(str(act.get("desarrollo") or ""))
            if vf:
                parts.append(_vf_block(vf))
                continue
        if act.get("inicio"):
            parts.append(r"\textbf{Inicio.}")
            parts.append(prose_latex(str(act["inicio"])))
        if act.get("desarrollo"):
            parts.append(r"\textbf{Desarrollo.}")
            parts.append(prose_latex(str(act["desarrollo"])))
        if act.get("cierre"):
            parts.append(r"\textbf{Cierre.}")
            parts.append(prose_latex(str(act["cierre"])))
    return "\n\n".join(parts)


def _eval_items_block(items: list[dict[str, Any]]) -> str:
    if not items:
        return ""
    parts = [r"\begin{enumerate}"]
    for item in items:
        pts = str(item.get("puntaje") or "").strip()
        suffix = f" ({escape_latex(pts)} pts)" if pts else ""
        kind = str(item.get("tipo_item") or "ítem").strip().lower()
        parts.append(
            rf"\item {escape_latex(_strip_md_inline(str(item.get('enunciado') or '')))}{suffix}"
        )
        opciones = list(item.get("opciones") or [])
        if kind in {"sm", "seleccion", "selección"} or (
            opciones and kind not in {"vf", "verdadero"}
        ):
            parts.append(_choice_list(opciones))
        elif kind in {"vf", "verdadero", "falso", "verdadero/falso"}:
            parts.append(r"\hfill \fbox{\strut V}\;\fbox{\strut F}")
        else:
            parts.append(_answer_rules(3 if len(str(item.get("enunciado") or "")) >= 80 else 2))
    parts.append(r"\end{enumerate}")
    return "\n".join(parts)


def _pauta_block(criterios: list[dict[str, Any]]) -> str:
    if not criterios:
        return r"\emph{(sin criterios)}"
    parts: list[str] = []
    for row in criterios:
        if isinstance(row, str):
            parts.append(rf"\subsection*{{{escape_latex(row)}}}")
            continue
        parts.append(rf"\subsection*{{{escape_latex(str(row.get('nombre') or ''))}}}")
        desc = list(row.get("descriptores") or [])
        if desc:
            parts.append(r"\begin{itemize}")
            for d in desc:
                parts.append(rf"\item {escape_latex(str(d))}")
            parts.append(r"\end{itemize}")
    return "\n".join(parts)


def _slides_block(slides: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for slide in slides:
        parts.append(r"\begin{frame}{" + escape_latex(str(slide.get("titulo") or "")) + "}")
        bullets = list(slide.get("bullets") or [])
        if bullets:
            parts.append(r"\begin{itemize}")
            for b in bullets:
                parts.append(rf"\item {escape_latex(str(b))}")
            parts.append(r"\end{itemize}")
        parts.append(r"\end{frame}")
    return "\n".join(parts) if parts else "% (sin slides)"


def export_latex(
    source: Path,
    dest: Path,
    *,
    tipo: str | None = None,
    payload: dict[str, Any] | None = None,
    try_pdf: bool = False,
) -> Path:
    """Write .tex next to an accepted/borrador markdown (or from explicit payload)."""
    if not source.exists() and payload is None:
        raise TeroError(f"No hay artefacto para exportar: {source}", code="export_missing")
    meta: dict[str, str] = {}
    body = ""
    if source.exists():
        body = source.read_text(encoding="utf-8")
        for key in ("tipo", "titulo", "curso", "asignatura", "oa", "duracion"):
            # parse front matter lightly
            from tero.latex.schemas import _front_matter_value

            value = _front_matter_value(body, key)
            if value:
                meta[key] = value
    art_tipo = tipo or meta.get("tipo") or ""
    if payload is not None:
        data = repair_payload(art_tipo or str(payload.get("tipo") or "guia"), payload)
    else:
        data = extract_payload_from_markdown(body, tipo=art_tipo or None, meta=meta)
    tex = render_latex(data, tipo=str(data.get("tipo") or art_tipo or "guia"))
    dest = Path(dest)
    if dest.suffix.lower() != ".tex":
        dest = dest.with_suffix(".tex")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(tex, encoding="utf-8")
    if try_pdf:
        compile_pdf(dest)
    return dest


def write_latex_artifact(
    folder: Path,
    payload: dict[str, Any],
    *,
    try_pdf: bool = False,
) -> Path:
    """Write a .tex under borradores/ or derivados/ from a schema payload."""
    data = repair_payload(str(payload.get("tipo") or "guia"), payload)
    titulo = str(data.get("titulo") or "artefacto")
    tipo = str(data.get("tipo") or "guia")
    name = f"{slugify(tipo)}-{slugify(titulo)[:40]}.tex"
    dest = Path(folder) / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_latex(data), encoding="utf-8")
    if try_pdf:
        compile_pdf(dest)
    return dest


def compile_pdf(tex_path: Path) -> Path | None:
    """Optional PDF via latexmk without shell-escape. Returns pdf path or None."""
    tex_path = Path(tex_path)
    if not tex_path.exists():
        return None
    latexmk = shutil.which("latexmk")
    if not latexmk:
        return None
    cmd = [
        latexmk,
        "-pdf",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-no-shell-escape",
        tex_path.name,
    ]
    try:
        subprocess.run(
            cmd,
            cwd=str(tex_path.parent),
            check=False,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    pdf = tex_path.with_suffix(".pdf")
    return pdf if pdf.exists() else None


def tipo_from_artifact(tipo: ArtifactType | str | None) -> str:
    if isinstance(tipo, ArtifactType):
        return tipo.value
    parsed = ArtifactType.parse(str(tipo) if tipo else None)
    return parsed.value if parsed else "guia"
