/**
 * Paint one captured OpenTUI state in a real terminal so we can screenshot it.
 * Usage: bun scripts/show-frame.ts home
 */
import { createCliRenderer } from "@opentui/core"
import { mountShell } from "../src/shell.ts"
import { theme } from "../src/theme.ts"
import { shots } from "./capture-frames.ts"

const name = process.argv[2] || "home"
const shot = shots.find((item) => item.name === name)
if (!shot) {
  console.error(`unknown frame: ${name}`)
  console.error(`frames: ${shots.map((item) => item.name).join(" ")}`)
  process.exit(1)
}

const renderer = await createCliRenderer({
  exitOnCtrlC: true,
  useMouse: false,
  targetFps: 20,
  backgroundColor: theme.bg,
  consoleMode: "disabled",
})
const shell = mountShell(renderer, () => {})
shell.sync(shot.state())
process.stderr.write(`ready ${name} ${renderer.width}x${renderer.height}\n`)
await new Promise<void>(() => {
  /* hold until the screenshot script stops the process */
})
