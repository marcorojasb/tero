/** TEMP probe: find the smallest viewport where a captured state renders clean. */
import { createTestRenderer } from "@opentui/core/testing"
import { mountShell } from "../src/shell.ts"
import { shots } from "./capture-frames.ts"

const wanted = process.argv[2] || "propuesta-adaptar"
const shot = shots.find((item) => item.name === wanted)
if (!shot) {
  console.error(`unknown frame: ${wanted}`)
  process.exit(1)
}

for (const rows of [40, 44, 46, 48, 50, 52, 54, 56, 60]) {
  const setup = await createTestRenderer({ width: 140, height: rows })
  const shell = mountShell(setup.renderer, () => {})
  shell.sync(shot.state())
  await setup.renderOnce()
  await setup.waitForVisualIdle({ maxFrames: 8, quietFrames: 2 }).catch(() => {})
  const text = setup.captureCharFrame()
  const lines = text.split("\n")
  const over = lines.filter((line) => Array.from(line).length > 140).length
  const maxLen = Math.max(...lines.map((line) => Array.from(line).length))
  console.log(`rows=${rows} lines=${lines.length} over140=${over} maxLen=${maxLen} last="${lines[lines.length - 1].slice(0, 40)}"`)
  setup.renderer.destroy()
}
