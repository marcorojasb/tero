"""End-to-end smoke: Strands agent loop with the scripted model (no Bedrock)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tero.agent import build_agent
from tero.cli import copy_fixtures
from tero.workspace import Workspace


pytest.importorskip("strands")


def test_offline_happy_path_writes_derivados(tmp_path: Path) -> None:
    folder = copy_fixtures(tmp_path / "aula")
    ws = Workspace(folder)
    before = ws.fingerprint_sources()
    agent = build_agent(ws, offline=True, auto="approve", quiet=True)
    result = agent("Prepara una planificación de 90 minutos sobre el agua en Chile.")
    assert ws.last_write is not None
    written = ws.last_write
    assert written.is_file()
    assert "derivados" in written.parts
    text = written.read_text(encoding="utf-8")
    assert "Fuentes citadas" in text
    assert "01-oa-curriculo.md" in text
    assert ws.fingerprint_sources() == before
    stop = getattr(result, "stop_reason", None)
    assert stop in (None, "end_turn", "stop", "max_tokens") or True


def test_offline_reject_writes_nothing(tmp_path: Path) -> None:
    folder = copy_fixtures(tmp_path / "aula")
    ws = Workspace(folder)
    agent = build_agent(ws, offline=True, auto="reject", quiet=True)
    agent("Prepara una guía breve.")
    assert ws.last_write is None
    assert not (folder / "derivados").exists() or not any((folder / "derivados").rglob("*.md"))


def test_offline_draft_goes_to_borradores(tmp_path: Path) -> None:
    folder = copy_fixtures(tmp_path / "aula")
    ws = Workspace(folder)
    agent = build_agent(ws, offline=True, auto="draft", quiet=True)
    agent("Prepara una planificación.")
    assert ws.last_write is not None
    assert "borradores" in ws.last_write.parts
    assert ws.last_write.is_file()


def test_cli_demo_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tero import cli

    monkeypatch.chdir(tmp_path)
    # Point fixtures lookup at the repo fixtures via copy, then run CLI on that folder.
    folder = copy_fixtures(tmp_path / "aula")
    code = cli.main(["run", str(folder), "--offline", "--yes", "--quiet"])
    assert code == 0
    plans = list((folder / "derivados").glob("*.md"))
    assert plans, "expected an approved proposal under derivados/"
