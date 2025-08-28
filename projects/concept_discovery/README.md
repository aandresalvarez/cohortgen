# Concept Discovery Pipeline

 Agentic pipeline to map a cohort definition into OMOP concept sets using ATHENA.

## What it does

- Decomposes a free‑text cohort definition into concept set intents (conditions, drugs, procedures, measurements, etc.).
- Searches ATHENA for initial candidates and then uses an agentic refiner to explore relationships (e.g., 'Maps to', hierarchy) to select STANDARD ('S') concepts per set.
 - Produces a final JSON spec: `{ concept_sets: [{ name, concepts: [{ concept_id, concept_name }], concept_ids, concept_names, include_descendants, standard_only }], assumptions: [] }` suitable for ATLAS concept set creation. Only standard concepts (standard_concept = 'S') are selected by default.

## Requirements

 - Python package: `athena-client`
  - Install: `pip install athena-client`
  - Public ATHENA is used by default; no keys required.
- Flujo CLI available and configured (see project root docs).

## Run

1) Validate the pipeline:
   - `uv run flujo dev validate --strict`

2) Run the pipeline from YAML:
   - `uv run flujo dev validate --strict` (validate first)
   - Then use your orchestrator to run `pipeline.yaml` (conversation is HITL-driven).

You will be prompted to paste a cohort definition. The pipeline will decompose concepts, search ATHENA, have an agent explore candidates to find STANDARD concepts, and output a final JSON concept set spec.

## Notes

- Skills live under `skills/` (`skills/athena_tools.py` provides the ATHENA integration and agent-friendly wrappers: `athena_search`, `athena_details`, `athena_relationships`, `athena_summary`, `athena_graph`).
- Budgets and execution limits can be configured in `flujo.toml` under `[budgets]`.
- See docs for more: https://aandresalvarez.github.io/flujo/
