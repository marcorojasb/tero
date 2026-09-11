"""Carpeta de trabajo: system of record.

Search / list / read only inside the folder. Originals are never overwritten.
Accepted artifacts land in derivados/; teacher drafts in borradores/.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tero.errors import HashMismatchError, WorkspaceError, WriteGuardError
from tero.hashutil import sha256_file
from tero.types import SourceRecord

INDEX_NAME = ".tero/index.json"
PROTECTED_WRITE_ROOTS = ("derivados", "borradores", ".tero")
SKIP_DIR_NAMES = {".git", "node_modules", "__pycache__", ".venv"}
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".csv",
    ".json",
    ".yml",
    ".yaml",
    ".oa",
    ".xml",
    ".markdown",
}
PDF_SUFFIX = ".pdf"


class Workspace:
    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        if not self.root.exists():
            raise WorkspaceError(f"La carpeta de trabajo no existe: {self.root}")
        if not self.root.is_dir():
            raise WorkspaceError(f"La carpeta de trabajo no es un directorio: {self.root}")
        (self.root / "derivados").mkdir(exist_ok=True)
        (self.root / "borradores").mkdir(exist_ok=True)
        (self.root / ".tero").mkdir(exist_ok=True)
        (self.root / ".tero" / "transcripciones").mkdir(exist_ok=True)

    @property
    def index_path(self) -> Path:
        return self.root / INDEX_NAME

    def is_write_allowed(self, path: Path) -> bool:
        relative = self._relative(path)
        return relative.parts[0] in PROTECTED_WRITE_ROOTS if relative.parts else False

    def resolve_source(self, relative: str) -> Path:
        target = self._safe_join(relative)
        if not target.exists() or not target.is_file():
            raise WorkspaceError(f"Fuente no encontrada: {relative}")
        if self.is_write_allowed(target) and target.parts[-2:] and "fuentes" not in target.parts:
            # derivados/borradores are not sources
            rel = self._relative(target).as_posix()
            if rel.startswith(("derivados/", "borradores/", ".tero/")):
                raise WorkspaceError(f"Eso no es una fuente original: {relative}")
        return target

    def list_sources(self) -> list[SourceRecord]:
        index = self.load_index()
        records: list[SourceRecord] = []
        for path in self._iter_source_files():
            relative = self._relative(path).as_posix()
            digest = sha256_file(path)
            previous = (index.get("files") or {}).get(relative) or {}
            changed = bool(previous) and previous.get("sha256") != digest
            records.append(
                SourceRecord(
                    relative_path=relative,
                    sha256=digest,
                    bytes=path.stat().st_size,
                    changed=changed,
                )
            )
        records.sort(key=lambda item: item.relative_path)
        return records

    def fingerprint_sources(self) -> dict[str, str]:
        return {item.relative_path: item.sha256 for item in self.list_sources()}

    def read_source(self, relative: str, *, max_chars: int = 12_000) -> dict[str, Any]:
        path = self.resolve_source(relative)
        digest = sha256_file(path)
        index = self.load_index()
        previous = (index.get("files") or {}).get(self._relative(path).as_posix()) or {}
        changed = bool(previous) and previous.get("sha256") != digest
        text = _read_file_text(path)
        truncated = False
        if len(text) > max_chars:
            text = text[:max_chars] + "\n…[truncado]"
            truncated = True
        payload = {
            "path": self._relative(path).as_posix(),
            "sha256": digest,
            "changed": changed,
            "truncated": truncated,
            "text": text,
        }
        if changed:
            payload["warning"] = HashMismatchError(payload["path"]).message
        return payload

    def list_artifacts(self) -> list[str]:
        """Material ya escrito (derivados/ y borradores/) que se puede editar o adaptar."""
        items: list[str] = []
        for folder in ("derivados", "borradores"):
            root = self.root / folder
            if not root.is_dir():
                continue
            for path in sorted(root.glob("*.md")):
                items.append(self._relative(path).as_posix())
        return items

    def read_document(self, relative: str, *, max_chars: int = 20_000) -> str:
        """Lee cualquier documento de la carpeta (fuentes, derivados, borradores). Solo lectura."""
        path = self._safe_join(relative)
        if not path.exists() or not path.is_file():
            raise WorkspaceError(f"No existe en la carpeta: {relative}")
        text = _read_file_text(path)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n…[truncado]"
        return text

    def unique_artifact_path(self, relative_under_allowed: str) -> str:
        """Ruta libre: agrega -2, -3… si ya existe. Nunca sobrescribe material escrito."""
        target = self._safe_join(relative_under_allowed)
        if not target.exists():
            return relative_under_allowed
        stem, suffix = target.stem, target.suffix
        parent = target.parent.relative_to(self.root).as_posix()
        prefix = "" if parent in {".", ""} else f"{parent}/"
        for n in range(2, 100):
            candidate = f"{prefix}{stem}-{n}{suffix}"
            if not self._safe_join(candidate).exists():
                return candidate
        raise WorkspaceError(f"Demasiadas versiones de {relative_under_allowed}")

    def write_artifact(
        self, relative_under_allowed: str, content: str, *, overwrite: bool = False
    ) -> Path:
        target = self._safe_join(relative_under_allowed)
        if not self.is_write_allowed(target):
            raise WriteGuardError(relative_under_allowed)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            raise WorkspaceError(f"Ya existe, no se sobreescribe: {relative_under_allowed}")
        target.write_text(content, encoding="utf-8")
        return target

    def rebuild_index(self) -> dict[str, Any]:
        files: dict[str, Any] = {}
        for path in self._iter_source_files():
            relative = self._relative(path).as_posix()
            files[relative] = {
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        payload = {
            "version": 1,
            "indexed_at": datetime.now(UTC).isoformat(),
            "files": files,
        }
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return payload

    def load_index(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return self.rebuild_index()
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return self.rebuild_index()

    def ensure_index(self) -> dict[str, Any]:
        if self.index_path.exists():
            return self.load_index()
        return self.rebuild_index()

    def search(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        needle = query.strip().lower()
        if not needle:
            return []
        hits: list[dict[str, Any]] = []
        for path in self._iter_source_files():
            try:
                text = _read_file_text(path)
            except OSError:
                continue
            lower = text.lower()
            idx = lower.find(needle)
            if idx < 0:
                continue
            start = max(0, idx - 80)
            snippet = text[start : idx + len(query) + 80].replace("\n", " ")
            hits.append(
                {
                    "path": self._relative(path).as_posix(),
                    "snippet": snippet.strip(),
                }
            )
            if len(hits) >= limit:
                break
        return hits

    def _iter_source_files(self) -> Iterable[Path]:
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            relative = self._relative(path)
            if relative.parts and relative.parts[0] in PROTECTED_WRITE_ROOTS:
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES and path.suffix.lower() != PDF_SUFFIX:
                continue
            yield path

    def _safe_join(self, relative: str) -> Path:
        if not relative or relative.startswith("/") or "\\" in relative:
            raise WorkspaceError(f"Ruta inválida: {relative}")
        candidate = (self.root / relative).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceError(f"Ruta fuera de la carpeta de trabajo: {relative}") from exc
        return candidate

    def _relative(self, path: Path) -> Path:
        return path.resolve().relative_to(self.root)


def _read_file_text(path: Path) -> str:
    if path.suffix.lower() == PDF_SUFFIX:
        return _read_pdf(path)
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return f"[PDF: instala pypdf para leer {path.name}]"
    reader = PdfReader(str(path))
    chunks: list[str] = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    text = "\n".join(chunks).strip()
    return text or f"[PDF sin texto extraíble: {path.name}]"
