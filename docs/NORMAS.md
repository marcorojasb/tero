# Normas / Engineering norms

## Producto (es)

- tero es un agente docente: el modelo prepara, la persona decide (`s` sí, `n` no, `b` borrador, `c` corregir).
- La carpeta de trabajo es la fuente de verdad. `derivados/` y `borradores/` son las únicas escrituras de artefacto. Los originales se indexan con SHA-256; si cambian, se avisa, no se pisan.
- UI en español, teclado primero, avisos que **no bloquean**.
- Modelo por defecto: Bedrock `amazon.nova-lite-v1:0`. Offline = modelo scripted de Strands, nunca un disfraz de API.

## Engineering (en)

- Python 3.11+, package under `src/tero`, tests under `tests/`.
- Lint/format: `ruff check` + `ruff format`. CI must stay green.
- TUI: Bun + `@opentui/core`. Frame tests use `@opentui/core/testing`.
- JSONL protocol versioned (`v: 1`). Unknown inbound types are errors, not silent drops.
- No secrets in the tree. `.env` is gitignored; `.env.example` lists names only.
- Commit style: conventional commits, small diffs, no drive-by refactors.
- HITL invariant: tools must not write teacher artifacts. `tero.gate` writes after a decision.

## How to run

```bash
# Offline / video
python -m tero demo --offline --yes

# Live Bedrock (credentials in the environment)
python -m tero tui

# Bridge only (OpenTUI spawns this)
python -m tero bridge --offline
```

## Hackathon disclosure

New project, public MIT repository. Concepts inspired by Pteron (teacher workflow) without copying that private Electron app. Declare offline vs Bedrock honestly in the demo video.
