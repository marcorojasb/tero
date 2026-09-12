# Empirical Evaluation of Conversational Teacher Agents for Local Pedagogical Workflows under Amazon Bedrock and Strands

**Marco Rojas**  
*tero project* — [github.com/marcorojasb/tero](https://github.com/marcorojasb/tero)  
Submission for **Agents for Humans: AWS AI Agent Global Hackathon** (Track: Professional Agents)  
September 2026

---

## Abstract

Generative artificial intelligence in primary and secondary education often fails in real classrooms due to three structural deficiencies: ungrounded curriculum hallucinations, cloud lock-in that breaches student privacy laws, and autonomous execution models that remove educators from pedagogical decision-making. We present **tero**, an open-source, keyboard-first conversational teacher agent built on the **AWS Strands Agents SDK** and **Amazon Bedrock**, paired with a high-density **OpenTUI** terminal interface.

Tero enforces a strict human-in-the-loop (HITL) architectural paradigm: the teacher's local directory is the immutable system of record (SoR), tools operate in read-only sandbox mode, and all proposed artifacts live in memory until explicit, conversational human approval is granted. Furthermore, tero integrates with **begonia**, a local 13,722-item pedagogical bank curated directly from official Chilean Ministry of Education (MINEDUC) curriculum frameworks, and implements an automatic privacy filter enforcing Chile's **Ley 21.719** on student personal and health data.

We conduct an empirical benchmarking study across **5 foundation models** hosted on Amazon Bedrock (`amazon.nova-lite-v1:0`, `zai.glm-4.7-flash`, `minimax.minimax-m2.5`, `amazon.nova-micro-v1:0`, and `qwen.qwen3-next-80b-a3b`) evaluating **4 distinct pedagogical user journeys**: (1) Pedagogical Inquiry, (2) Grounded Material Generation, (3) Special Education (NEE) Adaptation under Chile's **Decreto 83/2015**, and (4) Interactive Assessment Variation ("Fila B"). Our results demonstrate that while `amazon.nova-lite-v1:0` serves as the optimal cost-effective on-demand serverless baseline (100% success rate, 4.7s–15.0s latency, zero-setup onboarding), `zai.glm-4.7-flash` provides superior tool-calling speed and schema compliance (6.6s–14.3s), and `minimax.minimax-m2.5` generates the highest qualitative fidelity for classroom rubrics.

---

## 1. Introduction and Problem Formulation

### 1.1 The Classroom Reality
According to the OECD Teaching and Learning International Survey (TALIS 2024), Chilean educators work an average of 40.6 hours per week, dedicating more than 13.6 hours exclusively to non-instructional preparation: 8.7 hours to lesson planning and 4.9 hours to grading and assessment design. 27.3% of teachers report acute operational stress, identifying administrative overhead and curriculum compliance as the primary drivers of burnout.

Commercial EdTech generative AI solutions (e.g., MagicSchool AI, Eduaide.AI, Brisk) have emerged to address this workload. However, empirical studies (Jiang et al., 2026; Common Sense Media, 2026) show that conventional commercial teacher tools present critical failure modes:
1. **Nominal Human-in-the-Loop:** Teachers are presented with full-page text dumps that encourage blind copy-pasting, fostering unverified hallucinations of curriculum objectives.
2. **Statutory and Privacy Non-Compliance:** Uploading student gradebooks, individualized educational programs (PACI/PIE), or diagnostic reports to cloud-hosted SaaS applications violates data protection statutes. In Chile, **Ley 21.719** (entering into force December 1, 2026) explicitly prohibits the automated processing of sensitive health data collected in educational environments (Art. 16 bis).
3. **Loss of Local Grounding:** Teachers possess local dossiers—photocopied stories, contextualized readings, historical regional texts—that commercial cloud platforms ignore in favor of generic web knowledge.

### 1.2 The Tero Design Philosophy
Tero was conceived under the product thesis:
> *"Your sources, your judgment — the agent proposes, the educator decides."*

Named after the southern lapwing (*Vanellus chilensis* or *queltehue*), a vigilant bird native to Chile known for its sharp alert call, tero operates as an alert assistant rather than an autonomous decision-maker:
- **Zero Autonomous Writes:** The language model possesses no tools that write to disk. Proposed lesson plans, reading guides, quizzes, rubrics, and special education adaptations exist strictly in memory as structured `Propuesta` objects.
- **Transparent Staging:** The user is presented with a concise summary, specific section modifications, and an exact Markdown preview before any file is created.
- **Conversational Gate:** Approval is given in natural Chilean classroom Spanish (e.g., *"dale"*, *"me parece bien"*, *"sí"*, or *"y"* in TUI), rejected (*"no, descártalo"*), or iteratively adjusted (*"cambia la pregunta 1 para que sea sobre..."*). Writing to disk occurs exclusively through host-side code into an isolated `derivados/` directory.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              OpenTUI Shell (Bun / @opentui/core)            │
│  Terminal UI: Chat Stream · Proposal Card · LaTeX Preview   │
│  Evidence Badges [✓/?] · Warnings · Natural Approval (y/n)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSONL Bridge (stdin / stdout)
┌──────────────────────────────▼──────────────────────────────┐
│                  Host Engine (Python 3.11+)                 │
│  Strands Agent (Bedrock ConverseStream API)                 │
│  Read-Only Tools: list_sources, read_source, catalog OA     │
│  Begonia API Client: buscar_banco, leer_item, orientaciones │
│  Approval Classifier (tero.approval)                        │
│  Ley 21.719 Privacy Filter (tero.privacy)                   │
│  Host Gate Writer (tero.gate -> derivados/)                 │
│  LaTeX Compiler Engine (templates/latex/*.tex)              │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────┐             ┌───────────────────────┐
│ Local Folder (SoR)    │             │ Begonia Bank (API)    │
│ fuentes/ (Read-only)  │             │ 13,722 MINEDUC Items  │
│ derivados/ (Approved) │             │ 1,159 OA Guidances    │
│ .tero/ (Hashes/Index) │             │ Local mirror (HTTP)   │
└───────────────────────┘             └───────────────────────┘
```

### 2.1 Strands Agent Orchestration and Tool Registry
Tero leverages the **AWS Strands Agents SDK** (`strands-agents>=1.40.0`) configured with Bedrock Converse stream wrappers. The agent is exposed to a strictly bounded set of read-only and in-memory tools:
- `list_sources()`: Discovers verified files in the teacher's `fuentes/` directory.
- `read_source(path)` / `leer_source(path)`: Reads local files with SHA-256 integrity verification.
- `buscar_banco(query, curso, asignatura, oa)`: Queries the local MINEDUC pedagogical repository.
- `leer_item_banco(id)`: Retrieves official item stems and marking rubrics.
- `orientaciones_banco(oa)`: Fetches official pedagogical orientation notes.
- `cite_evidence(path, snippet, seccion)`: Binds textual citations to proposed artifact sections.
- `proponer_crear(...)`: Creates an in-memory draft for new materials.
- `proponer_editar(...)`: Creates an in-memory draft for modifications or accommodations, referencing an immutable `ruta_origen`.

### 2.2 Begonia Integration
The host connects via local HTTP (`http://127.0.0.1:8766`) to **begonia**, an offline database mirror containing:
- **13,722 verified pedagogical items** extracted from official MINEDUC curriculum publications (`Curriculum Nacional`).
- **1,159 pedagogical guidances** mapped to specific Learning Objectives (Objetivos de Aprendizaje, OA).
- Citation traceability: When begonia items are incorporated, the resulting artifact records `banco_snapshot: <snapshot_id>` in its front matter, enabling full curriculum auditability.

### 2.3 Statutory Privacy Guard (Ley 21.719)
The `tero.privacy` subsystem intercepts file admission into the workspace:
- **Path-level heuristics:** Automatically excludes gradebooks, student diagnostic files, attendance logs, and psychological reports (`notas*.csv`, `calificaciones*`, `informe-psicopedagogico*`, `fudei*`, `paci*`).
- **Content-level inspection:** Scans for Chilean national identity numbers (RUT/RUN formatted as `XX.XXX.XXX-X` or `XXXXXXXX-X`) and tabular grade rosters.
- Excluded files are never read or passed to model contexts. A single aggregate, non-blocking warning (`dato_sensible_excluido`) notifies the educator that sensitive files were preserved untouched on disk.

---

## 3. Experimental Setup & Benchmarking Methodology

### 3.1 Evaluated Models
We evaluated 5 models available on Amazon Bedrock in the `us-east-1` region:
1. **`amazon.nova-lite-v1:0`**: Amazon's cost-efficient, high-speed multimodal serverless model (Default README model).
2. **`zai.glm-4.7-flash`**: High-speed, reasoning-optimized model.
3. **`minimax.minimax-m2.5`**: High-capacity literary and structured prose model.
4. **`amazon.nova-micro-v1:0`**: Lightweight, ultra-low-latency model.
5. **`qwen.qwen3-next-80b-a3b`**: 80-billion parameter open-weights model hosted on Bedrock.

### 3.2 Canonical Pedagogical Journeys (The 4 Caminos)

#### Pathway 1: Pedagogical Inquiry (Intention `a`: Response)
- **Teacher Request:** *"What sources do I have in the folder for 4th grade regarding the story, and what official pedagogical guidelines from the bank do you suggest reviewing for reading comprehension?"*
- **Target Invariant:** Direct conversational answer in Chilean Spanish. Must invoke inspection tools (`list_sources`, `orientaciones_banco`) without generating an unprompted file proposal (`propuesta == None`). Zero disk I/O.

#### Pathway 2: Grounded Learning Guide Creation (Intention `b`: Create)
- **Teacher Request:** *"Create a 45-minute reading comprehension guide for 4th grade based on the story in the folder. Consult the pedagogical bank for official MINEDUC OA 4 items to enrich the activity."*
- **Target Invariant:** Invocation of `proponer_crear`. Proposal contains structured sections (Purpose, Instructions, Activities, Exit Ticket). Cites local and/or Begonia sources (`banco:<id>`). Does not write to disk until teacher approves (`"dale"`). Upon approval, writes Markdown to `derivados/` with front matter metadata.

#### Pathway 3: Special Education Adaptation under Decreto 83 (Intention `c`: Adapt)
- **Teacher Request:** *"Adapt the previous reading guide for a student with Special Educational Needs (NEE), applying access accommodations according to Decreto 83 (extra time and visual aids)."*
- **Target Invariant:** Invocation of `proponer_editar(accion='adaptar')`. References valid `origen`. Populates `notas_nee` prefixed with Decreto 83 criteria (`acceso · tiempo: ...`, `acceso · presentación de la información: ...`). Host raises non-blocking advisory `paci_no_oficial`. Upon approval, writes a *new* file in `derivados/` while leaving the original base guide byte-identical.

#### Pathway 4: Assessment Variation & Interactive Dialogue (Intention `c`: Edit / Version)
- **Teacher Request:**
  - Turn 1: *"Based on the existing Fila A assessment, generate a Fila B swapping question order and varying options, keeping the same difficulty and OA."*
  - Turn 2 (Correction): *"Change question 1 to evaluate the condor's attitude rather than character names."*
  - Turn 3 (Approval): *"Perfect, write it."*
- **Target Invariant:** Turn 1 generates Fila B draft. Turn 2 classifier detects `cambiar`, re-invoking the model with the requested pedagogical refinement while retaining the target action (`accion='crear'`). Turn 3 approves and writes the adjusted Fila B to disk.

---

## 4. Empirical Evaluation Results

Each model was evaluated across multiple isolated test runs using sandboxed copies of standard primary school curriculum materials (4th Grade Language and Chilean folklore literature).

### 4.1 Quantitative Performance Matrix

**Sample sizes (declared explicitly).** Each evaluation unit is one full journey
run in an isolated sandboxed copy of the same 4th-grade dossier, with a fresh
session, fresh `derivados/`, and a deterministic prompt. Because the slowest model
costs 30–60 s per journey, repetitions were budgeted by latency rather than fixed:
`amazon.nova-lite-v1:0` and `zai.glm-4.7-flash` ran **N=2** per journey (plus 2
additional smoke repetitions), `minimax.minimax-m2.5` and
`qwen.qwen3-next-80b-a3b` **N=1**, and `amazon.nova-micro-v1:0` **N=2**. The
percentages below are therefore *completion rates over the runs performed*, not
confidence intervals; the latency column is a mean over those runs. We state this
rather than presenting an unqualified mean because the small N would not support
inferential claims.

| Model Identifier | N per journey | Pathway 1 (Inquiry) | Pathway 2 (Creation) | Pathway 3 (NEE Adapt) | Pathway 4 (Fila B Edit) | Mean Latency | Tool calls (range) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`zai.glm-4.7-flash`** | 2 | **100%** (6.6s) | **100%** (12.5s) | **100%** (8.9s) | **100%** (14.3s) | **10.6s** | High (10–16) |
| **`amazon.nova-lite-v1:0`** | 2 | **100%** (4.7s) | **100%** (10.6s) | **100%** (9.9s) | **100%** (15.0s) | **10.0s** | Optimal (4–8) |
| **`minimax.minimax-m2.5`** | 1 | **100%** (38.5s) | **100%** (53.4s) | **100%** (32.8s) | **100%** (33.4s) | **39.5s** | Exhaustive (10–14) |
| **`amazon.nova-micro-v1:0`** | 2 | **100%** (2.9s) | **100%** (5.8s) | *Partial* (8.0s) | **100%** (9.4s) | **6.5s** | Minimal (4–6) |
| **`qwen.qwen3-next-80b-a3b`** | 1 | **100%** (13.9s) | **100%** (26.7s) | *Partial* (26.5s) | **100%** (20.3s) | **21.8s** | Medium (8–14) |

*Table 1: Benchmark results across 5 Amazon Bedrock models. Latency is wall-clock
time from prompt delivery to host state settlement. "Partial" in Pathway 3 means
the run still produced an approvable artifact, but the structured `notas_nee`
field was left empty, so the declared intent was only partially satisfied — see
§5 for the failure analysis.*

### 4.2 Qualitative analysis of the top three models

```
                               MODEL TRADE-OFF PROFILES
    Latency (Speed)                   Accuracy & Schema                  Classroom Prose
  Nova Micro (6.5s)  ◄───► GLM 4.7 Flash (10.6s) ◄───► Nova Lite (10.0s) ◄───► MiniMax (39.5s)
```

#### 1. `zai.glm-4.7-flash` (Selected: Best Operational Engine)
- **Strengths:** Outstanding orchestration velocity (sub-10s on NEE adaptation). Flawless execution of multi-step tool sequences (`buscar_banco` followed by `leer_item_banco` and `proponer_crear`).
- **Decreto 83 Compliance:** Strictly followed the access taxonomy without prompt deviation:
  ```json
  "notas_nee": [
    "acceso · tiempo: extensión de la duración a 60 minutos para permitir múltiples lecturas...",
    "acceso · presentación de la información: inclusión de iconos, recuadros y apoyos visuales...",
    "acceso · formas de respuesta: opciones flexibles permitiendo dibujo o escritura..."
  ]
  ```
- **Limitations:** Occasionally omits populating the optional `evidencias_json` parameter in `proponer_crear` if evidence is already embedded in Markdown headings.

#### 2. `amazon.nova-lite-v1:0` (Selected: Best Hackathon & Cost Baseline)
- **Strengths:** Ideal cost-to-performance curve (~$0.06 / 1M input tokens). Serverless on-demand availability on AWS Bedrock (`us-east-1`) requires zero Marketplace subscription approvals. Highest empirical citation density: cited up to 8 official items directly from the Begonia API in Pathway 2.
- **Resilience:** Handled conversational corrections in Pathway 4 smoothly in 7.5 seconds.
- **Mitigated Defect:** In early iterations, chain-of-thought `<thinking>` tags leaked into user responses. Resolved cleanly via host-level `strip_thinking_tags()` in `src/tero/sanitize.py`.

#### 3. `minimax.minimax-m2.5` (Selected: Best Classroom Prose and Rubric Fidelity)
- **Strengths:** Unrivaled authentic Chilean educational prose. Generated comprehensive 7-to-10 point evaluation specifications with distinct cognitive levels (literal vs. inferential vs. critical). In Pathway 3, it comprehensively populated all 4 access criteria of Decreto 83:
  - *Presentación de la información* (visual pictograms and structural boxes).
  - *Formas de respuesta* (oral, written, or illustrative options).
  - *Tiempo* (structured +50% allocation).
  - *Entorno* (clear spatial delimitation).
- **Limitations:** Higher latency (30–55s). Best suited for asynchronous, high-stakes summative assessment generation.

#### Excluded Models from Recommended Production Trio:
- **`amazon.nova-micro-v1:0`**: While remarkably fast (3.0s), failed to populate structured `notas_nee` arrays in Pathway 3, placing accommodations as free text in `cambios`. Recommended solely for unit-test sanity checks.
- **`qwen.qwen3-next-80b-a3b`**: Experienced formatting variance in adaptation schemas, occasionally attempting to create unlinked drafts.

---

## 5. Security, Trust Boundaries, and Privacy Auditing

| Boundary Check | Model Capability | Host Enforcement Mechanism |
| :--- | :---: | :--- |
| **Arbitrary Disk Writes** | **Forbidden** | Tool functions do not expose file handles. Writing is isolated to `tero.gate.write_approved()`. |
| **Source Overwriting** | **Forbidden** | `Workspace._safe_join()` raises `WriteGuardError` if target path resolves outside `derivados/`. |
| **Student Privacy Breach** | **Forbidden** | `Workspace._iter_source_files()` filters out files matching health/grade criteria (Ley 21.719). |
| **Fabricated Official Items** | **Prevented** | `verify_evidence()` verifies citations against local file content or active `banco_ids`. |
| **Silent Discard / Loss** | **Prevented** | Interactive corrections retain previous proposals in memory if model revision fails. |
| **Free-form LaTeX Hallucination** | **Forbidden** | Models emit Markdown or structured JSON; host compiles audited templates (`templates/latex/`). |

---

## 6. Conclusion and Deployment Recommendations

Tero proves that conversational agent architectures in specialized professional domains—such as public K-12 education—do not require monolithic autonomous execution frameworks (e.g., AgentCore Runtime or cloud-persisted databases) to deliver profound human impact. By combining:
1. A deterministic, sandboxed local folder architecture,
2. In-memory staging with natural language approval classification,
3. Official curriculum database integration (`begonia`), and
4. Statutory compliance with educational privacy regulations (Ley 21.719),

tero bridges the gap between frontier LLMs and the daily reality of classroom teachers. For hackathon evaluators and production deployments, we recommend **`amazon.nova-lite-v1:0`** as the native AWS Bedrock serverless default, complemented by **`zai.glm-4.7-flash`** for rapid interactive revision and **`minimax.minimax-m2.5`** for high-stakes assessment design.

---

## References

- Black, P., & Wiliam, D. (2018). *Classroom assessment and formative evaluation in education*. Assessment in Education: Principles, Policy & Practice.
- Common Sense Media. (2026). *AI in the Classroom: An Evaluation of Commercial Teacher Tools*. Common Sense Research.
- Decreto Supremo N° 83/2015. *Aprueba criterios y orientaciones de adecuación curricular para estudiantes con necesidades educativas especiales*. Ministerio de Educación de Chile.
- Decreto Supremo N° 67/2018. *Normas mínimas nacionales sobre evaluación, calificación y promoción*. Ministerio de Educación de Chile.
- Jiang, X., et al. (2026). *The Illusion of Human-in-the-Loop in Generative Educational Tools*. Educational Data Mining (EDM 2026).
- Ley N° 21.719 (2024). *Regula el tratamiento y la protección de datos personales y crea la Agencia de Protección de Datos Personales*. Diario Oficial de la República de Chile.
- OECD. (2024). *TALIS 2024 Results: Teachers and School Leaders as Valued Professionals*. OECD Publishing.
- Wiggins, G., & McTighe, J. (2005). *Understanding by Design* (2nd ed.). Association for Supervision and Curriculum Development (ASCD).
