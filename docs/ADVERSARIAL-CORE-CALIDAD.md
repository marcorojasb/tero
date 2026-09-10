# Adversarial — AgentCore, calidad del material, export

Qué promete tero, qué falló en las corridas Bedrock, qué pedacería de AgentCore
ayudaría de verdad, y qué sería teatro AWS. Sin nuevas reglas pedagógicas:
contratos de host, no recetas de aula.

## Tesis (léela en voz alta)

tero promete **preparar material de aula en la carpeta, con evidencia, y que
el docente decida**. El objetivo final no es “estar en AWS”: es una
**planificación / guía / prueba** que se pueda fotocopiar y usar mañana.

Amazon Bedrock AgentCore es una **plataforma de runtime** (Runtime, Memory,
Gateway, Identity, Observability, Code Interpreter, Browser, Registry). No
enseña, no alinea OA, no arma una ficha. Integrarlo como el sample
multi-agente de AWS **empeora** el producto: mueve la carpeta fuera del
host, parte el HITL, y invita a tools que tero prohibió (escribir
arbitrario, TeX libre, scrapear internet).

La integración honesta es **delgada y opcional**, encima del loop que ya
existe: Strands local + Bedrock Converse + `tero.gate` + plantillas
JSON→LaTeX. Primero se arregla la **disposición** del agente a entregar
el artefacto. Después, si aporta, Observability y Memory de *preferencias
docentes*, nunca como sistema de registro.

## Qué promete vs qué vimos

Promesa (README / AGENTS.md):

- El modelo prepara; la persona da `s` / `n` / `b` / `c`.
- La carpeta es SoR; `fuentes/` no se toca.
- OA del catálogo host, no inventados.
- Export LaTeX/PDF desde JSON/plantilla, no TeX del modelo.
- Español de aula, material usable.

Corridas MiniMax / GLM / Qwen (planificación, guía, evaluación, otros
pedidos):

| Falla | Dónde | No se arregla con |
| --- | --- | --- |
| Qwen escribe `draft_artifact(...)` como prosa (31–184 activity, 0 tool real) | `session._draft_phase` + Strands/Bedrock tool-use | AgentCore Runtime |
| MiniMax entrega **pauta** cuando el rumbo era evaluar/prueba | `draft_artifact` acepta cualquier `tipo` | Memory |
| 1° medio rellena `CIE-5B-OA02` / `LEN-4B-OA04` | `list_oa` vacío → el modelo elige otro nivel | Gateway MCP |
| Markdown→LaTeX pierde SM (`Ítem I:…`), tablas pipe, V/F sueltos | `latex/schemas` + plantillas | Code Interpreter |
| Portada PDF vacía (tcolorbox no partía) | host render | Browser |
| Citas parafraseadas `verified: false` y `s` igual las acepta | diseño HITL | Identity |
| Catálogo 4b–6b; media no existe | `curriculum/chile/catalogo.json` | Registry |

Salvage de texto, transcripciones JSONL, fichas (Nombre/Fecha, cajas SM,
tablas) **ya son host**. Siguen siendo el palanca correcta.

## Inventario AgentCore vs frontera de tero

| Pieza AgentCore | Qué es | ¿Para tero? |
| --- | --- | --- |
| **Runtime** | Contenedor ARM64, `/invocations` + `/ping`, sesión aislada en la nube | **No como SoR.** La carpeta vive en el disco del docente. Un runtime sin montar esa carpeta lee otra cosa. Un runtime que monta S3/EFS convierte `fuentes/` en objeto cloud y rompe el contrato “originales locales, hash”. |
| **Observability** | Trazas del loop (tools, latencia, errores) | **Sí, opcional.** Las transcripciones `.tero/transcripciones/` ya son el SoR local. CloudWatch/X-Ray duplican para debug Bedrock, no reemplazan el JSONL. |
| **Memory** | STM de sesión + hechos a largo plazo por `actor_id` | **Sí, estrecho.** Solo preferencias de *esta* docente / *esta* carpeta (“ticket de salida”, “sin calculadora”). Nunca el markdown del artefacto. El artefacto sigue en `derivados/` tras `s`. |
| **Gateway / MCP** | APIs y Lambdas como tools autenticadas | **No para la carpeta.** `list_sources` / `read_source` deben seguir en-process con sandbox. Un MCP remoto es path escape + otra IAM. |
| **Identity** | JWT / Cognito / 3LO | **Más adelante**, si hay multi-docente. Hoy un proceso local + credenciales Bedrock. |
| **Code Interpreter** | Python sandbox para gráficos/docs | **No para PDF.** El PDF es plantilla host. Darle al modelo un intérprete es otra vez TeX/libre. |
| **Browser / Nova Act** | Navegador headless | **No.** No scrapear MINEDUC ni “completar” el catálogo desde la web. El catálogo es paráfrasis host. |
| **Registry / A2A / multi-agente** | Orquestador + especialistas | **No.** Un segundo agente “redactor” vs “planificador” duplica fases que ya son `plan` / `draft` en el mismo `TeacherSession`. Parte el gate: ¿quién recibe `c`? |

El sample AWS (chatbot + Wikipedia + Tavily + A2A coding) es el **anti-patrón**
de tero: tools de internet, memoria global, runtime como producto.

## Ataques (y la respuesta que no es “más reglas de aula”)

### 1. “Hay que integrar AgentCore para el hackathon / para AWS”

Ataque: el README dice Agents for Humans; sin Core parece incompleto.

Respuesta: el path lean **ya es** Strands → Bedrock. Core no es el modelo.
Meter Runtime para la demo obliga a mentir sobre dónde está la carpeta, o a
subir fuentes a la cuenta. Un juez que abra `fuentes/` vs un bucket gana.

Paso: Observability **opt-in** (`TERO_AGENTCORE_OBSERVE=1`) envolviendo el
`Agent` actual. Cero cambio de tools. Offline intacto.

### 2. “Multi-agente: uno planifica, otro redacta, otro exporta”

Ataque: las fases ya existen; partámoslas en A2A.

Respuesta: el fallo de Qwen no fue “faltaba un redactor”. Fue **no llamar
la tool**. Tres agentes × el mismo bug = triple costo y un gate confuso.
El export no es un agente: es `repair_payload` + plantilla.

### 3. “Hardcodea más headings / más OA / más pedagogía en el prompt”

Ataque: si MiniMax no pone `## Propósito`, añade otra regla.

Respuesta: cada regla de markdown es un parser más. El modelo ya escribe
ítems; el host no los reconoce. **Disposición** = el contrato de la tool,
no la receta:

- `draft_artifact` debe aceptar **payload schema** (los campos de
  `templates/latex/schemas/*.json`) *además* del markdown. El markdown
  queda para la TUI; el JSON es lo que exporta. Así no hay que adivinar
  `Ítem I: Selección múltiple`.
- `list_oa` con cero filas debe decir `cubierto: false` y **prohibir**
  elegir un id de otro curso. Hoy devuelve `[]` y el modelo improvisa
  `CIE-5B`. Eso no es pedagogía; es honestidad del catálogo.
- `draft_artifact(tipo=…)` si el encargo ya trae tipo/rumbo, **el host
  conserva el tipo del plan aprobado** y deja el otro como nota (“el
  modelo pidió pauta; el rumbo era prueba”). El docente decide con `c`
  si quiere pauta aparte. No es “nunca hagas pauta”.
- Tope de tools en fase draft: si no hay `pending_draft`, salvage de
  texto (ya) y corte. No 184 `cite_evidence`.

Eso es disposición a cumplir el loop, no una guía MINEDUC pegada al
system prompt.

### 4. “El PDF se arregla con un Code Interpreter que genere LaTeX”

Ataque: las fichas feas son culpa de plantillas rígidas.

Respuesta: vintage-latex y `exam.cls` como documentclass pelean con
pdfLaTeX y con “el modelo no emite TeX”. La calidad visual se gana
**llenando bien el JSON** (SM con opciones, V/F, tablas, propósito
corto) y **render host** (cajas, líneas, omitir vacíos). Un intérprete
que compile TeX del modelo reabre `\write18`.

### 5. “Memory para que tero ‘aprenda’ de las transcripciones”

Ataque: ya hay JSONL; súbelo a AgentCore Memory.

Respuesta: las transcripciones son para **nosotros** (y para un
`tero analyze` local): loops de tools, tipo desviado, OA inventado.
Subir el delta completo a Memory mete el cuento y datos de curso en
un servicio AWS. Si hay Memory: namespace
`/docente/{id}/carpeta/{hash}/preferencias` con frases cortas que el
docente ya dijo en `c` (“más evidencia, menos adorno”). El JSONL
sigue en `.tero/transcripciones/`.

### 6. “Warnings no bloquean `s`, entonces no hay calidad”

Ataque cierto. Es el thesis: prepare, don’t decide.

Respuesta: no bloquees `s`. **Sí** haz que la puerta muestre el costo
de aceptar: tipo ≠ rumbo, OA de otro nivel, SM vacío al exportar
evaluación, 0 citas verificadas. El docente sigue siendo el gate; tero
deja de sonreírle al esqueleto.

## Disposición (lo que hay que construir, en orden)

Contratos de host, medibles en transcripción + PDF, sin nuevas normas
de “cómo se enseña”.

1. **Entregar el artefacto** — tool schema + salvage + corte de loop.
2. **Decir el tipo que el rumbo pidió** — o avisarlo en la puerta.
3. **No rellenar el catálogo** — `cubierto: false` en media / otras
   asignaturas hasta que el JSON exista.
4. **Export = schema, no arqueología de markdown** — `draft_artifact`
   con `payload_json`; el extract markdown queda de fallback.
5. **Ficha** — seguir el camino plantilla (tablas, V/F, claves al
   final). Nada de TeX del modelo.
6. **Ver la sesión** — JSONL ya; opcionalmente traza AgentCore.
7. **Recordar al docente, no al alumno** — Memory estrecho o, más
   barato, reutilizar `.tero/criticas/` + feedback sidecar.

## Siguientes pasos (secuencia)

No estimar calendario. Cada paso es un cambio de contrato o de
export, comprobable con `pytest` + una corrida Bedrock corta (GLM
basta para el loop; MiniMax para calidad de prosa).

### P0 — el loop entrega lo que promete (sin AgentCore)

1. `draft_artifact(..., payload_json="")`  
   Si viene JSON de guía/evaluación/plan, `repair_payload` y se guarda
   junto al markdown (front matter o sidecar). El export **prefiere**
   ese JSON. El modelo deja de depender de `##`.
2. `list_oa` / `get_oa`  
   Respuesta explícita `catalog_covers: false` cuando el curso no está
   (1° medio). Prohibido devolver OA de otro `curso` “por si acaso”.
   Warning de puerta `oa_wrong_level` (ya existe) visible en TUI.
3. Tipo del plan  
   Al aprobar el plan, `draft_artifact` que llegue con otro tipo no
   pisa el `turn.plan.tipo`; se emite aviso `tipo_desviado`. El
   docente `c` si quiere el otro entregable.
4. Corte de draft  
   Además del salvage: máximo de tools en fase `draft` (p. ej. 16)
   entonces salvage o `no_draft`. Qwen a 67 `cite_evidence` no es
   “esmerado”: es loop.
5. Export evaluación  
   SM/V-F/desarrollo desde el payload, no desde `### 1. (3 puntos)`
   perdido en instrucciones. El markdown sigue siendo legible en TUI.

### P1 — calidad del material y de la ficha (sigue sin Core)

6. Modelos de trabajo  
   Default documentado: GLM 4.7 Flash para iterar; MiniMax M2.5 para
   material que se va a `s`. Nova Lite sigue en el README como
   checklist free-tier, no como techo de calidad. `TERO_MODEL` ya
   existe: no hardcodear tres ids en el código, sí en `.env.example`.
7. Ficha  
   V/F sin ítems basura (“Justificación:”); ejemplos sin cercos
   \`\`\`; propósito corto en la caja (el vocabulario/tabla puede ir
   **fuera** del tcolorbox para que no se trague la guía entera).
8. Transcripción → mejora  
   Un comando local `tero inspect` (o script en `docs/`) que cuente
   por JSONL: tools, salvage, tipo, OA, `verified`. Eso es el banco
   de pruebas. No hace falta Memory para empezar.
9. Puerta honesta  
   Mostrar avisos que ya calcula `collect_warnings` **antes** de `s`,
   con una línea de costo (“OA de básica en un 1° medio”). Sigue sin
   bloquear.

### P2 — AgentCore delgado (solo si P0 está verde)

10. Observability opt-in  
    Envolver el `Agent` Strands con el exporter de AgentCore / GenAI
    observability. Misma `TeacherSession`. Métrica de éxito: se ve el
    loop de Qwen en una traza **y** en el JSONL local.
11. Memory opt-in, namespace docente  
    Guardar texto de `c` y supuestos que el docente editó. Recuperar
    al `start_turn` como *notas*, no como fuentes. IAM y datos: no
    subir `fuentes/`.
12. No Runtime, no Gateway de carpeta, no Browser, no Code Interpreter,
    no A2A, hasta que el docente pida tero **en un servidor** (otra
    tesis: entonces la carpeta se monta con consentimiento, no por
    el sample).

### P3 — diferido a propósito

- Catálogo media / otras asignaturas: **contenido**, no un scrape.
- CI Bedrock smoke barato (GLM, un turno, `--yes`, carpeta fixture).
- Viewer de evidencia con `start_line`.
- AgentCore Identity (multi-usuario).

## Criterio de “calidad de verdad”

Un material es bueno para tero si, en una carpeta real y un rumbo:

1. Hay **borrador** en la puerta (tool o salvage), no un error `no_draft`.
2. El **tipo** coincide con rumbo/plan, o el aviso está a la vista.
3. Las **citas** tienen path de la carpeta; al menos dos `verified`
   o el docente ve las `?`.
4. El **PDF** tiene encabezado de estudiante, ítems marcables, y no
   secciones “(sin ítems)”.
5. `fuentes/` no cambió.

Si eso no se cumple, AgentCore no lo disimula. Si se cumple, Core es
un extra de traza y memoria docente, no el producto.

## Relación con docs previos

- [ANALISIS-ADVERSARIAL.md](ANALISIS-ADVERSARIAL.md) — elegibilidad,
  HITL, TUI. El defer “no AgentCore” de video-day se **precisa** aquí:
  no Runtime/multi-agente; sí Observability/Memory estrechos *después*
  de P0.
- [ADVERSARIAL-LATEX-CURRICULO.md](ADVERSARIAL-LATEX-CURRICULO.md) —
  JSON→plantilla. Este doc añade: el JSON debe nacer en
  `draft_artifact`, no en un parser de headings.
- Transcripciones de bakeoff: `.tero/transcripciones/` en cada
  carpeta de corrida; copias de análisis en artefactos del agente.
