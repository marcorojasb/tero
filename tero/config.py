"""Environment and Bedrock model configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Amazon Nova Lite: widely available on Bedrock, Spanish-capable, no Anthropic
# first-use form. Override with TERO_MODEL_ID.
DEFAULT_MODEL_ID = "amazon.nova-lite-v1:0"
DEFAULT_REGION = "us-east-1"


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from the environment."""

    model_id: str
    region: str
    temperature: float
    max_tokens: int


def load_env(dotenv_path: str | Path | None = None) -> None:
    """Load `.env` from the given path or the current working directory."""
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)
    else:
        load_dotenv(override=False)


def get_settings() -> Settings:
    """Read model settings from the environment."""
    return Settings(
        model_id=os.environ.get("TERO_MODEL_ID", DEFAULT_MODEL_ID).strip() or DEFAULT_MODEL_ID,
        region=(
            os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or DEFAULT_REGION
        ).strip(),
        temperature=float(os.environ.get("TERO_TEMPERATURE", "0.3")),
        max_tokens=int(os.environ.get("TERO_MAX_TOKENS", "4096")),
    )


def has_aws_credentials() -> bool:
    """Return True if typical AWS or Bedrock credentials appear to be present."""
    if os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        return True
    if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        return True
    creds = Path.home() / ".aws" / "credentials"
    if creds.is_file() and creds.stat().st_size > 0:
        return True
    # IAM role / container credentials
    if os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI") or os.environ.get(
        "AWS_CONTAINER_CREDENTIALS_FULL_URI"
    ):
        return True
    return False
