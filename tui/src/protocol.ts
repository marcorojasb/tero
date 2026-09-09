export type Phase =
  | "idle"
  | "home"
  | "leyendo"
  | "proponiendo_plan"
  | "esperando_clarificacion"
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
  rumbo?: string
  tema?: string
}

export type PlanOption = {
  id: string
  label: string
  suggested?: boolean
}

export type PlanQuestion = {
  id: string
  prompt: string
  options: PlanOption[]
  answer?: string | null
  free_text?: string | null
}

export type PlanStep = {
  titulo: string
  detalle?: string
}

export type PlanAssumption = {
  id: string
  text: string
  editable?: boolean
}

export type PlanDeliverable = {
  tipo: string
  label: string
  description?: string
}

export type PlanDecisiones = {
  curso?: string
  asignatura?: string
  tema?: string
}

export type Plan = {
  objetivo: string
  tipo: string
  tipo_label?: string
  oa: string
  duracion: string
  notas: string
  titulo?: string
  meta?: string
  resultado_previsto?: string[]
  decisiones?: PlanDecisiones
  como_abordare?: PlanStep[]
  supuestos?: PlanAssumption[]
  questions?: PlanQuestion[]
  entregables?: PlanDeliverable[]
  status?: string
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
  | { type: "encargo.update"; encargo: Encargo }
  | { type: "rumbo"; rumbo: string }
  | { type: "plan.decide"; decision: "approve" | "edit" | "cancel"; plan?: Partial<Plan> }
  | {
      type: "plan.answer"
      option_id?: string
      text?: string
      question_id?: string
    }
  | { type: "plan.edit_assumption"; id: string; text: string }
  | { type: "gate"; decision: "s" | "n" | "b" | "c"; note?: string }
  | { type: "export"; format: "md" | "docx"; path?: string }
  | { type: "retry" }
  | { type: "shutdown" }
