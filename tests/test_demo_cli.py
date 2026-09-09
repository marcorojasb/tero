from __future__ import annotations

from pathlib import Path

from tero.cli import main


def test_demo_offline_yes(demo_carpeta: Path, capsys):
    code = main(["demo", "--offline", "--yes", "--carpeta", str(demo_carpeta)])
    captured = capsys.readouterr()
    assert code == 0
    assert "escrito:" in captured.out
    assert "listo." in captured.out
    derivados = list((demo_carpeta / "derivados").glob("*.md"))
    assert derivados, captured.out
    text = derivados[0].read_text(encoding="utf-8")
    assert "Planificación" in text or "planificación" in text.lower()
    sources = (demo_carpeta / "fuentes" / "cuento-el-condor-y-el-huemul.md").read_text(
        encoding="utf-8"
    )
    assert "El huemul no corrió" in sources
