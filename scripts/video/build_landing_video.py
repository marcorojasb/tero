#!/usr/bin/env python3
"""Generador del video de landing y demostración en español para tero.

Produce un video en alta definición (1080p, 1920x1080, 30fps) con:
1. Narración en voz chilena natural con edge-tts (es-CL-LorenzoNeural).
2. Subtítulos perfectamente sincronizados e incrustados con JetBrains Mono.
3. Vistas actualizadas de OpenTUI, fotocopias de aula, diagrama de arquitectura
   y diagnóstico en vivo de Amazon Bedrock Model Trio.
4. Exportación a site/assets/video/tero-demo-es.mp4 y subtítulos .srt.
"""

from __future__ import annotations

import functools
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Rutas principales del proyecto
REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_ASSETS = REPO_ROOT / "site" / "assets"
TUI_FRAMES = SITE_ASSETS / "tui" / "frames"
HOJAS_DIR = SITE_ASSETS / "hojas"
DOCS_HACKATHON = REPO_ROOT / "docs" / "hackathon"
OUTPUT_DIR = SITE_ASSETS / "video"
OUTPUT_MP4 = OUTPUT_DIR / "tero-demo-es.mp4"
OUTPUT_SRT = OUTPUT_DIR / "tero-demo-es.srt"

# Tipografía
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


@functools.lru_cache(maxsize=32)
def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = FONT_SEARCH_PATHS if bold else REGULAR_FONT_SEARCH_PATHS
    for path in paths:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                pass
    return ImageFont.load_default()


# Paleta de colores OpenTUI / Dark GitHub
BG_COLOR = (13, 17, 23)  # #0d1117
PANEL_BG = (22, 27, 34)  # #161b22
PANEL_BORDER = (48, 54, 61)  # #30363d
TEXT_WHITE = (240, 246, 252)  # #f0f6fc
TEXT_MUTED = (139, 148, 158)  # #8b949e
ACCENT_BLUE = (88, 166, 255)  # #58a6ff
ACCENT_GREEN = (46, 160, 67)  # #2ea043
ACCENT_AMBER = (210, 153, 34)  # #d29922
ACCENT_PURPLE = (188, 140, 255)  # #bc8cff


def create_base_canvas(
    badge_text: str = "", step_title: str = ""
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Crea el lienzo base de 1920x1080 con barra superior de marca y contexto."""
    canvas = Image.new("RGB", (1920, 1080), color=BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Barra superior (alto: 64px)
    draw.rectangle([0, 0, 1920, 64], fill=PANEL_BG)
    draw.line([0, 64, 1920, 64], fill=PANEL_BORDER, width=2)

    # Marca tero
    font_brand = get_font(26, bold=True)
    font_sub = get_font(18, bold=False)
    draw.text((32, 18), "tero", fill=ACCENT_GREEN, font=font_brand)
    draw.text((95, 23), "·  Agente Docente Conversacional", fill=TEXT_MUTED, font=font_sub)

    # Badges derecha
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
        cur_x -= bw + 10
        draw.rounded_rectangle(
            [cur_x, 16, cur_x + bw, 46], radius=6, outline=color, fill=(20, 25, 32), width=1
        )
        draw.text((cur_x + 10, 21), label, fill=color, font=font_badge)

    # Contexto / paso activo en centro
    if badge_text or step_title:
        title_full = (
            f"{badge_text.upper()}  |  {step_title}"
            if badge_text and step_title
            else (badge_text or step_title)
        )
        bbox = font_sub.getbbox(title_full)
        tw = bbox[2] - bbox[0]
        tx = (1920 - tw) // 2
        draw.text((tx, 22), title_full, fill=TEXT_WHITE, font=font_sub)

    return canvas, draw


def render_subtitles(draw: ImageDraw.ImageDraw, text: str):
    """Dibuja la franja de subtítulo inferior estilizada."""
    font_sub = get_font(24, bold=True)
    box_w = 1680
    box_h = 92
    box_x = (1920 - box_w) // 2
    box_y = 960

    # Fondo semi-translúcido para máxima legibilidad
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        radius=10,
        fill=PANEL_BG,
        outline=PANEL_BORDER,
        width=2,
    )

    # Dividir texto si es largo
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

    # Línea base al pie absoluto
    draw.line([0, 1076, 1920, 1076], fill=PANEL_BORDER, width=1)


def draw_progress_bar(draw: ImageDraw.ImageDraw, progress: float = 0.0):
    """Dibuja la barra verde de progreso del video al pie de la pantalla."""
    if progress > 0.0:
        prog_w = int(1920 * max(0.0, min(1.0, progress)))
        draw.rectangle([0, 1074, prog_w, 1080], fill=ACCENT_GREEN)


def fit_image_in_box(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Escala imagen manteniendo relación de aspecto sin distorsión."""
    w, h = img.size
    ratio = min(max_w / w, max_h / h)
    new_w = max(1, int(w * ratio))
    new_h = max(1, int(h * ratio))
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


# Definición de las 8 escenas maestras del video en español
SCENES = [
    {
        "id": "01_intro",
        "badge": "Introducción",
        "title": "El Problema Docente y la Tesis de tero",
        "speech": (
            "Los profesores no necesitan otro chatbot genérico de internet. "
            "Necesitan la fotocopia para la clase de mañana a partir de su propia carpeta de aula: "
            "el cuento que leyeron, el objetivo marcado y el vocabulario de la semana. "
            "Y bajo la legislación chilena, los datos de los estudiantes jamás deben subirse a la nube. "
            "tero es un agente docente conversacional: propone en memoria y nunca escribe sin tu aprobación."
        ),
        "caption": "tero es un agente docente conversacional: propone en memoria y nunca escribe sin tu aprobación.",
        "type": "intro_split",
    },
    {
        "id": "02_architecture",
        "badge": "Arquitectura",
        "title": "Grafo Multi-Agente Strands sobre Amazon Bedrock",
        "speech": (
            "Bajo el capó, tero orquesta un Grafo Multi-Agente con Strands Agents en Amazon Bedrock. "
            "Un redactor pedagógico prepara el material y un auditor de calidad verifica el apego al currículum. "
            "Los modelos de Bedrock realizan inferencia de texto, pero la carpeta local nunca sale del equipo. "
            "Cero herramientas de escritura directa: solo el host escribe tras la aprobación del profesor."
        ),
        "caption": "Grafo Multi-Agente con Strands Agents y compuerta estricta: cero escritura sin aprobación.",
        "type": "architecture",
    },
    {
        "id": "03_intent_a",
        "badge": "Intención A",
        "title": "Responder e Interactuar sin Escribir",
        "speech": (
            "En la interfaz OpenTUI, la interacción es directa y natural, sin menús rígidos. "
            "El profesor consulta qué fuentes tiene en su carpeta. "
            "tero inspecciona el espacio local, responde con exactitud pedagógica y no genera archivos innecesarios."
        ),
        "caption": "Intención a: responder e interactuar. Consulta fuentes y responde sin tocar el disco.",
        "type": "tui_single",
        "frame": "conversacion.png",
    },
    {
        "id": "04_intent_b",
        "badge": "Intención B",
        "title": "Crear Material con Citas de Evidencia Verificadas",
        "speech": (
            "Cuando se solicita una guía de lectura, tero consulta el currículum nacional y extrae evidencias de los archivos. "
            "Presenta una tarjeta de propuesta completa: resumen claro, advertencias no bloqueantes y vista previa en markdown antes de tocar el disco."
        ),
        "caption": "Intención b: crear material nuevo. Citas textuales verificadas contra tus fuentes locales.",
        "type": "tui_single",
        "frame": "propuesta-guia.png",
    },
    {
        "id": "05_gate_approval",
        "badge": "Compuerta de Aprobación",
        "title": "Aprobación Docente y Generación de la Fotocopia",
        "speech": (
            "Nada se escribe en el disco hasta que el docente aprueba con Y o escribiendo dale. "
            "Al aprobar, el host escribe el documento en derivados y compila la plantilla a LaTeX, "
            "generando de inmediato la fotocopia lista para imprimir y repartir en la sala de clases."
        ),
        "caption": "Tú apruebas con 'y' o 'dale'. El host escribe en derivados y entrega la fotocopia lista.",
        "type": "split_written_leaf",
    },
    {
        "id": "06_intent_c_nee",
        "badge": "Intención C",
        "title": "Adaptación Curricular NEE según Decreto 83/2015",
        "speech": (
            "Para educación especial y programas PIE, tero aplica el Decreto 83 de 2015. "
            "Prioriza adaptaciones de acceso antes de tocar los objetivos de aprendizaje. "
            "Crea una versión nueva con trazabilidad completa, manteniendo intacto el archivo original bajo hash SHA-256."
        ),
        "caption": "Intención c: adaptación a NEE con Decreto 83. Tu material original se mantiene intacto.",
        "type": "tui_single",
        "frame": "propuesta-adaptar.png",
    },
    {
        "id": "07_bedrock_trio",
        "badge": "Amazon Bedrock",
        "title": "Trío de Modelos en Vivo y Modo Offline Honesto",
        "speech": (
            "En el diagnóstico con check-aws, verificamos la latencia del Trío de Modelos de Bedrock: "
            "Amazon Nova Lite para rapidez y costo, GLM 4.7 Flash para rigor curricular, y MiniMax M2.5 para rúbricas detalladas. "
            "Y en lugares sin internet, el modelo tero-offline garantiza una experiencia pedagógica 100% reproducible."
        ),
        "caption": "Trío de modelos en Bedrock: Nova Lite, GLM 4.7 y MiniMax, más modelo tero-offline.",
        "type": "diagnostic_bedrock",
    },
    {
        "id": "08_close",
        "badge": "Código Abierto",
        "title": "Impacto Pedagógico para las Aulas de Chile",
        "speech": (
            "tero devuelve tiempo valioso a los profesores, protege la privacidad de los niños y fortalece la educación escolar. "
            "Proyecto de código abierto con licencia MIT para la hackathon Agents for Humans de AWS. "
            "Tu aula, tus fuentes, tu criterio."
        ),
        "caption": "tero · Tu aula, tus fuentes, tu criterio. Código abierto bajo licencia MIT.",
        "type": "closing",
    },
]


def render_scene_base(scene: dict) -> Image.Image:
    """Renderiza el fotograma base estático para la escena indicada (sin barra de progreso)."""
    canvas, draw = create_base_canvas(scene["badge"], scene["title"])
    stype = scene.get("type", "tui_single")

    content_box = (60, 80, 1860, 930)
    cw = content_box[2] - content_box[0]
    ch = content_box[3] - content_box[1]

    if stype == "intro_split":
        half_w = (cw - 40) // 2

        draw.rounded_rectangle(
            [content_box[0], content_box[1], content_box[0] + half_w, content_box[3]],
            radius=12,
            fill=PANEL_BG,
            outline=PANEL_BORDER,
            width=2,
        )
        font_h1 = get_font(34, bold=True)
        font_body = get_font(22, bold=False)
        font_bold = get_font(22, bold=True)

        draw.text(
            (content_box[0] + 40, content_box[1] + 50),
            "EL ASISTENTE DOCENTE CHILENO",
            fill=ACCENT_AMBER,
            font=font_h1,
        )

        points = [
            ("Tu carpeta es la verdad:", " Trabaja sobre los cuentos, guías y OA que ya usas."),
            ("Privacidad estricta:", " Cumple Ley 21.719; datos de alumnos no viajan a la nube."),
            (
                "Cero herramientas de escritura:",
                " El agente propone en memoria. Nada toca el disco.",
            ),
            (
                "El docente decide:",
                " Solo tu aprobación explícita [y / 'dale'] autoriza la escritura.",
            ),
            ("Listo para el aula:", " Exporta a LaTeX y entrega fotocopias impresas para mañana."),
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
            draw.rounded_rectangle(
                [fx - 4, fy - 4, fx + fitted.width + 4, fy + fitted.height + 4],
                radius=8,
                fill=(0, 0, 0),
                outline=ACCENT_GREEN,
                width=2,
            )
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "architecture":
        arch_path = DOCS_HACKATHON / "architecture.png"
        if arch_path.exists():
            arch_img = Image.open(arch_path).convert("RGBA")
            fitted = fit_image_in_box(arch_img, cw, ch - 20)
            fx = content_box[0] + (cw - fitted.width) // 2
            fy = content_box[1] + (ch - fitted.height) // 2
            draw.rounded_rectangle(
                [fx - 6, fy - 6, fx + fitted.width + 6, fy + fitted.height + 6],
                radius=10,
                fill=(18, 22, 28),
                outline=ACCENT_BLUE,
                width=2,
            )
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "tui_single":
        frame_name = scene.get("frame", "conversacion.png")
        frame_path = TUI_FRAMES / frame_name
        if frame_path.exists():
            tui_img = Image.open(frame_path).convert("RGBA")
            fitted = fit_image_in_box(tui_img, cw, ch - 10)
            fx = content_box[0] + (cw - fitted.width) // 2
            fy = content_box[1] + (ch - fitted.height) // 2
            draw.rounded_rectangle(
                [fx - 4, fy - 4, fx + fitted.width + 4, fy + fitted.height + 4],
                radius=8,
                fill=(0, 0, 0),
                outline=PANEL_BORDER,
                width=2,
            )
            canvas.paste(fitted, (fx, fy), fitted)

    elif stype == "split_written_leaf":
        half_w = (cw - 40) // 2

        esc_path = TUI_FRAMES / "escrito.png"
        if esc_path.exists():
            esc_img = Image.open(esc_path).convert("RGBA")
            fitted_l = fit_image_in_box(esc_img, half_w, ch)
            lx = content_box[0] + (half_w - fitted_l.width) // 2
            ly = content_box[1] + (ch - fitted_l.height) // 2
            draw.rounded_rectangle(
                [lx - 4, ly - 4, lx + fitted_l.width + 4, ly + fitted_l.height + 4],
                radius=8,
                fill=(0, 0, 0),
                outline=ACCENT_GREEN,
                width=2,
            )
            canvas.paste(fitted_l, (lx, ly), fitted_l)

        hoja_path = HOJAS_DIR / "guia-sistemas" / "p1.png"
        if hoja_path.exists():
            hoja_img = Image.open(hoja_path).convert("RGBA")
            fitted_r = fit_image_in_box(hoja_img, half_w, ch)
            rx = content_box[0] + half_w + 40 + (half_w - fitted_r.width) // 2
            ry = content_box[1] + (ch - fitted_r.height) // 2
            draw.rounded_rectangle(
                [rx - 6, ry - 6, rx + fitted_r.width + 6, ry + fitted_r.height + 6],
                radius=6,
                fill=(245, 245, 240),
                outline=ACCENT_AMBER,
                width=2,
            )
            canvas.paste(fitted_r, (rx, ry), fitted_r)

    elif stype == "diagnostic_bedrock":
        box_x = content_box[0] + 120
        box_y = content_box[1] + 20
        box_w = cw - 240
        box_h = ch - 40
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=12,
            fill=(16, 20, 26),
            outline=ACCENT_AMBER,
            width=2,
        )

        font_term_title = get_font(28, bold=True)
        font_mono = get_font(21, bold=False)
        font_mono_bold = get_font(21, bold=True)

        draw.text(
            (box_x + 36, box_y + 36),
            "DIAGNÓSTICO EN VIVO: AMAZON BEDROCK MODEL TRIO",
            fill=ACCENT_AMBER,
            font=font_term_title,
        )
        draw.text(
            (box_x + 36, box_y + 76),
            "$ python -m tero check-aws --all-models",
            fill=TEXT_MUTED,
            font=font_mono,
        )
        draw.line(
            [box_x + 36, box_y + 115, box_x + box_w - 36, box_y + 115], fill=PANEL_BORDER, width=1
        )

        models_data = [
            (
                "✓ amazon.nova-lite-v1:0",
                "1.04s",
                "Modelo Principal: rapidez extrema y bajo costo operacional",
            ),
            (
                "✓ zai.glm-4.7-flash",
                "0.33s",
                "Curricular & NEE: estricta adhesión a esquemas Decreto 83",
            ),
            (
                "✓ minimax.minimax-m2.5",
                "9.72s",
                "Profundidad Pedagógica: rúbricas y pautas de evaluación completas",
            ),
            (
                "✓ tero-offline",
                "<10ms",
                "Entornos Sin Conexión: modelo Strands 100% auditable y reproducible",
            ),
        ]

        my = box_y + 145
        for m_name, m_lat, m_desc in models_data:
            draw.text((box_x + 40, my), m_name, fill=ACCENT_GREEN, font=font_mono_bold)
            draw.rounded_rectangle(
                [box_x + 380, my - 2, box_x + 470, my + 26],
                radius=4,
                fill=(28, 36, 45),
                outline=ACCENT_BLUE,
            )
            draw.text((box_x + 395, my + 2), m_lat, fill=ACCENT_BLUE, font=font_mono_bold)
            draw.text((box_x + 490, my + 2), m_desc, fill=TEXT_WHITE, font=font_mono)
            my += 66

        draw.rectangle(
            [box_x + 40, my + 10, box_x + box_w - 40, my + 70],
            fill=(22, 27, 34),
            outline=PANEL_BORDER,
        )
        draw.text(
            (box_x + 60, my + 28),
            "Resultado: 5 modelos evaluados en 4 trayectorias pedagógicas reales. Cero fugas de datos.",
            fill=TEXT_MUTED,
            font=font_mono,
        )

    elif stype == "closing":
        box_x = content_box[0] + 160
        box_y = content_box[1] + 50
        box_w = cw - 320
        box_h = ch - 100
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=14,
            fill=PANEL_BG,
            outline=ACCENT_GREEN,
            width=2,
        )

        font_c_title = get_font(42, bold=True)
        font_c_sub = get_font(26, bold=False)
        font_c_code = get_font(22, bold=True)

        cx = box_x + box_w // 2

        t1 = "tero · Tu aula, tus fuentes, tu criterio"
        w1 = font_c_title.getbbox(t1)[2] - font_c_title.getbbox(t1)[0]
        draw.text((cx - w1 // 2, box_y + 70), t1, fill=TEXT_WHITE, font=font_c_title)

        t2 = "Agente docente de código abierto para la Hackathon Agents for Humans de AWS"
        w2 = font_c_sub.getbbox(t2)[2] - font_c_sub.getbbox(t2)[0]
        draw.text((cx - w2 // 2, box_y + 145), t2, fill=ACCENT_AMBER, font=font_c_sub)

        code_box_y = box_y + 240
        draw.rectangle(
            [box_x + 80, code_box_y, box_x + box_w - 80, code_box_y + 110],
            fill=(13, 17, 23),
            outline=PANEL_BORDER,
        )
        draw.text(
            (box_x + 110, code_box_y + 24),
            "git clone https://github.com/marcorojasb/tero",
            fill=ACCENT_BLUE,
            font=font_c_code,
        )
        draw.text(
            (box_x + 110, code_box_y + 60),
            "pip install -e '.[dev]' && python -m tero tui --offline",
            fill=ACCENT_GREEN,
            font=font_c_code,
        )

        t3 = "Licencia MIT · 100% Python & OpenTUI · Sin suscripciones propietarias"
        w3 = font_c_sub.getbbox(t3)[2] - font_c_sub.getbbox(t3)[0]
        draw.text((cx - w3 // 2, box_y + 400), t3, fill=TEXT_MUTED, font=font_c_sub)

    render_subtitles(draw, scene["caption"])
    return canvas


def render_scene_frame(scene: dict, progress: float = 0.0) -> Image.Image:
    """Renderiza un fotograma completo con la barra de progreso incluida."""
    base = render_scene_base(scene)
    frame = base.copy()
    draw = ImageDraw.Draw(frame)
    draw_progress_bar(draw, progress)
    return frame


def synthesize_audio(scene: dict, temp_dir: Path) -> tuple[Path, float]:
    raw_audio_path = temp_dir / f"audio_raw_{scene['id']}.mp3"
    padded_audio_path = temp_dir / f"audio_{scene['id']}.mp3"
    voice = "es-CL-LorenzoNeural"

    cmd = [
        sys.executable,
        "-m",
        "edge_tts",
        "--voice",
        voice,
        "--text",
        scene["speech"],
        "--write-media",
        str(raw_audio_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Añadir 0.4s de silencio al final para que la narración respire y las transiciones no sean abruptas
    pad_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(raw_audio_path),
        "-af",
        "apad=pad_dur=0.4",
        "-c:a",
        "libmp3lame",
        str(padded_audio_path),
    ]
    subprocess.run(pad_cmd, check=True, capture_output=True)

    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(padded_audio_path),
    ]
    res = subprocess.run(probe_cmd, check=True, capture_output=True, text=True)
    duration = float(res.stdout.strip())
    return padded_audio_path, duration


def render_scene_video(
    scene: dict,
    audio_path: Path,
    duration: float,
    scene_idx: int,
    total_scenes: int,
    temp_dir: Path,
) -> Path:
    scene_mp4 = temp_dir / f"clip_{scene['id']}.mp4"
    fps = 30
    total_frames = max(30, int(duration * fps))

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
        "-b:a",
        "192k",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-shortest",
        str(scene_mp4),
    ]

    base_frame = render_scene_base(scene)
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for idx in range(total_frames):
            progress = (scene_idx + idx / total_frames) / total_scenes
            frame_img = base_frame.copy()
            draw = ImageDraw.Draw(frame_img)
            draw_progress_bar(draw, progress)
            try:
                proc.stdin.write(frame_img.tobytes())
            except BrokenPipeError:
                break
    finally:
        if proc.stdin and not proc.stdin.closed:
            try:
                proc.stdin.close()
            except Exception:
                pass
        proc.wait()

    if proc.returncode != 0:
        err_msg = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        raise RuntimeError(f"Error renderizando escena {scene['id']}: {err_msg}")

    return scene_mp4


def format_srt_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{milis:03d}"


def build_full_video():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="tero_video_"))
    print("🎬 Iniciando producción de video de landing en español...")
    print(f"📁 Directorio temporal: {temp_dir}")

    scene_clips: list[Path] = []
    srt_entries: list[str] = []
    accumulated_time = 0.0

    total_scenes = len(SCENES)
    for idx, scene in enumerate(SCENES):
        print(f"\n[{idx + 1}/{total_scenes}] Generando escena: {scene['id']} ({scene['title']})")
        audio_path, duration = synthesize_audio(scene, temp_dir)
        print(f"   🔊 Audio sintetizado: {duration:.2f}s (es-CL-LorenzoNeural)")

        start_srt = format_srt_time(accumulated_time)
        end_srt = format_srt_time(accumulated_time + duration - 0.2)
        srt_entries.append(f"{idx + 1}\n{start_srt} --> {end_srt}\n{scene['caption']}\n")
        accumulated_time += duration

        print("   🖼️  Renderizando fotogramas y codificando H.264/AAC...")
        clip_path = render_scene_video(scene, audio_path, duration, idx, total_scenes, temp_dir)
        scene_clips.append(clip_path)

    OUTPUT_SRT.write_text("\n".join(srt_entries), encoding="utf-8")
    print(f"\n📝 Subtítulos SRT guardados en: {OUTPUT_SRT}")

    print(f"\n🎞️  Concatenando {len(scene_clips)} escenas en el video final...")
    concat_list_file = temp_dir / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            f.write(f"file '{clip.resolve()}'\n")

    concat_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list_file),
        "-c",
        "copy",
        str(OUTPUT_MP4),
    ]
    subprocess.run(concat_cmd, check=True)

    shutil.rmtree(temp_dir, ignore_errors=True)

    probe_final = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,bit_rate",
            "-of",
            "json",
            str(OUTPUT_MP4),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    final_info = json.loads(probe_final.stdout)
    dur = float(final_info["format"]["duration"])
    size_mb = int(final_info["format"]["size"]) / (1024 * 1024)
    format_bitrate = int(final_info["format"].get("bit_rate", 0)) // 1000

    streams = final_info.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    v_codec = video_stream.get("codec_name", "h264")
    v_res = f"{video_stream.get('width', 1920)}x{video_stream.get('height', 1080)}"
    v_fps = video_stream.get("r_frame_rate", "30/1")
    v_br = (
        int(video_stream.get("bit_rate", 0)) // 1000 if video_stream.get("bit_rate") else "variable"
    )

    a_codec = audio_stream.get("codec_name", "aac")
    a_br = (
        int(audio_stream.get("bit_rate", 0)) // 1000 if audio_stream.get("bit_rate") else "variable"
    )

    print("\n✅ ¡Video de landing en español generado exitosamente!")
    print(f"   🎥 Archivo: {OUTPUT_MP4}")
    print(f"   ⏱️  Duración: {dur:.2f} segundos ({dur / 60:.2f} minutos)")
    print(f"   💾 Tamaño: {size_mb:.2f} MB")
    print(f"   🎯 Resolución: {v_res} @ {v_fps} ({v_codec})")
    print(
        f"   📊 Bitrate Video: {v_br} kbps | Bitrate Audio: {a_br} kbps ({a_codec}) | Total: {format_bitrate} kbps"
    )


if __name__ == "__main__":
    build_full_video()
