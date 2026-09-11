/**
 * Capture authentic OpenTUI frames (characters + colored spans).
 * Writes site/assets/tui/frames/ so the Pages virtualization can match
 * the real shell rather than a restyled approximation.
 */
import { copyFileSync, mkdirSync, writeFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import { createTestRenderer } from "@opentui/core/testing"
import { mountShell } from "../src/shell.ts"
import { initialState, type AppState } from "../src/state.ts"
import { theme } from "../src/theme.ts"
import type { CardStatus, Encargo, Mensaje, Propuesta } from "../src/protocol.ts"

const here = dirname(fileURLToPath(import.meta.url))
const outDir = join(here, "../../site/assets/tui/frames")

/** Same carpeta `python -m tero tui --offline` uses in this repo. */
const CARPETA = "/workspace/examples/carpeta-demo"

type RGBA = { r: number; g: number; b: number; a: number }

type Span = {
  text: string
  fg: [number, number, number, number]
  bg: [number, number, number, number]
  attributes: number
  width: number
}

type FrameDump = {
  name: string
  cols: number
  rows: number
  cursor: [number, number]
  lines: { spans: Span[] }[]
  text: string
}

type ConversacionFixture = {
  encargo: Encargo
  messages: Mensaje[]
  card: Propuesta
  cardStatus: CardStatus
  statusLine: string
  sourceCount: number
  writtenPath?: string
  writtenAccion?: string
}

function rgbaTuple(c: RGBA | number[] | undefined): [number, number, number, number] {
  if (!c) return [0, 0, 0, 1]
  if (Array.isArray(c)) {
    return [c[0] ?? 0, c[1] ?? 0, c[2] ?? 0, c[3] ?? 1]
  }
  return [c.r, c.g, c.b, c.a]
}

function cssColor(c: [number, number, number, number]): string {
  const [r, g, b, a] = c
  const R = Math.round(r <= 1 ? r * 255 : r)
  const G = Math.round(g <= 1 ? g * 255 : g)
  const B = Math.round(b <= 1 ? b * 255 : b)
  if (a < 0.999) return `rgba(${R},${G},${B},${a.toFixed(3)})`
  return `#${[R, G, B].map((n) => n.toString(16).padStart(2, "0")).join("")}`
}

/** Tres turnos reales del flujo conversacional: crear, crear con NEE, adaptar. */
const fixtures: Record<"evaluacion" | "guia" | "adaptar", ConversacionFixture> = {
  evaluacion: {
    encargo: {
      curso: "4° básico",
      asignatura: "Lenguaje",
      tema: "cuento",
      oa: "OA 4",
      duracion: "45 min",
      tipo: "evaluacion",
    },
    messages: [
      { id: "m1", role: "persona", text: "Prepara una evaluación de comprensión lectora para 4° básico." },
      { id: "m2", role: "agente", text: "¿Incluyo pauta de corrección y los ítems citan el cuento de la carpeta?" },
      { id: "m3", role: "persona", text: "Sí, con pauta. Usa el cuento del cóndor y el huemul." },
    ],
    card: {
      accion: "crear",
      tipo: "evaluacion",
      tipo_label: "evaluación",
      titulo: "Evaluación de comprensión lectora — El cóndor y el huemul",
      resumen: "Prueba de 45 min con selección múltiple, verdadero/falso y una pregunta de desarrollo con cita.",
      vista_previa:
        "---\ntipo: evaluacion\ncurso: 4° básico\n---\n\n## Selección múltiple\n1. ¿Quién observa el mar desde la cornisa?\na) El huemul\nb) El cóndor\nc) El zorro\n\n## Verdadero o falso\n2. El huemul duda de lo que ve el cóndor.\n\n## Desarrollo\n3. Cita el fragmento donde el cóndor afirma ver el mar.",
      origen: null,
      cambios: [],
      notas_nee: [],
      evidencias: [
        {
          path: "fuentes/cuento-el-condor-y-el-huemul.md",
          snippet: "El cóndor afirma ver el mar desde la cornisa",
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
          code: "unverified_citation",
          message: "Hay parafraseo del cuento. No lo trates como cita literal.",
          blocking: false,
        },
      ],
    },
    cardStatus: "pendiente",
    statusLine: "tu decisión: y aprueba · n descarta · o escribe",
    sourceCount: 3,
  },
  guia: {
    encargo: {
      curso: "1° medio",
      asignatura: "Matemática",
      tema: "sistemas 2×2",
      oa: "",
      duracion: "90 min",
      tipo: "guia",
    },
    messages: [
      { id: "m1", role: "persona", text: "Necesito una guía para introducir sistemas 2×2." },
      { id: "m2", role: "agente", text: "¿La pienso para 90 minutos con trabajo en parejas?" },
      { id: "m3", role: "persona", text: "Sí, 90 minutos y con ejemplos resueltos." },
    ],
    card: {
      accion: "crear",
      tipo: "guia",
      tipo_label: "guía",
      titulo: "Guía de sistemas 2×2 — dos rectas, un punto",
      resumen: "Guía de 90 min: vocabulario, selección múltiple, verdadero/falso y desarrollo con verificación.",
      vista_previa:
        "---\ntipo: guia\ncurso: 1° medio\n---\n\n## Propósito\nReconocer un sistema 2×2 como dos condiciones a la vez.\n\n## I. Vocabulario\nsistema 2×2 · solución · verificación\n\n## II. Desarrollo\nResuelve por sustitución: 2x + y = 12, x − y = 3.",
      origen: null,
      cambios: [],
      notas_nee: [],
      evidencias: [
        {
          path: "fuentes/vocabulario-algebra.md",
          snippet: "sistema 2×2: dos ecuaciones lineales…",
          seccion: "Vocabulario",
          verified: false,
        },
        {
          path: "fuentes/ejemplos-sistemas-resueltos.md",
          snippet: "Ejemplo A",
          seccion: "Ejemplo A",
          verified: true,
        },
      ],
      warnings: [
        {
          code: "thin_evidence",
          message: "Menos de dos fuentes citadas. El panel de evidencia queda pobre.",
          blocking: false,
        },
        {
          code: "missing_structure",
          message: "Faltan apartados esperados para guía: instrucciones.",
          blocking: false,
        },
      ],
    },
    cardStatus: "pendiente",
    statusLine: "tu decisión: y aprueba · n descarta · o escribe",
    sourceCount: 3,
  },
  adaptar: {
    encargo: {
      curso: "4° básico",
      asignatura: "Lenguaje",
      tema: "cuento",
      oa: "OA 4",
      duracion: "45 min",
      tipo: "evaluacion",
    },
    messages: [
      { id: "m1", role: "persona", text: "Adapta la evaluación del cóndor para un estudiante con dislexia." },
      { id: "m2", role: "agente", text: "¿Agrego tiempo extendido y enunciados en dos pasos?" },
      { id: "m3", role: "persona", text: "Sí, y deja el texto más grande cuando se exporte." },
    ],
    card: {
      accion: "adaptar",
      tipo: "evaluacion",
      tipo_label: "evaluación",
      titulo: "Evaluación adaptada — El cóndor y el huemul",
      resumen: "Misma prueba con apoyos NEE: tiempo extendido, enunciados en dos pasos y sin doble negación.",
      vista_previa:
        "---\ntipo: evaluacion\naccion: adaptar\n---\n\n## Selección múltiple (tiempo extendido)\n1. ¿Quién observa el mar?\n\na) El huemul\nb) El cóndor\n\n## Apoyos\n- Enunciados en dos pasos.\n- Sin doble negación.",
      origen: "derivados/20260910-210457-evaluacion-condor-4a5586.md",
      cambios: [
        "Agrega tiempo extendido y apoyos NEE",
        "Reescribe los enunciados en dos pasos",
        "Suma pauta de corrección con criterios",
      ],
      notas_nee: [
        "Tiempo extendido (50% más)",
        "Enunciados en dos pasos, sin doble negación",
        "Texto ampliado al exportar",
      ],
      evidencias: [
        {
          path: "fuentes/cuento-el-condor-y-el-huemul.md",
          snippet: "Yo veo el mar desde aquí",
          seccion: "desarrollo",
          verified: true,
        },
        {
          path: "fuentes/bases-oa-lenguaje-4b.md",
          snippet: "OA 4",
          seccion: "OA 4",
          verified: false,
        },
      ],
      warnings: [
        {
          code: "adapted_source",
          message: "Es una versión nueva: el material de origen no se toca.",
          blocking: false,
        },
      ],
    },
    cardStatus: "pendiente",
    statusLine: "tu decisión: y aprueba · n descarta · o escribe",
    sourceCount: 2,
  },
}

function baseState(fixture: ConversacionFixture, patch: Partial<AppState> = {}): AppState {
  return {
    ...initialState(fixture.encargo),
    screen: "conversacion",
    started: true,
    mode: "offline",
    model: "tero-offline",
    carpeta: CARPETA,
    sourceCount: fixture.sourceCount,
    messages: fixture.messages,
    card: fixture.card,
    cardId: "turno-1",
    cardStatus: fixture.cardStatus,
    phase: "esperando_aprobacion",
    statusLine: fixture.statusLine,
    ...patch,
  }
}

function homeState(): AppState {
  return {
    ...initialState({
      curso: "",
      asignatura: "",
      oa: "",
      duracion: "",
      tipo: null,
    }),
    ready: true,
    mode: "offline",
    model: "tero-offline",
    carpeta: CARPETA,
    sourceCount: 5,
    statusLine: "5 fuentes en la carpeta",
    recentSessions: [
      {
        kind: "derivado",
        label: "20260910-210457-evaluacion-condor-4a5586.md",
        path: "derivados/20260910-210457-evaluacion-condor-4a5586.md",
      },
      {
        kind: "derivado",
        label: "20260910-205527-planificacion-cuento-e46559.md",
        path: "derivados/20260910-205527-planificacion-cuento-e46559.md",
      },
      {
        kind: "derivado",
        label: "20260910-201559-guia-sistemas-2bff17.md",
        path: "derivados/20260910-201559-guia-sistemas-2bff17.md",
      },
    ],
  }
}

/** Conversación sin tarjeta: el agente pregunta en lenguaje natural. */
function conversacionState(): AppState {
  return {
    ...homeState(),
    screen: "conversacion",
    started: true,
    messages: [
      {
        id: "m1",
        role: "persona",
        text: "Prepara una evaluación de comprensión lectora para 4° básico.",
      },
      { id: "m2", role: "agente", text: "¿Incluyo pauta de corrección y cuánto dura la prueba?" },
    ],
    statusLine: "",
  }
}

const shots: { name: string; width: number; height: number; state: () => AppState }[] = [
  {
    name: "home",
    width: 140,
    height: 40,
    state: homeState,
  },
  {
    name: "help",
    width: 140,
    height: 40,
    state: () => ({ ...homeState(), help: true }),
  },
  {
    name: "conversacion",
    width: 140,
    height: 40,
    state: conversacionState,
  },
  {
    name: "conversacion-streaming",
    width: 140,
    height: 40,
    state: () => ({
      ...conversacionState(),
      phase: "pensando",
      thinking: true,
      thinkingLabel: "escribiendo…",
      streaming: "Necesito el curso y el OA ",
      activities: [
        { tool: "list_sources", state: "end", detail: "3" },
        { tool: "read_source", state: "start", detail: "cuento-el-condor-y-el-huemul.md" },
      ],
    }),
  },
  {
    name: "propuesta",
    width: 140,
    height: 46,
    state: () => baseState(fixtures.evaluacion),
  },
  {
    name: "propuesta-guia",
    width: 140,
    height: 46,
    state: () => baseState(fixtures.guia),
  },
  {
    name: "propuesta-adaptar",
    width: 140,
    height: 46,
    state: () => baseState(fixtures.adaptar),
  },
  {
    name: "escrito",
    width: 140,
    height: 46,
    state: () => {
      const path = "derivados/20260911-101500-evaluacion-condor-9c1f2a.md"
      return baseState(fixtures.evaluacion, {
        cardStatus: "escrito",
        phase: "listo",
        writtenPath: path,
        writtenAccion: "crear",
        statusLine: `escrito · crear · ${path}`,
        messages: [
          ...fixtures.evaluacion.messages,
          { id: "m4", role: "host", text: "escrito · crear", path },
        ],
      })
    },
  },
  {
    name: "error",
    width: 140,
    height: 40,
    state: () => ({
      ...conversacionState(),
      phase: "error",
      lastError: "No pude leer fuentes/cuento-el-condor-y-el-huemul.md",
      errorCode: "read_failed",
      retryable: true,
      statusLine: "No pude leer fuentes/cuento-el-condor-y-el-huemul.md",
    }),
  },
  {
    name: "compacto",
    width: 96,
    height: 30,
    state: () => ({ ...baseState(fixtures.evaluacion), compact: true }),
  },
]

async function captureOne(shot: (typeof shots)[0]): Promise<FrameDump> {
  const setup = await createTestRenderer({ width: shot.width, height: shot.height })
  try {
    const shell = mountShell(setup.renderer, () => {})
    shell.sync(shot.state())
    await setup.renderOnce()
    await setup.waitForVisualIdle({ maxFrames: 8, quietFrames: 2 }).catch(() => {})
    const text = setup.captureCharFrame()
    const spans = setup.captureSpans()
    return {
      name: shot.name,
      cols: spans.cols,
      rows: spans.rows,
      cursor: spans.cursor,
      lines: spans.lines.map((line) => ({
        spans: line.spans.map((span) => ({
          text: span.text,
          fg: rgbaTuple(span.fg as RGBA),
          bg: rgbaTuple(span.bg as RGBA),
          attributes: span.attributes,
          width: span.width,
        })),
      })),
      text,
    }
  } finally {
    setup.renderer.destroy()
  }
}

function frameToHtml(frame: FrameDump): string {
  const rows = frame.lines
    .map((line) => {
      const inner = line.spans
        .map((span) => {
          const fg = cssColor(span.fg)
          const bg = cssColor(span.bg)
          const bold = span.attributes & 1 ? "font-weight:600;" : ""
          const text = span.text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
          return `<span style="color:${fg};background:${bg};${bold}">${text}</span>`
        })
        .join("")
      return `<div class="tui-row">${inner}</div>`
    })
    .join("\n")
  return `<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>tero OpenTUI · ${frame.name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="../../../styles.css?v=chilensis"/>
</head>
<body data-offline-model="tero-offline">
  <div class="window" id="app">
    <header class="window-chrome sr-only">
      <span class="window-title">tero</span>
      <span class="window-path">~/tero</span>
    </header>
    <div class="tui-host" id="tui-host">
      <div id="tui-grid" class="tui-grid">${rows}</div>
    </div>
  </div>
  <script src="../../../tui-grid.js?v=chilensis"></script>
  <script>
    (function () {
      const host = document.getElementById("tui-host");
      const grid = document.getElementById("tui-grid");
      const fit = function () {
        if (window.teroTui) window.teroTui.fitHost(host, grid, ${frame.cols}, ${frame.rows});
      };
      fit();
      window.addEventListener("resize", fit);
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
    })();
  </script>
</body>
</html>
`
}

async function main() {
  mkdirSync(outDir, { recursive: true })
  const gallery: string[] = []
  const index: { name: string; cols: number; rows: number }[] = []
  for (const shot of shots) {
    const dump = await captureOne(shot)
    writeFileSync(join(outDir, `${dump.name}.json`), `${JSON.stringify(dump)}\n`)
    writeFileSync(join(outDir, `${dump.name}.txt`), dump.text.endsWith("\n") ? dump.text : `${dump.text}\n`)
    writeFileSync(join(outDir, `${dump.name}.html`), frameToHtml(dump))
    index.push({ name: dump.name, cols: dump.cols, rows: dump.rows })
    gallery.push(
      `<section><h2>${dump.name} · ${dump.cols}×${dump.rows}</h2><div class="tui-grid">${dump.lines
        .map((line) => {
          const inner = line.spans
            .map((span) => {
              const fg = cssColor(span.fg)
              const bg = cssColor(span.bg)
              const text = span.text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
              return `<span style="color:${fg};background:${bg}">${text}</span>`
            })
            .join("")
          return `<div class="tui-row">${inner}</div>`
        })
        .join("")}</div></section>`,
    )
    console.log(`captured ${dump.name} ${dump.cols}x${dump.rows}`)
  }
  writeFileSync(join(outDir, "theme.json"), `${JSON.stringify(theme, null, 2)}\n`)
  writeFileSync(
    join(outDir, "index.json"),
    `${JSON.stringify({ generated: new Date().toISOString().slice(0, 10), frames: index }, null, 2)}\n`,
  )
  writeFileSync(
    join(outDir, "gallery.html"),
    `<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>tero OpenTUI frames</title>
  <style>
    html, body { margin: 0; background: ${theme.bg}; color: ${theme.text}; font: 13px/1.35 "JetBrains Mono", ui-monospace, monospace; }
    h1, h2 { font-weight: 500; color: ${theme.muted}; padding: 0.6rem 0.8rem; }
    section { margin-bottom: 1.5rem; border-top: 1px solid ${theme.border}; }
    .grid { font: 13px/1.2 "JetBrains Mono", ui-monospace, monospace; white-space: pre; }
    .row { height: 1.2em; }
  </style>
</head>
<body>
  <h1>OpenTUI · capturas reales</h1>
  ${gallery.join("\n")}
</body>
</html>
`,
  )
}

export { shots }

if (import.meta.main) {
  await main()
}
