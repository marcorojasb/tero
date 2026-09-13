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
