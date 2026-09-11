# AWS lo más barato — tero no vive en el playground

La forma más barata de **seguir probando tero** no es subirlo a un
runtime. Es el loop que ya existe: carpeta local + Strands + Nova Lite.
AgentCore Harness es un chat administrado. No es la TUI, no es la
puerta `s` / `n` / `b` / `c`, no es la carpeta hasheada.

Esto no es un pitch. Es cómo no quemar créditos y cómo postular a
[Agents for Humans](https://agentsforhumans.devpost.com/).

## Respuesta corta

| Pregunta | Respuesta |
| --- | --- |
| ¿Cargo tero al playground `tero-Xe4RaZkLO2`? | **No como producto.** Puedes pegar el prompt (ver [hackathon/harness-playground.md](hackathon/harness-playground.md)) para un sketch de AWS. El agente real corre en tu máquina. |
| ¿Cómo aprovecho ~USD 120 de Free Tier? | Nova Lite/Micro desde `python -m tero`. Offline para casi todo. No dejes Claude Sonnet ni Browser encendidos en el harness. |
| ¿Qué es gratis de verdad? | `--offline` (USD 0). GitHub Pages. Builder ID. Devpost. Actividades Extra Credit del widget Explore AWS (hasta USD 20 c/u). |
| ¿Los USD 50 del hackathon? | Formulario [forms.gle/6sjzKiX6bKUMA5NEA](https://forms.gle/6sjzKiX6bKUMA5NEA) **hoy 11 sep 2026, 12:00 PT**. En **Free plan no aplican** créditos promocionales: hay que estar en Paid plan. |

## Lo que ya está hecho (cuenta tero)

- Cuenta AWS **Free plan** (9 sep 2026). Incluye USD 100 al alta y hasta USD 100 más por actividades. Vence el **9 mar 2027** o cuando se acaben los créditos — lo que ocurra primero. Si se acaban en Free plan, **AWS cierra la cuenta**.
- Inscrito en Agents for Humans. El submission de Devpost **ya está empezado**.
- Hay un harness en us-east-1: [playground tero-Xe4RaZkLO2](https://us-east-1.console.aws.amazon.com/bedrock-agentcore/harnesses/playground?id=tero-Xe4RaZkLO2).

## Path barato (en este orden)

### 0. USD 0 — pruebas de verdad

```bash
python -m tero demo --offline --yes
python -m tero tui --offline
pytest && (cd tui && bun test src)
```

El modelo se llama `tero-offline`. No finge Bedrock. Úsalo para el
video de 2 minutos y para no gastar nada mientras arreglas la TUI.

### 1. Casi gratis — Nova Lite en tu laptop

Un Strands agent → Bedrock Converse. **Sin** Runtime, Gateway, Browser
ni Code Interpreter.

Checklist:

1. Región **us-east-1**.
2. **No hay página Model access.** AWS la retiró: los modelos serverless (Nova Lite incluido) se habilitan solos al **primer invoke** en la cuenta. Catálogo: [Model catalog](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/model-catalog). Humo barato: [text playground](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/text-playground) → Amazon Nova Lite → un prompt. Si Strands pide inference profile, `TERO_MODEL=us.amazon.nova-lite-v1:0`. Docs: [model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html).
3. IAM mínimo: [hackathon/iam-bedrock-minimo.json](hackathon/iam-bedrock-minimo.json) (`InvokeModel` + `InvokeModelWithResponseStream`). Nova es de Amazon: **no** pasa por Marketplace. El formulario de Anthropic / `aws-marketplace:Subscribe` solo aplica si invocas Claude u otro tercero — no lo hagas para ahorrar.
4. `cp .env.example .env` → `TERO_OFFLINE=0`. Credenciales en el entorno, **nunca en git**.
5. Presupuesto de alerta: [hackathon/budget-tero.json](hackathon/budget-tero.json) o créalo a mano en [Budgets](https://us-east-1.console.aws.amazon.com/billing/home#/budgets).

```bash
python -m tero tui          # Nova Lite
# smoke más barato:
TERO_MODEL=amazon.nova-micro-v1:0 python -m tero demo --yes
```

Precios on-demand us-east-1 (Bedrock, sep 2026, verificar en
[la lista oficial](https://aws.amazon.com/bedrock/pricing/)):

| Modelo | Input / 1M tok | Output / 1M tok | Para qué |
| --- | --- | --- | --- |
| Nova Micro | ~USD 0.035 | ~USD 0.14 | smokes |
| **Nova Lite** (default tero) | ~USD 0.06 | ~USD 0.24 | loop de aula |
| Claude Sonnet 4.6 (default del harness) | ~USD 3 | ~USD 15 | **no** para iterar |

Una sesión tero con Nova Lite (plan + draft + un par de tools) suele
costar **centavos**. Con USD 120 alcanzan cientos de corridas si no
enciendes AgentCore con Sonnet, Browser o una instancia EC2 olvidada.

### 2. Sketch AWS — el playground (opcional, acotado)

El harness **no cobra fee extra**; cobras modelo + Runtime (CPU/RAM) +
cualquier tool que dejes prendida.

En
[tu playground](https://us-east-1.console.aws.amazon.com/bedrock-agentcore/harnesses/playground?id=tero-Xe4RaZkLO2):

1. Cambia el modelo a **Nova Lite** (no dejes Claude Sonnet).
2. Apaga **Browser** y **Code Interpreter**.
3. Baja `maxIterations` (p. ej. 8) y `timeoutSeconds` (p. ej. 120).
4. Pega el system prompt de [hackathon/harness-playground.md](hackathon/harness-playground.md).
5. **No subas `fuentes/`.** El contrato de tero es carpeta local + hash.

Sirve para una captura de “está en AgentCore” que **refuerza** Technical
Implementation. No reemplaza el demo de la TUI. Las reglas del hackathon
dicen que AgentCore **no es obligatorio**.

### 3. Lo que no hagas (quema plata)

- Default del harness (Claude Sonnet + Browser + 75 iteraciones + 1 h).
- Dejar EC2/RDS de las actividades Extra Credit encendidos.
- Meter Runtime/Gateway/Memory como si fueran la carpeta.
- Subir originales de curso a S3 “para que el agente los lea”.
- Unirse a una AWS Organization: **se caen** los créditos Free Tier al tiro.

## Cómo estirar los ~USD 120 (Free Tier)

Documentación:

- [Free Tier](https://aws.amazon.com/free/)
- [Cómo ganar USD 100 extra](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html)
- [FAQ Free plan](https://aws.amazon.com/free/free-tier-faqs/)
- [Créditos en Billing](https://us-east-1.console.aws.amazon.com/billing/home#/credits)
- [Free Tier usage](https://us-east-1.console.aws.amazon.com/billing/home#/freetier)
- Widget **Explore AWS** en [Console Home](https://console.aws.amazon.com/console/home?region=us-east-1) → filtro **Earn AWS credits**

Al alta: **USD 100**. Actividades guiadas: **USD 20 cada una**, hasta
USD 100 más, dentro de 6 meses:

| Actividad | Cómo (corto) | Riesgo |
| --- | --- | --- |
| Amazon Bedrock | [Text playground](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/text-playground) → Nova Lite → un prompt. Ese invoke **es** el alta del modelo. | Bajo. Si ves ~USD 120, esta ya está. |
| AWS Budgets | [Crear presupuesto](https://us-east-1.console.aws.amazon.com/billing/home#/budgets) de USD 5 con alerta al 80%. | Nulo. Hazla. |
| AWS Lambda | Function URL hello-world y bórrala. | Bajo. |
| Amazon EC2 | Lanza t3.micro, **termina en el mismo rato**. | Alto si se te olvida. |
| Amazon RDS | Igual: crea y **borra**. | Alto. |

Los créditos extra tardan hasta ~30 min en
[Credits](https://us-east-1.console.aws.amazon.com/billing/home#/credits).

Free plan: **no te cobran la tarjeta** mientras no pases a Paid. Si se
acaban los créditos o llegan los 6 meses, la cuenta se cierra (90 días
para rescatar datos subiendo a Paid).

## USD 50 del hackathon (distintos a Free Tier)

- Formulario: <https://forms.gle/6sjzKiX6bKUMA5NEA>
- Tope: **11 septiembre 2026, 12:00 PT** (mientras queden; Resources
  ya dijo que varios se desembolsaron).
- Términos: <https://aws.amazon.com/awscredits/>
- Caducan **31 octubre 2026**.
- Hay que estar **registrado en Devpost** (ya lo estás).
- **Free plan no es elegible para créditos promocionales.** Para que
  entren estos USD 50 hay que [pasar a Paid](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html).
  Hazlo solo si el form los pide y **después** de tener Budget + alerta.
  En Paid, lo que no cubran créditos **sí se cobra**.

Si el form ya cerró o se acabaron: no importa. Nova Lite + Free Tier
alcanzan para el video y las corridas de jueces.

## Postular a Agents for Humans

Pack listo para pegar: [hackathon/README.md](hackathon/README.md).

| Qué | Link |
| --- | --- |
| Hackathon | <https://agentsforhumans.devpost.com/> |
| Reglas | <https://agentsforhumans.devpost.com/rules> |
| FAQ | <https://agentsforhumans.devpost.com/details/faqs> |
| Resources / créditos | <https://agentsforhumans.devpost.com/resources> |
| Entrar submission | <https://agentsforhumans.devpost.com/submissions/new> |
| Cierre | **14 sep 2026, 17:00 PDT** |
| Track | **Professional Agents** (docente; el brief nombra explícitamente a teachers) |
| Repo | <https://github.com/marcorojasb/tero> (público, MIT) |
| Demo viva (Pages) | <https://marcorojasb.github.io/tero/> |
| Builder ID | <https://profile.aws.amazon.com> |
| Post bonus | <https://builder.aws.com/> → `+` → Create article, hashtag `#AgentsforHumans` |
| Discord / dudas | tab Discussion en Devpost; mail <shawni@devpost.com> |

AgentCore **no es obligatorio**. Un demo local + Bedrock Nova Lite +
video honesto puntúa Design e Impact. Una captura del harness (Nova
Lite, sin Browser) suma Implementation sin mentir sobre la carpeta.

## MFA y usuario IAM

No uses el root para iterar. Activa MFA del root:
<https://us-east-1.console.aws.amazon.com/iam/home#/security_credentials>

Crea un usuario IAM con la policy mínima de Bedrock. Access keys solo
en `.env` local.

## Relación con el resto de docs

- [ADVERSARIAL-CORE-CALIDAD.md](ADVERSARIAL-CORE-CALIDAD.md) — por qué
  Runtime no es el producto.
- [ANALISIS-ADVERSARIAL.md](ANALISIS-ADVERSARIAL.md) — qué hay que decir
  en el video (offline ≠ Bedrock).
- [NORMAS.md](NORMAS.md) — disclosure Pteron / MIT.
