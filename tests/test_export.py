from __future__ import annotations

from tero.export import export_docx, export_latex, export_markdown
from tero.workspace import Workspace
from tests.support import PEDIDO_PLANIFICACION, open_session


def test_export_md_and_docx(tmp_path):
    source = tmp_path / "a.md"
    source.write_text("# Título\n\nHola **mundo**.\n\n- uno\n", encoding="utf-8")
    md = export_markdown(source, tmp_path / "out.md")
    assert md.read_text(encoding="utf-8").startswith("# Título")
    docx = export_docx(source, tmp_path / "out.docx")
    assert docx.exists()
    assert docx.stat().st_size > 100


def test_export_del_artefacto_recien_escrito(workspace: Workspace, tmp_path):
    session = open_session(workspace)
    assert session.exportable_path() is None

    session.start_turn(PEDIDO_PLANIFICACION)
    session.aprobar()

    source = session.exportable_path()
    assert source is not None
    assert source.parent.name == "derivados"

    md = export_markdown(source, tmp_path / "plan.export.md")
    assert md.exists()
    assert "generado_por: tero" in md.read_text(encoding="utf-8")

    tex = export_latex(source, tmp_path / "plan.tex", tipo="planificacion")
    cuerpo = tex.read_text(encoding="utf-8")
    assert cuerpo.strip()
    assert "generado_por" not in cuerpo
