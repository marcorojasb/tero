import {
  BoxRenderable,
  InputRenderable,
  InputRenderableEvents,
  ScrollBoxRenderable,
  TextRenderable,
  type CliRenderer,
} from "@opentui/core"
import {
  accionLabel,
  allWarnings,
  chips,
  decisionStrip,
  footerFor,
  helpFor,
  PHASE_LABEL,
  shortModel,
  shortPath,
  showChips,
  spinnerGlyph,
  TOOL_LABEL,
  type AppState,
} from "./state.ts"
import { theme } from "./theme.ts"

/** Vanellus chilensis de perfil — silueta de foto: cresta, pico, patas. */
export const HOME_BIRD = [
  "      ▄▄▄▄▄      ▄▄▄▄▄   ",
  "    ▄████████  ▀▀▀▀▀▀▀▀▀▀",
  "  ▀▀▀▀███████            ",
  "       ██████            ",
  "       ██████▄           ",
  "       ███████▄          ",
  "      ██████████▄        ",
  "      █████████████▄     ",
  "      ███████████████▄   ",
  "       ▀███████████████▄ ",
  "          ▀▀█████████████",
  "            ███  ▀▀██████",
  "            █ █      ▀▀██",
  "            ▀ ▀          ",
].join("\n")

export type Shell = {
  input: InputRenderable
  sync: (state: AppState) => void
  setPlaceholder: (text: string) => void
  scrollHelp: (delta: number) => void
  scrollThread: (delta: number) => void
}

export function mountShell(renderer: CliRenderer, onSubmit: (value: string) => void): Shell {
  renderer.setBackgroundColor(theme.bg)

  const root = new BoxRenderable(renderer, {
    id: "root",
    flexGrow: 1,
    flexDirection: "column",
    backgroundColor: theme.bg,
    padding: 0,
    overflow: "hidden",
    border: true,
    borderStyle: "rounded",
    borderColor: theme.border,
    title: " tero ",
    titleColor: theme.brand,
    bottomTitle: "",
  })

  // ── Header (status strip inside the window, not its own box) ──
  const header = new BoxRenderable(renderer, {
    id: "header",
    height: 1,
    flexDirection: "column",
    backgroundColor: theme.panel,
    border: false,
    paddingLeft: 1,
    paddingRight: 1,
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

  // ── Home (bird + one input line; no rumbos) ────────────
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
  const homeHint = new TextRenderable(renderer, {
    id: "home-hint",
    content: "Pregunta, explora o crea…",
    fg: theme.text,
    wrapMode: "word",
  })
  const homeSubHint = new TextRenderable(renderer, {
    id: "home-subhint",
    content: "El agente responde, crea o adapta · tú apruebas",
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
  home.add(homeHint)
  home.add(homeSubHint)
  home.add(recentText)

  // ── Body: hilo + propuesta + evidencia ─────────────────
  const body = new BoxRenderable(renderer, {
    id: "body",
    flexGrow: 1,
    flexDirection: "row",
    gap: 0,
  })

  const left = panel(renderer, "conversación")
  left.flexGrow = 1
  left.flexShrink = 1
  const threadScroll = scroll(renderer, "thread-scroll", undefined, "bottom")
  const threadText = new TextRenderable(renderer, {
    id: "thread-text",
    content: "",
    fg: theme.text,
    wrapMode: "word",
  })
  threadScroll.add(threadText)
  const activityScroll = scroll(renderer, "activity-scroll", 9)
  const activityText = new TextRenderable(renderer, {
    id: "activity-text",
    content: "",
    fg: theme.muted,
    wrapMode: "word",
  })
  activityScroll.add(activityText)
  left.add(threadScroll)
  left.add(
    new TextRenderable(renderer, {
      content: "actividad",
      fg: theme.faint,
    }),
  )
  left.add(activityScroll)

  const center = panel(renderer, "propuesta", undefined, true)
  const cardHeadScroll = scroll(renderer, "card-head-scroll", 11, "top")
  cardHeadScroll.flexShrink = 0
  const cardHeadText = new TextRenderable(renderer, {
    id: "card-head-text",
    content: "",
    fg: theme.text,
    wrapMode: "word",
  })
  cardHeadScroll.add(cardHeadText)
  const previewLabel = new TextRenderable(renderer, {
    id: "preview-label",
    content: "vista previa · markdown",
    fg: theme.faint,
    wrapMode: "none",
    height: 1,
    flexShrink: 0,
  })
  const previewScroll = scroll(renderer, "preview-scroll", undefined, "top")
  const previewText = new TextRenderable(renderer, {
    id: "preview-text",
    content: "",
    fg: theme.text,
    wrapMode: "word",
  })
  previewScroll.add(previewText)
  center.add(cardHeadScroll)
  center.add(previewLabel)
  center.add(previewScroll)

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
  const warnScroll = scroll(renderer, "warn-scroll", 4, "top")
  warnScroll.add(warnText)
  right.add(warnScroll)

  // Prefer the evidence viewport over avisos when the column is short.
  evidenceScroll.flexGrow = 1
  evidenceScroll.minHeight = 6

  body.add(left)
  body.add(center)
  body.add(right)

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

  // ── Decision strip (y aprueba / n descarta) ────────────
  const decisionBar = new BoxRenderable(renderer, {
    id: "decision-bar",
    height: 3,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.ok,
    backgroundColor: theme.overlay,
    paddingLeft: 1,
    title: " aprobación ",
    titleColor: theme.ok,
  })
  const decisionText = new TextRenderable(renderer, {
    id: "decision-text",
    content: "",
    fg: theme.text,
    wrapMode: "none",
  })
  decisionBar.add(decisionText)
  decisionBar.visible = false

  // ── Help (scrollable / contextual) ─────────────────────
  const helpBox = new BoxRenderable(renderer, {
    id: "help",
    height: 18,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.accent,
    backgroundColor: theme.overlay,
    paddingLeft: 1,
    title: " ayuda ",
    titleColor: theme.accent,
  })
  const helpScroll = scroll(renderer, "help-scroll", 16, "top")
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
    title: " pregunta ",
    titleColor: theme.muted,
  })
  const input = new InputRenderable(renderer, {
    id: "prompt",
    width: "100%",
    placeholder: "Pregunta, explora o crea…",
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
  root.add(errorBar)
  root.add(decisionBar)
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
    if (!state.started || state.screen === "home") {
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
      chipLine.content = state.screen === "home" ? "" : "[ sin contexto — /curso /asignatura /oa ]"
    }
    root.bottomTitle = state.carpeta ? ` ${shortPath(state.carpeta)} ` : ""
    const chipsVisible = showChips(state) || state.screen !== "home"
    chipLine.visible = chipsVisible
    header.height = chipsVisible ? 2 : 1

    const hasCard = Boolean(state.card)
    const isHome = state.screen === "home" && !state.messages.length && !hasCard
    home.visible = isHome
    body.visible = !isHome
    left.visible = !isHome && (!state.compact || !hasCard)
    center.visible = !isHome && hasCard
    right.visible = !isHome && !state.compact && (hasCard || state.warnings.length > 0)

    bird.visible = !state.compact
    homeSubHint.visible = !state.compact
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

    if (hasCard) {
      center.width = state.compact ? 46 : "auto"
      center.flexGrow = state.compact ? 0 : 1.15
      center.minWidth = state.compact ? 0 : 40
      right.width = 34
    }

    left.borderColor = state.focusPanel === "hilo" ? theme.borderFocus : theme.border
    center.borderColor = state.focusPanel === "propuesta" ? theme.borderFocus : theme.border
    right.borderColor = state.focusPanel === "evidencia" ? theme.borderFocus : theme.border
    left.title = state.focusPanel === "hilo" ? " ▸ conversación " : " conversación "
    center.title = state.focusPanel === "propuesta" ? " ▸ propuesta " : " propuesta "
    right.title = state.focusPanel === "evidencia" ? " ▸ evidencia " : " evidencia "

    threadText.content = renderThread(state)
    activityText.content = renderActivity(state)

    cardHeadScroll.height = state.compact ? 10 : 16
    cardHeadText.content = state.card ? renderCardHead(state) : ""
    previewText.content = state.card?.vista_previa ?? ""
    previewLabel.visible = hasCard
    previewScroll.visible = hasCard

    evidenceText.content = renderEvidence(state)
    warnText.content = renderWarnings(state)

    const strip = state.help ? "" : decisionStrip(state)
    decisionBar.visible = Boolean(strip)
    decisionText.content = strip
    if (state.cardStatus === "pendiente") {
      decisionBar.borderColor = theme.ok
      decisionBar.title = " aprobación "
      decisionBar.titleColor = theme.ok
    } else if (state.cardStatus === "escrito") {
      decisionBar.borderColor = theme.ok
      decisionBar.title = " escrito "
      decisionBar.titleColor = theme.ok
    } else if (state.cardStatus === "descartado") {
      decisionBar.borderColor = theme.warn
      decisionBar.title = " descartado "
      decisionBar.titleColor = theme.warn
    } else if (state.cardStatus === "aprobado") {
      decisionBar.borderColor = theme.accent
      decisionBar.title = " aprobado "
      decisionBar.titleColor = theme.accent
    } else if (state.phase === "error") {
      decisionBar.borderColor = theme.err
      decisionBar.title = " error "
      decisionBar.titleColor = theme.err
    }

    errorBar.visible = state.phase === "error" && Boolean(state.lastError)
    errorText.content = state.retryable
      ? `${state.lastError}\n→ r o /retry para reintentar`
      : state.lastError

    helpBox.visible = state.help
    if (state.help) helpText.content = helpFor(state)

    {
      const foot = footerFor(state)
      footer.content = foot ? ` ${state.statusLine}     ${foot}` : ` ${state.statusLine}`
    }
    const awaiting = state.cardStatus === "pendiente" && hasCard
    promptRow.title = state.help
      ? " ayuda "
      : awaiting
        ? " tu decisión "
        : state.screen === "home"
          ? " pregunta "
          : " mensaje "
    promptRow.borderColor = awaiting
      ? theme.ok
      : state.phase === "error"
        ? theme.err
        : theme.borderFocus
    input.placeholder = placeholderFor(state)

    if (state.help) input.blur()
    else input.focus()
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
    scrollThread: (delta: number) => {
      try {
        threadScroll.scrollBy(delta)
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

/** Hilo: persona, agente y notas del host; el streaming se pinta al final. */
function renderThread(state: AppState): string {
  const rows: string[] = []
  for (const m of state.messages) {
    if (m.role === "persona") {
      rows.push(`tú  › ${indentBody(m.text)}`, "")
      continue
    }
    if (m.role === "host") {
      rows.push(`·  ${m.text}${m.path ? ` · ${m.path}` : ""}`, "")
      continue
    }
    rows.push(`tero › ${indentBody(m.text)}`, "")
  }
  if (state.streaming) {
    rows.push(`tero › ${indentBody(state.streaming)}▌`)
  } else if (state.thinking) {
    rows.push(`${spinnerGlyph(state.spinnerFrame)} ${state.thinkingLabel || "pensando…"}`)
  }
  if (!rows.length) {
    return "Escribe lo que necesitas.\nEl agente responde, crea o adapta; tú apruebas."
  }
  return rows.join("\n").trimEnd()
}

function indentBody(text: string): string {
  return text.replace(/\n/g, "\n      ")
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

/**
 * Tarjeta de propuesta: qué hará (acción, tipo, título, resumen), origen y
 * cambios si edita/adapta, apoyos NEE, y el resultado si ya se escribió.
 */
function renderCardHead(state: AppState): string {
  const card = state.card
  if (!card) return ""
  const lines: string[] = []
  const tipo = card.tipo_label || card.tipo || "material"
  lines.push(card.titulo ? `${accionLabel(card.accion)} · ${tipo} — ${card.titulo}` : `${accionLabel(card.accion)} · ${tipo}`)
  if (card.resumen) lines.push(card.resumen)
  if (card.accion !== "crear" && card.origen) {
    lines.push(`origen  ${card.origen}`)
  }
  if (card.cambios.length) {
    lines.push("cambios")
    for (const change of card.cambios.slice(0, 6)) lines.push(`  · ${change}`)
  }
  if (card.notas_nee.length) {
    lines.push("apoyos y criterios NEE")
    for (const nota of card.notas_nee.slice(0, 6)) lines.push(`  · ${nota}`)
  }
  if (state.cardStatus === "escrito" && state.writtenPath) {
    lines.push(`escrito · ${accionLabel(state.writtenAccion)}`, state.writtenPath)
  } else if (state.cardStatus === "descartado") {
    lines.push("descartado · no se escribió nada")
  }
  return lines.join("\n")
}

function renderEvidence(state: AppState): string {
  const rows = state.card?.evidencias ?? []
  if (!rows.length) {
    return "Las citas aparecen cuando el agente propone un archivo.\n✓ en el archivo · ? parafraseo"
  }
  const total = rows.length
  return rows
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
  const rows = allWarnings(state)
  if (!rows.length) return "sin avisos"
  return rows.map((item) => `! ${item.message}`).join("\n")
}

function placeholderFor(state: AppState): string {
  if (state.cardStatus === "pendiente" && state.card) {
    return "y aprueba · n descarta · o escribe tu decisión…"
  }
  if (state.screen === "home") return "Pregunta, explora o crea…"
  if (state.phase === "error" && state.retryable) return "r reintenta · o sigue conversando"
  return "Escribe tu respuesta…  Enter envía"
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
