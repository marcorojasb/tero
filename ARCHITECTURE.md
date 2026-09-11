# Architecture — tero

tero is a **conversational Strands agent** plus an **OpenTUI** shell. The
agent understands the first message and acts on the intent: **a)**
answer or interact, **b)** create new material, **c)** edit or adapt
existing material (including NEE adaptation). It only writes when the
person approves. The only artifact writes are `derivados/` (approved)
and `borradores/` (draft kept without approval). Originals are hashed
and never overwritten.

> Target contract (this doc). Code migration follows in later PRs
> (session, TUI, CLI, tests); until then, code may still show the
> previous step-by-step flow.

The public face of the repo is the **OpenTUI of tero**, virtualized in
one window — not a splash wave, not a SaaS page. Photocopied paper is
only for pages tero creates:
[site/](site/) → <https://marcorojasb.github.io/tero/>.

## Thesis

> your sources, your judgment / agent converses, person approves

The teacher's folder is the system of record. Tools only read. There is
no step-by-step flow: no home rumbos 1–4, no typed plan with approve /
edit / cancel keys, no numbered clarifications, no `s` / `n` / `b` / `c`
gate. If information is missing, the agent **asks in natural language**.
Before writing, it shows **what it will do + a preview** and asks for
approval. Warnings never block approval. See
[docs/PUERTA-Y-PR8.md](docs/PUERTA-Y-PR8.md) for why the old blocking
gate was rejected — the same reasoning now applies to conversational
approval.

## Components

```mermaid
flowchart TB
  subgraph TUI["OpenTUI (Bun / @opentui/core)"]
    Chat[Conversación]
    Proposal[Propuesta: qué hará + vista previa]
    Approval[Aprobación en lenguaje natural]
  end

  subgraph Host["python -m tero bridge"]
    JSONL[JSONL stdin/stdout]
    Agent[Strands Agent]
    Offline[OfflineModel tero-offline]
    Bedrock[BedrockModel]
    Tools[list_sources / read_source (sandbox)]
    Salvage[salvage prose or JSON]
    Coerce[payload contracts]
    Approve[host writes only after approval]
  end

  subgraph Disk["Carpeta de trabajo"]
    Fuentes[Originales .md .txt .pdf]
    Derivados[derivados/]
    Borradores[borradores/]
  end

  TUI --> JSONL
  JSONL --> Agent
  Agent --> Offline
  Agent --> Bedrock
  Agent --> Tools
  Tools --> Fuentes
  Agent --> Salvage
  Salvage --> Coerce
  Approval --> Approve
  Approve --> Derivados
  Approve --> Borradores
```

## Loop

1. The teacher writes a first message in natural language. The agent
   understands the intent: **a)** answer / interact, **b)** create new
   material (planificación, guía, evaluación, pauta, actividad),
   **c)** edit or adapt existing material (versions, NEE adaptation).
2. If information is missing (course, subject, OA, length, which file to
   edit), the agent **asks in natural language** — no numbered options,
   no typed plan to approve.
3. The agent **reads** only inside the carpeta (path sandbox + hash index)
   and prepares the answer or material **in memory**, with evidence
   citations. Payload JSON (or markdown fallback) fills the LaTeX
   template. Tool use is capped (`DRAFT_TOOL_BUDGET`). Activity emits
   **one start per tool call**, not per stream delta.
4. Warnings (OA mismatch, thin skeleton, missing rubric, paraphrase,
   unknown path) are **visible and non-blocking**.
5. Before writing, the agent shows **what it will do + a preview** and
   asks for approval in natural language. On explicit approval the
   **host** writes `derivados/`; a draft the teacher shelves goes to
   `borradores/`; a correction (`c`-style critique under
   `.tero/criticas/`) triggers another pass. The model never writes files.
6. Re-hash originals after write. A change is a warning, never a rewrite
   of the source.

## Why this conversational shape

The previous tree used Strands `HumanInTheLoop` around a `write_derived`
tool, then a host gate with `s` / `n` / `b` / `c`, typed plans and
numbered clarifications. That flow is retired: it forced every teacher
through the same steps whether she wanted a quick answer, a new
evaluación, or a small edit.

What stays from that history: the agent loop is Strands, the write is
the **host** so the TUI can show the proposal, the evidence, and the
correction pass without the model being able to dump a file mid-stream.
Approval is now conversational, but it is still structural: only an
explicit user approval after a clear preview lets the host write.

A draft that blocked `s` on `thin_evidence` / `unknown_source` (PR #8)
was rejected: it made the host the teacher. Quality loops with Nova Lite,
MiniMax, GLM and Qwen showed usable fichas that almost always carry a
paraphrase warning. Those must still be approvable.

## Trust boundaries

| Can the agent… | |
| --- | --- |
| Read files outside the work folder | No |
| Overwrite originals | No (`WriteGuardError`) |
| Write `derivados/` itself | No — only the host, after explicit user approval of a clear preview |
| Invent a live Bedrock call in `--offline` | No — `tero-offline` is a scripted Strands `Model` |
| Cite a snippet that is not in the file | Allowed, but host marks it `verified: false` and warns |
| Block approval because citations are thin | No — that is the teacher’s call |

Package layout: `src/tero` (canonical). The older `tero/` layout from
PR #1 is not used.
