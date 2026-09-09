import { createCliRenderer } from "@opentui/core"
import { startBridge, type Bridge } from "./bridge.ts"
import type { Encargo } from "./protocol.ts"
import { applyHostEvent, handleCommand, handleHotkey, initialState, type AppState } from "./state.ts"
import { mountShell } from "./shell.ts"
import { theme } from "./theme.ts"

export type LaunchOptions = {
  python: string
  repoRoot: string
  offline: boolean
  carpeta: string
  encargo: Encargo
}

export async function launch(opts: LaunchOptions): Promise<void> {
  const renderer = await createCliRenderer({
    exitOnCtrlC: false,
    useMouse: true,
    targetFps: 30,
    backgroundColor: theme.bg,
    consoleMode: "disabled",
  })

  let state: AppState = initialState(opts.encargo)
  let bridge: Bridge | null = null

  const apply = (next: AppState) => {
    state = next
    shell.sync(state)
  }

  const dispatch = (action: ReturnType<typeof handleCommand>) => {
    if (action.kind === "quit") {
      bridge?.close()
      renderer.destroy()
      process.exit(0)
    }
    if (action.kind === "none") {
      apply(action.state)
      return
    }
    if (action.kind === "state") {
      apply(action.state)
      return
    }
    apply(action.state)
    bridge?.send(action.message)
  }

  const shell = mountShell(renderer, (value) => {
    dispatch(handleCommand(state, value))
  })
  shell.sync(state)

  renderer.keyInput.on("keypress", (key) => {
    if (key.ctrl && key.name === "c") {
      dispatch({ kind: "quit" })
      return
    }
    const name = key.name || key.sequence
    if (name === "q" && !shell.input.value && state.uiMode !== "critique" && state.phase !== "esperando_criterio" && state.phase !== "esperando_plan") {
      dispatch({ kind: "quit" })
      return
    }
    const typing = Boolean(shell.input.value) && state.uiMode !== "critique"
    const globalKeys = new Set(["?", "tab", "[", "]", "escape"])
    if (typing && !globalKeys.has(name) && !key.ctrl) {
      return
    }
    const busyInput =
      (state.uiMode === "critique" || (state.phase !== "esperando_plan" && state.phase !== "esperando_criterio")) &&
      name.length === 1 &&
      !key.ctrl
    if (busyInput && !globalKeys.has(name) && state.uiMode !== "critique") {
      return
    }
    if (state.uiMode === "critique" && name !== "escape" && name !== "?") return

    const action = handleHotkey(state, key.ctrl ? `ctrl+${name}` : name)
    if (action.kind !== "none") {
      key.preventDefault?.()
      dispatch(action)
    }
  })

  bridge = startBridge({
    python: opts.python,
    repoRoot: opts.repoRoot,
    offline: opts.offline,
    carpeta: opts.carpeta,
    encargo: opts.encargo,
    onEvent(event) {
      apply(applyHostEvent(state, event))
    },
    onExit(code) {
      if (code && code !== 0) {
        apply({ ...state, lastError: `bridge salió ${code}`, phase: "error", statusLine: `bridge salió ${code}` })
      }
    },
  })
  bridge.send({ type: "hello", encargo: opts.encargo, carpeta: opts.carpeta })

  renderer.on("destroy", () => {
    bridge?.close()
  })
}
