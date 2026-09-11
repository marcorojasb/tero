"""The public GitHub page is one OpenTUI window, not an AgentCore hero."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_ficha_landing_is_the_github_page():
    html = _flat(_read(SITE / "index.html"))
    css = _read(SITE / "styles.css")
    js = _read(SITE / "ficha.js")

    assert 'lang="es"' in html
    assert "tus fuentes, tu criterio" in html
    assert "tero-offline" in html
    assert 'data-offline-model="tero-offline"' in html
    assert 'data-warnings-block-s="false"' in html

    for key in ("s", "n", "b", "c"):
        assert f'data-gate="{key}"' in html
    for rumbo in ("1", "2", "3", "4"):
        assert f'data-rumbo="{rumbo}"' in html

    assert "AgentCore no es el producto" in html
    assert "derivados/" in html
    assert "borradores/" in html
    assert "fuentes/" in html
    assert "amazon.nova-lite-v1:0" in html
    assert 'id="consulta"' in html
    assert 'id="archivo"' in html
    assert "hojas/guia-sistemas" in js or "guia-sistemas/p1.png" in js

    assert "--tui-bg: #0b0d10" in css
    assert "--tui-accent: #82aaff" in css
    assert "--accent: #82aaff" in css
    assert 'id="tui-grid"' in html
    assert 'id="app"' in html
    assert "window-chrome" in html
    assert "window-chrome sr-only" in html
    assert "term-chrome" not in html
    assert 'id="splash"' not in html
    assert 'id="wave"' not in html
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
    assert html.count("window-chrome") == 1
    grid = _read(SITE / "tui-grid.js")
    assert "#82aaff" in grid
    assert "╭" in grid
    assert "Planificar" in grid

    assert "WARNINGS_BLOCK_S = false" in js
    assert "function canAccept" in js
    assert "tero-offline" in js
    assert "draft_artifact" in js
    assert "list_sources" in js
    assert "unverified_citation" in js
    assert "92.5" in js
    assert "94.9" in js
    assert "sistemas" in js.lower()
    assert "Selección múltiple" in js or "selección múltiple" in js
    assert "Verdadero o falso" in js or "verdadero o falso" in js
    assert "Desarrollo" in js
    # The rejected PR #8 override must not appear as a gate.
    assert "forzar" not in js
    assert "tú decides" in html
    assert "vos decidís" not in html
    assert "vos decidís" not in js
    assert "Get started" not in html
    assert "Sign up" not in html
    assert "enterSession" not in js
    assert 'id="session"' not in html
    assert "tui-grid.js" in html
    assert "styles.css?v=chilensis" in html
    assert "tui-grid.js?v=chilensis" in html
    assert "ficha.js?v=chilensis" in html
    assert "left: var(--cell-w, 10px)" in css
    assert "top: var(--cell-h, 24px)" in css
    assert "left: 8%" not in css
    assert 'host.style.setProperty("--cell-w"' in js
    assert "min-height: calc(100vh" not in css
    assert "0 24px 70px" not in css
    assert "border-radius: 10px" not in css
    assert "background: var(--tui-bg)" in css
    assert '$("consulta").hidden = false' not in js
    assert '$("consulta").hidden = true' in js
    assert '$("prompt").readOnly' in js
    assert 'state.phase === "esperando_criterio"' in js
    assert 'const editable = inPrompt && !$("prompt").readOnly' in js or "editable = inPrompt" in js
    assert "#consulta" in css
    assert "Never a second column" in css or "display: none !important" in css
    assert "paintFrame" in grid
    assert "paintShot" in grid
    assert "drawWindow" in grid
    assert "innerX" in grid
    assert "promptBoxFromFrame" in grid
    assert "viewportBudget" in grid
    assert "innerHeight - 96" not in grid
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
    assert "?v=chilensis" in js or "chilensis" in js
    assert "plan-2" in js
    assert "puerta-2" in js
    assert "leyendo-2" in js
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
    assert '$("window-path").textContent = "~/tero"' in js or 'textContent = "~/tero"' in js


def test_ficha_assets_and_pages_workflow():
    assert (SITE / "assets" / "tero-og.png").is_file()
    assert (SITE / "assets" / "tero-stamp.png").is_file()
    assert (SITE / "assets" / "tero-mark.svg").is_file()
    assert (SITE / "assets" / "tero-wordmark.svg").is_file()
    assert (SITE / "assets" / "tero.txt").is_file()
    assert (SITE / "brand.json").is_file()
    assert (SITE / "tui-grid.js").is_file()
    assert (SITE / "stamp.py").is_file()
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
    home_html = _read(SITE / "assets" / "tui" / "frames" / "home.html")
    assert "window-chrome sr-only" in home_html
    assert 'class="traffic"' not in home_html
    assert "tui-grid.js" in home_html
    assert "fitHost" in home_html
    home_frame = _read(SITE / "assets" / "tui" / "frames" / "home.txt")
    home_lines = [line for line in home_frame.splitlines() if line]
    assert home_lines[0].startswith("╭─ tero")
    assert home_lines[-1].startswith("╰")
    assert "examples/carpeta-demo" in home_lines[-1]
    assert not home_lines[2].startswith("╰")
    assert "[1] Planificar" in home_frame
    assert "tus fuentes, tu criterio" in home_frame
    assert "▀▀▀▀███████" in home_frame
    assert "secuencia de clase" in home_frame
    assert "5 fuentes" in home_frame
    assert "recientes" in home_frame
    puerta_lines = [
        line
        for line in _read(SITE / "assets" / "tui" / "frames" / "puerta-2.txt").splitlines()
        if line
    ]
    assert puerta_lines[0].startswith("╭─ tero")
    assert puerta_lines[-1].startswith("╰")
    assert "examples/carpeta-demo" in puerta_lines[-1]
    help_frame = _read(SITE / "assets" / "tui" / "frames" / "help.txt")
    assert "Rumbos" in help_frame
    assert "tero-offline" in help_frame or "cierra" in help_frame.lower()
    puerta_frame = _read(SITE / "assets" / "tui" / "frames" / "puerta.txt")
    assert "sí→derivados" in puerta_frame or "derivados" in puerta_frame
    guia_puerta = _read(SITE / "assets" / "tui" / "frames" / "puerta-2.txt")
    assert "guía" in guia_puerta.lower() or "sistemas" in guia_puerta.lower()
    assert "cóndor" not in guia_puerta.lower()
    leyendo = _read(SITE / "assets" / "tui" / "frames" / "leyendo-2.txt")
    assert "leyendo" in leyendo.lower()
    theme = _read(SITE / "assets" / "tui" / "frames" / "theme.json")
    assert "#82aaff" in theme
    assert "#0b0d10" in theme
    assert "#4c566a" in theme
    css = _read(SITE / "styles.css")
    assert "--border: #4c566a" in css
    assert 'border: "#4c566a"' in _read(SITE / "tui-grid.js")
    for folder, n in (
        ("plan", 3),
        ("guia-sistemas", 3),
        ("eval-sistemas", 3),
        ("eval-cuento", 3),
    ):
        for i in range(1, n + 1):
            path = SITE / "assets" / "hojas" / folder / f"p{i}.png"
            assert path.is_file(), path
            assert path.stat().st_size > 10_000
    frames_dir = SITE / "assets" / "tui" / "frames"
    for html_path in frames_dir.glob("*.html"):
        if html_path.name == "gallery.html":
            continue
        frame_html = _read(html_path)
        assert "window-chrome sr-only" in frame_html, html_path.name
        assert 'class="traffic"' not in frame_html, html_path.name
    for shot in ("home", "help", "puerta-2", "plan-2", "leyendo-2"):
        png = frames_dir / f"{shot}.png"
        assert png.is_file(), png
        assert png.stat().st_size > 8_000
    assert (SITE / "assets" / "tui" / "puerta.webp").is_file()
    assert (SITE / "404.html").is_file()
    not_found = _read(SITE / "404.html")
    assert "unknown_source" in not_found
    assert "no bloquea" in not_found
    assert "window-chrome" in not_found
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
