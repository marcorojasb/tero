# Video script — ≤ 5 minutes

Upload to **YouTube or Vimeo, public**. No need to appear on camera.
Voiceover in **English** (judges). On-screen UI stays Spanish.

Say out loud, once: **the 2-minute offline path uses `tero-offline`, a
scripted Strands model, not a live Bedrock call.** Then, if keys work,
20–40 s of Nova Lite.

## 0:00–0:40 — problem / who / why

Teachers don’t need another chatbot. They need tomorrow’s photocopy
from **this** folder: the story they actually read, the OA they marked,
the vocabulary of this week.

tero prepares. The teacher decides. Keys: `s` sí, `n` no, `b` borrador,
`c` corregir.

Track: Professional Agents.

## 0:40–1:10 — architecture (one slide)

Show `docs/hackathon/architecture.png`.

- Teacher types an encargo; tero (Strands) reads the folder and stops
- Nova Lite infers the draft; the classroom folder never goes to AWS
- `s` writes `derivados/`, `b` writes `borradores/`. Originals stay put
- `n` discards, `c` asks for another pass

One sentence: AgentCore is optional sketch, not the folder.

## 1:10–3:10 — working demo (offline, honest)

Terminal:

```bash
python -m tero demo --offline --yes
```

Cut to TUI if recorded (`python -m tero tui --offline`):

1. Splash + rumbo `1` Planificar
2. Encargo chips (curso / OA)
3. Plan card → `a`
4. Evidence panel (`✓` / `?`)
5. Gate `s` — file appears under `derivados/`
6. Optional `/export latex`

Show `git status` or a hash: `fuentes/` unchanged.

## 3:10–4:00 — live Bedrock (if it works)

```bash
python -m tero tui
```

Same loop, label **Amazon Nova Lite**. If it fails, do **not** pretend.
Stay on offline and say Bedrock is the live path in the README.

Optional 10 s: AgentCore playground on **Nova Lite**, Browser off.
Caption: “AWS sketch — product remains local.”

## 4:00–4:40 — impact

One teacher, one folder, pages for tomorrow. Catalog is host-side
Chile OA (paraphrase, not MINEDUC verbatim). Warnings visible, never
blocking `s`.

## 4:40–5:00 — close

Repo: github.com/marcorojasb/tero
`pip install -e ".[dev]"` → `python -m tero demo --offline --yes`
MIT. #AgentsforHumans

## Don’t

- Call offline “Bedrock”.
- Call the harness “tero in production”.
- Show AWS keys.
- Block `s` with a lecture about quality.
