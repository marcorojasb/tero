"""Scripted Strands model: same agent loop, no Bedrock calls.

Used for the offline demo and for CI so judges can exercise list → read →
propose → teacher gate → write without AWS credentials.
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any

from strands.models import Model
from strands.types.content import Messages, SystemContentBlock
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolChoice, ToolSpec

from tero.proposal import compose_proposal

_LIST_LINE = re.compile(r"^-\s+(\S+)")
_SOURCE_HEADER = re.compile(r"^--- tero:source path=(.+?) ---", re.MULTILINE)


class ScriptedTeacherModel(Model):
    """A tiny Model that always follows tero's pedagogical tool sequence."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {"model_id": "tero.scripted-offline"}
        self._task: str = ""

    def update_config(self, **model_config: Any) -> None:
        self._config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        return self._config

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):  # noqa: ANN001
        raise NotImplementedError("tero scripted model does not implement structured_output")
        yield  # pragma: no cover — makes this an async generator if ever partially consumed

    def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec] | None = None,
        system_prompt: str | None = None,
        *,
        tool_choice: ToolChoice | None = None,
        system_prompt_content: list[SystemContentBlock] | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamEvent]:
        return self._stream(messages)

    async def _stream(self, messages: Messages) -> AsyncGenerator[StreamEvent, None]:
        self._capture_task(messages)
        called = _tool_names(messages)
        if "list_sources" not in called:
            async for event in _tool_call_events("list_sources", {}):
                yield event
            return

        sources = _collect_sources(messages)
        listed = _listed_paths(messages)
        unread = [path for path in listed if path not in sources]
        if unread:
            calls = [("read_source", {"relative_path": path}) for path in unread]
            async for event in _multi_tool_events(calls):
                yield event
            return

        if "write_derived" not in called:
            if not sources and listed:
                # Reads failed or returned empty; still cite listed names.
                sources = {path: "(contenido no disponible)" for path in listed}
            filename, markdown, citations = compose_proposal(sources, self._task)
            async for event in _tool_call_events(
                "write_derived",
                {"filename": filename, "markdown": markdown, "citations": citations},
            ):
                yield event
            return

        write_texts = [text for name, text in _tool_results(messages) if name == "write_derived"]
        if write_texts and "Escrito (" in write_texts[-1]:
            closing = (
                "Listo. Revisé las fuentes, armé una propuesta con citas y quedó "
                "escrita en derivados/ después de tu aprobación. Los originales no se tocaron."
            )
        else:
            closing = (
                "La propuesta no se escribió en derivados/ (la rechazaste o se canceló). "
                "Los archivos originales siguen iguales."
            )
        async for event in _text_events(closing):
            yield event

    def _capture_task(self, messages: Messages) -> None:
        for message in messages:
            if message.get("role") != "user":
                continue
            for block in message.get("content") or []:
                if "text" in block and block["text"].strip():
                    self._task = block["text"]
                    return


def _tool_names(messages: Messages) -> set[str]:
    names: set[str] = set()
    for message in messages:
        if message.get("role") != "assistant":
            continue
        for block in message.get("content") or []:
            if "toolUse" in block:
                names.add(block["toolUse"]["name"])
    return names


def _tool_results(messages: Messages) -> list[tuple[str, str]]:
    """Pairs of (toolUseId, result text) in order."""
    id_to_name: dict[str, str] = {}
    for message in messages:
        for block in message.get("content") or []:
            if "toolUse" in block:
                use = block["toolUse"]
                id_to_name[use["toolUseId"]] = use["name"]
    results: list[tuple[str, str]] = []
    for message in messages:
        for block in message.get("content") or []:
            if "toolResult" not in block:
                continue
            result = block["toolResult"]
            name = id_to_name.get(result.get("toolUseId", ""), "")
            chunks = []
            for item in result.get("content") or []:
                if "text" in item:
                    chunks.append(item["text"])
            results.append((name, "\n".join(chunks)))
    return results


def _listed_paths(messages: Messages) -> list[str]:
    paths: list[str] = []
    for name, text in _tool_results(messages):
        if name != "list_sources":
            continue
        for line in text.splitlines():
            match = _LIST_LINE.match(line.strip())
            if match:
                paths.append(match.group(1))
    return paths


def _collect_sources(messages: Messages) -> dict[str, str]:
    sources: dict[str, str] = {}
    for name, text in _tool_results(messages):
        if name != "read_source":
            continue
        match = _SOURCE_HEADER.search(text)
        if match:
            path = match.group(1).strip()
            body = text[match.end() :].lstrip("\n")
            sources[path] = body
    return sources


async def _tool_call_events(name: str, inputs: dict[str, Any]) -> AsyncGenerator[StreamEvent, None]:
    async for event in _multi_tool_events([(name, inputs)]):
        yield event


async def _multi_tool_events(
    calls: list[tuple[str, dict[str, Any]]],
) -> AsyncGenerator[StreamEvent, None]:
    yield {"messageStart": {"role": "assistant"}}
    for name, inputs in calls:
        tool_use_id = f"tooluse_{uuid.uuid4().hex[:24]}"
        yield {
            "contentBlockStart": {
                "start": {"toolUse": {"toolUseId": tool_use_id, "name": name}},
            }
        }
        yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(inputs, ensure_ascii=False)}}}}
        yield {"contentBlockStop": {}}
    yield {"messageStop": {"stopReason": "tool_use"}}


async def _text_events(text: str) -> AsyncGenerator[StreamEvent, None]:
    yield {"messageStart": {"role": "assistant"}}
    yield {"contentBlockDelta": {"delta": {"text": text}}}
    yield {"contentBlockStop": {}}
    yield {"messageStop": {"stopReason": "end_turn"}}
