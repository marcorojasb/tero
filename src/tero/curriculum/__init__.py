"""Currículum Chile — catálogo host-side (el modelo selecciona; no inventa ids)."""

from __future__ import annotations

from tero.curriculum.catalog import (
    CurriculumCatalog,
    OARecord,
    get_catalog,
    get_oa,
    list_oa,
    normalize_asignatura,
    normalize_curso,
    resolve_oa,
    search_oa,
    validate_oa_id,
)

__all__ = [
    "CurriculumCatalog",
    "OARecord",
    "get_catalog",
    "get_oa",
    "list_oa",
    "normalize_asignatura",
    "normalize_curso",
    "resolve_oa",
    "search_oa",
    "validate_oa_id",
]
