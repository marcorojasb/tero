# Video script — ≤ 5 minutes

Upload to **YouTube or Vimeo, public**. No need to appear on camera.
Voiceover in **English** (judges). On-screen UI stays **Spanish** — that is the
product, built for Chilean teachers.

Say out loud, once: **the offline path uses `tero-offline`, a scripted Strands
model, not a live Bedrock call.** Then, if keys work, 20–40 s of Nova Lite.

## 0:00–0:40 — problem / who / why

Teachers don't need another chatbot. They need tomorrow's photocopy from **this**
folder: the story they actually read, the OA they marked, this week's vocabulary.
And they cannot paste their students' data into a cloud tool.

tero is a **conversational** teacher agent. You write in plain Spanish; it
understands what you want, shows you exactly what it will write, and waits.
Nothing is written until you approve — with `y`, or just saying *"dale"*.

Track: **Professional Agents**.

## 0:40–1:10 — architecture (one slide)

Show `docs/hackathon/architecture.png`.

- The teacher writes a message in natural Spanish; tero coordinates a **Strands Multi-Agent Graph** (`GraphBuilder`)
  with a pedagogical drafter and a quality gate auditor.
- Full OpenTelemetry tracing via **`StrandsTelemetry`** captures graph turns and audits.
- Amazon Bedrock Model Trio (`amazon.nova-lite-v1:0` with `ModelRouter` fallback, `zai.glm-4.7-flash`,
  and `minimax.minimax-m2.5`) does text inference; the classroom folder never leaves the machine.
- Three intents: **answer**, **create**, **edit or adapt** (including Decreto 83 NEE accommodations).
- In-memory proposal gate: zero write tools in the registry. Host writes to `derivados/` only after teacher approval.
- Originals in `fuentes/` are SHA-256 hashed and verified intact.

## 1:10–3:10 — working demo (offline, honest)

Terminal:

```bash
python -m tero demo --offline --yes
```

Cut to the TUI (`python -m tero tui --offline`):

1. Home: the queltehue and one prompt line — *"Pregunta, explora o crea…"*
2. **Intent a — answer:** ask *"¿Qué fuentes tengo en la carpeta?"*; tero answers
   and writes nothing.
3. **Intent b — create:** ask for a 45-minute reading guide. Show the proposal
   card: summary, citations, and the full preview. Press `y` → the file appears
   under `derivados/` and the photocopied page renders.
4. **Intent c — adapt:** *"Adapta la guía para un estudiante con NEE"*. Show
   `acceso · tiempo: …`, the non-blocking `paci_no_oficial` advisory, and that
   the **new** file references `origen:` while the original is byte-identical.
5. Optional conversational change: *"mejor hazlo para 2° básico"* → tero revises
   the same proposal instead of starting over.
6. Optional `/export latex`.

Show `git status` or a hash: `fuentes/` unchanged.

## 3:10–4:00 — live Bedrock & Model Trio (if keys are available)

Fast diagnostics in the terminal:
```bash
python -m tero check-aws --all-models
```
Show all 3 Bedrock models passing live in seconds (Nova Lite, GLM 4.7 Flash, MiniMax M2.5).

Then launch the live agent:
```bash
python -m tero tui
```

Same loop, now powered live by **Amazon Nova Lite** (`amazon.nova-lite-v1:0`) with
`ModelRouter` automatic regional failover. Mention the benchmark: 5 models tested across
4 pedagogical journeys; Nova Lite 100% at ~10 s mean, `zai.glm-4.7-flash` strictly adhering
to Decreto 83 NEE schema, and `minimax.minimax-m2.5` producing rich rubrics. If keys fail,
do **not** pretend. Stay on offline and say Bedrock is the live path in the README.

Optional 10 s: the official curriculum bank answering with real MINEDUC item ids.

## 4:00–4:40 — impact

One teacher, one folder, pages for tomorrow — grounded in official curriculum
items rather than invented, and compliant with Chile's Ley 21.719 because student
health and grade data never reaches the model. Warnings are visible and never
block the teacher.

## 4:40–5:00 — close

Repo: github.com/marcorojasb/tero
`pip install -e ".[dev]"` → `python -m tero demo --offline --yes`
MIT. #AgentsforHumans

## Don't

- Call offline "Bedrock".
- Call the harness "tero in production".
- Show AWS keys.
- Block approval with a lecture about quality.
- Show the old `s` / `n` / `b` / `c` gate or a rumbos menu — that flow is retired.
