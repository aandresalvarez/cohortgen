# Known Issues - Phase 1 MVP

## 🔍 Issue: Stage 1 Progress Not Visible in UI

**Status:** Known Limitation  
**Affects:** Stage 1 (Clinical Clarification)  
**Severity:** Low (cosmetic)

### Description
When Stage 1 is running, the clarification conversation (agent questions and auto-answers) is not displayed in the Gradio UI. The interaction happens in the background and only prints to the terminal/console.

### What You'll See
- UI shows: "🔄 Stage 1: Clinical Clarification - Running clarification (45-75s). Q&A happening in background..."
- Terminal shows: Full conversation with agent questions and auto-answers
- After ~45-75 seconds: Stage 1 completes and shows ✅

### Why This Happens
Phase 1 MVP runs Stage 1 in **non-interactive mode**:
- The clarification agent runs in a background thread
- It mocks `input()` to auto-answer with empty strings
- Agent asks 3-5 questions, then proceeds with best guess
- All output goes to terminal stdout (not captured by UI yet)

### Workaround
**Use detailed cohort descriptions** to minimize clarification needs:

❌ **Vague:**  
`"Diabetes patients"`

✅ **Detailed:**  
`"Adults age 18-65 with first type 2 diabetes diagnosis in 2020-2023, with at least one HbA1c measurement"`

The more specific you are, the better Stage 1 works without human interaction.

### Planned Fix (Phase 2)
- Add interactive chat UI for Stage 1
- Stream agent questions to the UI in real-time
- Allow user to provide answers via text input
- Show conversation history

---

## 🔧 Issue: Import Path Conflicts (FIXED)

**Status:** ✅ RESOLVED  
**Affects:** Stage 2, 3, 4  
**Fixed In:** Current version

### Description
Multiple `tools.py` files in different stage directories caused import conflicts.

### Solution
Each stage now temporarily adjusts `sys.path` to prioritize its own directory:
```python
# Stage 2 prioritizes projects/cd/
# Stage 3 prioritizes projects/qb/
# Stage 4 prioritizes projects/stats/
```

---

## 📊 Other Limitations

### Stage Results May Be Incomplete
- **Stage 1:** May produce partial definitions if description is vague
- **Stage 2:** Depends on quality of Stage 1 output
- **Stage 3:** Depends on concept sets from Stage 2
- **Stage 4:** Requires valid BigQuery credentials

### No Live Log Streaming
- Logs print to terminal only
- UI shows status updates every 2 seconds
- View logs in terminal or check `output/runs/{run_id}/run.json`

### No Run Cancellation
- Once started, runs execute to completion or failure
- Can't stop a running stage mid-execution
- Workaround: Stop UI (`make stop-ui`) or wait for completion

---

## 🎯 Best Practices

### For Best Results:

1. **Be Specific** - Detailed descriptions work better
2. **Use Fast Mode** - For quick iterations (3 questions vs 5)
3. **Check Artifacts** - Even partial Stage 1 results can be useful
4. **Watch Terminal** - See full Stage 1 conversation there
5. **Test Simple First** - Start with clear, simple cohorts

### Example Good Descriptions:

```
Adults age 18-65 with type 2 diabetes diagnosed in 2020-2023

Male patients with heart failure diagnosis followed by ESRD

Pediatric patients age 0-17 with autism spectrum disorder diagnosis
```

---

## 📚 Documentation

- **Main README:** `projects/ui/README.md`
- **Quick Start:** `projects/ui/QUICKSTART.md`
- **Implementation:** `projects/ui/IMPLEMENTATION.md`
- **Phase 1 Notes:** `projects/ui/PHASE1_NOTES.md`

---

**Last Updated:** October 6, 2025 (Phase 1 MVP)

