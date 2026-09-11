/**
 * Capture authentic OpenTUI frames (characters + colored spans).
 * Writes site/assets/tui/frames/ so the Pages virtualization can match
 * the real shell rather than a restyled approximation.
 */
import { mkdirSync, writeFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import { createTestRenderer } from "@opentui/core/testing"
import { mountShell } from "../src/shell.ts"
import { initialState, type AppState } from "../src/state.ts"
import { theme } from "../src/theme.ts"

const here = dirname(fileURLToPath(import.meta.url))
const outDir = join(here, "../../site/assets/tui/frames")

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

function encargoBase() {
  return {
    curso: "4° básico",
    asignatura: "Lenguaje",
    oa: "OA 4",
    duracion: "45 min",
    tipo: "planificacion" as const,
    tema: "cuento",
    rumbo: "planificar",
  }
}

function planFixture(state: AppState): AppState["plan"] {
  return {
    objetivo: "Extraer información explícita e implícita del cuento de la carpeta.",
    tipo: "planificacion",
    tipo_label: "planificación",
    oa: "OA 4",
    duracion: "45 min",
    notas: "",
    titulo: "Plan de planificación – cuento carpeta",
    meta: "Plan de trabajo · 1 entregable · Listo",
    resultado_previsto: ["Planificación"],
    decisiones: { curso: "4° básico", asignatura: "Lenguaje", tema: "cuento" },
    como_abordare: [{ titulo: "Lectura", detalle: "cuento de la carpeta" }],
    supuestos: [{ id: "s1", text: "45 min" }],
    questions: [],
  }
}

const shots: { name: string; width: number; height: number; state: () => AppState }[] = [
  {
    name: "home",
    width: 140,
    height: 40,
    state: () => ({
      ...initialState({
        curso: "",
        asignatura: "",
        oa: "",
        duracion: "",
        tipo: null,
      }),
      mode: "offline",
      model: "tero-offline",
      statusLine: "elige rumbo o escribe",
    }),
  },
  {
    name: "encargo",
    width: 140,
    height: 40,
    state: () => ({
      ...initialState(encargoBase()),
      screen: "workspace",
      started: true,
      phase: "idle",
      mode: "offline",
      model: "tero-offline",
      statusLine: "escribe el encargo",
      sourceCount: 5,
      carpeta: "/tmp/carpeta-tui",
    }),
  },
  {
    name: "plan",
    width: 140,
    height: 40,
    state: () => {
      const base = {
        ...initialState(encargoBase()),
        screen: "workspace" as const,
        started: true,
        phase: "esperando_plan" as const,
        planPinned: true,
        sourceCount: 5,
        mode: "offline",
        model: "tero-offline",
        statusLine: "plan listo",
        carpeta: "/tmp/carpeta-tui",
      }
      return { ...base, plan: planFixture(base) }
    },
  },
  {
    name: "puerta",
    width: 140,
    height: 40,
    state: () => {
      const base = {
        ...initialState(encargoBase()),
        screen: "workspace" as const,
        started: true,
        phase: "esperando_criterio" as const,
        proposalTitle: "Planificación",
        proposal:
          "## Objetivo\nExtraer información explícita e implícita.\n\nInicio pregunta. Desarrollo lectura. Cierre ticket.",
        evidence: [
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
        evidenceIndex: 0,
        warnings: [
          {
            code: "unverified_citation",
            message: "Hay parafraseo. No lo trates como cita literal.",
            blocking: false,
          },
        ],
        planPinned: true,
        sourceCount: 5,
        mode: "offline",
        model: "tero-offline",
        statusLine: "tu turno",
        carpeta: "/tmp/carpeta-tui",
      }
      return { ...base, plan: planFixture(base) }
    },
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
      return `<div class="row">${inner}</div>`
    })
    .join("\n")
  return `<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>tero OpenTUI · ${frame.name}</title>
  <style>
    html, body { margin: 0; background: ${theme.bg}; }
    .grid {
      font: 13px/1.2 "IBM Plex Mono", ui-monospace, monospace;
      white-space: pre;
      letter-spacing: 0;
      padding: 0;
    }
    .row { height: 1.2em; }
  </style>
</head>
<body>
  <div class="grid">${rows}</div>
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
      `<section><h2>${dump.name} · ${dump.cols}×${dump.rows}</h2>${frameToHtml(dump).match(/<div class="grid">[\s\S]*<\/div>/)![0]}</section>`,
    )
    console.log(`captured ${dump.name} ${dump.cols}x${dump.rows}`)
  }
  writeFileSync(
    join(outDir, "theme.json"),
    `${JSON.stringify(theme, null, 2)}\n`,
  )
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
    html, body { margin: 0; background: ${theme.bg}; color: ${theme.text}; font: 13px/1.35 "IBM Plex Mono", ui-monospace, monospace; }
    h1, h2 { font-weight: 500; color: ${theme.muted}; padding: 0.6rem 0.8rem; }
    section { margin-bottom: 1.5rem; border-top: 1px solid ${theme.border}; }
    .grid { font: 13px/1.2 "IBM Plex Mono", ui-monospace, monospace; white-space: pre; }
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

await main()
