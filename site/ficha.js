/* Interactive photocopied ficha. Warnings never block s.
   Consultation timings are compressed; corrida real is the measured run. */
(function () {
  "use strict";

  const WARNINGS_BLOCK_S = false;
  const $ = (id) => document.getElementById(id);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const scale = reduceMotion ? 0.05 : 1;

  const state = {
    phase: "home",
    rumbo: null,
    filename: null,
    warnings: [],
    activity: "rumbos 1–4 · puerta s n b c · ? ayuda",
    token: 0,
    pages: [],
    page: 0,
    clockMs: 0,
    clockTimer: null,
    startedAt: 0,
  };

  const GRAPH_A = `
    <figure class="plano">
      <figcaption>Lectura gráfica · x + y = 4 y x = 1 se cortan en (1, 3)</figcaption>
      <svg viewBox="0 0 240 180" role="img" aria-label="Rectas x+y=4 y x=1, punto (1,3)">
        <g stroke="#d8c9a8" stroke-width="0.4" fill="none">
          <path d="M40 15 V155 M60 15 V155 M80 15 V155 M100 15 V155 M120 15 V155 M140 15 V155 M160 15 V155 M180 15 V155 M200 15 V155"/>
          <path d="M20 35 H220 M20 55 H220 M20 75 H220 M20 95 H220 M20 115 H220 M20 135 H220"/>
        </g>
        <line x1="20" y1="155" x2="228" y2="155" stroke="#1c1712" stroke-width="1.2"/>
        <line x1="20" y1="155" x2="20" y2="12" stroke="#1c1712" stroke-width="1.2"/>
        <line x1="20" y1="75" x2="100" y2="155" stroke="#1f4e79" stroke-width="2.2"/>
        <line x1="40" y1="12" x2="40" y2="155" stroke="#b42318" stroke-width="2.2"/>
        <circle cx="40" cy="95" r="3.4" fill="#1c1712"/>
        <text x="48" y="92" font-size="11" fill="#1c1712">(1,3)</text>
        <text x="104" y="150" font-size="11" fill="#1f4e79">x+y=4</text>
        <text x="46" y="22" font-size="11" fill="#b42318">x=1</text>
        <text x="222" y="168" font-size="10" fill="#1c1712">x</text>
        <text x="8" y="16" font-size="10" fill="#1c1712">y</text>
      </svg>
    </figure>`;

  const GRAPH_B = `
    <figure class="plano">
      <figcaption>x + y = 10 y x − y = 4 se cortan en (7, 3)</figcaption>
      <svg viewBox="0 0 280 210" role="img" aria-label="Rectas x+y=10 y x-y=4, punto (7,3)">
        <g stroke="#d8c9a8" stroke-width="0.4" fill="none">
          <path d="M41 20 V178 M54 20 V178 M67 20 V178 M80 20 V178 M93 20 V178 M106 20 V178 M119 20 V178 M132 20 V178 M145 20 V178 M158 20 V178 M171 20 V178 M184 20 V178"/>
          <path d="M28 35 H250 M28 48 H250 M28 61 H250 M28 74 H250 M28 87 H250 M28 100 H250 M28 113 H250 M28 126 H250 M28 139 H250 M28 152 H250 M28 165 H250"/>
        </g>
        <line x1="28" y1="178" x2="255" y2="178" stroke="#1c1712" stroke-width="1.2"/>
        <line x1="28" y1="178" x2="28" y2="18" stroke="#1c1712" stroke-width="1.2"/>
        <line x1="28" y1="48" x2="158" y2="178" stroke="#1f4e79" stroke-width="2.2"/>
        <line x1="80" y1="178" x2="184" y2="74" stroke="#b42318" stroke-width="2.2"/>
        <circle cx="119" cy="139" r="3.4" fill="#1c1712"/>
        <text x="126" y="136" font-size="11" fill="#1c1712">(7,3)</text>
        <text x="162" y="174" font-size="11" fill="#1f4e79">x+y=10</text>
        <text x="188" y="72" font-size="11" fill="#b42318">x−y=4</text>
        <text x="250" y="192" font-size="10" fill="#1c1712">x</text>
        <text x="10" y="22" font-size="10" fill="#1c1712">y</text>
      </svg>
    </figure>`;

  const rumbos = {
    1: {
      chips: "4° básico · Lenguaje · 45 min · LEN-4B-OA04",
      tipo: "planificacion",
      filename: "planificacion-condor-y-huemul.pdf",
      fuentes: ["cuento-el-condor-y-el-huemul.md", "bases-oa-lenguaje-4b.md", "pauta-lectura.md"],
      corrida: "bakeoff LaTeX · GLM 4.7 Flash · planificación 4° básico",
      elapsed: null,
      tui: "plan",
      pages: [
        "./assets/hojas/plan/p1.png",
        "./assets/hojas/plan/p2.png",
        "./assets/hojas/plan/p3.png",
      ],
      steps: [
        { tool: "list_sources", ms: 700, tui: "encargo" },
        { tool: "list_oa", ms: 550, tui: "encargo" },
        { tool: "read_source", ms: 800, detail: "cuento-el-condor-y-el-huemul.md", tui: "encargo" },
        { tool: "read_source", ms: 650, detail: "bases-oa-lenguaje-4b.md" },
        { tool: "propose_plan", ms: 2400, tui: "plan", plan: true },
        { tool: "cite_evidence", ms: 500, tui: "clarificacion" },
        { tool: "draft_artifact", ms: 3200, tui: "export", draft: true },
      ],
      plan: "45 min · extraer explícito e implícito del cuento, con cita. Inicio pregunta, desarrollo lectura guiada + parejas, cierre ticket.",
      html: `
        <h1>Planificación — El cóndor y el huemul</h1>
        <p>tero · planificación · el docente decide</p>
        <h2>Objetivo</h2>
        <p>Extraer información explícita e implícita del cuento «El cóndor y el huemul», distinguiendo lo que el texto dice de lo que el lector infiere con evidencia (LEN-4B-OA04).</p>
        <h2>Inicio</h2>
        <ul>
          <li>Pregunta: ¿qué significa que un texto nos diga algo y que nosotros podamos agregar algo más?</li>
          <li>Ancla: la niña anota dos cosas en el cuaderno de tapa azul — una escrita, otra inferida.</li>
        </ul>
        <h2>Desarrollo</h2>
        <ul>
          <li>Lectura en voz alta del cuento de la carpeta.</li>
          <li>Parejas: tres ítems (explícito / implícito / cita).</li>
        </ul>
        <h2>Cierre</h2>
        <p>Ticket: una oración con evidencia. El JSON del modelo no se imprime crudo: el host arma la ficha.</p>
        <p class="muted">Al pulsar <kbd>s</kbd> se muestran las páginas reales del bakeoff LaTeX (GLM).</p>
      `,
      warnings: [
        {
          code: "unverified_citation",
          message:
            "Hay parafraseo del cuento (fuentes/cuento-el-condor-y-el-huemul.md). No lo trates como cita literal.",
        },
      ],
    },
    2: {
      chips: "1° medio · Matemática · 90 min · sistemas 2×2",
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
      tui: "puerta_sm",
      pages: [
        "./assets/hojas/guia-sistemas/p1.png",
        "./assets/hojas/guia-sistemas/p2.png",
        "./assets/hojas/guia-sistemas/p3.png",
      ],
      steps: [
        { tool: "list_sources", ms: 720, tui: "encargo" },
        { tool: "list_oa", ms: 580, tui: "encargo" },
        { tool: "read_source", ms: 820, detail: "vocabulario-algebra.md", tui: "encargo" },
        { tool: "read_source", ms: 780, detail: "ejemplos-sistemas-resueltos.md" },
        { tool: "read_source", ms: 700, detail: "bases-oa-matematica-1m.md" },
        { tool: "propose_plan", ms: 2600, tui: "plan", plan: true },
        { tool: "cite_evidence", ms: 520, tui: "clarificacion" },
        { tool: "draft_artifact", ms: 4200, tui: "puerta_sm", draft: true },
      ],
      plan: "Guía de autoaprendizaje: sistema 2×2 como dos rectas, un punto. Sustitución + verificación. SM, V/F, desarrollo y un problema de ruedas.",
      html: `
        <h1>Guía — sistemas de ecuaciones lineales 2×2</h1>
        <p>tero · guía · 1° medio · el docente decide</p>
        <h2>Propósito</h2>
        <p>Reconocer un sistema 2×2 como <strong>dos condiciones a la vez</strong>. La solución es el <strong>punto donde se cortan dos rectas</strong>. Sustitución y verificar en ambas ecuaciones.</p>
        ${GRAPH_A}
        ${GRAPH_B}
        <h2>I. Selección múltiple</h2>
        <ol>
          <li>¿Qué es un sistema 2×2?
            <ul>
              <li>A) Una ecuación con dos incógnitas</li>
              <li>B) Dos ecuaciones lineales con las mismas dos incógnitas</li>
              <li>C) Dos ecuaciones con cuatro incógnitas</li>
              <li>D) Una ecuación de segundo grado</li>
            </ul>
          </li>
          <li>¿Cuál par es solución de x + y = 5, x − y = 1?
            <ul><li>A) (3, 2)</li><li>B) (2, 3)</li><li>C) (4, 1)</li><li>D) (5, 0)</li></ul>
          </li>
        </ol>
        <h2>II. Verdadero o falso</h2>
        <p>El par (2, 4) verifica x + y = 6. _____ · Las rectas x = 2 e y = 3 se cortan en (2, 3). _____</p>
        <h2>III. Desarrollo</h2>
        <p>Resuelve por sustitución, con despeje, ambos valores y verificación: 2x + y = 8, x − y = 1.</p>
        <h2>Aplicación</h2>
        <p>12 vehículos y 34 ruedas (moto 2, auto 4). Plantea, resuelve, verifica.</p>
        <p class="muted">Al pulsar <kbd>s</kbd> se fotocopian las tres páginas LaTeX (tablas + gráficos, sin pipes ni fences).</p>
      `,
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
      chips: "1° medio · Matemática · 45 min · sistemas 2×2",
      tipo: "evaluacion",
      filename: "evaluacion-sistemas-ecuaciones-2x2.pdf",
      fuentes: ["vocabulario-algebra.md", "ejemplos-sistemas-resueltos.md", "bases-oa-matematica-1m.md"],
      corrida: "MiniMax M2.5 · loop09 · 92.5 s · 39 tools",
      elapsed: 92.5,
      tools: 39,
      tui: "puerta",
      pages: [
        "./assets/hojas/eval-sistemas/p1.png",
        "./assets/hojas/eval-sistemas/p2.png",
        "./assets/hojas/eval-sistemas/p3.png",
      ],
      steps: [
        { tool: "list_sources", ms: 680, tui: "encargo" },
        { tool: "list_oa", ms: 540, tui: "encargo" },
        { tool: "read_source", ms: 760, detail: "vocabulario-algebra.md" },
        { tool: "read_source", ms: 740, detail: "ejemplos-sistemas-resueltos.md" },
        { tool: "propose_plan", ms: 2300, tui: "plan", plan: true },
        { tool: "cite_evidence", ms: 480, tui: "clarificacion" },
        { tool: "draft_artifact", ms: 4000, tui: "puerta_vf", draft: true },
      ],
      plan: "Evaluación corta 50 pts: SM, V/F y desarrollo (sustitución y reducción). Sin calculadora.",
      html: `
        <h1>Evaluación corta: sistemas de ecuaciones lineales 2×2</h1>
        <p>tero · prueba / evaluación · el docente decide · 50 puntos</p>
        <h2>Ítems de selección múltiple</h2>
        <ol>
          <li>¿Qué es un sistema 2×2?
            <ul>
              <li>A) Dos ecuaciones con una sola incógnita</li>
              <li>B) Dos ecuaciones lineales con dos incógnitas que deben cumplirse a la vez</li>
              <li>C) Un par de rectas que nunca se cortan</li>
              <li>D) Una ecuación con dos soluciones</li>
            </ul>
          </li>
          <li>Al resolver x + y = 10, x − y = 4, ¿cuál es la solución?
            <ul><li>A) (7, 3)</li><li>B) (3, 7)</li><li>C) (6, 4)</li><li>D) (14, −4)</li></ul>
          </li>
        </ol>
        ${GRAPH_B}
        <h2>Verdadero o falso</h2>
        <p>(2, 5) es solución de x + y = 7 y 2x − y = −1. _____ · Un sistema lineal siempre tiene exactamente una solución. _____</p>
        <h2>Desarrollo</h2>
        <p>Sustitución: 2x + y = 12, x − y = 3. Muestra pasos y verifica en ambas.</p>
        <p class="muted">Al pulsar <kbd>s</kbd> se muestran las páginas de la corrida loop09 (MiniMax, 92.5 s).</p>
      `,
      warnings: [
        {
          code: "unverified_citation",
          message:
            "1 cita(s) no aparecen textuales (fuentes/vocabulario-algebra.md). Puede ser parafraseo; no las trates como cita literal.",
        },
      ],
    },
    4: {
      chips: "4° básico · Lenguaje · 45 min · LEN-4B-OA04",
      tipo: "evaluacion",
      filename: "evaluacion-el-condor-y-el-huemul.pdf",
      fuentes: ["cuento-el-condor-y-el-huemul.md", "bases-oa-lenguaje-4b.md"],
      corrida: "GLM 4.7 Flash · loop10 · 29.1 s · 33 tools",
      elapsed: 29.1,
      tools: 33,
      tui: "puerta_desarrollo",
      pages: [
        "./assets/hojas/eval-cuento/p1.png",
        "./assets/hojas/eval-cuento/p2.png",
        "./assets/hojas/eval-cuento/p3.png",
      ],
      steps: [
        { tool: "list_sources", ms: 640, tui: "encargo" },
        { tool: "read_source", ms: 820, detail: "cuento-el-condor-y-el-huemul.md", tui: "encargo" },
        { tool: "read_source", ms: 600, detail: "bases-oa-lenguaje-4b.md" },
        { tool: "propose_plan", ms: 2000, tui: "plan", plan: true },
        { tool: "cite_evidence", ms: 450, tui: "clarificacion" },
        { tool: "draft_artifact", ms: 2800, tui: "puerta_desarrollo", draft: true },
      ],
      plan: "Prueba corta 10 pts: SM 1–4, V/F 5–6, desarrollo con cita (ítem 7). Misma carpeta del rumbo 1, otro tipo.",
      html: `
        <h1>Prueba corta — El cóndor y el huemul</h1>
        <p>tero · evaluación · 4° básico · LEN-4B-OA04 · 10 puntos</p>
        <p>Lee el cuento de la carpeta. Responde en silencio. Misma carpeta que el rumbo 1; otro tipo de artefacto.</p>
        <h2>Selección múltiple</h2>
        <ol>
          <li>¿Quién observa el mar desde la cornisa?
            <ul><li>A) El huemul</li><li>B) El cóndor</li><li>C) La niña del pueblo</li><li>D) El río</li></ul>
          </li>
          <li>¿Qué le pregunta el huemul al cóndor?
            <ul>
              <li>A) Por qué el valle se acaba</li>
              <li>B) Por qué el cóndor se ríe</li>
              <li>C) Por qué el agua se fue</li>
              <li>D) Por qué hay ramas en la vertiente</li>
            </ul>
          </li>
        </ol>
        <h2>Verdadero o falso</h2>
        <p>El cóndor responde al huemul sobre la causa del agua que se fue. _____</p>
        <p>La niña escribe que el huemul tenía menos miedo que el que vuela. _____</p>
        <h2>Desarrollo</h2>
        <p>El cóndor afirma: «Yo veo el mar desde aquí». Explica, infiere y cita el cuento.</p>
        <p class="muted">Al pulsar <kbd>s</kbd> se muestran las páginas loop10 (GLM, 29.1 s).</p>
      `,
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

  function canAccept(_warnings) {
    return true;
  }

  function setPhase(phase, activity) {
    state.phase = phase;
    if (activity) state.activity = activity;
    $("tui-phase").textContent = phase;
    $("tui-activity").textContent = state.activity;
    $("tui-model").textContent = "tero-offline";
  }

  function setStamp(label) {
    $("stamp-label").textContent = label;
    $("ficha").dataset.stamp = label;
  }

  function setTuiShot(name) {
    $("tui-shot").src = `./assets/tui/${name}.webp`;
  }

  function renderAvisos(warnings) {
    state.warnings = warnings;
    const box = $("avisos");
    const list = $("aviso-list");
    list.innerHTML = "";
    if (!warnings.length) {
      box.hidden = true;
      return;
    }
    box.hidden = false;
    for (const item of warnings) {
      const li = document.createElement("li");
      const code = document.createElement("code");
      code.textContent = item.code;
      li.appendChild(code);
      li.appendChild(document.createTextNode(" — " + item.message));
      list.appendChild(li);
    }
  }

  function setGateEnabled(on) {
    for (const btn of document.querySelectorAll("[data-gate]")) {
      btn.disabled = !on;
    }
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
    }, 100);
  }

  function stopClock() {
    if (state.clockTimer) {
      window.clearInterval(state.clockTimer);
      state.clockTimer = null;
    }
  }

  function logLine(text, kind) {
    const li = document.createElement("li");
    if (kind) li.dataset.kind = kind;
    const t = (performance.now() - state.startedAt) / 1000;
    li.textContent = `${t.toFixed(1)}s  ${text}`;
    $("bitacora").appendChild(li);
    $("bitacora").scrollTop = $("bitacora").scrollHeight;
  }

  function showPages() {
    if (!state.pages.length) return;
    $("archivo").hidden = false;
    $("cuerpo").hidden = true;
    showPage(0);
  }

  function hidePages() {
    $("archivo").hidden = true;
    $("cuerpo").hidden = false;
  }

  function showPage(i) {
    const n = state.pages.length;
    if (!n) return;
    state.page = (i + n) % n;
    $("hoja-img").src = state.pages[state.page];
    $("hoja-pos").textContent = `${state.page + 1} / ${n}`;
    $("hoja-cap").textContent = `${state.filename} · página ${state.page + 1}`;
    $("hoja-prev").disabled = n < 2;
    $("hoja-next").disabled = n < 2;
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
    document.querySelectorAll("[data-rumbo]").forEach((btn) => {
      btn.setAttribute("aria-pressed", btn.dataset.rumbo === String(key) ? "true" : "false");
    });
    $("chips").textContent = rumbo.chips;
    setStamp("REVISAR");
    resetFolders();
    hidePages();
    setFuentes(rumbo.fuentes);
    setGateEnabled(false);
    renderAvisos([]);
    $("consulta").hidden = false;
    $("bitacora").innerHTML = "";
    $("corrida-real").textContent = rumbo.corrida;
    $("cuerpo").innerHTML = "<p class='home-copy'>Leyendo la carpeta…</p>";
    $("gate-note").textContent = "Consulta en curso. La puerta espera el borrador.";
    startClock();
    setPhase("leyendo", rumbo.steps[0].tool);
    setTuiShot(rumbo.steps[0].tui || "encargo");

    for (const step of rumbo.steps) {
      if (token !== state.token) return;
      if (step.tui) setTuiShot(step.tui);
      const label = step.detail ? `${step.tool} · ${step.detail}` : step.tool;
      setPhase(step.draft ? "escribiendo" : step.plan ? "plan" : "leyendo", label);
      logLine(label, step.tool);
      if (step.plan) {
        $("cuerpo").innerHTML = `<h1>Plan</h1><p>${rumbo.plan}</p><p class="muted">Aún no hay archivo. Eso viene con draft_artifact.</p>`;
      }
      await wait(step.ms * scale);
      if (token !== state.token) return;
      if (step.draft) {
        $("cuerpo").innerHTML = rumbo.html;
        renderAvisos(rumbo.warnings);
        setGateEnabled(true);
        $("gate-note").textContent =
          "Avisos a la vista. s escribe en derivados/ y muestra las páginas reales. n descarta. b deja borrador. c pide crítica.";
        setPhase("esperando_criterio", "1 activity start por tool · espera s/n/b/c");
        setTuiShot("puerta");
        stopClock();
        const s = (performance.now() - state.startedAt) / 1000;
        $("reloj").textContent = `${s.toFixed(1)} s`;
        logLine(
          rumbo.elapsed != null
            ? `listo · reloj ${s.toFixed(1)} s · corrida real ${rumbo.elapsed} s`
            : `listo · reloj ${s.toFixed(1)} s · ${rumbo.corrida}`,
          "ok",
        );
      }
    }
  }

  function decide(letter) {
    if (state.phase !== "esperando_criterio" && letter !== "c") {
      if (state.phase === "home") {
        $("gate-note").textContent = "Primero un rumbo (1–4).";
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
      setTuiShot("export");
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
    setPhase("escribiendo", "draft_artifact (corrección)");
    window.setTimeout(() => {
      const extra = document.createElement("p");
      extra.appendChild(document.createElement("em")).textContent = "Crítica docente: ";
      extra.appendChild(document.createTextNode(note));
      $("cuerpo").appendChild(extra);
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
    }, 400 * scale);
  }

  function help() {
    $("gate-note").textContent =
      "1–4 rumbos · s sí · n no · b borrador · c corregir · avisos nunca bloquean s · modelo tero-offline";
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

  document.addEventListener("keydown", (ev) => {
    if (ev.target && (ev.target.tagName === "INPUT" || ev.target.tagName === "TEXTAREA")) return;
    if (ev.key === "?" || (ev.shiftKey && ev.key === "/")) {
      ev.preventDefault();
      help();
      return;
    }
    if (["1", "2", "3", "4"].includes(ev.key)) {
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

  const now = new Date();
  $("fecha").textContent = `Fecha: ${now.toLocaleDateString("es-CL")}`;
  setGateEnabled(false);
  setPhase("home", "rumbos 1–4 · puerta s n b c · ? ayuda");
})();
