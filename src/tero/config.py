"""Runtime settings. No secrets. Defaults to Bedrock amazon.nova-lite-v1:0."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from tero import DEFAULT_MODEL_ID

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_CARPETA = PACKAGE_ROOT / "examples" / "carpeta-demo"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_timeout(name: str, default: float) -> float:
    """Non-negative seconds; blank → default."""
    value = _env_float(name, default)
    return max(0.0, value)


@dataclass(frozen=True)
class Settings:
    model_id: str = DEFAULT_MODEL_ID
    region: str = "us-east-1"
    offline: bool = False
    carpeta: Path = EXAMPLE_CARPETA
    skip_plan: bool = False
    temperature: float = 0.3
    # Wall-clock budget per plan/draft agent call (0 = unlimited). Bedrock default 120s.
    turn_timeout_s: float = 0.0

    @classmethod
    def from_env(cls, *, offline: bool | None = None, carpeta: Path | None = None) -> Settings:
        _load_dotenv()
        env_offline = os.environ.get("TERO_OFFLINE", "").strip() in {"1", "true", "yes"}
        resolved_offline = env_offline if offline is None else offline
        model_id = (
            os.environ.get("TERO_MODEL") or os.environ.get("TERO_MODEL_ID") or DEFAULT_MODEL_ID
        ).strip() or DEFAULT_MODEL_ID
        # Offline is fast/scripted; Bedrock can hang on EventStream — default budget.
        default_timeout = 0.0 if resolved_offline else 120.0
        return cls(
            model_id=model_id,
            region=os.environ.get("TERO_AWS_REGION")
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1",
            offline=resolved_offline,
            carpeta=(
                carpeta or Path(os.environ.get("TERO_CARPETA") or EXAMPLE_CARPETA)
            ).expanduser(),
            skip_plan=os.environ.get("TERO_SKIP_PLAN", "").strip() in {"1", "true", "yes"},
            temperature=_env_float("TERO_TEMPERATURE", 0.3),
            turn_timeout_s=_env_timeout("TERO_TURN_TIMEOUT", default_timeout),
        )
