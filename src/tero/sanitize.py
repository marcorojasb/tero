"""Strip leaked tool traces from ficha markdown and payload strings.

Qwen (and sometimes others) paste `cite_evidence: fuentes/…` into the
student-facing body. That is a host fingerprint, not classroom copy.
"""

from __future__ import annotations

import re
from typing import Any

_TOOL_NAMES = (
    "cite_evidence",
    "read_source",
    "list_sources",
    "search_sources",
    "draft_artifact",
    "propose_plan",
    "list_oa",
    "get_oa",
    "search_oa",
)
_TOOLS = "|".join(_TOOL_NAMES)

# (cite_evidence: fuentes/01-oa-curriculo.md)
_PAREN_TRACE = re.compile(
    rf"\s*\(\s*(?:{_TOOLS})\s*:\s*[^)]+\)",
    flags=re.IGNORECASE,
)
# cite_evidence: fuentes/03-contexto-chile.md
_BARE_TRACE = re.compile(
    rf"(?:(?<=\s)|(?<=[,;:(])|^)(?:{_TOOLS})\s*:\s*"
    rf"(?:fuentes/|\.tero/)?[\w./\-]+\.?\w*",
    flags=re.IGNORECASE | re.MULTILINE,
)
_NEEDLE = re.compile(_TOOLS, flags=re.IGNORECASE)


def strip_tool_traces(text: str) -> str:
    """Remove leaked tool-call fingerprints; keep the surrounding sentence."""
    if not text or not _NEEDLE.search(text):
        return text
    out = _PAREN_TRACE.sub("", text)
    out = _BARE_TRACE.sub("", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r" +([,.;:!?])", r"\1", out)
    out = re.sub(r"\(\s*\)", "", out)
    return out


def strip_tool_traces_value(value: Any) -> Any:
    """Walk JSON-ish payload strings (and nested lists/dicts)."""
    if isinstance(value, str):
        return strip_tool_traces(value)
    if isinstance(value, list):
        return [strip_tool_traces_value(item) for item in value]
    if isinstance(value, dict):
        return {key: strip_tool_traces_value(item) for key, item in value.items()}
    return value
