import type {
  Activity,
  CardStatus,
  ClientMessage,
  Encargo,
  Evidence,
  HostEvent,
  Mensaje,
  OAOption,
  Phase,
  Propuesta,
  PropuestaAccion,
  RecentSession,
  ThreadRole,
  WarningItem,
} from "./protocol.ts"

export type FocusPanel = "hilo" | "propuesta" | "evidencia"
export type Screen = "home" | "conversacion"
export const FOCUS_PANELS: FocusPanel[] = ["hilo", "propuesta", "evidencia"]

export type AppState = {
  ready: boolean
  mode: string
  model: string
  carpeta: string
  phase: Phase
  encargo: Encargo
  /** Hilo de conversación: persona, agente y notas del host. */
  messages: Mensaje[]
  /** Texto en streaming del turno en curso (`delta`). */
  streaming: string
  /** Última propuesta del agente (pendiente, escrita o descartada). */
  card: Propuesta | null
  cardId: string
  cardStatus: CardStatus | ""
  writtenPath: string
  writtenAccion: string
  activities: Activity[]
  warnings: WarningItem[]
  help: boolean
  statusLine: string
  lastError: string
  errorCode: string
  retryable: boolean
  lastPath: string
  lastExport: string
  evidenceIndex: number
  focusPanel: FocusPanel
  sourceCount: number
  changedCount: number
  screen: Screen
  recentSessions: RecentSession[]
  thinking: boolean
  thinkingLabel: string
  spinnerFrame: number
  compact: boolean
  started: boolean
  oaOptions: OAOption[]
  oaHint: string
  /** Correlativo local para ids de mensajes del hilo. */
  seq: number
}

export function initialState(encargo: Encargo): AppState {
  const hasContext = Boolean(encargo.curso || encargo.asignatura || encargo.oa || encargo.tema)
  return {
    ready: false,
    mode: "…",
    model: "…",
    carpeta: "",
    phase: "idle",
    encargo: hasContext ? encargo : { curso: "", asignatura: "", oa: "", duracion: "", tipo: null },
    messages: [],
    streaming: "",
    card: null,
    cardId: "",
    cardStatus: "",
    writtenPath: "",
    writtenAccion: "",
    activities: [],
    warnings: [],
    help: false,
    statusLine: "escribe lo que necesitas",
    lastError: "",
    errorCode: "",
    retryable: false,
    lastPath: "",
    lastExport: "",
    evidenceIndex: 0,
    focusPanel: "propuesta",
    sourceCount: 0,
    changedCount: 0,
    screen: "home",
    recentSessions: [],
    thinking: false,
    thinkingLabel: "",
    spinnerFrame: 0,
    compact: false,
    started: false,
    oaOptions: [],
    oaHint: "",
    seq: 0,
  }
}

export const PHASE_LABEL: Record<Phase, string> = {
  idle: "listo",
  pensando: "pensando",
  esperando_aprobacion: "tu decisión",
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
  cite_evidence: "cita",
  proponer_crear: "propuesta",
  proponer_editar: "propuesta",
  host: "host",
}

/** Etiqueta legible de la acción de una propuesta. */
export function accionLabel(accion: string): string {
  if (accion === "editar") return "editar"
  if (accion === "adaptar") return "adaptar (NEE)"
  return "crear"
}

const SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

export function spinnerGlyph(frame: number): string {
  return SPINNER[frame % SPINNER.length] ?? "⠋"
}

export function shortPath(path: string): string {
  const parts = path.split("/").filter(Boolean)
  if (parts.length <= 2) return path
  // Keep export filenames readable (…/derivados/20240910-….tex).
  const leaf = parts[parts.length - 1] || ""
  const parent = parts[parts.length - 2] || ""
  if (parent === "derivados" || parent === "borradores" || parent === "exports") {
    return `…/${parent}/${leaf}`
  }
  if (leaf.length > 28) return `…/${leaf.slice(0, 12)}…${leaf.slice(-10)}`
  return `…/${parts.slice(-2).join("/")}`
}

export function shortModel(model: string): string {
  if (!model) return model
  if (model === "tero-offline" || model.includes("offline")) return "offline"
  const leaf = model.split("/").pop() || model
  return leaf.length > 28 ? `${leaf.slice(0, 27)}…` : leaf
}

export function applyHostEvent(state: AppState, event: HostEvent): AppState {
  const next = {
    ...state,
    activities: [...state.activities],
    messages: [...state.messages],
    warnings: [...state.warnings],
  }
  switch (event.type) {
    case "ready":
      next.ready = true
      next.mode = String(event.mode ?? next.mode)
      next.model = String(event.model ?? next.model)
      next.carpeta = String(event.carpeta ?? next.carpeta)
      appendTranscript(next, event.transcript)
      next.statusLine =
        next.mode === "offline" ? "listo · offline" : `listo · ${shortModel(next.model)}`
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
      appendTranscript(next, event.transcript)
      if (!next.started) {
        next.phase = "idle"
        next.statusLine = next.sourceCount
          ? `${next.sourceCount} fuente${next.sourceCount === 1 ? "" : "s"} en la carpeta`
          : "escribe lo que necesitas"
      }
      break
    case "status": {
      const phase = normalizePhase(event.phase)
      if (phase) next.phase = phase
      const detail = event.detail ? String(event.detail) : ""
      if (next.phase === "pensando") {
        next.thinking = true
        next.thinkingLabel = detail || "pensando"
        next.statusLine = detail || "pensando…"
        next.lastError = ""
        next.errorCode = ""
        next.screen = "conversacion"
        next.started = true
      } else {
        next.thinking = false
        next.thinkingLabel = ""
        if (next.phase === "esperando_aprobacion") next.statusLine = "tu decisión: y / n"
        else if (next.phase === "error") next.statusLine = next.lastError || "error"
        else if (detail) next.statusLine = detail
      }
      break
    }
    case "delta":
      if (typeof event.text === "string" && event.text) {
        next.streaming = next.streaming + event.text
        next.thinking = true
        next.thinkingLabel = "escribiendo…"
        next.statusLine = `${spinnerGlyph(next.spinnerFrame)} escribiendo…`
        next.screen = "conversacion"
        next.started = true
      }
      break
    case "respuesta": {
      const text = String(event.texto ?? "")
      next.streaming = ""
      next.thinking = false
      next.thinkingLabel = ""
      next.screen = "conversacion"
      next.started = true
      next.phase = "idle"
      if (text) appendMessage(next, { id: eventId(event, next), role: "agente", text })
      next.statusLine =
        next.card && next.cardStatus === "pendiente"
          ? "respuesta · la propuesta sigue pendiente"
          : ""
      break
    }
    case "propuesta": {
      const card = normalizePropuesta(event.propuesta)
      next.streaming = ""
      next.thinking = false
      next.thinkingLabel = ""
      next.screen = "conversacion"
      next.started = true
      if (card) {
        next.card = card
        next.cardId = String(event.id ?? "")
        next.cardStatus = "pendiente"
        next.evidenceIndex = 0
        next.phase = "esperando_aprobacion"
        next.statusLine = "tu decisión: y aprueba · n descarta · o escribe"
      }
      break
    }
    case "aprobacion": {
      const decision = String(event.decision ?? "")
      const note = event.note ? String(event.note) : ""
      const suffix = note ? ` · ${note}` : ""
      if (decision === "descartar") {
        next.cardStatus = next.card ? "descartado" : ""
        next.phase = "idle"
        next.thinking = false
        next.statusLine = "descartado · no se escribió nada"
        appendMessage(next, {
          id: eventId(event, next),
          role: "host",
          text: `descartado${suffix} · no se escribió nada`,
        })
      } else {
        next.cardStatus = next.card ? "aprobado" : ""
        next.phase = "pensando"
        next.thinking = true
        next.thinkingLabel = "escribiendo"
        next.statusLine = `aprobado${suffix} · escribiendo…`
        appendMessage(next, {
          id: eventId(event, next),
          role: "host",
          text: `aprobado${suffix} · escribiendo…`,
        })
      }
      break
    }
    case "escrito": {
      const path = String(event.path ?? "")
      const accion = String(event.accion ?? "")
      next.cardStatus = next.card ? "escrito" : ""
      next.phase = "listo"
      next.thinking = false
      next.thinkingLabel = ""
      next.lastPath = path
      next.writtenPath = path
      next.writtenAccion = accion
      next.screen = "conversacion"
      next.started = true
      next.statusLine = `escrito · ${accionLabel(accion)} · ${shortPath(path)}`
      appendMessage(next, {
        id: eventId(event, next),
        role: "host",
        text: `escrito · ${accionLabel(accion)}`,
        path,
        accion,
      })
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
    case "warning":
      if (event.warning && typeof event.warning === "object") {
        next.warnings = mergeWarnings(next.warnings, [normalizeWarning(event.warning)])
      }
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
    case "exported": {
      next.lastExport = String(event.path ?? "")
      const fmt = event.format ? String(event.format) : "md"
      const pdf = event.pdf ? ` · pdf ${shortPath(String(event.pdf))}` : ""
      const base = `${fmt} · ${shortPath(String(event.path ?? ""))}`
      next.statusLine = event.feedback ? `${base}${pdf} · feedback` : `${base}${pdf}`
      if (next.lastPath) {
        appendMessage(next, {
          id: `e${next.seq + 1}`,
          role: "host",
          text: `export ${fmt}`,
          path: String(event.path ?? ""),
        })
      }
      break
    }
    case "error":
      next.streaming = ""
      next.lastError = String(event.message ?? "error")
      next.errorCode = String(event.code ?? "")
      next.retryable = Boolean(event.retryable)
      next.statusLine = next.lastError
      next.phase = "error"
      next.thinking = false
      next.thinkingLabel = ""
      break
    default:
      break
  }
  return next
}

function normalizePhase(raw: unknown): Phase | null {
  const value = String(raw ?? "")
  if (
    value === "idle" ||
    value === "pensando" ||
    value === "esperando_aprobacion" ||
    value === "listo" ||
    value === "error"
  ) {
    return value
  }
  return null
}

function normalizePropuesta(raw: unknown): Propuesta | null {
  if (!raw || typeof raw !== "object") return null
  const item = raw as Record<string, unknown>
  const accion = String(item.accion ?? "crear")
  return {
    accion: (accion === "editar" || accion === "adaptar" ? accion : "crear") as PropuestaAccion,
    tipo: String(item.tipo ?? ""),
    tipo_label: String(item.tipo_label ?? item.tipo ?? ""),
    titulo: String(item.titulo ?? ""),
    resumen: String(item.resumen ?? ""),
    vista_previa: String(item.vista_previa ?? ""),
    origen: item.origen ? String(item.origen) : null,
    cambios: stringList(item.cambios),
    notas_nee: stringList(item.notas_nee),
    evidencias: Array.isArray(item.evidencias)
      ? item.evidencias.map((row) => normalizeEvidence(row))
      : [],
    warnings: Array.isArray(item.warnings) ? item.warnings.map((row) => normalizeWarning(row)) : [],
  }
}

function normalizeEvidence(raw: unknown): Evidence {
  const item = (raw ?? {}) as Record<string, unknown>
  return {
    path: String(item.path ?? ""),
    snippet: String(item.snippet ?? ""),
    seccion: String(item.seccion ?? ""),
    verified: Boolean(item.verified),
  }
}

function normalizeWarning(raw: unknown): WarningItem {
  const item = (raw ?? {}) as Record<string, unknown>
  return {
    code: String(item.code ?? "warning"),
    message: String(item.message ?? ""),
    // Un aviso nunca bloquea la aprobación en el flujo conversacional.
    blocking: false,
  }
}

function stringList(raw: unknown): string[] {
  if (!Array.isArray(raw)) return []
  return raw.map((row) => String(row)).filter(Boolean)
}

function eventId(event: HostEvent, state: AppState): string {
  const id = event.id ? String(event.id) : ""
  return id || `h${state.seq + 1}`
}

function appendMessage(state: AppState, message: Mensaje) {
  state.messages = [...state.messages, message]
  state.seq = state.seq + 1
  if (state.messages.length > 200) state.messages = state.messages.slice(-200)
  state.screen = "conversacion"
  state.started = true
}

/** Transcribe el hilo que el host manda al abrir la sesión. */
function appendTranscript(state: AppState, raw: unknown) {
  if (!Array.isArray(raw)) return
  for (const row of raw) {
    if (!row || typeof row !== "object") continue
    const item = row as Record<string, unknown>
    const text = String(item.texto ?? item.text ?? "")
    if (!text) continue
    const role = String(item.role ?? "agente")
    appendMessage(state, {
      id: item.id ? String(item.id) : `h${state.seq + 1}`,
      role: (role === "persona" || role === "host" ? role : "agente") as ThreadRole,
      text,
    })
  }
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

/** Avisos de la propuesta vigente + avisos sueltos del host, sin repetir. */
export function allWarnings(state: AppState): WarningItem[] {
  return mergeWarnings(state.warnings, state.card?.warnings ?? [])
}

export type LocalAction =
  | { kind: "send"; message: ClientMessage; state: AppState }
  | { kind: "state"; state: AppState }
  | { kind: "quit" }
  | { kind: "none"; state: AppState }

function enterConversation(state: AppState, patch: Partial<AppState> = {}): AppState {
  return {
    ...state,
    ...patch,
    screen: "conversacion",
    started: true,
  }
}

function appendLocal(state: AppState, message: Omit<Mensaje, "id">): AppState {
  return {
    ...state,
    messages: [...state.messages, { ...message, id: `m${state.seq + 1}` }],
    seq: state.seq + 1,
  }
}

export function handleCommand(state: AppState, raw: string): LocalAction {
  const text = raw.trim()
  if (!text) {
    return {
      kind: "state",
      state: { ...state, statusLine: "Enter vacío no envía: escribe tu mensaje." },
    }
  }

  if (text === "/help" || text === "?") {
    return { kind: "state", state: { ...state, help: !state.help } }
  }
  if (text === "/q" || text === "/salir") {
    return { kind: "quit" }
  }
  if (text === "/retry" || text === "/reintentar") {
    return {
      kind: "send",
      message: { type: "retry" },
      state: enterConversation(state, {
        lastError: "",
        errorCode: "",
        retryable: false,
        thinking: true,
        thinkingLabel: "reintento",
        statusLine: "Reintentando…",
        activities: [],
      }),
    }
  }
  if (text.startsWith("/oa ")) {
    return applyContext(state, "oa", text.slice(4).trim())
  }
  if (text.startsWith("/tipo ")) {
    return applyContext(state, "tipo", text.slice(6).trim())
  }
  if (text.startsWith("/curso ")) {
    return applyContext(state, "curso", text.slice(7).trim())
  }
  if (text.startsWith("/asignatura ")) {
    return applyContext(state, "asignatura", text.slice(12).trim())
  }
  if (text.startsWith("/tema ")) {
    return applyContext(state, "tema", text.slice(6).trim())
  }
  if (text.startsWith("/duracion ") || text.startsWith("/duración ")) {
    return applyContext(state, "duracion", text.replace(/^\/duraci[oó]n\s+/, "").trim())
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

  // Todo lo demás es conversación: el agente infiere la intención (a/b/c).
  const visible = appendLocal(state, { role: "persona", text })
  const stale = state.cardStatus !== "" && state.cardStatus !== "pendiente"
  return {
    kind: "send",
    message: { type: "prompt", text },
    state: enterConversation(visible, {
      card: stale ? null : state.card,
      cardStatus: stale ? "" : state.cardStatus,
      activities: [],
      lastError: "",
      errorCode: "",
      retryable: false,
      phase: "pensando",
      statusLine: "pensando…",
      thinking: true,
      thinkingLabel: "leyendo fuentes",
      streaming: "",
    }),
  }
}

const CONTEXT_LABEL: Record<string, string> = {
  curso: "curso",
  asignatura: "asignatura",
  oa: "OA",
  tipo: "tipo",
  tema: "tema",
  duracion: "duración",
}

/**
 * Los comandos de contexto solo actualizan el encargo.
 * Ya no reinician ningún flujo por pasos: el hilo y la propuesta siguen.
 */
function applyContext(state: AppState, field: keyof Encargo, value: string): LocalAction {
  const label = CONTEXT_LABEL[field] ?? String(field)
  if (!value) {
    return { kind: "state", state: { ...state, statusLine: `/${label} necesita un valor` } }
  }
  let encargo: Encargo = { ...state.encargo, [field]: value }
  let hint = `${label} → ${value}`
  if (field === "oa") {
    const match = matchOA(state.oaOptions, value)
    const oa = match ? `${match.codigo} (${match.id})` : value
    encargo = { ...state.encargo, oa }
    hint = match
      ? `OA → ${oa}`
      : state.oaOptions.length
        ? `OA «${value}» no está en la lista cargada — se envía igual; el host valida el catálogo`
        : `OA → ${oa}  ·  fija /curso y /asignatura para cargar opciones`
  }
  return {
    kind: "send",
    message: { type: "encargo.update", encargo },
    state: {
      ...state,
      encargo,
      statusLine: `${hint}  ·  contexto del encargo`,
    },
  }
}

export function handleHotkey(state: AppState, key: string): LocalAction {
  if (key === "tab") {
    const idx = FOCUS_PANELS.indexOf(state.focusPanel)
    const focusPanel = FOCUS_PANELS[(idx + 1) % FOCUS_PANELS.length] ?? "hilo"
    return { kind: "state", state: { ...state, focusPanel } }
  }
  if (key === "?") {
    return { kind: "state", state: { ...state, help: !state.help } }
  }
  if (state.help && (key === "escape" || key === "q")) {
    return { kind: "state", state: { ...state, help: false } }
  }
  if (state.help) return { kind: "none", state }
  if (state.phase === "error" && state.retryable && (key === "r" || key === "enter")) {
    return {
      kind: "send",
      message: { type: "retry" },
      state: enterConversation(state, {
        lastError: "",
        errorCode: "",
        retryable: false,
        thinking: true,
        thinkingLabel: "reintento",
        statusLine: "Reintentando…",
        activities: [],
      }),
    }
  }
  if (key === "escape") {
    return { kind: "state", state: { ...state, help: false } }
  }
  if (key === "[" || key === "]") {
    const total = state.card?.evidencias.length ?? 0
    if (!total) {
      return { kind: "state", state: { ...state, statusLine: "Sin evidencia: todavía no hay propuesta" } }
    }
    if (total === 1) {
      return {
        kind: "state",
        state: {
          ...state,
          focusPanel: "evidencia",
          statusLine: "1/1 evidencia · [ ] no cambia (solo un ítem)",
        },
      }
    }
    const step = key === "]" ? 1 : -1
    const evidenceIndex = (state.evidenceIndex + step + total) % total
    return { kind: "state", state: { ...state, evidenceIndex, focusPanel: "evidencia" } }
  }
  // La propuesta sigue pendiente aunque el host la haya tratado como
  // conversación (preguntar/ambiguo): y/n deciden mientras siga pendiente.
  if (state.cardStatus === "pendiente" && state.card) {
    if (key === "y") {
      return {
        kind: "send",
        message: { type: "aprobar", decision: "aprobar" },
        state: { ...state, statusLine: "aprobando…", thinking: true, thinkingLabel: "escribiendo" },
      }
    }
    if (key === "n") {
      return {
        kind: "send",
        message: { type: "aprobar", decision: "descartar" },
        state: { ...state, statusLine: "descartando…" },
      }
    }
  }
  if (key === "q" || key === "ctrl+c") {
    // `q` suelto no sale: la primera letra de «qué», «cuándo» o «quién» debe
    // llegar al hilo. Salir: ctrl+c, /q o /salir.
    if (key === "ctrl+c") return { kind: "quit" }
    return { kind: "none", state }
  }
  return { kind: "none", state }
}

/**
 * Franja de decisión: y aprueba, n descarta (o se escribe en el hilo).
 * La ayuda no usa esta franja: se queda en su propio panel.
 */
export function decisionStrip(state: AppState): string {
  if (state.phase === "error" && state.retryable) return "[r] reintentar"
  if (state.cardStatus === "pendiente" && state.card) {
    const n = state.card.evidencias.length
    const mark = n ? `   evid ${state.evidenceIndex + 1}/${n}` : ""
    return `¿escribo el archivo?   [y] aprobar   [n] descartar   ·  o escribe tu decisión abajo${mark}`
  }
  if (state.cardStatus === "escrito") {
    return `escrito · ${accionLabel(state.writtenAccion)} · ${shortPath(state.writtenPath)}`
  }
  if (state.cardStatus === "descartado") {
    return "descartado · no se escribió nada"
  }
  if (state.cardStatus === "aprobado") return "aprobado · escribiendo…"
  return ""
}

/**
 * ¿La tecla pertenece al input? Mientras la persona escribe, el teclado es
 * suyo: solo `tab` y `escape` siguen siendo atajos. `?` abre la ayuda
 * únicamente con el input vacío (toda pregunta en español lleva `?`), y `q`
 * nunca sale: se comería la primera letra de «qué», «cuándo» o «quién».
 */
export function keyRoutesToInput(name: string, hasInput: boolean, helpOpen: boolean): boolean {
  if (helpOpen) return false
  if (!hasInput) return false
  return name !== "tab" && name !== "escape"
}

export function chips(encargo: Encargo): string[] {
  return [encargo.curso, encargo.asignatura, encargo.tema, encargo.oa, encargo.duracion, encargo.tipo]
    .map((item) => (item ?? "").trim())
    .filter(Boolean)
}

export function showChips(state: AppState): boolean {
  if (state.screen === "home" && !state.started) return false
  return chips(state.encargo).length > 0
}

/**
 * Texto del flujo viejo (plan a/e/x, puerta s/n/b/c, rumbos, clarificación
 * numerada). No debe aparecer en ninguna superficie de la TUI.
 */
export function hasKeyLegend(text: string): boolean {
  const t = text.toLowerCase()
  return (
    /\ba\s*aprobar\b/.test(t) ||
    /\be\s*supuesto\b/.test(t) ||
    /\bx\s*cancelar\b/.test(t) ||
    /\bs\s*sí\b/.test(t) ||
    /\bn\s*no\b/.test(t) ||
    /\bb\s*borrador\b/.test(t) ||
    /\bc\s*corregir\b/.test(t) ||
    /\[\s*[asebc]\s*\]/.test(t) ||
    /\brumbo/.test(t) ||
    /\b1[–-]4\b/.test(t) ||
    /\bclarificaci[oó]n\b/.test(t) ||
    /\bpuerta\b/.test(t) ||
    /\bplan tipado\b/.test(t)
  )
}

export function footerFor(state: AppState): string {
  if (state.help) return "PgUp/PgDn  esc cierra"
  // Las acciones de decisión viven en la franja: el pie queda callado.
  if (decisionStrip(state)) return ""
  if (state.screen === "home") return "Enter envía  ·  ? ayuda  ·  /salir"
  return "/export  ·  Tab  ·  PgUp/PgDn hilo  ·  ? ayuda"
}

export function helpFor(state: AppState): string {
  if (state.phase === "error") {
    return `Error

${state.lastError}

r o /retry  reintenta el último mensaje
Escribe abajo para seguir conversando.

Offline se etiqueta tero-offline (no es Bedrock).

? cierra`
  }
  if (state.cardStatus === "pendiente" && state.card) {
    return `Propuesta pendiente

y  aprobar → el host escribe en derivados/
n  descartar → no se escribe nada
También puedes escribir tu decisión o tus cambios abajo.

[ ] recorre la evidencia
✓ la cita está en el archivo
? es parafraseo del agente
Los avisos no bloquean la aprobación: tú decides.

? cierra`
  }
  if (state.screen === "home") {
    return `tero — conversación

Escribe abajo: «Pregunta, explora o crea…»
El agente entiende la intención y actúa:
  responde · crea material · edita o adapta

Cuando propone un archivo verás la vista previa.
  y  aprobar y escribir en derivados/
  n  descartar (no escribe nada)
O responde con tus palabras: el host clasifica.

Contexto del encargo
  /curso  /asignatura  /oa  /tipo  /tema  /duracion
  /export [md|latex|docx]   /retry   /salir

? cierra`
  }
  return `tero — el agente propone, tú decides

Escribe en lenguaje natural: pregunta, crea o adapta.
Verás qué hará y la vista previa antes de que escriba nada.

Teclas
  y / n decisión    [ ] evidencia    Tab paneles
  PgUp/PgDn hilo    ? ayuda         /salir

Comandos
  /curso /asignatura /oa /tipo /tema /duracion
  /export [md|docx|latex]   /retry

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
export const HELP_TEXT = helpFor(
  initialState({
    curso: "",
    asignatura: "",
    oa: "",
    duracion: "",
    tipo: null,
  }),
)
