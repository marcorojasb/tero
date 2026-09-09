"""Tests for tools and the teacher approval gate (no Bedrock)."""

from __future__ import annotations

from pathlib import Path

from tero.approval import decide_from_text, make_ask, parse_hitl_input, teacher_evaluate
from tero.tools import build_tools
from tero.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    (tmp_path / "oa.md").write_text("CN05 OA 12 agua dulce", encoding="utf-8")
    return Workspace(tmp_path)


def test_tools_list_read_write(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    list_sources, read_source, write_derived = build_tools(ws)
    listing = list_sources()
    assert "oa.md" in listing
    body = read_source("oa.md")
    assert "tero:source" in body
    assert "CN05 OA 12" in body
    result = write_derived("guia.md", "# Guía\n\nHola", "oa.md")
    assert "derivados/guia.md" in result
    assert (tmp_path / "derivados" / "guia.md").is_file()


def test_approval_yes_writes(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ask = make_ask(ws, auto="approve", print_fn=lambda _: None)
    assert ask('Approve "write_derived"?\n  Input: {"filename": "x.md"}') == "yes"


def test_approval_no_does_not_flag_draft(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ask = make_ask(ws, auto="reject", print_fn=lambda _: None)
    assert ask("Approve?\n  Input: {}") == "no"
    assert ws.as_draft is False


def test_approval_draft_sets_flag(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ask = make_ask(ws, auto="draft", print_fn=lambda _: None)
    assert ask("Approve?\n  Input: {}") == "yes"
    assert ws.as_draft is True


def test_interactive_spanish_yes(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ask = make_ask(ws, input_fn=lambda _: "sí", print_fn=lambda _: None)
    assert ask("Approve?\n  Input: {}") == "yes"


def test_decide_and_evaluate() -> None:
    assert decide_from_text("s") == "approve"
    assert decide_from_text("b") == "draft"
    assert decide_from_text("") == "reject"
    assert teacher_evaluate("yes")
    assert teacher_evaluate("s")
    assert teacher_evaluate("sí")
    assert not teacher_evaluate("no")


def test_parse_hitl_input() -> None:
    prompt = 'Approve "write_derived"?\n  Input: {"filename": "plan.md", "markdown": "# Hola"}'
    data = parse_hitl_input(prompt)
    assert data is not None
    assert data["filename"] == "plan.md"
