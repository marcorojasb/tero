# Agents for Humans: tero keeps the teacher in the chair

Paste into Builder Center: https://builder.aws.com/ → `+` → **Create article**.

Title must include **Agents for Humans**. First paragraph or tags: `#AgentsforHumans`.

Suggested tags (max 5): `agents-for-humans`, `strands-agents`, `amazon-bedrock`, `amazon-nova`, `education`

---

A Chilean teacher does not open another SaaS tab at 22:00. They have a
folder: a story, OA notes, last week’s vocabulary. What they need by
morning is a page they can photocopy — and they need to have **said
yes** to it.

**tero** is a Strands agent for that loop. The model prepares. The
teacher decides with `s` / `n` / `b` / `c`. I built it for the AWS
Agents for Humans hackathon, Professional Agents track.

## What I refused to put on AWS

Amazon Bedrock AgentCore is a strong runtime. It is also the wrong
system of record for a classroom folder. If the agent writes into
`fuentes/`, or if those files live in a bucket the teacher does not
hold, the product thesis is gone.

So the lean path is:

- **Strands Agents SDK** on the teacher’s machine
- **Amazon Bedrock** Nova Lite (`amazon.nova-lite-v1:0`) in `us-east-1`
- OpenTUI for the shell
- Host tools that only **read** (sandbox + SHA-256). `tero.gate` writes
  `derivados/` after `s`

An AgentCore Harness playground can hold a sketch of the system prompt.
That is fine for a screenshot. It is not tero.

## Free Tier without theater

New AWS Free plan: USD 100 on sign-up, up to USD 100 more from the
Explore AWS widget (Bedrock playground, Budgets, Lambda, EC2, RDS —
terminate the last two the same hour).

Nova Lite is cheap enough that those credits cover hundreds of teacher
turns. Claude Sonnet as the harness default is how you set the money
on fire. Offline mode is a real Strands `Model` labeled `tero-offline`,
not a fake `InvokeModel`.

I used AWS Budgets so the Free plan cannot close the account by
surprise (Free plan **closes** when credits hit zero).

## What “agent” means here

Not a chatbot that talks about pedagogy. A loop:

1. list/read sources in the carpeta
2. optional typed plan the teacher edits
3. citations checked against the file
4. draft artifact
5. human gate

If the model writes `draft_artifact(...)` as prose, the host salvages
it. If citations are paraphrases, the panel shows `?` and still lets
the teacher press `s`. That is the product: prepare, don’t decide.

## Links

- Repo: https://github.com/marcorojasb/tero
- Live splash: https://marcorojasb.github.io/tero/
- Hackathon: https://agentsforhumans.devpost.com/

#AgentsforHumans
