import { describe, expect, test } from "bun:test"
import { createTestRenderer } from "@opentui/core/testing"
import { applyHostEvent, initialState, type AppState } from "./state.ts"
import { mountShell } from "./shell.ts"
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
  titulo: "Evaluación de comprensión lectora",
  resumen: "Prueba de 45 min con selección múltiple y verdadero/falso.",
  vista_previa:
    "---\ntipo: evaluacion\n---\n\n## Ítems\n1. ¿Quién ve el mar desde la cornisa?\n2. Verdadero o falso: el huemul duda.",
  origen: null,
  cambios: [],
  notas_nee: [],
  evidencias: [
    {
      path: "fuentes/cuento-el-condor-y-el-huemel.md",
      snippet: "Yo veo el mar desde aquí",
      seccion: "desarrollo",
      verified: true,
    },
    {
      path: "fuentes/bases-oa-lenguaje-4b.md",
      snippet: "Extraer información explícita e implícita",
      seccion: "OA 4",
      verified: false,
    },
  ],
  warnings: [
    {
      code: "thin_evidence",
      message: "Menos de dos fuentes citadas.",
      blocking: false,
    },
  ],
}

async function frame(state: AppState, width = 140, height = 46) {
  const setup = await createTestRenderer({ width, height })
  const shell = mountShell(setup.renderer, () => {})
  shell.sync(state)
  await setup.renderOnce()
  const text = setup.captureCharFrame()
  setup.renderer.destroy()
  return text
}

describe("shell conversacional", () => {
  test("home muestra la marca, el queltehue y el prompt — sin rumbos", async () => {
    const state = {
      ...initialState({ curso: "", asignatura: "", oa: "", duracion: "", tipo: null }),
      ready: true,
      carpeta: "/workspace/examples/carpeta-demo",
      statusLine: "5 fuentes en la carpeta",
      recentSessions: [
        { kind: "derivado", label: "20260101-120000-prueba.md", path: "derivados/20260101-120000-prueba.md" },
      ],
    }
    const text = await frame(state, 120, 32)
    const lines = text.replace(/\n$/, "").split("\n")
    expect(lines[0]).toContain("╭─ tero")
    expect(lines[lines.length - 1]).toMatch(/^╰/)
    expect(lines[lines.length - 1]).toContain("carpeta-demo")
    expect(text).toContain("tero")
    expect(text).toContain("tus fuentes, tu criterio")
    expect(text).toContain("Pregunta, explora o crea")
    expect(text).toContain("▀▀▀▀███████")
    expect(text).toContain("▀▀▀▀▀▀▀▀▀▀")
    expect(text).toContain("recientes")
    expect(text).not.toContain("Planificar")
    expect(text).not.toContain("Evaluar")
    expect(text).not.toContain("Adaptar")
    expect(text).not.toContain("rumbo")
    expect(text).not.toContain("1–4")
    expect(text).not.toContain("sin encargo")
  })

  test("el hilo muestra los turnos de la persona y del agente", async () => {
    const state: AppState = {
      ...initialState(encargo),
      screen: "conversacion",
      started: true,
      mode: "offline",
      model: "tero-offline",
      carpeta: "/workspace/examples/carpeta-demo",
      messages: [
        { id: "m1", role: "persona", text: "Prepara una guía de fracciones" },
        { id: "m2", role: "agente", text: "¿Para qué curso y qué OA?" },
      ],
      statusLine: "",
    }
    const text = await frame(state, 120, 32)
    expect(text).toContain("tú")
    expect(text).toContain("Prepara una guía de fracciones")
    expect(text).toContain("tero")
    expect(text).toContain("¿Para qué curso y qué OA?")
    expect(text).not.toContain("Sin turnos")
  })

  test("el texto en streaming se pinta en el hilo antes de la respuesta", async () => {
    const state: AppState = {
      ...initialState(encargo),
      screen: "conversacion",
      started: true,
      phase: "pensando",
      thinking: true,
      thinkingLabel: "escribiendo…",
      streaming: "Necesito el curso",
    }
    const text = await frame(state, 120, 32)
    expect(text).toContain("Necesito el curso")
    expect(text).toContain("▌")
  })

  test("la tarjeta de propuesta muestra resumen, vista previa, evidencia y avisos", async () => {
    const setup = await createTestRenderer({ width: 140, height: 46 })
    try {
      const shell = mountShell(setup.renderer, () => {})
      let state: AppState = applyHostEvent(
        { ...initialState(encargo), mode: "offline", model: "tero-offline", carpeta: "/workspace/examples/carpeta-demo" },
        { type: "propuesta", id: "t1", propuesta },
      )
      shell.sync(state)
      await setup.renderOnce()
      const text = setup.captureCharFrame()
      expect(text).toContain("propuesta")
      expect(text).toContain("crear · evaluación")
      expect(text).toContain("Evaluación de comprensión")
      expect(text).toContain("Prueba de 45 min")
      expect(text).toContain("vista previa")
      expect(text).toContain("tipo: evaluacion")
      expect(text).toContain("¿Quién ve el mar")
      // Evidencia: ✓ en archivo / ? parafraseo (como hoy).
      expect(text).toContain("✓ en archivo")
      expect(text).toContain("desarrollo")
      // Avisos visibles y no bloqueantes.
      expect(text).toContain("Menos de dos")
      expect(text).toContain("no bloquean")
      // Franja de aprobación con atajos y/n.
      expect(text).toContain("[y] aprobar")
      expect(text).toContain("[n] descartar")
      expect(text).not.toMatch(/\[s\]|\[b\]|\[c\]|\ba aprobar\b/)

      // El segundo ítem, marcado como parafraseo, se ve al recorrer con [ ].
      state = { ...state, evidenceIndex: 1 }
      shell.sync(state)
      await setup.renderOnce()
      const second = setup.captureCharFrame()
      expect(second).toContain("? parafraseo")
      expect(second).toContain("explícita")
    } finally {
      setup.renderer.destroy()
    }
  })

  test("adaptar muestra origen, cambios y apoyos NEE", async () => {
    const state: AppState = applyHostEvent(
      { ...initialState(encargo), mode: "offline", model: "tero-offline" },
      {
        type: "propuesta",
        id: "t2",
        propuesta: {
          ...propuesta,
          accion: "adaptar",
          tipo: "planificacion",
          tipo_label: "planificación",
          origen: "derivados/20260101-120000-planificacion-cuento.md",
          cambios: ["Agrega pauta de corrección", "Sube la exigencia del ítem 3"],
          notas_nee: ["Tiempo extendido", "Enunciados en dos pasos"],
        },
      },
    )
    const text = await frame(state, 140, 46)
    expect(text).toContain("adaptar (NEE) · planificación")
    expect(text).toContain("origen")
    expect(text).toContain("derivados/20260101-120000-planificacion")
    expect(text).toContain("cambios")
    expect(text).toContain("Agrega pauta de corrección")
    expect(text).toContain("apoyos y criterios NEE")
    expect(text).toContain("Tiempo extendido")
  })

  test("escrito muestra la ruta en derivados con la acción", async () => {
    let state: AppState = applyHostEvent(
      { ...initialState(encargo), mode: "offline", model: "tero-offline" },
      { type: "propuesta", id: "t3", propuesta },
    )
    state = applyHostEvent(state, {
      type: "escrito",
      id: "t3",
      path: "derivados/20260101-120000-evaluacion-condor.md",
      accion: "crear",
    })
    const text = await frame(state, 140, 46)
    expect(text).toContain("escrito")
    expect(text).toContain("derivados/20260101-120000-evaluacion-condor.md")
    expect(text).toContain("crear")
    expect(text).not.toContain("[y] aprobar")
  })

  test("el panel de error es dedicado y ofrece r para reintentar", async () => {
    const state: AppState = applyHostEvent(initialState(encargo), {
      type: "error",
      message: "No pude leer fuentes/cuento.md",
      code: "read_failed",
      retryable: true,
    })
    const text = await frame(state, 120, 32)
    expect(text).toContain("error")
    expect(text).toContain("No pude leer fuentes/cuento.md")
    expect(text).toContain("[r] reintentar")
    expect(text).toContain("/retry")
  })

  test("la ayuda contextual abre con ? y es scrollable", async () => {
    const state: AppState = {
      ...initialState(encargo),
      screen: "conversacion",
      started: true,
      help: true,
    }
    const text = await frame(state, 120, 36)
    expect(text).toContain("ayuda")
    expect(text).toContain("y / n decisión")
    expect(text).toContain("/export")
    expect(text).toContain("PgUp/PgDn")
    expect(text).not.toContain("Rumbos")
    expect(text).not.toContain("Puerta")
  })

  test("modo compacto esconde el pájaro y la columna de evidencia", async () => {
    const wide: AppState = applyHostEvent(initialState(encargo), {
      type: "propuesta",
      id: "t4",
      propuesta,
    })
    const compactText = await frame({ ...wide, compact: true }, 90, 30)
    expect(compactText).toContain("crear · evaluación")
    // La columna de evidencia se esconde en compacto; la tarjeta sigue.
    expect(compactText).not.toContain("evidencia")
    const homeCompact = await frame(
      { ...initialState({ curso: "", asignatura: "", oa: "", duracion: "", tipo: null }), compact: true },
      90,
      30,
    )
    expect(homeCompact).not.toContain("▀▀▀▀███████")
    expect(homeCompact).toContain("tero")
    expect(homeCompact).toContain("Pregunta, explora o crea")
  })

  test("los chips de contexto y la evidencia larga se envuelven, no se cortan", async () => {
    const state: AppState = applyHostEvent(
      { ...initialState(encargo), mode: "offline", model: "tero-offline", sourceCount: 5 },
      {
        type: "propuesta",
        id: "t5",
        propuesta: {
          ...propuesta,
          evidencias: [
            {
              path: "fuentes/bases-oa-lenguaje-4b.md",
              snippet: "Extraer información explícita e implícita",
              seccion:
                'OA "Extraer información explícita e implícita de textos literarios y no literarios"',
              verified: true,
            },
          ],
        },
      },
    )
    const text = await frame(state, 140, 46)
    expect(text).toContain("Lenguaje")
    expect(text).toContain("OA 4")
    expect(text).toContain("5 fuentes")
    expect(text).toMatch(/explícita/)
  })
})
