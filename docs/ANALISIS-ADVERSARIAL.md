# Análisis adversarial — tero

Red-team notes for Agents for Humans / Devpost. This is not a pitch. Read it
before recording the video or submitting the URL.

## What this repo actually is

tero is a **new public MIT project**. The *product idea* (teacher-in-the-loop
preparation: carpeta as system of record, agent drafts, human gate) is a sibling
of **Pteron**, a private Electron/Solid/Meridian desktop. This tree does not
contain that desktop. If a judge diffs the two, they should see a Python
Strands host + an OpenTUI shell + a JSONL bridge — not a port.

If the video or README slides into “this is Pteron in the terminal”, that is a
disclosure failure. Say: new stack, same thesis.

## Eligibility / honesty risks

| Risk | Status |
| --- | --- |
| Offline path pretending to be Bedrock | **Mitigated.** `--offline` is a real Strands `Model` labeled `tero-offline`. No AWS call. The video must say this out loud. |
| Dual HITL stories | **Resolved in this tree.** The first MVP on `main` let the model call a write tool behind `HumanInTheLoop`. This branch writes only in `tero.gate` after `s`/`b`. Do not demo the old `tero/` package; it is gone. |
| Co-authored / agent-looking commits on the judge path | Process: later commits are Marco-attributed. Older commits on the abandoned `cursor/…` branch are agent-authored. Do not submit that branch. |
| Secrets | `.env` is gitignored. `.env.example` has names only. CI has no AWS keys; the Bedrock path is **not** proven in CI. |

## Demo gaps a judge will notice

1. **`--yes` is not a teacher.** It auto-approves the plan and sends `s`. The
   interesting product is the TUI gate (`s/n/b/c`, crítica). If the video is
   only `python -m tero demo --offline --yes`, you have shown the loop, not the
   judgment.
2. **Offline content is scripted.** On `examples/carpeta-demo/` the model
   follows a fixed tool sequence and canned Spanish markdown. That is honest
   for a 2-minute video. It is not “the agent understood the cuento”.
3. **Other carpetas.** Offline now lists/reads whatever is in the folder
   (including `fixtures/aula-5basico-agua/` and its PDF) and cites real paths.
   The *prose* of the draft is still a template. A judge who opens the
   markdown will see structure + local filenames, not a deep reading of the
   glaciar PDF.
4. **PDF.** `pypdf` extract. Scanned PDFs become `[PDF sin texto extraíble]`.
   There is no OCR.
5. **Bedrock is the unpaid bill.** Default `amazon.nova-lite-v1:0` in
   `us-east-1`. No account, no demo. Nova enablement, IAM
   `InvokeModel`/`InvokeModelWithResponseStream`, and region mismatch are the
   usual failure modes. Temperature is `TERO_TEMPERATURE` (default 0.3). There
   is no retry/backoff UI.
6. **OpenTUI needs Bun.** `python -m tero tui` fails closed if Bun is missing
   and tells you to run the CLI demo. A judge without Bun still has the
   offline CLI.

## HITL — what is true, what is theater

True:

- `propose_plan` / `cite_evidence` / `draft_artifact` are in-memory.
- Only `apply_gate` writes `derivados/` (`s`) or `borradores/` (`b`).
- `n` writes nothing. `c` writes nothing and runs another agent pass.
- Originals are hashed. A write outside `derivados|borradores|.tero` raises
  `WriteGuardError`.
- After `--yes`, the CLI fingerprints sources and refuses to say `listo.` if
  they changed.

Theater / weak:

- The model can still *claim* a citation. The host now checks whether the
  snippet string (or a whitespace-normalized form) appears in the file.
  `verified: false` is a warning, not a block. A fluent paraphrase still
  looks like evidence in the panel (`?`).
- Warnings never block `s`. A thin skeleton, a missing rúbrica, an OA
  mismatch, an unknown path — the teacher can accept all of them. That is
  intentional (the sloppy-demo risk is real; the host still must not
  become the teacher). Confirmed after quality loops 1–8: see
  [PUERTA-Y-PR8.md](PUERTA-Y-PR8.md). The draft that blocked `s` is closed.
- `c` does not persist the crítica to disk. If the second pass fails, the
  note lives only in the session.
- Plan “edit” is local (`/objetivo`, `/oa`, …) then `a` sends the dict.
  There is no field-by-field modal.

**Update (`feat/tui-pteron-opencode`):** `c` now writes under `.tero/criticas/`
and is appended when the artifact is saved. Plan assumptions edit inline
(`e`); clarifications use numbered options + free text. See mitigations below.

## Mitigaciones aterrizadas (`feat/tui-pteron-opencode`)

Stress + Pteron/OpenCode overhaul. Lo que cambió de verdad:

| Riesgo / gap | Mitigación |
| --- | --- |
| Encargo vs chips desync (fracciones 6° vs chips 4° Lenguaje) | `encargo_sync.sync_encargo_from_prompt` reescribe curso/asignatura/tema/tipo/rumbo antes del turno; TUI refresca chips vía evento `encargo`. |
| Citas de dominio incorrecto (math vs carpeta lenguaje) | Warning no bloqueante `domain_mismatch` en `collect_warnings` + al inicio del turno. |
| Plan delgado vs card Pteron | Plan card con título/meta, resultado previsto, decisiones, cómo lo abordaré, supuestos editables (`e` / `plan.edit_assumption`). |
| Sin clarificaciones | Preguntas tipadas con opciones + badge **SUGERIDA** + texto libre (`plan.answer`). |
| Home ausente (grilla vacía) | Pantalla `home`: marca tero, 4 rumbos, hero input; chips solo tras rumbo/prompt. |
| `/export` tras `b` confuso | Exporta último **aceptado o borrador**; copy dice cómo llegar a `s` si no hay nada. |
| `/oa` `/tipo` dejan propuesta stale | Al cambiar encargo o nuevo prompt: `proposal_cleared` + avisos; TUI vacía propuesta/evidencia. |
| `c` no persistía | Críticas en `.tero/criticas/` + apéndice en el markdown al aceptar/borrar. |
| Ayuda cortada / evidencia `[ ]` con 1 ítem | `helpFor(phase)` paginado corto; no-op claro `1/1` si no hay más citas. |
| Status opaco / errores solo en footer | Spinner + label de tool; panel de error dedicado + `retry`. |
| Bedrock falla en crudo | `humanize_exception` → mensajes de auth/throttle/modelo/red + `retryable`. |
| Cancelar plan deja sucio | `plan_cancelled` → idle/home, limpia plan/propuesta/evidencia. |

## Mitigaciones currículum + LaTeX (`feat/curriculum-latex-nova-lite`)

| Riesgo / gap | Mitigación |
| --- | --- |
| Alucinación de OA / ids inventados (Nova Lite) | Catálogo host `curriculum/chile/catalogo.json` + tools `list_oa` / `get_oa` / `search_oa`. `get_oa` falla cerrado. `/oa` resuelve contra catálogo; warning `oa_unknown`. Offline llama `list_oa`→`get_oa` antes de `propose_plan`. |
| Dump del currículum en el prompt | El system prompt **no** pega el JSON; el modelo consulta tools. Disclaimer: no es texto oficial MINEDUC verbatim. |
| Nova Lite emite LaTeX roto / `\write18` | El modelo rellena **JSON schema**; host `repair_payload` + `escape_latex` + plantillas en `templates/latex/`. Nunca se pide TeX libre. |
| Export LaTeX sin control | `tero export latex` / `/export latex` sobre aceptado o borrador; PDF opcional con `latexmk -no-shell-escape`. |
| Evaluación / pauta sin criterio | `curriculum/chile/evaluacion/lineamientos.md` (resumen de aula, no asesoría legal) alimenta plantillas pauta/evaluación. |

Detalle adversarial: [ADVERSARIAL-LATEX-CURRICULO.md](ADVERSARIAL-LATEX-CURRICULO.md).

## Mitigaciones lean AWS (`feat/curriculum-latex-nova-lite`)

| Riesgo / gap | Mitigación |
| --- | --- |
| Credenciales / IAM / región opacos | `humanize_exception`: auth vs model-access vs throttle vs network en español; tip `TERO_MODEL` / Nova Lite / `us-east-1`. |
| Nova Lite entrega tools/texto sin `draft_artifact` | `_draft_phase` reintenta **una** vez con nudge explícito (`step=draft_retry`); luego `r`/`/retry`. |
| Juez sin AWS | Offline `tero-offline` intacto; README reserva video day al demo offline. |
| Confusión de env vars | `.env.example` + README checklist free tier; `TERO_MODEL` canónico, alias `TERO_MODEL_ID`. |
| Tentación de “completar AWS” con infra | **Precisado.** No AgentCore Runtime / Gateway / multi-agente / Code Interpreter. Observability + Memory docente *después* de que el loop entregue el artefacto. Ver [ADVERSARIAL-CORE-CALIDAD.md](ADVERSARIAL-CORE-CALIDAD.md). |

## Diferido (a propósito, ~video day)

- AgentCore **Runtime / Gateway / A2A** (la carpeta es SoR local). Observability/Memory: ver [ADVERSARIAL-CORE-CALIDAD.md](ADVERSARIAL-CORE-CALIDAD.md) — solo tras P0 de calidad.
- Live Bedrock en CI (hace falta secret + smoke barato)
- Source viewer con highlight de línea
- Catálogo curricular MINEDUC completo (el JSON es mínimo 4°–6°; media no está)
- PDF LaTeX obligatorio en CI (`.tex` basta; `latexmk` opcional en host)
- Ollama / local LLM como default

Ver [ADVERSARIAL-LATEX-CURRICULO.md](ADVERSARIAL-LATEX-CURRICULO.md).

Sigue siendo verdad (no mitigué del todo):

- Warnings no bloquean `s` (diseño).
- Offline sigue siendo prosa template + paths reales.
- No hay source viewer con highlight de línea.
- Bedrock no corre en CI.
- OpenTUI ≠ paridad con OpenCode ni con el desktop Pteron.
- Catálogo Chile es mínimo (4°–6°, tres asignaturas), no bases curriculares completas.

Ver también [docs/INFORME-MEJORAS.md](INFORME-MEJORAS.md).

## Evidence / plan / gate UX (what is built vs OpenCode envy)

Built: home Pteron, rumbo chips, session log, streaming activity + spinner,
markdown proposal, evidence list with `[` `]` and ✓/?, non-blocking avisos,
deep plan card + clarifications + editable assumptions, dedicated `s/n/b/c`
strip with labels, Tab focus, `/export` (aceptado o borrador), error panel + retry.

Not built: split-diff of crítica vs previous draft, jump-to-line in the
source, mouse-drag selection of a quote, multi-file workspaces, session
replay, or anything that looks like Pteron’s Biblioteca.

If a judge has used OpenCode, this TUI is in the same family and still thinner.
Do not claim parity.

## Thin vs Pteron (say this if asked)

| | Pteron (private) | tero (this repo) |
| --- | --- | --- |
| Shell | Electron + Solid | OpenTUI (Bun) |
| Agent | not this codebase | AWS Strands |
| SoR | richer library / desktop | one carpeta |
| Gate | desktop HITL | host `s/n/b/c` |
| Offline | n/a here | scripted Strands model |

Copying UI chrome from Pteron into this repo would be a mistake twice:
eligibility and taste.

## Bedrock coupling

- Default model id is hardcoded as a constant and overridable with
  `TERO_MODEL` / `TERO_MODEL_ID`.
- No Ollama default. Local models are a future, not a fallback.
- Streaming in the TUI is whatever Strands + Bedrock emit. Offline fakes
  small text chunks so the activity pane is not a single dump.
- The TUI does not show token usage or cost.

## TODOs that are real, not decorative

- Verify snippet **position** (line range) and highlight it in a source
  viewer. Today `start_line` exists on the type and is almost unused.
- Persist session + crítica (`c`) next to the artifact.
- Live Bedrock CI (needs secrets + a cheap smoke, not a full lesson).
- Pedagogical eval: OA alignment is a string compare **plus** host catalog
  resolve (`curriculum/chile/`). Still not a curriculum expert; unknown ids
  warn, they do not block `s`.
- `search_sources` is naive substring. Fine for a 5-file carpeta; not a
  retrieval stack.
- Export docx depends on `python-docx` (in the `dev` extra). A judge who
  `pip install -e .` without extras cannot `/export docx`.
- Export latex needs no extra deps for `.tex`; PDF needs `latexmk` on PATH.
- Spanish-only UI. That is a product choice, not i18n debt we pretend
  to have paid.

## How to attack this in 10 minutes

1. `python -m tero demo --offline --yes` — must print `escrito:`,
   `Originales intactos.`, `listo.`
2. Open the markdown under `derivados/`. Check front matter
   `generado_por: tero` and `## Evidencia` with `verificada`.
3. Change a source file, rebuild nothing, run again? Hash warning path:
   edit `fuentes/` yourself; `read_source` should flag `changed` and still
   not overwrite.
4. `python -m tero tui --offline` — type an encargo, `a` the plan, then
   `c` with a one-line crítica, then `s`. Confirm `derivados/` grew and
   `fuentes/` hashes did not.
5. Point `--carpeta fixtures/aula-5basico-agua` and confirm the PDF is
   listed and a write to `derivados/` does not alter `05-glaciar-nota.pdf`.
6. Ask for Bedrock only if credentials exist. If they do not, stop. Do
   not record a fake live call.

## Verdict

Good enough to judge as a **teacher-loop agent**: sandboxed carpeta, typed
plan, evidence that the host actually checks, a gate the model cannot skip,
an honest offline path, and a TUI dense enough to operate without a mouse.

Not good enough to judge as a **finished classroom product**: scripted
offline prose, Bedrock untested in CI, no source viewer, warnings that never
block, and a thinner shell than the private desktop that inspired the thesis.

Ship the first. Do not advertise the second.
