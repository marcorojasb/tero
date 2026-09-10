# Puerta `s` y el PR #8

Decisión de producto, con evidencia de las corridas. No es un changelog.

## Qué proponía el PR #8

Rama `cursor/bedrock-stress-harden-404a`, borrador, conflicto con `main`
en `src/tero/session.py`. Tres ideas mezcladas:

1. Reintentar plan y borrador hasta 3 veces ante `EventStreamError`.
2. Cortar llamadas colgadas con `TERO_TURN_TIMEOUT` + `SIGALRM`.
3. **Bloquear** `s` → `derivados/` si hay `thin_evidence` o `unknown_source`,
   salvo que la nota empiece por `forzar`. `--yes` y el autogate del bridge
   caían a `borradores/`.

El punto 3 es el que no se mergea. Los puntos 1–2 ya tienen sucesor en
`main` (reintento de borrador + salvage) o son peores que el sucesor
(`SIGALRM` en un host que puede spawnear workers de Bedrock).

## Tesis

tero **prepara, no decide**. La puerta humana es `s` / `n` / `b` / `c`.

Los avisos (`thin_evidence`, `unknown_source`, `unverified_citation`,
`tipo_desviado`, `oa_mismatch`, esqueleto corto) se **muestran**. No
bloquean `s`. El docente ve el costo y acepta, descarta, deja borrador
o pide corrección.

Eso está en [NORMAS.md](NORMAS.md), [ARCHITECTURE.md](../ARCHITECTURE.md),
[ADVERSARIAL-CORE-CALIDAD.md](ADVERSARIAL-CORE-CALIDAD.md) («no bloquees
`s`; muestra el costo en la puerta») y en el test
`test_warnings_oa_and_thin` (`blocking is False` para todos los avisos).

El PR #8 invertía la tesis: el host decidía que una ficha usable no
merecía `derivados/` porque Nova Lite parafraseó o citó mal un path.

## Evidencia de las corridas (suficiente)

### Stress Nova Lite (el origen del PR)

[STRESS-BEDROCK.md](STRESS-BEDROCK.md): `EventStreamError`, hangs,
`thin_evidence` / `unknown_source` y aun así `--yes` escribía. El PR
trataba eso como un bug de puerta. Era un bug de **stream y de citas**,
no de HITL.

### Loops de calidad 1–8 (MiniMax / GLM / Qwen)

Pedidos reales: evaluación-cuento, plan-agua, evaluación-sistemas.
Tres modelos. Fichas PDF. Hallazgos estables:

- Llegan borradores **usables** (inicio / desarrollo / cierre, SM, V/F).
- Casi siempre hay `unverified_citation` (parafraseo). Eso es `?` en el
  panel, no basura.
- `thin_evidence` aparece cuando el modelo cita poco; el material sigue
  anclado a la carpeta.
- `--yes` tiene que escribir en `derivados/` para el camino de juez y
  para el loop. Si el autogate cae a `borradores/`, el demo “pasa” sin
  cumplir lo que promete el README.
- Lo que sí rompía el loop no era `s`: era no llamar `draft_artifact`
  (Qwen en prosa), gastar el turno en tools vacías, o emitir un
  `activity` por cada delta del stream. Eso ya está en `main`
  (salvage, tope de tools, un `start` por `toolUseId`).

Si el #8 hubiera estado en `main` durante esos loops, las fichas de
plan-agua (MiniMax y GLM, fotocopiables) habrían aterrizado en
`borradores/` por un parafraseo. El docente en TUI tendría que
inventar la palabra mágica `forzar`. Eso no es aula chilena: es un
captcha.

## Qué no se porta a `main`

| Pieza del #8 | Por qué no |
| --- | --- |
| `ACCEPT_BLOCKING_CODES` + `blocking=True` | Rompe la tesis y el test de avisos. |
| Nota `forzar…` para aceptar | Atajo oculto; la puerta ya es `s`. |
| `--yes` → `borradores/` si hay aviso | El camino de juez deja de escribir lo que muestra. |
| `SIGALRM` / `timeoututil.py` | Mala idea con Bedrock multiprocess; el corte útil es tope de tools + salvage. |
| 3 reintentos de plan/draft | `main` ya reintenta el borrador una vez y **arma** el draft desde prosa/JSON. Más vueltas = más costo, mismo Qwen en loop. |

## Qué sí quedó en el host (el sucesor)

Sin tocar la puerta:

- Reintento de stream + reintento de `draft_artifact`.
- Salvage de plan y de borrador desde texto/JSON (`draft_salvaged`,
  aviso no bloqueante).
- Tope de tools en draft (`DRAFT_TOOL_BUDGET = 16`).
- Un evento `activity` por llamada a tool, no por delta.
- Contratos de payload (aliases, ítems SM/V-F, no cues de un cuento).
- `unverified_citation` visible; `s` sigue abierto.

## Cómo se ve en la puerta (lo correcto)

```
avisos
  unverified_citation  — parafraseo; no lo trates como cita literal
  thin_evidence        — menos de dos fuentes; el panel queda pobre

s  sí → derivados/     n  no     b  borrador     c  corregir
```

El costo está a la vista. Quien pulsa `s` es la persona.

## Cierre

El PR #8 se **cierra sin merge**. No es “falta rebase”: el conflicto en
`session.py` es el síntoma de que `main` ya tomó otro camino (salvage y
tope, no candado). Reabrir solo tendría sentido si alguien reescribiera
el PR **sin** bloquear `s` y **sin** `SIGALRM`. No hace falta: el
reintento útil ya está.
