import type {
  Activity,
  ClientMessage,
  Encargo,
  Evidence,
  HostEvent,
  OAOption,
  Phase,
  Plan,
  PlanQuestion,
  RecentSession,
  TurnSummary,
  WarningItem,
} from "./protocol.ts"

export type UiMode = "prompt" | "critique" | "assumption" | "clarify"
export type FocusPanel = "session" | "proposal" | "evidence"
export type Screen = "home" | "workspace"
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
  errorCode: string
  retryable: boolean
  uiMode: UiMode
  lastPath: string
  evidenceIndex: number
  focusPanel: FocusPanel
  sourceCount: number
  changedCount: number
  planPinned: boolean
  screen: Screen
  recentSessions: RecentSession[]
  question: PlanQuestion | null
  thinking: boolean
  thinkingLabel: string
  spinnerFrame: number
  compact: boolean
  assumptionEditId: string
  lastExport: string
  started: boolean
  oaOptions: OAOption[]
  oaHint: string
}

export function initialState(encargo: Encargo): AppState {
  const hasChips = Boolean(encargo.curso || encargo.asignatura || encargo.oa || encargo.rumbo)
  return {
    ready: false,
    mode: "…",
    model: "…",
    carpeta: "",
    phase: "home",
    encargo: hasChips ? encargo : { curso: "", asignatura: "", oa: "", duracion: "", tipo: null },
    turns: [],
    activities: [],
    proposal: "",
    proposalTitle: "",
    evidence: [],
    warnings: [],
    plan: null,
    help: false,
    statusLine: "Pregunta, explora o crea con tero…",
    lastError: "",
    errorCode: "",
    retryable: false,
    uiMode: "prompt",
    lastPath: "",
    evidenceIndex: 0,
    focusPanel: "proposal",
    sourceCount: 0,
    changedCount: 0,
    planPinned: false,
    screen: "home",
    recentSessions: [],
    question: null,
    thinking: false,
    thinkingLabel: "",
    spinnerFrame: 0,
    compact: false,
    assumptionEditId: "",
    lastExport: "",
    started: false,
    oaOptions: [],
    oaHint: "",
  }
}

export const PHASE_LABEL: Record<Phase, string> = {
  idle: "listo",
  home: "inicio",
  leyendo: "leyendo fuentes",
  proponiendo_plan: "proponiendo plan",
  esperando_clarificacion: "clarificación",
  esperando_plan: "criterio · plan",
  escribiendo: "escribiendo borrador",
  esperando_criterio: "criterio · puerta",
  exportando: "exportando",
  listo: "listo",
  error: "error",
}

export const TOOL_LABEL: Record<string, string> = {
  list_sources: "fuentes",
  search_sources: "buscar",
  read_source: "leer",
  list_oa: "OA lista",
  get_oa: "OA",
  search_oa: "OA busca",
  propose_plan: "plan",
  plan: "plan",
  cite_evidence: "cita",
  draft_artifact: "borrador",
  draft: "borrador",
  host: "host",
}

export const RUMBOS = [
  { id: "planificar", key: "1", label: "Planificar", hint: "secuencia de clase" },
  { id: "crear", key: "2", label: "Crear", hint: "guía o actividad" },
  { id: "evaluar", key: "3", label: "Evaluar", hint: "prueba o pauta" },
  { id: "adaptar", key: "4", label: "Adaptar", hint: "ajustar material" },
] as const

const SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

export function spinnerGlyph(frame: number): string {
  return SPINNER[frame % SPINNER.length]
}

export function applyHostEvent(state: AppState, event: HostEvent): AppState {
  const next = {
    ...state,
    activities: [...state.activities],
    turns: [...state.turns],
    warnings: [...state.warnings],
  }
  switch (event.type) {
    case "ready":
      next.ready = true
      next.mode = String(event.mode ?? next.mode)
      next.model = String(event.model ?? next.model)
      next.carpeta = String(event.carpeta ?? next.carpeta)
      next.statusLine =
        next.mode === "offline"
          ? `listo · offline (tero-offline) · no es Bedrock`
          : `listo · bedrock · ${next.model}`
      break
    case "hello_ok":
      next.carpeta = String(event.carpeta ?? next.carpeta)
      if (event.encargo && typeof event.encargo === "object") {
        next.encargo = { ...next.encargo, ...(event.encargo as Encargo) }
      }
      if (typeof event.fuentes === "number") next.sourceCount = event.fuentes
      if (typeof event.changed === "number") next.changedCount = event.changed
      if (Array.isArray(event.sessions)) {
        next.recentSessions = event.sessions as RecentSession[]
      }
      if (!next.started) {
        next.screen = "home"
        next.phase = "home"
        next.statusLine = next.sourceCount
          ? `carpeta · ${next.sourceCount} fuente${next.sourceCount === 1 ? "" : "s"}`
          : "Pregunta, explora o crea con tero…"
      }
      break
    case "status": {
      next.phase = (event.phase as Phase) || next.phase
      const detail = event.detail ? String(event.detail) : ""
      const progress = event.progress ? String(event.progress) : ""
      const step = event.step ? String(event.step) : ""
      const label = [progress && `${progress}`, detail || PHASE_LABEL[next.phase] || next.phase]
        .filter(Boolean)
        .join(" · ")
      next.statusLine = label
      if (
        next.phase === "leyendo" ||
        next.phase === "proponiendo_plan" ||
        next.phase === "escribiendo"
      ) {
        next.lastError = ""
        next.errorCode = ""
        next.thinking = true
        next.thinkingLabel = step === "draft_retry"
          ? "reintento borrador"
          : detail || PHASE_LABEL[next.phase]
        next.screen = "workspace"
        next.started = true
      } else if (
        next.phase === "esperando_plan" ||
        next.phase === "esperando_clarificacion" ||
        next.phase === "esperando_criterio" ||
        next.phase === "idle" ||
        next.phase === "listo" ||
        next.phase === "home"
      ) {
        next.thinking = false
        next.thinkingLabel = ""
      }
      break
    }
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
      if (item.state !== "end") {
        next.thinking = true
        next.thinkingLabel = `${TOOL_LABEL[tool] ?? tool}${item.detail ? ` · ${item.detail}` : ""}`
      }
      break
    }
    case "delta":
      if (typeof event.text === "string" && event.text) {
        next.thinking = true
        next.thinkingLabel = "modelo · generando…"
        next.statusLine = `${spinnerGlyph(next.spinnerFrame)} ${next.thinkingLabel}`
      }
      break
    case "plan":
      next.plan = event.plan as Plan
      next.planPinned = true
      next.screen = "workspace"
      next.started = true
      next.thinking = false
      {
        const pending = pendingQuestion(next.plan)
        if (pending) {
          next.question = pending
          next.phase = "esperando_clarificacion"
          next.uiMode = "clarify"
          next.statusLine = "Responde 1/2/3 o con tus palabras"
        } else {
          next.question = null
          next.phase = "esperando_plan"
          next.uiMode = "prompt"
          next.statusLine = "Plan listo. a aprobar · e supuesto · x cancelar"
        }
      }
      break
    case "plan_question":
      next.plan = (event.plan as Plan) ?? next.plan
      next.question = event.question as PlanQuestion
      next.phase = "esperando_clarificacion"
      next.uiMode = "clarify"
      next.thinking = false
      next.planPinned = true
      next.statusLine = "Clarificación · 1/2/3 o texto libre"
      break
    case "plan_ready":
      next.plan = (event.plan as Plan) ?? next.plan
      next.question = null
      next.phase = "esperando_plan"
      next.uiMode = "prompt"
      next.thinking = false
      next.statusLine = "Plan listo. a aprobar · e supuesto · x cancelar"
      break
    case "plan_approved":
      next.plan = (event.plan as Plan) ?? next.plan
      next.question = null
      next.statusLine = "Plan aprobado. Redactando…"
      next.thinking = true
      next.thinkingLabel = "escribiendo borrador"
      break
    case "plan_cancelled":
      next.phase = "idle"
      next.plan = null
      next.question = null
      next.planPinned = false
      next.uiMode = "prompt"
      next.thinking = false
      next.proposal = ""
      next.proposalTitle = ""
      next.evidence = []
      next.warnings = []
      next.screen = "home"
      next.statusLine = "Plan cancelado. Elige un rumbo o escribe de nuevo."
      break
    case "proposal_cleared":
      next.proposal = ""
      next.proposalTitle = ""
      next.evidence = []
      if (String(event.reason ?? "") === "plan_cancelado") {
        next.warnings = []
      } else {
        next.warnings = [
          ...next.warnings.filter((w) => w.code !== "stale_proposal"),
          {
            code: "stale_proposal",
            message: "Propuesta anterior archivada — el nuevo encargo manda.",
            blocking: false,
          },
        ]
      }
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
      next.warnings = mergeWarnings(next.warnings, artifact?.warnings ?? [])
      next.evidenceIndex = 0
      next.phase = "esperando_criterio"
      next.thinking = false
      next.thinkingLabel = ""
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
      next.thinking = false
      stampPath(next, String(event.path ?? ""))
      break
    case "draft_saved":
      next.phase = "listo"
      next.lastPath = String(event.path ?? "")
      next.statusLine = `Borrador → ${next.lastPath}  ·  /export md funciona también desde borradores/`
      next.uiMode = "prompt"
      next.thinking = false
      stampPath(next, String(event.path ?? ""))
      break
    case "discarded":
      next.phase = "idle"
      next.statusLine = "Descartado. Nada se escribió."
      next.uiMode = "prompt"
      next.thinking = false
      break
    case "exported": {
      next.lastExport = String(event.path ?? "")
      const kind = event.source_kind === "borrador" ? "borrador" : "derivado"
      const fmt = event.format ? String(event.format) : "md"
      const base = `Exportado ${fmt} (${kind}) → ${event.path}`
      const pdf = event.pdf ? `  ·  pdf → ${event.pdf}` : ""
      next.statusLine = event.feedback
        ? `${base}${pdf}  ·  feedback → ${event.feedback}`
        : `${base}${pdf}`
      break
    }
    case "critique_saved":
      next.statusLine = `Crítica guardada (${event.n}) · reescribiendo…`
      next.thinking = true
      next.thinkingLabel = "corrección"
      break
    case "encargo":
      if (event.encargo && typeof event.encargo === "object") {
        next.encargo = { ...next.encargo, ...(event.encargo as Encargo) }
      }
      break
    case "oa_options": {
      const rows = Array.isArray(event.oas) ? (event.oas as OAOption[]) : []
      next.oaOptions = rows
      if (rows.length) {
        const sample = rows
          .slice(0, 4)
          .map((o) => o.codigo || o.id)
          .join(" · ")
        next.oaHint = `${rows.length} OA en catálogo: ${sample}${rows.length > 4 ? "…" : ""}`
        if (!next.encargo.oa) {
          next.statusLine = `OA disponibles · /oa ${rows[0]?.id || rows[0]?.codigo}`
        } else if (next.statusLine.startsWith("curso →") || next.statusLine.startsWith("asignatura →")) {
          next.statusLine = `${next.statusLine}  ·  ${next.oaHint}`
        }
      } else {
        next.oaHint = "sin OA para ese curso/asignatura en el catálogo mínimo"
      }
      break
    }
    case "rumbo":
      next.started = true
      next.statusLine = `Rumbo ${event.rumbo} · escribe el encargo`
      break
    case "warning":
      if (event.warning && typeof event.warning === "object") {
        next.warnings = mergeWarnings(next.warnings, [event.warning as WarningItem])
      }
      break
    case "error":
      next.lastError = String(event.message ?? "error")
      next.errorCode = String(event.code ?? "")
      next.retryable = Boolean(event.retryable)
      next.statusLine = next.lastError
      next.phase = "error"
      next.thinking = false
      break
    default:
      break
  }
  return next
}

function pendingQuestion(plan: Plan | null): PlanQuestion | null {
  if (!plan?.questions?.length) return null
  return (
    plan.questions.find((q) => q.answer == null && (q.free_text == null || q.free_text === "")) ??
    null
  )
}

function mergeWarnings(existing: WarningItem[], incoming: WarningItem[]): WarningItem[] {
  const out = [...existing]
  const seen = new Set(out.map((w) => `${w.code}:${w.message}`))
  for (const item of incoming) {
    const key = `${item.code}:${item.message}`
    if (seen.has(key)) continue
    seen.add(key)
    out.push(item)
  }
  return out.slice(-12)
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

function enterWorkspace(state: AppState, patch: Partial<AppState> = {}): AppState {
  return {
    ...state,
    ...patch,
    screen: "workspace",
    started: true,
  }
}

export function handleCommand(state: AppState, raw: string): LocalAction {
  const text = raw.trim()
  if (!text) {
    return {
      kind: "state",
      state: {
        ...state,
        statusLine: "Escribe un encargo o elige un rumbo (1–4). Enter vacío no envía.",
      },
    }
  }

  if (state.uiMode === "critique") {
    const next = {
      ...state,
      uiMode: "prompt" as const,
      statusLine: "Enviando corrección…",
      thinking: true,
      thinkingLabel: "corrección",
    }
    return { kind: "send", message: { type: "gate", decision: "c", note: text }, state: next }
  }

  if (state.uiMode === "assumption") {
    const id = state.assumptionEditId || "s1"
    return {
      kind: "send",
      message: { type: "plan.edit_assumption", id, text },
      state: {
        ...state,
        uiMode: "prompt",
        assumptionEditId: "",
        statusLine: "Supuesto actualizado",
      },
    }
  }

  if (state.uiMode === "clarify" || state.phase === "esperando_clarificacion") {
    if (/^[123]$/.test(text)) {
      return {
        kind: "send",
        message: {
          type: "plan.answer",
          option_id: text,
          question_id: state.question?.id,
        },
        state: { ...state, statusLine: `Opción ${text}…`, uiMode: "clarify" },
      }
    }
    return {
      kind: "send",
      message: {
        type: "plan.answer",
        text,
        question_id: state.question?.id,
      },
      state: { ...state, statusLine: "Respuesta enviada…", uiMode: "clarify" },
    }
  }

  if (text === "/help" || text === "?") {
    return { kind: "state", state: { ...state, help: !state.help } }
  }
  if (text === "/q" || text === "/salir") {
    return { kind: "quit" }
  }
  if (text === "/home" || text === "/inicio") {
    return {
      kind: "state",
      state: {
        ...state,
        screen: "home",
        phase: "home",
        statusLine: "Pregunta, explora o crea con tero…",
      },
    }
  }
  if (text === "/retry" || text === "/reintentar") {
    return {
      kind: "send",
      message: { type: "retry" },
      state: enterWorkspace(state, {
        lastError: "",
        thinking: true,
        thinkingLabel: "reintento",
        statusLine: "Reintentando…",
        activities: [],
      }),
    }
  }
  if (text.startsWith("/rumbo ")) {
    const rumbo = text.slice(7).trim()
    const encargo = { ...state.encargo, rumbo }
    return {
      kind: "send",
      message: { type: "rumbo", rumbo },
      state: enterWorkspace(state, {
        encargo,
        statusLine: `Rumbo → ${rumbo}`,
      }),
    }
  }
  if (text.startsWith("/oa ")) {
    const oaRaw = text.slice(4).trim()
    const match = matchOA(state.oaOptions, oaRaw)
    const oa = match ? `${match.codigo} (${match.id})` : oaRaw
    const encargo = { ...state.encargo, oa }
    const plan = state.plan ? { ...state.plan, oa } : state.plan
    const warn = match
      ? `OA → ${oa}`
      : state.oaOptions.length
        ? `OA «${oaRaw}» no está en la lista cargada — se envía igual; el host valida el catálogo`
        : `OA → ${oa}  ·  fija /curso y /asignatura para cargar opciones`
    return {
      kind: "send",
      message: { type: "encargo.update", encargo },
      state: {
        ...state,
        encargo,
        plan,
        statusLine: `${warn}  ·  nuevo encargo para regenerar`,
        proposal: "",
        proposalTitle: "",
        evidence: [],
      },
    }
  }
  if (text.startsWith("/tipo ")) {
    const tipo = text.slice(6).trim()
    const encargo = { ...state.encargo, tipo }
    const plan = state.plan ? { ...state.plan, tipo } : state.plan
    return {
      kind: "send",
      message: { type: "encargo.update", encargo },
      state: {
        ...state,
        encargo,
        plan,
        statusLine: `tipo → ${tipo}  ·  envía un nuevo encargo para regenerar`,
        proposal: "",
        proposalTitle: "",
        evidence: [],
      },
    }
  }
  if (text.startsWith("/curso ")) {
    const encargo = { ...state.encargo, curso: text.slice(7).trim() }
    const plan = state.plan
      ? {
          ...state.plan,
          decisiones: { ...(state.plan.decisiones || {}), curso: encargo.curso },
        }
      : state.plan
    return {
      kind: "send",
      message: { type: "encargo.update", encargo },
      state: {
        ...state,
        encargo,
        plan,
        statusLine: `curso → ${encargo.curso}`,
      },
    }
  }
  if (text.startsWith("/asignatura ")) {
    const encargo = { ...state.encargo, asignatura: text.slice(12).trim() }
    const plan = state.plan
      ? {
          ...state.plan,
          decisiones: { ...(state.plan.decisiones || {}), asignatura: encargo.asignatura },
        }
      : state.plan
    return {
      kind: "send",
      message: { type: "encargo.update", encargo },
      state: {
        ...state,
        encargo,
        plan,
        statusLine: `asignatura → ${encargo.asignatura}`,
      },
    }
  }
  if (text.startsWith("/tema ")) {
    const tema = text.slice(6).trim()
    const encargo = { ...state.encargo, tema }
    const plan = state.plan
      ? { ...state.plan, decisiones: { ...(state.plan.decisiones || {}), tema } }
      : state.plan
    return {
      kind: "send",
      message: { type: "encargo.update", encargo },
      state: { ...state, encargo, plan, statusLine: `tema → ${tema}` },
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
  if (text.startsWith("/supuesto ")) {
    if (!state.plan) return { kind: "none", state }
    return {
      kind: "send",
      message: { type: "plan.edit_assumption", id: "s1", text: text.slice(10).trim() },
      state: { ...state, statusLine: "Supuesto actualizado" },
    }
  }
  if (text === "/export" || text.startsWith("/export ")) {
    const rest = text.slice("/export".length).trim().toLowerCase()
    let format: "md" | "docx" | "latex" | "tex" = "md"
    if (rest.includes("docx")) format = "docx"
    else if (rest.includes("latex") || rest.includes("tex")) format = "latex"
    return {
      kind: "send",
      message: { type: "export", format },
      state: { ...state, statusLine: `exportando ${format}…` },
    }
  }

  // Numeric rumbo shortcut from home
  if (state.screen === "home" && /^[1234]$/.test(text)) {
    const rumbo = RUMBOS.find((r) => r.key === text)!
    const encargo = { ...state.encargo, rumbo: rumbo.id }
    return {
      kind: "send",
      message: { type: "rumbo", rumbo: rumbo.id },
      state: enterWorkspace(state, {
        encargo,
        statusLine: `${rumbo.label} · escribe qué necesitas`,
      }),
    }
  }

  const next = enterWorkspace(state, {
    activities: [],
    lastError: "",
    errorCode: "",
    phase: "leyendo",
    statusLine: "leyendo fuentes…",
    thinking: true,
    thinkingLabel: "leyendo fuentes",
    proposal: "",
    proposalTitle: "",
    evidence: [],
  })
  return { kind: "send", message: { type: "prompt", text }, state: next }
}

export function handleHotkey(state: AppState, key: string): LocalAction {
  if (key === "tab") {
    const idx = FOCUS_PANELS.indexOf(state.focusPanel)
    const focusPanel = FOCUS_PANELS[(idx + 1) % FOCUS_PANELS.length]
    return { kind: "state", state: { ...state, focusPanel } }
  }
  if (key === "e" && state.phase === "esperando_plan" && state.plan) {
    return {
      kind: "state",
      state: {
        ...state,
        uiMode: "assumption",
        assumptionEditId: state.plan.supuestos?.[0]?.id || "s1",
        statusLine: "Edita el supuesto y Enter. Esc cancela.",
      },
    }
  }
  if (key === "e" && state.evidence.length) {
    return { kind: "state", state: { ...state, focusPanel: "evidence" } }
  }
  if (key === "p" && state.plan) {
    return { kind: "state", state: { ...state, planPinned: !state.planPinned } }
  }
  if (key === "[") {
    if (state.evidence.length <= 1) {
      return {
        kind: "state",
        state: {
          ...state,
          focusPanel: "evidence",
          statusLine:
            state.evidence.length === 0
              ? "Sin evidencia aún"
              : "1/1 evidencia · [ ] no cambia (solo un ítem)",
        },
      }
    }
    const evidenceIndex = (state.evidenceIndex - 1 + state.evidence.length) % state.evidence.length
    return { kind: "state", state: { ...state, evidenceIndex, focusPanel: "evidence" } }
  }
  if (key === "]") {
    if (state.evidence.length <= 1) {
      return {
        kind: "state",
        state: {
          ...state,
          focusPanel: "evidence",
          statusLine:
            state.evidence.length === 0
              ? "Sin evidencia aún"
              : "1/1 evidencia · [ ] no cambia (solo un ítem)",
        },
      }
    }
    const evidenceIndex = (state.evidenceIndex + 1) % state.evidence.length
    return { kind: "state", state: { ...state, evidenceIndex, focusPanel: "evidence" } }
  }
  if (key === "?") {
    return { kind: "state", state: { ...state, help: !state.help } }
  }
  if (state.help && (key === "escape" || key === "q")) {
    return { kind: "state", state: { ...state, help: false } }
  }
  if (state.uiMode === "assumption" && key === "escape") {
    return {
      kind: "state",
      state: {
        ...state,
        uiMode: "prompt",
        assumptionEditId: "",
        statusLine: "a aprobar · e supuesto · x cancelar",
      },
    }
  }
  if (state.phase === "error" && state.retryable && (key === "r" || key === "enter")) {
    return {
      kind: "send",
      message: { type: "retry" },
      state: enterWorkspace(state, {
        lastError: "",
        thinking: true,
        thinkingLabel: "reintento",
        statusLine: "Reintentando…",
        activities: [],
      }),
    }
  }
  if (state.screen === "home" && ["1", "2", "3", "4"].includes(key)) {
    return handleCommand(state, key)
  }
  if (state.phase === "esperando_clarificacion" && ["1", "2", "3"].includes(key)) {
    return handleCommand(state, key)
  }
  if (state.phase === "esperando_plan") {
    if (key === "a" || key === "enter") {
      return {
        kind: "send",
        message: { type: "plan.decide", decision: "approve", plan: state.plan ?? undefined },
        state: {
          ...state,
          statusLine: "Plan aprobado. Redactando…",
          thinking: true,
          thinkingLabel: "escribiendo",
        },
      }
    }
    if (key === "x") {
      return {
        kind: "send",
        message: { type: "plan.decide", decision: "cancel" },
        state: {
          ...state,
          phase: "idle",
          statusLine: "Plan cancelado.",
          screen: "home",
          plan: null,
          question: null,
        },
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
      return {
        kind: "send",
        message: { type: "gate", decision: "b" },
        state: { ...state, statusLine: "Guardando borrador…" },
      }
    }
    if (key === "c") {
      return {
        kind: "state",
        state: {
          ...state,
          uiMode: "critique",
          statusLine: "Escribe la crítica y Enter. Esc cancela. Se persiste en .tero/criticas/",
        },
      }
    }
  }
  if (state.uiMode === "critique" && key === "escape") {
    return {
      kind: "state",
      state: { ...state, uiMode: "prompt", statusLine: "s sí · n no · b borrador · c corregir" },
    }
  }
  if (
    (key === "q" || key === "ctrl+c") &&
    state.uiMode !== "critique" &&
    state.phase !== "esperando_criterio" &&
    state.phase !== "esperando_clarificacion"
  ) {
    return { kind: "quit" }
  }
  return { kind: "none", state }
}

export function gateStrip(state: AppState): string {
  if (state.uiMode === "critique") {
    return "crítica abierta · Enter envía (se guarda) · esc vuelve a s/n/b/c"
  }
  if (state.uiMode === "assumption") {
    return "editando SUPUESTO · Enter guarda · esc cancela"
  }
  if (state.phase === "esperando_clarificacion") {
    return "clarificación · [1] [2] [3] elige · o escribe abajo · x cancela plan"
  }
  if (state.phase === "esperando_plan") {
    return "[ a ] aprobar     [ e ] supuesto     [ x ] cancelar     /oa /objetivo"
  }
  if (state.phase === "esperando_criterio") {
    const n = state.evidence.length
    const mark = n ? `     evid ${state.evidenceIndex + 1}/${n}` : "     sin evid"
    return `[ s ] sí→derivados/  [ n ] no  [ b ] borrador  [ c ] corregir${mark}`
  }
  if (state.phase === "error" && state.retryable) {
    return "[ r ] reintentar     /home volver al inicio"
  }
  return ""
}

export function chips(encargo: Encargo): string[] {
  return [
    encargo.rumbo,
    encargo.curso,
    encargo.asignatura,
    encargo.tema,
    encargo.oa,
    encargo.duracion,
    encargo.tipo,
  ]
    .map((item) => (item ?? "").trim())
    .filter(Boolean)
}

export function showChips(state: AppState): boolean {
  if (state.screen === "home" && !state.started) return false
  return chips(state.encargo).length > 0
}

export function footerFor(state: AppState): string {
  if (state.help) return "PgUp/PgDn desplaza  esc cierra ayuda"
  if (state.uiMode === "critique") return "crítica → Enter envía · esc cancela"
  if (state.uiMode === "assumption") return "supuesto → Enter · esc cancela"
  if (state.phase === "esperando_clarificacion") return "1/2/3 elige  texto libre  ? ayuda"
  if (state.phase === "esperando_plan") return "a aprobar  e supuesto  x cancelar  Tab  ? "
  if (state.phase === "esperando_criterio") return "s sí  n no  b borrador  c corregir  [ ] evid  ?"
  if (state.phase === "error") return state.retryable ? "r reintenta  /home  ? " : "/home  ? "
  if (state.screen === "home") return "1–4 rumbo  Enter envía  ? ayuda  q salir"
  return "Enter  /oa /curso /export latex  Tab  ?  q"
}

export function helpFor(state: AppState): string {
  if (state.screen === "home" || state.phase === "home") {
    return `tero — inicio

Rumbos
  1 Planificar   2 Crear   3 Evaluar   4 Adaptar

Escribe abajo: «Pregunta, explora o crea…»
Chips tras rumbo o encargo. Catálogo OA Chile (host).

? cierra · q sale`
  }
  if (state.phase === "esperando_clarificacion") {
    return `Clarificación del plan

Elige 1 / 2 / 3 (SUGERIDA marcada)
o escribe con tus palabras abajo.

a aún no — primero responde.
x cancela el plan y vuelve al inicio.

? cierra`
  }
  if (state.phase === "esperando_plan") {
    return `Plan tipado

a  aprobar y redactar
e  editar SUPUESTOS (inline)
x  cancelar → inicio limpio
/objetivo …  /oa LEN-4B-OA04  /supuesto …

El plan queda fijado (p) mientras redacta.

? cierra`
  }
  if (state.phase === "esperando_criterio") {
    return `Puerta docente

s  sí → derivados/
n  no  (no escribe)
b  borrador → borradores/  (/export md|latex)
c  corregir (crítica se guarda en .tero/)

[ ] evidencia  ·  ✓ en archivo  ·  ? parafraseo
Tab paneles

? cierra`
  }
  if (state.phase === "error") {
    return `Error

${state.lastError}

r o /retry  reintenta
/home       vuelve al inicio

Offline se etiqueta tero-offline (no es Bedrock).

? cierra`
  }
  return `tero — el agente prepara, el docente decide

Flujo
  home → rumbo/encargo → plan card → clarificación
  → borrador + evidencia → puerta s/n/b/c

Teclas
  s/n/b/c puerta   a/x plan   1-4 rumbo/opción
  [ ] evidencia    e supuesto o foco evidencia
  Tab paneles      p fijar plan   ? ayuda   q salir

Comandos
  /oa /tipo /curso /asignatura /tema /duracion
  /objetivo /supuesto   /export [md|docx|latex]   /retry /home

OA: catálogo host (list_oa). LaTeX: JSON→plantilla, no TeX libre.
Citas: ✓ en el archivo, ? parafraseo (aviso, no bloquea).
tero no sobreescribe originales (hash).`
}

export function matchOA(options: OAOption[], raw: string): OAOption | null {
  const needle = raw.trim().toLowerCase()
  if (!needle || !options.length) return null
  const compact = needle.replace(/[^a-z0-9]/g, "")
  for (const opt of options) {
    const id = (opt.id || "").toLowerCase()
    const codigo = (opt.codigo || "").toLowerCase()
    if (id === needle || codigo === needle) return opt
    if (id.replace(/[^a-z0-9]/g, "") === compact) return opt
    if (codigo.replace(/[^a-z0-9]/g, "") === compact) return opt
  }
  return null
}

/** @deprecated use helpFor(state) */
export const HELP_TEXT = helpFor(initialState({
  curso: "",
  asignatura: "",
  oa: "",
  duracion: "",
  tipo: null,
}))
