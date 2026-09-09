"""Strands tools. Read-only over the carpeta; plan/draft are in-memory until the teacher gates."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from strands import tool

from tero.evidence import parse_evidence_blob
from tero.plan import build_plan
from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence, Plan
from tero.workspace import Workspace

EmitFn = Callable[[dict[str, Any]], None]


@dataclass
class TurnContext:
    workspace: Workspace
    encargo: Encargo
    pending_plan: Plan | None = None
    pending_draft: ArtifactDraft | None = None
    evidence: list[Evidence] = field(default_factory=list)
    emit: EmitFn | None = None

    def _emit(self, event: dict[str, Any]) -> None:
        if self.emit:
            self.emit(event)


def build_tools(ctx: TurnContext, *, phase: str) -> list[Any]:
    tools: list[Any] = [_list_sources(ctx), _search_sources(ctx), _read_source(ctx)]
    if phase == "plan":
        tools.append(_propose_plan(ctx))
    if phase in {"draft", "correct"}:
        tools.extend([_cite_evidence(ctx), _draft_artifact(ctx)])
    return tools


def _list_sources(ctx: TurnContext):
    @tool
    def list_sources() -> str:
        """Lista archivos originales de la carpeta de trabajo (no derivados ni borradores)."""
        ctx._emit({"type": "activity", "tool": "list_sources", "state": "start"})
        records = ctx.workspace.list_sources()
        payload = [item.as_dict() for item in records]
        ctx._emit(
            {
                "type": "activity",
                "tool": "list_sources",
                "state": "end",
                "detail": f"{len(payload)} fuentes",
            }
        )
        return json.dumps({"fuentes": payload}, ensure_ascii=False)

    return list_sources


def _search_sources(ctx: TurnContext):
    @tool
    def search_sources(query: str) -> str:
        """Busca un texto solo dentro de la carpeta de trabajo."""
        ctx._emit({"type": "activity", "tool": "search_sources", "state": "start", "detail": query})
        hits = ctx.workspace.search(query)
        ctx._emit(
            {
                "type": "activity",
                "tool": "search_sources",
                "state": "end",
                "detail": f"{len(hits)} hallazgos",
            }
        )
        return json.dumps({"query": query, "hits": hits}, ensure_ascii=False)

    return search_sources


def _read_source(ctx: TurnContext):
    @tool
    def read_source(path: str) -> str:
        """Lee una fuente original. Comprueba el hash; nunca escribe el archivo."""
        ctx._emit({"type": "activity", "tool": "read_source", "state": "start", "detail": path})
        payload = ctx.workspace.read_source(path)
        ctx._emit({"type": "activity", "tool": "read_source", "state": "end", "detail": path})
        return json.dumps(payload, ensure_ascii=False)

    return read_source


def _propose_plan(ctx: TurnContext):
    @tool
    def propose_plan(
        objetivo: str,
        tipo: str,
        oa: str = "",
        duracion: str = "",
        notas: str = "",
    ) -> str:
        """Registra un plan tipado en memoria. No escribe archivos. El docente debe aprobarlo."""
        ctx._emit({"type": "activity", "tool": "plan", "state": "start"})
        plan = build_plan(
            objetivo=objetivo,
            tipo=tipo,
            oa=oa,
            duracion=duracion,
            notas=notas,
            encargo=ctx.encargo,
        )
        ctx.pending_plan = plan
        ctx._emit({"type": "activity", "tool": "plan", "state": "end", "detail": plan.tipo.label})
        return json.dumps(
            {
                "ok": True,
                "plan": plan.as_dict(),
                "mensaje": "Plan registrado. Detente: el docente debe aprobar, editar o cancelar.",
            },
            ensure_ascii=False,
        )

    return propose_plan


def _cite_evidence(ctx: TurnContext):
    @tool
    def cite_evidence(path: str, snippet: str, seccion: str = "") -> str:
        """Vincula un fragmento de una fuente a una sección de la propuesta. No escribe archivos."""
        ctx._emit({"type": "activity", "tool": "cite_evidence", "state": "start", "detail": path})
        item = Evidence(path=path, snippet=snippet, seccion=seccion)
        ctx.evidence.append(item)
        ctx._emit(
            {"type": "activity", "tool": "cite_evidence", "state": "end", "detail": seccion or path}
        )
        return json.dumps({"ok": True, "n": len(ctx.evidence)}, ensure_ascii=False)

    return cite_evidence


def _draft_artifact(ctx: TurnContext):
    @tool
    def draft_artifact(
        tipo: str, titulo: str, cuerpo_markdown: str, evidencias_json: str = "[]"
    ) -> str:
        """Entrega un borrador en memoria. No escribe a derivados. El docente decide s/n/b/c."""
        ctx._emit({"type": "activity", "tool": "draft", "state": "start", "detail": titulo})
        parsed = ArtifactType.parse(tipo)
        if parsed is None:
            return json.dumps(
                {"ok": False, "error": f"tipo desconocido: {tipo}"}, ensure_ascii=False
            )
        extra = parse_evidence_blob(evidencias_json)
        merged: list[Evidence] = []
        seen: set[tuple[str, str]] = set()
        for item in [*ctx.evidence, *extra]:
            key = (item.path, item.snippet[:80])
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        ctx.pending_draft = ArtifactDraft(
            tipo=parsed,
            titulo=titulo.strip() or parsed.label,
            cuerpo_markdown=cuerpo_markdown,
            evidencias=merged,
        )
        ctx._emit({"type": "activity", "tool": "draft", "state": "end", "detail": titulo})
        return json.dumps(
            {
                "ok": True,
                "titulo": ctx.pending_draft.titulo,
                "evidencias": len(merged),
                "mensaje": "Borrador en memoria. El docente revisa; tero no escribió archivos.",
            },
            ensure_ascii=False,
        )

    return draft_artifact
