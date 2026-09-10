"""Recover a draft or plan when the model prints tools as prose, not a tool call."""

from __future__ import annotations

import json
import re
from typing import Any

from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence, Plan

_CALL = re.compile(r"draft_artifact\s*\(", re.IGNORECASE)
_PLAN_CALL = re.compile(r"propose_plan\s*\(", re.IGNORECASE)
_HEADING = re.compile(r"#{1,6}\s+\S")
_FICHA_HINTS = (
    "instrucciones",
    "ítem",
    "item",
    "selección",
    "seleccion",
    "verdadero",
    "objetivo",
    "inicio",
    "desarrollo",
    "cierre",
    "propósito",
    "proposito",
    "puntaje",
    "evaluación",
    "evaluacion",
    "opción",
    "opcion",
    "criterio",
    "pauta",
    "nivel",
    "rúbrica",
    "rubrica",
    "descriptor",
    "momento",
)


def salvage_draft_from_text(
    text: str,
    *,
    fallback_tipo: ArtifactType | None = None,
    evidencias: list[Evidence] | None = None,
) -> ArtifactDraft | None:
    """Recover a ficha from a leaked tool call, a JSON dump, or streamed markdown."""
    blob = text or ""
    from_call = _draft_from_python_call(blob, fallback_tipo=fallback_tipo, evidencias=evidencias)
    if from_call is not None:
        return from_call
    from_json = _draft_from_json_blob(blob, fallback_tipo=fallback_tipo, evidencias=evidencias)
    if from_json is not None:
        return from_json
    return _draft_from_markdown_prose(blob, fallback_tipo=fallback_tipo, evidencias=evidencias)


def salvage_plan_from_text(text: str, *, encargo: Encargo | None = None) -> Plan | None:
    """Parse a leaked Python-style propose_plan(...) call or a JSON plan blob."""
    blob = text or ""
    from_call = _plan_from_python_call(blob, encargo=encargo)
    if from_call is not None:
        return from_call
    return _plan_from_json_blob(blob, encargo=encargo)


def _draft_from_python_call(
    blob: str,
    *,
    fallback_tipo: ArtifactType | None,
    evidencias: list[Evidence] | None,
) -> ArtifactDraft | None:
    """Parse a leaked Python-style draft_artifact(...) call from streamed text."""
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
    return _finish_draft(
        tipo_raw=tipo_raw,
        titulo=_unescape((titulo or "").strip()),
        cuerpo=_unescape(cuerpo or ""),
        payload_raw=_unescape(payload_raw) if payload_raw else None,
        fallback_tipo=fallback_tipo,
        evidencias=evidencias,
    )


def _draft_from_json_blob(
    blob: str,
    *,
    fallback_tipo: ArtifactType | None,
    evidencias: list[Evidence] | None,
) -> ArtifactDraft | None:
    """Qwen dumps {titulo, tipo, cuerpo_markdown, payload_json} instead of a tool call."""
    data = _extract_draft_json_object(blob)
    if not data:
        return None
    cuerpo = data.get("cuerpo_markdown")
    if not isinstance(cuerpo, str) or not cuerpo.strip():
        return None
    payload_raw: Any = data.get("payload_json")
    if payload_raw is None:
        payload_raw = data.get("payload")
    return _finish_draft(
        tipo_raw=str(data.get("tipo") or ""),
        titulo=str(data.get("titulo") or "").strip(),
        cuerpo=cuerpo,
        payload_raw=payload_raw,
        fallback_tipo=fallback_tipo,
        evidencias=evidencias,
    )


def _draft_from_markdown_prose(
    blob: str,
    *,
    fallback_tipo: ArtifactType | None,
    evidencias: list[Evidence] | None,
) -> ArtifactDraft | None:
    """Last resort: the model wrote the ficha as markdown and never called the tool."""
    cuerpo = _extract_ficha_markdown(blob)
    if not cuerpo:
        return None
    tipo_raw = ""
    titulo = ""
    match = _CALL.search(blob)
    if match:
        src = blob[match.start() :]
        tipo_raw = _kw_string(src, "tipo") or ""
        titulo = _unescape(_kw_string(src, "titulo") or "")
    return _finish_draft(
        tipo_raw=tipo_raw,
        titulo=titulo,
        cuerpo=cuerpo,
        payload_raw=None,
        fallback_tipo=fallback_tipo,
        evidencias=evidencias,
    )


def _finish_draft(
    *,
    tipo_raw: str | None,
    titulo: str,
    cuerpo: str,
    payload_raw: Any,
    fallback_tipo: ArtifactType | None,
    evidencias: list[Evidence] | None,
) -> ArtifactDraft | None:
    parsed = ArtifactType.parse(tipo_raw) or fallback_tipo or ArtifactType.GUIA
    payload = None
    if payload_raw not in (None, ""):
        from tero.latex.schemas import parse_payload_json

        payload = parse_payload_json(parsed.value, payload_raw)
    from tero.latex.schemas import enrich_payload_from_markdown

    payload = enrich_payload_from_markdown(parsed.value, payload, cuerpo)
    cuerpo = (cuerpo or "").strip()
    if not cuerpo and payload:
        title = (titulo or "").strip() or parsed.label
        cuerpo = f"# {title}"
    if not cuerpo:
        return None
    title = (titulo or "").strip() or _title_from_markdown(cuerpo) or parsed.label
    return ArtifactDraft(
        tipo=parsed,
        titulo=title[:180],
        cuerpo_markdown=cuerpo.strip() + "\n",
        evidencias=list(evidencias or []),
        payload=payload,
    )


def _extract_draft_json_object(blob: str) -> dict[str, Any] | None:
    """Pick the JSON object whose cuerpo_markdown is longest (the ficha, not a stub)."""
    marker = '"cuerpo_markdown"'
    best: dict[str, Any] | None = None
    best_len = -1
    decoder = json.JSONDecoder()
    start = 0
    while True:
        idx = blob.find(marker, start)
        if idx < 0:
            break
        cursor = idx
        while True:
            brace = blob.rfind("{", 0, cursor)
            if brace < 0:
                break
            try:
                data, _end = decoder.raw_decode(blob[brace:])
            except json.JSONDecodeError:
                cursor = brace
                continue
            if isinstance(data, dict):
                cuerpo = data.get("cuerpo_markdown")
                if isinstance(cuerpo, str) and cuerpo.strip() and len(cuerpo) > best_len:
                    best = data
                    best_len = len(cuerpo)
                    break
            cursor = brace
        start = idx + len(marker)
    return best


def _extract_ficha_markdown(text: str) -> str | None:
    """Pull a ficha-shaped markdown body out of streamed model text."""
    blob = text or ""
    cut = _CALL.search(blob)
    if cut:
        blob = blob[: cut.start()]
    fence = re.search(r"```json", blob, flags=re.IGNORECASE)
    if fence:
        blob = blob[: fence.start()]
    match = _HEADING.search(blob)
    if not match:
        return None
    body = blob[match.start() :].strip()
    if not _looks_like_ficha(body):
        return None
    return body


def _looks_like_ficha(text: str) -> bool:
    body = (text or "").strip()
    if len(body) < 280:
        return False
    if not _HEADING.search(body):
        return False
    folded = body.lower()
    hits = sum(1 for hint in _FICHA_HINTS if hint in folded)
    return hits >= 2


def _title_from_markdown(cuerpo: str) -> str:
    match = re.search(r"^#{1,6}\s+(.+)$", (cuerpo or "").strip(), flags=re.MULTILINE)
    if not match:
        return ""
    return re.sub(r"[*_`]+", "", match.group(1)).strip()


def _plan_from_python_call(blob: str, *, encargo: Encargo | None) -> Plan | None:
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
    return _build_salvaged_plan(
        objetivo=objetivo.strip(),
        tipo_raw=tipo_raw,
        oa=_unescape(_kw_string(src, "oa") or ""),
        duracion=_unescape(_kw_string(src, "duracion") or ""),
        notas=_unescape(_kw_string(src, "notas") or ""),
        titulo=_unescape(_kw_string(src, "titulo") or ""),
        curso=_unescape(_kw_string(src, "curso") or ""),
        asignatura=_unescape(_kw_string(src, "asignatura") or ""),
        tema=_unescape(_kw_string(src, "tema") or ""),
        encargo=encargo,
    )


def _plan_from_json_blob(blob: str, *, encargo: Encargo | None) -> Plan | None:
    """Qwen prints a plan dict as JSON instead of propose_plan(...)."""
    text = (blob or "").strip()
    if not text or "objetivo" not in text:
        return None
    from tero.latex.schemas import _parse_json_blob

    data = _parse_json_blob(text)
    if not data:
        return None
    if "cuerpo_markdown" in data or "sm_items" in data:
        return None
    items = data.get("items")
    if isinstance(items, list) and items:
        return None
    objetivo = str(data.get("objetivo") or "").strip()
    tipo_raw = str(data.get("tipo") or "")
    if not objetivo or not tipo_raw:
        return None
    decisiones = data.get("decisiones") if isinstance(data.get("decisiones"), dict) else {}
    return _build_salvaged_plan(
        objetivo=objetivo,
        tipo_raw=tipo_raw,
        oa=str(data.get("oa") or ""),
        duracion=str(data.get("duracion") or ""),
        notas=str(data.get("notas") or ""),
        titulo=str(data.get("titulo") or ""),
        curso=str(data.get("curso") or decisiones.get("curso") or ""),
        asignatura=str(data.get("asignatura") or decisiones.get("asignatura") or ""),
        tema=str(data.get("tema") or decisiones.get("tema") or ""),
        encargo=encargo,
    )


def _build_salvaged_plan(
    *,
    objetivo: str,
    tipo_raw: str,
    oa: str,
    duracion: str,
    notas: str,
    titulo: str,
    curso: str,
    asignatura: str,
    tema: str,
    encargo: Encargo | None,
) -> Plan | None:
    from tero.errors import TeroError
    from tero.plan import build_plan

    try:
        return build_plan(
            objetivo=objetivo.strip(),
            tipo=tipo_raw or (encargo.tipo.value if encargo and encargo.tipo else "guia"),
            oa=oa,
            duracion=duracion,
            notas=notas,
            titulo=titulo,
            encargo=encargo,
            decisiones={
                "curso": curso,
                "asignatura": asignatura,
                "tema": tema,
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
