"""Teacher approval gate: pretty-print the proposal and require an explicit decision."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Literal

from tero.workspace import Workspace

Decision = Literal["approve", "reject", "draft"]

YES = {"s", "si", "sí", "y", "yes", "ok"}
NO = {"n", "no"}
DRAFT = {"b", "borrador", "draft"}


def parse_hitl_input(prompt: str) -> dict | None:
    """Extract the tool-input JSON that HumanInTheLoop embeds in its prompt."""
    match = re.search(r"\n\s*Input:\s*(\{.*\})\s*$", prompt, re.DOTALL)
    if not match:
        marker = "Input:"
        if marker not in prompt:
            return None
        raw = prompt.split(marker, 1)[1].strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def format_proposal(data: dict | None, raw_prompt: str) -> str:
    """Human-readable Spanish preview of the pending write."""
    if not data:
        return raw_prompt
    filename = data.get("filename", "(sin nombre)")
    citations = data.get("citations", "")
    markdown = data.get("markdown", "")
    lines = [
        "",
        "─" * 64,
        "PROPUESTA PENDIENTE DE TU CRITERIO",
        "─" * 64,
        f"Archivo sugerido : {filename}",
        f"Fuentes citadas  : {citations}",
        "",
        markdown.strip() or "(propuesta vacía)",
        "",
        "─" * 64,
        "Los archivos originales NO se modificarán.",
        "s = escribir en derivados/   n = descartar   b = guardar borrador",
        "─" * 64,
    ]
    return "\n".join(lines)


def decide_from_text(text: str) -> Decision:
    """Map a typed answer to approve / reject / draft."""
    value = (text or "").strip().lower()
    if value in YES:
        return "approve"
    if value in DRAFT:
        return "draft"
    return "reject"


def make_ask(
    workspace: Workspace,
    *,
    auto: Decision | None = None,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> Callable[[str], str]:
    """Build a HumanInTheLoop `ask` callback.

    Returning 'yes' lets the write tool run. Returning 'no' cancels it.
    Draft mode approves the write but flags the workspace so the file lands
    under derivados/borradores/.
    """

    def ask(prompt: str, **kwargs: object) -> str:
        data = parse_hitl_input(prompt)
        print_fn(format_proposal(data, prompt))
        if auto is not None:
            decision = auto
            labels = {
                "approve": "sí (automático)",
                "reject": "no (automático)",
                "draft": "borrador (automático)",
            }
            print_fn(f"Decisión: {labels[decision]}")
        else:
            try:
                typed = input_fn("¿Escribir este derivado? [s]í / [N]o / [b]orrador: ")
            except EOFError:
                typed = "n"
            decision = decide_from_text(typed)
            if decision == "reject" and not (typed or "").strip():
                print_fn("Sin respuesta: se descarta la propuesta.")
            else:
                print_fn(f"Decisión: {decision}")

        if decision == "draft":
            workspace.as_draft = True
            return "yes"
        if decision == "approve":
            workspace.as_draft = False
            return "yes"
        workspace.as_draft = False
        return "no"

    return ask


def teacher_evaluate(response: object, **kwargs: object) -> bool:
    """Accept English and Spanish yes-values (HITL evaluate callback)."""
    if response is True:
        return True
    if isinstance(response, str):
        return decide_from_text(response) in {"approve", "draft"} or response.lower().strip() in YES
    return False
