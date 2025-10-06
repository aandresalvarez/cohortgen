# Stage 3: BigQuery SQL Generation

**Pydantic AI implementation for generating validated BigQuery SQL from OMOP cohort definitions.**

---

## 📋 Overview

This is **Stage 3** of the complete OMOP cohort workflow. It takes the clinical definition (Stage 1) and OMOP concept sets (Stage 2) and generates a validated BigQuery SQL query that can be executed against an OMOP CDM database.

---

## 🔄 Workflow Position

```
┌──────────────────┐
│   Stage 1:       │  User describes cohort
│   Clarification  │  → Structured clinical definition
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Stage 2:       │  Clinical text → OMOP concepts
│   Concept        │  → Standard concept IDs
│   Discovery      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Stage 3:       │  ◄── YOU ARE HERE
│   BigQuery SQL   │  Cohort + concepts → BigQuery SQL
│   Generation     │
└────────┬─────────┘
         │
         ▼
     Execute in BigQuery
```

---

## ⚙️ How It Works

### 1. **Input**

Reads from: `projects/run/complete_cohort_output.json`

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
      ],
      "include_descendants": true
    }
  ]
}
```

### 2. **SQL Generation Agent**

- **Model**: `gpt-4o-mini`
- **Task**: Generate BigQuery Standard SQL for OMOP CDM v5.x
- **Output**: Complete SELECT statement with CTEs

**Rules enforced**:
- Fully qualified table names (`project.dataset.table`)
- OMOP CDM v5.x field names
- Concept ID filtering
- Descendant expansion via `concept_ancestor`
- Standard concepts only (`standard_concept='S'`)

### 3. **Validation Loop**

- **BigQuery Dry Run**: Validates SQL syntax without executing
- **Cost Estimation**: Estimates bytes processed and USD cost
- **Auto-Fix**: If validation fails, SQL Fixer agent corrects errors

### 4. **Output**

```
projects/qb/
  ├── generated_cohort_query.sql    ← Validated SQL
  └── sql_generation_result.json    ← Validation metadata
```

---

## 🚀 Usage

### **Quick Start**

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen/projects/qb
./run_query_builder.sh
```

### **Standalone Python**

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen
uv run python projects/qb/create_bigquery_sql.py
```

### **Prerequisites**

1. **Stage 1 + Stage 2 complete**: `projects/run/complete_cohort_output.json` must exist
2. **Environment variables** (optional):
   ```bash
   OMOP_DATASET_ID="bigquery-public-data.cms_synthetic_patient_data_omop"
   BIGQUERY_PROJECT_ID="your-gcp-project"
   BIGQUERY_LOCATION="US"
   OPENAI_API_KEY="sk-..."
   ```

---

## 📝 Example Output

### **Generated SQL**

```sql
WITH cohort_base AS (
  SELECT DISTINCT m.person_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.measurement` m
  WHERE m.measurement_concept_id IN (4171852, 4171853)
    AND EXTRACT(YEAR FROM m.measurement_date) = 2020
),
demographics_filter AS (
  SELECT p.person_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.person` p
  WHERE p.gender_concept_id = 8507  -- Male
    AND EXTRACT(YEAR FROM CURRENT_DATE()) - p.year_of_birth BETWEEN 20 AND 30
)
SELECT DISTINCT cb.person_id
FROM cohort_base cb
INNER JOIN demographics_filter df ON cb.person_id = df.person_id;
```

### **Validation Result**

```json
{
  "sql": "WITH cohort_base AS (...",
  "is_valid": true,
  "errors": [],
  "estimated_cost_usd": 0.0012,
  "total_bytes_processed": 204800,
  "summary": "Query is valid. Estimated to process 0.20 GB, costing ~$0.0012."
}
```

---

## 🏗️ Architecture

### **Components**

1. **`tools.py`**: Pydantic AI wrapper for `bq_dry_run`
   - Validates SQL syntax
   - Estimates query cost
   - Returns structured results

2. **`create_bigquery_sql.py`**: Main workflow script
   - SQL Generator Agent
   - SQL Fixer Agent
   - Validation loop
   - File I/O

3. **`run_query_builder.sh`**: Shell script for easy execution

### **Agents**

#### **SQL Generator Agent**
- **Input**: Clinical definition + concept sets + OMOP dataset
- **Output**: BigQuery Standard SQL
- **System Prompt**: Expert OMOP CDM SQL developer with BigQuery focus

#### **SQL Fixer Agent**
- **Input**: Original SQL + BigQuery error messages
- **Output**: Corrected SQL
- **System Prompt**: SQL debugger that preserves logic and fixes syntax

### **Validation Loop**

```python
for iteration in range(max_fix_iterations):
    result = validate_bigquery_sql(current_sql)
    if result.success:
        return result  # ✅ Valid SQL
    # ❌ Has errors - fix it
    current_sql = sql_fixer_agent.run_sync(fix_prompt)
```

**Max iterations**: 3 (configurable)

---

## 🆚 Comparison: Flujo vs Pydantic AI

| Feature | Flujo Version | Pydantic AI Version |
|---------|---------------|---------------------|
| **File structure** | `pipeline.yaml` + `skills/*.py` | `create_bigquery_sql.py` + `tools.py` |
| **Agents** | Declarative YAML config | Python `Agent()` objects |
| **Validation loop** | `loop` step with `exit_expression` | Python `for` loop |
| **Tools** | Custom skills via `uses:` | Pydantic AI `tools=[]` |
| **Error handling** | Conditional steps | Python try/except |
| **State management** | Context + scratchpad | Python variables |
| **HITL** | Built-in `kind: hitl` | Not needed (fully automated) |

---

## 🔧 Configuration

### **Environment Variables**

Set in `/.env` or export before running:

```bash
# Required
OPENAI_API_KEY="sk-..."

# Optional (defaults shown)
OMOP_DATASET_ID="bigquery-public-data.cms_synthetic_patient_data_omop"
BIGQUERY_PROJECT_ID=""  # Empty = use default project
BIGQUERY_LOCATION="US"
```

### **OMOP Dataset**

Default: **BigQuery Public Dataset** (`bigquery-public-data.cms_synthetic_patient_data_omop`)
- Synthetic Medicare claims data
- OMOP CDM v5.x
- Free to query (standard BigQuery pricing applies)

**Custom dataset**: Set `OMOP_DATASET_ID` to your dataset path.

---

## 📚 Integration with Full Workflow

### **Run All 3 Stages**

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen/projects/run
./run_integrated.sh   # Stage 1 + 2

cd /Users/alvaro1/Documents/Coral/Code/cohortgen/projects/qb
./run_query_builder.sh  # Stage 3
```

### **Data Flow**

```
Stage 1: hitl_clarification_working.py
  ↓ (CohortDefinition object)
  
Stage 2: find_concepts.py
  ↓ (ConceptDiscoveryOutput object)
  
run_complete_workflow.py combines them
  ↓ (complete_cohort_output.json)
  
Stage 3: create_bigquery_sql.py
  ↓ (generated_cohort_query.sql)
  
Execute in BigQuery
```

---

## 🧪 Testing

### **Test with Sample Data**

```bash
# 1. Generate sample cohort (Stage 1 + 2)
cd projects/run
./run_integrated.sh
# Input: "male between 20 and 30 with positive flu test in 2020"

# 2. Generate SQL (Stage 3)
cd ../qb
./run_query_builder.sh

# 3. Review output
cat generated_cohort_query.sql
```

### **Validate Manually**

```bash
# Copy SQL to BigQuery console
# Click "More" → "Query Settings"
# Enable "Dry run" to validate without executing
```

---

## 🐛 Troubleshooting

### **Error: "Input file not found"**

**Cause**: Stage 1 + 2 haven't been run yet.

**Fix**:
```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen/projects/run
./run_integrated.sh
```

### **Error: "google-cloud-bigquery is not installed"**

**Cause**: BigQuery Python client not installed.

**Fix**:
```bash
uv add google-cloud-bigquery
```

### **Error: "SQL validation failed after 3 attempts"**

**Cause**: Generated SQL has persistent syntax errors.

**Fix**: Review `sql_generation_result.json` for error details. Common issues:
- Wrong table names (check `OMOP_DATASET_ID`)
- Missing fields (verify OMOP CDM version)
- Invalid concept IDs

---

## 📊 Output Files

### **`generated_cohort_query.sql`**

- **Purpose**: Ready-to-execute BigQuery SQL
- **Format**: Plain SQL (no markdown)
- **Usage**: Copy-paste into BigQuery console or use via API

### **`sql_generation_result.json`**

- **Purpose**: Validation metadata and cost estimates
- **Format**: JSON
- **Contents**:
  ```json
  {
    "sql": "WITH cohort_base AS ...",
    "is_valid": true,
    "errors": [],
    "estimated_cost_usd": 0.0012,
    "total_bytes_processed": 204800,
    "summary": "Query is valid. Estimated to process 0.20 GB..."
  }
  ```

---

## 🎯 Summary

| **Aspect** | **Details** |
|------------|-------------|
| **Purpose** | Generate validated BigQuery SQL for OMOP cohorts |
| **Input** | `complete_cohort_output.json` (from Stage 1 + 2) |
| **Output** | `generated_cohort_query.sql` + metadata |
| **Framework** | Pydantic AI |
| **Model** | `gpt-4o-mini` |
| **Validation** | BigQuery dry run (syntax + cost) |
| **Auto-fix** | Yes (up to 3 iterations) |
| **HITL** | No (fully automated) |

---

## 🚀 Next Steps

1. **Review SQL**: Check `generated_cohort_query.sql`
2. **Execute**: Run in BigQuery console or via API
3. **Analyze**: Export results and perform statistical analysis
4. **Iterate**: Refine cohort definition and regenerate

---

## 📖 Related Documentation

- **Stage 1**: `projects/clar/README.md`
- **Stage 2**: `projects/cd/README.md`
- **Full Workflow**: `HOW_TO_RUN.md`
- **Flujo Version**: `projects/query_builder/README.md`

