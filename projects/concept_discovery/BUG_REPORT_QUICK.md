# 🐛 Quick Bug Report: `flujo lens show` Hangs

**Issue:** `flujo lens show <run_id>` command hangs indefinitely and never returns.

---

## Reproduce

```bash
cd projects/concept_discovery

# 1. Run pipeline (works fine)
uv run flujo run --input "Type 2 Diabetes"
# Output: Run ID: run_ec00798feed049fb8b1e1c8bcb97eb17

# 2. List runs (works fine)
uv run flujo lens list
# Shows: run_ec00798feed049… | completed | 2025-10-01T22:14:5…

# 3. Show run details (HANGS)
uv run flujo lens show run_ec00798feed049fb8b1e1c8bcb97eb17
# Result: Hangs forever, must Ctrl+C to exit
```

---

## Environment

- **State backend:** `sqlite:///.flujo/flujo_ops.db`
- **OS:** macOS
- **Run status:** completed (7 steps, 8 spans)
- **Database:** Intact, all data present

---

## Data Confirms Issue is in Rendering

Direct SQLite query works instantly:

```bash
sqlite3 .flujo/flujo_ops.db \
  "SELECT step_name, status FROM steps \
   WHERE run_id='run_ec00798feed049fb8b1e1c8bcb97eb17' \
   ORDER BY created_at;"
```

Output:
```
parse_initial_payload|completed
decompose_concept_sets|completed
normalize_concept_plan|completed
search_initial_candidates|completed
exploration_loop|completed
store_concept_sets|completed
emit_for_parent|completed
```

**Conclusion:** Data exists and is accessible. Bug is in `lens show` logic.

---

## Impact

- ❌ Cannot inspect runs via CLI
- ❌ Debugging requires SQL knowledge
- ❌ No error message or timeout
- ✅ Workaround: Query SQLite directly

**Severity:** Medium (core feature broken, but workarounds exist)

---

## Suggested Fixes

1. **Add timeout** (30s default)
2. **Add progress indication** while loading
3. **Stream output** instead of buffering
4. **Profile/debug** what's hanging
5. **Support partial run_id matching**

---

## Workaround

Query database directly:

```bash
# List runs
sqlite3 -header -column .flujo/flujo_ops.db \
  "SELECT run_id, status, created_at FROM runs \
   ORDER BY created_at DESC LIMIT 10;"

# Get steps for a run
sqlite3 -header -column .flujo/flujo_ops.db \
  "SELECT step_name, status FROM steps \
   WHERE run_id='<FULL_RUN_ID>' ORDER BY created_at;"

# Get final output
sqlite3 .flujo/flujo_ops.db \
  "SELECT output FROM steps \
   WHERE run_id='<FULL_RUN_ID>' AND step_name='emit_for_parent';"
```

Or use `--debug-export` flag:
```bash
flujo run --input "query" --debug-export debug/run.json
flujo lens from-file debug/run.json
```

---

**Full report:** See `BUG_REPORT_flujo_lens.md` for detailed analysis.

