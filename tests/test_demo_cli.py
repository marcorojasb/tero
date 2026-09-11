"""CLI: `python -m tero demo --offline --yes` conversa, propone, aprueba y avisa."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from tero.cli import main
from tero.config import EXAMPLE_CARPETA, PACKAGE_ROOT

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_demo_offline_yes(demo_carpeta: Path, capsys):
    code = main(["demo", "--offline", "--yes", "--carpeta", str(demo_carpeta)])
    captured = capsys.readouterr()
    assert code == 0
    assert "PROPUESTA" in captured.out
    assert "escrito:" in captured.out
    assert "listo." in captured.out
    assert "Originales intactos." in captured.out
    derivados = list((demo_carpeta / "derivados").glob("*.md"))
    assert derivados, captured.out
    text = derivados[0].read_text(encoding="utf-8")
    assert "generado_por: tero" in text
    assert "accion: crear" in text
    sources = (demo_carpeta / "fuentes" / "cuento-el-condor-y-el-huemul.md").read_text(
        encoding="utf-8"
    )
    assert "El huemul no corrió" in sources
    assert (demo_carpeta / "borradores").glob("*.md")
    assert list((demo_carpeta / "borradores").glob("*.md")) == []


def test_demo_offline_yes_no_toca_los_originales(demo_carpeta: Path, capsys):
    from tero.hashutil import sha256_file

    fuentes = sorted((demo_carpeta / "fuentes").rglob("*"))
    antes = {path.name: sha256_file(path) for path in fuentes if path.is_file()}
    code = main(["demo", "--offline", "--yes", "--carpeta", str(demo_carpeta)])
    capsys.readouterr()
    assert code == 0
    despues = {path.name: sha256_file(path) for path in fuentes if path.is_file()}
    assert despues == antes


def test_demo_offline_yes_en_el_proceso_real(tmp_path: Path):
    """El comando exacto del README, en subprocess y contra este checkout."""
    destino = tmp_path / "carpeta"
    shutil.copytree(
        EXAMPLE_CARPETA,
        destino,
        ignore=shutil.ignore_patterns("derivados", "borradores", ".tero"),
    )
    env = {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT / "src"),
        "TERO_OFFLINE": "1",
    }
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tero",
            "demo",
            "--offline",
            "--yes",
            "--carpeta",
            str(destino),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(tmp_path),
        timeout=180,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "escrito:" in proc.stdout
    assert "Originales intactos." in proc.stdout
    derivados = list((destino / "derivados").glob("*.md"))
    assert derivados, proc.stdout
    assert "generado_por: tero" in derivados[0].read_text(encoding="utf-8")


def test_demo_offline_yes_on_mvp_fixtures(tmp_path: Path, capsys):
    dest = tmp_path / "aula"
    shutil.copytree(
        PACKAGE_ROOT / "fixtures" / "aula-5basico-agua",
        dest,
        ignore=shutil.ignore_patterns("derivados", "borradores", ".tero"),
    )
    code = main(["demo", "--offline", "--yes", "--carpeta", str(dest)])
    captured = capsys.readouterr()
    assert code == 0, captured.out + captured.err
    assert "escrito:" in captured.out
    assert "Originales intactos." in captured.out
    derivados = [
        path
        for path in (dest / "derivados").glob("*.md")
        if "generado_por: tero" in path.read_text(encoding="utf-8")
    ]
    assert derivados, captured.out
    body = derivados[0].read_text(encoding="utf-8")
    assert "fuentes de la carpeta" in body.lower() or "01-oa-curriculo" in body


def test_export_por_cli_sobre_un_artefacto(tmp_path: Path, capsys):
    source = tmp_path / "arte.md"
    source.write_text(
        "---\ngenerado_por: tero\ntipo: guia\ntitulo: Guía\n---\n\n# Guía\n\n## Propósito\nLeer.\n",
        encoding="utf-8",
    )
    code = main(["export", str(source), "--format", "md"])
    captured = capsys.readouterr()
    assert code == 0
    assert "exportado:" in captured.out
    assert (tmp_path / "arte.export.md").exists()
