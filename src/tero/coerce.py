"""Coerce model/tool inputs to plain strings.

Bedrock Nova Lite sometimes passes tool arguments as JSON arrays
(e.g. titulo, cuerpo_markdown, snippet, objetivo, tipo) where the host
expects a scalar string and calls ``.strip()``.
"""

from __future__ import annotations

from typing import Any


def as_text(value: Any, *, joiner: str = "\n") -> str:
    """Return a string safe for ``.strip()`` / labeling / parsing.

    Lists and tuples are joined (default newlines; use ``joiner=" "`` for
    short fields like titulo / tipo / snippet). Nested values are coerced
    recursively. ``None`` becomes ``""``.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple)):
        parts = [as_text(item, joiner=joiner) for item in value]
        return joiner.join(part for part in parts if part != "")
    if isinstance(value, dict):
        parts = [as_text(v, joiner=joiner) for v in value.values()]
        return joiner.join(part for part in parts if part != "")
    return str(value)
