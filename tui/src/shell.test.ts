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
      expect(frame).toContain("propuesta")
    } finally {
      setup.renderer.destroy()
    }
  })

  test("gate strip and selected evidence render", async () => {
    const setup = await createTestRenderer({ width: 140, height: 36 })
    try {
      const shell = mountShell(setup.renderer, () => {})
      const state = {
        ...initialState({
          curso: "4° básico",
          asignatura: "Lenguaje",
          oa: "OA 4",
          duracion: "45 min",
          tipo: "planificacion",
        }),
        phase: "esperando_criterio" as const,
        proposal: "## Objetivo\nLeer con evidencia.",
        proposalTitle: "Plan",
        evidence: [
          { path: "fuentes/a.md", snippet: "OA 4 extraer información", seccion: "OA", verified: true },
          { path: "fuentes/b.md", snippet: "El huemul preguntó", seccion: "desarrollo", verified: false },
        ],
        evidenceIndex: 0,
        focusPanel: "evidence" as const,
        plan: {
          objetivo: "Leer con evidencia",
          tipo: "planificacion",
          tipo_label: "planificación",
          oa: "OA 4",
          duracion: "45 min",
          notas: "Fuentes de la carpeta.",
        },
        sourceCount: 4,
      }
      shell.sync(state)
      await setup.renderOnce()
      const frame = setup.captureCharFrame()
      expect(frame).toContain("sí")
      expect(frame).toContain("derivados")
      expect(frame).toContain("fuentes/a.md")
      expect(frame).toContain("4 fuentes")
      expect(frame).toContain("evidencia")
    } finally {
      setup.renderer.destroy()
    }
  })
})
