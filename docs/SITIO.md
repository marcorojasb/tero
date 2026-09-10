# Sitio — la fotocopia

tero no se muestra como un producto de IA. Se muestra como **la hoja que
sale de la fotocopiadora**.

La landing (`site/`) es una ficha de aula chilena sobre un escritorio:
sello **REVISAR**, chips de curso, rumbos `1–4`, avisos a la vista, y la
puerta `s` / `n` / `b` / `c`. El modelo de la demo en esa página es
`tero-offline` (scripted). No finge Bedrock. AgentCore no es el producto.

## Cómo se ve

- Fondo de escritorio, papel con grano de tóner, sello rojo chueco.
- Elegir rumbo (`1` Planificar · `2` Crear · `3` Evaluar · `4` Adaptar)
  arma un borrador de ejemplo anclado a una carpeta.
- Un aviso `unverified_citation` aparece **y no bloquea** `s`. Eso es la
  tesis, no un bug. Ver [PUERTA-Y-PR8.md](PUERTA-Y-PR8.md).
- `s` deja el archivo en `derivados/` de la carpeta simulada; `b` en
  `borradores/`; `n` descarta; `c` pide crítica.
- La franja de abajo es la TUI (fondo `#0b0d10`, acento `#82aaff`).
- Imprimir la página (`Ctrl+P`) deja solo la hoja. Sirve de ficha.

## GitHub Pages

Workflow: `.github/workflows/pages.yml` publica `site/` desde `main`.

En el repo: Settings → Pages → Source **GitHub Actions** (una vez).
URL esperada: `https://marcorojasb.github.io/tero/`.

Vista previa local:

```bash
python3 -m http.server 4173 --directory site
# abrir http://127.0.0.1:4173/
```

## Qué no es

No es Electron, TipTap, Meridian, Biblioteca ni un dashboard de
AgentCore. No hay CTA de “Get started free”. La marca en la hoja es
**tero — agente docente** y el tagline **tus fuentes, tu criterio**.
