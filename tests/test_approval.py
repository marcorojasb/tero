"""Tests de la clasificación de aprobaciones en lenguaje natural. Sin red."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tero.approval import Approval, classify_approval

APROBAR = [
    "sí",
    "sí, dale",
    "s",
    "ok",
    "dale",
    "listo",
    "perfecto, gracias",
    "hazlo así",
    "está bien",
    "si",  # sin tilde
    "Sí.",
    "¡Dale!",
    "okay",
    "ya",
    "vale",
    "bueno",
    "correcto",
    "de acuerdo",
    "así nomás",
    "me gusta",
    "escríbelo",
    "guárdalo",
    "aprobado",
    "apruebo",
]

DESCARTAR = [
    "no",
    "n",
    "no gracias",
    "déjalo",
    "bórralo",
    "no me sirve",
    "No.",
    "¡No!",
    "nada",
    "descarta",
    "anúlalo",
    "olvídalo",
    "no sirve",
    "está mal",
]

CAMBIAR = [
    "cambia el cierre",
    "mejor hazlo para 2° básico",
    "agrega un ítem de alternativas",
    "quita la sección de materiales",
    "no, mejor cambia el título",
    "dale, pero cambia el título",
    "modifica el objetivo",
    "ajusta la duración a 90 minutos",
    "corrige las instrucciones",
    "arregla el título",
    "añade un ejemplo",
    "reemplaza el OA 4 por el OA 6",
    "elimina la lista de materiales",
    "saca la última pregunta",
    "simplifica las instrucciones",
    "acorta la actividad",
    "hazlo más corto",
    "hazlo para 2° básico",
    "adapta esto para NEE",
    "en vez de eso, usa el OA 2",
    "cámbiale el título",
]

PREGUNTAR = [
    "¿cuánto dura?",
    "¿puedes explicarme?",
    "¿por qué ese OA?",
    "¿qué evalúa esa actividad?",
    "cuanto dura",  # interrogativo sin signo de cierre
    "no sé",
    "no se",
    "no entiendo",
    "no cacho",
    "no estoy seguro",
    "no estoy segura",
]

AMBIGUO = ["", "   ", "\n", "hola", "jaja", "mmm", "buenas", "🎉", "..."]

# Negación pospuesta: el "no" no está al inicio, pero descarta igual.
DESCARTAR_POSPUESTO = [
    "ya, no gracias",
    "ok, no gracias",
    "bueno, no",
    "perfecto, no",
    "listo, no",
    "sí, no",
    "dale, no",
    "está bien, no",
    "vale, no",
    "correcto, no",
    "muy bien, no",
    "hazlo así, no",
    "escríbelo, no",
    "de acuerdo, no",
    "me gusta, no",
    "ok, no.",
]

# Modismo chileno de aceptación: "no más" / "nomás" no es una negación.
APROBAR_IDIOMA = [
    "hazlo no más",
    "dale no más",
    "así no más",
    "hazlo nomás",
    "ya no más",
]

# Consulta con algo después del "?": el signo manda en cualquier posición.
CONSULTAS_CON_SUFIJO = [
    "¿ok? 👍",
    "¿está bien? 🙂",
    "¿de acuerdo? 🤝",
    "¿ok?...",
    "¿está bien? gracias",
    "está bien? 🙂",
]

# Negadores que no son el token "no".
NEGADORES_ALTERNATIVOS = [
    "bueno, de ninguna manera",
    "ya, ni ahí",
    "bueno, ni ahí",
    "perfecto, ni cagando",
    "ya, tampoco",
    "perfecto, nunca",
    "ok, jamás",
]


@pytest.mark.parametrize("texto", APROBAR)
def test_aprobaciones(texto: str) -> None:
    resultado = classify_approval(texto)
    assert resultado.kind == "aprobar", texto
    assert resultado.raw == texto


@pytest.mark.parametrize("texto", DESCARTAR)
def test_descartes(texto: str) -> None:
    resultado = classify_approval(texto)
    assert resultado.kind == "descartar", texto
    assert resultado.raw == texto


@pytest.mark.parametrize("texto", CAMBIAR)
def test_cambios_llevan_la_peticion_completa(texto: str) -> None:
    resultado = classify_approval(texto)
    assert resultado.kind == "cambiar", texto
    assert resultado.note == texto.strip(), texto
    assert resultado.raw == texto


@pytest.mark.parametrize("texto", PREGUNTAR)
def test_preguntas(texto: str) -> None:
    resultado = classify_approval(texto)
    assert resultado.kind == "preguntar", texto
    assert resultado.raw == texto


@pytest.mark.parametrize("texto", AMBIGUO)
def test_ambiguos(texto: str) -> None:
    resultado = classify_approval(texto)
    assert resultado.kind == "ambiguo", texto
    assert resultado.raw == texto


@pytest.mark.parametrize("texto", DESCARTAR_POSPUESTO)
def test_negacion_pospuesta_descarta(texto: str) -> None:
    """El "no" descarta en cualquier posición, no solo al inicio."""
    resultado = classify_approval(texto)
    assert resultado.kind == "descartar", texto
    assert resultado.kind != "aprobar", texto


@pytest.mark.parametrize("texto", APROBAR_IDIOMA)
def test_idioma_no_mas_sigue_aprobando(texto: str) -> None:
    """ "no más" / "nomás" es aceptación, no negación."""
    resultado = classify_approval(texto)
    assert resultado.kind == "aprobar", texto
    assert resultado.note == "", texto


@pytest.mark.parametrize("texto", CONSULTAS_CON_SUFIJO)
def test_consulta_con_sufijo_no_aprueba(texto: str) -> None:
    """Un emoji o una palabra después del "?" no desactiva la consulta."""
    resultado = classify_approval(texto)
    assert resultado.kind == "preguntar", texto
    assert resultado.kind != "aprobar", texto


@pytest.mark.parametrize("texto", NEGADORES_ALTERNATIVOS)
def test_negadores_alternativos_descartan(texto: str) -> None:
    """ "tampoco", "nunca", "jamás", "ni ahí" y "de ninguna manera" descartan."""
    resultado = classify_approval(texto)
    assert resultado.kind == "descartar", texto
    assert resultado.kind != "aprobar", texto


def test_cualquier_interrogacion_nunca_aprueba() -> None:
    """Invariante: si el texto trae "?", no puede clasificarse como aprobar."""
    textos = [
        *CONSULTAS_CON_SUFIJO,
        "¿cuánto dura?",
        "¿puedes explicarme?",
        "¿por qué ese OA?",
        "¿ok?",
        "¿está bien?",
        "¿de acuerdo?",
        "¿me gusta?",
        "¿escríbelo?",
        "¿no?",
        "no sé, ¿qué me recomiendas?",
    ]
    for texto in textos:
        assert "?" in texto, texto
        assert classify_approval(texto).kind != "aprobar", texto


def test_como_no_es_aceptacion_chilena() -> None:
    """ "cómo no" aprueba; un reproche con "cómo no" no."""
    for texto in ("cómo no", "como no", "cómo no, dale", "cómo no po", "¡cómo no!"):
        assert classify_approval(texto).kind == "aprobar", texto
    assert classify_approval("cómo no me avisaste").kind != "aprobar"


def test_negacion_en_cualquier_posicion_nunca_aprueba() -> None:
    """Un "no" delimitado por palabras jamás puede terminar en aprobar."""
    textos = [
        *DESCARTAR,
        *DESCARTAR_POSPUESTO,
        "creo que no",
        "no lo escribas",
        "no lo guardes",
        "no me gusta",
        "¿no?",
        "no sé",  # duda: pregunta, tampoco aprueba
        "no entiendo",
        "no estoy seguro",
        "no más",  # modismo suelto, sin verbo: ambiguo
    ]
    for texto in textos:
        assert classify_approval(texto).kind != "aprobar", texto


def test_pregunta_con_marcador_firme_no_aprueba() -> None:
    """Una consulta nunca aprueba, ni con marcadores firmes."""
    assert classify_approval("¿de acuerdo?").kind == "preguntar"
    assert classify_approval("¿me gusta?").kind == "preguntar"
    assert classify_approval("¿escríbelo?").kind == "preguntar"
    for texto in ("¿de acuerdo?", "¿me gusta?", "¿escríbelo?", "¿lo guardas?"):
        assert classify_approval(texto).kind != "aprobar", texto


def test_ya_no_descarta_y_ya_no_mas_aprueba() -> None:
    """Decisión: "ya no" rechaza; "ya no más" es el modismo de aceptación."""
    assert classify_approval("ya no").kind == "descartar"
    assert classify_approval("ya no más").kind == "aprobar"


def test_cambio_gana_sobre_descarte() -> None:
    """Un "no" con petición de cambio es cambiar, no descartar."""
    resultado = classify_approval("no, mejor cambia el título")
    assert resultado.kind == "cambiar"
    assert resultado.kind != "descartar"
    assert "cambia el título" in resultado.note


def test_cambio_gana_sobre_aprobacion() -> None:
    """Un "dale" con petición de cambio es cambiar, no aprobar."""
    resultado = classify_approval("dale, pero cambia el título")
    assert resultado.kind == "cambiar"
    assert resultado.kind != "aprobar"


def test_cambio_gana_sobre_pregunta() -> None:
    """Una pregunta que propone un cambio es cambiar."""
    texto = "¿y si lo hacemos más corto?"
    resultado = classify_approval(texto)
    assert resultado.kind == "cambiar"
    assert resultado.note == texto


def test_pregunta_con_marcador_breve_no_aprueba() -> None:
    """ "¿está bien?" consulta; no es una aceptación."""
    assert classify_approval("¿está bien?").kind == "preguntar"
    assert classify_approval("¿ok?").kind == "preguntar"
    assert classify_approval("¿lo dejamos así?").kind != "aprobar"


def test_duda_no_es_descarte() -> None:
    """ "no sé" y "no entiendo" piden ayuda, no descartan la propuesta."""
    dudas = (
        "no sé",
        "no se",
        "no lo sé",
        "no entiendo",
        "no entendí",
        "no cacho",
        "no comprendo",
        "no me acuerdo",
        "no estoy seguro",
        "no estoy muy segura",
    )
    for texto in dudas:
        resultado = classify_approval(texto)
        assert resultado.kind == "preguntar", texto
        assert resultado.kind != "descartar", texto
        assert resultado.kind != "aprobar", texto


def test_hazlo_con_instruccion_es_cambio() -> None:
    assert classify_approval("hazlo más corto").kind == "cambiar"
    assert classify_approval("hazlo para 2° básico").kind == "cambiar"


def test_hazlo_solo_nunca_aprueba() -> None:
    """Sin instrucción nueva, "hazlo" no es aceptación explícita: ante duda, ambiguo."""
    assert classify_approval("hazlo").kind != "aprobar"


def test_raw_conserva_el_original() -> None:
    resultado = classify_approval("  ¡Dale!  ")
    assert resultado.raw == "  ¡Dale!  "
    assert resultado.kind == "aprobar"


def test_raw_conserva_el_original_al_cambiar() -> None:
    resultado = classify_approval("  mejor hazlo para 2° básico  ")
    assert resultado.raw == "  mejor hazlo para 2° básico  "
    assert resultado.note == "mejor hazlo para 2° básico"


def test_nota_de_aprobacion_es_el_comentario_extra() -> None:
    assert classify_approval("perfecto, gracias").note == "gracias"
    assert classify_approval("sí, dale").note == ""
    assert classify_approval("está bien").note == ""


@pytest.mark.parametrize(
    "texto",
    [
        "",
        "   ",
        "hola",
        "jaja",
        "mmm",
        "buenas",
        "🎉",
        "???",
        "no estoy seguro de nada",  # duda, no aceptación
        "hazlo",
        "tal vez",
        "a ver",
        "ni idea",
    ],
)
def test_textos_raros_jamas_aprueban(texto: str) -> None:
    """Regla de seguridad: el default nunca es aprobar."""
    assert classify_approval(texto).kind != "aprobar", texto


def test_es_pura_y_determinista() -> None:
    """Mismo texto, mismo resultado: sin estado global ni efectos."""
    textos = [
        *APROBAR,
        *APROBAR_IDIOMA,
        *DESCARTAR,
        *DESCARTAR_POSPUESTO,
        *NEGADORES_ALTERNATIVOS,
        *CAMBIAR,
        *PREGUNTAR,
        *CONSULTAS_CON_SUFIJO,
        *AMBIGUO,
    ]
    for texto in textos:
        primera = classify_approval(texto)
        segunda = classify_approval(texto)
        assert primera == segunda, texto
        assert primera.raw == texto, texto


def test_approval_es_inmutable_con_defaults() -> None:
    """El contrato tipado se mantiene: sin note ni raw, vacíos."""
    assert Approval(kind="aprobar") == Approval(kind="aprobar", note="", raw="")
    with pytest.raises(FrozenInstanceError):
        Approval(kind="aprobar").kind = "cambiar"  # type: ignore[misc]


def test_como_no_con_pregunta_no_aprueba() -> None:
    """La invariante del "?" no tiene excepciones, ni siquiera con "cómo no"."""
    for texto in (
        "cómo no, ¿y el OA?",
        "¡cómo no! ¿cuándo lo hacemos?",
        "cómo no, ¿ok?",
        "cómo no po, ¿te tinca?",
        "cómo no, ¿lo escribes?",
        "cómo no, ¿me avisas?",
        "cómo no. ¿quién?",
        "cómo no, ¿cuánto dura?",
        "¿cómo no si te lo pedí?",
        "¿cómo no, si te lo pedí?",
        "¿cómo no?",
    ):
        aprobacion = classify_approval(texto)
        assert aprobacion.kind != "aprobar", f"{texto!r} no puede aprobar: {aprobacion}"


def test_como_no_sin_pregunta_sigue_aprobando() -> None:
    """El modismo de aceptación no se pierde al cerrar la invariante."""
    for texto in (
        "cómo no",
        "como no",
        "cómo no, dale",
        "cómo no po",
        "¡cómo no!",
        "cómo no, gracias",
        "cómo no, obvio",
        "sí, cómo no",
    ):
        assert classify_approval(texto).kind == "aprobar", texto
