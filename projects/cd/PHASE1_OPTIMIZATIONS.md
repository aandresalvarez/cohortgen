# Phase 1 Optimizations - Implementation Plan

## Changes Made

### 1. Imports & Constants ✅
- Added `ThreadPoolExecutor, as_completed` from `concurrent.futures`
- Added `PARALLEL_CONCEPT_SETS = 5` constant
- Added `DOMAIN_VOCAB_MAP` for smart vocabulary filtering

### 2. Smart Vocabulary Filtering
**Location:** Every `search_athena` call
**Change:** Use `DOMAIN_VOCAB_MAP` to filter vocabularies by domain

Before:
```python
search_result = search_athena(
    ctx={},
    query=query,
    domain=concept_set.domain,
    vocabulary=concept_set.vocabulary,  # ❌ Searches all vocabs
    ...
)
```

After:
```python
# Use smart vocab filtering if domain is known
smart_vocab = DOMAIN_VOCAB_MAP.get(concept_set.domain, concept_set.vocabulary)
search_result = search_athena(
    ctx={},
    query=query,
    domain=concept_set.domain,
    vocabulary=smart_vocab if smart_vocab else concept_set.vocabulary,  # ✅ Focused search
    ...
)
```

### 3. Batch ATHENA Concept Details
**Location:** Inside the exploration loop
**Change:** Batch all concept detail requests per iteration

Before:
```python
for cid in ids:
    details_result = get_concept_details(ctx={}, concept_ids=[cid])  # ❌ N calls
    ...
```

After:
```python
# Batch fetch all concept details at once
all_details_result = get_concept_details(ctx={}, concept_ids=ids)  # ✅ 1 call
if all_details_result.get("success"):
    all_details = {c["concept_id"]: c for c in all_details_result.get("concepts", [])}
else:
    all_details = {}

# Then fetch relationships (can't batch these)
for cid in ids:
    details = all_details.get(cid, {})
    relationships_result = get_concept_relationships(ctx={}, concept_id=cid)
    ...
```

### 4. Early Exit Logic
**Location:** `concept_analyzer_agent` system prompt
**Change:** Add explicit early exit instructions

Add to system prompt:
```
CRITICAL FAST EXIT RULE:
If a concept is:
- Standard (S)  
- Correct domain
- Name matches perfectly (e.g., "Type 2 diabetes mellitus" for search "type 2 diabetes")
→ Mark as ACCEPTED and the system will stop exploring after collecting enough matches.

Do NOT continue exploring if you already have perfect standard matches!
```

### 5. Parallel Concept Set Processing
**Location:** `run_intelligent_concept_discovery` function
**Change:** Extract concept set processing to a helper function and parallelize

Create helper function:
```python
def _process_single_concept_set(
    concept_set, 
    max_visits: int,
    max_depth: int, 
    batch_size: int
) -> Dict[str, Any]:
    """Process a single concept set (extracted for parallelization)."""
    # Move the entire for-loop body here
    ...
    return final_concept_set
```

Then parallelize:
```python
# Sequential (old)
for concept_set in plan.concept_sets:
    result = process(concept_set)
    final_concept_sets.append(result)

# Parallel (new)
with ThreadPoolExecutor(max_workers=PARALLEL_CONCEPT_SETS) as executor:
    futures = {
        executor.submit(_process_single_concept_set, cs, max_visits, max_depth, batch_size): cs
        for cs in plan.concept_sets
    }
    
    for future in as_completed(futures):
        try:
            result = future.result()
            final_concept_sets.append(result)
        except Exception as e:
            concept_set = futures[future]
            print(f"❌ Failed to process {concept_set.name}: {e}")
            # Add empty concept set as fallback
            final_concept_sets.append({...})
```

## Expected Impact

| Optimization | Time Saved | Complexity |
|--------------|------------|------------|
| Smart vocab filtering | 10-15s | Low ⭐ |
| Batch ATHENA requests | 10-15s | Low ⭐ |
| Early exit logic | 30-60s | Low ⭐ |
| Parallel concept sets | 120s | Medium ⭐⭐ |
| **Total** | **~170-210s** | |

**Current**: 285s → **Target**: 75-115s (60-73% reduction)

## Implementation Order

1. ✅ Smart vocab filtering (5 min)
2. ✅ Batch ATHENA requests (10 min)
3. ✅ Early exit logic (5 min)
4. ⏳ Parallel concept sets (20-30 min)

## Testing

After implementation, test with:
```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen
make run-stage2 RUN_ID=test_performance
```

Monitor:
- Total duration
- Per-concept-set duration
- Number of ATHENA API calls
- Early exit frequency


