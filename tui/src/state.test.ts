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
  test("[ ] cycles evidence and focuses the panel", () => {
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
    const wrap = handleHotkey({ ...state, evidenceIndex: 1 }, "]")
    if (wrap.kind === "state") expect(wrap.state.evidenceIndex).toBe(0)
  })
  test("tab cycles focus panels", () => {
    const state = initialState(encargo)
    expect(state.focusPanel).toBe("proposal")
    const next = handleHotkey(state, "tab")
    expect(next.kind).toBe("state")
    if (next.kind === "state") expect(next.state.focusPanel).toBe("evidence")
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
})
