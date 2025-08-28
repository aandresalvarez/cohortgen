# Clinical Researcher Improvements (Prioritized)

A prioritized backlog of high‑impact UX and pipeline changes to make this project easier and safer for clinical researchers to use end‑to‑end.

1) Env‑Driven BigQuery + OMOP Config (P0)
- Type: Pipeline, DX
- Goal: Remove hardcoded credentials/paths and dataset IDs; use environment variables and sensible defaults.
- Details: 
  - Read `GOOGLE_APPLICATION_CREDENTIALS`, `BIGQUERY_PROJECT_ID`, `OMOP_DATASET_ID`, `BIGQUERY_LOCATION`.
  - Unify `bq_tools.py` to prefer ADC or env var path; remove hardcoded `DEFAULT_SA_PATH` in `main/skills/bq_tools.py`.
  - Parameterize `omop_dataset_id` step in `main/pipeline.yaml` via context/env.
- Acceptance: Pipeline runs with only env config; no code edits required per environment.

2) Concept Set Review Step (HITL) (P0)
- Type: UX, Pipeline
- Goal: Let researchers inspect and edit concept sets before SQL generation.
- Details: 
  - Add a HITL step after `search_athena` that renders a human‑readable table (name, domain, vocabulary, include_descendants, standard_only, candidate count) and accepts edits/additions/removals of concept IDs.
  - Persist back to `scratchpad.concept_sets`.
- Acceptance: Users can modify concept sets inline and proceed; modifications are reflected in downstream SQL.

3) Quick “Preview Counts” QC (P0)
- Type: UX, Validation
- Goal: Surface zero/implausible counts early.
- Details:
  - Optional step that runs small aggregate queries (total count, by sex/age bands, by year) against the selected OMOP dataset.
  - Present summary and flag issues prior to final SQL handoff.
- Acceptance: A preview summary is shown; zero/near‑zero sets are flagged with an option to revise.

4) Assumptions Ledger + Acknowledgment Gate (P0)
- Type: UX, Governance
- Goal: Make implicit assumptions explicit and acknowledged.
- Details: 
  - Aggregate “Assumptions” from cohort definition and concept summarizer; show a checklist requiring user acknowledgment before SQL generation.
- Acceptance: Gate prevents proceeding until assumptions are acknowledged; acknowledgments stored in run metadata.

5) Study Setup Wizard (Checklist) (P1)
- Type: UX
- Goal: Reduce cognitive load with a guided flow.
- Details: 
  - Consolidate slot filling (metric, population, window, grouping, exclusions) into a single wizard page with progress and unresolved items.
  - Display live “current cohort definition” preview.
- Acceptance: Wizard can complete all required slots without free‑form back‑and‑forth; produces the same `cohort_definition` artifact.

6) SQL Parameterization & Standards (P1)
- Type: Pipeline
- Goal: Make SQL generation consistent and configurable.
- Details: 
  - Enforce per‑run config for `project.dataset` and location.
  - Ensure consistent descendant expansion via `concept_ancestor` when `include_descendants=true`.
- Acceptance: Generated SQL always qualifies tables correctly and applies descendant expansion consistently.

7) SQL Templates for Common Patterns (P1)
- Type: Pipeline
- Goal: Reduce LLM variability and errors.
- Details: 
  - Provide template fragments for: index selection, washout, continuous observation, visit setting filters, deduplication.
  - Prompt the LLM to fill parameters rather than free‑form code.
- Acceptance: Lower dry‑run failure rate; cleaner, more standardized SQL.

8) ATLAS Export (Cohort + Concepts) (P1)
- Type: Interoperability
- Goal: Enable direct use in OHDSI ATLAS.
- Details:
  - Emit ATLAS cohort JSON and concept set JSON alongside plain text.
  - Keep export behind a toggle and write to `debug/`.
- Acceptance: Files import cleanly into ATLAS with equivalent logic.

9) Visual Diff of Cohort Definition (P1)
- Type: UX
- Goal: Improve transparency across clarification turns.
- Details:
  - Show highlighted changes between previous and current definition when slots change or user edits occur.
- Acceptance: Users can easily audit how each answer affected the phenotype.

10) Curated Concept Plan Library (P1)
- Type: Content, Pipeline
- Goal: Faster starts for common phenotypes.
- Details:
  - Ship vetted concept plans (AMI, HF, AF, COPD, Diabetes, Influenza, COVID‑19, CKD, Stroke, Pregnancy, etc.) with provenance and dates.
  - Allow selection during wizard and as fallback.
- Acceptance: Library selectable from UI; plans flow through ATHENA search and summarization.

11) ATHENA Evidence View (P1)
- Type: UX
- Goal: Better decision support when selecting concepts.
- Details: 
  - Display standard status, domain, vocabulary, relationships (e.g., Maps to) with links to ATHENA pages in the review step.
- Acceptance: Users can expand a concept row to view details and relationships.

12) Baseline “Table 1” QC (P2)
- Type: Validation
- Goal: Standard cohort sanity view.
- Details: 
  - After final SQL, run a light aggregation to produce age bands, sex, index year, and visit type distributions.
  - Save CSV and quick HTML/Markdown summary.
- Acceptance: “Table 1” artifacts are generated and attached to the run.

13) Sanity Probes & Negative Controls (P2)
- Type: Validation
- Goal: Detect mis‑specification early.
- Details:
  - Provide a panel of mini‑queries (e.g., event rates over time; unrelated negative control outcomes).
- Acceptance: Warnings produced when probes show implausible patterns.

14) Audit Trail + Review Gates (P2)
- Type: Governance
- Goal: Improve traceability and approval control.
- Details:
  - Persist prompts, tool I/O, env config, and artifacts to `flujo_ops.db`.
  - Gate approvals at Definition, Concepts, SQL with role and notes.
- Acceptance: Complete run logs exist; approvals captured before progression.

15) Cost Transparency & Budgets (P2)
- Type: UX, Governance
- Goal: Avoid cost surprises.
- Details:
  - Estimate token and BigQuery costs pre‑run; enforce budgets from `flujo.toml`.
- Acceptance: Users see estimates and remaining budget; runs stop when limits are hit.

16) Caching & Parallel ATHENA Search (P2)
- Type: Performance
- Goal: Faster iterations.
- Details:
  - Cache ATHENA results per query and concept set.
  - Fan‑out searches concurrently and merge.
- Acceptance: Repeat runs are faster; identical queries hit cache.

17) Multi‑Warehouse Adapters (P3)
- Type: Interoperability
- Goal: Support OMOP beyond BigQuery.
- Details: 
  - Add adapters for Snowflake/Databricks/Postgres with warehouse‑specific SQL generators and validator skills.
- Acceptance: Users can select a warehouse; dry‑run/validation uses the correct adapter.

18) Notebook Handoff (P3)
- Type: Interoperability, UX
- Goal: Smooth analysis transition.
- Details:
  - Auto‑generate a Jupyter notebook that runs the final SQL, renders Table 1, and saves CSVs.
- Acceptance: Notebook opens and runs end‑to‑end with minimal edits.

19) Unit/Measurement Guards for Labs (P3)
- Type: Validation
- Goal: Safer measurement‑based cohorts.
- Details: 
  - Enforce unit standardization, plausible ranges, and value normalization for LOINC‑based sets; prompt for unit mappings.
- Acceptance: Lab filters are validated; warnings for mismatched units.

20) Cohort Stability Checks (P3)
- Type: Validation
- Goal: Robustness to small perturbations.
- Details: 
  - Compare counts across small window shifts (e.g., ±7 days) or alternate definitions (first‑ever vs first‑in‑window).
- Acceptance: Report shows stability metrics; flags large swings for review.

---

Implementation notes
- Start with P0: env‑driven config, review step, preview counts, and assumptions ledger—these remove the biggest usability blockers.
- P1 focuses on standardization (SQL templates), interoperability (ATLAS), and clarity (visual diff, evidence view, library).
- P2 adds governance and QC depth; P3 broadens platform reach and advanced validation.

