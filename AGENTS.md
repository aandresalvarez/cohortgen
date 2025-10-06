# Repository Guidelines

## Project Structure & Module Organization
- `projects/clar/` Stage 1: clinical clarification (`hitl_clarification_working.py`).
- `projects/cd/` Stage 2: concept discovery (`find_concepts.py`, `tools.py`).
- `projects/qb/` Stage 3: BigQuery SQL generation (`create_bigquery_sql.py`, `tools.py`).
- `projects/run/` Orchestration (`run_complete_workflow.py`, shell runners).
- `projects/shared/` Shared utilities (`secrets.py`).
- `projects/tests/` Pytest suite (unit + integration).
- `disco/` Experimental/aux projects (custom tools, separate tests).
- Top-level: `Makefile`, `pyproject.toml`, `Dockerfile`, `deploy/`.

## Build, Test, and Development Commands
- `make install` Sync deps with uv (creates `.venv`).
- `make run` Run all stages; `make run-clar|run-cd|run-qb` for individual stages.
- `make test` Run tests; `make test-verbose` for detailed output.
- `make lint` Ruff checks; `make typecheck` Mypy; `make format` Black.
- `make doctor` Env health check; `make check-credentials` verify secrets.
- `make deploy-cloudrun` Deploy via `deploy/cloud_run_deploy.sh`.

## Coding Style & Naming Conventions
- Python 3.11+, line length 100. Tools: Ruff, Black, Mypy (configured in `pyproject.toml`).
- Modules/files: `snake_case.py` (e.g., `projects/cd/tools.py`).
- Functions/vars `snake_case`, Classes `PascalCase`, constants `UPPER_SNAKE`.
- Keep functions small, pure, and testable; avoid side effects in imports.

## Testing Guidelines
- Framework: Pytest. Location: `projects/tests/` (discovery per `pyproject.toml`).
- Naming: files `test_*.py`, classes `Test*`, functions `test_*`.
- Run locally with `make test`. Prefer deterministic tests; mock network/LLM calls.
- Add tests for new behavior and bug fixes.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `ci:`, `chore:`.
  - Example: `feat(qb): add dry-run validation` | `fix(clar): handle missing age range`.
- PRs: clear description, link issues (`#123`), test plan (`make test` output), and relevant logs/SQL snippets.
- Ensure `make lint`, `make typecheck`, and `make test` pass before requesting review.

## Security & Configuration Tips
- Never commit secrets. Create `.env` from `env.example`; verify with `make check-credentials`.
- For BigQuery validation, authenticate with `gcloud auth application-default login`.
- Use `make doctor` to confirm environment and structure.

## Agent-Specific Instructions
- Place new code under the appropriate `projects/*` stage or `projects/shared/`.
- Prefer Makefile tasks; don’t bypass configured tooling.
- Keep changes minimal and scoped; avoid broad refactors without discussion.
