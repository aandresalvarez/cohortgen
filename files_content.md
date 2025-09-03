# 📂 Project File Contents

- 📁 **cohortgen**
  - [`README.md`](#cohortgen-readmemd)
  - [`extract.py`](#cohortgen-extractpy)
  - [`files_content.md`](#cohortgen-files_contentmd)
  - [`pyproject.toml`](#cohortgen-pyprojecttoml)
  - [`to_implement.md`](#cohortgen-to_implementmd)
    - 📁 **workflows**
      - [`auto-update-flujo.yml`](#cohortgen-github-workflows-auto-update-flujoyml)
      - [`ci.yml`](#cohortgen-github-workflows-ciyml)
  - 📁 **.pytest_cache**
    - [`README.md`](#cohortgen-pytest_cache-readmemd)
        - 📁 **flujo**
          - [`CHANGELOG.md`](#cohortgen-venv-share-doc-flujo-changelogmd)
          - [`README.md`](#cohortgen-venv-share-doc-flujo-readmemd)
  - 📁 **output**
    - [`last_run_error.txt`](#cohortgen-output-last_run_errortxt)
    - 📁 **clarification**
      - [`README.md`](#cohortgen-projects-clarification-readmemd)
      - [`__init__.py`](#cohortgen-projects-clarification-__init__py)
      - [`flujo.toml`](#cohortgen-projects-clarification-flujotoml)
      - [`pipeline.yaml`](#cohortgen-projects-clarification-pipelineyaml)
      - 📁 **skills**
        - [`custom_tools.py`](#cohortgen-projects-clarification-skills-custom_toolspy)
    - 📁 **concept_discovery**
      - [`README.md`](#cohortgen-projects-concept_discovery-readmemd)
      - [`__init__.py`](#cohortgen-projects-concept_discovery-__init__py)
      - [`flujo.toml`](#cohortgen-projects-concept_discovery-flujotoml)
      - [`pipeline.yaml`](#cohortgen-projects-concept_discovery-pipelineyaml)
      - 📁 **skills**
        - [`__init__.py`](#cohortgen-projects-concept_discovery-skills-__init__py)
        - [`athena_tools.py`](#cohortgen-projects-concept_discovery-skills-athena_toolspy)
        - [`custom_tools.py`](#cohortgen-projects-concept_discovery-skills-custom_toolspy)
    - 📁 **main**
      - [`README.md`](#cohortgen-projects-main-readmemd)
      - [`flujo.toml`](#cohortgen-projects-main-flujotoml)
      - [`pipeline.yaml`](#cohortgen-projects-main-pipelineyaml)
      - 📁 **skills**
        - [`custom_tools.py`](#cohortgen-projects-main-skills-custom_toolspy)
    - 📁 **query_builder**
      - [`README.md`](#cohortgen-projects-query_builder-readmemd)
      - [`__init__.py`](#cohortgen-projects-query_builder-__init__py)
      - [`flujo.toml`](#cohortgen-projects-query_builder-flujotoml)
      - [`pipeline.yaml`](#cohortgen-projects-query_builder-pipelineyaml)
      - 📁 **skills**
        - [`__init__.py`](#cohortgen-projects-query_builder-skills-__init__py)
        - [`bq_tools.py`](#cohortgen-projects-query_builder-skills-bq_toolspy)
        - [`custom_tools.py`](#cohortgen-projects-query_builder-skills-custom_toolspy)
  - 📁 **scripts**
    - [`update_flujo.py`](#cohortgen-scripts-update_flujopy)
  - 📁 **src**
    - [`sitecustomize.py`](#cohortgen-src-sitecustomizepy)
    - 📁 **cohortgen**
      - [`__init__.py`](#cohortgen-src-cohortgen-__init__py)
      - [`__main__.py`](#cohortgen-src-cohortgen-__main__py)
      - [`cli.py`](#cohortgen-src-cohortgen-clipy)
  - 📁 **tests**
    - [`test_athena_tools.py`](#cohortgen-tests-test_athena_toolspy)
    - [`test_cli.py`](#cohortgen-tests-test_clipy)
    - [`test_main_tools.py`](#cohortgen-tests-test_main_toolspy)
    - [`test_yaml_regressions.py`](#cohortgen-tests-test_yaml_regressionspy)

---

# Target Folder: cohortgen

## Folder: cohortgen

> ℹ️ *Note: Contains a virtual environment folder (e.g., `venv`, `.venv`). Contents are excluded.*

### File: `cohortgen/README.md`
<a name="cohortgen-readmemd"></a>
```markdown
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

```

### File: `cohortgen/pyproject.toml`
<a name="cohortgen-pyprojecttoml"></a>
```toml
[project]
name = "cohortgen"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "flujo",
    # Pin to a version that still provides openai.resources.chat.Chat
    "openai==1.99.9",
    "athena-client==1.0.27",
    "google-cloud-bigquery>=3.19.0,<4.0.0",
    "sqlalchemy-bigquery>=1.10.0,<2.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.23",
    "ruff>=0.5",
    "mypy>=1.10",
    "black>=24",
    "ipython",
]

[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cohortgen"]
# Ensure top-level sitecustomize.py is included in wheels
[tool.hatch.build.targets.wheel.force-include]
"src/sitecustomize.py" = "sitecustomize.py"

[tool.uv]
package = true

[tool.uv.sources]
flujo = { git = "https://github.com/aandresalvarez/flujo.git", rev = "b6a0b6de286bb56d5d7ef30459acb0ae988b9364" }

[project.scripts]
cohortgen = "cohortgen.cli:main"

```

### File: `cohortgen/to_implement.md`
<a name="cohortgen-to_implementmd"></a>
```markdown
Of course. This is an excellent and quite sophisticated multi-pipeline project. After reviewing the `main` pipeline and its sub-pipelines (`clarification`, `concept_discovery`, and `query_builder`), here is a detailed analysis of potential bugs, issues, and high-impact improvements.

The feedback is categorized into three groups:
1.  **Bugs & Critical Issues:** Potential runtime errors or logical flaws that could break the workflow.
2.  **Architectural Improvements:** Suggestions to make the pipelines more robust, efficient, and maintainable.
3.  **User Experience (UX) & Operational Improvements:** Enhancements for the clinical researcher using the system.

---

### 1. Bugs & Critical Issues

#### Bug: The Main Orchestrator's HITL Pause/Resume Flow is Broken
*   **Problem:** The `main/pipeline.yaml` is designed to orchestrate the three sub-pipelines. It correctly uses `propagate_hitl: true` to allow a pause from a sub-pipeline to stop the main flow. However, there is no mechanism to **resume correctly**.
*   **Impact:** When the `clarification` pipeline pauses to ask the user a question, the user's answer is collected, but the `main` pipeline simply moves on to the `concept_discovery` step. It **never re-runs the `clarification` pipeline** with the new information. The user's input is effectively ignored, and the cohort definition will be incomplete.
*   **Suggested Solution:** The main orchestrator needs to be a `LoopStep` or `StateMachineStep`.
    *   **Loop-based Fix:** Wrap the three sub-pipeline calls inside a loop that runs until a "finalized" state is reached in the context. When a sub-pipeline pauses, the loop can re-run that same sub-pipeline on the next iteration after collecting the user's input.

#### Bug: Fragile Template Access in `clarification/pipeline.yaml`
*   **Problem:** The `clarification_loop`'s `history_template` uses `{{history.0.content}}` to reference the user's initial goal. This assumes the conversation history will always have at least one item.
*   **Impact:** If the preceding `get_initial_goal` step fails or returns an empty string for any reason, the `conversation_history` list could be empty. Accessing `history.0` would then cause a template rendering error, crashing the pipeline.
*   **Suggested Solution:** Use a more defensive templating approach.
    ```yaml
    # Instead of this:
    # Initial goal: {{history.0.content}}

    # Use this:
    Initial goal: {{ steps.get_initial_goal.output }}
    ```
    This directly references the output of the step that provides the goal, which is much more robust.

#### Bug: Brittle Data Passing Between Main and Sub-pipelines
*   **Problem:** The `main` pipeline passes data to sub-pipelines using expressions like `{{ (context.scratchpad.cohort_definition.value or context.scratchpad.cohort_definition) | tojson }}`. The `.value` access assumes the data is always a Pydantic wrapper model.
*   **Impact:** If a preceding step returns a raw string or dictionary instead of the expected model (which can easily happen), the `.value` access will fail, crashing the pipeline. This makes the data contract between pipelines very brittle.
*   **Suggested Solution:** Create a dedicated adapter step or use a safer templating function to normalize the data before passing it.
    *   Create a small, reusable skill like `skills.custom_tools:get_cohort_definition_text` that knows how to safely unwrap the object.
    *   Use a safer template fallback: `{{ (context.scratchpad.cohort_definition.value if context.scratchpad.cohort_definition.value is defined else context.scratchpad.cohort_definition) }}`.

---

### 2. Architectural Improvements

#### Improvement: Convert Hardcoded SQL Repair into a Dynamic Loop
*   **Problem:** The `query_builder/pipeline.yaml` uses a hardcoded, nested series of conditional steps (`fix_if_fail_1`, `fix_if_fail_2`) to attempt SQL repair. It's limited to exactly two repair attempts.
*   **Impact:** This is rigid and verbose. If a fix requires three attempts, the pipeline will fail. It's also difficult to modify or extend.
*   **Suggested Solution:** Replace the nested conditionals with a single `LoopStep`.
    *   The loop body would contain: `generate/fix_sql` -> `dry_run`.
    *   The `exit_expression` would be `steps['dry_run'].success`.
    *   Set `max_loops` to a reasonable limit (e.g., 3 or 4) to prevent infinite repair cycles.
    *   This makes the logic cleaner, more dynamic, and easier to configure.

#### Improvement: Consolidate Redundant Agents in Concept Discovery
*   **Problem:** The `concept_discovery` pipeline uses two different agents, `candidate_expander` and `concept_refiner`, that have the exact same tools and a very similar goal: to explore Athena search results and find standard concepts.
*   **Impact:** This adds unnecessary complexity and increases the potential for inconsistent logic. It also likely increases cost and latency due to running two separate, complex agentic steps.
*   **Suggested Solution:** Combine the logic into a single, more powerful agent.
    *   Create one agent named `concept_explorer_agent` that is responsible for the entire workflow: taking initial candidates, exploring relationships, running new searches if needed, and producing a final list of standard concepts.
    *   This simplifies the pipeline from `search -> expand -> smart_expand -> refine` to a much cleaner `search -> explore_and_refine`.

#### Improvement: Make Athena Tool Calls More Robust
*   **Problem:** The `athena_tools.py` skills make direct calls to the `athena-client`. If any of these calls fail due to a network issue or temporary API problem, the entire step fails.
*   **Impact:** The pipeline is not resilient to transient network errors, which are common in real-world use.
*   **Suggested Solution:** Add retry logic to the Athena tool functions.
    *   You can use a library like `tenacity` or a simple `for` loop with `try/except` and `asyncio.sleep` to retry failed API calls 2-3 times with exponential backoff. This would make the `concept_discovery` pipeline much more reliable.

---

### 3. User Experience (UX) & Operational Improvements

*This project already has an excellent `improvements.md` file. The suggestions below align with and reinforce the high-priority items listed there.*

#### Improvement: Add a HITL Review Step for Concept Sets
*   **Problem:** The `concept_discovery` pipeline agentically generates concept sets and immediately passes them to the `query_builder`. The clinical researcher never gets a chance to review or approve them.
*   **Impact:** This is a major operational risk. An LLM hallucination or misinterpretation could lead to an incorrect concept set, resulting in a flawed SQL query and an invalid cohort. This is the **single biggest risk** in the current workflow.
*   **Suggested Solution:** Add a `HumanInTheLoopStep` after `concept_discovery` and before `query_builder` in the `main` pipeline.
    *   This step should present the generated concept sets (name, included concepts, etc.) to the user for approval.
    *   Allow the user to say "yes" to proceed, or "no" with feedback to trigger a re-run of the concept discovery step. (This reinforces the need for the `main` pipeline to be a loop).

#### Improvement: Provide Status Updates in the Main Orchestrator
*   **Problem:** The `main` pipeline runs three complex sub-pipelines sequentially. From the user's perspective, they provide a goal and then wait a long time for a final SQL query, with no visibility into the progress.
*   **Impact:** Poor user experience. The user doesn't know if the system is working, stuck, or what stage it's on.
*   **Suggested Solution:** Add simple `stringify` steps in `main/pipeline.yaml` between the sub-pipeline calls to print status messages.
    ```yaml
    - kind: step
      name: run_clarification_subpipeline
      ...
    - kind: step
      name: status_update_1
      agent: "flujo.builtins.stringify"
      input: "✅ Cohort definition finalized. Now discovering medical concepts in ATHENA..."
    - kind: step
      name: run_concept_discovery_subpipeline
      ...
    ```

#### Improvement: Surface Key Assumptions to the User
*   **Problem:** The agents in sub-pipelines are correctly instructed to make and state assumptions (e.g., choosing a default time window). However, these assumptions are buried in the final text output.
*   **Impact:** The researcher might not notice a critical assumption that invalidates the cohort for their specific study.
*   **Suggested Solution:** As suggested in `improvements.md`, create an "Assumptions Ledger".
    *   After the `clarification` and `concept_discovery` steps, add a step that extracts any lines beginning with "Assumption:" from their outputs.
    *   Present this compiled list to the user in a `HumanInTheLoopStep` for explicit acknowledgment before proceeding to the final `query_builder` step. This creates a crucial governance gate.
```

## Folder: .pytest_cache

### File: `cohortgen/.pytest_cache/README.md`
<a name="cohortgen-pytest_cache-readmemd"></a>
```markdown
# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.

```

## Folder: .pytest_cache/v

## Folder: .pytest_cache/v/cache

## Folder: .ruff_cache

## Folder: .ruff_cache/0.12.10

## Folder: projects

## Folder: projects/clarification

### File: `cohortgen/projects/clarification/README.md`
<a name="cohortgen-projects-clarification-readmemd"></a>
```markdown
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

```

### File: `cohortgen/projects/clarification/__init__.py`
<a name="cohortgen-projects-clarification-__init__py"></a>
```python

```

### File: `cohortgen/projects/clarification/flujo.toml`
<a name="cohortgen-projects-clarification-flujotoml"></a>
```toml
# Flujo project configuration template

# Use an in-memory state backend by default for new projects
state_uri = "memory://"

# Load environment variables (API keys, etc.) from this file.
# Copy `.env.example` to `.env`, fill your keys, or change this path.
env_file = "../../.env"

[settings]
# default_solution_model = "gpt-4o-mini"
# reflection_enabled = true

# Centralized budgets (optional)
[budgets]
# [budgets.default]
# total_cost_usd_limit = 5.0
# total_tokens_limit = 100000

# Architect defaults
[architect]
# Enable the agentic Architect state machine by default for this project
state_machine_default = true
# To disable by default, set to false or remove this section.
# Per-run overrides:
#   - Force agentic: export FLUJO_ARCHITECT_STATE_MACHINE=1
#   - Force minimal: export FLUJO_ARCHITECT_MINIMAL=1

# Explicit cost configuration to silence pricing warnings and track spend accurately
[cost]
  strict = false
  [cost.providers]
    [cost.providers.openai]
      # Set explicit pricing for models used in this project
      [cost.providers.openai.gpt-4o]
        prompt_tokens_per_1k = 0.005   # USD per 1K prompt tokens
        completion_tokens_per_1k = 0.015 # USD per 1K completion tokens
      # Optional: include minis if you switch
      [cost.providers.openai.gpt-4o-mini]
        prompt_tokens_per_1k = 0.00015
        completion_tokens_per_1k = 0.0006
      # Explicit pricing for GPT-5 family used in this pipeline
      # Note: Values here are placeholders for manual testing only.
      #       Update with accurate prices for production tracking.
      [cost.providers.openai.gpt-5]
        prompt_tokens_per_1k = 0.01
        completion_tokens_per_1k = 0.03
      [cost.providers.openai.gpt-5-mini]
        prompt_tokens_per_1k = 0.002
        completion_tokens_per_1k = 0.006

```

### File: `cohortgen/projects/clarification/pipeline.yaml`
<a name="cohortgen-projects-clarification-pipelineyaml"></a>
```yaml
# 📂 flujo project/pipeline.yaml (Final Corrected Version)

version: "0.1"
name: "zero_boilerplate_conversation"

pipeline_config:
  conversation_mode: true

agents:
  clarification_agent:
    model: "openai:gpt-5-mini"
    model_settings:
      openai_reasoning_effort: "low"       # low | medium | high
    timeout: 120
    max_retries: 1
    system_prompt: |
      You are an expert clinical data analyst. Use the conversation history and current input to drive a slot-filling clarification.
      - Required slots: metric (e.g., count, rate), cohort/population (who to include), time window (e.g., year or dates), grouping/dimensions (e.g., age, sex, location), and any filters/exclusions.
      - Maintain a running slots map from prior turns; never re-ask for a slot that has already been answered in history. Assume short replies answer your most recent question unless contradicted.
      - Ask ONE clarifying question at a time that explicitly mentions the initial goal phrase found in the history.
      - Only return {"action":"finish"} when all required slots are sufficiently specified OR the user explicitly says they are done (e.g., "finish", "done", "go ahead", "that's all").
      - Output schema must be respected exactly: {"action":"ask","question":"..."} or {"action":"finish"}.
    output_schema:
      type: object
      properties:
        action: { type: string, enum: [ask, finish] }
        question: { type: string }
      required: [action]

  cohort_definer:
    model: "openai:gpt-5-mini"
    model_settings:
      openai_reasoning_effort: "medium"
    timeout: 120
    max_retries: 1
    system_prompt: |
      You are an expert clinical researcher and OMOP CDM cohort designer.
      Write a strong, unambiguous plain‑text cohort definition to be implemented later in ATLAS (no SQL, no JSON).
      Use the initial goal, the full clarification Q/A, and the synthesized slots. Resolve ambiguity by proposing explicit, conservative defaults and label them as "Assumption:" when necessary. Avoid medical advice.

      Produce a single cohesive section titled "Final Cohort Definition" with a concise, numbered outline covering:
      1) Index event: domain (condition/drug/procedure/measurement/visit/observation), concept set intent, standard concepts only, include descendants yes/no.
      2) Entry criteria: first-ever vs first-in-window, washout days, minimum prior observation.
      3) Population constraints: age at index, sex, any additional inclusion filters.
      4) Visit/setting restrictions: inpatient/outpatient/ED, if applicable.
      5) Time window for index: date/years allowed for index.
      6) Exclusions: prior conditions/exposures/procedures, pregnancy, etc., if specified.
      7) Cohort exit: end-of-observation or fixed window, and any episode/deduplication rules.
      8) Notes/assumptions: clearly list any assumptions made to remove ambiguity.

      Requirements:
      - Write in precise, implementation-ready language suitable for ATLAS configuration.
      - Do not ask questions. Do not include code or SQL.
      - If a detail is unspecified but important, choose a standard default and mark it under "Assumptions".
    output_schema: { type: string }

steps:
  - kind: conditional
    name: resolve_initial_goal
    condition_expression: "not context.initial_prompt"
    branches:
      true:
        - kind: hitl
          name: get_initial_goal
          message: "What would you like to accomplish?"
          updates_context: true
      false:
        - kind: step
          name: get_initial_goal
          agent: "flujo.builtins.passthrough"
          input: "{{ context.initial_prompt }}"
          updates_context: true

  # Interactive clarification loop (slot-filling)
  - kind: loop
    name: clarification_loop
    loop:
      conversation: true
      history_management:
        strategy: truncate_tokens
        max_tokens: 3000
      ai_turn_source: named_steps
      user_turn_sources: ["hitl"]
      named_steps: ["check_if_more_info_needed"]
      history_template: |
        --- Task Context ---
        Initial goal: {{ steps.get_initial_goal.output }}
        Recent turns:
        {{#each history}}{{ this.role }}: {{ this.content }}
        {{/each}}
        Instruction:
          Ask ONE clarifying question that explicitly references the initial goal {{ steps.get_initial_goal.output }}.
          If goal is clear, output {"action":"finish"}.
      body:
        - kind: step
          name: check_if_more_info_needed
          uses: agents.clarification_agent
          input: |
            --- Conversation So Far ---
            {{#each context.hitl_history}}
            assistant: {{ this.message_to_human }}
            user: {{ this.human_response }}
            {{/each}}

            --- Instruction ---
            Initial goal: {{ steps.get_initial_goal.output }}
            Ask ONE clarifying question referencing the goal and the conversation. If all slots are filled, output {"action":"finish"}.

        - kind: conditional
          name: ask_question_if_needed
          condition_expression: "previous_step.action == 'ask'"
          branches:
            true:
              - kind: hitl
                name: ask_user_for_clarification
                message: "{{ steps.check_if_more_info_needed.output.question }}"
                updates_context: true
            false:
              - kind: step
                name: passthrough
                agent: "flujo.builtins.passthrough"

      exit_expression: |
        (
          steps['check_if_more_info_needed'] and
          steps['check_if_more_info_needed'].action == 'finish'
        )
      max_loops: 6

  - kind: step
    name: synthesize_slots
    uses: "flujo.helpers.slot_synthesis:synthesize_slots"
    updates_context: true

  - kind: step
    name: generate_cohort_definition
    uses: agents.cohort_definer
    updates_context: true
    input: |
      Initial goal: {{ steps.get_initial_goal.output }}

      Clarifications (chronological):
      {{#each context.hitl_history}}
      Q: {{ this.message_to_human }}
      A: {{ this.human_response }}
      {{/each}}

      Synthesized slots:
      {{ context.scratchpad.slots | tojson }}

      Task: Produce the Final Cohort Definition per your system instructions. If any critical detail is missing, choose a standard, conservative default and list it under "Assumptions". Do not ask further questions.

  - kind: step
    name: store_cohort_definition
    uses: "skills.custom_tools:store_as_cohort_definition"
    input: "{{ steps.generate_cohort_definition.output }}"
    updates_context: true

  # Emit plain-text cohort definition as the subpipeline's final output
  - kind: step
    name: emit_for_parent
    agent: "flujo.builtins.passthrough"
    input: "{{ context.scratchpad.cohort_definition }}"

```

## Folder: projects/clarification/.flujo

## Folder: projects/clarification/.flujo/cache

## Folder: projects/clarification/skills

### File: `cohortgen/projects/clarification/skills/custom_tools.py`
<a name="cohortgen-projects-clarification-skills-custom_toolspy"></a>
```python
from __future__ import annotations
from typing import Any, Dict


async def echo_tool(x: str) -> str:
    return x


async def wrap_in_scratchpad(data: Any, *, key: str = "value") -> Dict[str, Any]:
    return {"scratchpad": {key: data}}


async def store_as_cohort_definition(text: Any) -> Dict[str, Any]:
    """Store plain-text cohort definition into scratchpad.cohort_definition."""
    if text is None:
        text = ""
    return {"scratchpad": {"cohort_definition": text}}

```

## Folder: projects/clarification/debug

## Folder: projects/welcome

## Folder: projects/query_builder

### File: `cohortgen/projects/query_builder/README.md`
<a name="cohortgen-projects-query_builder-readmemd"></a>
```markdown
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

```

### File: `cohortgen/projects/query_builder/__init__.py`
<a name="cohortgen-projects-query_builder-__init__py"></a>
```python

```

### File: `cohortgen/projects/query_builder/flujo.toml`
<a name="cohortgen-projects-query_builder-flujotoml"></a>
```toml
# Flujo project configuration template

# Use an in-memory state backend by default for new projects
state_uri = "memory://"

# Load environment variables (API keys, etc.) from this file.
# Copy `.env.example` to `.env`, fill your keys, or change this path.
env_file = ".env"

[settings]
# default_solution_model = "gpt-4o-mini"
# reflection_enabled = true

# Centralized budgets (optional)
[budgets]
# [budgets.default]
# total_cost_usd_limit = 5.0
# total_tokens_limit = 100000

# Architect defaults
[architect]
# Enable the agentic Architect state machine by default for this project
state_machine_default = true
# To disable by default, set to false or remove this section.
# Per-run overrides:
#   - Force agentic: export FLUJO_ARCHITECT_STATE_MACHINE=1
#   - Force minimal: export FLUJO_ARCHITECT_MINIMAL=1

```

### File: `cohortgen/projects/query_builder/pipeline.yaml`
<a name="cohortgen-projects-query_builder-pipelineyaml"></a>
```yaml
version: "0.1"
name: "query_builder_pipeline"

pipeline_config:
  conversation_mode: true

agents:
  sql_generator:
    model: "openai:gpt-5-mini"
    model_settings:
      openai_reasoning_effort: "medium"
    timeout: 120
    max_retries: 1
    system_prompt: |
      You are an expert OMOP CDM (v5.x) SQL developer targeting BigQuery Standard SQL.
      Generate a single, runnable BigQuery SQL query that implements the provided cohort definition using the supplied concept sets.

      Requirements:
      - Use BigQuery Standard SQL only.
      - Qualify all OMOP tables with the provided project.dataset prefix (e.g., `project.dataset.table`).
      - Use the concept sets to filter records by `concept_id`. If `include_descendants` is true and the concept_ancestor table is available, expand to descendants via `concept_ancestor` (standard concepts only unless specified otherwise).
      - Favor standard concepts (standard_concept = 'S') unless the input says otherwise.
      - Avoid multi-statement scripts; produce a single SELECT statement or a common table expression (CTE) block ending in a final SELECT.
      - Keep it syntactically correct for BigQuery and OMOP v5.x fields (e.g., condition_occurrence, person, visit_occurrence, observation_period, drug_exposure, procedure_occurrence, measurement, observation).
      - Do not include any commentary or markdown; output only SQL.
    output_schema: { type: string }

  sql_fixer:
    model: "openai:gpt-5-mini"
    model_settings:
      openai_reasoning_effort: "low"
    timeout: 120
    max_retries: 1
    system_prompt: |
      You fix BigQuery Standard SQL queries. Given the original SQL and a BigQuery dry-run error, return a corrected SQL that resolves the error while preserving logic and the project.dataset prefixes.
      - Do not remove table qualifiers.
      - Only output SQL. No commentary.
    output_schema: { type: string }

steps:
  # Optional: non-interactive inputs via JSON
  - kind: step
    name: parse_initial_payload
    uses: "skills.custom_tools:parse_initial_payload"
    input: "{{ context.initial_prompt }}"
    updates_context: true

  - kind: conditional
    name: resolve_cohort_definition
    condition_expression: "not context.scratchpad.get('cohort_definition')"
    branches:
      true:
        - kind: hitl
          name: get_cohort_definition
          message: "Paste the finalized cohort definition (plain text)."
          updates_context: true
      false:
        - kind: step
          name: get_cohort_definition
          agent: "flujo.builtins.passthrough"
          input: "{{ context.scratchpad.cohort_definition }}"
          updates_context: true

  - kind: conditional
    name: resolve_concept_sets
    condition_expression: "(not context.scratchpad.get('concept_sets')) and (context.scratchpad.get('status') != 'paused')"
    branches:
      true:
        - kind: hitl
          name: get_concept_sets
          message: |
            Paste the concept sets JSON from the previous step (concept_discovery). Example:
            {"concept_sets": [{"name":"Heart failure","concept_ids":[...],"include_descendants":true,"standard_only":true}]}
          updates_context: true
      false:
        - kind: step
          name: get_concept_sets
          agent: "flujo.builtins.passthrough"
          input: "{{ context.scratchpad.concept_sets | tojson }}"
          updates_context: true

  # Fixed dataset per requirement
  - kind: conditional
    name: stop_if_parent_paused
    condition_expression: "context.scratchpad.get('status') == 'paused'"
    branches:
      true:
        - kind: step
          name: noop_query_builder
          agent: "flujo.builtins.passthrough"
          input: "parent_paused"
      false:
        - kind: step
          name: omop_dataset_id
          agent: "flujo.builtins.passthrough"
          input: "{{ env.OMOP_DATASET_ID or 'bigquery-public-data.cms_synthetic_patient_data_omop' }}"

        - kind: step
          name: bq_location
          agent: "flujo.builtins.passthrough"
          input: "{{ env.BIGQUERY_LOCATION or 'US' }}"

        - kind: step
          name: bq_project_id
          agent: "flujo.builtins.passthrough"
          input: "{{ env.BIGQUERY_PROJECT_ID or '' }}"

        - kind: step
          name: normalize_concept_sets
          uses: "skills.custom_tools:ensure_dict"
          input: "{{ steps.get_concept_sets.output }}"
          updates_context: true

        - kind: step
          name: generate_sql
          uses: agents.sql_generator
          input: |
            Cohort definition:
            {{ steps.get_cohort_definition.output }}

            Concept sets JSON:
            {{ steps.normalize_concept_sets.output | tojson }}

            BigQuery OMOP prefix:
            {{ steps.omop_dataset_id.output }}

            Output ONLY SQL.

  - kind: step
    name: store_current_sql_initial
    uses: "skills.custom_tools:store_current_sql"
    input: "{{ steps.generate_sql.output }}"
    updates_context: true

  - kind: loop
    name: repair_sql_loop
    loop:
      ai_turn_source: named_steps
      user_turn_sources: []
      named_steps: ["dry_run", "maybe_fix_sql"]
      body:
        - kind: step
          name: dry_run
          uses: "skills.bq_tools:bq_dry_run"
          input: |
            {{ {
              "sql": context.scratchpad.current_sql,
              "default_dataset": steps.omop_dataset_id.output,
              "project_id": steps.bq_project_id.output,
              "location": steps.bq_location.output
            } | tojson }}
          updates_context: true

        - kind: conditional
          name: maybe_fix_sql
          condition_expression: "not steps['dry_run'].success"
          branches:
            true:
              - kind: step
                name: fix_sql
                uses: agents.sql_fixer
                input: |
                  Original SQL:
                  {{ context.scratchpad.current_sql }}

                  BigQuery error (from dry run):
                  {{ steps.dry_run.output | tojson }}

                  Output ONLY corrected SQL.
              - kind: step
                name: store_current_sql_fixed
                uses: "skills.custom_tools:store_current_sql"
                input: "{{ steps.fix_sql.output }}"
                updates_context: true
            false:
              - kind: step
                name: no_fix_needed
                agent: "flujo.builtins.passthrough"
      exit_expression: "steps['dry_run'].success"
      max_loops: 3

  - kind: step
    name: final_sql
    agent: "flujo.builtins.passthrough"
    input: "{{ context.scratchpad.current_sql }}"
    updates_context: true

  - kind: step
    name: store_final_sql
    uses: "skills.custom_tools:store_final_sql"
    input: "{{ steps.final_sql.output }}"
    updates_context: true

  # Final dry run to capture cost and stats for reporting
  - kind: step
    name: final_dry_run
    uses: "skills.bq_tools:bq_dry_run"
    input: |
      {{ {
        "sql": context.scratchpad.final_sql,
        "default_dataset": steps.omop_dataset_id.output,
        "project_id": steps.bq_project_id.output,
        "location": steps.bq_location.output
      } | tojson }}
    updates_context: true

  - kind: step
    name: store_final_dry_run
    uses: "skills.custom_tools:store_dry_run_result"
    input: "{{ steps.final_dry_run.output }}"
    updates_context: true

```

## Folder: projects/query_builder/skills

### File: `cohortgen/projects/query_builder/skills/__init__.py`
<a name="cohortgen-projects-query_builder-skills-__init__py"></a>
```python

```

### File: `cohortgen/projects/query_builder/skills/bq_tools.py`
<a name="cohortgen-projects-query_builder-skills-bq_toolspy"></a>
```python
from __future__ import annotations

import json
from typing import Any, Dict, Optional

try:
    from google.cloud import bigquery  # type: ignore
    from google.api_core.exceptions import BadRequest  # type: ignore
except Exception:
    bigquery = None  # type: ignore
    BadRequest = Exception  # type: ignore


def _ensure_client(project_id: Optional[str] = None, credentials_path: Optional[str] = None):
    if bigquery is None:
        raise RuntimeError("google-cloud-bigquery is not installed")
    if credentials_path:
        return bigquery.Client.from_service_account_json(credentials_path, project=project_id)
    return bigquery.Client(project=project_id)


def bq_dry_run(payload: str | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload, str):
        try:
            cfg = json.loads(payload)
        except Exception:
            cfg = {"sql": payload}
    else:
        cfg = payload
    sql: str = (cfg.get("sql") or "").strip()
    if not sql:
        return {"success": False, "errors": ["Empty SQL"], "total_bytes_processed": 0}
    project_id: Optional[str] = cfg.get("project_id")
    credentials_path: Optional[str] = cfg.get("credentials_path")
    default_dataset: Optional[str] = cfg.get("default_dataset")
    location: Optional[str] = cfg.get("location")
    client = _ensure_client(project_id=project_id, credentials_path=credentials_path)
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    if default_dataset:
        job_config.default_dataset = default_dataset
    try:
        job = client.query(sql, job_config=job_config, location=location)
        stats = getattr(job, "_properties", {}).get("statistics", {})
        total = getattr(job, "total_bytes_processed", 0) or stats.get("totalBytesProcessed", 0)
        try:
            total_int = int(total)
        except Exception:
            try:
                total_int = int(float(total))
            except Exception:
                total_int = 0
        # Estimate cost at ~$6 per TB
        tb = float(total_int) / float(1024 ** 4)
        est_cost = tb * 6.0
        return {
            "success": True,
            "errors": [],
            "total_bytes_processed": total_int,
            "estimated_cost_usd": round(est_cost, 6),
            "summary": f"Query is valid. Estimated to process {total_int / (1024**3):.2f} GB, costing ~${est_cost:.4f}.",
            "job_id": getattr(job, "job_id", ""),
            "statistics": stats,
        }
    except BadRequest as e:  # type: ignore
        errors = []
        try:
            errors = list(getattr(e, "errors", []) or [])
        except Exception:
            pass
        message = str(e)
        if not errors and message:
            errors = [message]
        return {"success": False, "errors": errors, "total_bytes_processed": 0}
    except Exception as e:
        return {"success": False, "errors": [str(e)], "total_bytes_processed": 0}

```

### File: `cohortgen/projects/query_builder/skills/custom_tools.py`
<a name="cohortgen-projects-query_builder-skills-custom_toolspy"></a>
```python
from __future__ import annotations

import json
from typing import Any, Dict


async def echo_tool(x: str) -> str:
    return x


async def ensure_dict(data: Dict[str, Any] | str | object) -> Dict[str, Any]:
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
            try:
                loaded = json.loads(data)
                return loaded if isinstance(loaded, dict) else {"data": loaded}
            except Exception:
                return {"data": data}
    try:
        return json.loads(json.dumps(data, default=str))
    except Exception:
        return {"data": str(data)}


async def wrap_in_scratchpad(data: Any, *, key: str = "value") -> Dict[str, Any]:
    return {"scratchpad": {key: data}}


async def parse_initial_payload(initial: Any) -> Dict[str, Any]:
    if initial is None:
        return {"scratchpad": {}}
    if isinstance(initial, str):
        try:
            data = json.loads(initial)
        except Exception:
            data = {}
    elif isinstance(initial, dict):
        data = initial
    else:
        try:
            data = json.loads(json.dumps(initial, default=str))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
    out: Dict[str, Any] = {}
    cd = data.get("cohort_definition")
    if isinstance(cd, str) and cd.strip():
        out["cohort_definition"] = cd
    cs = data.get("concept_sets")
    if isinstance(cs, (dict, list)):
        out["concept_sets"] = cs
    return {"scratchpad": out}


async def store_final_sql(sql: Any) -> Dict[str, Any]:
    if sql is None:
        sql = ""
    return {"scratchpad": {"final_sql": sql}}


async def store_current_sql(sql: Any) -> Dict[str, Any]:
    if sql is None:
        sql = ""
    return {"scratchpad": {"current_sql": sql}}


async def store_dry_run_result(result: Any) -> Dict[str, Any]:
    return {"scratchpad": {"dry_run_result": result or {}}}

```

## Folder: projects/query_builder/debug

## Folder: projects/concept_discovery

### File: `cohortgen/projects/concept_discovery/README.md`
<a name="cohortgen-projects-concept_discovery-readmemd"></a>
```markdown
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

```

### File: `cohortgen/projects/concept_discovery/__init__.py`
<a name="cohortgen-projects-concept_discovery-__init__py"></a>
```python

```

### File: `cohortgen/projects/concept_discovery/flujo.toml`
<a name="cohortgen-projects-concept_discovery-flujotoml"></a>
```toml
# Flujo project configuration template

# Use an in-memory state backend by default for new projects
state_uri = "memory://"

# Load environment variables (API keys, etc.) from this file.
# Copy `.env.example` to `.env`, fill your keys, or change this path.
env_file = "../../.env"

[settings]
# default_solution_model = "gpt-4o-mini"
# reflection_enabled = true

# Centralized budgets (optional)
[budgets]
# [budgets.default]
# total_cost_usd_limit = 5.0
# total_tokens_limit = 100000

# Architect defaults
[architect]
# Enable the agentic Architect state machine by default for this project
state_machine_default = true
# To disable by default, set to false or remove this section.
# Per-run overrides:
#   - Force agentic: export FLUJO_ARCHITECT_STATE_MACHINE=1
#   - Force minimal: export FLUJO_ARCHITECT_MINIMAL=1

# Explicit cost configuration to silence pricing warnings and track spend accurately
[cost]
  strict = false
  [cost.providers]
    [cost.providers.openai]
      # Set explicit pricing for models used in this project
      [cost.providers.openai.gpt-4o]
        prompt_tokens_per_1k = 0.005   # USD per 1K prompt tokens
        completion_tokens_per_1k = 0.015 # USD per 1K completion tokens
      # Optional: include minis if you switch
      [cost.providers.openai.gpt-4o-mini]
        prompt_tokens_per_1k = 0.00015
        completion_tokens_per_1k = 0.0006
      # Explicit pricing for GPT-5 family used in this pipeline
      # Note: Values here are placeholders for manual testing only.
      #       Update with accurate prices for production tracking.
      [cost.providers.openai.gpt-5]
        prompt_tokens_per_1k = 0.01
        completion_tokens_per_1k = 0.03
      [cost.providers.openai.gpt-5-mini]
        prompt_tokens_per_1k = 0.002
        completion_tokens_per_1k = 0.006

```

### File: `cohortgen/projects/concept_discovery/pipeline.yaml`
<a name="cohortgen-projects-concept_discovery-pipelineyaml"></a>
```yaml
version: "0.1"
name: "concept_discovery_pipeline"

pipeline_config:
  conversation_mode: true

agents:
  concept_decomposer:
    model: "openai:gpt-5-mini"
    model_settings:
      openai_reasoning_effort: "medium"
    timeout: 120
    max_retries: 1
    system_prompt: |
      You are an expert OMOP/ATLAS cohort designer. Task: Read the cohort definition and produce a structured plan of concept sets to build in ATHENA.
      Strict requirements:
      - No placeholders. Do NOT emit generic tokens like <CONDITION_NAME>.
      - Derive concrete query terms directly from the user's cohort definition.
      - Prefer standard concepts only ('S') unless the definition requires non‑standard.
      - Suggest domain/vocabulary restrictions when clear (e.g., SNOMED for conditions, RxNorm for drugs).
      - Include whether to include descendants (true by default).
      Output ONLY a valid JSON object.
    output_schema:
      type: object
      properties:
        concept_sets:
          type: array
          items:
            type: object
            properties:
              name: { type: string }
              intent: { type: string }
              domain: { type: string }
              vocabulary: { type: array, items: { type: string } }
              include_descendants: { type: boolean, default: true }
              standard_only: { type: boolean, default: true }
              queries: { type: array, items: { type: string } }
            required: [name, queries]

  concept_explorer_agent:
    model: "openai:gpt-5-mini"
    model_settings:
      openai_reasoning_effort: "medium"
    timeout: 180
    max_retries: 1
    system_prompt: |
      You are an expert OMOP concept explorer. Your goal is to build a final, high-quality list of STANDARD OMOP concepts.
      You are inside an exploration loop. On each turn, you will be given the current state of the concept sets and a history of your previous actions.
      Your task is to decide on the SINGLE BEST next action to take to improve the concept sets.
      
      Available Tools:
      - `athena_search`: To find new initial candidates.
      - `athena_details`: To get more information on specific concepts.
      - `athena_relationships`: To explore how concepts are connected (e.g., 'Maps to', 'Is a'). This is your primary tool for finding standard concepts from non-standard ones.
      
      Strategy:
      1. Analyze the `current_sets`. Identify gaps, non-standard concepts, or areas needing more detail.
      2. Consult your `exploration_history` to avoid repeating failed actions.
      3. Decide on ONE action: either call ONE tool to get more information, or decide you are finished.
      4. If you have enough high-quality, standard concepts and further exploration is unlikely to yield better results, call `finish`.

      Output ONLY JSON with the schema: {"action": "tool" | "finish", "tool_name": str?, "tool_input": object?, "final_sets": object?}.
      - If action is "tool", provide `tool_name` and `tool_input`.
      - If action is "finish", provide the `final_sets`.
    tools:
      - "skills.athena_tools:athena_search"
      - "skills.athena_tools:athena_details"
      - "skills.athena_tools:athena_relationships"
    output_schema:
      type: object
      properties:
        action: { type: string, enum: [tool, finish] }
        tool_name: { type: string }
        tool_input: { type: object }
        final_sets: { type: object }
      required: [action]

steps:
  - name: parse_initial_payload
    uses: "skills.custom_tools:parse_initial_payload"
    input: "{{ context.initial_prompt }}"
    updates_context: true

  - name: decompose_concept_sets
    uses: agents.concept_decomposer
    input: "{{ context.scratchpad.cohort_definition }}"
    updates_context: true

  - name: search_initial_candidates
    uses: "skills.athena_tools:athena_search_for_concept_plan"
    input: "{{ previous_step.output | tojson }}"
    updates_context: true

  - kind: loop
    name: exploration_loop
    loop:
      body:
        - name: decide_next_action
          uses: agents.concept_explorer_agent
          input: |
            Cohort Definition: {{ context.scratchpad.cohort_definition }}
            Current Concept Sets: {{ context.scratchpad.concept_sets | tojson }}
            Exploration History: {{ context.scratchpad.exploration_history | tojson }}
            Refinement Feedback: {{ context.scratchpad.refinement_feedback or '' }}
          updates_context: true
        
        - kind: conditional
          name: execute_action
          condition_expression: "previous_step.action == 'tool'"
          branches:
            true:
              - name: execute_tool
                uses: "skills.custom_tools:execute_athena_tool"
                input: "{{ steps.decide_next_action.output }}"
                updates_context: true
      
      exit_expression: "steps['decide_next_action'].action == 'finish'"
      max_loops: 15

  - name: store_concept_sets
    uses: "skills.custom_tools:store_as_concept_sets"
    input: "{{ steps.decide_next_action.output.final_sets }}"
    updates_context: true

  - name: emit_for_parent
    agent: "flujo.builtins.passthrough"
    input: "{{ context.scratchpad.concept_sets | tojson }}"

```

## Folder: projects/concept_discovery/.flujo

## Folder: projects/concept_discovery/.flujo/cache

## Folder: projects/concept_discovery/skills

### File: `cohortgen/projects/concept_discovery/skills/__init__.py`
<a name="cohortgen-projects-concept_discovery-skills-__init__py"></a>
```python

```

### File: `cohortgen/projects/concept_discovery/skills/athena_tools.py`
<a name="cohortgen-projects-concept_discovery-skills-athena_toolspy"></a>
```python
from __future__ import annotations

import json
from typing import Any, Dict, List, Union, Iterable
import time

try:
    from athena_client import Athena  # type: ignore
except Exception:
    Athena = None

# Allow-listed relationship names to reduce noise for the agent
RELATIONSHIP_ALLOW_LIST = {
    "Maps to",
    "Is a",
    "Has ingredient",
    "RxNorm has dose form",
    "Has tradename",
    "Constitutes",
    "Contains",
    "Form of",
    "Has mechanism of action",
    "Has physiologic effect",
    "Has clinical finding",
    "May treat",
    "May prevent",
    "Contraindication of",
    "Has finding site",
    "Causative agent of",
    "Has pathology",
    "Associated with",
    "Occurs in",
    "Variant of",
    "Subtype of",
    "Related to",
    "Same as",
    "Broader than",
}


def _normalize_domain(domain: str | None) -> str | None:
    if not domain:
        return None
    d = domain.strip().lower()
    mapping = {
        "condition": "Condition",
        "drug": "Drug",
        "procedure": "Procedure",
        "measurement": "Measurement",
        "observation": "Observation",
        "visit": "Visit",
        "device": "Device",
        "specimen": "Specimen",
        "note": "Note",
    }
    return mapping.get(d, domain)


def _safe_athena() -> Any:
    if Athena is None:
        raise RuntimeError("athena-client is not installed. pip install athena-client")
    return Athena()


def _retry(call, *args, attempts: int = 3, delay: float = 0.5, backoff: float = 2.0, **kwargs):
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return call(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if i == attempts - 1:
                break
            try:
                time.sleep(delay)
            except Exception:
                pass
            delay *= backoff
    if last_exc:
        raise last_exc
    raise RuntimeError("retry failed without exception")


def athena_search_for_concept_plan(plan: Union[str, Dict[str, Any]], top_k: int = 10) -> Dict[str, Any]:
    if isinstance(plan, str):
        try:
            plan_obj = json.loads(plan)
        except json.JSONDecodeError:
            start = plan.find("{")
            end = plan.rfind("}")
            if start != -1 and end != -1 and end > start:
                plan_obj = json.loads(plan[start : end + 1])
            else:
                raise
    else:
        plan_obj = plan
    concept_sets = plan_obj.get("concept_sets", []) if isinstance(plan_obj, dict) else []

    client = _safe_athena()
    out_sets: List[Dict[str, Any]] = []
    for item in concept_sets:
        name = item.get("name") or "unnamed_set"
        queries: List[str] = list(item.get("queries") or [])
        domain = _normalize_domain(item.get("domain"))
        vocab_prefs: List[str] = list(item.get("vocabulary") or [])
        include_desc = bool(item.get("include_descendants", True))
        standard_only = bool(item.get("standard_only", True))

        seen: set[int] = set()
        candidates: List[Dict[str, Any]] = []
        for q in queries:
            q = (q or "").strip()
            if not q:
                continue
            try:
                results = _retry(client.search, q)
            except Exception:
                continue
            try:
                raw = results.top(max(top_k * 3, 10))
                raw_list = raw if isinstance(raw, list) else getattr(raw, "all", lambda: [])()
            except Exception:
                try:
                    raw_list = _retry(results.all)
                except Exception:
                    raw_list = []
            # Use robust filter to handle field variations
            filtered = _filter_candidates(
                raw_list, domain=domain, vocabulary=vocab_prefs or None, standard_only=standard_only
            )
            for concept in filtered:
                cid = concept["concept_id"]
                if cid in seen:
                    continue
                seen.add(cid)
                candidates.append(concept)
                if len(candidates) >= top_k:
                    break
            if len(candidates) >= top_k:
                break
        out_sets.append(
            {
                "name": name,
                "candidates": candidates[:top_k],
                "include_descendants": include_desc,
                "standard_only": standard_only,
                "notes": item.get("intent") or "",
            }
        )
    return {"concept_sets": out_sets}


# === Minimal tool surface for the concept_refiner agent ===

def _as_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    try:
        import json

        if isinstance(obj, str):
            s = obj.strip()
            if s.startswith("{") and s.endswith("}"):
                return json.loads(s)
            return {"query": s}
        # Fallback to JSON round-trip
        data = json.loads(json.dumps(obj, default=str))
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {"data": str(obj)}


def _get_field(d: Dict[str, Any], *names: str) -> Any:
    for n in names:
        if n in d:
            return d.get(n)
    # Try case variants
    lowered = {k.lower(): v for k, v in d.items()}
    for n in names:
        v = lowered.get(n.lower())
        if v is not None:
            return v
    return None


def _to_plain_dict(obj: Any) -> Dict[str, Any]:
    """Best-effort conversion of client objects (e.g., Pydantic models) to plain dicts.

    Handles pydantic v1 (`.dict()` / `.json()`), pydantic v2 (`.model_dump()` / `.model_dump_json()`),
    and falls back to `__dict__` or stringification as a last resort.
    """
    if isinstance(obj, dict):
        return obj
    # Pydantic v2
    fn = getattr(obj, "model_dump", None)
    if callable(fn):
        try:
            data = fn()
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    # Pydantic v1
    fn = getattr(obj, "dict", None)
    if callable(fn):
        try:
            data = fn()
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    # Try JSON methods
    try:
        import json as _json

        fn = getattr(obj, "model_dump_json", None)
        if callable(fn):
            try:
                return _json.loads(fn())
            except Exception:
                pass
        fn = getattr(obj, "json", None)
        if callable(fn):
            try:
                return _json.loads(fn())
            except Exception:
                pass
    except Exception:
        pass
    # Fallback to __dict__
    d = getattr(obj, "__dict__", None)
    if isinstance(d, dict):
        return {k: v for k, v in d.items() if not k.startswith("_")}
    return {}


def _as_standard_flag(x: Any) -> str | None:
    # Accept 'S'/'C'/None or booleans
    if x is None:
        return None
    if isinstance(x, str):
        s = x.strip().upper()
        if s in ("S", "C"):
            return s
        # Some APIs might return 'Standard'/'Classification'
        if s.startswith("STANDARD"):
            return "S"
        if s.startswith("CLASS"):
            return "C"
        return None
    if isinstance(x, bool):
        return "S" if x else None
    # Handle Enum-like objects from clients (e.g., athena-client ConceptType)
    try:
        val = getattr(x, "value", x)
        s = str(val).strip().upper()
        if s in ("S", "C"):
            return s
        if "STANDARD" in s and "NON" not in s:
            return "S"
        if "CLASS" in s:
            return "C"
    except Exception:
        pass
    return None


def _filter_candidates(
    items: Iterable[Dict[str, Any]],
    *,
    domain: str | None,
    vocabulary: List[str] | None,
    standard_only: bool,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for raw in items:
        # Normalize possible Pydantic models or typed objects to dicts first
        c = _to_plain_dict(raw)
        if not c:
            continue
        # Pull fields with flexible naming
        cid_raw = _get_field(c, "concept_id", "conceptId", "id")
        try:
            cid = int(cid_raw)
        except Exception:
            continue
        sc_flag = _as_standard_flag(_get_field(c, "standard_concept", "standardConcept", "is_standard", "isStandard"))
        if standard_only and sc_flag not in ("S", "C"):
            continue
        c_domain = _get_field(c, "domain_id", "domainId", "domain")
        if domain and c_domain != domain:
            continue
        if vocabulary:
            c_vocab = _get_field(c, "vocabulary_id", "vocabularyId", "vocabulary")
            if c_vocab not in vocabulary:
                continue
        out.append(
            {
                "concept_id": cid,
                "concept_name": _get_field(c, "concept_name", "conceptName", "name"),
                "domain_id": c_domain,
                "vocabulary_id": _get_field(c, "vocabulary_id", "vocabularyId", "vocabulary"),
                "standard_concept": sc_flag,
                "concept_code": _get_field(c, "concept_code", "conceptCode", "code"),
            }
        )
    return out


def athena_search(payload: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Search Athena for a query with optional filters.

    Accepts:
      - String: treated as the query.
      - Dict: { query, top_k, domain, vocabulary:[], standard_only:bool }
    Returns: { success, query, candidates:[{concept_id,...}], note? }
    """
    cfg = _as_dict(payload)
    q: str = (cfg.get("query") or cfg.get("q") or cfg.get("term") or "").strip()
    if not q and isinstance(payload, str):
        q = payload.strip()
    top_k: int = int(cfg.get("top_k") or 20)
    domain = _normalize_domain(cfg.get("domain"))
    vocabulary = cfg.get("vocabulary") or cfg.get("vocab")
    if isinstance(vocabulary, str):
        vocabulary = [vocabulary]
    if vocabulary is not None:
        vocabulary = [str(v) for v in vocabulary]
    standard_only = bool(cfg.get("standard_only", True))

    if not q:
        return {"success": False, "query": q, "candidates": [], "error": "empty_query"}
    try:
        client = _safe_athena()
        results = _retry(client.search, q)
        try:
            raw: List[Dict[str, Any]] = results.top(max(top_k * 3, top_k))
        except Exception:
            try:
                raw = _retry(results.all)
            except Exception:
                raw = []
        candidates = _filter_candidates(
            raw, domain=domain, vocabulary=vocabulary, standard_only=standard_only
        )
        return {
            "success": True,
            "query": q,
            "candidates": candidates[:top_k],
            "filters": {
                "domain": domain,
                "vocabulary": vocabulary,
                "standard_only": standard_only,
            },
        }
    except Exception as e:
        return {"success": False, "query": q, "candidates": [], "error": str(e)}


def athena_details(payload: Union[int, List[int], Dict[str, Any], str]) -> Dict[str, Any]:
    """Fetch detailed metadata for one or more concept IDs.
    Accepts: int | [int] | { concept_id(s) } | JSON string.
    Returns: { success, concepts: [{...}] }
    """
    cfg = _as_dict(payload)
    ids: List[int] = []
    if isinstance(payload, int):
        ids = [payload]
    elif isinstance(payload, list):
        ids = [int(x) for x in payload]
    else:
        for key in ("concept_id", "concept_ids", "ids"):
            v = cfg.get(key)
            if v is None:
                continue
            if isinstance(v, list):
                ids = [int(x) for x in v]
            else:
                try:
                    ids = [int(v)]
                except Exception:
                    pass
            if ids:
                break
    if not ids:
        return {"success": False, "concepts": [], "error": "no_ids"}
    try:
        client = _safe_athena()
        out: List[Dict[str, Any]] = []
        for cid in ids:
            try:
                fn = getattr(client, "details", None) or getattr(client, "concept", None)
                data = _retry(fn, cid) if fn else {"concept_id": cid}
            except Exception:
                data = {"concept_id": cid}
            out.append(data)
        return {"success": True, "concepts": out}
    except Exception as e:
        return {"success": False, "concepts": [], "error": str(e)}


def athena_relationships(payload: Union[int, Dict[str, Any], str]) -> Dict[str, Any]:
    """Fetch relationships for a concept (e.g., 'Maps to').
    Returns: { success, concept_id, relationships:[{relationship_id, concept_id_2, ...}], maps_to:[int] }
    """
    cfg = _as_dict(payload)
    try:
        cid = int(cfg.get("concept_id") or cfg.get("id") or payload)  # type: ignore[arg-type]
    except Exception:
        return {"success": False, "relationships": [], "error": "invalid_id"}
    try:
        client = _safe_athena()
        fn = getattr(client, "relationships", None)
        rel_obj = None
        if fn:
            try:
                rel_obj = _retry(fn, cid)
            except Exception:
                rel_obj = None

        # Normalize and extract with allow-list filtering; also compute 'Maps to' IDs
        def _collect(obj: Any) -> tuple[list[dict[str, Any]], list[int]]:
            rels: List[Dict[str, Any]] = []
            maps_to: List[int] = []
            d = _to_plain_dict(obj) if obj is not None else {}
            groups = d.get("items") or d.get("relationships") or []
            if isinstance(groups, dict):
                groups = [groups]
            for g in groups:
                gd = _to_plain_dict(g)
                items = gd.get("relationships") or gd.get("items") or []
                if isinstance(items, dict):
                    items = [items]
                for r in items:
                    rd = _to_plain_dict(r)
                    rel_name = _get_field(rd, "relationship_id", "relationshipId", "relationshipName")
                    rel_name_str = (str(rel_name) if rel_name is not None else "").strip()
                    if rel_name_str in RELATIONSHIP_ALLOW_LIST:
                        rels.append(rd)
                    # also collect maps_to ids
                    if rel_name_str.lower() == "maps to":
                        cid2 = _get_field(rd, "concept_id_2", "conceptId2", "targetConceptId", "conceptId")
                        try:
                            maps_to.append(int(cid2))
                        except Exception:
                            pass
            return rels, maps_to

        rels_norm, maps_to_ids = _collect(rel_obj)
        return {"success": True, "concept_id": cid, "relationships": rels_norm, "maps_to": maps_to_ids}
    except Exception as e:
        return {"success": False, "relationships": [], "error": str(e)}


def athena_summary(payload: Union[int, Dict[str, Any], str]) -> Dict[str, Any]:
    """Fetch a summary for a concept if the client supports it.
    Returns: { success, concept_id, summary: {...}? }
    """
    cfg = _as_dict(payload)
    try:
        cid = int(cfg.get("concept_id") or cfg.get("id") or payload)  # type: ignore[arg-type]
    except Exception:
        return {"success": False, "error": "invalid_id"}
    try:
        client = _safe_athena()
        fn = getattr(client, "summary", None)
        if not fn:
            return {"success": True, "concept_id": cid, "summary": None}
        try:
            data = _retry(fn, cid)
        except Exception:
            data = None
        return {"success": True, "concept_id": cid, "summary": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def athena_graph(payload: Union[int, Dict[str, Any], str]) -> Dict[str, Any]:
    """Fetch a small relationship graph if supported.
    Returns: { success, concept_id, graph: {...}? }
    """
    cfg = _as_dict(payload)
    try:
        cid = int(cfg.get("concept_id") or cfg.get("id") or payload)  # type: ignore[arg-type]
    except Exception:
        return {"success": False, "error": "invalid_id"}
    try:
        client = _safe_athena()
        fn = getattr(client, "graph", None)
        if not fn:
            return {"success": True, "concept_id": cid, "graph": None}
        try:
            # Best-effort: depth or options may vary across clients
            data = _retry(fn, cid)
        except Exception:
            data = None
        return {"success": True, "concept_id": cid, "graph": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def athena_expand_candidates(search_results: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Expand Athena search candidates by following non-standard/"C" to 'Maps to' standard concepts.

    Input shape: { concept_sets: [ { name, candidates: [{...}], include_descendants, standard_only, ... } ] }
    Output shape: same as input, but 'candidates' per set is augmented with mapped standard concepts (deduped).
    """
    data = _as_dict(search_results)
    concept_sets = data.get("concept_sets") or []
    if not isinstance(concept_sets, list):
        return {"concept_sets": []}
    client = None
    try:
        client = _safe_athena()
    except Exception:
        client = None

    out_sets: List[Dict[str, Any]] = []
    for cs in concept_sets:
        name = cs.get("name") or "unnamed"
        raw_candidates: List[Dict[str, Any]] = list(cs.get("candidates") or [])
        include_desc = bool(cs.get("include_descendants", True))
        standard_only = bool(cs.get("standard_only", True))

        seen_ids: set[int] = set()
        expanded: List[Dict[str, Any]] = []

        # Helper to add a concept dict safely
        def add_concept(c: Dict[str, Any]) -> None:
            try:
                cid = int(c.get("concept_id"))
            except Exception:
                return
            if cid in seen_ids:
                return
            seen_ids.add(cid)
            expanded.append(
                {
                    "concept_id": cid,
                    "concept_name": c.get("concept_name"),
                    "domain_id": c.get("domain_id"),
                    "vocabulary_id": c.get("vocabulary_id"),
                    "standard_concept": c.get("standard_concept"),
                    "concept_code": c.get("concept_code"),
                }
            )

        # First, keep original standard concepts
        for c in raw_candidates:
            if (c.get("standard_concept") == "S") or not standard_only:
                add_concept(c)

        # For non-standard or classification candidates, try to fetch 'Maps to'
        for c in raw_candidates:
            sc = c.get("standard_concept")
            if sc == "S":
                continue
            try:
                cid = int(c.get("concept_id"))
            except Exception:
                continue
            # Follow relationships if client available
            maps_to_ids: List[int] = []
            if client is not None:
                try:
                    fn = getattr(client, "relationships", None)
                    rel_obj = _retry(fn, cid) if fn else None
                except Exception:
                    rel_obj = None
                # Extract 'Maps to' targets from possible pydantic structure
                d = _to_plain_dict(rel_obj) if rel_obj is not None else {}
                groups = d.get("items") or d.get("relationships") or []
                if isinstance(groups, dict):
                    groups = [groups]
                for g in groups:
                    gd = _to_plain_dict(g)
                    items = gd.get("relationships") or gd.get("items") or []
                    if isinstance(items, dict):
                        items = [items]
                    for r in items:
                        rd = _to_plain_dict(r)
                        rel_id = (
                            _get_field(rd, "relationship_id", "relationshipId", "relationshipName")
                            or ""
                        ).strip().lower()
                        if rel_id == "maps to":
                            cid2 = _get_field(rd, "concept_id_2", "conceptId2", "targetConceptId", "conceptId")
                            try:
                                maps_to_ids.append(int(cid2))
                            except Exception:
                                pass
                # Fetch details for mapped ids and add standard ones
                if maps_to_ids:
                    try:
                        df = getattr(client, "details", None) or getattr(client, "concept", None)
                        for mid in maps_to_ids:
                            try:
                                det_raw = _retry(df, mid) if df else {"concept_id": mid}
                            except Exception:
                                det_raw = {"concept_id": mid}
                            det = _to_plain_dict(det_raw)
                            sc = _as_standard_flag(
                                _get_field(det, "standard_concept", "standardConcept", "is_standard", "isStandard")
                            )
                            if sc == "S":
                                add_concept(
                                    {
                                        "concept_id": det.get("concept_id")
                                        or det.get("conceptId")
                                        or det.get("id"),
                                        "concept_name": det.get("concept_name")
                                        or det.get("conceptName")
                                        or det.get("name"),
                                        "domain_id": det.get("domain_id")
                                        or det.get("domainId")
                                        or det.get("domain"),
                                        "vocabulary_id": det.get("vocabulary_id")
                                        or det.get("vocabularyId")
                                        or det.get("vocabulary"),
                                        "standard_concept": "S",
                                        "concept_code": det.get("concept_code")
                                        or det.get("conceptCode")
                                        or det.get("code"),
                                    }
                                )
                    except Exception:
                        pass

        out_sets.append(
            {
                "name": name,
                "candidates": expanded if expanded else raw_candidates,
                "include_descendants": include_desc,
                "standard_only": standard_only,
            }
        )

    return {"concept_sets": out_sets}

```

### File: `cohortgen/projects/concept_discovery/skills/custom_tools.py`
<a name="cohortgen-projects-concept_discovery-skills-custom_toolspy"></a>
```python
from __future__ import annotations

import json
from typing import Any, Dict, List
try:
    from flujo.domain.models import PipelineContext  # type: ignore
except Exception:
    class PipelineContext:  # type: ignore
        pass


async def echo_tool(x: str) -> str:
    return x


async def ensure_concept_plan_dict(plan: Dict[str, Any] | str | object) -> Dict[str, Any]:
    if plan is None:
        return {}
    if isinstance(plan, dict):
        return plan
    try:
        from pydantic import BaseModel as PydanticBaseModel  # type: ignore
        if isinstance(plan, PydanticBaseModel):  # type: ignore[isinstance]
            try:
                return plan.model_dump()  # type: ignore[attr-defined]
            except Exception:
                return json.loads(plan.model_dump_json())  # type: ignore[attr-defined]
    except Exception:
        pass
    if isinstance(plan, str):
        try:
            loaded = json.loads(plan)
            if isinstance(loaded, dict):
                return loaded
            return {"data": loaded}
        except Exception:
            return {"data": plan}
    try:
        return json.loads(json.dumps(plan, default=str))
    except Exception:
        return {"data": str(plan)}


async def ensure_dict(data: Dict[str, Any] | str | object) -> Dict[str, Any]:
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            loaded = json.loads(data)
            return loaded if isinstance(loaded, dict) else {"data": loaded}
        except Exception:
            return {"data": data}
    try:
        return json.loads(json.dumps(data, default=str))
    except Exception:
        return {"data": str(data)}


async def wrap_in_scratchpad(data: Any, *, key: str = "value") -> Dict[str, Any]:
    return {"scratchpad": {key: data}}


async def parse_initial_payload(initial: Any) -> Dict[str, Any]:
    if initial is None:
        return {"scratchpad": {"exploration_history": []}}
    text: str | None = None
    if isinstance(initial, str):
        s = initial.strip()
        # Guard against status/control strings accidentally passed as the definition
        lowered = s.lower()
        status_markers = [
            "definition ready",
            "concepts ready",
            "sql validated",
            "sub-pipeline",
            "parent_paused",
        ]
        control_tokens = {"ok", "continue", "no changes", "no_changes"}
        if s.startswith("✅") or any(m in lowered for m in status_markers) or lowered in control_tokens:
            s = ""
        if s.startswith("{") and s.endswith("}"):
            try:
                data = json.loads(s)
                if isinstance(data, dict):
                    cd = data.get("cohort_definition")
                    if isinstance(cd, str) and cd.strip():
                        text = cd.strip()
                    else:
                        # Fallback: accept generic {"value": "..."} wrapper
                        val = data.get("value")
                        if isinstance(val, str) and val.strip():
                            text = val.strip()
            except Exception:
                text = s
        else:
            text = s
    elif isinstance(initial, dict):
        cd = initial.get("cohort_definition")
        if isinstance(cd, str) and cd.strip():
            text = cd.strip()
        else:
            val = initial.get("value")
            if isinstance(val, str) and val.strip():
                text = val.strip()
    else:
        try:
            data = json.loads(json.dumps(initial, default=str))
            if isinstance(data, dict):
                cd = data.get("cohort_definition")
                if isinstance(cd, str) and cd.strip():
                    text = cd.strip()
                else:
                    val = data.get("value")
                    if isinstance(val, str) and val.strip():
                        text = val.strip()
        except Exception:
            text = None
    sp: Dict[str, Any] = {"exploration_history": []}
    if text:
        sp["cohort_definition"] = text
    # Also capture refinement feedback when included in the initial payload
    try:
        init_dict = initial if isinstance(initial, dict) else json.loads(initial) if isinstance(initial, str) and initial.strip().startswith("{") else {}
    except Exception:
        init_dict = {}
    fb = init_dict.get("refinement_feedback") if isinstance(init_dict, dict) else None
    if isinstance(fb, str) and fb.strip():
        sp["refinement_feedback"] = fb.strip()
    return {"scratchpad": sp}


async def execute_athena_tool(payload: Dict[str, Any], *, context: PipelineContext) -> Dict[str, Any]:
    """Execute a chosen Athena tool and log to exploration_history.

    Expects payload like {"tool_name": str, "tool_input": {...}}
    """
    from . import athena_tools  # local import

    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    result: Dict[str, Any]
    if not tool_name or not hasattr(athena_tools, tool_name):
        result = {"success": False, "error": f"Tool '{tool_name}' not found."}
    else:
        try:
            func = getattr(athena_tools, tool_name)
            result = func(tool_input)
        except Exception as e:
            result = {"success": False, "error": str(e)}

    sp = getattr(context, "scratchpad", {})
    hist: List[Dict[str, Any]] = []
    try:
        hist = list(sp.get("exploration_history") or [])  # type: ignore[arg-type]
    except Exception:
        hist = []
    hist.append({"action": {"tool_name": tool_name, "tool_input": tool_input}, "result": result})
    return {"scratchpad": {"exploration_history": hist}}


async def store_as_concept_sets(data: Dict[str, Any] | str | object) -> Dict[str, Any]:
    """Store concept sets into scratchpad.concept_sets.

    Accepts a dict or JSON string from a previous summarizer/normalizer step.
    """
    parsed: Dict[str, Any]
    if data is None:
        parsed = {"concept_sets": []}
    elif isinstance(data, dict):
        parsed = data
    elif isinstance(data, str):
        try:
            loaded = json.loads(data)
            parsed = loaded if isinstance(loaded, dict) else {"concept_sets": []}
        except Exception:
            parsed = {"concept_sets": []}
    else:
        try:
            parsed = json.loads(json.dumps(data, default=str))
            if not isinstance(parsed, dict):
                parsed = {"concept_sets": []}
        except Exception:
            parsed = {"concept_sets": []}
    return {"scratchpad": {"concept_sets": parsed}}


async def summarize_candidate_counts(data: Dict[str, Any] | str | object) -> str:
    """Summarize candidate counts per concept set, flagging empty sets.

    Accepts the output of athena_search_for_concept_plan / athena_expand_candidates /
    smart expansion: {"concept_sets": [{"name":..., "candidates":[{...}], ...}]}
    Returns a human-readable string.
    """
    # Normalize input to dict
    if isinstance(data, dict):
        payload = data
    else:
        try:
            if isinstance(data, str):
                s = data.strip()
                if s.startswith("{") and s.endswith("}"):
                    payload = json.loads(s)
                else:
                    payload = {"data": s}
            else:
                payload = json.loads(json.dumps(data, default=str))
                if not isinstance(payload, dict):
                    payload = {"data": str(data)}
        except Exception:
            payload = {"data": str(data)}

    sets = payload.get("concept_sets") if isinstance(payload, dict) else None
    if not isinstance(sets, list):
        return "No concept sets available for summary."

    lines: list[str] = ["Concept candidate summary:"]
    zeros: int = 0
    for cs in sets:
        name = cs.get("name") or "unnamed"
        cands = cs.get("candidates") or []
        if not isinstance(cands, list):
            cands = []
        total = len(cands)
        s_cnt = 0
        c_cnt = 0
        ns_cnt = 0
        for c in cands:
            sc = c.get("standard_concept")
            if sc == "S":
                s_cnt += 1
            elif sc == "C":
                c_cnt += 1
            else:
                ns_cnt += 1
        flag = " ⚠️ EMPTY" if total == 0 else ""
        if total == 0:
            zeros += 1
        lines.append(f"- {name}: {total} candidates (S:{s_cnt}, C:{c_cnt}, non-std:{ns_cnt}){flag}")

    if zeros:
        lines.append(f"\nNote: {zeros} concept set(s) are empty. Consider adding terms or enabling deeper search.")
    return "\n".join(lines)

```

## Folder: projects/concept_discovery/debug

## Folder: projects/main

### File: `cohortgen/projects/main/README.md`
<a name="cohortgen-projects-main-readmemd"></a>
```markdown
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

Main imports and calls the sibling pipelines directly — no local skills are used for cohort work to keep concerns separated:

- `projects/clarification/pipeline.yaml` → clarification and cohort definition
- `projects/concept_discovery/pipeline.yaml` → ATHENA‑based concept discovery (+ inline review inside that pipeline)
- `projects/query_builder/pipeline.yaml` → SQL generation and BigQuery validation

How it’s wired:
- `imports` section in `main/pipeline.yaml` declares the three sub‑pipelines.
- Steps use `uses: imports.<alias>` to run them in‑process.
- Sub‑pipelines handle their own skills and context updates. Main does not call `main/skills/*` for cohort logic.

Data flow:
- Clarification writes `scratchpad.cohort_definition`.
- Concept discovery writes `scratchpad.concept_sets` (after an optional review inside that sub‑pipeline).
- Query builder reads those and writes `scratchpad.final_sql`.

```

### File: `cohortgen/projects/main/flujo.toml`
<a name="cohortgen-projects-main-flujotoml"></a>
```toml
# Flujo project configuration template

# Use an in-memory state backend by default for new projects
state_uri = "memory://"

# Load environment variables (API keys, etc.) from this file.
# Copy `.env.example` to `.env`, fill your keys, or change this path.
env_file = ".env"

[settings]
# default_solution_model = "gpt-4o-mini"
# reflection_enabled = true

# Centralized budgets (optional)
[budgets]
# [budgets.default]
# total_cost_usd_limit = 5.0
# total_tokens_limit = 100000

# Architect defaults
[architect]
# Enable the agentic Architect state machine by default for this project
state_machine_default = true
# To disable by default, set to false or remove this section.
# Per-run overrides:
#   - Force agentic: export FLUJO_ARCHITECT_STATE_MACHINE=1
#   - Force minimal: export FLUJO_ARCHITECT_MINIMAL=1

# Explicit cost configuration to avoid strict-pricing failures and track spend
[cost]
  strict = false
  [cost.providers]
    [cost.providers.openai]
      # Placeholder prices for testing; adjust for your account/models as needed
      [cost.providers.openai.gpt-5]
        prompt_tokens_per_1k = 0.010
        completion_tokens_per_1k = 0.030
      [cost.providers.openai.gpt-5-mini]
        prompt_tokens_per_1k = 0.002
        completion_tokens_per_1k = 0.006

```

### File: `cohortgen/projects/main/pipeline.yaml`
<a name="cohortgen-projects-main-pipelineyaml"></a>
```yaml
version: "0.1"
name: "cohort_orchestrator"

pipeline_config:
  conversation_mode: true

imports:
  clarification: "../clarification/pipeline.yaml"
  concept_discovery: "../concept_discovery/pipeline.yaml"
  query_builder: "../query_builder/pipeline.yaml"


steps:
  # 0) Capture initial goal at the top-level
  - kind: hitl
    name: get_initial_goal
    message: "What would you like to accomplish?"
    updates_context: true

  # State machine orchestrator ensures the same stage re-runs after HITL resume
  - kind: StateMachine
    name: orchestrate
    start_state: "clarification"
    end_states: ["done"]
    states:
      clarification:
        steps:
          - name: run_clarification_subpipeline
            uses: imports.clarification
            input: |
              {{ steps.get_initial_goal.output }}
            updates_context: true
            input_to: initial_prompt
            inherit_context: true
            inherit_conversation: true
            propagate_hitl: true
            outputs:
              - child: scratchpad.cohort_definition
                parent: scratchpad.cohort_definition
          

      concept_discovery:
        steps:
          - kind: step
            name: prepare_for_concepts
            uses: "skills.custom_tools:prepare_concept_discovery_input"
            updates_context: true
          - name: run_concept_discovery_subpipeline
            uses: imports.concept_discovery
            input: "{{ steps.prepare_for_concepts.output | tojson }}"
            updates_context: true
            input_to: initial_prompt
            inherit_context: true
            inherit_conversation: true
            propagate_hitl: true
            outputs:
              - child: scratchpad.concept_sets
                parent: scratchpad.concept_sets
          - kind: step
            name: clear_refinement_feedback
            uses: "skills.custom_tools:clear_refinement_feedback"
            updates_context: true
          

      review:
        steps:
          - kind: step
            name: summarize_sets
            uses: "skills.custom_tools:summarize_concept_sets_brief"
            input: "{{ context.scratchpad.concept_sets | tojson }}"
            updates_context: true
          - kind: hitl
            name: review_concept_sets
            message: |
              {{ (context.scratchpad.review_feedback + '\n\n') if context.scratchpad.review_feedback else '' }}{{ steps.summarize_sets.output }}

              Reply "yes" to accept, paste edited JSON with a top-level concept_sets array, or give feedback in plain language to refine concepts.
            updates_context: true
          - kind: step
            name: apply_concept_review
            uses: "skills.custom_tools:apply_concept_review"
            input: "{{ steps.review_concept_sets.output }}"
            updates_context: true
          

      assumptions_review:
        steps:
          - kind: step
            name: extract_assumptions
            uses: "skills.custom_tools:extract_assumptions_text"
            updates_context: true
          - kind: hitl
            name: acknowledge_assumptions
            message: |
              {{ steps.extract_assumptions.output }}

              Please type 'yes' to acknowledge and proceed to SQL generation, or anything else to stay here and adjust inputs.
            updates_context: true
          - kind: step
            name: set_assumptions_ack
            uses: "skills.custom_tools:parse_yes_flag"
            input: "{{ steps.acknowledge_assumptions.output }}"
            updates_context: true
          

      query_builder:
        steps:
          - kind: step
            name: prepare_for_query_builder
            uses: "skills.custom_tools:prepare_query_builder_input"
            updates_context: true
          - name: run_query_builder_subpipeline
            uses: imports.query_builder
            input: "{{ steps.prepare_for_query_builder.output | tojson }}"
            updates_context: true
            input_to: initial_prompt
            inherit_context: true
            inherit_conversation: true
            propagate_hitl: true
            outputs:
              - child: scratchpad.final_sql
                parent: scratchpad.final_sql
          

      done:
        steps:
          - kind: step
            name: generate_report
            uses: "skills.custom_tools:generate_final_report"
            updates_context: true
          - kind: step
            name: save_outputs
            uses: "skills.custom_tools:save_final_outputs"
            input: |
              {{ {"report": steps.generate_report.output, "sql": context.scratchpad.final_sql } | tojson }}
            updates_context: true

      failed:
        steps:
          - kind: step
            name: report_failure
            agent: "flujo.builtins.passthrough"
            input: "The workflow has encountered an unrecoverable error."

    transitions:
      # Clarification
      - from: clarification
        on: pause
        to: clarification
      - from: clarification
        on: success
        to: concept_discovery

      # Concept discovery
      - from: concept_discovery
        on: pause
        to: concept_discovery
      - from: concept_discovery
        on: success
        to: review

      # Review
      - from: review
        on: pause
        to: review
      - from: review
        on: success
        to: concept_discovery
        when: context.scratchpad.refinement_feedback
      - from: review
        on: success
        to: assumptions_review

      # Assumptions
      - from: assumptions_review
        on: pause
        to: assumptions_review
      - from: assumptions_review
        on: success
        to: query_builder
        when: context.scratchpad.assumptions_ack == true
      - from: assumptions_review
        on: success
        to: assumptions_review

      # Query builder
      - from: query_builder
        on: success
        to: done

      # Generic failure
      - from: "*"
        on: failure
        to: failed

```

## Folder: projects/main/skills

### File: `cohortgen/projects/main/skills/custom_tools.py`
<a name="cohortgen-projects-main-skills-custom_toolspy"></a>
```python
from __future__ import annotations

import json
from typing import Any, Dict, List
try:
    from flujo.domain.models import PipelineContext  # type: ignore
except Exception:  # Fallback for test environments without Flujo
    class PipelineContext:  # type: ignore
        pass


async def _to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        s = obj.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                loaded = json.loads(s)
                return loaded if isinstance(loaded, dict) else {"value": obj}
            except Exception:
                return {"value": obj}
        return {"value": obj}
    return {"value": str(obj)}


async def get_cohort_definition_text(value: Any) -> str:
    """Return a robust plain-text cohort definition from various wrappers.

    Accepts: plain string, {"cohort_definition": str}, {"value": str}, Pydantic-like.
    """
    d = await _to_dict(value)  # type: ignore[arg-type]
    # Prefer explicit key
    text = d.get("cohort_definition")
    if isinstance(text, str) and text.strip():
        return text.strip()
    # Common wrapper
    text = d.get("value")
    if isinstance(text, str) and text.strip():
        return text.strip()
    # Fallback to stringify
    if isinstance(value, str) and value.strip():
        return value.strip()
    return ""


async def get_concept_sets_obj(value: Any) -> Dict[str, Any]:
    """Return a dict with a top-level 'concept_sets' list if present or empty.

    Accepts: dict with concept_sets, JSON string, or generic object.
    """
    d = await _to_dict(value)  # type: ignore[arg-type]
    cs = d.get("concept_sets")
    if isinstance(cs, list):
        return {"concept_sets": cs}
    # Some flows use the value directly as a list
    if isinstance(value, list):
        return {"concept_sets": value}
    # Otherwise return empty
    return {"concept_sets": []}


"""State control helpers removed in favor of declarative transitions."""


async def prepare_concept_discovery_input(_: Any = None, *, context: PipelineContext) -> Dict[str, Any]:
    """Prepare input for concept_discovery sub-pipeline using shared context.

    Ignores direct payload and reads from context.scratchpad.
    """
    sp = getattr(context, "scratchpad", None)
    if sp is None and isinstance(context, dict):
        sp = context.get("scratchpad", {})
    if sp is None:
        sp = {}
    definition = await get_cohort_definition_text(sp.get("cohort_definition"))
    feedback = sp.get("refinement_feedback") or ""
    return {"cohort_definition": definition, "refinement_feedback": feedback}


async def prepare_query_builder_input(_: Any = None, *, context: PipelineContext) -> Dict[str, Any]:
    """Prepare input for query_builder sub-pipeline using shared context."""
    sp = getattr(context, "scratchpad", None)
    if sp is None and isinstance(context, dict):
        sp = context.get("scratchpad", {})
    if sp is None:
        sp = {}
    definition = await get_cohort_definition_text(sp.get("cohort_definition"))
    concepts = await get_concept_sets_obj(sp.get("concept_sets"))
    return {"cohort_definition": definition, "concept_sets": concepts}


async def apply_concept_review(payload: Any) -> Dict[str, Any]:
    # Accept simple yes/ok or allow JSON override for concept_sets
    text: str = ""
    if isinstance(payload, str):
        text = payload.strip()
    else:
        try:
            text = json.dumps(payload)
        except Exception:
            text = str(payload)
    accepted = False
    updated: Dict[str, Any] | None = None
    if text:
        low = text.lower().strip()
        if low in {"y", "yes", "ok", "okay", "accept", "approved"}:
            accepted = True
        else:
            try:
                data = json.loads(text)
                if isinstance(data, dict) and isinstance(data.get("concept_sets"), list):
                    updated = {"concept_sets": data["concept_sets"]}
                    accepted = True
                elif isinstance(data, list):
                    updated = {"concept_sets": data}
                    accepted = True
            except json.JSONDecodeError as e:  # type: ignore[name-defined]
                feedback = (
                    "Your input was not 'yes' and could not be parsed as valid JSON. "
                    "We'll treat it as refinement feedback to re-run concept discovery. "
                    f"Error: {e}"
                )
                return {
                    "scratchpad": {
                        "concept_review_accepted": False,
                        "review_feedback": feedback,
                        "refinement_feedback": text,
                    }
                }
            except Exception:
                accepted = False
    out: Dict[str, Any] = {"scratchpad": {"concept_review_accepted": accepted}}
    if updated is not None:
        out["scratchpad"]["concept_sets"] = updated  # type: ignore[index]
    if accepted:
        # Clear any previous feedback on success
        out["scratchpad"]["review_feedback"] = ""
        out["scratchpad"]["refinement_feedback"] = ""
    return out


async def summarize_concept_sets_brief(data: Dict[str, Any] | str | object) -> str:
    # Normalize
    obj: Dict[str, Any]
    if isinstance(data, dict):
        obj = data
    elif isinstance(data, str):
        try:
            obj = json.loads(data) if data.strip().startswith("{") else {"data": data}
        except Exception:
            obj = {"data": data}
    else:
        try:
            obj = json.loads(json.dumps(data, default=str))
            if not isinstance(obj, dict):
                obj = {"data": str(data)}
        except Exception:
            obj = {"data": str(data)}
    sets = obj.get("concept_sets")
    if not isinstance(sets, list) or not sets:
        return (
            "No valid concept sets were discovered. You can provide feedback to try again, "
            "or paste a valid JSON structure for the concept sets."
        )
    lines: List[str] = ["Concept sets summary:"]
    for cs in sets:
        if not isinstance(cs, dict):
            continue
        name = cs.get("name") or "unnamed"
        concepts = cs.get("concepts")
        ids = cs.get("concept_ids")
        n = len(concepts) if isinstance(concepts, list) else (len(ids) if isinstance(ids, list) else 0)
        lines.append(f"- {name}: {n} concepts")
    return "\n".join(lines)


async def clear_refinement_feedback(_: Any = None) -> Dict[str, Any]:
    return {"scratchpad": {"refinement_feedback": ""}}


async def parse_yes_flag(payload: Any) -> Dict[str, Any]:
    text = ""
    if isinstance(payload, str):
        text = payload.strip().lower()
    else:
        try:
            text = str(payload).strip().lower()
        except Exception:
            text = ""
    ack = text in {"y", "yes"}
    return {"scratchpad": {"assumptions_ack": ack}}


async def generate_final_report(_: Any = None, *, context: PipelineContext) -> str:
    sp = getattr(context, "scratchpad", {})
    cd = sp.get("cohort_definition") or "(no cohort definition)"
    assumptions = await extract_assumptions_text(context=context)
    cs = sp.get("concept_sets") or {}
    final_sql = sp.get("final_sql") or ""
    dry = sp.get("dry_run_result") or {}
    cost = None
    summary = None
    try:
        cost = dry.get("estimated_cost_usd")
        summary = dry.get("summary")
    except Exception:
        pass
    num_sets = 0
    if isinstance(cs, dict) and isinstance(cs.get("concept_sets"), list):
        num_sets = len(cs["concept_sets"])
    parts: List[str] = []
    parts.append("# Cohort Generation Run Summary\n")
    parts.append("## Final Cohort Definition\n")
    parts.append(str(cd) + "\n")
    parts.append("## Assumptions\n")
    parts.append(str(assumptions) + "\n")
    parts.append(f"## Concept Sets\nTotal sets: {num_sets}\n")
    parts.append("## SQL (first 80 chars)\n")
    parts.append((final_sql[:80] + ("..." if len(final_sql) > 80 else "")) + "\n")
    if summary or cost is not None:
        parts.append("## BigQuery Dry Run\n")
        if summary:
            parts.append(str(summary) + "\n")
        if cost is not None:
            parts.append(f"Estimated cost (USD): {cost}\n")
    return "\n".join(parts)


async def save_final_outputs(payload: Any) -> Dict[str, Any]:
    d: Dict[str, Any]
    if isinstance(payload, dict):
        d = payload
    else:
        try:
            d = json.loads(json.dumps(payload))
        except Exception:
            d = {}
    report = d.get("report") or ""
    sql = d.get("sql") or ""
    import os
    out_dir = os.path.join("output")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "final_report.md")
    sql_path = os.path.join(out_dir, "final_query.sql")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(str(report))
    except Exception:
        pass
    try:
        with open(sql_path, "w", encoding="utf-8") as f:
            f.write(str(sql))
    except Exception:
        pass
    return {"scratchpad": {"final_report_path": report_path, "final_sql_path": sql_path}}


async def extract_assumptions_text(_: Any = None, *, context: PipelineContext) -> str:
    # Pull assumptions from cohort_definition text and concept_sets assumptions
    sp = getattr(context, "scratchpad", None)
    if sp is None and isinstance(context, dict):
        sp = context.get("scratchpad", {})
    if sp is None:
        sp = {}
    lines: List[str] = []
    # From cohort definition
    cd = sp.get("cohort_definition")
    if isinstance(cd, str):
        for line in cd.splitlines():
            if line.strip().lower().startswith("assumption:"):
                lines.append(line.strip())
    # From concept sets (optional field assumptions)
    cs = sp.get("concept_sets")
    if isinstance(cs, dict):
        arr = cs.get("assumptions")
        if isinstance(arr, list):
            for a in arr:
                s = str(a).strip()
                if s:
                    if not s.lower().startswith("assumption:"):
                        s = f"Assumption: {s}"
                    lines.append(s)
    # Deduplicate while preserving order
    seen = set()
    ordered: List[str] = []
    for s in lines:
        if s not in seen:
            ordered.append(s)
            seen.add(s)
    if not ordered:
        return "No explicit assumptions were detected."
    out = ["Assumptions to review:"]
    for i, s in enumerate(ordered, start=1):
        out.append(f"{i}. {s}")
    return "\n".join(out)

```

## Folder: tests

### File: `cohortgen/tests/test_athena_tools.py`
<a name="cohortgen-tests-test_athena_toolspy"></a>
```python
from __future__ import annotations

import types
from typing import Any, Dict, List

import importlib


def _make_fake_results(items: List[Dict[str, Any]]):
    class FakeResults:
        def top(self, k: int):
            return items[:k]

        def all(self):
            return list(items)

    return FakeResults()


class FakeAthena:
    def __init__(self, mapping: Dict[str, List[Dict[str, Any]]]):
        self.mapping = mapping

    def search(self, q: str):
        return _make_fake_results(self.mapping.get(q, []))


def test_athena_search_for_concept_plan_filters_and_limits(monkeypatch):
    import sys
    from pathlib import Path

    skills_dir = (
        Path(__file__).resolve().parents[1]
        / "projects"
        / "concept_discovery"
        / "skills"
    )
    sys.path.insert(0, str(skills_dir))
    athena_tools = importlib.import_module("athena_tools")

    # Build a fake dataset returned by Athena
    items = [
        # Valid: standard 'S', correct domain/vocab
        {
            "concept_id": 1,
            "concept_name": "COVID-19",
            "domain_id": "Condition",
            "vocabulary_id": "SNOMED",
            "standard_concept": "S",
            "concept_code": "111",
        },
        # Excluded: wrong domain
        {
            "concept_id": 2,
            "concept_name": "Some drug",
            "domain_id": "Drug",
            "vocabulary_id": "RxNorm",
            "standard_concept": "S",
            "concept_code": "222",
        },
        # Excluded when standard_only: non-standard
        {
            "concept_id": 3,
            "concept_name": "COVID-NonStd",
            "domain_id": "Condition",
            "vocabulary_id": "SNOMED",
            "standard_concept": None,
            "concept_code": "333",
        },
        # Allowed by search filter stage: classification 'C'
        {
            "concept_id": 4,
            "concept_name": "COVID-19 class",
            "domain_id": "Condition",
            "vocabulary_id": "SNOMED",
            "standard_concept": "C",
            "concept_code": "444",
        },
    ]

    fake = FakeAthena({"COVID": items})

    # Patch the internal factory to use our fake client
    monkeypatch.setattr(athena_tools, "_safe_athena", lambda: fake)

    plan = {
        "concept_sets": [
            {
                "name": "Index condition",
                "intent": "Primary COVID-19",
                "domain": "Condition",
                "vocabulary": ["SNOMED"],
                "include_descendants": True,
                "standard_only": True,
                "queries": ["COVID"],
            }
        ]
    }

    out = athena_tools.athena_search_for_concept_plan(plan, top_k=2)

    assert "concept_sets" in out and len(out["concept_sets"]) == 1
    cs = out["concept_sets"][0]
    # Enforces top_k limit
    assert len(cs["candidates"]) <= 2
    # Ensure only domain+vocab-matching and standard-only (S or C) make it through
    ids = {c["concept_id"] for c in cs["candidates"]}
    assert 1 in ids  # S, Condition, SNOMED
    # 2 excluded (Drug)
    assert 2 not in ids
    # 3 excluded (non-standard)
    assert 3 not in ids
    # 4 allowed at this stage (classification 'C'); later stages may filter to 'S' only
    assert 4 in ids


def test_athena_search_accepts_camel_case_and_bools(monkeypatch):
    import sys
    from pathlib import Path
    skills_dir = (
        Path(__file__).resolve().parents[1]
        / "projects"
        / "concept_discovery"
        / "skills"
    )
    sys.path.insert(0, str(skills_dir))
    athena_tools = importlib.import_module("athena_tools")

    items = [
        {
            "conceptId": 10,
            "conceptName": "Influenza",
            "domainId": "Condition",
            "vocabularyId": "SNOMED",
            "isStandard": True,
            "conceptCode": "X1",
        },
        {
            "conceptId": 11,
            "conceptName": "Flu lab test",
            "domainId": "Measurement",
            "vocabularyId": "LOINC",
            "isStandard": True,
            "conceptCode": "X2",
        },
    ]

    fake = FakeAthena({"Influenza": items})
    # Patch factory
    monkeypatch.setattr(athena_tools, "_safe_athena", lambda: fake)

    plan = {
        "concept_sets": [
            {
                "name": "Influenza",
                "domain": "Condition",
                "vocabulary": ["SNOMED"],
                "include_descendants": True,
                "standard_only": True,
                "queries": ["Influenza"],
            }
        ]
    }
    out = athena_tools.athena_search_for_concept_plan(plan, top_k=5)
    cs = out["concept_sets"][0]
    assert len(cs["candidates"]) == 1
    c = cs["candidates"][0]
    assert c["concept_id"] == 10
    assert c["domain_id"] == "Condition"
    assert c["vocabulary_id"] == "SNOMED"

```

### File: `cohortgen/tests/test_cli.py`
<a name="cohortgen-tests-test_clipy"></a>
```python
from cohortgen.cli import main


def test_cli_list_projects(capsys):
    rc = main(["list"])  # lists projects and exits 0
    out = capsys.readouterr().out
    assert rc == 0
    # Either no projects or list header
    assert "Projects:" in out or "No Flujo projects" in out

```

### File: `cohortgen/tests/test_main_tools.py`
<a name="cohortgen-tests-test_main_toolspy"></a>
```python
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def _import_main_tools():
    import sys
    skills_dir = Path(__file__).resolve().parents[1] / "projects" / "main" / "skills"
    sys.path.insert(0, str(skills_dir))
    try:
        return importlib.import_module("custom_tools")
    finally:
        # Do not leave multiple duplicates; cleanup first occurrence we added
        try:
            sys.path.remove(str(skills_dir))
        except ValueError:
            pass


@pytest.mark.skip(reason="decide_stage removed in favor of declarative StateMachine transitions")
def test_decide_stage_flow():
    pass


@pytest.mark.asyncio
async def test_prepare_inputs_and_summary():
    tools = _import_main_tools()
    # Prepare concept discovery input
    ctx = {"scratchpad": {"cohort_definition": "My cohort definition"}}
    out = await tools.prepare_concept_discovery_input(context=ctx)
    assert out.get("cohort_definition") == "My cohort definition"
    assert "refinement_feedback" in out

    # Prepare query builder input
    ctx = {
        "scratchpad": {
            "cohort_definition": "My cohort definition",
            "concept_sets": {"concept_sets": [{"name": "A", "concept_ids": [1, 2]}]},
        }
    }
    out = await tools.prepare_query_builder_input(context=ctx)
    assert out["cohort_definition"] == "My cohort definition"
    assert isinstance(out["concept_sets"], dict)
    assert isinstance(out["concept_sets"].get("concept_sets"), list)

    # Summarize concept sets
    summary = await tools.summarize_concept_sets_brief(
        {"concept_sets": [{"name": "A", "concept_ids": [1, 2]}, {"name": "B", "concepts": [{"concept_id": 5}]}]}
    )
    assert "Concept sets summary:" in summary
    assert "A: 2 concepts" in summary
    assert "B: 1 concepts" in summary


@pytest.mark.asyncio
async def test_apply_concept_review_yes_and_json():
    tools = _import_main_tools()

    # Accept simple yes
    out = await tools.apply_concept_review("yes")
    assert out["scratchpad"]["concept_review_accepted"] is True

    # Provide JSON override
    payload = {"concept_sets": [{"name": "C", "concept_ids": [10]}]}
    out = await tools.apply_concept_review(payload)
    assert out["scratchpad"]["concept_review_accepted"] is True
    cs = out["scratchpad"].get("concept_sets")
    assert isinstance(cs, dict) and isinstance(cs.get("concept_sets"), list)

    # Invalid JSON should provide feedback and not accept
    out = await tools.apply_concept_review("{not json}")
    sp = out["scratchpad"]
    assert sp.get("concept_review_accepted") is False
    assert isinstance(sp.get("review_feedback"), str) and "could not be parsed" in sp.get("review_feedback")
    assert isinstance(sp.get("refinement_feedback"), str) and sp.get("refinement_feedback")

    # Natural language feedback should set refinement_feedback
    out = await tools.apply_concept_review("these sets include pregnancy; please exclude")
    sp = out["scratchpad"]
    assert sp.get("concept_review_accepted") is False
    assert isinstance(sp.get("refinement_feedback"), str) and "pregnancy" in sp.get("refinement_feedback")


@pytest.mark.asyncio
async def test_extract_assumptions_text():
    tools = _import_main_tools()
    ctx = {
        "scratchpad": {
            "cohort_definition": "Assumption: Using a 30-day washout.\nOther line.",
            "concept_sets": {"assumptions": ["Standard concepts only"]},
        }
    }
    out = await tools.extract_assumptions_text(context=ctx)
    assert "Assumptions to review:" in out
    assert "1. Assumption: Using a 30-day washout." in out
    assert "2. Assumption: Standard concepts only" in out

```

### File: `cohortgen/tests/test_yaml_regressions.py`
<a name="cohortgen-tests-test_yaml_regressionspy"></a>
```python
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_transitions_block_has_only_transition_rules():
    """Ensure no step mappings are nested inside the transitions block."""
    p = ROOT / "projects" / "main" / "pipeline.yaml"
    content = read(p)
    # Guard: transitions exists
    assert "\n    transitions:\n" in content or "\ntransitions:\n" in content
    # Everything under transitions must not include step-like keys
    trans_idx = content.index("transitions:")
    trans_block = content[trans_idx:]
    # No nested step keys within transitions
    forbidden = ["\n      - kind:", "\n      - name:", "\n      - uses:"]
    for needle in forbidden:
        assert needle not in trans_block, f"Found step-like key inside transitions: {needle.strip()}"


def test_import_steps_have_no_kind_and_inherit_context():
    """ImportStep should be inferred and inherit_context must be true."""
    p = ROOT / "projects" / "main" / "pipeline.yaml"
    lines = read(p).splitlines()
    for i, line in enumerate(lines):
        if "uses: imports." in line:
            # Ensure no 'kind:' immediately above this step item
            window = "\n".join(lines[max(0, i - 2): i])
            assert "kind:" not in window, f"Unexpected 'kind' near import step at line {i+1}"
            # Ensure inherit_context: true appears within the next few lines
            window_after = "\n".join(lines[i : i + 10])
            assert "inherit_context: true" in window_after, "Import step must set inherit_context: true"
    # And do not allow step-level 'config:' in main pipeline (allow pipeline_config)
    content = read(p)
    import re
    assert re.search(r"(^|\n)\s+config:\s*", content) is None


def test_states_have_steps_key():
    """Each state under states: must declare steps:"""
    p = ROOT / "projects" / "main" / "pipeline.yaml"
    content = read(p)
    # Spot check a few states
    assert "clarification:\n        steps:" in content or "clarification:\n      steps:" in content
    assert "concept_discovery:\n        steps:" in content or "concept_discovery:\n      steps:" in content
    assert "review:\n        steps:" in content or "review:\n      steps:" in content
    assert "assumptions_review:\n        steps:" in content or "assumptions_review:\n      steps:" in content
    assert "query_builder:\n        steps:" in content or "query_builder:\n      steps:" in content
    assert "done:\n        steps:" in content or "done:\n      steps:" in content


def test_no_unsupported_slice_filter_in_yaml():
    """Avoid non-standard template filters like slice() in YAML templates."""
    for p in (ROOT / "projects").rglob("*.yaml"):
        content = read(p)
        assert "| slice(" not in content, f"Unsupported filter slice() found in {p}"


def test_concept_discovery_execute_tool_input_not_json_stringified():
    """Ensure execute_tool receives object, not a JSON string."""
    p = ROOT / "projects" / "concept_discovery" / "pipeline.yaml"
    content = read(p)
    # Require exact input shape for execute_tool step
    assert "name: execute_tool" in content
    assert 'input: "{{ steps.decide_next_action.output }}"' in content

```

## Folder: output

### File: `cohortgen/output/last_run_error.txt`
<a name="cohortgen-output-last_run_errortxt"></a>
```text
Exit(1)
```

## Folder: .mypy_cache

## Folder: .mypy_cache/3.11

## Folder: .mypy_cache/3.11/cohortgen

## Folder: .mypy_cache/3.11/pathlib

## Folder: .mypy_cache/3.11/_typeshed

## Folder: .mypy_cache/3.11/zipfile

## Folder: .mypy_cache/3.11/sys

## Folder: .mypy_cache/3.11/os

## Folder: .mypy_cache/3.11/importlib

## Folder: .mypy_cache/3.11/importlib/resources

## Folder: .mypy_cache/3.11/importlib/metadata

## Folder: .mypy_cache/3.11/collections

## Folder: .mypy_cache/3.11/email

## Folder: .venv

## Folder: .venv/lib

## Folder: .venv/lib/python3.11

## Folder: .venv/share

## Folder: .venv/share/man

## Folder: .venv/share/man/man1

## Folder: .venv/share/doc

## Folder: .venv/share/doc/flujo

### File: `cohortgen/.venv/share/doc/flujo/CHANGELOG.md`
<a name="cohortgen-venv-share-doc-flujo-changelogmd"></a>
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Conversational Loops (FSD-033):
  - `conversation: true` loop mode with automatic conversation_history capture and prompt injection via processors
  - History management strategies: `truncate_tokens`, `truncate_turns`, `summarize` with centralized defaults and loop-level overrides
  - Selection controls: `ai_turn_source` (last/all_agents/named_steps), `user_turn_sources` (hitl and/or named steps)
  - Lens trace shows `agent.prompt` events with a sanitized preview of rendered history
  - Wizard support to scaffold conversation blocks and presets
  - Persistence: conversation_history survives pause/resume and project restarts (SQLite backend tested)

### Fixed
- StateMachine YAML loader now compiles `states` that use `uses: imports.<alias>` into first-class `ImportStep`s. This preserves policy-driven execution and prevents fallback to the default Step policy (which could trigger `MissingAgentError` if no agent is present on the import step). Tests include unit, integration, and a regression covering the original scenario.


### Added
- Declarative LoopStep enhancements in YAML loader:
  - `loop.init` (runs once on isolated iteration context)
  - `loop.propagation.next_input` (presets: `context` | `previous_output` | `auto` or template)
  - `loop.output_template` and `loop.output` (object mapping) compiled to `loop_output_mapper`
- Friendly presets for domain users:
  - `conversation: true`, `stop_when: agent_finished`, `propagation: context|previous_output`,
    `output: text: conversation_history`, and simple `init.history.start_with` helpers
- MapStep sugars:
  - `map.init` (pre-run init ops) and `map.finalize` (post-aggregation output mapping)
    with the same templating semantics as loop output.
- Parallel reduce sugar:
  - `reduce: keys|values|union|concat|first|last` to post-process branch outputs while preserving
    input branch order; default remains branch-output mapping.
- CLI improvements:
  - `flujo create --wizard` to generate a natural, friendly YAML without running the Architect.
  - `flujo explain <path>` to summarize a YAML's structure in plain language.
- Policy hook in `DefaultLoopStepExecutor` to execute compiled init ops at iteration 1

### Notes
- Aligns with FLUJO_TEAM_GUIDE policy-driven architecture: control-flow exceptions re-raised,
  context idempotency preserved via isolation, and quotas unchanged.

## [0.6.3] - 2025-08-10

### Added
- `core/default_components.py`: Centralized default implementations for executor composition
  - `OrjsonSerializer`, `Blake3Hasher`, `InMemoryLRUBackend`, `ThreadSafeMeter`
  - `DefaultAgentRunner`, `DefaultProcessorPipeline`, `DefaultValidatorRunner`, `DefaultPluginRunner`
  - `DefaultTelemetry`, `DefaultCacheKeyGenerator`
- `__all__` export list in `core/ultra_executor.py` to define the public API and re-export interfaces and defaults for backward compatibility.
- `__all__` in `core/default_components.py` and `core/executor_protocols.py` for explicit public surfaces.

### Changed
- Consolidated Protocol interfaces into `core/executor_protocols.py` as the single source of truth; removed duplicates from `ultra_executor.py`.
- `ultra_executor.py` now imports default components from `core/default_components.py` and stays focused on orchestration and policy routing.
- `application/runner.py` composition updated to import defaults from `core/default_components.py`.
- Classified `PipelineAbortSignal` as a control-flow category in `core/optimized_error_handler.py` to align with FSD-009 (non-retryable control flow).
 - Restored `_UsageTracker` compatibility shim in `core/ultra_executor.py` to satisfy legacy tests while usage metering moves to `ThreadSafeMeter`.

### Migration
- Recommended imports:
  - Defaults: `from flujo.application.core.default_components import OrjsonSerializer, ...`
  - Interfaces: `from flujo.application.core.executor_protocols import IAgentRunner, ...`
- Backward compatibility: Existing imports from `core/ultra_executor.py` continue to work via re-exports in this release. These re-exports will be deprecated in a future minor release.

### Notes
- This change aligns with the policy-driven architecture in `FLUJO_TEAM_GUIDE.md` and the FSD for decomposing the ultra executor. No runtime behavior changes are intended.

## [0.4.37] - 2025-08-14
### Added
- Project scaffolding via `flujo init` with templates (`flujo.toml`, `pipeline.yaml`, `skills/`, `.flujo/`).
- Conversational `flujo create` enhancements: optional goal prompt, pipeline name prompt (injected as top-level `name:`), and per-run budget prompt appended to `flujo.toml` under `[budgets.pipeline."<name>"]`.
- Project-aware defaults: `flujo run` and `flujo validate` now infer the project’s `pipeline.yaml` when no file path is provided.
- `lens replay` now looks for `pipeline.yaml` in the project when `--file` is omitted; still supports `--file` for `.yaml` or Python definitions.
- Template `flujo.toml` sets `state_uri = "sqlite:///.flujo/state.db"` so lens and telemetry use project-local state by default.

### Changed
- Inside a project, `flujo create` overwrites `pipeline.yaml` by default (no `--force` needed). For non-project output directories, original `--force` behavior remains.
- Documentation updated to reflect the new project-based journey and project-aware commands.

### Migration Guidance
- Existing flows that passed explicit file paths continue to work unchanged.
- Recommended: initialize a project (`flujo init`), then run `flujo create` and `flujo run` from inside the project.
- For `lens` tooling, the new template sets a project-local `state_uri`. If you used a global DB, you can keep using `FLUJO_STATE_URI` or set `state_uri` in your `flujo.toml`.

## [0.4.35] - 2025-01-15

### Added
- **Performance Optimizations**: Enhanced execution efficiency and resource management
  - Improved parallel step execution with better resource allocation
  - Optimized memory usage patterns for large-scale workflows
  - Enhanced caching mechanisms for better performance
  - Streamlined context handling for improved throughput

### Changed
- **Stability Improvements**: Enhanced error handling and recovery mechanisms
  - Improved error recovery and resilience patterns
  - Better exception handling across pipeline components
  - Enhanced validation and error reporting
  - More robust state management and persistence

### Fixed
- **Bug Fixes**: Resolved various edge cases and issues
  - Fixed context serialization issues in complex workflows
  - Resolved race conditions in parallel execution
  - Corrected memory leaks in long-running pipelines
  - Fixed edge cases in error recovery mechanisms

## [0.4.34] - 2025-01-15

### Added
- **Enhanced Documentation**: Improved documentation structure and content
  - Fixed broken internal links in documentation pages
  - Updated navigation structure for better user experience
  - Enhanced cookbook examples with current API patterns
  - Improved documentation coverage for new features

### Fixed
- **Documentation Build Warnings**: Resolved mkdocs build warnings and issues
  - Fixed missing cookbook pages and broken internal links
  - Corrected navigation structure and page references
  - Improved documentation build process reliability
  - Enhanced user experience with better documentation organization

### Changed
- **Code Quality Improvements**: Enhanced codebase maintainability and reliability
  - Improved error handling and validation patterns
  - Enhanced test coverage and reliability
  - Better code organization and documentation
  - Streamlined development workflow

## [0.4.33] - 2025-01-15

### Added
- **Budget-Aware Workflows**: Enhanced workflow execution with cost and token budget management
  - New budget-aware execution strategies for cost-effective AI workflows
  - Token usage tracking and optimization across pipeline steps
  - Cost monitoring and alerting capabilities for production deployments
  - Dynamic resource allocation based on budget constraints

### Changed
- **Performance Optimizations**: Improved execution efficiency and resource utilization
  - Enhanced parallel step execution with better resource management
  - Optimized context handling for large-scale workflows
  - Improved memory usage patterns for long-running pipelines
  - Better error recovery and resilience mechanisms

### Fixed
- **Documentation Updates**: Resolved documentation build warnings and link issues
  - Fixed broken internal links in documentation
  - Updated navigation structure for better user experience
  - Enhanced cookbook examples with current API patterns
  - Improved documentation coverage for new features

## [0.4.32] - 2025-07-14

### Fixed
- **CI/CD Workflow Improvements**: Enhanced GitHub Actions release workflow for robust PyPI publishing
  - Added `uv` installation step to fix missing dependency in CI environment
  - Simplified release workflow to industry-standard approach without automatic version bumping
  - Fixed permission issues by removing automatic tag creation and pushing
  - Improved changelog generation with manual control over release process
  - Added proper error handling and dependency management for reliable builds

### Changed
- **Release Process**: Streamlined release workflow for better reliability and control
  - Manual version management in `pyproject.toml` for explicit control
  - Tag-based triggers only (no automatic version bumping)
  - Simplified changelog generation without external dependencies
  - Enhanced build and test process with proper dependency installation

## [0.4.31] - 2025-07-14

### Fixed
- **Makefile Enhancements**: Added missing targets for CI/CD pipeline
  - Added `pip-dev` target for installing development dependencies
  - Added `package` target for building distribution files
  - Improved development workflow with comprehensive build system support
  - Enhanced CI/CD compatibility with proper dependency management

## [0.4.29] - 2025-07-14

### Added
- **Documentation Updates**: Enhanced project documentation and branding
  - Updated main documentation page with new headline "The Framework for AI Systems That Learn"
  - Improved documentation structure with comprehensive navigation
  - Enhanced mkdocs configuration for better user experience
  - Updated contact information and licensing details

### Changed
- **License Management**: Updated commercial licensing and contact information
  - Enhanced commercial license agreement with comprehensive legal terms
  - Updated contact email to aandresalvarez@gmail.com
  - Improved dual licensing strategy (AGPL-3.0 + Commercial)
  - Enhanced intellectual property protection and usage terms

## [0.6.2] - 2025-02-20

### Added
- `run_id` parameter for `Flujo.run()` and `run_async()` simplifies durable workflow APIs.
- `serializer_default` on `StateBackend` implementations for advanced serialization.

### Changed
- Upgraded to Pydantic 2.0.

### Fixed
- Nested Pydantic models persist correctly in workflow state.

## [0.6.1] - 2025-01-15

### Added
- **Optimized ParallelStep Context Copying**: New `context_include_keys` parameter for `Step.parallel()` to selectively copy only needed context fields
  - Significantly reduces memory usage and overhead when working with large context objects
  - Allows developers to specify which context fields are required by parallel branches
  - Maintains backward compatibility - omitting the parameter copies the entire context
  - Performance improvement scales with context size and number of parallel branches
- **Proactive Governor Cancellation**: Enhanced `ParallelStep` with immediate sibling task cancellation
  - When any branch exceeds usage limits (cost or token limits), all sibling branches are immediately cancelled
  - Prevents wasted resources and time by stopping unnecessary work early
  - Uses `asyncio.Event` for efficient coordination between parallel tasks
  - Improves cost efficiency and reduces execution time for usage-limited scenarios
- **Comprehensive Benchmark Tests**: Added performance validation for new ParallelStep features
  - Integration tests verify selective context copying behavior
  - Benchmark tests measure performance improvements with large context objects
  - Cancellation tests ensure proper cleanup when usage limits are exceeded
  - Example script demonstrates practical usage of new features

### Changed
- **Enhanced ParallelStep Implementation**: Refactored `_execute_parallel_step_logic` for better performance and resource management
  - Optimized context copying strategy with selective field inclusion
  - Improved error handling and cancellation logic
  - Better resource cleanup and task management
  - More efficient coordination between parallel branches

### Fixed
- **Test Context Model Inheritance**: Fixed test context models to inherit from `flujo.domain.models.BaseModel`
  - Resolves Pydantic model inheritance issues in test suite
  - Ensures proper type compatibility with Flujo's domain models
  - Maintains test isolation and reliability
- **Pydantic-AI Compatibility:** Fixed a `TypeError` by updating how generation parameters like `temperature` are passed to the underlying `pydantic-ai` agent, ensuring compatibility with `pydantic-ai>=0.4.1`.
- **Dependencies:** Updated `pyproject.toml` to require `pydantic-ai>=0.4.1`.
- **Deprecated Recipes:** Marked `AgenticLoop` and `Default` classes as deprecated. Use the factory functions in `flujo.recipes.factories`.

## [0.6.0] - 2025-01-15

### Added
- **Curated Layered Public API**: Complete architectural refactor with organized, layered import structure
  - Core types (`Pipeline`, `Step`, `Context`, `Result`) available at top level (`from flujo import Pipeline`)
  - Related components grouped into logical submodules (`recipes`, `testing`, `plugins`, `processors`, `models`, `exceptions`, `validation`, `tracing`, `utils`, `domain`, `application`, `infra`)
  - Improved discoverability and reduced import complexity
  - Enhanced developer experience with clear module boundaries
- **ContextAwareAgentProtocol**: Type-safe context handling for agents
  - New protocol for agents that need typed pipeline context
  - Eliminates runtime errors and provides better IDE support
  - Maintains backward compatibility with AsyncAgentProtocol
- **Comprehensive Test Suite**: Robust testing infrastructure with 359 passing tests
  - Fixed all import errors and circular dependency issues
  - Resolved context mutation and agent protocol signature mismatches
  - Implemented proper settings patching for isolated test execution
  - Added systematic test fixes for all submodules and components
- **Enhanced Code Quality**: Production-ready codebase with comprehensive quality checks
  - All linting errors resolved (`ruff` compliance)
  - Complete type checking compliance (`mypy` success)
  - Security scanning passed (`bandit` validation)
  - Removed unused imports and dead code
  - Improved error handling and validation patterns

### Changed
- **BREAKING CHANGE**: Complete API restructuring for better organization and maintainability
  - Moved from flat import structure to curated, layered public API
  - Core types remain at top level for backward compatibility
  - Related functionality grouped into logical submodules
  - Updated all examples and documentation to use new import structure
  - Added migration guide for users transitioning from flat imports
- **BREAKING CHANGE**: Standardized context parameter injection
  - Unified context parameter injection to use `context` exclusively
  - Removed support for `pipeline_context` parameter in step functions, agents, and plugins
  - All context injection now uses the `context` parameter name
  - This aligns the implementation with the documented API contract
- **Improved Module Organization**: Better separation of concerns and encapsulation
  - Domain models and business logic separated from infrastructure
  - Application services isolated from domain logic
  - Infrastructure concerns properly abstracted
  - Clear boundaries between different architectural layers
- **Enhanced Error Handling**: More robust error management throughout the codebase
  - Consistent error patterns and exception handling
  - Better error messages and debugging information
  - Improved validation error reporting
  - Structured exception mechanisms for better error recovery

### Fixed
- **Import System**: Resolved all circular dependency and import issues
  - Fixed module import errors in test suite
  - Eliminated circular dependencies between submodules
  - Proper module initialization and attribute access
  - Consistent import patterns across the codebase
- **TypeAdapter Handling**: Enhanced `make_agent_async` to seamlessly handle `pydantic.TypeAdapter` instances
  - Automatically unwraps TypeAdapter instances to extract underlying types
  - Supports complex nested types like `List[Dict[str, MyModel]]`
  - Supports Union types like `Union[ModelA, ModelB]`
  - Maintains backward compatibility with regular types
- **Test Infrastructure**: Comprehensive test suite fixes and improvements
  - Fixed settings singleton patching for isolated test execution
  - Resolved context mutation issues in test scenarios
  - Fixed agent protocol signature mismatches
  - Corrected custom context model usage in tests
  - Implemented robust test isolation and cleanup
- **Documentation and Examples**: Updated all documentation to reflect new API structure
  - Fixed import statements in all examples
  - Updated documentation to use new submodule structure
  - Corrected example execution paths and import patterns
  - Enhanced documentation clarity and accuracy
  - **Updated "The Flujo Way" guide** with current API structure and ContextAwareAgentProtocol
- **Development Workflow**: Improved development and testing experience
  - Fixed `make quality` command for comprehensive quality checks
  - Enhanced `make test` and `make cov` commands
  - Improved development environment setup
  - Better error reporting and debugging tools

### Removed
- **Obsolete Submodules**: Cleaned up problematic module structure
  - Removed empty `__init__.py` files that caused import issues
  - Eliminated redundant module hierarchies
  - Streamlined module organization for better maintainability
  - Reduced complexity in import resolution
- **Repository Artifacts**: Cleaned up development artifacts
  - Removed obsolete backup files (`*.orig`) and temporary documentation
  - Eliminated patch files and standalone debug scripts
  - Improved contributor onboarding experience with cleaner repository

## [0.5.0] - 2025-07-02

### Added
- **Robust TypeAdapter Support**: Enhanced `make_agent_async` to seamlessly handle `pydantic.TypeAdapter` instances
  - Automatically unwraps TypeAdapter instances to extract underlying types
  - Supports complex nested types like `List[Dict[str, MyModel]]`
  - Supports Union types like `Union[ModelA, ModelB]`
  - Maintains backward compatibility with regular types
  - Enables modern Pydantic v2 patterns for non-BaseModel types
- **Enhanced CLI User Experience**: Improved command-line interface robustness and usability
  - Added `typer.Choice` validation for `--scorer` option with automatic tab completion
  - Enhanced help text generation for scoring strategy options
  - Removed manual validation logic in favor of built-in Typer validation
- **Comprehensive Type Safety**: Enabled full type checking for CLI module
  - Removed global `# type: ignore` directive from CLI module
  - Added proper generic type annotations for Pipeline and Step types
  - Enhanced type safety throughout the command-line interface

### Changed
- **BREAKING CHANGE**: Unified context parameter injection to use `context` exclusively
  - Removed support for `pipeline_context` parameter in step functions, agents, and plugins
  - All context injection now uses the `context` parameter name
  - This aligns the implementation with the documented API contract
  - Users who relied on `pipeline_context` parameter must update their code to use `context`
  - Removed deprecation warnings and backward compatibility logic for `pipeline_context`
- **Enhanced Documentation**: Improved clarity and discoverability of validation features
  - Added comprehensive documentation for `strict` parameter in `Step.validate_step`
  - Clarified difference between strict and non-strict validation modes
  - Added practical examples showing audit vs. blocking validation patterns
  - Updated Pipeline DSL guide with validation best practices

### Fixed
- **Repository Hygiene**: Cleaned up development artifacts and improved project structure
  - Removed obsolete backup files (`*.orig`) and temporary documentation
  - Eliminated patch files and standalone debug scripts
  - Improved contributor onboarding experience with cleaner repository
- **Test Suite Stability**: Fixed test failures related to context parameter migration
  - Updated test assertions to use new `context` parameter consistently
  - Ensured all integration tests pass with unified parameter naming
- **Code Quality**: Addressed linting and type checking issues
  - Removed unused imports and variables
  - Fixed type comparison issues in test code
  - Enhanced overall code quality and maintainability

## [0.4.24] - 2025-06-30

### Added
- Pre-flight pipeline validation with `Pipeline.validate()` returning a detailed report.
- New `flujo validate` CLI command to check pipelines from the command line.

## [0.4.25] - 2025-07-01

### Fixed
- `make_agent_async` now accepts `pydantic.TypeAdapter` instances for
  `output_type`, unwrapping them for proper schema generation and validation.

## [0.4.23] - 2025-06-27

### Fixed
- Loop iteration spans now wrap each iteration, eliminating redundant spans
- Conditional branch spans record the executed branch key for clarity
- Console tracer tracks nesting depth, indenting start/end messages accordingly

## [0.4.22] - 2025-06-23

### Added
- Distributed `py.typed` for PEP 561 type hint compatibility.

### Fixed
- Improved CI/CD workflows to gracefully handle Git tag conflicts.

## [0.4.18] - 2024-12-19

### Fixed
- Fixed parameter passing to prioritize 'context' over 'pipeline_context' for backward compatibility
- Ensures step functions receive the parameter name they expect, maintaining compatibility with existing code
- Resolves issue where Flujo engine was passing 'pipeline_context' instead of 'context' to step functions

## [0.4.15] - 2024-12-19

### Changed
- Version bump for release

## [0.4.14] - 2024-12-19

### Changed
- Version bump for release

## [0.4.13] - 2025-06-19

### Added
- Enhanced Makefile with pip-based development workflow support
- New `pip-dev` target for installing development dependencies with pip
- New `pip-install` target for installing package in development mode
- New `clean` target for cleaning build artifacts and caches

### Changed
- Improved development environment setup with better tooling support
- Enhanced project documentation and build system configuration

## [0.4.12] - 2024-12-19

### Changed
- Version bump for release

## [0.4.11] - 2024-12-19

### Changed
- Additional improvements and fixes

## [0.4.1] - 2024-12-19

### Fixed
- Fixed step retry logic to properly handle max_retries configuration
- Fixed pipeline execution to allow step retries before halting
- Fixed plugin validation loop to correctly handle retries and redirections
- Fixed failure handler execution during retry attempts
- Fixed redirect loop detection for unhashable agent objects
- Added usage limits support to loop and conditional step execution
- Improved error handling in streaming pipeline execution
- Fixed token and cost accumulation in step results

## [0.4.0] - 2024-12-19

### Added
- Intelligent evaluation system with traceability
- Pluggable execution backends for enhanced flexibility
- Streaming support with async generators
- Human-in-the-loop (HITL) support for interactive workflows
- Usage governor with cost and token limits
- Managed resource injection system
- Benchmark harness for performance testing
- Comprehensive cookbook documentation with examples
- Lifecycle hooks and callbacks system
- Agentic loop recipe for exploration workflows
- Step factory and fluent builder patterns
- Enhanced error handling and validation

### Changed
- Improved step execution request handling
- Enhanced backend dispatch for nested steps
- Better context passing between pipeline components
- Updated documentation and examples
- Improved type safety and validation

### Fixed
- Step output handling issues
- Parameter detection cache for unhashable callables
- Agent wrapper compatibility with Pydantic models
- Various linting and formatting issues

## [0.3.6] - 2024-01-XX

### Fixed
- Changelog generation and version management
- Documentation formatting and references

## [0.3.5] - 2024-01-XX

### Fixed
- Workflow syntax and version management

## [0.3.4] - 2024-01-XX

### Added
- Initial release with core orchestration features

## [0.3.3] - 2024-01-XX

### Added
- Basic pipeline execution framework

## [0.3.2] - 2024-01-XX

### Added
- Initial project structure and core components

```

### File: `cohortgen/.venv/share/doc/flujo/README.md`
<a name="cohortgen-venv-share-doc-flujo-readmemd"></a>
```markdown
<div align="center">
  <a href="https://github.com/aandresalvarez/flujo">
    <img src="https://raw.githubusercontent.com/aandresalvarez/flujo/main/assets/flujo.png" alt="Flujo logo" width="180"/>
  </a> 
  
  <h1>Flujo — Your Conversational AI Workflow Server</h1>
  
  <p>
    <b>Go from a simple idea to a production-grade, auditable AI pipeline in a single conversation.</b>
  </p>

| CI/CD | PyPI | Docs | License |
| :---: | :---: | :---: | :---: |
| [![CI status](https://github.com/aandresalvarez/flujo/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aandresalvarez/flujo/actions/workflows/ci.yml) | [![PyPI version](https://img.shields.io/pypi/v/flujo.svg)](https://pypi.org/project/flujo/) | [![Documentation Status](https://readthedocs.org/projects/flujo/badge/?version=latest)](https://flujo.readthedocs.io/en/latest/?badge=latest) | [![License](https://img.shields.io/pypi/l/flujo.svg)](https://github.com/aandresalvarez/flujo/blob/main/LICENSE) |

</div>
---

## The Flujo Experience: Idea to Production in 3 Commands

Imagine you need to automate a task: "Summarize a web article, translate it to Spanish, and post it to our company's Slack." With traditional tools, this is hours of coding, testing, and deploying.

**With Flujo, it's a conversation.**

#### **Step 1: Initialize a Project**

Create and enter a new project directory, then scaffold it:

```bash
mkdir weekly-bot && cd weekly-bot
flujo init
```

Re-initialize an existing project (overwriting templates):

```bash
# Prompt for confirmation
flujo init --force

# Non-interactive (CI/scripts):
flujo init --force --yes
```

#### **Step 2: Tell Flujo Your Goal**

Start a conversation with the Flujo Architect from inside your project:

```bash
flujo create --goal "Summarize a web article, translate it to Spanish, and post to Slack."
```
> **Flujo Architect:** `Understood. To post to Slack, I have a 'post_to_slack' tool. Which channel should I use?`

#### **Step 2: Clarify and Confirm**

Provide the missing details. The Architect confirms the plan.

```bash
> #daily_news_es
```
> **Flujo Architect:** `Great. I've designed a 3-step pipeline: FetchArticle → SummarizeAndTranslate → PostToSlack. I've generated pipeline.yaml for you. It is ready to run.`

In seconds, Flujo has generated a complete, secure, and production-ready YAML blueprint. No code written. No complex configuration.

For details on the new programmatic Architect that powers `flujo create`, see:
- `flujo/architect/README.md` (usage, states, extension points)

#### **Step 3: Run and Inspect**

Execute your new pipeline. Flujo handles the orchestration, cost tracking, and logging automatically.

```bash
flujo run --input "https://flujo-ai.dev/blog/some-article"
```
Every run is saved. If something goes wrong, you have a complete, replayable trace.
```bash
# Get a visual trace of the last run to see exactly what happened
flujo lens trace <run_id>

# Replay a failed production run locally for perfect debugging
flujo lens replay <run_id>
```

**This is the core of Flujo:** a framework that uses AI to build AI, guided by you, and governed by production-ready safety rails.

---

## What Makes This Possible?

Flujo is not just a scripting library; it's a complete application server for AI workflows, built on a few core principles:

| Principle | How Flujo Delivers |
| :--- | :--- |
| **Declarative Blueprints** | Your entire workflow—agents, prompts, tools, and logic (`parallel`, `loops`)—is defined in a single, human-readable **YAML file**. This is the source of truth that the Architect Agent generates and the Runner executes. |
| **Safety by Design** | The framework is built around **proactive Quotas** and **centralized Budgets**. A pipeline cannot start if it might exceed its budget, and parallel steps can't create race conditions that lead to overspending. |
| **Auditability as a Contract** | Every execution produces a **formal, structured trace**. This isn't just logging; it's a deterministic ledger that enables 100% faithful replay, making bugs transparent and easy to fix. |
| **Extensibility via Skills** | Add new capabilities (Python functions, API clients) to a central **Skill Registry**. The Architect Agent can discover and intelligently wire these skills into the pipelines it generates, allowing you to safely grant AI new powers. |

---

## For Developers: The Power Under the Hood

While the CLI provides a no-code experience, Flujo offers a powerful, type-safe Python DSL for developers who need full control.

**Example: A Simple Translation Agent & Pipeline**
```python
# translate_pipeline.py
from pydantic import BaseModel
from flujo import Step, Pipeline, make_agent_async

class Translation(BaseModel):
    original_text: str
    translated_text: str
    language: str

# 1. Define an agent with a structured, Pydantic-validated output
translator_agent = make_agent_async(
    model="openai:gpt-4o",
    system_prompt="Translate the user's text into French.",
    output_type=Translation,
)

# 2. Compose your pipeline with the `>>` operator
pipeline = Step(name="TranslateToFrench", agent=translator_agent)
```
Your Python-defined pipelines get all the same benefits: automatic CLI generation, budget enforcement, and full traceability.

---

## Installation & Getting Started

**Install Flujo:**
```bash
pip install flujo
```

**Install with Extras (e.g., for specific LLM providers):**
```bash
pip install flujo[openai,anthropic,prometheus]
```

**Configure your API Keys:**
```bash
export OPENAI_API_KEY="sk-..."
```

For full guides, tutorials, and API references, please see our **[Official Documentation](https://flujo.readthedocs.io/)**.

Looking to use GPT‑5 with the Architect? See the guide: `docs/guides/gpt5_architect.md`.

---

## CLI Overview

- `init`: ✨ Initialize a new Flujo workflow project in this directory.
- `create`: 🤖 Start a conversation with the AI Architect to build your workflow.
- `run`: 🚀 Run the workflow in the current project.
- `lens`: 🔍 Inspect, debug, and trace past workflow runs.
  - `lens trace <run_id>` now shows prompt injection events per step (redacted preview). Use this to inspect how conversational history was rendered.
- `dev`: 🛠️ Access advanced developer and diagnostic tools.
  - `validate`, `show-steps`, `visualize`, `compile-yaml`, `show-config`, `version`
  - `experimental`: advanced tools like `solve`, `bench`, `add-case`, `improve`

### CLI Flags & Exit Codes (Quick Reference)

- Global flags:
  - `--project PATH`: Set project root and inject into `PYTHONPATH` (imports like `skills.*`).
  - `-v/--verbose`, `--trace`: Show full tracebacks.
- `validate`:
  - Strict-by-default (`--no-strict` to relax), `--format=json` for CI parsers.
- `run`:
  - `--dry-run` validates without executing (with `--json`, prints steps).
- Stable exit codes: `0` OK, `1` runtime, `2` config, `3` import, `4` validation failed, `130` SIGINT.

See the detailed reference: `docs/reference/cli.md`.

---

## CLI Input Piping (Non‑Interactive Usage)

Flujo supports standard Unix piping and env-based input for `flujo run`.

Input resolution precedence:
1) `--input VALUE` (if `VALUE` is `-`, read from stdin)
2) `FLUJO_INPUT` environment variable
3) Piped stdin (non‑TTY)
4) Empty string fallback

Examples:
```bash
# Pipe goal via stdin
echo "Summarize this" | uv run flujo run

# Read stdin explicitly via '-'
uv run flujo run --input - < input.txt

# Use environment variable
FLUJO_INPUT='Translate this to Spanish' uv run flujo run

# Run a specific pipeline file
printf 'hello' | uv run flujo run path/to/pipeline.yaml
```

---

## Conversational Loops (Zero‑Boilerplate)

Enable iterative, state‑aware conversations in loops using an opt‑in flag. Flujo automatically captures turns, injects conversation history into prompts, and surfaces a sanitized preview in `lens trace`.

Quick start:
```yaml
- kind: loop
  name: clarify
  loop:
    conversation: true
    history_management:
      strategy: truncate_tokens
      max_tokens: 4096
    body:
      - kind: step
        name: clarify
```

Advanced controls:
- `ai_turn_source`: `last` (default) | `all_agents` | `named_steps`
- `user_turn_sources`: include `'hitl'` and/or step names (e.g., `['hitl','ask_user']`)
- `history_template`: custom rendering

Use the `--wizard` flags to scaffold conversational loops with presets:
```bash
uv run flujo create \
  --wizard \
  --wizard-pattern loop \
  --wizard-conversation \
  --wizard-ai-turn-source all_agents \
  --wizard-user-turn-sources hitl,clarify \
  --wizard-history-strategy truncate_tokens \
  --wizard-history-max-tokens 4096
```

See `docs/conversational_loops.md` for details.

These semantics are implemented in the CLI layer only; policies and domain logic must not read from stdin or environment directly.

---

## Architect Pipeline Toggles

Control how the Architect pipeline is built (state machine vs. minimal) using environment variables:

- FLUJO_ARCHITECT_STATE_MACHINE=1: Force the full state-machine Architect.
- FLUJO_ARCHITECT_IGNORE_CONFIG=1: Ignore project config and use the minimal single-step generator.
- FLUJO_TEST_MODE=1: Test mode; behaves like ignore-config to keep unit tests deterministic.

Precedence: FLUJO_ARCHITECT_STATE_MACHINE → FLUJO_ARCHITECT_IGNORE_CONFIG/FLUJO_TEST_MODE → flujo.toml ([architect].state_machine_default) → minimal default.

---

## State Backend Configuration

Flujo persists workflow state (for traceability, resume, and lens tooling) via a pluggable state backend.

- Templates (init/demo): default to `state_uri = "memory://"` so projects don’t persist state unless you opt in.
- Core default when not using a project template: SQLite at `sqlite:///flujo_ops.db` (created in CWD) or as configured in `flujo.toml`.
- Ephemeral (in-memory): set one of the following to avoid any persistent files (handy for demos or CI):
  - In `flujo.toml`: `state_uri = "memory://"`
  - Env var: `FLUJO_STATE_URI=memory://`
  - Env var: `FLUJO_STATE_MODE=memory` or `FLUJO_STATE_MODE=ephemeral`
  - Env var: `FLUJO_EPHEMERAL_STATE=1|true|yes|on`

Examples:
```bash
# One-off ephemeral run
FLUJO_STATE_URI=memory:// flujo create --goal "Build a pipeline"

# Project-wide (recommended for demos)
echo 'state_uri = "memory://"' >> flujo.toml
```

When using persistent SQLite, ensure the containing directory exists and is writable (see `flujo/cli/config.py` for path normalization and validation).

---

## License

Flujo is available under a dual-license model:

*   **AGPL-3.0:** For open-source projects and non-commercial use, Flujo is licensed under the AGPL-3.0. See the [`LICENSE`](LICENSE) file for details.
*   **Commercial License:** For commercial use in proprietary applications, a separate commercial license is required. Please contact [Your Contact Email/Website] for more information.

```

## Folder: scripts

### File: `cohortgen/scripts/update_flujo.py`
<a name="cohortgen-scripts-update_flujopy"></a>
```python
#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path


PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
FLUJO_REPO = "https://github.com/aandresalvarez/flujo.git"
FLUJO_REF = "refs/heads/main"


def get_latest_commit(repo: str, ref: str) -> str:
    out = subprocess.check_output(["git", "ls-remote", repo, ref], text=True).strip()
    if not out:
        raise RuntimeError(f"No refs found for {repo} {ref}")
    sha = out.split()[0]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError(f"Invalid SHA from ls-remote: {sha}")
    return sha


def update_pyproject_rev(pyproject: Path, new_sha: str) -> bool:
    text = pyproject.read_text()
    # Match the flujo source line and capture current rev
    pattern = re.compile(
        r"^(\s*flujo\s*=\s*\{[^\n}]*rev\s*=\s*\")([0-9a-f]{40})(\"[^\n}]*\}\s*)$",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        raise RuntimeError("Could not find flujo source with a rev in pyproject.toml")
    current = m.group(2)
    if current == new_sha:
        return False
    new_text = pattern.sub(r"\g<1>" + new_sha + r"\g<3>", text, count=1)
    pyproject.write_text(new_text)
    return True


def main() -> int:
    new_sha = get_latest_commit(FLUJO_REPO, FLUJO_REF)
    changed = update_pyproject_rev(PYPROJECT, new_sha)
    if changed:
        print(f"Updated flujo rev to {new_sha}")
    else:
        print("flujo rev already up-to-date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

## Folder: .github

## Folder: .github/workflows

### File: `cohortgen/.github/workflows/auto-update-flujo.yml`
<a name="cohortgen-github-workflows-auto-update-flujoyml"></a>
```yaml
name: Auto-update flujo

on:
  schedule:
    - cron: '0 6 * * 1' # Mondays at 06:00 UTC
  workflow_dispatch: {}

permissions:
  contents: write
  pull-requests: write

jobs:
  update-flujo:
    runs-on: ubuntu-latest
    steps:
      - name: Check out
        uses: actions/checkout@v4

      - name: Set up uv
        uses: astral-sh/setup-uv@v3

      - name: Update flujo revision
        run: |
          python scripts/update_flujo.py
        shell: bash

      - name: Install and test
        run: |
          uv sync --python 3.11
          uv run pytest -q

      - name: Create Pull Request
        if: ${{ success() }}
        uses: peter-evans/create-pull-request@v6
        with:
          branch: chore/update-flujo
          commit-message: "chore(deps): bump flujo rev"
          title: "chore(deps): bump flujo rev"
          body: |
            Automated update of the `flujo` Git dependency to the latest commit on `main`.

            - Updated `pyproject.toml` with new `rev`
            - Ran `uv sync` and tests successfully
          signoff: false
          delete-branch: true


```

### File: `cohortgen/.github/workflows/ci.yml`
<a name="cohortgen-github-workflows-ciyml"></a>
```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - name: Check out
        uses: actions/checkout@v4

      - name: Set up uv
        uses: astral-sh/setup-uv@v3

      - name: Sync environment
        run: uv sync --python 3.11

      - name: Run tests
        run: uv run pytest -q

```

## Folder: src

### File: `cohortgen/src/sitecustomize.py`
<a name="cohortgen-src-sitecustomizepy"></a>
```python
"""
Lightweight path helper for Flujo projects.

When Python starts, it imports this module automatically if present on sys.path.
We detect if the current shell directory looks like a Flujo project (has
`flujo.toml` or `pipeline.yaml`) and ensure that directory is on `sys.path`.

This makes `import skills` work when users run `flujo` directly inside a
project directory, without needing to set PYTHONPATH manually.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_flujo_project_root(start: Path) -> Path | None:
    for p in [start, *start.parents]:
        if (p / "flujo.toml").exists() or (p / "pipeline.yaml").exists():
            return p
    return None


def _ensure_project_on_sys_path() -> None:
    # Prefer the shell's original working directory. If unavailable, fall back
    # to the current process cwd.
    pwd = os.environ.get("PWD")
    start = Path(pwd) if pwd else Path.cwd()
    project = _find_flujo_project_root(start)
    if not project:
        return

    proj_str = str(project)
    # Insert the absolute project path at the front to avoid being affected if
    # downstream tooling changes cwd later.
    if proj_str not in sys.path:
        sys.path.insert(0, proj_str)


try:
    _ensure_project_on_sys_path()
except Exception:
    # Never block interpreter startup due to path helper issues.
    pass

```

## Folder: src/cohortgen

### File: `cohortgen/src/cohortgen/__init__.py`
<a name="cohortgen-src-cohortgen-__init__py"></a>
```python
__all__: list[str] = []
__version__ = "0.1.0"

```

### File: `cohortgen/src/cohortgen/__main__.py`
<a name="cohortgen-src-cohortgen-__main__py"></a>
```python
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())

```

### File: `cohortgen/src/cohortgen/cli.py`
<a name="cohortgen-src-cohortgen-clipy"></a>
```python
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import __version__

ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT / "projects"


def _run(cmd: list[str], cwd: Path | None = None) -> int:
    env = os.environ.copy()
    if cwd is not None:
        # Ensure project-local Python packages (e.g., skills/) are importable
        pp = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(cwd) if not pp else f"{str(cwd)}{os.pathsep}{pp}"
    return subprocess.call(cmd, cwd=str(cwd) if cwd else None, env=env)


def cmd_list(_: argparse.Namespace) -> int:
    PROJECTS_DIR.mkdir(exist_ok=True)
    found = []
    for p in sorted(PROJECTS_DIR.iterdir() if PROJECTS_DIR.exists() else []):
        if not p.is_dir():
            continue
        if (p / "flujo.toml").exists():
            found.append(p.name)
    if not found:
        print("No Flujo projects found under 'projects/'.")
    else:
        print("Projects:")
        for name in found:
            print(f"- {name}")
    return 0


def cmd_init(ns: argparse.Namespace) -> int:
    name = ns.name
    PROJECTS_DIR.mkdir(exist_ok=True)
    target = PROJECTS_DIR / name
    target.mkdir(parents=True, exist_ok=True)
    rc = _run(["flujo", "init"], cwd=target)
    return rc


def cmd_run(ns: argparse.Namespace) -> int:
    name = ns.name
    target = PROJECTS_DIR / name
    if not (target / "flujo.toml").exists():
        print(
            f"Project '{name}' not found or not initialized under 'projects/'.",
            file=sys.stderr,
        )
        return 2
    # Pass through additional args after --
    extra = ns.args or []
    cmd = ["flujo", "run", *extra]
    return _run(cmd, cwd=target)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cohortgen", description="Manage multiple Flujo subprojects."
    )
    p.add_argument("--version", action="version", version=f"cohortgen {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_list = sub.add_parser("list", help="List Flujo projects under 'projects/'.")
    s_list.set_defaults(func=cmd_list)

    s_init = sub.add_parser(
        "init", help="Initialize a new Flujo project under 'projects/<name>'."
    )
    s_init.add_argument("name", help="Project name")
    s_init.set_defaults(func=cmd_init)

    s_run = sub.add_parser("run", help="Run a Flujo project by name.")
    s_run.add_argument("name", help="Project name")
    s_run.add_argument(
        "args", nargs=argparse.REMAINDER, help="Args passed to 'flujo run' after --"
    )
    s_run.set_defaults(func=cmd_run)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":
    raise SystemExit(main())

```
