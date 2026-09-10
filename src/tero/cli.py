"""CLI: demo, bridge, tui, init-carpeta. Spanish help. No secrets."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from tero import DEFAULT_MODEL_ID, __version__
from tero.config import EXAMPLE_CARPETA, PACKAGE_ROOT, Settings
from tero.session import TeacherSession
from tero.types import Encargo
from tero.workspace import Workspace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tero",
        description="tero — el agente prepara, el docente decide (s/n/b/c).",
    )
    parser.add_argument("--version", action="version", version=f"tero {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="Recorrido offline (o Bedrock) para video y jueces.")
    _add_common(demo)
    demo.add_argument(
        "--yes", action="store_true", help="Aprueba el plan y acepta (s) sin teclado."
    )
    demo.add_argument("--prompt", default="", help="Encargo en lenguaje natural.")

    bridge = sub.add_parser("bridge", help="Host JSONL para OpenTUI (stdin/stdout).")
    _add_common(bridge)
    bridge.add_argument("--yes", action="store_true", help="Autogate (solo tests/demo).")

    tui = sub.add_parser("tui", help="Lanza OpenTUI (Bun) y el bridge JSONL.")
    _add_common(tui)

    init = sub.add_parser("init-carpeta", help="Copia la carpeta demo a una ruta nueva.")
    init.add_argument("dest", type=Path)

    export = sub.add_parser(
        "export",
        help="Exporta un artefacto .md a md|docx|latex (JSON→plantilla; sin TeX libre).",
    )
    export.add_argument("source", type=Path, help="Markdown aceptado/borrador.")
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
    parser.add_argument(
        "--skip-plan", action="store_true", help="Saltar el plan tipado (no recomendado)."
    )
    parser.add_argument("--curso", default=None, help="Chip curso (vacío = home limpio en TUI).")
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
    """CLI encargo. Demo keeps classroom defaults; TUI starts empty (home-first)."""
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
    if args.skip_plan:
        object.__setattr__(settings, "skip_plan", True)
    return settings


def cmd_demo(args: argparse.Namespace) -> int:
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
    say(f"  encargo: {', '.join(session.encargo.chips())}")
    if not settings.offline and not args.yes:
        say("Bedrock requiere credenciales de entorno (nunca en git). Ctrl+C para salir.")
    turn = session.start_turn(prompt)
    # Autocomplete clarification questions in --yes (suggested option).
    while session.phase == "esperando_clarificacion" and turn.plan:
        pending = turn.plan.pending_question()
        if pending is None:
            break
        suggested = next((opt for opt in pending.options if opt.suggested), None)
        option_id = suggested or (pending.options[0] if pending.options else None)
        session.answer_plan_question(option_id=option_id.id if option_id else "1")
        turn = session.turns[-1]
    if session.phase == "esperando_plan":
        if args.yes:
            session.decide_plan("approve")
        else:
            print("\nPLAN (a=aprobar / x=cancelar):", flush=True)
            assert turn.plan is not None
            for key, value in turn.plan.as_dict().items():
                if key in {"questions", "como_abordare", "supuestos", "entregables"}:
                    continue
                print(f"  {key}: {value}", flush=True)
            choice = input("¿Aprobar plan? [a/x]: ").strip().lower()
            if choice in {"x", "n", "cancel"}:
                session.decide_plan("cancel")
                print("Plan cancelado.", flush=True)
                return 0
            session.decide_plan("approve")
    if session.phase == "esperando_criterio":
        assert session.turns[-1].draft is not None
        draft = session.turns[-1].draft
        say(f"\nPROPUESTA · {draft.tipo.label} · {draft.titulo}")
        say(f"  evidencias: {len(draft.evidencias)}")
        for warning in draft.warnings:
            say(f"  aviso ({warning.code}): {warning.message}")
        if args.yes:
            from tero.evidence import accept_blockers

            blockers = accept_blockers(draft)
            if blockers:
                codes = ", ".join(sorted({w.code for w in blockers}))
                say(
                    f"  evidencia débil ({codes}) → escribo en borradores/ "
                    "(no derivados/). Usa la TUI y 'forzar…' si quieres forzar s."
                )
                result = session.decide_gate("b")
            else:
                result = session.decide_gate("s")
        else:
            print("\nPuerta docente: s sí · n no · b borrador · c corregir", flush=True)
            decision = input("criterio [s/n/b/c]: ").strip().lower() or "s"
            note = ""
            if decision == "c":
                note = input("crítica: ").strip()
            if decision == "s":
                from tero.evidence import accept_blockers

                if accept_blockers(draft):
                    print(
                        "Evidencia débil: s irá a error a menos que la nota empiece por 'forzar'.",
                        flush=True,
                    )
                    note = input("nota (vacío=bloquear / forzar …): ").strip()
            if decision not in {"s", "n", "b", "c"}:
                print("decisión inválida", flush=True)
                return 2
            try:
                result = session.decide_gate(decision, note)  # type: ignore[arg-type]
            except Exception as exc:  # noqa: BLE001
                from tero.errors import TeroError

                if isinstance(exc, TeroError) and exc.code == "evidence_blocked":
                    print(exc.message, file=sys.stderr)
                    return 2
                raise
        if result.path:
            print(f"\nescrito: {result.path}", flush=True)
        after = workspace.fingerprint_sources()
        if after != before:
            print(
                "ADVERTENCIA: un original cambió. tero no debería haberlo escrito.", file=sys.stderr
            )
            return 1
        print("Originales intactos.", flush=True)
        print("listo.", flush=True)
        return 0
    print(f"fase inesperada: {session.phase}", flush=True)
    errors = [event for event in events if event.get("type") == "error"]
    for event in errors:
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
    env["TERO_SKIP_PLAN"] = "1" if settings.skip_plan else "0"
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
