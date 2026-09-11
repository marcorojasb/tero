"""Recover a proposal when the model prints a tool as prose instead of calling it."""

from __future__ import annotations

import json
import re
from typing import Any

from tero.types import ArtifactDraft, ArtifactType, Evidence, Propuesta, parse_accion

_CALL = re.compile(r"(?:proponer_crear|proponer_editar|draft_artifact)\s*\(", re.IGNORECASE)
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


def salvage_propuesta_from_text(
    text: str,
    *,
    fallback_tipo: ArtifactType | None = None,
    evidencias: list[Evidence] | None = None,
) -> Propuesta | None:
    """Arma la propuesta que el modelo dejó como texto en vez de llamar a la tool."""
    draft = salvage_draft_from_text(text, fallback_tipo=fallback_tipo, evidencias=evidencias)
    if draft is None:
        return None
    accion, origen, resumen, cambios, notas_nee = _proposal_meta_from_text(text)
    return Propuesta(
        accion=accion,
        draft=draft,
        resumen=resumen,
        origen=origen,
        cambios=cambios,
        notas_nee=notas_nee,
    )


def _proposal_meta_from_text(text: str) -> tuple[Any, str, str, list[str], list[str]]:
    """Lee accion/origen/resumen/cambios/notas_nee de una llamada filtrada."""
    blob = text or ""
    match = _CALL.search(blob)
    if not match:
        return "crear", "", "", [], []
    src = blob[match.start() :]
    accion = parse_accion(_unescape(_kw_string(src, "accion") or ""))
    origen = _unescape(_kw_string(src, "ruta_origen") or "").strip()
    resumen = _unescape(_kw_string(src, "resumen") or "").strip()
    cambios = _split_kw_items(_unescape(_kw_string(src, "cambios") or ""))
    notas = _split_kw_items(_unescape(_kw_string(src, "notas_nee") or ""))
    if accion == "crear" and origen:
        accion = "editar"
    return accion, origen, resumen, cambios, notas


def _split_kw_items(value: str) -> list[str]:
    items: list[str] = []
    for chunk in re.split(r"[\n;]+|\s+[•·]\s+", value or ""):
        item = chunk.strip().strip("-*•·").strip()
        if item:
            items.append(item)
    return items


def _draft_from_python_call(
    blob: str,
    *,
    fallback_tipo: ArtifactType | None,
    evidencias: list[Evidence] | None,
) -> ArtifactDraft | None:
    """Parse a leaked Python-style proponer_crear/proponer_editar (...) call."""
    match = _CALL.search(blob)
    if not match:
        return None
    src = blob[match.start() :]
    tipo_raw = _kw_string(src, "tipo")
    titulo = _kw_string(src, "titulo")
    cuerpo = _kw_string(src, "vista_previa_markdown") or _kw_string(src, "cuerpo_markdown")
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
    """Last resort: the model wrote the ficha as markdown and never called the tool.

    Ojo: una respuesta conversacional larga también trae headings. Solo se rescata
    si el cuerpo cumple la estructura de algún tipo de material; si no, es charla.
    """
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
    if not tipo_raw:
        inferido = _tipo_for_ficha(cuerpo, fallback_tipo)
        if inferido is None:
            return None
        tipo_raw = inferido.value
    return _finish_draft(
        tipo_raw=tipo_raw,
        titulo=titulo,
        cuerpo=cuerpo,
        payload_raw=None,
        fallback_tipo=fallback_tipo,
        evidencias=evidencias,
    )


def _tipo_for_ficha(cuerpo: str, fallback: ArtifactType | None) -> ArtifactType | None:
    """Tipo cuyos titulares calzan con el cuerpo. None = es una respuesta, no una ficha."""
    from tero.artifacts import missing_section_headings

    candidatos: list[ArtifactType] = []
    if fallback is not None:
        candidatos.append(fallback)
    candidatos.extend(tipo for tipo in ArtifactType if tipo is not fallback)
    for tipo in candidatos:
        if len(missing_section_headings(tipo, cuerpo)) <= 1:
            return tipo
    return None


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
    from tero.sanitize import scrub_ficha_text, strip_tool_traces_value

    cuerpo = scrub_ficha_text(cuerpo or "")
    payload = None
    if payload_raw not in (None, ""):
        from tero.latex.schemas import parse_payload_json

        payload = parse_payload_json(parsed.value, payload_raw)
    from tero.latex.schemas import enrich_payload_from_markdown

    payload = enrich_payload_from_markdown(parsed.value, payload, cuerpo)
    payload = strip_tool_traces_value(payload)
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
