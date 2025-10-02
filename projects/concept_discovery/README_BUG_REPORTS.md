# 🐛 Bug Report Files for Flujo Team

This directory contains bug reports and workarounds for issues discovered during development.

---

## Files Created

### 📄 **BUG_REPORT_flujo_lens.md** (Complete Report)
**Comprehensive bug report** with:
- Detailed reproduction steps
- Environment information
- Root cause analysis
- Database state verification
- Impact assessment
- Suggested fixes
- Testing recommendations

**Use this for:** Creating GitHub issues, detailed technical discussions

---

### 📄 **BUG_REPORT_QUICK.md** (Quick Summary)
**Condensed version** with:
- Essential reproduction steps
- Quick workarounds
- Key findings
- 1-page format

**Use this for:** Quick sharing, Slack messages, initial bug reports

---

### 🔧 **inspect_run.sh** (Workaround Tool)
**Shell script** to inspect runs directly from SQLite database.

**Usage:**
```bash
# List recent runs
./inspect_run.sh list

# Show run details
./inspect_run.sh show run_ec00798feed049

# Get final output
./inspect_run.sh final run_ec00798feed049

# Get specific step output
./inspect_run.sh output run_ec00798feed049 decompose_concept_sets

# Help
./inspect_run.sh help
```

**Features:**
- ✅ Partial run_id matching
- ✅ Colored output
- ✅ JSON pretty-printing
- ✅ Works instantly (no hanging)

---

## Issue Summary

### Problem
`flujo lens show <run_id>` hangs indefinitely when trying to display run details.

### Affected
- ❌ `flujo lens show`
- ✅ `flujo lens list` (works fine)
- ✅ Pipeline execution (works fine)
- ✅ Data storage (works fine)

### Root Cause
Likely an issue in trace rendering or output formatting logic when using SQLite backend.

### Severity
**Medium** - Core debugging feature broken, but workarounds exist.

---

## How to Submit

### To Flujo GitHub Repository:

1. **Create Issue:**
   - Go to: https://github.com/aandresalvarez/flujo/issues
   - Click "New Issue"
   - Title: "`flujo lens show` command hangs indefinitely"

2. **Copy Content:**
   - Use **BUG_REPORT_flujo_lens.md** for complete details
   - Or use **BUG_REPORT_QUICK.md** for quick report

3. **Attach:**
   - Both markdown files
   - `inspect_run.sh` as workaround reference

### To Flujo Discord/Slack:

1. **Share Quick Version:**
   - Copy content from **BUG_REPORT_QUICK.md**
   - Mention: "Full details available"

2. **Provide Workaround:**
   - Share `inspect_run.sh` script
   - Explain: "Works perfectly as temporary solution"

---

## Verification Steps

Maintainers can verify the bug:

```bash
# 1. Clone concept_discovery project
cd projects/concept_discovery

# 2. Ensure SQLite backend
grep "state_uri" flujo.toml
# Should show: state_uri = "sqlite:///.flujo/flujo_ops.db"

# 3. Run pipeline
uv run flujo run --input "Test query"

# 4. Try lens show (will hang)
uv run flujo lens show <run_id_from_step_3>
# Hangs forever - must Ctrl+C

# 5. Verify data exists
sqlite3 .flujo/flujo_ops.db "SELECT COUNT(*) FROM steps;"
# Returns number of steps (proves data is there)

# 6. Use workaround
./inspect_run.sh show <run_id_from_step_3>
# Works instantly!
```

---

## Impact on Development

### Before Fix
- ❌ Cannot use `flujo lens show` for debugging
- ❌ Must learn SQL to inspect runs
- ❌ Poor developer experience

### With Workaround
- ✅ `inspect_run.sh` provides same functionality
- ✅ Actually faster than original command
- ✅ Supports partial run_id matching
- ⚠️ Requires understanding of project structure

### After Fix
- ✅ Native `flujo lens` commands work
- ✅ Better integration with other tools
- ✅ Consistent CLI experience

---

## Additional Context

This issue was discovered while:
1. Reviewing the `concept_discovery` pipeline
2. Updating documentation (`llm.md`)
3. Fixing type mismatches in the pipeline
4. Testing with SQLite backend for persistence

The pipeline itself works perfectly - this is purely a CLI inspection tool bug.

---

## Contact

For questions about these bug reports:
- **Project:** `cohortgen/projects/concept_discovery`
- **Files:** All in project root directory
- **Database:** `.flujo/flujo_ops.db` (available for inspection)
- **Test Run ID:** `run_ec00798feed049fb8b1e1c8bcb97eb17`

---

## Status

- ✅ **Bug:** **FIXED** by Flujo team!
- 🟢 **Resolution:** `flujo lens show` now displays output correctly
- 🟡 **Performance:** Minor slowness remains (acceptable)
- 🔵 **Workaround:** `inspect_run.sh` kept (still useful, faster)

---

## 🎉 Update: Bug Fixed!

**Date:** 2025-10-01

The Flujo team has successfully patched the `flujo lens` functionality!

### What Changed:
- ✅ `flujo lens show` now displays formatted output
- ✅ Run summary appears within 10 seconds
- ✅ Step tables show correctly
- ⚠️ May be slower than workaround script

### Current Status:
**The critical bug is RESOLVED.** The command is now usable for daily operations.

**See:** `BUG_REPORT_STATUS.md` for detailed status update and testing results.

---

**Last Updated:** 2025-10-01  
**Reported By:** User via AI Assistant during pipeline development  
**Resolved By:** Flujo team (2025-10-01)

