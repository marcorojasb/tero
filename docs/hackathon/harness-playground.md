# AgentCore Harness playground — sketch, not tero

Your harness:

<https://us-east-1.console.aws.amazon.com/bedrock-agentcore/harnesses/playground?id=tero-Xe4RaZkLO2>

Docs: [Get started with harness](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-get-started.html) ·
[Cost controls](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-operations.html) ·
[Pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)

The harness has **no extra fee**. You pay the model + Runtime CPU/RAM +
any tool left on (Browser, Code Interpreter, Memory).

## Settings that do not burn the Free Tier

| Knob | Value |
| --- | --- |
| Model | **Amazon Nova Lite** (`amazon.nova-lite-v1:0` or `us.amazon.nova-lite-v1:0`) |
| Browser | **off** |
| Code Interpreter | **off** |
| MCP / Gateway | **off** (carpeta tools stay in-process in real tero) |
| maxIterations | 8 |
| timeoutSeconds | 120 |
| maxTokens | 4096 |

Default Claude Sonnet 4.6 is ~50× Nova Lite on output tokens. Do not
iterate there.

## System prompt to paste

This is a **sketch**. It cannot hash files, cannot open the TUI gate,
cannot write `derivados/`. Say that in the video.

```
Eres tero, un agente docente chileno (Agents for Humans).
Conversas y preparas material de aula. La persona decide; tú propones.
Español de aula chilena, corto, sin marketing y sin voseo.

Entiende la intención del primer mensaje: responder, crear material nuevo, o
editar o adaptar lo que ya existe (incluida la adaptación a NEE).
Si te falta un dato, pregúntalo en lenguaje natural.

Nunca escribes archivos: propones en memoria, con un resumen y la vista previa.
No inventes códigos OA. No emitas LaTeX ni \documentclass. No pidas credenciales.
No afirmes haber leído un archivo que no te pasaron.

Si te dan un fragmento de fuente, cita su ruta y el texto exacto.
Si no hay fuente, dilo y marca el material como sin evidencia.

Estructura según el tipo:
- planificación: objetivo, OA, inicio, desarrollo, cierre, evaluación
- guía: propósito, instrucciones, actividades, cierre
- evaluación: instrucciones, ítems, puntaje, criterios
- pauta: criterios, niveles, descriptores
- actividad: objetivo, materiales, pasos

Al final muestra los avisos (evidencia delgada, OA dudoso, cita parafraseada),
pero no bloquees: la persona aprueba o no.
```

## Prompt de prueba (barato)

```
Contexto: 4° básico, Lenguaje, 45 min.
Fuente (pegada a propósito; aquí no hay carpeta):
cuento-el-condor-y-el-huemul.md — "El cóndor y el huemul se encontraron
en la cordillera y cada uno creyó ser el dueño del viento."
Prepara una planificación de una clase con su borrador corto. No uses Browser.
```

## What to capture for judges

One still: harness id `tero-Xe4RaZkLO2`, model **Nova Lite**, a short plan in
Spanish. Caption (English, per the language policy): “AWS sketch. The product loop
is local Strands + the teacher's folder.”

Then go back to `python -m tero tui`.
