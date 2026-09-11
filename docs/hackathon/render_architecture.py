#!/usr/bin/env python3
"""Render architecture.png + architecture.svg. Requires Pillow.

python docs/hackathon/render_architecture.py

Fonts: prefers Inter / JetBrains Mono when installed, and falls back to DejaVu
(shipped with most Linux distributions) so the diagram can be regenerated on a
plain machine. The committed PNG is produced by whichever pair is available.
"""

from __future__ import annotations

import shutil
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

W, H = 1680, 880

# Layout: three columns, two rows.
PX, PY, PW, PH = 48, 120, 400, 290
TX, TY, TW, TH = 560, 120, 520, 290
AX, AY, AW, AH = 1192, 120, 440, 290

FX, FY, FW, FH = 560, 500, 520, 300   # carpeta de trabajo (host writes here)
BX, BY, BW, BH = 48, 500, 400, 300    # banco begonia (official curriculum)
LX, LY, LW, LH = 1192, 500, 440, 300  # privacidad (Ley 21.719)

# Font resolution: Inter/JetBrains when present, DejaVu otherwise.
_FONT_DIRS = (
    Path("/usr/share/fonts/truetype/macos"),
    Path("/usr/share/fonts/truetype/jetbrains-mono"),
    Path("/usr/share/fonts/truetype/inter"),
    Path.home() / ".local/share/fonts",
    Path.home() / "Library/Fonts",
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts"),
)

_FALLBACKS: dict[str, tuple[str, ...]] = {
    "Inter-Bold.ttf": ("DejaVuSans-Bold.ttf",),
    "Inter-SemiBold.ttf": ("DejaVuSans-Bold.ttf",),
    "Inter-Medium.ttf": ("DejaVuSans-Bold.ttf",),
    "Inter-Regular.ttf": ("DejaVuSans.ttf",),
    "JetBrainsMono-Medium.ttf": ("DejaVuSansMono-Bold.ttf",),
    "JetBrainsMono-Regular.ttf": ("DejaVuSansMono.ttf",),
}


def _font_path(name: str) -> Path:
    names = (name, *_FALLBACKS.get(name, ()))
    for folder in _FONT_DIRS:
        for candidate in names:
            path = folder / candidate
            if path.is_file():
                return path
    found = shutil.which(name)
    if found:
        return Path(found)
    raise FileNotFoundError(f"No encontré la fuente {name} ni su reemplazo.")


def fnt(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(_font_path(name)), size)


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


def arrow_elbow(
    draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, color, *, dash: bool = False
) -> None:
    """Two-segment connector: vertical from (x1, y1) to mid, then to (x2, y2)."""
    mid = (y1 + y2) // 2
    if dash:
        for yy in range(y1, mid, 14):
            draw.line((x1, yy, x1, min(yy + 7, mid)), fill=color, width=3)
        for xx in range(min(x1, x2), max(x1, x2), 14):
            start = xx if x1 <= x2 else x2 + (x1 - xx) - 7
            draw.line((start, mid, start + 7, mid), fill=color, width=3)
        for yy in range(mid, y2 - 12, 14):
            draw.line((x2, yy, x2, min(yy + 7, y2 - 12)), fill=color, width=3)
    else:
        draw.line((x1, y1, x1, mid), fill=color, width=3)
        draw.line((x1, mid, x2, mid), fill=color, width=3)
        draw.line((x2, mid, x2, y2 - 12), fill=color, width=3)
    draw.polygon([(x2, y2), (x2 - 7, y2 - 14), (x2 + 7, y2 - 14)], fill=color)


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
        "your sources, your judgment — the agent proposes, the educator decides",
        font=fnt("Inter-Regular.ttf", 20),
        fill=CREMA,
    )
    draw.text(
        (48, 74),
        "One turn: the teacher writes in Spanish, tero reads the folder and the official curriculum bank, "
        "Bedrock drafts, the teacher approves — and only then does the host write.",
        font=fnt("Inter-Regular.ttf", 15),
        fill=MUTED,
    )

    # ---- Column 1: teacher
    card(draw, PX, PY, PW, PH, CIAN, "Teacher")
    body(
        draw,
        PX + 24,
        PY + 62,
        [
            ("Types in natural Spanish", CREMA),
            ("\"dale\" / y  →  approve", MUTED),
            ("\"no, gracias\"  →  discard", MUTED),
            ("\"mejor para 2° básico\" → revise", MUTED),
        ],
    )
    chips(
        draw,
        PX + 24,
        PY + 190,
        [("y  approve", (20, 83, 45)), ("n  discard", (88, 28, 28))],
    )
    draw.text(
        (PX + 24, PY + 240),
        "Sees the warnings and the full preview first.",
        font=fnt("Inter-Regular.ttf", 13),
        fill=MUTED,
    )

    # ---- Column 2: tero (Strands)
    card(draw, TX, TY, TW, TH, MENTA, "tero  ·  Strands Agents")
    body(
        draw,
        TX + 24,
        TY + 62,
        [
            ("Reads the folder. Never touches the originals.", CREMA),
            ("Queries the official curriculum bank.", MUTED),
            ("Proposes in memory: plan / guide / test / rubric.", MUTED),
            ("No write tool exists in the registry.", MENTA),
        ],
    )

    # ---- Column 3: Bedrock
    card(draw, AX, AY, AW, AH, ORANGE, "Amazon Bedrock")
    body(
        draw,
        AX + 24,
        AY + 62,
        [
            ("amazon.nova-lite-v1:0", CREMA),
            ("us-east-1 · serverless", MUTED),
            ("infers text only", MUTED),
            ("the folder never leaves the machine", MUTED),
            ("no keys → tero-offline (scripted)", MUTED),
        ],
    )

    # ---- Row 2: bank (left), folder (center), privacy (right)
    card(draw, BX, BY, BW, BH, AMBER, "Begonia bank")
    body(
        draw,
        BX + 24,
        BY + 58,
        [
            ("Official MINEDUC curriculum", CREMA),
            ("13,722 approved items", MUTED),
            ("1,159 teacher guidances", MUTED),
        ],
    )
    folder_row(
        draw,
        BX + 20,
        BY + 150,
        BW - 40,
        52,
        AMBER,
        "banco:<id>",
        "verified citations + pauta oficial",
    )
    draw.text(
        (BX + 20, BY + 216),
        "Read-only HTTP. Material is not invented:",
        font=fnt("Inter-Regular.ttf", 13),
        fill=MUTED,
    )
    draw.text(
        (BX + 20, BY + 238),
        "it is grounded and traceable (banco_snapshot).",
        font=fnt("Inter-Regular.ttf", 13),
        fill=MUTED,
    )

    card(draw, FX, FY, FW, FH, VIOLET, "Working folder (system of record)")
    folder_row(
        draw,
        FX + 20,
        FY + 58,
        FW - 40,
        56,
        AMBER,
        "fuentes/",
        "originals · SHA-256 hashed · never overwritten",
    )
    folder_row(
        draw,
        FX + 20,
        FY + 124,
        FW - 40,
        56,
        MENTA,
        "derivados/",
        "written by the host only, after approval",
    )
    folder_row(
        draw,
        FX + 20,
        FY + 190,
        FW - 40,
        56,
        ORANGE,
        "borradores/",
        "legacy: readable, no new writes",
    )

    card(draw, LX, LY, LW, LH, ORANGE, "Privacy guard")
    body(
        draw,
        LX + 24,
        LY + 58,
        [
            ("Chile · Ley 21.719", CREMA),
            ("Gradebooks, rosters and", MUTED),
            ("health reports never reach", MUTED),
            ("the model. RUT-aware.", MUTED),
        ],
    )
    chips(draw, LX + 24, LY + 196, [("non-blocking advisory", (66, 48, 8))])
    draw.text(
        (LX + 24, LY + 244),
        "Files are never deleted, only left unread.",
        font=fnt("Inter-Regular.ttf", 13),
        fill=MUTED,
    )

    # ---- Arrows
    arrow_right(draw, PX + PW, TX, PY + 96, CIAN)
    caption(draw, (PX + PW + 16, PY + 74), "message", MUTED)
    arrow_left(draw, TX, PX + PW, PY + 152, MENTA)
    caption(draw, (PX + PW + 16, PY + 176), "proposal", MENTA)

    arrow_right(draw, TX + TW, AX, AY + 96, ORANGE)
    caption(draw, (TX + TW + 14, AY + 74), "prompt", MUTED)
    arrow_left(draw, AX, TX + TW, AY + 152, MENTA)
    caption(draw, (TX + TW + 10, AY + 160), "draft", MENTA)

    # tero -> folder (read sources, write approved)
    arrow_down(draw, TX + TW // 2, TY + TH, FY, AMBER)
    caption(draw, (TX + TW // 2 + 14, TY + TH + 16), "reads fuentes/ (hash)", AMBER)

    # tero -> begonia bank (dashed: read-only consultation)
    arrow_elbow(draw, TX + 60, TY + TH, BX + BW // 2, BY, AMBER, dash=True)
    caption(draw, (BX + BW // 2 + 14, BY - 34), "consults official items", AMBER)

    # tero -> privacy guard
    arrow_elbow(draw, TX + TW - 60, TY + TH, LX + LW // 2, LY, ORANGE, dash=True)
    caption(draw, (LX + LW // 2 - 96, LY - 34), "filters sensitive data", ORANGE)

    # host write path: approval -> derivados/
    write_y = FY + 152
    draw.line((PX + PW // 2, PY + PH, PX + PW // 2, write_y), fill=MENTA, width=3)
    draw.line((PX + PW // 2, write_y, FX - 12, write_y), fill=MENTA, width=3)
    draw.polygon([(FX, write_y), (FX - 14, write_y - 7), (FX - 14, write_y + 7)], fill=MENTA)
    caption(draw, ((PX + PW // 2 + FX) // 2 - 96, write_y - 40), "approval → host writes", MENTA)

    return img


def render_svg() -> str:
    def rgb(c: tuple[int, int, int]) -> str:
        return hex_rgb(c)

    fondo, panel, row = rgb(FONDO), rgb(PANEL), rgb(ROW)
    crema, cian, menta = rgb(CREMA), rgb(CIAN), rgb(MENTA)
    muted, line, amber = rgb(MUTED), rgb(LINE), rgb(AMBER)
    violet, orange = rgb(VIOLET), rgb(ORANGE)
    y_bg, n_bg, w_bg = "#14532D", "#581C1C", "#423008"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="tero architecture">
  <title>tero - your sources, your judgment</title>
  <rect width="{W}" height="{H}" fill="{fondo}"/>
  <text x="48" y="54" fill="{cian}" font-family="Inter, sans-serif" font-size="34" font-weight="700">tero</text>
  <text x="128" y="52" fill="{crema}" font-family="Inter, sans-serif" font-size="20">your sources, your judgment - the agent proposes, the educator decides</text>
  <text x="48" y="88" fill="{muted}" font-family="Inter, sans-serif" font-size="15">One turn: the teacher writes in Spanish, tero reads the folder and the official curriculum bank, Bedrock drafts, the teacher approves - and only then does the host write.</text>

  <defs>
    <marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{cian}"/></marker>
    <marker id="b" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{menta}"/></marker>
    <marker id="c" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{orange}"/></marker>
    <marker id="d" markerWidth="10" markerHeight="10" refX="5" refY="8" orient="auto"><path d="M0,0 L5,10 L10,0 Z" fill="{amber}"/></marker>
  </defs>

  <line x1="{PX + PW}" y1="{PY + 96}" x2="{TX - 8}" y2="{PY + 96}" stroke="{cian}" stroke-width="3" marker-end="url(#a)"/>
  <text x="{PX + PW + 16}" y="{PY + 86}" fill="{muted}" font-family="Inter, sans-serif" font-size="13">message</text>
  <line x1="{TX}" y1="{PY + 152}" x2="{PX + PW + 8}" y2="{PY + 152}" stroke="{menta}" stroke-width="3" marker-end="url(#b)"/>
  <text x="{PX + PW + 16}" y="{PY + 176}" fill="{menta}" font-family="Inter, sans-serif" font-size="13">proposal</text>
  <line x1="{TX + TW}" y1="{AY + 96}" x2="{AX - 8}" y2="{AY + 96}" stroke="{orange}" stroke-width="3" marker-end="url(#c)"/>
  <text x="{TX + TW + 14}" y="{AY + 86}" fill="{muted}" font-family="Inter, sans-serif" font-size="13">prompt</text>
  <line x1="{AX}" y1="{AY + 152}" x2="{TX + TW + 8}" y2="{AY + 152}" stroke="{menta}" stroke-width="3" marker-end="url(#b)"/>
  <text x="{TX + TW + 10}" y="{AY + 174}" fill="{menta}" font-family="Inter, sans-serif" font-size="13">draft</text>

  <rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="16" fill="{panel}" stroke="{line}"/>
  <rect x="{PX}" y="{PY}" width="6" height="{PH}" fill="{cian}"/>
  <text x="{PX + 24}" y="{PY + 42}" fill="{crema}" font-family="Inter, sans-serif" font-size="24" font-weight="600">Teacher</text>
  <text x="{PX + 24}" y="{PY + 78}" fill="{crema}" font-family="Inter, sans-serif" font-size="17">Types in natural Spanish</text>
  <text x="{PX + 24}" y="{PY + 106}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">&#8220;dale&#8221; / y &#8594; approve</text>
  <text x="{PX + 24}" y="{PY + 134}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">&#8220;no, gracias&#8221; &#8594; discard</text>
  <text x="{PX + 24}" y="{PY + 162}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">&#8220;mejor para 2&#176; b&#225;sico&#8221; &#8594; revise</text>
  <rect x="{PX + 24}" y="{PY + 190}" width="126" height="32" rx="8" fill="{y_bg}"/><text x="{PX + 36}" y="{PY + 212}" fill="{crema}" font-family="Inter, sans-serif" font-size="15" font-weight="600">y  approve</text>
  <rect x="{PX + 160}" y="{PY + 190}" width="126" height="32" rx="8" fill="{n_bg}"/><text x="{PX + 172}" y="{PY + 212}" fill="{crema}" font-family="Inter, sans-serif" font-size="15" font-weight="600">n  discard</text>
  <text x="{PX + 24}" y="{PY + 252}" fill="{muted}" font-family="Inter, sans-serif" font-size="13">Sees the warnings and the full preview first.</text>

  <rect x="{TX}" y="{TY}" width="{TW}" height="{TH}" rx="16" fill="{panel}" stroke="{line}"/>
  <rect x="{TX}" y="{TY}" width="6" height="{TH}" fill="{menta}"/>
  <text x="{TX + 24}" y="{TY + 42}" fill="{crema}" font-family="Inter, sans-serif" font-size="24" font-weight="600">tero  &#183;  Strands Agents</text>
  <text x="{TX + 24}" y="{TY + 78}" fill="{crema}" font-family="Inter, sans-serif" font-size="17">Reads the folder. Never touches the originals.</text>
  <text x="{TX + 24}" y="{TY + 106}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">Queries the official curriculum bank.</text>
  <text x="{TX + 24}" y="{TY + 134}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">Proposes in memory: plan / guide / test / rubric.</text>
  <text x="{TX + 24}" y="{TY + 162}" fill="{menta}" font-family="Inter, sans-serif" font-size="17">No write tool exists in the registry.</text>

  <rect x="{AX}" y="{AY}" width="{AW}" height="{AH}" rx="16" fill="{panel}" stroke="{line}"/>
  <rect x="{AX}" y="{AY}" width="6" height="{AH}" fill="{orange}"/>
  <text x="{AX + 24}" y="{AY + 42}" fill="{crema}" font-family="Inter, sans-serif" font-size="24" font-weight="600">Amazon Bedrock</text>
  <text x="{AX + 24}" y="{AY + 78}" fill="{crema}" font-family="Inter, sans-serif" font-size="17">amazon.nova-lite-v1:0</text>
  <text x="{AX + 24}" y="{AY + 106}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">us-east-1 &#183; serverless</text>
  <text x="{AX + 24}" y="{AY + 134}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">infers text only</text>
  <text x="{AX + 24}" y="{AY + 162}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">the folder never leaves the machine</text>
  <text x="{AX + 24}" y="{AY + 190}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">no keys &#8594; tero-offline (scripted)</text>

  <line x1="{TX + TW // 2}" y1="{TY + TH}" x2="{TX + TW // 2}" y2="{FY - 8}" stroke="{amber}" stroke-width="3" marker-end="url(#d)"/>
  <text x="{TX + TW // 2 + 14}" y="{TY + TH + 30}" fill="{amber}" font-family="Inter, sans-serif" font-size="13">reads fuentes/ (hash)</text>

  <path d="M{TX + 60} {TY + TH} L{TX + 60} {(TY + TH + BY) // 2} L{BX + BW // 2} {(TY + TH + BY) // 2} L{BX + BW // 2} {BY - 10}" fill="none" stroke="{amber}" stroke-width="3" stroke-dasharray="8 6" marker-end="url(#d)"/>
  <text x="{BX + BW // 2 + 14}" y="{BY - 34}" fill="{amber}" font-family="Inter, sans-serif" font-size="13">consults official items</text>

  <path d="M{TX + TW - 60} {TY + TH} L{TX + TW - 60} {(TY + TH + LY) // 2} L{LX + LW // 2} {(TY + TH + LY) // 2} L{LX + LW // 2} {LY - 10}" fill="none" stroke="{orange}" stroke-width="3" stroke-dasharray="8 6" marker-end="url(#c)"/>
  <text x="{LX + LW // 2 - 96}" y="{LY - 34}" fill="{orange}" font-family="Inter, sans-serif" font-size="13">filters sensitive data</text>

  <line x1="{PX + PW // 2}" y1="{PY + PH}" x2="{PX + PW // 2}" y2="{FY + 152}" stroke="{menta}" stroke-width="3"/>
  <line x1="{PX + PW // 2}" y1="{FY + 152}" x2="{FX - 8}" y2="{FY + 152}" stroke="{menta}" stroke-width="3" marker-end="url(#b)"/>
  <text x="{(PX + PW // 2 + FX) // 2 - 96}" y="{FY + 112}" fill="{menta}" font-family="Inter, sans-serif" font-size="13">approval &#8594; host writes</text>

  <rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="16" fill="{panel}" stroke="{line}"/>
  <rect x="{BX}" y="{BY}" width="6" height="{BH}" fill="{amber}"/>
  <text x="{BX + 24}" y="{BY + 42}" fill="{crema}" font-family="Inter, sans-serif" font-size="24" font-weight="600">Begonia bank</text>
  <text x="{BX + 24}" y="{BY + 78}" fill="{crema}" font-family="Inter, sans-serif" font-size="17">Official MINEDUC curriculum</text>
  <text x="{BX + 24}" y="{BY + 106}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">13,722 approved items</text>
  <text x="{BX + 24}" y="{BY + 134}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">1,159 teacher guidances</text>
  <rect x="{BX + 20}" y="{BY + 150}" width="{BW - 40}" height="52" rx="10" fill="{row}" stroke="{line}"/>
  <rect x="{BX + 20}" y="{BY + 150}" width="5" height="52" fill="{amber}"/>
  <text x="{BX + 36}" y="{BY + 174}" fill="{crema}" font-family="ui-monospace, monospace" font-size="15">banco:&lt;id&gt;</text>
  <text x="{BX + 36}" y="{BY + 194}" fill="{muted}" font-family="Inter, sans-serif" font-size="14">verified citations + pauta oficial</text>
  <text x="{BX + 20}" y="{BY + 226}" fill="{muted}" font-family="Inter, sans-serif" font-size="13">Read-only HTTP. Material is not invented:</text>
  <text x="{BX + 20}" y="{BY + 248}" fill="{muted}" font-family="Inter, sans-serif" font-size="13">it is grounded and traceable (banco_snapshot).</text>

  <rect x="{FX}" y="{FY}" width="{FW}" height="{FH}" rx="16" fill="{panel}" stroke="{line}"/>
  <rect x="{FX}" y="{FY}" width="6" height="{FH}" fill="{violet}"/>
  <text x="{FX + 24}" y="{FY + 42}" fill="{crema}" font-family="Inter, sans-serif" font-size="24" font-weight="600">Working folder (system of record)</text>

  <rect x="{FX + 20}" y="{FY + 58}" width="{FW - 40}" height="56" rx="10" fill="{row}" stroke="{line}"/>
  <rect x="{FX + 20}" y="{FY + 58}" width="5" height="56" fill="{amber}"/>
  <text x="{FX + 36}" y="{FY + 82}" fill="{crema}" font-family="ui-monospace, monospace" font-size="15">fuentes/</text>
  <text x="{FX + 36}" y="{FY + 104}" fill="{muted}" font-family="Inter, sans-serif" font-size="14">originals &#183; SHA-256 hashed &#183; never overwritten</text>

  <rect x="{FX + 20}" y="{FY + 124}" width="{FW - 40}" height="56" rx="10" fill="{row}" stroke="{line}"/>
  <rect x="{FX + 20}" y="{FY + 124}" width="5" height="56" fill="{menta}"/>
  <text x="{FX + 36}" y="{FY + 148}" fill="{crema}" font-family="ui-monospace, monospace" font-size="15">derivados/</text>
  <text x="{FX + 36}" y="{FY + 170}" fill="{muted}" font-family="Inter, sans-serif" font-size="14">written by the host only, after approval</text>

  <rect x="{FX + 20}" y="{FY + 190}" width="{FW - 40}" height="56" rx="10" fill="{row}" stroke="{line}"/>
  <rect x="{FX + 20}" y="{FY + 190}" width="5" height="56" fill="{orange}"/>
  <text x="{FX + 36}" y="{FY + 214}" fill="{crema}" font-family="ui-monospace, monospace" font-size="15">borradores/</text>
  <text x="{FX + 36}" y="{FY + 236}" fill="{muted}" font-family="Inter, sans-serif" font-size="14">legacy: readable, no new writes</text>

  <rect x="{LX}" y="{LY}" width="{LW}" height="{LH}" rx="16" fill="{panel}" stroke="{line}"/>
  <rect x="{LX}" y="{LY}" width="6" height="{LH}" fill="{orange}"/>
  <text x="{LX + 24}" y="{LY + 42}" fill="{crema}" font-family="Inter, sans-serif" font-size="24" font-weight="600">Privacy guard</text>
  <text x="{LX + 24}" y="{LY + 78}" fill="{crema}" font-family="Inter, sans-serif" font-size="17">Chile &#183; Ley 21.719</text>
  <text x="{LX + 24}" y="{LY + 106}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">Gradebooks, rosters and</text>
  <text x="{LX + 24}" y="{LY + 134}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">health reports never reach</text>
  <text x="{LX + 24}" y="{LY + 162}" fill="{muted}" font-family="Inter, sans-serif" font-size="17">the model. RUT-aware.</text>
  <rect x="{LX + 24}" y="{LY + 196}" width="196" height="32" rx="8" fill="{w_bg}"/><text x="{LX + 36}" y="{LY + 218}" fill="{crema}" font-family="Inter, sans-serif" font-size="15" font-weight="600">non-blocking advisory</text>
  <text x="{LX + 24}" y="{LY + 256}" fill="{muted}" font-family="Inter, sans-serif" font-size="13">Files are never deleted, only left unread.</text>
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
