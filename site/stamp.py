#!/usr/bin/env python3
"""Stamp the Git SHA onto the static site so the landing tracks the deploy."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "build-info.json"


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def stamp() -> dict[str, str]:
    sha = os.environ.get("GITHUB_SHA") or _git("rev-parse", "HEAD")
    short = sha[:7] if sha else "local"
    info = {
        "sha": sha or "local",
        "short": short,
        "ref": os.environ.get("GITHUB_REF_NAME") or _git("rev-parse", "--abbrev-ref", "HEAD") or "dev",
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "source": "github-actions" if os.environ.get("GITHUB_SHA") else "local",
    }
    OUT.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info


if __name__ == "__main__":
    printed = stamp()
    print(f"stamped {OUT} · {printed['short']}")
