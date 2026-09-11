"""Shared domain types. Keep this module free of I/O and AWS."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Literal

from tero.coerce import as_text

ProtocolPhase = Literal[
    "idle",
    "pensando",
    "esperando_aprobacion",
    "listo",
    "error",
]

# Intención del agente cuando propone escribir material.
AccionPropuesta = Literal["crear", "editar", "adaptar"]


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
    def parse(cls, value: Any) -> ArtifactType | None:
        text = as_text(value, joiner=" ")
        if not text:
            return None
        raw = text.strip().lower()
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


def parse_accion(value: Any) -> AccionPropuesta:
    """`editar` cuando la persona pide cambios; `adaptar` cuando pide apoyos/NEE."""
    raw = as_text(value, joiner=" ").strip().lower()
    if raw in {"editar", "edita", "modificar", "modifica", "versionar", "version"}:
        return "editar"
    if raw in {"adaptar", "adapta", "nee", "adecuar", "adecua", "accesible"}:
        return "adaptar"
    return "crear"


@dataclass(frozen=True)
class Encargo:
    curso: str = ""
    asignatura: str = ""
    oa: str = ""
    duracion: str = ""
    tipo: ArtifactType | None = None
    notas: str = ""
    rumbo: str = ""
    tema: str = ""

    def chips(self) -> list[str]:
        chips: list[str] = []
        if self.rumbo:
            chips.append(self.rumbo.capitalize())
        if self.curso:
            chips.append(self.curso)
        if self.asignatura:
            chips.append(self.asignatura)
        if self.tema:
            chips.append(self.tema if len(self.tema) <= 36 else self.tema[:33] + "…")
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
            rumbo=str(data.get("rumbo") or ""),
            tema=str(data.get("tema") or ""),
        )

    def merge(self, other: Encargo) -> Encargo:
        """Prefer non-empty fields from *other*."""
        return Encargo(
            curso=other.curso or self.curso,
            asignatura=other.asignatura or self.asignatura,
            oa=other.oa or self.oa,
            duracion=other.duracion or self.duracion,
            tipo=other.tipo or self.tipo,
            notas=other.notas or self.notas,
            rumbo=other.rumbo or self.rumbo,
            tema=other.tema or self.tema,
        )

    def context_line(self) -> str:
        """One-line context for the system prompt. Never a step to fill in."""
        parts = [
            f"{key}: {value}"
            for key, value in (
                ("curso", self.curso),
                ("asignatura", self.asignatura),
                ("OA", self.oa),
                ("duración", self.duracion),
                ("tema", self.tema),
                ("tipo preferido", self.tipo.label if self.tipo else ""),
            )
            if value
        ]
        return " · ".join(parts) if parts else "(sin contexto aún)"


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
    payload: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "tipo": self.tipo.value,
            "tipo_label": self.tipo.label,
            "titulo": self.titulo,
            "cuerpo_markdown": self.cuerpo_markdown,
            "evidencias": [item.as_dict() for item in self.evidencias],
            "warnings": [item.as_dict() for item in self.warnings],
        }
        if self.payload:
            data["payload"] = self.payload
        return data


@dataclass
class Propuesta:
    """Lo que el agente propone escribir. En memoria hasta que la persona aprueba."""

    accion: AccionPropuesta
    draft: ArtifactDraft
    resumen: str = ""
    origen: str = ""
    cambios: list[str] = field(default_factory=list)
    notas_nee: list[str] = field(default_factory=list)

    @property
    def tipo(self) -> ArtifactType:
        return self.draft.tipo

    @property
    def titulo(self) -> str:
        return self.draft.titulo

    @property
    def vista_previa(self) -> str:
        return self.draft.cuerpo_markdown

    def as_dict(self) -> dict[str, Any]:
        return {
            "accion": self.accion,
            "tipo": self.draft.tipo.value,
            "tipo_label": self.draft.tipo.label,
            "titulo": self.draft.titulo,
            "resumen": self.resumen,
            "vista_previa": self.draft.cuerpo_markdown,
            "origen": self.origen or None,
            "cambios": list(self.cambios),
            "notas_nee": list(self.notas_nee),
            "evidencias": [item.as_dict() for item in self.draft.evidencias],
            "warnings": [item.as_dict() for item in self.draft.warnings],
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
    respuesta: str = ""
    propuesta: Propuesta | None = None
    aprobada: bool = False
    artifact_path: str | None = None
    peticiones: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "phase": self.phase,
            "respuesta": self.respuesta,
            "propuesta": self.propuesta.as_dict() if self.propuesta else None,
            "aprobada": self.aprobada,
            "artifact_path": self.artifact_path,
            "peticiones": list(self.peticiones),
        }
