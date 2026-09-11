/* tero OpenTUI grid — paints the same rounded boxes as tui/src/shell.ts.
   Tokens copied from tui/src/theme.ts (also site/assets/tui/frames/theme.json). */
(function () {
  "use strict";

  const T = {
    bg: "#0b0d10",
    panel: "#12151a",
    panelAlt: "#161a20",
    border: "#4c566a",
    borderFocus: "#6cb6ff",
    borderSoft: "#3d4450",
    text: "#d8dee9",
    muted: "#7a8490",
    faint: "#4b5563",
    accent: "#82aaff",
    accentSoft: "#3d5a80",
    ok: "#9ece6a",
    warn: "#c9a227",
    err: "#e06c75",
    chip: "#1a2330",
    chipFg: "#c8d6f0",
    cursor: "#82aaff",
    inputBg: "#0e1116",
    overlay: "#0f141c",
    brand: "#9aa4b2",
    suggested: "#c9a227",
    homeMuted: "#6b7380",
  };

  const BIRD = [
    "              ▲  ",
    "             ╱   ",
    "       ▄▄▄▄▄╱(•)>",
    "      █▀  ▄▄▀▀▀  ",
    "      █  ▓▓▓  █  ",
    "       ▀▄▄▄▄▄▀   ",
    "         ║  ║    ",
    "        ─┘  └─   ",
  ];

  const RUMBOS = [
    { key: "1", label: "Planificar", hint: "secuencia de clase" },
    { key: "2", label: "Crear", hint: "guía o actividad" },
    { key: "3", label: "Evaluar", hint: "prueba o pauta" },
    { key: "4", label: "Adaptar", hint: "ajustar material" },
  ];

  const SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

  const TL = "╭";
  const TR = "╮";
  const BL = "╰";
  const BR = "╯";
  const H = "─";
  const V = "│";

  function Screen(cols, rows) {
    this.cols = cols;
    this.rows = rows;
    this.cells = new Array(cols * rows);
    this.clear(T.bg, T.text);
  }

  Screen.prototype.idx = function (x, y) {
    return y * this.cols + x;
  };

  Screen.prototype.clear = function (bg, fg) {
    const n = this.cols * this.rows;
    for (let i = 0; i < n; i++) this.cells[i] = { ch: " ", fg: fg || T.text, bg: bg || T.bg };
  };

  Screen.prototype.plot = function (x, y, ch, fg, bg) {
    if (x < 0 || y < 0 || x >= this.cols || y >= this.rows) return;
    const i = this.idx(x, y);
    const prev = this.cells[i];
    this.cells[i] = {
      ch: ch == null ? " " : String(ch)[0] || " ",
      fg: fg || prev.fg,
      bg: bg || prev.bg,
    };
  };

  Screen.prototype.text = function (x, y, str, fg, bg) {
    const s = str == null ? "" : String(str);
    for (let i = 0; i < s.length; i++) this.plot(x + i, y, s[i], fg, bg);
  };

  Screen.prototype.fill = function (x, y, w, h, ch, fg, bg) {
    for (let yy = 0; yy < h; yy++) {
      for (let xx = 0; xx < w; xx++) this.plot(x + xx, y + yy, ch, fg, bg);
    }
  };

  Screen.prototype.box = function (x, y, w, h, opt) {
    opt = opt || {};
    if (w < 3 || h < 2) return;
    const border = opt.border || T.border;
    const bg = opt.bg || T.panel;
    const fg = opt.fg || T.text;
    this.fill(x, y, w, h, " ", fg, bg);
    for (let i = 0; i < w; i++) {
      this.plot(x + i, y, H, border, bg);
      this.plot(x + i, y + h - 1, H, border, bg);
    }
    for (let j = 0; j < h; j++) {
      this.plot(x, y + j, V, border, bg);
      this.plot(x + w - 1, y + j, V, border, bg);
    }
    this.plot(x, y, TL, border, bg);
    this.plot(x + w - 1, y, TR, border, bg);
    this.plot(x, y + h - 1, BL, border, bg);
    this.plot(x + w - 1, y + h - 1, BR, border, bg);
    if (opt.title) {
      const title = opt.title.length + 2 > w - 2 ? opt.title.slice(0, Math.max(0, w - 4)) : opt.title;
      this.text(x + 1, y, title, opt.titleFg || T.muted, bg);
    }
    if (opt.bottomTitle) {
      const title =
        opt.bottomTitle.length + 2 > w - 2
          ? opt.bottomTitle.slice(0, Math.max(0, w - 4))
          : opt.bottomTitle;
      this.text(x + 1, y + h - 1, title, opt.titleFg || T.muted, bg);
    }
  };

  Screen.prototype.wrap = function (x, y, w, h, str, fg, bg) {
    const text = String(str || "");
    const lines = [];
    for (const raw of text.split("\n")) {
      if (raw.length <= w) {
        lines.push(raw);
        continue;
      }
      let rest = raw;
      while (rest.length > w) {
        let cut = rest.lastIndexOf(" ", w);
        if (cut < w * 0.4) cut = w;
        lines.push(rest.slice(0, cut));
        rest = rest.slice(cut).replace(/^ /, "");
      }
      if (rest) lines.push(rest);
    }
    const n = Math.min(lines.length, h);
    for (let i = 0; i < n; i++) this.text(x, y + i, lines[i].slice(0, w), fg, bg);
    return n;
  };

  function centerX(cols, text) {
    return Math.max(0, Math.floor((cols - text.length) / 2));
  }

  function clip(text, max) {
    const t = String(text || "");
    if (t.length <= max) return t;
    return `${t.slice(0, Math.max(1, max - 1))}…`;
  }

  function escapeHtml(ch) {
    if (ch === "&") return "&amp;";
    if (ch === "<") return "&lt;";
    if (ch === ">") return "&gt;";
    return ch == null ? " " : String(ch);
  }

  function paintTo(el, screen) {
    el.classList.remove("is-shot");
    el.style.setProperty("--tui-cols", String(screen.cols));
    const parts = [];
    for (let y = 0; y < screen.rows; y++) {
      for (let x = 0; x < screen.cols; x++) {
        const c = screen.cells[screen.idx(x, y)];
        parts.push(
          `<span class="tui-cell" style="color:${c.fg};background:${c.bg}">${escapeHtml(c.ch)}</span>`,
        );
      }
    }
    el.innerHTML = parts.join("");
  }

  function layout(model, cols, rows) {
    const compact = cols < 100 || rows < 28;
    const chips = model.chips || [];
    const showChips = chips.length > 0 && model.view !== "home";
    const inset = 1;
    const headerH = showChips ? 2 : 1;
    const promptH = 3;
    const footerH = 1;
    const gateH = model.gate ? 3 : 0;
    const clarifyH = model.clarify ? (compact ? 7 : 8) : 0;
    let planH = 0;
    if (model.plan) {
      if (model.view === "plan") planH = compact ? 12 : 16;
      else if (model.view === "puerta") planH = compact ? 4 : 5;
      else planH = compact ? 8 : 11;
    }
    const used = inset * 2 + headerH + promptH + footerH + gateH + planH + clarifyH;
    const midH = Math.max(6, rows - used);
    return {
      compact,
      showChips,
      inset,
      innerX: inset,
      innerW: cols - inset * 2,
      headerH,
      promptH,
      footerH,
      gateH,
      planH,
      clarifyH,
      midH,
    };
  }

  function drawWindow(screen, model) {
    const path = model.path ? ` ${clip(model.path, Math.max(8, screen.cols - 8))} ` : "";
    screen.box(0, 0, screen.cols, screen.rows, {
      title: " tero ",
      bottomTitle: path,
      bg: T.bg,
      border: T.border,
      titleFg: T.brand,
    });
  }

  function drawHeader(screen, model, L) {
    const x = L.innerX;
    const y = L.inset;
    const w = L.innerW;
    screen.fill(x, y, w, L.headerH, " ", T.text, T.panel);
    screen.text(x + 1, y, clip(model.header || "offline · inicio", w - 2), T.text, T.panel);
    if (L.showChips) {
      const chips = (model.chips || []).map((c) => `[ ${clip(c, 22)} ]`).join("  ");
      screen.text(x + 1, y + 1, clip(chips, w - 2), T.chipFg, T.panel);
    }
  }

  function drawPrompt(screen, model, L) {
    const y = screen.rows - L.inset - L.footerH - L.promptH;
    return drawPromptAt(screen, model, y, L);
  }

  function drawFooter(screen, model, L) {
    const y = screen.rows - L.inset - 1;
    const x = L.innerX;
    screen.fill(x, y, L.innerW, 1, " ", T.muted, T.bg);
    screen.text(x, y, clip(` ${model.footer || ""}`, L.innerW), T.muted, T.bg);
  }

  function drawHome(screen, model, L, hits) {
    const y0 = L.inset + L.headerH;
    const midH = L.midH;
    screen.fill(L.innerX, y0, L.innerW, midH, " ", T.text, T.bg);
    const rumboLine = RUMBOS.map((r) => `[${r.key}] ${r.label}`).join("   ");
    const hints = RUMBOS.map((r) => r.hint).join(" · ");
    const homeHint = "1–4 rumbo · o escribe abajo";
    const brand = "tero";
    const tag = model.tagline || "tus fuentes, tu criterio";
    const block = L.compact ? 6 : BIRD.length + 6;
    let y = y0 + Math.max(0, Math.floor((midH - block) / 2));
    if (!L.compact) {
      const birdW = Math.max(...BIRD.map((line) => line.length));
      const birdX = centerX(screen.cols, " ".repeat(birdW));
      for (const line of BIRD) {
        screen.text(birdX, y, line, T.accent, T.bg);
        y += 1;
      }
    }
    screen.text(centerX(screen.cols, brand), y, brand, T.brand, T.bg);
    y += 1;
    screen.text(centerX(screen.cols, tag), y, tag, T.homeMuted, T.bg);
    y += 2;
    const rumboX = centerX(screen.cols, rumboLine);
    screen.text(rumboX, y, rumboLine, T.text, T.bg);
    let cx = rumboX;
    for (const r of RUMBOS) {
      const label = `[${r.key}] ${r.label}`;
      hits.push({ action: "rumbo", key: r.key, x: cx, y, w: label.length, h: 1 });
      cx += label.length + 3;
    }
    y += 1;
    if (!L.compact) {
      screen.text(centerX(screen.cols, hints), y, hints, T.faint, T.bg);
      y += 1;
      screen.text(centerX(screen.cols, homeHint), y, homeHint, T.faint, T.bg);
    }
  }

  function drawPanel(screen, x, y, w, h, title, body, opt) {
    opt = opt || {};
    screen.box(x, y, w, h, {
      title: ` ${title} `,
      bg: T.panel,
      border: opt.focus ? T.borderFocus : T.border,
      titleFg: opt.focus ? T.borderFocus : T.muted,
    });
    screen.wrap(x + 2, y + 1, w - 4, h - 2, body || "", opt.fg || T.text, T.panel);
  }

  function drawWorkspace(screen, model, L) {
    const y = L.inset + L.headerH;
    const h = L.midH;
    const w = L.innerW;
    const hideLeft = L.compact || model.view === "puerta";
    const leftW = hideLeft ? 0 : Math.min(26, Math.max(18, Math.floor(w * 0.19)));
    const rightW = Math.min(model.view === "puerta" ? 36 : 34, Math.max(22, Math.floor(w * 0.26)));
    const centerW = w - leftW - rightW;
    let x = L.innerX;
    if (leftW) {
      screen.box(x, y, leftW, h, {
        title: model.focus === "session" ? " ▸ sesión " : " sesión ",
        bg: T.panel,
        border: model.focus === "session" ? T.borderFocus : T.border,
        titleFg: T.muted,
      });
      const actH = Math.min(9, Math.max(4, Math.floor(h * 0.32)));
      const sessH = h - actH - 1;
      screen.wrap(
        x + 2,
        y + 1,
        leftW - 4,
        sessH - 1,
        model.session || "Sin turnos aún.\n\nHistorial:\nrumbo → plan → borrador → criterio.",
        T.text,
        T.panel,
      );
      screen.text(x + 2, y + sessH, "actividad", T.faint, T.panel);
      screen.wrap(x + 2, y + sessH + 1, leftW - 4, actH - 1, model.activity || "en espera", T.muted, T.panel);
      x += leftW;
    }
    drawPanel(
      screen,
      x,
      y,
      centerW,
      h,
      model.focus === "proposal" ? "▸ propuesta" : "propuesta",
      model.proposal || "# El agente prepara. Tú decides.\n\nElige un rumbo o escribe el encargo.",
      { focus: model.focus === "proposal" },
    );
    x += centerW;
    screen.box(x, y, rightW, h, {
      title: model.focus === "evidence" ? " ▸ evidencia " : " evidencia ",
      bg: T.panel,
      border: model.focus === "evidence" ? T.borderFocus : T.border,
      titleFg: T.muted,
    });
    const warnH = 4;
    const evidH = h - warnH - 1;
    screen.wrap(
      x + 2,
      y + 1,
      rightW - 4,
      evidH - 1,
      model.evidence || "Citas al redactar.\n[ ] recorre · ✓ archivo · ? parafraseo",
      T.text,
      T.panel,
    );
    screen.text(x + 2, y + evidH, "avisos (no bloquean)", T.faint, T.panel);
    screen.wrap(
      x + 2,
      y + evidH + 1,
      rightW - 4,
      warnH - 1,
      model.warnings || "sin avisos",
      T.warn,
      T.panel,
    );
  }

  function drawPlan(screen, model, L) {
    if (!model.plan) return;
    const y = L.inset + L.headerH + (model.view === "plan" ? 0 : L.midH);
    screen.box(L.innerX, y, L.innerW, L.planH, {
      title: model.planTitle || " plan ",
      bg: T.overlay,
      border: T.accent,
      titleFg: T.accent,
    });
    screen.wrap(L.innerX + 2, y + 1, L.innerW - 4, L.planH - 2, model.plan, T.text, T.overlay);
  }

  function drawClarify(screen, model, L) {
    if (!model.clarify) return;
    const y = L.inset + L.headerH + (model.view === "plan" ? L.planH : L.midH + L.planH);
    screen.box(L.innerX, y, L.innerW, L.clarifyH, {
      title: " clarificación ",
      bg: T.overlay,
      border: T.suggested,
      titleFg: T.suggested,
    });
    screen.wrap(L.innerX + 2, y + 1, L.innerW - 4, L.clarifyH - 2, model.clarify, T.text, T.overlay);
  }

  function drawGate(screen, model, L, hits) {
    if (!model.gate) return;
    const y = screen.rows - L.inset - L.footerH - L.promptH - L.gateH;
    const border = model.view === "puerta" ? T.ok : T.accent;
    const title = model.gateTitle || (model.view === "puerta" ? " puerta " : " plan ");
    screen.box(L.innerX, y, L.innerW, L.gateH, {
      title,
      bg: T.overlay,
      border,
      titleFg: border,
    });
    screen.text(L.innerX + 2, y + 1, clip(model.gate, L.innerW - 4), T.text, T.overlay);
    const keys = [
      { action: "gate", key: "s", token: "[s]" },
      { action: "gate", key: "n", token: "[n]" },
      { action: "gate", key: "b", token: "[b]" },
      { action: "gate", key: "c", token: "[c]" },
      { action: "approve", key: "a", token: "[a]" },
    ];
    for (const item of keys) {
      const at = model.gate.indexOf(item.token);
      if (at >= 0) {
        hits.push({
          action: item.action,
          key: item.key,
          x: L.innerX + 2 + at,
          y: y + 1,
          w: item.token.length + 12,
          h: 1,
        });
      }
    }
  }

  function drawHelp(screen, model, L) {
    if (!model.help) return;
    const h = Math.min(14, L.midH);
    const y = L.inset + L.headerH;
    screen.box(L.innerX, y, L.innerW, h, {
      title: " ayuda ",
      bg: T.overlay,
      border: T.accent,
      titleFg: T.accent,
    });
    screen.wrap(L.innerX + 2, y + 1, L.innerW - 4, h - 2, model.help, T.text, T.overlay);
  }

  function paint(el, model) {
    const cols = model.cols;
    const rows = model.rows;
    const screen = new Screen(cols, rows);
    const L = layout(model, cols, rows);
    const hits = [];
    drawWindow(screen, model);
    drawHeader(screen, model, L);
    if (model.help) {
      drawHelp(screen, model, L);
      drawGate(screen, model, L, hits);
      const prompt = drawPrompt(screen, model, L);
      drawFooter(screen, model, L);
      paintTo(el, screen);
      return { cols, rows, hits, prompt, layout: L };
    }
    if (model.view === "home") {
      drawHome(screen, model, L, hits);
      const prompt = drawPrompt(screen, model, L);
      drawFooter(screen, model, L);
      paintTo(el, screen);
      return { cols, rows, hits, prompt, layout: L };
    }
    if (model.view === "plan") {
      /* OpenTUI packs plan + gate + prompt from the top; leftover rows sit below the footer. */
      drawPlan(screen, model, L);
      drawClarify(screen, model, L);
      const yGate = L.inset + L.headerH + L.planH + (model.clarify ? L.clarifyH : 0);
      const gateH = model.gate ? 3 : 0;
      const yPrompt = yGate + gateH;
      const yFooter = yPrompt + 3;
      if (model.gate) {
        screen.box(L.innerX, yGate, L.innerW, 3, {
          title: model.gateTitle || " plan ",
          bg: T.overlay,
          border: T.accent,
          titleFg: T.accent,
        });
        screen.text(L.innerX + 2, yGate + 1, clip(model.gate, L.innerW - 4), T.text, T.overlay);
        ["s", "n", "b", "c", "a"].forEach((key) => {
          const token = `[${key}]`;
          const at = model.gate.indexOf(token);
          if (at >= 0) {
            hits.push({
              action: key === "a" ? "approve" : "gate",
              key,
              x: L.innerX + 2 + at,
              y: yGate + 1,
              w: token.length + 12,
              h: 1,
            });
          }
        });
      }
      const prompt = drawPromptAt(screen, model, yPrompt, L);
      screen.fill(L.innerX, yFooter, L.innerW, 1, " ", T.muted, T.bg);
      screen.text(L.innerX, yFooter, clip(` ${model.footer || ""}`, L.innerW), T.muted, T.bg);
      paintTo(el, screen);
      return { cols, rows, hits, prompt, layout: L };
    }
    drawWorkspace(screen, model, L);
    if (model.plan && model.view === "puerta") drawPlan(screen, model, L);
    drawGate(screen, model, L, hits);
    const prompt = drawPrompt(screen, model, L);
    drawFooter(screen, model, L);
    paintTo(el, screen);
    return { cols, rows, hits, prompt, layout: L };
  }

  function drawPromptAt(screen, model, y, L) {
    const x = L ? L.innerX : 0;
    const w = L ? L.innerW : screen.cols;
    const title = ` ${model.promptTitle || "encargo"} `;
    const border =
      model.view === "puerta" ? T.ok : model.view === "plan" ? T.accent : T.borderFocus;
    screen.box(x, y, w, 3, {
      title,
      bg: T.inputBg,
      border,
      titleFg: T.muted,
    });
    const ph = model.promptValue || model.placeholder || "Pregunta, explora o crea…";
    const color = model.promptValue ? T.text : T.faint;
    screen.text(x + 2, y + 1, clip(ph, w - 4), color, T.inputBg);
    return { x: x + 2, y: y + 1, w: w - 4 };
  }

  function cssRgba(c) {
    if (!c || !c.length) return "#000";
    const r = Math.round((c[0] <= 1 ? c[0] : c[0] / 255) * 255);
    const g = Math.round((c[1] <= 1 ? c[1] : c[1] / 255) * 255);
    const b = Math.round((c[2] <= 1 ? c[2] : c[2] / 255) * 255);
    const a = c[3] == null ? 1 : c[3];
    if (a < 0.999) return `rgba(${r},${g},${b},${a})`;
    return `#${[r, g, b].map((n) => n.toString(16).padStart(2, "0")).join("")}`;
  }

  function promptBoxFromFrame(frame) {
    const lines = String(frame.text || "").split("\n");
    const markers = ["╭─ pregunta", "╭─ encargo", "╭─ crítica", "╭─ supuesto", "╭─ responde"];
    for (let y = 0; y < lines.length; y++) {
      if (markers.some((m) => lines[y].includes(m))) {
        const line = lines[y + 1] || "";
        const start = Math.max(2, line.search(/[^\s│╭╮╰╯─]/));
        return { x: start, y: y + 1, w: Math.max(8, (frame.cols || 140) - start - 2) };
      }
    }
    const cursor = frame.cursor || [2, Math.max(0, (frame.rows || 40) - 3)];
    return { x: 2, y: cursor[1], w: Math.max(8, (frame.cols || 140) - 4) };
  }

  function paintFrame(el, frame) {
    const cols = frame.cols || 140;
    const rows = frame.lines || [];
    el.classList.remove("is-shot");
    el.style.setProperty("--tui-cols", String(cols));
    const parts = [];
    for (const line of rows) {
      let filled = 0;
      for (const span of line.spans || []) {
        const fg = cssRgba(span.fg);
        const bg = cssRgba(span.bg);
        const bold = span.attributes & 1 ? "font-weight:600;" : "";
        const chars = Array.from(String(span.text || ""));
        const width = span.width == null ? chars.length : span.width;
        if (chars.length === width) {
          for (const ch of chars) {
            parts.push(
              `<span class="tui-cell" style="color:${fg};background:${bg};${bold}">${escapeHtml(ch)}</span>`,
            );
            filled += 1;
          }
        } else {
          for (let i = 0; i < width; i++) {
            const ch = chars[i] || " ";
            parts.push(
              `<span class="tui-cell" style="color:${fg};background:${bg};${bold}">${escapeHtml(ch)}</span>`,
            );
            filled += 1;
          }
        }
      }
      while (filled < cols) {
        parts.push(`<span class="tui-cell"> </span>`);
        filled += 1;
      }
    }
    el.innerHTML = parts.join("");
    const hits = hitsFromText(frame.text || "", cols);
    return {
      cols,
      rows: frame.rows,
      hits,
      prompt: promptBoxFromFrame(frame),
      capture: true,
    };
  }

  function hitsFromText(text, cols) {
    const hits = [];
    const lines = String(text || "").split("\n");
    lines.forEach((line, y) => {
      RUMBOS.forEach((r) => {
        const token = `[${r.key}] ${r.label}`;
        const x = line.indexOf(token);
        if (x >= 0) hits.push({ action: "rumbo", key: r.key, x, y, w: token.length, h: 1 });
      });
      ["s", "n", "b", "c"].forEach((key) => {
        const token = `[${key}]`;
        const x = line.indexOf(token);
        if (x >= 0) hits.push({ action: "gate", key, x, y, w: Math.min(16, cols - x), h: 1 });
      });
    });
    return hits;
  }

  function fitHost(host, el, cols, rows) {
    const probe = document.createElement("span");
    probe.textContent = "00000000";
    probe.style.cssText =
      'position:absolute;visibility:hidden;font:10px/1.2 "JetBrains Mono", ui-monospace, monospace;white-space:pre;font-variant-ligatures:none';
    host.appendChild(probe);
    const box = probe.getBoundingClientRect();
    probe.remove();
    const ratioW = box.width / 8 / 10;
    const ratioH = box.height / 10;
    const hostBox = host.getBoundingClientRect();
    const fs = Math.max(
      8,
      Math.floor(
        Math.min(hostBox.width / (cols * ratioW), hostBox.height / (rows * ratioH)) * 0.992,
      ),
    );
    const cellW = fs * ratioW;
    const cellH = fs * ratioH;
    el.style.fontSize = `${fs}px`;
    el.style.lineHeight = "1.2";
    el.style.setProperty("--tui-cols", String(cols));
    el.style.setProperty("--cell-w", `${cellW}px`);
    el.style.setProperty("--cell-h", `${cellH}px`);
    return { cellW, cellH, fontSize: fs, cols, rows };
  }

  function viewportBudget() {
    /* Reserve only body padding. There is no second titlebar. */
    const styles = getComputedStyle(document.body);
    const padX =
      (parseFloat(styles.paddingLeft) || 0) + (parseFloat(styles.paddingRight) || 0);
    const padY =
      (parseFloat(styles.paddingTop) || 0) + (parseFloat(styles.paddingBottom) || 0);
    return {
      maxW: Math.max(280, window.innerWidth - padX),
      maxH: Math.max(240, window.innerHeight - padY),
    };
  }

  function fitShot(host, img, cols, rows) {
    const nw = img.naturalWidth || cols * 10;
    const nh = img.naturalHeight || rows * 24;
    const { maxW, maxH } = viewportBudget();
    let scale = Math.min(maxW / nw, maxH / nh, 1);
    const width = Math.max(1, Math.round(nw * scale));
    const height = Math.max(1, Math.round(nh * scale));
    img.style.width = `${width}px`;
    img.style.height = `${height}px`;
    img.style.imageRendering = scale >= 0.999 ? "pixelated" : "auto";
    return {
      cellW: width / cols,
      cellH: height / rows,
      fontSize: (height / rows) * 0.7,
      cols,
      rows,
      width,
      height,
      scale,
    };
  }

  function blitCanvas(img, canvas, fitted) {
    if (!canvas || !img || img.naturalWidth < 8) return;
    const nw = img.naturalWidth;
    const nh = img.naturalHeight;
    if (canvas.width !== nw) canvas.width = nw;
    if (canvas.height !== nh) canvas.height = nh;
    canvas.style.width = `${fitted.width}px`;
    canvas.style.height = `${fitted.height}px`;
    canvas.style.imageRendering = fitted.scale >= 0.999 ? "pixelated" : "auto";
    canvas.hidden = false;
    img.hidden = true;
    const ctx = canvas.getContext("2d", { alpha: false });
    if (!ctx) return;
    ctx.imageSmoothingEnabled = fitted.scale < 0.999;
    ctx.drawImage(img, 0, 0, nw, nh);
    if (typeof createImageBitmap !== "function") return;
    createImageBitmap(img, { colorSpaceConversion: "none", premultiplyAlpha: "none" })
      .then((bmp) => {
        if (canvas.width !== nw || canvas.height !== nh) return;
        ctx.imageSmoothingEnabled = fitted.scale < 0.999;
        ctx.drawImage(bmp, 0, 0, nw, nh);
        if (bmp.close) bmp.close();
      })
      .catch(() => {});
  }

  function paintShot(host, stage, img, overlay, frame) {
    if (!frame || !frame.name) return null;
    const url = `./assets/tui/frames/${frame.name}.png?v=ave`;
    if (img.getAttribute("src") !== url) {
      img.alt = `OpenTUI · ${frame.name}`;
      img.src = url;
    }
    if (!img.complete || img.naturalWidth < 8) return null;
    const fitted = fitShot(host, img, frame.cols || 140, frame.rows || 40);
    const canvas = document.getElementById("tui-canvas");
    if (canvas) blitCanvas(img, canvas, fitted);
    else img.hidden = false;
    stage.style.width = `${fitted.width}px`;
    stage.style.height = `${fitted.height}px`;
    overlay.classList.add("is-shot");
    overlay.innerHTML = "";
    overlay.style.width = "100%";
    overlay.style.height = "100%";
    overlay.style.setProperty("--cell-w", `${fitted.cellW}px`);
    overlay.style.setProperty("--cell-h", `${fitted.cellH}px`);
    host.style.setProperty("--cell-w", `${fitted.cellW}px`);
    host.style.setProperty("--cell-h", `${fitted.cellH}px`);
    return {
      cols: frame.cols,
      rows: frame.rows,
      hits: hitsFromText(frame.text || "", frame.cols),
      prompt: promptBoxFromFrame(frame),
      capture: true,
      shot: true,
      cellW: fitted.cellW,
      cellH: fitted.cellH,
      fontSize: fitted.fontSize,
    };
  }

  window.teroTui = {
    theme: T,
    bird: BIRD,
    rumbos: RUMBOS,
    spinner: (n) => SPINNER[n % SPINNER.length],
    paint,
    paintFrame,
    paintShot,
    blitCanvas,
    promptBoxFromFrame,
    hitsFromText,
    fitHost,
    fitShot,
    clip,
  };
})();
