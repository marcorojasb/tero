# Sitio — la fotocopia

tero no se muestra como un producto de IA. Se muestra como **la hoja que
sale de la fotocopiadora**.

La landing (`site/`) es una ficha de aula chilena sobre un escritorio:
sello **REVISAR**, chips de curso, rumbos `1–4`, avisos a la vista, y la
puerta `s` / `n` / `b` / `c`. El modelo de la demo en esa página es
`tero-offline` (scripted). No finge Bedrock. AgentCore no es el producto.

## Cómo se ve

- Fondo de escritorio, papel con grano de tóner, sello rojo chueco.
- Un rumbo (`1` Planificar · `2` Crear · `3` Evaluar · `4` Adaptar)
  dispara una **consulta con reloj**: `list_sources`, `read_source`,
  `propose_plan`, `draft_artifact`. Los milisegundos de la hoja están
  comprimidos; al lado va el tiempo de la corrida real (p. ej. MiniMax
  92.5 s / 94.9 s, GLM 29.1 s).
- El borrador en la ficha trae **varios tipos de pregunta** (SM, V/F,
  desarrollo) y, en matemática, **gráficos de rectas** (sistemas 2×2).
- Las **páginas LaTeX reales** (capturas de las mejores corridas) se
  muestran **al final**, cuando `s` deja el archivo en `derivados/` o
  `b` en `borradores/`. `n` no publica hojas.
- Un aviso `unverified_citation` aparece **y no bloquea** `s`. Eso es la
  tesis, no un bug. Ver [PUERTA-Y-PR8.md](PUERTA-Y-PR8.md).
- La franja de abajo es la TUI (fondo `#0b0d10`, acento `#82aaff`).
- Imprimir (`Ctrl+P`) deja la hoja. Sirve de ficha.

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
AgentCore. No hay CTA de “Get started free”. La marca en la hoja es
**tero — agente docente** y el tagline **tus fuentes, tu criterio**.
