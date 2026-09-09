from __future__ import annotations

from tests.conftest import copy_demo_carpeta

from tero.cli import main


def test_demo_offline_yes(tmp_path, capsys):
    carpeta = copy_demo_carpeta(tmp_path)
    code = main(["demo", "--offline", "--yes", "--carpeta", str(carpeta)])
    captured = capsys.readouterr()
    assert code == 0
    assert "escrito:" in captured.out
    assert "listo." in captured.out
    derivados = list((carpeta / "derivados").glob("*.md"))
    assert derivados, captured.out
    text = derivados[0].read_text(encoding="utf-8")
    assert "Planificación" in text or "planificación" in text.lower()
    sources = (carpeta / "fuentes" / "cuento-el-condor-y-el-huemul.md").read_text(encoding="utf-8")
    assert "El huemul no corrió" in sources
