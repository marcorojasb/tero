"""Evidence records and non-blocking teacher warnings."""

from __future__ import annotations

import json
from typing import Any

from tero.artifacts import missing_headings
from tero.coerce import as_text
from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence, Plan, WarningItem
from tero.workspace import Workspace

THIN_CHARS = 700


def snippet_in_text(text: str, snippet: Any) -> bool:
    needle = as_text(snippet, joiner=" ").strip()
    haystack = as_text(text)
    if not needle or not haystack:
        return False
    if needle in haystack:
        return True
    compact = " ".join(haystack.lower().split())
    return " ".join(needle.lower().split()) in compact


def verify_evidence(workspace: Workspace, item: Evidence) -> Evidence:
    try:
        payload = workspace.read_source(item.path)
    except Exception:
        return Evidence(
            path=item.path,
            snippet=item.snippet,
            seccion=item.seccion,
            start_line=item.start_line,
            verified=False,
        )
    return Evidence(
        path=str(payload.get("path") or item.path),
        snippet=item.snippet,
        seccion=item.seccion,
        start_line=item.start_line,
        verified=snippet_in_text(str(payload.get("text") or ""), item.snippet),
    )


def parse_evidence_blob(raw: str | list[dict[str, Any]] | None) -> list[Evidence]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        payload = raw
    else:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return [
                Evidence(path="(sin parsear)", snippet=str(raw)[:240], seccion=""),
            ]
    items: list[Evidence] = []
    if not isinstance(payload, list):
        return items
    for row in payload:
        if not isinstance(row, dict):
            continue
        path = str(row.get("path") or "").strip()
        snippet = str(row.get("snippet") or "").strip()
        seccion = str(row.get("seccion") or row.get("section") or "").strip()
        start = row.get("start_line")
        start_line = int(start) if isinstance(start, int) else None
        verified = bool(row.get("verified"))
        if path or snippet:
            items.append(
                Evidence(
                    path=path,
                    snippet=snippet,
                    seccion=seccion,
                    start_line=start_line,
                    verified=verified,
                )
            )
    return items


def collect_warnings(
    *,
    workspace: Workspace,
    encargo: Encargo,
    plan: Plan | None,
    draft: ArtifactDraft,
    prompt: str = "",
) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    source_records = workspace.list_sources()
    sources = {item.relative_path for item in source_records}

    from tero.rumbos import domain_mismatch

    source_blob = " ".join(sources)
    mismatch = domain_mismatch(
        f"{prompt} {encargo.tema} {encargo.asignatura} {encargo.curso}",
        source_blob,
    )
    if mismatch:
        warnings.append(WarningItem(code="domain_mismatch", message=mismatch))

    plan_oa = (plan.oa if plan else "") or encargo.oa
    if encargo.oa and plan_oa and _normalize_oa(encargo.oa) != _normalize_oa(plan_oa):
        # Allow "OA 4" vs "OA 4 (LEN-4B-OA04)" when same catalog id / codigo
        from tero.curriculum.catalog import resolve_oa

        a = resolve_oa(encargo.oa, curso=encargo.curso, asignatura=encargo.asignatura)
        b = resolve_oa(plan_oa, curso=encargo.curso, asignatura=encargo.asignatura)
        if not (a and b and a.id == b.id):
            warnings.append(
                WarningItem(
                    code="oa_mismatch",
                    message=f"OA del encargo ({encargo.oa}) no coincide con el plan ({plan_oa}).",
                )
            )

    # Unknown OA relative to catalog (non-blocking)
    if encargo.oa or (plan and plan.oa):
        from tero.curriculum.catalog import resolve_oa

        check = (plan.oa if plan and plan.oa else "") or encargo.oa
        if check and resolve_oa(check, curso=encargo.curso, asignatura=encargo.asignatura) is None:
            warnings.append(
                WarningItem(
                    code="oa_unknown",
                    message=(
                        f"OA «{check}» no está en el catálogo Chile host-side. "
                        "El agente no debería inventar ids; usa list_oa/get_oa."
                    ),
                )
            )

    body = as_text(draft.cuerpo_markdown).strip()
    if len(body) < THIN_CHARS:
        warnings.append(
            WarningItem(
                code="thin_skeleton",
                message="El borrador es corto: revisa si es un esqueleto más que un material usable.",
            )
        )

    missing = missing_headings(draft.tipo, body)
    if missing:
        warnings.append(
            WarningItem(
                code="missing_structure",
                message=f"Faltan apartados esperados para {draft.tipo.label}: {', '.join(missing)}.",
            )
        )

    if draft.tipo == ArtifactType.EVALUACION and not _has_rubric_hint(body):
        warnings.append(
            WarningItem(
                code="missing_rubric",
                message="Evaluación sin pauta/rúbrica visible. Puedes aceptarla igual o pedir corrección.",
            )
        )

    if len(draft.evidencias) < 2:
        warnings.append(
            WarningItem(
                code="thin_evidence",
                message="Menos de dos fuentes citadas. El panel de evidencia quedará pobre.",
            )
        )

    for item in draft.evidencias:
        if item.path and item.path not in sources:
            warnings.append(
                WarningItem(
                    code="unknown_source",
                    message=f"Cita a una ruta que no está en la carpeta: {item.path}",
                )
            )
            continue
        checked = verify_evidence(workspace, item)
        if item.snippet and not checked.verified:
            warnings.append(
                WarningItem(
                    code="unverified_citation",
                    message=(
                        f"El fragmento citado no aparece en {item.path}. "
                        "Puede ser parafraseo del modelo; no lo trates como cita textual."
                    ),
                )
            )
        if any(
            record.relative_path == item.path and record.changed
            for record in workspace.list_sources()
        ):
            warnings.append(
                WarningItem(
                    code="hash_changed",
                    message=f"La fuente {item.path} cambió respecto del índice. tero no toca el original.",
                )
            )

    # de-duplicate by code+message
    unique: list[WarningItem] = []
    seen: set[str] = set()
    for item in warnings:
        key = f"{item.code}:{item.message}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _normalize_oa(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _has_rubric_hint(markdown: str) -> bool:
    lowered = markdown.lower()
    return any(
        token in lowered for token in ("rúbrica", "rubrica", "pauta", "criterios de evaluación")
    )
