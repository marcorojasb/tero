# Devpost — paste this

Track: **Professional Agents**

Built with: **Strands Agents SDK (Python)** + Amazon Bedrock (Nova Lite) + OpenTUI.

Live demo (optional): https://marcorojasb.github.io/tero/

Repo: https://github.com/marcorojasb/tero

Builder ID: *(the email you used at https://profile.aws.amazon.com)*

---

## Project name

tero

## Tagline (≤ 200 chars if the form is tight)

The agent prepares the lesson. The teacher decides. A Strands teacher agent with a keyboard-first TUI, hashed classroom folders, and a human gate (`s` / `n` / `b` / `c`).

## Description (paste)

**tero** is a teacher agent for Chilean classrooms: it reads the teacher’s own folder, proposes a plan, drafts a planificación / guía / prueba with citations, and **stops**. The human gate is `s` (accept to `derivados/`), `n` (discard), `b` (keep as draft), `c` (correct). The model never writes originals.

Teachers already do the judgment. What eats the afternoon is turning one encargo into photocopiable pages aligned to the lesson they actually taught — not a generic worksheet from the internet. tero takes that repetitive prep loop and keeps the teacher in the chair.

### Who it’s for

A teacher (4°–6° básico in the current catalog) who already has sources in a folder: a story, OA notes, vocabulary, a PDF. Spanish UI. Keyboard-first. No SaaS homepage as the product; the public face is a Terminal UI splash.

### How it works

1. OpenTUI shell (Bun, `@opentui/core`) talks to `python -m tero bridge` over one JSON object per line.
2. A **Strands** `Agent` calls host tools only: `list_sources` / `search_sources` / `read_source` (sandboxed, SHA-256 indexed), OA catalog (`list_oa` / `get_oa` / `search_oa`), `propose_plan`, `cite_evidence`, `draft_artifact`.
3. Live path: Amazon Bedrock **Nova Lite** (`amazon.nova-lite-v1:0`) in `us-east-1` via `BedrockModel`. Offline path: a real Strands `Model` labeled **`tero-offline`** — scripted on purpose, not a fake Bedrock call.
4. The host salvages prose if the model forgets the tool, caps draft tool-use, checks citations against the file, and shows warnings. Warnings **never block** `s`. The teacher is the gate.
5. Accepted pages land in `derivados/`. Export is markdown / docx / LaTeX from JSON templates — the model does not emit TeX.

Amazon Bedrock AgentCore is **not** the product. A managed harness playground can hold a sketch of the system prompt; the system of record stays the local carpeta. That is intentional: uploading student-adjacent sources to a runtime would break the hash contract.

### AWS used

- Amazon Bedrock (Nova Lite / Nova Micro) — inference
- IAM (least privilege InvokeModel*)
- Optional: AgentCore Harness playground for a bounded AWS sketch (Nova Lite, no Browser / Code Interpreter)
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

Bedrock: copy `.env.example` → `.env`, set `TERO_OFFLINE=0`, enable Nova Lite in us-east-1.

### Disclosure

New public MIT project built during the submission window. The *product thesis* (teacher-in-the-loop prep; your sources, your judgment) is a sibling idea of Pteron, a private Electron app. This repository does not contain that desktop. Offline demo is scripted; say that in the video.

### Architecture

See `docs/hackathon/architecture.svg` and `ARCHITECTURE.md`.

---

## Built with (checkboxes / tags)

Strands Agents SDK, Amazon Bedrock, Amazon Nova Lite, Python, OpenTUI, Bun, Amazon Bedrock AgentCore (optional sketch), AWS IAM, AWS Budgets

## Try it out

https://marcorojasb.github.io/tero/

```
python -m tero demo --offline --yes
```
