import { CliRenderEvents, createCliRenderer } from "@opentui/core"
import { startBridge, type Bridge } from "./bridge.ts"
import type { Encargo } from "./protocol.ts"
import {
  applyHostEvent,
  handleCommand,
  handleHotkey,
  initialState,
  keyRoutesToInput,
  type AppState,
} from "./state.ts"
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

  let state: AppState = {
    ...initialState(opts.encargo),
    compact: renderer.width < 100,
  }
  let bridge: Bridge | null = null
  let spinnerTimer: ReturnType<typeof setInterval> | null = null

  const apply = (next: AppState) => {
    state = next
    shell.sync(state)
    if (state.thinking) startSpinner()
    else stopSpinner()
  }

  const startSpinner = () => {
    if (spinnerTimer) return
    spinnerTimer = setInterval(() => {
      if (!state.thinking) {
        stopSpinner()
        return
      }
      state = { ...state, spinnerFrame: state.spinnerFrame + 1 }
      shell.sync(state)
    }, 80)
  }

  const stopSpinner = () => {
    if (spinnerTimer) {
      clearInterval(spinnerTimer)
      spinnerTimer = null
    }
  }

  const dispatch = (action: ReturnType<typeof handleCommand>) => {
    if (action.kind === "quit") {
      stopSpinner()
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

  renderer.on(CliRenderEvents.RESIZE, () => {
    const compact = renderer.width < 100 || renderer.height < 28
    if (compact !== state.compact) {
      apply({ ...state, compact })
    } else {
      shell.sync(state)
    }
  })

  renderer.keyInput.on("keypress", (key) => {
    if (key.ctrl && key.name === "c") {
      dispatch({ kind: "quit" })
      return
    }
    const name = key.name || key.sequence
    // Scrollable help and scrollable thread: PgUp / PgDn (+ Shift+↑↓ in help).
    if (
      state.help &&
      (name === "pageup" || name === "pagedown" || ((name === "up" || name === "down") && key.shift))
    ) {
      key.preventDefault?.()
      shell.scrollHelp(name === "pageup" || name === "up" ? -5 : 5)
      return
    }
    if (!state.help && (name === "pageup" || name === "pagedown")) {
      key.preventDefault?.()
      shell.scrollThread(name === "pageup" ? -5 : 5)
      return
    }
    // While there is text in the input, the keyboard belongs to the person:
    // `?` must land in the message (every Spanish question ends with one).
    if (keyRoutesToInput(name, Boolean(shell.input.value), state.help) && !key.ctrl) return
    if (state.help && name !== "?" && name !== "escape" && name !== "q") return

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
        apply({
          ...state,
          lastError: `bridge salió ${code}`,
          phase: "error",
          statusLine: `bridge salió ${code}`,
          retryable: true,
        })
      }
    },
  })
  bridge.send({ type: "hello", encargo: opts.encargo, carpeta: opts.carpeta })

  renderer.on("destroy", () => {
    stopSpinner()
    bridge?.close()
  })
}
