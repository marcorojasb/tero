"""Teacher gate: s accept, n discard, b draft, c correct. Host writes files — never the model."""

from __future__ import annotations

from dataclasses import dataclass
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
) -> GateResult:
    if decision == "n":
        return GateResult(decision="n", path=None, markdown=None, note=note)
    if decision == "c":
        return GateResult(decision="c", path=None, markdown=None, note=note)

    markdown = materialize_markdown(encargo, plan, draft)
    filename = artifact_filename(draft.tipo, draft.titulo)
    if decision == "s":
        path = write_accepted(workspace, filename, markdown)
        return GateResult(decision="s", path=path, markdown=markdown, note=note)
    if decision == "b":
        path = write_draft(workspace, filename, markdown)
        return GateResult(decision="b", path=path, markdown=markdown, note=note)
    raise ValueError(f"Decisión de puerta desconocida: {decision}")
