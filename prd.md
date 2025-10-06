# PRD: Gradio UI + Run Management for OMOP Cohort Workflow

## Overview
Build a Gradio-based UI for the full OMOP cohort workflow (Stage 1–4) with “Run Management” to create, monitor, and revisit multiple runs. The UX must stream logs per stage, persist artifacts (Stage 1 summary, Stage 2 concepts, Stage 3 SQL, Stage 4 analytics), and support a “fast-mode” for quicker iterations. Architecture should keep a clean service layer so Slack (and future UIs) can reuse the same run APIs.

## Goals
- Usable, end-to-end UI for Stage 1–4 with clear progress and logs.
- Create and manage multiple runs; view history; duplicate/resume; download artifacts.
- Adjustable speed/quality via runtime knobs and “fast-mode”.
- Architecture that can be fronted by Slack without refactoring core logic.

## Non‑Goals
- Full authentication/roles and multi-tenant quotas (future).
- Heavy enterprise features (SSO, audit logs) for the MVP.

## Users & Use Cases
- Data Scientists: iterate on definitions; compare runs; export SQL; run analytics.
- Clinicians/Researchers: sanity-check concept sets and summaries.
- Engineers: trigger runs via Slack or CI and fetch artifacts programmatically.

## UX Summary (Gradio) - IMPLEMENTED

**Dashboard + Chat Hybrid Design**

- **Left Sidebar: Run Management**
  - Run list table (ID, name, status, timestamp)
  - Search/filter (future)
  - Quick actions: Start, Duplicate, Delete
  - "+ New Run" button

- **Main Panel: Selected Run View (Chat-Style)**
  - Run header: name, status, duration
  - Input display (cohort description)
  - Stage progression (chat-like cards):
    - Stage 1: Clinical Clarification
    - Stage 2: Concept Discovery
    - Stage 3: SQL Generation
    - Stage 4: Analytics
  - Each stage shows:
    - Status icon (✅ complete, 🔄 running, ⏸ pending, ❌ failed)
    - Duration and metrics
    - Stage-specific results
  - Expandable "Download Artifacts" section with tabs:
    - Stage 1 JSON, Stage 2 JSON, Stage 3 SQL, Stage 4 JSON

- **New Run Modal** (hidden by default)
  - Cohort description input
  - Optional run name
  - Advanced Settings (collapsed):
    - Fast-mode toggle
    - Knobs: MAX_CONCEPT_SETS, MAX_QUERIES_PER_SET, SEARCH_TOP_K, etc.
  - Create/Cancel buttons

- **Auto-refresh**: Every 2 seconds for real-time status updates

**Key Design Decisions:**
- Single-page dashboard (no tabs)
- Run-first mental model (like email inbox)
- Progressive disclosure (stages expand as they run)
- Chat-style execution view (familiar UX)
- Fast mode hidden in Advanced Settings (not prominent)

## Core Flows
1) New Run → Stage 1 (chat) → Stage 2 (concept discovery) → Stage 3 (SQL) → Stage 4 (analytics) → Save artifacts
2) Resume Run → Load artifacts/logs; re-run selected stage(s)
3) Duplicate Run → Copy inputs/knobs/env to a new run; optionally modify inputs and rerun

## Functional Requirements
- Inputs
  - Cohort description (plain text)
  - Stage 2 knobs (env-backed): MAX_CONCEPT_SETS, MAX_QUERIES_PER_SET, SEARCH_TOP_K, PER_SET_TIME_LIMIT_SEC, MAX_ACCEPTED_PER_SET
  - BIGQUERY_PROJECT_ID, OMOP_DATASET_ID, BIGQUERY_LOCATION
- Outputs
  - Stage logs (streaming to UI and persisted)
  - Artifacts per stage: stage1.json (clinical), stage2.json (concepts), query.sql + validation.json, analytics.json
- Execution
  - Long-running tasks run in background threads; UI shows live status and partial results
  - Download buttons for artifacts

## Run Management
- Run model
  - `run_id`, `created_at`, `status` (pending|running|succeeded|failed)
  - `user_inputs` (cohort text, knobs, env)
  - `artifacts` (paths to stage outputs)
  - metrics: durations, token/call counts (if available), SQL bytes + cost
  - `error` (message/traceback when failed)
- Persistence (MVP)
  - File-based: `output/runs/{run_id}/` + `output/runs_index.json`
  - Each run folder contains: `stage1.json`, `stage2.json`, `query.sql`, `sql_validation.json`, `analytics.json`, `run_log.txt`, `inputs.json`
- Concurrency
  - ThreadPoolExecutor job per run; Gradio polls status; safe cancellation signal (best-effort)

## API & Integration Layer
- Python service module (no network) exposing:
  - `start_run(inputs) -> run_id`
  - `get_run(run_id) -> status + artifacts`
  - `run_stage(run_id, stage)` to resume/advance
- Slack (future)
  - Thin FastAPI wrapper that calls the same service
  - `/cohort` command kicks off a run; Slack bot posts updates and links to Gradio run page

## Performance & Bottlenecks
- Current bottlenecks
  - LLM calls for Stage 1/2/3 prompts
  - ATHENA network calls (search/details/relationships)
  - Queue-based exploration latency per concept set
  - BigQuery dry-run (network/API)
- Mitigations (MVP)
  - Caching: memoize ATHENA search + details/relationships keyed by (query, domain, vocab, standard_only); local cache folder `output/cache/`
  - Concurrency: parallel fetch details/relationships per batch (ThreadPool)
  - Early-stop: enforce per-set time budgets and `MAX_ACCEPTED_PER_SET`
  - Fast-mode presets: `MAX_CONCEPT_SETS=3`, `MAX_QUERIES_PER_SET=2`, `SEARCH_TOP_K=5`, `PER_SET_TIME_LIMIT_SEC=10`, `MAX_ACCEPTED_PER_SET=3`
  - SQL validation dedup: skip dry-run if SQL inputs unchanged (hash inputs)
  - Analytics scoped: top‑N, aggregate summaries first, defer heavy detail tables

## Quality & Observability
- Live logs in UI; streamed per stage; saved to `run_log.txt`
- Metrics surfaced: durations, ATHENA call counts, accepted anchors, SQL bytes & cost
- Error capture with actionable hints; persist partial artifacts to allow resume

## Security
- Secrets only on server: `OPENAI_API_KEY`, `GOOGLE_CLOUD_PROJECT` (ADC via `gcloud auth application-default login`)
- No client-side secret exposure; Slack integration will use signing secret & scoped tokens

## Rollout Plan
- Phase 1 (MVP, 2–4 days) ✅ COMPLETE
  - ✅ Gradio UI with dashboard + chat-style run view
  - ✅ Background runs with threading
  - ✅ Auto-refresh status updates (2s interval)
  - ✅ Artifacts saved + downloads
  - ✅ Fast-mode knobs (hidden in Advanced Settings)
  - ✅ Run management (create, list, start, duplicate, delete)
  - ✅ File-based persistence (output/runs/)
  - ✅ Service layer (reusable for Slack/API)
- Phase 2 (1–2 weeks)
  - Disk cache for ATHENA results; parallel fetches
  - Rich analytics charts (Plotly) and filters
  - Diff between runs (concepts/SQL)
- Phase 3 (2–3 weeks)
  - Optional FastAPI layer for Slack/API clients
  - SQLite (or Postgres) for runs/index to support multi-user environments

## Acceptance Criteria
- User can create a New Task and complete Stage 1–4 in the UI
- Each stage’s logs and outputs are visible in the UI and saved to `output/runs/{run_id}/`
- Runs tab lists prior runs; user can open, duplicate, delete
- Fast-mode produces results under target time budgets (e.g., < 2–5 min per full run with network variability)
- SQL dry-run results show bytes and $ cost (based on $5/TB) and are persisted
- Analytics tab shows counts and distributions and allows JSON download

## Open Questions / Risks
- ATHENA rate limits/call quotas: confirm limits; caching will reduce pressure
- LLM model availability/quotas: ensure fallback models are acceptable for Stage 2 reasoning
- BigQuery dataset variability (e.g., missing measurement): UI should adapt gracefully (already handled in Stage 4)

