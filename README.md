# tero

**your sources, your judgment — the agent proposes, the educator decides**

```
╭─ tero ─────────────────────────────────╮
│ offline · conversación                 │
╰────────────────────────────────────────╯
      ▄▄▄▄▄      ▄▄▄▄▄
    ▄████████  ▀▀▀▀▀▀▀▀▀▀
  ▀▀▀▀███████              tero
       ██████              tus fuentes, tu criterio
       ██████▄
      ██████████▄
            █ █
            ▀ ▀
╭─ mensaje ──────────────────────────────╮
│ Pregunta, explora o crea…              │
╰────────────────────────────────────────╯
```

**tero** is an open-source, keyboard-first conversational AI teacher agent built for Chilean K-12 educators. Powered by the **AWS Strands Agents SDK** and **Amazon Bedrock**, it runs inside a dense **OpenTUI** terminal shell (from the same terminal family as [OpenCode](https://opencode.ai)). 

While tero converses in authentic Chilean classroom Spanish—tailored for teachers preparing real-world lesson plans, reading guides, quizzes, and special education adaptations—the engineering and architecture are built to global standards for the **[Agents for Humans](https://agentsforhumans.devpost.com/) AWS Global Hackathon** (Track: **Professional Agents**).

- **Live Interactive Demo:** [marcorojasb.github.io/tero](https://marcorojasb.github.io/tero/) (virtualizes the authentic OpenTUI in a single window). If the GitHub Pages link returns 404 on a fresh fork, enable Pages under [Settings → Pages](https://github.com/marcorojasb/tero/settings/pages) (Source: **GitHub Actions**) and re-run the `pages` workflow.
- **Cheapest & Fastest Live Path:** Native serverless **Amazon Nova Lite** (`amazon.nova-lite-v1:0`) on Amazon Bedrock—see [docs/AWS-GRATIS.md](docs/AWS-GRATIS.md).
- **Scientific Benchmark Paper:** [docs/EVALUATION-PAPER.md](docs/EVALUATION-PAPER.md).
- **Judge Quickstart (English):** [docs/hackathon/JUDGES-EN.md](docs/hackathon/JUDGES-EN.md) · Submission Pack: [docs/hackathon/README.md](docs/hackathon/README.md).

![TUI de tero: OpenTUI terminal with southern lapwing silhouette](site/assets/tero-og.png)

---

## The Human-in-the-Loop (HITL) Contract

```
teacher message → intent inferred (inquiry | creation | adaptation) → in-memory proposal + preview → explicit human approval → derivados/
```

1. **The model never writes files directly:** Language model tools only read local files and query the curriculum bank. All proposed artifacts live strictly in memory as structured `Propuesta` objects.
2. **Your local folder is the immutable System of Record (SoR):** Original classroom readings in `fuentes/` are verified with SHA-256 digests; tero refuses to overwrite them.
3. **Transparent pre-write staging:** Before anything is written, tero displays a concise summary, specific section modifications, and an exact Markdown preview.
4. **Natural conversational approval:** The educator reviews the proposal and decides in natural language (e.g., *"dale"*, *"me parece bien"*, *"sí"*, or key **`y`** in the TUI), requests an adjustment (*"cambia la pregunta 1 para que sea..."*), or discards (*"no, descártalo"* / **`n`**). Only host-side code writes to `derivados/`.
5. **Warnings never block the educator:** Heuristics (`thin_evidence`, `unverified_citation`, `paci_no_oficial`) inform the teacher of trade-offs but **never block approval**. See [docs/PUERTA-Y-PR8.md](docs/PUERTA-Y-PR8.md) and protocol specification in [docs/CONVERSACIONAL.md](docs/CONVERSACIONAL.md).

---

## 20-Minute Judge Path

Requires **Python 3.10+** (Python 3.11+ recommended). Two execution tracks:

| Track | Elapsed Time | What it Proves |
| :--- | :---: | :--- |
| **Track A. Offline** | ~2 min | Full Strands Agent loop (tools + in-memory proposal + evidence + natural approval + file emission into `derivados/`) with a scripted model. **USD $0, zero API keys**. |
| **Track B. Bedrock** | ~15 min | Identical loop powered live by **Amazon Bedrock** (`amazon.nova-lite-v1:0`, `zai.glm-4.7-flash`, or `minimax.minimax-m2.5`). |

### Track A. Offline (Zero Keys — Instant Verification)

```bash
git clone https://github.com/marcorojasb/tero.git
cd tero
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m tero demo --offline --yes
```

Uses a real `strands.Agent` combined with a deterministic `OfflineModel` explicitly labeled **`tero-offline`** (does not fake a cloud call). It reads `examples/carpeta-demo/`, queries the local sources, proposes a lesson plan with citations and preview, auto-approves (`--yes`), and writes the generated Markdown to `derivados/`. Original files stay untouched.

To test the **interactive conversational gate** (drop `--yes`):
```bash
python -m tero demo --offline
# tero presents the in-memory proposal and asks:
# ¿Escribo este material? (sí / no / pide un cambio)
```

To launch the **OpenTUI terminal interface** (requires [Bun](https://bun.sh)):
```bash
python -m tero tui --offline
```

- **Keys & Shortcuts:** **`y`** approve (host writes to `derivados/`) · **`n`** discard · type naturally in the prompt stream (*"dale"*, *"no, gracias"*, *"mejor para 2° básico"*) · **`r`** retry · **`?`** contextual help · **`[` `]`** cycle evidence · **Tab** switch panels · **`/export md|docx|latex`** export latest approved artifact.

---

### Track B. Amazon Bedrock (Serverless Default)

Zero cloud infrastructure setup: one Strands agent connecting directly to Bedrock ConverseStream API. **No** AgentCore Runtime/Gateway servers required.

#### AWS Free Tier / Amazon Nova Lite Checklist

1. **AWS Region:** Default **`us-east-1`** (or any region with Amazon Nova on-demand).
2. **Model Access:** Serverless Amazon Nova models auto-enable on the first `InvokeModel` call.
3. **IAM Permissions:** `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on `amazon.nova-lite-v1:0`.
4. **Environment Setup:**
   ```bash
   cp .env.example .env
   # Edit .env -> set TERO_OFFLINE=0 and fill AWS credentials
   python -m tero demo --yes
   # or launch the live TUI:
   python -m tero tui
   ```

Default model: `amazon.nova-lite-v1:0` via `TERO_MODEL` (alias `TERO_MODEL_ID`). Alternative verified models on Bedrock: `zai.glm-4.7-flash` and `minimax.minimax-m2.5`.

---

## The 4 Canonical Pedagogical Journeys

Tero is engineered to handle 4 real-world classroom workflows without rigid menu steps:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Pedagogical Inquiry (Intent a)                                           │
│    "What sources do I have for 4th grade and what official guidelines       │
│     exist for reading comprehension?"                                       │
│    -> Conversational answer, inspects folder & Begonia bank, ZERO file writes.│
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Grounded Material Creation (Intent b)                                    │
│    "Create a 45-minute reading guide based on the folder's story, querying  │
│     the pedagogical bank for official MINEDUC OA 4 items."                  │
│    -> Reads local files + Begonia API, proposes in memory, writes on "dale". │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Special Education (NEE) Adaptation under Decreto 83 (Intent c)           │
│    "Adapt the previous guide for a student with learning accommodations     │
│     using Decreto 83 access criteria (extra time and visual scaffolding)."  │
│    -> Populates notas_nee ('acceso · tiempo: ...'), emits paci_no_oficial,  │
│       writes a NEW file in derivados/ leaving origin untouched.             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Assessment Variation ("Fila B") & Interactive Dialogue (Intent c)        │
│    "Generate a Fila B swapping questions. [Then]: Change item 1 to evaluate │
│     character attitude instead."                                            │
│    -> Model proposes, handles conversational refinement, and writes on OK.   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Empirical Model Benchmarks (Top 3 Selected)

We conducted an empirical evaluation across 5 models on Amazon Bedrock. See full paper in [docs/EVALUATION-PAPER.md](docs/EVALUATION-PAPER.md).

| Model Identifier | Success Rate | Mean Latency | Primary Recommended Use Case |
| :--- | :---: | :---: | :--- |
| **`amazon.nova-lite-v1:0`** | **100%** | **10.0s** | **Hackathon & Classroom Default:** Lowest cost (~$0.06/1M tok), native serverless, dense official Begonia citations. |
| **`zai.glm-4.7-flash`** | **100%** | **10.6s** | **High-Speed Precision Engine:** Sub-10s tool calling, exact Decreto 83 NEE schema compliance. |
| **`minimax.minimax-m2.5`** | **100%** | **39.5s** | **Classroom Prose & Rubrics:** Highest pedagogical depth, authentic Chilean classroom voice, full assessment rubrics. |

---

## Official Pedagogical Bank Integration (`begonia`)

Tero connects locally (`http://127.0.0.1:8766`) to **begonia**, an offline read-only database mirror curated from official Chilean Ministry of Education (`Curriculum Nacional`) frameworks:
- **13,722 approved pedagogical items** and **1,159 teacher guidances** indexed by official learning objectives (e.g., `CN05 OA 12`).
- Integrated tools: `buscar_banco`, `leer_item_banco`, and `orientaciones_banco`.
- Official citations receive the `banco:<id>` prefix, verified directly against the bank.
- Full provenance traceability: approved artifacts embed `banco_snapshot: <id>` in their front matter. If the bank is offline, tero degrades gracefully to local sources.

---

## Statutory Privacy Guard (Ley 21.719)

Chile's **Ley 21.719** on personal and health data protection takes effect on December 1, 2026, strictly forbidding automated processing of student health data in educational environments (Art. 16 bis).
- `tero.privacy` automatically intercepts file admission: gradebooks (`notas*.csv`), diagnostic reports (`fudei*`, `paci*`), and files containing Chilean national IDs (RUT) are **excluded from the model context**.
- Files remain intact on disk. A single non-blocking advisory (`dato_sensible_excluido`) informs the educator. Configurable via `TERO_DATOS_SENSIBLES=excluir|incluir`.

---

## LaTeX & PDF Compilation (Zero Hallucinated TeX)

Language models never emit raw LaTeX or uncontrolled `\documentclass` code. The host engine populates pre-audited templates in `templates/latex/` directly from Markdown or structured JSON schemas:

```bash
# Export approved artifact to LaTeX / PDF:
python -m tero export --format latex path/to/artifact.md
# Compile to PDF if latexmk is installed:
python -m tero export --format latex --pdf path/to/artifact.md
```

---

## Project Architecture & Trust Boundaries

```
┌─ OpenTUI (Bun, @opentui/core) ─────────────┐
│  home · conversación · actividad           │
│  propuesta: qué hará + vista previa        │
│  evidencia ✓/? · avisos · aprobación y/n   │
└─────────────── JSONL stdin/stdout ─────────┘
                    │
┌─ python -m tero bridge  (Strands Agent) ───┐
│  tools: list/search/read (sandbox)         │
│         list_artifacts/read_artifact       │
│         list_oa/get_oa/search_oa (catálogo)│
│         buscar_banco/leer_item_banco       │
│         cite_evidence, proponer_crear,     │
│         proponer_editar  (en memoria)      │
│  host: hash check, privacy, coerce payload │
│         warnings, aprobación, write        │
│         export md|docx|latex (templates)   │
└────────────────────────────────────────────┘
                    │
         carpeta originales  (read-only, hashed)
         carpeta/derivados   (aprobado)
         carpeta/borradores  (legado)
```

| In Scope | Out of Scope |
| :--- | :--- |
| Teacher's folder as system of record | Electron desktop / TipTap / Meridian |
| Conversational intents (inquiry, creation, NEE adaptation) | Full Biblioteca cloud UI |
| Chilean Decreto 83 NEE accommodations (access vs. curricular) | Native iPhone companion app |
| Evidence verification panel (local files + official Begonia bank) | SQLite session database as user-facing product |
| Ley 21.719 student health and personal data privacy filter | Ollama as default |
| Safe LaTeX/PDF export via JSON schema templates | Secrets stored in git repository |
| Visible, non-blocking pedagogical trade-off warnings | Magic `forzar` overrides to bypass human teacher |

---

## Testing & Verification

```bash
# Python unit, integration, and benchmark suite:
pytest
# Code style and formatting checks:
ruff check src tests && ruff format --check src tests
# OpenTUI terminal test suite:
cd tui && bun install && bun test src
```

---

## Hackathon Disclosure & Prior Work

This public repository is a **new project** built specifically for the **Agents for Humans: AWS AI Agent Global Hackathon**. The pedagogical product concept (teacher-in-the-loop preparation for Chilean schools) is inspired by **Pteron**, an earlier private application by the author. No code was copied from that private Electron/SolidJS codebase. The offline demonstration track is purposefully scripted with an honest `tero-offline` label so evaluators can run the system immediately without cloud keys.

See [docs/NORMAS.md](docs/NORMAS.md), [AGENTS.md](AGENTS.md), and [CONTRIBUTING.md](CONTRIBUTING.md).
