#!/usr/bin/env python3
"""Render the Devpost architecture diagram (PNG). Requires Pillow.

python docs/hackathon/render_architecture.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).with_name("architecture.png")

# Terminal UI Brand System v1.0
FONDO = (7, 11, 12, 255)
PANEL = (12, 18, 20, 255)
PANEL2 = (16, 26, 28, 255)
CREMA = (244, 241, 222, 255)
CIAN = (34, 211, 238, 255)
AQUA = (32, 212, 191, 255)
TEAL = (20, 184, 166, 255)
MENTA = (134, 239, 172, 255)
LIMA = (163, 230, 53, 255)
MUTED = (148, 168, 170, 255)
LINE = (36, 54, 58, 255)
AMBER = (251, 191, 36, 255)
VIOLET = (196, 181, 253, 255)
ORANGE = (251, 146, 60, 255)
WHITE = (255, 255, 255, 255)

W, H = 2000, 1240
FONT_DIR_INTER = Path("/usr/share/fonts/truetype/macos")
FONT_DIR_JB = Path("/usr/share/fonts/truetype/jetbrains-mono")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONT_DIR_INTER / name if name.startswith("Inter") else FONT_DIR_JB / name
    return ImageFont.truetype(str(path), size)


def rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    r: int,
    fill,
    outline=None,
    width: int = 2,
) -> None:
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, fnt, fill) -> None:
    draw.text(xy, value, font=fnt, fill=fill)


def measure(draw: ImageDraw.ImageDraw, value: str, fnt) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), value, font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def arrow_right(
    draw: ImageDraw.ImageDraw, x1: int, y: int, x2: int, color, stroke: int = 3
) -> None:
    draw.line((x1, y, x2 - 14, y), fill=color, width=stroke)
    draw.polygon([(x2, y), (x2 - 16, y - 8), (x2 - 16, y + 8)], fill=color)


def arrow_down(draw: ImageDraw.ImageDraw, x: int, y1: int, y2: int, color, stroke: int = 3) -> None:
    draw.line((x, y1, x, y2 - 14), fill=color, width=stroke)
    draw.polygon([(x, y2), (x - 8, y2 - 16), (x + 8, y2 - 16)], fill=color)


def chip(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, bg, fg, fnt) -> int:
    tw, th = measure(draw, label, fnt)
    pad_x, pad_y = 14, 8
    w, h = tw + pad_x * 2, th + pad_y * 2
    rounded(draw, (x, y, x + w, y + h), 8, bg)
    text(draw, (x + pad_x, y + pad_y - 2), label, fnt, fg)
    return w


def card(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    accent,
    kicker: str,
    title: str,
) -> None:
    rounded(draw, (x, y, x + w, y + h), 16, PANEL, outline=LINE, width=2)
    draw.rectangle((x, y, x + 6, y + h), fill=accent)
    kicker_f = font("Inter-Medium.ttf", 15)
    title_f = font("Inter-SemiBold.ttf", 22)
    text(draw, (x + 24, y + 16), kicker.upper(), kicker_f, accent)
    text(draw, (x + 24, y + 38), title, title_f, CREMA)


def render() -> Image.Image:
    img = Image.new("RGBA", (W, H), FONDO)
    draw = ImageDraw.Draw(img)

    f_title = font("Inter-Bold.ttf", 36)
    f_sub = font("Inter-Regular.ttf", 20)
    f_meta = font("Inter-Medium.ttf", 15)
    f_body = font("Inter-Regular.ttf", 16)
    f_small = font("Inter-Regular.ttf", 14)
    f_mono = font("JetBrainsMono-Regular.ttf", 14)
    f_mono_b = font("JetBrainsMono-Bold.ttf", 15)
    f_chip = font("JetBrainsMono-Bold.ttf", 14)
    f_kicker = font("Inter-Medium.ttf", 13)

    # Header
    text(draw, (48, 28), "tero", f_title, CIAN)
    tw, _ = measure(draw, "tero", f_title)
    text(draw, (48 + tw + 16, 40), "the agent prepares, the teacher decides", f_sub, CREMA)
    text(
        draw,
        (48, 78),
        "Agents for Humans  ·  Professional Agents  ·  Strands Agents SDK  ·  Amazon Bedrock Nova Lite",
        f_meta,
        AQUA,
    )
    draw.line((48, 112, W - 48, 112), fill=LINE, width=1)

    # Row 1 — conversation path
    y1, h1 = 132, 260
    a = (48, y1, 430, h1)
    b = (518, y1, 300, h1)
    c = (858, y1, 520, h1)
    d = (1418, y1, 534, h1)

    mid_y = y1 + 118
    arrow_right(draw, a[0] + a[2], mid_y, b[0], CIAN)
    arrow_right(draw, b[0] + b[2], mid_y, c[0], CIAN)
    arrow_right(draw, c[0] + c[2], mid_y, d[0], AQUA)

    card(draw, *a, CIAN, "1. User interface", "Teacher at the keyboard")
    text(draw, (a[0] + 24, a[1] + 78), "OpenTUI  ·  Bun  ·  @opentui/core", f_body, CREMA)
    text(draw, (a[0] + 24, a[1] + 102), "home · rumbos 1-4 · encargo chips", f_small, MUTED)
    text(draw, (a[0] + 24, a[1] + 122), "plan card · evidencia · avisos", f_small, MUTED)
    text(draw, (a[0] + 24, a[1] + 148), "CLI fallback", f_kicker, MUTED)
    text(draw, (a[0] + 24, a[1] + 168), "python -m tero demo | tui", f_mono, MENTA)
    text(draw, (a[0] + 24, a[1] + 200), "Human gate — the model never writes", f_small, MUTED)
    gx = a[0] + 24
    gy = a[1] + 222
    for label, bg in (
        ("s", (20, 83, 45, 255)),
        ("n", (88, 28, 28, 255)),
        ("b", (66, 48, 8, 255)),
        ("c", (30, 58, 90, 255)),
    ):
        gx += chip(draw, gx, gy, label, bg, CREMA, f_chip) + 8
    text(draw, (gx + 4, gy + 6), "teacher decides", f_small, MUTED)

    card(draw, *b, MENTA, "2. Bridge", "JSONL stdin/stdout")
    text(draw, (b[0] + 24, b[1] + 78), "python -m tero bridge", f_mono, MENTA)
    text(draw, (b[0] + 24, b[1] + 104), "One JSON object per line.", f_body, CREMA)
    text(draw, (b[0] + 24, b[1] + 128), "Logs on stderr only.", f_small, MUTED)
    text(draw, (b[0] + 24, b[1] + 152), "TUI drives the session.", f_small, MUTED)
    text(draw, (b[0] + 24, b[1] + 176), "Host owns the write.", f_small, MUTED)
    text(draw, (b[0] + 24, b[1] + 210), "protocol v1", f_mono_b, AQUA)

    card(draw, *c, AQUA, "3. Strands Agents SDK", "TeacherSession")
    text(draw, (c[0] + 24, c[1] + 78), "Agent loop", f_kicker, MUTED)
    text(draw, (c[0] + 24, c[1] + 98), "model  →  tools  →  reason  →  pause", f_mono, CREMA)
    text(draw, (c[0] + 24, c[1] + 128), "Phases: plan · draft · correct", f_body, CREMA)
    text(
        draw,
        (c[0] + 24, c[1] + 154),
        "propose_plan / draft_artifact stay in-memory.",
        f_small,
        MUTED,
    )
    text(
        draw,
        (c[0] + 24, c[1] + 176),
        "If the model writes prose, host salvages a typed draft.",
        f_small,
        MUTED,
    )
    text(
        draw,
        (c[0] + 24, c[1] + 198),
        "Draft tool budget is capped. Warnings never block s.",
        f_small,
        MUTED,
    )
    text(
        draw, (c[0] + 24, c[1] + 228), "HITL is structural, not a chat afterthought.", f_small, LIMA
    )

    card(draw, *d, ORANGE, "4. AWS (lean inference)", "Amazon Bedrock")
    text(draw, (d[0] + 24, d[1] + 78), "Live", f_kicker, ORANGE)
    text(draw, (d[0] + 24, d[1] + 98), "BedrockModel  amazon.nova-lite-v1:0", f_mono, CREMA)
    text(draw, (d[0] + 24, d[1] + 118), "us-east-1  ·  auto-enable on first invoke", f_small, MUTED)
    text(draw, (d[0] + 24, d[1] + 146), "Offline (honest)", f_kicker, MENTA)
    text(draw, (d[0] + 24, d[1] + 166), "OfflineModel  tero-offline", f_mono, MENTA)
    text(
        draw, (d[0] + 24, d[1] + 186), "real Strands Model — not a fake InvokeModel", f_small, MUTED
    )
    text(
        draw,
        (d[0] + 24, d[1] + 214),
        "IAM  bedrock:InvokeModel*     Budgets  Free Tier",
        f_small,
        CREMA,
    )
    rounded(
        draw,
        (d[0] + 20, d[1] + 236, d[0] + d[2] - 20, d[1] + h1 - 16),
        8,
        PANEL2,
        outline=(90, 60, 30, 255),
        width=1,
    )
    text(
        draw,
        (d[0] + 32, d[1] + 244),
        "AgentCore Harness = optional sketch, not the carpeta",
        f_small,
        AMBER,
    )

    # Row 2 — tools + carpeta
    y2, h2 = 468, 360
    tools = (48, y2, 920, h2)
    disk = (1108, y2, 844, h2)
    # Strands calls tools (not AWS writing the folder)
    tool_arrow_x = c[0] + 200
    arrow_down(draw, tool_arrow_x, y1 + h1, y2, AQUA)
    text(draw, (tool_arrow_x + 12, y1 + h1 + 18), "calls tools", f_small, AQUA)
    arrow_right(draw, tools[0] + tools[2], y2 + 130, disk[0], AMBER)
    text(draw, (tools[0] + tools[2] + 16, y2 + 108), "read + hash", f_small, AMBER)

    card(
        draw,
        *tools,
        AMBER,
        "5. Tools  (in-process, sandboxed)",
        "Host tools — the model cannot write files",
    )
    col1 = tools[0] + 24
    col2 = tools[0] + 470
    ty = tools[1] + 78
    text(draw, (col1, ty), "Read the carpeta", f_kicker, AMBER)
    text(draw, (col2, ty), "Prepare (in-memory)", f_kicker, AMBER)
    ty += 24
    for i, line in enumerate(
        (
            "list_sources",
            "search_sources",
            "read_source",
            "list_oa  /  get_oa  /  search_oa",
        )
    ):
        text(draw, (col1, ty + i * 22), line, f_mono, CREMA)
    for i, line in enumerate(("propose_plan", "cite_evidence", "draft_artifact + payload_json")):
        text(draw, (col2, ty + i * 22), line, f_mono, CREMA)

    ty = tools[1] + 220
    text(draw, (col1, ty), "Host contracts (not the model)", f_kicker, MUTED)
    text(
        draw,
        (col1, ty + 22),
        "SHA-256 index  ·  path sandbox  ·  salvage prose/JSON",
        f_small,
        CREMA,
    )
    text(
        draw,
        (col1, ty + 44),
        "citation check  ·  coerce tool args  ·  OA catalog Chile (host-side)",
        f_small,
        CREMA,
    )
    text(
        draw,
        (col1, ty + 66),
        "No Browser  ·  no Code Interpreter  ·  no write into fuentes/",
        f_small,
        MUTED,
    )
    text(
        draw,
        (col1, ty + 96),
        "Chile OA catalog is paraphrase, not MINEDUC verbatim.",
        f_small,
        MUTED,
    )

    card(
        draw,
        *disk,
        VIOLET,
        "6. Carpeta de trabajo  =  system of record",
        "Local disk — never S3, never Runtime",
    )
    rows = [
        ("fuentes/", "originals  .md .txt .pdf", "hashed, read-only, never overwritten"),
        ("borradores/", "after teacher presses b", "draft kept, not accepted"),
        ("derivados/", "after teacher presses s", "accepted pages for class tomorrow"),
        (".tero/", "criticas + transcripciones", "host notes, not the artifact"),
    ]
    ry = disk[1] + 80
    for name, role, note in rows:
        rounded(
            draw,
            (disk[0] + 20, ry, disk[0] + disk[2] - 20, ry + 58),
            10,
            PANEL2,
            outline=LINE,
            width=1,
        )
        text(draw, (disk[0] + 36, ry + 8), name, f_mono_b, VIOLET)
        text(draw, (disk[0] + 200, ry + 8), role, f_body, CREMA)
        text(draw, (disk[0] + 36, ry + 32), note, f_small, MUTED)
        ry += 66

    # Row 3 — gate / output
    y3, h3 = 868, 268
    gate = (48, y3, 1904, h3)
    arrow_down(draw, 538, y2 + h2, y3, VIOLET)
    text(draw, (550, y2 + h2 + 10), "in-memory draft", f_small, VIOLET)

    card(
        draw,
        *gate,
        LIMA,
        "7. Output  ·  tero.gate writes only after the teacher",
        "s / n / b / c is the product",
    )
    text(
        draw,
        (gate[0] + 24, gate[1] + 78),
        "The Strands agent prepares. The host applies the decision. Originals are re-hashed after every write.",
        f_body,
        CREMA,
    )
    gx = gate[0] + 24
    gy = gate[1] + 118
    chips = (
        ("s  →  derivados/", (20, 83, 45, 255)),
        ("b  →  borradores/", (66, 48, 8, 255)),
        ("n  →  discard", (88, 28, 28, 255)),
        ("c  →  another pass", (30, 58, 90, 255)),
    )
    for label, bg in chips:
        gx += chip(draw, gx, gy, label, bg, CREMA, f_chip) + 12
    text(
        draw,
        (gate[0] + 24, gate[1] + 168),
        "Export (host templates, not model TeX)",
        f_kicker,
        MUTED,
    )
    text(
        draw,
        (gate[0] + 24, gate[1] + 190),
        "markdown   ·   docx   ·   LaTeX/PDF from JSON schemas in templates/latex/",
        f_mono,
        MENTA,
    )
    text(
        draw,
        (gate[0] + 24, gate[1] + 214),
        "thin_evidence / unverified_citation stay visible and never block s.",
        f_small,
        MUTED,
    )

    text(
        draw,
        (48, H - 36),
        "No AgentCore Runtime as SoR  ·  no Gateway MCP for the folder  ·  no multi-agent A2A  ·  MIT  ·  github.com/marcorojasb/tero",
        f_small,
        MUTED,
    )
    return img.convert("RGB")


def main() -> None:
    img = render()
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} {img.size[0]}x{img.size[1]}")


if __name__ == "__main__":
    main()
