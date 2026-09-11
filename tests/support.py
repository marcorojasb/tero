"""Utilidades compartidas por los tests del agente conversacional.

Todo es offline: no hay Bedrock, ni red, ni claves. La carpeta demo se copia a
`tmp_path` en cada test, así que ningún test toca el repo.
"""

from __future__ import annotations

from pathlib import Path

from tero.config import Settings
from tero.session import TeacherSession
from tero.types import Encargo
from tero.workspace import Workspace

ENCARGO_DEMO = Encargo(
    curso="4° básico",
    asignatura="Lenguaje y Comunicación",
    oa="LEN-4B-OA04",
    duracion="45 min",
)

PEDIDO_PLANIFICACION = (
    "Prepara una planificación de 45 minutos sobre el cuento del cóndor y el huemul, "
    "alineada al OA de comprensión lectora. Usa solo las fuentes locales."
)
PEDIDO_GUIA = "Prepara una guía sobre el cuento del cóndor y el huemul."
PEDIDO_PREGUNTA = "¿Cuántos OA tiene el catálogo de 4° básico?"


def settings_for(workspace: Workspace) -> Settings:
    return Settings(offline=True, carpeta=workspace.root)


def open_session(
    workspace: Workspace,
    encargo: Encargo | None = None,
    events: list[dict] | None = None,
) -> TeacherSession:
    return TeacherSession(
        workspace,
        settings_for(workspace),
        encargo=encargo or ENCARGO_DEMO,
        emit=events.append if events is not None else None,
    )


def artifact_paths(workspace: Workspace, folder: str = "derivados") -> list[Path]:
    return sorted((workspace.root / folder).glob("*.md"))


def rel(workspace: Workspace, path: Path) -> str:
    return path.relative_to(workspace.root).as_posix()


def crear_y_aprobar(
    workspace: Workspace,
    prompt: str = PEDIDO_PLANIFICACION,
    encargo: Encargo | None = None,
) -> Path:
    """Deja un material escrito en derivados/ para poder editar o adaptar."""
    session = open_session(workspace, encargo)
    session.start_turn(prompt)
    result = session.aprobar()
    assert result.path is not None
    return result.path
