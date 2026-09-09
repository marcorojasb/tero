import type {
  Activity,
  ClientMessage,
  Encargo,
  Evidence,
  HostEvent,
  Phase,
  Plan,
  TurnSummary,
  WarningItem,
} from "./protocol.ts"

export type UiMode = "prompt" | "critique"
export type FocusPanel = "session" | "proposal" | "evidence"
export const FOCUS_PANELS: FocusPanel[] = ["session", "proposal", "evidence"]

export type AppState = {
  ready: boolean
  mode: string
  model: string
  carpeta: string
  phase: Phase
  encargo: Encargo
  turns: TurnSummary[]
  activities: Activity[]
  proposal: string
  proposalTitle: string
  evidence: Evidence[]
  warnings: WarningItem[]
  plan: Plan | null
  help: boolean
  statusLine: string
  lastError: string
  uiMode: UiMode
  lastPath: string
  evidenceIndex: number
  focusPanel: FocusPanel
  sourceCount: number
  changedCount: number
  planPinned: boolean
}

export function initialState(encargo: Encargo): AppState {
  return {
    ready: false,
    mode: "…",
    model: "…",
    carpeta: "",
    phase: "idle",
    encargo,
    turns: [],
    activities: [],
    proposal: "",
    proposalTitle: "",
    evidence: [],
    warnings: [],
    plan: null,
    help: false,
    statusLine: "Escribe un encargo. El agente prepara; tú decides.",
    lastError: "",
    uiMode: "prompt",
    lastPath: "",
    evidenceIndex: 0,
    focusPanel: "proposal",
    sourceCount: 0,
    changedCount: 0,
    planPinned: false,
  }
}

export const PHASE_LABEL: Record<Phase, string> = {
  idle: "listo",
  leyendo: "leyendo",
  proponiendo_plan: "proponiendo plan",
  esperando_plan: "esperando criterio · plan",
  escribiendo: "escribiendo",
  esperando_criterio: "esperando criterio",
  exportando: "exportando",
  listo: "listo",
  error: "error",
}

export const TOOL_LABEL: Record<string, string> = {
  list_sources: "fuentes",
  search_sources: "buscar",
  read_source: "leer",
  propose_plan: "plan",
  plan: "plan",
  cite_evidence: "cita",
  draft_artifact: "borrador",
  draft: "borrador",
}

export function applyHostEvent(state: AppState, event: HostEvent): AppState {
  const next = { ...state, activities: [...state.activities], turns: [...state.turns] }
  switch (event.type) {
    case "ready":
      next.ready = true
      next.mode = String(event.mode ?? next.mode)
      next.model = String(event.model ?? next.model)
      next.carpeta = String(event.carpeta ?? next.carpeta)
      next.statusLine = `listo · ${next.mode} · ${next.model}`
      break
    case "hello_ok":
      next.carpeta = String(event.carpeta ?? next.carpeta)
      if (event.encargo && typeof event.encargo === "object") {
        next.encargo = { ...next.encargo, ...(event.encargo as Encargo) }
      }
      if (typeof event.fuentes === "number") next.sourceCount = event.fuentes
      if (typeof event.changed === "number") next.changedCount = event.changed
      next.statusLine = next.sourceCount
        ? `carpeta · ${next.sourceCount} fuente${next.sourceCount === 1 ? "" : "s"}`
        : next.statusLine
      break
    case "status":
      next.phase = (event.phase as Phase) || next.phase
      next.statusLine = PHASE_LABEL[next.phase] ?? next.phase
      if (next.phase === "leyendo" || next.phase === "proponiendo_plan" || next.phase === "escribiendo") {
        next.lastError = ""
      }
      break
    case "activity": {
      const tool = String(event.tool ?? "")
      const item: Activity = {
        tool,
        state: String(event.state ?? ""),
        detail: event.detail ? String(event.detail) : undefined,
      }
      const idx = next.activities.findIndex((row) => row.tool === tool && row.state !== "end")
      if (idx >= 0 && item.state === "end") next.activities[idx] = item
      else next.activities.push(item)
      if (next.activities.length > 24) next.activities = next.activities.slice(-24)
      if (tool === "list_sources" && item.state === "end" && item.detail) {
        const n = Number.parseInt(item.detail, 10)
        if (!Number.isNaN(n)) next.sourceCount = n
      }
      break
    }
    case "delta":
      if (typeof event.text === "string" && event.text && !next.proposal) {
        next.statusLine = "el modelo habla…"
      }
      break
    case "plan":
      next.plan = event.plan as Plan
      next.phase = "esperando_plan"
      next.statusLine = "Plan listo. a aprobar · x cancelar"
      break
    case "plan_approved":
      next.plan = (event.plan as Plan) ?? next.plan
      next.statusLine = "Plan aprobado. Redactando…"
      break
    case "plan_cancelled":
      next.phase = "idle"
      next.statusLine = "Plan cancelado."
      break
    case "proposal": {
      const artifact = event.artifact as {
        titulo?: string
        tipo_label?: string
        cuerpo_markdown?: string
        evidencias?: Evidence[]
        warnings?: WarningItem[]
      }
      next.proposalTitle = artifact?.titulo ?? ""
      next.proposal = artifact?.cuerpo_markdown ?? ""
      next.evidence = artifact?.evidencias ?? []
      next.warnings = artifact?.warnings ?? []
      next.evidenceIndex = 0
      next.phase = "esperando_criterio"
      next.statusLine = "s sí · n no · b borrador · c corregir"
      next.turns = next.turns.map((turn, i) =>
        i === next.turns.length - 1
          ? { ...turn, titulo: artifact?.titulo, tipo: artifact?.tipo_label, phase: "esperando_criterio" }
          : turn,
      )
      break
    }
    case "turn": {
      const turn = event.turn as { id?: string; prompt?: string; phase?: string }
      if (turn?.id) {
        next.turns.push({
          id: turn.id,
          prompt: turn.prompt ?? "",
          phase: turn.phase ?? next.phase,
        })
      }
      break
    }
    case "accepted":
      next.phase = "listo"
      next.lastPath = String(event.path ?? "")
      next.statusLine = `Aceptado → ${next.lastPath}`
      next.uiMode = "prompt"
      stampPath(next, String(event.path ?? ""))
      break
    case "draft_saved":
      next.phase = "listo"
      next.lastPath = String(event.path ?? "")
      next.statusLine = `Borrador → ${next.lastPath}`
      next.uiMode = "prompt"
      stampPath(next, String(event.path ?? ""))
      break
    case "discarded":
      next.phase = "idle"
      next.statusLine = "Descartado. Nada se escribió."
      next.uiMode = "prompt"
      break
    case "exported":
      next.statusLine = `Exportado → ${event.path}`
      break
    case "encargo":
      if (event.encargo && typeof event.encargo === "object") {
        next.encargo = { ...next.encargo, ...(event.encargo as Encargo) }
      }
      break
    case "error":
      next.lastError = String(event.message ?? "error")
      next.statusLine = next.lastError
      next.phase = "error"
      break
    default:
      break
  }
  return next
}

function stampPath(state: AppState, path: string) {
  if (!state.turns.length) return
  const last = state.turns[state.turns.length - 1]
  state.turns[state.turns.length - 1] = { ...last, path, phase: "listo" }
}

export type LocalAction =
  | { kind: "send"; message: ClientMessage; state: AppState }
  | { kind: "state"; state: AppState }
  | { kind: "quit" }
  | { kind: "none"; state: AppState }

export function handleCommand(state: AppState, raw: string): LocalAction {
  const text = raw.trim()
  if (!text) return { kind: "none", state }

  if (state.uiMode === "critique") {
    const next = { ...state, uiMode: "prompt" as const, statusLine: "Enviando corrección…" }
    return { kind: "send", message: { type: "gate", decision: "c", note: text }, state: next }
  }

  if (text === "/help" || text === "?") {
    return { kind: "state", state: { ...state, help: !state.help } }
  }
  if (text === "/q" || text === "/salir") {
    return { kind: "quit" }
  }
  if (text.startsWith("/oa ")) {
    const oa = text.slice(4).trim()
    const encargo = { ...state.encargo, oa }
    const plan = state.plan ? { ...state.plan, oa } : state.plan
    return {
      kind: "send",
      message: { type: "encargo.update", encargo },
      state: { ...state, encargo, plan, statusLine: `OA → ${oa}` },
    }
  }
  if (text.startsWith("/tipo ")) {
    const tipo = text.slice(6).trim()
    const encargo = { ...state.encargo, tipo }
    const plan = state.plan ? { ...state.plan, tipo } : state.plan
    return {
      kind: "send",
      message: { type: "encargo.update", encargo },
      state: { ...state, encargo, plan, statusLine: `tipo → ${tipo}` },
    }
  }
  if (text.startsWith("/curso ")) {
    const encargo = { ...state.encargo, curso: text.slice(7).trim() }
    return {
      kind: "send",
      message: { type: "encargo.update", encargo },
      state: { ...state, encargo, statusLine: `curso → ${encargo.curso}` },
    }
  }
  if (text.startsWith("/asignatura ")) {
    const encargo = { ...state.encargo, asignatura: text.slice(12).trim() }
    return {
      kind: "send",
      message: { type: "encargo.update", encargo },
      state: { ...state, encargo, statusLine: `asignatura → ${encargo.asignatura}` },
    }
  }
  if (text.startsWith("/duracion ") || text.startsWith("/duración ")) {
    const duracion = text.replace(/^\/duraci[oó]n\s+/, "").trim()
    const encargo = { ...state.encargo, duracion }
    const plan = state.plan ? { ...state.plan, duracion } : state.plan
    return {
      kind: "send",
      message: { type: "encargo.update", encargo },
      state: { ...state, encargo, plan, statusLine: `duración → ${duracion}` },
    }
  }
  if (text.startsWith("/objetivo ")) {
    if (!state.plan) return { kind: "none", state }
    const plan = { ...state.plan, objetivo: text.slice(10).trim() }
    return {
      kind: "state",
      state: { ...state, plan, statusLine: "plan · objetivo editado — a aprueba" },
    }
  }
  if (text === "/export" || text.startsWith("/export ")) {
    const format = text.includes("docx") ? "docx" : "md"
    return {
      kind: "send",
      message: { type: "export", format },
      state: { ...state, statusLine: `exportando ${format}…` },
    }
  }

  const next: AppState = {
    ...state,
    activities: [],
    lastError: "",
    phase: "leyendo",
    statusLine: "leyendo fuentes…",
  }
  return { kind: "send", message: { type: "prompt", text }, state: next }
}

export function handleHotkey(state: AppState, key: string): LocalAction {
  if (key === "tab") {
    const idx = FOCUS_PANELS.indexOf(state.focusPanel)
    const focusPanel = FOCUS_PANELS[(idx + 1) % FOCUS_PANELS.length]
    return { kind: "state", state: { ...state, focusPanel } }
  }
  if (key === "e" && state.evidence.length) {
    return { kind: "state", state: { ...state, focusPanel: "evidence" } }
  }
  if (key === "p" && state.plan) {
    return { kind: "state", state: { ...state, planPinned: !state.planPinned } }
  }
  if (key === "[") {
    if (state.evidence.length) {
      const evidenceIndex = (state.evidenceIndex - 1 + state.evidence.length) % state.evidence.length
      return { kind: "state", state: { ...state, evidenceIndex, focusPanel: "evidence" } }
    }
  }
  if (key === "]") {
    if (state.evidence.length) {
      const evidenceIndex = (state.evidenceIndex + 1) % state.evidence.length
      return { kind: "state", state: { ...state, evidenceIndex, focusPanel: "evidence" } }
    }
  }
  if (key === "?" ) {
    return { kind: "state", state: { ...state, help: !state.help } }
  }
  if (state.help && (key === "escape" || key === "q")) {
    return { kind: "state", state: { ...state, help: false } }
  }
  if (state.phase === "esperando_plan") {
    if (key === "a" || key === "enter") {
      return {
        kind: "send",
        message: { type: "plan.decide", decision: "approve", plan: state.plan ?? undefined },
        state: { ...state, statusLine: "Plan aprobado. Redactando…" },
      }
    }
    if (key === "x") {
      return {
        kind: "send",
        message: { type: "plan.decide", decision: "cancel" },
        state: { ...state, phase: "idle", statusLine: "Plan cancelado." },
      }
    }
  }
  if (state.phase === "esperando_criterio" && state.uiMode !== "critique") {
    if (key === "s") {
      return { kind: "send", message: { type: "gate", decision: "s" }, state: { ...state, statusLine: "Aceptando…" } }
    }
    if (key === "n") {
      return { kind: "send", message: { type: "gate", decision: "n" }, state: { ...state, statusLine: "Descartando…" } }
    }
    if (key === "b") {
      return { kind: "send", message: { type: "gate", decision: "b" }, state: { ...state, statusLine: "Guardando borrador…" } }
    }
    if (key === "c") {
      return {
        kind: "state",
        state: {
          ...state,
          uiMode: "critique",
          statusLine: "Escribe la crítica y Enter. Esc cancela.",
        },
      }
    }
  }
  if (state.uiMode === "critique" && key === "escape") {
    return { kind: "state", state: { ...state, uiMode: "prompt", statusLine: "s sí · n no · b borrador · c corregir" } }
  }
  if ((key === "q" || key === "ctrl+c") && state.uiMode !== "critique" && state.phase !== "esperando_criterio") {
    return { kind: "quit" }
  }
  return { kind: "none", state }
}

export function gateStrip(state: AppState): string {
  if (state.uiMode === "critique") {
    return "crítica abierta · Enter envía al agente · esc vuelve a s/n/b/c"
  }
  if (state.phase === "esperando_plan") {
    return "[ a ] aprobar plan     [ x ] cancelar     /objetivo  /oa  /duracion"
  }
  if (state.phase === "esperando_criterio") {
    const n = state.evidence.length
    const mark = n ? `     [ ] ${state.evidenceIndex + 1}/${n}` : ""
    return `[ s ] sí → derivados/     [ n ] no     [ b ] borrador     [ c ] corregir${mark}`
  }
  return ""
}

export function chips(encargo: Encargo): string[] {
  return [encargo.curso, encargo.asignatura, encargo.oa, encargo.duracion, encargo.tipo]
    .map((item) => (item ?? "").trim())
    .filter(Boolean)
}

export function footerFor(state: AppState): string {
  if (state.help) return "esc cierra ayuda"
  if (state.uiMode === "critique") return "crítica → Enter envía · esc cancela"
  if (state.phase === "esperando_plan") return "a aprobar  x cancelar  /objetivo  Tab panel  ? ayuda"
  if (state.phase === "esperando_criterio") return "s sí  n no  b borrador  c corregir  [ ] evidencia  Tab  ? "
  return "Enter envía  /oa /tipo /export  Tab panel  ? ayuda  q salir"
}

export const HELP_TEXT = `tero — el agente prepara, el docente decide

Flujo
  1. Encargo (chips)  2. Plan tipado  3. Borrador + evidencia  4. Puerta

Teclas
  s  aceptar → derivados/     n  descartar
  b  borradores/              c  corregir
  a  aprobar plan             x  cancelar plan
  [ ]  recorrer evidencia     e  foco evidencia
  Tab  sesión/propuesta/evidencia
  p  fijar/ocultar plan       ?  ayuda   q  salir

Comandos
  /oa OA 6   /tipo guia|evaluacion|pauta|actividad|planificacion
  /curso 4°  /asignatura …  /duracion 45 min  /objetivo …
  /export [md|docx]

La carpeta es el sistema de registro. Citas: ✓ en el archivo, ? parafraseo.
tero no sobreescribe originales (hash).`
