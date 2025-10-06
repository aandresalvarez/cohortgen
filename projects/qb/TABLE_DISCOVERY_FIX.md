# Stage 3: Table Discovery Fix

## 🐛 Issue Identified

**Problem**: SQL generation was failing with "Table not found" errors because:

1. The SQL generator blindly assumed all OMOP domain tables exist
2. The public demo dataset (`bigquery-public-data.cms_synthetic_patient_data_omop`) is missing the `measurement` table
3. When concept sets included Measurement domain concepts, SQL would reference non-existent tables

**Example Error**:
```
❌ SQL validation failed (attempt 1/3)
   Errors: ['BigQuery API error: Not found: Table bigquery-public-data:cms_synthetic_patient_data_omop.measurement was not found in location US']
```

---

## ✅ Solution Implemented

### 1. **Table Discovery (Step 0)**

Before generating SQL, Stage 3 now:
- Connects to BigQuery
- Lists all available tables in the target OMOP dataset
- Identifies which domain tables are present

```python
[Step 0] Discovering available OMOP tables...
✅ Found 24 tables in bigquery-public-data.cms_synthetic_patient_data_omop
   Available domain tables: condition_occurrence, drug_exposure, observation, procedure_occurrence
```

### 2. **Concept Set Filtering**

During SQL generation:
- Checks each concept set's domain against available tables
- Warns about concept sets that reference missing tables
- **Excludes** those concept sets from SQL generation

```python
⚠️  Warning: Some concept sets reference tables that don't exist:
   - Lab Values (Domain: Measurement → measurement)
   These concepts will be excluded from the generated SQL.
```

### 3. **Graceful Degradation**

If table discovery fails (e.g., no BigQuery access):
- Falls back to default behavior
- Allows SQL generation to proceed
- Validation errors will still occur but won't prevent SQL creation

---

## 🔧 Technical Changes

### File: `projects/qb/create_bigquery_sql.py`

**Function**: `run_bigquery_sql_generation()`

**Changes**:
1. Added **Step 0** for table discovery:
   ```python
   from google.cloud import bigquery
   client = bigquery.Client(project=project_id, location=location)
   dataset_ref = client.dataset(ds_name, project=ds_project)
   available_tables = {table.table_id for table in client.list_tables(dataset_ref)}
   ```

2. Check concept sets against available tables:
   ```python
   domain_table_map = {
       "Condition": "condition_occurrence",
       "Procedure": "procedure_occurrence",
       "Drug": "drug_exposure",
       "Measurement": "measurement",
       "Observation": "observation",
   }
   
   for concept_set in cohort_input.concept_sets:
       domain = concept_set.get("domain", "")
       table_name = domain_table_map.get(domain, "")
       if table_name and table_name not in available_tables:
           # Warn and skip this concept set
   ```

3. Updated `_format_concept_sets()` to accept `available_tables` parameter:
   ```python
   def _format_concept_sets(
       concept_sets: List[ConceptSet], 
       available_tables: List[str] = None
   ) -> str:
       # Skip concept sets whose domain tables don't exist
       if available_tables is not None and len(available_tables) > 0:
           table_name = domain_table_map.get(domain, "")
           if table_name and table_name not in available_tables:
               continue  # Skip this concept set
   ```

---

## 🧪 Testing

### Available Tables in Public Dataset

```bash
uv run python3 -c "from google.cloud import bigquery; \
  client = bigquery.Client(); \
  tables = list(client.list_tables('bigquery-public-data.cms_synthetic_patient_data_omop')); \
  [print(t.table_id) for t in sorted(tables, key=lambda x: x.table_id)]"
```

**Result** (24 tables):
- ✅ `condition_occurrence`
- ✅ `procedure_occurrence`
- ✅ `drug_exposure`
- ✅ `observation`
- ❌ `measurement` (MISSING)

### Test Case: Heart Failure + ESRD Cohort

**Concept Sets**:
1. Heart Failure (Domain: Condition) → ✅ `condition_occurrence` exists
2. ESRD (Domain: Condition) → ✅ `condition_occurrence` exists
3. Dialysis (Domain: Procedure) → ✅ `procedure_occurrence` exists
4. Transplant (Domain: Procedure) → ✅ `procedure_occurrence` exists

**Expected Outcome**: ✅ All concept sets map to available tables → SQL validates successfully

### Test Case: Cohort with Lab Values

**Concept Sets**:
1. Diabetes (Domain: Condition) → ✅ `condition_occurrence` exists
2. HbA1c Lab (Domain: Measurement) → ❌ `measurement` MISSING

**Expected Outcome**:
```
⚠️  Warning: Some concept sets reference tables that don't exist:
   - HbA1c Lab (Domain: Measurement → measurement)
   These concepts will be excluded from the generated SQL.

✅ SQL generated (without measurement criteria)
```

---

## 📋 User Impact

### ✅ Benefits

1. **No more "Table not found" errors** for missing domain tables
2. **Clear warnings** about which concept sets are skipped
3. **Informed decisions**: Users know which data elements are missing
4. **SQL still generates** even if some tables are unavailable
5. **Works with any OMOP dataset** (public or private)

### ⚠️ Limitations

- If **all** concept sets reference missing tables, SQL will be empty/minimal
- Users with incomplete OMOP datasets should configure their own complete dataset
- Lab-based cohorts won't work with the public demo dataset (no `measurement` table)

### 🎯 Recommendations

**For Demo/Testing**: Public dataset is fine for condition/procedure-based cohorts

**For Production**:
1. Set up your own complete OMOP CDM dataset in BigQuery
2. Configure `OMOP_DATASET_ID` in `.env` or in UI per-run
3. Ensure all required domain tables exist

---

## 🚀 Next Steps

### Completed
- ✅ Table discovery before SQL generation
- ✅ Concept set filtering based on available tables
- ✅ Clear warnings in Stage 3 output
- ✅ Documentation (`BIGQUERY_SETUP.md`, `env.example` updated)

### Future Enhancements (Optional)
- [ ] Cache table discovery results per dataset
- [ ] Show available vs. missing tables in UI
- [ ] Suggest alternative datasets if tables are missing
- [ ] Validate OMOP schema completeness (all required tables present)

---

## 📚 Related Files

- `projects/qb/create_bigquery_sql.py` - Main SQL generation logic
- `projects/qb/tools.py` - BigQuery dry-run validation
- `projects/ui/service.py` - UI integration for SQL generation
- `env.example` - OMOP dataset configuration
- `BIGQUERY_SETUP.md` - User guide for BigQuery setup

---

**Status**: ✅ **FIXED** - SQL generation now robust to missing tables

