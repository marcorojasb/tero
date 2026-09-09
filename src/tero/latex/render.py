"""Deterministic LaTeX render from repaired JSON payloads. Optional latexmk PDF."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from tero.artifacts import slugify
from tero.config import PACKAGE_ROOT
from tero.errors import TeroError
from tero.latex.schemas import (
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
    for ch in text or "":
        out.append(_LATEX_SPECIALS.get(ch, ch))
    return "".join(out)


def _fill(template: str, mapping: dict[str, str]) -> str:
    result = template
    # longer keys first so {{oa_texto}} wins over {{oa}}
    for key in sorted(mapping.keys(), key=len, reverse=True):
        result = result.replace("{{" + key + "}}", mapping[key])
    # remove any leftover placeholders
    return re.sub(r"\{\{[a-z0-9_]+\}\}", "", result)


def _itemize(lines: list[str]) -> str:
    if not lines:
        return r"\item \emph{(sin ítems)}"
    return "\n".join(rf"\item {escape_latex(line)}" for line in lines)


def _enumerate(lines: list[str]) -> str:
    if not lines:
        return r"\item \emph{(sin instrucciones)}"
    return "\n".join(rf"\item {escape_latex(line)}" for line in lines)


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
    base = {
        "titulo": escape_latex(str(data.get("titulo") or "")),
        "curso": escape_latex(str(data.get("curso") or "—")),
        "asignatura": escape_latex(str(data.get("asignatura") or "—")),
        "oa": escape_latex(str(data.get("oa") or "—")),
        "oa_texto": escape_latex(str(data.get("oa_texto") or "")),
        "tiempo": escape_latex(str(data.get("tiempo") or data.get("duracion") or "—")),
        "duracion": escape_latex(str(data.get("duracion") or data.get("tiempo") or "—")),
        "proposito": escape_latex(str(data.get("proposito") or "")),
        "cierre": escape_latex(str(data.get("cierre") or "")),
        "objetivo": escape_latex(str(data.get("objetivo") or "")),
        "inicio": escape_latex(str(data.get("inicio") or "")),
        "desarrollo": escape_latex(str(data.get("desarrollo") or "")),
        "evaluacion": escape_latex(str(data.get("evaluacion") or "")),
        "puntaje_total": escape_latex(str(data.get("puntaje_total") or "—")),
        "nota_docente": escape_latex(str(data.get("nota_docente") or "")),
        "lineamientos_nota": escape_latex(str(data.get("lineamientos_nota") or "")),
        "subtitulo": escape_latex(str(data.get("subtitulo") or "")),
        "autor": escape_latex(str(data.get("autor") or "tero")),
        "materiales_items": _itemize(list(data.get("materiales") or [])),
        "instrucciones_items": _enumerate(list(data.get("instrucciones") or [])),
        "criterios_items": _itemize(
            [
                str(x) if not isinstance(x, dict) else str(x.get("nombre") or x)
                for x in (data.get("criterios") or [])
            ]
            if key == "evaluacion"
            else []
        ),
        "recursos_items": _itemize(list(data.get("recursos") or [])),
        "sm_block": _sm_block(list(data.get("sm_items") or [])),
        "desarrollo_block": _desarrollo_block(list(data.get("desarrollo_prompts") or [])),
        "actividades_block": _actividades_block(list(data.get("actividades") or [])),
        "items_block": _eval_items_block(list(data.get("items") or [])),
        "niveles_line": escape_latex(" · ".join(str(x) for x in (data.get("niveles") or []))),
        "criterios_block": _pauta_block(list(data.get("criterios") or []))
        if key == "pauta"
        else "",
        "slides_block": _slides_block(list(data.get("slides") or [])),
    }
    return base


def _sm_block(items: list[dict[str, Any]]) -> str:
    if not items:
        return r"\emph{(sin ítems SM en el JSON)}"
    parts: list[str] = [r"\begin{enumerate}"]
    for item in items:
        parts.append(rf"\item {escape_latex(str(item.get('enunciado') or ''))}")
        opciones = list(item.get("opciones") or [])
        if opciones:
            parts.append(r"\begin{itemize}")
            for idx, opt in enumerate(opciones):
                letter = chr(ord("A") + idx) if idx < 26 else str(idx + 1)
                parts.append(rf"\item [{letter}] {escape_latex(str(opt))}")
            parts.append(r"\end{itemize}")
        clave = str(item.get("clave") or "").strip()
        if clave:
            parts.append(rf"\textit{{clave docente: {escape_latex(clave)}}}")
    parts.append(r"\end{enumerate}")
    return "\n".join(parts)


def _desarrollo_block(prompts: list[str]) -> str:
    if not prompts:
        return r"\emph{(sin prompts de desarrollo)}"
    parts = [r"\begin{enumerate}"]
    for prompt in prompts:
        parts.append(rf"\item {escape_latex(prompt)}")
        parts.append(r"\par\vspace{1.2em}\noindent\rule{\textwidth}{0.3pt}")
    parts.append(r"\end{enumerate}")
    return "\n".join(parts)


def _actividades_block(acts: list[dict[str, Any]]) -> str:
    if not acts:
        return r"\emph{(sin actividades)}"
    parts: list[str] = []
    for act in acts:
        parts.append(rf"\subsection*{{{escape_latex(str(act.get('titulo') or 'Actividad'))}}}")
        if act.get("inicio"):
            parts.append(r"\textbf{Inicio. } " + escape_latex(str(act["inicio"])))
        if act.get("desarrollo"):
            parts.append(r"\textbf{Desarrollo. } " + escape_latex(str(act["desarrollo"])))
        if act.get("cierre"):
            parts.append(r"\textbf{Cierre. } " + escape_latex(str(act["cierre"])))
    return "\n\n".join(parts)


def _eval_items_block(items: list[dict[str, Any]]) -> str:
    if not items:
        return r"\emph{(sin ítems)}"
    parts = [r"\begin{enumerate}"]
    for item in items:
        pts = str(item.get("puntaje") or "").strip()
        suffix = f" ({escape_latex(pts)} pts)" if pts else ""
        parts.append(
            rf"\item [{escape_latex(str(item.get('tipo_item') or 'ítem'))}] "
            rf"{escape_latex(str(item.get('enunciado') or ''))}{suffix}"
        )
        opciones = list(item.get("opciones") or [])
        if opciones:
            parts.append(r"\begin{itemize}")
            for idx, opt in enumerate(opciones):
                letter = chr(ord("A") + idx) if idx < 26 else str(idx + 1)
                parts.append(rf"\item [{letter}] {escape_latex(str(opt))}")
            parts.append(r"\end{itemize}")
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
            text=True,
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
