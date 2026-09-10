"""Strands tools. Read-only over the carpeta; plan/draft are in-memory until the teacher gates."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from strands import tool

from tero.coerce import as_text
from tero.curriculum.catalog import catalog_covers_curso, normalize_curso
from tero.curriculum.catalog import get_oa as catalog_get_oa
from tero.curriculum.catalog import list_oa as catalog_list_oa
from tero.curriculum.catalog import resolve_oa as catalog_resolve_oa
from tero.curriculum.catalog import search_oa as catalog_search_oa
from tero.evidence import parse_evidence_blob, snippet_in_text, verify_evidence
from tero.latex.schemas import parse_payload_json
from tero.plan import build_plan
from tero.types import ArtifactDraft, ArtifactType, Encargo, Evidence, Plan
from tero.workspace import Workspace

EmitFn = Callable[[dict[str, Any]], None]

# Draft-phase host cap: Qwen-style cite_evidence loops are not "esmerado".
DRAFT_TOOL_BUDGET = 16
DRAFT_AGENT_TURNS = 18
PLAN_TOOL_BUDGET = 12
PLAN_AGENT_TURNS = 12

_UNCOVERED_HINT = (
    "Este curso no está en el catálogo Chile de tero. "
    "No elijas un OA de 4°–6° básico de relleno; deja el OA en texto libre."
)


@dataclass
class TurnContext:
    workspace: Workspace
    encargo: Encargo
    pending_plan: Plan | None = None
    pending_draft: ArtifactDraft | None = None
    evidence: list[Evidence] = field(default_factory=list)
    emit: EmitFn | None = None
    tool_calls: int = 0
    tool_budget: int | None = None
    budget_exhausted: bool = False

    def _emit(self, event: dict[str, Any]) -> None:
        if self.emit:
            self.emit(event)

    def reset_tool_budget(self, n: int | None) -> None:
        self.tool_calls = 0
        self.tool_budget = n
        self.budget_exhausted = False

    def consume_tool(self, name: str) -> str | None:
        """Return an error JSON if the host tool budget is spent or a deliverable exists."""
        if self.tool_budget is None:
            return None
        if self.pending_draft is not None:
            if name == "draft_artifact":
                return json.dumps(
                    {
                        "ok": True,
                        "already": True,
                        "titulo": self.pending_draft.titulo,
                        "hint": "Ya hay un borrador en memoria. Detente; el docente decide s/n/b/c.",
                    },
                    ensure_ascii=False,
                )
            return json.dumps(
                {
                    "ok": False,
                    "error": "borrador_ya_entregado",
                    "hint": "Ya hay un borrador. No llames más tools.",
                },
                ensure_ascii=False,
            )
        if name == "propose_plan" and self.pending_plan is not None:
            return json.dumps(
                {
                    "ok": True,
                    "already": True,
                    "hint": "El plan ya está registrado. Detente y espera al docente.",
                },
                ensure_ascii=False,
            )
        last_chance = name in {"draft_artifact", "propose_plan"}
        if self.tool_calls >= self.tool_budget:
            self.budget_exhausted = True
            if last_chance:
                return None
            return json.dumps(
                {
                    "ok": False,
                    "error": "presupuesto_herramientas_agotado",
                    "hint": (
                        "Llama draft_artifact ahora con cuerpo_markdown y, "
                        "si puedes, payload_json del schema."
                        if name != "propose_plan"
                        else "Llama propose_plan ahora y detente."
                    ),
                },
                ensure_ascii=False,
            )
        self.tool_calls += 1
        return None


def _blocked(ctx: TurnContext, name: str) -> str | None:
    err = ctx.consume_tool(name)
    if err:
        ctx._emit(
            {"type": "activity", "tool": name, "state": "end", "detail": "presupuesto agotado"}
        )
    return err


def build_tools(ctx: TurnContext, *, phase: str) -> list[Any]:
    tools: list[Any] = [
        _list_sources(ctx),
        _search_sources(ctx),
        _read_source(ctx),
        _list_oa(ctx),
        _get_oa(ctx),
        _search_oa(ctx),
    ]
    if phase == "plan":
        tools.extend(
            [_propose_plan(ctx), _cite_evidence_plan_stub(ctx), _draft_artifact_plan_stub(ctx)]
        )
    if phase in {"draft", "correct"}:
        tools.extend([_cite_evidence(ctx), _draft_artifact(ctx)])
    return tools


def _list_sources(ctx: TurnContext):
    @tool
    def list_sources() -> str:
        """Lista archivos originales de la carpeta de trabajo (no derivados ni borradores)."""
        blocked = _blocked(ctx, "list_sources")
        if blocked:
            return blocked
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
        query = as_text(query, joiner=" ")
        blocked = _blocked(ctx, "search_sources")
        if blocked:
            return blocked
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
        path = as_text(path, joiner=" ")
        blocked = _blocked(ctx, "read_source")
        if blocked:
            return blocked
        ctx._emit({"type": "activity", "tool": "read_source", "state": "start", "detail": path})
        payload = ctx.workspace.read_source(path)
        ctx._emit({"type": "activity", "tool": "read_source", "state": "end", "detail": path})
        return json.dumps(payload, ensure_ascii=False)

    return read_source


def _list_oa(ctx: TurnContext):
    @tool
    def list_oa(curso: str = "", asignatura: str = "") -> str:
        """Lista OA del catálogo Chile (host). No inventes ids: elige de esta lista."""
        curso_q = curso or ctx.encargo.curso
        asig_q = asignatura or ctx.encargo.asignatura
        blocked = _blocked(ctx, "list_oa")
        if blocked:
            return blocked
        ctx._emit(
            {
                "type": "activity",
                "tool": "list_oa",
                "state": "start",
                "detail": f"{curso_q} · {asig_q}".strip(" ·"),
            }
        )
        covers = catalog_covers_curso(curso_q)
        encargo_covers = catalog_covers_curso(ctx.encargo.curso)
        rows = catalog_list_oa(curso_q, asig_q) if covers else []
        payload = [item.as_dict() for item in rows]
        hint = ""
        if not covers:
            hint = _UNCOVERED_HINT
        elif not encargo_covers and covers:
            hint = (
                "El encargo no está cubierto por el catálogo. "
                "No uses estos OA de otro curso como si fueran del encargo."
            )
        ctx._emit(
            {
                "type": "activity",
                "tool": "list_oa",
                "state": "end",
                "detail": f"{len(payload)} OA",
            }
        )
        ctx._emit(
            {
                "type": "oa_options",
                "oas": payload,
                "curso": curso_q,
                "asignatura": asig_q,
                "catalog_covers": covers,
            }
        )
        return json.dumps(
            {
                "curso": curso_q,
                "asignatura": asig_q,
                "oas": payload,
                "catalog_covers": covers,
                "encargo_catalog_covers": encargo_covers,
                "hint": hint,
                "disclaimer": "Paráfrasis orientativas; no texto oficial MINEDUC verbatim.",
            },
            ensure_ascii=False,
        )

    return list_oa


def _get_oa(ctx: TurnContext):
    @tool
    def get_oa(id: str) -> str:
        """Obtiene un OA por id de catálogo (p. ej. LEN-4B-OA04). Falla si el id no existe."""
        blocked = _blocked(ctx, "get_oa")
        if blocked:
            return blocked
        ctx._emit({"type": "activity", "tool": "get_oa", "state": "start", "detail": id})
        record = catalog_get_oa(id)
        encargo_covers = catalog_covers_curso(ctx.encargo.curso)
        if record is None:
            ctx._emit(
                {"type": "activity", "tool": "get_oa", "state": "end", "detail": "no encontrado"}
            )
            return json.dumps(
                {
                    "ok": False,
                    "error": f"OA id desconocido: {id}. Usa list_oa o search_oa; no inventes ids.",
                    "catalog_covers": encargo_covers,
                    "hint": "" if encargo_covers else _UNCOVERED_HINT,
                },
                ensure_ascii=False,
            )
        encargo_curso_id = normalize_curso(ctx.encargo.curso) if ctx.encargo.curso else None
        matches = (encargo_curso_id is None) or (record.curso == encargo_curso_id)
        ctx._emit({"type": "activity", "tool": "get_oa", "state": "end", "detail": record.codigo})
        hint = ""
        if not encargo_covers:
            hint = _UNCOVERED_HINT
        elif not matches:
            hint = (
                f"El OA {record.id} es de {record.curso_label}, no de {ctx.encargo.curso}. "
                "No lo uses de relleno."
            )
        return json.dumps(
            {
                "ok": True,
                "oa": record.as_dict(),
                "catalog_covers": encargo_covers,
                "oa_matches_encargo_curso": matches,
                "hint": hint,
            },
            ensure_ascii=False,
        )

    return get_oa


def _search_oa(ctx: TurnContext):
    @tool
    def search_oa(q: str) -> str:
        """Busca OA en el catálogo Chile por texto (eje, código, palabras del OA)."""
        blocked = _blocked(ctx, "search_oa")
        if blocked:
            return blocked
        ctx._emit({"type": "activity", "tool": "search_oa", "state": "start", "detail": q})
        covers = catalog_covers_curso(ctx.encargo.curso)
        if not covers:
            ctx._emit(
                {"type": "activity", "tool": "search_oa", "state": "end", "detail": "0 hallazgos"}
            )
            return json.dumps(
                {
                    "query": q,
                    "oas": [],
                    "catalog_covers": False,
                    "hint": _UNCOVERED_HINT,
                },
                ensure_ascii=False,
            )
        rows = catalog_search_oa(q)
        payload = [item.as_dict() for item in rows]
        ctx._emit(
            {
                "type": "activity",
                "tool": "search_oa",
                "state": "end",
                "detail": f"{len(payload)} hallazgos",
            }
        )
        return json.dumps(
            {"query": q, "oas": payload, "catalog_covers": True},
            ensure_ascii=False,
        )

    return search_oa


def _propose_plan(ctx: TurnContext):
    @tool
    def propose_plan(
        objetivo: str,
        tipo: str,
        oa: str = "",
        duracion: str = "",
        notas: str = "",
        titulo: str = "",
        tema: str = "",
        curso: str = "",
        asignatura: str = "",
    ) -> str:
        """Registra un plan tipado (card Pteron) en memoria. No escribe archivos."""
        objetivo = as_text(objetivo, joiner=" ")
        tipo = as_text(tipo, joiner=" ")
        oa = as_text(oa, joiner=" ")
        duracion = as_text(duracion, joiner=" ")
        notas = as_text(notas, joiner=" ")
        titulo = as_text(titulo, joiner=" ")
        tema = as_text(tema, joiner=" ")
        curso = as_text(curso, joiner=" ")
        asignatura = as_text(asignatura, joiner=" ")
        blocked = _blocked(ctx, "propose_plan")
        if blocked:
            return blocked
        ctx._emit({"type": "activity", "tool": "plan", "state": "start"})
        decisiones = {
            "curso": curso or ctx.encargo.curso,
            "asignatura": asignatura or ctx.encargo.asignatura,
            "tema": tema or ctx.encargo.tema,
        }
        # Prefer catalog id / código when the model passes a known OA.
        resolved = catalog_resolve_oa(
            oa or ctx.encargo.oa,
            curso=decisiones["curso"],
            asignatura=decisiones["asignatura"],
        )
        oa_value = resolved.chip() if resolved else (oa or ctx.encargo.oa)
        plan = build_plan(
            objetivo=objetivo,
            tipo=tipo,
            oa=oa_value,
            duracion=duracion,
            notas=notas,
            encargo=ctx.encargo,
            decisiones=decisiones,
            titulo=titulo,
        )
        ctx.pending_plan = plan
        detail = plan.tipo.label
        if plan.pending_question():
            detail = f"{detail} · clarificación"
        ctx._emit({"type": "activity", "tool": "plan", "state": "end", "detail": detail})
        # Do not echo Plan.as_dict(): GLM pastes that card into payload_json.
        return json.dumps(
            {
                "ok": True,
                "tipo": plan.tipo.value,
                "titulo": plan.titulo,
                "n_preguntas": len(plan.questions),
                "mensaje": (
                    "Plan registrado. Si hay preguntas, el docente responde; "
                    "luego aprueba, edita supuestos o cancela. No redactes aún. "
                    "payload_json de draft_artifact es el schema de la ficha, no este plan."
                ),
            },
            ensure_ascii=False,
        )

    return propose_plan


def _cite_evidence(ctx: TurnContext):
    @tool
    def cite_evidence(path: str, snippet: str, seccion: str = "") -> str:
        """Vincula un fragmento de una fuente a una sección de la propuesta. No escribe archivos."""
        path = as_text(path, joiner=" ")
        snippet = as_text(snippet, joiner=" ")
        seccion = as_text(seccion, joiner=" ")
        blocked = _blocked(ctx, "cite_evidence")
        if blocked:
            return blocked
        ctx._emit({"type": "activity", "tool": "cite_evidence", "state": "start", "detail": path})
        try:
            payload = ctx.workspace.read_source(path)
        except Exception as exc:
            ctx._emit(
                {"type": "activity", "tool": "cite_evidence", "state": "end", "detail": "error"}
            )
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
        canonical = str(payload.get("path") or path)
        verified = snippet_in_text(str(payload.get("text") or ""), snippet)
        item = Evidence(path=canonical, snippet=snippet, seccion=seccion, verified=verified)
        ctx.evidence.append(item)
        ctx._emit(
            {
                "type": "activity",
                "tool": "cite_evidence",
                "state": "end",
                "detail": f"{'✓' if verified else '?'} {seccion or canonical}",
            }
        )
        return json.dumps(
            {"ok": True, "n": len(ctx.evidence), "verified": verified, "path": canonical},
            ensure_ascii=False,
        )

    return cite_evidence


def _draft_artifact(ctx: TurnContext):
    @tool
    def draft_artifact(
        tipo: str,
        titulo: str,
        cuerpo_markdown: str,
        evidencias_json: str = "[]",
        payload_json: str = "",
    ) -> str:
        """Entrega un borrador en memoria. No escribe a derivados. El docente decide s/n/b/c.

        payload_json opcional: JSON del schema de export (guía/evaluación/plan). El host
        exporta ese JSON; el markdown queda para la TUI.
        """
        tipo = as_text(tipo, joiner=" ")
        titulo = as_text(titulo, joiner=" ")
        cuerpo_markdown = as_text(cuerpo_markdown, joiner="\n")
        payload_json = as_text(payload_json, joiner="\n")
        blocked = _blocked(ctx, "draft_artifact")
        if blocked:
            return blocked
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
            checked = verify_evidence(ctx.workspace, item)
            key = (checked.path, checked.snippet[:80])
            if key in seen:
                continue
            seen.add(key)
            merged.append(checked)
        schema = parse_payload_json(parsed.value, payload_json)
        if schema:
            _fill_payload_from_encargo(schema, ctx.encargo)
        ctx.pending_draft = ArtifactDraft(
            tipo=parsed,
            titulo=titulo.strip() or parsed.label,
            cuerpo_markdown=cuerpo_markdown,
            evidencias=merged,
            payload=schema,
        )
        ctx._emit({"type": "activity", "tool": "draft", "state": "end", "detail": titulo})
        return json.dumps(
            {
                "ok": True,
                "titulo": ctx.pending_draft.titulo,
                "evidencias": len(merged),
                "payload": bool(schema),
                "mensaje": "Borrador en memoria. El docente revisa; tero no escribió archivos.",
            },
            ensure_ascii=False,
        )

    return draft_artifact


def _fill_payload_from_encargo(payload: dict[str, Any], encargo: Encargo) -> None:
    if not payload.get("curso") and encargo.curso:
        payload["curso"] = encargo.curso
    if not payload.get("asignatura") and encargo.asignatura:
        payload["asignatura"] = encargo.asignatura
    oa = str(payload.get("oa") or "").strip()
    essay = len(oa) > 80 or "catálogo" in oa.lower() or "catalog" in oa.lower()
    if encargo.oa and (not oa or essay):
        payload["oa"] = encargo.oa
    if not payload.get("tiempo") and encargo.duracion:
        payload["tiempo"] = encargo.duracion
    if not payload.get("duracion") and encargo.duracion:
        payload["duracion"] = encargo.duracion


def _cite_evidence_plan_stub(ctx: TurnContext):
    @tool
    def cite_evidence(path: str, snippet: str, seccion: str = "") -> str:
        """En fase plan no cites aún: primero propose_plan."""
        del path, snippet, seccion
        return json.dumps(
            {
                "ok": False,
                "error": "fase_plan",
                "hint": "Ahora solo propose_plan. Cita evidencia después de que el docente apruebe.",
            },
            ensure_ascii=False,
        )

    return cite_evidence


def _draft_artifact_plan_stub(ctx: TurnContext):
    @tool
    def draft_artifact(
        tipo: str,
        titulo: str,
        cuerpo_markdown: str,
        evidencias_json: str = "[]",
        payload_json: str = "",
    ) -> str:
        """En fase plan no redactes aún: primero propose_plan."""
        del tipo, titulo, cuerpo_markdown, evidencias_json, payload_json
        ctx._emit(
            {
                "type": "activity",
                "tool": "draft_artifact",
                "state": "end",
                "detail": "fase plan",
            }
        )
        return json.dumps(
            {
                "ok": False,
                "error": "fase_plan",
                "hint": (
                    "Ahora solo propose_plan. El docente aprueba y después "
                    "redactas con draft_artifact."
                ),
            },
            ensure_ascii=False,
        )

    return draft_artifact
