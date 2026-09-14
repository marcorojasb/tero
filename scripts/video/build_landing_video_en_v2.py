#!/usr/bin/env python3
"""tero — video de landing mejorado (español, v2).

Genera 1920x1080@30 con:
1. Narración es-CL por frases (edge-tts) con pausas controladas y subtítulos
   sincronizados por frase (SRT + VTT + burned-in).
2. Terminal OpenTUI reconstruido desde los .json de site/assets/tui/frames:
   tipeo real del prompt, streaming línea a línea y zooms de lectura.
3. Paleta de marca (site/brand.json), queltehue oficial, transiciones
   crossfade, barra de capítulos y colchón musical sutil.
4. Salidas en /tmp/tero-video-v2/out — nunca toca site/assets/video.

Uso:
    python scripts/video/build_landing_video_es_v2.py --plan     # solo TTS + timeline (rápido)
    python build_es_v2.py --frame 60 # renderiza el frame del segundo 60
    python build_es_v2.py --full     # todo (audio + video + subs)


Requiere (no están en [dev]): pillow, edge-tts, numpy.
Intermedios en temp (TTS/QC); entregables en site/assets/video/.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import subprocess
import sys
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parents[2]
SITE_ASSETS = REPO / "site" / "assets"
TUI_FRAMES = SITE_ASSETS / "tui" / "frames"
HOJAS = SITE_ASSETS / "hojas"
HACK = REPO / "docs" / "hackathon"
# Intermedios (TTS, QC) en temp; entregables a site/assets/video.
HERE = Path(tempfile.gettempdir()) / "tero-landing-v2-en"
AUDIO_DIR = HERE / "audio"
OUT_DIR = REPO / "site" / "assets" / "video"
QC_DIR = HERE / "qc"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
QC_DIR.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1920, 1080, 30

# ---------------------------------------------------------------- paleta marca
BRAND = json.loads((REPO / "site" / "brand.json").read_text())["palette"]
BG = tuple(int(BRAND["bg"][i : i + 2], 16) for i in (1, 3, 5))
PANEL = tuple(int(BRAND["panel"][i : i + 2], 16) for i in (1, 3, 5))
PANEL_HI = (24, 28, 36)
TXT = tuple(int(BRAND["text"][i : i + 2], 16) for i in (1, 3, 5))
MUT = (110, 120, 135)
ACC = tuple(int(BRAND["accent"][i : i + 2], 16) for i in (1, 3, 5))
OK = tuple(int(BRAND["ok"][i : i + 2], 16) for i in (1, 3, 5))
WARN = tuple(int(BRAND["warn"][i : i + 2], 16) for i in (1, 3, 5))
ERR = tuple(int(BRAND["err"][i : i + 2], 16) for i in (1, 3, 5))
PAPER = (243, 241, 234)

FONT_DIRS = [Path.home() / "Library" / "Fonts", Path("/System/Library/Fonts")]


def _find_font(names: list[str]) -> Path | None:
    for n in names:
        for d in FONT_DIRS:
            p = d / n
            if p.exists():
                return p
    return None


BOLD_PATH = _find_font(
    [
        "JetBrainsMonoNerdFont-Bold.ttf",
        "JetBrainsMonoNLNerdFont-Bold.ttf",
        "JetBrainsMono-Bold.ttf",
    ]
)
REG_PATH = _find_font(
    [
        "JetBrainsMonoNerdFont-Regular.ttf",
        "JetBrainsMonoNLNerdFont-Regular.ttf",
        "JetBrainsMonoNLNerdFont-Medium.ttf",
        "JetBrainsMono-Regular.ttf",
    ]
)
if BOLD_PATH is None or REG_PATH is None:
    sys.exit("Falta JetBrains Mono en ~/Library/Fonts")

_font_cache: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def F(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(BOLD_PATH if bold else REG_PATH), size)
    return _font_cache[key]


def text_w(font: ImageFont.FreeTypeFont, s: str) -> int:
    b = font.getbbox(s)
    return b[2] - b[0]


def ctext(draw, xy, s, fill, font, anchor="la"):
    draw.text(xy, s, fill=fill, font=font, anchor=anchor)


def rrect(draw, box, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def ease(t: float) -> float:
    return t * t * (3 - 2 * t)


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def fit(img: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    """Escala la imagen para caber en box (x0,y0,x1,y1) y la devuelve (sin pegar)."""
    x0, y0, x1, y1 = box
    s = min((x1 - x0) / img.width, (y1 - y0) / img.height)
    return img.resize(
        (max(1, int(img.width * s)), max(1, int(img.height * s))), Image.Resampling.LANCZOS
    )


def paste_center(canvas: Image.Image, img: Image.Image, box: tuple[int, int, int, int]):
    x0, y0, x1, y1 = box
    canvas.paste(img, (x0 + (x1 - x0 - img.width) // 2, y0 + (y1 - y0 - img.height) // 2))


# ------------------------------------------------------------- TUI renderer
CELL_W, CELL_H, FONT_CELL = 13, 26, 20
TERMINAL_BG = (11, 13, 16)
BORDER_CHARS = set(" │╭╰─┬┴├┤╮╯█▀")


@dataclass
class TuiFrame:
    name: str
    cols: int
    rows: int
    lines: list  # cada line: {"spans":[{"text","fg","bg","width"}]}

    @staticmethod
    def load(name: str) -> TuiFrame:
        d = json.loads((TUI_FRAMES / f"{name}.json").read_text())
        return TuiFrame(name, d["cols"], len(d["lines"]), d["lines"])

    def row_text(self, r: int) -> str:
        return "".join(s["text"] for s in self.lines[r]["spans"])

    def find(self, needle: str) -> int:
        for r, ln in enumerate(self.lines):
            if needle in "".join(s["text"] for s in ln["spans"]):
                return r
        return -1

    def col_of(self, needle: str) -> int:
        for r, ln in enumerate(self.lines):
            txt = "".join(s["text"] for s in ln["spans"])
            c = txt.find(needle)
            if c >= 0:
                return c
        return -1

    # --- estados de revelado -------------------------------------------------
    def blank_rows(self, r0: int, r1: int) -> TuiFrame:
        """Devuelve copia con filas r0..r1 en blanco (conserva bordes │ ╭ ╰ ─)."""
        import copy

        f = copy.deepcopy(self)
        for r in range(r0, min(r1 + 1, f.rows)):
            for s in f.lines[r]["spans"]:
                t = s["text"]
                if all(ch in " │╭╰─┬┴├┤" or ch == " " for ch in t):
                    continue  # es borde: conservar
                s["text"] = " " * len(t)
        return f

    def blank_panel_cols(self, r0: int, r1: int, c0: int, c1: int) -> TuiFrame:
        """Blank solo columnas c0..c1 en filas r0..r1 (para poblar paneles)."""
        import copy

        f = copy.deepcopy(self)
        for r in range(r0, min(r1 + 1, f.rows)):
            col = 0
            for s in f.lines[r]["spans"]:
                w = s["width"] or len(s["text"])
                if col >= c0 and col + w <= c1 + 1 and s["text"].strip():
                    if not all(ch in "│╭╰─┬┴├┤█▀" for ch in s["text"]):
                        s["text"] = " " * len(s["text"])
                col += w
        return f

    # --- render directo por viewport (nítido a cualquier zoom) ---------------
    def render_view(
        self,
        box: tuple[int, int, int, int],
        vp: tuple[float, float, float, float],
        row_states: dict | None = None,
        cursor_row: int | None = None,
        cursor_col: int | None = None,
    ) -> tuple[Image.Image, tuple[float, float]]:
        """Renderiza el viewport (c0,r0,c1,r1) ajustado a box, a resolución final.

        row_states: {row: 'blank' | ('partial', nchars) | ('cols', from_col)}
        Devuelve (imagen, (cw, ch)) con tamaño de celda en px.
        """
        row_states = row_states or {}
        c0, r0, c1, r1 = vp
        bw = box[2] - box[0]
        bh = box[3] - box[1]
        s = min(bw / ((c1 - c0) * CELL_W), bh / ((r1 - r0) * CELL_H))
        s = min(s, 2.9)  # tope de zoom
        cw, chh = CELL_W * s, CELL_H * s
        out_w = int((c1 - c0) * cw)
        out_h = int((r1 - r0) * chh)
        img = Image.new("RGB", (max(1, out_w), max(1, out_h)), TERMINAL_BG)
        d = ImageDraw.Draw(img)
        fsize = max(9, int(FONT_CELL * s))
        font = F(fsize, bold=False)
        # striping sutil: el interior vacío se lee como superficie, no como vacío
        for row in range(math.floor(r0), min(self.rows, math.ceil(r1))):
            if row % 2 == 0:
                d.rectangle(
                    [0, int((row - r0) * chh), out_w, int((row + 1 - r0) * chh)], fill=(13, 16, 21)
                )
        for row in range(math.floor(r0), min(self.rows, math.ceil(r1))):
            st = row_states.get(row, "full")
            if st == "blank":
                continue
            y = (row - r0) * chh
            col = 0
            cut_at = None
            blank_from = None
            if isinstance(st, tuple) and st[0] == "partial":
                cut_at = st[1]
            if isinstance(st, tuple) and st[0] == "cols":
                blank_from = st[1]
            for sp in self.lines[row]["spans"]:
                t = sp["text"]
                w = sp["width"] or len(t)
                if w <= 0 or col + w <= c0 or col >= c1:
                    col += w
                    continue
                vis = t
                if cut_at is not None:
                    vis = t[:cut_at]
                    if not vis:
                        break
                if blank_from is not None and col >= blank_from:
                    col += w
                    continue
                if col < c0 or col + len(vis) > c1:
                    cut_l = max(0, int(c0) - col)
                    cut_r = min(len(vis), int(math.ceil(c1)) - col)
                    if cut_r <= cut_l:
                        col += w
                        continue
                    vis = vis[cut_l:cut_r]
                x = (col - c0) * cw
                bg = tuple(int(cc * 255) for cc in sp["bg"][:3])
                if bg != TERMINAL_BG:
                    d.rectangle([x, y, x + len(vis) * cw - 1, y + chh - 1], fill=bg)
                if vis.strip():
                    fg = tuple(int(cc * 255) for cc in sp["fg"][:3])
                    d.text(
                        (x + 0.5 * cw * 0.08, y + (chh - fsize * 1.28) / 2), vis, fill=fg, font=font
                    )
                col += w
                if cut_at is not None:
                    break
            # cursor de tipeo
            if cursor_row == row and cursor_col is not None and (row in row_states):
                cx = (cursor_col - c0) * cw
                if 0 <= cx < out_w:
                    d.rectangle([cx, y + chh * 0.08, cx + cw, y + chh * 0.92], fill=(130, 175, 255))
        return img, (cw, chh)


def lerp_vp(a, b, k):
    k = clamp01(k)
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(4))


def paste_window(
    canvas: Image.Image, img: Image.Image, box, accent=(96, 124, 176)
) -> tuple[int, int, int, int]:
    """Pega la ventana del terminal: sombra, borde celeste marca y línea interior."""
    x0, y0, x1, y1 = box
    fx = x0 + (x1 - x0 - img.width) // 2
    fy = y0 + (y1 - y0 - img.height) // 2
    sh = Image.new("RGB", (img.width + 34, img.height + 34), (3, 4, 6))
    canvas.paste(sh, (fx - 17 + 8, fy - 17 + 12))
    canvas.paste(img, (fx, fy))
    d = ImageDraw.Draw(canvas)
    rrect(d, [fx - 4, fy - 4, fx + img.width + 4, fy + img.height + 4], 10, outline=accent, width=2)
    rrect(
        d,
        [fx - 1, fy - 1, fx + img.width + 1, fy + img.height + 1],
        8,
        outline=(44, 52, 64),
        width=1,
    )
    return (fx, fy, fx + img.width, fy + img.height)


# ------------------------------------------------------------------- guion
@dataclass
class Sent:
    text: str  # narración (TTS)
    cap: str  # subtítulo


@dataclass
class Scene:
    id: str
    badge: str
    title: str
    sents: list[Sent]
    render: object = None  # fn(t_local, scene, timeline) -> Image
    lead: float = 0.9
    tail: float = 0.9
    gap: float = 0.5


CHAPTERS = [
    "start",
    "privacy",
    "architecture",
    "answer",
    "create",
    "gate",
    "seal",
    "NEE",
    "bedrock",
    "close",
]

SCENES: list[Scene] = [
    Scene(
        "s1_hero",
        "Start",
        "tero · conversational teacher agent",
        [
            Sent(
                "This is tero: the conversational teacher agent for Chilean classrooms.",
                "tero · the conversational teacher agent for Chilean classrooms",
            ),
            Sent(
                "Tomorrow's photocopy, built from your own classroom folder. The agent proposes; the teacher decides.",
                "tomorrow's photocopy, from your own folder · the agent proposes, the teacher decides",
            ),
        ],
        lead=0.7,
        tail=0.8,
    ),
    Scene(
        "s2_priv",
        "Privacy",
        "your folder · the single source of truth",
        [
            Sent(
                "Your folder is the single source of truth: the story you read, the objective you marked, this week's vocabulary.",
                "your folder is the single source of truth",
            ),
            Sent(
                "And under Chile's Ley 21.719, student data never touches the cloud.",
                "Ley 21.719: student data never touches the cloud",
            ),
            Sent(
                "Everything stays on your machine, and nothing is written without your explicit approval.",
                "nothing is written without your explicit approval",
            ),
        ],
    ),
    Scene(
        "s3_arch",
        "Architecture",
        "Strands Multi-Agent Graph on Amazon Bedrock",
        [
            Sent(
                "Under the hood, tero orchestrates a Multi-Agent Graph with Strands Agents on Amazon Bedrock.",
                "Multi-Agent Graph · Strands Agents · Amazon Bedrock",
            ),
            Sent(
                "A pedagogical drafter prepares the material, and a quality auditor checks curriculum alignment.",
                "pedagogical drafter + curriculum quality auditor",
            ),
            Sent(
                "Nova Lite, GLM 4.7 Flash and MiniMax M2.5 run inference, with every turn traced in OpenTelemetry.",
                "Model Trio + OpenTelemetry traces on every turn",
            ),
            Sent(
                "Zero write tools for the model: the folder never leaves the machine.",
                "zero write tools · the folder never leaves",
            ),
        ],
    ),
    Scene(
        "s4_intent_a",
        "Intent A",
        "answer without writing",
        [
            Sent(
                "Write in natural Spanish and ask what is in the folder.",
                "ask in natural Spanish, no menus",
            ),
            Sent(
                "tero answers precisely: five sources, cited one by one. And it writes no files.",
                "precise answers · zero files written",
            ),
        ],
        lead=1.0,
    ),
    Scene(
        "s5_intent_b",
        "Intent B",
        "create material with verified citations",
        [
            Sent(
                "Ask it for a fourth-grade reading comprehension assessment.",
                "\u201cPrepara una evaluación de comprensión lectora para 4° básico\u201d",
            ),
            Sent(
                "tero discusses the details and builds the proposal in memory: summary, preview, and citations verified against your files.",
                "in-memory proposal · citations verified against your sources",
            ),
            Sent("Warnings inform; they never block.", "warnings inform · they never block"),
        ],
        lead=1.0,
    ),
    Scene(
        "s6_gate",
        "Approval gate",
        "approve and the handout is born",
        [
            Sent(
                "Nothing touches disk until you approve: press Y, or simply say dale.",
                "approve with [y] or \u201cdale\u201d · nothing is written before",
            ),
            Sent(
                "The host writes to derivados and compiles to LaTeX: the photocopy is ready for tomorrow.",
                "the host writes to derivados/ and compiles to LaTeX",
            ),
        ],
        lead=1.0,
    ),
    Scene(
        "s6b_seal",
        "Teacher seal",
        "cryptographic signature · proof of pedagogical agency",
        [
            Sent(
                "Here is what a chatbot does not have: every approved material leaves with a cryptographic seal in the teacher's name.",
                "every material, cryptographically sealed in your name",
            ),
            Sent(
                "The seal binds the hash of your sources, the derivative, the model, and the full trace: human-approved criterion in a local ledger.",
                "sources + derivative + model + trace hashes · .tero/decisiones/",
            ),
            Sent(
                "verify-seal checks integrity in seconds: a teacher approved this, with her sources, and nobody altered it.",
                "verify-seal · integrity verified in seconds",
            ),
        ],
        lead=1.0,
    ),
    Scene(
        "s7_nee",
        "Intent C",
        "NEE adaptation · Decreto 83",
        [
            Sent(
                "For a student with dyslexia, ask for the adaptation.",
                "\u201cAdapta la evaluación del cóndor para un estudiante con dislexia\u201d",
            ),
            Sent(
                "tero applies Decreto 83: access supports first, extended time and two-step instructions, before touching objectives.",
                "Decreto 83: access supports first, objectives later",
            ),
            Sent(
                "It delivers a new version with traceable origin. The original stays intact, hash-verified.",
                "new version with origin · the original stays intact",
            ),
        ],
        lead=1.0,
    ),
    Scene(
        "s8_trio",
        "Amazon Bedrock",
        "live model trio · honest tero-offline",
        [
            Sent(
                "Live diagnostics validate the Bedrock model trio.",
                "check-aws live · Amazon Bedrock Model Trio",
            ),
            Sent(
                "Nova Lite, fast and inexpensive; GLM 4.7 Flash, strict on NEE schemas; and MiniMax, with complete rubrics.",
                "Nova Lite · GLM 4.7 Flash · MiniMax M2.5",
            ),
            Sent(
                "And with no internet? tero-offline: a real Strands model, reproducible, never faking a cloud call.",
                "tero-offline: real Strands, never faking a cloud call",
            ),
        ],
    ),
    Scene(
        "s9_close",
        "Open source",
        "your classroom, your sources, your judgment",
        [
            Sent(
                "tero gives Sunday afternoons back to the people who teach.",
                "tero gives Sunday afternoons back to teachers",
            ),
            Sent(
                "And every material is signed in your name.", "every material, signed in your name"
            ),
            Sent(
                "Open source, MIT license, for the Agents for Humans Hackathon by AWS.",
                "MIT · open source · Agents for Humans Hackathon by AWS",
            ),
            Sent(
                "Your classroom, your sources, your judgment.",
                "tero · your classroom, your sources, your judgment",
            ),
        ],
    ),
]

VOICE = "en-US-AndrewNeural"
RATE = "+2%"
SEAL_ID = "tero-seal-9f2c4e7a1b0d"

# envolvente RMS real de la voz (por frame de video) para la onda del hero
ENV: list[float] = []


# --------------------------------------------------------------- audio TTS
async def tts_all(timeline):
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    import edge_tts

    for sc in SCENES:
        for i, s in enumerate(sc.sents):
            out = AUDIO_DIR / f"{sc.id}_{i}.mp3"
            if out.exists() and out.stat().st_size > 1000:
                continue
            c = edge_tts.Communicate(s.text, VOICE, rate=RATE)
            await c.save(str(out))
            print(f"  tts {out.name} ok")


def mp3_dur(path: Path) -> float:
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(r.stdout.strip())


def decode_mono(path: Path, sr=44100) -> np.ndarray:
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
        capture_output=True,
        check=True,
    )
    a = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return a


# ------------------------------------------------------------- timeline
OVERLAP = 0.6  # crossfade entre escenas


@dataclass
class Timeline:
    scene_starts: list[float]
    scene_durs: list[float]
    sent_abs: list[list[tuple[float, float]]]  # por escena: (start,end) absolutos
    total: float
    caps: list[tuple[float, float, str]]  # subtítulos absolutos
    voice_events: list[tuple[float, float]]  # ventanas con voz (para ducking)

    def scene_at(self, t: float) -> int:
        for i in range(len(self.scene_starts) - 1, -1, -1):
            if t >= self.scene_starts[i]:
                return i
        return 0


def build_timeline() -> Timeline:
    starts, durs, sent_abs, caps, voice = [], [], [], [], []
    cursor = 0.0
    for sc in SCENES:
        durs.append(0.0)  # placeholder
        starts.append(0.0)
        sent_abs.append([])
    for k, sc in enumerate(SCENES):
        start = cursor - (OVERLAP if k > 0 else 0.0)
        starts[k] = start
        t = start + sc.lead
        for i, s in enumerate(sc.sents):
            d = mp3_dur(AUDIO_DIR / f"{sc.id}_{i}.mp3")
            # tiempos LOCALES de la escena (los render reciben t local);
            # caps y voz siguen guardando tiempos absolutos.
            sent_abs[k].append((t - start, t - start + d))
            caps.append((t - 0.05, t + d + 0.25, s.cap))
            voice.append((t, t + d))
            t += d + sc.gap
        durs[k] = (t - start) + sc.tail
        cursor = start + durs[k]
    # envolvente aproximada por frase (RMS por frame) para la onda del hero
    if True:
        import json as _json

        sr = 44100
        cache_p = QC_DIR / "rms_cache.json"
        cache = _json.loads(cache_p.read_text()) if cache_p.exists() else {}
        dirty = False
        total_frames = int((cursor + 1.0) * FPS)
        env = np.zeros(total_frames, dtype=np.float32)
        for k2, sc2 in enumerate(SCENES):
            t2 = starts[k2] + sc2.lead
            for i2 in range(len(sc2.sents)):
                p = AUDIO_DIR / f"{sc2.id}_{i2}.mp3"
                d2 = mp3_dur(p)
                key = f"{sc2.id}_{i2}"
                if key not in cache:
                    arr = decode_mono(p, sr)
                    cache[key] = float(np.sqrt(np.mean(arr * arr))) if len(arr) else 0.0
                    dirty = True
                f0, f1 = int(t2 * FPS), int((t2 + d2) * FPS)
                env[f0:f1] = cache[key]
                t2 += d2 + sc2.gap
        if dirty:
            cache_p.write_text(_json.dumps(cache))
        env /= max(1e-6, float(env.max()))
        np.save(QC_DIR / "env.npy", env)
        ENV.clear()
        ENV.extend(float(x) for x in env)
    return Timeline(starts, durs, sent_abs, cursor, caps, voice)


# ------------------------------------------------------------- audio master
def build_voice_track(tl: Timeline, sr=44100) -> np.ndarray:
    total = int((tl.total + 1.0) * sr)
    track = np.zeros(total, dtype=np.float32)
    for k, sc in enumerate(SCENES):
        t = tl.scene_starts[k] + sc.lead
        for i in range(len(sc.sents)):
            a = decode_mono(AUDIO_DIR / f"{sc.id}_{i}.mp3", sr)
            i0 = int(t * sr)
            i1 = min(total, i0 + len(a))
            track[i0:i1] += a[: i1 - i0]
            d = mp3_dur(AUDIO_DIR / f"{sc.id}_{i}.mp3")
            t += d + sc.gap
    peak = np.max(np.abs(track)) or 1.0
    track *= 0.89 / peak
    # envolvente RMS por frame (para la onda del hero)
    sr = 44100
    spf = sr // FPS
    n_frames = len(track) // spf
    env = np.zeros(n_frames, dtype=np.float32)
    for i in range(n_frames):
        seg = track[i * spf : (i + 1) * spf]
        env[i] = float(np.sqrt(np.mean(seg * seg))) if len(seg) else 0.0
    env /= max(1e-6, float(env.max()))
    np.save(QC_DIR / "env.npy", env)
    return track


def build_music(total: float, voice: np.ndarray, sr=44100) -> np.ndarray:
    """Pad ambiental sutil: Am9 → Fmaj9 → Cmaj9 → G6, con ducking por voz."""
    n = len(voice)  # misma longitud que la voz para el ducking
    t = np.arange(n) / sr
    chords = [
        [110.0, 164.81, 220.0, 246.94, 329.63],
        [87.31, 174.61, 220.0, 261.63, 349.23],
        [130.81, 196.0, 261.63, 293.66, 392.0],
        [98.0, 196.0, 246.94, 293.66, 392.0],
    ]
    seg = 7.5
    music = np.zeros(n, dtype=np.float32)
    period = seg * len(chords)
    for i, ch in enumerate(chords):
        # posición de este acorde dentro del loop
        seg_start = i * seg
        idx = (t - seg_start) % period
        mask = (idx >= 0) & (idx < seg)
        if not mask.any():
            continue
        tt = idx[mask]
        env = np.clip(tt / 2.0, 0, 1) * np.clip((seg - tt) / 2.0, 0, 1)
        env = env * env * (3 - 2 * env)
        seg_w = np.zeros(len(tt), dtype=np.float32)
        for f in ch:
            for det, amp in ((0.9985, 0.5), (1.0015, 0.5)):
                ph = 2 * np.pi * f * det * (tt + seg_start)
                seg_w += amp * (np.sin(ph) + 0.35 * np.sin(2 * ph)) / len(ch)
        music[mask] += (seg_w * env).astype(np.float32)
    # low-pass: media móvil (filtro suave, rápido en numpy)
    k = 34
    lp = np.convolve(music, np.ones(k) / k, mode="same")
    lp /= max(1e-6, np.max(np.abs(lp)))
    # ducking por voz
    duck = np.zeros(n, dtype=np.float32)
    act = (np.abs(voice) > 0.02).astype(np.float32)
    kernel = np.ones(int(0.35 * sr)) / int(0.35 * sr)
    if len(kernel) < n:
        duck = np.convolve(act, kernel, mode="same")
    music_gain = 0.30 * (1.0 - 0.72 * np.clip(duck, 0, 1))
    pad = lp * music_gain
    # fade global
    fade_in = int(1.2 * sr)
    fade_out = int(3.0 * sr)
    pad[:fade_in] *= np.linspace(0, 1, fade_in)
    pad[-fade_out:] *= np.linspace(1, 0, fade_out)
    return pad


def write_wav_stereo(path: Path, left: np.ndarray, right: np.ndarray, sr=44100):
    data = np.stack([left, right], axis=1)
    pcm = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# --------------------------------------------------------------- chrome UI
TOP_H = 62
CAP_H = 96


def top_bar(draw: ImageDraw.ImageDraw, scene: Scene, chapter_idx: int):
    draw.rectangle([0, 0, W, TOP_H], fill=PANEL)
    draw.line([0, TOP_H, W, TOP_H], fill=(40, 46, 56), width=2)
    ctext(draw, (36, 16), "tero", fill=ACC, font=F(26, True))
    ctext(draw, (100, 22), "·  conversational teacher agent", fill=MUT, font=F(16))
    f_badge = F(14, True)
    x = W - 36
    for label, col in (
        ("OpenTUI", (188, 140, 255)),
        ("Strands Agents", ACC),
        ("AWS Bedrock", WARN),
    ):
        bw = text_w(f_badge, label) + 22
        x -= bw + 8
        rrect(draw, [x, 16, x + bw, 44], 6, fill=(18, 22, 28), outline=col, width=1)
        ctext(draw, (x + 11, 21), label, fill=col, font=f_badge)
    f_ctx = F(17, True)
    title = f"{scene.badge.upper()}  ·  {scene.title}"
    tw = text_w(f_ctx, title)
    ctext(draw, ((W - tw) // 2, 20), title, fill=TXT, font=f_ctx)


def chapter_bar(canvas: Image.Image, t_global: float, total: float):
    draw = ImageDraw.Draw(canvas)
    y0 = H - 8
    draw.rectangle([0, y0 - 2, W, H], fill=PANEL)
    n = len(CHAPTERS)
    seg = W / n
    prog = clamp01(t_global / total)
    draw.rectangle([0, y0 - 2, int(W * prog), H], fill=(64, 88, 140))
    f = F(13, True)
    for i, name in enumerate(CHAPTERS):
        cx = int(seg * i + seg / 2)
        col = TXT if t_global / total >= i / n else MUT
        ctext(draw, (cx, y0 - 22), name, fill=col, font=f, anchor="ma")
        draw.rectangle([int(seg * i), y0 - 2, int(seg * i), H], fill=(40, 46, 56))


Timeline_current_scene = [0]


def caption_card(canvas: Image.Image, text: str):
    draw = ImageDraw.Draw(canvas)
    f = F(29, True)
    box_w, box_h = 1560, CAP_H
    x0 = (W - box_w) // 2
    y0 = H - CAP_H - 26
    rrect(
        draw, [x0, y0, x0 + box_w, y0 + box_h], 12, fill=(16, 19, 24), outline=(48, 56, 68), width=2
    )
    draw.line([x0 + 14, y0 + 2, x0 + box_w - 14, y0 + 2], fill=ACC, width=3)
    # wrap 2 líneas máx
    words = text.split()
    lines, cur = [], []
    for w_ in words:
        cur.append(w_)
        if text_w(f, " ".join(cur)) > box_w - 90:
            cur.pop()
            lines.append(" ".join(cur))
            cur = [w_]
    if cur:
        lines.append(" ".join(cur))
    y = y0 + (box_h - len(lines) * 38) // 2 - 2
    for ln in lines[:2]:
        ctext(draw, ((W - text_w(f, ln)) // 2, y), ln, fill=TXT, font=f)
        y += 38


MARK = Image.open(SITE_ASSETS / "tero-mark-1024.png").convert("RGBA")


def pulse_alpha(t: float, period=1.1) -> float:
    return 0.5 + 0.5 * math.sin(2 * math.pi * t / period)


def highlight(canvas: Image.Image, box, t: float, color=ACC):
    """Marco pulsante + glow suave alrededor de box (px)."""
    a = pulse_alpha(t)
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(
        [x0 - 6, y0 - 6, x1 + 6, y1 + 6], radius=10, outline=(*color, int(120 + 110 * a)), width=4
    )
    glow = ov.filter(ImageFilter.GaussianBlur(6))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), glow).convert("RGB"), (0, 0))
    d2 = ImageDraw.Draw(canvas)
    d2.rounded_rectangle([x0 - 6, y0 - 6, x1 + 6, y1 + 6], radius=10, outline=color, width=3)


# ============================================================ ESCENAS (render)
# cada render: (t_local, sc, tl) -> Image 1920x1080 (sin caption ni chapter bar)


_CANVAS_BASE: Image.Image | None = None


def base_canvas() -> Image.Image:
    """Fondo con dot-grid sutil: ninguna zona se lee como vacío negro."""
    global _CANVAS_BASE
    if _CANVAS_BASE is None:
        img = Image.new("RGB", (W, H), (14, 17, 22))
        d = ImageDraw.Draw(img)
        for yy in range(24, H, 30):
            for xx in range(24, W, 30):
                d.point((xx, yy), fill=(26, 32, 41))
        vg = Image.new("L", (W, H), 0)
        dv = ImageDraw.Draw(vg)
        dv.ellipse([-260, -200, W + 260, H + 200], fill=70)
        vg = vg.filter(ImageFilter.GaussianBlur(200))
        dark = Image.new("RGB", (W, H), (8, 10, 13))
        _CANVAS_BASE = Image.composite(img, dark, vg.point(lambda p: 70 + p))
    return _CANVAS_BASE.copy()


# ---- S1 hero ---------------------------------------------------------------
BADGES_S1 = [
    ("Teacher cryptographic seal", ACC),
    ("Grafo Multi-Agente", OK),
    ("Amazon Bedrock", WARN),
    ("Strands Agents SDK", (188, 140, 255)),
]


def render_s1(t, sc, tl):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    sent = tl.sent_abs[0]
    # ---- columna izquierda: marca + discurso
    mh = 250
    rev = ease(clamp01(t / 0.9))
    m = MARK.resize((mh, mh), Image.Resampling.LANCZOS)
    m_part = m.crop((0, 0, mh, max(1, int(mh * rev))))
    bob = 5 * math.sin(2 * math.pi * 0.22 * t)
    halo = Image.new("RGBA", (mh + 140, mh + 140), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([45, 45, mh + 95, mh + 95], fill=(*ACC, 24))
    halo = halo.filter(ImageFilter.GaussianBlur(26))
    img.paste(halo, (130 - 70, int(170 + bob) - 70), halo)
    img.paste(m_part, (130, int(170 + bob)), m_part)
    ctext(d, (130, 448 + bob * 0.3), "Vanellus chilensis · the tero bird", fill=MUT, font=F(19))
    if t > 0.35:
        d.text((126, 500), "tero", fill=ACC, font=F(104, True))
    if t > 0.75:
        d.text((130, 638), "your sources, your judgment", fill=TXT, font=F(36, True))
        ctext(d, (130, 696), "The tero alerts. You decide.", fill=MUT, font=F(23))
    # badges desde el fin de la frase 1
    bx, by = 130, 760
    for i, (label, col) in enumerate(BADGES_S1):
        app_t = (sent[0][1] - 0.3 if sent else 4.0) + i * 0.24
        a = ease(clamp01((t - app_t) / 0.4))
        if a <= 0:
            continue
        fb = F(20, True)
        bw = text_w(fb, label) + 30
        off = (1 - a) * 14
        rrect(d, [bx, by + off, bx + bw, by + 42 + off], 9, fill=(17, 21, 27), outline=col, width=2)
        ctext(d, (bx + 15, by + 8 + off), label, fill=col, font=fb)
        bx += bw + 12
        if bx > 880:
            bx, by = 130, by + 52
    # onda con la envolvente REAL de la voz (historial desplazante)
    fidx = int(t * FPS)
    nb = 46
    base_y = 936
    for i in range(nb):
        fi = fidx - (nb - 1 - i)
        lvl = ENV[fi] if 0 <= fi < len(ENV) else 0.0
        hh = 3 + 44 * min(1.0, lvl * 1.35)
        xw = 130 + i * 17
        col = ACC if i > nb - 6 else (58, 74, 96)
        d.rounded_rectangle([xw, base_y - hh, xw + 9, base_y], radius=3, fill=col)
    # ---- columna derecha: mini-terminal real del producto
    a_in = ease(clamp01((t - 0.5) / 0.8))
    if a_in > 0 and "FR_A" in globals():
        term, _ = FR_A.render_view((960, 170, 1880, 700), (0, 0, 115, 12.5))
        tw_ = int(term.width * (0.95 + 0.05 * a_in))
        th_ = int(term.height * (0.95 + 0.05 * a_in))
        term = term.resize((tw_, th_), Image.Resampling.LANCZOS)
        glow = Image.new("RGB", (tw_ + 56, th_ + 56), (9, 12, 16))
        img.paste(glow, (960 + (920 - tw_) // 2 + 12, 170 + (530 - th_) // 2 + 16))
        tx0 = 960 + (920 - tw_) // 2
        ty0 = 170 + (530 - th_) // 2
        img.paste(term, (tx0, ty0))
        dd = ImageDraw.Draw(img)
        rrect(
            dd,
            [tx0 - 4, ty0 - 4, tx0 + tw_ + 4, ty0 + th_ + 4],
            10,
            outline=(96, 124, 176),
            width=2,
        )
        rrect(
            dd, [tx0 - 1, ty0 - 1, tx0 + tw_ + 1, ty0 + th_ + 1], 8, outline=(44, 52, 64), width=1
        )
        ctext(
            dd,
            (tx0 + tw_ // 2, ty0 + th_ + 18),
            "carpeta-demo · OpenTUI · the real product",
            fill=MUT,
            font=F(19),
            anchor="ma",
        )
    return img


# ---- S2 privacidad -----------------------------------------------------------
PRIN = [
    (
        "1 · YOUR FOLDER",
        "The story you read, the marked objective, the week's vocabulary: the only source of truth.",
        ACC,
    ),
    ("2 · LEY 21.719", "Grades, health and attendance never leave your machine.", OK),
    (
        "3 · YOUR APPROVAL",
        "The agent proposes in memory. Nothing is written without your 'y' or your 'dale'.",
        WARN,
    ),
]


def render_s2(t, sc, tl):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    sent = tl.sent_abs[1]
    cw, chh = 560, 560
    y0 = 150
    for i, (title, desc, col) in enumerate(PRIN):
        appear = 0.25 + i * 0.18  # el marco existe de inmediato
        activate = sent[i][0] - 0.55  # el contenido entra con su frase
        a = ease(clamp01((t - appear) / 0.4))
        act = ease(clamp01((t - activate) / 0.5))
        x0 = 80 + i * (cw + 40)
        y_off = (1 - a) * 36
        card = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        rrect(
            cd,
            [0, 0, cw, chh],
            18,
            fill=(*PANEL, int(255 * a)),
            outline=(*col, int(255 * a)),
            width=3,
        )
        cd.line([24, 3, cw - 24, 3], fill=(*col, int(230 * a)), width=4)
        cd.text((34, 46), title, fill=(*col, int(120 + 135 * act)), font=F(34, True))
        # glifo geométrico (opacidad según activación)
        gx, gy = cw // 2, 210
        if i == 0:  # carpeta
            cd.rounded_rectangle(
                [gx - 90, gy - 60, gx + 90, gy + 60],
                12,
                outline=(*col, int(125 + 130 * act)),
                width=5,
            )
            cd.rounded_rectangle(
                [gx - 90, gy - 60, gx - 10, gy - 20],
                8,
                outline=(*col, int(125 + 130 * act)),
                width=5,
            )
        elif i == 1:  # escudo
            cd.polygon(
                [
                    (gx, gy - 70),
                    (gx + 80, gy - 40),
                    (gx + 80, gy + 20),
                    (gx, gy + 75),
                    (gx - 80, gy + 20),
                    (gx - 80, gy - 40),
                ],
                outline=(*col, int(125 + 130 * act)),
                width=5,
            )
            cd.line(
                [(gx - 26, gy + 2), (gx - 6, gy + 26), (gx + 34, gy - 24)],
                fill=(*col, int(125 + 130 * act)),
                width=8,
                joint="curve",
            )
        else:  # compuerta
            cd.rounded_rectangle(
                [gx - 70, gy - 62, gx + 70, gy + 62],
                10,
                outline=(*col, int(125 + 130 * act)),
                width=5,
            )
            cd.line(
                [(gx - 70, gy - 8), (gx + 70, gy - 8)], fill=(*col, int(125 + 130 * act)), width=5
            )
            cd.text(
                (gx, gy + 16),
                "[y]",
                fill=(*TXT, int(125 + 130 * act)),
                font=F(34, True),
                anchor="ma",
            )
        words, lines_n, cur = desc.split(), [], []
        fd = F(23)
        for w_ in words:
            cur.append(w_)
            if text_w(fd, " ".join(cur)) > cw - 70:
                cur.pop()
                lines_n.append(" ".join(cur))
                cur = [w_]
        lines_n.append(" ".join(cur))
        yy = 330
        for ln in lines_n:
            cd.text((34, yy), ln, fill=(*TXT, int(105 + 130 * act)), font=fd)
            yy += 34
        img.paste(card, (x0, int(y0 + y_off)), card)
    # activo: pulso
    idx = (
        2
        if len(sent) > 2 and t >= sent[2][0] - 0.3
        else (1 if len(sent) > 1 and t >= sent[1][0] - 0.3 else 0)
    )
    x0 = 80 + idx * (cw + 40)
    a = pulse_alpha(t)
    d.rounded_rectangle(
        [x0 - 5, y0 - 5, x0 + cw + 5, y0 + chh + 5],
        20,
        outline=(*PRIN[idx][2], int(90 + 90 * a)),
        width=3,
    )
    return img


# ---- S3 arquitectura ---------------------------------------------------------
ARCH = Image.open(HACK / "architecture.png").convert("RGB")
CHIPS = [
    ("Strands Multi-Agent Graph", "GraphBuilder · drafter + auditor", ACC),
    ("Amazon Bedrock · Model Trio", "Nova Lite · GLM 4.7 · MiniMax", WARN),
    ("OpenTelemetry", "StrandsTelemetry · every turn traced", (188, 140, 255)),
    ("In-memory approval gate", "zero write tools · host writes", OK),
]


def render_s3(t, sc, tl):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    sent = tl.sent_abs[2]
    # imagen con ken burns sutil
    s = 1.0 + 0.045 * clamp01(t / 12.0)
    iw, ih = int(1600 * s), int((880 * 1600 / 1680) * s)
    ai = ARCH.resize((iw, ih), Image.Resampling.LANCZOS)
    box = (40, 100, 1636, 994)
    fit_ai = fit(ai, box)
    fx = 40 + (1620 - fit_ai.width) // 2
    fy = 100 + (894 - fit_ai.height) // 2
    rrect(
        d,
        [fx - 8, fy - 8, fx + fit_ai.width + 8, fy + fit_ai.height + 8],
        12,
        fill=(16, 19, 24),
        outline=(48, 56, 68),
        width=2,
    )
    img.paste(fit_ai, (fx, fy))
    # columna derecha de chips (título con wrap: nunca desborda)
    cx0, chip_w = 1664, 236
    cy = 120
    for i, (title, sub, col) in enumerate(CHIPS):
        appear = sent[min(i, len(sent) - 1)][0] - 0.4
        a = ease(clamp01((t - appear) / 0.45))
        if a <= 0:
            cy += 210
            continue
        off = (1 - a) * 24
        rrect(
            d,
            [cx0, cy + off, cx0 + chip_w, cy + 178 + off],
            12,
            fill=(16, 19, 24),
            outline=col,
            width=2,
        )
        d.line([cx0 + 12, cy + 2 + off, cx0 + chip_w - 12, cy + 2 + off], fill=col, width=3)
        ft = F(16, True)
        twords, tcur, tlines = title.split(), [], []
        for w_ in twords:
            tcur.append(w_)
            if text_w(ft, " ".join(tcur)) > chip_w - 28:
                tcur.pop()
                tlines.append(" ".join(tcur))
                tcur = [w_]
        tlines.append(" ".join(tcur))
        yy = cy + 14 + off
        for ln in tlines[:2]:
            d.text((cx0 + 14, yy), ln, fill=col, font=ft)
            yy += 21
        words, cur, lines_n = sub.split(), [], []
        fs = F(15)
        for w_ in words:
            cur.append(w_)
            if text_w(fs, " ".join(cur)) > chip_w - 28:
                cur.pop()
                lines_n.append(" ".join(cur))
                cur = [w_]
        lines_n.append(" ".join(cur))
        yy = max(yy + 6, cy + 62 + off)
        for ln in lines_n[:4]:
            d.text((cx0 + 14, yy), ln, fill=TXT, font=fs)
            yy += 24
        cy += 210
    return img


# ---- S4 intención A ----------------------------------------------------------
FR_A = TuiFrame.load("respuesta")
VP_FULL = (0, 0, 140, 40)
VP_A_TYPE = (0, 0, 92, 12.5)
VP_A_REPLY = (0, 2.2, 86, 11.2)


def render_s4(t, sc, tl):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    sent = tl.sent_abs[3]
    r_tu = FR_A.find("¿Qué tengo")
    r_rep0 = FR_A.find("Cinco fuentes")
    r_rep1 = r_rep0 + 1
    r_of = FR_A.find("Puedo responder")

    TYPE_START, TYPE_SPEED = 1.35, 30.0
    msg = "¿Qué tengo en la carpeta?"
    typing_end = TYPE_START + len(msg) / TYPE_SPEED + 0.5
    rep_start = max(typing_end + 0.3, sent[1][0] - 0.1) if len(sent) > 1 else typing_end + 0.5

    states: dict = {}
    cur_row = cur_col = None
    typed = clamp01((t - TYPE_START) * TYPE_SPEED / len(msg))
    if t < TYPE_START:
        states[r_tu] = "blank"
    elif t < typing_end:
        n = int(len(msg) * typed)
        states[r_tu] = ("partial", 3 + n)  # ││ + espacio antes del texto
        if (t * 2.6) % 1 < 0.6:
            cur_row, cur_col = r_tu, 3 + n
    if t < rep_start + 0.15:
        states[r_rep0] = "blank"
        states[r_rep1] = "blank"
    if len(sent) > 1 and t < sent[1][1] - 0.9:
        states[r_of] = "blank"

    # viewport guiado
    if t < 1.5:
        vp = lerp_vp((0, 0, 108, 13.5), VP_A_TYPE, ease((t - 0.3) / 1.0))
    elif t < rep_start + 0.5:
        vp = VP_A_TYPE
    else:
        vp = lerp_vp(VP_A_TYPE, VP_A_REPLY, ease((t - rep_start - 0.5) / 0.9))

    term, _ = FR_A.render_view((60, 92, 1860, 944), vp, states, cur_row, cur_col)
    win = paste_window(img, term, (60, 92, 1860, 944))
    if len(sent) > 1 and t > sent[1][1] - 1.6:
        a = pulse_alpha(t)
        rrect(
            d,
            [win[0] + 16, win[3] - 118, win[0] + 620, win[3] - 26],
            10,
            outline=OK,
            width=3 + int(2 * a),
        )
        ctext(
            d,
            (win[2] - 24, win[3] - 96),
            "0 archivos escritos",
            fill=OK,
            font=F(26, True),
            anchor="ra",
        )
    return img


# ---- S5 intención B ----------------------------------------------------------
FR_B = TuiFrame.load("propuesta")
VP_B_CONV = (0, 2.2, 56, 12.5)
VP_B_ALL = (0, 2, 140, 30)
VP_B_PROP = (49, 2.5, 106, 26.5)
VP_B_EVID = (96.5, 2.5, 140, 14.5)


def render_s5(t, sc, tl):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    sent = tl.sent_abs[4]
    r_tu0 = FR_B.find("Prepara una evaluación")
    r_hist_end = FR_B.find("Sí, con pauta") + 2
    panel_c0 = 52
    r_panel_end = 37
    s1s = sent[0][0]
    s2s = sent[1][0] if len(sent) > 1 else s1s + 5
    s2e = sent[1][1] if len(sent) > 1 else s2s + 5
    s3s = sent[2][0] if len(sent) > 2 else s2e + 1

    states: dict = {}
    ph = clamp01((t - 0.6) / 1.3)
    n_hist = r_hist_end - r_tu0
    vis_hist = int(n_hist * ph)
    for i in range(n_hist):
        if i >= vis_hist:
            states[r_tu0 + i] = "blank"
    pp = clamp01((t - (s2s - 0.15)) / 2.4)
    vis_pan = int((r_panel_end - 4) * pp)
    for r in range(4, r_panel_end):
        if r - 4 >= vis_pan and t < s2e - 0.2:
            states[r] = ("cols", panel_c0)

    if t < s2s + 0.6:
        vp = lerp_vp((0, 0, 118, 20), VP_B_CONV, ease((t - 0.5) / 1.1))
    elif t < s2s + 1.8:
        vp = lerp_vp(VP_B_CONV, VP_B_PROP, ease((t - (s2s + 0.6)) / 1.2))
    elif t < s2e:
        vp = VP_B_PROP
    elif t < s3s + 0.4:
        vp = lerp_vp(VP_B_PROP, VP_B_ALL, ease((t - s2e) / 0.9))
    elif t < s3s + 1.2:
        vp = VP_B_ALL
    else:
        vp = lerp_vp(VP_B_ALL, VP_B_EVID, ease((t - (s3s + 1.2)) / 0.9))

    term, _ = FR_B.render_view((60, 92, 1860, 944), vp, states)
    win = paste_window(img, term, (60, 92, 1860, 944))
    if t > s3s + 0.2:
        a = pulse_alpha(t)
        rrect(
            d,
            [win[0] + 12, win[1] + 10, win[2] - 12, win[1] + int((win[3] - win[1]) * 0.42)],
            12,
            outline=OK,
            width=3 + int(2 * a),
        )
        ctext(
            d,
            (win[2] - 20, win[1] - 34),
            "✓ verificada contra fuentes/cuento-el-condor-y-el-huemul.md",
            fill=OK,
            font=F(23, True),
            anchor="ra",
        )
    return img


# ---- S6 compuerta ------------------------------------------------------------
FR_C = TuiFrame.load("escrito")
VP_C = (0, 1.5, 54, 16.5)
HOJA = Image.open(HOJAS / "eval-cuento" / "p1.png").convert("RGB")


def render_s6(t, sc, tl):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    sent = tl.sent_abs[5]
    approved_t = sent[0][1] + 0.15
    r_esc_panel = FR_C.find("escrito · crear")
    r_esc_conv = FR_C.find("·   escrito · crear")
    states: dict = {}
    if t < approved_t:
        states[r_esc_panel] = "blank"
        states[r_esc_panel + 1] = "blank"
        states[r_esc_conv] = "blank"
        states[r_esc_conv + 1] = "blank"
    term, _ = FR_C.render_view((50, 100, 1010, 745), VP_C, states)
    # barra de aprobación (string real del producto) bajo la ventana
    bar_y = 770
    a = pulse_alpha(t, 0.85) if t < approved_t else 0.0
    col_bar = WARN if t < approved_t else OK
    rrect(
        d,
        [50, bar_y, 1010, bar_y + 64],
        10,
        fill=(13, 16, 21),
        outline=col_bar,
        width=3 if t < approved_t else 2,
    )
    if t < approved_t:
        d.text((74, bar_y + 18), "¿escribo el archivo?", fill=TXT, font=F(24, True))
        d.text((74 + 320, bar_y + 18), "[y] aprobar", fill=col_bar, font=F(24, True))
        d.text((74 + 320 + 220, bar_y + 18), "[n] descartar", fill=MUT, font=F(24, True))
        if a > 0.5:
            rrect(
                d, [74 + 312, bar_y + 10, 74 + 312 + 200, bar_y + 56], 8, outline=col_bar, width=3
            )
    else:
        d.text((74, bar_y + 18), "aprobado · host escribe · derivados/", fill=OK, font=F(24, True))
        d.text((74 + 560, bar_y + 18), "LaTeX ✓", fill=WARN, font=F(24, True))
        if t > approved_t + 1.1:
            d.text(
                (74, bar_y + 44),
                f"sello docente: {SEAL_ID} · registrado en .tero/decisiones/",
                fill=ACC,
                font=F(21, True),
            )
    # derecha: hoja fotocopia con scale-in
    appear = sent[1][0] - 0.55 if len(sent) > 1 else approved_t + 1.0
    aa = clamp01((t - appear) / 0.7)
    if aa > 0:
        e = 1.0 - (1.0 - aa) * (1.0 - aa)
        pop = 1.0 + 0.05 * math.sin(min(1.0, aa) * math.pi)
        hoja = fit(HOJA, (1080, 130, 1856, 900))
        hoja = hoja.resize(
            (max(1, int(hoja.width * e * pop)), max(1, int(hoja.height * e * pop))),
            Image.Resampling.LANCZOS,
        )
        hoja = hoja.rotate(-1.6, expand=True, resample=Image.Resampling.BICUBIC, fillcolor=PAPER)
        hx = 1080 + (776 - hoja.width) // 2
        hy = 130 + (770 - hoja.height) // 2
        paper = Image.new("RGB", (hoja.width + 22, hoja.height + 22), PAPER)
        img.paste(paper, (hx - 11 + 5, hy - 11 + 10))
        img.paste(hoja, (hx, hy))
        d.rectangle(
            [hx - 11, hy - 11, hx + hoja.width + 11, hy + hoja.height + 11], outline=WARN, width=2
        )
        ctext(
            d,
            (hx + hoja.width // 2, hy + hoja.height + 24),
            "handout ready · LaTeX · sealed footer",
            fill=WARN,
            font=F(23, True),
            anchor="ma",
        )
    return img


# ---- S7 NEE ------------------------------------------------------------------
FR_D = TuiFrame.load("propuesta-adaptar")
FR_D2 = TuiFrame.load("escrito-adaptar")
VP_D_CONV = (0, 0, 56, 14.5)
VP_D_PROP = (50, 2.5, 104, 26.5)
VP_D_ALL = (0, 2, 140, 38.5)


def render_s7(t, sc, tl):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    sent = tl.sent_abs[6]
    s2s = sent[1][0] if len(sent) > 1 else 5.0
    s3s = sent[2][0] if len(sent) > 2 else s2s + 5.0
    switch_t = s3s - 0.4

    panel_c0 = 52
    states: dict = {}
    pp = clamp01((t - 1.1) / 1.7)
    for r in range(4, 34):
        if (r - 4) / 30.0 >= pp and t < switch_t:
            states[r] = ("cols", panel_c0)

    if t < s2s + 0.6:
        vp = lerp_vp((0, 0, 116, 20), VP_D_CONV, ease((t - 0.4) / 0.9))
    elif t < s2s + 1.8:
        vp = lerp_vp(VP_D_CONV, VP_D_PROP, ease((t - (s2s + 0.6)) / 1.2))
    elif t < s3s + 0.4:
        vp = VP_D_PROP
    else:
        vp = lerp_vp(VP_D_PROP, (0, 2.2, 56, 12.8), ease((t - (s3s + 0.4)) / 0.9))

    term1, _ = FR_D.render_view((60, 92, 1860, 944), vp, states)
    alpha = clamp01((t - switch_t) / 0.5)
    if alpha > 0:
        term2, _ = FR_D2.render_view((60, 92, 1860, 944), vp, None)
        term = Image.blend(term1, term2, ease(alpha))
    else:
        term = term1
    win = paste_window(img, term, (60, 92, 1860, 944))
    if len(sent) > 2 and t > s3s + 0.3:
        a = pulse_alpha(t)
        ctext(
            d,
            (win[2] - 20, win[1] - 34),
            "origen: trazable · original intacto (SHA-256)",
            fill=ACC,
            font=F(23, True),
            anchor="ra",
        )
        oy = win[1] + int((win[3] - win[1]) * 0.52)
        rrect(
            d,
            [win[0] + 14, oy, win[2] - 14, oy + int((win[3] - win[1]) * 0.14)],
            8,
            outline=ACC,
            width=2 + int(2 * a),
        )
    return img


# ---- S8 trío Bedrock ---------------------------------------------------------
MODELS = [
    ("amazon.nova-lite-v1:0", 1.04, "primary model · fast, low cost", ACC),
    ("zai.glm-4.7-flash", 0.33, "NEE schemas · strict Decreto 83", OK),
    ("minimax.minimax-m2.5", 9.72, "complete rubrics and grids", (188, 140, 255)),
    ("tero-offline (scripted)", 0.01, "offline · real Strands · reproducible", WARN),
]


def render_s8(t, sc, tl):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    sent = tl.sent_abs[8]
    bx, by, bw, bh = 140, 100, 1640, 810
    rrect(d, [bx, by, bx + bw, by + bh], 14, fill=(13, 16, 21), outline=(52, 60, 72), width=2)
    d.rectangle([bx + 3, by + 3, bx + bw - 3, by + 42], fill=(16, 19, 24))
    for i, c in enumerate((ERR, WARN, OK)):
        d.ellipse([bx + 22 + i * 34, by + 15, bx + 38 + i * 34, by + 31], fill=c)
    ctext(d, (bx + 140, by + 13), "python -m tero check-aws --all-models", fill=MUT, font=F(21))
    # tipeo del comando
    cmd = "$ python -m tero check-aws --all-models"
    n = len(cmd)
    typed = int(clamp01((t - 0.55) / 1.15) * n)
    ctext(
        d,
        (bx + 40, by + 70),
        cmd[:typed] + ("▌" if (t * 2.6) % 1 < 0.55 and typed < n else ""),
        fill=TXT,
        font=F(26, True),
    )
    run_t = 1.9
    d.line([bx + 40, by + 124, bx + bw - 40, by + 124], fill=(40, 46, 56), width=1)
    my = by + 150
    f_name = F(25, True)
    f_desc = F(20)
    for i, (name, lat, desc, col) in enumerate(MODELS):
        appear = 0.9 + i * 0.22  # fila visible desde temprano (dim)
        active = run_t + 0.5 + i * 0.85  # spinner→✓ con su momento
        a = ease(clamp01((t - appear) / 0.4))
        if a <= 0:
            my += 108
            continue
        y = my + (1 - a) * 14
        act = clamp01((t - active) / 0.2)
        if act > 0 and t < active + 0.45:
            spin = "◐◓◑◒"[int(t * 8) % 4]
            d.text((bx + 44, y), spin, fill=col, font=f_name)
        elif act > 0:
            d.text((bx + 44, y), "✓", fill=col, font=F(27, True))
        else:
            d.text((bx + 44, y), "·", fill=(90, 100, 112), font=F(27, True))
        d.text((bx + 96, y), name, fill=(*col[:3],) if act > 0 else (128, 138, 150), font=f_name)
        # latencia contando
        lv = lat * ease(clamp01((t - appear - 0.35) / 0.55))
        lat_txt = f"{lv:0.2f}s" if lat > 0.05 else "<10ms"
        rrect(d, [bx + 620, y - 4, bx + 740, y + 34], 6, fill=(20, 24, 30), outline=col)
        ctext(
            d,
            (bx + 680, y + 3),
            lat_txt if lv > 0 else "…",
            fill=col,
            font=F(21, True),
            anchor="ma",
        )
        d.text((bx + 770, y + 4), desc, fill=TXT, font=f_desc)
        my += 108
    # franja resultado
    res_t = run_t + 0.5 + 4 * 0.85 + 0.5
    a = ease(clamp01((t - res_t) / 0.5))
    if a > 0:
        yy = by + 620
        rrect(
            d,
            [bx + 40, yy, bx + bw - 40, yy + 92],
            10,
            fill=(16, 19, 24),
            outline=(40, 46, 56),
            width=1,
        )
        ctext(
            d,
            (bx + 64, yy + 18),
            "5 models · 4 real teaching journeys · benchmark in the repo",
            fill=TXT,
            font=F(23),
        )
        ctext(
            d,
            (bx + 64, yy + 54),
            "honest demo: offline = tero-offline, never a faked Bedrock call",
            fill=MUT,
            font=F(20),
        )
    # pulso en tero-offline con sentencia 3
    if len(sent) > 2 and t > sent[2][0] - 0.15:
        a = pulse_alpha(t)
        yy = by + 150 + 3 * 108
        rrect(
            d,
            [bx + 30, yy - 12, bx + bw - 30, yy + 52],
            10,
            outline=(*WARN, 255) if False else WARN,
            width=3 + int(2 * a),
        )
    return img


# ---- S9 cierre ---------------------------------------------------------------
def render_s9(t, sc, tl):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    m = MARK.resize((230, 230), Image.Resampling.LANCZOS)
    rev = ease(clamp01(t / 0.8))
    m2 = m.crop((0, 0, 230, max(1, int(230 * rev))))
    bob = 4 * math.sin(2 * math.pi * 0.2 * t)
    img.paste(m2, ((W - 230) // 2, int(150 + bob)), m2)
    f_t = F(88, True)
    ctext(d, (W // 2, 400), "tero", fill=ACC, font=f_t, anchor="ma")
    f_m = F(44, True)
    ctext(
        d,
        (W // 2, 512),
        "your classroom, your sources, your judgment",
        fill=TXT,
        font=f_m,
        anchor="ma",
    )
    if t > 1.2:
        code = 'git clone https://github.com/marcorojasb/tero ·  pip install -e ".[dev]"'
        n = len(code)
        typed = int(clamp01((t - 1.2) / 1.6) * n)
        bx0 = (W - 1300) // 2
        rrect(d, [bx0, 600, bx0 + 1300, 668], 10, fill=(13, 16, 21), outline=(48, 56, 68), width=2)
        ctext(
            d,
            (bx0 + 24, 620),
            code[:typed] + ("▌" if (t * 2.6) % 1 < 0.55 and typed < n else ""),
            fill=OK,
            font=F(23, True),
        )
    if t > 2.4:
        chips = [
            ("MIT", OK),
            ("teacher cryptographic seal", ACC),
            ("Strands Agents", (188, 140, 255)),
            ("Amazon Bedrock", WARN),
            ("#AgentsforHumans", MUT),
        ]
        fc = F(21, True)
        total = sum(text_w(fc, c) + 34 + 14 for c, _ in chips) - 14
        cx = (W - total) // 2
        for c, col in chips:
            bw = text_w(fc, c) + 34
            rrect(d, [cx, 716, cx + bw, 758], 9, fill=(17, 21, 27), outline=col, width=2)
            ctext(d, (cx + 17, 726), c, fill=col, font=fc)
            cx += bw + 14
        ctext(
            d,
            (W // 2, 782),
            "Agents for Humans Hackathon · AWS + Strands Agents SDK",
            fill=MUT,
            font=F(20),
            anchor="ma",
        )
    return img


# ---- S6b sello criptográfico --------------------------------------------------
VERIFY_LINES = [
    ("header", "✓ Sello Criptográfico de Criterio Docente: VÁLIDO", ""),
    ("kv", "Seal ID", SEAL_ID),
    ("kv", "Criterio", "humano_aprobado (conversational_approval)"),
    ("kv", "Modelo", "tero-offline"),
    ("kv", "Trace ID", "0af7651916cd…  · OpenTelemetry"),
    ("kv", "Artefacto", "derivados/…-evaluacion-condor-9c1f2a.md · integridad ✓"),
    ("kv", "Fuentes", "3 fuente(s) verificada(s) sin alteración"),
]


def render_s6b(t, sc, tl):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    sent = tl.sent_abs[6]
    bx, by, bw, bh = 110, 110, 1090, 800
    rrect(d, [bx, by, bx + bw, by + bh], 14, fill=(12, 15, 20), outline=(96, 124, 176), width=2)
    d.rectangle([bx + 3, by + 3, bx + bw - 3, by + 44], fill=(16, 20, 26))
    for i, c in enumerate((ERR, WARN, OK)):
        d.ellipse([bx + 22 + i * 34, by + 16, bx + 38 + i * 34, by + 32], fill=c)
    ctext(d, (bx + 140, by + 14), "zsh — tero", fill=MUT, font=F(20))
    cmd = "$ python -m tero verify-seal derivados/…-evaluacion-condor-9c1f2a.md"
    n = len(cmd)
    typed = int(clamp01((t - 0.6) / 1.35) * n)
    ctext(
        d,
        (bx + 36, by + 74),
        cmd[:typed] + ("▌" if (t * 2.6) % 1 < 0.55 and typed < n else ""),
        fill=TXT,
        font=F(24, True),
    )
    run_t = 2.2
    s0e = sent[0][1] if sent else 6.0
    s1e = sent[1][1] if len(sent) > 1 else s0e + 4
    appear = [run_t, run_t + 0.3, s0e - 1.2, s0e - 0.9, s0e - 0.6, s1e - 0.9, s1e - 0.6]
    y = by + 140
    fk = F(23, True)
    fv = F(23)
    for (kind, key, val), at in zip(VERIFY_LINES, appear):
        a = ease(clamp01((t - at) / 0.4))
        if a <= 0:
            y += 62 if kind == "header" else 54
            continue
        yy = y + (1 - a) * 10
        if kind == "header":
            ctext(d, (bx + 36, yy), key, fill=OK, font=F(27, True))
            pu = pulse_alpha(t)
            rrect(
                d,
                [bx + 26, yy - 10, bx + 36 + text_w(F(27, True), key) + 14, yy + 40],
                8,
                outline=OK,
                width=2 + int(2 * pu),
            )
            y += 62
        else:
            ctext(d, (bx + 52, yy), f"{key}:", fill=MUT, font=fk)
            vx = bx + 52 + text_w(fk, "Artefacto:  ")
            ctext(d, (vx, yy + 1), val, fill=ACC if key == "Seal ID" else TXT, font=fv)
            y += 54
    # panel derecho: tarjeta de papel con el pie del artefacto
    appear_paper = (sent[1][0] - 1.2) if len(sent) > 1 else 6.0
    a = clamp01((t - appear_paper) / 0.6)
    if a <= 0 and t > 0.5:
        # marco tenue: la zona derecha nunca queda vacía
        rrect(d, [1250, 170, 1860, 800], 12, outline=(40, 48, 60), width=2)
        ctext(
            d, (1555, 470), "artifact certificate", fill=(70, 80, 94), font=F(22, True), anchor="ma"
        )
    if a > 0:
        e = 1.0 - (1.0 - a) * (1.0 - a)
        pw, ph = 560, 620
        card = Image.new("RGB", (pw, ph), PAPER)
        cd = ImageDraw.Draw(card)
        cd.text((36, 40), "derivados/…-evaluacion-condor-9c1f2a.md", fill=(60, 62, 66), font=F(19))
        cd.line([(36, 80), (pw - 36, 80)], fill=(190, 188, 178), width=2)
        footer = (
            "*Material co-creado y certificado bajo criterio docente · Tero Decisional Seal ID: "
            + SEAL_ID
        )
        fw = F(22, True)
        words, cur, lines = footer.split(), [], []
        for w_ in words:
            cur.append(w_)
            if text_w(fw, " ".join(cur)) > pw - 110:
                cur.pop()
                lines.append(" ".join(cur))
                cur = [w_]
        lines.append(" ".join(cur))
        yy = 150
        for ln in lines:
            cd.text((44, yy), ln, fill=(38, 40, 46), font=fw)
            yy += 34
        cd.line([(36, yy + 10), (pw - 36, yy + 10)], fill=(190, 188, 178), width=2)
        cd.text((44, yy + 40), "hash fuentes   4b1f…e29a", fill=(110, 108, 100), font=F(19))
        cd.text((44, yy + 74), "hash derivado  90c4…77b3", fill=(110, 108, 100), font=F(19))
        cd.text((44, yy + 108), "criterio       humano_aprobado", fill=(110, 108, 100), font=F(19))
        # sello circular (abajo-derecha, no toca el footer)
        cx, cy, r = pw - 132, ph - 132, 78
        cd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(92, 60, 20), width=5)
        cd.ellipse(
            [cx - r + 12, cy - r + 12, cx + r - 12, cy + r - 12], outline=(92, 60, 20), width=2
        )
        cd.text((cx, cy - 26), "CRITERIO", fill=(92, 60, 20), font=F(19, True), anchor="ma")
        cd.text((cx, cy - 2), "DOCENTE", fill=(92, 60, 20), font=F(19, True), anchor="ma")
        cd.text((cx, cy + 26), "✓ humano", fill=(92, 60, 20), font=F(17, True), anchor="ma")
        pwz, phz = int(pw * e), int(ph * e)
        card = card.resize((max(1, pwz), max(1, phz)), Image.Resampling.LANCZOS).rotate(
            -2.0, expand=True, resample=Image.Resampling.BICUBIC, fillcolor=PAPER
        )
        px = 1230 + (660 - card.width) // 2
        py = 150 + (680 - card.height) // 2
        img.paste(card, (px + 6, py + 12))
        img.paste(card, (px, py))
        d.rectangle(
            [px - 2, py - 2, px + card.width + 2, py + card.height + 2], outline=WARN, width=2
        )
        ctext(
            d,
            (px + card.width // 2, py + card.height + 22),
            "the printed footer carries the seal",
            fill=MUT,
            font=F(21),
            anchor="ma",
        )
    return img


RENDERERS = {
    "s1_hero": render_s1,
    "s2_priv": render_s2,
    "s3_arch": render_s3,
    "s4_intent_a": render_s4,
    "s5_intent_b": render_s5,
    "s6_gate": render_s6,
    "s6b_seal": render_s6b,
    "s7_nee": render_s7,
    "s8_trio": render_s8,
    "s9_close": render_s9,
}
for i, sc in enumerate(SCENES):
    sc.render = RENDERERS[sc.id]


# --------------------------------------------------------------- compositor
def active_cap(tl: Timeline, t: float) -> str | None:
    best = None
    for s, e, txt in tl.caps:
        if s <= t <= e:
            best = txt
    return best


def render_global_frame(tl: Timeline, t: float) -> Image.Image:
    k = tl.scene_at(t)
    Timeline_current_scene[0] = k
    sc = SCENES[k]
    local = t - tl.scene_starts[k]
    img = sc.render(min(local, tl.scene_durs[k]), sc, tl)
    # crossfade con escena anterior
    if k > 0:
        prev_start = tl.scene_starts[k]
        if t < prev_start + OVERLAP:
            prev = SCENES[k - 1]
            plocal = t - tl.scene_starts[k - 1]
            pimg = prev.render(plocal, prev, tl)
            al = ease(clamp01((t - prev_start) / OVERLAP))
            img = Image.blend(pimg, img, al)
    # fade in/out global
    if t < 0.5:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, t / 0.5)
    if t > tl.total - 0.9:
        img = Image.blend(
            img, Image.new("RGB", (W, H), (0, 0, 0)), clamp01((t - (tl.total - 0.9)) / 0.9)
        )
    # chrome
    d = ImageDraw.Draw(img)
    top_bar(d, sc, k)
    cap = active_cap(tl, t)
    if cap:
        caption_card(img, cap)
    chapter_bar(img, t, tl.total)
    return img


# --------------------------------------------------------------- subtítulos
def fmt_srt(t: float) -> str:
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_vtt(t: float) -> str:
    return fmt_srt(t).replace(",", ".")


def write_subs(tl: Timeline):
    srt, vtt = [], ["WEBVTT", ""]
    for i, (s, e, txt) in enumerate(sorted(tl.caps), 1):
        srt.append(f"{i}\n{fmt_srt(s)} --> {fmt_srt(e)}\n{txt}\n")
        vtt.append(f"{fmt_vtt(s)} --> {fmt_vtt(e)}\n{txt}\n")
    (OUT_DIR / "tero-demo-en.srt").write_text("\n".join(srt), encoding="utf-8")
    (OUT_DIR / "tero-demo-en.vtt").write_text("\n".join(vtt), encoding="utf-8")


# ------------------------------------------------------------------ render
def render_video(tl: Timeline, audio_path: Path, out_path: Path):
    n_frames = int(tl.total * FPS)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-s",
        f"{W}x{H}",
        "-pix_fmt",
        "rgb24",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-i",
        str(audio_path),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-maxrate",
        "2.6M",
        "-bufsize",
        "5M",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        "-shortest",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    import time as _time

    t0 = _time.time()
    for f in range(n_frames):
        t = f / FPS
        frame = render_global_frame(tl, t)
        proc.stdin.write(frame.tobytes())
        if f % 300 == 0:
            el = _time.time() - t0
            print(f"  frame {f}/{n_frames} ({100 * f / n_frames:.0f}%) {el:.0f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    print(f"render listo en {_time.time() - t0:.0f}s -> {out_path}")


# ------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--frame", type=float, default=None)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--no-music", action="store_true")
    args = ap.parse_args()

    HERE.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    QC_DIR.mkdir(parents=True, exist_ok=True)

    print("== TTS ==")
    asyncio.run(tts_all(None))
    tl = build_timeline()
    print("== timeline ==")
    for k, sc in enumerate(SCENES):
        print(f"  {sc.id:14s} start={tl.scene_starts[k]:7.2f}  dur={tl.scene_durs[k]:6.2f}")
    print(f"  TOTAL: {tl.total:.1f}s ({tl.total / 60:.2f} min)")
    if args.plan:
        return

    if args.frame is not None:
        img = render_global_frame(tl, args.frame)
        p = QC_DIR / f"frame_{int(args.frame * 1000):06d}.png"
        img.save(p)
        print("frame ->", p)
        return

    if not args.full:
        print("nada que hacer: usa --frame / --full / --plan")
        return

    print("== audio ==")
    voice = build_voice_track(tl)
    music = None if args.no_music else build_music(tl.total + 0.5, voice)
    if music is not None:
        mix = voice + music[: len(voice)]
    else:
        mix = voice
    # estéreo con el pad levemente panoramizado
    if music is not None:
        left = mix
        right = voice + music[: len(voice)] * 0.96
    else:
        left = right = mix
    raw = QC_DIR / "mix_raw.wav"
    write_wav_stereo(raw, left, right)
    loud = QC_DIR / "mix_loud.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(raw),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar",
            "44100",
            str(loud),
        ],
        check=True,
    )
    print("== subtítulos ==")
    write_subs(tl)
    print("== render ==")
    render_video(tl, loud, OUT_DIR / "tero-demo-en.mp4")
    print("== qc ==")
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate",
            "-of",
            "json",
            str(OUT_DIR / "tero-demo-en.mp4"),
        ],
        capture_output=True,
        text=True,
    )
    (QC_DIR / "ffprobe.json").write_text(r.stdout)
    print(r.stdout)


if __name__ == "__main__":
    main()
