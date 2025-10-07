
# Gradio UI for OMOP Cohort Builder

**Web interface for creating and managing cohort runs with chat-style execution view.**

---

## 🚀 Quick Start

```bash
# Install dependencies (includes Gradio)
make install

# Launch the UI
make run-ui
```

The UI will be available at: **http://localhost:7860**

---

## 🎨 UI Design

The interface uses a **dashboard + chat hybrid** design:

### Left Sidebar: Run List
- View all cohort runs (sorted by most recent)
- See status (Running, Complete, Failed, Pending)
- Quick access to start, duplicate, or delete runs

### Main Panel: Selected Run View
- **Chat-style progression** through stages 1-4
- Real-time updates as stages execute
- Expandable stage details with metrics
- Input display and configuration

### Bottom: Actions
- Start/resume runs
- Duplicate runs with same configuration
- Delete runs
- Download artifacts (JSON, SQL)

---

## 📋 Features

### ✅ Core Features (Phase 1 MVP)

- [x] Create new cohort runs
- [x] Run selection and history
- [x] Background execution with threading
- [x] Real-time status updates (auto-refresh every 2s)
- [x] Stage-by-stage progression display
- [x] Artifact download (JSON, SQL)
- [x] Fast mode toggle (hidden in advanced settings)
- [x] Run duplication
- [x] Run deletion
- [x] File-based persistence (`output/runs/`)

### 🚧 Planned Features (Phase 2+)

- [ ] Interactive Stage 1 (Q&A in UI chat)
- [ ] Live log streaming per stage
- [ ] Rich analytics charts (Plotly visualizations)
- [ ] Run comparison/diff view
- [ ] Search and filter runs
- [ ] Export multiple artifacts as zip
- [ ] ATHENA result caching
- [ ] Parallel concept fetching
- [ ] Run cancellation (best-effort)

---

## 🏗️ Architecture

### Service Layer (`service.py`)

Clean separation of concerns - can be used by:
- Gradio UI (current)
- Slack bot (future)
- FastAPI (future)
- CLI (future)

Key methods:
```python
service = CohortService()

# Create run
run_id = service.create_run(
    cohort_description="...",
    fast_mode=True
)

# Start execution (background)
service.start_run(run_id, stages=[1, 2, 3, 4])

# Get status
run = service.get_run(run_id)
print(run.status, run.get_progress_percentage())

# List all runs
runs = service.list_runs()
```

### Storage Layer (`storage.py`)

File-based persistence:
```
output/runs/
├── runs_index.json                  # Quick index for listing
├── 20251006_153142_408920/          # Run directory
│   ├── run.json                     # Run metadata
│   ├── inputs.json                  # User inputs
│   ├── stage1.json                  # Clinical definition
│   ├── stage2.json                  # Concept sets
│   ├── query.sql                    # Generated SQL
│   ├── sql_validation.json          # Dry-run results
│   ├── analytics.json               # Analytics summary
│   └── run_log.txt                  # Full execution log
```

### Models (`models.py`)

Strongly typed dataclasses:
- `CohortRun`: Complete run with status, stages, artifacts
- `UserInputs`: All configuration (description, knobs, BigQuery)
- `StageResult`: Per-stage execution details
- `StageMetrics`: Duration, call counts, errors

---

## 🎛️ Configuration

### Fast Mode

Hidden in "Advanced Settings" accordion when creating a new run.

**Fast Mode Defaults:**
- `MAX_CONCEPT_SETS`: 3 (vs 5)
- `MAX_QUERIES_PER_SET`: 2 (vs 3)
- `SEARCH_TOP_K`: 5 (vs 10)
- `PER_SET_TIME_LIMIT_SEC`: 10 (vs 30)
- `MAX_ACCEPTED_PER_SET`: 3 (vs 5)

Target: < 2-5 min per full run (network-dependent)

### BigQuery Settings

Currently read from environment (`.env`):
```env
BIGQUERY_PROJECT_ID=your-project
OMOP_DATASET_ID=your-dataset
BIGQUERY_LOCATION=US
```

Future: Will be configurable per-run in UI.

---

## 🔄 Workflow Execution

When you click "Start Run":

1. **Stage 1: Clinical Clarification**
   - Extracts demographics automatically
   - Asks clarifying questions (currently non-interactive)
   - Outputs structured clinical definition
   - Saved to: `stage1.json`

2. **Stage 2: Concept Discovery**
   - Reads Stage 1 output
   - Searches ATHENA for OMOP concepts
   - Validates and maps to standard concepts
   - Outputs concept sets
   - Saved to: `stage2.json`

3. **Stage 3: SQL Generation**
   - Reads Stage 1 + 2 outputs
   - Generates BigQuery SQL
   - Validates with dry-run (if BigQuery access available)
   - Saved to: `query.sql` + `sql_validation.json`

4. **Stage 4: Analytics**
   - Executes SQL in BigQuery
   - Computes cohort size, demographics, distributions
   - Saved to: `analytics.json`

Each stage runs in a background thread. The UI auto-refreshes every 2 seconds to show progress.

---

## 🐛 Troubleshooting

### UI won't start

```bash
# Make sure dependencies are installed
make install

# Check for port conflicts (default: 7860)
lsof -i :7860

# Run directly
uv run python projects/ui/app.py
```

### Runs not appearing

- Check `output/runs/runs_index.json` exists
- Verify run directories in `output/runs/`
- Look for errors in console output

### Stage execution fails

- Check `.env` has `OPENAI_API_KEY`
- For Stage 3/4: verify BigQuery credentials (`gcloud auth application-default login`)
- View full error in run display (shows traceback)

### UI is slow

- Reduce auto-refresh rate (edit `gr.Timer(value=2.0)` in `app.py`)
- Enable fast mode for quicker iterations
- Check network connection (ATHENA and OpenAI calls)

---

## 🧪 Development

### Run with auto-reload

```bash
# Gradio auto-reloads on file changes
uv run python projects/ui/app.py
```

### Test service layer independently

```python
from projects.ui.service import CohortService

service = CohortService()

# Create test run
run_id = service.create_run(
    cohort_description="Test cohort",
    fast_mode=True
)

# Start execution
service.start_run(run_id)

# Poll status
import time
while True:
    run = service.get_run(run_id)
    print(f"Status: {run.status}, Progress: {run.get_progress_percentage():.0f}%")
    if run.status in ["succeeded", "failed"]:
        break
    time.sleep(1)
```

### Add new UI features

1. Modify `app.py` (Gradio components)
2. Extend `service.py` if new backend logic needed
3. Update models in `models.py` if data structure changes
4. Adjust storage in `storage.py` for new artifact types

---

## 📚 References

- **Gradio Docs**: https://www.gradio.app/docs
- **PRD**: `../../prd.md` (Phase 1 MVP specification)
- **Service API**: See inline docstrings in `service.py`
- **Run Model**: See `models.py` for full data structure

---

## 🚀 Next Steps

After Phase 1 MVP is tested:

1. **Phase 2**: Analytics visualization with Plotly charts
2. **Phase 3**: Slack integration (same service layer)
3. **Phase 4**: ATHENA caching + parallel fetching
4. **Phase 5**: Interactive Stage 1 chat in UI

---

**Built for the OMOP community with ❤️**

