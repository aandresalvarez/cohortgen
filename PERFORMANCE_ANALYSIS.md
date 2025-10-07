# OMOP Cohort Workflow - Performance Analysis & Optimization

**Current Performance**: ~285 seconds (4.8 minutes) for full pipeline  
**Target**: <60 seconds without quality loss

---

## 📊 **Current Bottlenecks** (From Real Run Data)

| Stage | Duration | % of Total | Status |
|-------|----------|------------|--------|
| **Stage 1: Clarification** | 81.8s | 29% | ⚠️ Moderate |
| **Stage 2: Concept Discovery** | 161.6s | **57%** | 🔴 **CRITICAL** |
| **Stage 3: SQL Generation** | 40.4s | 14% | ⚠️ Moderate |
| **Stage 4: Analytics** | 1.3s | 0.5% | ✅ Fast |
| **Total** | 285.1s | 100% | |

### 🔴 **Critical Bottleneck: Stage 2 (Concept Discovery)**

Takes **2 minutes 41 seconds** - this is where we need to focus!

---

## 🎯 **Optimization Strategies**

### 1. ⚡ **Parallelize Concept Set Discovery** (Stage 2)

**Problem**: Each concept set is processed sequentially
```python
for concept_set in plan.concept_sets:  # ❌ Sequential
    result = explore_concept_set(concept_set)
```

**Solution**: Process concept sets in parallel
```python
with ThreadPoolExecutor(max_workers=5) as executor:  # ✅ Parallel
    futures = [executor.submit(explore_concept_set, cs) for cs in plan.concept_sets]
    results = [f.result() for f in futures]
```

**Impact**: 
- 7 concept sets × 23s each = 161s → ~30-40s (4-5x speedup)
- **Estimated savings: 120+ seconds**

---

### 2. 🚀 **Smarter Early Exit** (Stage 2)

**Current**: Explores up to 50 visits even when exact match found early

**Solution**: Immediate exit on exact standard matches
```python
# Add to explorer agent system prompt:
"""
FAST EXIT RULE:
If you find an EXACT match that is:
- Standard concept (S)
- Correct domain
- Name matches perfectly
→ IMMEDIATELY return with action="finish"

Do NOT continue exploring if you have a perfect match.
"""
```

**Impact**:
- Common concepts (diabetes, heart failure) found in first search
- **Estimated savings: 30-60 seconds for simple cohorts**

---

### 3. 💾 **Concept Cache** (Stage 2)

**Problem**: Re-searching common concepts (diabetes, hypertension, etc.) every run

**Solution**: In-memory LRU cache for ATHENA searches
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def search_athena_cached(query: str, domain: str, vocab: tuple) -> List[Dict]:
    return search_athena(query, domain, list(vocab))
```

**Impact**:
- 80% of cohorts use common 20% of concepts
- **Estimated savings: 20-40 seconds on repeated concepts**

---

### 4. 🎨 **Faster LLM Models** (All Stages)

**Current**: 
- Stage 1: gpt-4o-mini (reasonable)
- Stage 2: gpt-4o-mini (reasonable)
- Stage 3 generator: gpt-4o-mini → **gpt-o1-mini** ✅ (already upgraded)
- Stage 3 fixer: gpt-4o → **gpt-o1** ✅ (already upgraded)

**Alternative**: Use gpt-3.5-turbo for decomposition (Stage 1, Stage 2 decomposer)
```python
decomposer_agent = Agent(
    "openai:gpt-3.5-turbo",  # ⚡ 3-5x faster, 10x cheaper
    ...
)
```

**Quality Trade-off**:
- gpt-3.5-turbo: 90-95% accuracy vs gpt-4o-mini
- Good enough for decomposition tasks

**Impact**: **Estimated savings: 15-25 seconds**

---

### 5. 🔬 **Reduced Exploration Depth** (Stage 2 - Fast Mode)

**Current Fast Mode**:
```python
MAX_CONCEPT_SETS = 5
MAX_QUERIES_PER_SET = 3
max_visits = 50
max_depth = 2
```

**Optimized Fast Mode**:
```python
MAX_CONCEPT_SETS = 3  # Reduce concept sets
MAX_QUERIES_PER_SET = 2  # Fewer queries per set
max_visits = 20  # ↓ 60% reduction
max_depth = 1  # ↓ 50% reduction
BATCH_SIZE = 5  # Larger batches
```

**Impact**: **Estimated savings: 60-80 seconds in fast mode**

---

### 6. 📦 **Batch ATHENA Requests** (Stage 2)

**Current**: Individual API calls for each concept
```python
for concept_id in candidate_ids:  # ❌ N API calls
    details = get_concept_details([concept_id])
```

**Solution**: Batch concept detail requests
```python
# Single API call for all candidates
all_details = get_concept_details(candidate_ids)  # ✅ 1 API call
```

**Impact**: **Estimated savings: 10-15 seconds**

---

### 7. ⏭️ **Skip Stage 1 for Simple Cohorts** (Optional)

**Problem**: Simple cohorts ("diabetes patients") don't need 10 clarification questions

**Solution**: Detect simple cohorts and auto-complete
```python
def is_simple_cohort(description: str) -> bool:
    # Check if description is already clear
    has_condition = any(word in description.lower() for word in ["diabetes", "hypertension", "cancer"])
    is_short = len(description.split()) < 10
    return has_condition and is_short

if is_simple_cohort(description):
    # Skip clarification, use description directly
    cohort_def = auto_extract(description)  # Fast extraction
else:
    cohort_def = run_clarification_loop(description)  # Full clarification
```

**Impact**: **Estimated savings: 70-80 seconds for simple cohorts**

---

### 8. 🔄 **Parallel SQL Validation Attempts** (Stage 3)

**Current**: Sequential validation → fix → validate → fix
```python
for iteration in range(1, max_fix_iterations + 1):  # ❌ Sequential
    validation_result = validate_bigquery_sql(current_sql)
    if validation_result.success:
        break
    current_sql = fix_sql(current_sql, validation_result.errors)
```

**Solution**: Generate multiple SQL variations in parallel
```python
# Generate 3 variations simultaneously
variations = await asyncio.gather(
    generate_sql_variant(cohort_input, strategy="conservative"),
    generate_sql_variant(cohort_input, strategy="standard"),
    generate_sql_variant(cohort_input, strategy="aggressive"),
)

# Validate all in parallel
results = await asyncio.gather(*[validate(sql) for sql in variations])

# Use first valid one
valid_sql = next((sql for sql, result in zip(variations, results) if result.success), None)
```

**Impact**: **Estimated savings: 15-20 seconds**

---

### 9. 🎯 **Smart Vocabulary Filtering** (Stage 2)

**Problem**: Searching across all vocabularies when domain is known

**Current**:
```python
search_athena(query="diabetes", domain="Condition")  # Searches all vocabs
```

**Optimized**:
```python
DOMAIN_VOCAB_MAP = {
    "Condition": ["SNOMED"],  # Skip ICD9, ICD10, etc.
    "Drug": ["RxNorm"],
    "Procedure": ["SNOMED", "CPT4"],
    "Measurement": ["LOINC"],
}

search_athena(
    query="diabetes",
    domain="Condition",
    vocabulary=DOMAIN_VOCAB_MAP["Condition"]  # ✅ Focused search
)
```

**Impact**: **Estimated savings: 10-15 seconds**

---

### 10. 🔁 **Streaming Results to UI** (UX Improvement)

**Not faster, but feels faster!**

Currently: User sees nothing until stage completes  
Better: Stream progress in real-time

```python
# Emit progress events
emit_progress("Found 3 diabetes concepts...")
emit_progress("Exploring relationships...")
emit_progress("Validating standard concepts...")
```

**Impact**: **Perceived 2-3x speedup** (user sees progress)

---

## 📈 **Cumulative Impact Estimates**

### Conservative Scenario (All Optimizations)

| Optimization | Time Saved |
|--------------|------------|
| 1. Parallel concept sets | 120s |
| 2. Early exit | 30s |
| 3. Concept cache | 20s |
| 4. Faster models | 15s |
| 5. Reduced depth (fast mode) | 60s |
| 6. Batch ATHENA | 10s |
| 7. Skip Stage 1 (simple) | 70s |
| 8. Parallel SQL validation | 15s |
| 9. Smart vocab filtering | 10s |
| **Total Savings** | **350s** |

### Realistic Projection

**Current**: 285 seconds (4.8 minutes)

**After Core Optimizations** (1, 2, 3, 6, 9):
- **~100 seconds (1.7 minutes)** - 65% reduction

**After All Optimizations**:
- **~50-60 seconds (1 minute)** - 79% reduction

**Fast Mode** (aggressive):
- **~30-40 seconds** - 86% reduction

---

## 🛠️ **Implementation Priority**

### Phase 1: Quick Wins (1-2 hours)
1. ✅ Parallel concept set discovery
2. ✅ Early exit on exact matches
3. ✅ Smart vocabulary filtering
4. ✅ Batch ATHENA requests

**Expected**: 285s → ~120s (58% reduction)

### Phase 2: Moderate Effort (3-4 hours)
5. ✅ Concept cache
6. ✅ Faster LLM models (gpt-3.5-turbo for decomposition)
7. ✅ Reduced exploration depth (fast mode tuning)

**Expected**: 120s → ~70s (75% total reduction)

### Phase 3: Advanced (1-2 days)
8. ✅ Parallel SQL validation
9. ✅ Simple cohort detection
10. ✅ Streaming progress (UX)

**Expected**: 70s → ~45-55s (81-84% total reduction)

---

## ⚖️ **Quality vs Speed Trade-offs**

### No Quality Loss ✅
- Parallelization (same work, faster)
- Caching (reuses exact same results)
- Early exit (stops when perfect match found)
- Batch requests (same data, fewer calls)
- Smart vocab filtering (searches same concepts, faster)

### Minimal Quality Loss (~5%) ⚠️
- Reduced exploration depth (may miss rare synonyms)
- Faster LLM models for decomposition (90-95% accuracy vs 98%)
- Parallel SQL variations (may pick suboptimal SQL)

### User-Controlled Trade-off 🎛️
- **Normal Mode**: Full quality (70-100s)
- **Fast Mode**: Slight trade-off (30-40s)
- Let user choose based on use case

---

## 🎯 **Recommended Implementation Plan**

### Week 1: Core Optimizations
```python
# 1. Parallel concept discovery
# 2. Early exit logic
# 3. Batch ATHENA calls
# 4. Smart vocab filtering
```

**Target**: 285s → 120s

### Week 2: Caching & Fast Mode
```python
# 5. LRU cache for ATHENA
# 6. Optimized fast mode settings
# 7. Faster models for non-critical tasks
```

**Target**: 120s → 70s

### Week 3: Advanced Features
```python
# 8. Simple cohort detection
# 9. Parallel SQL validation
# 10. Progress streaming
```

**Target**: 70s → 50s

---

## 📊 **Monitoring Metrics**

Add to run metadata:
```python
{
  "duration_seconds": 50.2,
  "stage_durations": {
    "stage1": 15.3,
    "stage2": 25.1,  # Track concept set timings
    "stage3": 8.5,
    "stage4": 1.3
  },
  "stage2_details": {
    "concept_sets": 7,
    "parallel_execution": true,
    "cache_hits": 3,
    "athena_calls": 12,
    "llm_calls": 8
  }
}
```

---

## 🚀 **Next Steps**

1. **Implement Phase 1** (parallel + early exit + batch)
2. **Measure actual speedup** on 10 test cohorts
3. **Tune fast mode** settings based on data
4. **Add performance dashboard** to UI
5. **Iterate** based on user feedback

---

**Goal**: <60 seconds for 90% of cohorts, <30 seconds in fast mode, with minimal quality loss.

