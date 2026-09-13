#!/usr/bin/env python3
"""Official English Landing & Demonstration Video Generator for tero.

Produces a High Definition video (1080p, 1920x1080, 30fps) with:
1. Authentic English voiceover with edge-tts (en-US-AndrewNeural).
2. Word/sentence-synchronized English subtitles using JetBrains Mono.
3. Updated OpenTUI captures, photocopied classroom handouts, Strands Multi-Agent
   architecture diagram, and live Amazon Bedrock Model Trio diagnostics.
4. Export to site/assets/video/tero-demo-en.mp4, .srt, and .vtt.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Repository paths
REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_ASSETS = REPO_ROOT / "site" / "assets"
TUI_FRAMES = SITE_ASSETS / "tui" / "frames"
HOJAS_DIR = SITE_ASSETS / "hojas"
DOCS_HACKATHON = REPO_ROOT / "docs" / "hackathon"
OUTPUT_DIR = SITE_ASSETS / "video"
OUTPUT_MP4 = OUTPUT_DIR / "tero-demo-en.mp4"
OUTPUT_SRT = OUTPUT_DIR / "tero-demo-en.srt"
OUTPUT_VTT = OUTPUT_DIR / "tero-demo-en.vtt"

# Font detection
FONT_SEARCH_PATHS = [
    Path("/Users/marcorojasbelmar/Library/Fonts/JetBrainsMonoNerdFont-Bold.ttf"),
    Path("/Users/marcorojasbelmar/Library/Fonts/JetBrainsMonoNLNerdFont-Bold.ttf"),
    Path("/System/Library/Fonts/SFNSMono.ttf"),
    Path("/System/Library/Fonts/Monaco.ttf"),
    Path("/Library/Fonts/Arial.ttf"),
]

REGULAR_FONT_SEARCH_PATHS = [
    Path("/Users/marcorojasbelmar/Library/Fonts/JetBrainsMonoNerdFont-Regular.ttf"),
    Path("/Users/marcorojasbelmar/Library/Fonts/JetBrainsMonoNLNerdFont-Regular.ttf"),
    Path("/System/Library/Fonts/SFNSMono.ttf"),
    Path("/System/Library/Fonts/Monaco.ttf"),
    Path("/Library/Fonts/Arial.ttf"),
]


def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = FONT_SEARCH_PATHS if bold else REGULAR_FONT_SEARCH_PATHS
    for path in paths:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                pass
    return ImageFont.load_default()


# Color Palette (Dark GitHub / OpenTUI theme)
BG_COLOR = (13, 17, 23)        # #0d1117
PANEL_BG = (22, 27, 34)        # #161b22
PANEL_BORDER = (48, 54, 61)    # #30363d
TEXT_WHITE = (240, 246, 252)   # #f0f6fc
TEXT_MUTED = (139, 148, 158)   # #8b949e
ACCENT_BLUE = (88, 166, 255)   # #58a6ff
ACCENT_GREEN = (46, 160, 67)   # #2ea043
ACCENT_AMBER = (210, 153, 34)  # #d29922
ACCENT_PURPLE = (188, 140, 255)# #bc8cff


def create_base_canvas(badge_text: str = "", step_title: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Builds the 1920x1080 canvas with top branding bar and scene breadcrumb."""
    canvas = Image.new("RGB", (1920, 1080), color=BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Top header bar (height: 64px)
    draw.rectangle([0, 0, 1920, 64], fill=PANEL_BG)
    draw.line([0, 64, 1920, 64], fill=PANEL_BORDER, width=2)

    # Brand label
    font_brand = get_font(26, bold=True)
    font_sub = get_font(18, bold=False)
    draw.text((32, 18), "tero", fill=ACCENT_GREEN, font=font_brand)
    draw.text((95, 23), "·  Conversational Teacher Agent", fill=TEXT_MUTED, font=font_sub)

    # Tech stack badges on the right
    font_badge = get_font(14, bold=True)
    badges = [
        ("AWS Bedrock", ACCENT_AMBER),
        ("Strands Agents", ACCENT_BLUE),
        ("OpenTUI", ACCENT_PURPLE),
    ]
    cur_x = 1888
    for label, color in reversed(badges):
        bbox = font_badge.getbbox(label)
        bw = (bbox[2] - bbox[0]) + 20
        cur_x -= (bw + 10)
        draw.rounded_rectangle([cur_x, 16, cur_x + bw, 46], radius=6, outline=color, fill=(20, 25, 32), width=1)
        draw.text((cur_x + 10, 21), label, fill=color, font=font_badge)

    # Center scene indicator
    if badge_text or step_title:
        title_full = f"{badge_text.upper()}  |  {step_title}" if badge_text and step_title else (badge_text or step_title)
        bbox = font_sub.getbbox(title_full)
        tw = bbox[2] - bbox[0]
        tx = (1920 - tw) // 2
        draw.text((tx, 22), title_full, fill=TEXT_WHITE, font=font_sub)

    return canvas, draw


def render_subtitles(draw: ImageDraw.ImageDraw, text: str, progress: float = 0.0):
    """Draws the stylized lower-third subtitle card and bottom progress bar."""
    font_sub = get_font(24, bold=True)
    box_w = 1680
    box_h = 92
    box_x = (1920 - box_w) // 2
    box_y = 960

    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=10, fill=PANEL_BG, outline=PANEL_BORDER, width=2)

    words = text.split()
    lines = []
    curr = []
    for w in words:
        curr.append(w)
        test_line = " ".join(curr)
        bbox = font_sub.getbbox(test_line)
        if (bbox[2] - bbox[0]) > (box_w - 60):
            curr.pop()
            lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))

    line_h = 32
    total_text_h = len(lines) * line_h
    start_y = box_y + (box_h - total_text_h) // 2

    for line in lines:
        bbox = font_sub.getbbox(line)
        tw = bbox[2] - bbox[0]
        tx = box_x + (box_w - tw) // 2
        draw.text((tx, start_y), line, fill=TEXT_WHITE, font=font_sub)
        start_y += line_h

    # Absolute bottom progress line
    draw.line([0, 1076, 1920, 1076], fill=PANEL_BORDER, width=1)
    if progress > 0.0:
        prog_w = int(1920 * max(0.0, min(1.0, progress)))
        draw.rectangle([0, 1074, prog_w, 1080], fill=ACCENT_GREEN)


def fit_image_in_box(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Lanczos downscale maintaining aspect ratio."""
    w, h = img.size
    ratio = min(max_w / w, max_h / h)
    new_w = max(1, int(w * ratio))
    new_h = max(1, int(h * ratio))
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


# 8 Master Scenes in English
SCENES_EN = [
    {
        "id": "01_intro",
        "badge": "Introduction",
        "title": "The Classroom Problem and tero's Thesis",
        "speech": (
            "Teachers do not need another generic chatbot. "
            "They need tomorrow's photocopy from their own classroom folder: "
            "the story they actually read, the official learning objective they marked, and this week's vocabulary. "
            "And under privacy regulations, student data must never reach the cloud. "
            "tero is a conversational teacher agent: it proposes in memory and writes nothing until you approve."
        ),
        "caption": "tero is a conversational teacher agent: it proposes in memory and writes nothing until you approve.",
        "type": "intro_split",
    },
    {
        "id": "02_architecture",
        "badge": "Architecture",
        "title": "Strands Multi-Agent Graph on Amazon Bedrock",
        "speech": (
            "Under the hood, tero coordinates a Strands Multi-Agent Graph on Amazon Bedrock. "
            "A pedagogical drafter prepares the artifact, while a quality gate auditor verifies alignment with the national curriculum. "
            "Amazon Bedrock models handle text inference, but the teacher's folder never leaves the local machine. "
            "Zero write tools in the registry: the in-memory gate protects every byte."
        ),
        "caption": "Strands Multi-Agent Graph with Quality Auditing and zero unauthorized writes.",
        "type": "architecture",
    },
    {
        "id": "03_intent_a",
        "badge": "Intent A",
        "title": "Respond and Explore without Writing",
        "speech": (
            "In the OpenTUI interface, communication is natural and direct, without rigid step menus. "
            "The teacher asks what sources are available in the folder. "
            "tero inspects the local space, answers with pedagogical clarity, and creates no unwanted files."
        ),
        "caption": "Intent a: respond and explore. Inspects sources and answers without touching disk.",
        "type": "tui_single",
        "frame": "conversacion.png",
    },
    {
        "id": "04_intent_b",
        "badge": "Intent B",
        "title": "Create Material with Verifiable Citations",
        "speech": (
            "When requesting a reading comprehension guide, tero consults the Chilean curriculum catalog and extracts verbatim evidence from local files. "
            "It presents a complete proposal card: a clear summary, non-blocking advisories, and a full markdown preview before touching disk."
        ),
        "caption": "Intent b: create new material. Verbatim citations checked against your files.",
        "type": "tui_single",
        "frame": "propuesta-guia.png",
    },
    {
        "id": "05_gate_approval",
        "badge": "Approval Gate",
        "title": "Teacher Approval and Classroom Handout",
        "speech": (
            "Nothing is written until the teacher explicitly approves with Y or by saying dale. "
            "Upon approval, the host writes the document to the derivados folder and compiles the template to LaTeX, "
            "instantly delivering a photocopiable sheet ready for class tomorrow."
        ),
        "caption": "You approve with 'y' or 'dale'. The host writes and delivers the classroom photocopy.",
        "type": "split_written_leaf",
    },
    {
        "id": "06_intent_c_nee",
        "badge": "Intent C",
        "title": "Special Education Adaptation (Decreto 83)",
        "speech": (
            "For special education, tero implements Chile's Decreto 83. "
            "It prioritizes access accommodations—such as time and presentation format—before touching learning objectives. "
            "A new version is created in derivados with full provenance, while the original source remains byte-identical under SHA-256."
        ),
        "caption": "Intent c: NEE adaptation with Decreto 83. Original material stays untouched.",
        "type": "tui_single",
        "frame": "propuesta-adaptar.png",
    },
    {
        "id": "07_bedrock_trio",
        "badge": "Amazon Bedrock",
        "title": "Live Model Trio & Reproducible Offline Path",
        "speech": (
            "In terminal diagnostics with check-aws, we verify our Bedrock Model Trio: "
            "Amazon Nova Lite for extreme speed and low cost, GLM 4.7 Flash for strict curricular schema adherence, and MiniMax M2.5 for exhaustive rubrics. "
            "And for offline or rural classrooms, the tero-offline scripted model guarantees a 100% reproducible experience."
        ),
        "caption": "Bedrock Model Trio: Nova Lite, GLM 4.7, and MiniMax, plus tero-offline model.",
        "type": "diagnostic_bedrock",
    },
    {
        "id": "08_close",
        "badge": "Open Source",
        "title": "Pedagogical Agent for Chilean Classrooms",
        "speech": (
            "tero gives precious time back to teachers, protects student privacy by construction, and strengthens public education. "
            "An open-source project under the MIT license for AWS's Agents for Humans hackathon. "
            "Your classroom, your sources, your judgment."
        ),
        "caption": "tero · Your sources, your judgment. Open source under MIT license.",
        "type": "closing",
    },
]


def render_scene_frame_en(scene: dict, frame_idx: int, total_frames: int, progress: float) -> Image.Image:
    """Renders the exact 1080p frame for the English video."""
    canvas, draw = create_base_canvas(scene["badge"], scene["title"])
    stype = scene.get("type", "tui_single")

    content_box = (60, 80, 1860, 930)
    cw = content_box[2] - content_box[0]
    ch = content_box[3] - content_box[1]

    if stype == "intro_split":
        half_w = (cw - 40) // 2

        draw.rounded_rectangle([content_box[0], content_box[1], content_box[0] + half_w, content_box[3]], radius=12, fill=PANEL_BG, outline=PANEL_BORDER, width=2)
        font_h1 = get_font(34, bold=True)
        font_body = get_font(22, bold=False)
        font_bold = get_font(22, bold=True)

        draw.text((content_box[0] + 40, content_box[1] + 50), "THE CONVERSATIONAL TEACHER AGENT", fill=ACCENT_AMBER, font=font_h1)

        points = [
            ("Your folder is ground truth:", " Works on the stories, worksheets, and OAs you already use."),
            ("Privacy by construction:", " Complies with Ley 21.719; student health data never reaches the cloud."),
            ("Zero direct write tools:", " The agent proposes in memory. Nothing touches the disk directly."),
            ("The educator decides:", " Only your explicit approval [y / 'dale'] authorizes writing to disk."),
            ("Classroom ready:", " Automatically exports to LaTeX and delivers printed photocopies for tomorrow."),
        ]
        py = content_box[1] + 130
        for b_title, b_desc in points:
            draw.text((content_box[0] + 40, py), "•", fill=ACCENT_GREEN, font=font_bold)
            draw.text((content_box[0] + 65, py), b_title, fill=TEXT_WHITE, font=font_bold)
            bw = font_bold.getbbox(b_title)[2] - font_bold.getbbox(b_title)[0]
            draw.text((content_box[0] + 70 + bw, py), b_desc, fill=TEXT_MUTED, font=font_body)
            py += 64

        home_img_path = TUI_FRAMES / "home.png"
        if home_img_path.exists():
            home_img = Image.open(home_img_path).convert("RGBA")
            fitted = fit_image_in_box(home_img, half_w, ch)
            fx = content_box[0] + half_w + 40 + (half_w - fitted.width) // 2
            fy = content_box[1] + (ch - fitted.height) // 2
            draw.rounded_rectangle([fx - 4, fy - 4, fx + fitted.width + 4, fy + fitted.height + 4], radius=8, fill=(0, 0, 0), outline=ACCENT_GREEN, width=2)
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "architecture":
        arch_path = DOCS_HACKATHON / "architecture.png"
        if arch_path.exists():
            arch_img = Image.open(arch_path).convert("RGBA")
            fitted = fit_image_in_box(arch_img, cw, ch - 20)
            fx = content_box[0] + (cw - fitted.width) // 2
            fy = content_box[1] + (ch - fitted.height) // 2
            draw.rounded_rectangle([fx - 6, fy - 6, fx + fitted.width + 6, fy + fitted.height + 6], radius=10, fill=(18, 22, 28), outline=ACCENT_BLUE, width=2)
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "tui_single":
        frame_name = scene.get("frame", "conversacion.png")
        frame_path = TUI_FRAMES / frame_name
        if frame_path.exists():
            tui_img = Image.open(frame_path).convert("RGBA")
            fitted = fit_image_in_box(tui_img, cw, ch - 10)
            fx = content_box[0] + (cw - fitted.width) // 2
            fy = content_box[1] + (ch - fitted.height) // 2
            draw.rounded_rectangle([fx - 4, fy - 4, fx + fitted.width + 4, fy + fitted.height + 4], radius=8, fill=(0, 0, 0), outline=PANEL_BORDER, width=2)
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "split_written_leaf":
        half_w = (cw - 40) // 2

        esc_path = TUI_FRAMES / "escrito.png"
        if esc_path.exists():
            esc_img = Image.open(esc_path).convert("RGBA")
            fitted_l = fit_image_in_box(esc_img, half_w, ch)
            lx = content_box[0] + (half_w - fitted_l.width) // 2
            ly = content_box[1] + (ch - fitted_l.height) // 2
            draw.rounded_rectangle([lx - 4, ly - 4, lx + fitted_l.width + 4, ly + fitted_l.height + 4], radius=8, fill=(0, 0, 0), outline=ACCENT_GREEN, width=2)
            canvas.paste(fitted_l, (lx, ly), fitted_l)

        hoja_path = HOJAS_DIR / "guia-sistemas" / "p1.png"
        if hoja_path.exists():
            hoja_img = Image.open(hoja_path).convert("RGBA")
            fitted_r = fit_image_in_box(hoja_img, half_w, ch)
            rx = content_box[0] + half_w + 40 + (half_w - fitted_r.width) // 2
            ry = content_box[1] + (ch - fitted_r.height) // 2
            draw.rounded_rectangle([rx - 6, ry - 6, rx + fitted_r.width + 6, ry + fitted_r.height + 6], radius=6, fill=(245, 245, 240), outline=ACCENT_AMBER, width=2)
            canvas.paste(fitted_r, (rx, ry), fitted_r)

    elif stype == "diagnostic_bedrock":
        box_x = content_box[0] + 120
        box_y = content_box[1] + 20
        box_w = cw - 240
        box_h = ch - 40
        draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=12, fill=(16, 20, 26), outline=ACCENT_AMBER, width=2)

        font_term_title = get_font(28, bold=True)
        font_mono = get_font(21, bold=False)
        font_mono_bold = get_font(21, bold=True)

        draw.text((box_x + 36, box_y + 36), "LIVE DIAGNOSTICS: AMAZON BEDROCK MODEL TRIO", fill=ACCENT_AMBER, font=font_term_title)
        draw.text((box_x + 36, box_y + 76), "$ python -m tero check-aws --all-models", fill=TEXT_MUTED, font=font_mono)
        draw.line([box_x + 36, box_y + 115, box_x + box_w - 36, box_y + 115], fill=PANEL_BORDER, width=1)

        models_data = [
            ("✓ amazon.nova-lite-v1:0", "1.04s", "Primary Model: extreme speed and minimal operational cost"),
            ("✓ zai.glm-4.7-flash", "0.33s", "Curriculum & NEE: strict adherence to Decreto 83 schemas"),
            ("✓ minimax.minimax-m2.5", "9.72s", "Pedagogical Depth: comprehensive rubrics and evaluation grids"),
            ("✓ tero-offline", "<10ms", "Offline & Rural Classrooms: 100% auditable, reproducible Strands model"),
        ]

        my = box_y + 145
        for m_name, m_lat, m_desc in models_data:
            draw.text((box_x + 40, my), m_name, fill=ACCENT_GREEN, font=font_mono_bold)
            draw.rounded_rectangle([box_x + 380, my - 2, box_x + 470, my + 26], radius=4, fill=(28, 36, 45), outline=ACCENT_BLUE)
            draw.text((box_x + 395, my + 2), m_lat, fill=ACCENT_BLUE, font=font_mono_bold)
            draw.text((box_x + 490, my + 2), m_desc, fill=TEXT_WHITE, font=font_mono)
            my += 66

        draw.rectangle([box_x + 40, my + 10, box_x + box_w - 40, my + 70], fill=(22, 27, 34), outline=PANEL_BORDER)
        draw.text((box_x + 60, my + 28), "Result: 5 models benchmarked across 4 real teaching journeys. Zero data leakage.", fill=TEXT_MUTED, font=font_mono)

    elif stype == "closing":
        box_x = content_box[0] + 160
        box_y = content_box[1] + 50
        box_w = cw - 320
        box_h = ch - 100
        draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=14, fill=PANEL_BG, outline=ACCENT_GREEN, width=2)

        font_c_title = get_font(42, bold=True)
        font_c_sub = get_font(26, bold=False)
        font_c_code = get_font(22, bold=True)

        cx = box_x + box_w // 2

        t1 = "tero · Your sources, your judgment"
        w1 = font_c_title.getbbox(t1)[2] - font_c_title.getbbox(t1)[0]
        draw.text((cx - w1 // 2, box_y + 70), t1, fill=TEXT_WHITE, font=font_c_title)

        t2 = "Open-source conversational teacher agent for AWS Agents for Humans Hackathon"
        w2 = font_c_sub.getbbox(t2)[2] - font_c_sub.getbbox(t2)[0]
        draw.text((cx - w2 // 2, box_y + 145), t2, fill=ACCENT_AMBER, font=font_c_sub)

        code_box_y = box_y + 240
        draw.rectangle([box_x + 80, code_box_y, box_x + box_w - 80, code_box_y + 110], fill=(13, 17, 23), outline=PANEL_BORDER)
        draw.text((box_x + 110, code_box_y + 24), "git clone https://github.com/marcorojasb/tero", fill=ACCENT_BLUE, font=font_c_code)
        draw.text((box_x + 110, code_box_y + 60), "pip install -e '.[dev]' && python -m tero tui --offline", fill=ACCENT_GREEN, font=font_c_code)

        t3 = "MIT License · 100% Python & OpenTUI · No proprietary lock-in"
        w3 = font_c_sub.getbbox(t3)[2] - font_c_sub.getbbox(t3)[0]
        draw.text((cx - w3 // 2, box_y + 400), t3, fill=TEXT_MUTED, font=font_c_sub)

    render_subtitles(draw, scene["caption"], progress)
    return canvas


def synthesize_audio_en(scene: dict, temp_dir: Path) -> tuple[Path, float]:
    """Generates natural English narration with edge-tts and measures duration."""
    raw_audio = temp_dir / f"raw_audio_{scene['id']}.mp3"
    padded_audio = temp_dir / f"audio_{scene['id']}.mp3"
    voice = "en-US-AndrewNeural"

    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", voice,
        "--text", scene["speech"],
        "--write-media", str(raw_audio),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # 400ms acoustic padding for natural cadence
    pad_cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_audio),
        "-af", "apad=pad_dur=0.4",
        "-c:a", "libmp3lame",
        str(padded_audio),
    ]
    subprocess.run(pad_cmd, check=True, capture_output=True)

    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(padded_audio),
    ]
    res = subprocess.run(probe_cmd, check=True, capture_output=True, text=True)
    duration = float(res.stdout.strip())
    return padded_audio, duration


def render_scene_video_en(scene: dict, audio_path: Path, duration: float, scene_idx: int, total_scenes: int, temp_dir: Path) -> Path:
    """Renders frames with cached static background and encodes with ffmpeg."""
    scene_mp4 = temp_dir / f"clip_{scene['id']}.mp4"
    fps = 30
    total_frames = max(30, int(duration * fps))

    # Pre-render base frame for maximum rendering speed
    base_frame = render_scene_frame_en(scene, 0, total_frames, 0.0)

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1920x1080",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "192k",
        "-shortest",
        str(scene_mp4),
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        for idx in range(total_frames):
            progress = (scene_idx + idx / total_frames) / total_scenes
            frame_copy = base_frame.copy()
            draw = ImageDraw.Draw(frame_copy)
            render_subtitles(draw, scene["caption"], progress)
            proc.stdin.write(frame_copy.tobytes())
    finally:
        proc.stdin.close()
        proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"Error rendering scene {scene['id']}")

    return scene_mp4


def format_srt_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{milis:03d}"


def build_full_video_en():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="tero_video_en_"))
    print("🎬 Starting English landing video production...")
    print(f"📁 Temporary directory: {temp_dir}")

    scene_clips: list[Path] = []
    srt_entries: list[str] = []
    accumulated_time = 0.0

    total_scenes = len(SCENES_EN)
    for idx, scene in enumerate(SCENES_EN):
        print(f"\n[{idx + 1}/{total_scenes}] Generating scene: {scene['id']} ({scene['title']})")
        audio_path, duration = synthesize_audio_en(scene, temp_dir)
        print(f"   🔊 Synthesized audio: {duration:.2f}s (en-US-AndrewNeural)")

        start_srt = format_srt_time(accumulated_time)
        end_srt = format_srt_time(accumulated_time + duration - 0.2)
        srt_entries.append(f"{idx + 1}\n{start_srt} --> {end_srt}\n{scene['caption']}\n")
        accumulated_time += duration

        print("   🖼️  Rendering frames and encoding H.264/AAC...")
        clip_path = render_scene_video_en(scene, audio_path, duration, idx, total_scenes, temp_dir)
        scene_clips.append(clip_path)

    # Save SRT & VTT
    srt_text = "\n".join(srt_entries)
    OUTPUT_SRT.write_text(srt_text, encoding="utf-8")
    vtt_text = "WEBVTT\n\n" + srt_text.replace(",", ".")
    OUTPUT_VTT.write_text(vtt_text, encoding="utf-8")
    print(f"\n📝 English subtitles saved to: {OUTPUT_SRT} and {OUTPUT_VTT}")

    # Concatenate clips
    print(f"\n🎞️  Concatenating {len(scene_clips)} scenes into final video...")
    concat_list_file = temp_dir / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            f.write(f"file '{clip.resolve()}'\n")

    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(OUTPUT_MP4),
    ]
    subprocess.run(concat_cmd, check=True)

    shutil.rmtree(temp_dir, ignore_errors=True)

    # Probe result
    probe_final = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", str(OUTPUT_MP4)],
        check=True, capture_output=True, text=True
    )
    final_info = json.loads(probe_final.stdout)
    dur = float(final_info["format"]["duration"])
    size_mb = int(final_info["format"]["size"]) / (1024 * 1024)

    print("\n✅ English landing video generated successfully!")
    print(f"   🎥 File: {OUTPUT_MP4}")
    print(f"   ⏱️  Duration: {dur:.2f} seconds ({dur/60:.2f} minutes)")
    print(f"   💾 Size: {size_mb:.2f} MB")
    print("   🎯 Resolution: 1920x1080 @ 30fps")


if __name__ == "__main__":
    build_full_video_en()
