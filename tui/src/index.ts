import { resolve } from "node:path"
import { launch } from "./app.ts"
import type { Encargo } from "./protocol.ts"

function env(name: string, fallback = ""): string {
  return (process.env[name] ?? fallback).trim()
}

const encargo: Encargo = {
  curso: env("TERO_CURSO", "4° básico"),
  asignatura: env("TERO_ASIGNATURA", "Lenguaje y Comunicación"),
  oa: env("TERO_OA", "OA 4"),
  duracion: env("TERO_DURACION", "45 min"),
  tipo: env("TERO_TIPO", "planificacion"),
}

const repoRoot = resolve(import.meta.dir, "../..")
const offline = env("TERO_OFFLINE", "1") !== "0"
const carpeta = env("TERO_CARPETA", resolve(repoRoot, "examples/carpeta-demo"))
const python = env("TERO_PYTHON", "python3")

await launch({ python, repoRoot, offline, carpeta, encargo })
