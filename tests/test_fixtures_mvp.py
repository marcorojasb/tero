from __future__ import annotations

import shutil
from pathlib import Path

from tero.config import PACKAGE_ROOT
from tero.workspace import Workspace

AULA = PACKAGE_ROOT / "fixtures" / "aula-5basico-agua"


def _copy_aula(tmp_path: Path) -> Path:
    dest = tmp_path / "aula"
    shutil.copytree(AULA, dest, ignore=shutil.ignore_patterns("derivados", "borradores", ".tero"))
    return dest


def test_mvp_fixture_folder_is_readable_sor(tmp_path: Path):
    assert AULA.is_dir()
    dest = _copy_aula(tmp_path)
    workspace = Workspace(dest)
    paths = {item.relative_path for item in workspace.list_sources()}
    assert "01-oa-curriculo.md" in paths
    assert "05-glaciar-nota.pdf" in paths
    pdf = workspace.read_source("05-glaciar-nota.pdf")
    assert pdf["text"]
    assert not pdf["path"].startswith("derivados/")
    before = workspace.fingerprint_sources()
    workspace.write_artifact("derivados/probe.md", "ok")
    assert workspace.fingerprint_sources() == before
