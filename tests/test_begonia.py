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
    BegoniaClient,
    banco_oa_code,
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
    "items": [
        {
            "id": "item-arma-abierta-v2-1009",
            "type": "student_activity",
            "subject": "Ciencias Naturales",
            "grade": "5° Básico",
            "oa_code_primary": "CN05 OA 12",
            "stem": "¿Cuál es la importancia de los cuerpos de agua dulce?",
            "solution": "Pauta oficial: criterio de evaluación...",
            "pauta_kind": "pauta_oficial_abierta",
            "source_kind": "arma_jsonapi",
        }
    ],
}

DUMMY_ITEM = {
    "id": "item-arma-abierta-v2-1009",
    "stem": "¿Cuál es la importancia de los cuerpos de agua dulce?",
    "solution": "Pauta oficial completa con criterios y puntajes.",
    "pauta_kind": "pauta_oficial_abierta",
    "source_kind": "arma_jsonapi",
    "subject": "Ciencias Naturales",
    "grade": "5° Básico",
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


def test_resolve_api_key(tmp_path: Path):
    assert resolve_api_key(api_key="direct-key") == "direct-key"
    key_file = tmp_path / "keys.txt"
    key_file.write_text("# comentario\n\nkey-from-file\n# otra\nkey-2\n")
    assert resolve_api_key(key_file=key_file) == "key-from-file"
    assert resolve_api_key() == ""


def test_filters():
    assert "5° Básico" in grade_filter("5° básico")
    assert "Lenguaje y Comunicación" in subject_filter("lenguaje")
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
    assert client.configured
    assert client.available()
    assert client.snapshot_id() == "20260911T023022Z-test"

    search_reply = client.search("agua", grade="5° Básico", oa="CN05 OA 12")
    assert search_reply.ok
    assert len(search_reply.data["items"]) == 1

    item_reply = client.item("item-arma-abierta-v2-1009", text=True)
    assert item_reply.ok
    assert item_reply.data["stem"].startswith("¿Cuál")

    guidance_reply = client.guidance(oa="CN05 OA 12")
    assert guidance_reply.ok
    assert len(guidance_reply.data["guidance"]) == 1


def test_client_error_handling():
    def failing_transport(url: str, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
        if "timeout" in url:
            raise OSError("Connection timeout")
        if "401" in url:
            return 401, b'{"error": "unauthorized"}'
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

    r3 = client.search("err")
    assert not r3.ok
    assert r3.code == "banco_http_500"


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

    res_item = json.loads(tools["leer_item_banco"](id="banco:item-arma-abierta-v2-1009"))
    assert res_item["ok"] is True
    assert res_item["banco_path"] == "banco:item-arma-abierta-v2-1009"

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


@pytest.mark.skipif(
    not (
        Path("/home/ubuntu/begonia-publish/secrets/public-api-keys").exists()
        and os.environ.get("RUN_BEGONIA_LIVE_TEST") == "1"
    ),
    reason="Requiere servidor local de begonia y RUN_BEGONIA_LIVE_TEST=1",
)
def test_begonia_live_smoke():
    settings = Settings(
        begonia_url="http://127.0.0.1:8766",
        begonia_key_file="/home/ubuntu/begonia-publish/secrets/public-api-keys",
    )
    client = BegoniaClient.from_settings(settings)
    assert client.configured
    assert client.available()
    reply = client.search("comprensión lectora", limit=2)
    assert reply.ok
    assert len(reply.data.get("items", [])) > 0
