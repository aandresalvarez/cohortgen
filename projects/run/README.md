# Execution Directory for OMOP Cohort Workflow

**Simple, consolidated execution for all 3 stages.**

---

## 📂 Directory Contents

```
projects/run/
├── run_full_workflow.sh           # ⭐ MAIN SCRIPT - Run this!
├── run_complete_workflow.py       # Core integration (called by main script)
├── complete_cohort_output.json    # Output data (generated at runtime)
└── README.md                       # This file
```

---

## 🚀 How to Run

### **One Command to Rule Them All**

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen/projects/run
./run_full_workflow.sh
```

### **Menu Options**

When you run `./run_full_workflow.sh`, you'll see:

```
Choose a mode:
  1) Run all 3 stages (complete workflow: text → concepts → SQL)
  2) Run Stage 1 + 2 only (clinical clarification + concept discovery)
  3) Run Stage 1 only (clinical clarification)
  4) Run Stage 2 only (concept discovery)
  5) Run Stage 3 only (BigQuery SQL generation)
  6) Run demo (Stage 2 with test data)
```

---

## 🎯 Recommended Usage

### **First Time Users**

```bash
./run_full_workflow.sh
# Choose option 1: "Run all 3 stages"
```

This will:
1. Ask you to describe your cohort (interactive)
2. Generate OMOP concept IDs (automatic)
3. Generate BigQuery SQL (automatic)

### **Testing Changes**

If you're iterating on your cohort definition:

```bash
./run_full_workflow.sh
# Choose option 2: "Run Stage 1 + 2 only"
```

Then review `complete_cohort_output.json` before generating SQL.

### **Regenerate SQL Only**

If you want to regenerate SQL with different settings:

```bash
./run_full_workflow.sh
# Choose option 5: "Run Stage 3 only"
```

---

## 📤 Output Files

### **`complete_cohort_output.json`**

**Created by**: Options 1, 2 (Stage 1 + 2)

**Contains**:
- Clinical definition (structured)
- OMOP concept sets (with IDs)

**Used by**: Stage 3 (BigQuery SQL generation)

**Example**:
```json
{
  "clinical_definition": {
    "index_event": "positive flu test",
    "demographics": {"age": "20-30", "gender": "male"},
    "observation_window": "in year 2020"
  },
  "concept_sets": [
    {
      "name": "Influenza Test",
      "included_concepts": [
        {"concept_id": 4171852, "concept_name": "Influenza virus A RNA"}
      ]
    }
  ]
}
```

---

## 🔄 Data Flow

```
run_full_workflow.sh (option 1)
  ↓
run_complete_workflow.py
  ↓ calls
┌─────────────────────────────────────┐
│ Stage 1: hitl_clarification_working.py │
│  (projects/clar/)                      │
└────────────┬────────────────────────┘
             ↓ CohortDefinition
┌─────────────────────────────────────┐
│ Stage 2: find_concepts.py            │
│  (projects/cd/)                       │
└────────────┬────────────────────────┘
             ↓ ConceptDiscoveryOutput
┌─────────────────────────────────────┐
│ complete_cohort_output.json          │
│  (saved here in projects/run/)       │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ Stage 3: create_bigquery_sql.py      │
│  (projects/qb/)                       │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ generated_cohort_query.sql           │
│  (projects/qb/)                       │
└─────────────────────────────────────┘
```

---

## 🛠️ Technical Details

### **`run_full_workflow.sh`**

- **Purpose**: Interactive menu for all workflow options
- **Environment**: Loads `.env` from project root
- **Dependencies**: `uv`, Python, OpenAI API key
- **Exit codes**: 0 = success, 1 = error

### **`run_complete_workflow.py`**

- **Purpose**: Orchestrates Stage 1 + 2 integration
- **Called by**: `run_full_workflow.sh` (options 1, 2)
- **Input**: User's initial cohort description
- **Output**: `complete_cohort_output.json`
- **Key function**: `format_cohort_for_stage2()` - Converts Stage 1 output to Stage 2 input

---

## 🔧 Prerequisites

1. **Environment file**: `/.env` with `OPENAI_API_KEY`
2. **Python dependencies**: Installed via `uv sync`
3. **Active shell**: Run from terminal (interactive input required for Stage 1)

---

## 📚 Related Documentation

- **Full Workflow Guide**: `/HOW_TO_RUN.md`
- **Quick Start**: `/QUICK_START.md`
- **Stage 1**: `/projects/clar/README.md`
- **Stage 2**: `/projects/cd/README.md`
- **Stage 3**: `/projects/qb/README.md`

---

## 🎯 Summary

| **What** | **File** | **Purpose** |
|----------|----------|-------------|
| **Run this** | `run_full_workflow.sh` | Interactive menu for all options |
| **Integration** | `run_complete_workflow.py` | Stage 1 + 2 orchestration |
| **Output** | `complete_cohort_output.json` | Combined output for Stage 3 |

**Keep it simple**: Just run `./run_full_workflow.sh` and choose your option! 🚀
