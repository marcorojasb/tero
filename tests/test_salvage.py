"""Recover drafts when the model prints draft_artifact(...) as prose."""

from __future__ import annotations

from tero.salvage import salvage_draft_from_text
from tero.types import ArtifactType


def test_salvage_python_style_tool_call():
    blob = '''
Plan registrado. No redactes aún.draft_artifact(
  titulo="Prueba corta: Comprensión lectora - \\"El cóndor y el huemul\\"",
  tipo="evaluacion",
  cuerpo_markdown="""
# Prueba corta
## Selección múltiple
1. ¿Quién preguntó?
a) El huemul
b) El río
"""
)
'''
    draft = salvage_draft_from_text(blob)
    assert draft is not None
    assert draft.tipo == ArtifactType.EVALUACION
    assert "cóndor" in draft.titulo.lower() or "Prueba corta" in draft.titulo
    assert "Selección múltiple" in draft.cuerpo_markdown
    assert "huemul" in draft.cuerpo_markdown.lower()


def test_salvage_ignores_plain_prose():
    assert salvage_draft_from_text("Solo un comentario sin herramienta.") is None
