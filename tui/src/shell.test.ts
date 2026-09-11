import { describe, expect, test } from "bun:test"
import { createTestRenderer } from "@opentui/core/testing"
import { initialState } from "./state.ts"
import { mountShell } from "./shell.ts"

describe("shell frames", () => {
  test("home shows brand and rumbos without chips", async () => {
    const setup = await createTestRenderer({ width: 120, height: 32 })
    try {
      const shell = mountShell(setup.renderer, () => {})
      const state = {
        ...initialState({
          curso: "",
          asignatura: "",
          oa: "",
          duracion: "",
          tipo: null,
        }),
        carpeta: "/workspace/examples/carpeta-demo",
      }
      shell.sync(state)
      await setup.renderOnce()
      const frame = setup.captureCharFrame()
      const lines = frame.replace(/\n$/, "").split("\n")
      expect(lines[0]).toContain("╭─ tero")
      expect(lines[lines.length - 1]).toMatch(/^╰/)
      expect(lines[lines.length - 1]).toContain("carpeta-demo")
      expect(lines[2] ?? "").not.toMatch(/^╰/)
      expect(frame).toContain("tero")
      expect(frame).toContain("Planificar")
      expect(frame).toContain("Crear")
      expect(frame).toContain("Evaluar")
      expect(frame).toContain("Adaptar")
      expect(frame).toContain("Pregunta, explora o crea")
      expect(frame).toContain("secuencia de clase")
      expect(frame).toContain("guía o actividad")
      expect(frame).toMatch(/▲/)
      expect(frame).not.toContain("sin encargo")
    } finally {
      setup.renderer.destroy()
    }
  })

  test("workspace chips and empty proposal render", async () => {
    const setup = await createTestRenderer({ width: 120, height: 32 })
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
        screen: "workspace" as const,
        started: true,
        phase: "idle" as const,
        carpeta: "/workspace/examples/carpeta-demo",
      }
      shell.sync(state)
      await setup.renderOnce()
      const frame = setup.captureCharFrame()
      const lines = frame.replace(/\n$/, "").split("\n")
      expect(lines[0]).toContain("╭─ tero")
      expect(lines[lines.length - 1]).toMatch(/^╰/)
      expect(lines[lines.length - 1]).toContain("carpeta-demo")
      expect(frame).toContain("tero")
      expect(frame).toContain("básico")
      expect(frame).toContain("OA 4")
      expect(frame).toContain("El agente prepara")
      expect(frame).toContain("evidencia")
      expect(frame).toContain("sesión")
      expect(frame).toContain("propuesta")
    } finally {
      setup.renderer.destroy()
    }
  })

  test("plan card + clarification + gate strip render", async () => {
    const setup = await createTestRenderer({ width: 140, height: 48 })
    try {
      const shell = mountShell(setup.renderer, () => {})
      const state = {
        ...initialState({
          curso: "6° básico",
          asignatura: "Matemática",
          oa: "OA 4",
          duracion: "45 min",
          tipo: "guia",
          tema: "fracciones",
        }),
        screen: "workspace" as const,
        started: true,
        phase: "esperando_clarificacion" as const,
        uiMode: "clarify" as const,
        planPinned: true,
        plan: {
          objetivo: "Guía de práctica de fracciones para 6° básico",
          tipo: "guia",
          tipo_label: "guía",
          oa: "OA 4",
          duracion: "45 min",
          notas: "",
          titulo: "Plan de Guía de Práctica de Fracciones",
          meta: "Plan de trabajo · 1 entregable · Listo · 9 sept 2026",
          resultado_previsto: ["Guía de práctica"],
          decisiones: {
            curso: "6° básico",
            asignatura: "Matemática",
            tema: "Representación, comparación y equivalencia de fracciones",
          },
          como_abordare: [
            { titulo: "Selección múltiple", detalle: "Ítems de representación." },
            { titulo: "Desarrollo", detalle: "Problemas breves." },
          ],
          supuestos: [
            { id: "s1", text: "Se usará una extensión breve, pensada para una sesión." },
          ],
          questions: [],
        },
        question: {
          id: "q1",
          prompt: "¿Qué énfasis conviene para la práctica?",
          options: [
            { id: "1", label: "Representación y aplicación", suggested: true },
            { id: "2", label: "Cálculo y equivalencia" },
            { id: "3", label: "Resolución de problemas" },
          ],
        },
        sourceCount: 4,
      }
      shell.sync(state)
      await setup.renderOnce()
      const frame = setup.captureCharFrame()
      expect(frame).toContain("RESULTADO PREVISTO")
      expect(frame).toContain("SUGERIDA")
      expect(frame).toContain("énfasis")
      expect(frame).toContain("Responde con tus palabras")
      expect(frame).toContain("Matemática")
      // Plan body may scroll; header + visible sections are enough at this height.
      expect(frame).toMatch(/RESULTADO PREVISTO|DECISIONES CONFIRMADAS|guía ·/)
    } finally {
      setup.renderer.destroy()
    }
  })

  test("gate strip and selected evidence render", async () => {
    const setup = await createTestRenderer({ width: 140, height: 40 })
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
        screen: "workspace" as const,
        started: true,
        phase: "esperando_criterio" as const,
        proposal: "## Objetivo\nLeer con evidencia.",
        proposalTitle: "Plan",
        evidence: [
          { path: "fuentes/a.md", snippet: "OA 4 extraer información", seccion: "OA", verified: true },
          { path: "fuentes/b.md", snippet: "El huemul preguntó", seccion: "desarrollo", verified: false },
        ],
        evidenceIndex: 0,
        focusPanel: "evidence" as const,
        planPinned: true,
        plan: {
          objetivo: "Leer con evidencia",
          tipo: "planificacion",
          tipo_label: "planificación",
          oa: "OA 4",
          duracion: "45 min",
          notas: "Fuentes de la carpeta.",
          titulo: "Plan de planificación",
          meta: "1 entregable",
          resultado_previsto: ["planificación"],
          decisiones: { curso: "4° básico", asignatura: "Lenguaje", tema: "cuento" },
          como_abordare: [{ titulo: "Inicio", detalle: "activar" }],
          supuestos: [{ id: "s1", text: "45 min" }],
        },
        warnings: [
          {
            code: "unverified_citation",
            message: "El fragmento citado no aparece en fuentes/b.md.",
            blocking: false,
          },
        ],
        sourceCount: 4,
      }
      shell.sync(state)
      await setup.renderOnce()
      const frame = setup.captureCharFrame()
      expect(frame).toContain("sí")
      expect(frame).toContain("derivados")
      expect(frame).toContain("evid 1/2")
      expect(frame).toContain("4 fuentes")
      expect(frame).toContain("aviso")
    } finally {
      setup.renderer.destroy()
    }
  })

  test("plan stage hides empty propuesta/evidencia and keeps footer quiet", async () => {
    const setup = await createTestRenderer({ width: 120, height: 36 })
    try {
      const shell = mountShell(setup.renderer, () => {})
      const state = {
        ...initialState({
          curso: "4° básico",
          asignatura: "Lenguaje",
          oa: "OA 4",
          duracion: "45 min",
          tipo: "planificacion",
          tema: "cuento",
          rumbo: "planificar",
        }),
        screen: "workspace" as const,
        started: true,
        phase: "esperando_plan" as const,
        planPinned: true,
        sourceCount: 5,
        mode: "offline",
        model: "tero-offline",
        statusLine: "plan listo",
        plan: {
          objetivo: "Leer el cuento y distinguir lo explícito de lo implícito en el valle.",
          tipo: "planificacion",
          tipo_label: "planificación",
          oa: "OA 4",
          duracion: "45 min",
          notas: "",
          titulo: "Plan de planificación – planificación 45 min cuento carpeta",
          meta: "Plan de trabajo · 1 entregable · Listo · 10 sep 2026",
          resultado_previsto: ["Planificación"],
          decisiones: { curso: "4° básico", asignatura: "Lenguaje", tema: "cuento" },
          como_abordare: [{ titulo: "Lectura", detalle: "cuento" }],
          supuestos: [{ id: "s1", text: "45 min" }],
        },
      }
      shell.sync(state)
      await setup.renderOnce()
      const frame = setup.captureCharFrame()
      expect(frame).toContain("plan")
      expect(frame).toContain("aprobar")
      // Empty chrome must not dominate during plan wait.
      expect(frame).not.toContain("El agente prepara")
      expect(frame).not.toContain("Las citas aparecen")
      // Footer must not echo a/e/x (strip already has them).
      const footerLine = frame.split("\n").slice(-3).join(" ")
      expect(footerLine).not.toMatch(/a aprobar.*e supuesto.*x cancelar/)
      expect(frame).toContain("teclas arriba")
    } finally {
      setup.renderer.destroy()
    }
  })

  test("gate footer does not repeat s/n/b/c legend", async () => {
    const setup = await createTestRenderer({ width: 120, height: 36 })
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
        screen: "workspace" as const,
        started: true,
        phase: "esperando_criterio" as const,
        proposal: "## Objetivo\nLeer con evidencia.",
        proposalTitle: "Plan",
        statusLine: "tu turno",
        evidence: [
          {
            path: "fuentes/bases-oa-lenguaje-4b.md",
            snippet: "Extraer información explícita e implícita",
            seccion: 'OA "Extraer información explícita e implícita de textos literarios y no literarios"',
            verified: true,
          },
          { path: "fuentes/b.md", snippet: "huemul", seccion: "desarrollo", verified: false },
        ],
        evidenceIndex: 0,
        planPinned: true,
        plan: {
          objetivo: "Leer",
          tipo: "planificacion",
          tipo_label: "planificación",
          oa: "OA 4",
          duracion: "45 min",
          notas: "",
          titulo: "Plan de planificación – planificación 45 min cuento carpeta",
          meta: "1 entregable",
          resultado_previsto: ["Planificación"],
          decisiones: { curso: "4° básico", asignatura: "Lenguaje", tema: "cuento" },
          como_abordare: [{ titulo: "Inicio", detalle: "activar" }],
          supuestos: [{ id: "s1", text: "45 min" }],
        },
        sourceCount: 5,
        mode: "offline",
        model: "tero-offline",
      }
      shell.sync(state)
      await setup.renderOnce()
      const frame = setup.captureCharFrame()
      expect(frame).toContain("sí")
      expect(frame).toContain("derivados")
      // Evidence should wrap OA rather than mid-word clip on one long line.
      expect(frame).toMatch(/explícita/)
      expect(frame).toContain("teclas arriba")
      const lines = frame.split("\n")
      const footer = lines[lines.length - 1] + lines[lines.length - 2]
      // Must not show the legend twice on the footer line.
      const hits = footer.match(/s sí/g) || []
      expect(hits.length).toBeLessThan(2)
      expect(footer).not.toMatch(/s sí · n no · b borrador · c corregir\s+s sí/)
    } finally {
      setup.renderer.destroy()
    }
  })

})
