"""Tests unitarios y de integración para el banco pedagógico begonia.

Sin red externa. Las llamadas al banco se simulan con un transporte inyectado.
Incluye smoke test condicional contra el servidor local si está corriendo.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from tero.artifacts import materialize_markdown
from tero.begonia import (
    HOSTED_BASE_URL,
    BegoniaClient,
    banco_oa_code,
    compact_item_detail,
    compact_search_card,
    grade_filter,
    resolve_api_key,
    subject_filter,
)
from tero.config import Settings
from tero.evidence import collect_warnings, verify_evidence
from tero.tools import TurnContext, build_tools
from tero.types import (
    ArtifactDraft,
    ArtifactType,
    Encargo,
    Evidence,
    Propuesta,
)
from tero.workspace import Workspace

DUMMY_SUMMARY = {
    "snapshot_id": "20260911T023022Z-test",
    "created_at": "2026-09-11T02:30:32Z",
    "approved_count": 13722,
    "guidance_count": 1159,
    "reference_count": 7,
}

DUMMY_SEARCH = {
    "total": 1,
    "limit": 8,
    "offset": 0,
    "snapshot_id": "20260911T023022Z-test",
    "facets": {
        "type": {"student_activity": 1},
        "subject": {"Ciencias Naturales": 1},
        "grade": {"5° Básico": 1},
        "material_type": {"actividad": 1},
    },
    "items": [
        {
            "id": "item-arma-abierta-v2-1009",
            "type": "student_activity",
            "subject": "Ciencias Naturales",
            "grade": "5° Básico",
            "oa_code_primary": "CN05 OA 12",
            "stem": "¿Cuál es la importancia de los cuerpos de agua dulce?",
            "material_type": "actividad",
            "locator_kind": "nid",
            "formato": "pdf",
            "has_media": True,
            "updated_at": "2026-09-11T02:30:32Z",
        }
    ],
}

DUMMY_ITEM = {
    "id": "item-arma-abierta-v2-1009",
    "type": "student_activity",
    "stem": "¿Cuál es la importancia de los cuerpos de agua dulce?",
    "solution": "Pauta oficial completa con criterios y puntajes.",
    "pauta_kind": "respuesta",
    "subject": "Ciencias Naturales",
    "grade": "5° Básico",
    "oa_code_primary": "CN05 OA 12",
    "oa_codes": ["CN05 OA 12"],
    "material_type": "actividad",
    "license_note": "Uso educativo MINEDUC",
    "state": "approved",
    "student_facing": True,
    "metadata": {
        "title": "Cuerpos de agua dulce",
        "topics": ["hidrografía", "ecosistemas"],
    },
    "metadata_addenda": {
        "title": {
            "valor": "Cuerpos de agua dulce",
            "provenance_kind": "source_capture",
        },
        "topics": {
            "valor": ["hidrografía", "ecosistemas"],
            "provenance_kind": "inferred",
        },
    },
    "locator": {"url": "https://www.curriculumnacional.cl/item/1009", "kind": "nid"},
    "media": [
        {
            "name": "lamina-agua.pdf",
            "path": "media/lamina-agua.pdf",
            "url": "/v1/files?path=media/lamina-agua.pdf",
            "content_type": "application/pdf",
            "role": "primary",
        }
    ],
    "captures": [
        {
            "capture_id": "cap-1",
            "role": "source",
            "capture_kind": "pdf",
            "text": "OCR crudo que no debe ir al modelo.",
        }
    ],
    "snapshot_id": "20260911T023022Z-test",
}

DUMMY_FACETS = {
    "total": 13722,
    "snapshot_id": "20260911T023022Z-test",
    "facets": {
        "type": {"student_activity": 8000, "mc_question": 5000},
        "subject": {"Ciencias Naturales": 1200},
        "grade": {"5° Básico": 900},
        "material_type": {"actividad": 4000},
    },
}

DUMMY_GUIDANCE = {
    "total": 1,
    "snapshot_id": "20260911T023022Z-test",
    "guidance": [
        {
            "id": "guidance-1",
            "oa_code": "CN05 OA 12",
            "guidance_kind": "orientacion_didactica",
            "body_text": "Fomentar la observación y el registro de datos.",
        }
    ],
}


def make_fake_transport(responses: dict[str, tuple[int, dict[str, Any]]]):
    def fake_transport(url: str, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
        assert headers.get("X-Begonia-API-Key") == "secret-key"
        for path_prefix, (status, data) in responses.items():
            if path_prefix in url:
                return status, json.dumps(data).encode("utf-8")
        return 404, b'{"error": "not_found"}'

    return fake_transport


def test_client_sends_user_agent():
    seen: dict[str, str] = {}

    def capturing(url: str, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
        seen.update(headers)
        return 200, json.dumps(DUMMY_SUMMARY).encode("utf-8")

    client = BegoniaClient(base_url="http://fake-banco", api_key="secret-key", transport=capturing)
    reply = client.summary()
    assert reply.ok
    assert seen["X-Begonia-API-Key"] == "secret-key"
    assert seen["User-Agent"].startswith("tero/")


def test_resolve_api_key(tmp_path: Path):
    assert resolve_api_key(api_key="direct-key") == "direct-key"
    key_file = tmp_path / "keys.txt"
    key_file.write_text("# comentario\n\nkey-from-file\n# otra\nkey-2\n")
    assert resolve_api_key(key_file=key_file) == "key-from-file"
    assert resolve_api_key() == ""


def test_filters():
    assert grade_filter("5° básico") == "5° Básico"
    assert "," not in grade_filter("5° básico")
    assert subject_filter("lenguaje") == "Lenguaje y Comunicación"
    assert "," not in subject_filter("lenguaje")
    assert banco_oa_code("CN05 OA 12") == "CN05 OA 12"
    assert banco_oa_code("LEN-4B-OA04") == ""


def test_client_not_configured():
    client = BegoniaClient()
    assert not client.configured
    assert not client.available()
    assert client.snapshot_id() == ""
    reply = client.search("agua")
    assert not reply.ok
    assert not reply.disponible
    assert reply.code == "banco_no_configurado"


def test_client_endpoints():
    seen_urls: list[str] = []

    def tracking_transport(url: str, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
        seen_urls.append(url)
        return make_fake_transport(
            {
                "/v1/summary": (200, DUMMY_SUMMARY),
                "/v1/facets": (200, DUMMY_FACETS),
                "/v1/search": (200, DUMMY_SEARCH),
                "/v1/items/item-arma-abierta-v2-1009": (200, DUMMY_ITEM),
                "/v1/guidance": (200, DUMMY_GUIDANCE),
            }
        )(url, headers, timeout)

    client = BegoniaClient(
        base_url="http://fake-banco",
        api_key="secret-key",
        transport=tracking_transport,
    )
    assert client.configured
    assert client.available()
    assert client.snapshot_id() == "20260911T023022Z-test"

    facets_reply = client.facets()
    assert facets_reply.ok
    assert facets_reply.data["facets"]["grade"]["5° Básico"] == 900

    search_reply = client.search(
        "agua",
        grade="5° Básico",
        oa="CN05 OA 12",
        has_media=True,
        locator_kind="nid",
    )
    assert search_reply.ok
    assert len(search_reply.data["items"]) == 1
    search_urls = [url for url in seen_urls if "/v1/search" in url]
    assert search_urls
    assert "has_media=1" in search_urls[-1]
    assert "locator_kind=nid" in search_urls[-1]

    item_reply = client.item("item-arma-abierta-v2-1009", text=True)
    assert item_reply.ok
    assert item_reply.data["stem"].startswith("¿Cuál")
    assert item_reply.data["metadata"]["title"] == "Cuerpos de agua dulce"

    guidance_reply = client.guidance(oa="CN05 OA 12")
    assert guidance_reply.ok
    assert len(guidance_reply.data["guidance"]) == 1


def test_client_error_handling():
    def failing_transport(url: str, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
        if "timeout" in url:
            raise OSError("Connection timeout")
        if "401" in url:
            return 401, b'{"error": "unauthorized"}'
        if "forbidden" in url:
            return 403, b'{"error_code":1010}'
        if "missing" in url:
            return 404, b'{"error": "not_found"}'
        if "busy" in url:
            return 429, b'{"error": "rate_limited"}'
        return 500, b"Internal server error"

    client = BegoniaClient(
        base_url="http://fake-banco",
        api_key="secret-key",
        transport=failing_transport,
    )
    r1 = client.search("timeout")
    assert not r1.ok
    assert r1.code == "banco_sin_conexion"

    r2 = client.search("401")
    assert not r2.ok
    assert r2.code == "banco_no_autorizado"

    r_forbidden = client.search("forbidden")
    assert not r_forbidden.ok
    assert r_forbidden.code == "banco_bloqueado"

    r3 = client.search("err")
    assert not r3.ok
    assert r3.code == "banco_http_500"

    r4 = client.item("missing")
    assert not r4.ok
    assert r4.code == "banco_no_publicado"

    r5 = client.search("busy")
    assert not r5.ok
    assert r5.code == "banco_limite"


def test_tools_with_banco(workspace: Workspace):
    transport = make_fake_transport(
        {
            "/v1/summary": (200, DUMMY_SUMMARY),
            "/v1/search": (200, DUMMY_SEARCH),
            "/v1/items/item-arma-abierta-v2-1009": (200, DUMMY_ITEM),
            "/v1/guidance": (200, DUMMY_GUIDANCE),
        }
    )
    client = BegoniaClient(
        base_url="http://fake-banco",
        api_key="secret-key",
        transport=transport,
    )
    ctx = TurnContext(
        workspace=workspace,
        encargo=Encargo(curso="5° básico", asignatura="Ciencias Naturales"),
        banco=client,
    )
    tools = {t.tool_name: t for t in build_tools(ctx)}

    res_search = json.loads(tools["buscar_banco"](query="agua", oa="CN05 OA 12"))
    assert res_search["ok"] is True
    assert "item-arma-abierta-v2-1009" in ctx.banco_ids
    card = res_search["items"][0]
    assert card["material_type"] == "actividad"
    assert card["formato"] == "PDF"
    assert card["has_media"] is True
    assert "source_kind" not in card
    assert "thumb_url" not in card

    res_item = json.loads(tools["leer_item_banco"](id="banco:item-arma-abierta-v2-1009"))
    assert res_item["ok"] is True
    assert res_item["banco_path"] == "banco:item-arma-abierta-v2-1009"
    detail = res_item["item"]
    assert detail["title"] == "Cuerpos de agua dulce"
    assert detail["topics"] == ["hidrografía", "ecosistemas"]
    assert detail["pauta_kind"] == "respuesta"
    assert detail["locator_url"].startswith("https://")
    assert detail["media"][0]["name"] == "lamina-agua.pdf"
    assert "url" not in detail["media"][0]
    assert "captures" not in detail
    assert detail["metadata_addenda"]["title"]["provenance_kind"] == "source_capture"

    res_guidance = json.loads(tools["orientaciones_banco"](oa="CN05 OA 12"))
    assert res_guidance["ok"] is True
    assert len(res_guidance["guidance"]) == 1


def test_evidence_and_warnings_with_banco(workspace: Workspace):
    ctx = TurnContext(workspace=workspace, encargo=Encargo())
    ctx.banco_ids.add("item-arma-1009")

    ev_banco = Evidence(
        path="banco:item-arma-1009",
        snippet="importancia de los cuerpos de agua",
        seccion="desarrollo",
    )
    verified = verify_evidence(workspace, ev_banco, banco_ids=ctx.banco_ids)
    assert verified.verified is True

    draft = ArtifactDraft(
        tipo=ArtifactType.GUIA,
        titulo="Guía del Agua",
        cuerpo_markdown="# Guía\n\n## Propósito\nEstudio del agua.\n",
        evidencias=[verified],
        banco_snapshot="20260911T023022Z-test",
    )
    warnings = collect_warnings(
        workspace=workspace,
        encargo=ctx.encargo,
        draft=draft,
    )
    codes = {w.code for w in warnings}
    assert "unknown_source" not in codes
    assert "thin_evidence" not in codes
    assert "banco_cita_no_verificada" not in codes

    # Si se cita un id no servido en el turno:
    ev_unverified = Evidence(
        path="banco:item-no-servido",
        snippet="algo",
        seccion="inicio",
    )
    verified_bad = verify_evidence(workspace, ev_unverified, banco_ids=ctx.banco_ids)
    assert verified_bad.verified is False
    draft_bad = ArtifactDraft(
        tipo=ArtifactType.GUIA,
        titulo="Guía",
        cuerpo_markdown="# Guía\n\n## Propósito\nTest\n",
        evidencias=[verified_bad],
    )
    warnings_bad = collect_warnings(
        workspace=workspace,
        encargo=ctx.encargo,
        draft=draft_bad,
    )
    codes_bad = {w.code for w in warnings_bad}
    assert "banco_cita_no_verificada" in codes_bad


def test_materialize_markdown_includes_banco_snapshot(workspace: Workspace):
    ev = Evidence(
        path="banco:item-1",
        snippet="texto oficial",
        seccion="desarrollo",
        verified=True,
    )
    draft = ArtifactDraft(
        tipo=ArtifactType.GUIA,
        titulo="Guía con Banco",
        cuerpo_markdown="# Guía\n\n## Propósito\nOficial\n",
        evidencias=[ev],
        banco_snapshot="20260911T023022Z-test",
    )
    propuesta = Propuesta(accion="crear", draft=draft, resumen="Resumen")
    md = materialize_markdown(Encargo(curso="5° básico"), propuesta)
    assert "banco_snapshot: 20260911T023022Z-test" in md
    assert "banco pedagógico oficial (MINEDUC)" in md
    assert "verificada contra el banco oficial" in md


def test_compact_helpers_drop_binaries_and_keep_provenance():
    card = compact_search_card(DUMMY_SEARCH["items"][0])
    assert card["id"] == "item-arma-abierta-v2-1009"
    assert card["formato"] == "PDF"
    assert "solution" not in card

    detail = compact_item_detail(DUMMY_ITEM)
    assert detail["title"] == "Cuerpos de agua dulce"
    assert "captures" not in detail
    assert "url" not in detail["media"][0]
    assert detail["metadata_addenda"]["topics"]["provenance_kind"] == "inferred"


def test_leer_item_unpublished_hints_to_search(workspace: Workspace):
    def unpublished(_url: str, _headers: dict[str, str], _timeout: float) -> tuple[int, bytes]:
        return 404, b'{"error": "not_found"}'

    client = BegoniaClient(
        base_url="http://fake-banco",
        api_key="secret-key",
        transport=unpublished,
    )
    ctx = TurnContext(workspace=workspace, encargo=Encargo(), banco=client)
    tools = {t.tool_name: t for t in build_tools(ctx)}
    res = json.loads(tools["leer_item_banco"](id="banco:item-retirado"))
    assert res["ok"] is False
    assert res["code"] == "banco_no_publicado"
    assert "ya no está publicado" in res["hint"]


@pytest.mark.skipif(
    os.environ.get("RUN_BEGONIA_LIVE_TEST") != "1"
    or not (
        os.environ.get("TERO_BEGONIA_API_KEY", "").strip()
        or Path(os.environ.get("TERO_BEGONIA_KEY_FILE", "")).expanduser().is_file()
    ),
    reason="Requiere RUN_BEGONIA_LIVE_TEST=1 y TERO_BEGONIA_API_KEY o TERO_BEGONIA_KEY_FILE",
)
def test_begonia_live_smoke():
    settings = Settings(
        begonia_url=os.environ.get("TERO_BEGONIA_URL", "").strip() or HOSTED_BASE_URL,
        begonia_api_key=os.environ.get("TERO_BEGONIA_API_KEY", "").strip(),
        begonia_key_file=os.environ.get("TERO_BEGONIA_KEY_FILE", "").strip(),
    )
    client = BegoniaClient.from_settings(settings)
    assert client.configured
    assert client.available()
    summary = client.summary()
    assert summary.ok
    assert summary.data.get("snapshot_id")
    reply = client.search("comprensión lectora", limit=2)
    assert reply.ok
    assert len(reply.data.get("items", [])) > 0
    card = compact_search_card(reply.data["items"][0])
    assert card.get("id")
    facets = client.facets()
    assert facets.ok
    assert isinstance(facets.data.get("facets"), dict)
