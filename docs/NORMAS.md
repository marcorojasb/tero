# Engineering norms

## Product

- tero is a **conversational teacher agent**: the agent proposes in memory, the
  person decides. Approval is conversational (`y`, *"dale"*, *"sí"*) or a change
  request in the same breath (*"mejor para 2° básico"*); `n` / *"no, gracias"*
  discards. The old `s` / `n` / `b` / `c` gate and the numbered rumbos menu are
  **retired** — see [CONVERSACIONAL.md](CONVERSACIONAL.md).
- The working folder is the system of record. `derivados/` is the only artifact
  write, and only after explicit approval. `borradores/` is legacy. Originals are
  indexed with SHA-256; if they change, tero warns, it never overwrites.
- UI in Spanish (Chilean classroom register), keyboard first, warnings that
  **never block** approval. `thin_evidence` / `unknown_source` /
  `unverified_citation` / `paci_no_oficial` are shown before the decision; the
  decision stays with the person. There is no magic `forzar` word.
  See [PUERTA-Y-PR8.md](PUERTA-Y-PR8.md).
- Default model: Bedrock `amazon.nova-lite-v1:0`. Offline is a scripted Strands
  `Model` labeled `tero-offline`, never a disguised API call.
- Official curriculum grounding comes from the read-only **begonia** bank
  (13,722 MINEDUC items). Citations use `banco:<id>` and artifacts record
  `banco_snapshot`.
- Chile's **Ley 21.719** privacy guard: gradebooks, rosters and health reports are
  never indexed or sent to the model (`src/tero/privacy.py`).

## Engineering

- Python 3.11+, package under `src/tero`, tests under `tests/`.
- Lint/format: `ruff check` + `ruff format`. CI must stay green.
- TUI: Bun + `@opentui/core`. Frame tests use `@opentui/core/testing`.
- JSONL protocol versioned (`v: 1`). Unknown inbound types are errors, not silent drops.
- No secrets in the tree. `.env` is gitignored; `.env.example` lists names only.
- Commit style: conventional commits, small diffs, no drive-by refactors. No
  `Co-authored-by` trailers.
- PR titles are conventional (`fix:`, `feat:`, …) and must not contain the word
  `cursor`. Each PR is one concern; another agent analyzes and merges it
  independently. Do not merge your own PR.
- HITL invariant: no tool may write teacher artifacts. Only the host gate
  (`tero.gate.write_approved`) writes, after approval.
- Citations are host-checked: a snippet that is not in the file (or not served by
  the bank in this turn) is `verified: false` plus a non-blocking warning. Never
  treat a paraphrase as a quote.
- **Language policy:** the product (TUI, CLI output, generated classroom
  artifacts) is Spanish. The repository, docs, code comments in judge-facing
  material and the public page's framing are English.

## How to run

```bash
# Offline / video
python -m tero demo --offline --yes

# Live Bedrock (credentials in the environment)
python -m tero tui

# Bridge only (OpenTUI spawns this)
python -m tero bridge --offline

# Tests
pytest && (cd tui && bun test src)
```

## Hackathon disclosure

New project, public MIT repository. The product concept is inspired by Pteron
(teacher workflow) without copying that private Electron app. The offline demo is
scripted on purpose; declare offline vs Bedrock honestly in the demo video.
