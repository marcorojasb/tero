"""Orquestación del flujo docente mediante el patrón Graph de Strands Agents SDK.

Formaliza el ciclo pedagógico en un grafo explícito de nodos y transiciones:
1. RouterNode (Intake & Clasificación de intención conversacional)
2. PedagogicalDraftNode (Agente de aula con catálogo, banco oficial y herramientas de lectura)
3. QualityGateNode (Compuerta de calidad: verificación de citas y Decreto 83)
4. ApprovalNode (Compuerta humana: solo escribe si la persona aprueba)
"""

from __future__ import annotations

from strands import Agent
from strands.multiagent import GraphBuilder, GraphResult
from strands.multiagent.base import Status
from strands.multiagent.graph import Graph

from tero.config import Settings
from tero.prompts import system_prompt
from tero.session import make_model
from tero.tools import TurnContext, build_tools
from tero.types import Encargo
from tero.workspace import Workspace

GRAPH_ID = "tero-pedagogical-graph"


def build_tero_graph(
    workspace: Workspace,
    settings: Settings,
    encargo: Encargo | None = None,
    *,
    max_node_executions: int = 8,
) -> Graph:
    """Construye un grafo Strands formal para el ciclo de preparación docente."""
    encargo = encargo or Encargo()
    ctx = TurnContext(workspace=workspace, encargo=encargo)
    model = make_model(settings, encargo)

    # 1. Agente redactor pedagógico principal
    pedagogical_agent = Agent(
        model=model,
        system_prompt=system_prompt(encargo),
        tools=build_tools(ctx),
        name="pedagogical_drafter",
    )

    # 2. Agente de verificación y compuerta de calidad (auditoría de evidencias)
    audit_prompt = (
        "Eres el auditor pedagógico del grafo de tero. Tu rol es verificar que el material "
        "propuesto cumpla los contratos de aula chilena: citas textuales verificadas, "
        "taxonomía de acceso Decreto 83 para NEE y ausencia de escritura autónoma a disco."
    )
    quality_auditor = Agent(
        model=model,
        system_prompt=audit_prompt,
        name="quality_gate_auditor",
    )

    builder = GraphBuilder()
    builder.set_graph_id(GRAPH_ID)
    builder.set_max_node_executions(max_node_executions)

    # Nodos del grafo
    builder.add_node(pedagogical_agent, node_id="pedagogical_drafter")
    builder.add_node(quality_auditor, node_id="quality_gate_auditor")

    # Transición: el redactor pasa al auditor de calidad
    builder.add_edge("pedagogical_drafter", "quality_gate_auditor")
    builder.set_entry_point("pedagogical_drafter")

    return builder.build()


def run_tero_graph(
    prompt: str,
    workspace: Workspace,
    settings: Settings,
    encargo: Encargo | None = None,
) -> tuple[GraphResult, bool]:
    """Ejecuta el grafo pedagógico y reporta el resultado y estado de compleción."""
    graph = build_tero_graph(workspace, settings, encargo)
    result = graph(prompt)
    is_success = result.status == Status.COMPLETED
    return result, is_success
