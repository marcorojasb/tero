"""Strands tools. Leen la carpeta o proponen material en memoria: ninguna escribe."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from strands import tool

from tero.coerce import as_text
from tero.curriculum.catalog import catalog_covers_curso, normalize_curso
from tero.curriculum.catalog import get_oa as catalog_get_oa
from tero.curriculum.catalog import list_oa as catalog_list_oa
from tero.curriculum.catalog import search_oa as catalog_search_oa
from tero.evidence import parse_evidence_blob, snippet_in_text, verify_evidence
from tero.latex.schemas import enrich_payload_from_markdown, parse_payload_json
from tero.sanitize import strip_tool_traces_value
from tero.types import (
    ArtifactDraft,
    ArtifactType,
    Encargo,
    Evidence,
    Propuesta,
    parse_accion,
)
from tero.workspace import Workspace

EmitFn = Callable[[dict[str, Any]], None]

# Tope de tools por turno: un loop de cite_evidence no es "esmerado".
DRAFT_TOOL_BUDGET = 16
DRAFT_AGENT_TURNS = 18

# Tools que entregan la propuesta. Cierran el turno.
PROPOSAL_TOOLS = {"proponer_crear", "proponer_editar"}

_UNCOVERED_HINT = (
    "Este curso no está en el catálogo Chile de tero. "
    "No elijas un OA de 4°–6° básico de relleno; deja el OA en texto libre."
)


@dataclass
class TurnContext:
    workspace: Workspace
    encargo: Encargo
    pending_propuesta: Propuesta | None = None
    evidence: list[Evidence] = field(default_factory=list)
    emit: EmitFn | None = None
    tool_calls: int = 0
    tool_budget: int | None = None
    budget_exhausted: bool = False
    last_chance_used: set[str] = field(default_factory=set)

    def _emit(self, event: dict[str, Any]) -> None:
        if self.emit:
            self.emit(event)

    def reset_tool_budget(self, n: int | None) -> None:
        self.tool_calls = 0
        self.tool_budget = n
        self.budget_exhausted = False
        self.last_chance_used = set()

    def consume_tool(self, name: str, *, allow_last_chance: bool = True) -> str | None:
        """Return an error JSON if the host tool budget is spent or a proposal exists."""
        if self.tool_budget is None:
            return None
        if self.pending_propuesta is not None:
            if name in PROPOSAL_TOOLS:
                return json.dumps(
                    {
                        "ok": True,
                        "already": True,
                        "titulo": self.pending_propuesta.titulo,
                        "hint": (
                            "Ya hay una propuesta en memoria. Detente: la persona "
                            "decide si la aprueba o pide cambios."
                        ),
                    },
                    ensure_ascii=False,
                )
            return json.dumps(
                {
                    "ok": False,
                    "error": "propuesta_ya_entregada",
                    "hint": "Ya hay una propuesta. No llames más tools.",
                },
                ensure_ascii=False,
            )
        last_chance = name in PROPOSAL_TOOLS and allow_last_chance
        if self.tool_calls >= self.tool_budget:
            self.budget_exhausted = True
            # One extra proposal after the cap — not an unbounded loop.
            if last_chance and name not in self.last_chance_used:
                self.last_chance_used.add(name)
                return None
            return json.dumps(
                {
                    "ok": False,
                    "error": "presupuesto_herramientas_agotado",
                    "hint": (
                        "Llama proponer_crear o proponer_editar ahora con la vista "
                        "previa completa y, si puedes, payload_json del schema."
                    ),
                },
                ensure_ascii=False,
            )
        self.tool_calls += 1
        return None


def _blocked(ctx: TurnContext, name: str, *, allow_last_chance: bool = True) -> str | None:
    err = ctx.consume_tool(name, allow_last_chance=allow_last_chance)
    if err:
        ctx._emit(
            {"type": "activity", "tool": name, "state": "end", "detail": "presupuesto agotado"}
        )
    return err


def build_tools(ctx: TurnContext) -> list[Any]:
    """Un solo agente: leer, citar y proponer. Ninguna tool escribe en la carpeta."""
    return [
        _list_sources(ctx),
        _list_artifacts(ctx),
        _read_artifact(ctx),
        _search_sources(ctx),
        _read_source(ctx),
        _list_oa(ctx),
        _get_oa(ctx),
        _search_oa(ctx),
        _cite_evidence(ctx),
        _proponer_crear(ctx),
        _proponer_editar(ctx),
    ]


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


def _list_artifacts(ctx: TurnContext):
    @tool
    def list_artifacts() -> str:
        """Lista el material ya escrito (derivados/ y borradores/) que se puede editar o adaptar."""
        blocked = _blocked(ctx, "list_artifacts")
        if blocked:
            return blocked
        ctx._emit({"type": "activity", "tool": "list_artifacts", "state": "start"})
        items = ctx.workspace.list_artifacts()
        ctx._emit(
            {
                "type": "activity",
                "tool": "list_artifacts",
                "state": "end",
                "detail": f"{len(items)} materiales",
            }
        )
        return json.dumps({"materiales": items}, ensure_ascii=False)

    return list_artifacts


def _read_artifact(ctx: TurnContext):
    @tool
    def read_artifact(path: str) -> str:
        """Lee un material ya escrito (derivados/ o borradores/) para editarlo o adaptarlo."""
        path = as_text(path, joiner=" ")
        blocked = _blocked(ctx, "read_artifact")
        if blocked:
            return blocked
        ctx._emit({"type": "activity", "tool": "read_artifact", "state": "start", "detail": path})
        try:
            text = ctx.workspace.read_document(path)
        except Exception as exc:  # noqa: BLE001 — ruta inválida o fuera de la carpeta
            return json.dumps(
                {"ok": False, "error": "no_encontrado", "hint": str(exc)},
                ensure_ascii=False,
            )
        ctx._emit({"type": "activity", "tool": "read_artifact", "state": "end", "detail": path})
        return json.dumps({"path": path, "texto": text}, ensure_ascii=False)

    return read_artifact


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


def _split_items(value: str) -> list[str]:
    """Separa una lista escrita en una línea (o varias) en ítems limpios."""
    out: list[str] = []
    # Ojo: NO se parte por "·" — es el separador del criterio Decreto 83.
    for chunk in re.split(r"[\n;]+|^\s*[-*•]\s+", value, flags=re.MULTILINE):
        item = chunk.strip().strip("-*•·").strip()
        if item:
            out.append(item)
    return out


def _draft_from_args(
    ctx: TurnContext,
    *,
    tipo: str,
    titulo: str,
    vista_previa_markdown: str,
    evidencias_json: str,
    payload_json: str,
) -> ArtifactDraft | str:
    """Arma el borrador en memoria. Devuelve JSON de error si el tipo no sirve."""
    parsed = ArtifactType.parse(tipo)
    if parsed is None:
        return json.dumps({"ok": False, "error": f"tipo desconocido: {tipo}"}, ensure_ascii=False)
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
    schema = enrich_payload_from_markdown(parsed.value, schema, vista_previa_markdown)
    schema = strip_tool_traces_value(schema)
    if schema:
        _fill_payload_from_encargo(schema, ctx.encargo)
    return ArtifactDraft(
        tipo=parsed,
        titulo=titulo.strip() or parsed.label,
        cuerpo_markdown=vista_previa_markdown,
        evidencias=merged,
        payload=schema,
    )


def _proponer_crear(ctx: TurnContext):
    @tool
    def proponer_crear(
        tipo: str,
        titulo: str,
        resumen: str,
        vista_previa_markdown: str,
        evidencias_json: str = "[]",
        payload_json: str = "",
    ) -> str:
        """Propone material NUEVO en memoria: planificación, guía, evaluación, pauta o actividad.

        La persona ve tu resumen y la vista previa completa, y decide si lo aprueba.
        Tú no escribes archivos: el host escribe solo tras la aprobación.
        """
        tipo = as_text(tipo, joiner=" ")
        titulo = as_text(titulo, joiner=" ")
        resumen = as_text(resumen, joiner=" ")
        vista_previa_markdown = as_text(vista_previa_markdown, joiner="\n")
        evidencias_json = as_text(evidencias_json, joiner=" ")
        payload_json = as_text(payload_json, joiner="\n")
        blocked = _blocked(
            ctx,
            "proponer_crear",
            allow_last_chance=bool(ArtifactType.parse(tipo) and vista_previa_markdown.strip()),
        )
        if blocked:
            return blocked
        ctx._emit({"type": "activity", "tool": "proponer", "state": "start", "detail": titulo})
        draft = _draft_from_args(
            ctx,
            tipo=tipo,
            titulo=titulo,
            vista_previa_markdown=vista_previa_markdown,
            evidencias_json=evidencias_json,
            payload_json=payload_json,
        )
        if isinstance(draft, str):
            return draft
        ctx.pending_propuesta = Propuesta(accion="crear", draft=draft, resumen=resumen.strip())
        ctx._emit({"type": "activity", "tool": "proponer", "state": "end", "detail": draft.titulo})
        return json.dumps(
            {
                "ok": True,
                "accion": "crear",
                "tipo": draft.tipo.value,
                "titulo": draft.titulo,
                "evidencias": len(draft.evidencias),
                "payload": bool(draft.payload),
                "mensaje": (
                    "Propuesta en memoria. La persona ve el resumen y la vista previa; "
                    "si aprueba, el host escribe el archivo. Detente ahora."
                ),
            },
            ensure_ascii=False,
        )

    return proponer_crear


def _proponer_editar(ctx: TurnContext):
    @tool
    def proponer_editar(
        ruta_origen: str,
        accion: str,
        tipo: str,
        titulo: str,
        resumen: str,
        vista_previa_markdown: str,
        cambios: str = "",
        notas_nee: str = "",
        evidencias_json: str = "[]",
        payload_json: str = "",
    ) -> str:
        """Propone una versión NUEVA de material que ya está en la carpeta.

        `accion`: "editar" (cambios que pidió la persona) o "adaptar" (apoyos y
        criterios para NEE). `ruta_origen` es la ruta relativa del material
        (p. ej. derivados/2026…-guia.md); `cambios` y `notas_nee` son listas.
        El material de origen no se toca: si la persona aprueba, la versión nueva
        se escribe como archivo aparte. Tú no escribes archivos.
        """
        ruta_origen = as_text(ruta_origen, joiner=" ")
        accion = as_text(accion, joiner=" ")
        tipo = as_text(tipo, joiner=" ")
        titulo = as_text(titulo, joiner=" ")
        resumen = as_text(resumen, joiner=" ")
        vista_previa_markdown = as_text(vista_previa_markdown, joiner="\n")
        cambios = as_text(cambios, joiner="\n")
        notas_nee = as_text(notas_nee, joiner="\n")
        evidencias_json = as_text(evidencias_json, joiner=" ")
        payload_json = as_text(payload_json, joiner="\n")
        blocked = _blocked(
            ctx,
            "proponer_editar",
            allow_last_chance=bool(ArtifactType.parse(tipo) and vista_previa_markdown.strip()),
        )
        if blocked:
            return blocked
        ctx._emit({"type": "activity", "tool": "proponer", "state": "start", "detail": ruta_origen})
        if not ruta_origen.strip():
            return json.dumps(
                {
                    "ok": False,
                    "error": "falta_ruta_origen",
                    "hint": "Indica la ruta del material que vas a editar o adaptar.",
                },
                ensure_ascii=False,
            )
        try:
            origin_text = ctx.workspace.read_document(ruta_origen)
        except Exception as exc:  # noqa: BLE001 — ruta inválida o fuera de la carpeta
            return json.dumps(
                {
                    "ok": False,
                    "error": "origen_no_encontrado",
                    "hint": f"{exc} Revisa con list_artifacts qué material existe.",
                },
                ensure_ascii=False,
            )
        draft = _draft_from_args(
            ctx,
            tipo=tipo,
            titulo=titulo,
            vista_previa_markdown=vista_previa_markdown,
            evidencias_json=evidencias_json,
            payload_json=payload_json,
        )
        if isinstance(draft, str):
            return draft
        ctx.pending_propuesta = Propuesta(
            accion=parse_accion(accion),
            draft=draft,
            resumen=resumen.strip(),
            origen=ruta_origen.strip(),
            cambios=_split_items(cambios),
            notas_nee=_split_items(notas_nee),
        )
        ctx._emit({"type": "activity", "tool": "proponer", "state": "end", "detail": draft.titulo})
        return json.dumps(
            {
                "ok": True,
                "accion": ctx.pending_propuesta.accion,
                "origen": ctx.pending_propuesta.origen,
                "caracteres_origen": len(origin_text),
                "titulo": draft.titulo,
                "evidencias": len(draft.evidencias),
                "payload": bool(draft.payload),
                "mensaje": (
                    "Propuesta en memoria. El material de origen no se toca. "
                    "Detente ahora: la persona aprueba o pide cambios."
                ),
            },
            ensure_ascii=False,
        )

    return proponer_editar


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


def _fill_payload_from_encargo(payload: dict[str, Any], encargo: Encargo) -> None:
    """Chips on the encargo are the system of record; payload may not replace them."""
    if encargo.curso:
        payload["curso"] = encargo.curso
    if encargo.asignatura:
        payload["asignatura"] = encargo.asignatura
    oa = str(payload.get("oa") or "").strip()
    essay = len(oa) > 80 or "catálogo" in oa.lower() or "catalog" in oa.lower()
    if encargo.oa and (not oa or essay):
        payload["oa"] = encargo.oa
    if not payload.get("tiempo") and encargo.duracion:
        payload["tiempo"] = encargo.duracion
    if not payload.get("duracion") and encargo.duracion:
        payload["duracion"] = encargo.duracion
