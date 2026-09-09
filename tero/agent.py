"""Build a Strands Agent for tero (Bedrock or scripted/offline)."""

from __future__ import annotations

from strands import Agent
from strands.models import BedrockModel
from strands.vended_interventions.hitl import HumanInTheLoop

from tero.approval import Decision, make_ask, teacher_evaluate
from tero.config import Settings, get_settings
from tero.prompts import SYSTEM_PROMPT
from tero.scripted_model import ScriptedTeacherModel
from tero.tools import ALLOWED_TOOLS, build_tools
from tero.workspace import Workspace


def build_bedrock_model(settings: Settings | None = None) -> BedrockModel:
    """Amazon Bedrock model provider. Model id is env-configurable."""
    settings = settings or get_settings()
    return BedrockModel(
        model_id=settings.model_id,
        region_name=settings.region,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )


def build_agent(
    workspace: Workspace,
    *,
    offline: bool = False,
    auto: Decision | None = None,
    settings: Settings | None = None,
    quiet: bool = False,
) -> Agent:
    """Create the tero agent with tools and a teacher approval gate on writes."""
    tools = build_tools(workspace)
    ask = make_ask(workspace, auto=auto)
    hitl = HumanInTheLoop(
        allowed_tools=ALLOWED_TOOLS,
        ask=ask,
        evaluate=teacher_evaluate,
    )
    model = ScriptedTeacherModel() if offline else build_bedrock_model(settings)
    kwargs: dict = {
        "model": model,
        "tools": tools,
        "system_prompt": SYSTEM_PROMPT,
        "interventions": [hitl],
        "name": "tero",
        "description": "Agente pedagógico: el docente decide antes de escribir derivados.",
    }
    if quiet:
        kwargs["callback_handler"] = None
    return Agent(**kwargs)
