"""Recover a draft when the model prints draft_artifact(...) as prose, not a tool."""

from __future__ import annotations

import re

from tero.types import ArtifactDraft, ArtifactType, Evidence

_CALL = re.compile(r"draft_artifact\s*\(", re.IGNORECASE)


def salvage_draft_from_text(
    text: str,
    *,
    fallback_tipo: ArtifactType | None = None,
    evidencias: list[Evidence] | None = None,
) -> ArtifactDraft | None:
    """Parse a leaked Python-style draft_artifact(...) call from streamed text."""
    blob = text or ""
    if "draft_artifact" not in blob:
        return None
    match = _CALL.search(blob)
    if not match:
        return None
    src = blob[match.start() :]
    tipo_raw = _kw_string(src, "tipo")
    titulo = _kw_string(src, "titulo")
    cuerpo = _kw_string(src, "cuerpo_markdown")
    payload_raw = _kw_string(src, "payload_json")
    if not (cuerpo or "").strip() and not (payload_raw or "").strip():
        return None
    cuerpo = _unescape(cuerpo or "")
    parsed = ArtifactType.parse(tipo_raw) or fallback_tipo or ArtifactType.GUIA
    title = _unescape((titulo or "").strip()) or parsed.label
    payload = None
    if payload_raw:
        from tero.latex.schemas import parse_payload_json

        payload = parse_payload_json(parsed.value, _unescape(payload_raw))
    if not cuerpo.strip() and payload:
        cuerpo = f"# {title}\n"
    if not cuerpo.strip():
        return None
    return ArtifactDraft(
        tipo=parsed,
        titulo=title[:180],
        cuerpo_markdown=cuerpo.strip() + "\n",
        evidencias=list(evidencias or []),
        payload=payload,
    )


def _kw_string(src: str, name: str) -> str | None:
    triple = re.search(
        rf"""\b{name}\s*=\s*('''|\"\"\")(.*?)(\1)""",
        src,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if triple:
        return triple.group(2)
    single = re.search(
        rf"""\b{name}\s*=\s*(["'])((?:\\.|(?!\1).)*?)\1""",
        src,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if single:
        return single.group(2)
    return None


def _unescape(text: str) -> str:
    return (
        (text or "")
        .replace(r"\n", "\n")
        .replace(r"\t", "\t")
        .replace(r"\"", '"')
        .replace(r"\'", "'")
    )
