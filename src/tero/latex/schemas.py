"""JSON schemas + repair for small models (Nova Lite). Never ask the model for raw TeX."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tero.artifacts import REQUIRED_HEADINGS
from tero.config import PACKAGE_ROOT
from tero.types import ArtifactType

SCHEMAS_ROOT = PACKAGE_ROOT / "templates" / "latex" / "schemas"

SCHEMA_TYPES = ("guia", "evaluacion", "planificacion", "pauta", "beamer", "actividad")

_DEFAULTS: dict[str, dict[str, Any]] = {
    "guia": {
        "tipo": "guia",
        "titulo": "Guía",
        "curso": "",
        "asignatura": "",
        "oa": "",
        "oa_texto": "",
        "tiempo": "",
        "proposito": "",
        "materiales": [],
        "instrucciones": [],
        "sm_items": [],
        "vf_items": [],
        "desarrollo_prompts": [],
        "actividades": [],
        "cierre": "",
    },
    "evaluacion": {
        "tipo": "evaluacion",
        "titulo": "Evaluación",
        "curso": "",
        "asignatura": "",
        "oa": "",
        "oa_texto": "",
        "puntaje_total": "",
        "instrucciones": [],
        "items": [],
        "criterios": [],
        "nota_docente": "",
    },
    "planificacion": {
        "tipo": "planificacion",
        "titulo": "Planificación",
        "curso": "",
        "asignatura": "",
        "oa": "",
        "oa_texto": "",
        "duracion": "",
        "objetivo": "",
        "inicio": "",
        "desarrollo": "",
        "cierre": "",
        "evaluacion": "",
        "recursos": [],
    },
    "pauta": {
        "tipo": "pauta",
        "titulo": "Pauta",
        "curso": "",
        "asignatura": "",
        "oa": "",
        "oa_texto": "",
        "niveles": ["Inicial", "En proceso", "Logrado"],
        "criterios": [],
        "lineamientos_nota": "",
    },
    "beamer": {
        "tipo": "beamer",
        "titulo": "Presentación",
        "subtitulo": "",
        "autor": "tero",
        "slides": [],
    },
    "actividad": {
        "tipo": "guia",  # actividad reuses guía layout
        "titulo": "Actividad",
        "curso": "",
        "asignatura": "",
        "oa": "",
        "oa_texto": "",
        "tiempo": "",
        "proposito": "",
        "materiales": [],
        "instrucciones": [],
        "sm_items": [],
        "vf_items": [],
        "desarrollo_prompts": [],
        "actividades": [],
        "cierre": "",
    },
}


def load_schema(tipo: str) -> dict[str, Any]:
    key = _schema_key(tipo)
    path = SCHEMAS_ROOT / f"{key}.json"
    if not path.exists():
        return {"title": key, "type": "object"}
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_key(tipo: str) -> str:
    raw = (tipo or "").strip().lower()
    aliases = {
        "guía": "guia",
        "guia": "guia",
        "evaluación": "evaluacion",
        "evaluacion": "evaluacion",
        "planificación": "planificacion",
        "planificacion": "planificacion",
        "plan": "planificacion",
        "pauta": "pauta",
        "rúbrica": "pauta",
        "rubrica": "pauta",
        "beamer": "beamer",
        "actividad": "actividad",
    }
    return aliases.get(raw, raw if raw in SCHEMA_TYPES else "guia")


def repair_payload(tipo: str, raw: dict[str, Any] | str | None) -> dict[str, Any]:
    """Coerce Nova-Lite-ish JSON into a template-ready dict."""
    key = _schema_key(tipo)
    base = dict(_DEFAULTS.get(key, _DEFAULTS["guia"]))
    data: dict[str, Any]
    if raw is None:
        data = {}
    elif isinstance(raw, str):
        data = _parse_json_blob(raw)
    elif isinstance(raw, dict):
        data = dict(raw)
    else:
        data = {}
    # nested under payload/data common mistake
    for nest in ("payload", "data", "artifact", "json"):
        inner = data.get(nest)
        if isinstance(inner, dict) and "titulo" in inner:
            data = inner
            break
    merged = {**base, **{k: v for k, v in data.items() if v is not None}}
    merged["tipo"] = "guia" if key == "actividad" else key
    # stringify scalars that templates expect as text
    for field in (
        "titulo",
        "curso",
        "asignatura",
        "oa",
        "oa_texto",
        "tiempo",
        "proposito",
        "cierre",
        "objetivo",
        "inicio",
        "desarrollo",
        "evaluacion",
        "duracion",
        "nota_docente",
        "lineamientos_nota",
        "subtitulo",
        "autor",
    ):
        if field in merged and not isinstance(merged[field], (list, dict)):
            merged[field] = str(merged[field]).strip()
    if "puntaje_total" in merged:
        merged["puntaje_total"] = str(merged.get("puntaje_total") or "")
    for list_field in (
        "materiales",
        "instrucciones",
        "desarrollo_prompts",
        "recursos",
        "niveles",
    ):
        merged[list_field] = _as_str_list(merged.get(list_field))
    if key == "evaluacion":
        merged["criterios"] = _as_str_list(merged.get("criterios"))
    if key in {"guia", "actividad"}:
        merged["sm_items"] = _as_sm_items(merged.get("sm_items"))
        merged["vf_items"] = _as_vf_items(merged.get("vf_items"))
        merged["actividades"] = _as_actividades(merged.get("actividades"))
        has_items = bool(merged["sm_items"] or merged["vf_items"] or merged["desarrollo_prompts"])
        if not merged["actividades"] and merged.get("proposito") and not has_items:
            merged["actividades"] = [
                {
                    "titulo": "Actividad principal",
                    "inicio": "",
                    "desarrollo": merged.get("proposito") or "",
                    "cierre": merged.get("cierre") or "",
                }
            ]
    if key == "evaluacion":
        merged["items"] = _as_eval_items(merged.get("items"))
        if isinstance(merged.get("criterios"), list) and merged["criterios"]:
            # criterios may be objects; normalize to strings for template list
            fixed: list[str] = []
            for row in merged["criterios"]:
                if isinstance(row, dict):
                    fixed.append(str(row.get("nombre") or row.get("texto") or row))
                else:
                    fixed.append(str(row))
            merged["criterios"] = fixed
    if key == "planificacion":
        for field in ("objetivo", "inicio", "desarrollo", "cierre", "evaluacion"):
            merged[field] = _as_plan_prose(merged.get(field))
    if key == "pauta":
        merged["criterios"] = _as_pauta_criterios(merged.get("criterios"))
        if not merged.get("niveles"):
            merged["niveles"] = ["Inicial", "En proceso", "Logrado"]
    if key == "beamer":
        merged["slides"] = _as_slides(merged.get("slides"))
    if not merged.get("titulo"):
        merged["titulo"] = base.get("titulo") or key
    return merged


def parse_payload_json(tipo: str, raw: Any) -> dict[str, Any] | None:
    """Parse optional draft_artifact payload_json. Empty or garbage → None (markdown stays)."""
    if raw is None or raw == "":
        return None
    if isinstance(raw, dict):
        data: dict[str, Any] | None = raw
    elif isinstance(raw, (list, tuple)):
        text = "\n".join(str(item) for item in raw).strip()
        data = _parse_json_blob(text) if text else None
    else:
        text = str(raw).strip()
        if not text:
            return None
        data = _parse_json_blob(text)
    if not data:
        return None
    return repair_payload(tipo, data)


def validate_payload(tipo: str, payload: dict[str, Any]) -> list[str]:
    """Lightweight required-field check (no jsonschema dependency)."""
    key = _schema_key(tipo)
    schema = load_schema(key if key != "actividad" else "guia")
    required = list(schema.get("required") or [])
    if key == "actividad":
        required = ["tipo", "titulo", "proposito", "actividades"]
    errors: list[str] = []
    for field in required:
        value = payload.get(field)
        if value is None or value == "" or value == []:
            errors.append(f"falta campo requerido: {field}")
    return errors


def extract_payload_from_markdown(
    markdown: str,
    *,
    tipo: str | ArtifactType | None = None,
    meta: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Best-effort markdown → schema dict (export path for existing drafts)."""
    meta = meta or {}
    body = markdown or ""
    # Prefer fenced JSON block if Nova Lite / host stored one
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", body, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        parsed = _parse_json_blob(fenced.group(1))
        if parsed:
            inferred = str(parsed.get("tipo") or tipo or "guia")
            payload = repair_payload(inferred, parsed)
            _apply_meta(payload, meta, body)
            md_only = _strip_json_fence(body)
            if md_only.strip() and md_only.strip() != (markdown or "").strip():
                filled = extract_payload_from_markdown(md_only, tipo=inferred, meta=meta)
                _fill_empty_fields(payload, filled)
            return payload

    art = ArtifactType.parse(str(tipo) if tipo else None)
    if art is None:
        fm_tipo = _front_matter_value(body, "tipo")
        art = ArtifactType.parse(fm_tipo) or ArtifactType.GUIA
    key = art.value
    body = _strip_host_appendix(body)
    sections = _split_sections(body)
    titulo = _first_heading(body) or meta.get("titulo") or art.label.capitalize()

    if art == ArtifactType.PLANIFICACION:
        raw = {
            "tipo": "planificacion",
            "titulo": titulo,
            "objetivo": sections.get("objetivo") or sections.get("objetivos") or "",
            "inicio": sections.get("inicio") or "",
            "desarrollo": sections.get("desarrollo") or "",
            "cierre": sections.get("cierre") or "",
            "evaluacion": sections.get("evaluacion")
            or sections.get("evaluación")
            or sections.get("criterios")
            or "",
            "recursos": _bullets(sections.get("recursos") or sections.get("materiales") or ""),
            "oa": meta.get("oa") or _front_matter_value(body, "oa") or "",
            "duracion": meta.get("duracion") or _front_matter_value(body, "duracion") or "",
        }
    elif art == ArtifactType.EVALUACION:
        extracted = body
        items_from_sections = _eval_items_from_typed_sections(sections)
        if items_from_sections:
            items = items_from_sections
        else:
            items = _eval_items_from_markdown(
                sections.get("items") or sections.get("preguntas") or sections.get("sm") or "",
                vf_md=sections.get("vf") or "",
                desarrollo_md=sections.get("desarrollo") or "",
            )
        if not any(row.get("tipo_item") == "sm" for row in items):
            extra = _eval_items_from_heading_blocks(extracted)
            sm_extra = [row for row in extra if row.get("tipo_item") == "sm"]
            if sm_extra:
                others = [row for row in items if row.get("tipo_item") != "sm"]
                items = sm_extra + others
        if not items:
            items = _eval_items_from_heading_blocks(extracted)
        raw = {
            "tipo": "evaluacion",
            "titulo": titulo,
            "instrucciones": _bullets(sections.get("instrucciones") or ""),
            "items": items,
            "criterios": _bullets(sections.get("criterios") or ""),
            "puntaje_total": _guess_puntaje(
                sections.get("puntaje") or sections.get("puntaje total") or ""
            ),
            "nota_docente": sections.get("nota") or "",
        }
    elif art == ArtifactType.PAUTA:
        raw = {
            "tipo": "pauta",
            "titulo": titulo,
            "niveles": _bullets(sections.get("niveles") or "")
            or ["Inicial", "En proceso", "Logrado"],
            "criterios": _pauta_from_section(
                sections.get("criterios") or sections.get("descriptores") or ""
            ),
            "lineamientos_nota": sections.get("nota") or "",
        }
    else:
        # guía / actividad
        actividades: list[dict[str, str]] = []
        if sections.get("actividades"):
            actividades.append(
                {
                    "titulo": "Actividades",
                    "inicio": sections.get("inicio") or "",
                    "desarrollo": sections.get("actividades"),
                    "cierre": "",
                }
            )
        if sections.get("vf"):
            actividades.append(
                {
                    "titulo": "Verdadero o falso",
                    "inicio": "",
                    "desarrollo": sections["vf"],
                    "cierre": "",
                }
            )
        if sections.get("completar"):
            actividades.append(
                {
                    "titulo": "Completar",
                    "inicio": "",
                    "desarrollo": sections["completar"],
                    "cierre": "",
                }
            )
        if not actividades:
            actividades = [
                {
                    "titulo": "Secuencia",
                    "inicio": sections.get("inicio") or "",
                    "desarrollo": sections.get("desarrollo") or "",
                    "cierre": sections.get("cierre") or "",
                }
            ]
        raw = {
            "tipo": "guia",
            "titulo": titulo,
            "proposito": sections.get("proposito")
            or sections.get("propósito")
            or sections.get("objetivo")
            or "",
            "instrucciones": _bullets(sections.get("instrucciones") or ""),
            "materiales": _bullets(sections.get("materiales") or ""),
            "desarrollo_prompts": _bullets(sections.get("desarrollo") or ""),
            "actividades": actividades,
            "sm_items": _sm_from_section(sections.get("sm") or ""),
            "vf_items": _vf_from_section(sections.get("vf") or ""),
            "cierre": sections.get("cierre") or "",
            "tiempo": meta.get("duracion") or "",
        }
    payload = repair_payload(key, raw)
    _apply_meta(payload, meta, body)
    # ensure required headings awareness for thin drafts
    if art in REQUIRED_HEADINGS and not payload.get("titulo"):
        payload["titulo"] = art.label
    return payload


def _apply_meta(payload: dict[str, Any], meta: dict[str, str], body: str) -> None:
    for key in ("curso", "asignatura", "oa", "duracion", "tiempo"):
        if not payload.get(key):
            payload[key] = meta.get(key) or _front_matter_value(body, key) or ""
    if payload.get("duracion") and not payload.get("tiempo"):
        payload["tiempo"] = payload["duracion"]


def _parse_json_blob(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if not text:
        return {}
    # strip markdown fences leftovers
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # try to find first object
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
    return data if isinstance(data, dict) else {}


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip("-• \t") for line in value.splitlines() if line.strip()]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                name = str(
                    item.get("nombre")
                    or item.get("texto")
                    or item.get("label")
                    or item.get("criterio")
                    or ""
                ).strip()
                desc = str(
                    item.get("descripcion") or item.get("descriptor") or item.get("detalle") or ""
                ).strip()
                if name and desc and desc != name:
                    out.append(f"{name}: {desc}")
                elif name or desc:
                    out.append(name or desc)
            else:
                text = str(item).strip()
                if text:
                    out.append(text)
        return out
    return [str(value)]


def _as_vf_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    items: list[dict[str, Any]] = []
    for row in value:
        if isinstance(row, str):
            parsed = _vf_statement(row)
            if parsed:
                items.append(parsed)
            continue
        if not isinstance(row, dict):
            continue
        parsed = _vf_statement(str(row.get("enunciado") or row.get("texto") or "").strip())
        if not parsed:
            continue
        if row.get("clave"):
            parsed["clave"] = str(row.get("clave") or "").strip()[:8]
        items.append(parsed)
    return [item for item in items if item["enunciado"]]


def _as_sm_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    items: list[dict[str, Any]] = []
    for row in value:
        if isinstance(row, str):
            items.append({"enunciado": row, "opciones": [], "clave": ""})
            continue
        if not isinstance(row, dict):
            continue
        items.append(
            {
                "enunciado": str(row.get("enunciado") or row.get("pregunta") or "").strip(),
                "opciones": _as_str_list(row.get("opciones")),
                "clave": str(row.get("clave") or "").strip(),
            }
        )
    return [item for item in items if item["enunciado"]]


def _as_actividades(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, str]] = []
    for row in value:
        if isinstance(row, str):
            out.append({"titulo": row, "inicio": "", "desarrollo": "", "cierre": ""})
            continue
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "titulo": str(row.get("titulo") or "Actividad").strip(),
                "inicio": str(row.get("inicio") or "").strip(),
                "desarrollo": str(row.get("desarrollo") or "").strip(),
                "cierre": str(row.get("cierre") or "").strip(),
            }
        )
    return out


def _as_eval_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for row in value:
        if isinstance(row, str):
            out.append({"tipo_item": "desarrollo", "enunciado": row, "puntaje": "", "opciones": []})
            continue
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "tipo_item": str(row.get("tipo_item") or row.get("tipo") or "desarrollo"),
                "enunciado": str(row.get("enunciado") or "").strip(),
                "puntaje": str(row.get("puntaje") or ""),
                "opciones": _as_str_list(row.get("opciones")),
                "clave": str(row.get("clave") or "").strip(),
            }
        )
    return [item for item in out if item["enunciado"]]


def _as_pauta_criterios(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for row in value:
        if isinstance(row, str):
            out.append({"nombre": row, "descriptores": []})
            continue
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "nombre": str(row.get("nombre") or row.get("criterio") or "").strip(),
                "descriptores": _as_str_list(row.get("descriptores")),
            }
        )
    return [item for item in out if item["nombre"]]


def _as_slides(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for row in value:
        if isinstance(row, str):
            out.append({"titulo": row, "bullets": []})
            continue
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "titulo": str(row.get("titulo") or "").strip(),
                "bullets": _as_str_list(row.get("bullets")),
            }
        )
    return [item for item in out if item["titulo"]]


# Canonical keys the markdown→schema extractor understands.
# Longer aliases first so "objetivo de aprendizaje" wins over a bare prefix check.
_SECTION_ALIASES: tuple[tuple[str, str], ...] = (
    ("objetivo de aprendizaje", "objetivo"),
    ("objetivos de aprendizaje", "objetivo"),
    ("objetivo general", "objetivo"),
    ("evaluación formativa", "evaluacion"),
    ("evaluacion formativa", "evaluacion"),
    ("criterios de éxito", "evaluacion"),
    ("criterios de exito", "evaluacion"),
    ("objetivo", "objetivo"),
    ("objetivos", "objetivo"),
    ("inicio", "inicio"),
    ("desarrollo", "desarrollo"),
    ("cierre", "cierre"),
    ("evaluación", "evaluacion"),
    ("evaluacion", "evaluacion"),
    ("recursos", "recursos"),
    ("materiales", "materiales"),
    ("instrucciones", "instrucciones"),
    ("propósito", "proposito"),
    ("proposito", "proposito"),
    ("selección múltiple", "sm"),
    ("seleccion multiple", "sm"),
    ("ítems de selección", "sm"),
    ("items de seleccion", "sm"),
    ("verdadero o falso", "vf"),
    ("verdadero/falso", "vf"),
    ("ítems de desarrollo", "desarrollo"),
    ("items de desarrollo", "desarrollo"),
    ("completar", "completar"),
    ("actividades", "actividades"),
    ("ítems", "items"),
    ("items", "items"),
    ("preguntas", "preguntas"),
    ("criterios", "criterios"),
    ("descriptores", "descriptores"),
    ("niveles", "niveles"),
    ("puntaje total", "puntaje"),
    ("puntaje", "puntaje"),
    ("nota", "nota"),
    ("evidencia", "_host"),
)


def _canonical_section_key(title: str) -> str | None:
    """Map '## 1. Inicio (8-10 min)' / '#### Objetivo' onto schema field names."""
    raw = title.strip().lower()
    raw = re.sub(r"^\*+\s*", "", raw)
    raw = re.sub(r"\s*\*+$", "", raw)
    raw = raw.replace("**", "").strip()
    raw = re.sub(r"^[^a-záéíóúñü0-9]+", "", raw)
    raw = re.sub(r"^[ivxlcdm]+\.\s+", "", raw)
    raw = re.sub(r"^[\d]+(?:\.[\d]+)*[.)]\s*", "", raw)
    raw = re.sub(r"^[\d]+\s+", "", raw)
    for alias, key in _SECTION_ALIASES:
        if raw == alias:
            return key
        if raw.startswith(alias) and (len(raw) == len(alias) or raw[len(alias)] in " \t(-–—:."):
            return key
    folded = (
        raw.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    if "seleccion multiple" in folded or "items de seleccion" in folded:
        return "sm"
    if "verdadero" in folded and "falso" in folded:
        return "vf"
    if "items de desarrollo" in folded or folded.startswith("desarrollo "):
        return "desarrollo"
    return None


def _split_sections(markdown: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = "_preamble"
    chunks: dict[str, list[str]] = {current: []}
    for line in markdown.splitlines():
        heading = re.match(r"^#{1,6}\s+(.*)$", line.strip())
        if heading:
            key = _canonical_section_key(heading.group(1))
            if key is not None:
                current = key
                chunks.setdefault(current, [])
                continue
            # Nested unknown heading (### Lectura guiada): keep as body.
            chunks.setdefault(current, []).append(line)
            continue
        chunks.setdefault(current, []).append(line)
    for key, lines in chunks.items():
        sections[key] = "\n".join(lines).strip()
    return sections


def _first_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("#"):
            return re.sub(r"^#+\s*", "", line).strip()
    return ""


def _front_matter_value(markdown: str, key: str) -> str:
    if not markdown.startswith("---"):
        return ""
    end = markdown.find("\n---", 3)
    block = markdown[3:end] if end != -1 else ""
    for line in block.splitlines():
        if ":" in line:
            name, value = line.split(":", 1)
            if name.strip() == key:
                return value.strip().strip("\"'")
    return ""


def _strip_json_fence(markdown: str) -> str:
    return re.sub(
        r"```json\s*\{.*?\}\s*```",
        "",
        markdown or "",
        flags=re.DOTALL | re.IGNORECASE,
    )


def _fill_empty_fields(dst: dict[str, Any], src: dict[str, Any]) -> None:
    for key, value in src.items():
        if key in {"tipo"}:
            continue
        current = dst.get(key)
        empty = current is None or current == "" or current == [] or current == {}
        incoming_empty = value is None or value == "" or value == [] or value == {}
        if empty and not incoming_empty:
            dst[key] = value


def _as_plan_prose(value: Any) -> str:
    """Turn nested plan JSON (momentos, actividades, ítems) into classroom prose."""
    if value is None:
        return ""
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and ("titulo" in text or "actividades" in text):
            return text  # leftover repr; caller should pass dicts
        return text
    if isinstance(value, list):
        parts = [_as_plan_prose(item) for item in value]
        return "\n\n".join(part for part in parts if part)
    if not isinstance(value, dict):
        return str(value).strip()
    pregunta = str(value.get("pregunta") or value.get("enunciado") or "").strip()
    if pregunta:
        opts = value.get("opciones") or []
        if isinstance(opts, list) and opts:
            letters = "abcd"
            lines = [pregunta]
            for idx, opt in enumerate(opts[:8]):
                letter = letters[idx] if idx < len(letters) else str(idx + 1)
                lines.append(f"{letter}) {opt}")
            return "\n".join(lines)
        return pregunta
    chunks: list[str] = []
    titulo = str(value.get("titulo") or value.get("nombre") or "").strip()
    duracion = str(value.get("duracion") or value.get("tiempo") or "").strip()
    if titulo and duracion:
        chunks.append(f"{titulo} ({duracion})")
    elif titulo:
        chunks.append(titulo)
    for key in (
        "objetivo",
        "descripcion",
        "detalle",
        "texto",
        "prosa",
        "inicio",
        "desarrollo",
        "cierre",
        "actividades",
        "pasos",
        "items",
        "momentos",
        "items_ticket_salida",
    ):
        if key not in value:
            continue
        nested = value[key]
        if nested is value:
            continue
        chunk = _as_plan_prose(nested)
        if chunk and chunk not in chunks:
            chunks.append(chunk)
    if chunks:
        return "\n\n".join(chunks)
    bits: list[str] = []
    for key, nested in value.items():
        if key in {"id", "tipo", "clave", "respuesta_correcta"}:
            continue
        chunk = _as_plan_prose(nested)
        if chunk:
            bits.append(chunk)
    return "\n".join(bits)


def _strip_host_appendix(markdown: str) -> str:
    """Drop host-added evidence so export does not parse it as ítems."""
    text = markdown or ""
    cut = re.search(r"^##\s+Evidencia\b", text, flags=re.MULTILINE | re.IGNORECASE)
    if cut:
        text = text[: cut.start()]
    return text.rstrip() + ("\n" if text.strip() else "")


def _is_answer_chrome(text: str) -> bool:
    cleaned = re.sub(r"^[\s☐\[\]\*#_]+", "", (text or "").strip())
    if not cleaned:
        return True
    if re.match(
        r"^(respuesta(?:\s+correcta)?|justifica|puntaje total|nota:|clave)\b",
        cleaned,
        flags=re.IGNORECASE,
    ):
        return True
    compact = re.sub(r"[^a-záéíóúñü]", "", cleaned.lower())
    if compact in {"verdadero", "falso", "vf", "verdaderofalso"}:
        return True
    if "fuentes/" in cleaned.lower() and "verific" in cleaned.lower():
        return True
    return False


def _item_kind_from_heading(title: str) -> str | None:
    raw = (title or "").strip().lower()
    folded = (
        raw.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    if "seleccion multiple" in folded or "opcion multiple" in folded:
        return "sm"
    if "verdadero" in folded and "falso" in folded:
        return "vf"
    if "desarrollo" in folded:
        return "desarrollo"
    # ### 1. (3 puntos) — numbered stem without a kind word
    if re.match(r"^\d+[.)]", raw) and "punto" in folded:
        return "sm"
    return None


def _eval_items_from_typed_sections(sections: dict[str, str]) -> list[dict[str, Any]]:
    sm_md = sections.get("sm") or ""
    vf_md = sections.get("vf") or ""
    desarrollo_md = sections.get("desarrollo") or ""
    if not (sm_md or vf_md or desarrollo_md):
        return []
    return _eval_items_from_markdown(sm_md, vf_md=vf_md, desarrollo_md=desarrollo_md)


def _eval_items_from_heading_blocks(markdown: str) -> list[dict[str, Any]]:
    """Split ### 1. Selección múltiple / V-F / Desarrollo into typed items."""
    blocks: list[tuple[str, str]] = []
    current: str | None = None
    buf: list[str] = []
    for line in (markdown or "").splitlines():
        heading = re.match(r"^#{1,6}\s+(.*)$", line.strip())
        if heading:
            kind = _item_kind_from_heading(heading.group(1))
            if kind:
                if current is not None:
                    blocks.append((current, "\n".join(buf)))
                current = kind
                buf = []
                continue
        if current is not None:
            buf.append(line)
    if current is not None:
        blocks.append((current, "\n".join(buf)))
    out: list[dict[str, Any]] = []
    for kind, chunk in blocks:
        if kind == "sm":
            out.extend(_eval_items_from_markdown(chunk, vf_md="", desarrollo_md=""))
        elif kind == "vf":
            out.extend(_eval_items_from_markdown("", vf_md=chunk, desarrollo_md=""))
        else:
            out.extend(_eval_items_from_markdown("", vf_md="", desarrollo_md=chunk))
    return [
        row for row in out if row.get("enunciado") and not _is_answer_chrome(str(row["enunciado"]))
    ]


def _bullets(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        cleaned = re.sub(r"^[-*•]\s+", "", line.strip())
        cleaned = re.sub(r"^\d+\.\s+", "", cleaned)
        if cleaned and cleaned not in {"---", "***", "___", "-", "—", "–"}:
            items.append(cleaned)
    return items


def _sm_from_section(text: str) -> list[dict[str, Any]]:
    """Best-effort SM items from markdown (numbered stems + a/b/c options)."""
    if not (text or "").strip():
        return []
    items: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    preamble: list[str] = []
    for raw in text.splitlines():
        line = re.sub(r"^#+\s*", "", raw.strip())
        if not line or line in {"---", "***"}:
            continue
        if _is_answer_chrome(line):
            continue
        numbered = re.match(r"^(?:\*{0,2})(\d+)[.)](?:\*{0,2})\s+(.*)$", line)
        if numbered:
            if current and current.get("enunciado"):
                items.append(current)
            current = {"enunciado": numbered.group(2).strip(), "opciones": [], "clave": ""}
            preamble = []
            continue
        option = re.match(r"^([a-dA-D])[.)]\s+(.*)$", line)
        if option:
            if current is None:
                stem = " ".join(preamble).strip() or "Ítem"
                current = {"enunciado": stem, "opciones": [], "clave": ""}
                preamble = []
            current["opciones"].append(option.group(2).strip())
            continue
        clave = re.match(r"^(?:clave|correcta|respuesta)\s*[:\-]\s*(.+)$", line, flags=re.I)
        if clave and current is not None:
            current["clave"] = clave.group(1).strip()[:8]
            continue
        if current is not None and not current.get("opciones"):
            current["enunciado"] = (current["enunciado"] + " " + line).strip()
        elif current is None:
            preamble.append(line)
    if current and current.get("enunciado"):
        items.append(current)
    return [
        item
        for item in items
        if item["enunciado"] and (item["enunciado"] != "Ítem" or item.get("opciones"))
    ]


def _vf_statement(text: str) -> dict[str, str] | None:
    cleaned = (text or "").strip()
    if _is_answer_chrome(cleaned):
        return None
    if re.fullmatch(r"(v\s*/\s*f|respuesta.*|_+)", cleaned, flags=re.IGNORECASE):
        return None
    if len(cleaned) < 8:
        return None
    clave = ""
    tagged = re.search(
        r"[\(\[]\s*(V|F|verdadero|falso)\s*[\)\]]\s*$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if tagged:
        raw = tagged.group(1).lower()
        clave = "F" if raw.startswith("f") else "V"
        cleaned = cleaned[: tagged.start()].strip()
    keyed = re.search(
        r"(?:clave|respuesta)\s*[:\-]\s*(V|F|verdadero|falso)\s*$", cleaned, flags=re.I
    )
    if keyed:
        raw = keyed.group(1).lower()
        clave = "F" if raw.startswith("f") else "V"
        cleaned = cleaned[: keyed.start()].strip()
    return {"enunciado": cleaned, "clave": clave}


def _vf_from_section(text: str) -> list[dict[str, Any]]:
    if not (text or "").strip():
        return []
    items: list[dict[str, Any]] = []
    for bullet in _bullets(text):
        parsed = _vf_statement(bullet)
        if parsed:
            items.append(parsed)
    if not items:
        for para in re.split(r"\n\s*\n", text):
            parsed = _vf_statement(para.strip())
            if parsed:
                items.append(parsed)
                break
    return items


def _eval_items_from_markdown(
    items_md: str,
    *,
    vf_md: str = "",
    desarrollo_md: str = "",
) -> list[dict[str, Any]]:
    """Prefer SM/V-F structure when the evaluación markdown has it."""
    out: list[dict[str, Any]] = []
    sm = _sm_from_section(items_md)
    if sm:
        for row in sm:
            out.append(
                {
                    "tipo_item": "sm",
                    "enunciado": row["enunciado"],
                    "opciones": list(row.get("opciones") or []),
                    "puntaje": "",
                    "clave": row.get("clave") or "",
                }
            )
    elif items_md.strip() and not re.search(r"^[a-dA-D][.)]\s+", items_md, flags=re.MULTILINE):
        out.extend(_items_from_section(items_md))
    for row in _vf_from_section(vf_md):
        if _is_answer_chrome(row["enunciado"]):
            continue
        out.append(
            {
                "tipo_item": "vf",
                "enunciado": row["enunciado"],
                "opciones": ["Verdadero", "Falso"],
                "puntaje": "",
                "clave": row.get("clave") or "",
            }
        )
    for prompt in _desarrollo_prompts(desarrollo_md):
        out.append(
            {
                "tipo_item": "desarrollo",
                "enunciado": prompt,
                "opciones": [],
                "puntaje": "",
            }
        )
    return [row for row in out if not _is_answer_chrome(str(row.get("enunciado") or ""))]


def _desarrollo_prompts(text: str) -> list[str]:
    prompts: list[str] = []
    for bullet in _bullets(text):
        if not _is_answer_chrome(bullet):
            prompts.append(bullet)
    if prompts:
        return prompts
    paras = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    for para in paras:
        line = re.sub(r"\s+", " ", para).strip()
        line = re.sub(r"^\*+\s*|\s*\*+$", "", line)
        if line and not _is_answer_chrome(line) and line not in {"---", "***"}:
            return [line[:500]]
    return []


def _items_from_section(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for bullet in _bullets(text):
        items.append(
            {"tipo_item": "desarrollo", "enunciado": bullet, "puntaje": "", "opciones": []}
        )
    if not items and text.strip():
        items.append(
            {
                "tipo_item": "desarrollo",
                "enunciado": text.strip()[:500],
                "puntaje": "",
                "opciones": [],
            }
        )
    return items


def _pauta_from_section(text: str) -> list[dict[str, Any]]:
    return [{"nombre": item, "descriptores": []} for item in _bullets(text)]


def _guess_puntaje(text: str) -> str:
    match = re.search(r"(\d+)\s*(?:pts|puntos|ptos)?", text, flags=re.IGNORECASE)
    return match.group(1) if match else text.strip()[:40]


def schema_path_for(tipo: str) -> Path:
    return SCHEMAS_ROOT / f"{_schema_key(tipo)}.json"
