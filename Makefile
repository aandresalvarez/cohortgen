.PHONY: install sync test lint format clean

# Create/refresh the venv and install deps
install: sync

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

# Format code
format:
	uv run black .

# Remove the virtual environment
clean:
	rm -rf .venv
	rm -f uv.lock
