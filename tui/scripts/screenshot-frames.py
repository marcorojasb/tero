#!/usr/bin/env python3
"""Screenshot each OpenTUI frame from xfce4-terminal, JetBrains Mono 13.

Las alturas siguen a `capture-frames.ts`: home y la conversación caben en
40 filas; la tarjeta de propuesta necesita 46.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from PIL import Image

DISPLAY = os.environ.get("DISPLAY", ":1")
ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT.parent / "site" / "assets" / "tui" / "frames"
BUN = os.environ.get("BUN", str(Path.home() / ".bun/bin/bun"))
SHOW = ROOT / "scripts" / "show-frame.ts"
CELL_W = 10
CELL_H = 24
COLS = 140

# (frame, filas) — se leen de index.json si existe, para no quedar obsoletos.
FALLBACK = [
    ("home", 40),
    ("help", 40),
    ("respuesta", 40),
    ("conversacion", 40),
    ("conversacion-streaming", 40),
    ("propuesta", 46),
    ("propuesta-guia", 46),
    ("propuesta-adaptar", 46),
    ("escrito", 46),
    ("escrito-adaptar", 46),
    ("descartado", 46),
    ("error", 40),
]


def frames_index() -> list[tuple[str, int]]:
    path = FRAMES / "index.json"
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = [(item["name"], int(item["rows"])) for item in payload.get("frames") or []]
        if rows:
            return rows
    return list(FALLBACK)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY
    return subprocess.run(cmd, env=env, text=True, capture_output=True, **kwargs)


def window_id(title: str) -> str | None:
    found = run(["xdotool", "search", "--name", f"^{title}$"])
    ids = [line.strip() for line in found.stdout.splitlines() if line.strip()]
    return ids[-1] if ids else None


def geometry(wid: str) -> tuple[int, int, int, int]:
    info = run(["xwininfo", "-id", wid])
    vals: dict[str, int] = {}
    for line in info.stdout.splitlines():
        if "Absolute upper-left X" in line:
            vals["x"] = int(line.split(":")[-1])
        elif "Absolute upper-left Y" in line:
            vals["y"] = int(line.split(":")[-1])
        elif line.strip().startswith("Width:"):
            vals["w"] = int(line.split(":")[-1])
        elif line.strip().startswith("Height:"):
            vals["h"] = int(line.split(":")[-1])
    return vals["x"], vals["y"], vals["w"], vals["h"]


def grab(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "x11grab",
            "-draw_mouse",
            "0",
            "-video_size",
            "1920x1200",
            "-i",
            f"{DISPLAY}.0",
            "-frames:v",
            "1",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def crop_cells(img: Image.Image, rows: int) -> Image.Image:
    w, h = img.size
    target_w, target_h = COLS * CELL_W, rows * CELL_H
    x0 = max(0, (w - target_w) // 2)
    y0 = max(0, (h - target_h) // 2)
    if w >= target_w + 2 and h >= target_h + 2:
        x0 = 1
        y0 = 1
    return img.crop((x0, y0, x0 + min(target_w, w - x0), y0 + min(target_h, h - y0))).resize(
        (target_w, target_h),
        Image.Resampling.NEAREST,
    )


def capture_one(name: str, rows: int) -> None:
    title = f"tero-frame-{name}"
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY
    proc = subprocess.Popen(
        [
            "xfce4-terminal",
            "--disable-server",
            f"--display={DISPLAY}",
            f"--geometry={COLS}x{rows}",
            "--hide-menubar",
            "--hide-scrollbar",
            "--hide-toolbar",
            "--color-bg=#0b0d10",
            "--color-text=#d8dee9",
            "--font=JetBrains Mono 13",
            f"--title={title}",
            "--working-directory",
            str(ROOT),
            "-e",
            f"{BUN} {SHOW} {name}",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    wid = None
    for _ in range(20):
        time.sleep(0.25)
        wid = window_id(title)
        if wid:
            break
    if not wid:
        proc.kill()
        raise RuntimeError(f"no window for {title}")
    run(["xdotool", "windowraise", wid])
    run(["xdotool", "windowmove", wid, "0", "30"])
    time.sleep(0.8)
    x, y, w, h = geometry(wid)
    desktop = Path(f"/tmp/tero-desk-{name}.png")
    grab(desktop)
    full = Image.open(desktop).convert("RGB")
    term = full.crop((x, y, x + w, y + h))
    shot = crop_cells(term, rows)
    dest = FRAMES / f"{name}.png"
    shot.save(dest, format="PNG", optimize=True)
    print(f"shot {name} win={w}x{h} png={shot.size[0]}x{shot.size[1]} {dest.stat().st_size} bytes")
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> None:
    for name, rows in frames_index():
        capture_one(name, rows)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
