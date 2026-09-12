# Devpost — paste this

Track: **Professional Agents**

Built with: **Strands Agents SDK (Python)** + Amazon Bedrock (Nova Lite, GLM 4.7 Flash, MiniMax M2.5) + OpenTUI.

Live demo: https://marcorojasb.github.io/tero/

Repo: https://github.com/marcorojasb/tero

Builder ID: *(the email you used at https://profile.aws.amazon.com)*

---

## Project name

tero

## Tagline (≤ 200 chars if the form is tight)

A conversational teacher agent for Chilean classrooms: it grounds material in official MINEDUC curriculum, proposes in memory, and writes only after the teacher approves.

## Description (paste)

**tero** is a conversational teacher agent for Chilean K-12 classrooms. The teacher writes in plain Spanish; tero infers the intent and acts — answering a question, creating new material, or editing and adapting what already exists (including special-education accommodations under Chile's Decreto 83/2015). It reads the teacher's own working folder plus an official curriculum bank, prepares the artifact **in memory**, shows a summary and a full preview, and **writes nothing until the teacher approves** — by pressing `y` or simply replying *"dale"*.

Teachers already do the judgment. What eats the afternoon is turning one request into photocopiable, curriculum-aligned pages — not a generic worksheet from the internet. tero takes that repetitive prep loop and keeps the educator in the chair.

### Who it's for

Chilean teachers (4°–6° básico in the current catalog) who already have sources in a folder: a story, OA notes, vocabulary, a PDF. Spanish UI built for the Chilean classroom register; keyboard-first. No SaaS homepage as the product — the public face is a real OpenTUI terminal, virtualized in one window.

### The three intents

| Intent | Example | Result |
| --- | --- | --- |
| **a) Respond** | *"What sources do I have for 4th grade?"* | Answer in text; inspects folder + curriculum bank; writes nothing. |
| **b) Create** | *"Prepare a 45-minute reading guide"* | In-memory proposal with summary, preview and citations; writes on approval. |
| **c) Edit / adapt** | *"Adapt the guide for a student with NEE"* | New file with `origen:` pointing at the base material; original untouched. Decreto 83 access/objective criteria declared explicitly. |

### How it works

1. The OpenTUI shell (Bun, `@opentui/core`) talks to `python -m tero bridge` over one JSON object per line.
2. A **Strands** `Agent` calls host tools only: `list_sources` / `search_sources` / `read_source` / `list_artifacts` / `read_artifact` (sandboxed, SHA-256 indexed), the Chile OA catalog (`list_oa` / `get_oa` / `search_oa`), the official curriculum bank (`buscar_banco` / `leer_item_banco` / `orientaciones_banco`), `cite_evidence`, and the in-memory `proponer_crear` / `proponer_editar`.
3. Live path: Amazon Bedrock (`amazon.nova-lite-v1:0` by default) in `us-east-1` via `BedrockModel`. Offline path: a real Strands `Model` labeled **`tero-offline`** — scripted on purpose, not a fake Bedrock call.
4. **Nothing is written without explicit human approval.** Approval is conversational: the host classifies the teacher's reply (`tero.approval`) into approve / change / discard / ask, and only `tero.gate.write_approved()` touches disk, only under `derivados/`.
5. The host salvages prose if the model forgets the tool, caps tool use per turn, verifies every citation against the real file or the bank, and shows non-blocking warnings. Warnings **never block** the teacher.
6. Export is markdown / docx / LaTeX filled from JSON schemas — the model never emits TeX.

### Official curriculum grounding

Rather than inventing content, tero queries **begonia**, a read-only local API over an officially curated Chilean pedagogical bank (Curriculum Nacional / MINEDUC): **13,722 approved items** and **1,159 teacher guidances** indexed by official learning-objective codes, with item stems and marking rubrics. Grounded artifacts record `banco_snapshot: <id>` in their front matter for full provenance. If the bank is not configured, tero degrades gracefully to local sources and says so.

### Privacy by construction (Ley 21.719)

Chile's personal data protection law (in force 2026-12-01) forbids processing health data collected in educational settings. tero's admission filter refuses to index or send to the model any file that looks like a gradebook, roster, attendance log, or psychopedagogical/health report — and any text file containing national IDs (RUT/RUN). Files are never deleted or moved; one aggregate non-blocking advisory tells the teacher how many were left out.

### Empirical benchmark

We benchmarked 5 Bedrock models across 4 pedagogical journeys. Top three: `amazon.nova-lite-v1:0` (default; 100%, 10.0 s mean), `zai.glm-4.7-flash` (100%, 10.6 s, strictest Decreto 83 schema compliance) and `minimax.minimax-m2.5` (100%, 39.5 s, richest classroom prose and rubrics). Full method, tables and failure analysis: `docs/EVALUATION-PAPER.md`.

Amazon Bedrock AgentCore is **not** the product. A managed harness playground can hold a sketch of the system prompt; the system of record stays the local folder. That is intentional: uploading student-adjacent sources to a runtime would break the hash contract.

### AWS used

- Amazon Bedrock (`amazon.nova-lite-v1:0`, plus `zai.glm-4.7-flash` and `minimax.minimax-m2.5` for the quality loop) — inference
- Strands Agents SDK — agent loop and tool orchestration
- IAM (least privilege `InvokeModel*`)
- Optional: AWS Budgets so Free Tier credits are not a surprise

No Lambda-as-the-agent, no S3-as-the-folder, no multi-agent A2A.

### Run it (offline, no keys)

```bash
git clone https://github.com/marcorojasb/tero.git
cd tero
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m tero demo --offline --yes
```

TUI (needs Bun): `python -m tero tui --offline`

Bedrock: copy `.env.example` → `.env`, set `TERO_OFFLINE=0`. Nova Lite auto-enables on first invoke in us-east-1 (no Model access page).

### Disclosure

New public MIT project built during the submission window. The *product thesis* (teacher-in-the-loop prep; your sources, your judgment) builds on prior private desktop work by the same author. This repository does not contain that desktop and no code was copied from it. The offline demo is scripted and labeled `tero-offline`; say that in the video.

### Architecture

See `docs/hackathon/architecture.png` (upload this to Devpost) and `ARCHITECTURE.md`.

---

## Built with (checkboxes / tags)

Strands Agents SDK, Amazon Bedrock, Amazon Nova Lite, Amazon Nova, Python, OpenTUI, Bun, AWS IAM, AWS Budgets

## Try it out

https://marcorojasb.github.io/tero/

```
python -m tero demo --offline --yes
```
