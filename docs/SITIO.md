# Sitio — splash de terminal, y el papel al final

El chrome de [`site/`](../site/) sigue el **Terminal UI Brand System
v1.0**: ventana `tero` / `~/tero`, wordmark pixel, paleta ANSI (crema,
cian, aqua, teal, menta, lima) y una **ola ASCII generativa**
(`wave.js`). El tero avisa. Tú decides.

La ola no es un PNG congelado. Se dibuja en el cliente con la gramática
del sistema (puntos, cuadrados, bloques, cruces, curvas). El seed mezcla
`brand.json` con el SHA del deploy (`stamp.py` → `build-info.json`), así
que **cada push a `main` republica Pages y la marca se mueve un poco**
sin salirse del sistema.

El papel hiperrealista —grano de tóner, ficha fotocopiada— queda
**solo** en las páginas que tero crea (`#archivo` / `.hoja-frame`),
después de `s` o `b`.

Enter abre la sesión. Rumbos `1–4`, avisos a la vista, puerta `s` / `n`
/ `b` / `c`. El modelo de la demo es `tero-offline`. AgentCore no es el
producto.

## Cómo se ve

- Splash: `preguntas / mejores / aprendizajes / reales`, wordmark pixel,
  *Presiona Enter para comenzar*.
- Sesión: carpeta, consulta con reloj, borrador en terminal, TUI.
- Un rumbo dispara `list_sources` → `draft_artifact`. Al lado, el tiempo
  de la corrida real (MiniMax 92.5 s / 94.9 s, GLM 29.1 s).
- Las **páginas LaTeX reales** salen al final, con `s` o `b`. `n` no
  publica hojas.
- Un aviso `unverified_citation` **no bloquea** `s`. Ver
  [PUERTA-Y-PR8.md](PUERTA-Y-PR8.md).

## Virtualizar tero (OSS) y que se actualice solo

Elegido para este repo (cero dependencias nuevas en la landing):

| Pieza | Qué hace |
| --- | --- |
| `site/wave.js` | Virtualiza la marca (ola ASCII viva) en el navegador. |
| `site/brand.json` | Paleta y seed. Se edita a medida que avanza el sistema. |
| `site/stamp.py` | En cada Pages deploy escribe el SHA en `build-info.json`. |
| `.github/workflows/pages.yml` | Publica `site/` desde `main`. |

Otros proyectos MIT, por si más adelante queremos virtualizar **la TUI
real** o regenerar capturas cuando cambie el loop:

- [charmbracelet/vhs](https://github.com/charmbracelet/vhs) +
  [vhs-action](https://github.com/charmbracelet/vhs-action) — tapes
  `.tape` que CI vuelve a grabar. Encaja con `python -m tero demo
  --offline`.
- [opentui-web](https://github.com/rbbydotdev/opentui-web) y
  [`@opentui/three`](https://github.com/anomalyco/opentui) — el mismo
  OpenTUI de tero compilado a WASM / Three.js. Pesado; no es el
  producto.
- [xterm.js](https://xtermjs.org) — si algún día se transmite el bridge
  JSONL al browser.
- [@phyrex/ascii-canvas](https://github.com/phyrextsai/ascii-canvas) /
  [asciify-engine](https://github.com/KimTuxoan/asciify-engine) — video o
  canvas → ASCII en vivo.

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
(queltehue + ola ASCII) y el tagline **tus fuentes, tu criterio**.
