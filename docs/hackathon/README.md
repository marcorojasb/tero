# Agents for Humans — pack de postulación

Cierre: **lunes 14 septiembre 2026, 17:00 PDT**.
Créditos USD 50: formulario hasta **viernes 11 sep 2026, 12:00 PT**.

Cómo no gastar de más: [../AWS-GRATIS.md](../AWS-GRATIS.md).

## Estado

- [x] Repo público MIT: <https://github.com/marcorojasb/tero>
- [x] README + arquitectura en el repo
- [x] Inscrito en Devpost (submission empezado)
- [x] Cuenta AWS Free plan (us-east-1)
- [ ] Pedir USD 50 si el form sigue abierto: <https://forms.gle/6sjzKiX6bKUMA5NEA>
- [ ] Builder ID: <https://profile.aws.amazon.com>
- [ ] Pegar texto Devpost: [DEVPOST.md](DEVPOST.md)
- [ ] Subir diagrama: [architecture.png](architecture.png)
- [ ] Video ≤ 5 min (YouTube o Vimeo público): [VIDEO.md](VIDEO.md)
- [ ] Live demo: <https://marcorojasb.github.io/tero/> (si 404, enciende Pages)
- [ ] Post bonus `#AgentsforHumans`: [BUILDER-POST.md](BUILDER-POST.md)
- [ ] About del repo: Homepage = Pages; topics `strands-agents`, `amazon-bedrock`

## Archivos

| Archivo | Para |
| --- | --- |
| [JUDGES-EN.md](JUDGES-EN.md) | **Guía de jueces en inglés**: qué es / qué no es, puerta humana, uso de AWS, track A offline y B Bedrock con salidas reales, y tests. |
| [DEVPOST.md](DEVPOST.md) | Descripción EN para jueces (copiar/pegar) |
| [VIDEO.md](VIDEO.md) | Guion ≤ 5 min |
| [BUILDER-POST.md](BUILDER-POST.md) | Artículo Builder Center |
| [harness-playground.md](harness-playground.md) | Qué pegar en AgentCore (sketch, no el producto) |
| [architecture.png](architecture.png) | Diagrama para Devpost (regenerar: `python docs/hackathon/render_architecture.py`) |
| [architecture.svg](architecture.svg) | Misma arquitectura en vector |
| [iam-bedrock-minimo.json](iam-bedrock-minimo.json) | IAM lean |
| [budget-tero.json](budget-tero.json) | Alerta de gasto |

## Track

**Professional Agents.** El usuario primario es una o un docente, no un
curso entero (eso sería Good Neighbor). El brief de Devpost nombra a
teachers que convierten una clase en material para treinta alumnas.

## Lo que el juez tiene que poder hacer

```bash
git clone https://github.com/marcorojasb/tero.git
cd tero
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m tero demo --offline --yes
```

Bedrock es opcional. Si hay keys: `python -m tero tui` con Nova Lite.
