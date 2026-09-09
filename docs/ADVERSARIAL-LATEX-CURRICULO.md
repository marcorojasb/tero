# Adversarial notes — LaTeX + Currículo (Nova Lite)

Authorized track: `feat/curriculum-latex-nova-lite`. Read with
[ANALISIS-ADVERSARIAL.md](ANALISIS-ADVERSARIAL.md).

## What we claim

1. **Currículum Chile is host-side.** JSON under `curriculum/chile/` is loaded by
   Python (`list_oa` / `get_oa` / `search_oa`). The model **selects** an id; it does
   not receive a dump of the whole curriculum in the system prompt.
2. **Texts are not official MINEDUC verbatim.** Paráfrasis / short summaries for a
   minimal 4°–6° set (Lenguaje, Matemática, Ciencias). Judges who open the JSON
   should see the disclaimer.
3. **LaTeX is template-rendered.** Schemas in `templates/latex/schemas/`; Jinja-free
   `{{placeholders}}` in `templates/latex/*.tex`. The model fills JSON (or we
   infer from markdown). The host escapes TeX specials. Nova Lite is **never**
   asked for `\documentclass`.
4. **PDF is optional.** `latexmk -pdf -no-shell-escape` if present; otherwise `.tex`
   only. CI does not require TeX live.

## Attack surface

| Attack | Mitigation |
| --- | --- |
| Model invents `OA 99` / fake ids | Tools return error on unknown `get_oa`; `/oa` validates against catalog; warning `oa_unknown` |
| Model dumps curriculum into draft | Catalog not in system prompt; tools return short rows |
| Model emits `\write18` / raw TeX | Escaped in `escape_latex`; templates are static files |
| Thin JSON from Nova Lite | `repair_payload` coerces types, fills defaults, soft-validates required fields |
| Export without gate | Same as md/docx: needs accepted `derivados/` or `b` borrador |
| Shell-escape PDF | Explicit `-no-shell-escape`; missing latexmk → tex only |
| Judge thinks offline is Bedrock | Unchanged: `tero-offline` label |

## How to smoke

```bash
pip install -e ".[dev]"
python -m tero demo --offline --yes
# schema → tex
python -m tero export --format latex --payload /path/to/guia.json --out /tmp/guia.tex /tmp/noop.md
# after demo, from derivados:
python -m tero export --format latex examples/carpeta-demo/derivados/<file>.md
```

TUI: `/curso 4° básico` → `/asignatura Lenguaje` loads `oa_options`; `/oa LEN-4B-OA04`;
after `s` or `b`, `/export latex`.

## Honest gaps

- Catalog is minimal (not full bases curriculares).
- Markdown→schema heuristics are best-effort; prefer JSON payload for clean TeX.
- Beamer outline is optional and thin.
- No Bedrock CI for schema drafting; offline path still scripts tool order including
  `list_oa` → `get_oa` → `propose_plan`.
