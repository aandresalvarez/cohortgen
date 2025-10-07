# Phase 2 Optimizations - Implementation Plan

## Goal
Reduce Stage 2 from **102s → 40-50s** (additional 50-60s saved)
Reduce Total from **228s → 150-160s** (30% additional improvement)

---

## Optimizations

### 1. LRU Concept Cache (Priority: HIGH)
**Savings**: 20-40 seconds

#### Problem
We re-search the same common concepts every run:
- "diabetes" searched 100+ times across all users
- "hypertension" searched 50+ times
- etc.

#### Solution
Implement functools.lru_cache for ATHENA searches:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def search_athena_cached(query: str, domain: str, vocab_tuple: tuple) -> str:
    """Cached wrapper for search_athena."""
    vocab_list = list(vocab_tuple) if vocab_tuple else None
    result = search_athena(ctx={}, query=query, domain=domain, 
                          vocabulary=vocab_list, standard_only=True, top_k=SEARCH_TOP_K)
    return json.dumps(result)  # Cache JSON string

def search_athena_with_cache(ctx, query, domain, vocabulary=None, **kwargs):
    """Use cache if appropriate, otherwise call directly."""
    if vocabulary:
        vocab_tuple = tuple(sorted(vocabulary))  # Hashable
    else:
        vocab_tuple = None
    
    cached_json = search_athena_cached(query.lower().strip(), domain, vocab_tuple)
    return json.loads(cached_json)
```

**Also cache concept details**:
```python
@lru_cache(maxsize=2000)
def get_concept_details_cached(concept_ids_tuple: tuple) -> str:
    """Cached wrapper for concept details."""
    result = get_concept_details(ctx={}, concept_ids=list(concept_ids_tuple))
    return json.dumps(result)
```

#### Implementation
- Add to `projects/cd/tools.py`
- Replace direct `search_athena` calls with `search_athena_with_cache`
- Cache persists across runs within same process
- Clear cache with `search_athena_cached.cache_clear()` if needed

---

### 2. Optimized Fast Mode (Priority: HIGH)
**Savings**: 60-80 seconds (in fast mode)

#### Current Fast Mode
```python
MAX_CONCEPT_SETS = 5
MAX_QUERIES_PER_SET = 3
max_visits = 50
max_depth = 2
```

#### Optimized Fast Mode
```python
# For fast mode
FAST_MODE_SETTINGS = {
    "MAX_CONCEPT_SETS": 3,        # ↓ 40% (5 → 3)
    "MAX_QUERIES_PER_SET": 2,     # ↓ 33% (3 → 2)
    "max_visits": 20,             # ↓ 60% (50 → 20)
    "max_depth": 1,               # ↓ 50% (2 → 1)
    "BATCH_SIZE": 5,              # ↑ 67% (3 → 5, larger batches)
    "PER_SET_TIME_LIMIT": 10,     # ↓ 33% (15 → 10)
    "MAX_ACCEPTED_PER_SET": 2,    # ↓ 33% (3 → 2)
}

# For normal mode (current defaults)
NORMAL_MODE_SETTINGS = {
    "MAX_CONCEPT_SETS": 5,
    "MAX_QUERIES_PER_SET": 3,
    "max_visits": 50,
    "max_depth": 2,
    "BATCH_SIZE": 3,
    "PER_SET_TIME_LIMIT": 15,
    "MAX_ACCEPTED_PER_SET": 3,
}
```

#### Implementation
1. Add `fast_mode` parameter to `run_intelligent_concept_discovery()`
2. Apply settings based on mode
3. Update UI to pass `fast_mode` from user selection

**Quality Trade-off**: 
- Fast mode: ~90-95% quality (may miss rare synonyms)
- Normal mode: ~98% quality
- User chooses based on need

---

### 3. Faster LLM Models for Decomposition (Priority: MEDIUM)
**Savings**: 15-25 seconds

#### Current Models
```python
# Decomposer: gpt-4o-mini (slower but high quality)
decomposer_agent = Agent("openai:gpt-4o-mini", ...)

# Candidate aggregator: gpt-4o-mini
candidate_aggregator_agent = Agent("openai:gpt-4o-mini", ...)

# Analyzer: gpt-4o-mini (keep this one - critical for quality)
concept_analyzer_agent = Agent("openai:gpt-4o-mini", ...)
```

#### Optimized Models
```python
# Use gpt-3.5-turbo for decomposition (3-5x faster, 90-95% accuracy)
decomposer_agent = Agent("openai:gpt-3.5-turbo", ...)

# Use gpt-3.5-turbo for candidate aggregation (less critical)
candidate_aggregator_agent = Agent("openai:gpt-3.5-turbo", ...)

# KEEP gpt-4o-mini for analysis (critical for quality)
concept_analyzer_agent = Agent("openai:gpt-4o-mini", ...)
```

**Rationale**:
- Decomposition is straightforward (identify conditions, drugs, etc.)
- Candidate aggregation is simple selection
- Analysis requires nuance (keep high-quality model)

**Quality Trade-off**: Minimal (~2-3% accuracy loss on decomposition)

---

### 4. Additional Quick Wins

#### A. Reduce SEARCH_TOP_K in Fast Mode
```python
# Normal mode
SEARCH_TOP_K = 10

# Fast mode
SEARCH_TOP_K = 5  # Fewer candidates to evaluate
```

#### B. Skip Relationship Exploration in Fast Mode
```python
if not fast_mode:
    # Explore relationships (maps to, is a, etc.)
    relationships = get_concept_relationships(...)
else:
    # Skip relationships, rely on initial search only
    relationships = []
```

---

## Implementation Order

### Phase 2A (1-2 hours)
1. ✅ LRU cache for search_athena
2. ✅ LRU cache for get_concept_details
3. ✅ Test cache hit rates

**Expected**: 228s → 190-200s (10-15% improvement)

---

### Phase 2B (2-3 hours)
4. ✅ Fast mode parameter implementation
5. ✅ Apply optimized settings in fast mode
6. ✅ UI integration (fast mode checkbox)

**Expected**: Fast mode: 228s → 120-140s (40-50% improvement)

---

### Phase 2C (1-2 hours)
7. ✅ Switch decomposer to gpt-3.5-turbo
8. ✅ Switch candidate aggregator to gpt-3.5-turbo
9. ✅ Test quality impact

**Expected**: Additional 15-25s saved

---

## Testing Strategy

### Cache Testing
```bash
# Run 1: Cold cache
make run-stage2 RUN_ID=test1
# Note duration

# Run 2: Warm cache (same cohort)
make run-stage2 RUN_ID=test2
# Should be significantly faster
```

### Fast Mode Testing
```bash
# Normal mode
echo "diabetes patients" | uv run python find_concepts.py
# Note concepts found

# Fast mode
FAST_MODE=1 echo "diabetes patients" | uv run python find_concepts.py
# Compare concepts - should be 90-95% overlap
```

---

## Expected Results

### Conservative Scenario
| Optimization | Time Saved |
|--------------|------------|
| LRU cache (normal mode) | 15s |
| Fast mode settings | 60s |
| Faster LLM models | 15s |
| **Total** | **90s** |

**Normal mode**: 228s → 213s (7% improvement)
**Fast mode**: 228s → 138s (40% improvement)

---

### Optimistic Scenario
| Optimization | Time Saved |
|--------------|------------|
| LRU cache (with high hit rate) | 40s |
| Fast mode settings | 80s |
| Faster LLM models | 25s |
| **Total** | **145s** |

**Normal mode**: 228s → 188s (18% improvement)
**Fast mode**: 228s → 108s (53% improvement)

---

## Quality Validation

After each optimization, validate:

1. **Concept count**: Should be ≥90% of original
2. **Standard concepts**: Should be 100% standard
3. **Domain correctness**: Should be 100% correct domain
4. **SQL validation**: Should pass BigQuery dry run

---

## Rollback Plan

If quality degrades:
1. **Cache issues**: Clear cache with `.cache_clear()`
2. **Fast mode too aggressive**: Increase limits (visits, depth)
3. **LLM model too weak**: Revert to gpt-4o-mini

---

## Configuration

New environment variables:
```bash
# Cache size
ATHENA_SEARCH_CACHE_SIZE=1000
CONCEPT_DETAILS_CACHE_SIZE=2000

# Fast mode (set by UI)
FAST_MODE=0  # or 1

# LLM models
DECOMPOSER_MODEL=gpt-3.5-turbo  # or gpt-4o-mini
AGGREGATOR_MODEL=gpt-3.5-turbo  # or gpt-4o-mini
```

---

## Success Criteria

✅ Normal mode: <200s (vs 228s baseline)
✅ Fast mode: <140s (vs 228s baseline)
✅ Quality: ≥90% concept overlap
✅ Cache hit rate: ≥30% (after first few runs)
✅ No BigQuery SQL validation failures

---

## Next: Phase 3

After Phase 2, consider:
- Simple cohort detection (auto-skip Stage 1)
- Parallel SQL validation
- Progress streaming
- Target: <60s normal mode, <30s fast mode


