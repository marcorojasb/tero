# Sitio — la TUI real, en una ventana

El chrome de [`site/`](../site/) es **la OpenTUI de tero**, virtualizada
en el navegador. Una sola ventana (`traffic` + título `tero`) envuelve
el mismo layout que `tui/src/shell.ts`: header `╭─ tero ─╮`, home con
queltehue y rumbos, workspace `sesión` / `propuesta` / `evidencia`,
puerta `s` / `n` / `b` / `c`, prompt y footer. Los colores salen de
`tui/src/theme.ts` (`#0b0d10`, accent `#82aaff`).

La primera vista **es** el home de la TUI. Un rumbo no cambia de ventana:
solo pinta el cuerpo. Capturas auténticas (test renderer de OpenTUI) viven
en [`site/assets/tui/frames/`](../site/assets/tui/frames/). Se regeneran
con `cd tui && bun run capture`.

El papel hiperrealista —grano de tóner, ficha fotocopiada— queda
**solo** en las páginas que tero crea (`#archivo` / `.hoja-frame`),
después de `s` o `b`.

Rumbos `1–4`, avisos a la vista, puerta `s` / `n` / `b` / `c`. El modelo
de la demo es `tero-offline`. AgentCore no es el producto.

## Cómo se ve

- Home: queltehue, `tus fuentes, tu criterio`, `[1] Planificar` … `[4] Adaptar`.
- Un rumbo dispara `list_sources` → `draft_artifact` en los paneles.
  Al lado, el tiempo de la corrida real (MiniMax 92.5 s / 94.9 s, GLM 29.1 s).
- Las **páginas LaTeX reales** salen al final, con `s` o `b`. `n` no
  publica hojas.
- Un aviso `unverified_citation` **no bloquea** `s`. Ver
  [PUERTA-Y-PR8.md](PUERTA-Y-PR8.md).

## Virtualizar tero (OSS) y que se actualice solo

| Pieza | Qué hace |
| --- | --- |
| `site/tui-grid.js` | Pinta cajas `╭╮` y tokens de la TUI real. |
| `site/ficha.js` | Consulta (rumbos, reloj, puerta) sobre esa grilla. |
| `tui/scripts/capture-frames.ts` | Vuelca frames OpenTUI (`createTestRenderer` + `captureSpans`). |
| `site/assets/tui/frames/` | Home, leyendo, plan y puerta por rumbo 1–4, capturados del renderer OpenTUI. |
| `site/stamp.py` | En cada Pages deploy escribe el SHA en `build-info.json`. |
| `.github/workflows/pages.yml` | Publica `site/` desde `main`. |

Otros proyectos MIT, por si más adelante queremos WASM / grabación CI:

- [charmbracelet/vhs](https://github.com/charmbracelet/vhs) — tapes que CI vuelve a grabar.
- [opentui-web](https://github.com/rbbydotdev/opentui-web) — OpenTUI a WASM. Pesado; no es el producto.
- [xterm.js](https://xtermjs.org) — si algún día se transmite el bridge JSONL.

No metemos Electron, ni un runtime Python en el browser. La carpeta y
`--offline` siguen siendo el juez.

## GitHub Pages

URL: `https://marcorojasb.github.io/tero/`.

Source en Settings es **GitHub Actions**. `.github/workflows/pages.yml`
publica `site/` desde `main`. El token de Actions puede publicar, pero
no crear el sitio (`403 Resource not accessible by integration`); por
eso el workflow hace preflight `GET /pages` y si 404, avisa y no falla.
Fallback: [Settings → Pages](https://github.com/marcorojasb/tero/settings/pages).

Un push a `main` que toque `site/` o el workflow dispara el deploy.

Vista previa local (404.html y stamp incluidos):

```bash
python3 site/serve.py
# abrir http://127.0.0.1:4173/
```

## Qué no es

No es Electron, TipTap, Meridian, Biblioteca ni un dashboard de
AgentCore. No hay CTA de “Get started free”. La marca es **tero**
(queltehue + OpenTUI) y el tagline **tus fuentes, tu criterio**.
