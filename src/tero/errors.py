"""Domain errors with Spanish messages for the TUI and CLI."""


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
