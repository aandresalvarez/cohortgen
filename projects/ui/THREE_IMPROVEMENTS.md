# Three Major Improvements to OMOP Cohort UI

**Date**: October 6, 2025  
**Status**: ✅ COMPLETE

---

## 🎯 **User Requests**

1. **Individual Stage Testing** - "I want to test the steps individually so I do not have to wait for the entire pipeline to discover errors"
2. **Formatted SQL Display** - "I want to be able to see the final SQL formatted"
3. **Stage 4 Analytics** - "The step 4 is not showing any of the stats"

---

## ✅ **Improvement 1: Individual Stage Testing**

### Problem
- Had to run the entire 4-stage workflow to test each stage
- Errors in later stages required re-running everything
- Time-consuming and inefficient for debugging

### Solution

**UI Controls** (in "Individual Stage Testing" accordion):
- ✅ "Test Stage 1" button
- ✅ "Test Stage 2" button
- ✅ "Test Stage 3" button
- ✅ "Test Stage 4" button

**How it works**:
1. Select a run from the list
2. Open "🔬 Individual Stage Testing" accordion
3. Click any stage button to re-run just that stage
4. Auto-refresh shows progress in real-time

**Makefile Commands** (for CLI testing):
```bash
# Test individual stages for a specific run
make run-stage1 RUN_ID=20251006_123456_abc123
make run-stage2 RUN_ID=20251006_123456_abc123
make run-stage3 RUN_ID=20251006_123456_abc123
make run-stage4 RUN_ID=20251006_123456_abc123
```

**Benefits**:
- ✅ Test stages independently
- ✅ Skip successful stages
- ✅ Iterate quickly on problem stages
- ✅ No need to re-run entire pipeline

### Implementation Details

**File**: `projects/ui/app.py`

Added `test_individual_stage()` function:
```python
def test_individual_stage(run_id: str, stage_num: int) -> str:
    """Run a single stage for testing purposes."""
    if not run_id:
        return "⚠️ No run selected"
    
    run = service.storage.load_run(run_id)
    stage_methods = {
        1: service._execute_stage1,
        2: service._execute_stage2,
        3: service._execute_stage3,
        4: service._execute_stage4,
    }
    
    method = stage_methods.get(stage_num)
    
    # Run in background thread
    thread = threading.Thread(target=lambda: method(run), daemon=True)
    thread.start()
    
    return f"✅ Stage {stage_num} started! Refresh to see results."
```

**File**: `Makefile`

Added individual stage runners:
```makefile
run-stage1: ## Run Stage 1 for specific run
	@uv run python -c "from projects.ui.service import CohortService; ..."

run-stage2: ## Run Stage 2 for specific run
	@uv run python -c "from projects.ui.service import CohortService; ..."

# ... etc for stages 3 and 4
```

---

## ✅ **Improvement 2: Formatted SQL Display**

### Problem
- Generated SQL was hard to read (no formatting)
- No syntax highlighting
- Difficult to verify correctness visually

### Solution

**UI Component**: "🎨 Format SQL with Syntax Highlighting" button in Stage 3 (SQL) tab

**Features**:
- ✅ Line numbers
- ✅ SQL keyword highlighting (SELECT, FROM, WHERE, JOIN, etc.)
- ✅ Monospace font with proper spacing
- ✅ Scrollable view for long queries
- ✅ Clean, readable layout

**How it works**:
1. Go to "Download Artifacts" accordion
2. Select "Stage 3 (SQL)" tab
3. Load the SQL with "Load Stage 3 SQL"
4. Click "🎨 Format SQL with Syntax Highlighting"
5. See beautifully formatted SQL below

### Implementation Details

**File**: `projects/ui/app.py`

Added `format_sql()` function:
```python
def format_sql(sql_text: str) -> str:
    """Format SQL for display with basic syntax highlighting using HTML."""
    lines = sql_text.strip().split('\n')
    formatted_lines = []
    
    keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'INNER JOIN', 
                'GROUP BY', 'ORDER BY', 'HAVING', 'WITH', 'AS', 'DISTINCT', ...]
    
    for i, line in enumerate(lines, 1):
        line_html = line
        for keyword in keywords:
            # Highlight SQL keywords in blue
            line_html = re.sub(
                r'\b(' + keyword + r')\b',
                r'<span style="color: #0066CC; font-weight: bold;">\1</span>',
                line_html,
                flags=re.IGNORECASE
            )
        
        # Add line numbers
        formatted_lines.append(
            f'<span style="color: #888;">{i:3d}|</span> {line_html}'
        )
    
    return '<div style="font-family: monospace; ...">...</div>'
```

Added UI components:
```python
with gr.Tab("Stage 3 (SQL)"):
    stage3_output = gr.Code(language="sql", ...)
    load_stage3_btn = gr.Button("Load Stage 3 SQL")
    
    gr.Markdown("### Formatted SQL Preview")
    stage3_sql_formatted = gr.HTML(label="Formatted SQL")
    format_sql_btn = gr.Button("🎨 Format SQL with Syntax Highlighting")
```

**Example Output**:
```
  1| WITH
  2| -- Heart failure concepts
  3| heart_ancestor_ids AS (
  4|   SELECT 316139 AS concept_id UNION ALL SELECT 319835 UNION ALL SELECT 4229440
  5| ),
  6| 
  7| heart_concepts AS (
  8|   SELECT DISTINCT c.concept_id
  9|   FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
 10|   JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
 11|     ON ca.descendant_concept_id = c.concept_id
 12|   WHERE ca.ancestor_concept_id IN (SELECT concept_id FROM heart_ancestor_ids)
 13|     AND c.standard_concept = 'S'
 14| ),
...
```

**Keywords highlighted**: SELECT, FROM, WHERE, JOIN, WITH, AS, etc.

---

## ✅ **Improvement 3: Stage 4 Analytics Display**

### Problem
- Stage 4 was just showing "skipped" placeholder
- No actual analytics were being run
- User couldn't see cohort stats (size, gender, age, etc.)

### Solution

**Real Analytics Execution**:
- ✅ Runs actual BigQuery analytics queries
- ✅ Computes cohort size
- ✅ Gender distribution
- ✅ Age buckets (if index date available)
- ✅ Index year distribution
- ✅ Displays results in UI

**What it shows**:
```
📊 Cohort Size: 1,234 patients

👥 Gender Distribution:
- Female: 678
- Male: 556

🎂 Age Distribution:
- <18: 12
- 18-39: 234
- 40-64: 567
- 65-74: 289
- 75+: 132

📅 Index Year Distribution:
- 2015: 234
- 2016: 312
- 2017: 289
- 2018: 245
- 2019: 154
```

### Implementation Details

**File**: `projects/ui/service.py`

Replaced placeholder with real analytics:
```python
def _execute_stage4(self, run: CohortRun) -> None:
    # Get BigQuery configuration
    project_id = run.user_inputs.bigquery_project_id or os.getenv("BIGQUERY_PROJECT_ID")
    dataset = run.user_inputs.omop_dataset_id or os.getenv("OMOP_DATASET_ID")
    location = run.user_inputs.bigquery_location or "US"
    
    if not project_id:
        log_print("⚠️  No BigQuery project configured")
        analytics_output = {"status": "skipped", ...}
    else:
        # Load cohort input data
        with open(run.stage2_path) as f:
            input_data = json.load(f)
        
        # Extract ESRD concept IDs for index-date derivation
        esrd_ids = extract_concept_ids(input_data, ["end-stage renal disease", "esrd"])
        
        # Build analytics queries
        queries = build_analytics_queries(sql_content, project_id, dataset, esrd_ids)
        
        # Run queries
        client = bigquery.Client(project=project_id, location=location)
        results = {}
        
        for name, sql in queries.items():
            log_print(f"[Run] {name}...")
            job = client.query(sql)
            rows = list(job.result())
            items = [{k: r[k] for k in r.keys()} for r in rows]
            results[name] = items
            log_print(f"  ✓ {len(items)} rows")
        
        analytics_output = {
            "status": "complete",
            "project_id": project_id,
            "dataset": dataset,
            "results": results
        }
```

**File**: `projects/ui/app.py`

Added analytics display in `render_stage()`:
```python
elif stage_result.stage == 4:
    # Display analytics results
    if run.stage4_path:
        with open(run.stage4_path) as f:
            analytics = json.load(f)
        
        if analytics.get("status") == "complete":
            results = analytics.get("results", {})
            
            if "cohort_size" in results:
                cohort_size = results["cohort_size"][0].get("n", 0)
                output.append(f"**📊 Cohort Size:** {cohort_size:,} patients")
            
            if "by_gender" in results:
                output.append("**👥 Gender Distribution:**")
                for row in results["by_gender"]:
                    gender = row.get("gender", "unknown")
                    count = row.get("n", 0)
                    output.append(f"- {gender.capitalize()}: {count:,}")
            
            # ... age buckets and index year ...
```

---

## 📊 **Overall Impact**

| Feature | Before | After |
|---------|--------|-------|
| **Stage Testing** | ❌ Run all stages every time | ✅ Test individual stages |
| **SQL Display** | ⚠️ Raw text, hard to read | ✅ Formatted + syntax highlighted |
| **Analytics** | ❌ Placeholder/skipped | ✅ Real stats displayed |
| **Debugging Speed** | 🐌 Slow (re-run everything) | ⚡ Fast (test one stage) |
| **SQL Readability** | 📄 Plain text | 🎨 Highlighted + line numbers |
| **Result Visibility** | ⚠️ No cohort stats | 📊 Full analytics dashboard |

---

## 🧪 **How to Use**

### 1. Test Individual Stages (UI)

1. Select a run from the list
2. Open "🔬 Individual Stage Testing" accordion
3. Click "Test Stage X" button
4. Watch auto-refresh show progress

### 2. Test Individual Stages (CLI)

```bash
# Get run ID from UI or output/runs/ directory
RUN_ID=20251006_153305_c97fa6

# Test specific stage
make run-stage1 RUN_ID=$RUN_ID
make run-stage2 RUN_ID=$RUN_ID
make run-stage3 RUN_ID=$RUN_ID
make run-stage4 RUN_ID=$RUN_ID
```

### 3. View Formatted SQL

1. Select completed run
2. Open "📥 Download Artifacts" accordion
3. Go to "Stage 3 (SQL)" tab
4. Click "Load Stage 3 SQL"
5. Click "🎨 Format SQL with Syntax Highlighting"
6. See beautifully formatted SQL below

### 4. View Analytics

1. Run must complete Stage 4
2. Check the "Stage 4: Analytics" section in main view
3. See:
   - Cohort size
   - Gender distribution
   - Age buckets (if applicable)
   - Index year distribution

---

## 🎯 **Success Criteria**

All three improvements fully implemented:

1. ✅ **Individual Stage Testing**
   - UI buttons work
   - Makefile commands work
   - Stages run in background
   - Progress visible in real-time

2. ✅ **Formatted SQL Display**
   - Syntax highlighting for SQL keywords
   - Line numbers
   - Clean, readable layout
   - Scrollable for long queries

3. ✅ **Stage 4 Analytics**
   - Real BigQuery queries executed
   - Stats computed and displayed
   - Graceful handling when BigQuery not configured
   - Clear, formatted output

---

## 📚 **Related Files**

- `projects/ui/app.py` - All three improvements
- `projects/ui/service.py` - Stage 4 analytics execution
- `Makefile` - Individual stage CLI commands
- `projects/stats/run_stats.py` - Analytics query builder

---

**Status**: ✅ **ALL THREE IMPROVEMENTS COMPLETE AND WORKING**

