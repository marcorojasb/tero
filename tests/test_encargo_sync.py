"""Chips del encargo: el contexto se sincroniza desde el mensaje, sin flujo por pasos."""

from __future__ import annotations

from tero.encargo_sync import source_domain_warning, sync_encargo_from_prompt
from tero.rumbos import domain_mismatch, infer_curso, infer_tema
from tero.types import ArtifactType, Encargo
from tero.workspace import Workspace


def test_sync_encargo_actualiza_curso_asignatura_y_tipo():
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
    assert synced.oa == "OA 4"


def test_sync_conserva_el_curso_cuando_el_mensaje_solo_trae_duracion():
    base = Encargo(curso="4° básico", asignatura="Lenguaje", oa="OA 4", duracion="45 min")
    synced = sync_encargo_from_prompt(
        base,
        "Prepara una planificación de 45 min sobre el cuento, alineada al OA.",
    )
    assert synced.curso == "4° básico"
    assert "45°" not in synced.curso


def test_infer_tema_ignora_los_saludos():
    assert infer_tema("hola") == ""
    assert infer_tema("gracias") == ""
    assert "cuento" in infer_tema("planificación del cuento").lower()


def test_infer_curso_variantes():
    assert infer_curso("planificación 45 min") == ""
    assert infer_curso("4° básico") == "4° básico"
    assert infer_curso("4 basico") == "4° básico"
    assert "6°" in infer_curso("para 6to básico")
    # Una duración nunca debe volverse un curso.
    assert infer_curso("planificación de 45 minutos sobre el cuento") == ""
    assert infer_curso("duracion: 45 min") == ""


def test_domain_mismatch_avisa_sin_bloquear():
    warn = domain_mismatch(
        "fracciones 6° básico matemática",
        "fuentes/cuento-el-condor-y-el-huemul.md fuentes/bases-oa-lenguaje-4b.md",
    )
    assert warn is not None
    assert "matemática" in warn.lower() or "lenguaje" in warn.lower()


def test_source_domain_warning_usa_las_fuentes_de_la_carpeta(workspace: Workspace):
    aviso = source_domain_warning(
        workspace,
        "Prepara una guía de fracciones equivalentes para 6° básico de matemática.",
        Encargo(curso="6° básico", asignatura="Matemática"),
    )
    assert aviso is not None
    sin_aviso = source_domain_warning(
        workspace,
        "Prepara una guía de comprensión lectora del cuento.",
        Encargo(curso="4° básico", asignatura="Lenguaje y Comunicación"),
    )
    assert sin_aviso is None
