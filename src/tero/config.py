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


@dataclass(frozen=True)
class Settings:
    model_id: str = DEFAULT_MODEL_ID
    region: str = "us-east-1"
    offline: bool = False
    carpeta: Path = EXAMPLE_CARPETA
    skip_plan: bool = False
    temperature: float = 0.3

    @classmethod
    def from_env(cls, *, offline: bool | None = None, carpeta: Path | None = None) -> Settings:
        _load_dotenv()
        env_offline = os.environ.get("TERO_OFFLINE", "").strip() in {"1", "true", "yes"}
        model_id = (
            os.environ.get("TERO_MODEL") or os.environ.get("TERO_MODEL_ID") or DEFAULT_MODEL_ID
        ).strip() or DEFAULT_MODEL_ID
        return cls(
            model_id=model_id,
            region=os.environ.get("TERO_AWS_REGION")
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1",
            offline=env_offline if offline is None else offline,
            carpeta=(
                carpeta or Path(os.environ.get("TERO_CARPETA") or EXAMPLE_CARPETA)
            ).expanduser(),
            skip_plan=os.environ.get("TERO_SKIP_PLAN", "").strip() in {"1", "true", "yes"},
            temperature=_env_float("TERO_TEMPERATURE", 0.3),
        )
