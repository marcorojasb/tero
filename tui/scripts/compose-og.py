#!/usr/bin/env python3
"""Compose site/assets/tero-og.png from the captured OpenTUI home.

The OG card is the landing window (traffic + tero + ~/tero) hugging the
live 140×40 JetBrains shot — not the old splash wave.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1].parent
HOME = ROOT / "site" / "assets" / "tui" / "frames" / "home.png"
OUT = ROOT / "site" / "assets" / "tero-og.png"
FONT = Path("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf")

OG_W, OG_H = 1200, 630
BG = (11, 13, 16)
PANEL = (18, 21, 26)
BORDER = (44, 51, 60)
TEXT = (216, 222, 233)
MUTED = (122, 132, 144)
TRAFFIC = ((255, 95, 87), (254, 188, 46), (40, 200, 64))
CHROME_H = 36
PAD = 28


def main() -> None:
    shot = Image.open(HOME).convert("RGB")
    max_w = OG_W - PAD * 2
    max_h = OG_H - PAD * 2 - CHROME_H
    scale = min(max_w / shot.width, max_h / shot.height, 1)
    inner_w = max(1, round(shot.width * scale))
    inner_h = max(1, round(shot.height * scale))
    inner = shot.resize((inner_w, inner_h), Image.Resampling.LANCZOS)

    win_w = inner_w
    win_h = CHROME_H + inner_h
    window = Image.new("RGB", (win_w, win_h), (11, 13, 16))
    draw = ImageDraw.Draw(window)
    draw.rectangle((0, 0, win_w, CHROME_H), fill=PANEL)
    draw.line((0, CHROME_H - 1, win_w, CHROME_H - 1), fill=BORDER)
    draw.rectangle((0, 0, win_w - 1, win_h - 1), outline=BORDER)
    x = 14
    for color in TRAFFIC:
        draw.ellipse((x, 12, x + 12, 24), fill=color)
        x += 18
    font = ImageFont.truetype(str(FONT), 13) if FONT.is_file() else ImageFont.load_default()
    title = "tero"
    tw = draw.textlength(title, font=font)
    draw.text(((win_w - tw) / 2, 10), title, fill=TEXT, font=font)
    path = "~/tero"
    pw = draw.textlength(path, font=font)
    draw.text((win_w - pw - 14, 10), path, fill=MUTED, font=font)
    window.paste(inner, (0, CHROME_H))

    canvas = Image.new("RGB", (OG_W, OG_H), BG)
    canvas.paste(window, ((OG_W - win_w) // 2, (OG_H - win_h) // 2))
    canvas.save(OUT, optimize=True)
    print(f"wrote {OUT} {canvas.size} from {HOME.name} @{scale:.3f}")


if __name__ == "__main__":
    main()
