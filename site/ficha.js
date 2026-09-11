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
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const speed = reduceMotion ? 0.08 : 1;
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

  /* Escenas del guion. Cada beat: lo que se teclea, el frame real que se pinta,
     la fase del protocolo y lo que pasa después de la decisión. */
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

  /* Sesión guiada: se reproduce sola y en loop. Cualquier tecla la detiene. */
  const GUION = ["responder", "crear", "descartar", "adaptar"];

  const state = {
    phase: "idle",
    frame: "home",
    escena: null,
    auto: true,
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
  };

  const HELP = `tero — conversación

Escribe abajo: «Pregunta, explora o crea…»
El agente entiende la intención y actúa:
  a) responde          b) crea material          c) edita o adapta (NEE)

Cuando propone un archivo verás qué va a hacer y la vista previa.
  y  aprobar — el host escribe en derivados/
  n  descartar — no se escribe nada
También puedes responder con tus palabras («dale»); el host clasifica.

Los avisos no bloquean la aprobación: se muestran antes de decidir.
La TUI nunca escribe archivos: escribe el host, y solo tras aprobar.

? cierra`;

  /* --- clasificador de la decisión ---------------------------------------
     Espejo acotado de `tero.approval.classify_approval` (host). Ante duda no
     se aprueba: lo desconocido vuelve a preguntar. */
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
    if (APROBAR_FIRME.test(t)) return { kind: "aprobar", note: raw };
    if (APROBAR_CORTO.test(t)) return { kind: "aprobar", note: raw };
    if (["dale no mas", "no mas", "nomas", "como no", "asi no mas", "asi nomas"].includes(phrase)) {
      return { kind: "aprobar", note: raw };
    }
    if (phrase === "hazlo asi" || phrase === "hazla asi") return { kind: "aprobar", note: raw };
    return { kind: "ambiguo", note: raw };
  }

  /* --- ruteo del mensaje a la escena más parecida ------------------------- */
  function routeScene(text) {
    const t = fold(text);
    if (/\b(adapt\w*|nee|dislex\w*|tdah|tea\b|inclusi\w*|apoyo\w*|ajust\w*)/.test(t)) {
      return "adaptar";
    }
    if (/\b(guia|sistema|ecuacion|matematic|algebra|ejercicio)/.test(t)) return "descartar";
    if (/\b(evalua\w*|prueba|pauta|cuento|lectora|comprension|planifica\w*|actividad)/.test(t)) {
      return "crear";
    }
    return "responder";
  }

  /* --- pintura ----------------------------------------------------------- */
  function measure() {
    const fitted = Tui.fitHost($("tui-host"), $("tui-grid"), GRID_COLS, state.rows);
    state.cellW = fitted.cellW;
    state.cellH = fitted.cellH;
    state.fontSize = fitted.fontSize;
  }

  function syncPromptOverlay() {
    const input = $("prompt");
    const typing = Boolean(input.value);
    input.classList.toggle("is-typing", typing);
    input.placeholder = typing ? "" : "Pregunta, explora o crea…";
    input.style.background = typing ? Tui.theme.inputBg : "transparent";
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
    $("window-path").textContent = "~/tero";
    syncPromptOverlay();
    const host = $("tui-host");
    host.style.setProperty("--cell-w", `${state.cellW}px`);
    host.style.setProperty("--cell-h", `${state.cellH}px`);
  }

  function frameData() {
    if (state.help) return frames.help || frames.home;
    return frames[state.frame] || frames.home;
  }

  function paintLive(captured) {
    measure();
    const model = liveModel();
    model.cols = GRID_COLS;
    model.rows = state.rows;
    state.model = model;
    $("tui-shot").hidden = true;
    const canvas = $("tui-canvas");
    if (canvas) canvas.hidden = true;
    $("tui-grid").classList.remove("is-shot");
    const painted = captured
      ? Tui.paintFrame($("tui-grid"), captured)
      : Tui.paint($("tui-grid"), model);
    applyPainted(
      { ...painted, cellW: state.cellW, cellH: state.cellH, fontSize: state.fontSize },
      captured && captured.name ? captured.name : "live",
      captured && captured.name === "home" ? "home" : "session",
    );
  }

  function paint() {
    const captured = frameData();
    if (captured && captured.rows) state.rows = captured.rows;
    measure();
    const host = $("tui-host");
    const grid = $("tui-grid");
    const shot = $("tui-shot");
    const stage = $("tui-stage");
    if (captured && Tui.paintShot) {
      const painted = Tui.paintShot(host, stage, shot, grid, captured);
      if (painted) {
        applyPainted(painted, captured.name, captured.name === "home" ? "home" : "session");
        return;
      }
      return;
    }
    paintLive(captured);
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

  /* Modelo solo para el respaldo en vivo: si el PNG no carga, la grilla se
     pinta con los mismos tokens, no con el flujo viejo. */
  function liveModel() {
    const pendiente = state.pendiente;
    return {
      view: state.frame === "home" ? "home" : "conversacion",
      cols: state.cols,
      rows: state.rows,
      header: `offline · ${state.phase.replace(/_/g, " ")}`,
      chips: pendiente ? ["4° básico", "Lenguaje", pendiente.tipo_label] : [],
      path: "~/tero",
      promptTitle: pendiente ? "tu decisión" : state.frame === "home" ? "pregunta" : "mensaje",
      placeholder: pendiente
        ? "y aprueba · n descarta · o escribe tu decisión…"
        : state.frame === "home"
          ? "Pregunta, explora o crea…"
          : "Escribe tu respuesta…  Enter envía",
      footer: pendiente ? "tu decisión: y aprueba · n descarta · o escribe" : "",
      thread: "Escribe lo que necesitas.\nEl agente responde, crea o adapta; tú apruebas.",
      activity: "en espera",
      proposal: pendiente
        ? `${pendiente.accion} · ${pendiente.tipo_label} — ${pendiente.titulo}\n${pendiente.resumen}\n\nvista previa · markdown\n${pendiente.vista_previa}`
        : "",
      evidence: pendiente
        ? pendiente.evidencias
            .map(
              (e, i) =>
                `${i === 0 ? "▸" : " "} ${i + 1}/${pendiente.evidencias.length}  ${e.verified ? "✓" : "?"} ${e.verified ? "en archivo" : "parafraseo"}\n  ${e.path}`,
            )
            .join("\n\n")
        : "Las citas aparecen cuando el agente propone un archivo.\n✓ en el archivo · ? parafraseo",
      warnings: pendiente && pendiente.warnings.length
        ? pendiente.warnings.map((w) => `! ${w.message}`).join("\n")
        : "sin avisos",
      gate: pendiente ? "¿escribo el archivo?   [y] aprobar   [n] descartar" : "",
      gateTitle: " aprobación ",
      help: state.help ? HELP : "",
      focus: "propuesta",
      tagline: "tus fuentes, tu criterio",
    };
  }

  /* --- hilo y archivos --------------------------------------------------- */
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
    ul.querySelectorAll("[data-file]").forEach((n) => n.remove());
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
      if (state.frame === "conversacion-streaming") paint();
    }, 90);
  }

  function stopSpinner() {
    if (state.spinnerTimer) {
      window.clearInterval(state.spinnerTimer);
      state.spinnerTimer = null;
    }
  }

  /* --- guion ------------------------------------------------------------- */
  function show(beat) {
    state.help = false;
    state.frame = beat.frame || "conversacion-streaming";
    state.phase = beat.phase || (beat.pensando ? "pensando" : state.phase);
    state.pendiente = beat.pendiente || null;
    $("gate-note").textContent = beat.nota || "";
    if (beat.nota) logLine(beat.nota);
    $("prompt").placeholder = state.pendiente
      ? "y aprueba · n descarta · o escribe tu decisión…"
      : "Pregunta, explora o crea…";
    if (beat.pensando) startSpinner();
    else stopSpinner();
    paint();
  }

  async function typeInto(text, token) {
    const input = $("prompt");
    if (reduceMotion) {
      input.value = text;
      syncPromptOverlay();
      return;
    }
    for (let i = 1; i <= text.length; i++) {
      if (token !== state.token) return;
      input.value = text.slice(0, i);
      syncPromptOverlay();
      await wait(14 + Math.random() * 22);
    }
    await wait(320);
  }

  function decideBeat(beat, decision) {
    return decision === "aprobar" ? beat.aprobar : beat.descartar;
  }

  async function runScene(id, token) {
    const escena = ESCENAS[id];
    if (!escena) return;
    state.escena = id;
    clearDerivado();
    hidePages();
    state.pendiente = null;
    if (escena.prompt) {
      await typeInto(escena.prompt, token);
      if (token !== state.token) return;
      $("prompt").value = "";
      syncPromptOverlay();
    }
    logLine(`$ ${escena.prompt}`);
    for (const beat of escena.beats) {
      if (token !== state.token) return;
      if (beat.prompt) {
        await typeInto(beat.prompt, token);
        if (token !== state.token) return;
        $("prompt").value = "";
        syncPromptOverlay();
        logLine(`$ ${beat.prompt}`);
      }
      show(beat);
      await wait(beat.hold * speed);
      if (token !== state.token) return;
      if (!beat.decision) continue;
      await typeInto(beat.decision, token);
      if (token !== state.token) return;
      $("prompt").value = "";
      syncPromptOverlay();
      const kind = classifyDecision(beat.decision);
      logLine(`decisión «${beat.decision}» → ${kind.kind}`, kind.kind);
      const next = decideBeat(beat, kind.kind);
      if (!next) return;
      show({ ...next, pendiente: null });
      if (next.archivo) {
        putDerivado(next.archivo);
        const hoja = HOJAS[next.hoja];
        showPages(hoja, next.capFile || next.archivo, next.lead, next.cap);
        $("stamp-label").textContent = "REVISAR";
        logLine(`escrito · ${next.accion} · ${next.archivo} · ${hoja.corrida}`, "ok");
      }
      await wait(next.hold * speed);
    }
  }

  async function autoplay() {
    while (state.auto) {
      for (const id of GUION) {
        if (!state.auto) return;
        const token = ++state.token;
        await runScene(id, token);
        if (token !== state.token) return;
      }
      if (!state.auto) return;
      const token = ++state.token;
      state.frame = "home";
      state.phase = "idle";
      state.pendiente = null;
      show({ frame: "home", phase: "idle" });
      await wait(2600 * speed);
      if (token !== state.token) return;
    }
  }

  /* --- decisión de la persona -------------------------------------------- */
  function applyDecision(kind, note) {
    const pendiente = state.pendiente;
    if (!pendiente) return false;
    state.auto = false;
    state.token += 1;
    stopSpinner();
    if (kind === "aprobar") {
      state.phase = "listo";
      state.frame = pendiente.accion === "crear" ? "escrito" : "escrito-adaptar";
      state.pendiente = null;
      putDerivado(pendiente.archivo);
      const hoja = HOJAS[pendiente.hoja];
      showPages(hoja, pendiente.capFile || pendiente.archivo, pendiente.lead, pendiente.cap);
      $("gate-note").textContent =
        "Aprobado. El host escribió en derivados/; la TUI no escribe archivos. El original no se tocó.";
      logLine(`decisión «${note}» → aprobar · escrito · ${pendiente.archivo}`, "ok");
      paint();
      return true;
    }
    if (kind === "descartar") {
      state.phase = "idle";
      state.frame = "descartado";
      state.pendiente = null;
      clearDerivado();
      hidePages();
      $("gate-note").textContent = "Descartado: no se escribió nada.";
      logLine(`decisión «${note}» → descartar · sin archivo`, "descartar");
      paint();
      return true;
    }
    /* cambiar / preguntar / ambiguo: la propuesta sigue pendiente. */
    $("gate-note").textContent =
      kind === "cambiar"
        ? "Anotado el cambio: la propuesta sigue pendiente hasta que decidas."
        : "No lo tomo como aprobación. La propuesta sigue pendiente: y aprueba · n descarta.";
    logLine(`decisión «${note}» → ${kind} · sigue pendiente`, kind);
    return false;
  }

  function submit(text) {
    const value = (text || "").trim();
    if (!value) return;
    if (state.pendiente) {
      const kind = classifyDecision(value);
      if (kind.kind === "aprobar" || kind.kind === "descartar") {
        applyDecision(kind.kind, value);
        return;
      }
      if (kind.kind === "cambiar") {
        $("gate-note").textContent =
          "Anotado el cambio. La propuesta sigue pendiente: y aprueba · n descarta.";
        logLine(`cambio pedido: «${value}»`, "cambiar");
        return;
      }
      $("gate-note").textContent =
        "No lo tomo como aprobación. La propuesta sigue pendiente: y aprueba · n descarta.";
      logLine(`sin decisión clara: «${value}»`, kind.kind);
      return;
    }
    playScene(routeScene(value), value);
  }

  function playScene(id, texto) {
    state.auto = false;
    const token = ++state.token;
    const escena = ESCENAS[id];
    if (texto) escena.prompt = texto;
    runScene(id, token).then(() => {
      if (token !== state.token) return;
      state.frame = "home";
      state.phase = "idle";
      show({ frame: "home", phase: "idle", nota: "escribe otra vez, o espera: la sesión sigue sola" });
      window.setTimeout(() => {
        if (token === state.token) autoplay();
      }, 3000 * speed);
    });
  }

  /* --- eventos ----------------------------------------------------------- */
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

  document.querySelectorAll("[data-escena]").forEach((btn) => {
    btn.addEventListener("click", () => playScene(btn.dataset.escena, btn.dataset.prompt || ""));
  });
  document.querySelectorAll("[data-decision]").forEach((btn) => {
    btn.addEventListener("click", () => applyDecision(btn.dataset.decision, btn.dataset.decision));
  });
  $("hoja-prev").addEventListener("click", () => showPage(state.page - 1));
  $("hoja-next").addEventListener("click", () => showPage(state.page + 1));
  $("tui-stage").addEventListener("click", (ev) => {
    const hit = hitFromEvent(ev);
    if (!hit) {
      $("prompt").focus();
      return;
    }
    if (hit.action === "approve") applyDecision("aprobar", "y");
    if (hit.action === "discard") applyDecision("descartar", "n");
  });
  $("prompt").addEventListener("input", () => {
    state.auto = false;
    syncPromptOverlay();
  });
  $("prompt").addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter") return;
    ev.preventDefault();
    const text = $("prompt").value;
    $("prompt").value = "";
    syncPromptOverlay();
    submit(text);
  });

  document.addEventListener("keydown", (ev) => {
    const inPrompt = ev.target && ev.target.id === "prompt";
    if (ev.key === "?" && (!inPrompt || !$("prompt").value)) {
      ev.preventDefault();
      help();
      return;
    }
    if (ev.key === "Escape" && state.help) {
      ev.preventDefault();
      help();
      return;
    }
    if (!inPrompt && state.pendiente && (ev.key === "y" || ev.key === "n")) {
      ev.preventDefault();
      applyDecision(ev.key === "y" ? "aprobar" : "descartar", ev.key);
      return;
    }
    if (ev.key === "ArrowLeft" && !$("archivo").hidden) {
      showPage(state.page - 1);
      return;
    }
    if (ev.key === "ArrowRight" && !$("archivo").hidden) {
      showPage(state.page + 1);
    }
  });

  window.addEventListener("resize", () => paint());

  fetch("./build-info.json")
    .then((r) => (r.ok ? r.json() : null))
    .then((info) => {
      if (info && info.short) $("window-path").dataset.sha = info.short;
    })
    .catch(() => {});

  setFuentes([
    "cuento-el-condor-y-el-huemul.md",
    "bases-oa-lenguaje-4b.md",
    "pauta-lectura.md",
    "vocabulario-algebra.md",
    "ejemplos-sistemas-resueltos.md",
  ]);
  clearDerivado();
  hidePages();

  $("tui-shot").addEventListener("load", () => paint());
  $("tui-shot").addEventListener("error", () => paintLive(frameData()));
  const start = () => {
    paint();
  };
  loadFrames().finally(() => {
    start();
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => start()).catch(() => {});
    }
    window.setTimeout(() => {
      if (state.auto) autoplay();
    }, 900);
  });
})();
