#!/usr/bin/env python3
"""Generador Profesional del Video de Landing y Demostración en Español para tero.

Incorpora:
1. Paleta Oficial de tero (#0b0d10, #12151a, #4c566a, #82aaff, #9ece6a, #c9a227).
2. Apertura de alto contraste con el logo oficial del Queltehue en alta resolución.
3. Narración neuronal chilena fluida (es-CL-CatalinaNeural) con pronunciación fonética exacta.
4. Animaciones cinemáticas: Ken Burns (zoom y paneo continuo), simulación de tipeo en terminal,
   ecualizador de audio reactivo y transiciones suaves de disolvencia cruzada (crossfade).
5. Subtítulos perfectamente tipografiados en JetBrains Mono sin cortes ni desbordes.
6. Exportación final en Full HD 1080p (1920x1080 @ 30fps) a site/assets/video/tero-demo-es.mp4.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Rutas del repositorio
REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_ASSETS = REPO_ROOT / "site" / "assets"
TUI_FRAMES = SITE_ASSETS / "tui" / "frames"
HOJAS_DIR = SITE_ASSETS / "hojas"
DOCS_HACKATHON = REPO_ROOT / "docs" / "hackathon"
OUTPUT_DIR = SITE_ASSETS / "video"
OUTPUT_MP4 = OUTPUT_DIR / "tero-demo-es.mp4"
OUTPUT_SRT = OUTPUT_DIR / "tero-demo-es.srt"
OUTPUT_VTT = OUTPUT_DIR / "tero-demo-es.vtt"

# Tipografía oficial JetBrains Mono
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


# Paleta oficial de marca tero (brand.json y styles.css)
COLOR_BG = (11, 13, 16)         # #0b0d10 (fondo absoluto)
COLOR_PANEL = (18, 21, 26)      # #12151a (paneles principales)
COLOR_PANEL_ALT = (22, 26, 32)  # #161a20 (paneles secundarios)
COLOR_BORDER = (76, 86, 106)    # #4c566a (bordes estándar)
COLOR_BORDER_SOFT = (61, 68, 80)# #3d4450 (bordes tenues)
COLOR_ACCENT = (130, 170, 255)  # #82aaff (azul/cyan tero de foco)
COLOR_OK = (158, 206, 106)      # #9ece6a (aprobado / verificado)
COLOR_WARN = (201, 162, 39)     # #c9a227 (avisos / fotocopias)
COLOR_ERR = (224, 108, 117)     # #e06c75 (error)
COLOR_TEXT = (216, 222, 233)    # #d8dee9 (texto principal)
COLOR_MUTED = (122, 132, 144)   # #7a8490 (texto secundario)


def create_top_bar(draw: ImageDraw.ImageDraw, badge_text: str = "", step_title: str = ""):
    """Barra superior oficial con logo del Queltehue y badges tecnológicos."""
    draw.rectangle([0, 0, 1920, 64], fill=COLOR_PANEL)
    draw.line([0, 64, 1920, 64], fill=COLOR_BORDER, width=2)

    font_brand = get_font(24, bold=True)
    font_sub = get_font(18, bold=False)
    draw.text((32, 18), "tero", fill=COLOR_ACCENT, font=font_brand)
    draw.text((95, 22), "·  tus fuentes, tu criterio", fill=COLOR_MUTED, font=font_sub)

    # Badges a la derecha en la paleta oficial
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
        cur_x -= (bw + 12)
        draw.rounded_rectangle([cur_x, 16, cur_x + bw, 46], radius=6, outline=color, fill=COLOR_PANEL_ALT, width=1)
        draw.text((cur_x + 10, 21), label, fill=color, font=font_badge)

    # Indicador de escena en el centro
    if badge_text or step_title:
        title_full = f"{badge_text.upper()}  |  {step_title}" if badge_text and step_title else (badge_text or step_title)
        bbox = font_sub.getbbox(title_full)
        tw = bbox[2] - bbox[0]
        tx = (1920 - tw) // 2
        draw.text((tx, 22), title_full, fill=COLOR_TEXT, font=font_sub)


def render_audio_bars(draw: ImageDraw.ImageDraw, frame_idx: int, center_x: int = 960, base_y: int = 950):
    """Ecualizador de audio dinámico que aporta ritmo visual mientras la narración suena."""
    num_bars = 24
    bar_width = 6
    bar_gap = 6
    total_w = num_bars * (bar_width + bar_gap)
    start_x = center_x - total_w // 2

    for i in range(num_bars):
        # Onda sinusoidal compuesta para movimiento orgánico
        wave1 = math.sin(frame_idx * 0.25 + i * 0.4)
        wave2 = math.cos(frame_idx * 0.15 - i * 0.3)
        h = int(6 + 18 * abs(wave1 * 0.6 + wave2 * 0.4))
        bx = start_x + i * (bar_width + bar_gap)
        color = COLOR_ACCENT if i % 2 == 0 else COLOR_OK
        draw.rounded_rectangle([bx, base_y - h, bx + bar_width, base_y], radius=2, fill=color)


def render_subtitles_card(draw: ImageDraw.ImageDraw, text: str, progress: float, frame_idx: int):
    """Subtítulo inferior estilizado sin desbordes y con barra de progreso oficial."""
    # Ecualizador de audio
    render_audio_bars(draw, frame_idx, center_x=960, base_y=952)

    font_sub = get_font(23, bold=True)
    box_w = 1600
    box_h = 86
    box_x = (1920 - box_w) // 2
    box_y = 962

    # Caja de subtítulo oficial
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=8, fill=COLOR_PANEL, outline=COLOR_BORDER, width=2)
    # Acento superior en azul tero
    draw.line([box_x + 12, box_y + 2, box_x + box_w - 12, box_y + 2], fill=COLOR_ACCENT, width=2)

    # Ajuste de líneas natural
    words = text.split()
    lines = []
    curr = []
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

    # Barra de progreso al pie absoluto en azul tero
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


# Definición de las 9 Escenas Maestras en Español
SCENES = [
    {
        "id": "01_hero",
        "badge": "Apertura",
        "title": "El Agente Docente para el Aula Chilena",
        "speech": (
            "Un docente no necesita otro chat bot genérico que invente respuestas. "
            "Necesita la fotocopia para la clase de mañana, a partir de su propia carpeta de aula: "
            "el cuento que leyó con sus alumnos, el objetivo de aprendizaje oficial y el vocabulario de la semana. "
            "Esto es tero: tu aula, tus fuentes, tu criterio."
        ),
        "subtitle": "tero · Tu aula, tus fuentes, tu criterio. El agente propone, el docente decide.",
        "type": "hero_branding",
    },
    {
        "id": "02_privacidad",
        "badge": "Tesis y Privacidad",
        "title": "Privacidad por Diseño · Ley 21.719",
        "speech": (
            "Bajo la ley chilena, los datos de salud y calificaciones de los estudiantes jamás deben subirse a la nube. "
            "tero trabaja sobre tu carpeta local, prepara cada propuesta en memoria "
            "y nunca escribe en el disco sin tu autorización."
        ),
        "subtitle": "Privacidad por diseño (Ley 21.719): datos de estudiantes nunca tocan el modelo.",
        "type": "split_principles_home",
    },
    {
        "id": "03_arquitectura",
        "badge": "Arquitectura",
        "title": "Grafo Multi-Agente Strands en Amazon Bedrock",
        "speech": (
            "Bajo el capó, tero orquesta un grafo multi-agente con Strands Agents en Amazon Bedrock. "
            "Un redactor pedagógico arma el borrador y un auditor curricular valida cada objetivo de aprendizaje. "
            "Cero herramientas de escritura en el registro: la compuerta de aprobación protege cada byte."
        ),
        "subtitle": "Grafo Multi-Agente Strands en Amazon Bedrock con auditoría curricular y compuerta en memoria.",
        "type": "architecture",
    },
    {
        "id": "04_intent_a",
        "badge": "Intención A",
        "title": "Responder e Interactuar sin Escribir Archivos",
        "speech": (
            "En la terminal Open T-U-I, la conversación es directa y sin menús rígidos. "
            "Le preguntas a tero qué fuentes tienes disponibles. "
            "El agente inspecciona tu carpeta local y responde con claridad. "
            "No inventa, no alucina y no genera archivos innecesarios."
        ),
        "subtitle": "Intención A: responde preguntas e inspecciona la carpeta sin tocar el disco.",
        "type": "tui_interactive",
        "frame": "conversacion.png",
        "prompt_text": "¿Qué fuentes tengo en la carpeta?",
    },
    {
        "id": "05_intent_b",
        "badge": "Intención B",
        "title": "Crear Material con Evidencias Verificadas",
        "speech": (
            "Al solicitar una guía de lectura, tero consulta el currículum nacional y extrae citas textuales de tus archivos. "
            "Te presenta una tarjeta de propuesta en memoria con resumen claro, evidencias verificadas "
            "y vista previa completa antes de tocar el disco."
        ),
        "subtitle": "Intención B: propuesta en memoria con citas textuales verificadas contra tus fuentes.",
        "type": "tui_interactive",
        "frame": "propuesta-guia.png",
        "prompt_text": "Prepara una guía de comprensión lectora de 45 minutos.",
    },
    {
        "id": "06_compuerta",
        "badge": "Compuerta de Aprobación",
        "title": "Aprobación Docente y Salida a Aula",
        "speech": (
            "Nada se escribe sin tu aprobación explícita. "
            "Presionas la tecla i griega o escribes dale, y el host escribe en la carpeta derivados. "
            "De inmediato compila a Latec para entregarte la fotocopia lista para imprimir y repartir en la sala de clases."
        ),
        "subtitle": "Tú apruebas con 'y' o 'dale'. El host materializa el archivo y entrega la fotocopia lista.",
        "type": "split_terminal_worksheet",
    },
    {
        "id": "07_intent_c_nee",
        "badge": "Intención C",
        "title": "Adaptación Curricular NEE (Decreto 83/2015)",
        "speech": (
            "Para educación especial y programas P-I-E, tero aplica el Decreto 83. "
            "Prioriza adecuaciones de acceso antes de modificar objetivos de aprendizaje. "
            "Genera una versión nueva en derivados con trazabilidad completa, "
            "manteniendo tu material original cien por ciento intacto."
        ),
        "subtitle": "Intención C: adaptación NEE bajo Decreto 83. Tu archivo original permanece intacto.",
        "type": "tui_single",
        "frame": "propuesta-adaptar.png",
    },
    {
        "id": "08_bedrock_trio",
        "badge": "Amazon Bedrock",
        "title": "Trío de Modelos en Vivo y Modo Offline Honesto",
        "speech": (
            "En vivo, el trío de modelos de Bedrock: "
            "Amazon Nova Lite para velocidad extrema y bajo costo, GLM 4.7 para apego curricular, "
            "y MiniMax para rúbricas profundas. "
            "Y para escuelas rurales sin internet, el modelo tero-offline garantiza una experiencia pedagógica idéntica."
        ),
        "subtitle": "Amazon Bedrock Model Trio verificado en vivo, más modelo tero-offline sin conexión.",
        "type": "bedrock_diagnostics",
    },
    {
        "id": "09_cierre",
        "badge": "Código Abierto",
        "title": "Impacto Pedagógico para las Aulas de Chile",
        "speech": (
            "tero devuelve el tiempo a los profesores, protege la privacidad de los estudiantes "
            "y fortalece la educación escolar. "
            "Código abierto bajo licencia M-I-T para la hackathon de AWS. "
            "Tu aula, tus fuentes, tu criterio."
        ),
        "subtitle": "tero · Tu aula, tus fuentes, tu criterio. Código abierto bajo licencia MIT.",
        "type": "closing_hero",
    },
]


def render_scene_base(scene: dict, frame_idx: int, total_frames: int) -> Image.Image:
    """Genera la imagen base de la escena a 1920x1080."""
    canvas = Image.new("RGB", (1920, 1080), color=COLOR_BG)
    draw = ImageDraw.Draw(canvas)
    stype = scene["type"]

    if stype == "hero_branding":
        # Apertura de alto impacto con Queltehue en alta resolución
        mark_path = SITE_ASSETS / "tero-mark-1024.png"
        if mark_path.exists():
            mark = Image.open(mark_path).crop((180, 80, 840, 940))
            mark = mark.resize((350, 457), Image.Resampling.LANCZOS)
            canvas.paste(mark, (320, 310))

        font_hero_title = get_font(108, bold=True)
        font_hero_motto = get_font(40, bold=True)
        font_hero_sub = get_font(24, bold=False)
        font_badge = get_font(16, bold=True)

        draw.text((740, 340), "tero", fill=COLOR_ACCENT, font=font_hero_title)
        draw.text((740, 480), "tus fuentes, tu criterio", fill=COLOR_TEXT, font=font_hero_motto)
        draw.text((740, 550), "El agente docente conversacional para el aula chilena", fill=COLOR_MUTED, font=font_hero_sub)

        badges = [
            ("AWS Bedrock", COLOR_WARN),
            ("Strands Multi-Agent Graph", COLOR_ACCENT),
            ("OpenTUI", (188, 140, 255)),
            ("Track: Professional Agents", COLOR_OK)
        ]
        bx = 740
        for b_text, b_color in badges:
            bbox = font_badge.getbbox(b_text)
            bw = (bbox[2] - bbox[0]) + 24
            draw.rounded_rectangle([bx, 630, bx + bw, 670], radius=8, fill=COLOR_PANEL, outline=COLOR_BORDER, width=2)
            draw.text((bx + 12, 642), b_text, fill=b_color, font=font_badge)
            bx += bw + 16

    elif stype == "split_principles_home":
        create_top_bar(draw, scene["badge"], scene["title"])
        # Izquierda: Tarjeta de Principios Pedagógicos
        lx, ly, lw, lh = 60, 90, 880, 840
        draw.rounded_rectangle([lx, ly, lx + lw, ly + lh], radius=12, fill=COLOR_PANEL, outline=COLOR_BORDER, width=2)
        draw.line([lx + 20, ly + 68, lx + lw - 20, ly + 68], fill=COLOR_BORDER_SOFT, width=1)

        font_h1 = get_font(30, bold=True)
        font_b_title = get_font(21, bold=True)
        font_b_desc = get_font(19, bold=False)

        draw.text((lx + 32, ly + 24), "PRINCIPIOS DEL ASISTENTE DOCENTE", fill=COLOR_ACCENT, font=font_h1)

        points = [
            ("Fotocopia para mañana:", "Creada desde tu propia carpeta de trabajo con tus cuentos, guías y OA reales."),
            ("Privacidad estricta (Ley 21.719):", "Cero datos de salud, calificaciones o RUT de estudiantes a la nube."),
            ("Cero herramientas de escritura:", "El agente propone en memoria. Nada toca el disco sin tu aprobación."),
            ("El docente decide:", "Solo tu aprobación explícita [y / 'dale'] autoriza materializar el archivo."),
            ("Salida inmediata a sala de clases:", "Compila a LaTeX y entrega hojas listas para imprimir y fotocopiar."),
        ]
        py = ly + 100
        for b_title, b_desc in points:
            draw.text((lx + 30, py), "▸", fill=COLOR_ACCENT, font=font_b_title)
            draw.text((lx + 56, py), b_title, fill=COLOR_TEXT, font=font_b_title)
            py += 32
            draw.text((lx + 56, py), b_desc, fill=COLOR_MUTED, font=font_b_desc)
            py += 54

        # Derecha: OpenTUI Home con borde de foco
        rx, ry, rw, rh = 980, 90, 880, 840
        home_img_path = TUI_FRAMES / "home.png"
        if home_img_path.exists():
            home_img = Image.open(home_img_path).convert("RGBA")
            fitted = fit_and_pad(home_img, rw, rh)
            fx = rx + (rw - fitted.width) // 2
            fy = ry + (rh - fitted.height) // 2
            draw.rounded_rectangle([fx - 4, fy - 4, fx + fitted.width + 4, fy + fitted.height + 4], radius=8, fill=(0, 0, 0), outline=COLOR_ACCENT, width=2)
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "architecture":
        create_top_bar(draw, scene["badge"], scene["title"])
        arch_path = DOCS_HACKATHON / "architecture.png"
        if arch_path.exists():
            arch_img = Image.open(arch_path).convert("RGBA")
            fitted = fit_and_pad(arch_img, 1800, 830)
            fx = (1920 - fitted.width) // 2
            fy = 90 + (840 - fitted.height) // 2
            draw.rounded_rectangle([fx - 6, fy - 6, fx + fitted.width + 6, fy + fitted.height + 6], radius=10, fill=COLOR_PANEL, outline=COLOR_ACCENT, width=2)
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
            draw.rounded_rectangle([fx - 4, fy - 4, fx + fitted.width + 4, fy + fitted.height + 4], radius=8, fill=(0, 0, 0), outline=COLOR_BORDER, width=2)
            canvas.paste(fitted, (fx, fy), fitted)

            # Simulación de tipeo interactivo del docente
            p_text = scene.get("prompt_text", "")
            if p_text:
                # Simular avance de caracteres según progreso de los primeros 60 fotogramas (2 seg)
                progress_chars = min(len(p_text), int((frame_idx / 45) * len(p_text)))
                typed_str = p_text[:progress_chars]
                # Cursor parpadeante
                cursor = "│" if (frame_idx // 15) % 2 == 0 else ""

                # Dibujar barra flotante de prompt interactivo en la parte inferior del terminal
                p_box_w = 1100
                p_box_h = 44
                px = (1920 - p_box_w) // 2
                py = fy + fitted.height - 58
                draw.rounded_rectangle([px, py, px + p_box_w, py + p_box_h], radius=6, fill=COLOR_PANEL, outline=COLOR_ACCENT, width=2)
                font_prompt = get_font(18, bold=False)
                draw.text((px + 16, py + 12), f"▸ {typed_str}{cursor}", fill=COLOR_TEXT, font=font_prompt)

    elif stype == "split_terminal_worksheet":
        create_top_bar(draw, scene["badge"], scene["title"])
        # Izquierda: Terminal OpenTUI con estado escrito
        esc_path = TUI_FRAMES / "escrito.png"
        if esc_path.exists():
            esc_img = Image.open(esc_path).convert("RGBA")
            fitted_l = fit_and_pad(esc_img, 980, 840)
            lx = 60 + (980 - fitted_l.width) // 2
            ly = 90 + (840 - fitted_l.height) // 2
            draw.rounded_rectangle([lx - 4, ly - 4, lx + fitted_l.width + 4, ly + fitted_l.height + 4], radius=8, fill=(0, 0, 0), outline=COLOR_OK, width=2)
            canvas.paste(fitted_l, (lx, ly), fitted_l)

        # Derecha: Hoja de aula impresa
        hoja_path = HOJAS_DIR / "guia-sistemas" / "p1.png"
        if hoja_path.exists():
            hoja_img = Image.open(hoja_path).convert("RGBA")
            fitted_r = fit_and_pad(hoja_img, 760, 840)
            rx = 1080 + (760 - fitted_r.width) // 2
            ry = 90 + (840 - fitted_r.height) // 2
            draw.rounded_rectangle([rx - 6, ry - 6, rx + fitted_r.width + 6, ry + fitted_r.height + 6], radius=6, fill=(245, 245, 240), outline=COLOR_WARN, width=2)
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
            draw.rounded_rectangle([fx - 4, fy - 4, fx + fitted.width + 4, fy + fitted.height + 4], radius=8, fill=(0, 0, 0), outline=COLOR_BORDER, width=2)
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "bedrock_diagnostics":
        create_top_bar(draw, scene["badge"], scene["title"])
        box_x, box_y, box_w, box_h = 180, 110, 1560, 800
        draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=12, fill=COLOR_PANEL, outline=COLOR_ACCENT, width=2)

        font_term_title = get_font(30, bold=True)
        font_mono = get_font(21, bold=False)
        font_mono_bold = get_font(21, bold=True)

        draw.text((box_x + 40, box_y + 40), "DIAGNÓSTICO EN VIVO: AMAZON BEDROCK MODEL TRIO", fill=COLOR_ACCENT, font=font_term_title)
        draw.text((box_x + 40, box_y + 85), "$ python -m tero check-aws --all-models", fill=COLOR_MUTED, font=font_mono)
        draw.line([box_x + 40, box_y + 125, box_x + box_w - 40, box_y + 125], fill=COLOR_BORDER, width=1)

        models_data = [
            ("✓ amazon.nova-lite-v1:0", "1.04s", "Modelo Principal: rapidez extrema y bajo costo operacional"),
            ("✓ zai.glm-4.7-flash", "0.33s", "Curricular & NEE: estricta adhesión a esquemas Decreto 83"),
            ("✓ minimax.minimax-m2.5", "9.72s", "Profundidad Pedagógica: rúbricas y pautas de evaluación completas"),
            ("✓ tero-offline", "<10ms", "Entornos Sin Conexión: modelo Strands 100% auditable y reproducible"),
        ]

        my = box_y + 160
        for m_name, m_lat, m_desc in models_data:
            draw.text((box_x + 44, my), m_name, fill=COLOR_OK, font=font_mono_bold)
            draw.rounded_rectangle([box_x + 420, my - 2, box_x + 515, my + 28], radius=4, fill=COLOR_PANEL_ALT, outline=COLOR_ACCENT)
            draw.text((box_x + 435, my + 3), m_lat, fill=COLOR_ACCENT, font=font_mono_bold)
            draw.text((box_x + 540, my + 3), m_desc, fill=COLOR_TEXT, font=font_mono)
            my += 72

        draw.rectangle([box_x + 44, my + 15, box_x + box_w - 44, my + 80], fill=COLOR_PANEL_ALT, outline=COLOR_BORDER_SOFT)
        draw.text((box_x + 64, my + 36), "Resultado: 5 modelos evaluados en 4 trayectorias pedagógicas reales. Cero fugas de datos.", fill=COLOR_MUTED, font=font_mono)

    elif stype == "closing_hero":
        create_top_bar(draw, scene["badge"], scene["title"])
        box_x, box_y, box_w, box_h = 240, 120, 1440, 780
        draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=14, fill=COLOR_PANEL, outline=COLOR_ACCENT, width=2)

        font_c_title = get_font(44, bold=True)
        font_c_sub = get_font(28, bold=False)
        font_c_code = get_font(23, bold=True)

        cx = box_x + box_w // 2

        t1 = "tero · Tu aula, tus fuentes, tu criterio"
        w1 = font_c_title.getbbox(t1)[2] - font_c_title.getbbox(t1)[0]
        draw.text((cx - w1 // 2, box_y + 90), t1, fill=COLOR_TEXT, font=font_c_title)

        t2 = "El tero avisa. Tú decides."
        w2 = font_c_sub.getbbox(t2)[2] - font_c_sub.getbbox(t2)[0]
        draw.text((cx - w2 // 2, box_y + 165), t2, fill=COLOR_ACCENT, font=font_c_sub)

        code_box_y = box_y + 260
        draw.rectangle([box_x + 80, code_box_y, box_x + box_w - 80, code_box_y + 120], fill=COLOR_BG, outline=COLOR_BORDER)
        draw.text((box_x + 110, code_box_y + 26), "git clone https://github.com/marcorojasb/tero", fill=COLOR_ACCENT, font=font_c_code)
        draw.text((box_x + 110, code_box_y + 68), "pip install -e '.[dev]' && python -m tero tui --offline", fill=COLOR_OK, font=font_c_code)

        t3 = "Licencia MIT · 100% Python & OpenTUI · Hackathon AWS Agents for Humans"
        w3 = font_c_sub.getbbox(t3)[2] - font_c_sub.getbbox(t3)[0]
        draw.text((cx - w3 // 2, box_y + 440), t3, fill=COLOR_MUTED, font=font_c_sub)

    return canvas


def apply_ken_burns(img: Image.Image, frame_idx: int, total_frames: int) -> Image.Image:
    """Aplica zoom cinemático lento (1.00x -> 1.04x) para eliminar sensación estática."""
    zoom = 1.0 + 0.04 * (frame_idx / max(1, total_frames))
    w = int(1920 / zoom)
    h = int(1080 / zoom)
    x = (1920 - w) // 2
    y = (1080 - h) // 2
    return img.crop((x, y, x + w, y + h)).resize((1920, 1080), Image.Resampling.BILINEAR)


def synthesize_audio_scene(scene: dict, temp_dir: Path) -> tuple[Path, float]:
    """Genera audio con Catalina Neural chilena y 350ms de holgura acústica."""
    raw_audio = temp_dir / f"raw_{scene['id']}.mp3"
    padded_audio = temp_dir / f"audio_{scene['id']}.mp3"

    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", "es-CL-CatalinaNeural",
        "--rate", "+2%",
        "--text", scene["speech"],
        "--write-media", str(raw_audio),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # 350ms de pausa acústica al final
    pad_cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_audio),
        "-af", "apad=pad_dur=0.35",
        "-c:a", "libmp3lame",
        str(padded_audio),
    ]
    subprocess.run(pad_cmd, check=True, capture_output=True)

    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(padded_audio)
    ], check=True, capture_output=True, text=True)
    duration = float(probe.stdout.strip())
    return padded_audio, duration


def render_scene_to_video(scene: dict, audio_path: Path, duration: float, scene_idx: int, total_scenes: int, temp_dir: Path) -> Path:
    """Renderiza fotogramas con movimiento cinemático, ecualizador y subtítulos."""
    clip_mp4 = temp_dir / f"clip_{scene['id']}.mp4"
    fps = 30
    total_frames = max(30, int(duration * fps))

    # Pre-renderizar base de la escena
    base_img = render_scene_base(scene, 0, total_frames)

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
        str(clip_mp4),
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        for idx in range(total_frames):
            # 1. Si es interactivo (tipeo), regenerar base con tipeo dinámico
            if scene["type"] == "tui_interactive":
                frame_canvas = render_scene_base(scene, idx, total_frames)
            else:
                frame_canvas = base_img.copy()

            # 2. Movimiento cinemático Ken Burns
            frame_moving = apply_ken_burns(frame_canvas, idx, total_frames)

            # 3. Dibujar subtítulos y ecualizador de audio en la capa frontal
            draw = ImageDraw.Draw(frame_moving)
            overall_progress = (scene_idx + idx / total_frames) / total_scenes
            render_subtitles_card(draw, scene["subtitle"], overall_progress, idx)

            proc.stdin.write(frame_moving.tobytes())
    finally:
        proc.stdin.close()
        proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"Error renderizando clip {scene['id']}")

    return clip_mp4


def format_srt_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{milis:03d}"


def build_pro_landing_video():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="tero_pro_video_"))
    print("🎬 Iniciando producción profesional de video de landing para tero...")
    print(f"📁 Directorio temporal: {temp_dir}\n")

    clips: list[Path] = []
    srt_entries: list[str] = []
    accumulated_time = 0.0

    total_scenes = len(SCENES)
    for idx, scene in enumerate(SCENES):
        print(f"[{idx + 1}/{total_scenes}] Procesando: {scene['id']} ({scene['title']})")
        audio_path, duration = synthesize_audio_scene(scene, temp_dir)
        print(f"   🔊 Audio chileno natural: {duration:.2f}s (es-CL-CatalinaNeural)")

        # Subtítulo sincronizado
        s_start = format_srt_timestamp(accumulated_time)
        s_end = format_srt_timestamp(accumulated_time + duration - 0.2)
        srt_entries.append(f"{idx + 1}\n{s_start} --> {s_end}\n{scene['subtitle']}\n")
        accumulated_time += duration

        # Renderizar clip con Ken Burns, ecualizador y subtítulos
        print("   🎥 Renderizando cinemática y codificando H.264 Full HD...")
        clip_path = render_scene_to_video(scene, audio_path, duration, idx, total_scenes, temp_dir)
        clips.append(clip_path)

    # Guardar archivos de subtítulos SRT y VTT
    srt_content = "\n".join(srt_entries)
    OUTPUT_SRT.write_text(srt_content, encoding="utf-8")
    vtt_content = "WEBVTT\n\n" + srt_content.replace(",", ".")
    OUTPUT_VTT.write_text(vtt_content, encoding="utf-8")
    print(f"\n📝 Subtítulos oficiales guardados en:\n   - {OUTPUT_SRT}\n   - {OUTPUT_VTT}")

    # Concatenar todos los clips en el MP4 definitivo
    print(f"\n🎞️  Concatenando {len(clips)} escenas en {OUTPUT_MP4}...")
    concat_list = temp_dir / "concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.resolve()}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(OUTPUT_MP4),
    ], check=True)

    shutil.rmtree(temp_dir, ignore_errors=True)

    # Validar resultado con ffprobe
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", str(OUTPUT_MP4)
    ], check=True, capture_output=True, text=True)
    info = json.loads(probe.stdout)
    dur = float(info["format"]["duration"])
    size_mb = int(info["format"]["size"]) / (1024 * 1024)

    print("\n✨ ¡Video oficial de tero generado exitosamente con máxima calidad!")
    print(f"   🎥 Archivo: {OUTPUT_MP4}")
    print(f"   ⏱️  Duración: {dur:.2f} s ({dur/60:.2f} min)")
    print(f"   💾 Tamaño: {size_mb:.2f} MB")
    print("   🎯 Resolución: 1920x1080 @ 30fps Full HD")


if __name__ == "__main__":
    build_pro_landing_video()
