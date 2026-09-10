# Informe de mejoras — TUI Pteron × OpenCode

Autorizado por Marco Rojas. Rama: `feat/tui-pteron-opencode`.

## Stress notes (antes del overhaul)

Hallazgos del stress test (TUI Bedrock en la máquina de Marco + corridas offline):

1. **Chips desincronizados del encargo** — p.ej. prompt de *fracciones 6°* mientras los chips seguían en *4° Lenguaje*. El plan y las citas heredaban el encargo viejo.
2. **Fuentes de dominio incorrecto** — carpeta demo de lenguaje citada para un encargo de matemática, sin aviso visible de desajuste.
3. **Plan delgado vs card Pteron** — faltaban RESULTADO PREVISTO, DECISIONES CONFIRMADAS, CÓMO LO ABORDARÉ, SUPUESTOS QUE PUEDES CAMBIAR y clarificaciones con opción SUGERIDA.
4. **Home ausente** — la TUI abría en grilla 4 paneles vacía; no había landing con marca + 4 rumbos + hero input.
5. **`/export` confuso tras `b`** — mensaje *“no hay artefacto aceptado”* aunque existía borrador en `borradores/`.
6. **`/oa` / `/tipo` regeneraban plan** dejando propuesta previa → contexto mezclado / stale.
7. **Ayuda cortada**, evidencia `[ ]` rara con 1 ítem, status sin detalle de tools, errores solo en status line, supuestos solo por slash.

## Qué aterrizó (P0 + P1)

### Home Pteron
- Pantalla inicial: marca **tero**, tagline, rumbos **Planificar / Crear / Evaluar / Adaptar** (1–4), hero *“Pregunta, explora o crea…”*.
- Chips **solo después** de rumbo o prompt; sesiones recientes si hay artefactos en la carpeta.

### Plan profundo
- Card con título/meta, objetivo, RESULTADO PREVISTO, DECISIONES (curso/asignatura/tema), CÓMO LO ABORDARÉ, SUPUESTOS editables (`e` / `/supuesto`).
- Clarificaciones numeradas + badge **SUGERIDA** + texto libre.
- `a` aprueba; plan pinneado mientras redacta; `x` cancela → home limpio.

### Puerta / evidencia / avisos
- Franja de puerta con labels claros s/n/b/c.
- Evidencia ✓ (en archivo) / ? (parafraseo) + snippet; contador `1/N`; no-op limpio si N≤1.
- Avisos no bloqueantes visibles; panel de error dedicado + `r` / `/retry`.

### Densidad / flujo (hackathon UX)
- Menos leyendas duplicadas: atajos viven en la franja de puerta/plan; el pie no los repite.
- Home más quieto (sin repetir offline/modelo); chips y paths recortados.
- Etapas adaptativas: en plan/clarificar se oculta el chrome vacío de propuesta+evidencia; en puerta el plan pasa a resumen (`p` detalle) y mandan propuesta + s/n/b/c.
- Evidencia con wrap de OA/sección (menos cortes a mitad de frase); títulos de plan acortados.

### Stress Bedrock (2026-09-10)
- Ver [STRESS-BEDROCK.md](STRESS-BEDROCK.md): EventStreamError bajo carga, hangs del bridge, evidencia thin/unknown aceptada en `derivados/`, demos flaky en carpetas no-demo.

### Robustez
- Sync de chips desde el prompt (curso/asignatura/tema/tipo/rumbo).
- Aviso `domain_mismatch` si el encargo no calza con la carpeta.
- Nuevo encargo / `/oa` `/tipo` limpian propuesta stale.
- Enter vacío / basura / pegado largo: mensajes claros, sin crash.
- Errores Bedrock humanizados + reintento.
- Spinner / thinking con actividad de tools.
- Resize → modo compacto.
- `?` contextual por fase.
- Crítica `c` persistida en `.tero/criticas/`; `/export` acepta **aceptado o borrador** + sidecar de feedback.
- Rumbo → tipo; multi-entregable (p.ej. evaluación + pauta).

### P2 parcial
- Tokens de tema densos estilo OpenCode.
- Este informe + mitigaciones en `docs/ANALISIS-ADVERSARIAL.md`.
- README actualizado (flujo home → plan → puerta).

## Round 2 (post-CI format fix)

Additional adversarial hardening after `style: ruff format` went green:

| Gap | Fix |
| --- | --- |
| `/export` after `b` still felt like failure | Export accepts borrador; event carries `source_kind=borrador\|derivado` and copy says so |
| `/oa` `/tipo` left mixed proposal | `encargo.update` now **clears** pending draft + emits `proposal_cleared` (not only a warning) |
| Help clipped | Help panel is a ScrollBox; **PgUp/PgDn** (and Shift+↑/↓) scroll; footer hints it |
| Opaque “thinking” | Status emits `progress`/`step`/`detail` (1/2 read·plan, 2/2 draft, draft_retry) → TUI spinner label |
| Bedrock empty draft | `_draft_phase` auto-retries once with an explicit `draft_artifact` nudge before `no_draft` error |

Still open (honest): no source-line viewer; Bedrock not in CI.

Warnings **still** never block `s`. That is closed as product, not as
debt: [PUERTA-Y-PR8.md](PUERTA-Y-PR8.md). PR #8 (block `s` on thin /
unknown evidence, `SIGALRM`, `--yes` → `borradores/`) stays unmerged.

## Host contracts (corridas Bedrock 1–8)

Quality loop on plan-agua / eval-cuento / eval-sistemas (MiniMax, GLM,
Qwen) plus Nova Lite stress. What landed on `main` without hardcoding a
classroom recipe:

| Contrato | Dónde |
| --- | --- |
| Salvage de plan/borrador desde prosa o JSON | `tero.salvage` + `TeacherSession._draft_phase` |
| Reintento único de `draft_artifact` + stream retry | `session.py` |
| Tope de tools / turns en draft | `DRAFT_TOOL_BUDGET` / `DRAFT_AGENT_TURNS` |
| Un `activity` start por `toolUseId` (no por delta) | `TeacherSession._callback` |
| Payload aliases, ítems SM/V-F, guía anidada, pauta | `tero.coerce` + `latex/schemas` |
| `catalog_covers: false` en media; no relleno 4b–6b | tools OA |
| Avisos a la vista, `blocking: false` | `tero.evidence` |
| Landing = fotocopia | `site/` / GitHub Pages |

Qué no: AgentCore Runtime como producto; bloquear `s`; cues de un cuento
(`cóndor` / `huemul`) como si fueran el dominio universal.
