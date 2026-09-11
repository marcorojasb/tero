# Judge guide — tero (English)

For **Agents for Humans** (Devpost), Track **Professional Agents**.

Everything below was executed against `main` at commit
`2b2e76abbf7bd330668b651dfc62c12dd038cd2b` (2026-09-11). The pasted outputs are
what the commands actually printed; where a repo doc disagrees with the code,
this guide follows the code and says so (see §9).

Two ways to use this guide:

- **Reading / watching only (no install):** §1 what it is, §2 trust model,
  §3 AWS usage, §6 originality, §7 live demo.
- **20 minutes with a terminal:** §4. Track A needs no AWS account and no keys.

> Language note: the UI, the CLI output and the generated artifacts are in
> **Spanish** (Chilean classroom register). The judge-facing docs are in English.

## 1. What tero is

tero is a teacher agent for Chilean classrooms: it reads the teacher's own
working folder (a story, OA notes, vocabulary, a PDF), proposes a plan, and
drafts a *planificación* / *guía* / *evaluación* / *pauta* with citations to
those sources — then stops. The teacher decides with **`s`** (accept, written to
`derivados/`), **`n`** (discard), **`b`** (keep as draft), **`c`** (correct).
It is Python + **Strands Agents** + **Amazon Bedrock**, with an **OpenTUI**/Bun
terminal shell, MIT licensed.

**What it is not:**

- Not an Electron / desktop app. There is no GUI runtime; the shell is a
  terminal UI, and the public page is that TUI virtualized (see §7).
- Not a cloud runtime as the product. No AgentCore Runtime/Gateway/Browser, no
  S3-as-the-folder, no Lambda-as-the-agent. The agent is a local process; the
  teacher's folder stays on the teacher's machine. AgentCore is optional and
  **not required** (§3).
- Not a chatbot. The deliverable is a file in the teacher's folder, not a
  conversation transcript.

## 2. The human gate / trust model

- **The model never writes files.** Its tools read (`list_sources`,
  `search_sources`, `read_source`), query the Chile OA catalog (`list_oa`,
  `get_oa`, `search_oa`), and *propose in memory* (`propose_plan`,
  `cite_evidence`, `draft_artifact`). No tool can write an artifact.
- **Only the host writes, and only after the teacher's decision.**
  `s` → `<carpeta>/derivados/`; `b` → `<carpeta>/borradores/`; `n` writes
  nothing; `c` persists the critique under `<carpeta>/.tero/criticas/` and asks
  for another pass. Every artifact write goes through `Workspace.write_artifact`
  (`src/tero/workspace.py`), which raises `WriteGuardError` unless the target is
  under `derivados/`, `borradores/` or `.tero/`. The only caller is the host
  gate (`src/tero/gate.py`). `fuentes/` can never be a write target.
- **The teacher's folder is the system of record.** Sources are SHA-256 hashed
  into `<carpeta>/.tero/index.json`. Reads report `changed` when a hash moved,
  and `demo` re-fingerprints every source after the write: the line
  `Originales intactos.` is only printed if nothing moved. A changed original is
  a warning, never a rewrite.
- **Citations are checked against the file, not trusted.** The host looks for the
  quoted snippet in the real source and marks the citation `verified: false` with
  a non-blocking warning when it is a paraphrase.
- **Warnings never block `s`.** `thin_evidence`, `unverified_citation`,
  `oa_mismatch`, short skeleton: all carry `blocking: false`. The teacher is the
  gate (`docs/PUERTA-Y-PR8.md` explains why a blocking version was rejected).

## 3. AWS usage disclosure

| Item | Value |
| --- | --- |
| Agent SDK | **Strands Agents** (`strands-agents`, Python). The loop is a real `strands.Agent`. |
| Model provider | **Amazon Bedrock**, via `strands.models.BedrockModel(model_id=…, region_name=…, temperature=…)` (`src/tero/session.py`). |
| Default model id | **`amazon.nova-lite-v1:0`** (`DEFAULT_MODEL_ID` in `src/tero/__init__.py`; overridable with `TERO_MODEL`, alias `TERO_MODEL_ID`). |
| Region | **`us-east-1`** by default (`TERO_AWS_REGION` / `AWS_REGION` / `AWS_DEFAULT_REGION`). |
| IAM needed | `bedrock:InvokeModel` + `bedrock:InvokeModelWithResponseStream` on that model id. Least-privilege policy: `docs/hackathon/iam-bedrock-minimo.json`. Amazon Nova is first-party, so it does **not** go through AWS Marketplace (no `aws-marketplace:Subscribe`). |
| Credentials | Standard AWS resolution: environment variables, shared profile, or `AWS_BEARER_TOKEN_BEDROCK`. **Never committed** — `.env` is gitignored and `.env.example` lists names only, no values. |

**The offline path does not fake Bedrock.** `--offline` uses `OfflineModel`
(`src/tero/offline.py`), a real `strands.models.Model` subclass that streams
through the Strands protocol and is labeled **`tero-offline`** — no network, no
credentials, no imitation of a Bedrock call, and the CLI prints that label.

**AgentCore is not required by the product.** Nothing in the CLI or TUI path
needs AgentCore Runtime, Gateway or Browser. A managed harness playground can
hold a sketch of the system prompt, but uploading classroom sources to a runtime
would break the local-hash contract, so the product loop is deliberately local.
The hackathon rules treat AgentCore as optional.

CI runs the offline path only. No AWS credentials are used by any test.

*(Cost note, from `docs/AWS-GRATIS.md`, to be checked against current AWS
pricing: Nova Lite ≈ USD 0.06 / 1M input tokens and USD 0.24 / 1M output; a demo
turn costs cents. Nova Micro is cheaper for smokes.)*

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

Observed output on that commit (exit code **0**, ≈ 0.9 s after install):

```
tero demo
  modo: offline
  modelo: tero-offline
  carpeta: .../examples/carpeta-demo
  encargo: 4° básico, Lenguaje y Comunicación, LEN-4B-OA04, 45 min, planificación

PROPUESTA · planificación · Leer el cuento y distinguir lo explícito de lo implícito en el valle.
  evidencias: 2

escrito: .../examples/carpeta-demo/derivados/20260911-125103-planificacion-….md
Originales intactos.
listo.
```

What you should see at the end:

- A **markdown artifact under `derivados/`** (its name carries a timestamp, e.g.
  `20260911-125103-planificacion-….md`). It has YAML frontmatter
  (`generado_por`, `tipo`, `titulo`, `curso`, `asignatura`, `oa`, `duracion`),
  the ficha body, the typed payload as a JSON block, and an
  **`## Evidencia (fuentes usadas)`** section listing each source with its path,
  section, whether it is `verificada`, and the quoted snippet.
- `Originales intactos.` — printed only after re-hashing every source and
  finding no change.
- **Exit code `0`.**

`derivados/` is gitignored, so `git status` stays clean after a run.

Drop `--yes` to walk the gate yourself: type `a` / `x` on the plan, then
`s` / `n` / `b` / `c` at the artifact.

Exit codes: `0` success · `2` invalid gate decision · `1` unexpected phase, or a
source hash changed during the run (the host then says an original changed).

Alternative carpeta (verified, exit **0**) — a flat 5° básico classroom pack with
no `fuentes/` subfolder:

```bash
python -m tero demo --offline --yes --carpeta fixtures/aula-5basico-agua
```

One caveat: `demo` ships classroom defaults for the *encargo chips*
(`4° básico`, `LEN-4B-OA04`) that do not read the folder, so with the 5° básico
pack the frontmatter will say `4° básico` unless you pass the chips yourself:
`--curso "5° básico"` (verified: the artifact then reports `5° básico` and the
catalog resolves `LEN-5B-OA03`). This is CLI defaults, not a folder inspection.

With Bun installed, the same loop in the real TUI:

```bash
python -m tero tui --offline
```

### Track B — Amazon Bedrock / Nova Lite

Only if you have Bedrock access in a region with Nova on-demand:

```bash
cp .env.example .env
# edit .env: TERO_OFFLINE=0
# credentials, pick one: environment variables, AWS_PROFILE, or AWS_BEARER_TOKEN_BEDROCK
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1

python -m tero demo --yes        # no --offline
# or, with Bun: python -m tero tui
```

- `TERO_OFFLINE=0`, `TERO_MODEL=amazon.nova-lite-v1:0`, `TERO_AWS_REGION=us-east-1`.
- **Never commit `.env`.** It is gitignored; no keys are in the repo or in CI.
- If your account wants a cross-region inference profile:
  `TERO_MODEL=us.amazon.nova-lite-v1:0`.
- Expected end state is the same as Track A: a markdown artifact under
  `derivados/`, evidence citations, `Originales intactos.`, exit code `0` — with
  the model id instead of `tero-offline` in the header.
- The Bedrock path is **not** exercised by CI (it has no credentials). The
  offline path is what every push tests.

## 5. Where the interesting engineering is

| Area | Files | What to look at |
| --- | --- | --- |
| Sandboxed, read-only tools | `src/tero/tools.py`, `src/tero/workspace.py` | The model's only file access is `list_sources` / `search_sources` / `read_source`. `_safe_join` rejects absolute paths, backslashes, and anything resolving outside the carpeta. Artifact writes live in `write_artifact`, unreachable from any tool, guarded by `WriteGuardError`. |
| Payload JSON → LaTeX templates | `src/tero/latex/`, `templates/latex/` | The model fills a **JSON schema**, not free-form TeX. The host renders deterministic templates (`planificacion.tex`, `guia.tex`, `evaluacion.tex`, `pauta.tex`, `beamer.tex`) with schemas under `templates/latex/schemas/`. Try: `python -m tero export --format latex <artefacto.md>` (verified: exit `0`, writes a `.tex` next to the source; `--pdf` uses `latexmk` if installed). |
| Salvage of model prose | `src/tero/salvage.py` | When a model prints a tool call as prose, dumps JSON, or writes markdown without calling the tool, the host recovers a typed draft (`salvage_draft_from_text`, with a parallel plan path) so the gate still opens instead of erroring out. |
| One activity event per tool call | `src/tero/tools.py` | Each tool emits `{"type": "activity", "tool", "state": "start"/"end", "detail"}` — one start per call, not one per stream delta. Tool use is capped per turn (`DRAFT_TOOL_BUDGET = 16`). |
| Non-blocking warnings | `src/tero/evidence.py` | `collect_warnings` produces `thin_evidence`, `unverified_citation`, `oa_mismatch`, short-skeleton warnings; every one carries `blocking: false` and the write proceeds. Rationale and run evidence: `docs/PUERTA-Y-PR8.md`. |
| Hash contract | `src/tero/workspace.py`, `src/tero/hashutil.py` | SHA-256 per source, index at `.tero/index.json`, `changed` flag on read, and a before/after fingerprint around the gate. |

## 6. Originality and prior work

tero is a **new project**: this MIT repository was written for Agents for Humans
and contains no code from another codebase. The *product idea* —
teacher-in-the-loop pedagogical preparation, "your sources, your judgment" — is
inspired by **Pteron**, an earlier **private** desktop app by the same author
(Marco Rojas / Patagua). No Pteron code was copied, and none of its
Electron/SolidJS stack appears here. The offline demo is scripted on purpose so
the video never passes it off as a live Bedrock call. The Chile OA catalog in
`curriculum/chile/` is a host-side teaching paraphrase, **not** verbatim MINEDUC
text.

## 7. Live demo

<https://marcorojasb.github.io/tero/> — GitHub Pages (verified reachable,
HTTP 200).

It is the **real tero OpenTUI virtualized in one window**: frames captured from
the actual TUI (`tui/scripts/capture-frames.ts`) and replayed by
`site/tui-grid.js`. There is no second titlebar, no Electron, no Python runtime
in the browser, and no SaaS hero page. The "photocopied paper" pages appear only
after `s` or `b`, and only for the sheets tero creates. The model shown on the
site is `tero-offline`.

If the link ever 404s, Pages must be enabled once (Settings → Pages → Source:
*GitHub Actions*); the Actions token can publish but cannot create the site.

## 8. Tests — how to run them, and what green looks like

```bash
pytest                                    # Python suite
cd tui && bun install && bun test src     # OpenTUI frame/state tests
ruff check src tests && ruff format --check src tests
```

Observed at commit `2b2e76a`:

```
143 passed in 3.43s          # pytest, exit 0
31 pass · 0 fail             # bun test src, exit 0 (117 expect() calls, 2 files)
All checks passed!           # ruff check, exit 0
53 files already formatted   # ruff format --check, exit 0
```

CI (`.github/workflows/ci.yml`) runs exactly this on Python 3.12 and Bun 1.4.2,
plus `python -m tero demo --offline --yes --quiet --carpeta examples/carpeta-demo`.
No test needs AWS credentials or the network.

## 9. Docs vs. code at this commit (read this before judging the design docs)

The repository is mid-refactor, and those docs are partly **ahead of the code**:

- **What the code does today** is the flow in §4: a typed plan with `a` / `x`,
  numbered clarifications, and the `s` / `n` / `b` / `c` gate on the artifact.
  That is what the commands above really run.
- `ARCHITECTURE.md`, `AGENTS.md` and `docs/CONVERSACIONAL.md` describe the
  **target** conversational shape — natural-language approval, no rumbos 1–4, no
  numbered clarifications — specified as a frozen protocol for in-flight host and
  TUI migration PRs. `docs/CONVERSACIONAL.md` states it plainly: until those two
  PRs land, `main` still shows the step flow.
- Treat those three as design docs, not as a description of current behavior.
  Everything in §1–§8 of this guide was executed and observed at the commit
  above, not copied from the README.

## Repository map for judges

| Path | What it is |
| --- | --- |
| `src/tero/` | Host: Strands agent, session, tools, gate, salvage, LaTeX export, CLI. |
| `tui/` | OpenTUI shell (Bun, `@opentui/core`), JSONL bridge to the host. |
| `templates/latex/` | Deterministic LaTeX templates + JSON schemas. |
| `curriculum/chile/` | Host-side OA catalog (paraphrase, 4°–6°). |
| `examples/carpeta-demo/` | Default working folder: sources + empty `derivados/`. |
| `fixtures/aula-5basico-agua/` | Second classroom pack (flat carpeta, includes a PDF). |
| `docs/hackathon/` | Devpost text, video script, architecture diagram, minimum IAM policy. |
| `site/` | GitHub Pages source (the virtualized TUI). |
