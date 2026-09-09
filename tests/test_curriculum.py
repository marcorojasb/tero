"""Currículum Chile catalog — host-side OA selection."""

from __future__ import annotations

from tero.curriculum.catalog import (
    get_catalog,
    get_oa,
    list_oa,
    normalize_asignatura,
    normalize_curso,
    resolve_oa,
    search_oa,
    validate_oa_id,
)


def test_catalog_loads_minimal_set():
    catalog = get_catalog()
    assert catalog.meta.get("disclaimer")
    assert len(catalog.oas) >= 27
    cursos = {row["id"] for row in catalog.cursos}
    assert {"4b", "5b", "6b"} <= cursos
    asigs = {row["id"] for row in catalog.asignaturas}
    assert {"lenguaje", "matematica", "ciencias"} <= asigs


def test_list_oa_filters_curso_asignatura():
    rows = list_oa("4° básico", "Lenguaje")
    assert rows
    assert all(item.curso == "4b" and item.asignatura == "lenguaje" for item in rows)
    assert any(item.id == "LEN-4B-OA04" for item in rows)


def test_get_oa_and_validate():
    record = get_oa("LEN-4B-OA04")
    assert record is not None
    assert "explícita" in record.texto_corto or "explicita" in record.texto_corto.lower()
    assert validate_oa_id("LEN-4B-OA04")
    assert not validate_oa_id("FAKE-OA-999")


def test_search_oa_fracciones():
    hits = search_oa("fracciones 6")
    assert hits
    assert any(item.asignatura == "matematica" for item in hits)


def test_resolve_oa_codigo_with_context():
    resolved = resolve_oa("OA 4", curso="4° básico", asignatura="Lenguaje y Comunicación")
    assert resolved is not None
    assert resolved.id == "LEN-4B-OA04"


def test_normalize_helpers():
    assert normalize_curso("6° básico") == "6b"
    assert normalize_asignatura("Matemáticas") == "matematica"
    assert normalize_asignatura("Ciencias Naturales") == "ciencias"
