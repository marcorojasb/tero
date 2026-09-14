"""Tests para el Sello Criptográfico de Criterio Docente y Decisional Provenance Ledger."""

from __future__ import annotations

import hashlib

from tero.cli import main
from tero.export import export_latex
from tero.gate import write_approved
from tero.ledger import (
    FOOTER_STAMP_PREFIX,
    create_decisional_seal,
    extract_seal_from_markdown,
    inject_seal_into_markdown,
    load_seal,
    strip_seal_from_markdown,
)
from tero.types import ArtifactDraft, ArtifactType, Encargo, Propuesta
from tero.workspace import Workspace


def test_create_and_inject_seal(workspace: Workspace):
    markdown = "---\ngenerado_por: tero\ntipo: guia\ntitulo: Guia 1\n---\n# Guía\nContenido"
    seal = create_decisional_seal(
        workspace=workspace,
        unsealed_markdown=markdown,
        accion="crear",
        titulo="Guia 1",
        tipo="guia",
        note="Aprobado por el profesor",
        model_id="amazon.nova-lite-v1:0",
        trace_id="trace-12345",
    )
    assert seal.seal_id.startswith("tero-seal-")
    assert seal.criterio == "humano_aprobado"
    assert seal.decision_type == "conversational_approval"
    assert seal.approval_note == "Aprobado por el profesor"
    assert seal.model_id == "amazon.nova-lite-v1:0"
    assert seal.trace_id == "trace-12345"

    sealed = inject_seal_into_markdown(markdown, seal)
    assert "sello_docente:" in sealed
    assert f"seal_id: {seal.seal_id}" in sealed
    assert f"{FOOTER_STAMP_PREFIX} {seal.seal_id}*" in sealed

    # Comprobar extracción
    extracted = extract_seal_from_markdown(sealed)
    assert extracted["seal_id"] == seal.seal_id
    assert extracted["criterio"] == "humano_aprobado"

    # Comprobar despojo para verificar hash_derivado
    stripped = strip_seal_from_markdown(sealed)
    expected_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    computed_hash = hashlib.sha256(stripped.encode("utf-8")).hexdigest()
    assert seal.hash_derivado == expected_hash
    assert computed_hash == expected_hash


def test_write_approved_generates_ledger_entry(workspace: Workspace):
    fuente = workspace.root / "fuentes" / "lectura.md"
    fuente.parent.mkdir(parents=True, exist_ok=True)
    fuente.write_text("# Texto de prueba\nHabía una vez...", encoding="utf-8")
    workspace.rebuild_index()

    encargo = Encargo(curso="4° básico", tipo=ArtifactType.GUIA)
    propuesta = Propuesta(
        accion="crear",
        draft=ArtifactDraft(
            tipo=ArtifactType.GUIA,
            titulo="Guía de Prueba",
            cuerpo_markdown="# Guía\n## Propósito\nLeer.\n## Instrucciones\nSeguir.\n## Actividades\n1.\n## Cierre\nFin.\n",
        ),
    )

    resultado = write_approved(
        workspace=workspace,
        encargo=encargo,
        propuesta=propuesta,
        note="Excelente guía de aula",
        model_id="tero-offline",
        trace_id="trace-abc-999",
    )

    assert resultado.seal is not None
    seal_id = resultado.seal.seal_id
    assert seal_id.startswith("tero-seal-")

    # Verificar que el registro existe en .tero/decisiones/ y .tero/ledger/
    ledger_dec = workspace.root / ".tero" / "decisiones" / f"{seal_id}.json"
    ledger_led = workspace.root / ".tero" / "ledger" / f"{seal_id}.json"
    assert ledger_dec.is_file()
    assert ledger_led.is_file()

    loaded = load_seal(workspace, seal_id)
    assert loaded is not None
    assert loaded.seal_id == seal_id
    assert loaded.approval_note == "Excelente guía de aula"
    assert loaded.trace_id == "trace-abc-999"

    # Verificar integridad con workspace.verify_seal
    verif = workspace.verify_seal(resultado.path)
    assert verif.valid is True
    assert verif.checks["ledger_exists"] is True
    assert verif.checks["frontmatter_matches"] is True
    assert verif.checks["artifact_intact"] is True
    assert verif.checks["sources_intact"] is True
    assert verif.checks["decision_valid"] is True


def test_tampered_artifact_fails_verification(workspace: Workspace):
    encargo = Encargo(curso="4° básico", tipo=ArtifactType.ACTIVIDAD)
    propuesta = Propuesta(
        accion="crear",
        draft=ArtifactDraft(
            tipo=ArtifactType.ACTIVIDAD,
            titulo="Actividad 1",
            cuerpo_markdown="# Actividad\n## Objetivo\nJugar.\n## Materiales\nLápiz.\n## Pasos\nUno.\n",
        ),
    )
    resultado = write_approved(
        workspace=workspace, encargo=encargo, propuesta=propuesta, note="Aprobada"
    )
    assert resultado.path is not None

    # Verificación inicial válida
    assert workspace.verify_seal(resultado.path).valid is True

    # Alterar el cuerpo del archivo
    original_text = resultado.path.read_text(encoding="utf-8")
    tampered_text = original_text.replace("Jugar.", "Hacer trampa no detectada.")
    resultado.path.write_text(tampered_text, encoding="utf-8")

    # Debe fallar la verificación por alteración
    verif = workspace.verify_seal(resultado.path)
    assert verif.valid is False
    assert verif.checks["artifact_intact"] is False
    assert "alterado" in verif.message.lower()


def test_tampered_source_fails_verification(workspace: Workspace):
    source_file = workspace.root / "fuentes" / "poema.md"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("Verso uno.\nVerso dos.\n", encoding="utf-8")
    workspace.rebuild_index()

    encargo = Encargo(curso="4° básico", tipo=ArtifactType.ACTIVIDAD)
    propuesta = Propuesta(
        accion="crear",
        draft=ArtifactDraft(
            tipo=ArtifactType.ACTIVIDAD,
            titulo="Actividad Poema",
            cuerpo_markdown="# Actividad\n## Objetivo\nLeer.\n## Materiales\nPoema.\n## Pasos\nRecitar.\n",
        ),
    )
    resultado = write_approved(workspace=workspace, encargo=encargo, propuesta=propuesta)
    assert resultado.path is not None
    assert workspace.verify_seal(resultado.path).valid is True

    # Modificar la fuente original tras la aprobación
    source_file.write_text("Verso modificado maliciosamente tras emisión.\n", encoding="utf-8")

    verif = workspace.verify_seal(resultado.path)
    assert verif.valid is False
    assert verif.checks["sources_intact"] is False
    assert "fuentes originales alteradas" in verif.message.lower()


def test_cli_verify_seal(workspace: Workspace, capsys):
    encargo = Encargo(curso="4° básico", tipo=ArtifactType.PAUTA)
    propuesta = Propuesta(
        accion="crear",
        draft=ArtifactDraft(
            tipo=ArtifactType.PAUTA,
            titulo="Pauta de Cotejo",
            cuerpo_markdown="# Pauta\n## Criterios\nA.\n## Niveles\nB.\n## Descriptores\nC.\n",
        ),
    )
    resultado = write_approved(
        workspace=workspace,
        encargo=encargo,
        propuesta=propuesta,
        note="Validado en reunión de departamento",
    )
    assert resultado.path is not None

    # Probar CLI verify-seal con archivo válido
    code = main(["verify-seal", str(resultado.path), "--carpeta", str(workspace.root)])
    assert code == 0
    captured = capsys.readouterr()
    assert "VÁLIDO" in captured.out
    assert resultado.seal.seal_id in captured.out
    assert "Validado en reunión de departamento" in captured.out

    # Modificar archivo y verificar salida CLI fallida
    tampered = resultado.path.read_text(encoding="utf-8") + "\nLínea espuria"
    resultado.path.write_text(tampered, encoding="utf-8")
    code_bad = main(["verify-seal", str(resultado.path), "--carpeta", str(workspace.root)])
    assert code_bad == 1
    err_cap = capsys.readouterr()
    assert "INVÁLIDO" in err_cap.err


def test_latex_export_includes_certified_stamp(workspace: Workspace, tmp_path):
    encargo = Encargo(curso="4° básico", tipo=ArtifactType.GUIA)
    propuesta = Propuesta(
        accion="crear",
        draft=ArtifactDraft(
            tipo=ArtifactType.GUIA,
            titulo="Guía con Sello",
            cuerpo_markdown="# Guía\n## Propósito\nP.\n## Instrucciones\nI.\n## Actividades\nA.\n## Cierre\nC.\n",
        ),
    )
    resultado = write_approved(workspace=workspace, encargo=encargo, propuesta=propuesta)
    assert resultado.path is not None
    assert resultado.seal is not None

    dest_tex = tmp_path / "guia.tex"
    export_latex(resultado.path, dest_tex)
    assert dest_tex.is_file()
    content = dest_tex.read_text(encoding="utf-8")
    assert "Tero Decisional Seal ID" in content
    assert resultado.seal.seal_id in content


def test_unsealed_markdown_without_frontmatter_recovers_losslessly(workspace: Workspace):
    """Prueba que artefactos sin front matter original se recuperan idénticamente al despojar el sello."""
    raw_md = "# Actividad de Aula Directa\n\n1. Leer el cuento.\n2. Dialogar en grupos.\n"
    seal = create_decisional_seal(
        workspace=workspace,
        unsealed_markdown=raw_md,
        accion="crear",
        titulo="Actividad Directa",
        tipo="actividad",
        note="Aprobada sin frontmatter",
    )
    sealed = inject_seal_into_markdown(raw_md, seal)
    assert "sello_docente:" in sealed

    # Despojo debe restaurar byte a byte
    stripped = strip_seal_from_markdown(sealed)
    assert stripped == raw_md
    assert hashlib.sha256(stripped.encode("utf-8")).hexdigest() == seal.hash_derivado


def test_extract_seal_with_arbitrary_key_ordering_and_comments():
    """El parser de sello en front matter debe ser insensible al orden de claves y tolerar comentarios."""
    md = """---
tipo: guia
sello_docente:
  # Comentario explicativo
  criterio: humano_aprobado
  hash_fuentes: 111222333
  seal_id: tero-seal-abc999
  timestamp: "2026-09-13T22:00:00Z"
  hash_derivado: 444555666
---
# Contenido
"""
    extracted = extract_seal_from_markdown(md)
    assert extracted.get("seal_id") == "tero-seal-abc999"
    assert extracted.get("criterio") == "humano_aprobado"
    assert extracted.get("hash_fuentes") == "111222333"
    assert extracted.get("hash_derivado") == "444555666"
    assert extracted.get("timestamp") == "2026-09-13T22:00:00Z"


def test_tampered_frontmatter_missing_required_key_fails_verification(workspace: Workspace):
    """Si se altera el front matter eliminando claves requeridas del sello, debe fallar."""
    encargo = Encargo(curso="4° básico", tipo=ArtifactType.GUIA)
    propuesta = Propuesta(
        accion="crear",
        draft=ArtifactDraft(
            tipo=ArtifactType.GUIA,
            titulo="Guía Completa",
            cuerpo_markdown="# Guía\n## Contenido\nTexto\n",
        ),
    )
    res = write_approved(workspace=workspace, encargo=encargo, propuesta=propuesta)
    assert res.path is not None
    assert workspace.verify_seal(res.path).valid is True

    # Eliminar hash_fuentes del front matter
    text = res.path.read_text(encoding="utf-8")
    tampered = "\n".join(line for line in text.splitlines() if "hash_fuentes:" not in line)
    res.path.write_text(tampered + "\n", encoding="utf-8")

    verif = workspace.verify_seal(res.path)
    assert verif.valid is False
    assert verif.checks["frontmatter_matches"] is False


def test_cli_verify_seal_json_output(workspace: Workspace, capsys):
    """La bandera --json debe retornar un JSON estructurado para herramientas y CI."""
    import json

    encargo = Encargo(curso="4° básico", tipo=ArtifactType.ACTIVIDAD)
    propuesta = Propuesta(
        accion="crear",
        draft=ArtifactDraft(
            tipo=ArtifactType.ACTIVIDAD,
            titulo="Actividad JSON",
            cuerpo_markdown="# Actividad\n## Pasos\nUno\n",
        ),
    )
    res = write_approved(workspace=workspace, encargo=encargo, propuesta=propuesta)
    assert res.path is not None

    code = main(["verify-seal", str(res.path), "--carpeta", str(workspace.root), "--json"])
    assert code == 0
    cap = capsys.readouterr()
    data = json.loads(cap.out)
    assert data["valid"] is True
    assert data["seal_id"] == res.seal.seal_id
    assert data["checks"]["ledger_exists"] is True


def test_gate_verify_seal_reexport_and_workspace_str_path(workspace: Workspace):
    """Workspace debe aceptar rutas como str y gate debe reexportar verify_seal."""
    from tero.gate import verify_seal as gate_verify_seal

    ws_str = Workspace(str(workspace.root))
    encargo = Encargo(curso="4° básico", tipo=ArtifactType.GUIA)
    propuesta = Propuesta(
        accion="crear",
        draft=ArtifactDraft(
            tipo=ArtifactType.GUIA,
            titulo="Guía Str Path",
            cuerpo_markdown="# Guía\n## Texto\nHola\n",
        ),
    )
    res = write_approved(workspace=ws_str, encargo=encargo, propuesta=propuesta)
    verif = gate_verify_seal(ws_str, res.path)
    assert verif.valid is True


def test_export_docx_omits_frontmatter_and_includes_stamp(workspace: Workspace, tmp_path):
    """export_docx no debe volcar metadatos YAML en el cuerpo y debe dar estilo al sello."""
    from docx import Document

    from tero.export import export_docx

    encargo = Encargo(curso="4° básico", tipo=ArtifactType.GUIA)
    propuesta = Propuesta(
        accion="crear",
        draft=ArtifactDraft(
            tipo=ArtifactType.GUIA,
            titulo="Guía Docx",
            cuerpo_markdown="# Guía Docx\n\nTexto pedagógico limpio.\n",
        ),
    )
    res = write_approved(workspace=workspace, encargo=encargo, propuesta=propuesta)
    assert res.path is not None

    docx_dest = tmp_path / "guia.docx"
    export_docx(res.path, docx_dest)
    assert docx_dest.is_file()

    doc = Document(docx_dest)
    paras = [p.text for p in doc.paragraphs if p.text]
    # No deben figurar los encabezados YAML en el cuerpo
    assert not any("generado_por:" in p for p in paras)
    assert not any("sello_docente:" in p for p in paras)
    assert not any("hash_derivado:" in p for p in paras)
    # Debe figurar el contenido y el sello
    assert any("Texto pedagógico limpio" in p for p in paras)
    assert any("Material co-creado y certificado bajo criterio docente" in p for p in paras)
