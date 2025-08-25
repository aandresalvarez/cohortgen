cohortgen

Python project managed with `uv` (fast package/dependency manager). Includes a simple CLI and a
Makefile for common tasks.

Prerequisites
- Install `uv`: https://docs.astral.sh/uv/getting-started/installation/
- Python: this project targets `>=3.11`. `uv` will install/manage it for you.

Quick Start
- Bootstrap environment and install deps: `make install`
- Run the CLI: `uv run python -m cohortgen`
- Run tests: `make test`
- Lint and type-check: `make lint`
- Format: `make format`

Daily Usage
- Add a runtime dependency: `uv add <package>`
- Add a dev-only tool: `uv add --group dev <package>`
- Re-sync after edits to deps or Python version: `uv sync`

CLI
- Module entrypoint: `python -m cohortgen`
- Help: `python -m cohortgen --help`

Project Layout
- Source code: `src/cohortgen/`
- Tests: `tests/`
- Virtual environment: `.venv/` (managed by `uv`)

Dependency Policy
- Reproducibility: External Git dependency `flujo` is pinned to an exact commit via
  `[tool.uv.sources]` in `pyproject.toml`.
- To update `flujo` to a newer revision:
  1) Pick the desired commit SHA (or tag) from https://github.com/aandresalvarez/flujo
  2) Edit `pyproject.toml` and change:
     `flujo = { git = "https://github.com/aandresalvarez/flujo.git", rev = "<NEW_SHA>" }`
  3) Run `uv sync`
  4) Run `make test`

Notes
- You do not need to manually activate the `.venv`; prefer `uv run <cmd>` which runs inside it.
- `uv.lock` captures full resolution for reproducible installs.

Automation
- A scheduled GitHub Action keeps `flujo` up to date:
  - Workflow: `.github/workflows/auto-update-flujo.yml`
  - Runs weekly (Mon 06:00 UTC) and on manual trigger.
  - Steps: update the pinned commit via `scripts/update_flujo.py`, run `uv sync` and tests, open a PR if green.
  - Adjust the cron or disable as needed.
