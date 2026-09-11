"""Escritura del host: solo después de que la persona aprueba. El modelo nunca escribe."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tero.artifacts import artifact_filename, materialize_markdown, write_accepted
from tero.types import Encargo, Propuesta
from tero.workspace import Workspace


@dataclass
class WriteResult:
    path: Path | None
    markdown: str | None
    accion: str
    note: str = ""


def write_approved(
    *,
    workspace: Workspace,
    encargo: Encargo,
    propuesta: Propuesta,
    note: str = "",
) -> WriteResult:
    """Escribe la propuesta aprobada en `derivados/`. Nunca sobrescribe nada.

    `editar` y `adaptar` también escriben un archivo nuevo: el material de origen
    queda intacto y la fila nueva declara `origen:` en el front matter.
    """
    markdown = materialize_markdown(encargo, propuesta)
    filename = artifact_filename(propuesta.draft.tipo, propuesta.draft.titulo)
    path = write_accepted(workspace, filename, markdown)
    return WriteResult(path=path, markdown=markdown, accion=propuesta.accion, note=note)
