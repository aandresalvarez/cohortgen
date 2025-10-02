# Concept Discovery Pipeline V2

## 🎯 **Key Improvements Over V1**

### **Problem with V1:**
- Single "exploration_loop" agent tried to do everything:
  - Analyze all concept sets
  - Decide which tool to use
  - Execute tools
  - Decide when to finish
- Result: Complex decisions, tool hallucination, max loops reached

### **Solution in V2:**
- **Modular architecture** with focused agents
- **Parallel validation** of concept sets
- **Clear separation of concerns**
- **Simpler decision-making** at each step

---

## 🏗️ **Architecture Overview**

```
Phase 1: DECOMPOSITION & SEARCH (Sequential)
├─ parse_initial_payload      → Parse user input
├─ decompose_concept_sets      → Break into concept sets (Agent)
├─ normalize_concept_plan      → Convert to dict
└─ search_initial_candidates   → Find ATHENA candidates

Phase 2: VALIDATION (Parallel - Map over concept sets)
└─ validate_all_concept_sets
   └─ validate_single_set      → Check quality per set (Agent)

Phase 3: DECISION (Sequential)
├─ aggregate_validations       → Combine validation results
└─ decide_refinement           → Finish or refine? (Agent)

Phase 4: REFINEMENT (Conditional Loop, max 3 iterations)
└─ refinement_loop
   ├─ apply_refinements        → Remove bad candidates
   ├─ revalidate_concept_sets  → Re-check quality (Parallel)
   ├─ reaggregate_validations  → Update summary
   └─ redecide_refinement      → Check again

Phase 5: FINALIZATION (Sequential)
├─ finalize_concept_sets       → Convert to ATLAS format
└─ emit_for_parent             → Return result
```

---

## 🎭 **Agent Roles**

### **1. concept_decomposer** (GPT-5-Mini, Medium Reasoning)
**Single Responsibility:** Break cohort definition into concept sets
- **Input:** Raw cohort definition string
- **Output:** Structured plan with concept sets, queries, vocabularies
- **Decision:** None - just decomposition

### **2. concept_validator** (GPT-5-Mini, Low Reasoning)
**Single Responsibility:** Validate ONE concept set's quality
- **Input:** Single concept set with candidates
- **Output:** Quality score (1-10), issues list, recommendations
- **Decision:** Quality assessment only
- **Runs:** In parallel for each concept set (via `map`)

### **3. refinement_decision_agent** (GPT-5-Mini, Low Reasoning)
**Single Responsibility:** Decide if concept sets are ready
- **Input:** Validation summary (all concept sets)
- **Output:** "finish" or "refine" decision
- **Decision:** Simple binary choice
- **Criteria:**
  - Average quality >= 8 and no issues → FINISH
  - Quality < 8 or has issues → REFINE
  - Already refined 2+ times → FINISH (accept current)

---

## 🔧 **Helper Functions**

### **aggregate_validation_results**
- Combines parallel validation outputs
- Calculates average quality score
- Stores summary in `context.scratchpad.validation_summary`

### **apply_concept_refinements**
- Removes candidates marked for exclusion
- Tracks refinement count
- Updates `context.scratchpad.concept_sets`

### **increment_counter**
- Tracks refinement iterations
- Prevents infinite loops

### **finalize_concept_sets**
- Converts to ATLAS-compatible format
- Structures as `included_concepts` / `excluded_concepts`

---

## 📊 **Data Flow**

### **Context Structure:**

```yaml
context:
  scratchpad:
    cohort_definition: str
    concept_sets: List[Dict]
      - name: str
        candidates: List[Dict]
          - concept_id: int
          - concept_name: str
          - domain_id: str
          - vocabulary_id: str
          - standard_concept: str
          - concept_code: str
        include_descendants: bool
        standard_only: bool
        notes: str
    
    validation_summary:
      average_quality: float
      total_sets: int
      ready_to_finalize: bool
      all_issues: List[str]
      details: List[Dict]
        - name: str
          quality_score: int
          issues: List[str]
          recommendations: str
          exclude_concepts: List[int]
          missing_concepts: List[str]
    
    refinement_count: int
    
    final_concept_sets:
      concept_sets: List[Dict]
        - name: str
          included_concepts: List[Dict]
          excluded_concepts: List[Dict]
```

---

## ⚡ **Performance Benefits**

| Aspect | V1 | V2 |
|--------|----|----|
| **Parallel Processing** | ❌ None | ✅ Concept set validation |
| **Agent Complexity** | 🔴 High (all decisions) | 🟢 Low (focused tasks) |
| **Tool Calls** | 15+ per loop | 1 per concept set + decision |
| **Debugging** | 🔴 Hard (complex logs) | 🟢 Easy (clear phases) |
| **Max Iterations** | 15 (often hit) | 3 (usually 1-2) |
| **Success Rate** | ~30% (empty output) | Expected ~90%+ |

---

## 🧪 **Testing**

### **Run V2 Pipeline:**
```bash
cd projects/concept_discovery
uv run flujo run --file pipeline_v2.yaml --input "Lennox Gastaut Syndrome and Diabetes type 2"
```

### **Compare with V1:**
```bash
# V1 (original)
uv run flujo run --input "Lennox Gastaut Syndrome and Diabetes type 2"
```

### **Expected Behavior:**

**Phase 1 (Decomposition):**
- ✅ Find 2 concept sets
- ✅ 10 candidates per set

**Phase 2 (Validation - Parallel):**
- ✅ 2 parallel validation calls
- ✅ Quality scores calculated
- ⚠️ May identify false positives (e.g., "Term pregnancy" for LGS)

**Phase 3 (Decision):**
- ✅ Decide based on quality
- If quality < 8 → proceed to Phase 4
- If quality >= 8 → skip to Phase 5

**Phase 4 (Refinement - if needed):**
- ✅ Remove false positives
- ✅ Re-validate (parallel)
- ✅ Re-decide
- Max 3 iterations

**Phase 5 (Finalization):**
- ✅ Output in ATLAS format
- ✅ `included_concepts` populated
- ✅ `excluded_concepts` available

---

## 🎓 **Key Learnings for Future Pipelines**

1. **Break down complex decisions** into focused agents
2. **Use `map` for parallel processing** when iterating over collections
3. **Separate validation from decision-making**
4. **Store intermediate results** in `context.scratchpad`
5. **Limit loop iterations** and accept "good enough" results
6. **Clear outputs** make debugging easier

---

## 🔄 **Migration Guide**

### **To switch to V2:**

1. **Rename pipelines:**
   ```bash
   mv pipeline.yaml pipeline_v1_old.yaml
   mv pipeline_v2.yaml pipeline.yaml
   ```

2. **Update flujo.toml** (if needed):
   ```toml
   [settings]
   enabled_template_filters = ["tojson", "default", "upper", "lower"]
   ```

3. **Test thoroughly:**
   ```bash
   make validate-concept_discovery
   uv run flujo run --input "test cohort definition"
   ```

---

## 📝 **Notes**

- V2 uses **GPT-5-Mini** for all agents (cost-effective)
- Parallel validation runs **concurrently** (faster execution)
- Refinement loop has **max 3 iterations** (prevents runaway)
- Quality threshold is **8/10** (configurable in agent prompt)
- Helper functions are **reusable** for other pipelines

