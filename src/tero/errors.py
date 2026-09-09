"""Domain errors with Spanish messages for the TUI and CLI."""

from __future__ import annotations

from tero import DEFAULT_MODEL_ID


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
    """Return (code, Spanish message) for Bedrock / network / generic failures.

    Lean path: one Strands + Bedrock stack. No AgentCore. Messages must tell the
    teacher what to fix (creds, region, model enablement) without raw boto dumps.
    """
    if isinstance(exc, TeroError):
        return exc.code, exc.message

    name = type(exc).__name__
    text = str(exc) or name
    lower = text.lower()
    blob = f"{name} {text}".lower()

    # Model access denials first (often AccessDeniedException + model id wording).
    # Do not treat IAM InvokeModel denials as model-access (substring "InvokeModel").
    model_denied = any(
        token in blob
        for token in (
            "you don't have access to the model",
            "access to the model with the specified",
            "model is not authorized",
            "has no access to model",
        )
    ) or ("accessdenied" in blob and "model id" in blob)
    if model_denied:
        return (
            "bedrock_model",
            f"Sin acceso al modelo en esta cuenta/región ({text[:120]}). "
            f"En Bedrock → Model access habilita Nova Lite; "
            f"TERO_MODEL={DEFAULT_MODEL_ID}; región us-east-1.",
        )
    if any(
        token in blob
        for token in (
            "expiredtoken",
            "unrecognizedclient",
            "invalidclienttokenid",
            "accessdeniedexception",
            "accessdenied",
            "unauthorized",
            "not authorized to perform",
            "credentials",
            "unable to locate credentials",
            "nofilecredentials",
            "invalidsecuritytoken",
            "security token",
        )
    ):
        return (
            "bedrock_auth",
            "Amazon Bedrock no aceptó las credenciales o el IAM. "
            "Revisa AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY "
            "(o AWS_BEARER_TOKEN_BEDROCK / `aws configure`), "
            "permisos bedrock:InvokeModel* y región us-east-1.",
        )
    if any(
        token in blob
        for token in (
            "throttl",
            "toomanyrequests",
            "rate exceeded",
            "service unavailable",
            "modeltimeout",
            "model is getting throttled",
            "too many tokens",
            "limitexceeded",
        )
    ):
        return (
            "bedrock_throttle",
            "Bedrock limitó la cuota o está saturado. Espera unos segundos y reintenta (r).",
        )
    if any(
        token in blob
        for token in (
            "validationexception",
            "resourcenotfound",
            "model not ready",
            "isn't supported",
            "is not supported",
            "access to the model",
            "you don't have access",
            "modelidentifier",
            "on-demand throughput",
            "inference profile",
        )
    ):
        return (
            "bedrock_model",
            f"El modelo no está disponible en esta cuenta/región ({text[:140]}). "
            f"En la consola Bedrock habilita Nova Lite, usa región us-east-1, "
            f"y deja TERO_MODEL={DEFAULT_MODEL_ID} (o TERO_MODEL_ID).",
        )
    if any(
        token in blob
        for token in (
            "endpoint",
            "connect",
            "timeout",
            "timed out",
            "network",
            "resolve",
            "name or service not known",
            "temporary failure in name resolution",
        )
    ):
        return (
            "network",
            "No hubo red hacia Bedrock. Comprueba conexión/VPN/región (us-east-1) y reintenta.",
        )
    if "prompt vacío" in lower or "garbage" in lower:
        return "bad_input", text
    if any(
        token in blob
        for token in (
            "modelstreamerrorexception",
            "modelstreamerror",
            "tooluse",
            "tool use",
            "tool_use",
            "invalid tool",
            "unexpected tool",
            "conversationstream",
            "event stream error",
        )
    ):
        return (
            "bedrock_stream",
            "Bedrock interrumpió el stream (ToolUse/Nova Lite). "
            "tero reintenta el borrador una vez; si sigue, pulsa r o /retry.",
        )

    if "empty" in lower and "response" in lower:
        return (
            "bedrock_empty",
            "Bedrock devolvió una respuesta vacía. tero reintenta el borrador una vez; "
            "si sigue fallando, pulsa r o /retry.",
        )
    return (
        "host_error",
        f"Algo falló en el host: {text[:240]}. Puedes reintentar el último encargo (r).",
    )
