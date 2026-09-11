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
    for texto in ("no sé", "no se", "no entiendo", "no cacho", "no estoy seguro"):
        resultado = classify_approval(texto)
        assert resultado.kind == "preguntar", texto
        assert resultado.kind != "descartar", texto


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
    textos = [*APROBAR, *DESCARTAR, *CAMBIAR, *PREGUNTAR, *AMBIGUO]
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
