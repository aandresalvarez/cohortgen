# Flujo Lens Commands Update

**Date:** 2025-10-01  
**Update Type:** Documentation Enhancement  
**File Updated:** `llm.md`

---

## 🎉 New Flujo Lens Commands Documented

The Flujo team has implemented enhanced `lens` commands with improved usability. These updates have been added to the documentation.

---

## ✨ New Commands Added

### Quick Access Commands

```bash
# Quick find with partial ID
flujo lens get abc123

# Show run details (supports partial IDs)
flujo lens show abc123
```

### Output Format Options

```bash
# Show with all details
flujo lens show abc123 --verbose

# Show final output only
flujo lens show abc123 --final-output

# Export as JSON
flujo lens show abc123 --json
```

### Performance Control

```bash
# Adjust timeout if needed (default: 30 seconds)
flujo lens show abc123 --timeout 30
```

---

## 📚 Documentation Updates in llm.md

### 1. Enhanced "Tracing and Debugging" Section
**Location:** CLI Commands → Tracing and Debugging

**Added:**
- All new `lens` command variations
- `flujo lens get` for quick ID lookup
- `--verbose`, `--final-output`, `--json`, `--timeout` options
- Feature explanations for partial ID matching and output formats

### 2. New "Debugging Workflows" Section
**Location:** After Troubleshooting, before Summary

**Includes:**
- **Quick Debugging Workflow** - Step-by-step guide
- **Debugging Specific Issues** - Targeted commands for common scenarios
- **Tips for Efficient Debugging** - Best practices
- **Practical Examples** - Real-world command combinations

**Content:**
- 7-step debugging workflow
- Examples for checking execution, final output, performance
- JSON export with `jq` filtering examples
- Performance analysis with `spans`
- Tips for using partial IDs and timeouts

### 3. Updated Troubleshooting Section
**Location:** Loop debugging example

**Enhanced:**
- Replaced single `flujo lens trace` example
- Added multi-command debugging approach
- Shows `list`, `show --verbose`, `--final-output`, `trace`

### 4. Updated Table of Contents
**Added:** Section 14 - Debugging Workflows

---

## 🎯 Key Features Documented

### Partial ID Matching
Use shortened run IDs for convenience:
```bash
# Instead of:
flujo lens show run_ec00798feed049fb8b1e1c8bcb97eb17

# Use:
flujo lens show ec0079
```

### Multiple Output Formats
Choose the right level of detail:
- **Default**: Formatted summary with steps
- **`--verbose`**: All details including inputs/outputs
- **`--final-output`**: Just the pipeline result
- **`--json`**: Machine-readable format for scripting

### Quick Lookup
Fast ID resolution:
```bash
flujo lens get abc123
# Quickly find full run_id from partial match
```

### Configurable Timeout
Handle large runs:
```bash
flujo lens show abc123 --timeout 60
# Increase from default 30 seconds if needed
```

---

## 📖 New Documentation Sections

### Debugging Workflows Section

**Purpose:** Provide practical, step-by-step debugging guidance

**Structure:**
1. **Quick Debugging Workflow** - 7 steps from listing runs to full trace
2. **Debugging Specific Issues** - Targeted commands for:
   - Step-by-step execution verification
   - Final output validation
   - Performance analysis
   - JSON export for external tools
3. **Tips for Efficient Debugging** - 5 best practices

**Example Workflow:**
```bash
# 1. List recent runs
flujo lens list

# 2. Get quick overview
flujo lens get ec0079

# 3. Show full details
flujo lens show ec0079 --verbose

# 4. Check final output
flujo lens show ec0079 --final-output

# 5. Export for analysis
flujo lens show ec0079 --json > run_details.json

# 6. Check timing
flujo lens spans ec0079

# 7. See execution trace
flujo lens trace ec0079
```

---

## 🔍 Practical Examples Added

### JSON Export + jq Filtering
```bash
flujo lens show <run_id> --json | jq '.steps[] | {name: .name, status: .status}'
```

### Performance Analysis
```bash
flujo lens spans <run_id>  # See which steps took longest
```

### Quick Validation
```bash
flujo lens show <run_id> --final-output  # Verify pipeline result
```

---

## 📊 Impact

### Documentation Enhancements
- ✅ **+60 lines** added to llm.md
- ✅ **New section** "Debugging Workflows"
- ✅ **Enhanced** "Tracing and Debugging" CLI section
- ✅ **Updated** Table of Contents

### User Benefits
- ✅ **Faster debugging** with partial IDs
- ✅ **Better insights** with multiple output formats
- ✅ **Clearer guidance** with step-by-step workflows
- ✅ **More flexibility** with timeout and format options

### Coverage
- ✅ **All new commands** documented
- ✅ **Practical examples** provided
- ✅ **Best practices** included
- ✅ **Integration tips** (jq, scripting) added

---

## 🎓 Best Practices Documented

1. **Use partial IDs** - Copy first 6+ characters for faster typing
2. **Start with final output** - Use `--final-output` for quick verification
3. **Use JSON export** - Combine with `jq` for powerful filtering
4. **Check spans for performance** - Identify slow steps
5. **Increase timeout for large runs** - Use `--timeout` when needed

---

## 📝 Files Modified

| File | Changes | Lines Added |
|------|---------|-------------|
| `llm.md` | Enhanced CLI commands, new debugging section | +60 |
| `FLUJO_LENS_UPDATE.md` | This file (update log) | +250 |

---

## ✅ Validation

- ✅ No linter errors
- ✅ Table of Contents updated
- ✅ All links working
- ✅ Examples tested for syntax
- ✅ Formatting consistent

---

## 🚀 Next Steps for Users

1. **Update your workflows** to use new partial ID matching
2. **Try `--final-output`** for quick result checks
3. **Use `--json`** for scripting and automation
4. **Reference** the new Debugging Workflows section when troubleshooting

---

## 📚 Related Documentation

- **Main Guide:** `llm.md` - Complete Flujo LLM Guide
- **Bug Reports:** `projects/concept_discovery/BUG_REPORT_STATUS.md` - Original lens bug
- **Working Commands:** `projects/concept_discovery/FLUJO_LENS_WORKING.md` - Command reference

---

## 🙏 Acknowledgments

Thanks to the Flujo team for implementing these enhanced lens commands based on user feedback and bug reports!

---

**Last Updated:** 2025-10-01  
**Documentation Version:** v1.1 (lens commands enhanced)

