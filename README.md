# Flujo Project

Welcome! This project is scaffolded for use with Flujo.

## Getting Started

- Setup environment: `make install` (creates `.venv` and installs deps with uv)
- Initialize a Flujo project in this repo: `uv run flujo init`
- Run the default YAML pipeline: `uv run flujo run`
- Generate a pipeline with the AI Architect:
  - `uv run flujo create --goal "Fetch a webpage and summarize it"`
- Validate your pipeline:
  - `uv run flujo dev validate --strict`

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

- Use `uv run <cmd>` to run commands inside the project virtualenv.
- Skills live under `skills/`; register new tools there or via entry points.
- Budgets and execution limits can be configured in `flujo.toml` under `[budgets]`.
- For persistent state, set `state_uri = "sqlite:///.flujo/state.db"` in `flujo.toml`.
- See docs for more: https://aandresalvarez.github.io/flujo/

## Multiple Flujo projects

- Projects live under `projects/<name>/`. Each is an independent Flujo project.
- Initialize a new project: `uv run cohortgen init <name>`
- List projects: `uv run cohortgen list`
- Run a project: `uv run cohortgen run <name>`

You can still use the Flujo CLI directly by changing into a project directory:

- `cd projects/<name>`
- `uv run flujo run`
