"""Strands tools bound to a teacher workspace."""

from __future__ import annotations

from typing import TYPE_CHECKING

from strands import tool

from tero.workspace import Workspace, WorkspaceError

if TYPE_CHECKING:
    from collections.abc import Callable


def build_tools(workspace: Workspace) -> list[Callable]:
    """Create Strands tools closed over a single workspace."""

    @tool
    def list_sources() -> str:
        """Lista los archivos fuente originales de la carpeta de trabajo del o de la docente.

        No incluye la carpeta derivados/. Úsalo primero para saber qué hay disponible.
        """
        sources = workspace.list_sources()
        if not sources:
            return "No hay fuentes legibles (se aceptan .md, .txt, .csv, .json, .pdf)."
        lines = [f"Fuentes en la carpeta de trabajo ({len(sources)}):"]
        for item in sources:
            lines.append(f"- {item.relative_path} ({item.kind}, {item.size_bytes} bytes)")
        return "\n".join(lines)

    @tool
    def read_source(relative_path: str) -> str:
        """Lee el contenido de un archivo fuente original (texto o PDF).

        Args:
            relative_path: Ruta relativa dentro de la carpeta de trabajo, por ejemplo 01-oa-curriculo.md.
        """
        try:
            body = workspace.read_text(relative_path)
        except WorkspaceError as exc:
            return f"Error al leer fuente: {exc}"
        return f"--- tero:source path={relative_path} ---\n{body}"

    @tool
    def write_derived(filename: str, markdown: str, citations: str) -> str:
        """Escribe una propuesta derivada en derivados/ SOLO si el o la docente aprueba.

        Esta herramienta está protegida por una puerta de aprobación humana.
        Nunca sobrescribe archivos originales. Si el o la docente rechaza, no se escribe.
        Si pide borrador, se guarda en derivados/borradores/.

        Args:
            filename: Nombre del archivo .md a crear (solo el nombre, sin carpetas).
            markdown: Propuesta completa en Markdown, incluyendo una sección de fuentes citadas.
            citations: Archivos fuente citados, separados por punto y coma. Ejemplo: 01-oa-curriculo.md; 02-apuntes-docente.md
        """
        cites = [part.strip() for part in citations.replace(",", ";").split(";") if part.strip()]
        try:
            path = workspace.write_derived(filename, markdown, cites)
        except WorkspaceError as exc:
            return f"Error al escribir derivado: {exc}"
        rel = path.relative_to(workspace.root).as_posix()
        kind = "borrador" if "borradores" in path.parts else "propuesta aprobada"
        return f"Escrito ({kind}): {rel}\nCitas: {', '.join(cites)}"

    return [list_sources, read_source, write_derived]


ALLOWED_TOOLS = ["list_sources", "read_source"]
GATED_TOOL = "write_derived"
