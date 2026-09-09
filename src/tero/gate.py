"""Teacher gate: s accept, n discard, b draft, c correct. Host writes files — never the model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from tero.artifacts import artifact_filename, materialize_markdown, write_accepted, write_draft
from tero.types import ArtifactDraft, Encargo, GateDecision, Plan
from tero.workspace import Workspace


@dataclass
class GateResult:
    decision: GateDecision
    path: Path | None
    markdown: str | None
    note: str = ""


def apply_gate(
    *,
    workspace: Workspace,
    encargo: Encargo,
    plan: Plan | None,
    draft: ArtifactDraft,
    decision: GateDecision,
    note: str = "",
    critique_notes: list[str] | None = None,
) -> GateResult:
    if decision == "n":
        return GateResult(decision="n", path=None, markdown=None, note=note)
    if decision == "c":
        return GateResult(decision="c", path=None, markdown=None, note=note)

    markdown = materialize_markdown(encargo, plan, draft)
    if critique_notes:
        markdown = _append_critique_appendix(markdown, critique_notes)
    filename = artifact_filename(draft.tipo, draft.titulo)
    if decision == "s":
        path = write_accepted(workspace, filename, markdown)
        return GateResult(decision="s", path=path, markdown=markdown, note=note)
    if decision == "b":
        path = write_draft(workspace, filename, markdown)
        return GateResult(decision="b", path=path, markdown=markdown, note=note)
    raise ValueError(f"Decisión de puerta desconocida: {decision}")


def persist_critique(workspace: Workspace, turn_id: str, note: str) -> Path:
    """Persist a `c` critique note under .tero/ so it survives a failed rewrite."""
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    relative = f".tero/criticas/{stamp}-{turn_id}.md"
    body = f"# Crítica docente\n\n- turn: `{turn_id}`\n- utc: {stamp}\n\n{note.strip()}\n"
    return workspace.write_artifact(relative, body, overwrite=True)


def _append_critique_appendix(markdown: str, notes: list[str]) -> str:
    lines = ["", "## Críticas docentes (sesión)", ""]
    for i, note in enumerate(notes, start=1):
        lines.append(f"{i}. {note.strip()}")
    lines.append("")
    return markdown.rstrip() + "\n" + "\n".join(lines)
