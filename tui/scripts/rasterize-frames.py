#!/usr/bin/env python3
"""Rasterize OpenTUI captureSpans to PNG with the same font as `tero tui`.

xfce4-terminal --geometry=140x40 --font='JetBrains Mono 13' measures
10×24 px cells (1402×962 widget ≈ 140*10 + pad × 40*24 + pad).
"""

from __future__ import annotations

import json
from pathlib import Path
from shutil import copyfile

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FRAMES = HERE.parents[1] / "site" / "assets" / "tui" / "frames"
FONT_REG = Path("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf")
FONT_BOLD = Path("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf")

# 13pt at 96 dpi — same face xfce4-terminal uses for "JetBrains Mono 13".
FONT_PX = 17
CELL_W = 10
CELL_H = 24


def rgba(channel: list[float] | tuple[float, ...]) -> tuple[int, int, int]:
    r, g, b = channel[0], channel[1], channel[2]
    if r <= 1 and g <= 1 and b <= 1:
        r, g, b = r * 255, g * 255, b * 255
    return (int(round(r)), int(round(g)), int(round(b)))


def rasterize(frame: dict, regular: ImageFont.FreeTypeFont, bold: ImageFont.FreeTypeFont) -> Image.Image:
    cols = int(frame["cols"])
    rows = int(frame["rows"])
    img = Image.new("RGB", (cols * CELL_W, rows * CELL_H), (11, 13, 16))
    draw = ImageDraw.Draw(img)
    ascent, descent = regular.getmetrics()
    glyph_h = ascent + descent
    dy = max(0, (CELL_H - glyph_h) // 2)
    for y, line in enumerate(frame.get("lines") or []):
        x = 0
        for span in line.get("spans") or []:
            text = str(span.get("text") or "")
            width = int(span.get("width") or len(text))
            fg = rgba(span.get("fg") or [0.85, 0.87, 0.91])
            bg = rgba(span.get("bg") or [0.043, 0.051, 0.063])
            font = bold if int(span.get("attributes") or 0) & 1 else regular
            x1 = x + width * CELL_W
            y0 = y * CELL_H
            draw.rectangle((x, y0, x1 - 1, y0 + CELL_H - 1), fill=bg)
            chars = list(text)
            if len(chars) == width:
                for i, ch in enumerate(chars):
                    if ch != " ":
                        draw.text((x + i * CELL_W, y0 + dy), ch, font=font, fill=fg)
            else:
                draw.text((x, y0 + dy), text, font=font, fill=fg)
            x = x1
            if x >= cols * CELL_W:
                break
    return img


def main() -> None:
    regular = ImageFont.truetype(str(FONT_REG), FONT_PX)
    bold = ImageFont.truetype(str(FONT_BOLD), FONT_PX)
    index_path = FRAMES / "index.json"
    names: list[str] = []
    if index_path.is_file():
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        names = [item["name"] for item in payload.get("frames") or []]
    if not names:
        names = [path.stem for path in sorted(FRAMES.glob("*.json")) if path.name not in {"index.json", "theme.json"}]
    for name in names:
        src = FRAMES / f"{name}.json"
        if not src.is_file():
            continue
        frame = json.loads(src.read_text(encoding="utf-8"))
        png = rasterize(frame, regular, bold)
        dest = FRAMES / f"{name}.png"
        png.save(dest, format="PNG", optimize=True)
        print(f"raster {name} {png.size[0]}x{png.size[1]} → {dest.stat().st_size} bytes")
    for alias in ("plan", "puerta"):
        src = FRAMES / f"{alias}-1.png"
        if src.is_file():
            copyfile(src, FRAMES / f"{alias}.png")


if __name__ == "__main__":
    main()
