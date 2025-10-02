# Flujo Project

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
