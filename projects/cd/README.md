# OMOP Concept Discovery - Pydantic AI Version

**Stage 2: Clinical Text → OMOP Concept IDs**

This tool maps clinical cohort definitions to OMOP standard concepts using ATHENA.

---

## 🎯 What It Does

Takes a cohort definition (from Stage 1 or manual input) and produces ATLAS-compatible concept sets with OMOP concept IDs.

### Workflow:

```
Input: Clinical Cohort Definition
  ↓
[1] Decompose into Concept Sets
  ↓
[2] Search ATHENA for Candidates
  ↓
[3] Agent Explores & Validates
  ↓
Output: ATLAS-Compatible Concept Sets
```

---

## 🔧 Setup

### 1. Install Dependencies

The athena-client is already in your project:

```bash
# From project root
cd /Users/alvaro1/Documents/Coral/Code/cohortgen
uv sync
```

### 2. Set API Key

Your `.env` file should have:

```bash
OPENAI_API_KEY=your-key-here
```

---

## ▶️ How to Run

### Interactive Mode

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen/projects/cd
uv run python find_concepts.py
```

Then paste your cohort definition (or type `demo` for a test).

### Demo Mode

```bash
echo "demo" | uv run python find_concepts.py
```

### Programmatic Use

```python
from find_concepts import run_concept_discovery

cohort_def = """
Adults with type 2 diabetes
- Age 18+
- First diagnosis T2DM
- No prior T1DM
"""

result = run_concept_discovery(cohort_def)
print(result)  # ATLAS-compatible JSON
```

---

## 🧰 Features

### 1. **Smart Decomposition**

Agent analyzes your cohort definition and breaks it into concept sets:

- **Conditions** → SNOMED concepts
- **Medications** → RxNorm concepts
- **Procedures** → SNOMED/CPT4 concepts
- **Labs/Tests** → LOINC concepts

**No placeholders**: Agent generates concrete search queries directly from your text.

### 2. **ATHENA Search**

Uses the `athena-client` library to search public ATHENA:

- Filters by domain (Condition, Drug, etc.)
- Filters by vocabulary (SNOMED, RxNorm, etc.)
- Returns top candidates with metadata

### 3. **Agent-Driven Exploration**

The explorer agent has tools to:

- **`search_athena`**: Find new concepts
- **`get_concept_details`**: Verify concepts are standard
- **`get_concept_relationships`**: Follow "Maps to" links to find standard concepts

**Strategy**:
1. Check 1-2 candidates to verify they're standard
2. If issues found, use relationships to find alternatives
3. Finish quickly (within 3 tool calls)

### 4. **Quality Validation**

Agent ensures concepts are:
- ✅ Standard concepts (`standard_concept = 'S'`)
- ✅ Correct domain (Condition, Drug, etc.)
- ✅ Relevant to clinical intent

### 5. **ATLAS-Compatible Output**

Produces JSON ready for ATLAS import:

```json
{
  "concept_sets": [
    {
      "name": "Type 2 Diabetes",
      "included_concepts": [
        {
          "concept_id": 201826,
          "concept_name": "Type 2 diabetes mellitus",
          "domain_id": "Condition",
          "vocabulary_id": "SNOMED",
          "standard_concept": "S",
          "concept_code": "44054006"
        }
      ],
      "excluded_concepts": []
    }
  ]
}
```

---

## 📊 Example Session

```
$ uv run python find_concepts.py

Enter your cohort definition:
> Adults with newly diagnosed type 2 diabetes

[Step 1] Decomposing...
✅ Decomposed into 2 concept sets:
  1. Type 2 Diabetes (Condition)
     Intent: New diagnosis of type 2 diabetes mellitus
     Queries: type 2 diabetes, T2DM, diabetes mellitus type 2

  2. Adults (Demographics)
     Intent: Age 18 or older
     Queries: adult, age 18+

[Step 2] Searching ATHENA...
✅ Found 15 initial candidates across 2 sets
  - Type 2 Diabetes: 10 candidates
  - Adults: 5 candidates

[Step 3] Agent exploring...

[Exploration 1]
  Action: details
  Reasoning: Checking if top candidates are standard SNOMED concepts

[Exploration 2]
  Action: finish
  Reasoning: Top 5 candidates are all standard SNOMED. Ready to finalize.

✅ Agent finished after 2 exploration steps

[Final Concept Sets]
  - Type 2 Diabetes: 5 concepts
  - Adults: 2 concepts

✅ CONCEPT DISCOVERY COMPLETE
Output is ready for ATLAS import!
No nested loops! Clean exit! 🎉

✅ Saved to: concept_sets_output.json
```

---

## 🔗 Integration with Stage 1

This tool is **Stage 2** in a complete workflow:

### Stage 1: Clinical Clarification (`@clar/`)

```python
from clar.hitl_clarification_working import run_clarification_loop

# Get structured cohort definition in plain text
cohort_def = run_clarification_loop("patients with diabetes")
# Returns: CohortDefinition with clinical text descriptions
```

### Stage 2: Concept Discovery (`@cd/`)

```python
from cd.find_concepts import run_concept_discovery

# Convert plain text to OMOP concept IDs
concept_sets = run_concept_discovery(cohort_def.index_event)
# Returns: ATLAS-compatible concept sets with IDs
```

### Stage 3: ATLAS Generation (Future)

```python
# Generate ATLAS JSON from concept sets
atlas_json = generate_atlas_cohort(cohort_def, concept_sets)
# Returns: Complete ATLAS cohort definition
```

---

## 🛠️ Technical Details

### Architecture

- **Decomposer Agent**: GPT-4o-mini with structured output (ConceptPlan)
- **Explorer Agent**: GPT-4o-mini with tools (search, details, relationships)
- **Tools Module**: Wraps `athena-client` for Pydantic AI
- **No Flujo Dependencies**: Pure Pydantic AI implementation

### Key Files

- **`find_concepts.py`**: Main script with agents and workflow
- **`tools.py`**: Pydantic AI tool wrappers for ATHENA
- **`README.md`**: This file

### Dependencies

- `pydantic-ai>=1.0.15`
- `athena-client` (public ATHENA, no auth required)
- `openai>=2.1.0`
- `python-dotenv`

### Relationship to Flujo Version

This is a **Pydantic AI reimplementation** of `@concept_discovery/pipeline.yaml`.

**Why Pydantic AI?**
- ✅ Native HITL support without nested loop bugs
- ✅ Simpler tool integration
- ✅ Easier to debug and extend
- ✅ More flexible for complex workflows

**Same Capabilities**:
- ✅ Smart concept decomposition
- ✅ ATHENA search with filtering
- ✅ Relationship exploration
- ✅ Quality validation
- ✅ ATLAS-compatible output

---

## 📝 Notes

### ATHENA Client

- Uses public ATHENA (no authentication required)
- Robust error handling and retries
- Supports all OMOP vocabularies

### Concept Standards

- Focuses on **Standard concepts** (`standard_concept = 'S'`)
- Follows **"Maps to"** relationships to find standard concepts
- Filters by **domain** and **vocabulary**

### Performance

- Typically 2-3 exploration steps
- ~10-30 seconds per cohort definition
- Caches search results in exploration context

---

## 🎯 Status

✅ **Complete and Ready**

- ✅ Full ATHENA integration
- ✅ Agent-driven exploration
- ✅ Quality validation
- ✅ ATLAS-compatible output
- ✅ No nested loop bugs
- ✅ Clean, maintainable code

**Next Steps**: Integrate with Stage 1 (clinical clarification) and Stage 3 (ATLAS generation).

---

## 🔗 Related Projects

- **Stage 1**: `/projects/clar/` - Clinical text clarification
- **Flujo Version**: `/projects/concept_discovery/` - Original Flujo pipeline
- **Main Project**: Root `/` - CohortGen full system


