# Video v2 — demos de landing (ES + EN)

> Generado y auditado fuera del repo (carpeta temporal) el 2026-09-13/14; builders en `scripts/video/build_landing_video_{es,en}_v2.py` (intermedios en temp, salidas a `site/assets/video/`).

# Reporte — Videos de landing tero · ES v5 + EN v1

Fecha: 2026-09-14 · Carpeta aislada: `/tmp/tero-video-v2/` · **El repo no se tocó.**

## Entregables

| Archivo | Duración | Peso | Loudness | Subtítulos |
| --- | --- | --- | --- | --- |
| `out/tero-demo-es.mp4` | 3:07.7 | 13,8 MB | −16.1 LUFS | 29 cues (`.srt`/`.vtt`) |
| `out/tero-demo-en.mp4` | 3:07.3 | 14,1 MB | −16.1 LUFS | 29 cues (`.srt`/`.vtt`) |

Builders: `build_es_v2.py` y `build_en_v2.py` (generado por `gen_en.py`;
voz `en-US-AndrewNeural`, audio en `audio_en/`). Ambos: `--full / --frame t / --plan / --no-music`.

## Pulido v5 (ES) — lo pedido

- **0:58 desborde en cuadros**: los títulos de los chips de arquitectura
  ("Strands Multi-Agent Graph" ≈ 255 px) no cabían en chips de 210 px. Chips
  ahora de 236 px con **wrap de título a ≤2 líneas medido con `text_w`**.
  Verificado en el mp4: 0 píxeles de texto más allá del borde; y por
  construcción: todas las líneas ≤ 208 px (ES y EN). (El modelo de visión
  "vio" un FAIL con nombres de chips que no existen — alucinación por escala;
  la medición determinista es la que manda.)
- Chips del cierre aparecen antes (con el tipeo, no con la frase 2) y caja de
  código más ancha.
- Sello: marco tenue "certificado del artefacto" desde el arranque (la derecha
  nunca queda vacía durante el tipeo).
- Trío: filas dim visibles desde 0,9 s.

## Versión EN

- Guion propio (no traducción literal), tono del guion oficial para jueces:
  pitch (problema/para quién/por qué) + demo + honestidad tero-offline +
  sello docente como diferenciador.
- **Política de idioma del repo respetada**: terminal y strings de producto en
  español (autenticidad); framing, captions y overlays en inglés. Los prompts
  tipeados en pantalla son los reales del producto («¿Qué tengo en la
  carpeta?», «Adapta la evaluación…») con caption EN que los traduce.
- Verificación de la clase de bug de 0:58 en EN: 0 px de overflow + anchos
  medidos ≤ 208 px.
- QC determinista a 12 timestamps (hero, privacidad, chips, intents, gate,
  placeholder sello, papel, NEE, trío, cierre): todos con contenido.

## QC global (ambos)

- 1080p30 H.264+AAC · faststart · ≤ 5:00 (regla hackathon) ✓
- −16.1 LUFS integrado ✓ · cues sin solape ✓
- Terminal reconstruido desde `tui/frames/*.json` · paleta `brand.json` ·
  queltehue oficial · onda del hero = envolvente RMS real de la voz.

## Reversibles

`VOICE` (Catalina/otra), `--no-music`, `SEAL_ID` (usar el real de
`.tero/decisiones/` tras `python -m tero demo --offline --yes`), guiones en
`SCENES`. `/tmp` se borra al reiniciar: mover la carpeta al aprobar.
