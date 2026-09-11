"""Artifact types, required structure, and write paths under derivados/."""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tero.errors import WorkspaceError
from tero.types import ArtifactType, Encargo, Evidence, Propuesta
from tero.workspace import Workspace

REQUIRED_HEADINGS: dict[ArtifactType, tuple[str, ...]] = {
    ArtifactType.PLANIFICACION: (
        "objetivo",
        "oa",
        "inicio",
        "desarrollo",
        "cierre",
        "evaluación",
    ),
    ArtifactType.GUIA: ("propósito", "instrucciones", "actividades", "cierre"),
    ArtifactType.EVALUACION: ("instrucciones", "ítems", "puntaje", "criterios"),
    ArtifactType.PAUTA: ("criterios", "niveles", "descriptores"),
    ArtifactType.ACTIVIDAD: ("objetivo", "materiales", "pasos"),
}

SLUG_TYPE = {
    ArtifactType.PLANIFICACION: "planificacion",
    ArtifactType.GUIA: "guia",
    ArtifactType.EVALUACION: "evaluacion",
    ArtifactType.PAUTA: "pauta",
    ArtifactType.ACTIVIDAD: "actividad",
}


def required_headings(tipo: ArtifactType) -> tuple[str, ...]:
    return REQUIRED_HEADINGS[tipo]


def missing_headings(tipo: ArtifactType, markdown: str) -> list[str]:
    lowered = markdown.lower()
    missing: list[str] = []
    for heading in REQUIRED_HEADINGS[tipo]:
        variants = _heading_variants(heading)
        if not any(variant in lowered for variant in variants):
            missing.append(heading)
    return missing


def missing_section_headings(tipo: ArtifactType, markdown: str) -> list[str]:
    """Como `missing_headings`, pero solo mira titulares markdown.

    `missing_headings` busca substrings en todo el texto, así que una respuesta
    conversacional que *menciona* "inicio, desarrollo y cierre" parecería una ficha.
    Aquí solo cuentan los titulares reales.
    """
    heads = [
        match.group(1).strip().lower()
        for match in re.finditer(r"^#{1,6}\s+(.+)$", markdown, flags=re.MULTILINE)
    ]
    blob = " | ".join(heads)
    missing: list[str] = []
    for heading in REQUIRED_HEADINGS[tipo]:
        if not any(variant in blob for variant in _heading_variants(heading)):
            missing.append(heading)
    return missing


def _heading_variants(heading: str) -> tuple[str, ...]:
    aliases = {
        "objetivo": ("objetivo", "objetivos"),
        "oa": ("oa", "objetivo de aprendizaje", "objetivo de aprendizajes"),
        "inicio": ("inicio",),
        "desarrollo": ("desarrollo",),
        "cierre": ("cierre",),
        "evaluación": ("evaluación", "evaluacion"),
        "propósito": ("propósito", "proposito", "purpose"),
        "instrucciones": ("instrucciones",),
        "actividades": ("actividades", "actividad"),
        "ítems": ("ítems", "items", "preguntas"),
        "puntaje": ("puntaje", "puntaje total", "puntos"),
        "criterios": ("criterios", "criterio"),
        "niveles": ("niveles", "nivel"),
        "descriptores": ("descriptores", "descriptor"),
        "materiales": ("materiales", "recursos"),
        "pasos": ("pasos", "secuencia"),
    }
    return aliases.get(heading, (heading,))


def slugify(text: str) -> str:
    ascii_map = (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
        ("ñ", "n"),
        ("ü", "u"),
    )
    value = text.strip().lower()
    for src, dst in ascii_map:
        value = value.replace(src, dst)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "artefacto"


def artifact_filename(tipo: ArtifactType, titulo: str, *, stamp: str | None = None) -> str:
    when = stamp or datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"{when}-{SLUG_TYPE[tipo]}-{slugify(titulo)[:48]}-{uuid.uuid4().hex[:6]}.md"


def _unique_under(workspace: Workspace, folder: str, relative_name: str) -> str:
    candidate = f"{folder}/{relative_name}"
    if not (workspace.root / candidate).exists():
        return candidate
    stem = Path(relative_name).stem
    suffix = Path(relative_name).suffix or ".md"
    for _ in range(12):
        alt = f"{folder}/{stem}-{uuid.uuid4().hex[:4]}{suffix}"
        if not (workspace.root / alt).exists():
            return alt
    raise WorkspaceError(f"No pude elegir un nombre libre en {folder}/")


def render_front_matter(encargo: Encargo, propuesta: Propuesta) -> str:
    draft = propuesta.draft
    payload = draft.payload or {}
    lines = [
        "---",
        "generado_por: tero",
        f"tipo: {draft.tipo.value}",
        f"titulo: {draft.titulo}",
        f"accion: {propuesta.accion}",
    ]
    if propuesta.origen:
        lines.append(f"origen: {propuesta.origen}")
    if encargo.curso:
        lines.append(f"curso: {encargo.curso}")
    if encargo.asignatura:
        lines.append(f"asignatura: {encargo.asignatura}")
    oa = str(payload.get("oa") or "").strip() or encargo.oa
    if oa:
        lines.append(f"oa: {oa}")
    duracion = (
        str(payload.get("duracion") or payload.get("tiempo") or "").strip() or encargo.duracion
    )
    if duracion:
        lines.append(f"duracion: {duracion}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def render_evidence_appendix(evidencias: list[Evidence]) -> str:
    if not evidencias:
        return ""
    lines = ["", "## Evidencia (fuentes usadas)", ""]
    for item in evidencias:
        where = f" — sección *{item.seccion}*" if item.seccion else ""
        mark = "verificada" if item.verified else "no verificada en el archivo"
        lines.append(f"- `{item.path}`{where} · {mark}")
        snippet = item.snippet.strip().replace("\n", " ")
        if snippet:
            lines.append(f"  > {snippet[:280]}")
    lines.append("")
    return "\n".join(lines)


def render_payload_fence(payload: dict[str, Any] | None) -> str:
    """Host schema JSON so export does not depend on markdown headings."""
    if not payload:
        return ""
    blob = json.dumps(payload, ensure_ascii=False, indent=2)
    return f"\n```json\n{blob}\n```\n"


def materialize_markdown(encargo: Encargo, propuesta: Propuesta) -> str:
    """Markdown final de una propuesta aprobada: front matter + cuerpo + JSON + evidencia."""
    from tero.latex.schemas import enrich_payload_from_markdown

    draft = propuesta.draft
    payload = enrich_payload_from_markdown(draft.tipo.value, draft.payload, draft.cuerpo_markdown)
    from tero.sanitize import scrub_ficha_text, strip_tool_traces_value

    payload = strip_tool_traces_value(payload)
    draft.payload = payload
    body = scrub_ficha_text(draft.cuerpo_markdown).strip() + "\n"
    return (
        render_front_matter(encargo, propuesta)
        + body
        + render_payload_fence(payload)
        + render_evidence_appendix(draft.evidencias)
    )


def write_accepted(workspace: Workspace, relative_name: str, markdown: str) -> Path:
    return workspace.write_artifact(_unique_under(workspace, "derivados", relative_name), markdown)
