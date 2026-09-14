#!/usr/bin/env python3
"""Linter objetivo de frames: detecta bloques 'vacíos' (cuadros negros).

Para cada PNG: malla 8x5; cuenta píxeles de 'tinta' (lejanos a los fondos
conocidos del video). Un bloque con <1.5% de tinta dentro de la zona de
contenido se marca VACÍO. Reporta los peores frames."""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

BGS = np.array(
    [
        [14, 17, 22],  # canvas
        [8, 10, 13],  # canvas viñeta
        [11, 13, 16],  # terminal bg
        [13, 16, 21],  # terminal stripe
        [12, 15, 20],  # terminal bg seal card
        [3, 4, 6],  # sombra
    ],
    dtype=np.int16,
)

ROWS, COLS = 5, 8
Y0, Y1 = 70, 955  # zona de contenido (sin top bar ni caption)


def ink_fraction(block: np.ndarray) -> float:
    px = block.reshape(-1, 3).astype(np.int16)
    d = np.min(np.abs(px[:, None, :] - BGS[None, :, :]).sum(axis=2), axis=1)
    return float((d > 40).mean())


def main(folder: str):
    worst = []
    for p in sorted(Path(folder).glob("frame_*.png")):
        arr = np.asarray(Image.open(p).convert("RGB"))
        h, w = arr.shape[:2]
        empties = []
        for r in range(ROWS):
            for c in range(COLS):
                y0 = Y0 + r * (Y1 - Y0) // ROWS
                y1 = Y0 + (r + 1) * (Y1 - Y0) // ROWS
                x0 = c * w // COLS
                x1 = (c + 1) * w // COLS
                blk = arr[y0:y1, x0:x1]
                if blk.size == 0:
                    continue
                if ink_fraction(blk) < 0.008:
                    empties.append((r, c))
        if empties:
            frac = len(empties) / (ROWS * COLS)
            worst.append((frac, p.name, empties))
    worst.sort(reverse=True)
    for frac, name, e in worst[:25]:
        print(f"{name}: {int(frac * 100):3d}% bloques vacíos  {e}")
    if not worst:
        print("sin bloques vacíos detectados")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out/qc")
