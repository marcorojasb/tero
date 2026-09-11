"""Load and query the Chile curriculum catalog (JSON on disk, not in the LLM prompt dump)."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any

from tero.config import PACKAGE_ROOT

CATALOG_PATH = PACKAGE_ROOT / "curriculum" / "chile" / "catalogo.json"


@dataclass(frozen=True)
class OARecord:
    id: str
    curso: str
    asignatura: str
    codigo: str
    eje: str
    texto_corto: str
    curso_label: str = ""
    asignatura_label: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def chip(self) -> str:
        return f"{self.codigo} ({self.id})"


@dataclass
class CurriculumCatalog:
    meta: dict[str, Any]
    cursos: list[dict[str, Any]]
    asignaturas: list[dict[str, Any]]
    oas: list[OARecord]

    def curso_label(self, curso_id: str) -> str:
        for row in self.cursos:
            if row["id"] == curso_id:
                return str(row["label"])
        return curso_id

    def asignatura_label(self, asignatura_id: str) -> str:
        for row in self.asignaturas:
            if row["id"] == asignatura_id:
                return str(row["label"])
        return asignatura_id


def _fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", text or "")
    ascii_only = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", ascii_only.lower())


@lru_cache(maxsize=1)
def get_catalog() -> CurriculumCatalog:
    path = CATALOG_PATH
    if not path.exists():
        # Editable install fallback: next to package root already; empty catalog if missing.
        return CurriculumCatalog(
            meta={"disclaimer": "catálogo ausente"}, cursos=[], asignaturas=[], oas=[]
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    curso_labels = {row["id"]: row["label"] for row in data.get("cursos") or []}
    asig_labels = {row["id"]: row["label"] for row in data.get("asignaturas") or []}
    oas: list[OARecord] = []
    for row in data.get("oas") or []:
        curso = str(row.get("curso") or "")
        asignatura = str(row.get("asignatura") or "")
        oas.append(
            OARecord(
                id=str(row.get("id") or "").strip(),
                curso=curso,
                asignatura=asignatura,
                codigo=str(row.get("codigo") or "").strip(),
                eje=str(row.get("eje") or "").strip(),
                texto_corto=str(row.get("texto_corto") or "").strip(),
                curso_label=str(curso_labels.get(curso) or curso),
                asignatura_label=str(asig_labels.get(asignatura) or asignatura),
            )
        )
    return CurriculumCatalog(
        meta=dict(data.get("meta") or {}),
        cursos=list(data.get("cursos") or []),
        asignaturas=list(data.get("asignaturas") or []),
        oas=oas,
    )


def normalize_curso(value: str) -> str | None:
    if not value:
        return None
    catalog = get_catalog()
    folded = _fold(value)
    for row in catalog.cursos:
        candidates = [row["id"], row["label"], *(row.get("aliases") or [])]
        if any(_fold(str(item)) == folded for item in candidates):
            return str(row["id"])
        # soft: "4basico" in "4° básico"
        if folded and _fold(str(row["label"])).startswith(folded[:2]) and "b" in folded:
            if folded[0].isdigit() and folded[0] == _fold(str(row["id"]))[0]:
                return str(row["id"])
    # digit + basico heuristic
    match = re.search(r"([456])", value)
    if match and "bas" in folded:
        return f"{match.group(1)}b"
    return None


def normalize_asignatura(value: str) -> str | None:
    if not value:
        return None
    catalog = get_catalog()
    folded = _fold(value)
    for row in catalog.asignaturas:
        candidates = [row["id"], row["label"], *(row.get("aliases") or [])]
        if any(
            _fold(str(item)) == folded or _fold(str(item)) in folded or folded in _fold(str(item))
            for item in candidates
        ):
            return str(row["id"])
    if "leng" in folded or "comunica" in folded:
        return "lenguaje"
    if "mat" in folded:
        return "matematica"
    if "cien" in folded or folded in {"cn", "naturales"}:
        return "ciencias"
    return None


def catalog_covers_curso(curso: str) -> bool:
    """True when the host catalog has this course (today: 4b–6b). Empty curso is unconstrained."""
    if not (curso or "").strip():
        return True
    return normalize_curso(curso) is not None


def list_oa(curso: str = "", asignatura: str = "") -> list[OARecord]:
    if curso and not catalog_covers_curso(curso):
        return []
    catalog = get_catalog()
    curso_id = normalize_curso(curso) if curso else None
    asig_id = normalize_asignatura(asignatura) if asignatura else None
    results: list[OARecord] = []
    for item in catalog.oas:
        if curso_id and item.curso != curso_id:
            continue
        if asig_id and item.asignatura != asig_id:
            continue
        results.append(item)
    return results


def get_oa(oa_id: str) -> OARecord | None:
    if not oa_id:
        return None
    needle = oa_id.strip()
    catalog = get_catalog()
    for item in catalog.oas:
        if item.id == needle:
            return item
    # also allow bare codigo + context? only exact id here
    folded = _fold(needle)
    for item in catalog.oas:
        if _fold(item.id) == folded:
            return item
    return None


def search_oa(q: str, *, limit: int = 12) -> list[OARecord]:
    query = (q or "").strip()
    if not query:
        return []
    tokens = [_fold(tok) for tok in re.split(r"\s+", query) if tok.strip()]
    scored: list[tuple[int, OARecord]] = []
    for item in get_catalog().oas:
        blob = _fold(
            f"{item.id} {item.codigo} {item.eje} {item.texto_corto} "
            f"{item.curso_label} {item.asignatura_label}"
        )
        score = 0
        for tok in tokens:
            if tok and tok in blob:
                score += 2 if tok in _fold(item.id) or tok in _fold(item.codigo) else 1
        if score:
            scored.append((score, item))
    scored.sort(key=lambda row: (-row[0], row[1].id))
    return [item for _, item in scored[: max(1, limit)]]


def validate_oa_id(oa_id: str) -> bool:
    return get_oa(oa_id) is not None


def resolve_oa(
    raw: str,
    *,
    curso: str = "",
    asignatura: str = "",
) -> OARecord | None:
    """Resolve free-text OA chip to a catalog record when possible."""
    text = (raw or "").strip()
    if not text:
        return None
    direct = get_oa(text)
    if direct:
        return direct
    # Don't invent a básica OA when the course isn't in the catalog (p. ej. 1° medio).
    if curso and not catalog_covers_curso(curso):
        return None
    # "OA 4" / "oa4" within curso+asignatura
    curso_id = normalize_curso(curso)
    asig_id = normalize_asignatura(asignatura)
    codigo_fold = _fold(text)
    candidates = list_oa(curso, asignatura)
    if not candidates:
        candidates = list(get_catalog().oas)
    for item in candidates:
        if _fold(item.codigo) == codigo_fold or _fold(item.id) == codigo_fold:
            return item
        if codigo_fold and codigo_fold in _fold(item.id):
            return item
    # last resort: search
    hits = search_oa(text, limit=5)
    if curso_id or asig_id:
        filtered = [
            hit
            for hit in hits
            if (not curso_id or hit.curso == curso_id)
            and (not asig_id or hit.asignatura == asig_id)
        ]
        if filtered:
            return filtered[0]
    return hits[0] if hits else None


def catalog_summary() -> dict[str, Any]:
    catalog = get_catalog()
    return {
        "disclaimer": catalog.meta.get("disclaimer", ""),
        "cursos": [{"id": row["id"], "label": row["label"]} for row in catalog.cursos],
        "asignaturas": [{"id": row["id"], "label": row["label"]} for row in catalog.asignaturas],
        "oa_count": len(catalog.oas),
    }
