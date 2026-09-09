from __future__ import annotations

from pathlib import Path

from tero.config import PACKAGE_ROOT
from tero.workspace import Workspace

AULA = PACKAGE_ROOT / "fixtures" / "aula-5basico-agua"


def test_mvp_fixture_folder_is_readable_sor():
    assert AULA.is_dir()
    workspace = Workspace(AULA)
    paths = {item.relative_path for item in workspace.list_sources()}
    assert "01-oa-curriculo.md" in paths
    assert "05-glaciar-nota.pdf" in paths
    pdf = workspace.read_source("05-glaciar-nota.pdf")
    assert pdf["text"]
    assert not pdf["path"].startswith("derivados/")
    before = workspace.fingerprint_sources()
    workspace.write_artifact("derivados/probe.md", "ok")
    assert workspace.fingerprint_sources() == before
