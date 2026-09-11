"""Clasificación de la respuesta de la persona a una propuesta de tero. Sin I/O.

La persona responde en lenguaje natural ("dale", "mejor para 2° básico", "no sé",
"¿cuánto dura?"). Esta función traduce esa respuesta a una decisión tipada, sin
tocar disco ni red y sin estado global.

Precedencia: cambiar → descartar → aprobar → preguntar → ambiguo. Cualquier marca
de cambio gana, aunque venga acompañada de un "sí" o de un "no".

Reglas de seguridad:

- La negación cuenta en cualquier posición, no solo al inicio: "ya, no gracias" es
  un descarte. La única excepción es el modismo de aceptación "no más" / "nomás".
- Una consulta nunca aprueba: "¿está bien?", "¿de acuerdo?" son preguntas.
- La categoría por defecto nunca es ``aprobar``. Si el texto no calza en ninguna
  regla, la respuesta es ``ambiguo`` y tero vuelve a preguntar.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

ApprovalKind = Literal["aprobar", "cambiar", "descartar", "preguntar", "ambiguo"]


@dataclass(frozen=True)
class Approval:
    """Decisión de la persona sobre una propuesta de tero."""

    kind: ApprovalKind
    note: str = ""
    raw: str = ""


# --- Comparación sin mayúsculas y sin tildes --------------------------------

_TRIM = "¡!¿?.,;:()[]{}«»\"'…-"
_APERTURA = re.compile(r"^[^0-9a-z]+")
_MAX_FRASE = 3  # largo máximo (en palabras) de los marcadores de aceptación


def _fold(text: str) -> str:
    """Minúsculas y sin tildes, solo para comparar; ``raw`` nunca se toca."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


# --- Patrones ---------------------------------------------------------------

# Cambio: verbos y marcadores de modificación.
_CHANGE = re.compile(
    r"\b(?:cambia\w*|modific\w*|ajust\w*|corrig\w*|correg\w*|arregl\w*|agreg\w*|anad\w*"
    r"|quit\w*|sac\w*|elimin\w*|reemplaz\w*|adapt\w*|simplific\w*|acort\w*|alarg\w*|mejor\w*"
    r"|pero)\b"
    # "hazlo" pide cambio solo con una instrucción nueva detrás: "hazlo más corto"
    # sí, "hazlo" o "hazlo así" no (el segundo es una forma de aceptar).
    r"|\bhazl[oa]\s+(?!(?:asi|tal cual|igual|nomas|no mas|ya|listo|ok|dale)\b)\S"
    r"|\ben vez\b"
    r"|\bmas\s+(?:cort|larg|simpl)\w*"
    r"|\bpara\s+\d{1,2}\s*°(?:\s*(?:basico|media|medio))?\b"
    r"|\bpara\s+\d{1,2}\s+(?:basico|media|medio)\b"
    r"|\bpara\s+(?:primero|segundo|tercero|cuarto|quinto|sexto|septimo|octavo)\s+"
    r"(?:basico|media|medio)\b"
)

# Dudas que en realidad piden ayuda: no son un descarte. Se evalúan antes que la
# negación, así que "no lo sé" o "no entendí" preguntan en vez de descartar.
_DOUBT = re.compile(
    r"\bno\s+(?:lo\s+|la\s+)?se\b"
    r"|\bno\s+ent(?:iend|end)\w*\b"
    r"|\bno\s+cach\w*\b"
    r"|\bno\s+comprend\w*\b"
    r"|\bno\s+me\s+acuerd\w*\b"
    r"|\bno\s+estoy\s+(?:muy\s+|tan\s+|del todo\s+)?segur[oa]\b"
)

# Descartar: negativa limpia, sin verbo de cambio. El "no" descarta en cualquier
# posición ("ya, no gracias"), salvo el modismo de aceptación "no más" / "nomás".
_DISCARD_HEAD = re.compile(r"^n\b")
_DISCARD = re.compile(
    r"\b(?:dejal[oa]|deja|borr\w*|anul\w*|olvid\w*|descart\w*|nada|esta\s+mal\w*)\b"
    r"|\bno\s+(?:me\s+)?sirv\w*\b"
    r"|\bno\b(?!\s*mas\b)"  # el plegado ya dejó "más" como "mas"
)

# Preguntar: signo de interrogación o arranque interrogativo.
_QUESTION_END = re.compile(r"\?\s*[!?…]*\s*$")
_QUESTION_HEAD = re.compile(
    r"^(?:que|como|por que|porque|cuando|donde|cual|cuales|cuanto|cuanta|cuantos|cuantas"
    r"|puedes|podrias|podemos|se puede|quien|tienes|hay)\b"
)

# Aprobar: aceptación explícita. Los marcadores breves ("ok", "está bien") solo
# valen al inicio; los firmes valen en cualquier posición. Ninguno aprueba dentro
# de una consulta.
_APPROVE_FIRM = re.compile(
    r"\b(?:me gusta|escribel[oa]|guardal[oa]|aprobad[oa]|apruebo|de acuerdo|asi nomas"
    r"|asi no mas|hazl[oa] (?:asi|tal cual|igual|nomas|no mas))\b"
)
_APPROVE_SHORT = re.compile(
    r"^(?:si|s|dale|ok|okay|ya|listo|perfecto|bueno|bien|muy bien|correcto|vale"
    r"|esta bien|esta bueno|asi esta bien)\b"
)
_APPROVE_PHRASES = frozenset(
    {
        "si",
        "s",
        "dale",
        "ok",
        "okay",
        "ya",
        "listo",
        "perfecto",
        "bueno",
        "bien",
        "muy bien",
        "correcto",
        "vale",
        "me gusta",
        "esta bien",
        "esta bueno",
        "asi esta bien",
        "escribelo",
        "escribela",
        "guardalo",
        "guardala",
        "aprobado",
        "aprobada",
        "apruebo",
        "de acuerdo",
        "asi nomas",
        "asi no mas",
        "hazlo asi",
        "hazla asi",
        "hazlo tal cual",
        "hazla tal cual",
        "hazlo igual",
        "hazla igual",
        "hazlo nomas",
        "hazla nomas",
        "hazlo no mas",
        "hazla no mas",
        "dale no mas",
        "ya no mas",
        "nomas",
        "no mas",
    }
)


def _approve_note(text: str) -> str:
    """Comentario que acompaña a la aceptación: "perfecto, gracias" → "gracias"."""
    tokens = text.split()
    keys = [_fold(token).strip(_TRIM) for token in tokens]
    consumed = 0
    while consumed < len(tokens):
        size = 0
        for width in range(min(_MAX_FRASE, len(tokens) - consumed), 0, -1):
            phrase = " ".join(key for key in keys[consumed : consumed + width] if key)
            if phrase in _APPROVE_PHRASES:
                size = width
                break
        if size == 0:
            break
        consumed += size
    return " ".join(tokens[consumed:]).strip()


def classify_approval(text: str) -> Approval:
    """Clasifica la respuesta de la persona a una propuesta de tero.

    ``raw`` conserva el texto original tal cual llegó. ``note`` lleva la petición
    completa cuando hay cambio y el comentario adicional cuando aprueba. Ante
    cualquier duda devuelve ``ambiguo``: el default nunca aprueba.
    """
    raw = text if isinstance(text, str) else ""
    folded = _fold(raw).strip()
    if not any(ch.isalnum() for ch in folded):
        # Vacío, solo espacios, solo signos o solo emojis.
        return Approval(kind="ambiguo", raw=raw)

    # 1. Cambio: gana sobre cualquier "sí" o "no" que lo acompañe.
    if _CHANGE.search(folded):
        return Approval(kind="cambiar", note=raw.strip(), raw=raw)

    # 2. "no sé" / "no entiendo" no descartan: la persona pide ayuda.
    if _DOUBT.search(folded):
        return Approval(kind="preguntar", raw=raw)

    head = _APERTURA.sub("", folded)

    # 3. Descartar: negativa sin cambio, en cualquier posición del texto.
    if _DISCARD_HEAD.match(head) or _DISCARD.search(folded):
        return Approval(kind="descartar", raw=raw)

    question = bool(_QUESTION_END.search(folded) or _QUESTION_HEAD.match(head))

    # 4. Aprobar. Una consulta nunca aprueba, ni con marcadores firmes:
    #    "¿está bien?" y "¿de acuerdo?" son preguntas, no aceptaciones.
    if not question and (_APPROVE_FIRM.search(folded) or _APPROVE_SHORT.match(head)):
        return Approval(kind="aprobar", note=_approve_note(raw.strip()), raw=raw)

    # 5. Preguntar y, por defecto, ambiguo.
    return Approval(kind="preguntar" if question else "ambiguo", raw=raw)
