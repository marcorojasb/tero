# Protocolo del agente conversacional

Contrato entre el host (`python -m tero bridge`) y la TUI (OpenTUI). Es la
especificación de la que cuelgan los PRs de migración: host, TUI y offline
se implementan por separado contra este documento.

Reemplaza el flujo por pasos: **no hay** rumbos 1–4, plan tipado con
`a`/`e`/`x`, clarificaciones numeradas ni puerta `s` / `n` / `b` / `c`.

## Tesis

La persona escribe en lenguaje natural. El agente entiende la intención y
actúa:

| Intención | Qué hace | Cómo termina el turno |
| --- | --- | --- |
| **a) responder / interactuar** | Contesta, explica, pregunta lo que le falta | `respuesta` |
| **b) crear material nuevo** | Planificación, guía, evaluación, pauta, actividad | `propuesta` → aprobación |
| **c) editar / adaptar** | Versión nueva de un material existente; incluye adaptación a NEE | `propuesta` → aprobación |

Si le falta información (curso, tema, OA, duración, qué archivo editar),
**pregunta en lenguaje natural**. No inventa ni asume en silencio.

Nada se escribe sin aprobación explícita de la persona, después de ver
**qué va a hacer + la vista previa**. El modelo nunca escribe archivos: el
host escribe, y solo tras `aprobar`.

## Fases

```
idle → pensando → respuesta?                → idle
                → propuesta?                → esperando_aprobacion
                     aprobar                → escrito → idle
                     descartar              → idle
                     cambiar / nuevo prompt → pensando (revisa la propuesta)
                → error                     → (r en TUI reintenta)
```

`status.phase` solo toma esos cinco valores: `idle`, `pensando`,
`esperando_aprobacion`, `listo`, `error`. `listo` se usa al cerrar un
turno con archivo escrito.

## Cliente → host

Un objeto JSON por línea.

| Tipo | Campos | Qué hace |
| --- | --- | --- |
| `hello` | `carpeta?`, `encargo?` | Abre sesión; responde `hello_ok` |
| `prompt` | `text` | Mensaje de la persona. El agente infiere a/b/c |
| `aprobar` | `decision`: `aprobar`\|`descartar`, `note?` | Botones explícitos de la TUI |
| `retry` | — | Reintenta el último mensaje |
| `encargo.update` | `encargo` | Contexto (curso/asignatura/OA); no reinicia el flujo |
| `curriculum.list` | `curso?`, `asignatura?` | Lista OA del catálogo |
| `export` | `format`, `path?`, `pdf?` | Exporta el último artefacto escrito |
| `shutdown` | — | Cierra el host |

## Host → cliente

| Tipo | Campos | Cuándo |
| --- | --- | --- |
| `ready` | `mode`, `model`, `carpeta`, `transcript` | Al arrancar |
| `hello_ok` | `carpeta`, `fuentes`, `changed`, `sessions`, `curriculum`, `transcript` | Tras `hello` |
| `status` | `phase`, `detail?` | Cambio de fase (spinner) |
| `delta` | `text` | Texto en streaming de la respuesta |
| `respuesta` | `id`, `texto` | Turno resuelto como a) o pregunta del agente |
| `propuesta` | `id`, `propuesta` | Turno resuelto como b)/c); requiere aprobación |
| `aprobacion` | `id`, `decision`, `note` | Eco de la decisión de la persona |
| `escrito` | `id`, `path`, `accion` | El host escribió el archivo |
| `activity` | `tool`, `state`, `detail` | Un `start` por llamada a tool |
| `warning` | `warning` | Aviso **no bloqueante** |
| `error` | `message`, `code`, `retryable` | Error humanizado en español |
| `encargo` | `encargo` | Contexto actualizado |
| `oa_options` | `oas`, `curso`, `asignatura` | Catálogo para el contexto |
| `exported` | `path`, `format`, `source_kind`, `source_path`, `feedback?`, `pdf?` | Tras `export` |

### Objeto `propuesta`

```json
{
  "accion": "crear",
  "tipo": "evaluacion",
  "tipo_label": "evaluación",
  "titulo": "Evaluación de comprensión lectora — El cóndor y el huemul",
  "resumen": "Prueba de 45 min con ítems de selección múltiple y V/F.",
  "vista_previa": "---\ntipo: evaluacion\n...\n",
  "origen": null,
  "cambios": [],
  "notas_nee": [],
  "evidencias": [{"path": "fuentes/cuento.md", "snippet": "…", "verified": true}],
  "warnings": [{"code": "thin_evidence", "message": "…", "blocking": false}]
}
```

- `accion`: `crear` (material nuevo), `editar` (versión nueva de un
  material existente), `adaptar` (edición con apoyos/criterios NEE).
- `origen`: ruta relativa del material que se edita o adapta. `null` si es
  `crear`.
- `cambios`: lista corta de qué cambia respecto del origen (`editar`/`adaptar`).
- `notas_nee`: apoyos y criterios agregados (`adaptar`).
- `evidencias`: `verified` lo calcula el host contra el archivo real.
- `warnings` nunca bloquean la aprobación; se muestran antes de decidir.

## Tools del modelo

Leen o proponen **en memoria**. Ninguna escribe.

| Tool | Firma | Para |
| --- | --- | --- |
| `list_sources` | `()` | Inventario de la carpeta |
| `search_sources` | `(query)` | Buscar dentro de las fuentes |
| `read_source` | `(path)` | Leer una fuente (sandbox + hash) |
| `list_oa` | `(curso, asignatura)` | Catálogo Chile |
| `get_oa` | `(id)` | Detalle de un OA |
| `search_oa` | `(q)` | Buscar OA |
| `cite_evidence` | `(path, snippet, seccion)` | Evidencia para la propuesta |
| `proponer_crear` | `(tipo, titulo, resumen, vista_previa_markdown, evidencias_json, payload_json)` | Intención b) |
| `proponer_editar` | `(ruta_origen, accion, tipo, titulo, resumen, vista_previa_markdown, cambios, notas_nee, evidencias_json, payload_json)` | Intención c) |

Si el modelo contesta con texto y no llama a ninguna tool de propuesta, ese
texto **es** la respuesta (intención a). Es el camino normal, no un fallo.

## Escritura (solo el host)

- `aprobar` → `derivados/`, con marca de tiempo en el nombre. Nunca se
  sobrescribe un archivo existente.
- `editar` / `adaptar` → archivo **nuevo** en `derivados/` derivado del
  origen. El material de origen no se toca (ni en `derivados/` ni, jamás,
  en `fuentes/`).
- `descartar` → no escribe nada.
- Tras escribir, el host re-hashea los originales. Si algo cambió, avisa;
  nunca reescribe la fuente.

## Aprobación en lenguaje natural

La persona puede aprobar escribiendo. El host clasifica la respuesta con
`tero.approval.classify_approval` en `aprobar` / `cambiar` / `descartar` /
`preguntar` / `ambiguo`:

- `aprobar` → escribe. **Solo** con aceptación explícita.
- `cambiar` → el agente revisa la propuesta con esa nota (sigue pendiente).
- `descartar` → se bota la propuesta.
- `preguntar` / `ambiguo` → el mensaje se trata como conversación; la
  propuesta sigue pendiente hasta que la persona decida.

Regla dura: ante duda, **no** se aprueba. Un texto desconocido nunca
escribe un archivo.

## Migración

| Pieza | Estado |
| --- | --- |
| Protocolo (este doc) | Congelado |
| Host: sesión, tools, prompts, bridge, CLI, offline | PR de host |
| TUI: conversación + tarjeta de propuesta | PR de TUI |
| `docs/PUERTA-Y-PR8.md`, README, sitio | PR de docs |

Hasta que aterricen los dos PRs, el código en `main` todavía muestra el
flujo por pasos.
