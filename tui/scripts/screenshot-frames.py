#!/usr/bin/env python3
"""Screenshot each OpenTUI frame from xfce4-terminal at 140×40, JetBrains Mono 13."""

from __future__ import annotations

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
ROWS = 40

NAMES = [
    "home",
    "help",
    "encargo",
    "leyendo-1",
    "plan-1",
    "puerta-1",
    "leyendo-2",
    "plan-2",
    "puerta-2",
    "leyendo-3",
    "plan-3",
    "puerta-3",
    "leyendo-4",
    "plan-4",
    "puerta-4",
]


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


def crop_cells(img: Image.Image) -> Image.Image:
    w, h = img.size
    target_w, target_h = COLS * CELL_W, ROWS * CELL_H
    x0 = max(0, (w - target_w) // 2)
    y0 = max(0, (h - target_h) // 2)
    if w >= target_w + 2 and h >= target_h + 2:
        x0 = 1
        y0 = 1
    return img.crop((x0, y0, x0 + min(target_w, w - x0), y0 + min(target_h, h - y0))).resize(
        (target_w, target_h),
        Image.Resampling.NEAREST,
    )


def capture_one(name: str) -> None:
    title = f"tero-frame-{name}"
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY
    proc = subprocess.Popen(
        [
            "xfce4-terminal",
            "--disable-server",
            f"--display={DISPLAY}",
            "--geometry=140x40",
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
    shot = crop_cells(term)
    dest = FRAMES / f"{name}.png"
    shot.save(dest, format="PNG", optimize=True)
    print(f"shot {name} win={w}x{h} png={shot.size[0]}x{shot.size[1]} {dest.stat().st_size} bytes")
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> None:
    for name in NAMES:
        capture_one(name)
        time.sleep(0.2)
    for alias in ("plan", "puerta"):
        src = FRAMES / f"{alias}-1.png"
        if src.is_file():
            (FRAMES / f"{alias}.png").write_bytes(src.read_bytes())


if __name__ == "__main__":
    main()
