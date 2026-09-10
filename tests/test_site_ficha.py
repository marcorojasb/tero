"""The public GitHub page is a photocopied ficha, not an AgentCore hero."""

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

    assert "--tui-bg: #0b0d10" in css
    assert "--tui-accent: #82aaff" in css
    assert "photocopied" in css.splitlines()[0].lower() or "photocopied" in css[:400].lower()

    assert "WARNINGS_BLOCK_S = false" in js
    assert "function canAccept" in js
    assert "tero-offline" in js
    assert "draft_artifact" in js
    assert "unverified_citation" in js
    # The rejected PR #8 override must not appear as a gate.
    assert "forzar" not in js
    assert "tú decides" in html
    assert "vos decidís" not in html
    assert "vos decidís" not in js
    assert "Get started" not in html
    assert "Sign up" not in html


def test_ficha_assets_and_pages_workflow():
    assert (SITE / "assets" / "tero-og.png").is_file()
    assert (SITE / "assets" / "tero-stamp.png").is_file()
    assert (SITE / "404.html").is_file()
    not_found = _read(SITE / "404.html")
    assert "unknown_source" in not_found
    assert "no bloquea" in not_found
    workflow = _read(ROOT / ".github" / "workflows" / "pages.yml")
    assert "path: site" in workflow
    assert "deploy-pages" in workflow


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

    readme = _read(ROOT / "README.md")
    assert "marcorojasb.github.io/tero" in readme
    assert "site/assets/tero-og.png" in readme
    assert "PUERTA-Y-PR8.md" in readme
    assert "forzar" in readme  # listed as out of scope
