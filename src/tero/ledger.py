"""Proof of Pedagogical Agency: Sello Criptográfico de Criterio Docente y Decisional Provenance Ledger.

Registra de forma verificable e inmutable la decisión docente cuando aprueba
un material, ligando los hashes de las fuentes originales, el hash del derivado,
el modelo activo, el trace ID de OpenTelemetry y la nota de intervención pedagógica.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tero.hashutil import sha256_file

if TYPE_CHECKING:
    from tero.workspace import Workspace

FOOTER_STAMP_PREFIX = (
    "*Material co-creado y certificado bajo criterio docente · Tero Decisional Seal ID:"
)


@dataclass
class DecisionalSeal:
    """Sello criptográfico de procedencia decisional docente."""

    seal_id: str
    timestamp: str
    criterio: str = "humano_aprobado"
    decision_type: str = "conversational_approval"
    hash_fuentes: str = ""
    hash_derivado: str = ""
    file_sha256: str = ""
    model_id: str = "tero-offline"
    trace_id: str = ""
    approval_note: str = ""
    accion: str = "crear"
    artifact_path: str = ""
    titulo: str = ""
    tipo: str = ""
    sources: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionalSeal:
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class SealVerificationResult:
    """Resultado de la comprobación criptográfica de un sello docente."""

    valid: bool
    seal_id: str
    checks: dict[str, bool]
    details: dict[str, Any]
    message: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_sources_fingerprint(workspace: Workspace) -> tuple[str, dict[str, str]]:
    """Calcula el hash compuesto SHA-256 de todas las fuentes originales."""
    fingerprints = workspace.fingerprint_sources()
    if not fingerprints:
        return hashlib.sha256(b"{}").hexdigest(), {}
    canonical_json = json.dumps(fingerprints, sort_keys=True, ensure_ascii=False)
    composite_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return composite_hash, fingerprints


def generate_seal_id(hash_fuentes: str, hash_derivado: str, note: str = "") -> str:
    """Genera un identificador único para el sello (e.g. tero-seal-<short-hash>)."""
    seed = f"{hash_fuentes}:{hash_derivado}:{note}:{datetime.now(UTC).isoformat()}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"tero-seal-{digest}"


def create_decisional_seal(
    *,
    workspace: Workspace,
    unsealed_markdown: str,
    accion: str,
    titulo: str,
    tipo: str,
    note: str = "",
    model_id: str = "tero-offline",
    trace_id: str = "",
) -> DecisionalSeal:
    """Construye la estructura de sello antes de la inyección en el artefacto."""
    hash_derivado = hashlib.sha256(unsealed_markdown.encode("utf-8")).hexdigest()
    hash_fuentes, sources = compute_sources_fingerprint(workspace)
    seal_id = generate_seal_id(hash_fuentes, hash_derivado, note)
    timestamp = datetime.now(UTC).isoformat()

    return DecisionalSeal(
        seal_id=seal_id,
        timestamp=timestamp,
        criterio="humano_aprobado",
        decision_type="conversational_approval",
        hash_fuentes=hash_fuentes,
        hash_derivado=hash_derivado,
        file_sha256="",
        model_id=model_id,
        trace_id=trace_id,
        approval_note=note,
        accion=accion,
        artifact_path="",
        titulo=titulo,
        tipo=tipo,
        sources=sources,
    )


def inject_seal_into_markdown(markdown: str, seal: DecisionalSeal) -> str:
    """Inserta el bloque sello_docente en el front matter y el stamp al pie."""
    seal_yaml = (
        "sello_docente:\n"
        f"  seal_id: {seal.seal_id}\n"
        f'  timestamp: "{seal.timestamp}"\n'
        f"  hash_fuentes: {seal.hash_fuentes}\n"
        f"  hash_derivado: {seal.hash_derivado}\n"
        f"  criterio: {seal.criterio}\n"
    )

    footer_stamp = f"\n\n---\n{FOOTER_STAMP_PREFIX} {seal.seal_id}*\n"

    if markdown.startswith("---"):
        end_idx = markdown.find("\n---", 3)
        if end_idx != -1:
            head = markdown[:end_idx]
            tail = markdown[end_idx:]
            sealed_text = f"{head}\n{seal_yaml}{tail[1:]}"
            return sealed_text + footer_stamp

    # Si no había front matter, creamos uno básico
    fm = f"---\n{seal_yaml}---\n\n"
    return fm + markdown + footer_stamp


def extract_seal_from_markdown(markdown: str) -> dict[str, str]:
    """Extrae las claves del sello docente presentes en el front matter o pie."""
    seal_data: dict[str, str] = {}

    # Buscar en front matter
    fm_match = re.search(
        r"^sello_docente:\s*\n"
        r"(?:[ \t]+seal_id:\s*(?P<seal_id>[^\n]+)\n)?"
        r"(?:[ \t]+timestamp:\s*['\"]?(?P<timestamp>[^'\"\n]+)['\"]?\n)?"
        r"(?:[ \t]+hash_fuentes:\s*(?P<hash_fuentes>[^\n]+)\n)?"
        r"(?:[ \t]+hash_derivado:\s*(?P<hash_derivado>[^\n]+)\n)?"
        r"(?:[ \t]+criterio:\s*(?P<criterio>[^\n]+)\n)?",
        markdown,
        re.MULTILINE,
    )
    if fm_match:
        for k, v in fm_match.groupdict().items():
            if v:
                seal_data[k] = v.strip().strip("\"'")

    # Buscar también en pie si no vino en front matter
    if "seal_id" not in seal_data:
        footer_match = re.search(
            r"\*Material co-creado y certificado bajo criterio docente · Tero Decisional Seal ID:\s*([a-zA-Z0-9_-]+)\*",
            markdown,
        )
        if footer_match:
            seal_data["seal_id"] = footer_match.group(1).strip()

    return seal_data


def strip_seal_from_markdown(markdown: str) -> str:
    """Quita el bloque sello_docente y el footer stamp para recalcular hash_derivado."""
    cleaned = re.sub(
        r"sello_docente:\n(?:[ \t]+[a-zA-Z0-9_]+:[^\n]*\n)*",
        "",
        markdown,
    )
    cleaned = re.sub(
        r"\n\n---\n\*Material co-creado y certificado bajo criterio docente · Tero Decisional Seal ID:[^\n\*]+\*\n*",
        "",
        cleaned,
    )
    return cleaned


def save_seal(workspace: Workspace, seal: DecisionalSeal) -> Path:
    """Guarda el registro inmutable en .tero/decisiones/ y .tero/ledger/."""
    payload = json.dumps(seal.as_dict(), indent=2, ensure_ascii=False) + "\n"

    # Escribir en ambas carpetas permitidas (.tero/decisiones y .tero/ledger)
    path_decisiones = workspace.write_artifact(
        f".tero/decisiones/{seal.seal_id}.json", payload, overwrite=True
    )
    try:
        workspace.write_artifact(f".tero/ledger/{seal.seal_id}.json", payload, overwrite=True)
    except Exception:
        pass
    return path_decisiones


def load_seal(workspace: Workspace, seal_id: str) -> DecisionalSeal | None:
    """Carga un sello del ledger por su identificador."""
    clean_id = seal_id.strip()
    candidates = [
        workspace.root / ".tero" / "decisiones" / f"{clean_id}.json",
        workspace.root / ".tero" / "ledger" / f"{clean_id}.json",
    ]
    for path in candidates:
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return DecisionalSeal.from_dict(data)
            except Exception:
                continue
    return None


def verify_seal(workspace: Workspace, artifact_path: Path | str) -> SealVerificationResult:
    """Verifica la integridad criptográfica completa del sello contra fuentes y archivo."""
    target = Path(artifact_path)
    if not target.is_absolute():
        target = workspace.root / target

    if not target.is_file():
        return SealVerificationResult(
            valid=False,
            seal_id="",
            checks={"file_exists": False},
            details={"path": str(target)},
            message=f"Archivo no encontrado: {target}",
        )

    try:
        content = target.read_text(encoding="utf-8")
    except OSError as exc:
        return SealVerificationResult(
            valid=False,
            seal_id="",
            checks={"file_readable": False},
            details={"error": str(exc)},
            message=f"No se pudo leer el archivo: {exc}",
        )

    seal_meta = extract_seal_from_markdown(content)
    seal_id = seal_meta.get("seal_id", "")
    if not seal_id:
        return SealVerificationResult(
            valid=False,
            seal_id="",
            checks={"seal_present": False},
            details={"path": str(target)},
            message="El artefacto no contiene un sello docente válido.",
        )

    ledger_seal = load_seal(workspace, seal_id)
    if ledger_seal is None:
        return SealVerificationResult(
            valid=False,
            seal_id=seal_id,
            checks={"ledger_exists": False},
            details={"searched_seal_id": seal_id},
            message=f"El sello {seal_id} no está registrado en el ledger de decisiones (.tero/decisiones/).",
        )

    # 1. Front matter coincide con ledger
    frontmatter_matches = True
    for key in ("timestamp", "hash_fuentes", "hash_derivado", "criterio"):
        val = seal_meta.get(key)
        expected = getattr(ledger_seal, key, "")
        if val and expected and val != expected:
            frontmatter_matches = False
            break

    # 2. Integridad del artefacto: unsealed hash o file hash
    unsealed = strip_seal_from_markdown(content)
    computed_derivado = hashlib.sha256(unsealed.encode("utf-8")).hexdigest()
    current_file_sha256 = sha256_file(target)

    artifact_intact = computed_derivado == ledger_seal.hash_derivado or (
        bool(ledger_seal.file_sha256) and current_file_sha256 == ledger_seal.file_sha256
    )

    # 3. Integridad de las fuentes originales
    current_sources = workspace.fingerprint_sources()
    recorded_sources = ledger_seal.sources
    sources_mismatched: list[str] = []
    sources_missing: list[str] = []

    for src_path, recorded_hash in recorded_sources.items():
        curr_hash = current_sources.get(src_path)
        if curr_hash is None:
            sources_missing.append(src_path)
        elif curr_hash != recorded_hash:
            sources_mismatched.append(src_path)

    sources_intact = (len(sources_mismatched) == 0) and (len(sources_missing) == 0)

    # 4. Decisión
    decision_valid = ledger_seal.criterio == "humano_aprobado"

    is_valid = frontmatter_matches and artifact_intact and sources_intact and decision_valid

    checks = {
        "ledger_exists": True,
        "frontmatter_matches": frontmatter_matches,
        "artifact_intact": artifact_intact,
        "sources_intact": sources_intact,
        "decision_valid": decision_valid,
    }

    details = {
        "seal_id": ledger_seal.seal_id,
        "timestamp": ledger_seal.timestamp,
        "criterio": ledger_seal.criterio,
        "decision_type": ledger_seal.decision_type,
        "model_id": ledger_seal.model_id,
        "trace_id": ledger_seal.trace_id,
        "approval_note": ledger_seal.approval_note,
        "accion": ledger_seal.accion,
        "artifact_path": ledger_seal.artifact_path,
        "hash_derivado": ledger_seal.hash_derivado,
        "hash_fuentes": ledger_seal.hash_fuentes,
        "sources_checked": len(recorded_sources),
        "sources_mismatched": sources_mismatched,
        "sources_missing": sources_missing,
    }

    if is_valid:
        msg = f"Sello docente {seal_id} VÁLIDO. Integridad de fuentes y artefacto verificada."
    else:
        reasons = []
        if not frontmatter_matches:
            reasons.append("los metadatos del front matter discrepan del ledger")
        if not artifact_intact:
            reasons.append("el contenido del artefacto ha sido alterado")
        if not sources_intact:
            reasons.append(
                f"fuentes originales alteradas ({len(sources_mismatched)} modificadas, {len(sources_missing)} eliminadas)"
            )
        if not decision_valid:
            reasons.append("el criterio no está marcado como humano_aprobado")
        msg = f"Sello docente {seal_id} INVÁLIDO: {', '.join(reasons)}."

    return SealVerificationResult(
        valid=is_valid,
        seal_id=seal_id,
        checks=checks,
        details=details,
        message=msg,
    )
