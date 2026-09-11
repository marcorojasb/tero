# Sitio — la TUI real, en una ventana

El chrome de [`site/`](../site/) **es la OpenTUI de tero**: el PNG
capturado de `xfce4-terminal` 140×40 (JetBrains Mono 13). No hay un
segundo titlebar alrededor. El recuadro raíz `╭─ tero ─╮` envuelve
home y sesión; la carpeta va en el borde inferior. Colores de
`tui/src/theme.ts` (`#0b0d10`, accent `#82aaff`).

La primera vista **es** el home de la TUI: el queltehue, la marca y
`Pregunta, explora o crea…`. Escribir no cambia de ventana: solo pinta el
frame siguiente. Capturas auténticas viven en
[`site/assets/tui/frames/`](../site/assets/tui/frames/). Se regeneran
con `cd tui && bun run capture` (JSON + PNG raster) y, con display,
`bun run capture:live` (captura xfce4-terminal 140×40, JetBrains Mono 13).
El landing blitea esos PNG a 1×.

El papel hiperrealista —grano de tóner, ficha fotocopiada, sello
`REVISAR`— queda **solo** en las páginas que el host escribe
(`#archivo` / `.hoja-frame`), después de aprobar.

La sesión es **conversacional**
([CONVERSACIONAL.md](CONVERSACIONAL.md)): la persona escribe y el agente
infiere la intención —a) responder, b) crear, c) editar o adaptar
(incluida NEE)—. Cuando propone un archivo muestra qué va a hacer
(`resumen`), la `vista previa`, las evidencias (`✓` en el archivo, `?`
parafraseo) y los avisos, que **nunca bloquean**. Se aprueba con `y` o
escribiendo en el hilo («dale»); `n` descarta. La TUI **no escribe
archivos**: escribe el host, en `derivados/`, y solo tras la aprobación.
El modelo de la demo es `tero-offline`. AgentCore no es el producto.

## Cómo se ve la sesión

La simulación de `site/ficha.js` reproduce cuatro escenas en loop y se
detiene apenas alguien escribe:

- **a) responder**: «¿Qué tengo en la carpeta?» → el agente contesta; no
  hay tarjeta ni nada que aprobar.
- **b) crear**: una evaluación para 4° básico. El agente pregunta en
  lenguaje natural lo que le falta, propone la evaluación con vista
  previa y evidencias, y espera. Se aprueba con `dale` y aparece la
  **hoja fotocopiada** de `derivados/`.
- **b) descartar**: una guía de sistemas 2×2 que se responde con `n`: no
  se escribe nada.
- **c) adaptar (NEE)**: la misma evaluación adaptada para un estudiante
  con dislexia. La tarjeta muestra `acción: adaptar`, el `origen`, los
  `cambios` y los **apoyos y criterios NEE**. Al aprobar, el host escribe
  una versión nueva: el material de origen no se toca.
- Las **páginas LaTeX reales** salen al final, con la corrida que las
  produjo (loop10 GLM 4.7 Flash 29.1 s, MiniMax M2.5 94.9 s). `n` no
  publica hojas.
- Un aviso `unknown_source` **no bloquea** la aprobación. Ver
  [PUERTA-Y-PR8.md](PUERTA-Y-PR8.md).

## Virtualizar tero (OSS) y que se actualice solo

| Pieza | Qué hace |
| --- | --- |
| `site/tui-grid.js` | Encaja el PNG de la captura (o pinta celdas si falta). |
| `site/ficha.js` | Sesión conversacional (escenas, propuesta, aprobación, hoja). |
| `tui/scripts/capture-frames.ts` | Vuelca frames OpenTUI (`createTestRenderer` + `captureSpans`). |
| `tui/scripts/rasterize-frames.py` | PNG JetBrains si no hay display. |
| `tui/scripts/screenshot-frames.py` | PNG del terminal real, altura por frame. |
| `tui/scripts/compose-og.py` | OG de GitHub desde el home capturado. |
| `site/assets/tui/frames/` | Home, respuesta, conversación, propuesta (crear y adaptar), escrito y descartado. |
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
