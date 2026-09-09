from __future__ import annotations

from tests.conftest import open_demo

from tero.artifacts import missing_headings
from tero.evidence import collect_warnings, parse_evidence_blob
from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence


def test_parse_evidence_json():
    items = parse_evidence_blob('[{"path":"fuentes/a.md","snippet":"hola","seccion":"inicio"}]')
    assert items[0].path == "fuentes/a.md"
    assert items[0].seccion == "inicio"


def test_warnings_oa_and_thin(tmp_path):
    workspace = open_demo(tmp_path)
    draft = ArtifactDraft(
        tipo=ArtifactType.EVALUACION,
        titulo="corta",
        cuerpo_markdown="# Hola\n\nNada más.",
        evidencias=[Evidence(path="fuentes/no-existe.md", snippet="x")],
    )
    warnings = collect_warnings(
        workspace=workspace,
        encargo=Encargo(oa="OA 4"),
        plan=None,
        draft=draft,
    )
    codes = {item.code for item in warnings}
    assert "thin_skeleton" in codes
    assert "missing_rubric" in codes
    assert "unknown_source" in codes
    assert all(item.blocking is False for item in warnings)


def test_planificacion_structure_ok():
    body = """
## Objetivo
x
## OA
OA 4
## Inicio
x
## Desarrollo
x
## Cierre
x
## Evaluación
x
"""
    assert missing_headings(ArtifactType.PLANIFICACION, body) == []
