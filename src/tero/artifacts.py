"""Artifact types, required structure, and write paths under derivados/."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence, Plan
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
    return f"{when}-{SLUG_TYPE[tipo]}-{slugify(titulo)[:48]}.md"


def render_front_matter(encargo: Encargo, plan: Plan | None, draft: ArtifactDraft) -> str:
    lines = [
        "---",
        "generado_por: tero",
        f"tipo: {draft.tipo.value}",
        f"titulo: {draft.titulo}",
    ]
    if encargo.curso:
        lines.append(f"curso: {encargo.curso}")
    if encargo.asignatura:
        lines.append(f"asignatura: {encargo.asignatura}")
    oa = plan.oa if plan and plan.oa else encargo.oa
    if oa:
        lines.append(f"oa: {oa}")
    duracion = plan.duracion if plan and plan.duracion else encargo.duracion
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
        lines.append(f"- `{item.path}`{where}")
        snippet = item.snippet.strip().replace("\n", " ")
        if snippet:
            lines.append(f"  > {snippet[:280]}")
    lines.append("")
    return "\n".join(lines)


def materialize_markdown(
    encargo: Encargo,
    plan: Plan | None,
    draft: ArtifactDraft,
) -> str:
    body = draft.cuerpo_markdown.strip() + "\n"
    return (
        render_front_matter(encargo, plan, draft)
        + body
        + render_evidence_appendix(draft.evidencias)
    )


def write_accepted(workspace: Workspace, relative_name: str, markdown: str) -> Path:
    return workspace.write_artifact(f"derivados/{relative_name}", markdown)


def write_draft(workspace: Workspace, relative_name: str, markdown: str) -> Path:
    return workspace.write_artifact(f"borradores/{relative_name}", markdown)
