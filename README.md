# tero

**tus fuentes, tu criterio — el agente prepara, el o la docente decide**

```
tero@carpeta:~

              ▲
             ╱│
    ▄▄▄▄▄   ╱(o)*     tero
   █     █▄▀          Vanellus chilensis
   █ ▓▓▓▓  █          el tero avisa. tú decides.
    ▀▄▓▓▄▄▄▀
      ║   ║           s sí   n no
     ─┘   └─          b borrador   c corregir
```

Esto no es un dashboard de IA. El chrome es la **TUI**. Las hojas que
tero crea —la fotocopia que sale mañana a la sala— aparecen al final,
después de `s` o `b`. La [página de GitHub](https://marcorojasb.github.io/tero/)
es esa sesión: queltehue en ASCII, rumbos `1–4`, avisos a la vista,
puerta `s` / `n` / `b` / `c`.
Si el link da 404, enciende Pages una vez en
[Settings → Pages](https://github.com/marcorojasb/tero/settings/pages)
(Source **GitHub Actions**) y re-ejecuta el workflow `pages` — el token
de Actions no puede crear el sitio. Detalle: [docs/SITIO.md](docs/SITIO.md).
El modelo de la demo en el sitio es `tero-offline` (Strands scripted).
No finge Bedrock. AgentCore no es el producto.

![Terminal tero con ASCII del queltehue](site/assets/tero-og.png)

Teacher agent for [Agents for Humans](https://aws.amazon.com/): AWS
**Strands** behind a dense **OpenTUI** shell (same TUI family as
[OpenCode](https://opencode.ai)). Sibling *idea* of Pteron — your
sources, your judgment — without copying Pteron’s Electron/Solid/Meridian
desktop.

Spanish UI. Keyboard-first. MIT.

```
home (rumbos) → encargo (chips) → plan + clarificación → borrador + evidencia → s/n/b/c → derivados/
```

The model **never writes originals**. Accepted artifacts land in
`derivados/`. Drafts in `borradores/`. Sources are hashed; tero refuses
to overwrite them. Warnings (`thin_evidence`, `unverified_citation`, OA
raro) **do not block** `s`. The teacher sees the cost. See
[docs/PUERTA-Y-PR8.md](docs/PUERTA-Y-PR8.md).

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

Uses a real `strands.Agent` plus a scripted `OfflineModel` labeled
**`tero-offline`** (not a fake Bedrock call). It reads
`examples/carpeta-demo/`, proposes a typed plan, drafts a planificación
with citations, auto-accepts (`--yes` = `s`), and writes markdown under
`derivados/`. Originals stay hashed.

Interactive gate (drop `--yes`): type `s` / `n` / `b` / `c`.

OpenTUI (needs [Bun](https://bun.sh)):

```bash
python -m tero tui --offline
```

**Home first:** brand `tero`, four rumbos (`1` Planificar · `2` Crear ·
`3` Evaluar · `4` Adaptar), hero *Pregunta, explora o crea…*. Chips
appear after a rumbo or prompt.

**Keys:** **`s`** sí → `derivados/` · **`n`** no · **`b`** borrador ·
**`c`** corregir (crítica persistida). Plan: **`a`** aprobar · **`e`**
editar supuesto · **`x`** cancelar. Clarificación: **`1`/`2`/`3`** o
texto libre. Evidence: **`[` `]`** cycle · **Tab** panels · **`?`**
ayuda por fase · **`r`** reintentar error. Citas **✓** están in the
file; **?** is paraphrase. `/export` works on accepted **or** draft.

### B. Amazon Bedrock (lean — Nova Lite only)

One Strands agent → Bedrock. **No** AgentCore Runtime/Gateway/Browser
as the product. Observability, if ever, is opt-in and does not move the
carpeta.

#### AWS free tier / Nova Lite checklist

1. Region with Amazon Nova on-demand (README default **`us-east-1`**).
2. Bedrock console → **Model access** → enable **Amazon Nova Lite**
   (`amazon.nova-lite-v1:0`). Confirm in the playground.
3. IAM: `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream`
   on that model id (and `amazon.nova-micro-v1:0` only if you switch).
4. Credentials: `aws configure`, or `AWS_ACCESS_KEY_ID` /
   `AWS_SECRET_ACCESS_KEY`, or `AWS_BEARER_TOKEN_BEDROCK`. **Never commit
   `.env`.**
5. `cp .env.example .env` → set `TERO_OFFLINE=0` → fill keys:

```bash
python -m tero tui
# or
python -m tero demo --yes
```

Default model: `amazon.nova-lite-v1:0` via `TERO_MODEL` (alias
**`TERO_MODEL_ID`**). Nova Micro is cheaper for smokes. Other Bedrock
ids (GLM, MiniMax, Qwen) are the quality loop, not a hardcoded trio in
the host.

**Resilience (already in host):** Bedrock errors are humanized in Spanish
(auth / throttle / model / network). If the model returns tools/text
without a draft, tero **retries the draft once**, then **salvages**
prose/JSON into a typed artifact so the gate still opens. Curriculum OA
+ LaTeX stay **host-side** (catalog + templates). The model fills
**JSON**, not free-form TeX.

Video day: prefer `python -m tero demo --offline --yes` (honest
`tero-offline` label). Use Bedrock live only if keys + Nova access are
confirmed.

## What this is (and is not)

| In scope | Out of scope |
| --- | --- |
| Carpeta de trabajo as system of record | Electron desktop / TipTap / Meridian |
| Typed optional plan (objetivo, OA, duración, tipo) | Full Biblioteca UI |
| Artifact types: planificación, guía, evaluación, pauta/rúbrica, actividad | iPhone companion |
| Evidence panel (path + snippet + section) | SQLite session DB as product |
| Streaming activity (one event per tool call) | Ollama as default |
| Export `.md`, optional `.docx`, **LaTeX via JSON→plantilla** | Secrets in git |
| Catálogo OA Chile host-side (`list_oa` / `get_oa`) | Currículum oficial MINEDUC completo |
| Warnings at the gate, never blocking `s` | Magic `forzar` to override the teacher |

Ollama / local LLMs can come later; they are not the default.

## Architecture

```
┌─ OpenTUI (Bun, @opentui/core) ─────────────┐
│  home · rumbos · chips · sesión · actividad│
│  plan card · clarificación · propuesta     │
│  evidencia ✓/? · avisos · puerta s/n/b/c   │
└─────────────── JSONL stdin/stdout ─────────┘
                    │
┌─ python -m tero bridge  (Strands Agent) ───┐
│  tools: list/search/read (sandbox)         │
│         list_oa/get_oa/search_oa (catálogo)│
│         propose_plan, cite_evidence, draft │
│  host: hash check, salvage, coerce payload │
│         warnings, gate, write              │
│         export md|docx|latex (templates)   │
└────────────────────────────────────────────┘
                    │
         carpeta originales  (read-only, hashed)
         carpeta/derivados   (accepted)
         carpeta/borradores  (b)
```

HITL is structural: `propose_plan` / `draft_artifact` are **in-memory**.
Only `tero.gate` writes files.

See [ARCHITECTURE.md](ARCHITECTURE.md). Docs index:
[docs/README.md](docs/README.md). Adversarial self-critique:
[docs/ANALISIS-ADVERSARIAL.md](docs/ANALISIS-ADVERSARIAL.md). LaTeX +
currículo: [docs/ADVERSARIAL-LATEX-CURRICULO.md](docs/ADVERSARIAL-LATEX-CURRICULO.md).
Gate decision vs blocking-`s` draft:
[docs/PUERTA-Y-PR8.md](docs/PUERTA-Y-PR8.md). Ficha landing:
[docs/SITIO.md](docs/SITIO.md).

## Encargo chips + OA de catálogo

```bash
python -m tero tui --offline --curso "4° básico" --oa "LEN-4B-OA04" --duracion "45 min" --tipo planificacion
```

TUI: `/curso 4° básico` · `/asignatura Lenguaje` carga OA reales del
catálogo · `/oa LEN-4B-OA04` (valida) · `/tipo guia` · `/export latex`.

Catálogo mínimo (4°–6° Lenguaje/Matemática/Ciencias): `curriculum/chile/`
— **no** es texto oficial MINEDUC verbatim. Lineamientos de evaluación
(resumen de aula): `curriculum/chile/evaluacion/lineamientos.md`.

## Export LaTeX (JSON → plantilla)

Nova Lite (y el offline) **no** emiten TeX libre. El host rellena
plantillas en `templates/latex/` desde un JSON schema (o desde el
markdown del borrador):

```bash
# tras demo / gate:
python -m tero export --format latex path/al/artefacto.md
# o payload schema directo (smoke Nova Lite-safe):
python -m tero export --format latex --payload guia.json --out /tmp/guia.tex /tmp/noop.md
```

PDF opcional si hay `latexmk` (`--pdf` / sin shell-escape). Si no, queda
el `.tex`.

Extra classroom pack from the first MVP (agua / 5° básico, includes a
PDF): `fixtures/aula-5basico-agua/`.

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

This public MIT repo is a **new project** (tero), built for Agents for
Humans. The *product concept* (teacher-in-the-loop pedagogical
preparation) is inspired by **Pteron**, a private Electron app by Marco
Rojas / Patagua. It does **not** copy that Electron/SolidJS codebase.
Offline demo is scripted on purpose so the video does not pretend to be
a live Bedrock call.

See [docs/NORMAS.md](docs/NORMAS.md), [AGENTS.md](AGENTS.md),
[CONTRIBUTING.md](CONTRIBUTING.md).
