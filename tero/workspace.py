"""Sandboxed teacher work folder: originals stay read-only."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

TEXT_SUFFIXES = {".md", ".txt", ".markdown", ".csv", ".json"}
PDF_SUFFIX = ".pdf"
SKIP_DIR_NAMES = {"derivados", "out", ".git", "__pycache__", ".venv", "venv"}
MAX_FILE_BYTES = 400_000
SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}\.md$")


class WorkspaceError(ValueError):
    """Invalid path or write policy violation."""


@dataclass(frozen=True)
class SourceFile:
    """A readable source inside the teacher folder."""

    relative_path: str
    size_bytes: int
    kind: str


@dataclass
class Workspace:
    """A teacher work folder. Writes are allowed only under `derivados/`."""

    root: Path
    as_draft: bool = False
    last_write: Path | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root).expanduser().resolve()
        if not self.root.is_dir():
            raise WorkspaceError(f"La carpeta de trabajo no existe: {self.root}")

    @property
    def derivados(self) -> Path:
        return self.root / "derivados"

    def resolve_source(self, relative_path: str) -> Path:
        """Resolve a source path, blocking traversal and derivados."""
        if not relative_path or relative_path.strip() != relative_path:
            relative_path = (relative_path or "").strip()
        candidate = (self.root / relative_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceError("Ruta fuera de la carpeta de trabajo.") from exc
        if self._is_under_derivados(candidate):
            raise WorkspaceError("No se leen artefactos derivados como fuentes originales.")
        if not candidate.is_file():
            raise WorkspaceError(f"No existe el archivo fuente: {relative_path}")
        return candidate

    def _is_under_derivados(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.derivados.resolve())
            return True
        except ValueError:
            return False

    def list_sources(self) -> list[SourceFile]:
        """List original source files (never includes derivados/)."""
        found: list[SourceFile] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in path.relative_to(self.root).parts):
                continue
            suffix = path.suffix.lower()
            if suffix not in TEXT_SUFFIXES and suffix != PDF_SUFFIX:
                continue
            rel = path.relative_to(self.root).as_posix()
            kind = "pdf" if suffix == PDF_SUFFIX else suffix.lstrip(".")
            found.append(SourceFile(relative_path=rel, size_bytes=path.stat().st_size, kind=kind))
        return found

    def read_text(self, relative_path: str) -> str:
        """Read a source file as UTF-8 text (PDFs are extracted)."""
        path = self.resolve_source(relative_path)
        if path.stat().st_size > MAX_FILE_BYTES:
            raise WorkspaceError(f"Archivo demasiado grande (máx. {MAX_FILE_BYTES} bytes): {relative_path}")
        if path.suffix.lower() == PDF_SUFFIX:
            return _read_pdf(path)
        return path.read_text(encoding="utf-8", errors="replace")

    def fingerprint_sources(self) -> dict[str, str]:
        """SHA-256 of each original source, used to prove they were not overwritten."""
        fingerprints: dict[str, str] = {}
        for source in self.list_sources():
            data = (self.root / source.relative_path).read_bytes()
            fingerprints[source.relative_path] = hashlib.sha256(data).hexdigest()
        return fingerprints

    def write_derived(
        self,
        filename: str,
        markdown: str,
        citations: list[str],
        *,
        as_draft: bool | None = None,
    ) -> Path:
        """Write a proposal under derivados/. Never touches originals."""
        raw = (filename or "").strip()
        filename = Path(raw).name
        if raw != filename or not SAFE_FILENAME.match(filename):
            raise WorkspaceError(
                "Nombre de archivo inválido. Use solo letras, números, punto, "
                "guion o guion bajo, y extensión .md (ej. planificacion-clase.md)."
            )
        if not markdown or not markdown.strip():
            raise WorkspaceError("La propuesta está vacía.")
        if not citations:
            raise WorkspaceError("Toda propuesta debe citar al menos una fuente original.")

        missing = []
        for cite in citations:
            cite = cite.strip()
            try:
                self.resolve_source(cite)
            except WorkspaceError:
                missing.append(cite)
        if missing:
            raise WorkspaceError(
                "Citas que no coinciden con fuentes originales: " + ", ".join(missing)
            )

        draft = self.as_draft if as_draft is None else as_draft
        folder = self.derivados / "borradores" if draft else self.derivados
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / filename
        dest.write_text(markdown.strip() + "\n", encoding="utf-8")
        self.last_write = dest
        self.as_draft = False
        return dest


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise WorkspaceError("pypdf no está instalado; no se pueden leer PDF.") from exc
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    if not pages:
        raise WorkspaceError(f"PDF sin texto extraíble: {path.name}")
    return "\n\n".join(pages)
