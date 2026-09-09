from __future__ import annotations

import pytest

from tero.errors import WriteGuardError
from tero.hashutil import sha256_file
from tero.workspace import Workspace


def test_list_and_read_only_inside_carpeta(workspace: Workspace):
    sources = workspace.list_sources()
    paths = {item.relative_path for item in sources}
    assert any(path.startswith("fuentes/") for path in paths)
    assert not any(path.startswith("derivados/") for path in paths)
    payload = workspace.read_source("fuentes/cuento-el-condor-y-el-huemul.md")
    assert "huemul" in payload["text"].lower()
    assert payload["changed"] is False


def test_never_overwrite_originals(workspace: Workspace):
    with pytest.raises(WriteGuardError):
        workspace.write_artifact("fuentes/cuento-el-condor-y-el-huemul.md", "hack")
    original = workspace.root / "fuentes" / "cuento-el-condor-y-el-huemul.md"
    digest = sha256_file(original)
    workspace.write_artifact("derivados/ok.md", "si")
    assert sha256_file(original) == digest
    assert (workspace.root / "derivados" / "ok.md").read_text(encoding="utf-8") == "si"


def test_path_escape_rejected(workspace: Workspace):
    with pytest.raises(Exception):
        workspace.resolve_source("../secret.md")


def test_hash_change_is_flagged_not_rewritten(workspace: Workspace):
    workspace.rebuild_index()
    target = workspace.root / "fuentes" / "notas-curso.md"
    original = target.read_text(encoding="utf-8")
    target.write_text(original + "\n# extra\n", encoding="utf-8")
    payload = workspace.read_source("fuentes/notas-curso.md")
    assert payload["changed"] is True
    assert "no lo sobreescribe" in payload["warning"]
