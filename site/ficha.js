/* OpenTUI session in one window. Warnings never block s.
   Consultation timings are compressed; corrida real is the measured run.
   Photocopied pages appear only after s / b (#archivo). */
(function () {
  "use strict";

  const WARNINGS_BLOCK_S = false;
  const $ = (id) => document.getElementById(id);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const scale = reduceMotion ? 0.05 : 1;
  const Tui = window.teroTui;
  const GRID_COLS = 140;
  const GRID_ROWS = 40;
  const FRAME_NAMES = [
    "home",
    "help",
    "encargo",
    "plan",
    "puerta",
    "leyendo-1",
    "leyendo-2",
    "leyendo-3",
    "leyendo-4",
    "plan-1",
    "plan-2",
    "plan-3",
    "plan-4",
    "puerta-1",
    "puerta-2",
    "puerta-3",
    "puerta-4",
  ];
  const frames = Object.fromEntries(FRAME_NAMES.map((name) => [name, null]));

  function loadFrames() {
    return Promise.all(
      FRAME_NAMES.map((name) =>
        fetch(`./assets/tui/frames/${name}.json?v=ave`)
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            frames[name] = data;
          })
          .catch(() => {}),
      ),
    );
  }

  const state = {
    phase: "home",
    view: "home",
    rumbo: null,
    filename: null,
    warnings: [],
    token: 0,
    pages: [],
    page: 0,
    clockMs: 0,
    clockTimer: null,
    startedAt: 0,
    help: false,
    spinner: 0,
    spinnerTimer: null,
    promptValue: "",
    stamp: "REVISAR",
    cols: 120,
    rows: 36,
    cellW: 8,
    cellH: 15.6,
    fontSize: 13,
    hits: [],
    promptBox: null,
    model: null,
  };

  const rumbos = {
    1: {
      chips: ["planificar", "4° básico", "Lenguaje", "cuento", "OA 4", "45 min", "planificacion"],
      tipo: "planificacion",
      filename: "planificacion-condor-y-huemul.pdf",
      fuentes: ["cuento-el-condor-y-el-huemul.md", "bases-oa-lenguaje-4b.md", "pauta-lectura.md"],
      corrida: "bakeoff LaTeX · GLM 4.7 Flash · planificación 4° básico",
      elapsed: null,
      pages: [
        "./assets/hojas/plan/p1.png",
        "./assets/hojas/plan/p2.png",
        "./assets/hojas/plan/p3.png",
      ],
      steps: [
        { tool: "list_sources", ms: 700 },
        { tool: "list_oa", ms: 550 },
        { tool: "read_source", ms: 800, detail: "cuento-el-condor-y-el-huemul.md" },
        { tool: "read_source", ms: 650, detail: "bases-oa-lenguaje-4b.md" },
        { tool: "propose_plan", ms: 2400, plan: true },
        { tool: "cite_evidence", ms: 500 },
        { tool: "draft_artifact", ms: 3200, draft: true },
      ],
      planTitle: "planificación · cuento",
      plan:
        "planificación · cuento\nPlan de trabajo · 1 entregable · Listo\n\nExtraer información explícita e implícita del cuento «El cóndor y el huemul», con cita.\n\nRESULTADO PREVISTO\n  · Planificación\n\nCÓMO LO ABORDARÉ\n  1. Inicio — pregunta ancla\n  2. Desarrollo — lectura guiada + parejas\n  3. Cierre — ticket de salida\n\nSUPUESTOS  (e)\n  · 45 min, fuentes de la carpeta",
      draft:
        "# Planificación — El cóndor y el huemul\n\ntero · planificación · el docente decide\n\n## Objetivo\nExtraer información explícita e implícita del cuento «El cóndor y el huemul», distinguiendo lo que el texto dice de lo que el lector infiere con evidencia (LEN-4B-OA04).\n\n## Inicio\n- ¿Qué significa que un texto nos diga algo y que nosotros podamos agregar algo más?\n- Ancla: la niña anota dos cosas en el cuaderno de tapa azul.\n\n## Desarrollo\n- Lectura en voz alta del cuento de la carpeta.\n- Parejas: tres ítems (explícito / implícito / cita).\n\n## Cierre\nTicket: una oración con evidencia. El JSON del modelo no se imprime crudo.",
      evidence:
        "▸ 1/2  ✓ en archivo\n  fuentes/cuento-el-condor-y-el-huemul.md\n  desarrollo\n\n  2/2  ?  fuentes/bases-oa-lenguaje-4b.md\n    OA 4",
      warnings: [
        {
          code: "unverified_citation",
          message:
            "Hay parafraseo del cuento (fuentes/cuento-el-condor-y-el-huemul.md). No lo trates como cita literal.",
        },
      ],
    },
    2: {
      chips: ["crear", "1° medio", "Matemática", "sistemas 2×2", "90 min", "guia"],
      tipo: "guia",
      filename: "guia-sistemas-ecuaciones-lineales-2x2.pdf",
      fuentes: [
        "vocabulario-algebra.md",
        "ejemplos-sistemas-resueltos.md",
        "bases-oa-matematica-1m.md",
      ],
      corrida: "MiniMax M2.5 · guía 1° medio · 94.9 s",
      elapsed: 94.9,
      tools: 13,
      pages: [
        "./assets/hojas/guia-sistemas/p1.png",
        "./assets/hojas/guia-sistemas/p2.png",
        "./assets/hojas/guia-sistemas/p3.png",
      ],
      steps: [
        { tool: "list_sources", ms: 720 },
        { tool: "list_oa", ms: 580 },
        { tool: "read_source", ms: 820, detail: "vocabulario-algebra.md" },
        { tool: "read_source", ms: 780, detail: "ejemplos-sistemas-resueltos.md" },
        { tool: "read_source", ms: 700, detail: "bases-oa-matematica-1m.md" },
        { tool: "propose_plan", ms: 2600, plan: true },
        { tool: "cite_evidence", ms: 520 },
        { tool: "draft_artifact", ms: 4200, draft: true },
      ],
      planTitle: "guía · sistemas",
      plan:
        "guía · sistemas de ecuaciones lineales 2×2\nPlan de trabajo · 1 entregable · Listo\n\nIntroducir el sistema 2×2 como dos rectas, un punto. Sustitución + verificación.\n\nRESULTADO PREVISTO\n  · Guía de autoaprendizaje\n\nCÓMO LO ABORDARÉ\n  1. Selección múltiple\n  2. Verdadero o falso\n  3. Desarrollo y ruedas\n\nSUPUESTOS  (e)\n  · 90 min, fuentes de la carpeta",
      draft:
        "# Guía — sistemas de ecuaciones lineales 2×2\n\ntero · guía · 1° medio · el docente decide\n\n## Propósito\nReconocer un sistema 2×2 como dos condiciones a la vez. La solución es el punto donde se cortan dos rectas.\n\n## I. Selección múltiple\n1. ¿Qué es un sistema 2×2?\n   A) Una ecuación con dos incógnitas\n   B) Dos ecuaciones lineales con las mismas dos incógnitas\n   C) Dos ecuaciones con cuatro incógnitas\n   D) Una ecuación de segundo grado\n2. ¿Cuál par es solución de x + y = 5, x − y = 1?\n   A) (3, 2)  B) (2, 3)  C) (4, 1)  D) (5, 0)\n\n## II. Verdadero o falso\nEl par (2, 4) verifica x + y = 6. _____ · Las rectas x = 2 e y = 3 se cortan en (2, 3). _____\n\n## III. Desarrollo\nResuelve por sustitución: 2x + y = 8, x − y = 1.\n\nAl pulsar s se muestran las tres páginas LaTeX (tablas + gráficos, sin pipes ni fences).",
      evidence:
        "▸ 1/2  ? parafraseo\n  fuentes/vocabulario-algebra.md\n  Vocabulario\n  “sistema 2×2: dos ecuaciones lineales…”\n\n  2/2  ?  fuentes/ejemplos-sistemas-resueltos.md\n    Ejemplo A",
      warnings: [
        {
          code: "unverified_citation",
          message:
            "2 cita(s) no aparecen textuales (fuentes/vocabulario-algebra.md, ejemplos-sistemas-resueltos.md). Puede ser parafraseo; no las trates como cita literal.",
        },
        {
          code: "missing_structure",
          message: "Faltan apartados esperados para guía: instrucciones. El plan no se pisa: tú decides s o c.",
        },
      ],
    },
    3: {
      chips: ["evaluar", "1° medio", "Matemática", "sistemas 2×2", "45 min", "evaluacion"],
      tipo: "evaluacion",
      filename: "evaluacion-sistemas-ecuaciones-2x2.pdf",
      fuentes: ["vocabulario-algebra.md", "ejemplos-sistemas-resueltos.md", "bases-oa-matematica-1m.md"],
      corrida: "MiniMax M2.5 · loop09 · 92.5 s · 39 tools",
      elapsed: 92.5,
      tools: 39,
      pages: [
        "./assets/hojas/eval-sistemas/p1.png",
        "./assets/hojas/eval-sistemas/p2.png",
        "./assets/hojas/eval-sistemas/p3.png",
      ],
      steps: [
        { tool: "list_sources", ms: 680 },
        { tool: "list_oa", ms: 540 },
        { tool: "read_source", ms: 760, detail: "vocabulario-algebra.md" },
        { tool: "read_source", ms: 740, detail: "ejemplos-sistemas-resueltos.md" },
        { tool: "propose_plan", ms: 2300, plan: true },
        { tool: "cite_evidence", ms: 480 },
        { tool: "draft_artifact", ms: 4000, draft: true },
      ],
      planTitle: "evaluación · sistemas",
      plan:
        "evaluación · sistemas 2×2\nPlan de trabajo · 1 entregable · Listo\n\nEvaluación corta 50 pts: SM, V/F y desarrollo (sustitución y reducción). Sin calculadora.\n\nRESULTADO PREVISTO\n  · Evaluación\n\nCÓMO LO ABORDARÉ\n  1. Selección múltiple\n  2. Verdadero o falso\n  3. Desarrollo\n\nSUPUESTOS  (e)\n  · 45 min",
      draft:
        "# Evaluación corta: sistemas de ecuaciones lineales 2×2\n\ntero · prueba / evaluación · el docente decide · 50 puntos\n\n## Ítems de selección múltiple\n1. ¿Qué es un sistema 2×2?\n   B) Dos ecuaciones lineales con dos incógnitas que deben cumplirse a la vez\n2. Al resolver x + y = 10, x − y = 4, ¿cuál es la solución?\n   A) (7, 3)\n\n## Verdadero o falso\n(2, 5) es solución de x + y = 7 y 2x − y = −1. _____ · Un sistema lineal siempre tiene exactamente una solución. _____\n\n## Desarrollo\nSustitución: 2x + y = 12, x − y = 3. Muestra pasos y verifica en ambas.\n\nAl pulsar s se muestran las páginas de la corrida loop09 (MiniMax, 92.5 s).",
      evidence:
        "▸ 1/1  ? parafraseo\n  fuentes/vocabulario-algebra.md\n  Vocabulario",
      warnings: [
        {
          code: "unverified_citation",
          message:
            "1 cita(s) no aparecen textuales (fuentes/vocabulario-algebra.md). Puede ser parafraseo; no las trates como cita literal.",
        },
      ],
    },
    4: {
      chips: ["adaptar", "4° básico", "Lenguaje", "cuento", "OA 4", "45 min", "evaluacion"],
      tipo: "evaluacion",
      filename: "evaluacion-el-condor-y-el-huemul.pdf",
      fuentes: ["cuento-el-condor-y-el-huemul.md", "bases-oa-lenguaje-4b.md"],
      corrida: "GLM 4.7 Flash · loop10 · 29.1 s · 33 tools",
      elapsed: 29.1,
      tools: 33,
      pages: [
        "./assets/hojas/eval-cuento/p1.png",
        "./assets/hojas/eval-cuento/p2.png",
        "./assets/hojas/eval-cuento/p3.png",
      ],
      steps: [
        { tool: "list_sources", ms: 640 },
        { tool: "read_source", ms: 820, detail: "cuento-el-condor-y-el-huemul.md" },
        { tool: "read_source", ms: 600, detail: "bases-oa-lenguaje-4b.md" },
        { tool: "propose_plan", ms: 2000, plan: true },
        { tool: "cite_evidence", ms: 450 },
        { tool: "draft_artifact", ms: 2800, draft: true },
      ],
      planTitle: "evaluación · cuento",
      plan:
        "evaluación · El cóndor y el huemul\nPlan de trabajo · 1 entregable · Listo\n\nPrueba corta 10 pts: SM 1–4, V/F 5–6, desarrollo con cita (ítem 7). Misma carpeta del rumbo 1, otro tipo.\n\nRESULTADO PREVISTO\n  · Evaluación\n\nCÓMO LO ABORDARÉ\n  1. Selección múltiple\n  2. Verdadero o falso\n  3. Desarrollo con cita\n\nSUPUESTOS  (e)\n  · 45 min",
      draft:
        "# Prueba corta — El cóndor y el huemul\n\ntero · evaluación · 4° básico · LEN-4B-OA04 · 10 puntos\n\nLee el cuento de la carpeta. Responde en silencio. Misma carpeta que el rumbo 1; otro tipo de artefacto.\n\n## Selección múltiple\n1. ¿Quién observa el mar desde la cornisa?\n   B) El cóndor\n2. ¿Qué le pregunta el huemul al cóndor?\n   A) Por qué el valle se acaba\n\n## Verdadero o falso\nEl cóndor responde al huemul sobre la causa del agua que se fue. _____\n\n## Desarrollo\nEl cóndor afirma: «Yo veo el mar desde aquí». Explica, infiere y cita el cuento.\n\nAl pulsar s se muestran las páginas loop10 (GLM, 29.1 s).",
      evidence:
        "▸ 1/2  ✓ en archivo\n  fuentes/cuento-el-condor-y-el-huemul.md\n\n  2/2  ?  fuentes/bases-oa-lenguaje-4b.md",
      warnings: [
        {
          code: "thin_evidence",
          message: "Menos de dos fuentes citadas. El panel de evidencia quedará pobre.",
        },
        {
          code: "unverified_citation",
          message: "La cita del ítem de desarrollo es parafraseo. Marcada ?, no ✓.",
        },
      ],
    },
  };

  const TOOL_LABEL = {
    list_sources: "fuentes",
    list_oa: "OA lista",
    read_source: "leer",
    propose_plan: "plan",
    cite_evidence: "cita",
    draft_artifact: "borrador",
  };

  const HELP = `tero — inicio

Rumbos
  1 Planificar   2 Crear   3 Evaluar   4 Adaptar

Escribe abajo: «Pregunta, explora o crea…»
Chips tras rumbo o encargo. Catálogo OA Chile (host).

El tero avisa. Tú decides. Vanellus chilensis · queltehue.
tero-offline (Strands Model scripted). AgentCore no es el producto.
Default README: amazon.nova-lite-v1:0.
python -m tero demo --offline --yes

? cierra · 1–4 rumbo · s / n / b / c en la puerta`;

  function canAccept(_warnings) {
    return true;
  }

  function looksPhatic(text) {
    const blob = (text || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/\p{M}/gu, "")
      .replace(/[^\p{L}\p{N} ]+/gu, " ")
      .replace(/\s+/g, " ")
      .trim();
    if (!blob) return true;
    const exact = new Set(["hola", "holi", "hello", "hi", "hey", "buenas", "ok", "ya", "gracias"]);
    return exact.has(blob);
  }

  function sessionListing(rumbo, extra) {
    const src = (rumbo && rumbo.fuentes) || [];
    const lines = ["fuentes/"];
    for (const name of src) lines.push(`  ${name}`);
    lines.push("", "derivados/");
    const der = $("derivados").querySelector("[data-file]");
    lines.push(der ? `  ${der.textContent}` : "  (vacío hasta que pulses s)");
    lines.push("", "borradores/");
    const bor = $("borradores").querySelector("[data-file]");
    lines.push(bor ? `  ${bor.textContent}` : "  (vacío hasta que pulses b)");
    if (extra) lines.push("", extra);
    return lines.join("\n");
  }

  function warnText(warnings) {
    if (!warnings || !warnings.length) return "sin avisos";
    return warnings.map((item) => `! ${item.message}`).join("\n");
  }

  function measure() {
    const fitted = Tui.fitHost($("tui-host"), $("tui-grid"), GRID_COLS, GRID_ROWS);
    state.cellW = fitted.cellW;
    state.cellH = fitted.cellH;
    state.fontSize = fitted.fontSize;
    state.cols = GRID_COLS;
    state.rows = GRID_ROWS;
  }

  function frameForPhase() {
    if (state.help) return frames.help;
    if (state.phase === "home") return frames.home;
    const rumbo = state.rumbo || "1";
    if (state.phase === "esperando_plan" || state.phase === "plan") {
      return frames[`plan-${rumbo}`] || frames.plan;
    }
    if (state.phase === "esperando_criterio" || state.phase === "listo") {
      return frames[`puerta-${rumbo}`] || frames.puerta;
    }
    return frames[`leyendo-${rumbo}`] || frames.encargo;
  }

  function syncPromptOverlay() {
    const input = $("prompt");
    const typing = Boolean(input.value);
    input.classList.toggle("is-typing", typing);
    input.placeholder = typing ? "Pregunta, explora o crea…" : "";
    input.style.background = typing ? Tui.theme.inputBg : "transparent";
  }

  function applyPainted(painted, frameName, view) {
    state.cellW = painted.cellW || state.cellW;
    state.cellH = painted.cellH || state.cellH;
    state.fontSize = painted.fontSize || state.fontSize;
    state.cols = GRID_COLS;
    state.rows = GRID_ROWS;
    state.hits = painted.hits;
    state.promptBox = painted.prompt;
    placePrompt(painted.prompt);
    document.body.dataset.view = view;
    document.body.dataset.frame = frameName || "live";
    $("window-path").textContent = "~/tero";
    syncPromptOverlay();
    $("prompt").readOnly =
      state.phase === "esperando_criterio" ||
      state.phase === "esperando_plan" ||
      state.phase === "listo";
    const host = $("tui-host");
    host.style.setProperty("--cell-w", `${state.cellW}px`);
    host.style.setProperty("--cell-h", `${state.cellH}px`);
  }

  function paintLive(captured) {
    measure();
    const model = currentModel();
    model.cols = GRID_COLS;
    model.rows = GRID_ROWS;
    state.model = model;
    const shot = $("tui-shot");
    shot.hidden = true;
    const canvas = $("tui-canvas");
    if (canvas) canvas.hidden = true;
    $("tui-grid").classList.remove("is-shot");
    const painted = captured
      ? Tui.paintFrame($("tui-grid"), captured)
      : Tui.paint($("tui-grid"), model);
    applyPainted(
      { ...painted, cellW: state.cellW, cellH: state.cellH, fontSize: state.fontSize },
      captured && captured.name ? captured.name : "live",
      model.view === "home" ? "home" : "session",
    );
  }

  function paint() {
    const captured = frameForPhase();
    const host = $("tui-host");
    const grid = $("tui-grid");
    const shot = $("tui-shot");
    const stage = $("tui-stage");
    if (captured && Tui.paintShot) {
      const painted = Tui.paintShot(host, stage, shot, grid, captured);
      if (painted) {
        applyPainted(
          painted,
          captured.name,
          state.phase === "home" && !state.help ? "home" : "session",
        );
        return;
      }
      return;
    }
    paintLive(captured);
  }

  function placePrompt(box) {
    const input = $("prompt");
    const host = $("tui-host").getBoundingClientRect();
    const stage = ($("tui-stage") || $("tui-grid")).getBoundingClientRect();
    input.style.left = `${stage.left - host.left + box.x * state.cellW}px`;
    input.style.top = `${stage.top - host.top + box.y * state.cellH}px`;
    input.style.width = `${box.w * state.cellW}px`;
    input.style.height = `${state.cellH}px`;
    input.style.fontSize = `${state.fontSize || 13}px`;
    input.style.lineHeight = `${state.cellH}px`;
  }

  function currentModel() {
    const rumbo = state.rumbo ? rumbos[state.rumbo] : null;
    const clock = $("reloj").textContent;
    let header = "offline · inicio";
    let footer = "elige rumbo o escribe     1–4 rumbo  Enter  ?  q";
    let promptTitle = "pregunta";
    let placeholder = "Pregunta, explora o crea…";
    let view = state.view;
    let proposal = "";
    let activity = "en espera";
    let evidence = "Citas al redactar.\n[ ] recorre · ✓ archivo · ? parafraseo";
    let plan = "";
    let gate = "";
    let gateTitle = " plan ";
    let session = "Sin turnos aún.\n\nHistorial:\nrumbo → plan → borrador → criterio.";

    if (state.phase === "home") {
      view = "home";
    } else if (state.phase === "esperando_plan" || state.phase === "plan") {
      view = "plan";
      header = `offline · plan · ${rumbo ? rumbo.fuentes.length : 0} fuentes`;
      promptTitle = "encargo";
      placeholder = "teclas arriba · /objetivo /oa";
      footer = "plan listo";
      plan = rumbo ? rumbo.plan.split("\n").slice(1).join("\n").replace(/^\n/, "") : "";
      gate = "[a] aprobar   [e] supuesto   [x] cancelar";
      session = sessionListing(rumbo);
      activity = `${Tui.spinner(state.spinner)} plan`;
      proposal = rumbo ? rumbo.plan : "";
    } else if (state.phase === "esperando_criterio") {
      view = "puerta";
      header = `offline · puerta · ${rumbo ? rumbo.fuentes.length : 0} fuentes`;
      promptTitle = "encargo";
      placeholder = "teclas arriba · o crítica con c";
      footer = "tu turno";
      plan = rumbo ? rumbo.plan.split("\n").slice(1).join("\n").replace(/^\n/, "") : "";
      gate = `[s] sí→derivados/  [n] no  [b] borrador  [c] corregir   evid 1/2`;
      gateTitle = " puerta ";
      proposal = rumbo ? rumbo.draft : "";
      evidence = rumbo ? rumbo.evidence : evidence;
      session = sessionListing(rumbo, `reloj ${clock}`);
      activity = "1 activity start por tool · espera s/n/b/c";
    } else if (state.phase === "listo") {
      view = "puerta";
      header = `offline · listo · ${rumbo ? rumbo.fuentes.length : 0} fuentes`;
      promptTitle = "encargo";
      placeholder = "1–4 otro rumbo · o escribe";
      footer = state.stamp === "ACEPTADO" ? "s → derivados/" : state.stamp === "BORRADOR" ? "b → borradores/" : "listo";
      plan = rumbo ? rumbo.plan.split("\n").slice(1, 5).join("\n") : "";
      gate = "";
      proposal = rumbo ? rumbo.draft : "";
      evidence = rumbo ? rumbo.evidence : evidence;
      session = sessionListing(rumbo);
      activity = footer;
    } else {
      view = "workspace";
      header = `offline · leyendo · ${rumbo ? rumbo.fuentes.length : 0} fuentes · ${Tui.spinner(state.spinner)}`;
      promptTitle = "encargo";
      placeholder = "Describe el material…  Enter envía";
      footer = `${clock}     /export  Tab  ?  q`;
      session = sessionListing(rumbo);
      activity = state.activity || "leyendo";
      proposal = `# ${Tui.spinner(state.spinner)} trabajando\n\n${state.activity || "leyendo la carpeta"}`;
    }

    return {
      view,
      cols: state.cols,
      rows: state.rows,
      header,
      chips: rumbo ? rumbo.chips : [],
      path: state.phase === "home" ? "" : "~/tero",
      promptTitle,
      placeholder,
      promptValue: "",
      footer,
      session,
      activity,
      proposal,
      evidence,
      warnings: warnText(state.warnings),
      plan,
      planTitle: rumbo ? ` ${rumbo.planTitle || "plan"} ` : " plan ",
      gate,
      gateTitle,
      help: state.help ? HELP : "",
      focus: view === "puerta" ? "proposal" : "proposal",
      tagline: "tus fuentes, tu criterio",
    };
  }

  function setPhase(phase, activity) {
    state.phase = phase;
    if (activity) state.activity = activity;
    paint();
  }

  function setStamp(label) {
    state.stamp = label;
    $("stamp-label").textContent = label;
  }

  function renderAvisos(warnings) {
    state.warnings = warnings;
  }

  function setGateEnabled(_on) {
    /* keys are always parsed; decide() guards on phase */
  }

  function resetFolders() {
    for (const id of ["derivados", "borradores"]) {
      const ul = $(id);
      ul.querySelectorAll("[data-file]").forEach((n) => n.remove());
      const empty = ul.querySelector(".empty");
      if (empty) empty.hidden = false;
    }
  }

  function putFile(folderId, name) {
    const ul = $(folderId);
    const empty = ul.querySelector(".empty");
    if (empty) empty.hidden = true;
    ul.querySelectorAll("[data-file]").forEach((n) => n.remove());
    const li = document.createElement("li");
    li.dataset.file = name;
    li.textContent = name;
    ul.appendChild(li);
  }

  function setFuentes(names) {
    const ul = $("fuentes");
    ul.innerHTML = "";
    const dir = document.createElement("li");
    dir.dataset.kind = "dir";
    dir.textContent = "fuentes/";
    ul.appendChild(dir);
    for (const name of names) {
      const li = document.createElement("li");
      li.textContent = name;
      ul.appendChild(li);
    }
  }

  function startClock() {
    stopClock();
    state.startedAt = performance.now();
    $("reloj").textContent = "0.0 s";
    state.clockTimer = window.setInterval(() => {
      const s = (performance.now() - state.startedAt) / 1000;
      $("reloj").textContent = `${s.toFixed(1)} s`;
      if (state.phase !== "home" && state.phase !== "esperando_criterio" && state.phase !== "listo") {
        if (!frameForPhase()) paint();
      }
    }, 120);
    stopSpinner();
    state.spinnerTimer = window.setInterval(() => {
      state.spinner += 1;
      if (state.phase !== "esperando_criterio" && state.phase !== "listo" && state.phase !== "home") {
        if (!frameForPhase()) paint();
      }
    }, 80);
  }

  function stopClock() {
    if (state.clockTimer) {
      window.clearInterval(state.clockTimer);
      state.clockTimer = null;
    }
    stopSpinner();
  }

  function stopSpinner() {
    if (state.spinnerTimer) {
      window.clearInterval(state.spinnerTimer);
      state.spinnerTimer = null;
    }
  }

  function logLine(text, kind) {
    const li = document.createElement("li");
    if (kind) li.dataset.kind = kind;
    const t = (performance.now() - state.startedAt) / 1000;
    li.textContent = `${t.toFixed(1)}s  $ ${text}`;
    $("bitacora").appendChild(li);
  }

  function showPages() {
    if (!state.pages.length) return;
    $("archivo").hidden = false;
    showPage(0);
  }

  function hidePages() {
    $("archivo").hidden = true;
  }

  function showPage(i) {
    const n = state.pages.length;
    if (!n) return;
    state.page = (i + n) % n;
    $("hoja-img").src = state.pages[state.page];
    $("hoja-pos").textContent = `${state.page + 1} / ${n}`;
    $("hoja-cap").textContent = `${state.filename} · página ${state.page + 1}`;
  }

  function wait(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  async function prepare(key) {
    const rumbo = rumbos[key];
    if (!rumbo) return;
    const token = ++state.token;
    state.rumbo = key;
    state.filename = rumbo.filename;
    state.pages = rumbo.pages.slice();
    state.help = false;
    $("chips").textContent = rumbo.chips.join(" · ");
    setStamp("REVISAR");
    resetFolders();
    hidePages();
    setFuentes(rumbo.fuentes);
    setGateEnabled(false);
    renderAvisos([]);
    $("consulta").hidden = true;
    $("bitacora").innerHTML = "";
    $("corrida-real").textContent = rumbo.corrida;
    $("gate-note").textContent = "Consulta en curso. La puerta espera el borrador.";
    document.querySelectorAll("[data-rumbo]").forEach((btn) => {
      btn.setAttribute("aria-pressed", btn.dataset.rumbo === String(key) ? "true" : "false");
    });
    startClock();
    const acts = [];
    setPhase("leyendo", rumbo.steps[0].tool);

    for (const step of rumbo.steps) {
      if (token !== state.token) return;
      const label = step.detail ? `${step.tool} · ${step.detail}` : step.tool;
      const nice = TOOL_LABEL[step.tool] || step.tool;
      acts.push(`✓ ${nice}${step.detail ? `  ${step.detail}` : ""}`);
      state.activity = acts.slice(-8).join("\n") + `\n${Tui.spinner(state.spinner)} ${nice}`;
      if (step.plan) {
        stopSpinner();
        setPhase("esperando_plan", label);
      } else if (step.draft) {
        setPhase("escribiendo", label);
      } else {
        setPhase(step.plan ? "plan" : "leyendo", label);
      }
      logLine(label, step.tool);
      await wait(step.ms * scale);
      if (token !== state.token) return;
      if (step.draft) {
        renderAvisos(rumbo.warnings);
        setGateEnabled(true);
        $("gate-note").textContent =
          "Avisos a la vista. s escribe en derivados/ y muestra las páginas reales. n descarta. b deja borrador. c pide crítica.";
        stopClock();
        const s = (performance.now() - state.startedAt) / 1000;
        $("reloj").textContent = `${s.toFixed(1)} s`;
        logLine(
          rumbo.elapsed != null
            ? `listo · reloj ${s.toFixed(1)} s · corrida real ${rumbo.elapsed} s`
            : `listo · reloj ${s.toFixed(1)} s · ${rumbo.corrida}`,
          "ok",
        );
        setPhase("esperando_criterio", "1 activity start por tool · espera s/n/b/c");
      }
    }
  }

  function decide(letter) {
    if (state.phase === "esperando_plan" && letter === "a") {
      return;
    }
    if (state.phase !== "esperando_criterio" && letter !== "c") {
      if (state.phase === "home") {
        $("gate-note").textContent = "Primero un rumbo (1–4).";
        paint();
        return;
      }
    }
    if (state.phase !== "esperando_criterio") return;

    if (letter === "s") {
      if (!canAccept(state.warnings) || WARNINGS_BLOCK_S) {
        $("gate-note").textContent = "Esto no debería pasar: s no se bloquea.";
        return;
      }
      putFile("derivados", state.filename);
      setStamp("ACEPTADO");
      $("archivo-lead").textContent = "Archivo en derivados/ — páginas de la corrida real";
      showPages();
      $("gate-note").textContent =
        "Aceptado. El original no se tocó. Hash de fuentes intacto. Estas son las hojas, no el mock.";
      setGateEnabled(false);
      setPhase("listo", "s → derivados/");
      return;
    }
    if (letter === "n") {
      resetFolders();
      hidePages();
      setStamp("DESCARTADO");
      $("gate-note").textContent = "Descartado. No quedó archivo. Las páginas no se publican.";
      setGateEnabled(false);
      setPhase("listo", "n → nada en disco");
      return;
    }
    if (letter === "b") {
      putFile("borradores", state.filename);
      setStamp("BORRADOR");
      $("archivo-lead").textContent = "Borrador en borradores/ — mismas páginas, aún no derivados/";
      showPages();
      $("gate-note").textContent = "Borrador en borradores/. /export también funciona sobre esto.";
      setGateEnabled(false);
      setPhase("listo", "b → borradores/");
      return;
    }
    if (letter === "c") {
      setStamp("CORREGIR");
      $("critica").showModal();
    }
  }

  function applyCritique() {
    const note = $("critica-text").value.trim() || "Más evidencia, menos adorno.";
    hidePages();
    const rumbo = rumbos[state.rumbo];
    if (rumbo) {
      rumbo.draft = `${rumbo.draft}\n\n> Crítica docente: ${note}`;
    }
    renderAvisos([
      {
        code: "unverified_citation",
        message: "Sigue habiendo parafraseo. Sigue sin bloquear s.",
      },
    ]);
    setStamp("REVISAR");
    setGateEnabled(true);
    $("gate-note").textContent = "Reescrito. La crítica quedó; vuelve a la puerta.";
    setPhase("esperando_criterio", "c persistida · s/n/b/c");
  }

  function help() {
    state.help = !state.help;
    paint();
  }

  function hitFromEvent(ev) {
    const target = $("tui-stage") || $("tui-grid");
    const grid = target.getBoundingClientRect();
    const x = Math.floor((ev.clientX - grid.left) / state.cellW);
    const y = Math.floor((ev.clientY - grid.top) / state.cellH);
    return state.hits.find((h) => x >= h.x && x < h.x + h.w && y >= h.y && y < h.y + h.h);
  }

  document.querySelectorAll("[data-rumbo]").forEach((btn) => {
    btn.addEventListener("click", () => prepare(btn.dataset.rumbo));
  });
  document.querySelectorAll("[data-gate]").forEach((btn) => {
    btn.addEventListener("click", () => decide(btn.dataset.gate));
  });
  $("critica-ok").addEventListener("click", (ev) => {
    ev.preventDefault();
    $("critica").close();
    applyCritique();
  });
  $("hoja-prev").addEventListener("click", () => showPage(state.page - 1));
  $("hoja-next").addEventListener("click", () => showPage(state.page + 1));
  $("tui-stage").addEventListener("click", (ev) => {
    const hit = hitFromEvent(ev);
    if (!hit) {
      $("prompt").focus();
      return;
    }
    if (hit.action === "rumbo") prepare(hit.key);
    if (hit.action === "gate") decide(hit.key);
  });
  $("prompt").addEventListener("input", () => {
    syncPromptOverlay();
  });
  $("prompt").addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter") return;
    ev.preventDefault();
    const text = $("prompt").value.trim();
    $("prompt").value = "";
    if (!text) return;
    if (looksPhatic(text)) {
      $("gate-note").textContent = "hola no es un encargo. 1–4 rumbo, o describe el material.";
      paint();
      return;
    }
    prepare("1");
  });

  document.addEventListener("keydown", (ev) => {
    if (ev.target && ev.target.tagName === "TEXTAREA") return;
    const inPrompt = ev.target && ev.target.id === "prompt";
    const editable = inPrompt && !$("prompt").readOnly;
    /* Editable prompt: rumbo/? on empty, otherwise type. Gate keys s/n/b/c
       only fire here when the prompt is readOnly (puerta / plan / listo). */
    if (editable) {
      if (!$("prompt").value) {
        if (["1", "2", "3", "4"].includes(ev.key)) {
          ev.preventDefault();
          prepare(ev.key);
          return;
        }
        if (ev.key === "?" || (ev.shiftKey && ev.key === "/")) {
          ev.preventDefault();
          help();
          return;
        }
      }
      return;
    }
    if (inPrompt && $("prompt").readOnly) {
      $("prompt").blur();
    }
    if (ev.key === "?" || (ev.shiftKey && ev.key === "/")) {
      ev.preventDefault();
      help();
      return;
    }
    if (["1", "2", "3", "4"].includes(ev.key)) {
      ev.preventDefault();
      prepare(ev.key);
      return;
    }
    if (ev.key === "ArrowLeft" && !$("archivo").hidden) {
      showPage(state.page - 1);
      return;
    }
    if (ev.key === "ArrowRight" && !$("archivo").hidden) {
      showPage(state.page + 1);
      return;
    }
    const letter = ev.key.toLowerCase();
    if (letter === "s" || letter === "n" || letter === "b" || letter === "c") {
      ev.preventDefault();
      decide(letter);
    }
  });

  window.addEventListener("resize", () => paint());

  fetch("./build-info.json")
    .then((r) => (r.ok ? r.json() : null))
    .then((info) => {
      if (info && info.short) {
        $("window-path").dataset.sha = info.short;
      }
    })
    .catch(() => {});

  setGateEnabled(false);
  const start = () => {
    paint();
  };
  $("tui-shot").addEventListener("load", () => paint());
  $("tui-shot").addEventListener("error", () => paintLive(frameForPhase()));
  loadFrames().finally(() => {
    start();
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => start()).catch(() => {});
    }
  });
})();
