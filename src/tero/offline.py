"""Scripted Strands Model: real Agent loop, no network, no AWS."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any

from strands.models import Model
from strands.types.content import Messages
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolSpec

from tero import DEFAULT_MODEL_ID
from tero.demo_content import demo_draft_markdown, demo_plan, infer_tipo
from tero.types import Encargo


class OfflineModel(Model):
    """Deterministic provider that still speaks the Strands stream protocol."""

    def __init__(self, encargo: Encargo | None = None, *, model_id: str = "tero-offline") -> None:
        self.config: dict[str, Any] = {"model_id": model_id or "tero-offline"}
        self.encargo = encargo or Encargo()

    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        return dict(self.config)

    async def structured_output(  # type: ignore[override]
        self,
        output_model: type[Any],
        prompt: Messages,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        del output_model, prompt, system_prompt, kwargs
        if False:
            yield {}
        raise NotImplementedError("El modelo offline de tero no implementa structured_output.")

    async def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        del system_prompt, kwargs
        available = {spec["name"] for spec in (tool_specs or [])}
        called = _tool_names(messages)
        action = self._next_action(messages, available, called)
        async for event in _emit_action(action):
            yield event

    def _next_action(
        self,
        messages: Messages,
        available: set[str],
        called: list[str],
    ) -> dict[str, Any]:
        prompt = _last_user_text(messages)
        tipo = infer_tipo(prompt, self.encargo)
        if len(called) >= 12:
            return {"text": "Listo. Esperando el criterio del docente."}
        listed = _listed_paths(messages)
        reads = _read_payloads(messages)
        if "list_sources" in available and "list_sources" not in called:
            return {"tool": "list_sources", "input": {}}
        if "read_source" in available and called.count("read_source") < 2:
            path = _read_path_for(listed, called.count("read_source"))
            return {"tool": "read_source", "input": {"path": path}}
        if "propose_plan" in available and "propose_plan" not in called:
            plan = demo_plan(self.encargo, tipo, sources=listed)
            return {"tool": "propose_plan", "input": plan}
        if "cite_evidence" in available and called.count("cite_evidence") < 2:
            citation = _citation_for(listed, reads, called.count("cite_evidence"))
            return {"tool": "cite_evidence", "input": citation}
        if "draft_artifact" in available and "draft_artifact" not in called:
            critique = ""
            if "CORRECCIÓN" in prompt or "CORRECCION" in prompt:
                critique = prompt
            citations = [
                _citation_for(listed, reads, 0),
                _citation_for(listed, reads, 1),
            ]
            return {
                "tool": "draft_artifact",
                "input": {
                    "tipo": tipo.value,
                    "titulo": demo_plan(self.encargo, tipo, sources=listed)["objetivo"][:80],
                    "cuerpo_markdown": demo_draft_markdown(
                        self.encargo,
                        tipo,
                        critique=critique,
                        sources=listed or list(reads),
                    ),
                    "evidencias_json": json.dumps(citations, ensure_ascii=False),
                },
            }
        return {"text": "Listo. Esperando el criterio del docente."}


DEMO_READS = (
    "fuentes/bases-oa-lenguaje-4b.md",
    "fuentes/cuento-el-condor-y-el-huemul.md",
)
DEMO_CITATIONS = (
    {
        "path": DEMO_READS[0],
        "snippet": (
            "Extraer información explícita e implícita de textos literarios y no literarios, "
            "distinguiendo lo que el texto dice de lo que el lector infiere con evidencia."
        ),
        "seccion": "OA",
    },
    {
        "path": DEMO_READS[1],
        "snippet": "El huemul no corrió: preguntó al cóndor por qué el valle tenía sed.",
        "seccion": "desarrollo",
    },
)


def _listed_paths(messages: Messages) -> list[str]:
    for payload in _tool_result_payloads(messages):
        fuentes = payload.get("fuentes")
        if isinstance(fuentes, list):
            paths = [
                str(row.get("relative_path") or "")
                for row in fuentes
                if isinstance(row, dict) and row.get("relative_path")
            ]
            if paths:
                return paths
    return []


def _read_payloads(messages: Messages) -> dict[str, str]:
    out: dict[str, str] = {}
    for payload in _tool_result_payloads(messages):
        path = str(payload.get("path") or "")
        text = str(payload.get("text") or "")
        if path and text:
            out[path] = text
    return out


def _tool_result_payloads(messages: Messages) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for message in messages:
        for block in message.get("content") or []:
            if not isinstance(block, dict) or "toolResult" not in block:
                continue
            result = block.get("toolResult") or {}
            for part in result.get("content") or []:
                raw = ""
                if isinstance(part, dict) and "text" in part:
                    raw = str(part["text"])
                elif isinstance(part, dict) and "json" in part and isinstance(part["json"], dict):
                    payloads.append(part["json"])
                    continue
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict):
                    payloads.append(data)
    return payloads


def _read_path_for(listed: list[str], index: int) -> str:
    if listed and all(path in listed for path in DEMO_READS):
        return DEMO_READS[index % 2]
    if listed:
        return listed[index % len(listed)]
    return DEMO_READS[index % 2]


def _citation_for(listed: list[str], reads: dict[str, str], index: int) -> dict[str, str]:
    if listed and all(path in listed for path in DEMO_READS):
        return dict(DEMO_CITATIONS[index % 2])
    path = _read_path_for(listed, index)
    text = reads.get(path) or ""
    snippet = _snippet_from(text) or path
    seccion = "OA" if index == 0 else "desarrollo"
    return {"path": path, "snippet": snippet, "seccion": seccion}


def _snippet_from(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if len(cleaned) >= 40 and not cleaned.startswith("#"):
            return cleaned[:220]
    compact = " ".join(text.split())
    return compact[:220]


def _tool_names(messages: Messages) -> list[str]:
    names: list[str] = []
    for message in messages:
        if message.get("role") != "assistant":
            continue
        for block in message.get("content") or []:
            if isinstance(block, dict) and "toolUse" in block:
                names.append(str(block["toolUse"].get("name") or ""))
    return names


def _last_user_text(messages: Messages) -> str:
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        parts: list[str] = []
        for block in message.get("content") or []:
            if isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
        if parts:
            return "\n".join(parts)
    return ""


async def _emit_action(action: dict[str, Any]) -> AsyncIterable[StreamEvent]:
    yield {"messageStart": {"role": "assistant"}}
    if "tool" in action:
        tool_use_id = f"tooluse_{uuid.uuid4().hex[:12]}"
        name = str(action["tool"])
        payload = json.dumps(action.get("input") or {}, ensure_ascii=False)
        yield {
            "contentBlockStart": {"start": {"toolUse": {"toolUseId": tool_use_id, "name": name}}}
        }
        yield {"contentBlockDelta": {"delta": {"toolUse": {"input": payload}}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "tool_use"}}
        return
    text = str(action.get("text") or "")
    yield {"contentBlockStart": {"start": {}}}
    # tiny chunks so the TUI can stream without looking like a dump
    for index in range(0, len(text), 24):
        yield {"contentBlockDelta": {"delta": {"text": text[index : index + 24]}}}
    yield {"contentBlockStop": {}}
    yield {"messageStop": {"stopReason": "end_turn"}}
    yield {
        "metadata": {
            "usage": {"inputTokens": 0, "outputTokens": max(1, len(text) // 4)},
            "metrics": {"latencyMs": 1},
        }
    }


def model_label(offline: bool, model_id: str) -> str:
    return "tero-offline" if offline else (model_id or DEFAULT_MODEL_ID)
