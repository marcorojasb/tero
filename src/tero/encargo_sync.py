"""Sync encargo chips from natural-language prompts and slash edits."""

from __future__ import annotations

from tero.rumbos import (
    Rumbo,
    domain_mismatch,
    infer_asignatura,
    infer_curso,
    infer_rumbo,
    infer_tema,
    infer_tipo_from_text,
    tipo_for_rumbo,
)
from tero.types import Encargo
from tero.workspace import Workspace


def sync_encargo_from_prompt(encargo: Encargo, prompt: str) -> Encargo:
    """Update chips when the teacher changes topic/tipo/curso in free text."""
    rumbo = Rumbo.parse(encargo.rumbo) or infer_rumbo(prompt)
    curso = infer_curso(prompt) or encargo.curso
    asignatura = infer_asignatura(prompt) or encargo.asignatura
    tema = infer_tema(prompt) or encargo.tema
    tipo = infer_tipo_from_text(prompt) or encargo.tipo
    if rumbo and tipo is None:
        tipo = tipo_for_rumbo(rumbo, prompt)
    elif rumbo and encargo.tipo is None:
        tipo = tipo_for_rumbo(rumbo, prompt)
    return Encargo(
        curso=curso,
        asignatura=asignatura,
        oa=encargo.oa,
        duracion=encargo.duracion,
        tipo=tipo,
        notas=encargo.notas,
        rumbo=rumbo.value if rumbo else encargo.rumbo,
        tema=tema,
    )


def apply_rumbo(encargo: Encargo, rumbo_raw: str) -> Encargo:
    rumbo = Rumbo.parse(rumbo_raw)
    if rumbo is None:
        return encargo
    tipo = encargo.tipo or rumbo.default_tipo
    return Encargo(
        curso=encargo.curso,
        asignatura=encargo.asignatura,
        oa=encargo.oa,
        duracion=encargo.duracion,
        tipo=tipo,
        notas=encargo.notas,
        rumbo=rumbo.value,
        tema=encargo.tema,
    )


def source_domain_warning(workspace: Workspace, prompt: str, encargo: Encargo) -> str | None:
    """Non-blocking aviso when carpeta domain ≠ encargo domain."""
    try:
        sources = workspace.list_sources()
    except Exception:
        return None
    blob = " ".join(item.relative_path for item in sources)
    # also peek filenames + a bit of content names
    text = f"{prompt} {encargo.tema} {encargo.asignatura} {encargo.curso}"
    return domain_mismatch(text, blob)
