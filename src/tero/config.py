"""Runtime settings. No secrets. Defaults to Bedrock amazon.nova-lite-v1:0."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from tero import DEFAULT_MODEL_ID

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_CARPETA = PACKAGE_ROOT / "examples" / "carpeta-demo"


@dataclass(frozen=True)
class Settings:
    model_id: str = DEFAULT_MODEL_ID
    region: str = "us-east-1"
    offline: bool = False
    carpeta: Path = EXAMPLE_CARPETA
    skip_plan: bool = False

    @classmethod
    def from_env(cls, *, offline: bool | None = None, carpeta: Path | None = None) -> Settings:
        env_offline = os.environ.get("TERO_OFFLINE", "").strip() in {"1", "true", "yes"}
        return cls(
            model_id=os.environ.get("TERO_MODEL", DEFAULT_MODEL_ID).strip() or DEFAULT_MODEL_ID,
            region=os.environ.get("TERO_AWS_REGION")
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1",
            offline=env_offline if offline is None else offline,
            carpeta=(
                carpeta or Path(os.environ.get("TERO_CARPETA") or EXAMPLE_CARPETA)
            ).expanduser(),
            skip_plan=os.environ.get("TERO_SKIP_PLAN", "").strip() in {"1", "true", "yes"},
        )
