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
        if "list_sources" in available and "list_sources" not in called:
            return {"tool": "list_sources", "input": {}}
        if "read_source" in available and called.count("read_source") < 2:
            path = (
                "fuentes/bases-oa-lenguaje-4b.md"
                if called.count("read_source") == 0
                else "fuentes/cuento-el-condor-y-el-huemul.md"
            )
            return {"tool": "read_source", "input": {"path": path}}
        if "propose_plan" in available and "propose_plan" not in called:
            plan = demo_plan(self.encargo, tipo)
            return {"tool": "propose_plan", "input": plan}
        if "cite_evidence" in available and called.count("cite_evidence") < 2:
            if called.count("cite_evidence") == 0:
                return {
                    "tool": "cite_evidence",
                    "input": {
                        "path": "fuentes/bases-oa-lenguaje-4b.md",
                        "snippet": "OA 4: extraer información explícita e implícita de textos literarios.",
                        "seccion": "OA",
                    },
                }
            return {
                "tool": "cite_evidence",
                "input": {
                    "path": "fuentes/cuento-el-condor-y-el-huemul.md",
                    "snippet": "El huemul no corrió: preguntó al cóndor por qué el valle tenía sed.",
                    "seccion": "desarrollo",
                },
            }
        if "draft_artifact" in available and "draft_artifact" not in called:
            critique = ""
            if "CORRECCIÓN" in prompt or "CORRECCION" in prompt:
                critique = prompt
            return {
                "tool": "draft_artifact",
                "input": {
                    "tipo": tipo.value,
                    "titulo": demo_plan(self.encargo, tipo)["objetivo"][:80],
                    "cuerpo_markdown": demo_draft_markdown(self.encargo, tipo, critique=critique),
                    "evidencias_json": json.dumps(
                        [
                            {
                                "path": "fuentes/bases-oa-lenguaje-4b.md",
                                "snippet": "OA 4: extraer información explícita e implícita.",
                                "seccion": "OA",
                            },
                            {
                                "path": "fuentes/cuento-el-condor-y-el-huemul.md",
                                "snippet": "El huemul no corrió: preguntó al cóndor.",
                                "seccion": "desarrollo",
                            },
                        ],
                        ensure_ascii=False,
                    ),
                },
            }
        return {"text": "Listo. Esperando el criterio del docente."}


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
