# Cheapest AWS path — tero does not live in the playground

The cheapest way to **keep testing tero** is not to deploy it to a runtime. It is
the loop that already exists: local folder + Strands + Amazon Bedrock. AgentCore
Harness is a managed chat: **AgentCore Harness es un chat administrado** — it is not
the TUI, not the conversational approval, not the hashed folder.

This is not a pitch. It is how not to burn credits and how to submit to
[Agents for Humans](https://agentsforhumans.devpost.com/).

## Short answer

| Question | Answer |
| --- | --- |
| Do I upload tero to the harness playground? | **Not as the product.** You can paste the system prompt (see [hackathon/harness-playground.md](hackathon/harness-playground.md)) for an AWS sketch. The real agent runs on your machine. |
| How do I use the Free Tier credits? | Nova Lite/Micro from `python -m tero`. Offline for almost everything. Do not leave Claude Sonnet or Browser running in the harness. |
| What is genuinely free? | `--offline` (USD 0). GitHub Pages. Builder ID. Devpost. |
| The USD 50 hackathon credits? | The form (<https://forms.gle/6sjzKiX6bKUMA5NEA>) **closed on 2026-09-11** and Resources states all credits were disbursed. Not needed for the submission. |

## What is already done

- AWS account in `us-east-1`.
- Registered on Agents for Humans; the Devpost submission is started.
- A harness playground exists (optional sketch only).

## Cheap path, in order

### 0. USD 0 — real tests

```bash
python -m tero demo --offline --yes
python -m tero tui --offline
pytest && (cd tui && bun test src)
```

The model is labeled `tero-offline`. It does not fake Bedrock. Use it for the video
and to fix the TUI without spending anything.

### 1. Almost free — Bedrock on your laptop

One Strands agent → Bedrock ConverseStream. **No** Runtime, Gateway, Browser or
Code Interpreter.

Checklist:

1. Region **`us-east-1`**.
2. **There is no Model access page** — AWS retired it: serverless models (Nova
   Lite included) **se habilitan solos** on the first `InvokeModel` in the
   account. Catalog:
   [Model catalog](https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/model-catalog).
   Cheap smoke: the text playground with `amazon.nova-lite-v1:0`. If Strands asks
   for an inference profile, `TERO_MODEL=us.amazon.nova-lite-v1:0`.
3. Minimum IAM: [hackathon/iam-bedrock-minimo.json](hackathon/iam-bedrock-minimo.json)
   (`InvokeModel` + `InvokeModelWithResponseStream`). Nova is first-party: it does
   **not** go through Marketplace, so no `aws-marketplace:Subscribe` is needed.
4. `cp .env.example .env` → `TERO_OFFLINE=0`. Credentials live in the environment,
   **never in git**.
5. Spend alert: [hackathon/budget-tero.json](hackathon/budget-tero.json), or create
   one by hand in [Budgets](https://us-east-1.console.aws.amazon.com/billing/home#/budgets).

```bash
python -m tero tui          # default: Nova Lite
# cheaper smoke:
TERO_MODEL=amazon.nova-micro-v1:0 python -m tero demo --yes
```

On-demand prices in `us-east-1` (Bedrock, Sep 2026 — check the
[official list](https://aws.amazon.com/bedrock/pricing/)):

| Model | Input / 1M tok | Output / 1M tok | For |
| --- | --- | --- | --- |
| Nova Micro | ~USD 0.035 | ~USD 0.14 | smokes |
| **Nova Lite** (tero default) | ~USD 0.06 | ~USD 0.24 | the classroom loop |
| Claude Sonnet 4.6 (harness default) | ~USD 3 | ~USD 15 | **not** for iterating |

A tero session with Nova Lite (proposal + approval + a couple of tools) costs
**cents**.

### 2. Recommended model trio (measured)

An empirical benchmark across 5 Bedrock models and 4 pedagogical journeys is in
[EVALUATION-PAPER.md](EVALUATION-PAPER.md). The selected trio:

| Model | Success | Mean latency | Use |
| --- | :---: | :---: | :--- |
| `amazon.nova-lite-v1:0` | 100% | 10.0 s | Serverless default; cheapest; densest official citations |
| `zai.glm-4.7-flash` | 100% | 10.6 s | Fastest tool calling; strict Decreto 83 NEE schema |
| `minimax.minimax-m2.5` | 100% | 39.5 s | Richest classroom prose and assessment rubrics |

### 3. AWS sketch — the playground (optional, bounded)

The harness charges no extra fee; you pay for model + Runtime (CPU/RAM) + any tool
you leave turned on.

In the playground:

1. Switch the model to **Nova Lite** (never leave Claude Sonnet on).
2. Turn **Browser** and **Code Interpreter** off.
3. Lower `maxIterations` (e.g. 8) and `timeoutSeconds` (e.g. 120).
4. Paste the system prompt from [hackathon/harness-playground.md](hackathon/harness-playground.md).
5. **Do not upload `fuentes/`.** tero's contract is a local folder + hash.

It is useful for a screenshot that reinforces Technical Implementation. It does not
replace the TUI demo. The hackathon rules say AgentCore is **not required**.

### 4. What not to do (it burns money)

- The harness default (Claude Sonnet + Browser + 75 iterations + 1 h).
- Leaving EC2/RDS from the Extra Credit activities running.
- Treating Runtime/Gateway/Memory as if they were the folder.
- Uploading classroom originals to S3 "so the agent can read them".
- Joining an AWS Organization: Free Tier credits drop immediately.

## Applying to Agents for Humans

Pack ready to paste: [hackathon/README.md](hackathon/README.md).

| What | Link |
| --- | --- |
| Hackathon | <https://agentsforhumans.devpost.com/> |
| Rules | <https://agentsforhumans.devpost.com/rules> |
| FAQ | <https://agentsforhumans.devpost.com/details/faqs> |
| Submit | <https://agentsforhumans.devpost.com/submissions/new> |
| Close | **Sep 14, 2026, 17:00 PDT** (= 21:00 Chile) |
| Track | **Professional Agents** (the brief explicitly names teachers) |
| Repo | <https://github.com/marcorojasb/tero> (public, MIT) |
| Live demo (Pages) | <https://marcorojasb.github.io/tero/> |
| Builder ID | <https://profile.aws.amazon.com> |
| Bonus post | <https://builder.aws.com/> → `+` → Create article |
| Judge guide | [hackathon/JUDGES-EN.md](hackathon/JUDGES-EN.md) |

AgentCore **is not required**. A local demo + Bedrock Nova Lite + an honest video
scores Design and Impact. A harness screenshot (Nova Lite, no Browser) adds
Implementation without lying about the folder.

## MFA and IAM user

Do not iterate with root. Enable root MFA:
<https://us-east-1.console.aws.amazon.com/iam/home#/security_credentials>

Create an IAM user with the minimum Bedrock policy. Access keys only in the local
`.env`.

## Relation to the other docs

- [EVALUATION-PAPER.md](EVALUATION-PAPER.md) — which models, how they were measured.
- [ADVERSARIAL-CORE-CALIDAD.md](ADVERSARIAL-CORE-CALIDAD.md) — why a runtime is not
  the product.
- [NORMAS.md](NORMAS.md) — Pteron / MIT disclosure.
