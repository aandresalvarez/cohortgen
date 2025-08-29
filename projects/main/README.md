#  Cohort Copilot

Welcome! This project is scaffolded for use with Flujo.

## Getting Started

- Generate a pipeline with the AI Architect:
  - `uv run flujo create --goal "Fetch a webpage and summarize it"`
- Validate your pipeline:
  - `uv run flujo dev validate --strict`
- Run a pipeline from `pipeline.yaml`:
  - `uv run flujo run -p pipeline.py --input "Hello"` (for Python pipelines)
  - `uv run flujo dev validate --strict` then use your orchestrator for YAML pipelines.

## Architect Defaults

This project enables the agentic Architect (state machine) by default via `flujo.toml`:

```
[architect]
state_machine_default = true
```

- To disable by default, set `state_machine_default = false` or remove the section.
- Per-run overrides:
  - Force agentic: `FLUJO_ARCHITECT_STATE_MACHINE=1`
  - Force minimal: `FLUJO_ARCHITECT_MINIMAL=1`
- CLI override on the create command:
  - `uv run flujo create --agentic --goal "..."`
  - `uv run flujo create --no-agentic --goal "..."`

## Notes

- Skills live under `skills/`; register new tools there or via entry points.
- Budgets and execution limits can be configured in `flujo.toml` under `[budgets]`.
- See docs for more: https://aandresalvarez.github.io/flujo/

## Env-Driven BigQuery/OMOP Configuration

This project reads environment variables (loaded via `.env` per `flujo.toml`) to configure BigQuery and the OMOP dataset:

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to a GCP service account JSON. If unset, Application Default Credentials (ADC) are used.
- `BIGQUERY_PROJECT_ID`: GCP project ID to use for queries/dry-runs.
- `OMOP_DATASET_ID`: BigQuery dataset prefix for OMOP tables (e.g., `bigquery-public-data.cms_synthetic_patient_data_omop`).
- `BIGQUERY_LOCATION`: Region for BigQuery jobs (e.g., `US`).

Defaults:
- If `OMOP_DATASET_ID` is not set, the pipeline defaults to `bigquery-public-data.cms_synthetic_patient_data_omop`.
- If `BIGQUERY_LOCATION` is not set, it defaults to `US`.

Where used:
- The pipeline step `resolve_omop_dataset_id` pulls `OMOP_DATASET_ID` (with default) for SQL generation.
- BigQuery dry-run uses `BIGQUERY_PROJECT_ID` and `BIGQUERY_LOCATION` if provided.

## Orchestrating Sub‑Pipelines (Separation of Concerns)

Main can delegate to the sibling pipelines for clearer separation:

- `projects/clarification`: clarification + cohort definition (not yet wired by default)
- `projects/concept_discovery`: concept set discovery via ATHENA
- `projects/query_builder`: SQL generation + BigQuery dry‑run

Enable sub‑pipelines in Main by setting:

- `USE_SUBPIPELINES=1` (in `projects/main/.env` or your shell)

Behavior when enabled:
- Concept discovery: Main calls `concept_discovery/pipeline.yaml` with the cohort definition and ingests the resulting concept sets.
- Query builder: Main calls `query_builder/pipeline.yaml` non‑interactively by passing a JSON payload as `initial_prompt`:
  `{ "cohort_definition": "...", "concept_sets": { ... } }`.
  The query builder now parses this payload automatically.

Notes:
- Main falls back to its internal concept discovery + SQL generation when `USE_SUBPIPELINES` is unset.
- Clarification sub‑pipeline can be wired similarly; today Main keeps its own clarification flow for continuity.
