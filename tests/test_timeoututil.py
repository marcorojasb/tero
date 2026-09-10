"""Turn timeout helper."""

from __future__ import annotations

import time

import pytest

from tero.config import Settings
from tero.timeoututil import TurnTimeoutError, call_with_timeout


def test_call_with_timeout_disabled():
    assert call_with_timeout(0, lambda: 42) == 42


def test_call_with_timeout_fires():
    with pytest.raises(TurnTimeoutError) as exc:
        call_with_timeout(0.2, time.sleep, 2.0)
    assert exc.value.code == "turn_timeout"


def test_settings_bedrock_default_timeout(monkeypatch):
    monkeypatch.delenv("TERO_TURN_TIMEOUT", raising=False)
    monkeypatch.setenv("TERO_OFFLINE", "0")
    monkeypatch.delenv("TERO_MODEL", raising=False)
    settings = Settings.from_env(offline=False)
    assert settings.turn_timeout_s == 120.0


def test_settings_offline_default_no_timeout(monkeypatch):
    monkeypatch.delenv("TERO_TURN_TIMEOUT", raising=False)
    settings = Settings.from_env(offline=True)
    assert settings.turn_timeout_s == 0.0
