"""Command-line interface for tero."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from tero import __version__
from tero.agent import build_agent
from tero.approval import Decision
from tero.config import get_settings, has_aws_credentials, load_env
from tero.prompts import DEFAULT_DEMO_TASK
from tero.workspace import Workspace

BANNER = """
════════════════════════════════════════════════════════════
  tero
  tus fuentes, tu criterio
  el agente prepara, el o la docente decide
════════════════════════════════════════════════════════════
"""

FIXTURES_REL = Path("fixtures") / "aula-5basico-agua"


def main(argv: list[str] | None = None) -> int:
    load_env()
    parser = argparse.ArgumentParser(
        prog="tero",
        description="Agente Strands para docentes: propone, tú decides.",
    )
    parser.add_argument("--version", action="version", version=f"tero {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Correr el agente sobre una carpeta de trabajo")
    run_p.add_argument("folder", type=Path, help="Carpeta con fuentes del o de la docente")
    _add_common(run_p)

    demo_p = sub.add_parser("demo", help="Happy path con materiales de fixtures/")
    _add_common(demo_p)

    args = parser.parse_args(argv)
    if args.command == "demo":
        return cmd_demo(args)
    return cmd_run(args)


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--task",
        default=DEFAULT_DEMO_TASK,
        help="Encargo al agente (planificación, guía, etc.)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Usar el modelo scripted de Strands (sin Bedrock / sin AWS)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Auto-aprobar la escritura a derivados/ (solo para demos)",
    )
    parser.add_argument(
        "--reject",
        action="store_true",
        help="Auto-rechazar la propuesta (para ver que no se escribe nada)",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Auto-guardar como borrador en derivados/borradores/",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="No mostrar el stream del modelo",
    )


def _auto_decision(args: argparse.Namespace) -> Decision | None:
    if args.reject:
        return "reject"
    if args.draft:
        return "draft"
    if args.yes:
        return "approve"
    return None


def cmd_demo(args: argparse.Namespace) -> int:
    root = _fixtures_path()
    print(BANNER)
    print("Demo: carpeta de trabajo =", root)
    print("Materiales: OA de 5° básico (agua), apuntes docentes, contexto Chile.")
    return _execute(root, args)


def cmd_run(args: argparse.Namespace) -> int:
    folder = args.folder.expanduser().resolve()
    print(BANNER)
    print("Carpeta de trabajo =", folder)
    return _execute(folder, args)


def _execute(folder: Path, args: argparse.Namespace) -> int:
    offline = bool(args.offline)
    if not offline and not has_aws_credentials():
        print(
            "No hay credenciales AWS/Bedrock visibles.\n"
            "  • Configura AWS (README → Setup) y vuelve a intentar, o\n"
            "  • Corre el mismo loop Strands sin Bedrock: añade --offline\n",
            file=sys.stderr,
        )
        return 2

    workspace = Workspace(folder)
    before = workspace.fingerprint_sources()
    settings = get_settings()
    auto = _auto_decision(args)

    print()
    if offline:
        print("Modelo: tero.scripted-offline (Strands Agents SDK, sin llamadas a Bedrock)")
    else:
        print(f"Modelo: {settings.model_id}  región={settings.region}  (Amazon Bedrock)")
    print("Herramientas: list_sources, read_source, write_derived (esta última con puerta docente)")
    print()
    print("Encargo:")
    print(args.task.strip())
    print()

    agent = build_agent(
        workspace,
        offline=offline,
        auto=auto,
        settings=settings,
        quiet=bool(args.quiet or offline),
    )

    try:
        result = agent(args.task)
    except KeyboardInterrupt:
        print("\nCancelado por el o la docente.")
        return 130
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"Error al ejecutar el agente: {exc}", file=sys.stderr)
        print(
            "Si es un error de Bedrock (acceso al modelo / región / IAM), "
            "revisa README.md → Amazon Bedrock.",
            file=sys.stderr,
        )
        return 1

    after = workspace.fingerprint_sources()
    if before != after:
        print("ALERTA: un archivo original cambió. Eso no debería ocurrir.", file=sys.stderr)
        return 3

    print()
    print("Originales intactos (hash sin cambios).")
    if workspace.last_write:
        rel = workspace.last_write.relative_to(workspace.root).as_posix()
        print(f"Derivado escrito: {rel}")
    else:
        print("No se escribió ningún derivado (propuesta descartada o no hubo write_derived).")

    message = getattr(result, "message", None)
    if message:
        text = _message_text(message)
        if text:
            print()
            print("Cierre del agente:")
            print(text)
    return 0


def _message_text(message: object) -> str:
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        parts = []
        for block in message.get("content") or []:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "\n".join(parts)
    return str(message)


def _fixtures_path() -> Path:
    here = Path(__file__).resolve().parent.parent
    path = here / FIXTURES_REL
    if path.is_dir():
        return path
    cwd = Path.cwd() / FIXTURES_REL
    if cwd.is_dir():
        return cwd
    raise FileNotFoundError(
        f"No encuentro {FIXTURES_REL}. Ejecuta tero desde el clon del repositorio."
    )


def copy_fixtures(dest: Path) -> Path:
    """Copy sample materials into dest (used by tests)."""
    src = _fixtures_path()
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name == "derivados":
            continue
        target = dest / item.name
        if item.is_file():
            shutil.copy2(item, target)
    return dest
