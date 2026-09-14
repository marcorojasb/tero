"""Tests para Frugal Architect & Token Cost Transparency y Multi-Region Auto-Hedging."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from strands.models import ModelRouter

from tero.config import Settings
from tero.cost import (
    MODEL_PRICING,
    SessionUsageTracker,
    calculate_cost,
)
from tero.session import TelemetricFallbackStrategy, make_model
from tero.types import Encargo
from tero.workspace import Workspace
from tests.fake_models import TextModel
from tests.support import open_session


def test_pricing_rates_and_calculation():
    """Verifica precios publicados para el trío Bedrock y el principio Werner Vogels."""
    # Nova Lite
    assert MODEL_PRICING["amazon.nova-lite-v1:0"] == (0.06, 0.24)
    cost_nova = calculate_cost("amazon.nova-lite-v1:0", 10_000, 2_000)
    # 10,000 * 0.06 / 1M = 0.0006; 2,000 * 0.24 / 1M = 0.00048; total = 0.00108
    assert cost_nova == pytest.approx(0.00108, rel=1e-4)

    # Trío documentado: GLM 4.7 Flash (Zhipu AI en Bedrock)
    assert MODEL_PRICING["zai.glm-4.7-flash"] == (0.06, 0.24)
    assert MODEL_PRICING["us.zai.glm-4.7-flash"] == (0.06, 0.24)
    cost_glm = calculate_cost("zai.glm-4.7-flash", 1_000_000, 1_000_000)
    assert cost_glm == pytest.approx(0.30, rel=1e-4)

    # Trío documentado: MiniMax M2.5 en Bedrock
    assert MODEL_PRICING["minimax.minimax-m2.5"] == (0.30, 1.20)
    assert MODEL_PRICING["us.minimax.minimax-m2.5"] == (0.30, 1.20)
    cost_minimax = calculate_cost("minimax.minimax-m2.5", 100_000, 50_000)
    # 100k * 0.30 / 1M = 0.03; 50k * 1.20 / 1M = 0.06; total = 0.09
    assert cost_minimax == pytest.approx(0.09, rel=1e-4)

    # tero-offline: estrictamente 0 tokens y $0.00 USD
    assert MODEL_PRICING["tero-offline"] == (0.0, 0.0)
    cost_offline = calculate_cost("tero-offline", 500_000, 500_000)
    assert cost_offline == 0.0


def test_session_usage_tracker_accumulation():
    tracker = SessionUsageTracker()

    # Turno 1: Nova Lite
    t1 = tracker.record_turn("amazon.nova-lite-v1:0", input_tokens=10_000, output_tokens=1_000)
    assert t1.total_tokens == 11_000
    assert t1.cost_usd > 0
    assert tracker.total_tokens == 11_000
    assert tracker.total_input_tokens == 10_000
    assert tracker.total_output_tokens == 1_000

    # Turno 2: Nova Lite
    t2 = tracker.record_turn("amazon.nova-lite-v1:0", input_tokens=5_000, output_tokens=2_000)
    assert tracker.total_tokens == 18_000
    assert tracker.total_cost_usd == pytest.approx(t1.cost_usd + t2.cost_usd, rel=1e-5)

    summary = tracker.get_summary()
    assert summary["total_tokens"] == 18_000
    assert summary["turns_count"] == 2
    assert "Frugal Architecture" in summary["banner"]
    assert "$" in summary["total_cost_formatted"]


def test_offline_explicit_zero_tokens_and_cost():
    """El modo offline debe registrar explícitamente 0 tokens y $0.00 USD."""
    tracker = SessionUsageTracker()
    turn = tracker.record_turn("tero-offline", input_tokens=10_000, output_tokens=5_000)

    assert turn.input_tokens == 0
    assert turn.output_tokens == 0
    assert turn.total_tokens == 0
    assert turn.cost_usd == 0.0

    summary = tracker.get_summary()
    assert summary["total_tokens"] == 0
    assert summary["total_cost_usd"] == 0.0
    assert "air-gapped offline" in summary["banner"]


def test_session_emits_cost_event_on_turn(workspace: Workspace):
    events: list[dict] = []
    session = open_session(workspace, events=events)

    turn = session.start_turn("Hola, ¿qué fuentes tengo en la carpeta?")
    assert turn is not None
    assert turn.usage is not None
    assert turn.usage["model_id"] == "tero-offline"
    assert turn.usage["total_tokens"] == 0

    cost_events = [ev for ev in events if ev.get("type") == "cost"]
    assert len(cost_events) >= 1
    ev = cost_events[0]
    assert ev["turn_id"] == turn.id
    assert "session" in ev
    assert "Frugal Architecture" in ev["session"]["banner"]


def test_multi_region_auto_hedging_model_router():
    """make_model configura ModelRouter con TelemetricFallbackStrategy para el trío Bedrock."""
    encargo = Encargo(curso="4° básico")

    with patch("strands.models.BedrockModel") as mock_bedrock:
        mock_bedrock.side_effect = lambda model_id, **kw: TextModel(f"model-{model_id}")

        # 1. Nova Lite
        settings_nova = Settings(
            offline=False, model_id="amazon.nova-lite-v1:0", region="us-east-1"
        )
        router_nova = make_model(settings_nova, encargo)
        assert isinstance(router_nova, ModelRouter)
        assert isinstance(router_nova._strategy, TelemetricFallbackStrategy)
        assert router_nova.candidates[0].name == "amazon.nova-lite-v1:0 (us-east-1)"
        assert router_nova.candidates[1].name == "us.amazon.nova-lite-v1:0 (us-east-1)"

        # 2. GLM 4.7 Flash
        settings_glm = Settings(offline=False, model_id="zai.glm-4.7-flash", region="us-east-1")
        router_glm = make_model(settings_glm, encargo)
        assert isinstance(router_glm, ModelRouter)
        assert isinstance(router_glm._strategy, TelemetricFallbackStrategy)
        assert router_glm.candidates[0].name == "zai.glm-4.7-flash (us-east-1)"
        assert router_glm.candidates[1].name == "zai.glm-4.7-flash (us-west-2)"

        # 3. MiniMax M2.5
        settings_minimax = Settings(
            offline=False, model_id="minimax.minimax-m2.5", region="us-east-1"
        )
        router_minimax = make_model(settings_minimax, encargo)
        assert isinstance(router_minimax, ModelRouter)
        assert isinstance(router_minimax._strategy, TelemetricFallbackStrategy)
        assert router_minimax.candidates[0].name == "minimax.minimax-m2.5 (us-east-1)"
        assert router_minimax.candidates[1].name == "minimax.minimax-m2.5 (us-west-2)"


def test_telemetric_fallback_strategy_failover_span():
    """TelemetricFallbackStrategy captura excepciones previas y emite span de failover."""
    import asyncio

    async def _run():
        strategy = TelemetricFallbackStrategy()

        cand1 = MagicMock()
        cand1.model = "primary-region-model"
        cand2 = MagicMock()
        cand2.model = "hedged-cross-region-model"

        attempt_fail = MagicMock()
        attempt_fail.candidate = cand1
        attempt_fail.exception = ConnectionError("us-east-1 timeout")

        mock_context = MagicMock()
        mock_context.candidates = [cand1, cand2]
        mock_context.attempts = [attempt_fail]

        with patch("tero.telemetry.record_router_failover_span") as mock_record:
            # FallbackStrategy.select elegirá el candidato no fallado (cand2)
            chosen = await strategy.select(mock_context)
            assert chosen == cand2
            assert mock_record.called
            args, _ = mock_record.call_args
            assert "primary-region-model" in str(args[0])
            assert "hedged-cross-region-model" in str(args[1])

    asyncio.run(_run())
