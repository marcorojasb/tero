"""Recover a draft or plan when the model prints tools as prose, not a tool call."""

from __future__ import annotations

import re

from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence, Plan

_CALL = re.compile(r"draft_artifact\s*\(", re.IGNORECASE)
_PLAN_CALL = re.compile(r"propose_plan\s*\(", re.IGNORECASE)


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


def salvage_plan_from_text(text: str, *, encargo: Encargo | None = None) -> Plan | None:
    """Parse a leaked Python-style propose_plan(...) call from streamed text."""
    blob = text or ""
    if "propose_plan" not in blob:
        return None
    match = _PLAN_CALL.search(blob)
    if not match:
        return None
    src = blob[match.start() :]
    objetivo = _unescape(_kw_string(src, "objetivo") or "")
    tipo_raw = _unescape(_kw_string(src, "tipo") or "")
    if not objetivo.strip():
        return None
    from tero.errors import TeroError
    from tero.plan import build_plan

    try:
        return build_plan(
            objetivo=objetivo.strip(),
            tipo=tipo_raw or (encargo.tipo.value if encargo and encargo.tipo else "guia"),
            oa=_unescape(_kw_string(src, "oa") or ""),
            duracion=_unescape(_kw_string(src, "duracion") or ""),
            notas=_unescape(_kw_string(src, "notas") or ""),
            titulo=_unescape(_kw_string(src, "titulo") or ""),
            encargo=encargo,
            decisiones={
                "curso": _unescape(_kw_string(src, "curso") or ""),
                "asignatura": _unescape(_kw_string(src, "asignatura") or ""),
                "tema": _unescape(_kw_string(src, "tema") or ""),
            },
        )
    except TeroError:
        return None


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
