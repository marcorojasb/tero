/* tero wave — Terminal UI Brand System v1.0
   Grammar: dots, squares, blocks, plus, curves. Seeded so each deploy
   shifts the ribbon a little (build-info.json) without leaving the system. */
(function () {
  "use strict";

  const DEFAULT_BRAND = {
    seed: 77,
    palette: {
      crema: "#F4F1DE",
      cian: "#22D3EE",
      aqua: "#20D4BF",
      teal: "#14B8A6",
      menta: "#86EFAC",
      lima: "#A3E635",
      fondo: "#070B0C",
    },
  };

  function mulberry32(a) {
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function hexToRgb(hex) {
    const n = parseInt(hex.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function mix(c1, c2, t) {
    return [
      Math.round(lerp(c1[0], c2[0], t)),
      Math.round(lerp(c1[1], c2[1], t)),
      Math.round(lerp(c1[2], c2[2], t)),
    ];
  }

  function rgba(rgb, a) {
    return `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`;
  }

  function hash32(i, j, seed) {
    let h = (i * 374761393 + j * 668265263 + seed * 1013904223) | 0;
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  }

  function alongColor(p, t) {
    const lima = hexToRgb(p.lima);
    const menta = hexToRgb(p.menta);
    const teal = hexToRgb(p.teal);
    const aqua = hexToRgb(p.aqua);
    const cian = hexToRgb(p.cian);
    if (t < 0.25) return mix(lima, menta, t / 0.25);
    if (t < 0.5) return mix(menta, teal, (t - 0.25) / 0.25);
    if (t < 0.75) return mix(teal, aqua, (t - 0.5) / 0.25);
    return mix(aqua, cian, (t - 0.75) / 0.25);
  }

  function pointOnRibbon(u, lane, lanes, time, twist) {
    const v = lane / (lanes - 1) - 0.5;
    const wave = Math.sin(u * Math.PI * 1.7 + time * 0.32 + twist);
    const x = 0.04 + u * 0.94;
    const y = 0.78 - u * 0.58 + wave * 0.13 + v * (0.038 + u * 0.028);
    return { x, y, v, u };
  }

  function drawPlus(ctx, x, y, s, color) {
    ctx.fillStyle = color;
    ctx.fillRect(x - s, y - s * 0.22, s * 2, s * 0.44);
    ctx.fillRect(x - s * 0.22, y - s, s * 0.44, s * 2);
  }

  function drawBlock(ctx, x, y, s, color) {
    ctx.fillStyle = color;
    const r = Math.min(2.2, s * 0.18);
    ctx.beginPath();
    ctx.roundRect(x - s / 2, y - s / 2, s, s, r);
    ctx.fill();
  }

  function paint(ctx, w, h, time, brand, compact) {
    const p = brand.palette;
    ctx.fillStyle = p.fondo;
    ctx.fillRect(0, 0, w, h);

    const lanes = compact ? 7 : 12;
    const steps = compact ? 90 : 210;
    const seed = brand.seed | 0;

    for (let lane = 0; lane < lanes; lane++) {
      for (let i = 0; i < steps; i++) {
        const u = i / (steps - 1);
        const pt = pointOnRibbon(u, lane, lanes, time, seed * 0.017);
        const x = pt.x * w;
        const y = pt.y * h;
        const dist = Math.abs(pt.v);
        const core = Math.max(0, 1 - dist * 3.1);
        const mid = Math.sin(u * Math.PI);
        const rgb = alongColor(p, u);
        const alpha = 0.22 + core * 0.78;
        const color = rgba(rgb, alpha);
        const roll = hash32(i, lane, seed);
        const size = (compact ? 2.2 : 3.4) + core * mid * (compact ? 7 : 12);

        if (core > 0.55 && roll > 0.74) {
          ctx.save();
          ctx.shadowColor = rgba(rgb, 0.45);
          ctx.shadowBlur = compact ? 4 : 8;
          drawBlock(ctx, x, y, size, color);
          ctx.restore();
        } else if (roll > 0.93) {
          drawPlus(ctx, x, y, 2.2 + core * 3.2, rgba(rgb, 0.55 + core * 0.4));
        } else {
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(x, y, 0.55 + (1 - dist) * (compact ? 1.3 : 2.1), 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    const extras = compact ? 40 : 110;
    const rng = mulberry32(seed ^ 0x9e3779b9);
    for (let k = 0; k < extras; k++) {
      const u = rng();
      const lane = rng() * lanes;
      const pt = pointOnRibbon(u, lane, lanes, time * 0.7, seed * 0.017);
      const jitter = (rng() - 0.5) * 0.06;
      const x = pt.x * w;
      const y = (pt.y + jitter) * h;
      const rgb = alongColor(p, u);
      if (rng() > 0.7) {
        drawPlus(ctx, x, y, 1.6 + rng() * 2.2, rgba(rgb, 0.35));
      } else {
        ctx.fillStyle = rgba(rgb, 0.28);
        ctx.beginPath();
        ctx.arc(x, y, 0.5 + rng() * 1.2, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  async function loadJSON(url, fallback) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) return fallback;
      return await res.json();
    } catch {
      return fallback;
    }
  }

  function mount(canvas, opts) {
    const compact = Boolean(opts && opts.compact);
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const ctx = canvas.getContext("2d");
    if (!ctx) return () => {};
    if (typeof ctx.roundRect !== "function") {
      ctx.roundRect = function (x, y, w, h) {
        this.rect(x, y, w, h);
      };
    }

    let brand = DEFAULT_BRAND;
    let raf = 0;
    let start = performance.now();
    let running = true;

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const rect = canvas.getBoundingClientRect();
      const w = Math.max(1, Math.floor(rect.width * dpr));
      const h = Math.max(1, Math.floor(rect.height * dpr));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
      return { w, h };
    }

    function frame(now) {
      if (!running) return;
      const { w, h } = resize();
      const t = reduce ? 0 : (now - start) / 1000;
      paint(ctx, w, h, t, brand, compact);
      if (!reduce) raf = window.requestAnimationFrame(frame);
    }

    function onVis() {
      if (document.hidden) {
        window.cancelAnimationFrame(raf);
      } else if (!reduce) {
        start = performance.now();
        raf = window.requestAnimationFrame(frame);
      }
    }

    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("resize", () => frame(performance.now()));

    Promise.all([loadJSON("./brand.json", DEFAULT_BRAND), loadJSON("./build-info.json", null)]).then(
      ([b, info]) => {
        brand = {
          ...DEFAULT_BRAND,
          ...b,
          palette: { ...DEFAULT_BRAND.palette, ...(b.palette || {}) },
        };
        if (info && info.short) {
          let n = 0;
          for (let i = 0; i < info.short.length; i++) n = (n * 33 + info.short.charCodeAt(i)) | 0;
          brand.seed = ((brand.seed || 77) ^ (n >>> 0)) | 0;
          const el = document.getElementById("deploy-sha");
          if (el) el.textContent = `${info.short} · ${info.date || ""} · ${info.source || ""}`.trim();
        }
        frame(performance.now());
      },
    );

    frame(performance.now());
    return function destroy() {
      running = false;
      window.cancelAnimationFrame(raf);
      document.removeEventListener("visibilitychange", onVis);
    };
  }

  window.teroWave = { mount };
})();
