"""Regenera build_landing_video_en_v2.py desde la versión ES (guion + literales EN)."""

from pathlib import Path

#!/usr/bin/env python3
"""Genera build_en_v2.py desde build_es_v2.py (guion + literales EN)."""

src = open(Path(__file__).parent / "build_landing_video_es_v2.py").read()

R = [
    ('AUDIO_DIR = HERE / "audio"', 'AUDIO_DIR = HERE / "audio_en"'),
    ('VOICE = "es-CL-LorenzoNeural"', 'VOICE = "en-US-AndrewNeural"'),
    ('"tero-demo-es', '"tero-demo-en'),
    (
        'CHAPTERS = ["inicio", "privacidad", "arquitectura", "responde", "crea", "compuerta", "sello", "NEE", "bedrock", "cierre"]',
        'CHAPTERS = ["start", "privacy", "architecture", "answer", "create", "gate", "seal", "NEE", "bedrock", "close"]',
    ),
    ('"·  agente docente conversacional"', '"·  conversational teacher agent"'),
    ('("Sello criptográfico docente", ACC)', '("Teacher cryptographic seal", ACC)'),
    ('"Vanellus chilensis · queltehue"', '"Vanellus chilensis · the tero bird"'),
    (
        '"tus fuentes, tu criterio", fill=TXT, font=F(36, True))',
        '"your sources, your judgment", fill=TXT, font=F(36, True))',
    ),
    ('"El tero avisa. Tú decides."', '"The tero alerts. You decide."'),
    (
        '"carpeta-demo · OpenTUI · modo real del producto"',
        '"carpeta-demo · OpenTUI · the real product"',
    ),
    (
        '("1 · TU CARPETA", "El cuento que leíste, el OA marcado, el vocabulario de la semana: la única fuente de verdad.", ACC)',
        '("1 · YOUR FOLDER", "The story you read, the marked objective, the week\'s vocabulary: the only source of truth.", ACC)',
    ),
    (
        '("2 · LEY 21.719", "Notas, salud y asistencia nunca viajan a la nube: quedan en tu equipo, siempre.", OK)',
        '("2 · LEY 21.719", "Grades, health and attendance never leave your machine.", OK)',
    ),
    (
        '("3 · TU APROBACIÓN", "El agente propone en memoria. Nada se escribe sin tu «y» o tu «dale».", WARN)',
        "(\"3 · YOUR APPROVAL\", \"The agent proposes in memory. Nothing is written without your 'y' or your 'dale'.\", WARN)",
    ),
    (
        '("Strands Multi-Agent Graph", "GraphBuilder · redactor + auditor", ACC)',
        '("Strands Multi-Agent Graph", "GraphBuilder · drafter + auditor", ACC)',
    ),
    (
        '("OpenTelemetry", "StrandsTelemetry · cada turno trazado", (188, 140, 255))',
        '("OpenTelemetry", "StrandsTelemetry · every turn traced", (188, 140, 255))',
    ),
    (
        '("Compuerta en memoria", "cero write tools · host escribe", OK)',
        '("In-memory approval gate", "zero write tools · host writes", OK)',
    ),
    ('"fotocopia lista · LaTeX · sello al pie"', '"handout ready · LaTeX · sealed footer"'),
    ('"el pie del material lleva el sello"', '"the printed footer carries the seal"'),
    ('"certificado del artefacto"', '"artifact certificate"'),
    (
        '("amazon.nova-lite-v1:0", 1.04, "modelo principal · rápido y de bajo costo", ACC)',
        '("amazon.nova-lite-v1:0", 1.04, "primary model · fast, low cost", ACC)',
    ),
    (
        '("zai.glm-4.7-flash", 0.33, "esquemas NEE · Decreto 83 estricto", OK)',
        '("zai.glm-4.7-flash", 0.33, "NEE schemas · strict Decreto 83", OK)',
    ),
    (
        '("minimax.minimax-m2.5", 9.72, "rúbricas y pautas completas", (188, 140, 255))',
        '("minimax.minimax-m2.5", 9.72, "complete rubrics and grids", (188, 140, 255))',
    ),
    (
        '("tero-offline (scripted)", 0.01, "sin conexión · Strands real · reproducible", WARN)',
        '("tero-offline (scripted)", 0.01, "offline · real Strands · reproducible", WARN)',
    ),
    (
        '"5 modelos · 4 trayectorias pedagógicas reales · benchmark en el repo"',
        '"5 models · 4 real teaching journeys · benchmark in the repo"',
    ),
    (
        '"demo honesta: offline = tero-offline, nunca una llamada fingida a Bedrock"',
        '"honest demo: offline = tero-offline, never a faked Bedrock call"',
    ),
    (
        '("MIT", OK), ("sello docente criptográfico", ACC)',
        '("MIT", OK), ("teacher cryptographic seal", ACC)',
    ),
    (
        '"tu aula, tus fuentes, tu criterio", fill=TXT, font=f_m, anchor="ma")',
        '"your classroom, your sources, your judgment", fill=TXT, font=f_m, anchor="ma")',
    ),
    (
        '"Hackathon Agents for Humans · AWS + Strands Agents SDK"',
        '"Agents for Humans Hackathon · AWS + Strands Agents SDK"',
    ),
]

for a, b in R:
    if a not in src:
        raise SystemExit(f"NO ENCONTRADO: {a[:70]}")
    src = src.replace(a, b)

s_start = src.index("SCENES: list[Scene] = [")
s_end = src.index("\n]", s_start)
scenes_en = """SCENES: list[Scene] = [
    Scene(
        "s1_hero", "Start", "tero · conversational teacher agent",
        [
            Sent("This is tero: the conversational teacher agent for Chilean classrooms.",
                 "tero · the conversational teacher agent for Chilean classrooms"),
            Sent("Tomorrow's photocopy, built from your own classroom folder. The agent proposes; the teacher decides.",
                 "tomorrow's photocopy, from your own folder · the agent proposes, the teacher decides"),
        ],
        lead=0.7, tail=0.8,
    ),
    Scene(
        "s2_priv", "Privacy", "your folder · the single source of truth",
        [
            Sent("Your folder is the single source of truth: the story you read, the objective you marked, this week's vocabulary.",
                 "your folder is the single source of truth"),
            Sent("And under Chile's Ley 21.719, student data never touches the cloud.",
                 "Ley 21.719: student data never touches the cloud"),
            Sent("Everything stays on your machine, and nothing is written without your explicit approval.",
                 "nothing is written without your explicit approval"),
        ],
    ),
    Scene(
        "s3_arch", "Architecture", "Strands Multi-Agent Graph on Amazon Bedrock",
        [
            Sent("Under the hood, tero orchestrates a Multi-Agent Graph with Strands Agents on Amazon Bedrock.",
                 "Multi-Agent Graph · Strands Agents · Amazon Bedrock"),
            Sent("A pedagogical drafter prepares the material, and a quality auditor checks curriculum alignment.",
                 "pedagogical drafter + curriculum quality auditor"),
            Sent("Nova Lite, GLM 4.7 Flash and MiniMax M2.5 run inference, with every turn traced in OpenTelemetry.",
                 "Model Trio + OpenTelemetry traces on every turn"),
            Sent("Zero write tools for the model: the folder never leaves the machine.",
                 "zero write tools · the folder never leaves"),
        ],
    ),
    Scene(
        "s4_intent_a", "Intent A", "answer without writing",
        [
            Sent("Write in natural Spanish and ask what is in the folder.",
                 "ask in natural Spanish, no menus"),
            Sent("tero answers precisely: five sources, cited one by one. And it writes no files.",
                 "precise answers · zero files written"),
        ],
        lead=1.0,
    ),
    Scene(
        "s5_intent_b", "Intent B", "create material with verified citations",
        [
            Sent("Ask it for a fourth-grade reading comprehension assessment.",
                 "\\u201cPrepara una evaluación de comprensión lectora para 4° básico\\u201d"),
            Sent("tero discusses the details and builds the proposal in memory: summary, preview, and citations verified against your files.",
                 "in-memory proposal · citations verified against your sources"),
            Sent("Warnings inform; they never block.",
                 "warnings inform · they never block"),
        ],
        lead=1.0,
    ),
    Scene(
        "s6_gate", "Approval gate", "approve and the handout is born",
        [
            Sent("Nothing touches disk until you approve: press Y, or simply say dale.",
                 "approve with [y] or \\u201cdale\\u201d · nothing is written before"),
            Sent("The host writes to derivados and compiles to LaTeX: the photocopy is ready for tomorrow.",
                 "the host writes to derivados/ and compiles to LaTeX"),
        ],
        lead=1.0,
    ),
    Scene(
        "s6b_seal", "Teacher seal", "cryptographic signature · proof of pedagogical agency",
        [
            Sent("Here is what a chatbot does not have: every approved material leaves with a cryptographic seal in the teacher's name.",
                 "every material, cryptographically sealed in your name"),
            Sent("The seal binds the hash of your sources, the derivative, the model, and the full trace: human-approved criterion in a local ledger.",
                 "sources + derivative + model + trace hashes · .tero/decisiones/"),
            Sent("verify-seal checks integrity in seconds: a teacher approved this, with her sources, and nobody altered it.",
                 "verify-seal · integrity verified in seconds"),
        ],
        lead=1.0,
    ),
    Scene(
        "s7_nee", "Intent C", "NEE adaptation · Decreto 83",
        [
            Sent("For a student with dyslexia, ask for the adaptation.",
                 "\\u201cAdapta la evaluación del cóndor para un estudiante con dislexia\\u201d"),
            Sent("tero applies Decreto 83: access supports first, extended time and two-step instructions, before touching objectives.",
                 "Decreto 83: access supports first, objectives later"),
            Sent("It delivers a new version with traceable origin. The original stays intact, hash-verified.",
                 "new version with origin · the original stays intact"),
        ],
        lead=1.0,
    ),
    Scene(
        "s8_trio", "Amazon Bedrock", "live model trio · honest tero-offline",
        [
            Sent("Live diagnostics validate the Bedrock model trio.",
                 "check-aws live · Amazon Bedrock Model Trio"),
            Sent("Nova Lite, fast and inexpensive; GLM 4.7 Flash, strict on NEE schemas; and MiniMax, with complete rubrics.",
                 "Nova Lite · GLM 4.7 Flash · MiniMax M2.5"),
            Sent("And with no internet? tero-offline: a real Strands model, reproducible, never faking a cloud call.",
                 "tero-offline: real Strands, never faking a cloud call"),
        ],
    ),
    Scene(
        "s9_close", "Open source", "your classroom, your sources, your judgment",
        [
            Sent("tero gives Sunday afternoons back to the people who teach.",
                 "tero gives Sunday afternoons back to teachers"),
            Sent("And every material is signed in your name.",
                 "every material, signed in your name"),
            Sent("Open source, MIT license, for the Agents for Humans Hackathon by AWS.",
                 "MIT · open source · Agents for Humans Hackathon by AWS"),
            Sent("Your classroom, your sources, your judgment.",
                 "tero · your classroom, your sources, your judgment"),
        ],
    ),
"""
src = src[:s_start] + scenes_en + src[s_end:]
(Path(__file__).parent / "build_landing_video_en_v2.py").write_text(src)
print("build_en_v2.py generado OK")
