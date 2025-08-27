"""
Lightweight path helper for Flujo projects.

When Python starts, it imports this module automatically if present on sys.path.
We detect if the current shell directory looks like a Flujo project (has
`flujo.toml` or `pipeline.yaml`) and ensure that directory is on `sys.path`.

This makes `import skills` work when users run `flujo` directly inside a
project directory, without needing to set PYTHONPATH manually.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_flujo_project_root(start: Path) -> Path | None:
    for p in [start, *start.parents]:
        if (p / "flujo.toml").exists() or (p / "pipeline.yaml").exists():
            return p
    return None


def _ensure_project_on_sys_path() -> None:
    # Prefer the shell's original working directory. If unavailable, fall back
    # to the current process cwd.
    pwd = os.environ.get("PWD")
    start = Path(pwd) if pwd else Path.cwd()
    project = _find_flujo_project_root(start)
    if not project:
        return

    proj_str = str(project)
    # Insert the absolute project path at the front to avoid being affected if
    # downstream tooling changes cwd later.
    if proj_str not in sys.path:
        sys.path.insert(0, proj_str)


try:
    _ensure_project_on_sys_path()
except Exception:
    # Never block interpreter startup due to path helper issues.
    pass
