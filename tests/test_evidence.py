from __future__ import annotations

from tero.artifacts import missing_headings
from tero.evidence import collect_warnings, parse_evidence_blob, snippet_in_text, verify_evidence
from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence
from tero.workspace import Workspace


def test_parse_evidence_json():
    items = parse_evidence_blob('[{"path":"fuentes/a.md","snippet":"hola","seccion":"inicio"}]')
    assert items[0].path == "fuentes/a.md"
    assert items[0].seccion == "inicio"


def test_warnings_oa_and_thin(workspace: Workspace):
    draft = ArtifactDraft(
        tipo=ArtifactType.EVALUACION,
        titulo="corta",
        cuerpo_markdown="# Hola\n\nNada más.",
        evidencias=[Evidence(path="fuentes/no-existe.md", snippet="x")],
    )
    warnings = collect_warnings(
        workspace=workspace,
        encargo=Encargo(oa="OA 4"),
        draft=draft,
    )
    codes = {item.code for item in warnings}
    assert "thin_skeleton" in codes
    assert "missing_rubric" in codes
    assert "unknown_source" in codes
    assert all(item.blocking is False for item in warnings)
    assert "unverified_citation" not in codes or "unknown_source" in codes


def test_oa_unknown_skipped_when_catalog_does_not_cover(workspace: Workspace):
    draft = ArtifactDraft(
        tipo=ArtifactType.EVALUACION,
        titulo="Sistemas",
        cuerpo_markdown="# Evaluación\n\n## Instrucciones\nLee.\n## Ítems\n1. x\n## Criterios\nPasos\n"
        + "x" * 800,
        evidencias=[
            Evidence(path="fuentes/notas-curso.md", snippet="OA"),
            Evidence(path="fuentes/cuento-el-condor-y-el-huemul.md", snippet="huemul"),
        ],
    )
    warnings = collect_warnings(
        workspace=workspace,
        encargo=Encargo(curso="1° medio", asignatura="Matemática", oa="sistemas 2x2"),
        draft=draft,
    )
    codes = {item.code for item in warnings}
    assert "oa_unknown" not in codes


def test_snippet_must_appear_in_source(workspace: Workspace):
    assert snippet_in_text("hola mundo largo", "hola mundo")
    assert not snippet_in_text("hola mundo", "no está")
    ok = verify_evidence(
        workspace,
        Evidence(
            path="fuentes/cuento-el-condor-y-el-huemul.md",
            snippet="El huemul no corrió: preguntó al cóndor por qué el valle tenía sed.",
        ),
    )
    assert ok.verified is True
    fake = verify_evidence(
        workspace,
        Evidence(path="fuentes/cuento-el-condor-y-el-huemul.md", snippet="Los pingüinos votaron"),
    )
    assert fake.verified is False
    draft = ArtifactDraft(
        tipo=ArtifactType.ACTIVIDAD,
        titulo="x",
        cuerpo_markdown="# Actividad\n\n## Objetivo\n...\n## Materiales\n...\n## Pasos\n..."
        + "x" * 800,
        evidencias=[
            Evidence(
                path="fuentes/cuento-el-condor-y-el-huemul.md", snippet="Los pingüinos votaron"
            ),
            Evidence(path="fuentes/notas-curso.md", snippet="x"),
        ],
    )
    warnings = collect_warnings(
        workspace=workspace,
        encargo=Encargo(oa="OA 4"),
        draft=draft,
    )
    assert "unverified_citation" in {item.code for item in warnings}
    unverified = [item for item in warnings if item.code == "unverified_citation"]
    assert len(unverified) == 1
    assert "cuento-el-condor-y-el-huemul.md" in unverified[0].message
    assert "notas-curso.md" in unverified[0].message


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
