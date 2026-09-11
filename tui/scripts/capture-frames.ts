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
import type { Encargo, Evidence, Plan, WarningItem } from "../src/protocol.ts"

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

type RumboId = 1 | 2 | 3 | 4

type RumboFixture = {
  encargo: Encargo
  plan: Plan
  proposalTitle: string
  proposal: string
  evidence: Evidence[]
  warnings: WarningItem[]
  sourceCount: number
  thinkingLabel: string
  activityDetail: string
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

const rumbos: Record<RumboId, RumboFixture> = {
  1: {
    encargo: {
      rumbo: "planificar",
      curso: "4° básico",
      asignatura: "Lenguaje",
      tema: "cuento",
      oa: "OA 4",
      duracion: "45 min",
      tipo: "planificacion",
    },
    plan: {
      objetivo:
        "Extraer información explícita e implícita del cuento «El cóndor y el huemul», con cita.",
      tipo: "planificacion",
      tipo_label: "planificación",
      oa: "OA 4",
      duracion: "45 min",
      notas: "",
      titulo: "Plan de planificación – cuento",
      meta: "Plan de trabajo · 1 entregable · Listo",
      resultado_previsto: ["Planificación"],
      decisiones: { curso: "4° básico", asignatura: "Lenguaje", tema: "cuento" },
      como_abordare: [
        { titulo: "Inicio", detalle: "pregunta ancla" },
        { titulo: "Desarrollo", detalle: "lectura guiada + parejas" },
        { titulo: "Cierre", detalle: "ticket de salida" },
      ],
      supuestos: [{ id: "s1", text: "45 min, fuentes de la carpeta" }],
      questions: [],
    },
    proposalTitle: "Planificación",
    proposal:
      "## Objetivo\nExtraer información explícita e implícita del cuento «El cóndor y el huemul», distinguiendo lo que el texto dice de lo que el lector infiere con evidencia (LEN-4B-OA04).\n\nInicio pregunta. Desarrollo lectura. Cierre ticket.",
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
    warnings: [
      {
        code: "unverified_citation",
        message: "Hay parafraseo del cuento. No lo trates como cita literal.",
        blocking: false,
      },
    ],
    sourceCount: 3,
    thinkingLabel: "leyendo fuentes",
    activityDetail: "cuento-el-condor-y-el-huemul.md",
  },
  2: {
    encargo: {
      rumbo: "crear",
      curso: "1° medio",
      asignatura: "Matemática",
      tema: "sistemas 2×2",
      oa: "",
      duracion: "90 min",
      tipo: "guia",
    },
    plan: {
      objetivo: "Introducir el sistema 2×2 como dos rectas, un punto. Sustitución + verificación.",
      tipo: "guia",
      tipo_label: "guía",
      oa: "",
      duracion: "90 min",
      notas: "",
      titulo: "Plan de guía – sistemas",
      meta: "Plan de trabajo · 1 entregable · Listo",
      resultado_previsto: ["Guía de autoaprendizaje"],
      decisiones: { curso: "1° medio", asignatura: "Matemática", tema: "sistemas 2×2" },
      como_abordare: [
        { titulo: "Selección múltiple" },
        { titulo: "Verdadero o falso" },
        { titulo: "Desarrollo y ruedas" },
      ],
      supuestos: [{ id: "s1", text: "90 min, fuentes de la carpeta" }],
      questions: [],
    },
    proposalTitle: "Guía",
    proposal:
      "## Propósito\nReconocer un sistema 2×2 como dos condiciones a la vez. La solución es el punto donde se cortan dos rectas.\n\nI. Selección múltiple  II. Verdadero o falso  III. Desarrollo.",
    evidence: [
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
        verified: false,
      },
    ],
    warnings: [
      {
        code: "unverified_citation",
        message:
          "2 cita(s) no aparecen textuales. Puede ser parafraseo; no las trates como cita literal.",
        blocking: false,
      },
      {
        code: "missing_structure",
        message: "Faltan apartados esperados para guía: instrucciones. Tú decides s o c.",
        blocking: false,
      },
    ],
    sourceCount: 3,
    thinkingLabel: "leyendo fuentes",
    activityDetail: "vocabulario-algebra.md",
  },
  3: {
    encargo: {
      rumbo: "evaluar",
      curso: "1° medio",
      asignatura: "Matemática",
      tema: "sistemas 2×2",
      oa: "",
      duracion: "45 min",
      tipo: "evaluacion",
    },
    plan: {
      objetivo:
        "Evaluación corta 50 pts: SM, V/F y desarrollo (sustitución y reducción). Sin calculadora.",
      tipo: "evaluacion",
      tipo_label: "evaluación",
      oa: "",
      duracion: "45 min",
      notas: "",
      titulo: "Plan de evaluación – sistemas",
      meta: "Plan de trabajo · 1 entregable · Listo",
      resultado_previsto: ["Evaluación"],
      decisiones: { curso: "1° medio", asignatura: "Matemática", tema: "sistemas 2×2" },
      como_abordare: [
        { titulo: "Selección múltiple" },
        { titulo: "Verdadero o falso" },
        { titulo: "Desarrollo" },
      ],
      supuestos: [{ id: "s1", text: "45 min" }],
      questions: [],
    },
    proposalTitle: "Evaluación",
    proposal:
      "## Ítems de selección múltiple\n¿Qué es un sistema 2×2?\n\n## Verdadero o falso\n## Desarrollo\nSustitución: 2x + y = 12, x − y = 3.",
    evidence: [
      {
        path: "fuentes/vocabulario-algebra.md",
        snippet: "sistema 2×2",
        seccion: "Vocabulario",
        verified: false,
      },
    ],
    warnings: [
      {
        code: "unverified_citation",
        message: "1 cita(s) no aparecen textuales. Puede ser parafraseo; no las trates como cita literal.",
        blocking: false,
      },
    ],
    sourceCount: 3,
    thinkingLabel: "leyendo fuentes",
    activityDetail: "vocabulario-algebra.md",
  },
  4: {
    encargo: {
      rumbo: "adaptar",
      curso: "4° básico",
      asignatura: "Lenguaje",
      tema: "cuento",
      oa: "OA 4",
      duracion: "45 min",
      tipo: "evaluacion",
    },
    plan: {
      objetivo:
        "Prueba corta 10 pts: SM 1–4, V/F 5–6, desarrollo con cita (ítem 7). Misma carpeta del rumbo 1, otro tipo.",
      tipo: "evaluacion",
      tipo_label: "evaluación",
      oa: "OA 4",
      duracion: "45 min",
      notas: "",
      titulo: "Plan de evaluación – cuento",
      meta: "Plan de trabajo · 1 entregable · Listo",
      resultado_previsto: ["Evaluación"],
      decisiones: { curso: "4° básico", asignatura: "Lenguaje", tema: "cuento" },
      como_abordare: [
        { titulo: "Selección múltiple" },
        { titulo: "Verdadero o falso" },
        { titulo: "Desarrollo con cita" },
      ],
      supuestos: [{ id: "s1", text: "45 min" }],
      questions: [],
    },
    proposalTitle: "Evaluación",
    proposal:
      "## Selección múltiple\n¿Quién observa el mar desde la cornisa?\n\n## Verdadero o falso\n## Desarrollo\nEl cóndor afirma: «Yo veo el mar desde aquí».",
    evidence: [
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
        code: "thin_evidence",
        message: "Menos de dos fuentes citadas. El panel de evidencia quedará pobre.",
        blocking: false,
      },
      {
        code: "unverified_citation",
        message: "La cita del ítem de desarrollo es parafraseo. Marcada ?, no ✓.",
        blocking: false,
      },
    ],
    sourceCount: 2,
    thinkingLabel: "leyendo fuentes",
    activityDetail: "cuento-el-condor-y-el-huemul.md",
  },
}

function baseWorkspace(encargo: Encargo, sourceCount: number): AppState {
  return {
    ...initialState(encargo),
    screen: "workspace",
    started: true,
    mode: "offline",
    model: "tero-offline",
    carpeta: CARPETA,
    sourceCount,
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
    statusLine: "5 fuentes",
    recentSessions: [
      {
        kind: "derivado",
        label: "20260910-210457-planificacion-leer-el-cuento-y-distinguir-lo-explicito-de-lo-i-4a5586.md",
        path: "derivados/20260910-210457-planificacion-leer-el-cuento-y-distinguir-lo-explicito-de-lo-i-4a5586.md",
      },
      {
        kind: "derivado",
        label: "20260910-205527-planificacion-leer-el-cuento-y-distinguir-lo-explicito-de-lo-i-e46559.md",
        path: "derivados/20260910-205527-planificacion-leer-el-cuento-y-distinguir-lo-explicito-de-lo-i-e46559.md",
      },
      {
        kind: "derivado",
        label: "20260910-201559-planificacion-leer-el-cuento-y-distinguir-lo-explicito-de-lo-i-2bff17.md",
        path: "derivados/20260910-201559-planificacion-leer-el-cuento-y-distinguir-lo-explicito-de-lo-i-2bff17.md",
      },
    ],
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
    name: "encargo",
    width: 140,
    height: 40,
    state: () => ({
      ...baseWorkspace(rumbos[1].encargo, rumbos[1].sourceCount),
      phase: "idle",
      statusLine: "escribe el encargo",
    }),
  },
]

for (const id of [1, 2, 3, 4] as RumboId[]) {
  const rumbo = rumbos[id]
  shots.push({
    name: `leyendo-${id}`,
    width: 140,
    height: 40,
    state: () => ({
      ...baseWorkspace(rumbo.encargo, rumbo.sourceCount),
      phase: "leyendo",
      thinking: true,
      thinkingLabel: rumbo.thinkingLabel,
      spinnerFrame: 2,
      statusLine: "0.0 s",
      activities: [
        { tool: "list_sources", state: "end" },
        { tool: "read_source", state: "start", detail: rumbo.activityDetail },
      ],
    }),
  })
  shots.push({
    name: `plan-${id}`,
    width: 140,
    height: 40,
    state: () => ({
      ...baseWorkspace(rumbo.encargo, rumbo.sourceCount),
      phase: "esperando_plan",
      planPinned: true,
      plan: rumbo.plan,
      statusLine: "plan listo",
    }),
  })
  shots.push({
    name: `puerta-${id}`,
    width: 140,
    height: 40,
    state: () => ({
      ...baseWorkspace(rumbo.encargo, rumbo.sourceCount),
      phase: "esperando_criterio",
      proposalTitle: rumbo.proposalTitle,
      proposal: rumbo.proposal,
      evidence: rumbo.evidence,
      evidenceIndex: 0,
      warnings: rumbo.warnings,
      planPinned: true,
      plan: rumbo.plan,
      statusLine: "tu turno",
    }),
  })
}

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
  <link rel="stylesheet" href="../../../styles.css?v=outer-win"/>
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
  <script src="../../../tui-grid.js?v=outer-win"></script>
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
  for (const alias of ["plan", "puerta"] as const) {
    copyFileSync(join(outDir, `${alias}-1.json`), join(outDir, `${alias}.json`))
    copyFileSync(join(outDir, `${alias}-1.txt`), join(outDir, `${alias}.txt`))
    copyFileSync(join(outDir, `${alias}-1.html`), join(outDir, `${alias}.html`))
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
