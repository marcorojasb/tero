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
import { chips, footerFor, gateStrip, PHASE_LABEL, TOOL_LABEL, HELP_TEXT, type AppState } from "./state.ts"
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

export type Shell = {
  input: InputRenderable
  sync: (state: AppState) => void
  setPlaceholder: (text: string) => void
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
    titleColor: theme.accent,
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

  const body = new BoxRenderable(renderer, {
    id: "body",
    flexGrow: 1,
    flexDirection: "row",
    gap: 0,
  })

  const left = panel(renderer, "sesión", 28)
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
  const activityScroll = scroll(renderer, "activity-scroll", 8)
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

  const right = panel(renderer, "evidencia", 32)
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
  const warnScroll = scroll(renderer, "warn-scroll", 8)
  warnScroll.add(warnText)
  right.add(warnScroll)

  body.add(left)
  body.add(center)
  body.add(right)

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

  const planBar = new BoxRenderable(renderer, {
    id: "plan-bar",
    height: 4,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.accent,
    backgroundColor: theme.overlay,
    paddingLeft: 1,
    title: " plan ",
    titleColor: theme.accent,
  })
  const planText = new TextRenderable(renderer, {
    id: "plan-text",
    content: "",
    fg: theme.text,
    wrapMode: "word",
  })
  planBar.add(planText)

  const helpBox = new BoxRenderable(renderer, {
    id: "help",
    height: 16,
    border: true,
    borderStyle: "rounded",
    borderColor: theme.accent,
    backgroundColor: theme.overlay,
    paddingLeft: 1,
    title: " ayuda ",
    titleColor: theme.accent,
  })
  const helpText = new TextRenderable(renderer, {
    id: "help-text",
    content: HELP_TEXT,
    fg: theme.text,
    wrapMode: "word",
  })
  helpBox.add(helpText)
  helpBox.visible = false
  planBar.visible = false

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
    placeholder: "Describe el material…  Enter envía",
    backgroundColor: theme.inputBg,
    focusedBackgroundColor: theme.inputBg,
    textColor: theme.text,
    cursorColor: theme.cursor,
    placeholderColor: theme.faint,
    maxLength: 2000,
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
  root.add(body)
  root.add(planBar)
  root.add(gateBar)
  root.add(helpBox)
  root.add(promptRow)
  root.add(footer)
  renderer.root.add(root)
  input.focus()

  const sync = (state: AppState) => {
    const mode = state.mode === "offline" ? "offline" : "bedrock"
    const sources = state.sourceCount ? `  ·  ${state.sourceCount} fuentes` : ""
    const dirty = state.changedCount ? `  ·  ${state.changedCount} hash≠` : ""
    headerLine.content = `${mode}  ·  ${state.model}  ·  ${PHASE_LABEL[state.phase] ?? state.phase}${sources}${dirty}`
    const chip = chips(state.encargo)
    chipLine.content = chip.length ? chip.map((c) => `[ ${c} ]`).join("  ") : "[ sin encargo — /oa /tipo /curso ]"
    header.bottomTitle = state.carpeta ? ` ${shortPath(state.carpeta)} ` : ""
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
    const hasDraft = Boolean(state.proposal)
    proposalMd.visible = hasDraft
    proposalText.visible = !hasDraft
    if (hasDraft) proposalMd.content = proposalBody
    else proposalText.content = proposalBody
    evidenceText.content = renderEvidence(state)
    warnText.content = renderWarnings(state)

    const showPlan =
      Boolean(state.plan) &&
      (state.planPinned ||
        state.phase === "esperando_plan" ||
        state.phase === "escribiendo" ||
        state.phase === "esperando_criterio")
    if (showPlan && state.plan) {
      planBar.visible = true
      const notas = state.plan.notas ? `\n${state.plan.notas}` : ""
      planText.content = `objetivo  ${state.plan.objetivo}\n${state.plan.tipo_label ?? state.plan.tipo}  ·  ${state.plan.oa || "sin OA"}  ·  ${state.plan.duracion || "sin duración"}${notas}`
    } else {
      planBar.visible = false
    }
    const strip = gateStrip(state)
    gateBar.visible = Boolean(strip)
    gateText.content = strip
    if (state.phase === "esperando_criterio") {
      gateBar.borderColor = theme.ok
      gateBar.title = " puerta  s/n/b/c "
      gateBar.titleColor = theme.ok
    } else if (state.phase === "esperando_plan") {
      gateBar.borderColor = theme.accent
      gateBar.title = " plan "
      gateBar.titleColor = theme.accent
    }
    helpBox.visible = state.help

    footer.content = ` ${state.statusLine}     ${footerFor(state)}`
    promptRow.title = state.uiMode === "critique" ? " crítica docente " : " encargo "
    promptRow.borderColor = gateColor(state)
    input.placeholder =
      state.uiMode === "critique"
        ? "Qué debe corregir el agente…"
        : state.phase === "esperando_criterio"
          ? "s/n/b/c — o escribe otra crítica con c"
          : "Describe el material…  Enter envía"

    if (state.phase === "esperando_criterio" || state.phase === "esperando_plan") {
      if (state.uiMode === "critique") input.focus()
      else input.blur()
    } else if (!state.help) {
      input.focus()
    }
  }

  return { input, sync, setPlaceholder: (text) => { input.placeholder = text } }
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
    return "Sin turnos aún.\n\nEl historial vive aquí:\nplan → borrador → tu criterio."
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
  if (!state.activities.length) return "en espera"
  return state.activities
    .slice(-8)
    .map((row) => {
      const name = TOOL_LABEL[row.tool] ?? row.tool
      const icon = row.state === "end" ? "✓" : row.state === "start" ? "›" : "·"
      const detail = row.detail ? `  ${row.detail}` : ""
      return `${icon} ${name}${detail}`
    })
    .join("\n")
}

function emptyProposal(state: AppState): string {
  return [
    "# El agente prepara. Tú decides.",
    "",
    "1. Completa el encargo (chips arriba).",
    "2. Escribe qué material necesitas.",
    "3. Revisa el plan; luego la propuesta y la evidencia.",
    "4. `s` escribe en derivados/. `n` no toca nada.",
    "",
    state.lastError ? `> ${state.lastError}` : "_Sin propuesta en esta sesión._",
  ].join("\n")
}

function renderEvidence(state: AppState): string {
  if (!state.evidence.length) {
    return "Las citas aparecen al redactar.\npath + fragmento + sección.\n\n[ ] recorre  ·  e enfoca  ·  ✓ en el archivo  ·  ? parafraseo"
  }
  return state.evidence
    .map((item, i) => {
      const selected = i === state.evidenceIndex
      const snippet = item.snippet.replace(/\s+/g, " ").slice(0, selected ? 360 : 120)
      const sec = item.seccion ? ` · ${item.seccion}` : ""
      const mark = selected ? "▸" : " "
      const trust = item.verified ? "✓" : "?"
      if (selected) {
        return `${mark} ${i + 1}/${state.evidence.length}  ${trust}  ${item.path}${sec}\n     “${snippet}”`
      }
      return `${mark} ${i + 1}. ${trust}  ${item.path}${sec}`
    })
    .join("\n\n")
}

function renderWarnings(state: AppState): string {
  if (!state.warnings.length) return "sin avisos"
  return state.warnings.map((item) => `! ${item.message}`).join("\n")
}

function gateColor(state: AppState): string {
  if (state.phase === "esperando_criterio") return theme.ok
  if (state.phase === "esperando_plan") return theme.accent
  if (state.phase === "error") return theme.err
  return theme.borderFocus
}

function shortPath(path: string): string {
  const parts = path.split("/")
  return parts.length > 3 ? `…/${parts.slice(-3).join("/")}` : path
}
