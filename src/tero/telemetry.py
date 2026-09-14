"""Observabilidad nativa con StrandsTelemetry y OpenTelemetry.

Proporciona configuración de trazabilidad y métricas para sesiones docentes sin
depender de la infraestructura de AgentCore Runtime.
"""

from __future__ import annotations

import logging
import os

from strands.telemetry import StrandsTelemetry

from tero.config import Settings

logger = logging.getLogger("tero.telemetry")

_TELEMETRY_INSTANCE: StrandsTelemetry | None = None


def get_or_create_telemetry(settings: Settings | None = None) -> StrandsTelemetry:
    """Inicializa o devuelve la instancia global de telemetría de Strands."""
    global _TELEMETRY_INSTANCE
    if _TELEMETRY_INSTANCE is not None:
        return _TELEMETRY_INSTANCE

    # Si se define endpoint OTLP en el entorno, configurarlo
    telemetry = StrandsTelemetry()
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if otlp_endpoint:
        try:
            telemetry.setup_otlp_exporter()
            telemetry.setup_meter(enable_otlp_exporter=True)
            logger.info("OTLP export configurado hacia %s", otlp_endpoint)
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo configurar exportador OTLP: %s", exc)

    _TELEMETRY_INSTANCE = telemetry
    return telemetry


def is_telemetry_active() -> bool:
    """Indica si el sistema de telemetría está activo."""
    return _TELEMETRY_INSTANCE is not None


def get_current_trace_id() -> str:
    """Obtiene el trace ID activo de OpenTelemetry o genera un ID de 32 caracteres hexadecimales."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span:
            ctx = span.get_span_context()
            if ctx and ctx.trace_id != 0:
                return format(ctx.trace_id, "032x")
    except Exception:  # noqa: BLE001
        pass
    import uuid

    return uuid.uuid4().hex


def record_frugal_cost_metric(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    session_cost_usd: float,
) -> None:
    """Registra métricas OTel de costos y tokens siguiendo el principio Werner Vogels."""
    try:
        from opentelemetry import metrics

        meter = metrics.get_meter("tero.frugal")
        cost_counter = meter.create_counter(
            "tero.token.cost_usd",
            unit="USD",
            description="Costo acumulado estimado en USD",
        )
        cost_counter.add(cost_usd, {"model_id": model_id})

        token_counter = meter.create_counter(
            "tero.token.count",
            unit="tokens",
            description="Conteo de tokens procesados",
        )
        token_counter.add(input_tokens, {"model_id": model_id, "type": "input"})
        token_counter.add(output_tokens, {"model_id": model_id, "type": "output"})
    except Exception as exc:  # noqa: BLE001
        logger.debug("No se pudo emitir métrica frugal a OTel: %s", exc)


def record_router_failover_span(
    from_candidate: str,
    to_candidate: str,
    error: Exception | str,
) -> None:
    """Emite un span y evento de OpenTelemetry ante failover multi-región de ModelRouter."""
    err_str = str(error)
    logger.warning(
        "ModelRouter failover auto-hedging activado: origen=%s -> destino=%s | motivo: %s",
        from_candidate,
        to_candidate,
        err_str,
    )
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer("tero.router")
        with tracer.start_as_current_span("model_router_hedged_failover") as span:
            span.set_attribute("routing.from_candidate", str(from_candidate))
            span.set_attribute("routing.to_candidate", str(to_candidate))
            span.set_attribute(
                "routing.error",
                type(error).__name__ if isinstance(error, Exception) else "RouterError",
            )
            span.add_event(
                "multi_region_failover_hedged",
                {
                    "from_candidate": str(from_candidate),
                    "to_candidate": str(to_candidate),
                    "error_detail": err_str,
                },
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("No se pudo emitir span de failover: %s", exc)
