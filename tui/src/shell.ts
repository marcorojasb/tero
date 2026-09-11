import {
  BoxRenderable,
  InputRenderable,
  InputRenderableEvents,
  MarkdownRenderable,
  ScrollBoxRenderable,
  SyntaxStyle,
  TextRenderable,
  type CliRenderer,
} from "@opentui/core"
import {
  chips,
  footerFor,
  gateStrip,
  helpFor,
  PHASE_LABEL,
  planShowsDetail,
  RUMBOS,
  shortModel,
  shortPath,
  showChips,
  spinnerGlyph,
  TOOL_LABEL,
  type AppState,
} from "./state.ts"
import { theme } from "./theme.ts"

const syntax = SyntaxStyle.fromStyles({
  default: { fg: theme.text },
  "markup.heading.1": { fg: theme.accent, bold: true },
  "markup.heading.2": { fg: theme.accent, bold: true },
  "markup.heading.3": { fg: theme.accent },
  "markup.list": { fg: theme.text },
  "markup.raw": { fg: theme.ok },
  "markup.italic": { fg: theme.muted, italic: true },
  "markup.bold": { fg: theme.text, bold: true },
})

/** Compact queltehue — same bird as site/assets/tero.txt, sized for the home card. */
export const HOME_BIRD = [
  "         ▲",
  "        ╱│",
  " ▄▄▄▄▄ ╱(o)*",
  "█     █▄▀",
  "█ ▓▓▓▓  █",
  " ▀▄▓▓▄▄▄▀",
  "   ║   ║",
  "  ─┘   └─",
].join("\n")

export type Shell = {
  input: InputRenderable
  sync: (state: AppState) => void
  setPlaceholder: (text: string) => void
  scrollHelp: (delta: number) => void
}

export function mountShell(renderer: CliRenderer, onSubmit: (value: string) => void): Shell {
  renderer.setBackgroundColor(theme.bg)

  const root = new BoxRenderable(renderer, {
    id: "root",
    flexGrow: 1,
    flexDirection: "column",
    backgroundColor: theme.bg,
    padding: 0,
  })

  // ── Header ──────────────────────────────────────────────
  const header = new BoxRenderable(renderer, {
    id: "header",
    height: 4,
    flexDirection: "column",
    backgroundColor: theme.panel,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.border,
    paddingLeft: 1,
    paddingRight: 1,
    title: " tero ",
    titleColor: theme.brand,
    bottomTitle: "",
  })
  const headerLine = new TextRenderable(renderer, {
    id: "header-line",
    content: "",
    fg: theme.text,
    wrapMode: "none",
  })
  const chipLine = new TextRenderable(renderer, {
    id: "chips",
    content: "",
    fg: theme.chipFg,
    wrapMode: "none",
  })
  header.add(headerLine)
  header.add(chipLine)

  // ── Home (Pteron landing, denser) ───────────────────────
  const home = new BoxRenderable(renderer, {
    id: "home",
    flexGrow: 1,
    flexDirection: "column",
    backgroundColor: theme.bg,
    justifyContent: "center",
    alignItems: "center",
    paddingLeft: 2,
    paddingRight: 2,
  })
  const bird = new TextRenderable(renderer, {
    id: "bird",
    content: HOME_BIRD,
    fg: theme.accent,
    wrapMode: "none",
  })
  const brand = new TextRenderable(renderer, {
    id: "brand",
    content: "tero",
    fg: theme.brand,
    wrapMode: "none",
  })
  const tagline = new TextRenderable(renderer, {
    id: "tagline",
    content: "tus fuentes, tu criterio",
    fg: theme.homeMuted,
    wrapMode: "word",
  })
  const rumboRow = new TextRenderable(renderer, {
    id: "rumbos",
    content: "",
    fg: theme.text,
    wrapMode: "word",
  })
  const rumboHints = new TextRenderable(renderer, {
    id: "rumbo-hints",
    content: "",
    fg: theme.faint,
    wrapMode: "word",
  })
  const homeHint = new TextRenderable(renderer, {
    id: "home-hint",
    content: "1–4 rumbo · o escribe abajo",
    fg: theme.faint,
    wrapMode: "word",
  })
  const recentText = new TextRenderable(renderer, {
    id: "recent",
    content: "",
    fg: theme.faint,
    wrapMode: "word",
  })
  home.add(bird)
  home.add(brand)
  home.add(tagline)
  home.add(
    new TextRenderable(renderer, {
      content: "",
      height: 1,
      fg: theme.bg,
    }),
  )
  home.add(rumboRow)
  home.add(rumboHints)
  home.add(homeHint)
  home.add(recentText)

  // ── Workspace body ─────────────────────────────────────
  const body = new BoxRenderable(renderer, {
    id: "body",
    flexGrow: 1,
    flexDirection: "row",
    gap: 0,
  })

  const left = panel(renderer, "sesión", 26)
  const sessionScroll = scroll(renderer, "session-scroll", undefined, "top")
  const sessionText = new TextRenderable(renderer, {
    id: "session-text",
    content: "",
    fg: theme.text,
    wrapMode: "word",
  })
  sessionScroll.add(sessionText)
  const activityText = new TextRenderable(renderer, {
    id: "activity-text",
    content: "",
    fg: theme.muted,
    wrapMode: "word",
  })
  left.add(sessionScroll)
  left.add(
    new TextRenderable(renderer, {
      content: "actividad",
      fg: theme.faint,
    }),
  )
  const activityScroll = scroll(renderer, "activity-scroll", 9)
  activityScroll.add(activityText)
  left.add(activityScroll)

  const center = panel(renderer, "propuesta", undefined, true)
  const proposalScroll = scroll(renderer, "proposal-scroll", undefined, "top")
  const proposalMd = new MarkdownRenderable(renderer, {
    id: "proposal-md",
    content: "",
    syntaxStyle: syntax,
    conceal: true,
    fg: theme.text,
    bg: theme.panel,
    width: "100%",
    flexGrow: 1,
  })
  const proposalText = new TextRenderable(renderer, {
    id: "proposal-text",
    content: "",
    fg: theme.text,
    wrapMode: "word",
    width: "100%",
  })
  proposalScroll.add(proposalMd)
  proposalScroll.add(proposalText)
  center.add(proposalScroll)

  const right = panel(renderer, "evidencia", 34)
  const evidenceScroll = scroll(renderer, "evidence-scroll", undefined, "top")
  const evidenceText = new TextRenderable(renderer, {
    id: "evidence-text",
    content: "",
    fg: theme.text,
    wrapMode: "word",
  })
  evidenceScroll.add(evidenceText)
  const warnText = new TextRenderable(renderer, {
    id: "warn-text",
    content: "",
    fg: theme.warn,
    wrapMode: "word",
  })
  right.add(evidenceScroll)
  right.add(
    new TextRenderable(renderer, {
      content: "avisos (no bloquean)",
      fg: theme.faint,
    }),
  )
  const warnScroll = scroll(renderer, "warn-scroll", 4)
  warnScroll.add(warnText)
  right.add(warnScroll)

  // Prefer evidence viewport over avisos when the column is short.
  evidenceScroll.flexGrow = 1
  evidenceScroll.minHeight = 6

  body.add(left)
  body.add(center)
  body.add(right)

  // ── Plan card (deep, scrollable) ───────────────────────
  const planBar = new BoxRenderable(renderer, {
    id: "plan-bar",
    height: 14,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.accent,
    backgroundColor: theme.overlay,
    paddingLeft: 1,
    paddingRight: 1,
    title: " plan ",
    titleColor: theme.accent,
  })
  const planScroll = scroll(renderer, "plan-scroll", 12, "top")
  const planText = new TextRenderable(renderer, {
    id: "plan-text",
    content: "",
    fg: theme.text,
    wrapMode: "word",
  })
  planScroll.add(planText)
  planBar.add(planScroll)
  planBar.visible = false

  // ── Clarification card ─────────────────────────────────
  const clarifyBar = new BoxRenderable(renderer, {
    id: "clarify-bar",
    height: 8,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.suggested,
    backgroundColor: theme.overlay,
    paddingLeft: 1,
    paddingRight: 1,
    title: " clarificación ",
    titleColor: theme.suggested,
  })
  const clarifyText = new TextRenderable(renderer, {
    id: "clarify-text",
    content: "",
    fg: theme.text,
    wrapMode: "word",
  })
  clarifyBar.add(clarifyText)
  clarifyBar.visible = false

  // ── Gate strip (dense) ─────────────────────────────────
  const gateBar = new BoxRenderable(renderer, {
    id: "gate-bar",
    height: 3,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.ok,
    backgroundColor: theme.overlay,
    paddingLeft: 1,
    title: " puerta ",
    titleColor: theme.ok,
  })
  const gateText = new TextRenderable(renderer, {
    id: "gate-text",
    content: "",
    fg: theme.text,
    wrapMode: "none",
  })
  gateBar.add(gateText)
  gateBar.visible = false

  // ── Error panel ────────────────────────────────────────
  const errorBar = new BoxRenderable(renderer, {
    id: "error-bar",
    height: 4,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.err,
    backgroundColor: theme.overlay,
    paddingLeft: 1,
    title: " error ",
    titleColor: theme.err,
  })
  const errorText = new TextRenderable(renderer, {
    id: "error-text",
    content: "",
    fg: theme.err,
    wrapMode: "word",
  })
  errorBar.add(errorText)
  errorBar.visible = false

  // ── Help (scrollable / phase-aware) ────────────────────
  const helpBox = new BoxRenderable(renderer, {
    id: "help",
    height: 14,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.accent,
    backgroundColor: theme.overlay,
    paddingLeft: 1,
    title: " ayuda ",
    titleColor: theme.accent,
  })
  const helpScroll = scroll(renderer, "help-scroll", 12, "top")
  const helpText = new TextRenderable(renderer, {
    id: "help-text",
    content: "",
    fg: theme.text,
    wrapMode: "word",
  })
  helpScroll.add(helpText)
  helpBox.add(helpScroll)
  helpBox.visible = false

  // ── Prompt ─────────────────────────────────────────────
  const promptRow = new BoxRenderable(renderer, {
    id: "prompt-row",
    height: 3,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.borderFocus,
    backgroundColor: theme.inputBg,
    paddingLeft: 1,
    title: " encargo ",
    titleColor: theme.muted,
  })
  const input = new InputRenderable(renderer, {
    id: "prompt",
    width: "100%",
    placeholder: "Pregunta, explora o crea con tero…",
    backgroundColor: theme.inputBg,
    focusedBackgroundColor: theme.inputBg,
    textColor: theme.text,
    cursorColor: theme.cursor,
    placeholderColor: theme.faint,
    maxLength: 8000,
  })
  input.on(InputRenderableEvents.ENTER, (value: string) => {
    onSubmit(value)
    input.value = ""
  })
  promptRow.add(input)

  const footer = new TextRenderable(renderer, {
    id: "footer",
    content: "",
    fg: theme.muted,
    wrapMode: "none",
    height: 1,
  })

  root.add(header)
  root.add(home)
  root.add(body)
  root.add(planBar)
  root.add(clarifyBar)
  root.add(errorBar)
  root.add(gateBar)
  root.add(helpBox)
  root.add(promptRow)
  root.add(footer)
  renderer.root.add(root)
  input.focus()

  const sync = (state: AppState) => {
    const phase = PHASE_LABEL[state.phase] ?? state.phase
    const sources = state.sourceCount ? ` · ${state.sourceCount} fuentes` : ""
    const dirty = state.changedCount ? ` · ${state.changedCount}≠` : ""
    const think = state.thinking
      ? ` · ${spinnerGlyph(state.spinnerFrame)} ${state.thinkingLabel || phase}`
      : ""
    if (state.screen === "home" && !state.started) {
      headerLine.content =
        state.mode === "offline" ? `offline · ${phase}${sources}` : `${phase}${sources}`
    } else if (state.mode === "offline") {
      headerLine.content = `offline · ${phase}${sources}${dirty}${think}`
    } else {
      headerLine.content = `${shortModel(state.model)} · ${phase}${sources}${dirty}${think}`
    }
    if (showChips(state)) {
      chipLine.content = chips(state.encargo)
        .map((c) => `[ ${clipChip(c)} ]`)
        .join("  ")
    } else {
      chipLine.content = state.screen === "home" ? "" : "[ sin encargo — 1–4 o escribe ]"
    }
    header.bottomTitle = state.carpeta ? ` ${shortPath(state.carpeta)} ` : ""
    header.height = showChips(state) || state.screen !== "home" ? 4 : 3

    const isHome = state.screen === "home" && !state.thinking && !state.plan && !state.proposal
    const awaitingPlan =
      state.phase === "esperando_plan" ||
      state.phase === "esperando_clarificacion" ||
      state.phase === "proponiendo_plan"
    // Hide empty propuesta/evidencia chrome during plan/clarify — plan card + strip dominate.
    const planFocus = awaitingPlan && !state.proposal
    const gateFocus =
      state.phase === "esperando_criterio" ||
      state.phase === "listo" ||
      (state.phase === "escribiendo" && Boolean(state.proposal))
    home.visible = isHome
    body.visible = !isHome && !planFocus
    // Belt-and-suspenders: collapse child panels too (visible=false alone can leave flex gap).
    left.visible = !isHome && !planFocus && !state.compact && !gateFocus
    center.visible = !isHome && !planFocus
    right.visible = !isHome && !planFocus

    bird.visible = !state.compact
    rumboRow.content = RUMBOS.map((r) => `[${r.key}] ${r.label}`).join("   ")
    rumboHints.content = state.compact ? "" : RUMBOS.map((r) => r.hint).join(" · ")
    rumboHints.visible = !state.compact
    homeHint.visible = !state.compact
    if (state.recentSessions.length) {
      recentText.content =
        "\nrecientes\n" +
        state.recentSessions
          .slice(0, state.compact ? 2 : 3)
          .map((s) => `  · ${s.kind} · ${clipChip(s.label, 36)}`)
          .join("\n")
    } else {
      recentText.content = ""
    }

    // Compact / gate: evidence column width.
    if (!planFocus) {
      right.width = state.compact ? 28 : gateFocus ? 36 : 34
    }

    left.borderColor = state.focusPanel === "session" ? theme.borderFocus : theme.border
    center.borderColor = state.focusPanel === "proposal" ? theme.borderFocus : theme.border
    right.borderColor = state.focusPanel === "evidence" ? theme.borderFocus : theme.border
    left.title = state.focusPanel === "session" ? " ▸ sesión " : " sesión "
    center.title = state.focusPanel === "proposal" ? " ▸ propuesta " : " propuesta "
    right.title = state.focusPanel === "evidence" ? " ▸ evidencia " : " evidencia "

    sessionText.content = renderSession(state)
    activityText.content = renderActivity(state)
    const proposalBody = state.proposal
      ? `# ${state.proposalTitle || "propuesta"}\n\n${state.proposal}`
      : emptyProposal(state)
    // Text path is reliable in OpenTUI frames; Markdown was painting blank.
    proposalMd.visible = false
    proposalText.visible = true
    proposalText.content = proposalBody
    evidenceText.content = renderEvidence(state)
    warnText.content = renderWarnings(state)

    const showPlan =
      Boolean(state.plan) &&
      (state.planPinned ||
        state.phase === "esperando_plan" ||
        state.phase === "esperando_clarificacion" ||
        state.phase === "escribiendo" ||
        state.phase === "esperando_criterio")
    if (showPlan && state.plan) {
      planBar.visible = true
      const detail = planShowsDetail(state)
      if (planFocus) {
        planBar.height = state.compact ? 12 : state.phase === "esperando_clarificacion" ? 14 : 16
        planScroll.height = planBar.height - 2
        planBar.title = " plan "
      } else if (gateFocus) {
        planBar.height = detail ? (state.compact ? 8 : 10) : state.compact ? 4 : 5
        planScroll.height = planBar.height - 2
        planBar.title = detail ? " plan " : " plan · p detalle "
      } else {
        planBar.height = state.compact ? 8 : 11
        planScroll.height = planBar.height - 2
        planBar.title = " plan "
      }
      planText.content = renderPlanCard(state, detail)
    } else {
      planBar.visible = false
    }

    if (state.phase === "esperando_clarificacion" && state.question) {
      clarifyBar.visible = true
      clarifyBar.height = state.compact ? 7 : 8
      clarifyText.content = renderQuestion(state)
    } else {
      clarifyBar.visible = false
    }

    const strip = gateStrip(state)
    gateBar.visible = Boolean(strip)
    gateText.content = strip
    if (state.phase === "esperando_criterio") {
      gateBar.borderColor = theme.ok
      gateBar.title = " puerta "
      gateBar.titleColor = theme.ok
    } else if (state.phase === "esperando_plan" || state.phase === "esperando_clarificacion") {
      gateBar.borderColor = theme.accent
      gateBar.title = state.phase === "esperando_clarificacion" ? " clarificación " : " plan "
      gateBar.titleColor = theme.accent
    } else if (state.phase === "error") {
      gateBar.borderColor = theme.err
      gateBar.title = " error "
      gateBar.titleColor = theme.err
    }

    errorBar.visible = state.phase === "error" && Boolean(state.lastError)
    errorText.content = state.retryable
      ? `${state.lastError}\n→ r o /retry para reintentar · /home para volver`
      : state.lastError

    helpBox.visible = state.help
    if (state.help) helpText.content = helpFor(state)

    {
      const foot = footerFor(state)
      footer.content = foot ? ` ${state.statusLine}     ${foot}` : ` ${state.statusLine}`
    }
    promptRow.title =
      state.uiMode === "critique"
        ? " crítica docente "
        : state.uiMode === "assumption"
          ? " supuesto "
          : state.uiMode === "clarify"
            ? " responde "
            : state.screen === "home"
              ? " pregunta "
              : " encargo "
    promptRow.borderColor = gateColor(state)
    input.placeholder = placeholderFor(state)

    if (
      state.phase === "esperando_criterio" ||
      state.phase === "esperando_plan" ||
      state.phase === "esperando_clarificacion"
    ) {
      if (state.uiMode === "critique" || state.uiMode === "assumption" || state.uiMode === "clarify") {
        input.focus()
      } else if (state.phase === "esperando_clarificacion") {
        input.focus()
      } else {
        input.blur()
      }
    } else if (!state.help) {
      input.focus()
    }
  }

  return {
    input,
    sync,
    setPlaceholder: (text) => {
      input.placeholder = text
    },
    scrollHelp: (delta: number) => {
      try {
        helpScroll.scrollBy(delta)
      } catch {
        /* ignore if not scrollable yet */
      }
    },
  }
}

function panel(renderer: CliRenderer, title: string, width?: number, grow = false) {
  return new BoxRenderable(renderer, {
    id: `panel-${title}`,
    width,
    flexGrow: grow ? 1 : 0,
    flexShrink: grow ? 1 : 0,
    flexDirection: "column",
    backgroundColor: theme.panel,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.border,
    title: ` ${title} `,
    titleColor: theme.muted,
    paddingLeft: 1,
    paddingRight: 1,
    marginRight: 0,
  })
}

function scroll(
  renderer: CliRenderer,
  id: string,
  height?: number,
  stickyStart: "top" | "bottom" = "bottom",
) {
  return new ScrollBoxRenderable(renderer, {
    id,
    flexGrow: height ? 0 : 1,
    height,
    stickyScroll: true,
    stickyStart,
    viewportCulling: true,
    scrollX: false,
    backgroundColor: theme.panel,
    border: false,
  })
}

function renderSession(state: AppState): string {
  if (!state.turns.length) {
    return "Sin turnos aún.\n\nHistorial:\nrumbo → plan → borrador → criterio."
  }
  return state.turns
    .map((turn, i) => {
      const mark = turn.path ? "✓" : "·"
      const title = turn.titulo || turn.prompt.slice(0, 42)
      return `${mark} ${i + 1}. ${title}\n   ${turn.phase}${turn.path ? `\n   ${shortPath(turn.path)}` : ""}`
    })
    .join("\n\n")
}

function renderActivity(state: AppState): string {
  if (state.thinking && !state.activities.length) {
    return `${spinnerGlyph(state.spinnerFrame)} ${state.thinkingLabel || "trabajando…"}`
  }
  if (!state.activities.length) return "en espera"
  const rows = state.activities.slice(-8).map((row) => {
    const name = TOOL_LABEL[row.tool] ?? row.tool
    const icon = row.state === "end" ? "✓" : row.state === "start" ? "›" : "·"
    const detail = row.detail ? `  ${row.detail}` : ""
    return `${icon} ${name}${detail}`
  })
  if (state.thinking) {
    rows.push(`${spinnerGlyph(state.spinnerFrame)} ${state.thinkingLabel || "…"}`)
  }
  return rows.join("\n")
}

function emptyProposal(state: AppState): string {
  if (state.thinking) {
    return [
      `# ${spinnerGlyph(state.spinnerFrame)} trabajando`,
      "",
      state.thinkingLabel || PHASE_LABEL[state.phase],
    ].join("\n")
  }
  return [
    "# El agente prepara. Tú decides.",
    "",
    state.plan ? "Revisa el plan. `a` aprueba." : "Elige un rumbo o escribe el encargo.",
    state.lastError ? `\n> ${state.lastError}` : "",
  ].join("\n")
}

function renderPlanCard(state: AppState, detail = true): string {
  const plan = state.plan!
  const lines: string[] = []
  lines.push(shortPlanTitle(plan, state))
  if (detail && plan.meta) lines.push(clipChip(plan.meta, 72))
  lines.push("")
  lines.push(plan.objetivo)
  if (!detail) {
    const bits = [
      plan.decisiones?.curso || state.encargo.curso,
      plan.oa || state.encargo.oa,
      plan.duracion || state.encargo.duracion,
    ].filter(Boolean)
    if (bits.length) lines.push(bits.join(" · "))
    lines.push(plan.supuestos?.length ? `supuestos ${plan.supuestos.length} · p detalle` : "p detalle")
    return lines.join("\n")
  }
  lines.push("")
  if (plan.resultado_previsto?.length) {
    lines.push("RESULTADO PREVISTO")
    for (const item of plan.resultado_previsto) lines.push(`  · ${item}`)
    lines.push("")
  }
  const chipSet = new Set(chips(state.encargo).map((c) => c.toLowerCase()))
  const d = plan.decisiones || {}
  const rows: string[] = []
  const curso = d.curso || state.encargo.curso || ""
  const asig = d.asignatura || state.encargo.asignatura || ""
  const tema = d.tema || state.encargo.tema || ""
  if (curso && !chipSet.has(curso.toLowerCase())) rows.push(`  Curso        ${curso}`)
  if (asig && !chipSet.has(asig.toLowerCase())) rows.push(`  Asignatura   ${asig}`)
  if (tema && !chipSet.has(tema.toLowerCase())) rows.push(`  Tema         ${clipChip(tema, 48)}`)
  if (plan.oa && !chipSet.has(String(plan.oa).toLowerCase())) rows.push(`  OA           ${plan.oa}`)
  if (plan.duracion && !chipSet.has(String(plan.duracion).toLowerCase())) {
    rows.push(`  Duración     ${plan.duracion}`)
  }
  if (rows.length) {
    lines.push("DECISIONES CONFIRMADAS")
    lines.push(...rows)
    lines.push("")
  }
  if (plan.como_abordare?.length) {
    lines.push("CÓMO LO ABORDARÉ")
    plan.como_abordare.forEach((step, i) => {
      lines.push(`  ${i + 1}. ${step.titulo}${step.detalle ? ` — ${step.detalle}` : ""}`)
    })
    lines.push("")
  }
  if (plan.supuestos?.length) {
    lines.push("SUPUESTOS  (e)")
    for (const s of plan.supuestos) lines.push(`  · ${s.text}`)
  }
  if (plan.entregables && plan.entregables.length > 1) {
    lines.push("")
    lines.push("ENTREGABLES")
    for (const e of plan.entregables) lines.push(`  · ${e.label}`)
  }
  return lines.join("\n")
}

function renderQuestion(state: AppState): string {
  const q = state.question!
  const lines = [q.prompt, ""]
  q.options.forEach((opt, i) => {
    const n = opt.id || String(i + 1)
    const badge = opt.suggested ? "  ★ SUGERIDA" : ""
    lines.push(`  [${n}]${badge}  ${opt.label}`)
  })
  lines.push("")
  lines.push("Responde con tus palabras · o 1/2/3")
  return lines.join("\n")
}

function renderEvidence(state: AppState): string {
  if (!state.evidence.length) {
    return "Citas al redactar.\n[ ] recorre · ✓ archivo · ? parafraseo"
  }
  const total = state.evidence.length
  return state.evidence
    .map((item, i) => {
      const selected = i === state.evidenceIndex
      const trust = item.verified ? "✓" : "?"
      const trustLabel = item.verified ? "en archivo" : "parafraseo"
      const mark = selected ? "▸" : " "
      const path = shortPath(item.path)
      const sec = (item.seccion || "").replace(/\s+/g, " ").trim()
      if (selected) {
        const lines = [`${mark} ${i + 1}/${total}  ${trust} ${trustLabel}`, `  ${path}`]
        if (sec) {
          // Wrap OA/sección on its own lines — never mid-word truncate on one row.
          for (const row of wrapLines(sec, 28)) lines.push(`  ${row}`)
        }
        const snippet = (item.snippet || "").replace(/\s+/g, " ").trim().slice(0, 160)
        if (snippet) {
          for (const row of wrapLines(`“${snippet}”`, 28)) lines.push(`  ${row}`)
        }
        return lines.join("\n")
      }
      // Compact rows: path only; sección on next line if present (avoids mid-OA clip).
      if (sec) return `${mark} ${i + 1}/${total}  ${trust}  ${path}\n    ${clipChip(sec, 28)}`
      return `${mark} ${i + 1}/${total}  ${trust}  ${path}`
    })
    .join("\n\n")
}

function renderWarnings(state: AppState): string {
  if (!state.warnings.length) return "sin avisos"
  return state.warnings.map((item) => `! ${item.message}`).join("\n")
}

function placeholderFor(state: AppState): string {
  if (state.uiMode === "critique") return "Qué debe corregir el agente…"
  if (state.uiMode === "assumption") return "Nuevo texto del supuesto…"
  if (state.uiMode === "clarify" || state.phase === "esperando_clarificacion") {
    return "Responde con tus palabras…"
  }
  if (state.phase === "esperando_criterio") return "teclas arriba · o crítica con c"
  if (state.phase === "esperando_plan") return "teclas arriba · /objetivo /oa"
  if (state.phase === "error" && state.retryable) return "r reintenta · o otro encargo"
  if (state.screen === "home") return "Pregunta, explora o crea…"
  return "Describe el material…  Enter envía"
}

function gateColor(state: AppState): string {
  if (state.phase === "esperando_criterio") return theme.ok
  if (state.phase === "esperando_plan" || state.phase === "esperando_clarificacion") return theme.accent
  if (state.phase === "error") return theme.err
  return theme.borderFocus
}

function clipChip(text: string, max = 22): string {
  const t = (text || "").trim()
  if (t.length <= max) return t
  return `${t.slice(0, Math.max(1, max - 1))}…`
}

function wrapLines(text: string, width: number): string[] {
  const words = text.replace(/\s+/g, " ").trim().split(" ").filter(Boolean)
  const lines: string[] = []
  let row = ""
  for (const w of words) {
    // Prefer breaking before a too-long token rather than mid-word clip.
    if (w.length > width) {
      if (row) {
        lines.push(row)
        row = ""
      }
      for (let i = 0; i < w.length; i += width) lines.push(w.slice(i, i + width))
      continue
    }
    const next = row ? `${row} ${w}` : w
    if (next.length > width && row) {
      lines.push(row)
      row = w
    } else {
      row = next
    }
  }
  if (row) lines.push(row)
  return lines
}

function wrapLine(text: string, width: number): string {
  return wrapLines(text, width).join("\n  ")
}

function shortPlanTitle(plan: NonNullable<AppState["plan"]>, state: AppState): string {
  const tipo = plan.tipo_label || plan.tipo || "plan"
  const tema = plan.decisiones?.tema || state.encargo.tema || ""
  if (tema) return clipChip(`${tipo} · ${tema}`, 64)
  const raw = (plan.titulo || "").replace(/^Plan de\s+/i, "").trim()
  if (raw) return clipChip(raw, 64)
  return String(tipo)
}
