import { describe, expect, test } from "bun:test"
import { createTestRenderer } from "@opentui/core/testing"
import { initialState } from "./state.ts"
import { mountShell } from "./shell.ts"

describe("shell frames", () => {
  test("Spanish empty state and chips render", async () => {
    const setup = await createTestRenderer({ width: 120, height: 32 })
    try {
      const shell = mountShell(setup.renderer, () => {})
      const state = initialState({
        curso: "4° básico",
        asignatura: "Lenguaje",
        oa: "OA 4",
        duracion: "45 min",
        tipo: "planificacion",
      })
      shell.sync(state)
      await setup.renderOnce()
      const frame = setup.captureCharFrame()
      expect(frame).toContain("tero")
      expect(frame).toContain("básico")
      expect(frame).toContain("OA 4")
      expect(frame).toContain("El agente prepara")
      expect(frame).toContain("evidencia")
      expect(frame).toContain("sesión")
      expect(frame).toContain("Enter envía")
    } finally {
      setup.renderer.destroy()
    }
  })
})
