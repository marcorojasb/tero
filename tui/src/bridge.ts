import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process"
import { resolve } from "node:path"
import type { ClientMessage, Encargo, HostEvent } from "./protocol.ts"

export type Bridge = {
  send: (message: ClientMessage) => void
  close: () => void
}

export function startBridge(opts: {
  python: string
  repoRoot: string
  offline: boolean
  carpeta: string
  encargo: Encargo
  extraArgs?: string[]
  onEvent: (event: HostEvent) => void
  onExit: (code: number | null) => void
}): Bridge {
  const args = ["-m", "tero", "bridge"]
  if (opts.offline) args.push("--offline")
  if (opts.carpeta) args.push("--carpeta", opts.carpeta)
  if (opts.encargo.curso) args.push("--curso", opts.encargo.curso)
  if (opts.encargo.asignatura) args.push("--asignatura", opts.encargo.asignatura)
  if (opts.encargo.oa) args.push("--oa", opts.encargo.oa)
  if (opts.encargo.duracion) args.push("--duracion", opts.encargo.duracion)
  if (opts.encargo.tipo) args.push("--tipo", opts.encargo.tipo)
  if (opts.extraArgs) args.push(...opts.extraArgs)

  const env = { ...process.env, PYTHONPATH: resolve(opts.repoRoot, "src") }
  const child: ChildProcessWithoutNullStreams = spawn(opts.python, args, {
    cwd: opts.repoRoot,
    env,
    stdio: ["pipe", "pipe", "pipe"],
  })

  let buffer = ""
  child.stdout.setEncoding("utf8")
  child.stdout.on("data", (chunk: string) => {
    buffer += chunk
    const lines = buffer.split("\n")
    buffer = lines.pop() ?? ""
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue
      try {
        opts.onEvent(JSON.parse(trimmed) as HostEvent)
      } catch {
        opts.onEvent({ type: "error", message: `JSONL inválido: ${trimmed.slice(0, 120)}` })
      }
    }
  })
  child.stderr.setEncoding("utf8")
  child.stderr.on("data", (chunk: string) => {
    const text = chunk.trim()
    if (text) opts.onEvent({ type: "activity", tool: "host", state: "log", detail: text.slice(0, 160) })
  })
  child.on("exit", (code) => opts.onExit(code))

  return {
    send(message) {
      child.stdin.write(`${JSON.stringify(message)}\n`)
    },
    close() {
      try {
        child.stdin.write(`${JSON.stringify({ type: "shutdown" })}\n`)
      } catch {
        /* ignore */
      }
      child.kill("SIGTERM")
    },
  }
}
