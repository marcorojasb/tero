"""Rumbos (Planificar / Crear / Evaluar / Adaptar) → tipo de artefacto."""

from __future__ import annotations

import re
from enum import StrEnum

from tero.types import ArtifactType


class Rumbo(StrEnum):
    PLANIFICAR = "planificar"
    CREAR = "crear"
    EVALUAR = "evaluar"
    ADAPTAR = "adaptar"

    @property
    def default_tipo(self) -> ArtifactType:
        return {
            Rumbo.PLANIFICAR: ArtifactType.PLANIFICACION,
            Rumbo.CREAR: ArtifactType.GUIA,
            Rumbo.EVALUAR: ArtifactType.EVALUACION,
            Rumbo.ADAPTAR: ArtifactType.ACTIVIDAD,
        }[self]

    @classmethod
    def parse(cls, value: str | None) -> Rumbo | None:
        if not value:
            return None
        raw = value.strip().lower()
        aliases = {
            "1": cls.PLANIFICAR,
            "planificar": cls.PLANIFICAR,
            "plan": cls.PLANIFICAR,
            "planificación": cls.PLANIFICAR,
            "planificacion": cls.PLANIFICAR,
            "2": cls.CREAR,
            "crear": cls.CREAR,
            "create": cls.CREAR,
            "3": cls.EVALUAR,
            "evaluar": cls.EVALUAR,
            "eval": cls.EVALUAR,
            "4": cls.ADAPTAR,
            "adaptar": cls.ADAPTAR,
            "adapt": cls.ADAPTAR,
        }
        return aliases.get(raw)


# Require °/º or an explicit level word. Bare "45" in "45 min" must NOT become "45° básico".
_CURSO_RE = re.compile(
    r"\b(\d{1,2})\s*[°º]\s*(b[aá]sico|medio)?\b"
    r"|\b(\d{1,2})\s+(b[aá]sico|medio)\b"
    r"|\b(prekinder|k[ií]nder|1ro|2do|3ro|4to|5to|6to|7mo|8vo)\b",
    re.IGNORECASE,
)

# Digits glued to duration units are never a grade (belt-and-suspenders vs bare \d matches).
_DURATION_UNIT_RE = re.compile(
    r"\b\d{1,2}\s*(?:min|mins|minuto|minutos|hrs?|horas?)\b",
    re.IGNORECASE,
)

_ASIGNATURA_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("matem", "fracción", "fraccion", "númer", "numer", "álgebra", "algebra"), "Matemática"),
    (("lengua", "lectura", "cuento", "literat", "comprensi"), "Lenguaje y Comunicación"),
    (
        ("cienc", "biolog", "qu[ií]mic", "f[ií]sic", "ecosistem", "laboratorio"),
        "Ciencias Naturales",
    ),
    (("histori", "geograf", "civica", "cívica"), "Historia y Geografía"),
    (("ingl[eé]s", "english"), "Inglés"),
)

_TIPO_HINTS: tuple[tuple[tuple[str, ...], ArtifactType], ...] = (
    (("planific", "clase de", "secuencia"), ArtifactType.PLANIFICACION),
    (("gu[ií]a", "guia", "ficha", "taller"), ArtifactType.GUIA),
    (("evalua", "prueba", "[ií]tems", "control"), ArtifactType.EVALUACION),
    (("pauta", "r[uú]brica", "rubrica"), ArtifactType.PAUTA),
    (("actividad", "juego", "din[aá]mica"), ArtifactType.ACTIVIDAD),
)

_RUMBO_HINTS: tuple[tuple[tuple[str, ...], Rumbo], ...] = (
    (("planific", "plan de clase", "secuencia"), Rumbo.PLANIFICAR),
    (("crear", "gu[ií]a", "ficha", "material"), Rumbo.CREAR),
    (("evalua", "prueba", "pauta", "r[uú]brica"), Rumbo.EVALUAR),
    (("adapt", "diferenc", "ajustar", "nivelar"), Rumbo.ADAPTAR),
)


def infer_curso(text: str) -> str:
    blob = text or ""
    # Strip duration chips so "45 min" cannot feed a digit-only grade guess.
    blob = _DURATION_UNIT_RE.sub(" ", blob)
    match = _CURSO_RE.search(blob)
    if not match:
        return ""
    if match.group(1):
        n = int(match.group(1))
        if not 1 <= n <= 12:
            return ""
        level = (match.group(2) or "básico").lower().replace("basico", "básico")
        return f"{n}° {level}"
    if match.group(3):
        n = int(match.group(3))
        if not 1 <= n <= 12:
            return ""
        level = (match.group(4) or "básico").lower().replace("basico", "básico")
        return f"{n}° {level}"
    token = (match.group(5) or "").lower()
    mapping = {
        "prekinder": "prekínder",
        "kinder": "kínder",
        "kínder": "kínder",
        "1ro": "1° básico",
        "2do": "2° básico",
        "3ro": "3° básico",
        "4to": "4° básico",
        "5to": "5° básico",
        "6to": "6° básico",
        "7mo": "7° básico",
        "8vo": "8° básico",
    }
    return mapping.get(token, token)


def infer_asignatura(text: str) -> str:
    blob = (text or "").lower()
    for needles, label in _ASIGNATURA_HINTS:
        if any(re.search(n, blob) for n in needles):
            return label
    return ""


def infer_tema(text: str) -> str:
    """Heuristic topic line from free text (short, classroom tone)."""
    raw = " ".join((text or "").strip().split())
    if not raw:
        return ""
    # A greeting is not a lesson topic (e.g. "hola" must not become chip tema).
    if raw.lower().rstrip("!?.") in {"hola", "holi", "holis", "hi", "hello", "buenas", "gracias"}:
        return ""
    cleaned = re.sub(
        r"^(prepara|haz|crea|quiero|necesito|arma|diseña|diseña)\w*\s+",
        "",
        raw,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\b(una|un|la|el|de|del|para|sobre|con)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > 90:
        cleaned = cleaned[:87] + "…"
    return cleaned


def infer_tipo_from_text(text: str) -> ArtifactType | None:
    blob = (text or "").lower()
    for needles, tipo in _TIPO_HINTS:
        if any(re.search(n, blob) for n in needles):
            return tipo
    return None


def infer_rumbo(text: str) -> Rumbo | None:
    blob = (text or "").lower()
    for needles, rumbo in _RUMBO_HINTS:
        if any(re.search(n, blob) for n in needles):
            return rumbo
    return None


def tipo_for_rumbo(rumbo: Rumbo | None, text: str = "") -> ArtifactType:
    explicit = infer_tipo_from_text(text)
    if explicit:
        return explicit
    if rumbo:
        return rumbo.default_tipo
    return ArtifactType.PLANIFICACION


DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "matemática": ("fraccion", "fracción", "numero", "número", "matem", "algebra", "álgebra"),
    "lenguaje": ("cuento", "lectura", "lengua", "literat", "vocabulario", "poema", "noticia"),
    "ciencias": (
        "ciencia",
        "biolog",
        "quimic",
        "químic",
        "fisic",
        "físic",
        "ecosistem",
        "laboratorio",
        "naturalez",
        "fotosint",
    ),
    "historia": ("histori", "geograf", "civica", "cívica"),
}


def domain_of_text(text: str) -> str | None:
    blob = (text or "").lower()
    for domain, needles in DOMAIN_KEYWORDS.items():
        if any(n in blob for n in needles):
            return domain
    return None


def domain_mismatch(prompt: str, source_blob: str) -> str | None:
    """Warn when the encargo domain looks alien to the carpeta sources."""
    want = domain_of_text(prompt)
    have = domain_of_text(source_blob)
    if want and have and want != have:
        return (
            f"El encargo apunta a {want}, pero la carpeta parece de {have}. "
            "Las citas pueden ser irrelevantes; cambia de carpeta o revisa con cuidado."
        )
    return None
