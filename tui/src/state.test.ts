import { describe, expect, test } from "bun:test"
import { applyHostEvent, chips, footerFor, handleCommand, handleHotkey, initialState } from "./state.ts"

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
  test("footer changes at the gate", () => {
    const state = { ...initialState(encargo), phase: "esperando_criterio" as const }
    expect(footerFor(state)).toContain("s sí")
    expect(footerFor(state)).toContain("c corregir")
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
        evidencias: [{ path: "fuentes/a.md", snippet: "OA 4", seccion: "OA" }],
        warnings: [{ code: "thin_skeleton", message: "corto", blocking: false }],
      },
    })
    expect(state.phase).toBe("esperando_criterio")
    expect(state.evidence).toHaveLength(1)
    expect(state.warnings[0]?.code).toBe("thin_skeleton")
    expect(state.statusLine).toContain("s sí")
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
  test("a approves plan", () => {
    const state = { ...initialState(encargo), phase: "esperando_plan" as const }
    const action = handleHotkey(state, "a")
    expect(action.kind).toBe("send")
    if (action.kind === "send") expect(action.message.type).toBe("plan.decide")
  })
})

describe("commands", () => {
  test("prompt becomes JSONL prompt", () => {
    const action = handleCommand(initialState(encargo), "Prepara una guía")
    expect(action.kind).toBe("send")
    if (action.kind === "send") expect(action.message).toEqual({ type: "prompt", text: "Prepara una guía" })
  })
  test("/oa updates encargo", () => {
    const action = handleCommand(initialState(encargo), "/oa OA 6")
    expect(action.kind).toBe("send")
    if (action.kind === "send" && action.message.type === "encargo.update") {
      expect(action.message.encargo.oa).toBe("OA 6")
    }
  })
})
