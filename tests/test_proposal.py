"""Tests for the deterministic proposal composer."""

from tero.proposal import compose_proposal


def test_compose_cites_all_sources_and_oa() -> None:
    sources = {
        "01-oa-curriculo.md": "CN05 OA 12 distribución del agua dulce y salada.",
        "02-apuntes-docente.md": "Quiero partir de Petorca y el Pacífico.",
    }
    filename, markdown, citations = compose_proposal(sources, "Haz una clase de 90 min.")
    assert filename.endswith(".md")
    assert "01-oa-curriculo.md" in citations
    assert "02-apuntes-docente.md" in citations
    assert "CN05 OA 12" in markdown
    assert "Fuentes citadas" in markdown
    assert "90" in markdown
