#!/usr/bin/env python3
"""Local preview of the ficha. GitHub Pages already serves 404.html; this mimics it."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class FichaHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        if code != 404:
            super().send_error(code, message, explain)
            return
        body = (ROOT / "404.html").read_bytes()
        self.send_response(404, "File not found")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD" and self.wfile:
            self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sirve la ficha de tero (con 404.html).")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    try:
        import sys

        sys.path.insert(0, str(ROOT))
        import stamp as stamp_mod

        stamp_mod.stamp()
    except Exception:
        pass
    handler = partial(FichaHandler, directory=str(ROOT))
    httpd = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"ficha tero en http://{args.host}:{args.port}/", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
