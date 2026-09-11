"""Settings: modelo por defecto, overrides por entorno y carpeta de trabajo."""

from __future__ import annotations

from pathlib import Path

from tero import DEFAULT_MODEL_ID
from tero.config import Settings


def test_settings_accepts_tero_model_id(monkeypatch):
    monkeypatch.setattr("tero.config._load_dotenv", lambda: None)
    monkeypatch.setenv("TERO_MODEL_ID", "amazon.nova-micro-v1:0")
    monkeypatch.delenv("TERO_MODEL", raising=False)
    settings = Settings.from_env(offline=True)
    assert settings.model_id == "amazon.nova-micro-v1:0"


def test_tero_model_gana_sobre_tero_model_id(monkeypatch):
    monkeypatch.setenv("TERO_MODEL", "us.amazon.nova-lite-v1:0")
    monkeypatch.setenv("TERO_MODEL_ID", "amazon.nova-micro-v1:0")
    assert Settings.from_env(offline=True).model_id == "us.amazon.nova-lite-v1:0"


def test_modelo_por_defecto_y_region(monkeypatch):
    monkeypatch.delenv("TERO_MODEL", raising=False)
    monkeypatch.delenv("TERO_MODEL_ID", raising=False)
    monkeypatch.delenv("TERO_AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    settings = Settings.from_env(offline=True)
    assert settings.model_id == DEFAULT_MODEL_ID
    assert settings.region == "us-east-1"
    assert settings.skip_plan is False


def test_carpeta_explicita_gana_sobre_el_entorno(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TERO_CARPETA", str(tmp_path / "otra"))
    settings = Settings.from_env(offline=True, carpeta=tmp_path / "elegida")
    assert settings.carpeta == tmp_path / "elegida"
