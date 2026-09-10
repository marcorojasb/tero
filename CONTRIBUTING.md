# Contributing

## English (short)

1. Use a venv: `pip install -e ".[dev]"`.
2. Offline first: `python -m tero demo --offline --yes` and `pytest` must pass.
3. TUI: install [Bun](https://bun.sh), then `cd tui && bun install && bun test src`.
4. Never commit secrets. Copy `.env.example` only.
5. Commits: `feat|fix|docs|test|ci|chore: summary`.
6. Python formatted/linted with Ruff. Do not add Electron or local-LLM-as-default.
7. Public landing is `site/` (Terminal UI splash + ASCII wave on GitHub Pages).
   Photocopied paper only for created pages. Not a product hero.
   Docs index: `docs/README.md`.

Hackathon: this is a **new public MIT project**. Offline mode is scripted; Bedrock is the live path.

## Español (corto)

1. Entorno: `pip install -e ".[dev]"`.
2. Primero offline: `python -m tero demo --offline --yes` y `pytest`.
3. TUI con Bun: `cd tui && bun install && bun test src`.
4. Cero secretos en git. Solo `.env.example`.
5. Commits convencionales, un tema por commit.
6. Ruff en Python. Sin Electron, sin Ollama como default.
7. Docs en `docs/` (índice: `docs/README.md`). La landing pública es
   `site/` (splash de terminal + ola ASCII, GitHub Pages). El papel
   fotocopiado es solo de las páginas que tero crea. No conviertas eso
   en un hero de producto.

Hackathon: proyecto **nuevo**, MIT, público. El modo offline es scripted a propósito; Bedrock es el camino real.
