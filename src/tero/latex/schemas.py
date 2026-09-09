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
        merged["actividades"] = _as_actividades(merged.get("actividades"))
        if not merged["actividades"] and merged.get("proposito"):
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
    if key == "pauta":
        merged["criterios"] = _as_pauta_criterios(merged.get("criterios"))
        if not merged.get("niveles"):
            merged["niveles"] = ["Inicial", "En proceso", "Logrado"]
    if key == "beamer":
        merged["slides"] = _as_slides(merged.get("slides"))
    if not merged.get("titulo"):
        merged["titulo"] = base.get("titulo") or key
    return merged


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
            return payload

    art = ArtifactType.parse(str(tipo) if tipo else None)
    if art is None:
        fm_tipo = _front_matter_value(body, "tipo")
        art = ArtifactType.parse(fm_tipo) or ArtifactType.GUIA
    key = art.value
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
            "evaluacion": sections.get("evaluación") or sections.get("evaluacion") or "",
            "recursos": _bullets(sections.get("recursos") or sections.get("materiales") or ""),
            "oa": meta.get("oa") or _front_matter_value(body, "oa") or "",
            "duracion": meta.get("duracion") or _front_matter_value(body, "duracion") or "",
        }
    elif art == ArtifactType.EVALUACION:
        raw = {
            "tipo": "evaluacion",
            "titulo": titulo,
            "instrucciones": _bullets(sections.get("instrucciones") or ""),
            "items": _items_from_section(
                sections.get("ítems") or sections.get("items") or sections.get("preguntas") or ""
            ),
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
        raw = {
            "tipo": "guia",
            "titulo": titulo,
            "proposito": sections.get("propósito")
            or sections.get("proposito")
            or sections.get("objetivo")
            or "",
            "instrucciones": _bullets(sections.get("instrucciones") or ""),
            "materiales": _bullets(sections.get("materiales") or ""),
            "desarrollo_prompts": _bullets(
                sections.get("desarrollo") or sections.get("actividades") or ""
            ),
            "actividades": [
                {
                    "titulo": "Secuencia",
                    "inicio": sections.get("inicio") or "",
                    "desarrollo": sections.get("desarrollo") or sections.get("actividades") or "",
                    "cierre": sections.get("cierre") or "",
                }
            ],
            "sm_items": [],
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
                out.append(str(item.get("texto") or item.get("label") or item))
            else:
                text = str(item).strip()
                if text:
                    out.append(text)
        return out
    return [str(value)]


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


def _split_sections(markdown: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = "_preamble"
    chunks: dict[str, list[str]] = {current: []}
    for line in markdown.splitlines():
        heading = re.match(r"^#{1,3}\s+(.*)$", line.strip())
        if heading:
            current = heading.group(1).strip().lower()
            chunks.setdefault(current, [])
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


def _bullets(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        cleaned = re.sub(r"^[-*•]\s+", "", line.strip())
        cleaned = re.sub(r"^\d+\.\s+", "", cleaned)
        if cleaned:
            items.append(cleaned)
    return items


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
