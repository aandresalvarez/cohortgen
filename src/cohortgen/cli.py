from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import __version__

ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT / "projects"


def _run(cmd: list[str], cwd: Path | None = None) -> int:
    env = os.environ.copy()
    if cwd is not None:
        # Ensure project-local Python packages (e.g., skills/) are importable
        pp = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            str(cwd) if not pp else f"{str(cwd)}{os.pathsep}{pp}"
        )
    return subprocess.call(cmd, cwd=str(cwd) if cwd else None, env=env)


def cmd_list(_: argparse.Namespace) -> int:
    PROJECTS_DIR.mkdir(exist_ok=True)
    found = []
    for p in sorted(PROJECTS_DIR.iterdir() if PROJECTS_DIR.exists() else []):
        if not p.is_dir():
            continue
        if (p / "flujo.toml").exists():
            found.append(p.name)
    if not found:
        print("No Flujo projects found under 'projects/'.")
    else:
        print("Projects:")
        for name in found:
            print(f"- {name}")
    return 0


def cmd_init(ns: argparse.Namespace) -> int:
    name = ns.name
    PROJECTS_DIR.mkdir(exist_ok=True)
    target = PROJECTS_DIR / name
    target.mkdir(parents=True, exist_ok=True)
    rc = _run(["flujo", "init"], cwd=target)
    return rc


def cmd_run(ns: argparse.Namespace) -> int:
    name = ns.name
    target = PROJECTS_DIR / name
    if not (target / "flujo.toml").exists():
        print(
            f"Project '{name}' not found or not initialized under 'projects/'.",
            file=sys.stderr,
        )
        return 2
    # Pass through additional args after --
    extra = ns.args or []
    cmd = ["flujo", "run", *extra]
    return _run(cmd, cwd=target)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cohortgen", description="Manage multiple Flujo subprojects."
    )
    p.add_argument("--version", action="version", version=f"cohortgen {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_list = sub.add_parser("list", help="List Flujo projects under 'projects/'.")
    s_list.set_defaults(func=cmd_list)

    s_init = sub.add_parser(
        "init", help="Initialize a new Flujo project under 'projects/<name>'."
    )
    s_init.add_argument("name", help="Project name")
    s_init.set_defaults(func=cmd_init)

    s_run = sub.add_parser("run", help="Run a Flujo project by name.")
    s_run.add_argument("name", help="Project name")
    s_run.add_argument(
        "args", nargs=argparse.REMAINDER, help="Args passed to 'flujo run' after --"
    )
    s_run.set_defaults(func=cmd_run)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":
    raise SystemExit(main())
