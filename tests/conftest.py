from __future__ import annotations

import shutil
from pathlib import Path

from tero.config import EXAMPLE_CARPETA
from tero.workspace import Workspace


def copy_demo_carpeta(dest: Path) -> Path:
    target = dest / "carpeta"
    shutil.copytree(EXAMPLE_CARPETA, target)
    return target


def open_demo(dest: Path) -> Workspace:
    return Workspace(copy_demo_carpeta(dest))
