# Sample classroom fixtures

`aula-5basico-agua/` is a **teacher work folder** for the happy-path demo:
5° básico, Ciencias Naturales, unidad *El agua y los océanos*.

Files are original notes written for tero. They paraphrase public MINEDUC *Objetivos
de Aprendizaje*; they are not an official curriculum PDF.

Default judge path uses `examples/carpeta-demo/`. This pack is the extra classroom folder
from the first MVP (includes a PDF). Same host rules: originals hashed, writes only under
`derivados/` / `borradores/`.

```bash
python -m tero demo --offline --yes
python -m tero demo --offline --yes --carpeta fixtures/aula-5basico-agua
python -m tero demo --yes          # Amazon Bedrock
```
