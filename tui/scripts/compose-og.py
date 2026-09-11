#!/usr/bin/env python3
"""Compose site/assets/tero-og.png from the captured OpenTUI home.

The card is the live 140×40 JetBrains shot on Nord — not a splash wave
and not a second macOS titlebar around the TUI.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1].parent
HOME = ROOT / "site" / "assets" / "tui" / "frames" / "home.png"
OUT = ROOT / "site" / "assets" / "tero-og.png"

OG_W, OG_H = 1200, 630
BG = (11, 13, 16)
PAD = 28


def main() -> None:
    shot = Image.open(HOME).convert("RGB")
    max_w = OG_W - PAD * 2
    max_h = OG_H - PAD * 2
    scale = min(max_w / shot.width, max_h / shot.height, 1)
    inner_w = max(1, round(shot.width * scale))
    inner_h = max(1, round(shot.height * scale))
    inner = shot.resize((inner_w, inner_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (OG_W, OG_H), BG)
    canvas.paste(inner, ((OG_W - inner_w) // 2, (OG_H - inner_h) // 2))
    canvas.save(OUT, optimize=True)
    print(f"wrote {OUT} {canvas.size} from {HOME.name} @{scale:.3f}")


if __name__ == "__main__":
    main()
