"""Typed optional plan shown before drafting — Pteron-depth card + clarifications."""

from __future__ import annotations

from datetime import UTC, datetime

from tero.errors import TeroError
from tero.rumbos import infer_tema
from tero.types import (
    ArtifactType,
    Encargo,
    Plan,
    PlanAssumption,
    PlanDecisionFields,
    PlanDeliverable,
    PlanOption,
    PlanQuestion,
    PlanStep,
)

TEMPLATES: dict[ArtifactType, tuple[PlanStep, ...]] = {
    ArtifactType.PLANIFICACION: (
        PlanStep("Inicio", "Activación y foco del OA en pocos minutos."),
        PlanStep("Desarrollo", "Lectura / práctica con evidencia de la carpeta."),
        PlanStep("Cierre", "Síntesis y chequeo formativo breve."),
    ),
    ArtifactType.GUIA: (
        PlanStep("Propósito", "Qué logrará el o la estudiante al terminar."),
        PlanStep("Actividades", "Ítems o tareas con instrucciones claras."),
        PlanStep("Cierre", "Autochequeo o entrega."),
    ),
    ArtifactType.EVALUACION: (
        PlanStep("Instrucciones", "Tiempo, puntaje y condiciones."),
        PlanStep("Ítems", "Selección múltiple y/o desarrollo."),
        PlanStep("Criterios", "Qué cuenta como correcto o suficiente."),
    ),
    ArtifactType.PAUTA: (
        PlanStep("Criterios", "Dimensiones a observar."),
        PlanStep("Niveles", "Destacado → no observado."),
        PlanStep("Descriptores", "Qué se ve en cada celda."),
    ),
    ArtifactType.ACTIVIDAD: (
        PlanStep("Objetivo", "Para qué sirve la dinámica."),
        PlanStep("Materiales", "Qué se necesita en el aula."),
        PlanStep("Pasos", "Secuencia corta y rotativa."),
    ),
}


def build_plan(
    *,
    objetivo: str,
    tipo: str,
    oa: str = "",
    duracion: str = "",
    notas: str = "",
    encargo: Encargo | None = None,
    resultado_previsto: list[str] | None = None,
    decisiones: dict[str, str] | None = None,
    como_abordare: list[dict[str, str]] | None = None,
    supuestos: list[dict[str, str]] | None = None,
    questions: list[dict] | None = None,
    entregables: list[dict] | None = None,
    titulo: str = "",
) -> Plan:
    parsed = ArtifactType.parse(tipo)
    if parsed is None:
        raise TeroError(f"Tipo de artefacto desconocido: {tipo}", code="bad_tipo")
    objetivo_clean = objetivo.strip()
    if not objetivo_clean:
        raise TeroError("El plan necesita un objetivo.", code="bad_plan")
    encargo = encargo or Encargo()
    oa_final = (oa or encargo.oa).strip()
    duracion_final = (duracion or encargo.duracion).strip()
    curso = (decisiones or {}).get("curso") or encargo.curso
    asignatura = (decisiones or {}).get("asignatura") or encargo.asignatura
    tema = (decisiones or {}).get("tema") or encargo.tema or infer_tema(objetivo_clean)

    steps = (
        [PlanStep.from_dict(row) for row in como_abordare if isinstance(row, dict)]
        if como_abordare
        else list(TEMPLATES.get(parsed, ()))
    )
    assumptions = (
        [PlanAssumption.from_dict(row) for row in supuestos if isinstance(row, dict)]
        if supuestos
        else default_supuestos(duracion_final, encargo)
    )
    qs = (
        [PlanQuestion.from_dict(row) for row in questions if isinstance(row, dict)]
        if questions
        else default_questions(parsed, encargo)
    )
    dels = (
        [PlanDeliverable.from_dict(row) for row in entregables if isinstance(row, dict)]
        if entregables
        else default_entregables(parsed, encargo)
    )
    resultados = resultado_previsto or [item.label for item in dels]
    n = len(dels)
    when = datetime.now(UTC).strftime("%d %b %Y").lower().lstrip("0")
    titulo_final = titulo.strip() or f"Plan de {parsed.label} — {tema or objetivo_clean[:48]}"
    meta = f"Plan de trabajo · {n} entregable{'s' if n != 1 else ''} · Listo · {when}"

    return Plan(
        objetivo=objetivo_clean,
        tipo=parsed,
        oa=oa_final,
        duracion=duracion_final,
        notas=notas.strip(),
        titulo=titulo_final,
        meta=meta,
        resultado_previsto=resultados,
        decisiones=PlanDecisionFields(curso=curso, asignatura=asignatura, tema=tema),
        como_abordare=steps,
        supuestos=assumptions,
        questions=qs,
        entregables=dels,
        status="clarificando"
        if any(q.answer is None and q.free_text is None for q in qs)
        else "propuesto",
    )


def default_supuestos(duracion: str, encargo: Encargo) -> list[PlanAssumption]:
    dur = duracion or encargo.duracion or "una sesión breve"
    items = [
        PlanAssumption(
            id="s1",
            text=f"Se usará una extensión pensada para {dur}, salvo que prefieras otra.",
        ),
        PlanAssumption(
            id="s2",
            text="Solo se citarán fuentes de la carpeta local (no internet).",
        ),
    ]
    if encargo.oa:
        items.append(
            PlanAssumption(
                id="s3",
                text=f"El OA de referencia es {encargo.oa}; puedes cambiarlo con /oa.",
            )
        )
    return items


def default_questions(tipo: ArtifactType, encargo: Encargo) -> list[PlanQuestion]:
    """One interactive clarification, Pteron-style, with a SUGERIDA option."""
    if tipo is ArtifactType.GUIA:
        return [
            PlanQuestion(
                id="q_enfasis",
                prompt="¿Qué énfasis conviene para la práctica?",
                options=[
                    PlanOption(id="1", label="Representación y aplicación", suggested=True),
                    PlanOption(id="2", label="Cálculo y equivalencia"),
                    PlanOption(id="3", label="Resolución de problemas"),
                ],
            )
        ]
    if tipo is ArtifactType.EVALUACION:
        return [
            PlanQuestion(
                id="q_formato",
                prompt="¿Qué formato de evaluación prefieres?",
                options=[
                    PlanOption(id="1", label="Selección múltiple + desarrollo", suggested=True),
                    PlanOption(id="2", label="Solo desarrollo con evidencia"),
                    PlanOption(id="3", label="Ítems breves de entrada/salida"),
                ],
            )
        ]
    if tipo is ArtifactType.PAUTA:
        return [
            PlanQuestion(
                id="q_niveles",
                prompt="¿Cuántos niveles quieres en la pauta?",
                options=[
                    PlanOption(
                        id="1", label="4 niveles (destacado → no observado)", suggested=True
                    ),
                    PlanOption(id="2", label="3 niveles (logrado / proceso / inicial)"),
                    PlanOption(id="3", label="Lista de cotejo sí/no"),
                ],
            )
        ]
    if tipo is ArtifactType.ACTIVIDAD:
        return [
            PlanQuestion(
                id="q_dinamica",
                prompt="¿Cómo quieres organizar la actividad?",
                options=[
                    PlanOption(id="1", label="Trabajo en parejas o tríos", suggested=True),
                    PlanOption(id="2", label="Individual con puesta en común"),
                    PlanOption(id="3", label="Rotación de estaciones"),
                ],
            )
        ]
    # planificación
    curso = encargo.curso or "el curso"
    return [
        PlanQuestion(
            id="q_foco",
            prompt=f"¿Qué foco conviene para la clase de {curso}?",
            options=[
                PlanOption(id="1", label="Comprensión con evidencia textual", suggested=True),
                PlanOption(id="2", label="Práctica guiada y modelamiento"),
                PlanOption(id="3", label="Producción / escritura breve"),
            ],
        )
    ]


def default_entregables(tipo: ArtifactType, encargo: Encargo) -> list[PlanDeliverable]:
    primary = PlanDeliverable(tipo=tipo, label=tipo.label.capitalize())
    # Multi-entregable when rumbo evaluar asks for both prueba + pauta
    if encargo.rumbo == "evaluar" and tipo is ArtifactType.EVALUACION:
        return [
            primary,
            PlanDeliverable(
                tipo=ArtifactType.PAUTA,
                label="Pauta/rúbrica",
                description="Acompañamiento de criterios para la misma evaluación.",
            ),
        ]
    if encargo.rumbo == "crear" and tipo is ArtifactType.GUIA:
        return [primary]
    return [primary]


def apply_plan_edits(plan: Plan, edits: dict[str, str] | None) -> Plan:
    if not edits:
        return plan
    tipo = ArtifactType.parse(edits.get("tipo") or plan.tipo.value) or plan.tipo
    decisiones = PlanDecisionFields(
        curso=(edits.get("curso") if "curso" in edits else plan.decisiones.curso).strip(),
        asignatura=(
            edits.get("asignatura") if "asignatura" in edits else plan.decisiones.asignatura
        ).strip(),
        tema=(edits.get("tema") if "tema" in edits else plan.decisiones.tema).strip(),
    )
    supuestos = list(plan.supuestos)
    if "supuesto" in edits or "supuestos" in edits:
        text = (edits.get("supuesto") or edits.get("supuestos") or "").strip()
        if text:
            if supuestos:
                supuestos[0] = PlanAssumption(
                    id=supuestos[0].id, text=text, editable=supuestos[0].editable
                )
            else:
                supuestos = [PlanAssumption(id="s1", text=text)]
    return Plan(
        objetivo=(edits.get("objetivo") or plan.objetivo).strip(),
        tipo=tipo,
        oa=(edits.get("oa") if "oa" in edits else plan.oa).strip(),
        duracion=(edits.get("duracion") if "duracion" in edits else plan.duracion).strip(),
        notas=(edits.get("notas") if "notas" in edits else plan.notas).strip(),
        titulo=(edits.get("titulo") if "titulo" in edits else plan.titulo).strip(),
        meta=plan.meta,
        resultado_previsto=list(plan.resultado_previsto),
        decisiones=decisiones,
        como_abordare=list(plan.como_abordare),
        supuestos=supuestos,
        questions=list(plan.questions),
        entregables=list(plan.entregables),
        status=plan.status,
    )


def answer_question(
    plan: Plan,
    *,
    question_id: str | None = None,
    option_id: str | None = None,
    free_text: str | None = None,
) -> Plan:
    """Apply a clarification answer; fold it into notas / supuestos."""
    target = None
    for question in plan.questions:
        if question_id and question.id == question_id:
            target = question
            break
        if question_id is None and question.answer is None and question.free_text is None:
            target = question
            break
    if target is None:
        raise TeroError("No hay pregunta de clarificación pendiente.", code="no_question")

    label = ""
    if option_id:
        for opt in target.options:
            if opt.id == option_id or opt.label.lower() == option_id.lower():
                target.answer = opt.id
                label = opt.label
                break
        if not label:
            target.answer = option_id
            label = option_id
    if free_text and free_text.strip():
        target.free_text = free_text.strip()
        if not label:
            label = free_text.strip()

    if not label:
        raise TeroError("Responde con un número de opción o con tus palabras.", code="empty_answer")

    # Fold into plan notes / approach
    note_line = f"Énfasis acordado: {label}."
    notas = (plan.notas + " " + note_line).strip() if plan.notas else note_line
    steps = list(plan.como_abordare)
    if steps and label:
        first = steps[0]
        steps[0] = PlanStep(titulo=first.titulo, detalle=f"{first.detalle} Foco: {label}.".strip())

    pending = any(q.answer is None and q.free_text is None for q in plan.questions)
    return Plan(
        objetivo=plan.objetivo,
        tipo=plan.tipo,
        oa=plan.oa,
        duracion=plan.duracion,
        notas=notas,
        titulo=plan.titulo,
        meta=plan.meta,
        resultado_previsto=list(plan.resultado_previsto),
        decisiones=plan.decisiones,
        como_abordare=steps,
        supuestos=list(plan.supuestos),
        questions=list(plan.questions),
        entregables=list(plan.entregables),
        status="propuesto" if not pending else "clarificando",
    )


def edit_assumption(plan: Plan, assumption_id: str, text: str) -> Plan:
    cleaned = text.strip()
    if not cleaned:
        raise TeroError("El supuesto no puede quedar vacío.", code="bad_supuesto")
    supuestos: list[PlanAssumption] = []
    found = False
    for item in plan.supuestos:
        if item.id == assumption_id or (assumption_id in {"1", "s1"} and item.id == "s1"):
            supuestos.append(PlanAssumption(id=item.id, text=cleaned, editable=item.editable))
            found = True
        else:
            supuestos.append(item)
    if not found and plan.supuestos:
        # edit first editable
        first = plan.supuestos[0]
        supuestos = [
            PlanAssumption(id=first.id, text=cleaned, editable=first.editable),
            *plan.supuestos[1:],
        ]
        found = True
    if not found:
        supuestos = [PlanAssumption(id="s1", text=cleaned)]
    return Plan(
        objetivo=plan.objetivo,
        tipo=plan.tipo,
        oa=plan.oa,
        duracion=plan.duracion,
        notas=plan.notas,
        titulo=plan.titulo,
        meta=plan.meta,
        resultado_previsto=list(plan.resultado_previsto),
        decisiones=plan.decisiones,
        como_abordare=list(plan.como_abordare),
        supuestos=supuestos,
        questions=list(plan.questions),
        entregables=list(plan.entregables),
        status=plan.status,
    )
