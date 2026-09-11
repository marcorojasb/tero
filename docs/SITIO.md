# Site — the real TUI, in one window

The chrome of [`site/`](../site/) **is tero's OpenTUI**: a PNG captured from
`xfce4-terminal` at 140×40 (JetBrains Mono 13). There is no second titlebar
around it. The root box `╭─ tero ─╮` wraps the home screen and the session; the
folder is shown on the bottom border. Colors come from `tui/src/theme.ts`
(`#0b0d10`, accent `#82aaff`).

The first view **is** the TUI home: the southern lapwing (*queltehue*), the brand
and `Pregunta, explora o crea…` (the UI stays Spanish — it is the product).
Typing does not change windows: it only paints the next frame. Authentic captures
live in [`site/assets/tui/frames/`](../site/assets/tui/frames/) and are
regenerated with `cd tui && bun run capture` (JSON + rasterized PNG) or, with a
display, `bun run capture:live` (xfce4-terminal 140×40, JetBrains Mono 13). The
landing blits those PNGs at 1×.

Hyperrealistic paper — toner grain, photocopied worksheet, `REVISAR` stamp — is
used **only** for the pages the host writes (`#archivo` / `.hoja-frame`), after
approval.

## The session is conversational

See [CONVERSACIONAL.md](CONVERSACIONAL.md). The person writes and the agent infers
the intent: **a)** answer, **b)** create, **c)** edit or adapt (including special
education). When it proposes a file it shows what it will do (`resumen` label),
the preview, the evidence (`✓` found in the file, `?` paraphrase) and the
warnings, which **never block**. Approval is `y` or simply typing in the thread
(*"dale"*); `n` discards. The TUI **never writes files**: the host writes, into
`derivados/`, and only after approval. The demo model is `tero-offline`.
AgentCore is not the product.

## What the session looks like

`site/ficha.js` simulates scenes in a loop and stops as soon as someone types:

- **a) answer**: *"¿Qué tengo en la carpeta?"* → the agent replies; there is no
  card and nothing to approve.
- **b) create**: an assessment for 4th grade. The agent asks in natural language
  for what it is missing, proposes the assessment with a preview and evidence, and
  waits. Approving with *dale* makes the **photocopied sheet** from `derivados/`
  appear.
- **b) discard**: a guide that is answered with `n`: nothing is written.
- **c) adapt (NEE)**: the same assessment adapted for a student with dyslexia. The
  card shows `acción: adaptar`, the `origen`, the `cambios` and the **NEE supports
  and criteria** (Decreto 83 vocabulary). On approval the host writes a new
  version: the source material is untouched.
- The **real LaTeX pages** appear at the end, with the run that produced them. `n`
  publishes no sheets.
- An `unknown_source` warning **does not block** approval. See
  [PUERTA-Y-PR8.md](PUERTA-Y-PR8.md).

## Virtualizing tero (OSS) so it keeps itself updated

| Piece | What it does |
| --- | --- |
| `site/tui-grid.js` | Fits the captured PNG (or paints cells if it is missing). |
| `site/ficha.js` | Conversational session (scenes, proposal, approval, sheet). |
| `tui/scripts/capture-frames.ts` | Dumps OpenTUI frames (`createTestRenderer` + `captureSpans`). |
| `tui/scripts/rasterize-frames.py` | JetBrains PNGs when there is no display. |
| `tui/scripts/screenshot-frames.py` | PNGs of the real terminal, height per frame. |
| `tui/scripts/compose-og.py` | GitHub OG image from the captured home. |
| `site/assets/tui/frames/` | Home, response, conversation, proposal (create and adapt), written, discarded. |
| `site/stamp.py` | On every Pages deploy it writes the SHA into `build-info.json`. |
| `.github/workflows/pages.yml` | Publishes `site/` from `main`. |

Other MIT projects, in case WASM or CI recording becomes interesting later:

- [charmbracelet/vhs](https://github.com/charmbracelet/vhs) — tapes that CI re-records.
- [opentui-web](https://github.com/rbbydotdev/opentui-web) — OpenTUI to WASM. Heavy; not the product.
- [xterm.js](https://xtermjs.org) — if the JSONL bridge is ever streamed.

No Electron, no Python runtime in the browser. The folder and `--offline` remain
the judge.

## GitHub Pages

URL: `https://marcorojasb.github.io/tero/`.

Source in Settings is **GitHub Actions**. `.github/workflows/pages.yml` publishes
`site/` from `main`. The Actions token can publish but cannot create the site
(`403 Resource not accessible by integration`), so the workflow preflights
`GET /pages` and, on 404, warns instead of failing. Fallback:
[Settings → Pages](https://github.com/marcorojasb/tero/settings/pages).

A push to `main` that touches `site/` or the workflow triggers the deploy.

Local preview (404.html and stamp included):

```bash
python3 site/serve.py
# open http://127.0.0.1:4173/
```

## Judge-facing layer

The terminal stays Spanish, but the page carries an English strip (`#judge-legend`,
`lang="en"`) explaining what an evaluator is looking at: the three intents, that
nothing is written until approval, and where the source and judge guide live.
`tui-grid.js` reserves its height in `viewportBudget()` so it never covers the TUI.
The document head (`<title>`, `description`, Open Graph) is also English.

## What it is not

Not Electron, TipTap, Meridian, Biblioteca, nor an AgentCore dashboard. There is no
"Get started free" CTA. The brand is **tero** (*queltehue* + OpenTUI) and the
tagline is **tus fuentes, tu criterio**.
