"""The public GitHub page is one OpenTUI window showing the conversational session.

The landing virtualizes the real OpenTUI. There are no rumbos 1–4, no typed
plan `a`/`e`/`x`, no numbered clarifications and no gate `s` / `n` / `b` / `c`:
the person writes, the agent infers the intent (a responder, b crear,
c editar/adaptar) and nothing is written without explicit approval.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DOCS = ROOT / "docs"
FRAMES = SITE / "assets" / "tui" / "frames"

# Flujo viejo: no puede quedar ni en el HTML ni en la simulación.
FLUJO_VIEJO = [
    "rumbo",
    "data-gate",
    "data-rumbo",
    "Espera un rumbo",
    "elige un rumbo",
    "la puerta se enciende",
    "Planificar",
    "leyendo-",
    "plan-1",
    "puerta-1",
    "borradores/",
    "WARNINGS_BLOCK_S",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _site_texts() -> dict[str, str]:
    return {
        "index.html": _read(SITE / "index.html"),
        "ficha.js": _read(SITE / "ficha.js"),
        "styles.css": _read(SITE / "styles.css"),
        "404.html": _read(SITE / "404.html"),
    }


def test_ficha_landing_is_the_github_page():
    html = _flat(_read(SITE / "index.html"))
    css = _read(SITE / "styles.css")
    js = _read(SITE / "ficha.js")
    grid = _read(SITE / "tui-grid.js")

    assert 'lang="es"' in html
    assert "tus fuentes, tu criterio" in html
    assert "tero-offline" in html
    assert 'data-offline-model="tero-offline"' in html

    # El flujo por pasos no existe en la cara pública.
    for old in FLUJO_VIEJO:
        assert old not in html, old
        assert old not in js, old
    assert "forzar" not in js
    assert not (SITE / "tui" / "frames" / "puerta-2.txt").exists()

    # La sesión conversacional: intenciones a/b/c, propuesta y aprobación.
    assert "conversa" in html or "Conversa" in html
    assert "responde" in html
    assert "adapta" in html
    for escena in ("responder", "crear", "descartar", "adaptar"):
        assert f'data-escena="{escena}"' in html
    assert 'data-decision="aprobar"' in html
    assert 'data-decision="descartar"' in html
    assert "aprobación" in html
    assert "derivados/" in html

    # Aprobación con y o escribiendo en el hilo; n descarta.
    assert "ESCENAS" in js
    assert 'decision: "dale"' in js
    assert 'decision: "n"' in js
    assert 'decision: "y"' in js
    assert "classifyDecision" in js
    assert "applyDecision" in js
    assert '"aprobar"' in js and '"descartar"' in js
    assert "dale" in js
    assert '"?": ' not in js

    # La TUI nunca escribe: escribe el host, y solo tras aprobación.
    assert "La TUI nunca escribe archivos" in js
    assert "El host escribió" in js
    assert "el host escribe" in html
    assert "no se escribió nada" in js
    assert "readOnly" not in js

    # Las tres intenciones y las fases del protocolo están a la vista.
    for fase in ("idle", "pensando", "esperando_aprobacion", "listo", "error"):
        assert fase in js, fase
    assert "esperando_aprobacion" in js
    assert "notas_nee" in js or "apoyos y criterios NEE" in js
    assert "propuesta-adaptar" in js
    assert "vista previa" in js.lower()
    assert "evidencia" in js

    # Assets de la ventana y del papel.
    assert "AgentCore no es el producto" in html
    assert "amazon.nova-lite-v1:0" in html
    assert "fuentes/" in html
    assert 'id="consulta"' in html
    assert 'id="archivo"' in html
    assert "eval-cuento/p1.png" in js
    assert "terraform" not in html
    assert "Get started" not in html
    assert "Sign up" not in html
    assert "enterSession" not in js
    assert 'id="session"' not in html

    # La ventana: una sola OpenTUI, sin segundo titlebar.
    assert "--tui-bg: #0b0d10" in css
    assert "--tui-accent: #82aaff" in css
    assert "--accent: #82aaff" in css
    assert 'id="tui-grid"' in html
    assert 'id="app"' in html
    assert "window-chrome" in html
    assert "window-chrome sr-only" in html
    assert html.count("window-chrome") == 1
    assert "term-chrome" not in html
    assert 'id="splash"' not in html
    assert "wave.js" not in html
    assert not (SITE / "wave.js").exists()
    assert "asistente pedagógico" in html
    assert "Vanellus chilensis" in html
    assert "queltehue" in html
    assert "El tero avisa" in html
    assert "JetBrains Mono" in css
    assert ".hoja-frame" in css
    assert "photocopied" in css.lower()
    header = "\n".join(css.splitlines()[:8]).lower()
    assert "opentui" in header or "tui" in header
    assert "#82aaff" in grid
    assert "╭" in grid

    # El sello REVISAR sigue siendo la fotocopia, no un CTA.
    assert 'id="stamp-label"' in html
    assert "REVISAR" in html
    assert "stamp-label" in css
    assert ".stamp-label" in css

    assert "tui-grid.js" in html
    assert "styles.css?v=conversacional" in html
    assert "tui-grid.js?v=conversacional" in html
    assert "ficha.js?v=conversacional" in html
    assert "left: var(--cell-w, 10px)" in css
    assert "top: var(--cell-h, 24px)" in css
    assert "left: 8%" not in css
    assert 'host.style.setProperty("--cell-w"' in js
    assert "min-height: calc(100vh" not in css
    assert "background: var(--tui-bg)" in css
    assert "#consulta" in css
    assert "Never a second column" in css or "display: none !important" in css
    assert "paintFrame" in grid
    assert "paintShot" in grid
    assert "drawWindow" in grid
    assert "innerX" in grid
    assert "promptBoxFromFrame" in grid
    assert "viewportBudget" in grid
    assert "paddingLeft" in grid
    assert 'scale >= 0.999 ? "pixelated"' in grid
    assert "html,\nbody {\n  margin: 0;\n  min-height: 100%;\n  overflow: hidden;\n}" in css
    assert "padding: 12px" in css
    assert "justify-content: flex-start" in css
    assert ".window-chrome.sr-only" in css
    assert "image-rendering: pixelated" in css
    assert ".tui-prompt:not(.is-typing)" in css
    assert "loadFrames" in js
    assert "assets/tui/frames/" in js
    assert "conversacional" in js
    assert "frames.help" in js
    assert "~/carpeta-tui" not in html
    assert 'id="window-path"' in html
    assert "blitCanvas" in grid
    assert "createImageBitmap" in grid
    assert "colorSpaceConversion" in grid
    assert 'id="tui-shot"' in html
    assert ".tui-shot-src" in css
    assert '$("tui-canvas")' in js
    assert "~/tero" in html
    assert 'textContent = "~/tero"' in js


def test_ficha_frames_are_conversational_and_referenced():
    index = json.loads(_read(FRAMES / "index.json"))
    names = [item["name"] for item in index["frames"]]
    assert names, "index.json sin frames"

    # Los frames que la simulación pide existen en el index y en disco.
    js = _read(SITE / "ficha.js")
    declared = re.findall(r'^\s*"([a-z-]+)",$', js, flags=re.M)
    for name in declared:
        assert name in names, f"{name} no está en index.json"
    for required in (
        "home",
        "respuesta",
        "conversacion",
        "conversacion-streaming",
        "propuesta",
        "propuesta-adaptar",
        "escrito",
        "escrito-adaptar",
        "descartado",
        "help",
        "error",
    ):
        assert required in names, required
        assert required in js, required

    # Nada del flujo viejo quedó en el directorio de frames.
    leftovers = [
        path.name
        for path in FRAMES.glob("*")
        if re.match(r"^(encargo|leyendo|plan|puerta)", path.name)
    ]
    assert leftovers == [], leftovers

    for item in index["frames"]:
        name = item["name"]
        for suffix in ("json", "txt", "html", "png"):
            path = FRAMES / f"{name}.{suffix}"
            assert path.is_file(), path
        png = FRAMES / f"{name}.png"
        assert png.stat().st_size > 8_000, png
        text = _read(FRAMES / f"{name}.txt")
        lines = [line for line in text.splitlines() if line]
        assert lines[0].startswith("╭─ tero"), name
        assert lines[-1].startswith("╰"), name
        assert "examples/carpeta-demo" in lines[-1], name
        assert len({len(line) for line in text.splitlines() if line}) == 1, name

    home = _read(FRAMES / "home.txt")
    assert "tus fuentes, tu criterio" in home
    assert "▀▀▀▀███████" in home
    assert "Pregunta, explora o crea…" in home
    assert "El agente responde, crea o adapta · tú apruebas" in home
    assert "5 fuentes" in home
    assert "recientes" in home
    assert "rumbo" not in home.lower()
    assert "[1] Planificar" not in home

    propuesta = _read(FRAMES / "propuesta.txt")
    assert "crear · evaluación" in propuesta
    assert "vista previa · markdown" in propuesta
    assert "evidencia" in propuesta
    assert "? " in propuesta and "✓" in propuesta
    assert "avisos (no bloquean)" in propuesta
    assert "¿escribo el archivo?" in propuesta
    assert "[y] aprobar" in propuesta
    assert "[n] descartar" in propuesta
    assert "[s]" not in propuesta and "[b]" not in propuesta and "[c]" not in propuesta

    adaptar = _read(FRAMES / "propuesta-adaptar.txt")
    assert "adaptar (NEE) · evaluación" in adaptar
    assert "Evaluación adaptada" in adaptar
    assert "origen" in adaptar
    assert "cambios" in adaptar
    assert "apoyos y criterios NEE" in adaptar
    assert "Tiempo extendido" in adaptar
    assert "[y] aprobar" in adaptar

    escrito = _read(FRAMES / "escrito.txt")
    assert "escrito · crear" in escrito
    assert "derivados/" in escrito
    adaptada = _read(FRAMES / "escrito-adaptar.txt")
    assert "escrito · adaptar" in adaptada
    assert "adaptada" in adaptada

    respuesta = _read(FRAMES / "respuesta.txt")
    assert "¿Qué tengo en la carpeta?" in respuesta
    assert "Puedo responder sobre ellas, crear material nuevo o adaptar" in respuesta
    assert "decidir" not in respuesta.lower()

    descartado = _read(FRAMES / "descartado.txt")
    assert "descartado · no se escribió nada" in descartado

    theme = json.loads(_read(FRAMES / "theme.json"))
    assert theme["accent"] == "#82aaff"
    assert theme["bg"] == "#0b0d10"
    assert theme["border"] == "#4c566a"
    css = _read(SITE / "styles.css")
    assert "--border: #4c566a" in css
    assert 'border: "#4c566a"' in _read(SITE / "tui-grid.js")


def test_ficha_referenced_assets_exist():
    """Ningún asset referenciado por el HTML o la simulación puede faltar."""
    html = _read(SITE / "index.html")
    js = _read(SITE / "ficha.js")
    css = _read(SITE / "styles.css")
    grid = _read(SITE / "tui-grid.js")

    refs: set[str] = set()
    for blob in (html, js, css, grid):
        refs.update(re.findall(r"\./(assets/[\w./-]+\.(?:png|svg|webp|txt|json))", blob))
        refs.update(re.findall(r"assets/tui/frames/([\w-]+)\.png", blob))
    frames_refs = re.findall(r"assets/tui/frames/([\w-]+)\.png", js + grid)
    assert refs, "sin assets referenciados"
    for ref in sorted(refs):
        if ref.endswith(".png") and not ref.startswith("assets/"):
            continue
        path = SITE / ref
        assert path.is_file(), ref
        assert path.stat().st_size > 0, ref
    for name in frames_refs:
        assert (FRAMES / f"{name}.png").is_file(), name

    for local in ("./styles.css", "./tui-grid.js", "./ficha.js", "./assets/tero-mark.svg"):
        assert local in html, local
        assert (SITE / local.lstrip("./")).is_file(), local

    for folder, n in (
        ("eval-cuento", 3),
        ("guia-sistemas", 3),
        ("eval-sistemas", 3),
        ("plan", 3),
    ):
        for i in range(1, n + 1):
            path = SITE / "assets" / "hojas" / folder / f"p{i}.png"
            assert path.is_file(), path
            assert path.stat().st_size > 10_000, path


def test_ficha_assets_and_pages_workflow():
    assert (SITE / "assets" / "tero-og.png").is_file()
    assert (SITE / "assets" / "tero-stamp.png").is_file()
    assert (SITE / "assets" / "tero-mark.svg").is_file()
    assert (SITE / "assets" / "tero-wordmark.svg").is_file()
    assert (SITE / "assets" / "tero.txt").is_file()
    assert (SITE / "brand.json").is_file()
    assert (SITE / "tui-grid.js").is_file()
    assert (SITE / "stamp.py").is_file()
    assert not (SITE / "assets" / "tui" / "puerta.webp").exists()
    assert not list((SITE / "assets" / "tui").glob("puerta*.webp"))
    assert not list((SITE / "assets" / "tui").glob("plan*.webp"))
    brand = _read(SITE / "brand.json")
    assert "82AAFF" in brand
    assert "Vanellus chilensis" in brand
    mark = _read(SITE / "assets" / "tero.txt")
    assert "Vanellus chilensis" in mark
    assert "queltehue" in mark
    assert "▀▀▀▀███████" in mark
    mark_svg = _read(SITE / "assets" / "tero-mark.svg")
    assert "Vanellus chilensis" in mark_svg
    assert "<path" in mark_svg
    home_html = _read(FRAMES / "home.html")
    assert "window-chrome sr-only" in home_html
    assert 'class="traffic"' not in home_html
    assert "tui-grid.js" in home_html
    assert "fitHost" in home_html
    for html_path in FRAMES.glob("*.html"):
        if html_path.name == "gallery.html":
            continue
        frame_html = _read(html_path)
        assert "window-chrome sr-only" in frame_html, html_path.name
        assert 'class="traffic"' not in frame_html, html_path.name
    assert (SITE / "404.html").is_file()
    not_found = _flat(_read(SITE / "404.html"))
    assert "unknown_source" in not_found
    assert "no bloquea" in not_found
    assert "window-chrome" in not_found
    assert "Nada se escribe sin tu aprobación" in not_found
    assert "la TUI nunca escribe archivos" in not_found
    assert "la puerta" not in not_found
    workflow = _read(ROOT / ".github" / "workflows" / "pages.yml")
    assert "path: site" in workflow
    assert "deploy-pages" in workflow
    assert "enablement: true" not in workflow
    assert "repos/${GITHUB_REPOSITORY}/pages" in workflow
    assert "enabled=false" in workflow
    assert "site/stamp.py" in workflow
    sitio = _read(DOCS / "SITIO.md")
    assert "settings/pages" in sitio
    assert "Resource not accessible by integration" in sitio
    assert "marcorojasb.github.io/tero" in sitio
    assert "queltehue" in sitio.lower()
    assert "stamp.py" in sitio
    assert "tui-grid.js" in sitio
    assert "capture-frames" in sitio
    assert "compose-og" in sitio
    assert "una sola ventana" in sitio.lower() or "una ventana" in sitio.lower()
    assert "rumbo" not in sitio.lower()
    assert "planificar" not in sitio.lower()
    assert "`s` / `n` / `b` / `c`" not in sitio
    assert "respuesta" in sitio.lower()
    assert "aprobación" in sitio.lower()
    readme = _read(ROOT / "README.md")
    assert "settings/pages" in readme
    agents = _read(ROOT / "AGENTS.md")
    assert "splash + ASCII wave" not in agents
    assert "OpenTUI" in agents
    arch = _read(ROOT / "ARCHITECTURE.md")
    assert "not a splash wave" in arch.lower()
    assert "OpenTUI of tero" in arch
    contrib = _read(ROOT / "CONTRIBUTING.md")
    assert "ola ASCII" not in contrib
    assert "OpenTUI" in contrib


def test_ficha_serve_maps_missing_path_to_extraviada_sheet():
    import importlib.util
    import threading
    from http.client import HTTPConnection

    spec = importlib.util.spec_from_file_location("ficha_serve", SITE / "serve.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    from functools import partial
    from http.server import ThreadingHTTPServer

    handler = partial(mod.FichaHandler, directory=str(SITE))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = httpd.server_address
        conn = HTTPConnection(host, port, timeout=3)
        conn.request("GET", "/no-existe")
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == 404
        assert "Esta hoja no está en la carpeta" in body
        assert "unknown_source" in body
        assert "tero-offline" in body
        conn.close()
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_docs_record_pr8_decision_and_index():
    puerta = _read(DOCS / "PUERTA-Y-PR8.md")
    assert "no se mergea" in puerta.lower() or "no se mergea" in puerta
    assert "SIGALRM" in puerta
    assert "thin_evidence" in puerta
    assert "unknown_source" in puerta
    assert "prepara" in puerta

    index = _read(DOCS / "README.md")
    assert "PUERTA-Y-PR8.md" in index
    assert "SITIO.md" in index
    assert "AWS-GRATIS.md" in index
    assert "hackathon/README.md" in index

    aws = _read(DOCS / "AWS-GRATIS.md")
    assert "forms.gle/6sjzKiX6bKUMA5NEA" in aws
    assert "amazon.nova-lite-v1:0" in aws
    assert "AgentCore Harness es un chat administrado" in aws
    assert "modelaccess" not in aws
    assert "model-catalog" in aws
    assert "se habilitan solos" in aws
    assert (DOCS / "hackathon" / "architecture.svg").is_file()
    png = DOCS / "hackathon" / "architecture.png"
    assert png.is_file()
    assert png.stat().st_size > 80_000
    assert (DOCS / "hackathon" / "DEVPOST.md").is_file()

    readme = _read(ROOT / "README.md")
    assert "marcorojasb.github.io/tero" in readme
    assert "site/assets/tero-og.png" in readme
    assert "PUERTA-Y-PR8.md" in readme
    assert "forzar" in readme  # listed as out of scope
