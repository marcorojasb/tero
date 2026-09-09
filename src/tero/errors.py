"""Domain errors with Spanish messages for the TUI and CLI."""

from __future__ import annotations


class TeroError(Exception):
    def __init__(self, message: str, *, code: str = "tero_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class WorkspaceError(TeroError):
    def __init__(self, message: str, *, code: str = "workspace") -> None:
        super().__init__(message, code=code)


class HashMismatchError(WorkspaceError):
    def __init__(self, path: str) -> None:
        super().__init__(
            f"El original cambió desde el índice: {path}. tero no lo sobreescribe.",
            code="hash_mismatch",
        )
        self.path = path


class WriteGuardError(WorkspaceError):
    def __init__(self, path: str) -> None:
        super().__init__(
            f"Escritura rechazada fuera de derivados/borradores/.tero: {path}",
            code="write_guard",
        )
        self.path = path


class ProtocolError(TeroError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="protocol")


def humanize_exception(exc: BaseException) -> tuple[str, str]:
    """Return (code, Spanish message) for Bedrock / network / generic failures."""
    if isinstance(exc, TeroError):
        return exc.code, exc.message

    name = type(exc).__name__
    text = str(exc) or name
    lower = text.lower()
    blob = f"{name} {text}".lower()

    if any(
        token in blob
        for token in (
            "expiredtoken",
            "unrecognizedclient",
            "invalidclienttokenid",
            "accessdenied",
            "credentials",
            "unable to locate credentials",
            "nofilecredentials",
        )
    ):
        return (
            "bedrock_auth",
            "Amazon Bedrock no aceptó las credenciales. "
            "Revisa AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / "
            "AWS_BEARER_TOKEN_BEDROCK o `aws configure`, y vuelve a intentar.",
        )
    if any(
        token in blob
        for token in (
            "throttl",
            "toomanyrequests",
            "rate exceeded",
            "service unavailable",
            "modeltimeout",
        )
    ):
        return (
            "bedrock_throttle",
            "Bedrock está saturado o limitó la cuota. Espera unos segundos y reintenta (Enter).",
        )
    if any(
        token in blob
        for token in (
            "validationexception",
            "resourcenotfound",
            "model not ready",
            "isn't supported",
            "access to the model",
        )
    ):
        return (
            "bedrock_model",
            f"El modelo no está disponible en esta cuenta/región ({text[:160]}). "
            "Prueba amazon.nova-lite-v1:0 en us-east-1 o cambia TERO_MODEL.",
        )
    if any(token in blob for token in ("endpoint", "connect", "timeout", "network", "resolve")):
        return (
            "network",
            "No hubo red hacia Bedrock. Comprueba conexión/VPN/región y reintenta.",
        )
    if "prompt vacío" in lower or "garbage" in lower:
        return "bad_input", text
    return "host_error", f"Algo falló en el host: {text[:240]}. Puedes reintentar el último encargo."
