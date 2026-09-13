/* La landing pública es la OpenTUI real, virtualizada en una ventana, con la
   sesión conversacional del protocolo (docs/CONVERSACIONAL.md).

   La persona escribe y el agente infiere la intención:
     a) responder          → `respuesta`, sin tarjeta ni aprobación
     b) crear material     → `propuesta` (resumen + vista previa + evidencias + avisos)
     c) editar o adaptar   → `propuesta` con acción `adaptar` y notas NEE
   Se aprueba con `y` o escribiendo en el hilo («dale»); `n` descarta.

   Nada se escribe sin aprobación, y quien escribe es el host: la TUI solo
   pinta. La hoja fotocopiada (`#archivo`) aparece recién después de aprobar. */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const Tui = window.teroTui;
  const GRID_COLS = 140;
  const BASE_ROWS = 40;

  const FRAME_NAMES = [
    "home",
    "help",
    "respuesta",
    "conversacion",
    "conversacion-streaming",
    "propuesta",
    "propuesta-guia",
    "propuesta-adaptar",
    "escrito",
    "escrito-adaptar",
    "descartado",
    "error",
  ];
  const frames = Object.fromEntries(FRAME_NAMES.map((name) => [name, null]));

  function loadFrames() {
    return Promise.all(
      FRAME_NAMES.map((name) =>
        fetch(`./assets/tui/frames/${name}.json?v=conversacional`)
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            frames[name] = data;
          })
          .catch(() => {}),
      ),
    );
  }

  /* Páginas LaTeX reales de las corridas ya hechas. Se muestran solo después
     de aprobar: son la fotocopia de lo que el host escribió en derivados/. */
  const HOJAS = {
    cuento: {
      corrida: "loop10 · GLM 4.7 Flash · 29.1 s · 33 tools",
      pages: [
        "./assets/hojas/eval-cuento/p1.png",
        "./assets/hojas/eval-cuento/p2.png",
        "./assets/hojas/eval-cuento/p3.png",
      ],
    },
    guia: {
      corrida: "MiniMax M2.5 · guía 1° medio · 94.9 s",
      pages: [
        "./assets/hojas/guia-sistemas/p1.png",
        "./assets/hojas/guia-sistemas/p2.png",
        "./assets/hojas/guia-sistemas/p3.png",
      ],
    },
  };

  /* Escenas del protocolo conversacional */
  const ESCENAS = {
    responder: {
      prompt: "¿Qué tengo en la carpeta?",
      beats: [
        { pensando: true, hold: 1400 },
        {
          frame: "respuesta",
          phase: "idle",
          hold: 3400,
          nota: "intención a) responder: el agente contesta y no hay nada que aprobar",
        },
      ],
    },
    crear: {
      prompt: "Prepara una evaluación de comprensión lectora para 4° básico.",
      beats: [
        { pensando: true, hold: 1600 },
        {
          frame: "conversacion",
          phase: "idle",
          hold: 2600,
          nota: "le falta información: el agente pregunta en lenguaje natural",
        },
        { prompt: "Sí, con pauta. Usa el cuento del cóndor y el huemul.", pensando: true, hold: 1800 },
        {
          frame: "propuesta",
          phase: "esperando_aprobacion",
          hold: 5600,
          decision: "dale",
          nota: "intención b) crear: resumen, vista previa, evidencias ✓/? y avisos que no bloquean",
          aprobar: {
            frame: "escrito",
            phase: "listo",
            hold: 5600,
            hoja: "cuento",
            accion: "crear",
            archivo: "derivados/20260911-101500-evaluacion-condor-9c1f2a.md",
            lead: "El host escribió el archivo en derivados/ después de tu aprobación. Estas son sus páginas, la fotocopia para revisar.",
          },
          descartar: {
            frame: "descartado",
            phase: "idle",
            hold: 2800,
            lead: "Descartado: no se escribió nada. La carpeta quedó igual.",
          },
        },
      ],
    },
    descartar: {
      prompt: "Necesito una guía para introducir sistemas 2×2 en 1° medio.",
      beats: [
        { pensando: true, hold: 1600 },
        {
          frame: "propuesta-guia",
          phase: "esperando_aprobacion",
          hold: 4600,
          decision: "n",
          nota: "también se puede decir que no: `n` descarta y no escribe nada",
          aprobar: {
            frame: "escrito",
            phase: "listo",
            hold: 5200,
            hoja: "guia",
            accion: "crear",
            archivo: "derivados/20260911-103100-guia-sistemas-2x2-77c1de.md",
            lead: "El host escribió el archivo en derivados/ después de tu aprobación. Estas son sus páginas, la fotocopia para revisar.",
          },
          descartar: {
            frame: "descartado",
            phase: "idle",
            hold: 3200,
            lead: "Descartado: no se escribió nada. La guía quedó solo como propuesta.",
          },
        },
      ],
    },
    adaptar: {
      prompt: "Adapta la evaluación del cóndor para un estudiante con dislexia.",
      beats: [
        { pensando: true, hold: 1600 },
        {
          frame: "propuesta-adaptar",
          phase: "esperando_aprobacion",
          hold: 6400,
          decision: "y",
          nota: "intención c) adaptar: acción adaptar, origen, cambios, apoyos y criterios NEE",
          aprobar: {
            frame: "escrito-adaptar",
            phase: "listo",
            hold: 6400,
            hoja: "cuento",
            accion: "adaptar",
            archivo: "derivados/20260911-101800-evaluacion-condor-adaptada-4d7b31.md",
            capFile: "derivados/20260910-210457-evaluacion-condor-4a5586.md",
            lead: "El host escribió una versión nueva en derivados/: el material de origen no se tocó. Estas son las páginas del origen, para contrastar con la adaptación.",
            cap: "páginas del material de origen",
          },
          descartar: {
            frame: "descartado",
            phase: "idle",
            hold: 3200,
            lead: "Descartado: no se escribió nada. El material de origen sigue intacto.",
          },
        },
      ],
    },
  };

  /* Estado interactivo: NUNCA reproduce un video en bucle */
  const state = {
    phase: "idle",
    frame: "home",
    escena: null,
    auto: false, // Modo interactivo real
    token: 0,
    pages: [],
    page: 0,
    filename: null,
    warning: "",
    help: false,
    spinner: 0,
    spinnerTimer: null,
    cols: GRID_COLS,
    rows: BASE_ROWS,
    cellW: 10,
    cellH: 24,
    fontSize: 13,
    hits: [],
    promptBox: null,
    model: null,
    pendiente: null,
    messages: [],
    activities: [],
    lastWritten: null,
    promptValue: "",
    focus: "propuesta",
    evidenceIndex: 0,
  };

  const HELP = `tero — conversación

Escribe abajo: «Pregunta, explora o crea…»
El agente entiende la intención y actúa:
  a) responde          b) crea material          c) edita o adapta (NEE)

Cuando propone un archivo verás qué va a hacer y la vista previa.
  y  aprobar — el host escribe en derivados/
  n  descartar — no se escribe nada
También puedes responder con tus palabras («dale»); el host clasifica.

Atajos:
  Tab    cambiar foco entre paneles
  [ ]    recorrer citas de evidencia
  ?      abrir o cerrar esta ayuda
  /clear reiniciar la pantalla a inicio

Los avisos no bloquean la aprobación: se muestran antes de decidir.
La TUI nunca escribe archivos: escribe el host, y solo tras aprobar.

? o Esc cierra`;

  /* Clasificador de la decisión (espejo de tero.approval) */
  const TRIM = /^[¡!¿?.,;:()[\]{}«»"'\u2026-]+|[¡!¿?.,;:()[\]{}«»"'\u2026-]+$/g;

  function fold(text) {
    return (text || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/\p{M}/gu, "");
  }

  const APROBAR_FIRME =
    /\b(?:me gusta|escribel[oa]|guardal[oa]|aprobad[oa]|apruebo|de acuerdo|asi nomas|asi no mas|hazl[oa] (?:asi|tal cual|igual|nomas|no mas))\b/;
  const APROBAR_CORTO =
    /^(?:si|s|dale|ok|okay|ya|listo|perfecto|bueno|bien|muy bien|correcto|vale|esta bien|esta bueno|asi esta bien)\b/;
  const DESCARTAR =
    /\b(?:dejal[oa]|deja|borr\w*|anul\w*|olvid\w*|descart\w*|nada|esta mal\w*)\b|\bno\b(?!\s*mas\b)|\b(?:tampoco|nunca|jamas|ni ahi|de ninguna manera)\b/;
  const CAMBIAR =
    /\b(?:cambia\w*|modific\w*|ajust\w*|corrig\w*|correg\w*|arregl\w*|agreg\w*|anad\w*|quit\w*|sac\w*|elimin\w*|reemplaz\w*|adapt\w*|simplific\w*|acort\w*|alarg\w*|mejor\w*|pero)\b|\ben vez\b/;
  const DUDA = /\bno\s+(?:lo\s+|la\s+)?se\b|\bno\s+ent(?:iend|end)\w*\b|\bno\s+cach\w*\b|\bno\s+comprend\w*\b/;

  function classifyDecision(text) {
    const raw = (text || "").trim();
    if (!raw) return { kind: "ambiguo", note: raw };
    const t = fold(raw).replace(TRIM, " ").replace(/\s+/g, " ").trim();
    const words = t.split(" ").filter(Boolean);
    const blobs = words.map((w) => w.replace(TRIM, ""));
    const phrase = blobs.join(" ");
    if (CAMBIAR.test(t)) return { kind: "cambiar", note: raw };
    if (DUDA.test(t)) return { kind: "preguntar", note: raw };
    if (
      /\b(?:no\s+gracias|ya,?\s*no|no,?\s*gracias)\b/.test(t) ||
      DESCARTAR.test(t) ||
      /^n\b/.test(t) ||
      blobs.includes("no")
    ) {
      return { kind: "descartar", note: raw };
    }
    if (/\?/.test(raw)) return { kind: "preguntar", note: raw };
    if (APROBAR_FIRME.test(t) || APROBAR_CORTO.test(t)) return { kind: "aprobar", note: raw };
    if (["dale no mas", "no mas", "nomas", "como no", "asi no mas", "asi nomas"].includes(phrase)) {
      return { kind: "aprobar", note: raw };
    }
    if (phrase === "hazlo asi" || phrase === "hazla asi") return { kind: "aprobar", note: raw };
    return { kind: "ambiguo", note: raw };
  }

  function measure() {
    const fitted = Tui.fitHost($("tui-host"), $("tui-grid"), GRID_COLS, state.rows);
    state.cellW = fitted.cellW;
    state.cellH = fitted.cellH;
    state.fontSize = fitted.fontSize;
    const host = $("tui-host");
    host.style.setProperty("--cell-w", `${state.cellW}px`);
    host.style.setProperty("--cell-h", `${state.cellH}px`);
  }

  function placePrompt(box) {
    if (!box) return;
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

  function syncPromptOverlay() {
    const input = $("prompt");
    const typing = Boolean(input.value);
    input.classList.toggle("is-typing", typing);
    input.placeholder =
      state.phase === "esperando_aprobacion"
        ? "y aprueba · n descarta · o escribe un cambio…"
        : state.frame === "home"
          ? "Pregunta, explora o crea…"
          : "Escribe tu respuesta…  Enter envía";
    $("window-path").textContent = "~/tero";
  }

  function applyPainted(painted, frameName, view) {
    state.cellW = painted.cellW || state.cellW;
    state.cellH = painted.cellH || state.cellH;
    state.fontSize = painted.fontSize || state.fontSize;
    state.hits = painted.hits || [];
    state.promptBox = painted.prompt;
    placePrompt(painted.prompt);
    document.body.dataset.view = view;
    document.body.dataset.frame = frameName || "live";
    document.body.dataset.phase = state.phase;
    syncPromptOverlay();
  }

  function frameData() {
    if (state.help) return frames.help || frames.home;
    return frames[state.frame] || frames.home;
  }

  /* Modelo vivo dinámico para renderizar con Tui.paint */
  function liveModel() {
    const p = state.pendiente;

    let thread = "Escribe lo que necesitas.\nEl agente responde, crea o adapta; tú apruebas.";
    if (state.messages.length > 0) {
      thread = state.messages
        .map((m) => `${m.role === "persona" ? "Docente:\n" : "tero:\n"}${m.text}`)
        .join("\n\n");
    }

    let activity = state.activities.length ? state.activities.slice(-3).join("\n") : "en espera";
    if (state.phase === "pensando") {
      activity = `${Tui.spinner(state.spinner)} ${activity}`;
    }

    let proposal = "";
    let evidence = "Las citas aparecen cuando el agente propone un archivo.\n✓ en el archivo · ? parafraseo";
    let warnings = "sin avisos";
    let gate = "";

    if (p) {
      if (p.status === "escrito") {
        proposal = `✓ ESCRITO · ${p.accion} · ${p.tipo_label}\n` +
          `Ruta: ${p.writtenPath || "derivados/..."}\n\n` +
          `Originales intactos (SHA-256 verificado).\n` +
          `El host escribió el archivo en derivados/ tras tu aprobación.\n\n` +
          `── vista previa ──\n` +
          p.vista_previa;
      } else if (p.status === "descartado") {
        proposal = `✕ DESCARTADO · ${p.tipo_label}\n` +
          `No se escribió ningún archivo.\n` +
          `La carpeta de trabajo quedó intacta.`;
      } else {
        let extra = "";
        if (p.accion === "adaptar") {
          extra = `\norigen: ${p.origen || "derivados/..."}\n` +
            `cambios: ${(p.cambios || []).join("; ")}\n` +
            `notas_nee: ${(p.notas_nee || []).join("; ")}\n`;
        }
        proposal = `PROPUESTA · ${p.accion} · ${p.tipo_label}\n` +
          `${p.titulo}\n\n` +
          `${p.resumen}\n` +
          extra +
          `\n── vista previa ──\n` +
          p.vista_previa;
      }

      if (p.evidencias && p.evidencias.length) {
        evidence = p.evidencias
          .map((e, idx) => {
            const marker = idx === state.evidenceIndex ? "▸" : " ";
            const check = e.verified ? "✓ en archivo" : "? parafraseo";
            return `${marker} ${idx + 1}/${p.evidencias.length}  ${check}\n  ${e.path}\n  «${e.snippet}»`;
          })
          .join("\n\n");
      }

      if (p.warnings && p.warnings.length) {
        warnings = p.warnings.map((w) => `! ${w.message}`).join("\n");
      }

      if (p.status === "pendiente") {
        gate = "¿escribo el archivo?   [y] aprobar   [n] descartar   o escribe un cambio";
      }
    }

    let header = "offline · inicio";
    if (state.phase === "pensando") header = `offline · pensando ${Tui.spinner(state.spinner)}`;
    else if (state.phase === "esperando_aprobacion") header = "offline · tu decisión: y / n";
    else if (state.phase === "listo") header = "offline · escrito en derivados/";
    else if (state.frame !== "home") header = "offline · conversación";

    return {
      view: state.frame === "home" ? "home" : "conversacion",
      cols: state.cols,
      rows: state.rows,
      header,
      chips: p ? [`tarea: ${p.accion || "crear"} · ${p.tipo_label}`, "4° básico", "Lenguaje"] : ["4° básico", "Lenguaje", "LEN-4B-OA04"],
      path: "~/tero",
      promptTitle: p && p.status === "pendiente" ? "▸ ACCIÓN REQUERIDA · Pulsa [y] aprobar o [n] descartar" : state.frame === "home" ? "pregunta" : "▸ TU TURNO · Escribe y pulsa Enter",
      placeholder: p && p.status === "pendiente"
        ? "y aprueba · n descarta · o escribe tu decisión…"
        : state.frame === "home"
          ? "Pregunta, explora o crea…"
          : "Escribe tu respuesta…  Enter envía",
      promptValue: $("prompt") ? $("prompt").value : "",
      footer: p && p.status === "pendiente"
        ? "tu decisión: y aprueba · n descarta · o escribe tu decisión"
        : "? ayuda · tab paneles · [ ] evidencia · /clear reinicia",
      thread,
      activity,
      proposal,
      evidence,
      warnings,
      gate,
      gateTitle: p && p.status === "pendiente" ? "▸ ACCIÓN REQUERIDA · Aprobación" : " aprobación ",
      help: state.help ? HELP : "",
      focus: state.focus,
      tagline: "tus fuentes, tu criterio",
    };
  }

  function paint() {
    measure();
    const model = liveModel();
    $("tui-shot").hidden = true;
    const canvas = $("tui-canvas");
    if (canvas) canvas.hidden = true;
    $("tui-grid").classList.remove("is-shot");

    const painted = Tui.paint($("tui-grid"), model);
    applyPainted(
      { ...painted, cellW: state.cellW, cellH: state.cellH, fontSize: state.fontSize },
      state.frame,
      state.frame === "home" ? "home" : "session",
    );
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

  function putDerivado(name) {
    const ul = $("derivados");
    const empty = ul.querySelector(".empty");
    if (empty) empty.hidden = true;
    const li = document.createElement("li");
    li.dataset.file = name;
    li.textContent = name;
    ul.appendChild(li);
  }

  function clearDerivado() {
    const ul = $("derivados");
    ul.querySelectorAll("[data-file]").forEach((n) => n.remove());
    const empty = ul.querySelector(".empty");
    if (empty) empty.hidden = false;
  }

  function logLine(text, kind) {
    const li = document.createElement("li");
    if (kind) li.dataset.kind = kind;
    li.textContent = text;
    $("bitacora").appendChild(li);
  }

  function hidePages() {
    $("archivo").hidden = true;
    state.pages = [];
    state.page = 0;
    $("prompt").focus();
  }

  function showPages(hoja, caption, lead, cap) {
    const pages = hoja.pages.slice();
    if (!pages.length) return;
    state.pages = pages;
    state.filename = caption;
    $("archivo").hidden = false;
    $("archivo-lead").textContent = lead;
    $("corrida-real").textContent = hoja.corrida;
    $("hoja-cap").dataset.cap = cap || "";
    showPage(0);
  }

  function showPage(i) {
    const n = state.pages.length;
    if (!n) return;
    state.page = (i + n) % n;
    $("hoja-img").src = state.pages[state.page];
    $("hoja-img").alt = `Página ${state.page + 1} de la ficha escrita en derivados/`;
    $("hoja-pos").textContent = `${state.page + 1} / ${n}`;
    const cap = $("hoja-cap").dataset.cap;
    $("hoja-cap").textContent = `${state.filename}${cap ? ` · ${cap}` : ""} · página ${state.page + 1}`;
  }

  function wait(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  function startSpinner() {
    stopSpinner();
    state.spinnerTimer = window.setInterval(() => {
      state.spinner += 1;
      paint();
    }, 90);
  }

  function stopSpinner() {
    if (state.spinnerTimer) {
      window.clearInterval(state.spinnerTimer);
      state.spinnerTimer = null;
    }
  }

  /* Plantillas deterministas para interacción en vivo */
  const LIVE_TEMPLATES = {
    planificacion: {
      accion: "crear",
      tipo: "planificacion",
      tipo_label: "planificación",
      titulo: "Planificación: Leer el cuento y distinguir lo explícito de lo implícito en el valle",
      resumen: "Planificación lista para usar en aula, con evidencia de las fuentes de la carpeta.",
      vista_previa: `---
generado_por: tero
tipo: planificacion
titulo: "Planificación: Leer el cuento y distinguir lo explícito de lo implícito en el valle"
curso: 4° básico
asignatura: Lenguaje y Comunicación
oa: LEN-4B-OA04
duracion: 45 min
---
# Planificación — El cóndor y el huemul

## Objetivo
Que las y los estudiantes de 4° básico extraigan información explícita e implícita del cuento, usando el diálogo del huemul como evidencia — no como adorno.

## OA
LEN-4B-OA04 (Lenguaje y Comunicación). Comprensión lectora de narraciones: lo que el texto dice y lo que deja inferir.

## Inicio (10 min)
- Pregunta abierta al curso: «¿Quién sabe más del valle? ¿El que vuela alto o el que pregunta por el agua?»
- Anotar en la pizarra dos columnas: *explícito* / *implícito*.

## Desarrollo (25 min)
1. Lectura compartida del cuento de la carpeta (\`fuentes/cuento-el-condor-y-el-huemul.md\`).
2. Primera pasada: subrayar datos explícitos (el río bajo, el maitén seco, el vuelo del cóndor).
3. Segunda pasada: inferir motivaciones (el huemul no huye porque necesita entender; preguntar es valentía).
4. Trabajo en parejas: responder la pregunta «¿Por qué el cóndor baja cuando el huemul no corre?».

## Cierre (10 min)
- Ticket de salida de 2 líneas: escribir una afirmación explícita y una inferencia sobre el cuento.`,
      evidencias: [
        {
          path: "fuentes/cuento-el-condor-y-el-huemul.md",
          snippet: "El huemul no corrió. Miró el agua del valle y preguntó por qué el río estaba tan bajo.",
          verified: true,
        },
        {
          path: "fuentes/cuento-el-condor-y-el-huemul.md",
          snippet: "El cóndor bajó al maitén y abrió las alas para tapar el sol…",
          verified: true,
        },
      ],
      warnings: [],
      hojaKey: "cuento",
    },

    evaluacion: {
      accion: "crear",
      tipo: "evaluacion",
      tipo_label: "evaluación",
      titulo: "Evaluación formativa de comprensión lectora — El cóndor y el huemul",
      resumen: "Prueba de 45 min con ítems de selección múltiple y V/F con pauta.",
      vista_previa: `---
generado_por: tero
tipo: evaluacion
titulo: "Evaluación de comprensión lectora — El cóndor y el huemul"
curso: 4° básico
asignatura: Lenguaje y Comunicación
oa: LEN-4B-OA04
duracion: 45 min
puntaje_total: 10
---
# Evaluación formativa — El cóndor y el huemul

**Nombre:** ____________________________________ **Fecha:** ___________
**Instrucciones:** Lee el cuento de la carpeta. Tiempo 45 minutos.

## Ítem 1: Selección múltiple (4 puntos)
1. ¿Qué anotó la niña detrás del maitén?
   a) Que el río estaba bajo
   b) Que el cóndor tenía hambre
   c) Que el huemul corrió

2. ¿Qué significa que el cóndor abriera las alas para tapar el sol?
   a) Dar sombra
   b) Demostrar tamaño y poder
   c) Avisar que llovería

## Ítem 2: Verdadero o Falso con justificación (3 puntos)
1. ___ El huemul huyó asustado hacia la quebrada.
2. ___ El río del valle llevaba poca agua.

## Ítem 3: Desarrollo con cita textual (3 puntos)
Cita el cuento para explicar por qué el huemul decidió no correr.`,
      evidencias: [
        {
          path: "fuentes/cuento-el-condor-y-el-huemul.md",
          snippet: "El huemul no corrió. Miró el agua del valle y preguntó por qué el río estaba tan bajo.",
          verified: true,
        },
        {
          path: "fuentes/cuento-el-condor-y-el-huemul.md",
          snippet: "El cóndor bajó al maitén y abrió las alas para tapar el sol…",
          verified: true,
        },
      ],
      warnings: [],
      hojaKey: "cuento",
    },

    adaptacion: {
      accion: "adaptar",
      tipo: "evaluacion",
      tipo_label: "evaluación adaptada (NEE)",
      titulo: "Evaluación adaptada: El cóndor y el huemul (Apoyos Decreto 83/2015)",
      resumen: "Adaptación con Decreto 83: apoyos visuales y tiempo adicional.",
      origen: "derivados/20260911-101500-evaluacion-condor-9c1f2a.md",
      cambios: [
        "Instrucciones directas destacadas paso a paso",
        "Menos carga de lectura por ítem y formato espaciado",
      ],
      notas_nee: [
        "acceso · presentación de la información: lectura guiada en voz alta y apoyos visuales de la secuencia",
        "acceso · tiempo: 15 minutos adicionales y pausas programadas",
      ],
      vista_previa: `---
generado_por: tero
tipo: evaluacion
titulo: "Evaluación adaptada (NEE) — El cóndor y el huemul"
origen: derivados/20260911-101500-evaluacion-condor-9c1f2a.md
curso: 4° básico
asignatura: Lenguaje y Comunicación
oa: LEN-4B-OA04
apoyos_decreto_83:
  - "acceso · presentación: lectura guiada y apoyos visuales"
  - "acceso · tiempo: 15 min extra con pausa intermedia"
---
# Evaluación adaptada — El cóndor y el huemul

**Nombre:** ____________________________________ **Fecha:** ___________
**Instrucción:** Puedes responder por escrito o conversando con tu docente.

## Paso 1: Lee junto a tu docente el fragmento
«El huemul no corrió. Miró el agua del valle y preguntó…»

## Paso 2: Marca la respuesta correcta (3 pts)
1. ¿Qué hizo el huemul cuando vio al cóndor?
   [ ] Corrió rápido
   [ ] Se quedó y preguntó
   [ ] Se durmió

## Paso 3: Dibuja y cuenta (3 pts)
Dibuja qué le respondió el cóndor al huemul.`,
      evidencias: [
        {
          path: "derivados/20260911-101500-evaluacion-condor-9c1f2a.md",
          snippet: "Ítem 1: Selección múltiple... ¿Qué hizo el huemul cuando vio al cóndor descender?",
          verified: true,
        },
        {
          path: "fuentes/cuento-el-condor-y-el-huemul.md",
          snippet: "El huemul no corrió. Miró el agua del valle y preguntó…",
          verified: true,
        },
      ],
      warnings: [
        {
          code: "paci_no_oficial",
          message: "Apoyos de aula bajo Decreto 83/2015. No constituye un PACI ni adecuación curricular formal MINEDUC.",
          blocking: false,
        },
      ],
      hojaKey: "cuento",
    },
  };

  /* Ejecución de un turno interactivo */
  async function submit(text) {
    const value = (text || "").trim();
    if (!value) return;

    // Comandos slash
    if (value === "/clear" || value === "/reset") {
      state.frame = "home";
      state.phase = "idle";
      state.messages = [];
      state.activities = [];
      state.pendiente = null;
      hidePages();
      paint();
      return;
    }
    if (value === "/help" || value === "?") {
      state.help = !state.help;
      paint();
      return;
    }
    if (value.startsWith("/export")) {
      const fmt = value.split(" ")[1] || "markdown";
      state.messages.push({ role: "persona", text: value });
      state.messages.push({
        role: "agente",
        text: state.lastWritten
          ? `Exportado a ${fmt.toUpperCase()}: ${state.lastWritten.replace(/\.md$/, "." + (fmt === "latex" ? "tex" : fmt))}`
          : "No hay ningún archivo aprobado en derivados/ para exportar.",
      });
      paint();
      return;
    }

    // Decisión pendiente
    if (state.pendiente && state.pendiente.status === "pendiente") {
      const kind = classifyDecision(value);
      if (kind.kind === "aprobar") {
        applyDecision("aprobar", value);
        return;
      }
      if (kind.kind === "descartar") {
        applyDecision("descartar", value);
        return;
      }
      if (kind.kind === "cambiar") {
        await revisePending(value);
        return;
      }
      state.messages.push({ role: "persona", text: value });
      state.messages.push({
        role: "agente",
        text: "Entendido. La propuesta sigue en pantalla esperando tu decisión: presiona 'y' para aprobar, 'n' para descartar o escribe el cambio que deseas.",
      });
      paint();
      return;
    }

    // Nuevo turno del usuario
    state.frame = "conversacion";
    state.phase = "pensando";
    state.messages.push({ role: "persona", text: value });
    state.activities = ["list_sources · 4 fuentes en carpeta"];
    startSpinner();
    paint();

    await wait(240);
    state.activities.push("read_source · fuentes/cuento-el-condor-y-el-huemul.md");
    paint();

    await wait(240);
    state.activities.push("get_oa · LEN-4B-OA04");
    paint();

    const folded = fold(value);
    const isAdaptar = /\b(adapt\w*|nee|dislex\w*|tdah|tea\b|inclusi\w*|apoyo\w*|decreto\s*83)\b/.test(folded);
    const isCrear = /\b(crear|prepara\w*|haz\w*|planifi\w*|evalua\w*|prueba|guia|pauta|actividad|ficha)\b/.test(folded);
    const isQuestion = /\b(fuente\w*|carpeta|que tengo|que hay|hola|como funcion\w*|quien eres|mineduc)\b/.test(folded);

    await wait(260);
    stopSpinner();

    if (isAdaptar) {
      state.activities.push("cite_evidence · 2 citas");
      state.activities.push("proponer_editar · accion: adaptar");
      state.pendiente = JSON.parse(JSON.stringify(LIVE_TEMPLATES.adaptacion));
      state.pendiente.status = "pendiente";
      state.phase = "esperando_aprobacion";
      state.messages.push({
        role: "agente",
        text: "He preparado la propuesta de adaptación según Decreto 83 con apoyos de acceso. Revisa la vista previa y dime si la apruebas.",
      });
    } else if (isCrear || !isQuestion) {
      let tmpl = LIVE_TEMPLATES.planificacion;
      if (/\b(evalua\w*|prueba|pauta|test)\b/.test(folded)) {
        tmpl = LIVE_TEMPLATES.evaluacion;
      }
      state.activities.push("cite_evidence · 2 citas verificadas");
      state.activities.push(`proponer_crear · tipo: ${tmpl.tipo}`);
      state.pendiente = JSON.parse(JSON.stringify(tmpl));
      state.pendiente.status = "pendiente";
      state.phase = "esperando_aprobacion";
      state.messages.push({
        role: "agente",
        text: `He preparado la propuesta de ${state.pendiente.tipo_label} con citas verificadas de tus fuentes. ¿Escribo este material en derivados/?`,
      });
    } else {
      state.phase = "idle";
      let respuesta = "";
      if (/\b(fuente\w*|carpeta|que tengo|que hay)\b/.test(folded)) {
        respuesta = "Tienes 4 fuentes locales en la carpeta de trabajo:\n" +
          "• `fuentes/cuento-el-condor-y-el-huemul.md` (cuento del valle cordillerano)\n" +
          "• `fuentes/bases-oa-lenguaje-4b.md` (OA 4 de comprensión lectora)\n" +
          "• `fuentes/vocabulario-unidad.md`\n" +
          "• `fuentes/notas-curso.md`\n\n" +
          "Puedo preparar una planificación o una evaluación sobre este cuento. ¿Qué te gustaría hacer?";
      } else {
        respuesta = "¡Hola! Soy tero, tu asistente pedagógico con AWS Strands Agents y Amazon Bedrock.\n" +
          "Leo las fuentes de tu carpeta, preparo propuestas pedagógicas en memoria y solo escribo cuando tú lo apruebas.";
      }
      state.messages.push({ role: "agente", text: respuesta });
    }

    paint();
  }

  async function revisePending(changeText) {
    state.phase = "pensando";
    state.messages.push({ role: "persona", text: changeText });
    state.activities = ["revisar_propuesta · aplicando ajuste docente"];
    startSpinner();
    paint();

    await wait(500);
    stopSpinner();
    state.phase = "esperando_aprobacion";
    if (state.pendiente) {
      state.pendiente.resumen += ` [Ajuste aplicado: ${changeText}]`;
      state.pendiente.vista_previa = `> Corrección docente: ${changeText}\n\n` + state.pendiente.vista_previa;
    }
    state.messages.push({
      role: "agente",
      text: `He actualizado la propuesta con tu indicación («${changeText}»). Revisa los cambios y dime si la apruebas.`,
    });
    paint();
  }

  function applyDecision(decision, note) {
    if (!state.pendiente || state.pendiente.status !== "pendiente") return;

    if (decision === "aprobar") {
      state.pendiente.status = "escrito";
      const now = new Date();
      const ts = now.toISOString().slice(0, 10).replace(/-/g, "") + "-" +
        now.toTimeString().slice(0, 8).replace(/:/g, "");
      const path = `derivados/${ts}-${state.pendiente.tipo}-${state.pendiente.accion}-9c1f2a.md`;
      state.pendiente.writtenPath = path;
      state.lastWritten = path;
      state.phase = "listo";

      putDerivado(path);
      state.messages.push({ role: "persona", text: note || "y" });
      state.messages.push({
        role: "agente",
        text: `✓ Aprobado. El host escribió el archivo en \`${path}\`.\nOriginales intactos (SHA-256 verificado).`,
      });

      const hoja = HOJAS.cuento;
      showPages(hoja, path, "El host escribió el archivo en derivados/ después de tu aprobación. Estas son sus páginas, la fotocopia para revisar.");
      $("stamp-label").textContent = "REVISAR";
      logLine(`escrito · ${state.pendiente.accion} · ${path}`, "ok");
    } else {
      state.pendiente.status = "descartado";
      state.phase = "idle";
      state.messages.push({ role: "persona", text: note || "n" });
      state.messages.push({
        role: "agente",
        text: "Descartado: no se escribió nada. La carpeta quedó igual.",
      });
      logLine("descartado · no se escribió nada");
    }

    paint();
  }

  function hitFromEvent(ev) {
    const target = $("tui-stage") || $("tui-grid");
    const grid = target.getBoundingClientRect();
    const x = Math.floor((ev.clientX - grid.left) / state.cellW);
    const y = Math.floor((ev.clientY - grid.top) / state.cellH);
    return state.hits.find((h) => x >= h.x && x < h.x + h.w && y >= h.y && y < h.y + h.h);
  }

  /* Eventos de la interfaz */
  $("tui-stage").addEventListener("click", (ev) => {
    const hit = hitFromEvent(ev);
    if (hit) {
      if (hit.action === "approve") applyDecision("aprobar", "y");
      if (hit.action === "discard") applyDecision("descartar", "n");
      return;
    }
    $("prompt").focus();
  });

  const promptInput = $("prompt");
  promptInput.addEventListener("input", () => {
    state.auto = false;
    syncPromptOverlay();
    paint();
  });

  promptInput.addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter") return;
    ev.preventDefault();
    const text = promptInput.value;
    promptInput.value = "";
    syncPromptOverlay();
    submit(text);
  });

  // Atajos globales
  document.addEventListener("keydown", (ev) => {
    const inPrompt = ev.target && ev.target.id === "prompt";
    if (ev.key === "?" && (!inPrompt || !promptInput.value)) {
      ev.preventDefault();
      state.help = !state.help;
      paint();
      return;
    }
    if (ev.key === "Escape") {
      if (state.help) {
        ev.preventDefault();
        state.help = false;
        paint();
        return;
      }
      if (!$("archivo").hidden) {
        hidePages();
        return;
      }
    }
    if (ev.key === "Tab") {
      ev.preventDefault();
      const panels = ["hilo", "propuesta", "evidencia"];
      const next = (panels.indexOf(state.focus) + 1) % panels.length;
      state.focus = panels[next];
      paint();
      return;
    }
    if (ev.key === "[" || ev.key === "]") {
      if (!inPrompt && state.pendiente && state.pendiente.evidencias && state.pendiente.evidencias.length > 1) {
        ev.preventDefault();
        const n = state.pendiente.evidencias.length;
        state.evidenceIndex = ev.key === "]" ? (state.evidenceIndex + 1) % n : (state.evidenceIndex - 1 + n) % n;
        paint();
        return;
      }
    }
    if (!inPrompt && state.pendiente && state.pendiente.status === "pendiente") {
      if (ev.key === "y" || ev.key === "Y") {
        ev.preventDefault();
        applyDecision("aprobar", "y");
        return;
      }
      if (ev.key === "n" || ev.key === "N") {
        ev.preventDefault();
        applyDecision("descartar", "n");
        return;
      }
    }
    if (ev.key === "ArrowLeft" && !$("archivo").hidden) {
      showPage(state.page - 1);
      return;
    }
    if (ev.key === "ArrowRight" && !$("archivo").hidden) {
      showPage(state.page + 1);
    }
  });

  // Botones de acciones rápidas (chips)
  document.querySelectorAll("[data-run]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const run = btn.dataset.run;
      if (run === "responder") submit("¿Qué fuentes tengo en la carpeta?");
      else if (run === "planificar") submit("Prepara una planificación de 45 minutos sobre el cuento de la carpeta.");
      else if (run === "evaluar") submit("Prepara una evaluación de comprensión lectora con pauta para 4° básico.");
      else if (run === "adaptar") submit("Adapta la evaluación del cóndor para un estudiante con dislexia.");
      else if (run === "help") {
        state.help = !state.help;
        paint();
      } else if (run === "reset") {
        submit("/clear");
      }
      promptInput.focus();
    });
  });

  document.querySelectorAll("[data-escena]").forEach((btn) => {
    btn.addEventListener("click", () => {
      submit(btn.dataset.prompt || "");
      promptInput.focus();
    });
  });

  document.querySelectorAll("[data-decision]").forEach((btn) => {
    btn.addEventListener("click", () => {
      applyDecision(btn.dataset.decision, btn.dataset.decision);
      promptInput.focus();
    });
  });

  $("hoja-prev").addEventListener("click", () => showPage(state.page - 1));
  $("hoja-next").addEventListener("click", () => showPage(state.page + 1));
  const closeBtn = $("hoja-close");
  if (closeBtn) closeBtn.addEventListener("click", hidePages);

  window.addEventListener("resize", () => paint());

  setFuentes([
    "cuento-el-condor-y-el-huemul.md",
    "bases-oa-lenguaje-4b.md",
    "notas-curso.md",
    "vocabulario-unidad.md",
  ]);
  clearDerivado();
  hidePages();

  loadFrames().finally(() => {
    paint();
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => paint()).catch(() => {});
    }
    setTimeout(() => {
      promptInput.focus();
    }, 150);
  });
})();
