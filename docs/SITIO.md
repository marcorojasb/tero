# Sitio — la TUI, y el papel al final

tero no se muestra como un producto de IA. El chrome de
[`site/`](../site/) es una **sesión de terminal**: mismos tokens que la
TUI (`#0b0d10`, acento `#82aaff`, IBM Plex Mono) y un **queltehue en
ASCII** (`Vanellus chilensis`). El tero avisa. Tú decides.

El papel hiperrealista —grano de tóner, ficha fotocopiada— queda
**solo** en las páginas que tero crea (`#archivo` / `.hoja-frame`),
después de `s` o `b`. El resto no finge un escritorio.

La landing lleva rumbos `1–4`, avisos a la vista y la puerta `s` / `n`
/ `b` / `c`. El modelo de la demo es `tero-offline` (scripted). No
finge Bedrock. AgentCore no es el producto.

## Cómo se ve

- Ventana `tero@carpeta:~`, arte ASCII del queltehue (cresta, pecho,
  carúncula, patas de teru), panes de carpeta / sesión / TUI.
- Un rumbo (`1` Planificar · `2` Crear · `3` Evaluar · `4` Adaptar)
  dispara una **consulta con reloj**: `list_sources`, `read_source`,
  `propose_plan`, `draft_artifact`. Los milisegundos de la hoja están
  comprimidos; al lado va el tiempo de la corrida real (p. ej. MiniMax
  92.5 s / 94.9 s, GLM 29.1 s).
- El borrador en la sesión trae **varios tipos de pregunta** (SM, V/F,
  desarrollo) y, en matemática, **gráficos de rectas** (sistemas 2×2).
- Las **páginas LaTeX reales** (capturas de las mejores corridas) se
  muestran **al final**, cuando `s` deja el archivo en `derivados/` o
  `b` en `borradores/`. `n` no publica hojas. Ahí sí: fotocopia.
- Un aviso `unverified_citation` aparece **y no bloquea** `s`. Eso es la
  tesis, no un bug. Ver [PUERTA-Y-PR8.md](PUERTA-Y-PR8.md).
- La franja de abajo es la barra de la TUI.
- Imprimir (`Ctrl+P`) deja las hojas creadas.

## GitHub Pages

URL: `https://marcorojasb.github.io/tero/`.

Source en Settings es **GitHub Actions**. `.github/workflows/pages.yml`
publica `site/` desde `main`. El token de Actions puede publicar, pero
no crear el sitio (`403 Resource not accessible by integration`); por
eso el workflow hace preflight `GET /pages` y si 404, avisa y no falla.
Fallback: [Settings → Pages](https://github.com/marcorojasb/tero/settings/pages).

Un push a `main` que toque `site/` o el workflow dispara el deploy.
`workflow_dispatch` desde este agente da 403; hay que tocar esos paths
o Run workflow con cuenta de admin.

Vista previa local (404.html incluido, como en GitHub Pages):

```bash
python3 site/serve.py
# abrir http://127.0.0.1:4173/
```

## Qué no es

No es Electron, TipTap, Meridian, Biblioteca ni un dashboard de
AgentCore. No hay CTA de “Get started free”. La marca es **tero**
(queltehue) y el tagline **tus fuentes, tu criterio**.
