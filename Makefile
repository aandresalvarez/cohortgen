.PHONY: install sync test lint typecheck format clean run run-log run-stats doctor check-credentials setup-bigquery help

# Default target
help:
	@echo "╔═══════════════════════════════════════════════════════════════════╗"
	@echo "║           OMOP Cohort Workflow - Makefile Commands               ║"
	@echo "╚═══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Setup:"
	@echo "  make install           Install/sync dependencies with uv"
	@echo "  make sync              Sync dependencies (uv sync)"
	@echo "  make check-credentials Check OpenAI and BigQuery credentials"
	@echo "  make setup-bigquery    Setup BigQuery authentication (interactive)"
	@echo ""
	@echo "Running:"
	@echo "  make run               Run full workflow (all 3 stages)"
	@echo "  make run-log           Run full workflow WITH LOGGING to timestamped file"
	@echo "  make run-ui            Launch Gradio UI (web interface)"
	@echo "  make stop-ui           Stop Gradio UI if running"
	@echo "  make run-stats         Run Stage 4 (Analytics) on latest SQL"
	@echo "  make run-clar          Run Stage 1 (Clinical Clarification)"
	@echo "  make run-cd            Run Stage 2 (Concept Discovery)"
	@echo "  make run-qb            Run Stage 3 (BigQuery SQL Generation)"
	@echo ""
	@echo "Testing:"
	@echo "  make test              Run all tests"
	@echo "  make test-verbose      Run tests with verbose output"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              Run linters (ruff)"
	@echo "  make typecheck         Type check code (mypy)"
	@echo "  make format            Format code (black)"
	@echo "  make fmt               Alias for format"
	@echo ""
	@echo "Development:"
	@echo "  make doctor            Check environment setup"
	@echo "  make clean             Remove virtual environment"
	@echo "  make deploy-cloudrun   Deploy to Google Cloud Run"
	@echo ""

# Install dependencies using uv (creates .venv if missing)
install: sync

# Sync dependencies using uv
sync:
	uv sync

# Check credentials setup
check-credentials:
	@echo "Checking credentials..."
	@uv run python projects/shared/secrets.py

# Setup BigQuery authentication
setup-bigquery:
	@./setup_bigquery_auth.sh

# Run full workflow (all 3 stages)
run:
	@cd projects/run && ./run_full_workflow.sh

# Run full workflow WITH LOGGING to timestamped file
run-log:
	@TIMESTAMP=$$(date +"%Y%m%d_%H%M%S") && \
	LOG_FILE="run_log_$${TIMESTAMP}.txt" && \
	echo "════════════════════════════════════════════════════════════════" && \
	echo "OMOP Cohort Workflow - Logging Run" && \
	echo "Log file: $${LOG_FILE}" && \
	echo "════════════════════════════════════════════════════════════════" && \
	echo "" && \
	$(MAKE) run 2>&1 | tee "$${LOG_FILE}" && \
	echo "" && \
	echo "════════════════════════════════════════════════════════════════" && \
	echo "✅ Complete log saved to: $${LOG_FILE}" && \
	echo "════════════════════════════════════════════════════════════════"

# Launch Gradio UI
run-ui:
	@echo "════════════════════════════════════════════════════════════════"
	@echo "🧬 OMOP Cohort Builder - Web UI"
	@echo "════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "Starting Gradio interface..."
	@echo "UI will be available at: http://localhost:7860"
	@echo ""
	@uv run python projects/ui/app.py

# Stop the Gradio UI if it's running
stop-ui:
	@echo "Stopping Gradio UI..."
	@lsof -ti:7860 | xargs kill -9 2>/dev/null && echo "✓ UI stopped" || echo "✓ UI was not running"

# Run Stage 1: Clinical Clarification
run-clar:
	@cd projects/clar && python3 hitl_clarification_working.py

# Run Stage 2: Concept Discovery
run-cd:
	@cd projects/cd && ./run_discovery.sh

# Run Stage 3: BigQuery SQL Generation
run-qb:
	@cd projects/qb && ./run_query_builder.sh

# Run Stage 4: Analytics
run-stats:
	@uv run python projects/stats/run_stats.py

## Individual stage runners for specific run ID (UI-based runs)
run-stage1: ## Run Stage 1 for specific run (Usage: make run-stage1 RUN_ID=20251006_123456_abc123)
	@if [ -z "$(RUN_ID)" ]; then echo "❌ Error: RUN_ID not set"; echo "Usage: make run-stage1 RUN_ID=your_run_id"; exit 1; fi
	@echo "Running Stage 1 for run $(RUN_ID)..."
	@uv run python -c "import sys; sys.path.insert(0, '.'); from projects.ui.service import CohortService; from projects.ui.storage import FileSystemStorage; storage = FileSystemStorage(); service = CohortService(storage); run = storage.load_run('$(RUN_ID)'); service._execute_stage1(run); print('✅ Stage 1 complete')"

run-stage2: ## Run Stage 2 for specific run (Usage: make run-stage2 RUN_ID=20251006_123456_abc123)
	@if [ -z "$(RUN_ID)" ]; then echo "❌ Error: RUN_ID not set"; echo "Usage: make run-stage2 RUN_ID=your_run_id"; exit 1; fi
	@echo "Running Stage 2 for run $(RUN_ID)..."
	@uv run python -c "import sys; sys.path.insert(0, '.'); from projects.ui.service import CohortService; from projects.ui.storage import FileSystemStorage; storage = FileSystemStorage(); service = CohortService(storage); run = storage.load_run('$(RUN_ID)'); service._execute_stage2(run); print('✅ Stage 2 complete')"

run-stage3: ## Run Stage 3 for specific run (Usage: make run-stage3 RUN_ID=20251006_123456_abc123)
	@if [ -z "$(RUN_ID)" ]; then echo "❌ Error: RUN_ID not set"; echo "Usage: make run-stage3 RUN_ID=your_run_id"; exit 1; fi
	@echo "Running Stage 3 for run $(RUN_ID)..."
	@uv run python -c "import sys; sys.path.insert(0, '.'); from projects.ui.service import CohortService; from projects.ui.storage import FileSystemStorage; storage = FileSystemStorage(); service = CohortService(storage); run = storage.load_run('$(RUN_ID)'); service._execute_stage3(run); print('✅ Stage 3 complete')"

run-stage4: ## Run Stage 4 for specific run (Usage: make run-stage4 RUN_ID=20251006_123456_abc123)
	@if [ -z "$(RUN_ID)" ]; then echo "❌ Error: RUN_ID not set"; echo "Usage: make run-stage4 RUN_ID=your_run_id"; exit 1; fi
	@echo "Running Stage 4 for run $(RUN_ID)..."
	@uv run python -c "import sys; sys.path.insert(0, '.'); from projects.ui.service import CohortService; from projects.ui.storage import FileSystemStorage; storage = FileSystemStorage(); service = CohortService(storage); run = storage.load_run('$(RUN_ID)'); service._execute_stage4(run); print('✅ Stage 4 complete')"

# Run tests
test:
	@cd projects/tests && ./run_tests.sh

# Run tests with verbose output
test-verbose:
	uv run pytest projects/tests/ -v --tb=long

# Lint code
lint:
	uv run ruff check projects/

# Type-check code
typecheck:
	uv run mypy projects/ --ignore-missing-imports

# Format code
format:
	uv run black projects/

# Alias for formatter
fmt: format

# Environment doctor: check setup
doctor:
	@echo "╔═══════════════════════════════════════════════════════════════════╗"
	@echo "║              Environment Health Check                             ║"
	@echo "╚═══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Python executable:"
	@which python3 || echo "  ❌ python3 not found"
	@echo ""
	@echo "Python version:"
	@python3 --version || echo "  ❌ Cannot get version"
	@echo ""
	@echo "UV version:"
	@uv --version || echo "  ❌ uv not found (install from: https://docs.astral.sh/uv/)"
	@echo ""
	@echo "Virtual environment:"
	@test -d .venv && echo "  ✅ .venv exists" || echo "  ⚠️  .venv not found (run: make install)"
	@echo ""
	@echo "Checking credentials..."
	@uv run python projects/shared/secrets.py
	@echo ""
	@echo "Project structure:"
	@test -d projects/clar && echo "  ✅ Stage 1 (clar) exists" || echo "  ❌ Stage 1 missing"
	@test -d projects/cd && echo "  ✅ Stage 2 (cd) exists" || echo "  ❌ Stage 2 missing"
	@test -d projects/qb && echo "  ✅ Stage 3 (qb) exists" || echo "  ❌ Stage 3 missing"
	@test -d projects/run && echo "  ✅ Orchestration (run) exists" || echo "  ❌ Orchestration missing"
	@test -d projects/shared && echo "  ✅ Shared utilities exist" || echo "  ❌ Shared utilities missing"
	@test -d projects/tests && echo "  ✅ Tests exist" || echo "  ❌ Tests missing"
	@echo ""

# Deploy to Google Cloud Run
deploy-cloudrun:
	@test -f deploy/cloud_run_deploy.sh || (echo "❌ Deploy script not found" && exit 1)
	@./deploy/cloud_run_deploy.sh

# Remove the virtual environment
clean:
	rm -rf .venv
	rm -f uv.lock
	@echo "✅ Virtual environment removed"
