# tero

**tus fuentes, tu criterio — el agente prepara, el o la docente decide**

Teacher agent for [Agents for Humans](https://aws.amazon.com/): an AWS **Strands** loop behind a dense **OpenTUI** shell (same TUI family as [OpenCode](https://opencode.ai)). Sibling *idea* of Pteron — your sources, your judgment — without copying Pteron’s Electron/Solid/Meridian desktop.

Spanish UI. Keyboard-first. MIT.

```
encargo (chips) → leer carpeta → plan tipado → borrador + evidencia → s/n/b/c → derivados/
```

The model **never writes originals**. Accepted artifacts land in `derivados/`. Drafts in `borradores/`. Sources are hashed; tero refuses to overwrite them.

## 20-minute judge path

Python **3.10+**. Two tracks:

| Track | Time | What it proves |
| --- | --- | --- |
| **A. Offline** | ~2 min | Full Strands loop (tools + plan + evidence + gate + `derivados/`) with a scripted model. No AWS. |
| **B. Bedrock** | ~15 min | Same loop with **Amazon Nova Lite** (`amazon.nova-lite-v1:0`). |

### A. Offline (no keys) — video path

```bash
git clone https://github.com/marcorojasb/tero.git
cd tero
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m tero demo --offline --yes
# or: make demo-offline
```

Uses a real `strands.Agent` plus a scripted `OfflineModel` labeled **`tero-offline`** (not a fake Bedrock call). It reads `examples/carpeta-demo/`, proposes a typed plan, drafts a planificación with citations, auto-accepts (`--yes` = `s`), and writes markdown under `derivados/`. Originals stay hashed.

Interactive gate (drop `--yes`): type `s` / `n` / `b` / `c`.

OpenTUI (needs [Bun](https://bun.sh)):

```bash
python -m tero tui --offline
```

Keys: **`s`** sí → `derivados/` · **`n`** no · **`b`** borrador · **`c`** corregir (another agent pass). Plan: **`a`** aprobar · **`x`** cancelar. Evidence: **`[` `]`** cycle · **Tab** session/proposal/evidence. Citas **✓** are in the file; **?** is a paraphrase the host did not find.

### B. Amazon Bedrock

1. Region with Amazon Nova (README default **`us-east-1`**).
2. IAM: `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on `amazon.nova-lite-v1:0` (and `amazon.nova-micro-v1:0` if you switch). Confirm Nova Lite in the Bedrock playground.
3. Credentials: `aws configure`, or `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`, or `AWS_BEARER_TOKEN_BEDROCK`. **Never commit `.env`.**
4. `cp .env.example .env` then:

```bash
python -m tero tui
# or
python -m tero demo --yes
```

Default model: `amazon.nova-lite-v1:0` (`TERO_MODEL` or alias `TERO_MODEL_ID`). Nova Micro is cheaper; Claude needs extra account enablement.

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
         carpeta originales  (read-only, hashed)
         carpeta/derivados   (accepted)
         carpeta/borradores  (b)
```

HITL is structural: `propose_plan` / `draft_artifact` are **in-memory**. Only `tero.gate` writes files.

See [ARCHITECTURE.md](ARCHITECTURE.md). Adversarial self-critique: [docs/ANALISIS-ADVERSARIAL.md](docs/ANALISIS-ADVERSARIAL.md).

## Encargo chips

```bash
python -m tero tui --offline --curso "4° básico" --oa "OA 4" --duracion "45 min" --tipo planificacion
```

TUI commands: `/oa OA 6` · `/tipo guia` · `/export md`.

Extra classroom pack from the first MVP (agua / 5° básico, includes a PDF): `fixtures/aula-5basico-agua/`.

```bash
python -m tero demo --offline --yes --carpeta fixtures/aula-5basico-agua
```

## Tests

```bash
pytest
ruff check src tests && ruff format --check src tests
cd tui && bun install && bun test src
```

## Hackathon disclosure

This public MIT repo is a **new project** (tero), built for Agents for Humans. The *product concept* (teacher-in-the-loop pedagogical preparation) is inspired by **Pteron**, a private Electron app by Marco Rojas / Patagua. It does **not** copy that Electron/SolidJS codebase. Offline demo is scripted on purpose so the video does not pretend to be a live Bedrock call.

See [docs/NORMAS.md](docs/NORMAS.md), [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md).
