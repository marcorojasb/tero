import { describe, expect, test } from "bun:test"
import {
  applyHostEvent,
  chips,
  footerFor,
  handleCommand,
  handleHotkey,
  helpFor,
  initialState,
  showChips,
} from "./state.ts"

const encargo = {
  curso: "4° básico",
  asignatura: "Lenguaje",
  oa: "OA 4",
  duracion: "45 min",
  tipo: "planificacion",
}

describe("chips y pie", () => {
  test("chips in Spanish encargo", () => {
    expect(chips(encargo)).toEqual(["4° básico", "Lenguaje", "OA 4", "45 min", "planificacion"])
  })
  test("home hides chips until started", () => {
    const home = initialState({
      curso: "",
      asignatura: "",
      oa: "",
      duracion: "",
      tipo: null,
    })
    expect(home.screen).toBe("home")
    expect(showChips(home)).toBe(false)
  })
  test("footer stays quiet at the gate (actions live in gate strip)", () => {
    const state = { ...initialState(encargo), phase: "esperando_criterio" as const, screen: "workspace" as const }
    expect(footerFor(state)).toContain("?")
    expect(footerFor(state)).not.toMatch(/s sí/)
    expect(footerFor(state)).not.toMatch(/c corregir/)
  })
})

describe("host events", () => {
  test("proposal fills evidence and waits for teacher", () => {
    let state = initialState(encargo)
    state = applyHostEvent(state, { type: "ready", mode: "offline", model: "tero-offline" })
    state = applyHostEvent(state, {
      type: "proposal",
      artifact: {
        titulo: "Plan",
        tipo_label: "planificación",
        cuerpo_markdown: "## Objetivo\n...",
        evidencias: [{ path: "fuentes/a.md", snippet: "OA 4", seccion: "OA", verified: true }],
        warnings: [{ code: "thin_skeleton", message: "corto", blocking: false }],
      },
    })
    expect(state.phase).toBe("esperando_criterio")
    expect(state.evidence).toHaveLength(1)
    expect(state.warnings[0]?.code).toBe("thin_skeleton")
    expect(state.statusLine).toMatch(/tu turno|sí/)
  })

  test("plan with questions enters clarification", () => {
    let state = initialState(encargo)
    state = applyHostEvent(state, {
      type: "plan",
      plan: {
        objetivo: "Guía de fracciones",
        tipo: "guia",
        oa: "OA 4",
        duracion: "45 min",
        notas: "",
        titulo: "Plan de guía",
        meta: "1 entregable",
        resultado_previsto: ["Guía de práctica"],
        decisiones: { curso: "6° básico", asignatura: "Matemática", tema: "fracciones" },
        questions: [
          {
            id: "q1",
            prompt: "¿Qué énfasis?",
            options: [
              { id: "1", label: "Representación", suggested: true },
              { id: "2", label: "Cálculo" },
            ],
          },
        ],
        supuestos: [{ id: "s1", text: "Sesión breve" }],
        como_abordare: [{ titulo: "Ítems", detalle: "SM + desarrollo" }],
      },
    })
    expect(state.phase).toBe("esperando_clarificacion")
    expect(state.question?.prompt).toContain("énfasis")
    expect(state.planPinned).toBe(true)
  })

  test("plan_cancelled clears and returns home", () => {
    let state = {
      ...initialState(encargo),
      screen: "workspace" as const,
      proposal: "viejo",
      plan: {
        objetivo: "x",
        tipo: "guia",
        oa: "",
        duracion: "",
        notas: "",
      },
    }
    state = applyHostEvent(state, { type: "plan_cancelled" })
    expect(state.screen).toBe("home")
    expect(state.proposal).toBe("")
    expect(state.plan).toBeNull()
  })

  test("proposal_cleared archives stale draft", () => {
    let state = {
      ...initialState(encargo),
      proposal: "stale",
      evidence: [{ path: "a.md", snippet: "x", seccion: "" }],
    }
    state = applyHostEvent(state, { type: "proposal_cleared", reason: "nuevo_encargo" })
    expect(state.proposal).toBe("")
    expect(state.evidence).toHaveLength(0)
    expect(state.warnings.some((w) => w.code === "stale_proposal")).toBe(true)
  })
})

describe("hotkeys HITL", () => {
  test("s sends accept", () => {
    const state = { ...initialState(encargo), phase: "esperando_criterio" as const }
    const action = handleHotkey(state, "s")
    expect(action.kind).toBe("send")
    if (action.kind === "send") expect(action.message).toEqual({ type: "gate", decision: "s" })
  })
  test("c waits for critique instead of sending immediately", () => {
    const state = { ...initialState(encargo), phase: "esperando_criterio" as const }
    const action = handleHotkey(state, "c")
    expect(action.kind).toBe("state")
    if (action.kind === "state") expect(action.state.uiMode).toBe("critique")
  })
  test("a approves plan and sends local edits", () => {
    const plan = {
      objetivo: "Leer con evidencia",
      tipo: "planificacion",
      oa: "OA 6",
      duracion: "45 min",
      notas: "",
    }
    const state = { ...initialState(encargo), phase: "esperando_plan" as const, plan }
    const action = handleHotkey(state, "a")
    expect(action.kind).toBe("send")
    if (action.kind === "send") {
      expect(action.message).toEqual({ type: "plan.decide", decision: "approve", plan })
    }
  })
  test("[ ] with one evidence is a no-op message", () => {
    const state = {
      ...initialState(encargo),
      evidence: [{ path: "a.md", snippet: "uno", seccion: "OA", verified: true }],
      evidenceIndex: 0,
    }
    const next = handleHotkey(state, "]")
    expect(next.kind).toBe("state")
    if (next.kind === "state") {
      expect(next.state.evidenceIndex).toBe(0)
      expect(next.state.statusLine).toContain("1/1")
    }
  })
  test("[ ] cycles evidence when multiple", () => {
    const evidence = [
      { path: "a.md", snippet: "uno", seccion: "OA", verified: true },
      { path: "b.md", snippet: "dos", seccion: "cierre", verified: false },
    ]
    const state = { ...initialState(encargo), evidence, evidenceIndex: 0 }
    const next = handleHotkey(state, "]")
    expect(next.kind).toBe("state")
    if (next.kind === "state") {
      expect(next.state.evidenceIndex).toBe(1)
      expect(next.state.focusPanel).toBe("evidence")
    }
  })
  test("tab cycles focus panels", () => {
    const state = initialState(encargo)
    expect(state.focusPanel).toBe("proposal")
    const next = handleHotkey(state, "tab")
    expect(next.kind).toBe("state")
    if (next.kind === "state") expect(next.state.focusPanel).toBe("evidence")
  })
  test("home rumbo 2 sends rumbo crear", () => {
    const state = initialState({
      curso: "",
      asignatura: "",
      oa: "",
      duracion: "",
      tipo: null,
    })
    const action = handleHotkey(state, "2")
    expect(action.kind).toBe("send")
    if (action.kind === "send") expect(action.message).toEqual({ type: "rumbo", rumbo: "crear" })
  })
  test("clarify option 1 answers plan", () => {
    const state = {
      ...initialState(encargo),
      phase: "esperando_clarificacion" as const,
      uiMode: "clarify" as const,
      question: {
        id: "q1",
        prompt: "¿Énfasis?",
        options: [{ id: "1", label: "A", suggested: true }],
      },
    }
    const action = handleHotkey(state, "1")
    expect(action.kind).toBe("send")
    if (action.kind === "send" && action.message.type === "plan.answer") {
      expect(action.message.option_id).toBe("1")
    }
  })
})

describe("commands", () => {
  test("empty enter does not send", () => {
    const action = handleCommand(initialState(encargo), "   ")
    expect(action.kind).toBe("state")
    if (action.kind === "state") expect(action.state.statusLine).toContain("vacío")
  })
  test("prompt becomes JSONL prompt and clears stale proposal", () => {
    const state = { ...initialState(encargo), proposal: "viejo", screen: "workspace" as const }
    const action = handleCommand(state, "Prepara una guía")
    expect(action.kind).toBe("send")
    if (action.kind === "send") {
      expect(action.message).toEqual({ type: "prompt", text: "Prepara una guía" })
      expect(action.state.proposal).toBe("")
      expect(action.state.thinking).toBe(true)
    }
  })
  test("/oa updates encargo and clears proposal", () => {
    const state = { ...initialState(encargo), proposal: "x" }
    const action = handleCommand(state, "/oa OA 6")
    expect(action.kind).toBe("send")
    if (action.kind === "send" && action.message.type === "encargo.update") {
      expect(action.message.encargo.oa).toBe("OA 6")
      expect(action.state.proposal).toBe("")
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
  test("/objetivo edits the pending plan locally", () => {
    const state = {
      ...initialState(encargo),
      phase: "esperando_plan" as const,
      plan: {
        objetivo: "viejo",
        tipo: "planificacion",
        oa: "OA 4",
        duracion: "45 min",
        notas: "",
      },
    }
    const action = handleCommand(state, "/objetivo Distinguir explícito e implícito")
    expect(action.kind).toBe("state")
    if (action.kind === "state") {
      expect(action.state.plan?.objetivo).toBe("Distinguir explícito e implícito")
    }
  })
  test("help is contextual by phase", () => {
    const home = helpFor(initialState({ curso: "", asignatura: "", oa: "", duracion: "", tipo: null }))
    expect(home).toContain("Rumbos")
    const gate = helpFor({
      ...initialState(encargo),
      phase: "esperando_criterio",
      screen: "workspace",
    })
    expect(gate).toContain("derivados")
    expect(gate).toContain("corregir")
  })
})
