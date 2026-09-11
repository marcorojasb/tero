/* tero OpenTUI grid — paints the same rounded boxes as tui/src/shell.ts.
   Tokens copied from tui/src/theme.ts (also site/assets/tui/frames/theme.json). */
(function () {
  "use strict";

  const T = {
    bg: "#0b0d10",
    panel: "#12151a",
    panelAlt: "#161a20",
    border: "#2c333c",
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
    "         ▲",
    "        ╱│",
    " ▄▄▄▄▄ ╱(o)*",
    "█     █▄▀",
    "█ ▓▓▓▓  █",
    " ▀▄▓▓▄▄▄▀",
    "   ║   ║",
    "  ─┘   └─",
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

  function paintTo(el, screen) {
    const parts = [];
    for (let y = 0; y < screen.rows; y++) {
      parts.push('<div class="tui-row">');
      let run = "";
      let fg = "";
      let bg = "";
      const flush = () => {
        if (!run) return;
        parts.push(
          `<span style="color:${fg};background:${bg}">${run
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")}</span>`,
        );
        run = "";
      };
      for (let x = 0; x < screen.cols; x++) {
        const c = screen.cells[screen.idx(x, y)];
        if (c.fg !== fg || c.bg !== bg) {
          flush();
          fg = c.fg;
          bg = c.bg;
        }
        run += c.ch;
      }
      flush();
      parts.push("</div>");
    }
    el.innerHTML = parts.join("");
  }

  function layout(model, cols, rows) {
    const compact = cols < 100 || rows < 28;
    const chips = model.chips || [];
    const showChips = chips.length > 0 && model.view !== "home";
    const headerH = showChips ? 4 : 3;
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
    const used = headerH + promptH + footerH + gateH + planH + clarifyH;
    const midH = Math.max(6, rows - used);
    return { compact, showChips, headerH, promptH, footerH, gateH, planH, clarifyH, midH };
  }

  function drawHeader(screen, model, L) {
    const w = screen.cols;
    const path = model.path ? ` ${clip(model.path, Math.max(8, w - 8))} ` : "";
    screen.box(0, 0, w, L.headerH, {
      title: " tero ",
      bottomTitle: path,
      bg: T.panel,
      border: T.border,
      titleFg: T.brand,
    });
    screen.text(2, 1, clip(model.header || "offline · inicio", w - 4), T.text, T.panel);
    if (L.showChips) {
      const chips = (model.chips || []).map((c) => `[ ${clip(c, 22)} ]`).join("  ");
      screen.text(2, 2, clip(chips, w - 4), T.chipFg, T.panel);
    }
  }

  function drawPrompt(screen, model, L) {
    const y = screen.rows - L.footerH - L.promptH;
    const w = screen.cols;
    const title = ` ${model.promptTitle || "encargo"} `;
    const border =
      model.view === "puerta" ? T.ok : model.view === "plan" ? T.accent : T.borderFocus;
    screen.box(0, y, w, L.promptH, {
      title,
      bg: T.inputBg,
      border,
      titleFg: T.muted,
    });
    const ph = model.promptValue || model.placeholder || "Pregunta, explora o crea…";
    const color = model.promptValue ? T.text : T.faint;
    screen.text(2, y + 1, clip(ph, w - 4), color, T.inputBg);
    return { x: 2, y: y + 1, w: w - 4 };
  }

  function drawFooter(screen, model) {
    const y = screen.rows - 1;
    screen.fill(0, y, screen.cols, 1, " ", T.muted, T.bg);
    screen.text(0, y, clip(` ${model.footer || ""}`, screen.cols), T.muted, T.bg);
  }

  function drawHome(screen, model, L, hits) {
    const y0 = L.headerH;
    const midH = L.midH;
    screen.fill(0, y0, screen.cols, midH, " ", T.text, T.bg);
    const rumboLine = RUMBOS.map((r) => `[${r.key}] ${r.label}`).join("   ");
    const hints = RUMBOS.map((r) => r.hint).join(" · ");
    const homeHint = "1–4 rumbo · o escribe abajo";
    const brand = "tero";
    const tag = model.tagline || "tus fuentes, tu criterio";
    const block = L.compact ? 6 : BIRD.length + 6;
    let y = y0 + Math.max(0, Math.floor((midH - block) / 2));
    if (!L.compact) {
      for (const line of BIRD) {
        screen.text(centerX(screen.cols, line), y, line, T.accent, T.bg);
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
    const y = L.headerH;
    const h = L.midH;
    const w = screen.cols;
    const hideLeft = L.compact || model.view === "puerta";
    const leftW = hideLeft ? 0 : Math.min(26, Math.max(18, Math.floor(w * 0.19)));
    const rightW = Math.min(model.view === "puerta" ? 36 : 34, Math.max(22, Math.floor(w * 0.26)));
    const centerW = w - leftW - rightW;
    let x = 0;
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
    const y = L.headerH + (model.view === "plan" ? 0 : L.midH);
    screen.box(0, y, screen.cols, L.planH, {
      title: model.planTitle || " plan ",
      bg: T.overlay,
      border: T.accent,
      titleFg: T.accent,
    });
    screen.wrap(2, y + 1, screen.cols - 4, L.planH - 2, model.plan, T.text, T.overlay);
  }

  function drawClarify(screen, model, L) {
    if (!model.clarify) return;
    const y = L.headerH + (model.view === "plan" ? L.planH : L.midH + L.planH);
    screen.box(0, y, screen.cols, L.clarifyH, {
      title: " clarificación ",
      bg: T.overlay,
      border: T.suggested,
      titleFg: T.suggested,
    });
    screen.wrap(2, y + 1, screen.cols - 4, L.clarifyH - 2, model.clarify, T.text, T.overlay);
  }

  function drawGate(screen, model, L, hits) {
    if (!model.gate) return;
    const y = screen.rows - L.footerH - L.promptH - L.gateH;
    const border = model.view === "puerta" ? T.ok : T.accent;
    const title = model.gateTitle || (model.view === "puerta" ? " puerta " : " plan ");
    screen.box(0, y, screen.cols, L.gateH, {
      title,
      bg: T.overlay,
      border,
      titleFg: border,
    });
    screen.text(2, y + 1, clip(model.gate, screen.cols - 4), T.text, T.overlay);
    const keys = [
      { action: "gate", key: "s", token: "[s]" },
      { action: "gate", key: "n", token: "[n]" },
      { action: "gate", key: "b", token: "[b]" },
      { action: "gate", key: "c", token: "[c]" },
      { action: "approve", key: "a", token: "[a]" },
    ];
    for (const item of keys) {
      const at = model.gate.indexOf(item.token);
      if (at >= 0) hits.push({ action: item.action, key: item.key, x: 2 + at, y: y + 1, w: item.token.length + 12, h: 1 });
    }
  }

  function drawHelp(screen, model, L) {
    if (!model.help) return;
    const h = Math.min(14, L.midH);
    const y = L.headerH;
    screen.box(0, y, screen.cols, h, {
      title: " ayuda ",
      bg: T.overlay,
      border: T.accent,
      titleFg: T.accent,
    });
    screen.wrap(2, y + 1, screen.cols - 4, h - 2, model.help, T.text, T.overlay);
  }

  function paint(el, model) {
    const cols = model.cols;
    const rows = model.rows;
    const screen = new Screen(cols, rows);
    const L = layout(model, cols, rows);
    const hits = [];
    drawHeader(screen, model, L);
    if (model.help) {
      drawHelp(screen, model, L);
    } else if (model.view === "home") {
      drawHome(screen, model, L, hits);
    } else if (model.view === "plan") {
      drawPlan(screen, model, L);
      drawClarify(screen, model, L);
    } else {
      drawWorkspace(screen, model, L);
      if (model.plan && model.view === "puerta") drawPlan(screen, model, L);
    }
    drawGate(screen, model, L, hits);
    const prompt = drawPrompt(screen, model, L);
    drawFooter(screen, model);
    paintTo(el, screen);
    return { cols, rows, hits, prompt, layout: L };
  }

  window.teroTui = {
    theme: T,
    bird: BIRD,
    rumbos: RUMBOS,
    spinner: (n) => SPINNER[n % SPINNER.length],
    paint,
    clip,
  };
})();
