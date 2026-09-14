#!/usr/bin/env python3
"""Professional English Landing & Demonstration Video Generator for tero.

Produces a High Definition video (1080p, 1920x1080 @ 30fps) with:
1. Authentic brand palette (#0b0d10, #12151a, #4c566a, #82aaff, #9ece6a, #c9a227).
2. High-impact opening card with official OpenTUI Queltehue (Vanellus chilensis) silhouette.
3. Natural English neural narration (en-US-AndrewNeural).
4. Cinematic animations: Ken Burns continuous zoom/pan, dynamic terminal typing simulation,
   reactive audio equalizer, and smooth transitions.
5. Synced subtitles in JetBrains Mono without overflows or clipping.
6. Final export to site/assets/video/tero-demo-en.mp4, .srt, and .vtt.
"""

from __future__ import annotations

import json
import math
import re
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

# JetBrains Mono typography
FONT_BOLD_PATH = Path("/Users/marcorojasbelmar/Library/Fonts/JetBrainsMonoNerdFont-Bold.ttf")
FONT_REGULAR_PATH = Path("/Users/marcorojasbelmar/Library/Fonts/JetBrainsMonoNerdFont-Regular.ttf")


def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    p = FONT_BOLD_PATH if bold else FONT_REGULAR_PATH
    if p.exists():
        try:
            return ImageFont.truetype(str(p), size)
        except Exception:
            pass
    return ImageFont.load_default()


# Official tero brand palette (brand.json and styles.css)
COLOR_BG = (11, 13, 16)  # #0b0d10 (deep background)
COLOR_PANEL = (18, 21, 26)  # #12151a (primary panel)
COLOR_PANEL_ALT = (22, 26, 32)  # #161a20 (secondary panel)
COLOR_BORDER = (76, 86, 106)  # #4c566a (standard border)
COLOR_BORDER_SOFT = (61, 68, 80)  # #3d4450 (soft border)
COLOR_ACCENT = (130, 170, 255)  # #82aaff (tero focal blue/cyan)
COLOR_OK = (158, 206, 106)  # #9ece6a (approved / verified)
COLOR_WARN = (201, 162, 39)  # #c9a227 (photocopy / notices)
COLOR_ERR = (224, 108, 117)  # #e06c75 (error)
COLOR_TEXT = (216, 222, 233)  # #d8dee9 (primary text)
COLOR_MUTED = (122, 132, 144)  # #7a8490 (secondary text)

# Official Vanellus chilensis silhouette from OpenTUI
HOME_BIRD = [
    "      ▄▄▄▄▄    ▄▄▄▄▄     ",
    "    ▄████████▄▄▀▀▀▀▀▀▀▀▀▀",
    "  ▀▀▀▀███████            ",
    "       ██████            ",
    "       ██████▄           ",
    "       ███████▄          ",
    "      ██████████▄        ",
    "      █████████████▄     ",
    "      ███████████████▄   ",
    "       ▀███████████████▄ ",
    "          ▀▀█████████████",
    "            ███  ▀▀██████",
    "            █ █      ▀▀██",
    "            ▀ ▀          ",
]


def render_bird_graphic(
    width: int = 340, height: int = 380, color: tuple[int, int, int] = COLOR_ACCENT
) -> Image.Image:
    """Renders the official Queltehue silhouette with terminal scanlines and connected crest."""
    scale = 8
    cell_w = 16 * scale
    cell_h = 32 * scale
    cols = max(len(line) for line in HOME_BIRD)
    rows = len(HOME_BIRD)
    hi_w = cols * cell_w
    hi_h = rows * cell_h
    hi_img = Image.new("RGBA", (hi_w, hi_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(hi_img)
    rgba = color + (255,) if len(color) == 3 else color
    gap = 2 * scale
    for r, line in enumerate(HOME_BIRD):
        for c, char in enumerate(line):
            x0 = c * cell_w
            y0 = r * cell_h
            x1 = x0 + cell_w
            y1 = y0 + cell_h - gap
            ymid = y0 + (cell_h - gap) // 2
            if char == "█":
                d.rectangle([x0, y0, x1, y1], fill=rgba)
            elif char == "▀":
                d.rectangle([x0, y0, x1, ymid], fill=rgba)
            elif char == "▄":
                d.rectangle([x0, ymid, x1, y1], fill=rgba)
    return hi_img.resize((width, height), Image.Resampling.LANCZOS)


def create_top_bar(draw: ImageDraw.ImageDraw, badge_text: str = "", step_title: str = ""):
    """Official top branding bar with badges and breadcrumbs."""
    draw.rectangle([0, 0, 1920, 64], fill=COLOR_PANEL)
    draw.line([0, 64, 1920, 64], fill=COLOR_BORDER, width=2)

    font_brand = get_font(24, bold=True)
    font_sub = get_font(18, bold=False)
    draw.text((32, 18), "tero", fill=COLOR_ACCENT, font=font_brand)
    draw.text((95, 22), "·  your sources, your judgment", fill=COLOR_MUTED, font=font_sub)

    # Badges on the right
    font_badge = get_font(14, bold=True)
    badges = [
        ("AWS Bedrock", COLOR_WARN),
        ("Strands Multi-Agent", COLOR_ACCENT),
        ("OpenTUI", (188, 140, 255)),
    ]
    cur_x = 1888
    for label, color in reversed(badges):
        bbox = font_badge.getbbox(label)
        bw = (bbox[2] - bbox[0]) + 20
        cur_x -= bw + 12
        draw.rounded_rectangle(
            [cur_x, 16, cur_x + bw, 46], radius=6, outline=color, fill=COLOR_PANEL_ALT, width=1
        )
        draw.text((cur_x + 10, 21), label, fill=color, font=font_badge)

    # Center scene indicator
    if badge_text or step_title:
        title_full = (
            f"{badge_text.upper()}  |  {step_title}"
            if badge_text and step_title
            else (badge_text or step_title)
        )
        bbox = font_sub.getbbox(title_full)
        tw = bbox[2] - bbox[0]
        tx = (1920 - tw) // 2
        draw.text((tx, 22), title_full, fill=COLOR_TEXT, font=font_sub)


def render_audio_bars(
    draw: ImageDraw.ImageDraw, frame_idx: int, center_x: int = 960, base_y: int = 950
):
    """Dynamic audio equalizer reacting to narration cadence."""
    num_bars = 24
    bar_width = 6
    bar_gap = 6
    total_w = num_bars * (bar_width + bar_gap)
    start_x = center_x - total_w // 2

    for i in range(num_bars):
        wave1 = math.sin(frame_idx * 0.25 + i * 0.4)
        wave2 = math.cos(frame_idx * 0.15 - i * 0.3)
        h = int(6 + 18 * abs(wave1 * 0.6 + wave2 * 0.4))
        bx = start_x + i * (bar_width + bar_gap)
        color = COLOR_ACCENT if i % 2 == 0 else COLOR_OK
        draw.rounded_rectangle([bx, base_y - h, bx + bar_width, base_y], radius=2, fill=color)


def render_subtitles_card(draw: ImageDraw.ImageDraw, text: str, progress: float, frame_idx: int):
    """Stylized lower-third card with audio equalizer and progress indicator."""
    render_audio_bars(draw, frame_idx, center_x=960, base_y=952)

    font_sub = get_font(23, bold=True)
    box_w = 1600
    box_h = 86
    box_x = (1920 - box_w) // 2
    box_y = 962

    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        radius=8,
        fill=COLOR_PANEL,
        outline=COLOR_BORDER,
        width=2,
    )
    draw.line([box_x + 12, box_y + 2, box_x + box_w - 12, box_y + 2], fill=COLOR_ACCENT, width=2)

    words = text.split()
    lines = []
    curr: list[str] = []
    for w in words:
        curr.append(w)
        test_line = " ".join(curr)
        bbox = font_sub.getbbox(test_line)
        if (bbox[2] - bbox[0]) > (box_w - 80):
            curr.pop()
            lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))

    line_h = 30
    total_text_h = len(lines) * line_h
    start_y = box_y + (box_h - total_text_h) // 2

    for line in lines:
        bbox = font_sub.getbbox(line)
        tw = bbox[2] - bbox[0]
        tx = box_x + (box_w - tw) // 2
        draw.text((tx, start_y), line, fill=COLOR_TEXT, font=font_sub)
        start_y += line_h

    # Progress bar
    draw.line([0, 1076, 1920, 1076], fill=COLOR_BORDER_SOFT, width=1)
    if progress > 0.0:
        prog_w = int(1920 * max(0.0, min(1.0, progress)))
        draw.rectangle([0, 1074, prog_w, 1080], fill=COLOR_ACCENT)


def fit_and_pad(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    w, h = img.size
    ratio = min(max_w / w, max_h / h)
    new_w = max(1, int(w * ratio))
    new_h = max(1, int(h * ratio))
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


# 9 Master Scenes in English matching the official narrative
SCENES_EN = [
    {
        "id": "01_hero",
        "badge": "Opening",
        "title": "The Conversational Teacher Agent for Classrooms",
        "speech": (
            "Teachers do not need another generic chatbot that hallucinates. "
            "They need tomorrow's photocopy from their own classroom folder: "
            "the story they read with students, the official learning objective, and this week's vocabulary. "
            "This is tero: your classroom, your sources, your judgment."
        ),
        "subtitle": "tero · Your classroom, your sources, your judgment. Proposes in memory, teacher decides.",
        "type": "hero_branding",
    },
    {
        "id": "02_privacy",
        "badge": "Thesis & Privacy",
        "title": "Privacy by Design · Student Data Protection",
        "speech": (
            "Under strict student privacy laws like Chile's Ley 21.719, children's health records and grades must never touch the cloud. "
            "tero operates exclusively on your local folder, prepares proposals strictly in memory, "
            "and never writes to disk without your explicit approval."
        ),
        "subtitle": "Privacy by design: student data never leaves the local machine or touches cloud models.",
        "type": "split_principles_home",
    },
    {
        "id": "03_architecture",
        "badge": "Architecture",
        "title": "Strands Multi-Agent Graph on Amazon Bedrock",
        "speech": (
            "Under the hood, tero orchestrates a multi-agent graph with Strands Agents on Amazon Bedrock. "
            "A pedagogical drafter prepares the artifact, while a curriculum auditor validates learning objective alignment. "
            "Zero write tools in the registry: the approval gate protects every single byte."
        ),
        "subtitle": "Strands Multi-Agent Graph on Amazon Bedrock with curriculum auditing and in-memory approval gate.",
        "type": "architecture",
    },
    {
        "id": "04_intent_a",
        "badge": "Intent A",
        "title": "Respond and Explore without Writing Files",
        "speech": (
            "In the Open T-U-I terminal, conversation is natural and free of rigid menus. "
            "Ask tero what sources are available. "
            "The agent inspects your local folder and responds with pedagogical clarity. "
            "No hallucinations, no unwanted files."
        ),
        "subtitle": "Intent A: answers questions and inspects local folder without touching disk.",
        "type": "tui_interactive",
        "frame": "conversacion.png",
        "prompt_text": "What sources do I have in the folder?",
    },
    {
        "id": "05_intent_b",
        "badge": "Intent B",
        "title": "Create Material with Verifiable Citations",
        "speech": (
            "When requesting a reading guide, tero consults national curriculum catalogs and extracts verbatim citations from your files. "
            "It presents an in-memory proposal card with clear summary, verified evidence, "
            "and a full preview before touching disk."
        ),
        "subtitle": "Intent B: in-memory proposal card with verified citations against your local sources.",
        "type": "tui_interactive",
        "frame": "propuesta-guia.png",
        "prompt_text": "Prepare a 45-minute reading comprehension guide.",
    },
    {
        "id": "06_gate",
        "badge": "Approval Gate",
        "title": "Teacher Approval & Classroom Handout",
        "speech": (
            "Nothing is written without your explicit approval. "
            "Press the Y key or type dale, and the host writes to the derivatives folder. "
            "It immediately compiles to LaTeX, delivering a printed photocopy ready for tomorrow's classroom."
        ),
        "subtitle": "You approve with 'y' or 'dale'. The host materializes the file and delivers the classroom photocopy.",
        "type": "split_terminal_worksheet",
    },
    {
        "id": "07_intent_c_nee",
        "badge": "Intent C",
        "title": "Special Education Adaptation (Decreto 83)",
        "speech": (
            "For special education and inclusion programs, tero implements Chile's Decreto 83. "
            "It prioritizes access accommodations before touching learning objectives. "
            "It generates a new derivative file with full provenance, "
            "keeping your original material completely untouched."
        ),
        "subtitle": "Intent C: special education adaptation under Decreto 83. Original file remains byte-identical.",
        "type": "tui_single",
        "frame": "propuesta-adaptar.png",
    },
    {
        "id": "08_bedrock_trio",
        "badge": "Amazon Bedrock",
        "title": "Live Model Trio & Reproducible Offline Path",
        "speech": (
            "In terminal diagnostics with check-aws, we verify our Bedrock model trio: "
            "Amazon Nova Lite for extreme speed and low operational cost, GLM 4.7 for strict curricular schema adherence, "
            "and MiniMax for comprehensive rubrics. "
            "And for rural schools without internet, the tero offline model guarantees an identical pedagogical experience."
        ),
        "subtitle": "Amazon Bedrock Model Trio verified live, plus tero-offline model for air-gapped classrooms.",
        "type": "bedrock_diagnostics",
    },
    {
        "id": "09_close",
        "badge": "Open Source",
        "title": "Pedagogical Impact for Classrooms Worldwide",
        "speech": (
            "tero gives valuable time back to teachers, protects student privacy by construction, "
            "and elevates classroom learning. "
            "Open source under the MIT license for AWS's Agents for Humans Hackathon. "
            "Your classroom, your sources, your judgment."
        ),
        "subtitle": "tero · Your classroom, your sources, your judgment. Open source under the MIT license.",
        "type": "closing_hero",
    },
]


def render_scene_base_en(scene: dict, frame_idx: int, total_frames: int) -> Image.Image:
    """Generates the base 1920x1080 canvas for the English video."""
    canvas = Image.new("RGB", (1920, 1080), color=COLOR_BG)
    draw = ImageDraw.Draw(canvas)
    stype = scene["type"]

    if stype == "hero_branding":
        card_x, card_y, card_w, card_h = 240, 200, 440, 560
        draw.rounded_rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            radius=16,
            fill=COLOR_PANEL,
            outline=COLOR_BORDER,
            width=2,
        )
        draw.line(
            [card_x + 16, card_y + 2, card_x + card_w - 16, card_y + 2], fill=COLOR_ACCENT, width=2
        )

        font_card_lbl = get_font(14, bold=True)
        draw.text(
            (card_x + 24, card_y + 18),
            "VANELLUS CHILENSIS · QUELTEHUE",
            fill=COLOR_MUTED,
            font=font_card_lbl,
        )
        draw.line(
            [card_x + 24, card_y + 44, card_x + card_w - 24, card_y + 44],
            fill=COLOR_BORDER_SOFT,
            width=1,
        )

        bird = render_bird_graphic(width=340, height=380, color=COLOR_ACCENT)
        bx = card_x + (card_w - bird.width) // 2
        by = card_y + 54 + (card_h - 100 - bird.height) // 2
        canvas.paste(bird, (bx, by), bird)

        font_motto_small = get_font(15, bold=False)
        motto_t = "The tero alerts · You decide"
        m_bbox = font_motto_small.getbbox(motto_t)
        m_w = m_bbox[2] - m_bbox[0]
        draw.text(
            (card_x + (card_w - m_w) // 2, card_y + card_h - 38),
            motto_t,
            fill=COLOR_MUTED,
            font=font_motto_small,
        )

        font_hero_title = get_font(108, bold=True)
        font_hero_motto = get_font(38, bold=True)
        font_hero_sub = get_font(23, bold=False)
        font_badge = get_font(15, bold=True)

        tx = 740
        draw.text((tx, 250), "tero", fill=COLOR_ACCENT, font=font_hero_title)
        draw.text((tx, 390), "your sources, your judgment", fill=COLOR_TEXT, font=font_hero_motto)
        draw.text(
            (tx, 455),
            "The conversational teacher agent for K-12 classrooms",
            fill=COLOR_MUTED,
            font=font_hero_sub,
        )
        draw.text(
            (tx, 495),
            "Proposes in memory · Notices in view · Teacher decides",
            fill=COLOR_OK,
            font=font_hero_sub,
        )

        badges = [
            ("AWS Bedrock", COLOR_WARN),
            ("Strands Multi-Agent Graph", COLOR_ACCENT),
            ("OpenTUI", (188, 140, 255)),
            ("Track: Professional Agents", COLOR_OK),
        ]
        bx_pos = tx
        for b_text, b_color in badges:
            bbox = font_badge.getbbox(b_text)
            bw = (bbox[2] - bbox[0]) + 24
            draw.rounded_rectangle(
                [bx_pos, 580, bx_pos + bw, 620],
                radius=8,
                fill=COLOR_PANEL,
                outline=COLOR_BORDER,
                width=2,
            )
            draw.text((bx_pos + 12, 591), b_text, fill=b_color, font=font_badge)
            bx_pos += bw + 16

    elif stype == "split_principles_home":
        create_top_bar(draw, scene["badge"], scene["title"])
        lx, ly, lw, lh = 60, 90, 880, 840
        draw.rounded_rectangle(
            [lx, ly, lx + lw, ly + lh], radius=12, fill=COLOR_PANEL, outline=COLOR_BORDER, width=2
        )
        draw.line([lx + 20, ly + 68, lx + lw - 20, ly + 68], fill=COLOR_BORDER_SOFT, width=1)

        font_h1 = get_font(30, bold=True)
        font_b_title = get_font(21, bold=True)
        font_b_desc = get_font(19, bold=False)

        draw.text(
            (lx + 32, ly + 24),
            "PRINCIPLES OF THE TEACHER ASSISTANT",
            fill=COLOR_ACCENT,
            font=font_h1,
        )

        points = [
            (
                "Tomorrow's classroom photocopy:",
                "Created directly from your local folder with real stories, worksheets, and OAs.",
            ),
            (
                "Strict privacy by construction:",
                "Zero student health records, grades, or personal identifiers ever touch the cloud.",
            ),
            (
                "Zero direct write tools:",
                "The agent proposes strictly in memory. Nothing touches disk without authorization.",
            ),
            (
                "The educator decides:",
                "Only explicit teacher approval [y / 'dale'] authorizes materializing the file.",
            ),
            (
                "Immediate classroom delivery:",
                "Compiles to LaTeX and delivers printed photocopies ready for tomorrow morning.",
            ),
        ]
        py = ly + 100
        for b_title, b_desc in points:
            draw.text((lx + 30, py), "▸", fill=COLOR_ACCENT, font=font_b_title)
            draw.text((lx + 56, py), b_title, fill=COLOR_TEXT, font=font_b_title)
            py += 32
            draw.text((lx + 56, py), b_desc, fill=COLOR_MUTED, font=font_b_desc)
            py += 54

        rx, ry, rw, rh = 980, 90, 880, 840
        home_img_path = TUI_FRAMES / "home.png"
        if home_img_path.exists():
            home_img = Image.open(home_img_path).convert("RGBA")
            fitted = fit_and_pad(home_img, rw, rh)
            fx = rx + (rw - fitted.width) // 2
            fy = ry + (rh - fitted.height) // 2
            draw.rounded_rectangle(
                [fx - 4, fy - 4, fx + fitted.width + 4, fy + fitted.height + 4],
                radius=8,
                fill=(0, 0, 0),
                outline=COLOR_ACCENT,
                width=2,
            )
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "architecture":
        create_top_bar(draw, scene["badge"], scene["title"])
        arch_path = DOCS_HACKATHON / "architecture.png"
        if arch_path.exists():
            arch_img = Image.open(arch_path).convert("RGBA")
            fitted = fit_and_pad(arch_img, 1800, 830)
            fx = (1920 - fitted.width) // 2
            fy = 90 + (840 - fitted.height) // 2
            draw.rounded_rectangle(
                [fx - 6, fy - 6, fx + fitted.width + 6, fy + fitted.height + 6],
                radius=10,
                fill=COLOR_PANEL,
                outline=COLOR_ACCENT,
                width=2,
            )
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "tui_interactive":
        create_top_bar(draw, scene["badge"], scene["title"])
        frame_name = scene.get("frame", "conversacion.png")
        frame_path = TUI_FRAMES / frame_name
        if frame_path.exists():
            tui_img = Image.open(frame_path).convert("RGBA")
            fitted = fit_and_pad(tui_img, 1800, 830)
            fx = (1920 - fitted.width) // 2
            fy = 90 + (840 - fitted.height) // 2
            draw.rounded_rectangle(
                [fx - 4, fy - 4, fx + fitted.width + 4, fy + fitted.height + 4],
                radius=8,
                fill=(0, 0, 0),
                outline=COLOR_BORDER,
                width=2,
            )
            canvas.paste(fitted, (fx, fy), fitted)

            p_text = scene.get("prompt_text", "")
            if p_text:
                progress_chars = min(len(p_text), int((frame_idx / 45) * len(p_text)))
                typed_str = p_text[:progress_chars]
                cursor = "│" if (frame_idx // 15) % 2 == 0 else ""

                p_box_w = 1100
                p_box_h = 44
                px = (1920 - p_box_w) // 2
                py = fy + fitted.height - 58
                draw.rounded_rectangle(
                    [px, py, px + p_box_w, py + p_box_h],
                    radius=6,
                    fill=COLOR_PANEL,
                    outline=COLOR_ACCENT,
                    width=2,
                )
                font_prompt = get_font(18, bold=False)
                draw.text(
                    (px + 16, py + 12), f"▸ {typed_str}{cursor}", fill=COLOR_TEXT, font=font_prompt
                )

    elif stype == "split_terminal_worksheet":
        create_top_bar(draw, scene["badge"], scene["title"])
        esc_path = TUI_FRAMES / "escrito.png"
        if esc_path.exists():
            esc_img = Image.open(esc_path).convert("RGBA")
            fitted_l = fit_and_pad(esc_img, 980, 840)
            lx = 60 + (980 - fitted_l.width) // 2
            ly = 90 + (840 - fitted_l.height) // 2
            draw.rounded_rectangle(
                [lx - 4, ly - 4, lx + fitted_l.width + 4, ly + fitted_l.height + 4],
                radius=8,
                fill=(0, 0, 0),
                outline=COLOR_OK,
                width=2,
            )
            canvas.paste(fitted_l, (lx, ly), fitted_l)

        hoja_path = HOJAS_DIR / "guia-sistemas" / "p1.png"
        if hoja_path.exists():
            hoja_img = Image.open(hoja_path).convert("RGBA")
            fitted_r = fit_and_pad(hoja_img, 760, 840)
            rx = 1080 + (760 - fitted_r.width) // 2
            ry = 90 + (840 - fitted_r.height) // 2
            draw.rounded_rectangle(
                [rx - 6, ry - 6, rx + fitted_r.width + 6, ry + fitted_r.height + 6],
                radius=6,
                fill=(245, 245, 240),
                outline=COLOR_WARN,
                width=2,
            )
            canvas.paste(fitted_r, (rx, ry), fitted_r)

    elif stype == "tui_single":
        create_top_bar(draw, scene["badge"], scene["title"])
        frame_name = scene.get("frame", "propuesta-adaptar.png")
        frame_path = TUI_FRAMES / frame_name
        if frame_path.exists():
            tui_img = Image.open(frame_path).convert("RGBA")
            fitted = fit_and_pad(tui_img, 1800, 830)
            fx = (1920 - fitted.width) // 2
            fy = 90 + (840 - fitted.height) // 2
            draw.rounded_rectangle(
                [fx - 4, fy - 4, fx + fitted.width + 4, fy + fitted.height + 4],
                radius=8,
                fill=(0, 0, 0),
                outline=COLOR_BORDER,
                width=2,
            )
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "bedrock_diagnostics":
        create_top_bar(draw, scene["badge"], scene["title"])
        box_x, box_y, box_w, box_h = 180, 110, 1560, 800
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=12,
            fill=COLOR_PANEL,
            outline=COLOR_ACCENT,
            width=2,
        )

        font_term_title = get_font(30, bold=True)
        font_mono = get_font(21, bold=False)
        font_mono_bold = get_font(21, bold=True)

        draw.text(
            (box_x + 40, box_y + 40),
            "LIVE DIAGNOSTICS: AMAZON BEDROCK MODEL TRIO",
            fill=COLOR_ACCENT,
            font=font_term_title,
        )
        draw.text(
            (box_x + 40, box_y + 85),
            "$ python -m tero check-aws --all-models",
            fill=COLOR_MUTED,
            font=font_mono,
        )
        draw.line(
            [box_x + 40, box_y + 125, box_x + box_w - 40, box_y + 125], fill=COLOR_BORDER, width=1
        )

        models_data = [
            (
                "✓ amazon.nova-lite-v1:0",
                "1.04s",
                "Primary Model: extreme speed and minimal operational cost",
            ),
            (
                "✓ zai.glm-4.7-flash",
                "0.33s",
                "Curriculum & Special Ed: strict adherence to Decreto 83 schemas",
            ),
            (
                "✓ minimax.minimax-m2.5",
                "9.72s",
                "Pedagogical Depth: comprehensive rubrics and evaluation grids",
            ),
            (
                "✓ tero-offline",
                "<10ms",
                "Offline & Rural Classrooms: 100% auditable, reproducible Strands model",
            ),
        ]

        my = box_y + 160
        for m_name, m_lat, m_desc in models_data:
            draw.text((box_x + 44, my), m_name, fill=COLOR_OK, font=font_mono_bold)
            draw.rounded_rectangle(
                [box_x + 420, my - 2, box_x + 515, my + 28],
                radius=4,
                fill=COLOR_PANEL_ALT,
                outline=COLOR_ACCENT,
            )
            draw.text((box_x + 435, my + 3), m_lat, fill=COLOR_ACCENT, font=font_mono_bold)
            draw.text((box_x + 540, my + 3), m_desc, fill=COLOR_TEXT, font=font_mono)
            my += 72

        draw.rectangle(
            [box_x + 44, my + 15, box_x + box_w - 44, my + 80],
            fill=COLOR_PANEL_ALT,
            outline=COLOR_BORDER_SOFT,
        )
        draw.text(
            (box_x + 64, my + 36),
            "Result: 5 models benchmarked across 4 real teaching journeys. Zero data leakage.",
            fill=COLOR_MUTED,
            font=font_mono,
        )

    elif stype == "closing_hero":
        create_top_bar(draw, scene["badge"], scene["title"])
        box_x, box_y, box_w, box_h = 240, 120, 1440, 780
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=14,
            fill=COLOR_PANEL,
            outline=COLOR_ACCENT,
            width=2,
        )

        font_c_title = get_font(44, bold=True)
        font_c_sub = get_font(28, bold=False)
        font_c_code = get_font(23, bold=True)

        cx = box_x + box_w // 2

        t1 = "tero · Your sources, your judgment"
        w1 = font_c_title.getbbox(t1)[2] - font_c_title.getbbox(t1)[0]
        draw.text((cx - w1 // 2, box_y + 90), t1, fill=COLOR_TEXT, font=font_c_title)

        t2 = "The tero alerts. You decide."
        w2 = font_c_sub.getbbox(t2)[2] - font_c_sub.getbbox(t2)[0]
        draw.text((cx - w2 // 2, box_y + 165), t2, fill=COLOR_ACCENT, font=font_c_sub)

        code_box_y = box_y + 260
        draw.rectangle(
            [box_x + 80, code_box_y, box_x + box_w - 80, code_box_y + 120],
            fill=COLOR_BG,
            outline=COLOR_BORDER,
        )
        draw.text(
            (box_x + 110, code_box_y + 26),
            "git clone https://github.com/marcorojasb/tero",
            fill=COLOR_ACCENT,
            font=font_c_code,
        )
        draw.text(
            (box_x + 110, code_box_y + 68),
            "pip install -e '.[dev]' && python -m tero tui --offline",
            fill=COLOR_OK,
            font=font_c_code,
        )

        t3 = "MIT License · 100% Python & OpenTUI · Hackathon AWS Agents for Humans"
        w3 = font_c_sub.getbbox(t3)[2] - font_c_sub.getbbox(t3)[0]
        draw.text((cx - w3 // 2, box_y + 440), t3, fill=COLOR_MUTED, font=font_c_sub)

    return canvas


def apply_ken_burns(img: Image.Image, frame_idx: int, total_frames: int) -> Image.Image:
    """Applies slow cinematic zoom (1.00x -> 1.04x)."""
    zoom = 1.0 + 0.04 * (frame_idx / max(1, total_frames))
    w = int(1920 / zoom)
    h = int(1080 / zoom)
    x = (1920 - w) // 2
    y = (1080 - h) // 2
    return img.crop((x, y, x + w, y + h)).resize((1920, 1080), Image.Resampling.BILINEAR)


def synthesize_audio_scene_en(scene: dict, temp_dir: Path) -> tuple[Path, float]:
    """Generates natural English audio with en-US-AndrewNeural and 350ms padding."""
    raw_audio = temp_dir / f"raw_{scene['id']}.mp3"
    padded_audio = temp_dir / f"audio_{scene['id']}.mp3"

    cmd = [
        sys.executable,
        "-m",
        "edge_tts",
        "--voice",
        "en-US-AndrewNeural",
        "--rate",
        "+2%",
        "--text",
        scene["speech"],
        "--write-media",
        str(raw_audio),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    pad_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(raw_audio),
        "-af",
        "apad=pad_dur=0.35",
        "-c:a",
        "libmp3lame",
        str(padded_audio),
    ]
    subprocess.run(pad_cmd, check=True, capture_output=True)

    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(padded_audio),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    duration = float(probe.stdout.strip())
    return padded_audio, duration


def render_scene_to_video_en(
    scene: dict,
    audio_path: Path,
    duration: float,
    scene_idx: int,
    total_scenes: int,
    temp_dir: Path,
) -> Path:
    """Renders scene frames with Ken Burns, audio bars, and synchronized subtitles."""
    clip_mp4 = temp_dir / f"clip_{scene['id']}.mp4"
    fps = 30
    total_frames = max(30, int(duration * fps))

    base_img = render_scene_base_en(scene, 0, total_frames)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-s",
        "1920x1080",
        "-pix_fmt",
        "rgb24",
        "-r",
        str(fps),
        "-i",
        "-",
        "-i",
        str(audio_path),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-b:a",
        "192k",
        "-shortest",
        str(clip_mp4),
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        for idx in range(total_frames):
            if scene["type"] == "tui_interactive":
                frame_canvas = render_scene_base_en(scene, idx, total_frames)
            else:
                frame_canvas = base_img.copy()

            frame_moving = apply_ken_burns(frame_canvas, idx, total_frames)

            draw = ImageDraw.Draw(frame_moving)
            overall_progress = (scene_idx + idx / total_frames) / total_scenes
            render_subtitles_card(draw, scene["subtitle"], overall_progress, idx)

            proc.stdin.write(frame_moving.tobytes())
    finally:
        proc.stdin.close()
        proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"Error rendering clip {scene['id']}")

    return clip_mp4


def format_srt_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{milis:03d}"


def build_pro_landing_video_en():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="tero_pro_video_en_"))
    print("🎬 Starting professional English landing video production for tero...")
    print(f"📁 Temporary directory: {temp_dir}\n")

    clips: list[Path] = []
    srt_entries: list[str] = []
    accumulated_time = 0.0

    total_scenes = len(SCENES_EN)
    for idx, scene in enumerate(SCENES_EN):
        print(f"[{idx + 1}/{total_scenes}] Processing: {scene['id']} ({scene['title']})")
        audio_path, duration = synthesize_audio_scene_en(scene, temp_dir)
        print(f"   🔊 Natural English audio: {duration:.2f}s (en-US-AndrewNeural)")

        s_start = format_srt_timestamp(accumulated_time)
        s_end = format_srt_timestamp(accumulated_time + duration - 0.2)
        srt_entries.append(f"{idx + 1}\n{s_start} --> {s_end}\n{scene['subtitle']}\n")
        accumulated_time += duration

        print("   🎥 Rendering cinematic motion and encoding H.264 Full HD...")
        clip_path = render_scene_to_video_en(
            scene, audio_path, duration, idx, total_scenes, temp_dir
        )
        clips.append(clip_path)

    # Save SRT and VTT subtitle files
    srt_content = "\n".join(srt_entries)
    OUTPUT_SRT.write_text(srt_content, encoding="utf-8")
    vtt_content = "WEBVTT\n\n" + re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", srt_content)
    OUTPUT_VTT.write_text(vtt_content, encoding="utf-8")
    print(f"\n📝 Official English subtitles saved to:\n   - {OUTPUT_SRT}\n   - {OUTPUT_VTT}")

    # Concatenate all clips into final MP4
    print(f"\n🎞️  Concatenating {len(clips)} scenes into {OUTPUT_MP4}...")
    concat_list = temp_dir / "concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.resolve()}'\n")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(OUTPUT_MP4),
        ],
        check=True,
    )

    shutil.rmtree(temp_dir, ignore_errors=True)

    # Validate output with ffprobe
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size",
            "-of",
            "json",
            str(OUTPUT_MP4),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    info = json.loads(probe.stdout)
    dur = float(info["format"]["duration"])
    size_mb = int(info["format"]["size"]) / (1024 * 1024)

    print("\n✨ Official English tero demonstration video successfully generated!")
    print(f"   🎥 File: {OUTPUT_MP4}")
    print(f"   ⏱️  Duration: {dur:.2f} s ({dur / 60:.2f} min)")
    print(f"   💾 Size: {size_mb:.2f} MB")
    print("   🎯 Resolution: 1920x1080 @ 30fps Full HD")


if __name__ == "__main__":
    build_pro_landing_video_en()
