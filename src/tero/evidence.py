"""Evidence records and non-blocking teacher warnings."""

from __future__ import annotations

import json
import re
from typing import Any

from tero.artifacts import missing_headings
from tero.coerce import as_text
from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence, Propuesta, WarningItem
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

    # El tipo es contexto, no un plan aprobado: si el agente entregó otro,
    # la persona lo ve en la tarjeta y decide igual.
    expected_tipo = encargo.tipo
    if expected_tipo is not None and draft.tipo != expected_tipo:
        warnings.append(
            WarningItem(
                code="tipo_desviado",
                message=(
                    f"El contexto decía {expected_tipo.label} y la propuesta llegó como "
                    f"{draft.tipo.label}. Puedes aprobarla igual o pedir el otro entregable."
                ),
            )
        )
    payload_oa = str((draft.payload or {}).get("oa") or "").strip()
    plan_oa = payload_oa or encargo.oa
    if encargo.oa and payload_oa and _normalize_oa(encargo.oa) != _normalize_oa(payload_oa):
        # Allow "OA 4" vs "OA 4 (LEN-4B-OA04)" when same catalog id / codigo
        from tero.curriculum.catalog import resolve_oa

        a = resolve_oa(encargo.oa, curso=encargo.curso, asignatura=encargo.asignatura)
        b = resolve_oa(plan_oa, curso=encargo.curso, asignatura=encargo.asignatura)
        if not (a and b and a.id == b.id):
            warnings.append(
                WarningItem(
                    code="oa_mismatch",
                    message=(
                        f"OA del contexto ({encargo.oa}) no coincide con el de la "
                        f"propuesta ({plan_oa})."
                    ),
                )
            )

    # Unknown OA relative to catalog (non-blocking). Skip when the course
    # is not in the catalog: free-text OA is the honest path (1° medio).
    if encargo.oa or payload_oa:
        from tero.curriculum.catalog import catalog_covers_curso, resolve_oa

        check = payload_oa or encargo.oa
        covers = catalog_covers_curso(encargo.curso)
        if (
            check
            and covers
            and resolve_oa(check, curso=encargo.curso, asignatura=encargo.asignatura) is None
        ):
            warnings.append(
                WarningItem(
                    code="oa_unknown",
                    message=(
                        f"OA «{check}» no está en el catálogo Chile host-side. "
                        "El agente no debería inventar ids; usa list_oa/get_oa."
                    ),
                )
            )
        if (
            check
            and "medio" in (encargo.curso or "").lower()
            and re.search(r"-(4B|5B|6B)-", check, flags=re.IGNORECASE)
        ):
            warnings.append(
                WarningItem(
                    code="oa_wrong_level",
                    message=(
                        f"OA «{check}» es de básica y el encargo es {encargo.curso}. "
                        "El catálogo host no cubre media: no uses un OA de 4°–6° básico de relleno."
                    ),
                )
            )

    body = as_text(draft.cuerpo_markdown).strip()
    payload_rich = bool(draft.payload)
    if len(body) < THIN_CHARS and not payload_rich:
        warnings.append(
            WarningItem(
                code="thin_skeleton",
                message="La propuesta es corta: revisa si es un esqueleto más que un material usable.",
            )
        )

    missing = missing_headings(draft.tipo, body)
    if missing and not payload_rich:
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
                message="Evaluación sin pauta/rúbrica visible. Puedes aprobarla igual o pedir cambios.",
            )
        )

    if len(draft.evidencias) < 2:
        warnings.append(
            WarningItem(
                code="thin_evidence",
                message="Menos de dos fuentes citadas. El panel de evidencia quedará pobre.",
            )
        )

    unverified_paths: list[str] = []
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
            unverified_paths.append(item.path)
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
    if unverified_paths:
        unique_paths = list(dict.fromkeys(unverified_paths))
        listed = ", ".join(unique_paths)
        warnings.append(
            WarningItem(
                code="unverified_citation",
                message=(
                    f"{len(unverified_paths)} cita(s) no aparecen textuales "
                    f"({listed}). Puede ser parafraseo; no las trates como cita literal."
                ),
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


# Decreto 83/2015 (Chile): adecuaciones de acceso y adecuaciones en los objetivos.
NEE_CRITERIOS_ACCESO = (
    "presentación de la información",
    "formas de respuesta",
    "entorno",
    "tiempo",
)
NEE_CRITERIOS_OBJETIVOS = (
    "graduación",
    "priorización",
    "temporalización",
    "enriquecimiento",
    "eliminación",
)
# El decreto es taxativo: la eliminación nunca toca estos aprendizajes.
NEE_ELIMINACION_PROHIBIDA = ("lectoescritura", "operaciones matemáticas", "vida cotidiana")


def propuesta_warnings(propuesta: Propuesta) -> list[WarningItem]:
    """Avisos propios de una propuesta de adaptación. Nunca bloquean: informan."""
    if propuesta.accion != "adaptar":
        return []
    notas = [str(nota).strip().lower() for nota in propuesta.notas_nee]
    warnings = [
        WarningItem(
            code="paci_no_oficial",
            message=(
                "Estos son apoyos para la clase, no una adecuación curricular formal ni un "
                "PACI. El PACI es un documento oficial ante el MINEDUC: si lo necesitas, "
                "revísalo con tu equipo PIE."
            ),
        )
    ]
    hay_objetivos = any(nota.startswith("objetivos") for nota in notas)
    hay_acceso = any(nota.startswith("acceso") for nota in notas)
    if hay_objetivos and not hay_acceso:
        warnings.append(
            WarningItem(
                code="nee_sin_apoyos_de_acceso",
                message=(
                    "Ajustaste objetivos y no dejaste adecuaciones de acceso. El Decreto 83 "
                    "pide considerar primero las adecuaciones de acceso."
                ),
            )
        )
    if any("eliminación" in nota or "eliminacion" in nota for nota in notas):
        warnings.append(
            WarningItem(
                code="nee_eliminacion",
                message=(
                    "Hay un criterio de eliminación. El Decreto 83 no permite eliminar "
                    "aprendizajes de lectoescritura, de operaciones matemáticas ni los que "
                    "permiten desenvolverse en la vida cotidiana."
                ),
            )
        )
    return warnings
