#!/usr/bin/env python3
"""Render architecture.png + architecture.svg. Requires Pillow.

python docs/hackathon/render_architecture.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PNG = HERE / "architecture.png"
SVG = HERE / "architecture.svg"

FONDO = (7, 11, 12)
PANEL = (12, 18, 20)
ROW = (18, 26, 28)
CREMA = (244, 241, 222)
CIAN = (34, 211, 238)
MENTA = (134, 239, 172)
MUTED = (148, 168, 170)
LINE = (42, 62, 66)
AMBER = (251, 191, 36)
VIOLET = (196, 181, 253)
ORANGE = (251, 146, 60)

W, H = 1680, 820
INTER = Path("/usr/share/fonts/truetype/macos")
JB = Path("/usr/share/fonts/truetype/jetbrains-mono")

# Layout
PX, PY, PW, PH = 48, 120, 400, 300
TX, TY, TW, TH = 560, 120, 520, 300
AX, AY, AW, AH = 1192, 120, 440, 300
FX, FY, FW, FH = 560, 500, 520, 272


def fnt(name: str, size: int) -> ImageFont.FreeTypeFont:
    root = INTER if name.startswith("Inter") else JB
    return ImageFont.truetype(str(root / name), size)


def hex_rgb(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def card(draw: ImageDraw.ImageDraw, x, y, w, h, accent, title: str) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), 16, fill=PANEL, outline=LINE, width=2)
    draw.rectangle((x, y, x + 6, y + h), fill=accent)
    draw.text((x + 24, y + 18), title, font=fnt("Inter-SemiBold.ttf", 24), fill=CREMA)


def body(draw: ImageDraw.ImageDraw, x, y, lines: list[tuple[str, tuple[int, int, int]]]) -> None:
    yy = y
    font = fnt("Inter-Regular.ttf", 17)
    for text, color in lines:
        draw.text((x, yy), text, font=font, fill=color)
        yy += 28


def arrow_right(draw: ImageDraw.ImageDraw, x1: int, x2: int, y: int, color) -> None:
    draw.line((x1, y, x2 - 12, y), fill=color, width=3)
    draw.polygon([(x2, y), (x2 - 14, y - 7), (x2 - 14, y + 7)], fill=color)


def arrow_left(draw: ImageDraw.ImageDraw, x1: int, x2: int, y: int, color) -> None:
    draw.line((x1, y, x2 + 12, y), fill=color, width=3)
    draw.polygon([(x2, y), (x2 + 14, y - 7), (x2 + 14, y + 7)], fill=color)


def arrow_down(draw: ImageDraw.ImageDraw, x: int, y1: int, y2: int, color) -> None:
    draw.line((x, y1, x, y2 - 12), fill=color, width=3)
    draw.polygon([(x, y2), (x - 7, y2 - 14), (x + 7, y2 - 14)], fill=color)


def caption(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color) -> None:
    draw.text(xy, text, font=fnt("Inter-Medium.ttf", 13), fill=color)


def chips(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    items: list[tuple[str, tuple[int, int, int]]],
) -> None:
    font = fnt("Inter-SemiBold.ttf", 15)
    cx = x
    for text, bg in items:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0] + 24
        draw.rounded_rectangle((cx, y, cx + tw, y + 32), 8, fill=bg)
        draw.text((cx + 12, y + 6), text, font=font, fill=CREMA)
        cx += tw + 10


def folder_row(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    accent,
    left: str,
    right: str,
) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), 10, fill=ROW, outline=LINE, width=1)
    draw.rectangle((x, y, x + 5, y + h), fill=accent)
    draw.text((x + 16, y + 8), left, font=fnt("JetBrainsMono-Medium.ttf", 15), fill=CREMA)
    draw.text((x + 16, y + 32), right, font=fnt("Inter-Regular.ttf", 14), fill=MUTED)


def render_png() -> Image.Image:
    img = Image.new("RGB", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    draw.text((48, 28), "tero", font=fnt("Inter-Bold.ttf", 34), fill=CIAN)
    draw.text(
        (128, 36),
        "el agente prepara, el profesor decide",
        font=fnt("Inter-Regular.ttf", 20),
        fill=CREMA,
    )
    draw.text(
        (48, 74),
        "Una vuelta: el profesor pide, tero lee la carpeta, Nova Lite redacta, el profesor dice s / n / b / c.",
        font=fnt("Inter-Regular.ttf", 15),
        fill=MUTED,
    )

    # People -> agent -> model
    arrow_right(draw, PX + PW, TX, PY + 88, CIAN)
    caption(draw, (PX + PW + 18, PY + 66), "encargo", MUTED)
    arrow_left(draw, TX, PX + PW, PY + 148, MENTA)
    caption(draw, (PX + PW + 18, PY + 156), "borrador", MENTA)
    arrow_right(draw, TX + TW, AX, AY + 88, ORANGE)
    caption(draw, (TX + TW + 14, AY + 66), "pide texto", MUTED)
    arrow_left(draw, AX, TX + TW, AY + 148, MENTA)
    caption(draw, (TX + TW + 10, AY + 156), "redacci\u00f3n", MENTA)

    card(draw, PX, PY, PW, PH, CIAN, "Profesor")
    body(
        draw,
        PX + 24,
        PY + 62,
        [
            ("En la terminal", CREMA),
            ("pide un encargo", MUTED),
            ("ve plan, borrador y avisos", MUTED),
        ],
    )
    chips(
        draw,
        PX + 24,
        PY + 168,
        [
            ("s  s\u00ed", (20, 83, 45)),
            ("n  no", (88, 28, 28)),
        ],
    )
    chips(
        draw,
        PX + 24,
        PY + 212,
        [
            ("b  borrador", (66, 48, 8)),
            ("c  corregir", (30, 58, 90)),
        ],
    )
    draw.text(
        (PX + 24, PY + 258),
        "n tira el papel. c pide otra pasada.",
        font=fnt("Inter-Regular.ttf", 14),
        fill=MUTED,
    )

    card(draw, TX, TY, TW, TH, MENTA, "tero  (Strands)")
    body(
        draw,
        TX + 24,
        TY + 62,
        [
            ("Lee la carpeta. Nunca la pisa.", CREMA),
            ("Arma un plan y un borrador.", MUTED),
            ("El borrador queda en memoria", MUTED),
            ("hasta s o b. No decide.", MENTA),
        ],
    )

    card(draw, AX, AY, AW, AH, ORANGE, "Amazon Bedrock")
    body(
        draw,
        AX + 24,
        AY + 62,
        [
            ("Nova Lite · us-east-1", CREMA),
            ("solo infiere texto", MUTED),
            ("la carpeta no sube a AWS", MUTED),
            ("sin clave: tero-offline", MUTED),
        ],
    )

    # Agent reads the folder
    arrow_down(draw, TX + TW // 2, TY + TH, FY, AMBER)
    caption(draw, (TX + TW // 2 + 12, TY + TH + 18), "lee fuentes/", AMBER)

    # Teacher write path: down from profesor, then into the folder
    write_y = FY + 184
    draw.line((PX + PW // 2, PY + PH, PX + PW // 2, write_y), fill=MENTA, width=3)
    draw.line((PX + PW // 2, write_y, FX - 12, write_y), fill=MENTA, width=3)
    draw.polygon(
        [(FX, write_y), (FX - 14, write_y - 7), (FX - 14, write_y + 7)],
        fill=MENTA,
    )
    caption(draw, ((PX + PW // 2 + FX) // 2 - 42, write_y - 38), "s / b escribe", MENTA)

    card(draw, FX, FY, FW, FH, VIOLET, "Carpeta de trabajo")
    folder_row(
        draw,
        FX + 20,
        FY + 58,
        FW - 40,
        58,
        AMBER,
        "fuentes/",
        "originales. tero lee, nadie las pisa",
    )
    folder_row(
        draw,
        FX + 20,
        FY + 126,
        FW - 40,
        58,
        ORANGE,
        "borradores/",
        "si el profesor aprieta b",
    )
    folder_row(
        draw,
        FX + 20,
        FY + 194,
        FW - 40,
        58,
        MENTA,
        "derivados/",
        "si el profesor aprieta s  (para la clase)",
    )

    return img


def render_svg() -> str:
    def rgb(c: tuple[int, int, int]) -> str:
        return hex_rgb(c)

    fondo, panel, row = rgb(FONDO), rgb(PANEL), rgb(ROW)
    crema, cian, menta = rgb(CREMA), rgb(CIAN), rgb(MENTA)
    muted, line, amber = rgb(MUTED), rgb(LINE), rgb(AMBER)
    violet, orange = rgb(VIOLET), rgb(ORANGE)
    s_bg, n_bg, b_bg, c_bg = "#14532D", "#581C1C", "#423008", "#1E3A5A"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="tero architecture">
  <title>tero - el agente prepara, el profesor decide</title>
  <rect width="{W}" height="{H}" fill="{fondo}"/>
  <text x="48" y="54" fill="{cian}" font-family="Inter, sans-serif" font-size="34" font-weight="700">tero</text>
  <text x="128" y="52" fill="{crema}" font-family="Inter, sans-serif" font-size="20">el agente prepara, el profesor decide</text>
  <text x="48" y="88" fill="{muted}" font-family="Inter, sans-serif" font-size="15">Una vuelta: el profesor pide, tero lee la carpeta, Nova Lite redacta, el profesor dice s / n / b / c.</text>

  <defs>
    <marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{cian}"/></marker>
    <marker id="b" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{menta}"/></marker>
    <marker id="c" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{orange}"/></marker>
    <marker id="d" markerWidth="10" markerHeight="10" refX="5" refY="8" orient="auto"><path d="M0,0 L5,10 L10,0 Z" fill="{amber}"/></marker>
  </defs>

  <line x1="{PX + PW}" y1="{PY + 88}" x2="{TX - 8}" y2="{PY + 88}" stroke="{cian}" stroke-width="3" marker-end="url(#a)"/>
  <text x="{PX + PW + 18}" y="{PY + 78}" fill="{muted}" font-family="Inter, sans-serif" font-size="13">encargo</text>
  <line x1="{TX}" y1="{PY + 148}" x2="{PX + PW + 8}" y2="{PY + 148}" stroke="{menta}" stroke-width="3" marker-end="url(#b)"/>
  <text x="{PX + PW + 18}" y="{PY + 172}" fill="{menta}" font-family="Inter, sans-serif" font-size="13">borrador</text>
  <line x1="{TX + TW}" y1="{AY + 88}" x2="{AX - 8}" y2="{AY + 88}" stroke="{orange}" stroke-width="3" marker-end="url(#c)"/>
  <text x="{TX + TW + 18}" y="{AY + 78}" fill="{muted}" font-family="Inter, sans-serif" font-size="13">pide texto</text>
  <line x1="{AX}" y1="{AY + 148}" x2="{TX + TW + 8}" y2="{AY + 148}" stroke="{menta}" stroke-width="3" marker-end="url(#b)"/>
  <text x="{TX + TW + 10}" y="{AY + 172}" fill="{menta}" font-family="Inter, sans-serif" font-size="13">redacci&#243;n</text>

  <rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="16" fill="{panel}" stroke="{line}"/>
  <rect x="{PX}" y="{PY}" width="6" height="{PH}" fill="{cian}"/>
  <text x="{PX + 24}" y="{PY + 42}" fill="{crema}" font-family="Inter, sans-serif" font-size="24" font-weight="600">Profesor</text>
  <text x="{PX + 24}" y="{PY + 78}" fill="{crema}" font-family="Inter, sans-serif" font-size="17">En la terminal</text>
  <text x="{PX + 24}" y="{PY + 106}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">pide un encargo</text>
  <text x="{PX + 24}" y="{PY + 134}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">ve plan, borrador y avisos</text>
  <rect x="{PX + 24}" y="{PY + 168}" width="88" height="32" rx="8" fill="{s_bg}"/><text x="{PX + 36}" y="{PY + 190}" fill="{crema}" font-family="Inter, sans-serif" font-size="15" font-weight="600">s  s&#237;</text>
  <rect x="{PX + 122}" y="{PY + 168}" width="88" height="32" rx="8" fill="{n_bg}"/><text x="{PX + 134}" y="{PY + 190}" fill="{crema}" font-family="Inter, sans-serif" font-size="15" font-weight="600">n  no</text>
  <rect x="{PX + 24}" y="{PY + 212}" width="140" height="32" rx="8" fill="{b_bg}"/><text x="{PX + 36}" y="{PY + 234}" fill="{crema}" font-family="Inter, sans-serif" font-size="15" font-weight="600">b  borrador</text>
  <rect x="{PX + 174}" y="{PY + 212}" width="140" height="32" rx="8" fill="{c_bg}"/><text x="{PX + 186}" y="{PY + 234}" fill="{crema}" font-family="Inter, sans-serif" font-size="15" font-weight="600">c  corregir</text>
  <text x="{PX + 24}" y="{PY + 274}" fill="{muted}" font-family="Inter, sans-serif" font-size="14">n tira el papel. c pide otra pasada.</text>

  <rect x="{TX}" y="{TY}" width="{TW}" height="{TH}" rx="16" fill="{panel}" stroke="{line}"/>
  <rect x="{TX}" y="{TY}" width="6" height="{TH}" fill="{menta}"/>
  <text x="{TX + 24}" y="{TY + 42}" fill="{crema}" font-family="Inter, sans-serif" font-size="24" font-weight="600">tero  (Strands)</text>
  <text x="{TX + 24}" y="{TY + 78}" fill="{crema}" font-family="Inter, sans-serif" font-size="17">Lee la carpeta. Nunca la pisa.</text>
  <text x="{TX + 24}" y="{TY + 106}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">Arma un plan y un borrador.</text>
  <text x="{TX + 24}" y="{TY + 134}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">El borrador queda en memoria</text>
  <text x="{TX + 24}" y="{TY + 162}" fill="{menta}" font-family="Inter, sans-serif" font-size="17">hasta s o b. No decide.</text>

  <rect x="{AX}" y="{AY}" width="{AW}" height="{AH}" rx="16" fill="{panel}" stroke="{line}"/>
  <rect x="{AX}" y="{AY}" width="6" height="{AH}" fill="{orange}"/>
  <text x="{AX + 24}" y="{AY + 42}" fill="{crema}" font-family="Inter, sans-serif" font-size="24" font-weight="600">Amazon Bedrock</text>
  <text x="{AX + 24}" y="{AY + 78}" fill="{crema}" font-family="Inter, sans-serif" font-size="17">Nova Lite · us-east-1</text>
  <text x="{AX + 24}" y="{AY + 106}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">solo infiere texto</text>
  <text x="{AX + 24}" y="{AY + 134}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">la carpeta no sube a AWS</text>
  <text x="{AX + 24}" y="{AY + 162}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">sin clave: tero-offline</text>

  <line x1="{TX + TW // 2}" y1="{TY + TH}" x2="{TX + TW // 2}" y2="{FY - 8}" stroke="{amber}" stroke-width="3" marker-end="url(#d)"/>
  <text x="{TX + TW // 2 + 12}" y="{TY + TH + 32}" fill="{amber}" font-family="Inter, sans-serif" font-size="13">lee fuentes/</text>

  <line x1="{PX + PW // 2}" y1="{PY + PH}" x2="{PX + PW // 2}" y2="{FY + 184}" stroke="{menta}" stroke-width="3"/>
  <line x1="{PX + PW // 2}" y1="{FY + 184}" x2="{FX - 8}" y2="{FY + 184}" stroke="{menta}" stroke-width="3" marker-end="url(#b)"/>
  <text x="{(PX + PW // 2 + FX) // 2 - 42}" y="{FY + 170}" fill="{menta}" font-family="Inter, sans-serif" font-size="13">s / b escribe</text>

  <rect x="{FX}" y="{FY}" width="{FW}" height="{FH}" rx="16" fill="{panel}" stroke="{line}"/>
  <rect x="{FX}" y="{FY}" width="6" height="{FH}" fill="{violet}"/>
  <text x="{FX + 24}" y="{FY + 42}" fill="{crema}" font-family="Inter, sans-serif" font-size="24" font-weight="600">Carpeta de trabajo</text>

  <rect x="{FX + 20}" y="{FY + 58}" width="{FW - 40}" height="58" rx="10" fill="{row}" stroke="{line}"/>
  <rect x="{FX + 20}" y="{FY + 58}" width="5" height="58" fill="{amber}"/>
  <text x="{FX + 36}" y="{FY + 82}" fill="{crema}" font-family="ui-monospace, monospace" font-size="15">fuentes/</text>
  <text x="{FX + 36}" y="{FY + 104}" fill="{muted}" font-family="Inter, sans-serif" font-size="14">originales. tero lee, nadie las pisa</text>

  <rect x="{FX + 20}" y="{FY + 126}" width="{FW - 40}" height="58" rx="10" fill="{row}" stroke="{line}"/>
  <rect x="{FX + 20}" y="{FY + 126}" width="5" height="58" fill="{orange}"/>
  <text x="{FX + 36}" y="{FY + 150}" fill="{crema}" font-family="ui-monospace, monospace" font-size="15">borradores/</text>
  <text x="{FX + 36}" y="{FY + 172}" fill="{muted}" font-family="Inter, sans-serif" font-size="14">si el profesor aprieta b</text>

  <rect x="{FX + 20}" y="{FY + 194}" width="{FW - 40}" height="58" rx="10" fill="{row}" stroke="{line}"/>
  <rect x="{FX + 20}" y="{FY + 194}" width="5" height="58" fill="{menta}"/>
  <text x="{FX + 36}" y="{FY + 218}" fill="{crema}" font-family="ui-monospace, monospace" font-size="15">derivados/</text>
  <text x="{FX + 36}" y="{FY + 240}" fill="{muted}" font-family="Inter, sans-serif" font-size="14">si el profesor aprieta s  (para la clase)</text>
</svg>
"""


def main() -> None:
    img = render_png()
    img.save(PNG, "PNG", optimize=False, compress_level=1)
    SVG.write_text(render_svg(), encoding="utf-8")
    print(f"wrote {PNG} {img.size[0]}x{img.size[1]} {PNG.stat().st_size} bytes")
    print(f"wrote {SVG} {SVG.stat().st_size} bytes")


if __name__ == "__main__":
    main()
