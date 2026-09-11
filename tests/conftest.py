from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tero.config import EXAMPLE_CARPETA
from tero.workspace import Workspace


def copy_demo_carpeta(dest: Path) -> Path:
    """Copia la carpeta demo sin material generado: cada test parte hermético.

    Si alguien corrió el demo en el repo, `examples/carpeta-demo/derivados/` puede
    tener archivos sueltos. Los tests no deben depender de eso.
    """
    target = dest / "carpeta"
    shutil.copytree(
        EXAMPLE_CARPETA,
        target,
        ignore=shutil.ignore_patterns("derivados", "borradores", ".tero"),
    )
    return target


def open_demo(dest: Path) -> Workspace:
    return Workspace(copy_demo_carpeta(dest))


@pytest.fixture
def demo_carpeta(tmp_path: Path) -> Path:
    return copy_demo_carpeta(tmp_path)


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    return open_demo(tmp_path)
