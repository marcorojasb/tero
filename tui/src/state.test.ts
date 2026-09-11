import { describe, expect, test } from "bun:test"
import {
  allWarnings,
  applyHostEvent,
  chips,
  decisionStrip,
  footerFor,
  hasKeyLegend,
  handleCommand,
  handleHotkey,
  helpFor,
  initialState,
  keyRoutesToInput,
  showChips,
  type AppState,
} from "./state.ts"
import type { Propuesta } from "./protocol.ts"

const encargo = {
  curso: "4° básico",
  asignatura: "Lenguaje",
  oa: "OA 4",
  duracion: "45 min",
  tipo: "planificacion",
}

const propuesta: Propuesta = {
  accion: "crear",
  tipo: "evaluacion",
  tipo_label: "evaluación",
  titulo: "Evaluación de comprensión lectora — El cóndor y el huemul",
  resumen: "Prueba de 45 min con ítems de selección múltiple y V/F.",
  vista_previa: "---\ntipo: evaluacion\n---\n\n## Ítems\n1. ¿Quién ve el mar?",
  origen: null,
  cambios: [],
  notas_nee: [],
  evidencias: [
    { path: "fuentes/cuento.md", snippet: "Yo veo el mar desde aquí", seccion: "desarrollo", verified: true },
    { path: "fuentes/bases-oa.md", snippet: "Extraer información", seccion: "OA 4", verified: false },
  ],
  warnings: [{ code: "thin_evidence", message: "Menos de dos fuentes citadas.", blocking: false }],
}

function withCard(state: AppState, card: Propuesta = propuesta): AppState {
  return {
    ...state,
    screen: "conversacion",
    started: true,
    card,
    cardId: "t1",
    cardStatus: "pendiente",
    phase: "esperando_aprobacion",
  }
}

describe("home conversacional", () => {
  test("arranca en home, sin rumbos y con línea de entrada", () => {
    const home = initialState({ curso: "", asignatura: "", oa: "", duracion: "", tipo: null })
    expect(home.screen).toBe("home")
    expect(home.phase).toBe("idle")
    expect(home.messages).toHaveLength(0)
    expect(home.card).toBeNull()
    expect(hasKeyLegend(home.statusLine)).toBe(false)
    expect(showChips(home)).toBe(false)
  })

  test("un mensaje en lenguaje natural se manda como prompt y abre el hilo", () => {
    const home = initialState({ curso: "", asignatura: "", oa: "", duracion: "", tipo: null })
    const action = handleCommand(home, "Prepara una guía de fracciones para 6° básico")
    expect(action.kind).toBe("send")
    if (action.kind !== "send") return
    expect(action.message).toEqual({
      type: "prompt",
      text: "Prepara una guía de fracciones para 6° básico",
    })
    expect(action.state.screen).toBe("conversacion")
    expect(action.state.started).toBe(true)
    expect(action.state.phase).toBe("pensando")
    expect(action.state.thinking).toBe(true)
    expect(action.state.messages).toHaveLength(1)
    expect(action.state.messages[0]?.role).toBe("persona")
    expect(action.state.messages[0]?.text).toContain("guía de fracciones")
  })

  test("un saludo también es conversación (el host responde)", () => {
    const action = handleCommand(initialState(encargo), "hola")
    expect(action.kind).toBe("send")
    if (action.kind === "send") expect(action.message).toEqual({ type: "prompt", text: "hola" })
  })

  test("enter vacío no envía", () => {
    const action = handleCommand(initialState(encargo), "   ")
    expect(action.kind).toBe("state")
    if (action.kind === "state") expect(action.state.statusLine).toContain("vacío")
  })
})

describe("hilo conversacional", () => {
  test("delta acumula streaming y respuesta cierra el turno en el hilo", () => {
    let state = initialState(encargo)
    state = applyHostEvent(state, { type: "status", phase: "pensando", detail: "leyendo fuentes" })
    state = applyHostEvent(state, { type: "delta", text: "Necesito el curso " })
    state = applyHostEvent(state, { type: "delta", text: "y el OA." })
    expect(state.streaming).toBe("Necesito el curso y el OA.")
    expect(state.thinking).toBe(true)

    state = applyHostEvent(state, {
      type: "respuesta",
      id: "t1",
      texto: "¿Para qué curso y qué OA?",
    })
    expect(state.streaming).toBe("")
    expect(state.thinking).toBe(false)
    expect(state.phase).toBe("idle")
    expect(state.messages).toHaveLength(1)
    expect(state.messages[0]).toEqual({ id: "t1", role: "agente", text: "¿Para qué curso y qué OA?" })
  })

  test("una pregunta del agente es una respuesta normal y se contesta escribiendo", () => {
    let state = initialState(encargo)
    state = applyHostEvent(state, { type: "respuesta", id: "a1", texto: "¿Qué curso?" })
    const action = handleCommand(state, "4° básico, Lenguaje")
    expect(action.kind).toBe("send")
    if (action.kind === "send") {
      expect(action.message).toEqual({ type: "prompt", text: "4° básico, Lenguaje" })
      expect(action.state.messages.map((m) => m.role)).toEqual(["agente", "persona"])
    }
  })
})

describe("tarjeta de propuesta", () => {
  test("propuesta crea la tarjeta y espera aprobación", () => {
    let state = initialState(encargo)
    state = applyHostEvent(state, { type: "propuesta", id: "t7", propuesta })
    expect(state.phase).toBe("esperando_aprobacion")
    expect(state.cardStatus).toBe("pendiente")
    expect(state.card?.accion).toBe("crear")
    expect(state.card?.tipo_label).toBe("evaluación")
    expect(state.card?.titulo).toContain("El cóndor y el huemul")
    expect(state.card?.resumen).toContain("selección múltiple")
    expect(state.card?.vista_previa).toContain("tipo: evaluacion")
    expect(state.card?.evidencias).toHaveLength(2)
    expect(state.card?.evidencias[0]?.verified).toBe(true)
    expect(state.card?.evidencias[1]?.verified).toBe(false)
    expect(state.card?.warnings[0]?.code).toBe("thin_evidence")
    expect(state.card?.warnings[0]?.blocking).toBe(false)
    expect(state.statusLine).toContain("y aprueba")
  })

  test("propuesta de adaptar trae origen, cambios y notas NEE", () => {
    const adaptar: Propuesta = {
      ...propuesta,
      accion: "adaptar",
      origen: "derivados/20260101-120000-evaluacion.md",
      cambios: ["Agrega pauta de corrección", "Sube la exigencia del ítem 3"],
      notas_nee: ["Tiempo extendido", "Enunciados en dos pasos"],
    }
    const state = applyHostEvent(initialState(encargo), { type: "propuesta", id: "t8", propuesta: adaptar })
    expect(state.card?.accion).toBe("adaptar")
    expect(state.card?.origen).toContain("derivados/")
    expect(state.card?.cambios).toHaveLength(2)
    expect(state.card?.notas_nee).toEqual(["Tiempo extendido", "Enunciados en dos pasos"])
  })

  test("los avisos de la propuesta nunca bloquean y se suman a los del host", () => {
    let state = applyHostEvent(initialState(encargo), { type: "propuesta", id: "t9", propuesta })
    state = applyHostEvent(state, {
      type: "warning",
      warning: { code: "fuente_cambiada", message: "Cambió un original.", blocking: true },
    })
    const rows = allWarnings(state)
    expect(rows.map((w) => w.code)).toEqual(["fuente_cambiada", "thin_evidence"])
    expect(rows.every((w) => w.blocking === false)).toBe(true)
  })

  test("la propuesta sigue pendiente si el host la trató como conversación", () => {
    let state = applyHostEvent(initialState(encargo), { type: "propuesta", id: "t10", propuesta })
    state = applyHostEvent(state, { type: "respuesta", id: "t11", texto: "¿Te refieres a la prueba?" })
    expect(state.cardStatus).toBe("pendiente")
    const action = handleHotkey(state, "y")
    expect(action.kind).toBe("send")
    if (action.kind === "send") {
      expect(action.message).toEqual({ type: "aprobar", decision: "aprobar" })
    }
  })
})

describe("decisión", () => {
  test("y aprueba la propuesta pendiente", () => {
    const state = withCard(initialState(encargo))
    const action = handleHotkey(state, "y")
    expect(action.kind).toBe("send")
    if (action.kind === "send") {
      expect(action.message).toEqual({ type: "aprobar", decision: "aprobar" })
    }
  })

  test("n descarta la propuesta pendiente", () => {
    const state = withCard(initialState(encargo))
    const action = handleHotkey(state, "n")
    expect(action.kind).toBe("send")
    if (action.kind === "send") {
      expect(action.message).toEqual({ type: "aprobar", decision: "descartar" })
    }
  })

  test("sin propuesta pendiente y/n no deciden nada", () => {
    const state = initialState(encargo)
    expect(handleHotkey(state, "y").kind).toBe("none")
    expect(handleHotkey(state, "n").kind).toBe("none")
  })

  test("aprobacion hace eco y descartar no escribe", () => {
    let state = withCard(initialState(encargo))
    state = applyHostEvent(state, { type: "aprobacion", id: "t1", decision: "aprobar", note: "" })
    expect(state.cardStatus).toBe("aprobado")
    expect(state.messages.at(-1)?.text).toContain("aprobado")

    let discarded = withCard(initialState(encargo))
    discarded = applyHostEvent(discarded, { type: "aprobacion", id: "t1", decision: "descartar", note: "" })
    expect(discarded.cardStatus).toBe("descartado")
    expect(discarded.phase).toBe("idle")
    expect(discarded.messages.at(-1)?.text).toContain("descartado")
    expect(decisionStrip(discarded)).toContain("no se escribió nada")
  })

  test("escribir la decisión en el hilo va como prompt (el host clasifica)", () => {
    const state = withCard(initialState(encargo))
    const action = handleCommand(state, "dale, adelante")
    expect(action.kind).toBe("send")
    if (action.kind === "send") {
      expect(action.message).toEqual({ type: "prompt", text: "dale, adelante" })
      expect(action.state.cardStatus).toBe("pendiente")
    }
  })

  test("escribir un cambio en el hilo tampoco bota la propuesta", () => {
    const state = withCard(initialState(encargo))
    const action = handleCommand(state, "mejor cambia el título")
    expect(action.kind).toBe("send")
    if (action.kind === "send") {
      expect(action.message).toEqual({ type: "prompt", text: "mejor cambia el título" })
      expect(action.state.card).not.toBeNull()
      expect(action.state.cardStatus).toBe("pendiente")
    }
  })
})

describe("resultado y error", () => {
  test("escrito muestra la ruta en derivados con la acción", () => {
    let state = withCard(initialState(encargo))
    state = applyHostEvent(state, {
      type: "escrito",
      id: "t1",
      path: "derivados/20260101-120000-evaluacion-condor.md",
      accion: "crear",
    })
    expect(state.phase).toBe("listo")
    expect(state.cardStatus).toBe("escrito")
    expect(state.writtenPath).toContain("derivados/")
    expect(state.statusLine).toContain("derivados/")
    expect(state.statusLine).toContain("crear")
    const note = state.messages.at(-1)
    expect(note?.role).toBe("host")
    expect(note?.path).toContain("derivados/")
    expect(decisionStrip(state)).toContain("derivados/")
  })

  test("un error deja fase error y r reintenta", () => {
    let state = initialState(encargo)
    state = applyHostEvent(state, {
      type: "error",
      message: "No pude leer fuentes/cuento.md",
      code: "read_failed",
      retryable: true,
    })
    expect(state.phase).toBe("error")
    expect(state.retryable).toBe(true)
    expect(state.lastError).toContain("cuento.md")

    const action = handleHotkey(state, "r")
    expect(action.kind).toBe("send")
    if (action.kind === "send") expect(action.message).toEqual({ type: "retry" })
  })

  test("un error no retirable no responde a r", () => {
    let state = applyHostEvent(initialState(encargo), {
      type: "error",
      message: "Carpeta inexistente",
      code: "carpeta",
      retryable: false,
    })
    expect(handleHotkey(state, "r").kind).toBe("none")
  })
})

describe("teclado y ayuda", () => {
  test("el ? escrito llega al mensaje y no abre la ayuda", () => {
    // Con texto en el input, el teclado es de la persona: toda pregunta en
    // español termina en `?` y no puede abrir la ayuda.
    expect(keyRoutesToInput("?", true, false)).toBe(true)
    expect(keyRoutesToInput("a", true, false)).toBe(true)
    expect(keyRoutesToInput("?", false, false)).toBe(false)
    expect(keyRoutesToInput("a", false, false)).toBe(false)
    // Tab y escape siguen siendo atajos aunque haya texto.
    expect(keyRoutesToInput("tab", true, false)).toBe(false)
    expect(keyRoutesToInput("escape", true, false)).toBe(false)
    // Con la ayuda abierta, el input no recibe nada.
    expect(keyRoutesToInput("?", true, true)).toBe(false)
  })

  test("? con el input vacío sí abre la ayuda", () => {
    const state = initialState(encargo)
    expect(keyRoutesToInput("?", false, state.help)).toBe(false)
    const action = handleHotkey(state, "?")
    expect(action.kind).toBe("state")
    if (action.kind === "state") expect(action.state.help).toBe(true)
  })

  test("una pregunta con ? en medio y al final se envía completa", () => {
    const withFinal = handleCommand(initialState(encargo), "cuantos OA hay?")
    expect(withFinal.kind).toBe("send")
    if (withFinal.kind === "send") {
      expect(withFinal.message).toEqual({ type: "prompt", text: "cuantos OA hay?" })
      expect(withFinal.state.messages[0]?.text).toBe("cuantos OA hay?")
      expect(withFinal.state.help).toBe(false)
    }
    const inMiddle = handleCommand(initialState(encargo), "ab?cd")
    expect(inMiddle.kind).toBe("send")
    if (inMiddle.kind === "send") {
      expect(inMiddle.message).toEqual({ type: "prompt", text: "ab?cd" })
      expect(inMiddle.state.messages[0]?.text).toBe("ab?cd")
    }
  })

  test("la franja de decisión no se usa para la ayuda", () => {
    const helpState = { ...initialState(encargo), help: true }
    // La ayuda vive en su panel: no inventa franja de decisión.
    expect(decisionStrip(helpState)).toBe("")
    expect(decisionStrip(helpState)).not.toContain("PgUp/PgDn")
    expect(footerFor(helpState)).toContain("PgUp/PgDn")
    // Con propuesta pendiente la franja es la de aprobación; la shell la
    // esconde mientras la ayuda está abierta (ver shell.test.ts).
    const pendingHelp = { ...withCard(initialState(encargo)), help: true }
    expect(decisionStrip(pendingHelp)).toContain("¿escribo el archivo?")
    expect(decisionStrip({ ...pendingHelp, help: false })).toBe(decisionStrip(pendingHelp))
  })
})

describe("contexto y comandos", () => {
  test("chips en español sin rumbo", () => {
    expect(chips(encargo)).toEqual(["4° básico", "Lenguaje", "OA 4", "45 min", "planificacion"])
  })

  test("los comandos de contexto solo actualizan y no reinician el hilo", () => {
    let state = withCard(initialState(encargo))
    state = { ...state, messages: [{ id: "m1", role: "persona", text: "prepara una prueba" }] }
    const action = handleCommand(state, "/oa OA 6")
    expect(action.kind).toBe("send")
    if (action.kind === "send" && action.message.type === "encargo.update") {
      expect(action.message.encargo.oa).toBe("OA 6")
      expect(action.state.messages).toHaveLength(1)
      expect(action.state.cardStatus).toBe("pendiente")
    }
  })

  test("/oa matches catalog option id", () => {
    const state = {
      ...initialState(encargo),
      oaOptions: [
        {
          id: "LEN-4B-OA04",
          curso: "4b",
          asignatura: "lenguaje",
          codigo: "OA 4",
          texto_corto: "Extraer info",
        },
      ],
    }
    const action = handleCommand(state, "/oa LEN-4B-OA04")
    expect(action.kind).toBe("send")
    if (action.kind === "send" && action.message.type === "encargo.update") {
      expect(action.message.encargo.oa).toContain("LEN-4B-OA04")
    }
  })

  test("/export latex sends format latex", () => {
    const action = handleCommand(initialState(encargo), "/export latex")
    expect(action.kind).toBe("send")
    if (action.kind === "send" && action.message.type === "export") {
      expect(action.message.format).toBe("latex")
    }
  })

  test("exported deja la ruta del último artefacto", () => {
    let state = withCard(initialState(encargo))
    state = applyHostEvent(state, {
      type: "exported",
      path: "derivados/20260101-120000-evaluacion.tex",
      format: "latex",
      source_kind: "derivado",
      source_path: "derivados/20260101-120000-evaluacion.md",
    })
    expect(state.lastExport).toContain(".tex")
    expect(state.statusLine).toContain("latex")
  })

  test("oa_options event fills hint", () => {
    let state = initialState(encargo)
    state = applyHostEvent(state, {
      type: "oa_options",
      curso: "4° básico",
      asignatura: "Lenguaje",
      oas: [
        {
          id: "LEN-4B-OA04",
          curso: "4b",
          asignatura: "lenguaje",
          codigo: "OA 4",
          texto_corto: "Extraer",
        },
      ],
    })
    expect(state.oaOptions).toHaveLength(1)
    expect(state.oaHint).toContain("OA")
  })

  test("un evento del flujo viejo no rompe el estado", () => {
    const state = initialState(encargo)
    const next = applyHostEvent(state, {
      type: "plan",
      plan: { objetivo: "viejo", tipo: "guia", oa: "", duracion: "", notas: "" },
    })
    expect(next.phase).toBe("idle")
    expect(next.card).toBeNull()
  })
})

describe("evidencia y foco", () => {
  test("[ ] recorre la evidencia de la propuesta", () => {
    const state = withCard(initialState(encargo))
    const next = handleHotkey(state, "]")
    expect(next.kind).toBe("state")
    if (next.kind === "state") {
      expect(next.state.evidenceIndex).toBe(1)
      expect(next.state.focusPanel).toBe("evidencia")
    }
  })

  test("[ ] con una sola evidencia no cambia de índice", () => {
    const state = withCard(initialState(encargo), {
      ...propuesta,
      evidencias: [propuesta.evidencias[0]!],
    })
    const next = handleHotkey(state, "]")
    expect(next.kind).toBe("state")
    if (next.kind === "state") {
      expect(next.state.evidenceIndex).toBe(0)
      expect(next.state.statusLine).toContain("1/1")
    }
  })

  test("[ ] sin propuesta avisa y no inventa evidencia", () => {
    const next = handleHotkey(initialState(encargo), "]")
    expect(next.kind).toBe("state")
    if (next.kind === "state") expect(next.state.statusLine).toContain("Sin evidencia")
  })

  test("tab cicla los paneles del flujo conversacional", () => {
    const state = initialState(encargo)
    expect(state.focusPanel).toBe("propuesta")
    const a = handleHotkey(state, "tab")
    expect(a.kind).toBe("state")
    if (a.kind !== "state") return
    expect(a.state.focusPanel).toBe("evidencia")
    const b = handleHotkey(a.state, "tab")
    expect(b.kind).toBe("state")
    if (b.kind === "state") expect(b.state.focusPanel).toBe("hilo")
  })

  test("? abre la ayuda y esc la cierra", () => {
    const opened = handleHotkey(initialState(encargo), "?")
    expect(opened.kind).toBe("state")
    if (opened.kind !== "state") return
    expect(opened.state.help).toBe(true)
    const closed = handleHotkey(opened.state, "escape")
    if (closed.kind === "state") expect(closed.state.help).toBe(false)
  })
})

describe("chrome sin el flujo viejo", () => {
  test("ninguna superficie menciona rumbos, plan a/e/x ni la puerta s/n/b/c", () => {
    const surfaces: string[] = []
    const base = withCard(initialState(encargo))
    surfaces.push(decisionStrip(base), footerFor(base))
    surfaces.push(decisionStrip(initialState(encargo)), footerFor(initialState(encargo)))
    const err = applyHostEvent(base, {
      type: "error",
      message: "falló",
      code: "x",
      retryable: true,
    })
    surfaces.push(decisionStrip(err), footerFor(err))
    for (const state of [initialState(encargo), base, err]) {
      surfaces.push(helpFor(state))
    }
    for (const text of surfaces) {
      expect(hasKeyLegend(text)).toBe(false)
      expect(text).not.toContain("rumbo")
      expect(text).not.toContain("Puerta")
      expect(text).not.toContain("puerta")
      expect(text).not.toContain("Clarificación")
      expect(text).not.toContain("borrador")
    }
  })

  test("el pie no repite los atajos cuando hay franja de decisión", () => {
    const state = withCard(initialState(encargo))
    expect(decisionStrip(state).length).toBeGreaterThan(0)
    expect(footerFor(state)).toBe("")
  })

  test("la ayuda es contextual", () => {
    const home = helpFor(initialState({ curso: "", asignatura: "", oa: "", duracion: "", tipo: null }))
    expect(home).toContain("Pregunta, explora o crea")
    expect(home).toContain("y  aprobar")
    const awaiting = helpFor(withCard(initialState(encargo)))
    expect(awaiting).toContain("derivados")
    expect(awaiting).toContain("descartar")
    const error = helpFor(
      applyHostEvent(initialState(encargo), {
        type: "error",
        message: "no pude leer",
        code: "read",
        retryable: true,
      }),
    )
    expect(error).toContain("no pude leer")
    expect(error).toContain("/retry")
  })
})

  test("la ayuda nombra la tesis y no el flujo retirado", () => {
    const vacio = { curso: "", asignatura: "", oa: "", duracion: "", tipo: null }
    const home = helpFor(initialState(vacio))
    expect(home).toContain("responde · crea material · edita o adapta")
    expect(home).toContain("? cierra")

    const enHilo = applyHostEvent(initialState(vacio), {
      type: "respuesta",
      id: "t1",
      texto: "Listo.",
    })
    const hilo = helpFor(enHilo)
    expect(hilo).toContain("el agente propone, tú decides")

    for (const texto of [home, hilo]) {
      expect(texto).not.toMatch(/el docente decide|plan a\/e\/x|s\/n\/b\/c|rumbo|borrador \/|puerta/i)
    }
  })
