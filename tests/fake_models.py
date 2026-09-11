"""Modelos Strands mínimos para tests: sin red, sin AWS, deterministas."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterable
from typing import Any

from strands.models import Model
from strands.types.content import Messages
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolSpec


async def _text_events(text: str) -> AsyncIterable[StreamEvent]:
    """Un turno de solo texto, en trozos chicos como el stream real."""
    yield {"messageStart": {"role": "assistant"}}
    yield {"contentBlockStart": {"start": {}}}
    for index in range(0, len(text), 24):
        yield {"contentBlockDelta": {"delta": {"text": text[index : index + 24]}}}
    yield {"contentBlockStop": {}}
    yield {"messageStop": {"stopReason": "end_turn"}}


class _BaseModel(Model):
    def __init__(self, *, model_id: str = "tero-test") -> None:
        self.config: dict[str, Any] = {"model_id": model_id}

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
    ) -> AsyncIterable[dict[str, Any]]:
        del output_model, prompt, system_prompt, kwargs
        if False:  # pragma: no cover - generador vacío
            yield {}
        raise NotImplementedError("El modelo de prueba no implementa structured_output.")

    async def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        del messages, tool_specs, system_prompt, kwargs
        async for event in self._events():
            yield event

    async def _events(self) -> AsyncIterable[StreamEvent]:
        raise NotImplementedError


class TextModel(_BaseModel):
    """Devuelve siempre el mismo texto, como si el modelo escribiera en prosa."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

    async def _events(self) -> AsyncIterable[StreamEvent]:
        async for event in _text_events(self.text):
            yield event


class ToolModel(_BaseModel):
    """Llama una tool y después responde texto: el guion mínimo de un turno."""

    def __init__(self, name: str, payload: dict[str, Any], *, then_text: str = "Listo.") -> None:
        super().__init__()
        self.name = name
        self.payload = payload
        self.then_text = then_text
        self.calls = 0

    async def _events(self) -> AsyncIterable[StreamEvent]:
        self.calls += 1
        if self.calls > 1:
            async for event in _text_events(self.then_text):
                yield event
            return
        yield {"messageStart": {"role": "assistant"}}
        yield {
            "contentBlockStart": {
                "start": {
                    "toolUse": {"toolUseId": f"tooluse_{uuid.uuid4().hex[:10]}", "name": self.name}
                }
            }
        }
        yield {
            "contentBlockDelta": {
                "delta": {"toolUse": {"input": json.dumps(self.payload, ensure_ascii=False)}}
            }
        }
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "tool_use"}}


class BoomModel(_BaseModel):
    """Rompe el stream: para probar la ruta de error sin red."""

    def __init__(self, message: str = "boom de prueba") -> None:
        super().__init__()
        self.message = message

    async def _events(self) -> AsyncIterable[StreamEvent]:
        raise RuntimeError(self.message)
        yield {}  # pragma: no cover - inalcanzable, mantiene el tipo generador
