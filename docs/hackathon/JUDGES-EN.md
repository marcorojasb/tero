# Judge guide — tero (English)

For **Agents for Humans** (Devpost), Track **Professional Agents**.

Verified against `main` at `7500c62`. The pasted outputs are what the commands
actually printed.

- **Reading or watching only:** §1–§3, §5–§9.
- **20 minutes with a terminal:** §4. Track A needs no AWS account and no keys.

> Language note: the UI, the CLI output and the generated artifacts are in
> **Spanish** (Chilean classroom register) — tero is built for Chilean teachers.
> The judge-facing repository, docs and this guide are in **English**.

---

## 1. What tero is

tero is a **conversational teacher agent** for Chilean classrooms. The teacher
writes in natural language; the agent infers the intent and acts:

| Intent | What the teacher asks | What tero does |
| --- | --- | --- |
| **a) Respond / interact** | *"What sources do I have for 4th grade?"* | Answers in text, inspecting the folder and the official curriculum bank. Writes nothing. |
| **b) Create new material** | *"Prepare a 45-minute reading guide"* | Reads local sources + the official bank, and proposes a **planificación / guía / evaluación / pauta / actividad in memory**, with a summary and a full Markdown preview. |
| **c) Edit or adapt** | *"Adapt the guide for a student with NEE"* | Produces a **new version** referencing `origen: …`, with special-education accommodations under Chile's **Decreto 83/2015**. The original file is untouched. |

There is **no wizard**: no home menu of numbered rumbos, no typed plan to approve
with `a`/`e`/`x`, no numbered clarification questions, and no `s` / `n` / `b` / `c`
gate. If information is missing (grade, topic, which file to adapt), the agent
**asks in natural language**.

**Approval is conversational and structural.** Before writing, tero shows what it
will do and the preview. The teacher approves with **`y`** in the TUI or by simply
replying *"dale"*, *"sí"*, *"me parece bien"*; rejects with **`n`** or *"no, no me
sirve"*; or asks for a change in the same breath (*"mejor hazlo para 2° básico"*),
which triggers another pass on the same proposal. Only then does host-side code
write into `derivados/`.

---

## 2. Trust model — the model never writes files

- **The model has no write tool.** Tools read the folder and the catalog, query
  the curriculum bank, bind citations, and **propose in memory**
  (`proponer_crear`, `proponer_editar`). No write primitive exists in the
  registry; the full table is in `docs/CONVERSACIONAL.md`.
- **Only the host writes, and only after approval.** Approval calls
  `tero.gate.write_approved()` → `Workspace.write_artifact()`, which raises
  `WriteGuardError` unless the target resolves under `derivados/`. `fuentes/` can
  never be a write target. `borradores/` is legacy: existing files can be read,
  edited or adapted, but tero writes nothing new there.
- **Editing never overwrites.** `proponer_editar` records `origen: <path>` in the
  front matter of the **new** file. The base material keeps its bytes.
- **The teacher's folder is the system of record.** Sources are SHA-256 hashed
  into `<carpeta>/.tero/index.json`. Reads report `changed` when a hash moved, and
  the CLI re-fingerprints every source after writing: the line
  `Originales intactos.` is printed only if nothing moved. A changed original is a
  warning, never a rewrite.
- **Citations are checked, not trusted.** The host looks for the quoted snippet in
  the real source (or verifies the `banco:<id>` against the bank) and marks the
  citation `verified: false` with a non-blocking warning when it is a paraphrase.
  Unverified citations still appear, marked `?` in the TUI.
- **Warnings never block the teacher.** `thin_evidence`, `unverified_citation`,
  `oa_mismatch` and `paci_no_oficial` are visible trade-offs. The human decides.
  See `docs/PUERTA-Y-PR8.md`.

---

## 3. AWS usage disclosure

| Item | Value |
| --- | --- |
| Agent SDK | **Strands Agents** (`strands-agents>=1.40.0`, Python). The loop is a real `strands.Agent`. |
| Model provider | **Amazon Bedrock**, via `strands.models.BedrockModel(model_id=…, region_name=…, temperature=…)` (`src/tero/session.py`). |
| Default model id | **`amazon.nova-lite-v1:0`** (`DEFAULT_MODEL_ID` in `src/tero/__init__.py`; overridable with `TERO_MODEL`, alias `TERO_MODEL_ID`). |
| Region | **`us-east-1`** by default (`TERO_AWS_REGION` / `AWS_REGION` / `AWS_DEFAULT_REGION`). |
| IAM needed | `bedrock:InvokeModel` + `bedrock:InvokeModelWithResponseStream` on that model id. Least-privilege policy: `docs/hackathon/iam-bedrock-minimo.json`. Amazon Nova is first-party, so it does **not** go through AWS Marketplace (no `aws-marketplace:Subscribe`). |
| Credentials | Standard AWS resolution: environment variables, shared profile, or `AWS_BEARER_TOKEN_BEDROCK`. **Never committed** — `.env` is gitignored and `.env.example` lists names only, no values. |

Empirically benchmarked on Bedrock (full method and numbers in
`docs/EVALUATION-PAPER.md`):

| Model | Success across 4 journeys | Mean latency | Recommended for |
| --- | :---: | :---: | :--- |
| `amazon.nova-lite-v1:0` | 100% | 10.0 s | Default: cheapest, serverless, densest official citations |
| `zai.glm-4.7-flash` | 100% | 10.6 s | High-speed tool calling, strict Decreto 83 schema |
| `minimax.minimax-m2.5` | 100% | 39.5 s | Richest classroom prose and assessment rubrics |

**The offline path does not fake Bedrock.** `--offline` uses `OfflineModel`
(`src/tero/offline.py`), a real `strands.models.Model` subclass that streams
through the Strands protocol and is labeled **`tero-offline`** — no network, no
credentials, no imitation of a Bedrock call, and the CLI prints that label.

**AgentCore is not required by the product.** Nothing in the CLI or TUI path needs
AgentCore Runtime, Gateway or Browser. A managed harness playground can hold a
sketch of the system prompt, but uploading classroom sources to a runtime would
break the local-hash contract, so the product loop is deliberately local. The
hackathon rules treat AgentCore as optional.

CI runs the offline path only. No AWS credentials are used by any test.

*(Cost note, from `docs/AWS-GRATIS.md`, to be checked against current AWS pricing:
Nova Lite ≈ USD 0.06 / 1M input tokens and USD 0.24 / 1M output; a demo turn costs
cents. Nova Micro is cheaper for smokes.)*

---

## 4. The 20-minute judge path

Requirements: Python 3.11+ (package metadata declares `>=3.10`; CI uses 3.12).
Bun is needed only for the TUI.

### Track A — offline, no keys, no AWS account (~3 min including install)

```bash
git clone https://github.com/marcorojasb/tero.git
cd tero
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m tero demo --offline --yes
# equivalent: make demo-offline
```

Observed output on this commit (exit code **0**, ≈ 1 s after install):

```
tero demo
  modo: offline
  modelo: tero-offline
  carpeta: .../examples/carpeta-demo
  contexto: curso: 4° básico · asignatura: Lenguaje y Comunicación · OA: LEN-4B-OA04 · duración: 45 min · tipo preferido: planificación
  mensaje: Prepara una planificación de 45 minutos sobre el cuento de la carpeta, …

PROPUESTA · crear · planificación · Planificación: Leer el cuento y distinguir lo explícito de lo implícito en el valle.
  Planificación lista para usar en aula, con evidencia de las fuentes de la carpeta.
  evidencias: 2

escrito: .../examples/carpeta-demo/derivados/20260911-…-planificacion-….md
Originales intactos.
listo.
```

Drop `--yes` to hit the interactive gate: tero prints the proposal and asks
`¿Escribo este material? (sí / no / pide un cambio)`.

What you should see at the end:

- A **markdown artifact under `derivados/`** (its name carries a timestamp). It has
  YAML front matter (`generado_por`, `tipo`, `titulo`, `accion`, `curso`,
  `asignatura`, `oa`, `duracion`), the material body, the typed payload as a JSON
  block, and an **`## Evidencia (fuentes usadas)`** section listing each source with
  its path, section, whether it is `verificada`, and the quoted snippet.
- `Originales intactos.` — printed only after re-hashing every source and finding
  no change.
- **Exit code `0`.**

`derivados/` is gitignored, so `git status` stays clean after a run.

### The TUI (needs Bun)

```bash
python -m tero tui --offline
```

- **`y`** approve (host writes to `derivados/`) · **`n`** discard · **`r`** retry
  after an error · **`?`** contextual help · **`[`** **`]`** cycle evidence ·
  **Tab** panels · **PgUp/PgDn** scroll.
- Typing a decision in the thread works too — the host classifies it with
  `tero.approval` (*"dale"*, *"no, gracias"*, *"mejor para 2° básico"*).
- `/export md|docx|latex` exports the last written artifact.

### Track B — live Amazon Bedrock (~15 min)

```bash
cp .env.example .env      # then set TERO_OFFLINE=0 and your AWS credentials
python -m tero demo --yes
# or, for the live TUI:
python -m tero tui
```

Never commit `.env`. Credentials resolve the standard AWS way (`aws configure`,
`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`, or `AWS_BEARER_TOKEN_BEDROCK`).

### Verification — what "green" means

```bash
pytest
ruff check src tests && ruff format --check src tests
cd tui && bun install && bun test src
```

Actual results at this commit:

```
354 passed, 1 skipped, 7 xfailed in 6.95s
All checks passed!
62 files already formatted
49 pass / 0 fail / 273 expect() calls   (OpenTUI)
```

---

## 5. Official curriculum grounding — the `begonia` bank

tero refuses to invent curriculum content. Alongside the teacher's folder it can
query **begonia**, a read-only local API over an officially-curated pedagogical
bank built from Chile's Curriculum Nacional:

- **13,722 approved items** and **1,159 teacher guidances**, indexed by official
  learning-objective codes (e.g. `CN05 OA 12`), with item stems and official
  marking rubrics.
- Tools: `buscar_banco` (filter by query, subject, grade, OA), `leer_item_banco`
  (full stem + rubric) and `orientaciones_banco` (official didactic guidance for
  an OA).
- Bank citations use the `banco:<id>` prefix and are verified against the bank.
- **Provenance:** approved artifacts that used the bank record
  `banco_snapshot: <snapshot_id>` in their front matter, so any material can be
  traced back to the exact bank version that grounded it.
- **Graceful degradation:** with `TERO_BEGONIA_URL` empty (the default) the bank is
  simply disabled; tero works from the local folder and says so. Configure with
  `TERO_BEGONIA_URL` plus `TERO_BEGONIA_API_KEY` or `TERO_BEGONIA_KEY_FILE` (the key
  is never committed).

---

## 6. Privacy by construction — Ley 21.719

Chile's **Ley 21.719** (personal data protection, in force **2026-12-01**) forbids
processing health data collected in educational settings (Art. 16 bis) and hardens
protection of children's data. Most teacher AI tools ingest whatever the user drops
in a folder. tero does not:

- **Admission filter** (`src/tero/privacy.py`): files whose name or path suggests
  gradebooks, student rosters, attendance, or psychopedagogical/health reports — and
  any text file containing Chilean national IDs (RUT/RUN) or a names-and-grades
  table — are **excluded from the index and never sent to the model**.
- **Conservative default:** when in doubt, exclude.
  `TERO_DATOS_SENSIBLES=incluir` opts out, as the teacher's explicit decision.
- **Nothing is deleted or moved.** Excluded files stay exactly where they were; tero
  only declines to read them.
- **One aggregate, non-blocking advisory** (`dato_sensible_excluido`) tells the
  teacher how many files were left out and why — not twenty separate cards.

---

## 7. Special education (NEE) under Decreto 83/2015

Chilean **Decreto 83/2015** already writes the taxonomy, so tero does not invent
pedagogy. Adaptations declare their criterion explicitly:

```
acceso · <criterion>: <classroom support>
objetivos · <criterion>: <what was adjusted and how>
```

- **Access accommodations (4):** presentation of information, forms of response,
  environment, time.
- **Curricular-objective accommodations (5):** graduation, prioritization,
  temporalization, enrichment, **elimination**.
- The decree's rules are enforced as guidance: consider access accommodations first;
  elimination is a last resort and can never touch literacy, arithmetic operations,
  or competencies for daily life; access supports used for learning must be the same
  at assessment time.
- The host attaches a **non-blocking** `paci_no_oficial` advisory on every
  adaptation: these are classroom supports, **not** a PACI or a formal curricular
  accommodation (an official MINEDUC document — a legal instrument, not something an
  agent should produce silently).

---

## 8. Originality and prior work disclosure

This public MIT repository is a **new project** built for Agents for Humans. The
*product concept* (teacher-in-the-loop pedagogical preparation for Chilean
classrooms) builds on prior private desktop work by the same author. No code was
copied from that predecessor — the stack here is Python + Strands + OpenTUI. The
offline demo is scripted on purpose so that a recording never pretends to be a live
Bedrock call.

No third-party code is vendored. Dependencies are permissively licensed (Strands
Agents Apache-2.0, OpenTUI MIT, pypdf BSD-3-Clause, python-docx MIT, pytest MIT,
ruff MIT), compatible with this repo's MIT license.

---

## 9. Live demo

- **Public page:** <https://marcorojasb.github.io/tero/> — the real OpenTUI,
  virtualized in **one** window. It simulates the conversational scenes (inquiry,
  creation, NEE adaptation, Fila B) and shows the photocopied pages the host writes
  into `derivados/`. The in-browser model is labeled `tero-offline`; it does not
  fake Bedrock.
- **Repository:** <https://github.com/marcorojasb/tero> (MIT).
- **Benchmark paper:** `docs/EVALUATION-PAPER.md`.
- **Protocol spec:** `docs/CONVERSACIONAL.md`.

If the Pages link 404s on a fresh fork, enable Pages once under
[Settings → Pages](https://github.com/marcorojasb/tero/settings/pages) with Source
**GitHub Actions**, then re-run the `pages` workflow — the Actions token cannot
create the site.
