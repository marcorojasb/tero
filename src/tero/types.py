"""Shared domain types. Keep this module free of I/O and AWS."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Literal

ProtocolPhase = Literal[
    "idle",
    "leyendo",
    "proponiendo_plan",
    "esperando_plan",
    "escribiendo",
    "esperando_criterio",
    "exportando",
    "listo",
    "error",
]

GateDecision = Literal["s", "n", "b", "c"]
PlanDecision = Literal["approve", "edit", "cancel"]


class ArtifactType(StrEnum):
    PLANIFICACION = "planificacion"
    GUIA = "guia"
    EVALUACION = "evaluacion"
    PAUTA = "pauta"
    ACTIVIDAD = "actividad"

    @property
    def label(self) -> str:
        return {
            ArtifactType.PLANIFICACION: "planificación",
            ArtifactType.GUIA: "guía",
            ArtifactType.EVALUACION: "evaluación",
            ArtifactType.PAUTA: "pauta/rúbrica",
            ArtifactType.ACTIVIDAD: "actividad",
        }[self]

    @classmethod
    def parse(cls, value: str | None) -> ArtifactType | None:
        if not value:
            return None
        raw = value.strip().lower()
        aliases = {
            "planificación": cls.PLANIFICACION,
            "planificacion": cls.PLANIFICACION,
            "plan": cls.PLANIFICACION,
            "guía": cls.GUIA,
            "guia": cls.GUIA,
            "evaluación": cls.EVALUACION,
            "evaluacion": cls.EVALUACION,
            "prueba": cls.EVALUACION,
            "pauta": cls.PAUTA,
            "rúbrica": cls.PAUTA,
            "rubrica": cls.PAUTA,
            "pauta/rúbrica": cls.PAUTA,
            "pauta/rubrica": cls.PAUTA,
            "actividad": cls.ACTIVIDAD,
        }
        if raw in aliases:
            return aliases[raw]
        try:
            return cls(raw)
        except ValueError:
            return None


@dataclass(frozen=True)
class Encargo:
    curso: str = ""
    asignatura: str = ""
    oa: str = ""
    duracion: str = ""
    tipo: ArtifactType | None = None
    notas: str = ""

    def chips(self) -> list[str]:
        chips: list[str] = []
        if self.curso:
            chips.append(self.curso)
        if self.asignatura:
            chips.append(self.asignatura)
        if self.oa:
            chips.append(self.oa)
        if self.duracion:
            chips.append(self.duracion)
        if self.tipo:
            chips.append(self.tipo.label)
        return chips

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tipo"] = self.tipo.value if self.tipo else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Encargo:
        data = data or {}
        tipo = ArtifactType.parse(data.get("tipo"))
        return cls(
            curso=str(data.get("curso") or ""),
            asignatura=str(data.get("asignatura") or ""),
            oa=str(data.get("oa") or ""),
            duracion=str(data.get("duracion") or ""),
            tipo=tipo,
            notas=str(data.get("notas") or ""),
        )


@dataclass
class Plan:
    objetivo: str
    tipo: ArtifactType
    oa: str = ""
    duracion: str = ""
    notas: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "objetivo": self.objetivo,
            "tipo": self.tipo.value,
            "tipo_label": self.tipo.label,
            "oa": self.oa,
            "duracion": self.duracion,
            "notas": self.notas,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Plan:
        tipo = ArtifactType.parse(data.get("tipo")) or ArtifactType.PLANIFICACION
        return cls(
            objetivo=str(data.get("objetivo") or "").strip(),
            tipo=tipo,
            oa=str(data.get("oa") or "").strip(),
            duracion=str(data.get("duracion") or "").strip(),
            notas=str(data.get("notas") or "").strip(),
        )


@dataclass
class Evidence:
    path: str
    snippet: str
    seccion: str = ""
    start_line: int | None = None
    verified: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WarningItem:
    code: str
    message: str
    blocking: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ArtifactDraft:
    tipo: ArtifactType
    titulo: str
    cuerpo_markdown: str
    evidencias: list[Evidence] = field(default_factory=list)
    warnings: list[WarningItem] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "tipo": self.tipo.value,
            "tipo_label": self.tipo.label,
            "titulo": self.titulo,
            "cuerpo_markdown": self.cuerpo_markdown,
            "evidencias": [item.as_dict() for item in self.evidencias],
            "warnings": [item.as_dict() for item in self.warnings],
        }


@dataclass
class SourceRecord:
    relative_path: str
    sha256: str
    bytes: int
    changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Turn:
    id: str
    prompt: str
    phase: ProtocolPhase
    plan: Plan | None = None
    draft: ArtifactDraft | None = None
    gate: GateDecision | None = None
    artifact_path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "phase": self.phase,
            "plan": self.plan.as_dict() if self.plan else None,
            "draft": self.draft.as_dict() if self.draft else None,
            "gate": self.gate,
            "artifact_path": self.artifact_path,
        }
