"""Bridge JSONL: el camino que usa la TUI (stdin comandos, stdout eventos)."""

from __future__ import annotations

import io
import json
from pathlib import Path

from tero.bridge import Bridge
from tero.config import Settings
from tero.protocol import decode, encode
from tests.support import PEDIDO_GUIA, PEDIDO_PLANIFICACION, PEDIDO_PREGUNTA, artifact_paths


def _run(carpeta: Path, lines: list[dict], *, auto_yes: bool = False) -> tuple[int, list[dict]]:
    stdin = io.StringIO("".join(json.dumps(line) + "\n" for line in lines))
    stdout = io.StringIO()
    bridge = Bridge(
        Settings(offline=True, carpeta=carpeta),
        stdin=stdin,
        stdout=stdout,
        auto_yes=auto_yes,
    )
    code = bridge.serve()
    events = [json.loads(row) for row in stdout.getvalue().splitlines() if row.strip()]
    return code, events


def _types(events: list[dict]) -> list[str]:
    return [event["type"] for event in events]


def test_protocol_roundtrip():
    line = encode({"type": "prompt", "text": "hola"})
    data = decode(line)
    assert data["type"] == "prompt"
    assert data["v"] == 1


def test_bridge_autogate_yes_aprueba_y_escribe(workspace):
    code, events = _run(
        workspace.root,
        [
            {"type": "hello", "encargo": {"curso": "4° básico", "oa": "LEN-4B-OA04"}},
            {"type": "prompt", "text": PEDIDO_PLANIFICACION},
            {"type": "shutdown"},
        ],
        auto_yes=True,
    )
    assert code == 0
    tipos = _types(events)
    assert "ready" in tipos
    assert "propuesta" in tipos
    assert "escrito" in tipos
    escrito = next(event for event in events if event["type"] == "escrito")
    assert escrito["path"].endswith(".md")
    assert Path(escrito["path"]).exists()
    assert len(artifact_paths(workspace)) == 1


def test_bridge_prompt_con_propuesta_pendiente_clasifica_dale(workspace):
    code, events = _run(
        workspace.root,
        [
            {"type": "prompt", "text": PEDIDO_GUIA},
            {"type": "prompt", "text": "dale"},
            {"type": "shutdown"},
        ],
    )
    assert code == 0
    aprobaciones = [event for event in events if event["type"] == "aprobacion"]
    assert [event["decision"] for event in aprobaciones] == ["aprobar"]
    assert "escrito" in _types(events)
    assert len(artifact_paths(workspace)) == 1


def test_bridge_prompt_con_propuesta_pendiente_clasifica_no(workspace):
    code, events = _run(
        workspace.root,
        [
            {"type": "prompt", "text": PEDIDO_GUIA},
            {"type": "prompt", "text": "no, gracias"},
            {"type": "shutdown"},
        ],
    )
    assert code == 0
    aprobaciones = [event for event in events if event["type"] == "aprobacion"]
    assert [event["decision"] for event in aprobaciones] == ["descartar"]
    assert "escrito" not in _types(events)
    assert artifact_paths(workspace) == []


def test_bridge_prompt_con_propuesta_pendiente_clasifica_cambia(workspace):
    code, events = _run(
        workspace.root,
        [
            {"type": "prompt", "text": PEDIDO_GUIA},
            {"type": "prompt", "text": "cambia el inicio, hazlo más corto"},
            {"type": "shutdown"},
        ],
    )
    assert code == 0
    aprobaciones = [event for event in events if event["type"] == "aprobacion"]
    assert [event["decision"] for event in aprobaciones] == ["cambiar"]
    assert _types(events).count("propuesta") == 2
    assert "escrito" not in _types(events)
    assert artifact_paths(workspace) == []


def test_bridge_crear_pregunta_dale_termina_escribiendo(workspace):
    """El camino completo de la TUI: conversar no pierde la propuesta pendiente."""
    code, events = _run(
        workspace.root,
        [
            {
                "type": "hello",
                "carpeta": str(workspace.root),
                "encargo": {
                    "curso": "4° básico",
                    "asignatura": "Lenguaje y Comunicación",
                    "oa": "LEN-4B-OA04",
                },
            },
            {"type": "prompt", "text": PEDIDO_GUIA},
            {"type": "prompt", "text": PEDIDO_PREGUNTA},
            {"type": "prompt", "text": "dale"},
            {"type": "shutdown"},
        ],
    )
    assert code == 0
    tipos = _types(events)
    assert "propuesta" in tipos
    assert "respuesta" in tipos
    respuesta = next(event for event in events if event["type"] == "respuesta")
    assert respuesta["texto"].strip()
    # La propuesta es anterior a la respuesta y el "dale" la aprueba igual.
    assert tipos.index("propuesta") < tipos.index("respuesta") < tipos.index("escrito")
    assert len(artifact_paths(workspace)) == 1


def test_bridge_export_sobre_el_artefacto_recien_escrito(workspace):
    code, events = _run(
        workspace.root,
        [
            {"type": "prompt", "text": PEDIDO_PLANIFICACION},
            {"type": "prompt", "text": "dale"},
            {"type": "export", "format": "md"},
            {"type": "shutdown"},
        ],
    )
    assert code == 0
    exportado = next(event for event in events if event["type"] == "exported")
    assert exportado["source_kind"] == "derivado"
    assert exportado["format"] == "md"
    destino = Path(exportado["path"])
    assert destino.exists()
    assert destino.read_text(encoding="utf-8").strip()


def test_bridge_export_sin_material_avisa_sin_romperse(workspace):
    code, events = _run(
        workspace.root,
        [
            {"type": "export", "format": "md"},
            {"type": "shutdown"},
        ],
    )
    assert code == 0
    assert "exported" not in _types(events)
    error = next(event for event in events if event["type"] == "error")
    assert "Aprueba una propuesta" in error["message"]


def test_bridge_error_de_protocolo_no_mata_el_host(workspace):
    stdin = io.StringIO("esto no es json\n" + json.dumps({"type": "shutdown"}) + "\n")
    stdout = io.StringIO()
    bridge = Bridge(Settings(offline=True, carpeta=workspace.root), stdin=stdin, stdout=stdout)
    assert bridge.serve() == 0
    events = [json.loads(row) for row in stdout.getvalue().splitlines() if row.strip()]
    assert "error" in _types(events)
    assert "bye" in _types(events)
