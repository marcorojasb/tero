"""Frugal Architect: Contabilidad y transparencia de tokens y costo en Amazon Bedrock.

Implementa el principio de arquitectura frugal de Werner Vogels:
1. Medición exacta de tokens por turno y acumulados en la sesión docente.
2. Estimación transparente de costos en USD según precios públicos de Bedrock.
3. Tratamiento explícito de tero-offline: 0 tokens / $0.00 USD (air-gapped).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Tarifas públicas en USD por cada 1.000.000 de tokens (input, output)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # Bedrock Nova Lite (por defecto en tero)
    "amazon.nova-lite-v1:0": (0.06, 0.24),
    "us.amazon.nova-lite-v1:0": (0.06, 0.24),
    # Bedrock Nova Micro (para pruebas rápidas)
    "amazon.nova-micro-v1:0": (0.035, 0.14),
    "us.amazon.nova-micro-v1:0": (0.035, 0.14),
    # Bedrock Nova Pro
    "amazon.nova-pro-v1:0": (0.80, 3.20),
    "us.amazon.nova-pro-v1:0": (0.80, 3.20),
    # Trío documentado: GLM 4.7 Flash (Zhipu AI en Bedrock)
    "zai.glm-4.7-flash": (0.06, 0.24),
    # Trío documentado: MiniMax M2.5 en Bedrock
    "minimax.minimax-m2.5": (0.30, 1.20),
    # Modo sin red: estrictamente 0 tokens y $0.00 USD
    "tero-offline": (0.0, 0.0),
}


def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Calcula el costo estimado en USD a partir de tokens y modelo."""
    if model_id == "tero-offline":
        return 0.0
    input_rate, output_rate = MODEL_PRICING.get(model_id, (0.06, 0.24))
    cost = (input_tokens * input_rate / 1_000_000.0) + (output_tokens * output_rate / 1_000_000.0)
    return round(cost, 6)


def format_cost_usd(cost: float, *, offline: bool = False) -> str:
    """Formatea el costo en USD para despliegue humano en TUI, CLI y telemetría."""
    if offline or cost == 0.0:
        return "$0.0000 USD"
    if cost < 0.0001:
        return f"${cost:.6f} USD"
    return f"${cost:.4f} USD"


@dataclass
class TurnUsage:
    """Consumo y costo de un turno conversacional individual."""

    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["cost_formatted"] = format_cost_usd(
            self.cost_usd, offline=(self.model_id == "tero-offline")
        )
        return data


@dataclass
class SessionUsageTracker:
    """Rastreador acumulado de tokens y costos de la sesión pedagógica."""

    turns: list[TurnUsage] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    def record_turn(
        self,
        model_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> TurnUsage:
        """Registra el consumo de un turno y actualiza los acumulados de la sesión."""
        if model_id == "tero-offline":
            # Para tero-offline: estrictamente 0 tokens y 0.00 USD
            in_tok = 0
            out_tok = 0
            tot_tok = 0
            cost = 0.0
        else:
            in_tok = max(0, int(input_tokens))
            out_tok = max(0, int(output_tokens))
            tot_tok = in_tok + out_tok
            cost = calculate_cost(model_id, in_tok, out_tok)

        turn = TurnUsage(
            model_id=model_id,
            input_tokens=in_tok,
            output_tokens=out_tok,
            total_tokens=tot_tok,
            cost_usd=cost,
        )
        self.turns.append(turn)

        self.total_input_tokens += in_tok
        self.total_output_tokens += out_tok
        self.total_tokens += tot_tok
        self.total_cost_usd = round(self.total_cost_usd + cost, 6)

        return turn

    def get_summary(self) -> dict[str, Any]:
        """Resumen de transparencia de costos para la TUI, status y telemetría."""
        is_offline_session = len(self.turns) > 0 and all(
            t.model_id == "tero-offline" for t in self.turns
        )
        if is_offline_session:
            banner = "Costo estimado sesión: $0.00 USD (air-gapped offline) · Frugal Architecture"
        else:
            cost_str = format_cost_usd(self.total_cost_usd, offline=(self.total_cost_usd == 0.0))
            banner = f"Costo estimado sesión: {cost_str} · Frugal Architecture"

        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "total_cost_formatted": format_cost_usd(
                self.total_cost_usd, offline=is_offline_session
            ),
            "turns_count": len(self.turns),
            "banner": banner,
        }
