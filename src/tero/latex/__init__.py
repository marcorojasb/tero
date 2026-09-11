"""LaTeX export: LLM fills JSON schema; host renders deterministic templates."""

from __future__ import annotations

from tero.latex.render import (
    TEMPLATES_ROOT,
    compile_pdf,
    export_latex,
    render_latex,
)
from tero.latex.schemas import (
    SCHEMA_TYPES,
    enrich_payload_from_markdown,
    extract_payload_from_markdown,
    load_schema,
    parse_payload_json,
    repair_payload,
    validate_payload,
)

__all__ = [
    "SCHEMA_TYPES",
    "TEMPLATES_ROOT",
    "compile_pdf",
    "enrich_payload_from_markdown",
    "export_latex",
    "extract_payload_from_markdown",
    "load_schema",
    "parse_payload_json",
    "render_latex",
    "repair_payload",
    "validate_payload",
]
