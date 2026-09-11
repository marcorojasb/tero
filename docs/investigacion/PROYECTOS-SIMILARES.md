# Proyectos similares — qué lógica conviene copiar o integrar

Investigación de producto para **tero** (agente docente, Chile, MIT, hackathon
"Agents for Humans"). Fecha de verificación: **2026-09-11**. Cierre del
hackathon: **14-09-2026**.

> **Método y honestidad de fuentes.** Cada URL de este documento fue abierta y
> su código HTTP observado en esta sesión, o proviene de una búsqueda y queda
> marcada como tal. Lo que no se pudo confirmar aparece como
> **`no verificado`**. No se inventó ninguna URL, número de checkpoint ni
> término de vocabulario. Las licencias se leyeron de **fuente primaria**
> (`raw.githubusercontent` de cada `LICENSE`, API de PyPI, specs oficiales,
> API CKAN), no de la ficha del repositorio.
>
> **Limitaciones de red encontradas** (importante para no repetir el trabajo):
> `web_search` se cayó a mitad de la investigación (HTTP 402), así que el
> descubrimiento se hizo con fetch directo, `gh` autenticado, Wayback y proxys de
> texto. `curriculumnacional.cl` no responde desde esta red (timeout),
> `bcn.cl` exige `User-Agent` de navegador, `rand.org` y Reddit devuelven 403,
> `eduaide.ai` bloquea con Vercel 429 (se recuperó vía Wayback Machine),
> `unesdoc.unesco.org` da 403. Un agente concurrente ejecutó `git clean` y borró
> dos veces los archivos no rastreados: los informes crudos se conservan **fuera
> del repo**, en `/home/ubuntu/investigacion-tero-raw/`.
>
> **Historial de correcciones.** Dos afirmaciones iniciales fueron **refutadas
> antes de entregar** y quedan corregidas en este documento: (1) "no existe API
> del currículum chileno" — **sí existe** (`/jsonapi`); (2) "OpenStax es CC BY" —
> en 2026 **la mayoría de sus títulos son CC BY-NC-SA**.

**Contrato de referencia.** tero está migrando al agente conversacional:
intenciones **a)** responder, **b)** crear, **c)** editar/adaptar (incluida NEE),
aprobación en lenguaje natural, y un objeto `propuesta` con `accion`, `tipo`,
`titulo`, `resumen`, `vista_previa`, `origen`, `cambios`, `notas_nee`,
`evidencias` y `warnings` (`docs/CONVERSACIONAL.md`). Este documento recomienda
**contra ese contrato**, no contra el flujo por pasos retirado.

---

## 1. Tabla de proyectos y productos

### 1.1 Asistentes docentes comerciales

| Nombre | URL | Qué es | Licencia | Qué vale la pena copiar | Qué NO copiar y por qué |
| --- | --- | --- | --- | --- | --- |
| **MagicSchool AI** | https://www.magicschool.ai/ | Plataforma K-12, 80+ herramientas docentes; ~8 M registros, 10.000+ escuelas | Propietaria | **Edición antes de exportar** ("Export when ready") + biblioteca con **versiones** del mismo material. Formulario con campos fijos (`grade`, `number of slides`, `topic`). | El **generador de IEP**: Common Sense Media recomienda explícitamente *no* usar IA para IEP/504. Casos de sesgo medido (planes de conducta distintos según raza). No vender "documento oficial". |
| **Eduaide.AI** | https://www.eduaide.ai/ (snapshot: https://web.archive.org/web/20250901073530/https://www.eduaide.ai/) | +110 recursos, asistente "Erasmus", banco de estándares, export Word/Docs/PDF | Propietaria | Flujo de **3 pasos** (elegir recurso → tema/adjunto → generar → *"refine, edit and export"*) y catálogo de recursos con nombre propio. | Su **export a Google Docs pierde tablas y negritas** (41 reseñas). El eslabón más débil en confianza del conjunto: sin SOC 2 ni Common Sense verificables. |
| **Brisk Teaching** | https://www.briskteaching.com/ | Extensión Chrome/Edge que actúa sobre lo que ya está en pantalla | Propietaria | **"Change Level"** (diferenciación + 50 idiomas) y **feedback en borrador** dentro del documento: *"Feedback stays hidden from students until you've reviewed and approved it"*. Catálogo literal incluye **Text Leveler**, **DOK Questions**, **UDL Lesson Plan**. | Extensión de navegador + QTI/LTI: fuera de alcance para una TUI. Sus cifras de adopción se contradicen entre sus propias páginas (10.000 vs 20.000 distritos): no citarlas. |
| **Diffit** | https://web.diffit.me/ | Diferenciación de lectura: pegar texto/URL/YouTube → banda de grado → pasaje nivelado + vocabulario + preguntas | Propietaria | El **paquete de apoyo** alrededor del texto adaptado: vocabulario clave con definiciones amigables, preguntas de opción múltiple y abiertas, resumen, prompts de escritura. **Cuatro tipos de entrada.** | Nivelación ingenua: *"the level adaptations occasionally oversimplify, smoothing out nuance that a stronger reader should wrestle with"*. Sin verificación de nivel no debe presentarse como "adaptado al curso". |
| **Curipod** | https://curipod.com/ | Lecciones interactivas en vivo + escritura con feedback "Glow & Grow" | Propietaria | **Modo de moderación docente** antes de que algo llegue al estudiante. Rúbrica propia para puntuar. | Pivote constante de posicionamiento. Auditoría independiente lo deja en **66/100, "Does Not Meet Data Transparency Standard"**. No copiar la lógica de presentación en vivo: no es el problema de tero. |
| **SchoolAI** | https://schoolai.com/ | Docente diseña "Spaces"; estudiante conversa con un sidekick | Propietaria | La frase-contrato: *"Teachers review everything before it reaches a student."* **Estándares propios cargables** por el distrito. | Chatbot de estudiante siempre disponible: superficie de riesgo que tero no necesita. Free = **5 sesiones al año**; sin plan individual pago. |
| **Khanmigo** (Khan Academy) | https://khanmigo.ai/ | Tutor + asistente docente, ONG | Propietaria | **Catálogo de actividades agrupado por intención pedagógica** (Plan / Create / Differentiate / Support / Learn) y *"No prompting is required"*. **Common Sense Media: "Low risk"**, la mejor calificación del conjunto. | Acceso de estudiantes atado a distrito. Un catálogo de 25+ actividades es lo contrario de la conversación libre de tero: sirve como **inspiración de taxonomía**, no como UI. |
| **Teachmate** (TeachMateAI) | https://www.teachmate.com/ | 160 herramientas, foco UK/SEND | Propietaria | **"Every section remains editable and regenerable"** + "unlimited refinements". Transparencia: retención 28 días, ISO 27001 *en curso* y lo admiten. | Único del conjunto **sin LMS nativo ni API pública**. El generador de EHCP (equivalente al PIE chileno) es justo el uso de alto riesgo que los evaluadores piden evitar. |
| **Almanack** | https://www.almanack.ai/ | "Curriculum implementation companion"; no student-facing, no pide datos de alumnos | Propietaria | **Posicionamiento**: *"Almanack assists planning, it doesn't replace professional judgment"* y no reemplaza al LMS. **"Regenerate using AI" por sección** (edición granular). | Su calificación independiente de transparencia de datos es **F, 26/100, 9 de 35 checks**. No copiar el discurso de "alineado a 500+ frameworks" sin poder verificar la alineación. |
| **Google Gemini for Education** | https://support.google.com/edu/classroom/answer/15410566 | Gemini en Classroom + Gemini for Education + AI Pro for Education | Propietaria | **"Re-level text"** como acción nombrada de primer nivel. Etiquetado de estándares vía **1EdTech CASE Network 2** (NGSS, ISTE, ACT). | **Common Sense califica "Gemini K-12" como HIGH RISK** (salud mental, no ajusta por edad, genera IEP y avisos de retiro sin contexto legal). Muchas funciones "coming soon" y sólo en inglés. |
| **Microsoft Copilot for Education** | https://www.microsoft.com/en-us/education/products/copilot-in-education | Copilot Chat / Teach / Study and Learn / M365 Copilot académico | Propietaria | **Diferenciación que preserva el vocabulario técnico de dominio** — el único del conjunto que lo declara explícitamente. "Treat Teach outputs as **drafts to be adapted, not final canonical documents**". | Complejidad de licenciamiento; **sin audit logs ni provenance** verificables; LTI 1.3 atado a M365. Fuera del alcance de una TUI MIT. |

**Datos duros de adopción** (útiles para el pitch, con fuente primaria):

- Gallup × Walton Family Foundation 2025 (n=2.232): **60 %** de docentes usó IA;
  quienes la usan semanalmente ahorran **5,9 h/semana ≈ 6 semanas por año**;
  **≤7 %** dice que le quita tiempo. https://news.gallup.com/poll/691967/three-teachers-weekly-saving-six-weeks-year.aspx
- Gallup × WFF 2026 (n=2.069): sólo **18 %** recibe guía formal sobre IA; **69 %**
  sin ninguna guía sobre tutoría 1-a-1. https://news.gallup.com/poll/710534/teachers-receive-no-formal-guidance.aspx
- **Advertencia de comparabilidad:** las definiciones de "usar IA" no son
  comparables entre estudios (Gallup 60 %, RAND 18 % "AI users", EdWeek 61 %).
  No promediar. Los ahorros declarados por proveedores (9-10 h/semana) son
  sistemáticamente mayores que el benchmark independiente (5,9 h/semana).

### 1.2 Código abierto, datos y benchmarks

| Nombre | URL | Qué es | Licencia (verificada) | Qué vale la pena copiar | Qué NO copiar y por qué |
| --- | --- | --- | --- | --- | --- |
| **Kolibri** (Learning Equality) | https://learningequality.org/kolibri/ | Suite de aprendizaje offline para contextos sin conectividad | **MIT** (verificado en `learningequality/kolibri/LICENSE`) | Modelo de **canal de contenido versionado** y de metadatos de recurso por nivel/idioma. Es el proyecto OSS más alineado con "carpeta local como sistema de registro". | Es una plataforma completa con su propio runtime; nada de su UI es transportable a una TUI. |
| **Kolibri Studio** | https://github.com/learningequality/studio | Curaduría de contenido para Kolibri | **MIT** (verificado en `learningequality/studio/LICENSE`) | Esquema de **árbol de contenido** (canal → tópico → recurso → ejercicio) y chequeos de calidad de curaduría. | Depende de Django/Postgres; es una app web, no una librería. |
| **Oppia** | https://www.oppia.org/ | Lecciones interactivas con feedback por ramificación | **Apache-2.0** (verificado en `oppia/oppia/LICENSE`) | El **exploration data model**: estados, reglas de respuesta y retroalimentación tipada. Referencia para estructurar ítems de evaluación como datos, no como prosa. | El editor de lecciones es su producto; no aporta al loop docente de tero. |
| **Open edX** (`edx-platform`) | https://openedx.org/ | LMS de referencia | **AGPL-3.0** (verificado en `openedx/edx-platform/LICENSE`) | Nada de código. Sí el formato **OLX** como referencia conceptual de estructura de curso. | **AGPL-3.0 es incompatible con copiar código dentro de un proyecto MIT.** Copiar cualquier línea obligaría a relicenciar tero. |
| **Canvas LMS** (Instructure) | https://github.com/instructure/canvas-lms | LMS | **AGPL-3.0** (verificado en `instructure/canvas-lms/LICENSE`) | Nada de código. | Igual que Open edX: **AGPL-3.0 incompatible con MIT** para copia de código. |
| **Moodle** | https://moodle.org/ | LMS | **GPL-3.0** (`COPYING.txt`) | Referencia conceptual: el **subsistema de IA está en el core** (`public/ai/provider/{openai,azureai,anthropic,awsbedrock,deepseek,gemini,ollama}`, `aiplacement_{courseassist,editor}`, `aiactions/*`) y enseña cómo un LMS abstrae el proveedor de modelo. Las **rúbricas** viven en `public/grade/grading/form/rubric/`. | **GPL-3.0 incompatible con MIT** para copiar código. Nótese que `aiprovider_awsbedrock` es GPL-3.0: no se puede portar a tero. Es PHP. |
| **H5P** (`h5p-php-library`) | https://h5p.org/ | Tipos de contenido interactivo | **GPL-3.0 para la librería PHP**; el proyecto declara que usa **MIT donde puede** pero la librería PHP queda GPL por CKEditor4. Fuente: https://h5p.org/licensing | El **formato de archivo `.h5p`** (ZIP + `h5p.json` + `content.json`) se puede generar uno mismo. Los **content types de Joubel son MIT** (campo `license` en `library.json`), y `h5p-cli` es MIT. | **GPL-3.0 incompatible con MIT.** ⚠️ Además `h5p-editor-php-library` tiene **licencia en conflicto**: el README dice MIT, el `composer.json` dice GPL-3.0 y no hay archivo `LICENSE`. No incrustar el PHP. |
| **PhET** (simulaciones) | https://phet.colorado.edu/ | Simulaciones interactivas de ciencia y matemática | **Contenido CC BY**; **código MIT o GPL según la simulación** (verificado: `phet-core`, `joist`, `energy-skate-park` MIT; `circuit-construction-kit-dc`, `vector-addition`, `gravity-force-lab`, `friction` **GPL-3.0**). PhET-iO propietario. | Enlazable y citable como **recurso externo** sugerido dentro de una guía, con atribución. **API de metadatos funcional:** `https://phet.colorado.edu/services/metadata/1.3/simulations?format=json&type=html` (200, ~4,5 MB). | No empaquetar assets sin revisar la licencia **por simulación**: varias son GPL-3.0. |
| **CK-12** | https://www.ck12.org/ | Contenido STEM (FlexBook) | **Propietaria y limitada**, no CC: *"limited, non-exclusive, non-transferable, non-sublicensable, revocable license"*, *"not permitted to resell"*; el currículo se rige por la *CK-12 Curriculum Materials License* y las fotos de stock son **sólo uso personal no comercial** (leído vía Wayback; el sitio da 403 a curl). | Nada de contenido. Referencia de **estructura de FlexBook**. | **No es OER permisiva**: la suposición contraria es un error frecuente. No empaquetar ni redistribuir. |
| **OER Commons** (ISKME) | https://www.oercommons.org/ | Repositorio OER | **Propietaria**; el contenido es por defecto **CC BY-NC-SA 4.0** y sus términos **prohíben scraping y robots**. `ISKME/OER-Commons-API` **sin licencia**. | Nada. | **Prohibido el scraping** y el contenido por defecto es NC-SA. No usar como fuente. |
| **Khan Academy `perseus`** | https://github.com/Khan/perseus | Motor de ejercicios de Khan Academy | **MIT** | Modelo de datos de ejercicio con *widgets* tipados (útil como referencia de estructura de ítems). | `khan-exercises` **no tiene licencia**. Khanmigo es propietario. |
| **OpenStax** | https://openstax.org/ | Textos abiertos (Rice University) | **MIXTO por título** — su API pública declara: de **129 libros, 72 son CC BY-NC-SA 4.0 y 46 CC BY 4.0** (11 sin dato). API: `https://openstax.org/apps/cms/api/v2/pages/?type=books.Book&fields=title,license_name,license_version,slug&limit=200`. Su código (`openstax/openstax-cms`) es **AGPL-3.0**. | Fuente de **texto base citable** para enseñanza media/superior. **"OpenStax = CC BY" es falso en 2026: la mayoría es NC-SA.** Verificar por título. | Nivel universitario; poco aplicable a 4°–6° básico, y la mayoría **no** es reutilizable comercialmente. |

### 1.2b Datasets, benchmarks y harness de calidad

| Nombre | URL | Qué mide | Licencia (verificada) | Reusable para tero |
| --- | --- | --- | --- | --- |
| **EduBench** | HF `DirectionAI/EduBench` | 9 escenarios, +4.000 contextos, 12 aspectos docente/estudiante | **MIT** | **El mejor análogo público de harness de material educativo.** |
| **The Pedagogy Benchmark** | HF | Calidad pedagógica | **MIT** | Sí, sin fricción. |
| **Learning Commons `evaluators`** | https://github.com/learning-commons-org | *"Evaluation for AI outputs against trusted educational rubrics"* | **Código MIT + prompts CC BY 4.0 + corpus anotado CC BY-NC-SA 4.0** | **El harness de rúbrica pedagógica más directamente reutilizable.** El corpus anotado es NC-SA: usar los prompts y el código, **no** el corpus. |
| **Learning Commons `knowledge-graph`** | https://github.com/learning-commons-org | Estándares K-12 (CCSS + 15 estados) con **UUID de CASE**, JSONL público | **Código MIT + datos CC BY 4.0** (el campo license de GitHub dice NOASSERTION; manda `LICENSE.md`) | Modelo de **grafo de estándares con identificador estable**. REST/MCP en beta privada. |
| **LessonBench-V1** | Kaggle (arXiv 2607.13041) | 647 lecciones evaluadas con **Bloom + Gagné + Merrill + 5E** | Datos **CC BY-SA 4.0**; paper **NC-SA** | El harness **más alineado con evaluar planificaciones**, pero **SA**: no derivar un esquema propietario. |
| **MathDial** | https://github.com/eth-nlped/mathdial | 2.861 diálogos tutor-estudiante + taxonomía de *teacher moves* | **CONFLICTO:** README dice **CC BY-SA 4.0**, la tarjeta de HF dice `cc-by-4.0` | Útil por la **taxonomía de movimientos docentes**, no por los datos. Resolver el conflicto antes de usarlo. |
| **Prometheus 2** | https://github.com/prometheus-eval | LLM-as-judge con rúbrica propia | **Apache-2.0** (repo **y pesos**) | Mejor encaje para un juez con rúbrica propia. (`JudgeLM`: repo Apache-2.0 pero **pesos sin licencia**.) |
| **ASAP-AES** | — | Automated essay scoring | **"Subject to Competition Rules": NO redistribuible.** La **métrica QWK sí** es reimplementable (`scikit-learn`, BSD-3-Clause) | Sólo la métrica. |
| **PERSUADE 2.0** · **ASAP 2.0/AES 2.0** · **TOEFL11 (LDC2014T06)** | — | Essay scoring | **CC BY-NC-SA 4.0** · **CC BY-NC 4.0** · no comercial + no redistribuible + pago | **No.** NC incompatible. |
| **GSM8K** · **MathBench** · **SocraticChat/PlatoLM** | — | Exactitud matemática / diálogo socrático | **MIT** · **Apache-2.0** · **Apache-2.0** | Sí, pero **no miden pedagogía**: miden corrección. |
| **CIMA** | https://github.com/kstats/CIMA | Acciones de tutor y estudiante | **CC BY 2.5** | Sí, con atribución. |
| **Beacon** | HF `sanskxr02/Beacon` | Sicofancia (no pedagogía) | **CC BY 4.0** | Marginal. |

**Patrón transversal:** en Hugging Face, la mayoría de los datasets marcados
"education" **no traen licencia**. La disponibilidad pública **no** implica
permiso. Y hay repos grandes y populares **sin licencia = no reutilizables**:
`ECNU-ICALK/EduChat` (★969), `EduEval`, `OmniEduBench`, `ISKME/OER-Commons-API`.
Google **LearnLM no tiene artefactos abiertos** (`no longer a separate listing in
AI Studio… integrated into the Gemini 2.5 model series`).

### 1.3 Marcos curriculares, de accesibilidad y de adaptación

Ver la sección **"Formatos y datos abiertos"** para el detalle de campos y URLs.

| Nombre | URL | Qué es | Licencia | Qué vale la pena copiar |
| --- | --- | --- | --- | --- |
| **CAST UDL Guidelines 3.0** | https://udlguidelines.cast.org/ · ES: https://udlguidelines.cast.org/es/ | 9 directrices / 36 consideraciones, 3 principios, 3 capas | **Propietaria y restrictiva** — https://www.cast.org/copyright/ | **Sólo los identificadores numéricos** (`1.1`…`9.4`) + la cita oficial. Ver riesgo legal abajo. |
| **W3C a11y-discov-vocab 1.1** | https://www.w3.org/community/reports/a11y-discov-vocab/CG-FINAL-vocabulary-20260326/ | Vocabulario cerrado de accesibilidad (el que usa schema.org) | W3C Community Final Specification Agreement | **Todo.** Listas cerradas de términos, listas para `enum` en un JSON Schema. |
| **schema.org (accesibilidad)** | https://schema.org/accessibilityFeature | Transporte JSON-LD de los metadatos de accesibilidad | **CC BY-SA 3.0** | Las 7 propiedades como nombres de campo; el transporte JSON-LD si algún día se publica el material. |
| **WCAG 2.2** | https://www.w3.org/TR/WCAG22/ | Criterios de conformidad A/AA/AAA | W3C Document License (**no permite derivados**) | Los **identificadores** `SC x.y.z` como campos verificables (contraste, espaciado, nivel lector). No reproducir el texto normativo. |
| **Decreto 83/2015 (Chile)** | https://www.bcn.cl/leychile/navegar?idNorma=1074511 | Criterios y orientaciones de adecuación curricular para NEE | Norma pública (textos legales fuera del derecho de autor, art. 71 C Ley 17.336) | **El contrato de datos ya escrito:** 2 tipos de adecuación (**acceso** vs **objetivos de aprendizaje**), con **4 + 5 criterios exactos**, más la regla de oro (acceso antes que objetivos) y los **11 campos del PACI**. Ver §3.5. |
| **Decreto 170/2009 (Chile)** | https://www.bcn.cl/leychile/navegar?idNorma=1012570 | Fija normas para determinar alumnos con NEE beneficiarios de subvención | Norma pública | Vocabulario oficial: **NEE permanente** (6 categorías) vs **transitoria** (4 categorías). |
| **Ley 21.545 (2023, TEA)** | **Número de ley: Ley 21.545** (publicada el 10-03-2023). **`idNorma` no confirmado** — ver la advertencia sobre el endpoint JSON en §3.1. | Promoción de la inclusión y atención integral de personas con TEA | Norma pública | Título IV, arts. 18-21. **No dice "ajustes razonables"**: dice *"los ajustes necesarios en sus reglamentos y procedimientos internos"*. |
| **Ley 20.422** | https://www.bcn.cl/leychile/navegar?idNorma=1010903 | Igualdad de oportunidades e inclusión social de personas con discapacidad | Norma pública | Art. 3 define **Diseño Universal** y **Accesibilidad Universal**; art. 36 obliga a **adaptar materiales**. |
| **UNESCO — Guía para la IA generativa en educación** | https://www.unesco.org/en/articles/guidance-generative-ai-education-and-research (`no verificado` en esta red: 403/timeout) | Recomendaciones de agencia humana | Documento UNESCO | Principio rector: **la IA asiste, la persona decide**. Refuerza el diseño de tero. Discrepancia con la práctica comercial: tres de las cuatro plataformas evaluadas por Common Sense ofrecen generación de IEP igual. |

---

## 2. Lógica que conviene integrar

Cada ítem: **qué problema del docente resuelve**, **cómo se vería en tero**,
**costo** y **si cabe antes del cierre (14-09-2026)**. Hoy es 2026-09-11:
quedan **3 días**. "Cabe" significa que entra sin tocar el camino offline ni el
contrato congelado de `docs/CONVERSACIONAL.md`.

### P0 — Hacerlo antes del cierre

#### P0.1 Vista previa con estructura obligatoria y "qué va a hacer" explícito

- **Problema del docente:** el costo real de la IA no es generar, es **revisar**.
  La queja documentada es *"the review process is time-consuming"* y *"Diffit is
  a drafting partner, not an autopilot"*. Los 11 productos prometen preview;
  ninguno la hace **barata**.
- **Cómo se vería en tero:** el objeto `propuesta` ya tiene `resumen` y
  `vista_previa`. Falta que la TUI muestre **primero** la línea
  `accion + tipo + titulo` y `resumen` en una franja fija, y **después** la
  vista previa con scroll, de modo que el docente pueda decidir sin leer todo el
  markdown. En `editar`/`adaptar`, mostrar `cambios` **antes** de la vista previa.
- **Contrato:** sin cambio de esquema. Es orden de render en la TUI.
- **Costo:** bajo. **Cabe:** sí.

#### P0.2 Advertencia de alto riesgo en adaptación NEE (no vender documento oficial)

- **Problema del docente:** un material "adaptado a NEE" puede confundirse con un
  documento del **PIE** o con una adecuación curricular formal, que en Chile es un
  instrumento con valor normativo. Common Sense recomienda explícitamente
  **evitar** generar IEP / 504 / planes de conducta con IA; tres de las cuatro
  plataformas evaluadas lo ofrecen igual.
- **Cómo se vería en tero:** cuando `accion == "adaptar"`, `warnings` incluye
  **siempre** un aviso no bloqueante del tipo `nee_no_es_documento_oficial`:
  "Esto son apoyos y criterios para tu clase, no una adecuación curricular
  formal. Contrasta con el Decreto 83/2015 y el equipo PIE." El aviso **no
  bloquea la aprobación** (`PUERTA-Y-PR8.md`).
- **Contrato:** un `code` nuevo en `warnings`; nada más.
- **Costo:** bajo. **Cabe:** sí.

#### P0.3 `notas_nee` con vocabulario cerrado y atribuible, no prosa libre

- **Problema del docente:** "adaptado a NEE" sin decir **qué** se adaptó, **con
  qué criterio** y **con qué respaldo normativo** es un texto que no puede
  defender ante la dirección, la familia ni la Superintendencia.
- **La buena noticia: el contrato ya está escrito y es chileno.** El **Decreto
  83/2015** trae la taxonomía y los criterios exactos (§3.5). No hay que traducir
  marcos extranjeros.
- **Cómo se vería en tero:** `notas_nee` deja de ser `list[str]` y pasa a
  `list[NotaNee]`:

  | Campo | Tipo | Valores |
  | --- | --- | --- |
  | `tipo` | enum | `"acceso"` \| `"objetivos_aprendizaje"` (los dos tipos del Decreto 83) |
  | `criterio` | enum | `acceso`: `presentacion_informacion`, `formas_respuesta`, `entorno`, `organizacion_tiempo`. `objetivos_aprendizaje`: `graduacion_complejidad`, `priorizacion_objetivos`, `temporalizacion`, `enriquecimiento`, `eliminacion_aprendizajes` |
  | `descripcion` | string | **redacción propia de tero**: qué se hizo en este material |
  | `justificacion` | string | **obligatoria cuando `criterio == "eliminacion_aprendizajes"`** |
  | `fuente` | const | `"Decreto 83/2015, MINEDUC Chile"` + URL a `leychile.cl` |

- **La regla de oro como validación del host:** el decreto dice que hay que
  *"considerar **en primera instancia las adecuaciones curriculares de acceso
  antes de afectar los objetivos de aprendizaje**"*. Validación no bloqueante:
  si aparece un criterio de `objetivos_aprendizaje` y **ningún** criterio de
  `acceso`, emitir un `warning` (`nee_sin_apoyos_de_acceso`) recordando la
  regla. **No bloquea la aprobación** — es información para el docente.
- **Segundo vocabulario, opcional: UDL.** Si además se quiere mapear a DUA, usar
  `udl_version` (`"3.0"`), `udl_code` (`^[1-9]\.[1-9]$`, validado contra las 36
  consideraciones) y `udl_note`. **Por qué vocabulario cerrado:** evita que el
  modelo invente códigos, y es la **única parte del marco UDL que tero puede
  codificar sin riesgo legal**.
- **`requiere_paci` no lo decide tero.** En el FUDEI se marca si el estudiante
  requiere adecuaciones a los objetivos de aprendizaje, y ese booleano determina
  si corresponde un PACI. Es un campo oficial y fiscalizado: **tero no lo infiere
  ni lo emite.**
- **Contrato:** nuevo esquema en `templates/schemas/` o `curriculum/chile/`.
- **Costo:** medio (validación + prompt + offline). **Cabe:** parcialmente — ver
  abajo.
- **Estado actual del código (la migración conversacional ya está en `main`):**
  el tipo `Propuesta` está declarado en `tui/src/protocol.ts` con
  `accion: PropuestaAccion` (`"crear" | "editar" | "adaptar"`),
  `cambios: string[]`, **`notas_nee: string[]`** y `evidencias: Evidence[]`;
  `src/tero/approval.py` ya clasifica `aprobar | cambiar | descartar | preguntar |
  ambiguo` con la regla dura *"ante duda, no se aprueba"*.
- **Consecuencia de implementación:** pasar `notas_nee` de `string[]` a
  `NotaNee[]` **rompe el protocolo TUI↔host**, así que es un cambio coordinado
  (host + `protocol.ts` + offline), no un parche de una línea.
  **Lo que sí entra en 3 días sin romper el tipo:** exigir en el prompt que cada
  entrada de `notas_nee` venga **prefijada con el criterio del Decreto 83**
  (`"acceso · presentación de la información: …"`), lo que ya obliga al modelo a
  elegir del vocabulario cerrado y permite renderizarlo agrupado. **La estructura
  completa queda para después del cierre.**

#### P0.4 Herramienta de verificación de accesibilidad calculada por el host

- **Problema del docente:** no tiene forma de saber si el material que va a
  fotocopiar es legible para un estudiante con baja visión o dislexia.
- **Cómo se vería en tero:** una tool **de sólo lectura** (el modelo no puede
  escribir) que devuelve métricas calculadas en Python sobre el markdown
  generado: longitud media de oración, palabras por oración, proporción de
  oraciones largas, presencia de listas vs párrafos densos, y —si hay LaTeX o
  imágenes— recordatorios de `alt_text_decision` y `describedMath`. Se expone
  como `warnings` informativos, nunca bloqueantes.
- **Vocabulario de accesibilidad:** reutilizar `accessibilityFeature`
  (`alternativeText`, `describedMath`, `largePrint`, `highContrastDisplay`,
  `structuralNavigation`, `readingOrder`) del **W3C a11y-discov-vocab 1.1** como
  valores de un campo `accessibility`, en lugar de inventar etiquetas.
- **Por qué el host y no el modelo:** es aritmética, no generación. El host no
  puede alucinar un conteo, y así el warning es verificable.
- **Costo:** bajo-medio. **Cabe:** sí.

#### P0.5 Edición granular por sección en la propuesta

- **Problema del docente:** "regenerar todo" tira el trabajo que ya revisó. La
  investigación sobre edición documenta que los docentes ejecutan **cinco
  operaciones concretas**: agregar, extender, modificar, condensar y eliminar
  (Han y Li, 2026), y reclaman control **justo donde el juicio pedagógico importa
  más** (Wei et al., 2026).
- **Cómo se vería en tero:** al aprobar con `cambiar`, la nota libre ya viaja al
  agente; lo que falta es que `cambios` en la siguiente `propuesta` **nombre la
  sección** afectada (p. ej. `"Cierre: acortar a 5 minutos"`), para que el
  docente vea que se respetó el resto. Es un contrato de **etiquetado**, no un
  editor nuevo.
- **Costo:** bajo. **Cabe:** sí.
- **No hacer:** un editor markdown embebido. Prohibido por `AGENTS.md` (TipTap) y
  no es el problema.

#### P0.6 Puerta de aprobación con costo de revisión menor que aceptar a ciegas

- **Problema:** un "humano en el circuito" nominal no garantiza revisión. Jiang
  et al. (2026) muestran que los docentes **reconocen** que deben revisar pero
  **adoptan directamente por conveniencia**. El diseño debe hacer que revisar
  cueste menos que aceptar a ciegas.
- **Cómo se vería en tero:** (a) el número de `evidencias` verificadas `✓` vs
  parafraseadas `?` visible en la misma línea que el botón de aprobar; (b) los
  `warnings` **arriba** de la vista previa, no al final; (c) recordar en la franja
  que **los originales no se tocan** — la garantía estructural del host.
- **Costo:** bajo. **Cabe:** sí.

### P1 — Después del cierre, próximo ciclo

#### P1.1 Selector de nivel lector como operación de primera clase

- **Problema del docente:** es **la función de mayor valor percibido** de toda la
  categoría (Brisk "Change Level", Diffit, MagicSchool "Text Rewriter", Khanmigo
  "ajustar complejidad", Google "Re-level text", Almanack below/above-grade).
  Y es exactamente el cuello de botella de un curso heterogéneo.
- **Cómo se vería en tero:** una tool `adaptar_nivel(texto_o_path, nivel_destino,
  preservar_vocabulario=True)` que devuelve una `propuesta` con
  `accion: "adaptar"` y `cambios` explícitos. **`preservar_vocabulario` es la
  clave:** Microsoft es el único del conjunto que declara preservar el vocabulario
  técnico al bajar el nivel, y es justo el error que un docente detecta de
  inmediato.
- **Costo:** medio. **Cabe:** no (requiere rúbrica de nivel y pruebas en español).

#### P1.2 Métricas de legibilidad en español, calculadas en el host

- **Problema:** el "nivel" de un texto adaptado hoy es una afirmación del modelo.
  Con métricas en el host pasa a ser un **número** que el docente puede ver.
- **La dependencia ya existe:** **`textstat` (MIT) implementa 4 de las 6 fórmulas
  españolas** — Fernández-Huerta, Szigriszt-Pazos, Gutiérrez de Polini y Crawford
  — con `set_lang("es")` para el conteo de sílabas.
- **Qué está realmente verificado y qué no** (importante para no inventar
  precisión):
  - **INFLESZ / Flesch-Szigriszt:** **verificado en fuente arbitrada** —
    Barrio-Cantalejo et al., *Anales del Sistema Sanitario de Navarra* 2008;31(2),
    https://scielo.isciii.es/scielo.php?script=sci_arttext&pid=S1137-66272008000300004.
    Escala de **5 tramos**: *Muy Difícil* (<40) · *Algo Difícil* (40-55) ·
    *Normal* (55-65) · *Bastante Fácil* (65-80) · *Muy Fácil* (>80); umbral
    práctico **superar 55**. Calibración: Quiosco adultos 60, revistas
    científicas 37,9, **libros escolares 67,39**.
  - ⚠️ **Discrepancia de fórmula sin resolver:** el artículo imprime
    `INFZ = 206,835 – 62,3 × (Sílabas/Palabra – Palabras/Frases)`, mientras la
    literatura circulante usa los dos cocientes restados por separado. **No
    inventar coeficientes:** si se muestra INFLESZ, decir qué implementación se
    usó, o mejor **mostrar el tramo, no la fórmula**.
  - ⚠️ **Fernández-Huerta tiene 7 tramos ligados a nivel académico, pero los
    coeficientes y los cortes no se pudieron verificar** (la fuente primaria es
    *Consigna* nº 214, 1959, no digitalizada). `textstat` la implementa; **no
    afirmar que sus cortes son los oficiales**.
  - ⚠️ **INFLESZ está validado en España**, con hábitos lectores españoles — el
    propio artículo descarta Flesch y Szigriszt por eso. **No hay validación
    chilena localizada.** Usarlo como **indicador aproximado en la UI, nunca como
    criterio normativo.**
- **Cuidado con las licencias** (detalle en §3.2b): `legibilidad` es
  **GPL-3.0 de facto** aunque PyPI declare MIT, `language_tool_python` es
  **GPL-3.0**, y los modelos `es_core_news_*` de spaCy son **GPL-3.0 en los
  pesos** (el código de spaCy es MIT).
- **Costo:** bajo (la dependencia existe; el trabajo es de encuadre honesto).

#### P1.3 Continuidad entre sesiones por curso/asignatura, sin datos personales

- **Problema:** **ninguna** de las 11 herramientas comerciales recuerda al
  estudiante entre tareas (Brisk: *"feedback lives in the document"*; Eduaide:
  *"generations are one-shot"*; Almanack: *"no student assessment data
  tracking"*). Hay una tensión estructural: privacidad máxima ⇒ cero
  continuidad pedagógica.
- **Cómo se ve en tero:** tero **ya tiene** el activo que ninguno tiene — una
  carpeta que persiste y que nunca se sobrescribe. Basta un índice local en
  `.tero/` (no un "Biblioteca" UI, prohibido por `AGENTS.md`) que registre
  `{curso, asignatura, oa, tipo, fecha, path}` de lo aprobado, para que el agente
  pueda decir *"la semana pasada trabajaron el OA 4 con este texto"*.
- **Contrato:** un archivo de índice; el modelo sólo lo **lee**.
- **Costo:** medio. **Cabe:** no. Es la recomendación P1 con mejor relación
  valor/riesgo.

#### P1.4 Perfil de necesidades como datos estructurados, no como prompt

- **Problema:** hoy el docente escribe "tengo un niño con TDAH" en el prompt y esa
  información se pierde. La adaptación sería más útil si el perfil persistiera.
- **Cómo se vería en tero:** un archivo **local, sin datos personales**, en la
  carpeta de trabajo (p. ej. `.tero/perfil-adecuaciones.json`) con
  `{curso, apoyos: [{tipo: "acceso"|"curricular", descripcion, udl_code}]}`.
  El agente lo lee para adaptar y **nunca lo escribe**. Ventaja de privacidad:
  describe **apoyos**, no diagnósticos ni nombres — coherente con la postura de
  Almanack ("no student data required") pero sin perder continuidad.
- **Costo:** medio. **Cabe:** no, y **requiere decisión explícita de producto**
  por el riesgo de datos de menores.

#### P1.5 Alineación curricular como campo verificable con `educationalAlignment`

- **Problema:** "alineado al OA" hoy es una afirmación en prosa.
- **Cómo se vería en tero:** en el catálogo Chile, cada OA ya tiene `id`,
  `curso`, `asignatura`, `eje`. Añadir `objetivo_aprendizaje` +
  `educationalAlignment` (schema.org, CC BY-SA 3.0) con `alignmentType`,
  `educationalFramework: "Bases Curriculares MINEDUC"` y `targetName` permite
  que el host **valide** que el OA citado existe en el catálogo y que el curso
  declarado coincide — el warning `oa_mismatch` ya existe y ganaría precisión.
- **Costo:** bajo-medio. **Cabe:** parcialmente (el mapeo de campos es barato;
  ampliar el catálogo más allá de 4°–6° básico no).

#### P1.6 Export a QTI como puente a LMS, sin copiar código AGPL

- **Problema:** el terreno real de integración es el LMS (Canvas, Moodle,
  Schoology), no el botón "descargar". Pero **todos** los LMS relevantes son
  GPL/AGPL.
- **Cómo se vería en tero:** generar un **archivo QTI 3.0** (XML empaquetado) a
  partir del `payload` de una evaluación. QTI es un **formato abierto de
  1EdTech**: se implementa el formato, no se copia código de nadie. Brisk ya
  exporta QTI a Canvas; es un requisito de tabla.
- **Costo:** alto. **Cabe:** no.
- **Ojo:** QTI 3.0 es un estándar de 1EdTech; el esquema XSD es público pero la
  implementación completa es grande. No intentarlo en 3 días.

### P2 — Interesante, no ahora

#### P2.1 Publicar el material con metadatos de accesibilidad en JSON-LD

Si algún día el material sale de la carpeta, emitir `schema.org` JSON-LD con
`accessMode`, `accessibilityFeature`, `accessibilityHazard` y
`accessibilitySummary` es barato **una vez que P0.4 existe**, porque los valores
ya estarían calculados. Riesgo: schema.org es **CC BY-SA 3.0**, así que un
esquema derivado debería respetar esa licencia.

#### P2.2 Evaluación de calidad pedagógica como harness reproducible

La literatura ofrece rúbricas con base teórica para evaluar planes generados por
IA — alineación constructiva (Biggs), Bloom revisado (Anderson & Krathwohl),
coherencia interna, diferenciación, asignación de tiempo. Un harness local que
puntúe los borradores contra esos ejes convertiría "calidad" en una métrica del
repo, no en una opinión. **Costo:** medio-alto. **Cabe:** no. Nota: los dos
estudios localizados son de acceso abierto pero **no se verificó su licencia de
reutilización**; la rúbrica se puede reconstruir de fuentes primarias (Biggs,
Anderson & Krathwohl), no copiar del paper.

#### P2.3 Explicitaciones de incertidumbre calibrada

Karim, Wang y Yuan (EMNLP 2025) muestran clasificadores con garantías formales de
cobertura (conjuntos de predicción al 90 %). Es el rasgo con mejor base técnica
**y el más barato de implementar** según el informe de confianza. En tero se
vería como un campo de confianza por evidencia. **Costo:** bajo, pero requiere
un calibrador entrenado; el valor percibido por el docente no está demostrado
para este caso de uso. **Cabe:** no.

---

## 3. Formatos y datos abiertos

### 3.1 Currículum

| Qué | URL | Notas |
| --- | --- | --- |
| Catálogo Chile de tero | `curriculum/chile/catalogo.json` | 4°–6° básico, Lenguaje/Matemática/Ciencias. **Paráfrasis orientativas, no texto oficial MINEDUC verbatim.** |
| Curriculum Nacional (MINEDUC/UCE) | https://www.curricumnacional.cl → **real:** https://www.curricumnacional.cl/ | **`no verificado`: no responde desde esta red (timeout).** Existen documentos oficiales (PDF/DOCX) en ese dominio según resultados de búsqueda; **no se pudo confirmar que exista una API pública.** Tratar como "sin API conocida". |
| Ley Chile (BCN) | https://www.bcn.cl/leychile/ | Requiere `User-Agent` de navegador (sin él devuelve 401). |
| **API oficial de Ley Chile** | Spec OpenAPI 3.1: https://www.bcn.cl/leychile/leychile-api-doc/assets/leychile-api-doc-v1.yaml · servidor `https://www.bcn.cl/leychile/api/v1` · condiciones: https://www.bcn.cl/leychile/api/condiciones-de-uso · solicitud de API-KEY: https://www.leychile.cl/leychile/privado/admin/api/solicitud | **Existe y está documentada.** Auth por `apiKey` en query param `secret`; cuota **500 solicitudes / 24 h**. **PERO la licencia de contenidos es CC BY-NC-ND 4.0** — ver riesgo grave en §4.1. |
| Endpoint JSON histórico (sin key) | `https://servicios-leychile.bcn.cl/Navegar/get_norma_json?idNorma=<id>` | **Endpoint no documentado. Fiable para normas antiguas, NO para recientes.** Verificado: `idNorma=1074511` → `Decreto-83 EXENTO` (correcto), pero **`idNorma=1190987` → `Decreto-188` de Transportes** y **`idNorma=1191290` → `Decreto-86` de "Otorgamiento de destinación marítima"** — ninguno es la Ley 21.545. **El servicio contradice lo que sirve la página `navegar?idNorma=`.** Consecuencia: **no usar este endpoint para descubrir ni verificar el `idNorma` de una norma reciente**, y **no inventar el id** de la Ley 21.545: citarla por su **número de ley** (`Ley 21.545`, publicada el 10-03-2023) y buscar la URL a mano. Para normas antiguas y estables sirve como verificación puntual. |
| **Curriculum Nacional — JSON:API** | https://www.curriculumnacional.cl/jsonapi | **Sí existe API pública** (Drupal JSON:API, anónimo). Endpoints: `/jsonapi/node/recurso` (**43.298 nodos**, con relaciones `field_cn_learning_objectives`, `field_cn_grades`, `field_cn_subjects`, **`field_licencia`**, `field_adjuntos`, `field_alineacion_curricular`; usar `?include=field_licencia,field_adjuntos`), `/jsonapi/cn_learning_objective/cn_learning_objective` (**3.139 códigos OA**, atributo `code`), `cn_grade` (32), `cn_subject` (147), `cn_topic` (218), `taxonomy_term/licencia` (8). **Bloqueados para anónimo:** `cn_attitude_learning_objective` (643 OAT), `cn_skill_learning_objective` (351), `cn_subject_plan` (3). `page[limit]` tope **6** en `node--recurso` y 50 en `cn_*`. ⚠️ **Drupal interno, indocumentado y sin versión**: cachear agresivamente y degradar a parseo local de PDFs. |
| **Curriculum Nacional — HTML público** | `https://www.curriculumnacional.cl/curriculum/<nivel>/<asignatura>/<curso>/<slug-oa>` (p. ej. `/curriculum/1o-6o-basico/lenguaje-comunicacion/4-basico`) | Fuente del **texto** de los OA. `api.curriculumnacional.cl` **no resuelve** y `sitemap.xml` da 404 — no usar esas rutas. **`no verificado` desde esta red:** el host no respondió (timeout) en esta sesión; la estructura proviene de una verificación que sí completó. Probar conectividad antes de prometer scraping. |
| **PDFs oficiales con URL estable** | `https://www.curriculumnacional.cl/sites/default/files/newtenberg/614/articles-<id>_<nombre>.pdf` (p. ej. `.../articles-22394_bases.pdf`) | Patrón verificado. ⚠️ Los PDF **no llevan aviso de licencia interno** (grep en las Bases 1°–6°, 414 páginas: cero menciones de ©/derechos/CC). La cita debe apuntar al **registro del sitio + fecha de consulta**, no al archivo. |
| **Esquema canónico de códigos OA** | Mismo dominio | Confirmado alfanumérico: `LE04 OA 01`…`OA 30` (Lenguaje 4°), `CN06 OA 01`…, `MA04 OA 01`…, `HI01 OA 01`…; **actitudes** `LE04 OAA A`…`G`; **3°/4° medio FG** `FG-LELI-3M-OAC-01`…`09`; **parvularia** `OA 01 LV NT` / `OA 01 LA NT`. El JSON:API sólo guarda `"OA 1."`: la sigla compuesta se arma con grado+topic o se saca del HTML. **`no verificado`:** patrón de rutas HC/TP (devolvieron 404) — no inventarlo. |
| **SIMCE / IDPS — API pública** | `https://informacionestadistica.agenciaeducacion.cl/rest/archivo/getAllByTipo/0` (JSON, 144 registros: Simce 71, IDPS 28, categorías 7) · descarga `rest/archivo/obtener?uuid=<uuid>%3B1.0` | Sin autenticación. Cobertura **Simce 1998→2024, IDPS 2014→2024**, por establecimiento/comuna/región. **Licencia `no verificado`:** el portal **no publica licencia ni términos** (pie: *"© Agencia de Calidad de la Educación 2026"*) → **pedir autorización antes de redistribuir**. 🚨 **Ese endpoint filtra credenciales**: cada registro incluye un objeto `usuario` con **password en base64** y `esAdministrador`. **No construir sobre esa forma de endpoint** y **reportarlo a la Agencia**. |
| Chile en estándares internacionales | — | **Chile no publica currículum en CASE, LOM ni Dublin Core** (0 coincidencias en los 109 resource types del JSON:API, en 21 términos de documentación curricular y en 37 de formato; las páginas de 1EdTech CASE no mencionan Chile). La adopción de CASE **no tiene fuente local**. |
| CASE Network (1EdTech) | https://www.1edtech.org/standards/case · https://case.network/ | Estándar de intercambio de estándares (JSON/XML) con identificadores `GUID` por competencia. Google etiqueta estándares vía **CASE Network 2**. Adopción completa: **fuera de alcance**; adoptar el **concepto de identificador estable**. |
| ASN (Achievement Standards Network) | https://asn.desire2learn.com/ | Vivo, pero el dominio histórico `achievementstandards.org` **ya no responde**. Antes de depender de él, verificar términos. |
| schema.org `educationalAlignment` | https://schema.org/educationalAlignment · https://schema.org/AlignmentObject | `alignmentType`, `educationalFramework`, `targetName`, `targetUrl`. **CC BY-SA 3.0.** |
| LRMI (Learning Resource Metadata Initiative) | https://www.dublincore.org/specifications/lrmi/ | Vivo. Vocabulario de metadatos de recurso educativo; base de `educationalAlignment`. |
| schema.org `LearningResource` | https://schema.org/LearningResource | Tipo padre para material educativo. |

**Dos esquemas de identificador conviviendo.** El catálogo de tero usa
`LEN-4B-OA04` (asignatura-curso-OA), que es **cómodo y estable pero propio**. El
esquema canónico chileno es alfanumérico y distinto: `LE04 OA 04`, con variantes
`OAA` para actitudes y `FG-LELI-3M-OAC-01` para formación general de 3°/4° medio.
**La correspondencia entre ambos no está verificada contra fuente oficial** —
el catálogo se declara paráfrasis. Si se adopta `educationalAlignment`,
`targetName` debería llevar el **código canónico** (`LE04 OA 04`) y `targetUrl`
la fuente oficial; el id interno de tero queda como clave local.

**Datos abiertos chilenos: hallazgos negativos verificados.**

| Fuente | Resultado |
| --- | --- |
| `datos.gob.cl` (portal CKAN) | **No existe dataset de currículum.** 3.209 datasets, 272 organismos; `curriculum`, `curricular`, `curriculo`, `bases curriculares`, `minedu` y `textos escolares` devuelven **0 resultados**. `ministerio-de-educacion` tiene 1 dataset; `subsecretaria_de_educacion` 30, todos administrativos (matrícula, SIMCE, docentes, FUAS). ⚠️ **La licencia por defecto publicada es una trampa:** los términos dicen que *"la licencia predeterminada para la publicación de datos es Creative Commons Zero (CC0)"* (https://datos.gob.cl/terms_and_conditions), pero el facet real sobre 3.211 datasets es **`cc-nc` 1.310 (41 %)**, `cc-by` 922, `cc-zero` 462 — y en el subconjunto **educación (166) el `cc-nc` sube a 124 (75 %)**. **Leer `license_id` por dataset, nunca asumir el default.** SIMCE 2025 es **CC0**; SIMCE 2006-2012 es **CC-NC**. |
| `datosabiertos.mineduc.cl` | **Portal propio de MINEDUC** (WordPress). **No hay API** (la ruta CKAN `/api/3/action/package_list` responde "Página no encontrada"; `/wp-json/` da **401**) y **no hay página de licencia** (404). `datos.mineduc.cl` **no existe** (falla TLS) — no citarlo. Sí publica [Planes y Programas de estudio](https://datosabiertos.mineduc.cl/planes-y-programas-de-estudio/) 2002→2025 en `.RAR` anual (p. ej. `.../wp-content/uploads/2026/03/Planes-y-Programas-de-Estudio-2025.rar`, 4,9 MB) → **CSV de ~327 MB, 1.318.796 filas** con esquema oficial de identificadores: **`COD_PLAN_EST`** (código del plan = nº y fecha del decreto), `NOM_PLAN_EST`, `TIPO_PLAN_EST` (0=indicativo, 1=propio), `COD_DEC_EV`, `COD_SUBSECTOR`, `COD_ENSE/GRADO/RAMA/SEC/ESPE`. ⚠️ **No es el texto de los programas**: es el registro por estudiante de qué plan cursó → sirve para mapear **curso local → plan y decreto oficial**. También publica el **Directorio de Establecimientos 1992→2025**. |
| Decretos curriculares citables | Página madre: https://www.curriculumnacional.cl/Curriculum/Normativa — **439/2012** y **433/2012** (bases básica etapas 1 y 2), **614/2013** y **369/2015** (7° básico–2° medio), **193/2019** (3°–4° medio), **10/2022** (EPJA), **481** (parvularia), **97** (pueblos originarios), **Decreto Exento 83** (adecuación NEE). Estándares: **DS 129/2013**, **178/2015**, **225/2017**, **129/2019**, **158/2022**, **DS 171/2026**. |

**Verificación empírica del vínculo plan ↔ decreto.** Se descargó y procesó el
CSV oficial de Planes y Programas 2025 (1.318.796 filas) para comprobar el valor
real de `COD_DEC_EV`. Resultado: **el campo sólo tiene 6 códigos distintos no
vacíos** — `1121999` (112 DE 1999), `21692007` (2169 DE 2007), `5111997`
(511 DE 1997), `672018` (67 DE 2018), `832001`/`83` (83 DE 2001) — más `0`
(indicativo) y vacíos. Es decir: **el dataset cubre planes de educación de
adultos y programas especiales, no el currículum regular completo.** El campo
existe y es oficial, pero **no permite mapear todo el currículum a su decreto**.
Nota metodológica: los datos vienen `;`-separados con BOM UTF-8 y columnas
multilínea — `awk -F';'` con el índice de campo equivocado devuelve basura sin
avisar. Verificar el índice contra una fila de muestra antes de confiar en el
resultado (aquí se hizo: `COD_DEC_EV` está en el campo **27**, no 26).

### 3.2 Rúbricas y evaluación

**Sí existe un esquema abierto de rúbrica descubierto en esta investigación:**
el **ASN Rubric Model** — http://standards.asn.desire2learn.com/rubric.html —
licencia **CC BY 4.0** literal, con las clases `Rubric`, `RubricCriterion`,
`CriterionLevel`, `CriterionCategory` y `ProgressionModel`, y anexos **AAC&U
VALUE** y **EntreComp** en JSON-LD. **Caveat:** está **dormido desde 2019** y no
tiene XSD propio.

`templates/latex/schemas/pauta.json` de tero ya define
`{criterios: [{nombre, descriptores[]}], niveles[]}`. Recomendación: **mantener
el formato propio** (simple, sin dependencias) y mapear a ASN o CASE **sólo si
aparece una necesidad real de interoperabilidad**. Naming alineado con ASN:
`criterios` ≈ `RubricCriterion`, `niveles` ≈ `CriterionLevel`.

| Qué | URL | Licencia / nota |
| --- | --- | --- |
| **ASN Rubric Model** | http://standards.asn.desire2learn.com/rubric.html | **CC BY 4.0.** Esquema abierto real. Dormido desde 2019. |
| Esquema de pauta de tero | `templates/latex/schemas/pauta.json` | Formato propio. `criterios[].nombre` + `descriptores[]` + `niveles[]`. |
| QTI 3.0 (1EdTech) | https://www.imsglobal.org/spec/qti/v3p0/ | Formato abierto de ítems. XSD descargables sin cabecera de licencia. **Implementable; las muestras oficiales son sólo para miembros y no se pueden re-licenciar.** Ojo: **"QTID" no existe.** |
| Open Badges 3.0 | https://www.imsglobal.org/spec/ob/v3p0/ | Doc v1.4.5 (2026-06-29), es un VC. Validador: `1EdTech/openbadges-validator-core`, **Apache-2.0, Python** — la mejor dependencia lista si se necesitara. |
| CLR 2.0 (1EdTech) | https://www.imsglobal.org/spec/clr/v2p0/ | Final 2.0, 2025-10-14. Tiene `RubricCriterionLevel`. Fuera de alcance. |

### 3.2b Librerías reutilizables para calidad pedagógica

**Legibilidad en español — el hallazgo que ahorra trabajo:**

| Librería | Licencia | Nota |
| --- | --- | --- |
| **`textstat`** | **MIT** | ✅ **Ya implementa 4 de las 6 fórmulas españolas**: Fernández-Huerta, Szigriszt-Pazos, Gutiérrez de Polini y Crawford, con `set_lang("es")` para sílabas. **Es la dependencia obvia para P1.2.** |
| `pyphen` | Tri-licencia **GPL-2.0+ / LGPL-2.1 / MPL-1.1** | Elegir **LGPL o MPL**, nunca la GPL. Segmentación silábica. |
| INFLESZ | — | Son **5 bandas de Szigriszt-Pazos**: 3 líneas propias de código, no una librería. |
| SOL | — | **No es "Sistema de Lecturabilidad"**: son fórmulas de conversión de SMOG (Contreras, 1999), **sin implementación abierta**. |
| ❌ `legibilidad` | **GPL-3.0+ de facto** | **PyPI miente: declara MIT**, pero el sdist trae cabecera GPL y el repo es GPL-3.0. |
| ❌ `language_tool_python` | **GPL-3.0** | Gramática. Alternativa: **LanguageTool como servicio Java (LGPL-2.1)**. |
| ❌ spaCy `es_core_news_sm/md/lg` | **GPL-3.0 en los pesos** | El código de spaCy es MIT, **los modelos en español no**. No empaquetar ni autodescargar. |
| ❌ `MultiAzterTest` / `AzterTest` / `spanish-nlp` | **GPL-3.0** | — |
| ❌ `egtcpu/legibilidad` | **AGPL-3.0** | Peor que GPL. |
| ✅ `venezuelau/spanish-readability` | **MIT** | Vendorizar (no está en npm). |
| ✅ `readability` (Python) | **Apache-2.0** | Alternativa. |
| ✅ `pyspellchecker` · `symspellpy` | **MIT** | Ortografía. |

**Scoring, rúbricas y evaluación:**

| Librería | Licencia | Nota |
| --- | --- | --- |
| `scikit-learn` | **BSD-3-Clause** | QWK (`cohen_kappa_score`) para acuerdo con corrección humana. |
| `deepeval` | **Apache-2.0** | Incluye G-Eval. (El paper original de G-Eval es **CC BY-NC-ND**: el código sí, el paper no.) |
| `ragas` · `prometheus-eval` · `auto-rag-eval` | **Apache-2.0** | — |
| `promptfoo` · `inspect_ai` · `promptflow` · `openai-evals` · `rubric` | **MIT** | `inspect_ai` es el harness más cómodo para un CI de calidad. |
| `hermes-rubric` | **Apache-2.0** | — |
| ⚠️ `Langfuse` | **MIT excepto `ee/`** | La carpeta `ee/` es Enterprise. No vendorizar el árbol completo. |
| ⚠️ `veraPDF` | **Dual GPL-3.0+ / MPL-2.0+** | Usar **MPL**. Valida accesibilidad de PDF. |

**Accesibilidad y entrega de documentos:**

| Librería | Licencia | Nota |
| --- | --- | --- |
| `axe-core` | **MPL-2.0** | ✅ Permisiva débil, compatible con MIT. Envoltorios MIT/MPL. |
| ⚠️ `pa11y` | **LGPL-3.0-only** | Complicado de empaquetar. Preferir `axe-core` o `vnu-jar`. |
| `eslint-plugin-jsx-a11y` | **MIT** | — |
| `lighthouse` · `equal-access` · `color-contrast-checker` | **Apache-2.0** | — |
| `html-validate` · `vnu-jar` | **MIT** | Validación HTML. |
| `wcag-contrast` | **BSD-2** | Cálculo de contraste. |
| `reportlab` | **BSD-3** | PDF. |
| `python-docx` · `openpyxl` · `beautifulsoup4` | **MIT** | DOCX/XLSX/HTML. |
| `jinja2` · `pandas` | **BSD-3** | — |

### 3.3 Accesibilidad — el vocabulario listo para usar

**Fuente autoritativa: W3C a11y-discov-vocab 1.1** (Final Community Group
Report, 26-03-2026):
https://www.w3.org/community/reports/a11y-discov-vocab/CG-FINAL-vocabulary-20260326/

- La URL histórica `https://www.w3.org/2021/a11y-discov-vocab/` **da 404**, y
  `/latest/` es un stub con meta-refresh: **no usar para fetch programático.**
- Origen: propiedades desarrolladas por **Benetech e IMS Global**, derivadas del
  **AccessForAll (AfA) Information Model** de 1EdTech. Esa es la cadena de
  atribución.
- **No es un estándar W3C** (es un Final Community Group Report), pero es el
  vocabulario al que apunta schema.org, y sus listas son **cerradas**.

Campos propuestos para tero:

| Campo | Cardinalidad | Vocabulario |
| --- | --- | --- |
| `accessMode` | uno | `auditory`, `tactile`, `textual`, `visual` |
| `accessModeSufficient` | lista | los mismos 4 |
| `accessibilityFeature` | lista | 43 valores en 7 grupos (estructura, adaptación, control de render, marcado especializado, claridad, táctil, internacionalización) |
| `accessibilityHazard` | lista | 11 valores (movimiento, sonido, destello) |
| `accessibilityAPI` | uno | 14 valores (`ARIA` está **deprecado** como API: usar `accessibilityFeature: "ARIA"`) |
| `accessibilityControl` | lista | **6** valores (`fullKeyboardControl`, `fullMouseControl`, `fullSwitchControl`, `fullTouchControl`, `fullVideoControl`, `fullVoiceControl`) |
| `accessibilitySummary` | uno | texto libre en español (único campo no enumerado) |

Cuidados verificados:

- **`captions` está deprecado** → usar `closedCaptions` / `openCaptions`.
- **`annotations` y `bookmarks` están deprecados.**
- Los placeholders **`none` / `unknown` no deben combinarse** con ningún otro valor.
- **`haptic` no es un valor de `accessibilityFeature`** (sí lo es de
  `adaptationType` en AfA).

Otros marcos de accesibilidad:

| Qué | URL | Licencia / nota |
| --- | --- | --- |
| schema.org accesibilidad | https://schema.org/accessibilityFeature · https://schema.org/accessibilitySummary · https://schema.org/accessMode · https://schema.org/accessModeSufficient · https://schema.org/accessibilityHazard | **CC BY-SA 3.0.** Las 7 propiedades son de tipo `Text`; **no hay tipo enumeración** y `schema.org/AccessibilityFeature` **da 404**. |
| 1EdTech AccessForAll | https://www.1edtech.org/standards/accessibility/index | `1edtech.org/standards/accessforall` **da 404**. AfA usa **`adaptationType`, `hazard`, `controlFlexibility`, `apiInteroperable`** — no los nombres de schema.org. La especificación PNP está en **Public Draft (2012)** y el acceso a `/standards/afa-pnp` redirige a login. |
| WCAG 2.2 | https://www.w3.org/TR/WCAG22/ · Quickref: https://www.w3.org/WAI/WCAG22/quickref/ | Criterios citables por identificador. Relevantes para material de aula: `1.4.3` contraste (AA), `1.4.11` contraste no textual (AA), `1.4.12` espaciado de texto (AA), `1.4.5` imágenes de texto (AA), `3.1.3` palabras inusuales (AAA), `3.1.5` nivel lector (AAA), `3.1.6` pronunciación (AAA). **`2.4.13` Focus Appearance es AAA, no AA.** Licencia W3C Document License: **no permite derivados.** |
| EPUB Accessibility 1.1 | https://www.w3.org/TR/epub-a11y-11/ | Usa el string de conformidad `EPUB Accessibility 1.1 - WCAG 2.2 Level AA` (**no un URI**). W3C Software and Document License (permisiva). |
| EPUB 3 | https://www.w3.org/TR/epub-33/ | Metadatos de accesibilidad en el paquete. |
| Alt text — árbol de decisión | https://www.w3.org/WAI/tutorials/images/decision-tree/ | Decisión tipada reutilizable: decorativa / funcional / informativa / compleja. |
| Poet (Benetech/DIAGRAM) | https://poet.diagramcenter.org/ | Herramienta de **entrenamiento** para describir imágenes (no es "Publisher's Online Editing Tool"). |

### 3.4 UDL / DUA — y la advertencia legal

**Estructura vigente (UDL Guidelines 3.0, publicadas el 30-07-2024):**

- **Tres principios:** Engagement (directrices **7-8-9**), Representation
  (**1-2-3**), Action & Expression (**4-5-6**). La numeración **no es
  consecutiva**: Engagement va al final, arrastrado de versiones anteriores.
- **Tres capas:** `access` / `support` / `executive_function` (en 2.2 eran
  `access` / `build` / `internalize` / `goal`).
- **36 consideraciones**, no 31 checkpoints. **Cambio de vocabulario clave:**
  `Consideration 1.1 "Support opportunities to customize the display of
  information"`. La frase habitual *"Checkpoint 1.1 Offer ways of customizing the
  display of information"* es **vocabulario 2.2**.
- **Consecuencia de contrato:** hace falta un campo **`udl_version` obligatorio**,
  porque el mismo código `1.1` significa cosas distintas según versión.
- **Español:** existe versión oficial en https://udlguidelines.cast.org/es/ y el
  organizador gráfico en **español latinoamericano** (donado por el Dr. Juan
  Carlos Araya Vargas, Universidad Central de Chile):
  https://udlguidelines.cast.org/static/udlg3-graphicorganizer-digital-numbers-a11y-spanish-latin-america.pdf
  Cita sugerida por CAST: *CAST (2024). CAST Universal Design for Learning
  Guidelines version 3.0. https://udlguidelines.cast.org*.
- **No existe** versión machine-readable oficial de UDL (sólo PDF/DOCX). Sí hay
  un checklist descargable: *"Key Questions to Consider When Planning Lessons"*
  (3 bloques de preguntas, **sin numeración**).

**La salida elegante: usar el Decreto 83 en vez de CAST.** El Decreto 83/2015
**ya incorpora el DUA** con sus tres principios en español oficial (§3.5) y fija
el escalonamiento DUA → diagnóstico → adecuación. Para un docente chileno, citar
el decreto es **más útil y más defendible** que citar un marco extranjero, y de
paso **esquiva el problema de licencia de CAST**. Recomendación: **Decreto 83 como
marco primario**, identificadores UDL sólo si se necesita el mapeo internacional.

**Advertencia legal — leer antes de codificar:**

CAST **no** publica las Pautas UDL bajo Creative Commons. Verificado en
https://www.cast.org/copyright/ y https://www.cast.org/terms-of-use/ (ambos 200):

> *"You may not change the materials found on the CAST websites without CAST's
> written permission."*
>
> *"Copy any of the material on Our Sites without Our prior written consent
> unless such copying is expressly permitted by virtue of a license granted on
> the applicable Site."*

Consecuencias para tero:

1. **Se puede** citar con la cita oficial y enlazar al sitio.
2. **Se puede** guardar copia local del organizador para uso educativo limitado,
   sin cobro y con el aviso `© CAST, 2024`.
3. **NO se puede** modificar el organizador (recortarlo, re-etiquetarlo,
   traducir campos, incrustarlo en una UI propia) sin permiso escrito.
4. **NO se puede** publicar un esquema derivado que **reproduzca el texto** de las
   36 consideraciones en un repo MIT.
5. **Postura defendible:** mapear **sólo los identificadores numéricos**
   (`1.1`…`9.4`) + la cita, con `descripcion` **redactada por tero**. El texto de
   la adaptación es de tero; el código es de CAST.

**No existe** versión machine-readable oficial de UDL: no hay JSON, XML ni API.

### 3.5 Normativa chilena NEE

| Norma | URL canónica | Qué obliga / aporta |
| --- | --- | --- |
| **Decreto 83/2015** | https://www.bcn.cl/leychile/navegar?idNorma=1074511 | La norma madre. **Trae el contrato de datos ya escrito** — ver abajo. |
| **Decreto 170/2009** | https://www.bcn.cl/leychile/navegar?idNorma=1012570 | Define **NEE permanente** (Título IV, 6 categorías) vs **NEE transitoria** (Título III, 4 categorías). Arts. 11 (reevaluación anual), 12 (informe anual), 94 (cupos: 2 permanentes + 5 transitorias por curso). |
| **Ley 20.422** | https://www.bcn.cl/leychile/navegar?idNorma=1010903 | Art. 3 define **Diseño Universal** y **Accesibilidad Universal**; art. 36 obliga a incorporar adecuaciones curriculares y **adaptar materiales**. |
| **Ley 21.545 (2023, TEA)** | **Ley 21.545**, publicada el 10-03-2023. `idNorma` **no confirmado** (§3.1). | Título IV, arts. 18-21. **Ojo:** la ley **no** dice "ajustes razonables" — dice *"los ajustes necesarios en sus reglamentos y procedimientos internos"*. No citarla mal. |
| **Educación Especial MINEDUC — documentos** | https://especial.mineduc.cl/documentos/ | **Sí publica formularios oficiales** (ver abajo). |
| **Anexo PIE 2025** | https://especial.mineduc.cl/wp-content/uploads/sites/31/2025/04/ANEXO-PIE_2025-version-actualizada.pdf | Documentación, procesos y vigencia del PIE. Contiene el campo booleano que gobierna el PACI. |
| **Instructivo FUDEI-PIE 2026** | `https://especial.mineduc.cl/wp-content/uploads/sites/31/2026/04/INSTRUCTIVO-INTEGRACIÓN-FUDEI_PIE-ACTUALIZADO-2026.pdf` | **La URL lleva `Ó` literal UTF-8**; percent-encoded (`%C3%93`) da 404. **FUDEI** = *Formulario Único de Evaluación Integral*, obligatorio desde 2025 antes de postular a PIE. Es **plataforma web** (RUT + clave), **no** plantilla PDF/DOCX. |

#### Decreto 83/2015 — la taxonomía exacta que el contrato debe codificar

El decreto define **dos** tipos de adecuación (no tres), con criterios enumerados:

**a) Adecuaciones curriculares de acceso** — *"reducir o incluso eliminar las barreras… sin
disminuir las expectativas de aprendizaje"*. **4 criterios:**

1. `presentacion_informacion` — modos alternativos: auditivo, táctil, visual y combinaciones.
2. `formas_respuesta` — distintas formas y dispositivos: escrito, Braille, lengua de señas, oral,
   ilustración, manipulación, multimedia.
3. `entorno` — espacio, ubicación y condiciones donde se desarrolla la tarea.
4. `organizacion_tiempo` — horario y tiempo: adecuación del tiempo de tarea/evaluación, pausas.

**b) Adecuaciones curriculares en los objetivos de aprendizaje** — **5 criterios:**

1. `graduacion_complejidad` — metas más pequeñas o más amplias.
2. `priorizacion_objetivos` — jerarquizar sin renunciar.
3. `temporalizacion` — flexibilizar tiempos sin alterar la secuencia.
4. `enriquecimiento` — incorporar objetivos **no previstos** en las Bases Curriculares.
5. `eliminacion_aprendizajes` — *"decisión a tomar en **última instancia**"*.

**Regla de oro (verbatim) — la restricción más importante del contrato:**

> *"Las adecuaciones curriculares a utilizar para los estudiantes con necesidades educativas
> especiales **no deberían afectar los aprendizajes básicos imprescindibles**; por lo tanto, es
> importante considerar **en primera instancia las adecuaciones curriculares de acceso antes de
> afectar los objetivos de aprendizaje del currículo**."*

Traducido a contrato: **`acceso` debe considerarse antes que `eliminacion`**, y `eliminacion` exige
justificación explícita. Ese es el check válido, publicado y defendible.

> **Nota de taxonomía:** el Decreto 83 **no usa** "acomodación" ni "modificación" (vocabulario
> US/IDEA). La equivalencia *acceso ≈ accommodation*, *objetivos ≈ modification* es una **analogía,
> no una equivalencia oficial**: no citarla como si el decreto las identificara.

#### El instrumento se llama PACI — y sus 11 campos son un contrato ya escrito

**PACI = *Plan de Adecuaciones Curriculares Individualizado*** (no "ACI"). El decreto enumera sus
**11 aspectos mínimos**: identificación del establecimiento; identificación del estudiante y sus NEE
individuales y contextuales; tipo de adecuación y criterios; asignatura(s); herramientas o
estrategias metodológicas; tiempo de aplicación; responsable(s); recursos humanos y materiales;
estrategias de seguimiento y evaluación; evaluación de resultados de aprendizaje; revisión y ajustes.

Estatus (verbatim): es *"un **documento oficial ante el Ministerio de Educación**"* que *"debe
acompañar al estudiante durante su trayectoria escolar"*, y la evaluación, calificación y promoción
*"se determinará en función de lo establecido en el **PACI**"*.

**El booleano oficial que gobierna todo:** en el FUDEI se marca SÍ/NO si el estudiante *"requiere
adecuaciones curriculares a los objetivos de aprendizaje"*; si está en **SÍ**, *"requerirán contar
con dicho documento [PACI]"* para la fiscalización de la Superintendencia. → **`requiere_paci` es un
campo oficial, publicado y fiscalizado. El PACI no es para todos los estudiantes.**

**`no verificado`:** no existe plantilla PACI descargable (se elabora localmente sobre los 11
campos) y no hay API ni export JSON de la plataforma PIE.

**Consecuencia de producto:** tero **no genera un PACI**. Un PACI es un documento oficial con
responsables legales, fiscalización y efectos en la promoción. tero puede producir **apoyos de
acceso para la clase**, y debe decirlo.

#### DUA ya está dentro del Decreto 83

El decreto menciona el DUA explícitamente y fija el **escalonamiento**: DUA primero → si no basta,
evaluación diagnóstica individual → adecuación curricular. Sus tres principios, en español oficial:
**a)** múltiples medios de **presentación y representación**; **b)** múltiples medios de **ejecución y
expresión**; **c)** múltiples medios de **participación y compromiso**.

Esto importa: **tero puede citar el Decreto 83 para el DUA en vez de CAST**, y así esquiva el
problema de licencia de las Pautas UDL (ver §3.4). El vocabulario chileno es además el que el
docente reconoce.

### 3.6 Diferenciación, andamiaje y taxonomía de apoyos

**La pieza más valiosa y con mejor licencia de toda la investigación: el
CCSSO Accessibility Manual (2021), CC BY 4.0** —
https://www.isbe.net/Documents/accommodations_manual.pdf. Trae
**Three-Tiered Approach → Five-Step Decision-Making Process → Tools 1–11**
(conjuntos de preguntas que son **checklists de facto**) → Appendices A–E.

Sus definiciones verbatim dan la **taxonomía limpia que tero necesita** para
`notas_nee`, y son mejores que el vocabulario US/IDEA genérico:

| Categoría | Definición (verbatim) | Efecto en las expectativas |
| --- | --- | --- |
| **Universal features** | *"available to all students"* | No cambian nada |
| **Designated features** | *"for whom the need has been identified by an informed educator or team"*, *"assigned using a consistent process"* | No cambian nada |
| **Accommodations** | *"changes in procedures or materials which (a) ensure… equitable access… and (b) support valid assessment results… **do not reduce expectations for learning**"* | **Preservan** las expectativas |
| **Modifications** | *"practices or materials that **change, lower, or reduce state-required learning expectations**… may change the underlying construct"* | **Bajan** las expectativas. En evaluación: *"constitutes a test irregularity, **invalidates test scores**, and results in an investigation"* |

⚠️ **El modelo de 3 niveles (2021) reemplazó al de 4 categorías de 2005**
(presentation / response / setting / timing-scheduling, CCSSO *Accommodations
Manual* 2nd ed., https://nceo.umn.edu/docs/OnlinePubs/AccommodationsManual.pdf).
Y NCEO advierte que *"the terminology… may differ by state and by assessment"* →
**versionar siempre el marco citado.**

⚠️ **"Scaffolds" NO es una categoría publicada.** No aparece como categoría par
en CCSSO 2005, CCSSO 2021, NCEO ni IDEA. **Existen dos familias: preserva
expectativas (accommodation) vs baja expectativas (modification).** Modelarlo como
**metadato** (`temporary_support: true`), **no** como valor hermano del enum. No
inventarle respaldo normativo.

⚠️ **Chile ↔ EE. UU. no está mapeado en ninguna fuente publicada.** La analogía
*acceso ≈ accommodation*, *objetivos ≈ modification* es **interpretación nuestra**
(§3.5 ya lo advierte). No citarla como equivalencia oficial.

**Universal Design of Assessment** — 7 elementos, útiles como checklist de diseño
de una evaluación: población de evaluación inclusiva · constructos definidos con
precisión · ítems accesibles y no sesgados · susceptibles de acomodaciones ·
instrucciones simples, claras e intuitivas · máxima legibilidad y comprensibilidad
· máxima legibilidad tipográfica. https://nceo.info/Assessments/universal_design

**Andamiaje cognitivo, con licencias limpias:**

| Marco | Fuente | Licencia / nota |
| --- | --- | --- |
| **Bloom revisado** | 6 procesos (`remember`→`create`) + **19 procesos específicos** (`1.1 Recognizing`…`6.3 Producing`) + 4 dimensiones de conocimiento (Factual/Conceptual/Procedural/Metacognitive) | Los nombres de los 6 procesos son de uso común. **Mejor lista de verbos abierta: Newton, Da Silva & Peters (2020), *Frontiers in Education* 5:107 — CC BY 4.0**, consensuada sobre **47 listas publicadas**, con lista de "verbos a evitar". ⚠️ No usar Wikipedia (omite la dimensión de conocimiento) ni citar páginas de editoriales privadas. |
| **Webb DOK** | 4 niveles | ⚠️ El monográfico de 1997 (https://files.eric.ed.gov/fulltext/ED414305.pdf) **no contiene los 4 niveles**. **Los nombres difieren por área curricular** (Science: Recall and Reproduction / Skills and Concepts / Strategic Thinking / Extended Thinking; Social Studies: Recall of Information / Basic Reasoning / Complex Reasoning / Extended Reasoning; Language Arts no tiene nombres). → **Anclar a `content_area` + número, nunca a un string global.** DOK ≠ Bloom: *"Verbs such as 'describe' and 'explain' could be classified at different DOK levels"*. |
| **Tomlinson (diferenciación)** | 4 elementos (content/process/product/learning_environment) + tríada readiness/interest/learning_profile | **ERIC ED443572 — dominio público explícito**, https://files.eric.ed.gov/fulltext/ED443572.pdf. **Nada machine-readable**: habría que modelarlo. |

**Modelo IEP de EE. UU. como referencia de esquema** (no aplicable en Chile, pero
es el contrato mejor documentado del mundo): el **ED Model IEP Form** es real —
https://sites.ed.gov/idea/files/modelform1_IEP.pdf — con **11 secciones** y sus
citas §300.320(a)(1)…(c); reglamento en
https://sites.ed.gov/idea/regs/b/d/300.320, equipo en §300.321, desarrollo en
§300.324. **Todo el 34 CFR §300 es dominio público** (17 U.S.C. §105).

⚠️ **IEP ≠ plan 504.** El §504 **no prescribe contenido ni formulario** (OCR:
*"generally will not evaluate the content of a Section 504 plan"*). **No
modelarlos como el mismo objeto**: el IEP es esquema fijo, el 504 es lista libre
de servicios. Aplicado a Chile: **el PACI se parece al IEP, no al 504.**

⚠️ **`differentiationcentral.com` está secuestrado y sirve spam de casino.**
**Nunca citarlo.** Otras URLs muertas verificadas: `c2f.vanderbilt.edu` (Bloom,
redirigido), `celt.iastate.edu/teaching/...` (404),
`www2.ed.gov/.../504faq.html` (404), `schema.org/AccessibilityFeature` (404),
`1edtech.org/standards/accessforall` (404), `w3.org/2021/a11y-discov-vocab/` (404).

**API no documentada de Ley Chile** (funcional, verificada):

```bash
curl -sS -A "Mozilla/5.0" \
  "https://servicios-leychile.bcn.cl/Navegar/get_norma_json?idNorma=1074511"
```

Devuelve `metadatos.titulo_norma`, `metadatos.organismos`,
`metadatos.tipos_numeros[].compuesto` (p. ej. `Decreto-83 EXENTO`),
`metadatos.fecha_publicacion` (`2015-02-05`) y `estructura`. Con esto tero puede
**citar la norma con identificador verificable** en lugar de texto libre. Al no
estar documentada, cualquier uso debe degradar bien si deja de responder.

---

## 4. Riesgos — qué NO conviene hacer

### 4.1 Licencias incompatibles con MIT

| Componente | Licencia | Por qué es un problema |
| --- | --- | --- |
| **H5P `h5p-php-library`** | **GPL-3.0** | Copiar cualquier parte obliga a relicenciar tero. H5P declara que usa MIT "donde puede", pero la librería PHP queda GPL por código de terceros (https://h5p.org/licensing). **Si algún día se exporta H5P, hacerlo por formato de archivo**, no por código. |
| **Moodle** | **GPL-3.0** (declarada; no verificada por fetch directo) | Misma razón. Además PHP. |
| **Open edX (`edx-platform`)** | **AGPL-3.0** (verificado) | Peor que GPL: la AGPL alcanza el uso en red. Ni copiar ni derivar. |
| **Canvas LMS** | **AGPL-3.0** (verificado) | Igual. |
| **CAST UDL Guidelines** | **Propietaria / sin CC** (verificado) | **No reproducir el texto de las 36 consideraciones** en un esquema del repo. Sólo identificadores + cita. |
| **CK-12 (parte del catálogo)** | Mezcla, incluye **CC BY-NC** | CC BY-NC **prohíbe uso comercial**. No empaquetar. |
| **schema.org** | **CC BY-SA 3.0** | Copyleft débil: un esquema derivado debe respetar la licencia. Usar los nombres de propiedades es uso normal; derivar un vocabulario propio, no. |
| **WCAG 2.2** | W3C Document License | **No permite derivados.** Citar los identificadores `SC x.y.z`, no reproducir el texto normativo. |
| **API de Ley Chile (BCN)** | **CC BY-NC-ND 4.0** (declarada en la propia spec OpenAPI) | **El riesgo legal más serio detectado en esta investigación.** Ver abajo. |
| **Currículum MINEDUC** | **Por ítem:** Dominio público, **CC BY-NC-SA**, **CC BY-NC-ND** o *Todos los derechos reservados* | 82 de 296 Programas de estudio son NC/ND. Ver abajo. |
| **`legibilidad` (PyPI)** | **GPL-3.0+ de facto** | **PyPI declara MIT, pero el sdist trae cabecera GPL y el repo es GPL-3.0.** Un `pip install` no avisa: hay que auditar. |
| **`language_tool_python`** | **GPL-3.0** | Usar LanguageTool como **servicio Java (LGPL-2.1)**. |
| **spaCy `es_core_news_sm/md/lg`** | **GPL-3.0 en los pesos** | El código de spaCy es MIT; **los modelos en español no**. No empaquetar ni autodescargar. |
| **`egtcpu/legibilidad`** | **AGPL-3.0** | Peor que GPL. |
| **Repos sin licencia** | **Sin licencia = no reusable** | `ECNU-ICALK/EduChat` (★969), `EduEval`, `OmniEduBench`, `ISKME/OER-Commons-API`, `khan-exercises`. La disponibilidad pública **no** es permiso. |

**Marcos que se pueden usar enteros, con su licencia:**

| Marco | Licencia | Cómo usarlo |
| --- | --- | --- |
| **CCSSO Accessibility Manual 2021** (Tools 1–11) | **CC BY 4.0** | ✅ **Reproducible con atribución.** Es la mejor fuente para convertir los apoyos en checklists dentro de un esquema de tero. |
| **Newton, Da Silva & Peters (2020)** — verbos de Bloom | **CC BY 4.0** | ✅ Lista de verbos consensuada (47 listas) y "verbos a evitar". |
| **ERIC ED443572** (Tomlinson) | **Dominio público** | ✅ Modelable sin fricción. |
| **ED Model IEP Form + 34 CFR §300** | **Dominio público** (17 U.S.C. §105) | ✅ Referencia de esquema de 11 secciones. |
| **Textos legales chilenos** (`bcn.cl`) y documentos MINEDUC (PIE/FUDEI) | Oficiales / sin restricción de autor | ✅ Citar y mapear. **Ojo:** eso **no** cubre los materiales curriculares, que se licencian por ítem. |
| **ASN Rubric Model** | **CC BY 4.0** | ✅ Esquema abierto de rúbrica. |
| **W3C a11y-discov-vocab 1.1** | W3C Community FSA | ✅ Listas cerradas para usar como `enum`. |
| ⛔ **CAST UDL**, ASCD, CCSSO 2005, NCEO, materiales de editoriales privadas | Restrictivas | **Sólo citar. No reproducir en un JSON Schema ni empaquetar en la UI.** |

#### El caso del currículum chileno — "Dominio público" NO es universal

**El hallazgo más importante de esta investigación para tero.** El JSON:API de
`curriculumnacional.cl` expone un campo **`field_licencia` por ítem**, y el
vocabulario tiene **8 valores**, incluidos **`CC BY-NC-SA`**, **`CC BY-NC-ND`** y
**`C - Copyright - Todos los derechos reservados`**. Censo real por etiqueta:

| Colección | Dominio público | CC BY-NC-SA | CC BY-NC-ND | Sin licencia |
| --- | --- | --- | --- | --- |
| Programas de Estudio (296) | 213 | 70 | 12 | 1 |
| Propuesta curricular (306) | — | **290** | — | — |
| Actualización curricular 2025-2026 (26) | — | **17** | — | — |
| Base curricular (15) | 11 | 1 | — | 3 |

**82 de 296 Programas de Estudio son NC y/o ND. Lo más nuevo es lo más
restringido.**

Consecuencias:

1. **No hardcodear "Dominio público".** Hay que leer `field_licencia` por ítem.
2. **No redistribuir un corpus empaquetado** de materiales curriculares.
3. **Los materiales ND (12 programas) bloquean obra derivada** — que es
   exactamente lo que tero hace cuando adapta. **No adaptar material ND.**
4. Los PDF **no llevan aviso de licencia interno**: la cita debe apuntar al
   **registro del sitio + fecha de consulta**, no al archivo.

**Y el caso de la API de Ley Chile (BCN).** La spec oficial declara **CC BY-NC-ND
4.0**, pero las condiciones de uso (`https://www.bcn.cl/leychile/assets/doc/condiciones-de-uso-api-v1.1.pdf`)
matizan con precisión jurídica: los **textos legales, reglamentarios,
administrativos y judiciales están fuera del ámbito del derecho de autor**
(art. 71 C, Ley 17.336), mientras que las **compilaciones y metadatos de BCN sí
son CC BY-NC-ND 4.0**, y el **uso de datos de la API para entrenar o ajustar
modelos de IA requiere autorización expresa de la BCN**.

**Ojo con la trampa lógica:** la doctrina de "los textos oficiales no tienen
copyright" **NO cubre los documentos curriculares de MINEDUC**, que se licencian
**por ítem** (tabla de arriba). Son dos regímenes distintos y es fácil
confundirlos.

**Regla para tero:**

- Citar el OA **por identificador canónico + URL** es uso informativo: **sí**.
- Empaquetar o adaptar el texto de un material **ND**: **no**.
- Usar la API de BCN para **entrenar o ajustar** cualquier cosa: **no** sin
  autorización escrita.
- **Si tero llegara a cobrar, toda cláusula NC es un bloqueo.**

#### El caso de la API de Ley Chile — leer antes de integrarla

La spec oficial lo declara sin ambigüedad
(https://www.bcn.cl/leychile/leychile-api-doc/assets/leychile-api-doc-v1.yaml):

```yaml
license:
  name: CC BY-NC-ND 4.0
  url: https://creativecommons.org/licenses/by-nc-nd/4.0/deed.es
```

**BY-NC-ND** significa: atribución, **No Comercial** y **Sin Derivados**. Las
condiciones de uso (https://www.bcn.cl/leychile/api/condiciones-de-uso) además
prohíben **extracción masiva**, **replicar Ley Chile**, **indexación masiva** y
**almacenamiento persistente**, y declaran que *"el entrenamiento o ajuste de
modelos de inteligencia artificial con datos obtenidos desde la API requiere
autorización expresa de la Biblioteca"*. La infracción se califica de
**gravísima**. Atribución obligatoria: *"Ley Chile - Biblioteca del Congreso
Nacional"* + fecha de obtención.

**Consecuencias para tero (MIT, y potencialmente comercial):**

1. **No cachear masivamente decretos** ni construir un corpus normativo local.
2. **No empaquetar el texto de la API** en el repo ni en `derivados/`.
3. **No usar la API como fuente del prompt** ni para entrenar/ajustar nada.
4. **Sí se puede** citar la norma por su **URL de `leychile.cl`** y su
   **identificador** (`idNorma`). Una cita con enlace es uso informativo.
5. Si se necesita el texto en un turno, hacer **fetch puntual**, no caché.
6. **Si tero llegara a cobrar, la cláusula NC es un bloqueo.** Es una razón más
   para no apoyar nada del producto en contenido de BCN.

**Nota sobre el endpoint histórico** `servicios-leychile.bcn.cl`: funciona sin
key hoy, pero **no está documentado y no tiene condiciones de uso publicadas**.
Que no haya licencia explícita **no equivale a permiso** — el contenido sigue
siendo de BCN. Tratarlo como conveniencia de verificación, nunca como fuente
de datos del producto.

**Regla práctica:** tero es MIT. Nada de GPL, AGPL ni CC BY-NC entra como
código, texto normativo reproducido o asset. Los **formatos** (QTI, CASE, H5P
como archivo, EPUB) y los **vocabularios cerrados** (a11y-discov-vocab) sí son
implementables **desde su especificación**, que es distinto de copiar una
implementación.

### 4.2 Complejidad fuera de alcance

1. **LMS, LTI, SSO, rostering.** Es la superficie donde compiten los productos
   comerciales (Canvas, Classroom, Schoology, Clever, ClassLink), y es
   exactamente lo que una TUI MIT no necesita. **No perseguir esta tabla.**
   Teachmate —420.000 docentes— no tiene LMS nativo ni API pública: la adopción
   individual no lo exige.
2. **Editor de material embebido.** Prohibido por `AGENTS.md` (TipTap). La
   edición se hace **por conversación**, con `cambios` etiquetados por sección.
3. **Buscador de contenido web / RAG sobre internet abierto.** tero lee **sólo**
   la carpeta de trabajo. La evolución 2026 de la categoría es *grounding en el
   currículo adoptado*, no en internet: tero ya está en el lado correcto y no
   debe moverse.
4. **Catálogo curricular completo.** El catálogo host-side cubre 4°–6° básico en
   tres asignaturas y lo **declara**. Ampliarlo sin fuente oficial verificable
   convertiría una paráfrasis honesta en una afirmación falsa.
5. **Generación de documentos de alto riesgo.** IEP equivalente, planes de
   conducta, informes de progreso, boletines. Common Sense recomienda evitarlos y
   tres de cuatro plataformas evaluadas los ofrecen igual. tero puede **adaptar
   material de clase**; no debe producir instrumentos con valor normativo.
6. **Voz, avatar, antropomorfismo.** La evidencia (Viberg et al., Lucas et al.,
   Ayanwale et al.) muestra que **la falta de rasgos humanos no afecta la
   confianza**, y que invertir en "humanizar" es mal uso de recursos frente a
   invertir en **explicabilidad del dominio**.

### 4.3 Dependencias cloud y de red

1. **`servicios-leychile.bcn.cl` no está documentado.** Es un hallazgo valioso
   pero frágil: puede cambiar sin aviso. Usarlo para **verificar** una cita en
   tiempo de construcción del catálogo, no para resolver en tiempo de ejecución
   del turno del docente.
2. **`curriculumnacional.cl` no respondió** desde esta red. Cualquier promesa de
   "descarga el currículum oficial" debe probarse antes de escribirla.
3. **La API de UNICEF/UNESCO y `unesdoc.unesco.org`** devolvieron 403/timeout.
   No prometer integración con ellas.
4. **La trampa de la categoría es el costo de inferencia.** Los free tiers se
   limitan justo donde nace el interés (Curipod 2 sesiones/semana, SchoolAI 5
   sesiones **al año**). tero no tiene ese problema porque el docente trae sus
   fuentes y el turno es corto — pero **no agregar llamadas al modelo que no
   paguen su costo**: toda verificación aritmética (P0.4) va en el host.

### 4.4 Riesgos de producto que la evidencia señala

1. **"Outsourced thinking".** Common Sense lo lista como falla de la categoría:
   *"many platforms make it too easy to push AI-generated material directly to
   classrooms without review"*, y recomienda considerar la fricción como
   beneficiosa. **Riesgo de tero:** que la aprobación en lenguaje natural sea
   *demasiado* fácil ("dale") y se convierta en un sello de goma. Mitigación:
   P0.6.
2. **Automatización complaciente.** Jiang et al. (2026): los docentes saben que
   deben revisar y aun así adoptan por conveniencia. Un preview largo **no**
   garantiza revisión. Mitigación: subir `warnings` y el conteo de evidencia
   verificada por encima de la vista previa.
3. **Explicaciones que anclan.** Ghai et al. (CSCW 2020): las explicaciones
   calibran **y** anclan, y aumentan la carga de trabajo. Swamy et al. (LAK 2023):
   distintos explicadores **se contradicen** entre sí. Mitigación: la explicación
   es **opcional y progresiva**, nunca un veredicto.
4. **La confianza no se maximiza, se calibra.** Wong, Bulathwela y Cukurova
   (2025) concluyen que la transparencia debe ayudar al docente a **no
   sobre-confiar**. Un agente que dice "esto es excelente" es un mal agente.
5. **Nivelación que empobrece.** Common Sense: *"if you're giving a struggling
   reader access to easier text for an entire school year, that reader isn't
   going to be making progress toward grade-level text."* Microsoft es el único
   que declara **preservar el vocabulario de dominio** al bajar el nivel. Si tero
   adapta nivel (P1.1), ese flag no es opcional.
6. **Sesgo difícil de detectar.** El experimento con nombres "white-coded" vs
   "Black-coded" produjo estrategias sistemáticamente distintas en Gemini y
   MagicSchool. tero no tiene forma de auditar esto hoy; conviene **no afirmar**
   que el material es imparcial.

### 4.5 Un patrón de interacción que conviene adoptar (no evitar)

La investigación de patrones HITL encontró una división útil: las herramientas de
**código** aplican el cambio directamente y ofrecen *deshacer* + checkpoints; las
herramientas de **escritura** **nunca sobrescriben sin una acción explícita de
conservación** (*Keep it / Replace / Accept*). **tero produce prosa: pertenece a
la familia escritura**, y su contrato de aprobación ya está del lado correcto.

El equivalente documentado más cercano a "propongo y tú apruebas" es **Notion
Agent** (release 28-08-2026), que pasó a *"proponer cambios en lugar de hacerlos
directamente… avanza de arriba a abajo para aprobar cada uno"*. **Grammarly**
documenta además una métrica relevante: su **panel de previsualización subió la
activación más de 10 %**, y el *undo* se añadió como **requisito de diseño**, no
como extra.

**Lección para tero:** la aprobación **secuencial por ítem** (como Notion Agent)
es el patrón con precedente de producto para revisar cambios múltiples. Si en
`adaptar` la propuesta acumula varios cambios, ofrecer aprobación **cambio por
cambio** es más barato cognitivamente que aprobar el bloque entero.

**Correcciones de URL útiles para futuras investigaciones:** `docs.cursor.com` →
`cursor.com/docs`; Claude Code ahora en `code.claude.com/docs/en/*.md`; VS Code
movió la revisión de ediciones a `/docs/agents/run/review-code-edits`.
**GitHub Copilot Workspace** (dominio 404, proyecto marcado *"Completed"*, último
changelog feb-2025) está **probablemente retirado**: no citarlo como referencia
vigente.

### 4.6 Integrar estándares 1EdTech sin violar su licencia

La licencia viva es https://www.1edtech.org/standards/specification-license
(**`imsglobal.org/license` y `1edtech.org/license` dan 404**). Concede una
licencia *"worldwide, perpetual, royalty-free, nontransferable, nonexclusive,
nonsublicenseable"* para **implementar productos**, con atribución, y en su §4
**"No right to create modifications or derivatives"**. El documento
*how-to-use-1edtech-documents* §10 dice que *"cualquier individuo u organización
puede desarrollar productos que implementen las especificaciones"*; §11 se
reservan aprobar **herramientas de conformidad**.

- ✅ **Implementar una especificación es libre** (QTI, CASE, OB, CLR, OneRoster).
- ❌ **No copiar la prosa** de las specs ni publicar una suite de certificación.
- ⚠️ **Marcas registradas:** CASE®, QTI®, Caliper®, OneRoster®, LTI®, CC®, AfA®.
- **CASE Network** (https://casenetwork.1edtech.org/, UI *"Standards Satchel"*)
  existe, pero su API `GET /ims/case/v1p0/CFDocuments` responde **403 "Invalid
  credentials provided"**: **no hay registro CASE abierto sin credenciales**, y
  la certificación es de membresía pagada.
- **AccessForAll 3.0 no tiene URL propia**: sus XSD viajan dentro de QTI
  (`imsqtiv3p0_afa3p0pnp_v1p0.xsd`). **No existe una spec UDL de 1EdTech.**
- **`learningregistry.org` está muerto y el dominio fue reciclado como granja
  SEO**: no citarlo ni scrapearlo. **`achievementstandards.org` no responde**:
  usar https://asn.desire2learn.com/ (D2L opera el ASN desde feb-2014; los datos
  del RDF declaran **CC BY 4.0**, titular University of Washington).
- **Edu-API 1.0 está detrás de login** (*"Sign in to view this content"*,
  "Candidate Final"): usar **OneRoster 1.2**. **Common Cartridge 1.4 da 403 sólo
  miembros**; Thin CC es público (2015) pero su aviso de licencia apunta a un
  **404**.
- **schema.org:** vocabulario, docs y ejemplos son **CC BY-SA 3.0**
  (https://schema.org/docs/terms.html), el código es **Apache-2.0**. **Emitir
  URIs es libre; vendorizar las definiciones activa ShareAlike.**

---

## 5. Las tres cosas que hacer antes del cierre

Ver justificación completa en P0.
1. **P0.1 + P0.6 — Hacer la vista previa barata y la revisión más fácil que
   aceptar a ciegas.** Orden de render en la TUI: `accion + tipo + titulo` →
   `resumen` → `cambios` (si `editar`/`adaptar`) → `warnings` → conteo de
   evidencias `✓`/`?` → `vista_previa`. Es donde la categoría entera falla y no
   requiere tocar ningún contrato.
2. **P0.3 — `notas_nee` con la taxonomía del Decreto 83/2015.** Convierte
   "adaptado a NEE" de prosa en datos defendibles: `tipo`
   (`acceso` | `objetivos_aprendizaje`), `criterio` (los **4 + 5 criterios
   exactos** del decreto), `descripcion` de redacción propia y `justificacion`
   obligatoria en `eliminacion_aprendizajes`. Más el `warning` no bloqueante
   `nee_sin_apoyos_de_acceso` cuando se ajustan objetivos sin ningún apoyo de
   acceso — literalmente la regla de oro del decreto.
3. **P0.2 — Advertencia no bloqueante de alto riesgo en `adaptar`.** Un `code`
   nuevo en `warnings` que diga que son apoyos para la clase y **no** una
   adecuación curricular formal ni un PACI. Cuesta casi nada y evita el error más
   caro que tero puede cometer: un PACI es un **documento oficial ante el
   MINEDUC**, con responsables legales y efectos en la promoción.

**Lo que NO hacer en 3 días:** integración con la API de BCN (licencia
CC BY-NC-ND + prohibición de uso para IA), empaquetar materiales curriculares
(82/296 programas son NC/ND), QTI, o cualquier cosa que toque el camino offline.
Las tres acciones de arriba son **contrato y render**, no integraciones nuevas —
que es exactamente donde está el valor según toda la evidencia recogida.

---

## Anexo — trazabilidad y límites

**Informes crudos que respaldan este documento** (fuera del repo, en
`/home/ubuntu/investigacion-tero-raw/`, porque un `git clean` concurrente los
borró dos veces):

| Archivo | Contenido |
| --- | --- |
| `asistentes-ia-docentes-2026.md` | 11 fichas de producto, 9 bloques de encuestas, 15 patrones, tabla de "no verificado". |
| `nee/marcos-verificados.md` | UDL 3.0, Decreto 83/2015, **CCSSO Accessibility Manual**, accesibilidad, normativa chilena, Bloom/DOK/Tomlinson, legibilidad española (1.431 líneas). |
| `nee/a11y-discov-vocab-1.1-enums.json` | Las 6 listas de términos del vocabulario W3C, listas para `enum`. |
| `hitl/confianza-docente-ia-ui.md` | Evidencia sobre confianza docente y rasgos de UI, con UNESCO. |
| `oss/licencias-reutilizacion-2026.md` | Semáforo de licencias A/B/C/D con la URL de evidencia de cada afirmación. |
| `oss/edtech-standards-licenses-2026.md` | Estándares 1EdTech, CASE, QTI, Caliper, OB, CLR. |
| `leychile/*.json` | Textos legales crudos (Decretos 83, 170, Leyes 20.422 y 21.545) y los scripts de extracción. |

**Nivel de verificación de las citas.** Las URLs de producto, estándar,
licencia y normativa chilena de este documento se abrieron y su código HTTP se
observó. Los **identificadores arXiv** del informe de confianza se verificaron uno
a uno (título contrastado), y **los DOI de revista se resolvieron contra la API
de Crossref** (`https://api.crossref.org/works/<doi>`) — se confirmó el título de
los diez DOI principales, incluidos `10.1007/s40593-025-00486-6`,
`10.1111/bjet.13466`, `10.1145/3581641.3584046`, `10.1111/bjet.13232`,
`10.1103/hm13-jv98`, `10.1007/s40299-025-01068-9`, `10.1111/ejed.70795`,
`10.1111/flan.70042`, `10.1109/iceit68991.2026.11521608` y
`10.1145/3748522.3779879`. **Cautela restante:** que un DOI resuelva prueba que el
paper existe **y** que el título corresponde; **no** prueba que el resumen que
este documento le atribuye sea exacto. Antes de citar un hallazgo concreto en el
post del hackathon, releer el abstract.

**Los dos hallazgos negativos más útiles**, para no repetir el trabajo:
(1) **no existe** un registro CASE abierto sin credenciales, ni currículum
chileno publicado en CASE/LOM/Dublin Core; (2) **no existe** una versión
machine-readable oficial de las Pautas UDL, ni en CAST ni en 1EdTech; (3) **no
existe** un mapeo publicado entre la taxonomía chilena (Decreto 83) y la
estadounidense (accommodation/modification) — la analogía es nuestra.

**Advertencia final sobre dos fuentes envenenadas**, por si alguien repite la
búsqueda: `differentiationcentral.com` (Tomlinson) está **secuestrado y sirve
spam de casino**, y `learningregistry.org` fue reciclado como **granja SEO**. El
buscador de `agenciaeducacion.cl` devolvió **spam inyectado** en una consulta.
No citar ninguno de los tres.

