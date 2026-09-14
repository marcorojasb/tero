"""Escritura del host: solo después de que la persona aprueba. El modelo nunca escribe."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tero.artifacts import artifact_filename, materialize_markdown, write_accepted
from tero.errors import WorkspaceError
from tero.hashutil import sha256_file
from tero.ledger import (
    DecisionalSeal,
    create_decisional_seal,
    inject_seal_into_markdown,
    save_seal,
)
from tero.types import Encargo, Propuesta
from tero.workspace import Workspace


@dataclass
class WriteResult:
    path: Path | None
    markdown: str | None
    accion: str
    note: str = ""
    seal: DecisionalSeal | None = None


def write_approved(
    *,
    workspace: Workspace,
    encargo: Encargo,
    propuesta: Propuesta,
    note: str = "",
    model_id: str = "tero-offline",
    trace_id: str = "",
) -> WriteResult:
    """Escribe la propuesta aprobada en `derivados/`. Nunca sobrescribe nada.

    Genera un Sello Criptográfico de Criterio Docente registrado en el
    Decisional Provenance Ledger (`.tero/decisiones/` y `.tero/ledger/`), vinculando
    los hashes de las fuentes originales, el hash del artefacto derivado,
    la nota de aprobación y el trace ID de telemetría.
    """
    if propuesta.accion in {"editar", "adaptar"} and propuesta.origen:
        origen_path = workspace.root / propuesta.origen
        if not origen_path.is_file():
            raise WorkspaceError(f"Material de origen no encontrado: {propuesta.origen}")
    unsealed_markdown = materialize_markdown(encargo, propuesta)
    filename = artifact_filename(propuesta.draft.tipo, propuesta.draft.titulo)

    # Crear el sello criptográfico de criterio docente
    seal = create_decisional_seal(
        workspace=workspace,
        unsealed_markdown=unsealed_markdown,
        accion=propuesta.accion,
        titulo=propuesta.draft.titulo,
        tipo=propuesta.draft.tipo.value,
        note=note,
        model_id=model_id,
        trace_id=trace_id,
    )
    sealed_markdown = inject_seal_into_markdown(unsealed_markdown, seal)
    path = write_accepted(workspace, filename, sealed_markdown)

    # Guardar en ledger con la ruta y el hash del archivo escrito
    rel_path = path.resolve().relative_to(workspace.root).as_posix()
    seal.artifact_path = rel_path
    seal.file_sha256 = sha256_file(path)
    save_seal(workspace, seal)

    return WriteResult(
        path=path,
        markdown=sealed_markdown,
        accion=propuesta.accion,
        note=note,
        seal=seal,
    )
