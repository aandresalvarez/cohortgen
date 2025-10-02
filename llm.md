# Flujo LLM Guide: Creating AI Workflows

**Purpose**: This guide helps LLMs understand Flujo's syntax, structure, and patterns to create production-ready AI workflow pipelines.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Project Structure](#project-structure)
3. [YAML Pipeline Syntax](#yaml-pipeline-syntax)
4. [Agent Definitions](#agent-definitions)
5. [Step Types Reference](#step-types-reference)
6. [Template System & Expressions](#template-system--expressions)
7. [Configuration (flujo.toml)](#configuration-flujotoml)
8. [Common Patterns](#common-patterns)
9. [CLI Commands](#cli-commands)
10. [Quick Reference](#quick-reference)
11. [Best Practices](#best-practices)
12. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
13. [Troubleshooting](#troubleshooting)
14. [Debugging Workflows](#debugging-workflows)
15. [Summary](#summary)

---

## Core Concepts

### What is Flujo?

Flujo is a framework for building AI workflows using declarative YAML pipelines. Key principles:

- **Declarative**: Define workflows in YAML, not code
- **Type-Safe**: Strict validation with Pydantic schemas
- **Auditable**: Every execution is traced and replayable
- **Budget-Aware**: Proactive cost controls and quota management
- **Composable**: Modular pipelines via imports

### Key Terms

- **Pipeline**: A sequence of steps that process input to produce output
- **Step**: A single unit of work (LLM call, API request, conditional, loop, etc.)
- **Agent**: An LLM configured with a model, prompt, and output schema
- **Context**: Shared state passed between steps
- **Skill**: A reusable function/tool (built-in or custom)

---

## Project Structure

### Recommended Layout

```
my-project/
├── flujo.toml              # Project configuration
├── pipeline.yaml           # Main pipeline definition
├── agents.yaml             # (Optional) Separate agent definitions
├── skills/                 # (Optional) Custom Python skills
│   ├── __init__.py
│   └── helpers.py
├── imports/                # (Optional) Reusable sub-pipelines
│   ├── clarification.yaml
│   └── validation.yaml
└── .flujo/
    └── flujo_ops.db       # State persistence (auto-created)
```

### Initialization

```bash
# Create a new project
mkdir my-project && cd my-project
flujo init

# Generate pipeline via AI architect
flujo create --goal "Your workflow description"

# Run the pipeline
flujo run --input "Your input data"
```

---

## YAML Pipeline Syntax

### Basic Structure

Every Flujo pipeline follows this structure:

```yaml
version: "0.1"                    # Required: API version
name: "my_pipeline"               # Optional: Pipeline name

agents:                           # Optional: Inline agent definitions
  my_agent:
    model: "openai:gpt-4o"
    system_prompt: "You are..."
    output_schema: {...}

imports:                          # Optional: Import other pipelines
  sub_workflow: "./sub.yaml"

steps:                            # Required: List of steps
  - kind: step
    name: first_step
    uses: agents.my_agent
```

### Required Fields

- `version`: Must be `"0.1"`
- `steps`: Array of step definitions (at least one)

### Optional Top-Level Fields

- `name`: Pipeline identifier
- `agents`: Inline agent definitions
- `imports`: External pipeline imports

---

## Agent Definitions

### Basic Agent

```yaml
agents:
  text_processor:
    model: "openai:gpt-4o"                # Required: Model identifier
    system_prompt: "Process text..."      # Required: Instructions
    output_schema:                        # Recommended: Output structure
      type: object
      properties:
        result: { type: string }
        confidence: { type: number }
      required: [result]
```

### Agent Properties

| Property | Required | Description | Example |
|----------|----------|-------------|---------|
| `model` | Yes | LLM identifier | `"openai:gpt-4o"`, `"anthropic:claude-3-5-sonnet"` |
| `system_prompt` | Yes | Agent instructions | `"You are a data analyst..."` |
| `output_schema` | No | JSON Schema for output | `{ type: object, properties: {...} }` |
| `model_settings` | No | Provider-specific config | `{ reasoning: { effort: "high" } }` (GPT-5) |
| `timeout` | No | Execution timeout (seconds) | `180` |
| `max_retries` | No | Retry attempts | `3` |

### Advanced Agent (GPT-5)

```yaml
agents:
  advanced_analyzer:
    model: "openai:gpt-5"
    model_settings:
      reasoning: { effort: "high" }       # GPT-5: Reasoning effort (low/medium/high)
      text: { verbosity: "medium" }       # GPT-5: Response verbosity (low/medium/high)
    system_prompt: |
      You are an expert data analyst.
      Analyze the input and provide structured insights.
    output_schema:
      type: object
      properties:
        insights: { type: array, items: { type: string } }
        confidence: { type: number, minimum: 0, maximum: 1 }
      required: [insights, confidence]
```

**GPT-5 Model Settings:**
- `reasoning.effort`: Controls reasoning depth - `"low"`, `"medium"`, or `"high"`
- `text.verbosity`: Controls response detail - `"low"`, `"medium"`, or `"high"`

**Note:** For GPT-5-mini, use the same format:
```yaml
agents:
  fast_analyzer:
    model: "openai:gpt-5-mini"
    model_settings:
      reasoning: { effort: "medium" }
```

### Tool-Calling Agent

Agents can call external tools/functions to gather information or perform actions.

```yaml
agents:
  research_agent:
    model: "openai:gpt-4o"
    system_prompt: |
      You are a research assistant. Use available tools to answer questions.
      Output JSON with: {"action": "tool" | "finish", "tool_name": str?, "tool_input": object?}
    tools:
      - "skills.my_tools:search_database"
      - "skills.my_tools:fetch_api"
      - "skills.my_tools:calculate"
    output_schema:
      type: object
      properties:
        action: { type: string, enum: [tool, finish] }
        tool_name: { type: string }
        tool_input: { type: object }
      required: [action]
```

**Key Points:**
- `tools`: List of Python callable paths (module:function format)
- Agent decides which tool to call based on context
- Use with loops for multi-step agentic workflows
- Tools must accept dict/str input and return dict/str output

**Example Tool Implementation:**
```python
# skills/my_tools.py
async def search_database(query: dict | str) -> dict:
    search_term = query.get("term") if isinstance(query, dict) else query
    results = # ... your search logic
    return {"success": True, "results": results}
```

---

## Step Types Reference

### 1. Basic Step (`kind: step`)

Execute a single operation (LLM call, API request, etc.).

```yaml
- kind: step
  name: process_data                    # Required: Step name
  uses: agents.my_agent                 # Required: Agent reference
  input: "{{ context.raw_data }}"       # Optional: Templated input
  updates_context: true                 # Optional: Merge output to context
  config:                               # Optional: Step configuration
    max_retries: 3
    timeout_s: 60
  fallback:                             # Optional: Fallback step
    kind: step
    name: backup_processor
    uses: agents.backup_agent
```

**Important:** While Flujo allows implicit `kind: step` (omitting the `kind` field), **always declare it explicitly** for clarity and maintainability.

```yaml
# ❌ Implicit (works but discouraged)
- name: process_data
  uses: agents.my_agent

# ✅ Explicit (recommended)
- kind: step
  name: process_data
  uses: agents.my_agent
```

**Use Cases**: LLM calls, data processing, API interactions

### 2. Parallel Step (`kind: parallel`)

Execute multiple branches concurrently.

```yaml
- kind: parallel
  name: parallel_analysis
  merge_strategy: context_update        # How to merge branch results
  on_branch_failure: ignore             # How to handle failures
  context_include_keys: ["user_id"]     # Limit context passed to branches
  branches:
    sentiment:
      - kind: step
        name: analyze_sentiment
        uses: agents.sentiment_analyzer
    keywords:
      - kind: step
        name: extract_keywords
        uses: agents.keyword_extractor
```

**Merge Strategies**:
- `context_update` (default): Safe merge, fails on conflicts
- `overwrite`: Later branches overwrite earlier ones
- `no_merge`: No context merging
- `merge_scratchpad`: Only merge scratchpad dictionaries

**Failure Handling**:
- `propagate` (default): Fail if any branch fails
- `ignore`: Continue with successful branches

**Use Cases**: Independent analysis, fan-out/fan-in patterns

### 3. Conditional Step (`kind: conditional`)

Route execution based on a condition.

```yaml
- kind: conditional
  name: route_by_type
  condition: "pkg.module:my_function"           # Python callable
  # OR
  condition_expression: "previous_step.type"    # Expression language
  default_branch: general                       # Optional fallback
  branches:
    code:
      - kind: step
        name: process_code
        uses: agents.code_processor
    text:
      - kind: step
        name: process_text
        uses: agents.text_processor
    general:
      - kind: step
        name: general_processor
        uses: agents.general_processor
```

**Boolean Conditionals** (true/false branches):

```yaml
- kind: conditional
  name: check_approval
  condition_expression: "{{ context.approved }}"
  branches:
    true:
      - kind: step
        name: proceed
        uses: agents.executor
    false:
      - kind: step
        name: abort
        uses: agents.logger
```

**Use Cases**: Content routing, user role workflows, error handling

### 4. Loop Step (`kind: loop`)

Execute steps repeatedly until a condition is met.

**Basic Loop**:

```yaml
- kind: loop
  name: refinement_loop
  loop:
    body:
      - kind: step
        name: refine
        uses: agents.refiner
    max_loops: 5
    exit_condition: "pkg:is_done"       # Python callable
    # OR
    exit_expression: "context.status == 'complete'"  # Expression
```

**Conversational Loop (Declarative)**:

```yaml
- kind: loop
  name: clarification_loop
  loop:
    conversation: true                  # Enable conversation mode
    history_management:
      strategy: truncate_tokens
      max_tokens: 4096
    body:
      - kind: step
        name: clarify
        uses: agents.clarifier
        updates_context: true
    stop_when: agent_finished           # Natural exit condition
    output:
      text: conversation_history        # Return history as text
```

**Advanced Loop with Mappers**:

```yaml
- kind: loop
  name: agentic_loop
  loop:
    body:
      - kind: step
        name: planner
        uses: agents.planner
      - kind: step
        name: executor
        uses: agents.executor
    initial_input_mapper: "skills:map_initial"      # Transform input
    iteration_input_mapper: "skills:map_iteration"  # Transform between iterations
    loop_output_mapper: "skills:map_final"          # Transform final output
    exit_condition: "skills:is_complete"
    max_loops: 10
```

**Declarative State Management**:

```yaml
- kind: loop
  name: stateful_loop
  loop:
    body: [...]
    max_loops: 5
    init:                                # Run once before first iteration
      - append:
          target: "context.scratchpad.history"
          value: "User: {{ steps.get_goal.output }}"
    state:                               # Run after each iteration
      append:
        - target: "context.scratchpad.history"
          value: "Agent: {{ previous_step }}"
      set:
        - target: "context.summary"
          value: "{{ previous_step }}"
    propagation:
      next_input: context                # How to pass data: context | previous_output | auto
    exit_expression: "context.done == true"
    output_template: "{{ context.scratchpad.history | join('\\n') }}"
```

**Use Cases**: Iterative refinement, conversational AI, agentic workflows

### 5. Map Step (`kind: map`)

Apply a pipeline to each item in a collection.

```yaml
- kind: map
  name: process_items
  map:
    iterable_input: "context.items"     # Path to array in context
    body:
      - kind: step
        name: process_item
        uses: agents.processor
        input: "{{ this }}"              # 'this' = current item
```

**With Hooks**:

```yaml
- kind: map
  name: batch_transform
  map:
    iterable_input: "context.data"
    body: [...]
    init:                                # Run once before mapping
      - set:
          target: "context.scratchpad.count"
          value: "0"
    finalize:                            # Run once after mapping
      output:
        results_str: "{{ previous_step | join(', ') }}"
```

**Use Cases**: Batch processing, collection transformation

### 6. Dynamic Router (`kind: dynamic_router`)

Let an agent decide which branches to execute.

```yaml
- kind: dynamic_router
  name: smart_router
  router:
    router_agent: agents.workflow_router    # Agent returns branch names
    branches:
      billing:
        - kind: step
          name: handle_billing
          uses: agents.billing_handler
      support:
        - kind: step
          name: handle_support
          uses: agents.support_handler
```

**Use Cases**: AI-driven workflow selection, intelligent task delegation

### 7. Human-in-the-Loop (`kind: hitl`)

Pause for human input or approval.

```yaml
- kind: hitl
  name: user_approval
  message: "Please review and approve (yes/no)"
  input_schema:
    type: object
    properties:
      confirmation: { type: string, enum: ["yes", "no"] }
      comments: { type: string }
    required: [confirmation]
```

**Use Cases**: Approval workflows, manual validation, interactive decisions

### 8. State Machine (`kind: StateMachine`)

Drive execution through named states.

```yaml
- kind: StateMachine
  name: workflow_sm
  start_state: analyze
  end_states: [complete]
  states:
    analyze:
      - kind: step
        name: analyze_data
        uses: agents.analyzer
    refine:
      - kind: step
        name: refine_results
        uses: agents.refiner
    complete:
      - kind: step
        name: finalize
        uses: agents.finalizer
```

**Use Cases**: Complex multi-state workflows

### 9. Cache Step (`kind: cache`)

Cache results for identical inputs.

```yaml
- kind: cache
  name: cached_operation
  wrapped_step:
    kind: step
    name: expensive_operation
    uses: agents.expensive_agent
```

**Use Cases**: Expensive operations, rate-limited APIs, deterministic transformations

### 10. Agentic Loop (`kind: agentic_loop`)

Sugar for conversational loops with planning and execution.

```yaml
- kind: agentic_loop
  name: research_loop
  planner: "agents.planner"             # Agent or import path
  registry: "agents.tool_registry"      # Map of tool name → agent
  config:
    max_retries: 5
  output_template: "Result: {{ previous_step.execution_result }}"
```

**Use Cases**: Multi-tool agentic workflows

---

## Template System & Expressions

### Template Variables

Available in `input` fields and expressions:

| Variable | Description | Example |
|----------|-------------|---------|
| `context` | Pipeline context | `{{ context.user_id }}` |
| `previous_step` | Last step's output | `{{ previous_step }}` |
| `steps` | Map of prior steps | `{{ steps.fetch_data.output }}` |
| `this` | Current item (in `map`) | `{{ this }}` |

### Template Filters

Chain filters with `|` to transform values:

```yaml
input: "{{ context.tags | join(', ') }}"        # Join array
input: "{{ previous_step | upper }}"            # Uppercase
input: "{{ context.items | length }}"           # Length
input: "{{ context.data | tojson }}"            # JSON serialization
input: "{{ context.name or 'default' | lower }}" # Fallback + lowercase
```

**Available Filters**: `join(delim)`, `upper`, `lower`, `length`, `tojson`

### Expression Language

For `condition_expression` and `exit_expression`:

**Allowed**:
- Literals: strings, numbers, booleans, `null`
- Names: `previous_step`, `output`, `context`, `steps`
- Operators: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`, `and`, `or`, `not`
- Attribute access: `obj.attr`, `obj['key']`
- Safe methods: `dict.get(key[, default])`, `str.lower()`, `str.upper()`, `str.strip()`, `str.startswith()`, `str.endswith()`

**Examples**:
```yaml
exit_expression: "context.status == 'done'"
condition_expression: "previous_step.lower().startswith('ok')"
exit_expression: "context.scratchpad.get('action', '') == 'finish'"
```

---

## Configuration (flujo.toml)

### Basic Configuration

```toml
## Project configuration

# State persistence (SQLite or memory)
state_uri = "sqlite:///.flujo/flujo_ops.db"
# OR for ephemeral (no persistence)
# state_uri = "memory://"

# Cost tracking
[cost]
strict = false  # Set true to fail on missing model prices

# Model pricing (OpenAI example)
[cost.providers.openai.gpt-4o-mini]
prompt_tokens_per_1k = 0.00015
completion_tokens_per_1k = 0.0006

[cost.providers.openai.gpt-4o]
prompt_tokens_per_1k = 0.005
completion_tokens_per_1k = 0.015

# Optional: Budget limits
[budgets]
[budgets.default]
total_cost_usd_limit = 10.0
total_tokens_limit = 100000

# Optional: Security - allowed imports in YAML
blueprint_allowed_imports = ["skills", "flujo.builtins"]

# Optional: Template filters allowlist
[settings]
enabled_template_filters = ["upper", "lower", "join", "tojson", "length"]

# Optional: Architect mode
[architect]
state_machine_default = false  # Use simple architect by default
```

### Environment Variables

Override config via environment:

```bash
export FLUJO_STATE_URI="memory://"
export FLUJO_COST_STRICT=1
export FLUJO_EPHEMERAL_STATE=1
export OPENAI_API_KEY="sk-..."
```

---

## Common Patterns

### 1. Sequential Processing

```yaml
steps:
  - kind: step
    name: extract
    uses: agents.extractor
    updates_context: true
  
  - kind: step
    name: transform
    uses: agents.transformer
    input: "{{ context.extracted_data }}"
    updates_context: true
  
  - kind: step
    name: load
    uses: agents.loader
    input: "{{ context.transformed_data }}"
```

### 2. Parallel Analysis

```yaml
- kind: parallel
  name: multi_analysis
  merge_strategy: context_update
  branches:
    sentiment:
      - kind: step
        name: sentiment
        uses: agents.sentiment_analyzer
    entities:
      - kind: step
        name: entities
        uses: agents.entity_extractor
    summary:
      - kind: step
        name: summary
        uses: agents.summarizer
```

### 3. Error Handling with Fallback

```yaml
- kind: step
  name: primary_task
  uses: agents.primary
  config:
    max_retries: 3
    timeout_s: 60
  fallback:
    kind: step
    name: backup_task
    uses: agents.backup
```

### 4. Conditional Routing

```yaml
- kind: conditional
  name: route_by_language
  condition_expression: "context.language"
  branches:
    en:
      - kind: step
        name: process_english
        uses: agents.en_processor
    es:
      - kind: step
        name: process_spanish
        uses: agents.es_processor
```

### 5. Conversational Loop

```yaml
- kind: step
  name: get_goal
  agent:
    id: "flujo.builtins.ask_user"
  input: "What is your goal?"

- kind: loop
  name: clarify
  loop:
    conversation: true
    history_management:
      strategy: truncate_tokens
      max_tokens: 4096
    body:
      - kind: step
        name: clarify_goal
        uses: agents.clarifier
        updates_context: true
    stop_when: agent_finished
    output:
      text: conversation_history
```

### 6. Batch Processing

```yaml
- kind: step
  name: fetch_items
  uses: agents.fetcher
  updates_context: true

- kind: map
  name: process_batch
  map:
    iterable_input: "context.items"
    body:
      - kind: step
        name: process_item
        uses: agents.item_processor
        input: "{{ this }}"
```

### 7. Approval Workflow

```yaml
- kind: step
  name: generate_content
  uses: agents.generator
  updates_context: true

- kind: hitl
  name: approval
  message: "Approve content? (yes/no)"
  input_schema:
    type: object
    properties:
      approved: { type: boolean }
    required: [approved]

- kind: conditional
  name: check_approval
  condition_expression: "previous_step.approved"
  branches:
    true:
      - kind: step
        name: publish
        uses: agents.publisher
    false:
      - kind: step
        name: reject
        uses: agents.rejector
```

### 8. Pipeline Composition with Imports

```yaml
# main.yaml
version: "0.1"
imports:
  clarification: "./clarification.yaml"
  generation: "./generation.yaml"

steps:
  - kind: step
    name: clarify
    uses: imports.clarification
    updates_context: true
    config:
      input_to: initial_prompt
      propagate_hitl: true
      outputs:
        - { child: scratchpad.goal, parent: scratchpad.goal }
  
  - kind: step
    name: generate
    uses: imports.generation
    config:
      input_to: scratchpad
      outputs:
        - { child: scratchpad.result, parent: scratchpad.result }
```

### 9. Built-in Data Transforms

```yaml
# Convert list of dicts to CSV
- kind: step
  name: to_csv
  agent:
    id: "flujo.builtins.to_csv"
    params: { headers: ["id", "name", "price"] }
  input: "{{ context.products }}"

# Aggregate numeric values
- kind: step
  name: total_price
  agent:
    id: "flujo.builtins.aggregate"
    params: { operation: "sum", field: "price" }
  input: "{{ context.products }}"

# Select/rename fields
- kind: step
  name: project_fields
  agent:
    id: "flujo.builtins.select_fields"
    params:
      include: ["id", "name"]
      rename: { name: "display_name" }
  input: "{{ context.users }}"

# Flatten nested lists
- kind: step
  name: flatten
  agent:
    id: "flujo.builtins.flatten"
  input: "{{ context.nested_data }}"
```

### 10. Built-in Skills Reference

Common built-in skills (use via `agent.id`):

| Skill ID | Purpose | Example |
|----------|---------|---------|
| `flujo.builtins.ask_user` | Get user input | Interactive prompts |
| `flujo.builtins.check_user_confirmation` | Validate approval | Approval workflows |
| `flujo.builtins.stringify` | Convert to string | Type conversion |
| `flujo.builtins.web_search` | Search the web | Information retrieval |
| `flujo.builtins.http_get` | HTTP GET request | API calls |
| `flujo.builtins.fs_write_file` | Write file | File operations |
| `flujo.builtins.extract_from_text` | Extract structured data | Text parsing |
| `flujo.builtins.to_csv` | Convert to CSV | Data export |
| `flujo.builtins.aggregate` | Aggregate numbers | Sum, avg, count |
| `flujo.builtins.select_fields` | Project/rename fields | Data transformation |
| `flujo.builtins.flatten` | Flatten nested lists | List processing |
| `flujo.builtins.passthrough` | Identity function | No-op step |

### 11. Agentic Tool Exploration Pattern

Complex pattern for AI agents that explore and use tools iteratively.

```yaml
# Step 1: Initialize exploration state
- kind: step
  name: parse_input
  uses: "skills.custom:parse_input"
  input: "{{ context.user_query }}"
  updates_context: true

# Step 2: Agentic exploration loop
- kind: loop
  name: exploration_loop
  loop:
    body:
      # Agent decides next action
      - kind: step
        name: decide_action
        uses: agents.explorer_agent  # Tool-calling agent
        input: |
          Current state: {{ context.scratchpad.state | tojson }}
          History: {{ context.scratchpad.history | tojson }}
        updates_context: true
      
      # Execute tool if agent chose one
      - kind: conditional
        name: execute_if_tool
        condition_expression: "previous_step.action == 'tool'"
        branches:
          "true":
            - kind: step
              name: run_tool
              uses: "skills.custom:execute_tool"
              input: "{{ steps.decide_action.output }}"
              updates_context: true
          "false":
            - kind: step
              name: skip
              agent: "flujo.builtins.passthrough"
    
    # Exit when agent signals completion
    exit_expression: "steps['decide_action'].action == 'finish'"
    max_loops: 10

# Step 3: Extract final result
- kind: step
  name: finalize
  uses: "skills.custom:format_output"
  input: "{{ steps.decide_action.output.result }}"
```

**Use Cases**: Research assistants, data discovery, iterative problem-solving

**Real-World Example:** See `projects/concept_discovery/` for production implementation

---

## CLI Commands

### Project Management

```bash
# Initialize project
flujo init

# Generate pipeline via AI
flujo create --goal "Your workflow description"

# Non-interactive creation
flujo create --goal "Summarize news" --non-interactive
```

### Pipeline Execution

```bash
# Run pipeline
flujo run --input "Hello world"

# Run with context data
flujo run --input "Hello" --context-data '{"user_id": "123"}'

# Run with context file
flujo run --input "Hello" --context-file context.json

# Dry run (validate only)
flujo run --dry-run

# Pipe input
echo "Hello" | flujo run
cat input.txt | flujo run --input -
```

### Validation and Inspection

```bash
# Validate pipeline
flujo validate pipeline.yaml

# Show pipeline steps
flujo dev show-steps pipeline.yaml

# Visualize pipeline
flujo dev visualize pipeline.yaml

# Explain pipeline in plain language
flujo explain pipeline.yaml
```

### Tracing and Debugging

```bash
# List recent runs
flujo lens list

# Quick find with partial ID
flujo lens get abc123

# Show run details (supports partial IDs)
flujo lens show abc123

# Show with all details
flujo lens show abc123 --verbose

# Show final output only
flujo lens show abc123 --final-output

# Export as JSON
flujo lens show abc123 --json

# Adjust timeout if needed (default: 30 seconds)
flujo lens show abc123 --timeout 30

# Show execution trace
flujo lens trace <run_id>

# Show detailed spans
flujo lens spans <run_id>

# Replay a run
flujo lens replay <run_id>
```

**Lens Command Features:**
- **Partial ID matching**: Use shortened run IDs (e.g., `abc123` instead of full `run_abc123...`)
- **Multiple output formats**: Text (default), verbose, final output only, or JSON
- **Configurable timeout**: Adjust if inspecting large runs
- **Quick lookup**: Use `get` for fast ID resolution

### Configuration

```bash
# Show current config
flujo dev show-config

# Show version
flujo dev version
```

---

## Quick Reference

### Essential YAML Structure

```yaml
version: "0.1"
name: "my_pipeline"

agents:
  my_agent:
    model: "openai:gpt-4o"
    system_prompt: "Instructions..."
    output_schema:
      type: object
      properties:
        result: { type: string }

steps:
  - kind: step
    name: step1
    uses: agents.my_agent
    input: "{{ context.data }}"
    updates_context: true
    config:
      max_retries: 3
      timeout_s: 60
```

### Common Step Kinds

| Kind | Purpose | Key Feature |
|------|---------|-------------|
| `step` | Single operation | Basic building block (always explicit!) |
| `parallel` | Concurrent branches | Merge strategies |
| `conditional` | Branching logic | Expression or function-based |
| `loop` | Iterative execution | Exit conditions, max_loops |
| `map` | Collection processing | Iterate over collections |
| `dynamic_router` | AI-driven routing | Agent chooses branches |
| `hitl` | Human input | Pause for approval |
| `StateMachine` | State-based workflow | Complex state transitions |
| `cache` | Result caching | Memoization |
| `agentic_loop` | Planning + execution | Tool-calling pattern |

### Template Variables

- `{{ context.field }}` - Access context
- `{{ previous_step }}` - Last step output
- `{{ steps.name.output }}` - Named step output
- `{{ this }}` - Current item (in map)

### Template Filters

- `{{ value | join(', ') }}` - Join array
- `{{ value | upper }}` - Uppercase
- `{{ value | lower }}` - Lowercase
- `{{ value | length }}` - Length
- `{{ value | tojson }}` - JSON encode

### Expression Language

```yaml
condition_expression: "context.status == 'ready'"
exit_expression: "previous_step.action == 'finish'"
condition_expression: "context.count > 5 and context.ready"
```

### Built-in Skills (Common)

```yaml
# User input
agent: { id: "flujo.builtins.ask_user" }

# String conversion
agent: { id: "flujo.builtins.stringify" }

# Web search
agent: { id: "flujo.builtins.web_search", params: { query: "...", max_results: 5 } }

# HTTP request
agent: { id: "flujo.builtins.http_get", params: { url: "..." } }

# File write
agent: { id: "flujo.builtins.fs_write_file", params: { path: "...", content: "..." } }

# Data transforms
agent: { id: "flujo.builtins.to_csv", params: { headers: [...] } }
agent: { id: "flujo.builtins.aggregate", params: { operation: "sum", field: "..." } }
agent: { id: "flujo.builtins.select_fields", params: { include: [...], rename: {...} } }
agent: { id: "flujo.builtins.flatten" }
```

### Configuration Keys (flujo.toml)

```toml
state_uri = "sqlite:///.flujo/flujo_ops.db"
[cost]
strict = false
[cost.providers.openai.gpt-4o]
prompt_tokens_per_1k = 0.005
completion_tokens_per_1k = 0.015
[budgets.default]
total_cost_usd_limit = 10.0
blueprint_allowed_imports = ["skills"]
```

---

## Best Practices

### 1. **Start Simple, Add Complexity**

Begin with basic steps, then add error handling, retries, and fallbacks as needed.

### 2. **Use Descriptive Names**

Names should be action-oriented and clear: `analyze_sentiment`, not `step1`.

### 3. **Leverage Built-in Skills**

Explore `flujo.builtins.*` before creating custom solutions.

### 4. **Define Output Schemas**

Always specify `output_schema` for agents to ensure type safety.

### 5. **Handle Errors Gracefully**

Use `fallback` steps and `max_retries` for critical operations.

### 6. **Optimize Context**

Use `context_include_keys` in parallel steps to limit data copying.

### 7. **Validate Early**

Run `flujo validate` before executing to catch errors.

### 8. **Use Imports for Modularity**

Break complex workflows into reusable sub-pipelines.

### 9. **Test Incrementally**

Test each step independently before composing complex workflows.

### 10. **Monitor Costs**

Set budget limits in `flujo.toml` and enable `strict = true` for production.

### 11. **Write Type-Safe Custom Skills**

Always use type hints and handle multiple input formats:

```python
# skills/my_tools.py
from typing import Any, Dict

async def my_skill(input_data: Dict[str, Any] | str) -> Dict[str, Any]:
    """Process input data robustly.
    
    Accepts dict or JSON string for flexibility.
    """
    # Normalize input
    if isinstance(input_data, str):
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            data = {"raw": input_data}
    else:
        data = input_data
    
    # Process with error handling
    try:
        result = process(data)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 12. **Implement Retry Logic for External APIs**

```python
import time

def retry_with_backoff(func, *args, max_attempts=3, delay=0.5, backoff=2.0, **kwargs):
    """Retry function with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise e
            time.sleep(delay)
            delay *= backoff
```

### 13. **Always Declare `kind` Explicitly**

Even though Flujo allows implicit step kinds, always be explicit:

```yaml
# ✅ Good - Clear and maintainable
- kind: step
  name: process
  uses: agents.processor

# ❌ Avoid - Implicit, harder to read
- name: process
  uses: agents.processor
```

### 14. **Use Context Scratchpad for State**

Store intermediate state in `context.scratchpad` to avoid polluting the main context:

```yaml
- kind: step
  name: init_state
  uses: "skills.custom:initialize"
  updates_context: true
  # Returns: {"scratchpad": {"history": [], "count": 0}}
```

### 15. **Test Custom Skills Independently**

Create unit tests for all custom skills:

```python
# tests/test_my_skills.py
import pytest
from skills.my_tools import my_skill

@pytest.mark.asyncio
async def test_my_skill_with_dict():
    result = await my_skill({"input": "test"})
    assert result["success"] is True

@pytest.mark.asyncio
async def test_my_skill_with_string():
    result = await my_skill('{"input": "test"}')
    assert result["success"] is True
```

---

## Anti-Patterns to Avoid

### ❌ Monolithic Steps

Don't combine multiple responsibilities in one step.

### ❌ Hardcoded Values

Use context variables instead of hardcoding URLs, paths, etc.

### ❌ Ignoring Failures

Always consider failure modes and add error handling.

### ❌ Deep Nesting

Avoid deeply nested conditionals; use routers or flatten logic.

### ❌ Missing Schemas

Always define `output_schema` for predictable behavior.

### ❌ Skipping Validation

Always run `flujo validate` before production deployment.

---

## Example: Complete Pipeline

```yaml
version: "0.1"
name: "Content Analysis Pipeline"

agents:
  analyzer:
    model: "openai:gpt-4o"
    system_prompt: |
      You are a content analyst. Extract key insights from text.
    output_schema:
      type: object
      properties:
        sentiment: { type: string, enum: ["positive", "negative", "neutral"] }
        keywords: { type: array, items: { type: string } }
        summary: { type: string }
      required: [sentiment, keywords, summary]

  validator:
    model: "openai:gpt-4o-mini"
    system_prompt: "Validate analysis quality."
    output_schema:
      type: object
      properties:
        valid: { type: boolean }
        reason: { type: string }

steps:
  # 1. Get input
  - kind: step
    name: get_content
    agent:
      id: "flujo.builtins.ask_user"
    input: "Enter content to analyze:"
  
  # 2. Analyze content
  - kind: step
    name: analyze
    uses: agents.analyzer
    input: "{{ previous_step }}"
    updates_context: true
    config:
      max_retries: 3
      timeout_s: 60
    fallback:
      kind: step
      name: simple_analysis
      agent:
        id: "flujo.builtins.extract_from_text"
      input: "Extract sentiment and keywords from: {{ previous_step }}"
  
  # 3. Validate results
  - kind: step
    name: validate
    uses: agents.validator
    input: |
      Validate this analysis:
      {{ context.analyze | tojson }}
  
  # 4. Check if valid
  - kind: conditional
    name: check_validation
    condition_expression: "previous_step.valid"
    branches:
      true:
        - kind: step
          name: save_result
          agent:
            id: "flujo.builtins.fs_write_file"
            params:
              path: "analysis.json"
              content: "{{ context.analyze | tojson }}"
      false:
        - kind: step
          name: log_failure
          agent:
            id: "flujo.builtins.stringify"
          input: "Validation failed: {{ previous_step.reason }}"
```

---

## Summary

This guide covers everything needed to create Flujo pipelines:

- **Project structure**: `flujo.toml`, YAML pipelines, imports
- **YAML syntax**: version, agents, imports, steps
- **Agent definitions**: model, prompts, schemas, settings, tools
- **Step types**: 10+ step kinds for different patterns
- **Templates**: Variables, filters, expressions
- **Patterns**: Sequential, parallel, conditional, loops, agentic exploration
- **CLI**: Create, run, validate, trace, debug
- **Best practices**: Naming, error handling, modularity, testing, type safety

**Key Takeaways**:
1. **Always declare `kind` explicitly** for clarity
2. Define clear output schemas for all agents
3. Use descriptive, action-oriented names
4. Handle errors gracefully with retries and fallbacks
5. Write type-safe custom skills with robust input handling
6. Implement retry logic for external API calls
7. Test custom skills independently with unit tests
8. Use context scratchpad for intermediate state
9. Validate pipelines before running (`flujo validate`)
10. Monitor costs and enable budget limits for production
11. Start simple and add complexity incrementally

**Real-World Examples**:
- **Agentic exploration**: `projects/concept_discovery/` - Tool-calling agent with iterative refinement
- **Sequential workflows**: See patterns in Common Patterns section
- **Approval workflows**: HITL + conditional branching examples

For deeper details, see:
- Full YAML reference: `docs/creating_yaml.md`
- Best practices: `docs/creating_yaml_best_practices.md`
- Team guide: `FLUJO_TEAM_GUIDE.md`
- Examples: `examples/`

---

## Troubleshooting

### Common Issues and Solutions

#### Pipeline Validation Errors

**Problem:** `Invalid step kind` or `Missing required field`

**Solution:**
```bash
# Run strict validation
flujo validate pipeline.yaml --strict

# Check for:
# 1. Missing 'kind' declarations
# 2. Required fields (name, uses, version)
# 3. Valid agent references (agents.name_here)
```

#### Model Settings Not Applied

**Problem:** GPT-5 reasoning settings ignored

**Solution:** Use correct nested format:
```yaml
# ❌ Wrong
model_settings:
  openai_reasoning_effort: "high"

# ✅ Correct
model_settings:
  reasoning: { effort: "high" }
  text: { verbosity: "medium" }
```

#### Context Not Updating

**Problem:** Step output not available in subsequent steps

**Solution:** Add `updates_context: true`:
```yaml
- kind: step
  name: extract_data
  uses: agents.extractor
  updates_context: true  # ← Required to merge output into context
```

#### Loop Never Exits

**Problem:** Infinite loop, hits max_loops

**Solution:** Check exit condition:
```yaml
loop:
  exit_expression: "steps['decision'].action == 'finish'"  # Must match output
  max_loops: 10  # Safety limit
```

Debug by checking step output:
```bash
# List recent runs
flujo lens list

# Get details with partial ID
flujo lens show abc123 --verbose

# Check final output
flujo lens show abc123 --final-output

# See execution trace
flujo lens trace abc123
```

#### Custom Skill Import Errors

**Problem:** `ModuleNotFoundError` or `Skill not found`

**Solution:**
1. Check path format: `"skills.module_name:function_name"`
2. Ensure `skills/__init__.py` exists
3. Add to `flujo.toml`:
   ```toml
   blueprint_allowed_imports = ["skills", "flujo.builtins"]
   ```

#### Cost Tracking Warnings

**Problem:** `Missing pricing data for model`

**Solution:** Add explicit pricing in `flujo.toml`:
```toml
[cost.providers.openai.gpt-4o]
prompt_tokens_per_1k = 0.005
completion_tokens_per_1k = 0.015
```

Or disable warnings:
```toml
[cost]
strict = false
```

#### Template Rendering Errors

**Problem:** `Undefined variable` or `Filter not found`

**Solution:**
1. Check variable exists: `{{ context.field_name }}`
2. Use safe access: `{{ context.get('field', 'default') }}`
3. Enable filter in config:
   ```toml
   [settings]
   enabled_template_filters = ["upper", "lower", "join", "tojson", "length"]
   ```

#### Agent Tool Calls Fail

**Problem:** Agent returns tool name but execution fails

**Solution:**
1. Ensure tool exists and is importable
2. Tool must accept dict/str and return dict/str
3. Check output schema matches:
   ```yaml
   output_schema:
     properties:
       action: { enum: [tool, finish] }
       tool_name: { type: string }
       tool_input: { type: object }
   ```

#### Conditional Branch Not Taken

**Problem:** Wrong branch executed or no branch taken

**Solution:**
1. Check condition return type (must be string for branch name)
2. Use quotes for boolean branches: `"true"`, `"false"`
3. Add `default_branch` as fallback:
   ```yaml
   conditional:
     default_branch: fallback
     branches:
       expected_value: [...]
       fallback: [...]
   ```

---

## Debugging Workflows

### Quick Debugging Workflow

When a pipeline fails or produces unexpected results:

```bash
# 1. List recent runs
flujo lens list

# 2. Get quick overview (use partial ID from list)
flujo lens get ec0079

# 3. Show full details with verbose output
flujo lens show ec0079 --verbose

# 4. Check just the final output
flujo lens show ec0079 --final-output

# 5. Export for analysis
flujo lens show ec0079 --json > run_details.json

# 6. Check timing and performance
flujo lens spans ec0079

# 7. See full execution trace
flujo lens trace ec0079
```

### Debugging Specific Issues

**Check step-by-step execution:**
```bash
# Verbose mode shows all step inputs/outputs
flujo lens show <run_id> --verbose
```

**Verify final output:**
```bash
# Quick check of what the pipeline returned
flujo lens show <run_id> --final-output
```

**Performance analysis:**
```bash
# See which steps took longest
flujo lens spans <run_id>
```

**Export for external analysis:**
```bash
# JSON format for scripting/analysis
flujo lens show <run_id> --json | jq '.steps[] | {name: .name, status: .status}'
```

### Tips for Efficient Debugging

1. **Use partial IDs**: Copy first 6+ characters of run_id for faster typing
2. **Start with final output**: Use `--final-output` to quickly verify results
3. **Use JSON export**: Combine with `jq` for powerful filtering
4. **Check spans for performance**: Identify slow steps with `spans` command
5. **Increase timeout for large runs**: Use `--timeout` if needed

---

