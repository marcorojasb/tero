# tero

**El agente prepara. El docente decide.**

tero is a teacher agent for [Agents for Humans](https://aws.amazon.com/): an AWS **Strands** loop behind a dense **OpenTUI** shell (the same family of terminal UI that powers [OpenCode](https://opencode.ai)). It is the sibling *idea* of Pteron — your sources, your judgment — without copying Pteron’s Electron/Solid/Meridian desktop.

Spanish UI. Keyboard-first. MIT.

```
encargo (chips) → leer carpeta → plan tipado → borrador + evidencia → s/n/b/c → derivados/
```

The model **never writes originals**. Accepted artifacts land in `derivados/`. Drafts in `borradores/`. Sources are hashed; tero refuses to overwrite them.

## Judge path (offline, no AWS)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m tero demo --offline --yes
```

That run uses a real `strands.Agent` with a **scripted** `OfflineModel` (honest about not calling Bedrock). It reads `examples/carpeta-demo/`, proposes a typed plan, drafts a planificación with citations, auto-accepts (`--yes` = `s`), and writes markdown under `derivados/`.

Interactive TUI (needs [Bun](https://bun.sh)):

```bash
python -m tero tui --offline
```

Keys: **`s`** sí → `derivados/` · **`n`** no · **`b`** borrador · **`c`** corregir (another agent pass). Plan: **`a`** aprobar · **`x`** cancelar.

## Bedrock (default model)

Default: **`amazon.nova-lite-v1:0`**. Copy `.env.example`, export AWS credentials *in the environment* (never commit them), enable model access in Bedrock, then:

```bash
python -m tero tui          # TERO_OFFLINE=0
# or
python -m tero demo         # interactive gate in the terminal
```

## What this is (and is not)

| In scope | Out of scope |
| --- | --- |
| Carpeta de trabajo as system of record | Electron desktop / TipTap / Meridian |
| Typed optional plan (objetivo, OA, duración, tipo) | Full Biblioteca UI |
| Artifact types: planificación, guía, evaluación, pauta/rúbrica, actividad | iPhone companion |
| Evidence panel (path + snippet + section) | SQLite session DB as product |
| Streaming activity (list_sources, read, plan, draft) | Ollama as default |
| Export `.md` and optional `.docx` | Secrets in git |

Ollama / local LLMs can come later; they are not the default.

## Architecture

```
┌─ OpenTUI (Bun, @opentui/core) ─────────────┐
│  chips · sesión · actividad · propuesta    │
│  evidencia · avisos · plan · puerta s/n/b/c│
└─────────────── JSONL stdin/stdout ─────────┘
                    │
┌─ python -m tero bridge  (Strands Agent) ───┐
│  tools: list/search/read (sandbox)         │
│         propose_plan, cite_evidence, draft │
│  host: hash check, warnings, gate, write   │
└────────────────────────────────────────────┘
                    │
         carpeta/fuentes     (read-only originals)
         carpeta/derivados   (accepted)
         carpeta/borradores  (b)
```

HITL is not a prompt slogan: `draft_artifact` and `propose_plan` return **in-memory only**. `tero.gate.apply_gate` is the only writer.

## Encargo chips

Visible before the run: curso / asignatura / OA / duración / tipo.

```bash
python -m tero tui --offline --curso "4° básico" --oa "OA 4" --duracion "45 min" --tipo planificacion
```

In the TUI: `/oa OA 6` · `/tipo guia` · `/export md`.

## Tests

```bash
pytest
ruff check src tests && ruff format --check src tests
cd tui && bun install && bun test src
```

## Hackathon disclosure

This public MIT repo is a **new project** (tero), built for Agents for Humans. It reuses *product concepts* from Pteron (private teacher workflow) without copying that Electron codebase. Offline demo is scripted on purpose so the video does not pretend to be a live Bedrock call.

See [docs/NORMAS.md](docs/NORMAS.md), [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md).
