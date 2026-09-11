# site/

Fuente de GitHub Pages. Una ventana; adentro, la OpenTUI de tero
(`tui-grid.js`, frames en `assets/tui/frames/`). El papel fotocopiado
es solo de las páginas que tero crea, al aceptar (`s`) o guardar
borrador (`b`). Ver [docs/SITIO.md](../docs/SITIO.md).

```bash
python3 site/serve.py
cd ../tui && bun run capture   # regenera frames desde la TUI real
```
