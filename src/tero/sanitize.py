"""Strip leaked tool traces and TeX dumps from ficha markdown and payload.

Qwen (and sometimes others) paste `cite_evidence: fuentes/…` or
`\\begin{cases}` into the student-facing body. That is a host fingerprint,
not classroom copy. The model fills JSON; the host renders LaTeX.
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
_CASES = re.compile(r"\\+begin\{cases\}(.*?)\\+end\{cases\}", flags=re.IGNORECASE | re.DOTALL)
_MATH_WRAP = re.compile(r"\\+[()\[\]]")


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


def flatten_tex_leaks(text: str) -> str:
    """Turn leaked TeX math into plain classroom text."""
    if not text:
        return text
    if "begin{cases}" not in text and "\\(" not in text and "\\[" not in text and "; [" not in text:
        return text

    def _rows(match: re.Match[str]) -> str:
        inner = match.group(1)
        parts = re.split(r"\\\\|\n", inner)
        cleaned: list[str] = []
        for part in parts:
            row = re.sub(r"\s+", " ", part).strip().strip("&").strip()
            row = _MATH_WRAP.sub("", row).strip()
            if row:
                cleaned.append(row)
        return "; ".join(cleaned)

    out = _CASES.sub(_rows, text)
    out = _MATH_WRAP.sub("", out)
    # Half-flattened \[ cases \] leftovers: "sistema: ; [ \ x+y=5; x-y=1 \ ; ]"
    out = re.sub(r":\s*;\s*\[\s*\\*\s*", ": ", out)
    out = re.sub(r"\s*\\*\s*;\s*\]", "", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r" +([,.;:!?])", r"\1", out)
    return out


def scrub_ficha_text(text: str) -> str:
    """Tool traces first, then leaked TeX. Safe on ordinary Spanish prose."""
    return flatten_tex_leaks(strip_tool_traces(text))


def strip_tool_traces_value(value: Any) -> Any:
    """Walk JSON-ish payload strings (and nested lists/dicts)."""
    if isinstance(value, str):
        return scrub_ficha_text(value)
    if isinstance(value, list):
        return [strip_tool_traces_value(item) for item in value]
    if isinstance(value, dict):
        return {key: strip_tool_traces_value(item) for key, item in value.items()}
    return value
