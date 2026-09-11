# AGENTS.md

Instructions for AI contributors working on tero.

## Product
- Teacher agent: **conversa, propone, y solo escribe si la persona aprueba**.
  Entiende el primer mensaje y actúa según la intención: **a)** responder o
  interactuar, **b)** crear material nuevo, **c)** editar o adaptar material
  existente (incluida adaptación a NEE).
- Sin flujo por pasos: no hay rumbos 1–4, plan tipado con `a`/`e`/`x`,
  clarificaciones numeradas ni puerta `s` / `n` / `b` / `c`. Si falta
  información, el agente **pregunta en lenguaje natural**.
- Antes de escribir, muestra en interfaz clara **lo que va a hacer + vista
  previa** y pide aprobación. Solo la aprobación explícita del usuario
  permite escribir. El modelo nunca escribe archivos directamente.
- Spanish UI copy. Chilean classroom tone, not marketing Spanish.
- Carpeta de trabajo is the system of record. Never overwrite originals. Hash-check reads.
- Default model id: `amazon.nova-lite-v1:0`. Offline scripted path must stay green.
- Public face: the real OpenTUI, virtualized in one window on GitHub Pages (`site/`).
  Photocopied paper only for pages tero creates. Not a SaaS hero.
  Warnings never block approval — see `docs/PUERTA-Y-PR8.md`.

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
- Commits: conventional, present tense, one concern each (`feat:`, `fix:`, `docs:`, `test:`, `ci:`). **Sin `Co-authored-by`.**
- Prefer depth on the teacher loop over new gadgets.

## Pull requests
- El título del PR es conventional (`fix:`, `feat:`, `docs:`, `test:`, `ci:`) y **no puede contener la palabra `cursor`**. El PR no se llama cursor.
- Los commits **no llevan `Co-authored-by`**. Sin coautoría de Cursor, bots ni otras personas.
- Cada PR es un solo concern. En cuanto se abre, **otro agente lo analiza y lo mergea de forma independiente**. No mergees tu propio PR. No juntes trabajo no relacionado en el mismo PR.
