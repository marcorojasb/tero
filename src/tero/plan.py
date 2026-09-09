"""Typed optional plan shown before drafting."""

from __future__ import annotations

from tero.errors import TeroError
from tero.types import ArtifactType, Encargo, Plan


def build_plan(
    *,
    objetivo: str,
    tipo: str,
    oa: str = "",
    duracion: str = "",
    notas: str = "",
    encargo: Encargo | None = None,
) -> Plan:
    parsed = ArtifactType.parse(tipo)
    if parsed is None:
        raise TeroError(f"Tipo de artefacto desconocido: {tipo}", code="bad_tipo")
    objetivo_clean = objetivo.strip()
    if not objetivo_clean:
        raise TeroError("El plan necesita un objetivo.", code="bad_plan")
    encargo = encargo or Encargo()
    return Plan(
        objetivo=objetivo_clean,
        tipo=parsed,
        oa=(oa or encargo.oa).strip(),
        duracion=(duracion or encargo.duracion).strip(),
        notas=notas.strip(),
    )


def apply_plan_edits(plan: Plan, edits: dict[str, str] | None) -> Plan:
    if not edits:
        return plan
    tipo = ArtifactType.parse(edits.get("tipo") or plan.tipo.value) or plan.tipo
    return Plan(
        objetivo=(edits.get("objetivo") or plan.objetivo).strip(),
        tipo=tipo,
        oa=(edits.get("oa") if "oa" in edits else plan.oa).strip(),
        duracion=(edits.get("duracion") if "duracion" in edits else plan.duracion).strip(),
        notas=(edits.get("notas") if "notas" in edits else plan.notas).strip(),
    )
