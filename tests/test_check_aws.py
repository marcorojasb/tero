"""Pruebas para el comando y módulo de diagnóstico de AWS/Bedrock."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocore.exceptions import NoCredentialsError

from tero.check_aws import mask_account_id, run_check_aws
from tero.cli import main
from tero.config import Settings


def test_mask_account_id():
    assert mask_account_id("123456789012") == "********9012"
    assert mask_account_id("1234") == "****"
    assert mask_account_id("12") == "****"
    assert mask_account_id("") == "****"


def test_check_aws_no_credentials_in_empty_env(monkeypatch, capsys):
    # Asegurar que no hay credenciales en el entorno de pruebas
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    with patch("boto3.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session.get_credentials.return_value = None
        mock_session_cls.return_value = mock_session

        settings = Settings(offline=False)
        code = run_check_aws(settings)
        assert code == 1

        captured = capsys.readouterr()
        assert "No se encontraron credenciales de AWS" in captured.out
        assert "cp .env.example .env" in captured.out


def test_check_aws_sts_failure(capsys):
    with patch("boto3.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session.get_credentials.return_value = MagicMock(method="env")
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.side_effect = NoCredentialsError()
        mock_session.client.return_value = mock_sts
        mock_session_cls.return_value = mock_session

        settings = Settings(offline=False)
        code = run_check_aws(settings)
        assert code == 1
        captured = capsys.readouterr()
        assert "Error de autenticación STS" in captured.err


def test_check_aws_success_mock(capsys):
    with patch("boto3.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session.get_credentials.return_value = MagicMock(method="env")

        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:user/profesor",
        }

        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = {
            "usage": {"inputTokens": 5, "outputTokens": 2},
        }

        def mock_client(service, **kwargs):
            if service == "sts":
                return mock_sts
            if service == "bedrock-runtime":
                return mock_bedrock
            return MagicMock()

        mock_session.client.side_effect = mock_client
        mock_session_cls.return_value = mock_session

        settings = Settings(offline=False, model_id="amazon.nova-lite-v1:0")
        code = run_check_aws(settings)
        assert code == 0

        captured = capsys.readouterr()
        assert "✓ Credenciales detectadas" in captured.out
        assert "Cuenta   : ********9012" in captured.out
        assert "✓ Modelo activo: amazon.nova-lite-v1:0" in captured.out
        assert "✓ Conexión completa y verificada" in captured.out


def test_cli_check_aws_subcommand(capsys):
    with patch("boto3.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session.get_credentials.return_value = None
        mock_session_cls.return_value = mock_session

        code = main(["check-aws"])
        assert code == 1
        captured = capsys.readouterr()
        assert "diagnóstico de conexión a AWS" in captured.out


def test_check_aws_all_models_mock(capsys):
    with patch("boto3.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session.get_credentials.return_value = MagicMock(method="env")

        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:user/profesor",
        }

        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = {
            "usage": {"inputTokens": 5, "outputTokens": 2},
        }

        def mock_client(service, **kwargs):
            if service == "sts":
                return mock_sts
            if service == "bedrock-runtime":
                return mock_bedrock
            return MagicMock()

        mock_session.client.side_effect = mock_client
        mock_session_cls.return_value = mock_session

        settings = Settings(offline=False)
        code = run_check_aws(settings, all_models=True)
        assert code == 0

        captured = capsys.readouterr()
        assert "✓ Credenciales detectadas" in captured.out
        assert "trio documentado" in captured.out
        assert "amazon.nova-lite-v1:0" in captured.out
        assert "zai.glm-4.7-flash" in captured.out
        assert "minimax.minimax-m2.5" in captured.out
        assert "✓ Conexión completa y verificada" in captured.out
