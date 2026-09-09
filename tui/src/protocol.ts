export type Phase =
  | "idle"
  | "leyendo"
  | "proponiendo_plan"
  | "esperando_plan"
  | "escribiendo"
  | "esperando_criterio"
  | "exportando"
  | "listo"
  | "error"

export type Encargo = {
  curso: string
  asignatura: string
  oa: string
  duracion: string
  tipo: string | null
  notas?: string
}

export type Plan = {
  objetivo: string
  tipo: string
  tipo_label?: string
  oa: string
  duracion: string
  notas: string
}

export type Evidence = {
  path: string
  snippet: string
  seccion: string
  verified?: boolean
}

export type WarningItem = {
  code: string
  message: string
  blocking: boolean
}

export type Activity = {
  tool: string
  state: string
  detail?: string
}

export type TurnSummary = {
  id: string
  prompt: string
  phase: string
  tipo?: string
  titulo?: string
  path?: string
}

export type HostEvent = {
  v?: number
  type: string
  [key: string]: unknown
}

export type ClientMessage =
  | { type: "hello"; encargo?: Encargo; carpeta?: string }
  | { type: "prompt"; text: string }
  | { type: "encargo.update"; encargo: Encargo }
  | { type: "plan.decide"; decision: "approve" | "edit" | "cancel"; plan?: Partial<Plan> }
  | { type: "gate"; decision: "s" | "n" | "b" | "c"; note?: string }
  | { type: "export"; format: "md" | "docx"; path?: string }
  | { type: "shutdown" }
