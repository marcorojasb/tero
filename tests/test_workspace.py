"""Tests for the sandboxed teacher workspace."""

from __future__ import annotations

from pathlib import Path

import pytest

from tero.workspace import Workspace, WorkspaceError


def _folder(tmp_path: Path) -> Path:
    (tmp_path / "nota.md").write_text("# Hola\ncontenido", encoding="utf-8")
    (tmp_path / "extra.txt").write_text("texto", encoding="utf-8")
    return tmp_path


def test_list_skips_derivados(tmp_path: Path) -> None:
    folder = _folder(tmp_path)
    hidden = folder / "derivados"
    hidden.mkdir()
    (hidden / "no-es-fuente.md").write_text("x", encoding="utf-8")
    ws = Workspace(folder)
    names = [s.relative_path for s in ws.list_sources()]
    assert "nota.md" in names
    assert "extra.txt" in names
    assert "derivados/no-es-fuente.md" not in names


def test_rejects_path_traversal(tmp_path: Path) -> None:
    folder = _folder(tmp_path)
    ws = Workspace(folder)
    with pytest.raises(WorkspaceError):
        ws.read_text("../nota.md")


def test_write_derived_does_not_touch_originals(tmp_path: Path) -> None:
    folder = _folder(tmp_path)
    ws = Workspace(folder)
    before = ws.fingerprint_sources()
    dest = ws.write_derived("plan.md", "# Plan\n\nHola", ["nota.md"])
    assert dest == folder / "derivados" / "plan.md"
    assert dest.is_file()
    assert (folder / "nota.md").read_text(encoding="utf-8") == "# Hola\ncontenido"
    assert ws.fingerprint_sources() == before


def test_write_requires_real_citations(tmp_path: Path) -> None:
    folder = _folder(tmp_path)
    ws = Workspace(folder)
    with pytest.raises(WorkspaceError, match="Citas"):
        ws.write_derived("plan.md", "# Plan", ["no-existe.md"])


def test_rejects_unsafe_filename(tmp_path: Path) -> None:
    folder = _folder(tmp_path)
    ws = Workspace(folder)
    with pytest.raises(WorkspaceError):
        ws.write_derived("../../etc.md", "# x", ["nota.md"])
    with pytest.raises(WorkspaceError):
        ws.write_derived("plan.txt", "# x", ["nota.md"])


def test_draft_lands_in_borradores(tmp_path: Path) -> None:
    folder = _folder(tmp_path)
    ws = Workspace(folder)
    ws.as_draft = True
    dest = ws.write_derived("plan.md", "# Borrador", ["nota.md"])
    assert dest == folder / "derivados" / "borradores" / "plan.md"
    assert ws.as_draft is False


def test_read_fixture_pdf(tmp_path: Path) -> None:
    from tero.cli import copy_fixtures

    folder = copy_fixtures(tmp_path / "aula")
    ws = Workspace(folder)
    text = ws.read_text("05-glaciar-nota.pdf")
    assert "Campo de Hielo Sur" in text


def test_pdf_is_listed(tmp_path: Path) -> None:
    pytest.importorskip("pypdf")
    from pypdf import PdfWriter

    pdf_path = tmp_path / "glaciar.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=400, height=200)
    writer.write(pdf_path)
    ws = Workspace(tmp_path)
    listed = [s.relative_path for s in ws.list_sources()]
    assert "glaciar.pdf" in listed
    with pytest.raises(WorkspaceError, match="PDF|texto"):
        ws.read_text("glaciar.pdf")
