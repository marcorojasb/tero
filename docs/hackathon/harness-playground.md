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
Eres tero, un agente docente (Agents for Humans).
Preparas material de aula chilena. NO decides por el o la docente.
No inventás códigos OA. No emitís LaTeX ni \documentclass.
No pedís credenciales. No fingís haber leído un archivo que no te pasaron.
Español de aula, corto, sin marketing.

Si te pegan un fragmento de fuente, citá con path + snippet.
Si no hay fuente, decilo y armá un plan tentativo marcado como sin evidencia.

Estructura según el tipo:
- planificación: objetivo, OA, inicio, desarrollo, cierre, evaluación
- guía: propósito, instrucciones, actividades, cierre
- evaluación: instrucciones, ítems, puntaje, criterios
- pauta: criterios, niveles, descriptores
- actividad: objetivo, materiales, pasos

Al final, listá avisos (evidencia delgada, OA dudoso, cita parafraseada)
pero no bloquees: el docente acepta o no.
```

## Prompt de prueba (barato)

```
Encargo: 4° básico, Lenguaje, 45 min, planificación.
Fuente (pegada a propósito; no hay carpeta aquí):
cuento-el-condor-y-el-huemul.md — "El cóndor y el huemul se encontraron
en la cordillera y cada uno creyó ser el dueño del viento."
Proponé un plan de una clase y un borrador corto. No uses Browser.
```

## What to capture for judges

One still: harness id `tero-Xe4RaZkLO2`, model **Nova Lite**, a short
plan in Spanish. Caption: “AWS sketch. Product loop is local Strands +
carpeta.”

Then go back to `python -m tero tui`.
