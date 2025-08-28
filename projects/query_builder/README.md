# Flujo Project

Welcome! This project is scaffolded for use with Flujo.

## Getting Started

- Install dependencies (BigQuery support is included in `pyproject.toml`):
  - `uv sync`
- Validate the pipeline:
  - `uv run flujo dev validate --strict`
- Run the YAML pipeline:
  - Use your orchestrator per Flujo docs after validation.

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

### BigQuery Dry-Run Validation

- The pipeline performs a BigQuery dry run to validate generated SQL and will attempt up to 2 automatic fixes using an LLM if the dry run fails.
- Update or confirm the service account at `projects/query_builder/skills/service_account.json`.
- Dataset used (fixed): `bigquery-public-data.cms_synthetic_patient_data_omop` (US)
- The SQL generator will qualify OMOP tables with this prefix.
