# llm.md Documentation Updates

**Date:** 2025-10-01  
**Based on:** Review of `projects/concept_discovery/` pipeline

---

## Summary of Changes

Updated the Flujo LLM Guide (`llm.md`) with insights gained from reviewing the production-ready `concept_discovery` pipeline. Added clarifications, best practices, and troubleshooting guidance to help LLMs create better Flujo pipelines.

---

## 1. Enhanced Agent Definitions Section

### Added: Tool-Calling Agent Pattern (NEW Section)

**Location:** After "Advanced Agent (GPT-5)" section

**What:** Complete documentation of tool-calling agents with example implementation

**Why:** The `concept_discovery` project demonstrates this pattern extensively but it wasn't documented

**Example Added:**
```yaml
agents:
  research_agent:
    model: "openai:gpt-4o"
    tools:
      - "skills.my_tools:search_database"
      - "skills.my_tools:fetch_api"
    output_schema:
      properties:
        action: { enum: [tool, finish] }
        tool_name: { type: string }
        tool_input: { type: object }
```

**Includes:**
- Tool registration syntax
- Output schema requirements
- Example tool implementation in Python
- Use cases and integration with loops

---

## 2. Clarified Step Type: Basic Step

### Added: Explicit vs Implicit `kind` Declaration

**Location:** Step Types Reference → Basic Step section

**What:** Warning about implicit steps and best practice recommendation

**Why:** The `concept_discovery` pipeline had several implicit steps (missing `kind: step`), which works but reduces clarity

**Example Added:**
```yaml
# ❌ Implicit (works but discouraged)
- name: process_data
  uses: agents.my_agent

# ✅ Explicit (recommended)
- kind: step
  name: process_data
  uses: agents.my_agent
```

**Impact:** Encourages consistent, maintainable code

---

## 3. Enhanced GPT-5 Model Settings Documentation

### Updated: Advanced Agent (GPT-5) Section

**Location:** Agent Definitions → Advanced Agent

**What:** 
- Added comments showing valid values (low/medium/high)
- Added explicit GPT-5-mini example
- Clarified nested format requirements

**Why:** The `concept_discovery` pipeline used a different format (`openai_reasoning_effort`) which doesn't match the documented format

**Clarification Added:**
```yaml
model_settings:
  reasoning: { effort: "medium" }  # low/medium/high
  text: { verbosity: "medium" }    # low/medium/high
```

---

## 4. New Common Pattern: Agentic Tool Exploration

### Added: Pattern #11 in Common Patterns Section

**Location:** Common Patterns → #11 Agentic Tool Exploration Pattern

**What:** Complete pattern showing:
- State initialization
- Agentic exploration loop
- Tool-calling agent with conditional execution
- Exit condition based on agent decision
- Final result extraction

**Why:** This is the core pattern used in `concept_discovery` and represents a sophisticated real-world use case

**References:** Direct link to `projects/concept_discovery/` as production implementation

---

## 5. Expanded Best Practices (5 New Practices)

### Added Best Practices #11-15

**Location:** Best Practices section

#### #11: Write Type-Safe Custom Skills
- Type hints requirement
- Multi-format input handling (dict, str, JSON)
- Structured error responses
- Example implementation

**Inspired by:** `custom_tools.py` and `athena_tools.py` robust input handling

#### #12: Implement Retry Logic for External APIs
- Exponential backoff pattern
- Complete retry function implementation
- Error handling best practices

**Inspired by:** `athena_tools.py` `_retry()` function (lines 65-82)

#### #13: Always Declare `kind` Explicitly
- Reinforces explicit step declarations
- Side-by-side comparison
- Maintainability rationale

**Inspired by:** Missing `kind` declarations in `concept_discovery`

#### #14: Use Context Scratchpad for State
- Intermediate state management
- Avoiding context pollution
- Example with initialization

**Inspired by:** Extensive scratchpad usage in `concept_discovery`

#### #15: Test Custom Skills Independently
- Unit testing requirement
- pytest examples
- Testing both dict and string inputs

**Inspired by:** Lack of visible tests in `concept_discovery` project

---

## 6. New Section: Troubleshooting

### Added: Complete Troubleshooting Guide

**Location:** New section between Anti-Patterns and Summary

**Covers 9 Common Issues:**

1. **Pipeline Validation Errors**
   - Missing `kind` declarations
   - Required field checks
   - Validation command

2. **Model Settings Not Applied**
   - GPT-5 format issues
   - Correct vs incorrect examples

3. **Context Not Updating**
   - `updates_context: true` requirement
   - When to use it

4. **Loop Never Exits**
   - Exit condition debugging
   - Using `flujo lens trace`
   - `max_loops` safety

5. **Custom Skill Import Errors**
   - Path format requirements
   - `__init__.py` necessity
   - Config allowlist

6. **Cost Tracking Warnings**
   - Adding explicit pricing
   - Disabling strict mode

7. **Template Rendering Errors**
   - Safe access patterns
   - Filter enablement

8. **Agent Tool Calls Fail**
   - Tool requirements
   - Schema matching
   - Common mistakes

9. **Conditional Branch Not Taken**
   - Boolean branch naming
   - Default branch fallback
   - Debugging tips

**Why:** These are issues that could arise from patterns seen in `concept_discovery` and common pitfalls

---

## 7. Updated Summary Section

### Enhanced Key Takeaways

**Changed:** From 7 items to 11 items

**Reordered:** Prioritized explicit `kind` declaration as #1

**Added:**
- Type safety emphasis
- Testing requirements
- Scratchpad usage
- Incremental approach

**New Real-World Examples Section:**
- Direct reference to `concept_discovery` as agentic exploration example
- Links to other patterns
- Production-ready code references

---

## 8. Updated Quick Reference

### Enhanced Common Step Kinds Table

**Changed:** Added "Key Feature" column

**Updated:** 
- Added note about explicit `kind` for steps
- Clarified feature distinctions
- Better at-a-glance understanding

---

## 9. Updated Table of Contents

### Added New Sections

**New entries:**
11. Best Practices
12. Anti-Patterns to Avoid
13. Troubleshooting (NEW)
14. Summary

**Why:** These sections existed but weren't in TOC; added Troubleshooting as new

---

## Impact Summary

### Documentation Improvements

| Category | Before | After | Impact |
|----------|--------|-------|--------|
| **Agent Types** | 2 (Basic, GPT-5) | 3 (+Tool-Calling) | High - enables agentic patterns |
| **Common Patterns** | 10 | 11 (+Agentic Exploration) | High - production pattern |
| **Best Practices** | 10 | 15 (+5 advanced) | High - type safety, testing |
| **Troubleshooting** | None | 9 solutions | High - reduces debugging time |
| **Step Kind Clarity** | Implicit allowed | Explicit required | Medium - consistency |
| **Real Examples** | Generic | `concept_discovery` | High - concrete reference |

---

## Key Learnings from concept_discovery Review

### What Worked Well
1. ✅ Robust input handling in custom skills
2. ✅ Retry logic for external APIs
3. ✅ Scratchpad for state management
4. ✅ Tool-calling agent pattern
5. ✅ Comprehensive error handling
6. ✅ Type hints throughout

### What Could Be Improved
1. ⚠️ Missing explicit `kind` declarations
2. ⚠️ Model settings format inconsistency
3. ⚠️ No visible unit tests
4. ⚠️ Budget limits disabled

### Documentation Gaps Filled
1. Tool-calling agents (completely missing)
2. Agentic exploration pattern (not documented)
3. Troubleshooting guide (didn't exist)
4. Custom skill best practices (minimal coverage)
5. Testing guidance (not emphasized)

---

## Backward Compatibility

✅ **All changes are backward compatible:**
- No breaking changes to syntax
- Existing pipelines continue to work
- New sections are additive
- Recommendations, not requirements (except explicit `kind`)

---

## Recommendations for Next Steps

### For llm.md
1. ✅ All critical updates complete
2. Consider adding more real-world examples from other projects
3. Consider adding performance optimization section
4. Consider adding security best practices section

### For concept_discovery Project
Based on review, recommended fixes:
1. Add explicit `kind: step` to all basic steps
2. Fix model_settings format (lines 11, 43)
3. Enable budget limits in flujo.toml
4. Add unit tests for custom skills
5. Enhance README with examples

### For Other Projects
Use updated `llm.md` to audit:
1. Check for implicit steps
2. Verify model_settings format
3. Ensure budgets are configured
4. Add tests where missing

---

## Files Modified

1. **llm.md** - Main documentation file
   - Added ~300 lines
   - 9 major sections updated/added
   - No breaking changes

2. **REVIEW.md** (created) - Review of concept_discovery
   - Complete compliance analysis
   - Line-by-line assessment
   - Recommendations with examples

3. **LLM_MD_UPDATES.md** (this file) - Change log
   - Detailed update summary
   - Rationale for each change
   - Impact assessment

---

## Validation

✅ **Quality Checks:**
- [x] No linter errors
- [x] All code examples valid YAML
- [x] All Python examples valid syntax
- [x] Internal links verified
- [x] Table of contents updated
- [x] Consistent formatting
- [x] Clear examples for each new concept

✅ **Content Checks:**
- [x] Accurately reflects concept_discovery patterns
- [x] All new sections have examples
- [x] Troubleshooting covers real issues
- [x] Best practices are actionable
- [x] References to real projects included

---

## Conclusion

The `llm.md` documentation has been significantly enhanced based on insights from reviewing the production-ready `concept_discovery` pipeline. The updates:

1. **Fill critical documentation gaps** (tool-calling agents, agentic patterns)
2. **Add practical troubleshooting guidance** (9 common issues)
3. **Enhance best practices** (type safety, testing, explicitness)
4. **Provide real-world examples** (direct project references)
5. **Maintain backward compatibility** (all additive changes)

The documentation is now more comprehensive, practical, and aligned with real-world Flujo usage patterns.


