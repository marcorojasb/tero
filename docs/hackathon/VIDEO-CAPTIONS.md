# Video captions — canonical copy

Copy for the demo video, so on-screen text matches the product exactly. Two rules:

1. **The terminal is Spanish** — never subtitle over it in another language; the
   strings below marked *on screen* are the real ones from `tui/src/state.ts` and
   `tui/src/shell.ts`.
2. **The captions are English** — the video goes to English-speaking judges. Spanish
   belongs inside the terminal, English belongs in the framing.

Typography: use a **monospace** face (JetBrains Mono when available, otherwise the
same family the captured frames use). Do not set captions in a display sans — it
reads as a different product.

---

## Shot list

| # | Shot | On screen (Spanish, real) | Caption (English) |
| --- | --- | --- | --- |
| 1 | TUI home | `tero` · `tus fuentes, tu criterio` · `Pregunta, explora o crea…` | **The teacher's folder, not a chatbot** |
| 2 | Same | `El agente responde, crea o adapta · tú apruebas` | **Ask in plain Spanish** |
| 3 | Intent a: the teacher asks what is in the folder | thread | **It answers** |
| 4 | Intent b: request a 45-minute guide | `propuesta` card, `vista previa · markdown` | **Or it proposes a draft. In memory.** |
| 5 | Evidence panel | `evidencia` · `✓` / `?` · `avisos (no bloquean)` | **Every claim is checked against your files** |
| 6 | Decision bar | `¿escribo el archivo?   [y] aprobar   [n] descartar` | **Nothing is written until you say so** |
| 7 | Approval | `aprobado` → `escrito · …` | **You approve. The host writes.** |
| 8 | Photocopied sheet | rendered LaTeX pages | **A page for tomorrow's class** |
| 9 | Intent c: adapt | `apoyos y criterios NEE`, `origen` | **Adapt for NEE, Decreto 83** |
| 10 | After adaptation | new file; base untouched | **A new version. The original stays.** |
| 11 | Live Bedrock take | `amazon.nova-lite-v1:0` | **Live on Amazon Bedrock** |
| 12 | Close | `tero` · `MIT · github.com/marcorojasb/tero` | **Strands Agents. MIT. Open source.** |

## Cover captions

One line each, English, no colon-soup and no sentence fragments:

| Use | Text |
| --- | --- |
| Opening kicker | `TERO — A TEACHER AGENT FOR CHILEAN CLASSROOMS` |
| Thesis | `The agent proposes. The teacher decides.` |
| Privacy | `Student data never reaches the model` |
| Curriculum | `Grounded in the official MINEDUC bank` |
| Offline take | `Scripted model — not a Bedrock call` |
| Live take | `Live: amazon.nova-lite-v1:0` |
| Closing | `Your sources, your judgment` |

## Avoid

- Sentence fragments with symbols: `✓ en el archivo · ? parafraseo — avisos que no bloquean`.
- Mixed person and register: pick *the teacher* / *you*, never both in one card.
- Unaccented Spanish (`sin guion`, `aprobacion`) and lowercase sentence starts.
- Claiming Bedrock while the `tero-offline` label is on screen, and vice versa.
