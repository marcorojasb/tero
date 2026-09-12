# Agents for Humans (AWS × Devpost) — reglas, puntaje y plan de 72 horas

Investigación competitiva para **tero**. Cierre: **lunes 14 de septiembre de 2026, 17:00 PDT**
= **00:00 UTC del 15 de septiembre** = **21:00 hora de Chile continental** (UTC-3).

Hoy: viernes 11 de septiembre de 2026. Quedan **~72 horas**.

Fuentes primarias: [portada](https://agentsforhumans.devpost.com/),
[rules](https://agentsforhumans.devpost.com/rules),
[FAQ](https://agentsforhumans.devpost.com/details/faqs),
[resources](https://agentsforhumans.devpost.com/resources),
[updates](https://agentsforhumans.devpost.com/updates).

---

## 0. Resumen ejecutivo

| Decisión | Respuesta | Por qué |
| --- | --- | --- |
| Track | **Professional Agents** | El usuario primario es *una o un docente*. El brief de Resources nombra textualmente "a teacher turning one lesson into materials for thirty different students". |
| ¿Chile es elegible? | **Sí** | Chile **no** aparece en la lista de países excluidos. |
| ¿AgentCore es obligatorio? | **No** | "it's not required" (Rules §4 y FAQ). |
| ¿Basta Strands + Bedrock? | **Sí para ser elegible**, con desventaja parcial | 6 de 8 ganadores del hackathon AWS 2025 usaron AgentCore → compensar con §3.3 |
| ¿Bedrock es obligatorio? | **No en la letra** | Strands es model-agnostic. Bedrock es la ruta *demostrable* de AWS. |
| ¿Nova da bonus? | **No** | `\bNova\b` = 0 ocurrencias en Rules/FAQ/Resources. Es nuestra elección técnica, no un requisito. |
| **Qué sube más el puntaje técnico** | **Patrón `Graph` de Strands + OpenTelemetry** | §3.3 — y `Graph` es literalmente "approvals, or quality gates", o sea la puerta de tero |
| ¿El repo tiene que ser público? | **Sí** | Regla dura. Ya lo es, con MIT detectable. |
| **El hallazgo que manda** | **Los jueces no instalan nada** | Rules: "Judges are not required to test the Project and may choose to judge based solely on the text description, images, and video provided." → **el video y la descripción SON el submission.** |
| Palanca #1 en 72 h | **Grabar el video** | Es 1 de 5 criterios y es el único vehículo de los otros 4. |
| Palanca #2 | **Post bonus en builder.aws.com** | Hasta **+0.6** sobre una base de 5.0 (≈ +10,7 % del máximo). Texto ya escrito, falta publicar. |
| Palanca #3 | **About del repo + diagrama** | Trivial de hacer, y sin ello se pierde en la revisión de encuadre (*Stage One*). |

---

## 1. Reglas y requisitos obligatorios

### 1.1 Fechas

| Hito | Fecha | Fuente |
| --- | --- | --- |
| Periodo de submission | 10 ago 2026 09:00 PT → **14 sep 2026 17:00 PT** | [Rules §1](https://agentsforhumans.devpost.com/rules) |
| Juicio | 15 sep → 8 oct 2026 | [Rules §1](https://agentsforhumans.devpost.com/rules) |
| Ganadores | ~14 oct 2026 14:00 PT | [Rules §1](https://agentsforhumans.devpost.com/rules) |
| Créditos USD 50 | formulario hasta **11 sep 12:00 PT** — *ya vencido* | [Rules §4](https://agentsforhumans.devpost.com/rules), [FAQ](https://agentsforhumans.devpost.com/details/faqs) |

> **Créditos: no cuentes con ellos.** [Resources](https://agentsforhumans.devpost.com/resources) dice
> textualmente *"All credits for this hackathon have been disbursed."* Además
> [docs/AWS-GRATIS.md](../AWS-GRATIS.md) ya advierte que el **Free plan no es
> elegible para créditos promocionales**. No es bloqueante: Nova Lite sobre Free
> Tier alcanza para grabar el video y para las corridas de jueces.

### 1.2 Elegibilidad

- Mayoría de edad en el país de residencia; individuos, equipos u organizaciones.
- **Sin límite de integrantes** (FAQ: *"There's no limit on team size"*).
- **Chile es elegible.** Los excluidos son: Argentina, Australia, Brasil, Hong Kong,
  Indonesia, Italia, Malasia, Filipinas, Tailandia, Vietnam, Singapur, Bielorrusia,
  DNR, LNR, EAU, Quebec, Rusia, Crimea, Cuba, Irán, Corea del Norte, Siria.
  ([Rules §3](https://agentsforhumans.devpost.com/rules))
- Prohibido: empleados/jueces de AWS y Devpost, y proyectos con **soporte financiero
  o preferencial del Sponsor previo al cierre**. Los USD 50 del hackathon están
  ofrecidos *para* construir el proyecto, así que no caen aquí.

### 1.3 Qué es OBLIGATORIO en el submission

Fuente: [Rules §4 "Submission Requirements"](https://agentsforhumans.devpost.com/rules) y [FAQ](https://agentsforhumans.devpost.com/details/faqs).

| # | Requisito | Letra de la regla | Estado en tero |
| --- | --- | --- | --- |
| 1 | **Proyecto nuevo** | *"Projects must be newly created during the Submission Period"* (10 ago – 14 sep) | ✅ Primer commit `c66655c` = **9 sep 2026**, dentro de la ventana |
| 2 | **Strands Agents SDK** | *"Build a new AI agent with Strands Agents"*; *"Name Strands Agents explicitly — it's one of the first things reviewed"* ([update](https://agentsforhumans.devpost.com/updates/46174-pro-tips-for-your-project)) | ✅ `strands-agents>=1.40.0`, `strands.Agent`, `strands.models.Model` |
| 3 | **Cuenta AWS + Strands instalado** | Rules §4 pasos 2–3 | ✅ Free plan us-east-1 |
| 4 | **Descripción de texto** | *"explain the features and functionality"*; *"Lead with the problem"* | ✅ borrador EN en [DEVPOST.md](../hackathon/DEVPOST.md) |
| 5 | **Repo PÚBLICO** | GitHub/GitLab/Bitbucket; *"must contain all necessary source code, assets, and instructions required for the project to be functional"* | ✅ `github.com/marcorojasb/tero` público |
| 6 | **Licencia MIT o Apache** | *"include MIT/Apache open source license by including an open source license file. This license should be detectable and visible at the top of the repository page (in the About section)"* | ✅ `LICENSE` MIT + GitHub la detecta (`licenseInfo.key = mit`) |
| 7 | **README** | Requisito explícito | ✅ [README.md](../../README.md) |
| 8 | **Diagrama de arquitectura** | Requisito explícito + contenido mínimo en FAQ | ⚠️ existe, hay que actualizarlo (ver §3.6) |
| 9 | **Video ≤ 5 min, público en YouTube o Vimeo** | Debe incluir **demo funcionando** + pitch con (1) problema, (2) para quién, (3) por qué importa | ❌ **FALTA — es lo más caro y lo más importante** |
| 10 | **AWS Builder ID** | Se pide el **email** con que se creó en `profile.aws.amazon.com` | ❌ **FALTA** |
| 11 | **Idioma inglés** | *"All Submission materials must be in English or… the Entrant must provide an English translation of the demonstration video, text description, and testing instructions"* | ⚠️ **DUDOSO** — ver §5.3 |
| 12 | **Divulgación de código previo** | *"must disclose any other pre-existing code or work incorporated into the Project"* | ✅ hay disclosure, hay que **elevarlo** (ver §6) |
| 13 | **Un solo track** | *"your Project may only fall into one track"* | ✅ Professional Agents |
| 14 | **Acceso para juicio** | *"Access must be provided… free of charge and without any restriction"* | ⚠️ repo público lo cubre; el link vivo ayuda |

### 1.4 Opcionales que suman

| Opcional | Efecto | Fuente |
| --- | --- | --- |
| **Link a demo viva** | *"this will help your Project score better in the Technical Implementation Judging Criteria"* | [Rules §4](https://agentsforhumans.devpost.com/rules) |
| **Post en builder.aws.com** con *"Agents for Humans"* en el título | **+0.2 cada uno, máximo +0.6**; el score final va de 1 a 5.6 | [Rules §6](https://agentsforhumans.devpost.com/rules) |
| Despliegue en **AgentCore** | *"will strengthen your Technical Implementation score, but it's not required"* | [Rules §4](https://agentsforhumans.devpost.com/rules), [FAQ](https://agentsforhumans.devpost.com/details/faqs) |

> **Sobre el post bonus:** las reglas se actualizaron el **12 ago 2026** para
> **eliminar el requisito del hashtag `#AgentsforHumans`** (*"Updated 8/12/26 to remove
> requirement of #AgentsforHumans in Blog Post Bonus Submission items"*). Lo que sí
> sigue siendo obligatorio es que **el título contenga "Agents for Humans"**. El
> hashtag es inofensivo, pero no lo cuentes como requisito — y no dejes que un hashtag
> faltante te haga reescribir el post.
>
> **Es la palanca más barata del hackathon:** hasta **+0.6** sobre una base de 5.0
> (≈ **+12 %**), y `docs/hackathon/BUILDER-POST.md` **ya está escrito**. Se pueden
> publicar hasta 3 posts (0.2 cada uno).

### 1.5 Límites y letra chica

- **Video:** máximo **5 minutos**, público en YouTube o Vimeo. Slides, screen recording
  y voiceover son aceptables; no hay que salir en cámara.
- **Equipo:** sin límite. Si es equipo u organización, se nombra **un Representative**.
- **Licencias:** MIT o Apache, con archivo, detectable en el About.
- **Código previo:** frameworks, librerías, starter templates y asistentes de IA
  están permitidos; **cualquier otro código o trabajo previo incorporado se divulga**.
  FAQ: *"The project itself needs to be newly created during that window, not an
  existing project you're repackaging"* y *"when in doubt, disclose it."*
- **Terceros:** hay que estar autorizado a usar cada SDK/API/dato según sus términos.
  Open source es aceptable si se cumplen las licencias y el envío **construye sobre**
  el producto subyacente.
- **PII:** *"We recommend against it"* — usar datos sintéticos, anonimizados o
  públicos. El submission es responsable de tener derecho a lo que muestra.
- **Múltiples submissions:** permitidas, pero cada una *"unique and substantially
  different"*.
- **Modificaciones:** después del cierre **no se puede cambiar el submission**.

---

## 2. Criterios de evaluación → evidencia → acción en 72 h

### 2.1 Cómo se puntúa

**Stage One (pass/fail).** *"whether the ideas meet a baseline level of viability, in
that the Project reasonably fits the theme and reasonably applies the required
tools/APIs/SDKs."* → Si un juez no ve **Strands** claro, no se llega a Stage Two.

**Stage Two.** Cinco criterios **de igual peso**. Score final **1 a 5.6**
(5.0 de base + hasta 0.6 de bonus).

**Desempate:** gana quien tenga más puntaje en el **primer criterio listado =
Technical Implementation**.

### 2.2 Tabla criterio → evidencia → acción

| Criterio (peso 1/5 c/u) | Qué mira el juez (texto oficial) | Evidencia concreta que ya existe en tero | Acción en 72 h | Quién |
| --- | --- | --- | --- | --- |
| **1. Technical Implementation** ⭐ *desempate* | *"How thoroughly and skillfully does the project use Strands Agents? Does the code reflect genuine effort and a working, non-trivial implementation? A live demo and/or AWS AgentCore deployment will strengthen this score."* | `strands.Agent` real; `OfflineModel(Model)` es un **`Model` de Strands de verdad** (`src/tero/offline.py:20`); `BedrockModel` + Nova Lite (`src/tero/session.py:41`); 9 tools host-side; loop agéntico con tools→reasoning→draft; bridge JSONL; 143 tests verdes | (a) **Patrón multi-agente `Graph`** para la puerta de aprobación — ver §3.3; (b) **OpenTelemetry** (`strands-agents[otel]`); (c) **diagrama que muestre el loop Strands** (model→tools→reasoning→response) — lo pide el FAQ; (d) sección EN "Where Strands is used" con rutas y líneas; (e) demo viva en el About; (f) lane AgentCore **delgada y honesta** *solo si sobra tiempo* | Agente (a–d) / Humano (e) |
| **2. Design** | *"Does the project deliver a complete, coherent product experience and not just a technical proof of concept?"* | TUI OpenTUI real en una ventana, virtualizada en Pages; carpeta como sistema de registro; avisos que no bloquean | **Mostrar la TUI en el video, no solo la CLI.** El demo `--offline` es texto plano: no es el mejor escaparate del criterio | Humano (grabar) |
| **3. Potential Impact** | *"Does the project make a credible, specific case for solving a real problem for a real audience, and does the solution actually address that problem based on what's demonstrated?"* | Un docente, una carpeta, 4°–6° básico, catálogo OA Chile, material fotocopiable al día siguiente | **Abrir el video con el problema, no con la arquitectura.** Una frase concreta: "el domingo a las 22:00 convirtiendo una clase en treinta guías". Cerrar con el antes/después | Humano (guion/voz) |
| **4. Creativity & Originality** | *"Is this a creative, non-obvious use of Strands Agents and does the team demonstrate genuine understanding of the problem space?"* | La puerta humana **estructural** (el modelo nunca escribe; escribe `tero.gate`), hash SHA-256 de originales, citas verificadas contra el archivo, offline como `Model` real | Nombrar explícitamente **por qué** el diseño es no obvio: *el agente no decide, prepara*. Es el diferenciador contra "otro chatbot que habla de pedagogía" | Agente (texto) |
| **5. Presentation** | *"Does the video clearly demonstrate the project working end-to-end? Does the pitch communicate what problem is solved, who it's for, and why it matters? Is the overall presentation easy to follow?"* | [VIDEO.md](../hackathon/VIDEO.md) tiene guion minuto a minuto, en inglés | **Grabar. Editar. Subir público.** Ensayar que quepa en <5:00. Es el criterio con **100 % de control** y el que más se descuida | **Humano** |

> **La asimetría clave:** los otros cuatro criterios **solo se comunican a través del
> video y la descripción**. Un proyecto excelente con un video mediocre pierde en
> cuatro frentes a la vez.

---

## 3. ¿Qué premia AWS realmente?

### 3.1 Strands es el eje — nombrado y visible

Dos avisos oficiales de los organizadores, no interpretación nuestra:

- *"Name Strands Agents explicitly — it's one of the first things reviewed."*
  ([Pro tips for your project](https://agentsforhumans.devpost.com/updates/46174-pro-tips-for-your-project))
- *"Make your use of Strands Agents impossible to miss. Name it in your project
  description, add it to your 'Built With' section, and show it clearly in your demo
  video."* ([How to actually stand out](https://agentsforhumans.devpost.com/updates/45987-how-to-actually-stand-out-in-agents-for-humans))

**Acción:** "Strands Agents SDK" debe aparecer en la descripción de Devpost, en el
"Built with", en el video y en el diagrama. tero ya lo hace en README y DEVPOST.md.

### 3.2 AgentCore: cuánto pesa de verdad

La regla es literal y está en dos lugares:

> *"Deploying with Amazon Bedrock AgentCore is a smart architectural choice and will
> strengthen your **Technical Implementation** score, but it's not required."*
> — [Rules §4](https://agentsforhumans.devpost.com/rules) y [portada](https://agentsforhumans.devpost.com/)

> *"Q: Do I need to use AWS AgentCore? A: **No.** AgentCore is encouraged and will
> strengthen your Technical Implementation score, but it's not required. Build with
> Strands Agents as your foundation and deploy however works for you."*
> — [FAQ](https://agentsforhumans.devpost.com/details/faqs)

**Lectura cuantitativa honesta:**

- No es un criterio propio. Afecta **a uno de cinco** criterios, y ahí es un
  *fortalecedor*, no un interruptor.
- La frase es un **OR**: *"A live demo **and/or** AWS AgentCore deployment"*. El link
  a demo viva satisface el mismo estímulo y es lo que tero puede cumplir de verdad.
- Techo del riesgo/beneficio: un despliegue apresurado de Runtime en 72 h aporta una
  fracción de 1/5 del puntaje, y a cambio arriesga romper la tesis del producto
  (la carpeta local es el sistema de registro) y quemar créditos.
  Hay fricción real y documentada en el propio foro del hackathon
  ([AgentCore Runtime quota stuck at 0](https://agentsforhumans.devpost.com/forum_topics/44925-agentcore-runtime-quota-stuck-at-0),
  solo título verificable), así que desplegar Runtime a última hora es el peor uso
  posible de las horas.
- **Pero seamos honestos con la evidencia:** en el hackathon AWS comparable
  (**AWS AI Agent Global Hackathon**, sep–oct 2025, 9 466 participantes, USD 45 000,
  [portada](https://aws-agent-hackathon.devpost.com/)), **6 de los 8 ganadores usaron
  AgentCore**, incluido el 1.er lugar (*EcoLafaek*) y el premio *Best Strands SDK
  Implementation* (*AgentShell*). Sí existe un top-3 sin AgentCore: el 2.º lugar
  (*AegisAgent*, `aws-bedrock` + `nova-pro` + Kiro,
  [ficha](https://devpost.com/software/aegisagent-an-insurance-claim-app-fully-developed-by-kiro)).
  (Aviso metodológico: los "Built With" son autodeclarados, así que la ausencia de la
  etiqueta no *prueba* que no se usara.)
  → **Omitir AgentCore es una desventaja real pero parcial**, no un descalificador.
- **Conclusión operativa:** Strands + Bedrock sin AgentCore es compliant y puede
  puntuar bien, pero esa desventaja hay que compensarla **en el mismo criterio**, por
  la vía del **live demo** y de §3.3. Si se hace AgentCore, que sea **delgado y
  honesto** (una captura del harness con Nova Lite, sin Browser/Code Interpreter), tal
  como ya está documentado en [AWS-GRATIS.md](../AWS-GRATIS.md) y
  [harness-playground.md](../hackathon/harness-playground.md).

### 3.3 Cómo subir Technical Implementation (el criterio de desempate)

Es el **primer criterio** y por lo tanto el que rompe empates. Tres adiciones
concretas, todas oficiales, ordenadas por puntaje esperado por hora:

**1. Nombrar un patrón multi-agente de Strands — recomendado `Graph`.**
El criterio pregunta literalmente *"How thoroughly and skillfully does the project use
Strands Agents?"*, y la orquestación multi-agente es el titular de Strands 1.0.
`Graph` encaja casi sospechosamente bien con tero, porque la descripción oficial de
AWS es: *"Graphs let you define explicit agent workflows with conditional routing and
decision points, helpful for processes that require specific steps, **approvals, or
quality gates**."* — es exactamente la puerta humana de tero.
Docs: [Graph](https://strandsagents.com/docs/user-guide/concepts/multi-agent/graph/) ·
[patrones multi-agente](https://strandsagents.com/docs/user-guide/concepts/multi-agent/multi-agent-patterns/) ·
[Agents as Tools](https://strandsagents.com/docs/user-guide/concepts/multi-agent/agents-as-tools/)
(`delegate: true`) · [Swarm](https://strandsagents.com/docs/user-guide/concepts/multi-agent/swarm/) ·
[Workflow](https://strandsagents.com/docs/user-guide/concepts/multi-agent/workflow/).
⚠️ No inventar nombres de patrón: "Handoffs" y "Autonomous agent" **no** tienen página
propia (Handoffs vive dentro de Swarm, y en el blog de 1.0 significa agente→**humano**).

**2. Observabilidad OpenTelemetry real.** `pip install 'strands-agents[otel]'` +
`from strands.telemetry import StrandsTelemetry`
([docs](https://strandsagents.com/docs/user-guide/observability-evaluation/observability/)).
Es barato, oficial, y es la **única capacidad del perímetro de AgentCore obtenible sin
desplegar AgentCore** (cubre su "Observability"). Además los traces alimentan
directamente el diagrama obligatorio y el video.

**3. Un live demo que funcione sin instalar nada.** Las reglas dicen que el link
*"will help your Project score better in the Technical Implementation Judging
Criteria"*. Mínimo viable: la página de Pages con transcripciones reales capturadas +
el diagrama + el video embebido. Nota honesta: eso es *"a link to a website"*, no un
*"functioning demo"* — nadie ha bendecido ni prohibido explícitamente un sitio
estático como live demo. Si sobra tiempo, un runner mínimo que ejecute el agente
**real** sobre datos sintéticos vale más.

**Bonus de bajo costo: MCP.** Strands soporta herramientas MCP
([docs](https://strandsagents.com/docs/user-guide/concepts/tools/mcp-tools/),
transportes stdio / Streamable HTTP / SSE). Es oficial, barato, y `mcp` estaba en el
stack del ganador a *Best Strands SDK Implementation* del hackathon 2025.

### 3.4 Amazon Nova

**No hay bonus por Nova.** Verificado de forma programática sobre Overview, Rules,
FAQ, Dates, Updates y Resources: `\bNova\b` = **0 ocurrencias** (los dos falsos
positivos por página son la subcadena dentro de *"innovation"*). Tampoco hay track,
ni premio, ni preferencia por Nova. Es más: **"Bedrock" aparece una sola vez por
página y en 4 de 5 casos dentro de la frase "Amazon Bedrock AgentCore"** — nunca como
requisito independiente. Lo único técnicamente obligatorio es **Strands**.

Nova Lite sigue siendo una decisión de costo/velocidad defendible para tero.
Menciónalo en "Built with" porque es verdad y refuerza el uso de Bedrock; no esperes
puntos extra por ello.

> Contraste histórico: en el hackathon AWS de 2025 **sí** había un premio de USD 3 000
> a *Best Amazon Nova Act Integration* y Nova aparecía en 4 stacks ganadores. **Esta
> vez no.** No diseñes para Nova pensando en un bonus que no existe.

### 3.5 La única cosa realmente obligatoria: Strands

De Rules §4: *"Build a new AI agent with Strands Agents that does real work for real
people"*, y en el paso 2 de How-To-Enter: *"Install the Strands Agents SDK"*.
El SDK es **provider-agnostic** (*"the same agent code runs against any supported
provider"*, [docs](https://strandsagents.com/docs/user-guide/concepts/model-providers/)),
y el manager del hackathon confirmó a un participante con Bedrock bloqueado que
*"Your project stays eligible if you build it with Strands Agents and a different
model host"*
([hilo](https://agentsforhumans.devpost.com/forum_topics/44937-bedrock-model-access-blocked-account-wide-anyone-else)).
tero usa Bedrock igual, así que esto no cambia nada — pero confirma que **la apuesta
segura es Strands, no Bedrock**.

### 3.6 El diagrama de arquitectura (requisito subestimado)

El FAQ publica el contenido mínimo esperado:

- **User input/interface** — cómo interactúa la persona (aquí: TUI OpenTUI + bridge JSONL)
- **Strands Agents** — *"the core agent and its agentic loop (model → tools → reasoning → response)"*
- **Tools & integrations** — APIs, datasets, servicios externos
- **AWS services used** — *"Bedrock, Lambda, S3, DynamoDB, AgentCore, etc. — whatever's in your stack"*
- **Output** — qué devuelve el agente

`docs/hackathon/architecture.png` (1680×820, PNG válido) existe y
`render_architecture.py` lo regenera, pero **está acoplado al flujo antiguo**
(menciona `s / n / b / c`). Hay que regenerarlo cuando se congede el flujo final.

---

## 4. Checklist de submission LISTO / FALTA / DUDOSO

Rutas relativas a la raíz del repo. Verificado contra `origin/main` (`2b2e76a`).

### 4.1 Obligatorios

| Estado | Ítem | Ruta / evidencia |
| --- | --- | --- |
| ✅ **LISTO** | Proyecto nuevo en ventana | primer commit `c66655c`, 9 sep 2026 |
| ✅ **LISTO** | Repo público | `github.com/marcorojasb/tero`, `isPrivate: false` |
| ✅ **LISTO** | Licencia MIT detectable en About | `LICENSE`; GitHub reporta `licenseInfo.key = mit` |
| ✅ **LISTO** | README | `README.md` (248 líneas, bilingüe) |
| ✅ **LISTO** | Instrucciones de ejecución | `README.md` §"20-minute judge path"; verificadas: `python -m tero demo --offline --yes` → **exit 0** |
| ✅ **LISTO** | Uso de Strands evidente | `src/tero/offline.py:20` (`class OfflineModel(Model)`), `src/tero/session.py:41` (`BedrockModel`) |
| ✅ **LISTO** | Uso de AWS/Bedrock | Nova Lite `amazon.nova-lite-v1:0` en `src/tero/__init__.py:5` |
| ✅ **LISTO** | Divulgación de código previo (base) | `README.md` §"Hackathon disclosure"; `docs/NORMAS.md` §"Hackathon disclosure"; `docs/hackathon/DEVPOST.md` §"Disclosure" |
| ✅ **LISTO** | Track decidido y justificado | `docs/hackathon/README.md` §"Track" → Professional Agents |
| ✅ **LISTO** | Descripción EN redactada | `docs/hackathon/DEVPOST.md` |
| ✅ **LISTO** | Guion del video EN | `docs/hackathon/VIDEO.md` |
| ✅ **LISTO** | Post bonus redactado | `docs/hackathon/BUILDER-POST.md` |
| ✅ **LISTO** | Sin secretos en git | `.env` no trackeado; scan de `AKIA*`/`aws_secret*`/`sk-*` sin hallazgos; `.env.example` solo nombres |
| ✅ **LISTO** | Tests verdes | `pytest` → 143 passed |
| ⚠️ **DUDOSO** | Coherencia tesis ↔ código ↔ video | `main` ya dice "sin flujo por pasos" (`AGENTS.md`, `docs/CONVERSACIONAL.md`, PRs #32/#33 mergeados) pero **el código sigue con `s`/`n`/`b`/`c`** (migración pendiente; #34 solo trae el clasificador). Ver §5.2 |
| ⚠️ **DUDOSO** | Diagrama de arquitectura | `docs/hackathon/architecture.png` existe **pero está acoplado al flujo `s`/`n`/`b`/`c`**; hay que regenerarlo |
| ⚠️ **DUDOSO** | Traducción al inglés | `DEVPOST.md` y `VIDEO.md` están en EN, pero `README.md` es mayoritariamente en español. La regla exige traducción de *"testing instructions"* |
| ⚠️ **DUDOSO** | Demo viva | `https://marcorojasb.github.io/tero/` responde **HTTP 200**, pero **no está en el About** (`homepageUrl` vacío) y muestra el flujo antiguo (rumbos 1–4) |
| ❌ **FALTA** | **Video ≤5 min público en YouTube/Vimeo** | — (guion en `docs/hackathon/VIDEO.md`) |
| ❌ **FALTA** | **AWS Builder ID** | `profile.aws.amazon.com` |
| ❌ **FALTA** | **Submission enviado en Devpost** | empezado, sin enviar |
| ❌ **FALTA** | About del repo: `homepageUrl` | hoy vacío → debe ser la URL de Pages |
| ❌ **FALTA** | About del repo: topics | `repositoryTopics: null` → `strands-agents`, `amazon-bedrock` |
| ❌ **FALTA** | Diagrama subido a Devpost | el formulario pide la imagen |
| ❌ **FALTA** | Post en `builder.aws.com` | `docs/hackathon/BUILDER-POST.md` listo para pegar |

### 4.2 Verificación rápida (comandos)

```bash
cd <worktree>
python -m tero demo --offline --yes          # exit 0, escribe en examples/carpeta-demo/derivados/
pytest -q                                     # 143 passed
head -1 LICENSE                               # MIT License
gh repo view marcorojasb/tero --json licenseInfo,homepageUrl,repositoryTopics
curl -s -o /dev/null -w "%{http_code}\n" -L https://marcorojasb.github.io/tero/   # 200
git log --reverse --format='%ci' | head -1    # 2026-09-09 → dentro de la ventana
```

---

## 5. Los 5 riesgos de descalificación (y cómo evitarlos)

### 5.1 🔴 Código previo no divulgado — el riesgo #1 de tero

**Regla:** *"Projects must be newly created during the Submission Period… must
disclose any other pre-existing code or work incorporated into the Project"* y
*"not an existing project you're repackaging."*

**Por qué aplica:** tero nace de una idea previa (desktop privado del mismo autor).

**Mitigación (ya en marcha, hay que reforzarla):**
1. Los hechos juegan a favor: el repo nació **9 sep 2026**, dentro de la ventana;
   no hay una línea de Electron/SolidJS/Meridian; el stack es Python + Strands + OpenTUI.
2. Divulgar **proactivamente y en tres lugares**: descripción de Devpost, README y
   el video (decirlo en voz alta).
3. Usar la fórmula exacta de §6, que separa **idea** de **código**.
4. **Nunca** afirmar "100 % nuevo, sin trabajo previo". La divulgación es la que
   protege; la negación es la que descalifica.

### 5.2 🔴 Deriva entre el producto enviado y el video

**Regla:** *"must function as depicted in the video and/or expressed in the text
description."*

**Por qué aplica (hallazgo de esta investigación, agravado durante la investigación):**
hay un **refactor a medio aterrizar**. Mientras se redactaba este documento, los PRs
**#32** (tesis) y **#33** (protocolo) **se mergearon a `origin/main`**, así que hoy
`AGENTS.md` y `docs/CONVERSACIONAL.md` en `main` dicen:

> *"Sin flujo por pasos: no hay rumbos 1–4, plan tipado con `a`/`e`/`x`,
> clarificaciones numeradas ni puerta `s` / `n` / `b` / `c`."*

Pero **el código todavía implementa el flujo antiguo**: la migración de sesión, CLI,
TUI y tests no se ha hecho (el PR **#34** aporta `src/tero/approval.py`, que es solo el
clasificador; el resto sigue pendiente). Y `docs/hackathon/VIDEO.md`, `DEVPOST.md`,
`render_architecture.py` y el sitio de Pages **siguen describiendo `s`/`n`/`b`/`c`**.

Es decir: `main` es hoy internamente inconsistente — sus documentos de tesis describen
un producto que el código aún no es.

**Riesgo concreto:** que el video muestre `s`/`n`/`b`/`c` mientras la documentación de
`main` habla de aprobación en lenguaje natural → *"no funciona como se muestra"*.
Y al revés: si se graba el flujo conversacional antes de que el código lo implemente,
el video muestra algo que el repo no hace.

**Mitigación — decisión del humano, hoy:**
- **Opción A (recomendada): congelar y ser explícito.** Grabar el video contra el
  código que **realmente corre hoy** (`python -m tero demo --offline --yes` →
  `s`/`n`/`b`/`c`, verificado), y **decir en el propio video** que la migración a
  aprobación en lenguaje natural está en curso. Un juez perdona una hoja de ruta
  declarada; no perdona una contradicción no declarada.
- **Opción B: esperar la migración completa.** Solo si el flujo conversacional queda
  implementado **y verde** antes del domingo, y se actualizan a la vez `VIDEO.md`,
  `DEVPOST.md`, `render_architecture.py`, `README.md` y `site/`.
- En cualquiera de las dos: **video, README, diagrama y sitio deben describir el mismo
  flujo.** Etiquetar (`git tag`) el commit enviado ayuda a auditarlo.

> ⚠️ **No enviar el estado actual sin decidir.** Es el único riesgo de este documento
> que puede crecer solo con el paso de las horas.

### 5.3 🟠 Falta de traducción al inglés

**Regla:** *"All Submission materials must be in English or… the Entrant must provide
an English translation of the demonstration video, text description, and testing
instructions."*

**Por qué aplica:** la UI es en español (correcto para el producto) y `README.md` es
mayoritariamente en español.

**Mitigación:**
- Video con **voiceover en inglés** (ya previsto en `VIDEO.md`). La UI en pantalla
  puede quedar en español.
- Descripción de Devpost en inglés (`DEVPOST.md` ✅).
- **Añadir un `docs/hackathon/JUDGES-EN.md`**: quickstart de 10 líneas en inglés,
  requisitos, comandos y cómo verificar que funciona. Enlazarlo desde `README.md`.
  Es la pieza que hoy falta para cumplir la regla sin ambigüedad.

### 5.4 🟠 Repo privado, licencia no visible o instrucciones insuficientes

**Regla:** repo público con todo el código, licencia MIT/Apache **detectable en el
About**, e instrucciones *"good enough that a stranger could get it running cold"*.

**Estado:** público ✅, MIT detectado ✅, instrucciones verificadas ✅.
**Riesgo residual:** el **About está incompleto** (`homepageUrl` vacío,
`repositoryTopics: null`). Sin homepage, el juez que no instala nada **pierde el link
a la demo viva** — que es justamente el estímulo de Technical Implementation.
**Mitigación:** `gh repo edit` para fijar homepage y topics. 2 minutos.

### 5.5 🟠 Demos falsos, secretos expuestos o video fuera de límite

Tres causas distintas, misma familia:

- **Demo falso.** `--offline` **no** finge Bedrock: `OfflineModel` es un `Model` de
  Strands real etiquetado `tero-offline` (`src/tero/offline.py:20`,
  `src/tero/session.py:40`). Mantener la frase del guion: *"the offline path uses
  `tero-offline`, a scripted Strands model, not a live Bedrock call."*
  Si Bedrock falla en vivo, **no simularlo**: quedarse en offline y decirlo.
  El sitio de Pages ya cumple esto por su cuenta — dice textualmente en pantalla
  *"El modelo de esta sesión es tero-offline: un Strands Model scripted, no un
  Bedrock disfrazado. AgentCore no es el producto."* Es un activo honesto y
  conviene que el video no lo contradiga.
- **Secretos.** El aviso oficial es explícito: *"A public repo with an exposed key is
  an open invitation to run up charges… scan your repo before you submit."*
  Hoy: `.env` no trackeado, scan sin hallazgos. **Repetir el scan antes del envío.**
- **Video >5 min.** El límite es duro y es la forma más tonta de perder Presentation.
  `VIDEO.md` suma 5:00 exactos → **dejar 15 s de margen** (apuntar a 4:30–4:45).

### 5.6 Riesgo adicional: caer en Stage One

*"reasonably applies the required tools/APIs/SDKs"*. Si el juez entra al repo y no ve
**Strands** en 30 segundos, no se llega a Stage Two. **Mitigación:** Strands nombrado
en el título de la descripción, en el About, en el diagrama y en el video.

---

## 6. Divulgación honesta: qué decir exactamente

`docs/NORMAS.md` §"Hackathon disclosure" fija la línea: *"New project, public MIT
repository. The product thesis builds on prior private desktop work by the same
author without copying that predecessor. Declare offline vs Bedrock honestly in
the demo video."*

Eso es correcto pero **demasiado breve para el formulario**. Texto recomendado, para
pegar en la sección **"Disclosure / Pre-existing work"** de la descripción de Devpost
y repetir —más corto— en el video:

> **Pre-existing work disclosure.** tero is a new project: the first commit is dated
> 9 September 2026, inside the submission period, and every line in this repository
> was written for this hackathon. Nothing is copied or repackaged from another
> codebase.
>
> Two things are worth disclosing. (1) The *product thesis* — a teacher-in-the-loop
> preparation loop where your own sources stay the system of record — builds on
> prior private desktop work by the same author. No code from that predecessor is
> used here: that app was Electron/SolidJS; tero is Python + Strands Agents SDK with
> an OpenTUI shell. No assets, files, or student data from that predecessor are
> included. (2) The
> `--offline` path runs a **scripted Strands `Model`** labelled `tero-offline`. It is a
> real `strands.models.Model` implementation, not a stand-in for an Amazon Bedrock
> call, and it never claims to be one. The live Amazon Bedrock (Nova Lite) path is
> separate and is shown as such in the demo video.
>
> Standard tools used: Strands Agents SDK, Amazon Bedrock (Nova Lite), OpenTUI
> (`@opentui/core`), Bun, pypdf, python-docx, pytest, ruff. All open source, used
> under their own licenses; no third-party source code is vendored into this
> repository.
>
> Example materials under `examples/` and `fixtures/` are synthetic. The Chilean
> curriculum catalogue under `curriculum/` is a host-side paraphrase, not verbatim
> MINEDUC text, and contains no student data.

**En voz alta en el video** (~10 s, dentro del bloque de demo offline):

> "This offline segment runs `tero-offline`, a scripted Strands model — a real
> `Model` implementation, not a live Bedrock call. The Bedrock path is separate, and
> I'll show it in a moment."

**Qué NO decir:** "todo es 100 % nuevo, sin ninguna relación con nada previo"
(falso y contradice el README); "esto corre en Bedrock" sobre el segmento offline;
"AgentCore corre tero" si solo hay una captura del harness.

---

## 7. Plan de las próximas 72 horas, por impacto

Ordenado por puntaje esperado por hora invertida. **H** = requiere humano
(no delegable a un agente de código).

### Día 1 — viernes 11 sep (hoy)

| # | Acción | Quién | Tiempo | Impacto |
| --- | --- | --- | --- | --- |
| 1 | **Congelar la decisión de flujo** (Opción A vs B de §5.2). Si es A: `git tag` del commit a enviar | **H** | 15 min | 🔴 Evita descalificación |
| 2 | `gh repo edit` → homepage = Pages, topics `strands-agents`, `amazon-bedrock` | Agente | 5 min | 🟠 Habilita el estímulo de Technical Implementation |
| 3 | **Crear AWS Builder ID** en `profile.aws.amazon.com` | **H** | 10 min | 🔴 Requisito obligatorio |
| 4 | Escribir `docs/hackathon/JUDGES-EN.md` (quickstart EN + verificación) | Agente | 30 min | 🟠 Cumple la regla de idioma |
| 5 | Sección EN "Where Strands is used" con rutas y líneas en `README.md` | Agente | 30 min | 🟠 Stage One + Technical Implementation |
| 6 | **OpenTelemetry**: `strands-agents[otel]` + `StrandsTelemetry` (§3.3) | Agente | 1 h | 🟠 **Sube el criterio de desempate sin desplegar AgentCore** |
| 7 | Publicar el **primer** post en `builder.aws.com` (`BUILDER-POST.md`) | **H** | 20 min | 🟢 **+0.2** |

### Día 2 — sábado 12 sep

| # | Acción | Quién | Tiempo | Impacto |
| --- | --- | --- | --- | --- |
| 8 | **Patrón `Graph` de Strands** para la puerta de aprobación (§3.3) — *solo si no arriesga el flujo congelado* | Agente | 2–3 h | 🟠 El ítem de mayor puntaje técnico |
| 9 | **Regenerar el diagrama** para el flujo congelado y verificar el contenido mínimo del FAQ | Agente | 1 h | 🟠 Requisito + Technical Implementation |
| 10 | **Grabar la demo**: `python -m tero tui --offline`. Repetir tomas hasta que salga limpia | **H** | 1–2 h | 🔴🔴 **Palanca #1** |
| 11 | Escribir los posts bonus **2 y 3** (uno técnico sobre Strands + el loop; otro sobre Free Tier/costos desde `AWS-GRATIS.md`) | Agente redacta / **H** publica | 1 h | 🟢 **+0.4** |
| 12 | Verificar que `site/` y el README describen el flujo congelado | Agente | 30 min | 🟠 Coherencia |

### Día 3 — domingo 13 sep

| # | Acción | Quién | Tiempo | Impacto |
| --- | --- | --- | --- | --- |
| 13 | **Grabar voiceover en inglés** sobre la demo | **H** | 1 h | 🔴 Presentation |
| 14 | **Editar el video a 4:30–4:45** con los 5 bloques del guion | **H** | 1–2 h | 🔴 Presentation |
| 15 | **Subir a YouTube, público** (no listado) y verificar en ventana de incógnito | **H** | 20 min | 🔴 Requisito |
| 16 | Scan final de secretos + `pytest` + smoke test del demo | Agente | 20 min | 🟠 |
| 17 | **Llenar el formulario de Devpost**: descripción, repo, diagrama, video, Builder ID, track, "Built with", link vivo | **H** | 45 min | 🔴 |
| 18 | **Enviar el submission** con ≥12 h de margen | **H** | 5 min | 🔴 |

### Lunes 14 sep (colchón)

| # | Acción | Quién | Impacto |
| --- | --- | --- | --- |
| 17 | Verificar que el repo sigue público y que la licencia sigue en el About | Agente | 🟠 |
| 18 | Confirmar que el video abre sin login y dura <5:00 | **H** | 🔴 |
| 19 | **No tocar el submission después del cierre** (no se puede modificar) | — | — |

### Lo que un agente de código puede hacer sin humano

- `gh repo edit` (homepage, topics, descripción).
- `docs/hackathon/JUDGES-EN.md` y la sección EN de Strands del README.
- Regenerar `architecture.png` desde `render_architecture.py`.
- Redactar los posts bonus 2 y 3 (el humano solo pega y publica).
- Actualizar `DEVPOST.md`, `VIDEO.md` y `site/` al flujo congelado.
- Scan de secretos, `pytest`, smoke test, y verificar el HTTP del sitio.
- **No puede:** crear el Builder ID, publicar en `builder.aws.com`, grabar el video,
  subirlo a YouTube, ni enviar el formulario de Devpost.

### Presupuesto de tiempo del humano

**≈ 6–8 horas repartidas en 3 días.** El video es 3–4 de esas horas. **Es el camino
crítico y no se puede paralelizar con agentes.**

---

## 8. Anexos

### 8.1 Enlaces primarios

| Recurso | URL |
| --- | --- |
| Portada | https://agentsforhumans.devpost.com/ |
| Reglas oficiales | https://agentsforhumans.devpost.com/rules |
| FAQ | https://agentsforhumans.devpost.com/details/faqs |
| Resources | https://agentsforhumans.devpost.com/resources |
| Updates (guía de organizadores) | https://agentsforhumans.devpost.com/updates |
| Pro tips for your project | https://agentsforhumans.devpost.com/updates/46174-pro-tips-for-your-project |
| How to actually stand out | https://agentsforhumans.devpost.com/updates/45987-how-to-actually-stand-out-in-agents-for-humans |
| Formulario de submission | https://agentsforhumans.devpost.com/submissions/new |
| AWS Builder ID | https://profile.aws.amazon.com |
| Builder Center (post bonus) | https://builder.aws.com/ |
| Strands Agents — quickstart | https://strandsagents.com/docs/user-guide/quickstart/overview/ |
| AgentCore — docs | https://docs.aws.amazon.com/bedrock-agentcore/ |
| Contacto del manager | shawni@devpost.com |

### 8.2 Estado verificado de tero (`origin/main` = `2b2e76a`)

| Hecho | Evidencia |
| --- | --- |
| Primer commit dentro de la ventana | `c66655c`, 2026-09-09 19:52 UTC |
| Demo offline funciona | `python -m tero demo --offline --yes` → exit 0, escribe en `derivados/` |
| El demo no ensucia el repo | `git status --short` vacío tras correr (`.gitignore:157,229` cubren `derivados/`) |
| Tests verdes | `pytest -q` → 143 passed |
| Offline es Strands real | `src/tero/offline.py:20` `class OfflineModel(Model)`; `src/tero/session.py:40` |
| Bedrock es Nova Lite | `src/tero/__init__.py:5` `amazon.nova-lite-v1:0`; `src/tero/session.py:41` `BedrockModel` |
| Sin secretos | `.env` no trackeado; scan de patrones sin hallazgos |
| Sin código de terceros vendorizado | sin `NOTICE`/`THIRD-PARTY`, sin headers de copyright ajenos en `src/` ni `tui/src` |
| Diagrama válido | `architecture.png`, PNG 1680×820, 82 304 bytes |
| Sitio vivo | `https://marcorojasb.github.io/tero/` → HTTP 200 |
| El sitio no finge ser el producto | `site/index.html` declara en pantalla que el modelo es `tero-offline` y que "AgentCore no es el producto" |
| About incompleto | `homepageUrl: ""`, `repositoryTopics: null` |
| **Riesgo de deriva** | `render_architecture.py`, `VIDEO.md`, `DEVPOST.md` y `site/` describen `s`/`n`/`b`/`c`; el refactor conversacional está en PRs #32–#34 |

### 8.3 Nota sobre verificabilidad

Todo lo citado de Rules, FAQ, Resources, portada y Updates fue leído directamente de
las páginas oficiales. La frase *"Judges are not required to test the Project and may
choose to judge based solely on the text description, images, and video provided in
the Submission"* está **textualmente en [Rules §4](https://agentsforhumans.devpost.com/rules)**
y es la base de la estrategia de §2. Las páginas de foro de Devpost devuelven
HTTP 202 sin cuerpo a clientes que no son navegador, así que los hilos de discusión
no pudieron reverificarse desde la línea de comandos y **no se usan como fuente de
ninguna afirmación de este documento**.
