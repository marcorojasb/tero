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
        plan=None,
        draft=draft,
    )
    codes = {item.code for item in warnings}
    assert "thin_skeleton" in codes
    assert "missing_rubric" in codes
    assert "unknown_source" in codes
    # thin_evidence / unknown_source block s→derivados (teacher can still use b/c/forzar).
    by_code = {item.code: item for item in warnings}
    assert by_code["unknown_source"].blocking is True
    assert by_code["thin_evidence"].blocking is True
    assert by_code["thin_skeleton"].blocking is False
    assert "unverified_citation" not in codes or "unknown_source" in codes


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
        plan=None,
        draft=draft,
    )
    assert "unverified_citation" in {item.code for item in warnings}


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
