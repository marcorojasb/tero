"""Shared domain types. Keep this module free of I/O and AWS."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Literal

from tero.coerce import as_text

ProtocolPhase = Literal[
    "idle",
    "home",
    "leyendo",
    "proponiendo_plan",
    "esperando_clarificacion",
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


@dataclass
class PlanDecisionFields:
    curso: str = ""
    asignatura: str = ""
    tema: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PlanDecisionFields:
        data = data or {}
        return cls(
            curso=str(data.get("curso") or ""),
            asignatura=str(data.get("asignatura") or ""),
            tema=str(data.get("tema") or ""),
        )


@dataclass
class PlanStep:
    titulo: str
    detalle: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanStep:
        return cls(
            titulo=str(data.get("titulo") or data.get("title") or "").strip(),
            detalle=str(data.get("detalle") or data.get("detail") or "").strip(),
        )


@dataclass
class PlanAssumption:
    id: str
    text: str
    editable: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanAssumption:
        return cls(
            id=str(data.get("id") or "s1"),
            text=str(data.get("text") or "").strip(),
            editable=bool(data.get("editable", True)),
        )


@dataclass
class PlanOption:
    id: str
    label: str
    suggested: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanOption:
        return cls(
            id=str(data.get("id") or ""),
            label=str(data.get("label") or "").strip(),
            suggested=bool(data.get("suggested")),
        )


@dataclass
class PlanQuestion:
    id: str
    prompt: str
    options: list[PlanOption] = field(default_factory=list)
    answer: str | None = None
    free_text: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "options": [item.as_dict() for item in self.options],
            "answer": self.answer,
            "free_text": self.free_text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanQuestion:
        options = [
            PlanOption.from_dict(row)
            for row in (data.get("options") or [])
            if isinstance(row, dict)
        ]
        return cls(
            id=str(data.get("id") or "q1"),
            prompt=str(data.get("prompt") or "").strip(),
            options=options,
            answer=str(data["answer"]) if data.get("answer") is not None else None,
            free_text=str(data["free_text"]) if data.get("free_text") is not None else None,
        )


@dataclass
class PlanDeliverable:
    tipo: ArtifactType
    label: str = ""
    description: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "tipo": self.tipo.value,
            "label": self.label or self.tipo.label,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanDeliverable:
        tipo = ArtifactType.parse(data.get("tipo")) or ArtifactType.PLANIFICACION
        return cls(
            tipo=tipo,
            label=str(data.get("label") or tipo.label),
            description=str(data.get("description") or ""),
        )


@dataclass
class Plan:
    objetivo: str
    tipo: ArtifactType
    oa: str = ""
    duracion: str = ""
    notas: str = ""
    titulo: str = ""
    meta: str = ""
    resultado_previsto: list[str] = field(default_factory=list)
    decisiones: PlanDecisionFields = field(default_factory=PlanDecisionFields)
    como_abordare: list[PlanStep] = field(default_factory=list)
    supuestos: list[PlanAssumption] = field(default_factory=list)
    questions: list[PlanQuestion] = field(default_factory=list)
    entregables: list[PlanDeliverable] = field(default_factory=list)
    status: str = "propuesto"

    def pending_question(self) -> PlanQuestion | None:
        for question in self.questions:
            if question.answer is None and question.free_text is None:
                return question
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "objetivo": self.objetivo,
            "tipo": self.tipo.value,
            "tipo_label": self.tipo.label,
            "oa": self.oa,
            "duracion": self.duracion,
            "notas": self.notas,
            "titulo": self.titulo,
            "meta": self.meta,
            "resultado_previsto": list(self.resultado_previsto),
            "decisiones": self.decisiones.as_dict(),
            "como_abordare": [item.as_dict() for item in self.como_abordare],
            "supuestos": [item.as_dict() for item in self.supuestos],
            "questions": [item.as_dict() for item in self.questions],
            "entregables": [item.as_dict() for item in self.entregables],
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Plan:
        tipo = ArtifactType.parse(data.get("tipo")) or ArtifactType.PLANIFICACION
        entregables = [
            PlanDeliverable.from_dict(row)
            for row in (data.get("entregables") or [])
            if isinstance(row, dict)
        ]
        if not entregables:
            entregables = [PlanDeliverable(tipo=tipo, label=tipo.label)]
        return cls(
            objetivo=str(data.get("objetivo") or "").strip(),
            tipo=tipo,
            oa=str(data.get("oa") or "").strip(),
            duracion=str(data.get("duracion") or "").strip(),
            notas=str(data.get("notas") or "").strip(),
            titulo=str(data.get("titulo") or "").strip(),
            meta=str(data.get("meta") or "").strip(),
            resultado_previsto=[
                str(item) for item in (data.get("resultado_previsto") or []) if str(item).strip()
            ],
            decisiones=PlanDecisionFields.from_dict(data.get("decisiones")),
            como_abordare=[
                PlanStep.from_dict(row)
                for row in (data.get("como_abordare") or [])
                if isinstance(row, dict)
            ],
            supuestos=[
                PlanAssumption.from_dict(row)
                for row in (data.get("supuestos") or [])
                if isinstance(row, dict)
            ],
            questions=[
                PlanQuestion.from_dict(row)
                for row in (data.get("questions") or [])
                if isinstance(row, dict)
            ],
            entregables=entregables,
            status=str(data.get("status") or "propuesto"),
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
    critique_notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "phase": self.phase,
            "plan": self.plan.as_dict() if self.plan else None,
            "draft": self.draft.as_dict() if self.draft else None,
            "gate": self.gate,
            "artifact_path": self.artifact_path,
            "critique_notes": list(self.critique_notes),
        }
