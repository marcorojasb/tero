# Agents for Humans — submission pack

Deadline: **Monday, September 14, 2026, 17:00 PDT** (21:00 Chile continental).
USD 50 credits form: closed (credits fully disbursed as of 2026-09-11).

How not to overspend: [../AWS-GRATIS.md](../AWS-GRATIS.md).

## Status

- [x] Public MIT repo: <https://github.com/marcorojasb/tero>
- [x] README, ARCHITECTURE and benchmark paper in English
- [x] Registered on Devpost (submission started)
- [x] AWS account, `us-east-1`
- [x] Repo About: Homepage = Pages; topics `strands-agents`, `amazon-bedrock`
- [ ] AWS Builder ID: <https://profile.aws.amazon.com>
- [ ] Paste Devpost text: [DEVPOST.md](DEVPOST.md)
- [ ] Upload diagram: [architecture.png](architecture.png)
- [ ] Video ≤ 5 min (public YouTube or Vimeo): [VIDEO.md](VIDEO.md)
- [ ] Live demo: <https://marcorojasb.github.io/tero/> (if 404, enable Pages)
- [ ] Bonus post: [BUILDER-POST.md](BUILDER-POST.md)

## Files

| File | Purpose |
| --- | --- |
| [JUDGES-EN.md](JUDGES-EN.md) | **English judge guide**: what tero is / is not, trust model, AWS usage, official curriculum bank, Ley 21.719 privacy, Decreto 83 NEE, Track A offline + Track B Bedrock with real outputs, and what "green" means. |
| [DEVPOST.md](DEVPOST.md) | English submission text (copy/paste). |
| [VIDEO.md](VIDEO.md) | ≤ 5 min script covering the three intents. |
| [VIDEO-CAPTIONS.md](VIDEO-CAPTIONS.md) | Canonical on-screen copy: English captions, Spanish terminal strings. |
| [BUILDER-POST.md](BUILDER-POST.md) | Builder Center article. |
| [harness-playground.md](harness-playground.md) | Optional AgentCore sketch (not the product). |
| [architecture.png](architecture.png) | Diagram for Devpost (regenerate: `python docs/hackathon/render_architecture.py`). |
| [architecture.svg](architecture.svg) | Same architecture, vector. |
| [iam-bedrock-minimo.json](iam-bedrock-minimo.json) | Lean IAM policy. |
| [budget-tero.json](budget-tero.json) | Spend alert. |

## Track

**Professional Agents.** The primary user is a teacher, not a whole school
distribution (that would be Good Neighbor). The Devpost brief names teachers who
turn one class into material for thirty students.

## What a judge must be able to do

```bash
git clone https://github.com/marcorojasb/tero.git
cd tero
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m tero demo --offline --yes
```

Bedrock is optional. With keys: `python -m tero tui` using Nova Lite.

## Language policy

The **product** (TUI, CLI output, generated classroom artifacts) is in **Spanish**,
because tero is built for Chilean teachers. Everything judge-facing — this pack,
the README, ARCHITECTURE, the benchmark paper and the judge guide — is in
**English**.
