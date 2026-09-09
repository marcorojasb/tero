# AGENTS.md

Instructions for AI contributors working on tero.

## Product
- Teacher agent: **prepare, don’t decide**. The human gate is `s` / `n` / `b` / `c`.
- Spanish UI copy. Chilean classroom tone, not marketing Spanish.
- Carpeta de trabajo is the system of record. Never overwrite originals. Hash-check reads.
- Default model id: `amazon.nova-lite-v1:0`. Offline scripted path must stay green.

## Stack
- Python 3.11+ / `strands-agents` in `src/tero`.
- OpenTUI in `tui/` via Bun and `@opentui/core` (imperative renderables, not React/Solid).
- Bridge: one JSON object per line. Logs on stderr only.

## Do not
- Put secrets, `.env`, or AWS keys in git.
- Add Electron, TipTap, Meridian, Biblioteca, iPhone, or Ollama-as-default.
- Give the model a tool that writes into `fuentes/` or arbitrary paths.
- Fake a Bedrock call in `--offline`. The OfflineModel is a real Strands `Model` and must stay labeled `tero-offline`.
- Collapse all artifact types into one undifferentiated markdown dump.

## How to run
```
pip install -e ".[dev]"
python -m tero demo --offline --yes
python -m tero tui --offline
pytest && (cd tui && bun test src)
```

## Style
- Python: ruff (`E,F,I,W,UP`), format with ruff.
- Commits: conventional, present tense, one concern each (`feat:`, `fix:`, `docs:`, `test:`, `ci:`).
- Prefer depth on the teacher loop over new gadgets.
