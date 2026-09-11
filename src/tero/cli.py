"""CLI: demo, bridge, tui, init-carpeta. Spanish help. No secrets."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from tero import DEFAULT_MODEL_ID, __version__
from tero.approval import classify_approval
from tero.config import EXAMPLE_CARPETA, PACKAGE_ROOT, Settings
from tero.session import TeacherSession
from tero.types import Encargo
from tero.workspace import Workspace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tero",
        description="tero — el agente propone, la persona decide.",
    )
    parser.add_argument("--version", action="version", version=f"tero {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="Recorrido offline (o Bedrock) para video y jueces.")
    _add_common(demo)
    demo.add_argument(
        "--yes", action="store_true", help="Aprueba la propuesta sin teclado (demo/tests)."
    )
    demo.add_argument("--prompt", default="", help="Encargo en lenguaje natural.")

    bridge = sub.add_parser("bridge", help="Host JSONL para OpenTUI (stdin/stdout).")
    _add_common(bridge)
    bridge.add_argument(
        "--yes", action="store_true", help="Aprueba automáticamente (solo tests/demo)."
    )

    tui = sub.add_parser("tui", help="Lanza OpenTUI (Bun) y el bridge JSONL.")
    _add_common(tui)

    init = sub.add_parser("init-carpeta", help="Copia la carpeta demo a una ruta nueva.")
    init.add_argument("dest", type=Path)

    export = sub.add_parser(
        "export",
        help="Exporta un artefacto .md a md|docx|latex (JSON→plantilla; sin TeX libre).",
    )
    export.add_argument("source", type=Path, help="Markdown escrito en derivados/.")
    export.add_argument(
        "--format",
        dest="fmt",
        default="latex",
        choices=["md", "docx", "latex", "tex"],
        help="Formato de salida (default latex).",
    )
    export.add_argument("--out", type=Path, default=None, help="Ruta destino.")
    export.add_argument("--tipo", default=None, help="guia|evaluacion|planificacion|pauta|beamer")
    export.add_argument(
        "--pdf",
        action="store_true",
        help="Intentar latexmk -pdf -no-shell-escape si está instalado.",
    )
    export.add_argument(
        "--payload",
        type=Path,
        default=None,
        help="JSON schema (Nova Lite) en vez de inferir desde markdown.",
    )

    args = parser.parse_args(argv)
    if args.cmd == "demo":
        return cmd_demo(args)
    if args.cmd == "bridge":
        return cmd_bridge(args)
    if args.cmd == "tui":
        return cmd_tui(args)
    if args.cmd == "init-carpeta":
        return cmd_init(args.dest)
    if args.cmd == "export":
        return cmd_export(args)
    return 1


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--offline", action="store_true", help="Modelo scripted, sin AWS.")
    parser.add_argument("--carpeta", type=Path, default=None, help="Carpeta de trabajo (SoR).")
    parser.add_argument(
        "--model", default=None, help=f"Bedrock model id (default {DEFAULT_MODEL_ID})."
    )
    parser.add_argument("--curso", default=None, help="Contexto: curso (p. ej. «4° básico»).")
    parser.add_argument("--asignatura", default=None)
    parser.add_argument("--oa", default=None)
    parser.add_argument("--duracion", default=None)
    parser.add_argument(
        "--tipo",
        default=None,
        help="planificacion | guia | evaluacion | pauta | actividad",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Menos ruido en stdout (sigue imprimiendo escrito:/listo.).",
    )


def _encargo(args: argparse.Namespace, *, demo_defaults: bool = False) -> Encargo:
    """CLI context. The demo keeps classroom defaults; the TUI starts empty."""
    if demo_defaults:
        return Encargo.from_dict(
            {
                "curso": args.curso or "4° básico",
                "asignatura": args.asignatura or "Lenguaje y Comunicación",
                "oa": args.oa or "LEN-4B-OA04",
                "duracion": args.duracion or "45 min",
                "tipo": args.tipo or "planificacion",
            }
        )
    return Encargo.from_dict(
        {
            "curso": args.curso or "",
            "asignatura": args.asignatura or "",
            "oa": args.oa or "",
            "duracion": args.duracion or "",
            "tipo": args.tipo or "",
        }
    )


def _settings(args: argparse.Namespace) -> Settings:
    settings = Settings.from_env(
        offline=True if args.offline else None,
        carpeta=args.carpeta,
    )
    if args.model:
        object.__setattr__(settings, "model_id", args.model)
    return settings


def cmd_demo(args: argparse.Namespace) -> int:
    """Recorrido para jueces y video: conversa, propone y (con --yes) aprueba."""
    settings = _settings(args)
    workspace = Workspace(settings.carpeta)
    before = workspace.fingerprint_sources()
    events: list[dict] = []
    session = TeacherSession(
        workspace, settings, encargo=_encargo(args, demo_defaults=True), emit=events.append
    )
    prompt = args.prompt.strip() or (
        "Prepara una planificación de 45 minutos sobre el cuento de la carpeta, "
        "alineada al OA de comprensión lectora. Usa solo las fuentes locales."
    )
    quiet = bool(getattr(args, "quiet", False))

    def say(text: str) -> None:
        if not quiet:
            print(text, flush=True)

    say("tero demo")
    say(f"  modo: {'offline' if settings.offline else 'bedrock'}")
    say(f"  modelo: {settings.model_id if not settings.offline else 'tero-offline'}")
    say(f"  carpeta: {workspace.root}")
    say(f"  contexto: {session.encargo.context_line()}")
    say(f"  mensaje: {prompt}")
    turn = session.start_turn(prompt)

    result = None
    for _ in range(3):
        propuesta = session.pending_propuesta
        if propuesta is None:
            break
        say(f"\nPROPUESTA · {propuesta.accion} · {propuesta.tipo.label} · {propuesta.titulo}")
        if propuesta.resumen:
            say(f"  {propuesta.resumen}")
        if propuesta.origen:
            say(f"  origen: {propuesta.origen}")
        for cambio in propuesta.cambios:
            say(f"  cambio: {cambio}")
        for nota in propuesta.notas_nee:
            say(f"  nee: {nota}")
        say(f"  evidencias: {len(propuesta.draft.evidencias)}")
        for warning in propuesta.draft.warnings:
            say(f"  aviso ({warning.code}): {warning.message}")
        if args.yes:
            result = session.aprobar()
            break
        print("\n¿Escribo este material? (sí / no / pide un cambio)", flush=True)
        answer = input("respuesta: ").strip()
        decision = classify_approval(answer)
        if decision.kind == "aprobar":
            result = session.aprobar(decision.note or answer)
            break
        if decision.kind == "descartar":
            session.descartar(decision.note or answer)
            print("Descartado. No escribí nada.", flush=True)
            return 0
        session.pedir_cambio(decision.note or answer)

    if result is not None and result.path is not None:
        print(f"\nescrito: {result.path}", flush=True)
        after = workspace.fingerprint_sources()
        if after != before:
            print(
                "ADVERTENCIA: un original cambió. tero no debería haberlo escrito.",
                file=sys.stderr,
            )
            return 1
        print("Originales intactos.", flush=True)
        print("listo.", flush=True)
        return 0
    if session.pending_propuesta is not None:
        print("Quedó una propuesta sin decisión. No escribí nada.", flush=True)
        return 0
    if turn.respuesta:
        say(turn.respuesta)
        print("listo.", flush=True)
        return 0
    print(f"fase inesperada: {session.phase}", flush=True)
    for event in events:
        if event.get("type") == "error":
            print(event.get("message"), file=sys.stderr)
    return 1


def cmd_bridge(args: argparse.Namespace) -> int:
    from tero.bridge import Bridge

    settings = _settings(args)
    encargo = _encargo(args)
    bridge = Bridge(settings, auto_yes=bool(args.yes))
    bridge.session.set_encargo(encargo)
    return bridge.serve()


def cmd_tui(args: argparse.Namespace) -> int:
    bun = shutil.which("bun") or str(Path.home() / ".bun" / "bin" / "bun")
    tui_dir = PACKAGE_ROOT / "tui"
    entry = tui_dir / "src" / "index.ts"
    if not entry.exists():
        print("No encuentro tui/src/index.ts. ¿clon incompleto?", file=sys.stderr)
        return 1
    settings = _settings(args)
    env = os.environ.copy()
    env["TERO_OFFLINE"] = "1" if settings.offline else "0"
    env["TERO_CARPETA"] = str(settings.carpeta.resolve())
    env["TERO_MODEL"] = settings.model_id
    env["TERO_AWS_REGION"] = settings.region
    env["TERO_PYTHON"] = sys.executable
    env["TERO_CURSO"] = args.curso or ""
    env["TERO_ASIGNATURA"] = args.asignatura or ""
    env["TERO_OA"] = args.oa or ""
    env["TERO_DURACION"] = args.duracion or ""
    env["TERO_TIPO"] = args.tipo or ""
    cmd = [bun, str(entry)]
    try:
        return subprocess.call(cmd, cwd=tui_dir, env=env)
    except FileNotFoundError:
        print(
            "Bun no está instalado. https://bun.sh — o usa: python -m tero demo --offline --yes",
            file=sys.stderr,
        )
        return 1


def cmd_init(dest: Path) -> int:
    dest = dest.expanduser().resolve()
    if dest.exists() and any(dest.iterdir()):
        print(f"Destino no vacío: {dest}", file=sys.stderr)
        return 2
    shutil.copytree(EXAMPLE_CARPETA, dest, dirs_exist_ok=True)
    print(f"carpeta lista: {dest}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    from tero.export import export_docx, export_latex, export_markdown

    source = Path(args.source).expanduser().resolve()
    if not source.exists() and not args.payload:
        print(f"No existe: {source}", file=sys.stderr)
        return 2
    fmt = str(args.fmt or "latex").lower()
    out = Path(args.out).expanduser().resolve() if args.out else None
    payload = None
    if args.payload:
        import json

        payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    if fmt == "docx":
        dest = out or source.with_suffix(".docx")
        path = export_docx(source, dest)
    elif fmt in {"latex", "tex"}:
        dest = out or (source.with_suffix(".tex") if source.exists() else Path("artefacto.tex"))
        path = export_latex(
            source if source.exists() else dest,
            dest,
            tipo=args.tipo,
            payload=payload,
            try_pdf=bool(args.pdf),
        )
    else:
        dest = out or source.with_name(source.stem + ".export.md")
        path = export_markdown(source, dest)
    print(f"exportado: {path}", flush=True)
    pdf = path.with_suffix(".pdf")
    if pdf.exists():
        print(f"pdf: {pdf}", flush=True)
    return 0
