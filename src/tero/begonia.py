"""Cliente de solo lectura del banco pedagógico "begonia" (material oficial MINEDUC).

El banco es un servidor local del docente con una API HTTP pública. tero lo
consulta por GET y **nunca** escribe en él: no hay métodos de escritura en este
módulo. Si el banco no está configurado o no responde, todo degrada a un estado
explícito en español y el turno del agente sigue con la carpeta local.

Sin dependencias nuevas: `urllib.request` de la stdlib.
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

DEFAULT_TIMEOUT = 6.0

# El snapshot del banco se reusa dentro del turno; pasado el TTL se vuelve a pedir.
SNAPSHOT_TTL = 300.0

# Un transporte devuelve (status, cuerpo). Se inyecta en tests para no usar red.
Transport = Callable[[str, dict[str, str], float], "tuple[int, bytes]"]

NO_CONFIGURADO = "banco_no_configurado"

_MENSAJE_NO_CONFIGURADO = (
    "El banco pedagógico (begonia) no está configurado en este equipo: falta "
    "TERO_BEGONIA_URL o la clave (TERO_BEGONIA_API_KEY / TERO_BEGONIA_KEY_FILE)."
)

INSTRUCCION_NO_CONFIGURADO = (
    "Sigue con la carpeta local (list_sources, search_sources, read_source) y dile "
    "a la persona que no pudiste consultar el banco oficial de material MINEDUC."
)

INSTRUCCION_ERROR = (
    "Puedes reintentar la consulta al banco una vez; si vuelve a fallar, sigue con "
    "la carpeta local y dilo en la propuesta."
)

# Códigos OA del banco, p. ej. "CN05 OA 12". El id del catálogo de tero
# (LEN-4B-OA04) NO sirve como filtro del banco.
_OA_CODE = re.compile(r"^[A-Z]{2,4}\d{2}\s+OA\s+\d{1,2}$", flags=re.IGNORECASE)


@dataclass(frozen=True)
class Reply:
    """Respuesta del banco. Nunca se lanza una excepción hacia el agente."""

    ok: bool
    disponible: bool
    code: str = ""
    error: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"ok": self.ok, "disponible": self.disponible}
        if self.code:
            payload["code"] = self.code
        if self.error:
            payload["error"] = self.error
        payload.update(self.data)
        return payload


def no_configurado() -> Reply:
    return Reply(
        ok=False,
        disponible=False,
        code=NO_CONFIGURADO,
        error=_MENSAJE_NO_CONFIGURADO,
    )


def resolve_api_key(api_key: str = "", key_file: str | os.PathLike[str] = "") -> str:
    """Clave directa o la primera línea útil del archivo de claves.

    El archivo del docente tiene líneas `# etiqueta` y líneas de clave: se ignora
    lo comentado y lo vacío. Nunca se registra ni se muestra el valor.
    """
    direct = str(api_key or "").strip()
    if direct:
        return direct
    raw_path = str(key_file or "").strip()
    if not raw_path:
        return ""
    try:
        with open(os.path.expanduser(raw_path), encoding="utf-8") as handle:
            for line in handle:
                candidate = line.strip()
                if candidate and not candidate.startswith("#"):
                    return candidate
    except OSError:
        return ""
    return ""


def _fold(value: Any) -> str:
    """Minúsculas sin acentos ni símbolos de grado, para comparar etiquetas."""
    text = str(value or "").strip().lower().replace("º", "°")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.split())


# El banco etiqueta el mismo curso de varias formas ("5° Básico", "5º Básico",
# "5º básico"): se piden todas las variantes separadas por coma (el API las une).
_LEVELS = {"basico": "Básico", "medio": "Medio"}

_NIVELES_ESPECIALES = {
    "nt": "NT (Nivel Transición)",
    "sc": "SC (Sala Cuna)",
    "nm": "NM (Nivel Medio)",
}

_CURSO = re.compile(r"^(\d{1,2})\s*°?\s*(basico|medio)\b\s*(tp|fg|hc)?", flags=re.IGNORECASE)

# Nombre canónico de la asignatura en el banco (los cuenta el propio /v1/facets).
_SUBJECT_NAMES = (
    "Lenguaje y Comunicación",
    "Lengua y Literatura",
    "Matemática",
    "Ciencias Naturales",
    "Historia, Geografía y Ciencias Sociales",
    "Inglés",
    "Música",
    "Artes Visuales",
    "Educación Física y Salud",
    "Tecnología",
    "Orientación",
    "Filosofía",
    "Educación ciudadana",
    "Comunicación integral",
)

# Abreviaturas y equivalencias de aula chilena.
_SUBJECT_ALIASES: dict[str, tuple[str, ...]] = {
    "lenguaje": ("Lenguaje y Comunicación", "Lengua y Literatura"),
    "lenguaje y comunicacion": ("Lenguaje y Comunicación", "Lengua y Literatura"),
    "lengua y literatura": ("Lengua y Literatura", "Lenguaje y Comunicación"),
    "historia": ("Historia, Geografía y Ciencias Sociales",),
    "historia, geografia y ciencias sociales": ("Historia, Geografía y Ciencias Sociales",),
    "ciencias": ("Ciencias Naturales",),
    "ciencias naturales": ("Ciencias Naturales",),
    "matematica": ("Matemática",),
    "matematicas": ("Matemática",),
    "educacion fisica": ("Educación Física y Salud",),
    "educacion fisica y salud": ("Educación Física y Salud",),
    "artes": ("Artes Visuales",),
    "ingles": ("Inglés",),
    "musica": ("Música",),
    "filosofia": ("Filosofía",),
    "tecnologia": ("Tecnología",),
    "orientacion": ("Orientación",),
}


def grade_filter(curso: str) -> str:
    """Curso del encargo → valor exacto del filtro `grade` del banco ("" si no calza)."""
    text = _fold(curso)
    if not text:
        return ""
    for prefix, label in _NIVELES_ESPECIALES.items():
        if text.startswith(prefix):
            return label
    match = _CURSO.match(text)
    if not match:
        return ""
    number, level, suffix = match.group(1), match.group(2).lower(), (match.group(3) or "")
    label = _LEVELS[level]
    variants = [f"{number}° {label}", f"{number}º {label}", f"{number}º {label.lower()}"]
    if suffix:
        variants.append(f"{number}° {label} {suffix.upper()}")
    return ",".join(variants)


def subject_filter(asignatura: str) -> str:
    """Asignatura del encargo → valor exacto del filtro `subject` ("" si no calza)."""
    key = _fold(asignatura)
    if not key:
        return ""
    if key in _SUBJECT_ALIASES:
        return ",".join(_SUBJECT_ALIASES[key])
    for name in _SUBJECT_NAMES:
        if key == _fold(name):
            return name
    return ""


def banco_oa_code(value: str) -> str:
    """Devuelve el código si ya está en formato del banco; "" si es un id de tero."""
    text = " ".join(str(value or "").split())
    return text.upper() if _OA_CODE.match(text) else ""


def _urllib_get(url: str, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
    """Transporte real: GET con la clave en el header. Errores HTTP se devuelven."""
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return int(getattr(response, "status", 200)), response.read()
    except urllib.error.HTTPError as exc:  # 4xx/5xx: cuerpo legible, sin excepción
        return int(exc.code), exc.read()


class BegoniaClient:
    """GET contra el banco. Solo lectura; nunca lanza excepciones al agente."""

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
        *,
        timeout: float = DEFAULT_TIMEOUT,
        transport: Transport | None = None,
        snapshot_ttl: float = SNAPSHOT_TTL,
    ) -> None:
        self.base_url = str(base_url or "").strip().rstrip("/")
        self.api_key = str(api_key or "").strip()
        self.timeout = float(timeout or DEFAULT_TIMEOUT)
        self._transport: Transport = transport or _urllib_get
        self._snapshot = ""
        self._snapshot_at = 0.0
        self._snapshot_ttl = float(snapshot_ttl)
        self._clock = time.monotonic

    # ------------------------------------------------------------------ fábrica

    @classmethod
    def from_settings(cls, settings: Any, *, transport: Transport | None = None) -> BegoniaClient:
        """Construye el cliente desde `Settings`. Sin URL o sin clave queda inactivo."""
        return cls(
            base_url=str(getattr(settings, "begonia_url", "") or ""),
            api_key=resolve_api_key(
                str(getattr(settings, "begonia_api_key", "") or ""),
                str(getattr(settings, "begonia_key_file", "") or ""),
            ),
            timeout=float(getattr(settings, "begonia_timeout", DEFAULT_TIMEOUT) or DEFAULT_TIMEOUT),
            transport=transport,
            snapshot_ttl=float(getattr(settings, "begonia_snapshot_ttl", SNAPSHOT_TTL)),
        )

    # ------------------------------------------------------------------- estado

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def available(self) -> bool:
        """True si está configurado y el banco responde (una consulta por turno)."""
        return bool(self.configured and self.snapshot_id())

    def snapshot_id(self, *, force: bool = False) -> str:
        """Versión del banco con la que se trabajó ("" si no se pudo saber).

        Se cachea: cualquier respuesta del banco ya trae `snapshot_id`, así que
        basta una consulta por turno. `force` vuelve a preguntar con `/v1/summary`.
        """
        if not self.configured:
            return ""
        fresh = bool(self._snapshot) and (self._clock() - self._snapshot_at) < self._snapshot_ttl
        if fresh and not force:
            return self._snapshot
        self.summary()
        return self._snapshot

    def reset(self) -> None:
        """Olvida el snapshot cacheado (el host lo llama al abrir cada turno)."""
        self._snapshot = ""
        self._snapshot_at = 0.0

    # ----------------------------------------------------------------- endpoints

    def summary(self) -> Reply:
        reply = self._request("/v1/summary")
        return reply

    def search(
        self,
        query: str = "",
        *,
        type: str = "",
        subject: str = "",
        grade: str = "",
        material_type: str = "",
        oa: str = "",
        limit: int = 8,
        offset: int = 0,
        sort: str = "",
    ) -> Reply:
        params: dict[str, Any] = {
            "q": query,
            "type": type,
            "subject": subject,
            "grade": grade,
            "material_type": material_type,
            "oa": oa,
            "limit": limit,
            "offset": offset,
            "sort": sort,
        }
        return self._request("/v1/search", params)

    def item(self, item_id: str, *, text: bool = False, max_chars: int = 6000) -> Reply:
        ident = str(item_id or "").strip()
        if not ident:
            return Reply(
                ok=False,
                disponible=self.configured,
                code="banco_item_sin_id",
                error="Falta el id del ítem del banco.",
            )
        params: dict[str, Any] = {}
        if text:
            params["text"] = 1
            params["max_chars"] = max_chars
        return self._request(f"/v1/items/{urllib.parse.quote(ident, safe='')}", params)

    def guidance(
        self,
        oa: str | None = None,
        q: str | None = None,
        *,
        limit: int = 6,
        offset: int = 0,
    ) -> Reply:
        params: dict[str, Any] = {"oa": oa or "", "q": q or "", "limit": limit, "offset": offset}
        return self._request("/v1/guidance", params)

    # -------------------------------------------------------------------- interna

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Reply:
        if not self.configured:
            return no_configurado()
        url = self._url(path, params or {})
        try:
            status, body = self._transport(
                url,
                {"X-Begonia-API-Key": self.api_key, "Accept": "application/json"},
                self.timeout,
            )
        except Exception as exc:  # noqa: BLE001 — red caída: el turno sigue
            return Reply(
                ok=False,
                disponible=True,
                code="banco_sin_conexion",
                error=(
                    f"No pude alcanzar el banco pedagógico ({type(exc).__name__}: {exc}). "
                    "Revisa que el servicio local esté arriba."
                ),
            )
        if status == 401:
            return Reply(
                ok=False,
                disponible=True,
                code="banco_no_autorizado",
                error="El banco respondió 401: la clave no es válida o no llegó.",
            )
        if status == 404:
            return Reply(
                ok=False,
                disponible=True,
                code="banco_no_encontrado",
                error="El banco no tiene ese recurso (404).",
            )
        if status >= 400:
            detail = _short(body, 160)
            return Reply(
                ok=False,
                disponible=True,
                code=f"banco_http_{status}",
                error=f"El banco respondió HTTP {status}. {detail}".strip(),
            )
        try:
            data = json.loads(body.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, ValueError):
            return Reply(
                ok=False,
                disponible=True,
                code="banco_respuesta_invalida",
                error="El banco respondió algo que no es JSON. No uses esa respuesta.",
            )
        if not isinstance(data, dict):
            return Reply(
                ok=False,
                disponible=True,
                code="banco_respuesta_invalida",
                error="El banco respondió un JSON con forma inesperada.",
            )
        snapshot = data.get("snapshot_id")
        if isinstance(snapshot, str) and snapshot.strip():
            self._snapshot = snapshot.strip()
            self._snapshot_at = self._clock()
        return Reply(ok=True, disponible=True, data=data)

    def _url(self, path: str, params: dict[str, Any]) -> str:
        clean = {key: value for key, value in params.items() if value not in ("", None)}
        query = urllib.parse.urlencode(clean)
        base = f"{self.base_url}{path}"
        return f"{base}?{query}" if query else base


def _short(value: bytes | str, limit: int) -> str:
    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
    text = " ".join(text.split())
    return text[:limit]
