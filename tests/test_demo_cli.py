from __future__ import annotations

import shutil
from pathlib import Path

from tero.cli import main
from tero.config import PACKAGE_ROOT


def test_demo_offline_yes(demo_carpeta: Path, capsys):
    code = main(["demo", "--offline", "--yes", "--carpeta", str(demo_carpeta)])
    captured = capsys.readouterr()
    assert code == 0
    assert "escrito:" in captured.out
    assert "listo." in captured.out
    assert "Originales intactos." in captured.out
    derivados = list((demo_carpeta / "derivados").glob("*.md"))
    assert derivados, captured.out
    text = derivados[0].read_text(encoding="utf-8")
    assert "Planificación" in text or "planificación" in text.lower()
    sources = (demo_carpeta / "fuentes" / "cuento-el-condor-y-el-huemul.md").read_text(
        encoding="utf-8"
    )
    assert "El huemul no corrió" in sources
    assert "verificada" in text


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
