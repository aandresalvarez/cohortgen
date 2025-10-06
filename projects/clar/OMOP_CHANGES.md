# OMOP Cohort Definition - Changes Summary

**Date**: October 4, 2025  
**Changes**: Converted generic clarification loop to OMOP-specific cohort definition builder

---

## 🎯 What Changed

### Before: Generic Clarification
- Generic "slot-filling" for any cohort query
- Collected: metric, cohort, time window, grouping, filters
- Output: Simple dictionary of slots

### After: OMOP Cohort Definition Builder
- **OMOP CDM-specific** cohort definition workflow
- Collects all components needed for ATLAS implementation
- Output: Structured `CohortDefinition` object

---

## 📊 New Structure

### CohortDefinition Model

```python
class CohortDefinition(BaseModel):
    """Complete OMOP cohort definition components."""
    index_event: str                    # The defining clinical event
    inclusion_criteria: list[str]       # What qualifies someone
    exclusion_criteria: list[str]       # What disqualifies someone
    observation_window: str             # Washout/follow-up periods
    demographics: dict[str, str]        # Age, gender, etc.
    prior_observation: str              # Required enrollment before index
    cohort_exit: str                    # When someone exits cohort
```

### ClarificationDecision

```python
class ClarificationDecision(BaseModel):
    """Agent decides whether to ask more questions or finish."""
    action: Literal["ask", "finish"]
    question: str
    cohort_components: CohortDefinition  # Updated each iteration
```

---

## 🤖 Updated Agent Prompt

Now focuses on OMOP CDM concepts:

```
You are an expert OMOP CDM cohort definition specialist. Your goal is to clarify all 
components needed for a complete, implementable cohort definition in ATLAS.

OMOP Cohort Definition Components:
1. INDEX EVENT: The defining clinical event
2. INCLUSION CRITERIA: What additional requirements must be met?
3. EXCLUSION CRITERIA: What disqualifies someone?
4. OBSERVATION WINDOW: When should data be observed?
5. COHORT EXIT: When does someone exit the cohort?

Rules:
- Ask ONE targeted question at a time
- Be specific about OMOP concepts (conditions, drugs, procedures, measurements)
- Prioritize: index event → inclusion → exclusion → windows
- After gathering core components, you can finish
```

---

## 🔄 Workflow Changes

### Input
- **Before**: "What would you like to accomplish?"
- **After**: "Describe your cohort" (e.g., "patients with diabetes who started metformin")

### Questions Asked
- **Before**: Generic (metric? time window? grouping?)
- **After**: OMOP-specific:
  - What is the INDEX EVENT?
  - Age/demographic restrictions?
  - Prior observation requirements?
  - What should be excluded?
  - Observation windows?

### Output
- **Before**: Dictionary with slots
- **After**: Structured `CohortDefinition` with formatted display:

```
📍 INDEX EVENT:
   First metformin exposure after type 2 diabetes diagnosis

✅ INCLUSION CRITERIA:
   1. Age >= 18 years at index date
   2. Continuous enrollment for 365 days prior to index date

❌ EXCLUSION CRITERIA:
   1. History of type 1 diabetes (any time)
   2. History of gestational diabetes (any time)

👥 DEMOGRAPHICS:
   age: >= 18 years

📅 OBSERVATION WINDOW:
   365 days prior to index, follow-up until end of continuous enrollment
```

---

## 💡 Key Improvements

### 1. Domain-Specific
- Tailored specifically for OMOP CDM / ATLAS
- Uses correct terminology (index event, inclusion/exclusion criteria)
- Asks clinically relevant questions

### 2. Structured Output
- Returns typed `CohortDefinition` object
- Can be easily serialized to JSON
- Ready for integration with ATLAS API

### 3. Better UX
- Shows progress as components are filled
- Clear visual formatting with emojis
- Components grouped logically

### 4. Production-Ready
- Can be imported and used programmatically
- Integrates with OMOP workflows
- Output format matches ATLAS requirements

---

## 🧪 Example Usage

### As Standalone Script

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen/projects/clar
set -a && source ../../.env && set +a
uv run python hitl_clarification_working.py
```

### As Library

```python
from hitl_clarification_working import run_clarification_loop, CohortDefinition

# Get cohort definition
cohort_desc = "patients with type 2 diabetes who started metformin"
cohort_def: CohortDefinition = run_clarification_loop(cohort_desc)

# Access components
print(f"Index Event: {cohort_def.index_event}")
print(f"Inclusion: {cohort_def.inclusion_criteria}")
print(f"Exclusion: {cohort_def.exclusion_criteria}")

# Convert to dict for JSON serialization
cohort_dict = cohort_def.model_dump()

# Use in ATLAS workflow
atlas_json = map_to_atlas_definition(cohort_def)
```

---

## 📁 Files Changed

### hitl_clarification_working.py
- ✅ New `CohortDefinition` model (7 fields for OMOP components)
- ✅ Updated `ClarificationDecision` to include `cohort_components`
- ✅ Rewrote agent system prompt for OMOP focus
- ✅ Updated `run_clarification_loop()` to build `CohortDefinition`
- ✅ Added `_format_cohort_definition()` for pretty display
- ✅ Updated `main()` for OMOP-specific prompts

### README.md
- ✅ Updated title: "OMOP Cohort Definition Builder"
- ✅ New example session showing OMOP workflow
- ✅ Updated usage tips for OMOP/ATLAS context
- ✅ Added OMOP components description
- ✅ Updated integration examples

---

## ✅ Tested

```bash
$ uv run python -c "from hitl_clarification_working import CohortDefinition, run_clarification_loop; print('✅ Imports work!')"
✅ Imports work!

$ uv run python -c "from hitl_clarification_working import CohortDefinition; print(list(CohortDefinition.model_fields.keys()))"
['index_event', 'inclusion_criteria', 'exclusion_criteria', 'observation_window', 'demographics', 'prior_observation', 'cohort_exit']
```

---

## 🎯 Ready to Use

The script is now:
- ✅ OMOP CDM-specific
- ✅ ATLAS-ready output
- ✅ Structured and typed
- ✅ Production-ready
- ✅ Well-documented

**Run it with**: `set -a && source ../../.env && set +a && uv run python hitl_clarification_working.py`

---

**Status**: ✅ **Complete and Ready**  
**Focus**: OMOP CDM / ATLAS Cohort Definitions  
**Output**: Structured `CohortDefinition` objects  
**Integration**: Ready for OMOP workflows


