.PHONY: install sync test lint typecheck format clean update-flujo run validate doctor which-flujo openai-version

# Create/refresh the venv and install deps
# Also ensure Flujo git source is bumped to latest main
install: update-flujo sync

# Update Flujo pin in pyproject.toml to latest commit on main
update-flujo:
	@echo "Updating Flujo revision to latest main..."
	@uv run python scripts/update_flujo.py 2>/dev/null || python3 scripts/update_flujo.py 2>/dev/null || python scripts/update_flujo.py

# Sync dependencies using uv (creates .venv if missing)
sync:
	uv sync

# Validate orchestrator pipeline (projects/main)
validate:
	cd projects/main && uv run flujo dev validate --strict

# Run orchestrator pipeline with correct project venv
run:
	cd projects/main && uv run flujo run --debug-export

# Environment doctor: ensure you're using this project's venv and SDKs
doctor:
	@echo "Python used by uv:" && uv run python -c 'import sys; print(sys.executable)'
	@echo "OpenAI SDK version (project venv):" && uv run python -c 'import openai,inspect; print(getattr(openai, "__version__", "unknown"), inspect.getfile(openai))'
	@echo "flujo status (providers):" && uv run flujo status || true
	@echo "Which flujo binary:" && command -v flujo || true
	@echo "Env file configured in flujo.toml (projects/main):" && sed -n '1,80p' projects/main/flujo.toml | sed -n '1,40p' | grep -i '^env_file' || true

# Convenience helpers
which-flujo:
	@command -v flujo || true

openai-version:
	uv run python -c 'import openai,inspect; print(getattr(openai, "__version__", "unknown"), inspect.getfile(openai))'

# Run tests
test:
	uv run pytest -q

# Lint code
lint:
	uv run ruff check .
	uv run mypy src

# Type-check code
typecheck:
	uv run mypy src

# Format code
format:
	uv run black .

# Remove the virtual environment
clean:
	rm -rf .venv
	rm -f uv.lock
