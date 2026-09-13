"""Diagnóstico de conectividad con AWS y Amazon Bedrock.

Verifica:
1. Detección de credenciales (variables de entorno, .env, perfiles de AWS).
2. STS Caller Identity (cuenta ofuscada, usuario o rol IAM).
3. Invocación mínima a Amazon Bedrock (Nova Lite o perfil cross-region) midiendo latencia y cuota.
"""

from __future__ import annotations

import sys
import time
from typing import Any

from tero.config import Settings
from tero.errors import humanize_exception


def mask_account_id(account: str) -> str:
    """Ofusca el Account ID para no exponer datos sensibles en logs o consola."""
    raw = account.strip()
    if len(raw) <= 4:
        return "****"
    return "*" * (len(raw) - 4) + raw[-4:]


def check_aws_credentials(settings: Settings | None = None) -> tuple[bool, str, dict[str, Any]]:
    """Comprueba si hay credenciales de AWS configuradas en el entorno."""
    try:
        import boto3
    except ImportError:
        return False, "boto3 no está instalado en el entorno.", {}

    settings = settings or Settings.from_env()
    session = boto3.Session(region_name=settings.region)
    creds = session.get_credentials()
    if not creds:
        return False, "No se encontraron credenciales de AWS activas.", {}

    method = getattr(creds, "method", "desconocido")
    return True, f"Credenciales encontradas vía '{method}'.", {"session": session, "method": method}


DOCUMENTED_MODELS: tuple[str, ...] = (
    "amazon.nova-lite-v1:0",
    "zai.glm-4.7-flash",
    "minimax.minimax-m2.5",
)


def _test_single_model(bedrock: Any, model_id: str) -> tuple[bool, str, float, int, int, str]:
    """Prueba invocación de un modelo en Bedrock. Devuelve (ok, active_id, latencia, in_tok, out_tok, error_msg)."""
    candidates = [model_id]
    if model_id == "amazon.nova-lite-v1:0":
        candidates.append("us.amazon.nova-lite-v1:0")

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            start = time.perf_counter()
            response = bedrock.converse(
                modelId=candidate,
                messages=[{"role": "user", "content": [{"text": "Responde con la palabra OK."}]}],
                inferenceConfig={"maxTokens": 10, "temperature": 0.0},
            )
            elapsed = time.perf_counter() - start
            usage = response.get("usage", {})
            in_tokens = usage.get("inputTokens", 0)
            out_tokens = usage.get("outputTokens", 0)
            return True, candidate, elapsed, in_tokens, out_tokens, ""
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            error_msg = getattr(exc, "response", {}).get("Error", {}).get("Message", "")
            if (
                "inference profile" in str(error_msg).lower()
                and candidate != "us.amazon.nova-lite-v1:0"
            ):
                continue
            break

    _code, human_msg = humanize_exception(last_error or RuntimeError("Invocación fallida"))
    return False, model_id, 0.0, 0, 0, human_msg


def run_check_aws(settings: Settings | None = None, *, all_models: bool = False) -> int:
    """Ejecuta el diagnóstico completo e imprime el informe en stdout."""
    print("tero · diagnóstico de conexión a AWS y Bedrock\n")
    settings = settings or Settings.from_env()

    print(f"  Región objetivo : {settings.region}")
    if all_models:
        print(f"  Modelos objetivo: {', '.join(DOCUMENTED_MODELS)} (trio documentado)")
    else:
        print(f"  Modelo objetivo : {settings.model_id}")
    print(f"  Modo en entorno : {'offline' if settings.offline else 'bedrock (online)'}\n")

    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError:
        print("ERROR: boto3 no está instalado en el entorno Python.", file=sys.stderr)
        return 1

    session = boto3.Session(region_name=settings.region)
    creds = session.get_credentials()

    if not creds:
        print("✗ No se encontraron credenciales de AWS.", flush=True)
        print("\nPara conectar Tero con tus claves de AWS:")
        print("  1. Copia la plantilla de configuración:")
        print("     cp .env.example .env")
        print("  2. Edita el archivo .env y completa:")
        print("     TERO_OFFLINE=0")
        print("     TERO_AWS_REGION=us-east-1")
        print("     TERO_MODEL=amazon.nova-lite-v1:0")
        print("     AWS_ACCESS_KEY_ID=tu_access_key_aqui")
        print("     AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui")
        print("  3. (Opcional) Si usas AWS CLI:")
        print("     aws configure")
        print("     export TERO_OFFLINE=0")
        return 1

    method = getattr(creds, "method", "desconocido")
    print(f"✓ Credenciales detectadas (origen: {method})")

    # 1. Verificar STS Caller Identity
    print("  Comprobando identidad con AWS STS...", end="", flush=True)
    try:
        sts = session.client("sts", region_name=settings.region)
        identity = sts.get_caller_identity()
        account_masked = mask_account_id(identity.get("Account", ""))
        arn = identity.get("Arn", "desconocido")
        print(" OK")
        print(f"  - Cuenta   : {account_masked}")
        print(f"  - Identidad: {arn}")
    except (NoCredentialsError, ClientError) as exc:
        print(" FALLÓ")
        _code, msg = humanize_exception(exc)
        print(f"\n✗ Error de autenticación STS: {msg}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(" FALLÓ")
        print(f"\n✗ Error inesperado conectando a STS: {exc}", file=sys.stderr)
        return 1

    # 2. Invocación de prueba a Amazon Bedrock
    bedrock = session.client("bedrock-runtime", region_name=settings.region)
    target_models = list(DOCUMENTED_MODELS) if all_models else [settings.model_id]

    overall_success = True
    print("\n  Comprobando modelos en Amazon Bedrock:")
    for mid in target_models:
        print(f"  • {mid:25s} ...", end="", flush=True)
        ok, active_id, elapsed, in_tok, out_tok, err = _test_single_model(bedrock, mid)
        if ok:
            print(" OK")
            print(f"✓ Modelo activo: {active_id}")
            print(f"    - Latencia     : {elapsed:.2f} s")
            print(f"    - Consumo      : {in_tok} in / {out_tok} out tokens")
            if active_id != mid:
                print(f"    - Perfil cross-region requerido: {active_id}")
        else:
            print(" FALLÓ")
            print(f"    - Error: {err}")
            overall_success = False

    if not overall_success:
        print("\n✗ Uno o más modelos fallaron. Posibles soluciones:", file=sys.stderr)
        print("  - Revisa permisos IAM (bedrock:InvokeModel, InvokeModelWithResponseStream).")
        print("  - Asegúrate de usar la región us-east-1.")
        return 1

    print("\n✓ Conexión completa y verificada. Tero está listo para usar con Bedrock real.")
    print("  Puedes iniciar con:")
    print("    python -m tero tui\n")
    return 0


if __name__ == "__main__":
    sys.exit(run_check_aws())
