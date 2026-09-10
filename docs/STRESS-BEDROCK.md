# Stress Bedrock — hallazgos (2026-09-10)

Corridas con `amazon.nova-lite-v1:0` / `us-east-1` y el path offline como control.
Objetivo: **romper** el loop docente y dejar material accionable (no checklist verde).

## Resumen

| Área | Resultado |
| --- | --- |
| Offline demo / bridge / export LaTeX | Estable |
| Bedrock demo `--yes` (carpeta-demo) | A menudo escribe; **EventStreamError** frecuente |
| Bridge HITL Bedrock | **Hang / stream error** (~340s sin propuesta usable) |
| Concurrencia ×3 demos | 3/3 escribieron, **2/3** con `EventStreamError` |
| Evidencia real | Frecuente `thin_evidence`, citas a OA como “path”, o **0 evidencias** y aun así `s` escribe |
| Carpeta agua / domain mismatch | Flaky: a veces “no propuso un plan” (`fase error`); a veces escribe con `domain_mismatch` |
| Demo ×5 seguido | Al menos un **timeout >300s** (hang) |
| Modelo inválido | Falla en español (graceful) |

## Quiebres reales (prioridad)

### P0 — Stream Bedrock / hang

- Log típico: `exception=<EventStreamError> | event loop cycle failed`.
- A veces el host reintenta y igual llega a `escrito:`; a veces el demo queda en `fase inesperada: error` o el bridge **no cierra**.
- Peor bajo carga (3 demos en paralelo) y en `python -m tero bridge --yes` sin TUI.

**Mejora:** backoff más agresivo, timeout de turno visible, no dejar el bridge colgado; métrica/contador de retries en status.

### P0 — Evidencia débil aceptada en `derivados/`

Ejemplos observados en propuestas Bedrock:

- `evidencias: []` + warning `thin_evidence` (no bloquea).
- `path: "OA 4 (LEN-4B-OA04)"` → `unknown_source`.
- Tras `c` (corregir), el rewrite a veces **empeora** (pierde citas).

**Mejora:** en puerta, si `thin_evidence` / `unknown_source`, exigir confirmación explícita o impedir `s` hasta citar ≥2 rutas reales de la carpeta (política de producto a decidir).

### P1 — Demo flaky en carpetas “difíciles”

- `fixtures/aula-5basico-agua` + chips Ciencias: falló una vez (“no propuso plan”), pasó después.
- Encargo Lenguaje sobre carpeta Ciencias: mismo patrón flaky + `domain_mismatch` cuando sí escribe.

**Mejora:** no tratar “sin plan” como hard fail opaco; surfacing del error Bedrock + `r`/`--skip-plan` más claro en CLI.

### P1 — Títulos / tipo genéricos

Varios artefactos: `Plan de planificación — …` / cuerpo genérico sin anclar al cuento real de la carpeta.

**Mejora:** prompt/host: exigir `read_source` de ≥1 fuente listada antes de `draft_artifact`; rechazar draft sin tool-use de lectura.

## Controles que no se rompieron

- Offline `--yes`, cancel plan (`x` → `idle`), `n` → `listo`, double `s` sin crash.
- Export LaTeX de derivados existentes.
- Modelo inexistente → mensaje humano, exit ≠ 0.
- Fuentes malformadas (binario + huge.md + empty): offline aguanta.

## Cómo reproducir

```bash
# stream / hang
python -m tero demo --yes --carpeta examples/carpeta-demo
python -m tero bridge --yes --carpeta examples/carpeta-demo   # JSONL hello+prompt; observar EventStream

# evidencia floja
# aceptar con s una propuesta con warnings thin_evidence / unknown_source

# flaky carpeta
python -m tero demo --yes --carpeta fixtures/aula-5basico-agua \
  --curso "5° básico" --asignatura Ciencias --tipo guia
```

## Mitigaciones aplicadas (ciclo 2026-09-10b)

- Retry plan + draft (hasta 3) con backoff; match de `EventStreamError` / `event loop cycle failed`.
- `s` bloqueado ante `thin_evidence` / `unknown_source` salvo nota `forzar…`; `--yes`/bridge → `borradores/`.
- Prompt de corrección `c` exige citas con paths reales.

## Mitigaciones (ciclo 2026-09-10c)

- `TERO_TURN_TIMEOUT` (default **120s** online, 0 offline): SIGALRM corta llamadas agent colgadas; reintenta hasta agotar intentos.
- Warnings `thin_evidence` / `unknown_source` con `blocking=True` (tests alineados).

Post-fix: concurrent ×3 OK; empty → borradores; hang >240s del demo → ahora debería cortar por timeout de turno.
