"""Admisión de archivos: los datos personales y de salud no entran al modelo.

La Ley 21.719 (protección de datos personales), que entra en vigencia el 1 de
diciembre de 2026, prohíbe tratar datos de salud recolectados en el ámbito
educativo (art. 16 bis) y refuerza la protección de datos de niños, niñas y
adolescentes. El consentimiento no levanta una prohibición legal, así que tero
no indexa ni le pasa al modelo archivos que parecen notas, fichas, nóminas o
informes de salud: los deja exactamente donde están.

Postura conservadora: ante la duda se excluye, y se avisa una sola vez sin
bloquear nada. `TERO_DATOS_SENSIBLES=incluir` lo desactiva; es decisión de la
persona, no del modelo.

Este módulo no escribe, no mueve y no borra archivos: solo decide y explica.
"""

from __future__ import annotations

import os
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ENV_FLAG = "TERO_DATOS_SENSIBLES"
MODE_EXCLUDE = "excluir"
MODE_INCLUDE = "incluir"
WARNING_CODE = "dato_sensible_excluido"
MOTIVO_LEGAL = "los datos personales o de salud de tus estudiantes (Ley 21.719)"

BLOCKED_MESSAGE = (
    "Esa fuente queda fuera: protección de datos personales o de salud. "
    "tero no la lee ni se la pasa al modelo."
)
MOTIVO_NOMBRE = "el nombre del archivo o de su carpeta sugiere notas, fichas o informes"
MOTIVO_RUT = "el contenido trae RUT con formato"
MOTIVO_NOMINA = "el contenido parece una nómina de estudiantes con nombres y notas"

# Tope de lectura para el análisis de contenido: no hace falta más para decidir.
MAX_ESCANEO = 400_000
MAX_LINEAS_CABECERA = 30

# Palabras completas del nombre o la ruta (sensibles a tildes y separadores).
_TOKENS = frozenset(
    {
        "calificaciones",
        "fudei",
        "paci",
        "salud",
        "medico",
        "medica",
        "medicos",
        "medicas",
        "alergia",
        "alergias",
        "nomina",
        "nominas",
        "asistencia",
        "inasistencia",
        "conducta",
        "conductas",
        "rut",
        "anamnesis",
        "tamizaje",
        "apoderado",
        "apoderada",
        "apoderados",
        "apoderadas",
    }
)

# Prefijos: cubren variantes sin listar cada forma.
_PREFIJOS = (
    "psicopedagog",
    "diagnostic",
    "calificacion",
    "vulnerab",
    "vacun",
)

# Frases (ya normalizadas: minúsculas, sin tildes, separadores como espacio).
_FRASES = (
    "boletin de notas",
    "boletin notas",
    "informe de notas",
    "acta de notas",
    "acta de calificaciones",
    "informe psicopedagogico",
    "informe psicopedagogica",
    "informe psicologico",
    "informe psicologica",
    "informe social",
    "informe medico",
    "informe de salud",
    "informe salud",
    "ficha estudiante",
    "ficha estudiantes",
    "ficha alumno",
    "ficha alumnos",
    "ficha personal",
    "ficha social",
    "ficha medica",
    "ficha clinica",
    "lista curso",
    "lista del curso",
    "lista estudiantes",
    "lista alumnos",
    "lista de estudiantes",
    "lista de alumnos",
    "entrevista apoderado",
    "entrevista apoderados",
    "entrevista apoderada",
    "entrevista apoderadas",
    "entrevista familia",
    "entrevista familias",
    "datos personales",
    "datos estudiantes",
    "datos alumnos",
    "datos del estudiante",
    "registro de notas",
    "registro de estudiantes",
    "libro de notas",
    "planilla de notas",
    "hoja de notas",
    "tabla de notas",
    "promedios curso",
    "certificado medico",
    "licencia medica",
    "consentimiento informado",
    "grupo sanguineo",
    "peso y talla",
    "peso talla",
    "curriculum vitae",
)

# El nombre del archivo, solo, es una nómina.
_TALLOS_NOMINA = frozenset(
    {
        "estudiantes",
        "estudiante",
        "alumnos",
        "alumnas",
        "alumno",
        "alumna",
        "apoderados",
        "apoderadas",
    }
)

# RUT chileno con formato: 12.345.678-9 o 12345678-9.
_RUT = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b")

_SEPARADOR = re.compile(r"[,;\t|]")
_FIN_ORACION = re.compile(r"[.!?¿¡]")
_MARCA_LISTA = re.compile(r"^[-*•#>]")

_COLUMNAS_NOMBRE = frozenset(
    {
        "nombre",
        "nombres",
        "apellido",
        "apellidos",
        "alumno",
        "alumna",
        "alumnos",
        "alumnas",
        "estudiante",
        "estudiantes",
    }
)
_COLUMNAS_NOTA = frozenset(
    {"nota", "notas", "calificacion", "calificaciones", "promedio", "promedios"}
)
_COLUMNAS_RUT = frozenset({"rut", "run"})


@dataclass(frozen=True)
class ExcludedSource:
    """Archivo que queda fuera del índice y del modelo. Nunca se modifica."""

    path: str
    name: str
    motivo: str

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "name": self.name, "motivo": self.motivo}


def mode_from_env(raw: str | None = None) -> str:
    """`incluir` solo si la persona lo pidió explícito; cualquier otra cosa excluye."""
    value = (raw if raw is not None else os.environ.get(ENV_FLAG, "")).strip().casefold()
    if value in {"incluir", "incluye", "include", "1", "true", "yes", "si", "sí"}:
        return MODE_INCLUDE
    return MODE_EXCLUDE


def is_excluding(mode: str) -> bool:
    return mode != MODE_INCLUDE


def slug(text: str) -> str:
    """Minúsculas, sin tildes y con separadores (_ - . /) como espacio simple."""
    plano = unicodedata.normalize("NFKD", text.casefold())
    sin_tildes = "".join(ch for ch in plano if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes).strip()


def motivo_por_nombre(relative: str) -> str | None:
    """Motivo si el nombre o la ruta sugieren datos personales o de salud."""
    path_obj = Path(relative)
    stem_slug = slug(path_obj.stem)
    # Planillas de notas en formato tabular (.csv, .xlsx, .tsv)
    if stem_slug in {"notas", "calificaciones", "promedios"} and path_obj.suffix.lower() in {
        ".csv",
        ".tsv",
        ".xlsx",
        ".xls",
    }:
        return MOTIVO_NOMBRE
    # Diagnóstico o informe PIE/NEE
    if any(
        combo in relative.lower()
        for combo in (
            "diagnostico_pie",
            "diagnostico-pie",
            "informe_pie",
            "informe-pie",
            "alumno_pie",
            "alumno-pie",
        )
    ):
        return MOTIVO_NOMBRE
    # Carpeta notas/ o frases con notas de evaluacion
    if "/notas/" in relative.lower() or "\\notas\\" in relative.lower():
        return MOTIVO_NOMBRE
    normalized = slug(relative)
    tokens = set(normalized.split())
    if tokens & _TOKENS:
        return MOTIVO_NOMBRE
    if any(token.startswith(_PREFIJOS) for token in tokens):
        return MOTIVO_NOMBRE
    if any(frase in normalized for frase in _FRASES):
        return MOTIVO_NOMBRE
    if slug(Path(relative).stem) in _TALLOS_NOMINA:
        return MOTIVO_NOMBRE
    return None


def motivo_por_contenido(text: str) -> str | None:
    """Motivo si el texto trae identificadores personales o una nómina."""
    if not text:
        return None
    muestra = text[:MAX_ESCANEO]
    if _RUT.search(muestra):
        return MOTIVO_RUT
    if _nomina_en_cabecera(muestra):
        return MOTIVO_NOMINA
    return None


def _nomina_en_cabecera(text: str) -> bool:
    """Encabezado de planilla con nombres y notas (o nombres y RUT).

    Deliberadamente estrecho: líneas cortas, separadas en columnas, sin puntuación
    de oración y sin marca de lista. Así una oración de un cuento no se confunde
    con una planilla de notas.
    """
    for line in text.splitlines()[:MAX_LINEAS_CABECERA]:
        stripped = line.strip()
        if not stripped or len(stripped) > 200:
            continue
        if _FIN_ORACION.search(stripped) or _MARCA_LISTA.match(stripped):
            continue
        columnas = [col for col in _SEPARADOR.split(stripped) if col.strip()]
        if len(columnas) < 2:
            continue
        tokens = [slug(col).split() for col in columnas]
        if sum(len(item) for item in tokens) > 20:
            continue
        nombre = any(item and item[0] in _COLUMNAS_NOMBRE and len(item) <= 3 for item in tokens)
        nota = any(item and item[0] in _COLUMNAS_NOTA and len(item) <= 2 for item in tokens)
        rut = any(item and item[0] in _COLUMNAS_RUT and len(item) <= 2 for item in tokens)
        if nombre and (nota or rut):
            return True
    return False


def aviso(excluidos: Sequence[ExcludedSource]) -> str:
    """Un solo aviso honesto: cuántos quedaron fuera, por qué y qué no se tocó."""
    total = len(excluidos)
    if total <= 0:
        return ""
    plural = "archivo" if total == 1 else "archivos"
    nombres = ", ".join(item.name for item in excluidos[:3])
    if total > 3:
        nombres += f" y {total - 3} más"
    motivos = " y ".join(dict.fromkeys(item.motivo for item in excluidos))
    return (
        f"Dejé {total} {plural} fuera de lo que tero lee y le pasa al modelo "
        f"({nombres}), para cuidar {MOTIVO_LEGAL}. Motivo: {motivos}. "
        "Los originales siguen intactos en tu carpeta: tero no los borra ni los cambia. "
        f"Si los necesitas igual, es tu decisión: {ENV_FLAG}=incluir."
    )


def aviso_para_modelo(total: int) -> str:
    """Aviso agregado y sin nombres: el modelo no necesita saber cuáles son."""
    if total <= 0:
        return ""
    plural = "archivo" if total == 1 else "archivos"
    return (
        f"El host dejó {total} {plural} de la carpeta fuera de esta lista por "
        "protección de datos personales o de salud. No están disponibles: no los "
        "nombres ni los cites. Si la carpeta parece vacía, dilo con este dato."
    )


def resumen(excluidos: Sequence[ExcludedSource], mode: str) -> dict[str, Any]:
    """Payload para hello_ok y eventos del host."""
    return {
        "modo": mode,
        "excluidos": len(excluidos),
        "motivo": MOTIVO_LEGAL,
        "aviso": aviso_para_modelo(len(excluidos)),
    }
