# Test Phase 1 Optimizations

## Quick Test

### Option 1: Test Stage 2 Directly

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen/projects/cd
echo 'demo' | uv run python find_concepts.py
```

**What to look for**:
- `🚀 Phase 1 Optimization: Processing X concept sets in parallel`
- Completion messages appearing out of order (indicates parallel execution)
- Total duration < 60s (vs ~160s before)

---

### Option 2: Test Full Workflow via UI

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen
make run-ui
```

Then:
1. Create a new run
2. **Cohort Input**: "Prior heart failure diagnosis, end-stage renal disease"
3. Click "🚀 Start Run"
4. Watch Stage 2 progress

**Expected**:
- Stage 2 duration: 40-60s (vs ~160s before)
- Parallel processing visible in Stage 2 log
- Total pipeline: ~2.7-3.1 min (vs ~4.8 min before)

---

### Option 3: Quick Syntax Check

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen
python -m py_compile projects/cd/find_concepts.py
echo "✅ No syntax errors!"
```

---

## Performance Comparison

### Before Phase 1:
```
Stage 1: 81.8s   (29%)
Stage 2: 161.6s  (57%) ← BOTTLENECK
Stage 3: 40.4s   (14%)
Stage 4: 1.3s    (0.5%)
───────────────────────
Total:   285.1s  (4.8 min)
```

### After Phase 1 (Expected):
```
Stage 1: 81.8s   (49%)
Stage 2: 40-60s  (24-36%) ← OPTIMIZED 4-5x faster!
Stage 3: 40.4s   (24%)
Stage 4: 1.3s    (0.8%)
───────────────────────
Total:   163-183s (2.7-3.1 min)

Improvement: 102-122s saved (36-43% faster)
```

---

## What to Monitor

Look for these optimization indicators in the logs:

### 1. Parallel Execution
```
🚀 Phase 1 Optimization: Processing 7 concept sets in parallel (max_workers=5)
✅ Completed: Heart Failure
✅ Completed: Diabetes  
✅ Completed: ESRD
```
*Note: Completion order ≠ input order = parallel execution*

### 2. Batch API Calls
```
Fetching details for 3 concepts (batched)...
```
*Instead of N individual "Fetching details for concept X..." messages*

### 3. Early Exit
```
✅ Collected 3 accepted anchors; stopping exploration
```
*Stops early when perfect matches found*

### 4. Smart Vocabulary Filtering
*Look for faster search times for common concept types*

---

## Troubleshooting

### If Stage 2 is Still Slow

1. **Check parallelization**:
   ```bash
   # Increase workers (if you have >4 CPU cores)
   export PARALLEL_CONCEPT_SETS=7
   ```

2. **Check for errors**:
   - Look for "❌ Failed to process..." messages
   - Check if API rate limits are hit

3. **Reduce parallelization** (if rate-limited):
   ```bash
   export PARALLEL_CONCEPT_SETS=2
   ```

### If You See Interleaved Print Statements

This is normal with parallel execution. It doesn't affect functionality.

To reduce:
```bash
export PARALLEL_CONCEPT_SETS=2  # Less parallelism = less interleaving
```

---

## Success Criteria

✅ Stage 2 completes in <60s (vs ~160s before)  
✅ Parallel execution message appears  
✅ Batch API call messages appear  
✅ No syntax/import errors  
✅ Concept sets still found correctly  

If all criteria met → **Phase 1 successful!**


