#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path


PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
FLUJO_REPO = "https://github.com/aandresalvarez/flujo.git"
FLUJO_REF = "refs/heads/main"


def get_latest_commit(repo: str, ref: str) -> str:
    out = subprocess.check_output(["git", "ls-remote", repo, ref], text=True).strip()
    if not out:
        raise RuntimeError(f"No refs found for {repo} {ref}")
    sha = out.split()[0]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError(f"Invalid SHA from ls-remote: {sha}")
    return sha


def update_pyproject_rev(pyproject: Path, new_sha: str) -> bool:
    text = pyproject.read_text()
    # Match the flujo source line and capture current rev
    pattern = re.compile(
        r"^(\s*flujo\s*=\s*\{[^\n}]*rev\s*=\s*\")([0-9a-f]{40})(\"[^\n}]*\}\s*)$",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        raise RuntimeError("Could not find flujo source with a rev in pyproject.toml")
    current = m.group(2)
    if current == new_sha:
        return False
    new_text = pattern.sub(r"\g<1>" + new_sha + r"\g<3>", text, count=1)
    pyproject.write_text(new_text)
    return True


def main() -> int:
    new_sha = get_latest_commit(FLUJO_REPO, FLUJO_REF)
    changed = update_pyproject_rev(PYPROJECT, new_sha)
    if changed:
        print(f"Updated flujo rev to {new_sha}")
    else:
        print("flujo rev already up-to-date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

