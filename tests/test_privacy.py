"""Tests unitarios para la exclusión de datos personales y de salud (Ley 21.719).

Sin red. Valida que notas, informes psicopedagógicos, nóminas y archivos con
RUT no se indexen ni se lean, y que la carpeta permanezca intacta.
"""

from __future__ import annotations

import json
from pathlib import Path

from tero import privacy
from tero.hashutil import sha256_file
from tero.tools import TurnContext, build_tools
from tero.workspace import Workspace
from tests.support import open_session


def test_deteccion_por_nombre_y_ruta():
    # Nombres que deben excluirse
    sensibles = [
        "notas.csv",
        "calificaciones.txt",
        "informe-psicopedagogico.md",
        "informe_psicopedagogico.txt",
        "diagnostico_pie.md",
        "fudei-2026.md",
        "paci_alumno.md",
        "nomina_estudiantes.txt",
        "lista-curso-4b.csv",
        "asistencia-marzo.txt",
        "entrevista-apoderado.md",
        "subcarpeta/notas/parcial1.txt",
        "fichas/ficha-estudiante.md",
    ]
    for s in sensibles:
        motivo = privacy.motivo_por_nombre(s)
        assert motivo is not None, f"Debería excluirse por nombre: {s}"

    # Nombres legítimos que deben admitirse
    legitimos = [
        "cuento.md",
        "guia-comprension.txt",
        "planificacion-agua.md",
        "rubrica-lectura.md",
        "actividad-ciencias.txt",
    ]
    for leg in legitimos:
        assert privacy.motivo_por_nombre(leg) is None


def test_deteccion_por_contenido():
    # RUT chileno
    con_rut = "El estudiante Juan Pérez, RUT 12.345.678-9, asistió a la evaluación."
    assert privacy.motivo_por_contenido(con_rut) == privacy.MOTIVO_RUT

    con_rut_k = "RUT: 18765432-K presenta certificado."
    assert privacy.motivo_por_contenido(con_rut_k) == privacy.MOTIVO_RUT

    # Nómina con nombres y notas
    nomina = "Nombre,Nota 1,Nota 2,Promedio\nJuan Perez,6.5,5.0,5.8\nMaria Soto,7.0,6.8,6.9\n"
    assert privacy.motivo_por_contenido(nomina) == privacy.MOTIVO_NOMINA

    # Texto pedagógico limpio
    limpio = (
        "# El cóndor y el huemul\n\n"
        "Había una vez un cóndor que volaba sobre la cordillera de los Andes.\n"
        "Preguntas de comprensión:\n"
        "1. ¿Por qué el huemul no corrió?\n"
    )
    assert privacy.motivo_por_contenido(limpio) is None


def test_workspace_excluye_archivos_sensibles(tmp_path: Path):
    ws_dir = tmp_path / "carpeta"
    ws_dir.mkdir()
    (ws_dir / "fuentes").mkdir()

    # Archivo legítimo
    normal = ws_dir / "fuentes" / "cuento.md"
    normal.write_text("# Cuento\n\nTexto pedagógico normal.", encoding="utf-8")

    # Archivos sensibles por nombre
    sensible_nombre = ws_dir / "fuentes" / "calificaciones.csv"
    sensible_nombre.write_text("1,2,3", encoding="utf-8")

    sensible_pie = ws_dir / "fuentes" / "informe-psicopedagogico.md"
    sensible_pie.write_text("Informe del estudiante...", encoding="utf-8")

    # Archivo con nombre inocente pero con RUT adentro
    sensible_rut = ws_dir / "fuentes" / "registro.txt"
    sensible_rut.write_text("Datos alumno: RUT 15.432.109-8 presente.", encoding="utf-8")

    ws = Workspace(ws_dir)
    sources = ws.list_sources()
    paths = [s.relative_path for s in sources]

    assert "fuentes/cuento.md" in paths
    assert "fuentes/calificaciones.csv" not in paths
    assert "fuentes/informe-psicopedagogico.md" not in paths
    assert "fuentes/registro.txt" not in paths

    excluidos = ws.excluded_sources()
    assert len(excluidos) == 3
    excl_names = {e.name for e in excluidos}
    assert "calificaciones.csv" in excl_names
    assert "informe-psicopedagogico.md" in excl_names
    assert "registro.txt" in excl_names


def test_modo_incluir_admite_todo(tmp_path: Path):
    ws_dir = tmp_path / "carpeta"
    ws_dir.mkdir()
    (ws_dir / "fuentes").mkdir()

    (ws_dir / "fuentes" / "cuento.md").write_text("# Cuento", encoding="utf-8")
    (ws_dir / "fuentes" / "notas.txt").write_text("Juan: 6.0", encoding="utf-8")

    ws = Workspace(ws_dir, datos_sensibles="incluir")
    sources = ws.list_sources()
    paths = [s.relative_path for s in sources]
    assert "fuentes/cuento.md" in paths
    assert "fuentes/notas.txt" in paths
    assert len(ws.excluded_sources()) == 0


def test_archivos_sensibles_quedan_intactos(tmp_path: Path):
    ws_dir = tmp_path / "carpeta"
    ws_dir.mkdir()
    (ws_dir / "fuentes").mkdir()

    notas_file = ws_dir / "fuentes" / "notas.csv"
    contenido_original = "alumno,nota\nPedro,5.5\n"
    notas_file.write_text(contenido_original, encoding="utf-8")
    hash_antes = sha256_file(notas_file)

    ws = Workspace(ws_dir)
    ws.list_sources()
    ws.ensure_index()

    assert notas_file.exists()
    assert notas_file.read_text(encoding="utf-8") == contenido_original
    assert sha256_file(notas_file) == hash_antes


def test_aviso_unico_en_session(tmp_path: Path):
    ws_dir = tmp_path / "carpeta"
    ws_dir.mkdir()
    (ws_dir / "fuentes").mkdir()
    (ws_dir / "fuentes" / "cuento.md").write_text("# Cuento", encoding="utf-8")
    (ws_dir / "fuentes" / "notas.csv").write_text("6.0, 7.0", encoding="utf-8")

    ws = Workspace(ws_dir)
    events: list[dict] = []
    session = open_session(ws, events=events)
    session.start_turn("Hola, ¿qué puedes hacer?")

    warnings = [
        e
        for e in events
        if e.get("type") == "warning"
        and e.get("warning", {}).get("code") == "dato_sensible_excluido"
    ]
    assert len(warnings) == 1
    assert warnings[0]["warning"]["blocking"] is False
    assert "Ley 21.719" in warnings[0]["warning"]["message"]


def test_tools_list_sources_informa_omitidos(tmp_path: Path):
    ws_dir = tmp_path / "carpeta"
    ws_dir.mkdir()
    (ws_dir / "fuentes").mkdir()
    (ws_dir / "fuentes" / "cuento.md").write_text("# Cuento", encoding="utf-8")
    (ws_dir / "fuentes" / "notas.csv").write_text("6.0, 7.0", encoding="utf-8")

    ws = Workspace(ws_dir)
    ctx = TurnContext(workspace=ws, encargo=None)
    tools = {t.tool_name: t for t in build_tools(ctx)}

    res = json.loads(tools["list_sources"]())
    assert len(res["fuentes"]) == 1
    assert res["omitidos_por_proteccion_de_datos"] == 1
    assert "protección de datos" in res["aviso"]

    # Intentar leer el sensible da error de protección
    res_read = json.loads(tools["read_source"](path="fuentes/notas.csv"))
    assert res_read["ok"] is False
    assert res_read["error"] == "dato_sensible_excluido"
