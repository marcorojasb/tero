import { resolve } from "node:path"
import { launch } from "./app.ts"
import type { Encargo } from "./protocol.ts"

function env(name: string, fallback = ""): string {
  return (process.env[name] ?? fallback).trim()
}

// Home-first: empty encargo unless the teacher (or CLI flags) set context.
const encargo: Encargo = {
  curso: env("TERO_CURSO", ""),
  asignatura: env("TERO_ASIGNATURA", ""),
  oa: env("TERO_OA", ""),
  duracion: env("TERO_DURACION", ""),
  tipo: env("TERO_TIPO", "") || null,
  tema: env("TERO_TEMA", ""),
}

const repoRoot = resolve(import.meta.dir, "../..")
const offline = env("TERO_OFFLINE", "1") !== "0"
const carpeta = env("TERO_CARPETA", resolve(repoRoot, "examples/carpeta-demo"))
const python = env("TERO_PYTHON", "python3")

await launch({ python, repoRoot, offline, carpeta, encargo })
