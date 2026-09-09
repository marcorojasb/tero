from __future__ import annotations

from tero.export import export_docx, export_markdown


def test_export_md_and_docx(tmp_path):
    source = tmp_path / "a.md"
    source.write_text("# Título\n\nHola **mundo**.\n\n- uno\n", encoding="utf-8")
    md = export_markdown(source, tmp_path / "out.md")
    assert md.read_text(encoding="utf-8").startswith("# Título")
    docx = export_docx(source, tmp_path / "out.docx")
    assert docx.exists()
    assert docx.stat().st_size > 100
