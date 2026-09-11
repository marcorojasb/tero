/**
 * Protocolo host ↔ TUI: agente conversacional.
 * Contrato congelado: /tmp/tero-protocolo.md (PR de TUI).
 *
 * No hay rumbos 1–4, plan tipado (a/e/x), clarificaciones numeradas ni
 * puerta s/n/b/c. La persona escribe; el agente infiere la intención:
 *   a) responder/interactuar → `respuesta`
 *   b) crear material        → `propuesta` → aprobación
 *   c) editar/adaptar        → `propuesta` → aprobación
 */

/** `status.phase` solo toma estos cinco valores. */
export type Phase = "idle" | "pensando" | "esperando_aprobacion" | "listo" | "error"

export type Encargo = {
  curso: string
  asignatura: string
  oa: string
  duracion: string
  tipo: string | null
  notas?: string
  tema?: string
}

export type OAOption = {
  id: string
  curso: string
  asignatura: string
  codigo: string
  eje?: string
  texto_corto: string
  curso_label?: string
  asignatura_label?: string
}

export type Evidence = {
  path: string
  snippet: string
  seccion: string
  /** `verified` lo calcula el host contra el archivo real. */
  verified?: boolean
}

export type WarningItem = {
  code: string
  message: string
  /** Siempre false en el flujo conversacional: nunca impide aprobar. */
  blocking: boolean
}

export type Activity = {
  tool: string
  state: string
  detail?: string
}

export type PropuestaAccion = "crear" | "editar" | "adaptar"

/** Objeto `propuesta` del protocolo. */
export type Propuesta = {
  accion: PropuestaAccion
  tipo: string
  tipo_label: string
  titulo: string
  resumen: string
  /** Markdown que el host escribirá en derivados/. */
  vista_previa: string
  /** Ruta relativa del material editado/adaptado; null si es `crear`. */
  origen: string | null
  cambios: string[]
  notas_nee: string[]
  evidencias: Evidence[]
  warnings: WarningItem[]
}

export type CardStatus = "pendiente" | "aprobado" | "escrito" | "descartado"

export type ThreadRole = "persona" | "agente" | "host"

/** Un mensaje del hilo. `host` son notas del sistema (aprobación, escrito). */
export type Mensaje = {
  id: string
  role: ThreadRole
  text: string
  path?: string
  accion?: string
}

export type RecentSession = {
  label: string
  path: string
  kind: string
}

export type HostEvent = {
  v?: number
  type: string
  [key: string]: unknown
}

export type ClientMessage =
  | { type: "hello"; encargo?: Encargo; carpeta?: string }
  | { type: "prompt"; text: string }
  | { type: "aprobar"; decision: "aprobar" | "descartar"; note?: string }
  | { type: "encargo.update"; encargo: Encargo }
  | { type: "curriculum.list"; curso?: string; asignatura?: string }
  | { type: "export"; format: "md" | "docx" | "latex" | "tex"; path?: string; pdf?: boolean }
  | { type: "retry" }
  | { type: "shutdown" }
