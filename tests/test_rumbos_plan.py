from __future__ import annotations

from tero.encargo_sync import apply_rumbo, sync_encargo_from_prompt
from tero.plan import answer_question, build_plan, edit_assumption
from tero.rumbos import Rumbo, domain_mismatch, infer_curso, tipo_for_rumbo
from tero.types import ArtifactType, Encargo


def test_rumbo_maps_to_tipo():
    assert tipo_for_rumbo(Rumbo.PLANIFICAR).value == "planificacion"
    assert tipo_for_rumbo(Rumbo.CREAR).value == "guia"
    assert tipo_for_rumbo(Rumbo.EVALUAR).value == "evaluacion"
    assert apply_rumbo(Encargo(), "2").rumbo == "crear"
    assert apply_rumbo(Encargo(), "crear").tipo is ArtifactType.GUIA


def test_sync_encargo_updates_curso_and_domain():
    base = Encargo(
        curso="4° básico",
        asignatura="Lenguaje y Comunicación",
        oa="OA 4",
        tipo=ArtifactType.PLANIFICACION,
    )
    synced = sync_encargo_from_prompt(
        base, "Guía de práctica de fracciones para 6° básico con selección múltiple"
    )
    assert "6°" in synced.curso
    assert "Matemática" in synced.asignatura
    assert synced.tipo is ArtifactType.GUIA
    warn = domain_mismatch(
        "fracciones 6° básico matemática",
        "fuentes/cuento-el-condor-y-el-huemul.md fuentes/bases-oa-lenguaje-4b.md",
    )
    assert warn is not None
    assert "matemática" in warn.lower() or "lenguaje" in warn.lower()


def test_infer_curso_variants():
    assert infer_curso("planificación 45 min") == ""
    assert infer_curso("4° básico") == "4° básico"
    assert infer_curso("4 basico") == "4° básico"
    assert "6°" in infer_curso("para 6to básico")
    # Duration chips must never become a grade.
    assert infer_curso("planificación de 45 minutos sobre el cuento") == ""
    assert infer_curso("duracion: 45 min") == ""


def test_sync_keeps_grado_when_prompt_only_has_duration():
    base = Encargo(curso="4° básico", asignatura="Lenguaje", oa="OA 4", duracion="45 min")
    synced = sync_encargo_from_prompt(
        base,
        "Prepara una planificación de 45 min sobre el cuento, alineada al OA.",
    )
    assert synced.curso == "4° básico"
    assert "45°" not in synced.curso


def test_plan_card_and_clarification():
    plan = build_plan(
        objetivo="Guía de fracciones",
        tipo="guia",
        encargo=Encargo(curso="6° básico", asignatura="Matemática", tema="fracciones"),
    )
    assert plan.titulo
    assert plan.resultado_previsto
    assert plan.decisiones.curso.startswith("6")
    assert plan.como_abordare
    assert plan.supuestos
    assert plan.pending_question() is not None
    answered = answer_question(plan, option_id="1")
    assert answered.pending_question() is None
    assert "Énfasis" in answered.notas
    edited = edit_assumption(answered, "s1", "Sesión de 90 minutos.")
    assert edited.supuestos[0].text.startswith("Sesión")
