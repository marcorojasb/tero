/* Interactive photocopied ficha. Warnings never block s. */
(function () {
  "use strict";

  const WARNINGS_BLOCK_S = false;

  const $ = (id) => document.getElementById(id);

  const state = {
    phase: "home",
    rumbo: null,
    filename: null,
    warnings: [],
    activity: "rumbos 1–4 · puerta s n b c · ? ayuda",
  };

  const rumbos = {
    1: {
      chips: "5° básico · Ciencias Naturales · 90 min · CIE-5B-OA06",
      tipo: "planificacion",
      filename: "planificacion-el-agua-en-el-planeta.md",
      title: "El agua en el planeta: ¿tanta agua y tan poca para usar?",
      html: `
        <h1>El agua en el planeta: ¿tanta agua y tan poca para usar?</h1>
        <p>tero · planificación · el docente decide</p>
        <h2>Objetivo</h2>
        <p>Que las y los estudiantes expliquen con un ejemplo chileno por qué «hay mucha agua en el planeta» no significa «hay agua dulce fácil de usar».</p>
        <h2>Inicio</h2>
        <ul>
          <li>Pregunta en la pizarra: ¿de dónde viene el agua del grifo de tu casa?</li>
          <li>Anclar a sequía en zona central (p. ej. Petorca) y al agua como bien crítico en el norte.</li>
        </ul>
        <h2>Desarrollo</h2>
        <ul>
          <li>Vaso con agua, después con sal: ¿sigue siendo la misma?</li>
          <li>Lectura guiada de las fuentes de la carpeta (OA + contexto Chile).</li>
        </ul>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Tipo</th><th>Ejemplo en Chile</th><th>¿Salada o dulce?</th></tr></thead>
            <tbody>
              <tr><td>Océano</td><td>Pacífico</td><td>Salada</td></tr>
              <tr><td>Río</td><td>________</td><td>Dulce</td></tr>
              <tr><td>Glaciar</td><td>________</td><td>Dulce</td></tr>
            </tbody>
          </table>
        </div>
        <h2>Cierre</h2>
        <p>Una oración con evidencia: mucha agua ≠ agua dulce fácil de usar.</p>
      `,
      warnings: [
        {
          code: "unverified_citation",
          message:
            "2 cita(s) no aparecen textuales (fuentes/03-contexto-chile.md). Puede ser parafraseo; no las trates como cita literal.",
        },
      ],
    },
    2: {
      chips: "2° medio · Historia y Geografía · 45 min · cabildo 1810",
      tipo: "guia",
      filename: "guia-cabildo-1810-dos-voces.md",
      title: "Cabildo 1810, dos voces",
      html: `
        <h1>Guía — cabildo 1810, dos voces</h1>
        <p>Nombre / Fecha en el encabezado. tero · guía de trabajo.</p>
        <h2>Propósito</h2>
        <p>Analizar dos voces del cabildo de 1810 (acta formal y voz de vecino): quién tiene voz y quién queda fuera.</p>
        <h2>Instrucciones</h2>
        <ol>
          <li>Lee el fragmento del acta y la hoja de prensa de la carpeta.</li>
          <li>Completa el análisis comparativo.</li>
          <li>Ticket de salida: una cita de cada voz.</li>
        </ol>
        <h2>Cierre</h2>
        <p>Entrega escrita con una cita de cada fuente. El JSON del modelo no se imprime crudo: el host lo arma como ficha.</p>
      `,
      warnings: [
        {
          code: "unverified_citation",
          message:
            "1 cita no aparece textual (fuentes/02-apuntes-docente.md). Puede ser parafraseo.",
        },
      ],
    },
    3: {
      chips: "4° básico · Lenguaje · 45 min · LEN-4B-OA04",
      tipo: "evaluacion",
      filename: "evaluacion-el-condor-y-el-huemul.md",
      title: "Evaluación — el cóndor y el huemul",
      html: `
        <h1>Evaluación — el cóndor y el huemul</h1>
        <p>Lee el cuento de la carpeta. Responde en silencio.</p>
        <h2>Ítem I · Selección múltiple</h2>
        <ol>
          <li>¿Por qué el valle tenía sed, según el huemul?
            <ul>
              <li>a) Porque el cóndor se bebió el río</li>
              <li>b) Porque nadie preguntó a las fuentes</li>
              <li>c) Porque siempre fue así</li>
            </ul>
          </li>
        </ol>
        <h2>Ítem II · Verdadero / falso</h2>
        <p>El huemul corre sin preguntar. _____</p>
        <h2>Desarrollo</h2>
        <p>Con una cita del cuento, explicá una decisión del personaje.</p>
      `,
      warnings: [
        {
          code: "thin_evidence",
          message: "Menos de dos fuentes citadas. El panel de evidencia quedará pobre.",
        },
        {
          code: "unverified_citation",
          message: "La cita del ítem I es parafraseo. Marcada ? , no ✓.",
        },
      ],
    },
    4: {
      chips: "4° básico · Ciencias Naturales · 45 min · adaptar",
      tipo: "actividad",
      filename: "actividad-agua-4b.md",
      title: "Adaptar — el agua, un curso más abajo",
      html: `
        <h1>Actividad — el agua, un curso más abajo</h1>
        <p>Mismo material de la carpeta, otro curso. tero no inventa un OA de 5° para rellenar 4° si el catálogo no cubre: avisa.</p>
        <h2>Pasos</h2>
        <ol>
          <li>Dibuja en el cuaderno: mar, río, glaciar.</li>
          <li>Marca cuál se puede tomar (con ayuda del o la docente).</li>
          <li>Una frase: «en Chile el agua dulce no es toda el agua que se ve».</li>
        </ol>
      `,
      warnings: [
        {
          code: "tipo_desviado",
          message:
            "El rumbo pedía actividad y el modelo a veces llega con pauta. El plan no se pisa: tú decides s o c.",
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
      li.innerHTML = `<code>${item.code}</code> — ${item.message}`;
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

  function prepare(key) {
    const rumbo = rumbos[key];
    if (!rumbo) return;
    state.rumbo = key;
    state.filename = rumbo.filename;
    document.querySelectorAll("[data-rumbo]").forEach((btn) => {
      btn.setAttribute("aria-pressed", btn.dataset.rumbo === String(key) ? "true" : "false");
    });
    $("chips").textContent = rumbo.chips;
    setStamp("REVISAR");
    resetFolders();
    setPhase("leyendo", "list_sources");
    window.setTimeout(() => {
      setPhase("leyendo", "read_source");
    }, 180);
    window.setTimeout(() => {
      setPhase("escribiendo", "draft_artifact");
    }, 360);
    window.setTimeout(() => {
      $("cuerpo").innerHTML = rumbo.html;
      renderAvisos(rumbo.warnings);
      setGateEnabled(true);
      $("gate-note").textContent =
        "Avisos a la vista. s escribe en derivados/ aunque haya parafraseo. n descarta. b deja borrador. c pide crítica.";
      setPhase("esperando_criterio", "1 activity start por tool · esperá s/n/b/c");
    }, 520);
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
      $("gate-note").textContent =
        "Aceptado. El original no se tocó. Hash de fuentes intacto. El --yes del demo hace esto mismo.";
      setGateEnabled(false);
      setPhase("listo", "s → derivados/");
      return;
    }
    if (letter === "n") {
      resetFolders();
      setStamp("DESCARTADO");
      $("gate-note").textContent = "Descartado. No quedó archivo.";
      setGateEnabled(false);
      setPhase("listo", "n → nada en disco");
      return;
    }
    if (letter === "b") {
      putFile("borradores", state.filename);
      setStamp("BORRADOR");
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
    setPhase("escribiendo", "draft_artifact (corrección)");
    window.setTimeout(() => {
      const extra = document.createElement("p");
      extra.innerHTML = `<em>Crítica docente:</em> ${note}`;
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
    }, 400);
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
