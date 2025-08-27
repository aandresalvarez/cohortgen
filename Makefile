.PHONY: install sync test lint typecheck format clean update-flujo

# Create/refresh the venv and install deps
# Also ensure Flujo git source is bumped to latest main
install: update-flujo sync

# Update Flujo pin in pyproject.toml to latest commit on main
update-flujo:
	@echo "Updating Flujo revision to latest main..."
	# Prefer running via uv's Python; fall back to system Python
	@uv run python scripts/update_flujo.py 2>/dev/null || \\
	python3 scripts/update_flujo.py 2>/dev/null || \\
	python scripts/update_flujo.py

# Sync dependencies using uv (creates .venv if missing)
sync:
	uv sync

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
