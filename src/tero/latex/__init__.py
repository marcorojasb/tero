"""LaTeX export: LLM fills JSON schema; host renders deterministic templates."""

from __future__ import annotations

from tero.latex.render import (
    TEMPLATES_ROOT,
    compile_pdf,
    export_latex,
    render_latex,
    write_latex_artifact,
)
from tero.latex.schemas import (
    SCHEMA_TYPES,
    extract_payload_from_markdown,
    load_schema,
    repair_payload,
    validate_payload,
)

__all__ = [
    "SCHEMA_TYPES",
    "TEMPLATES_ROOT",
    "compile_pdf",
    "export_latex",
    "extract_payload_from_markdown",
    "load_schema",
    "render_latex",
    "repair_payload",
    "validate_payload",
    "write_latex_artifact",
]
