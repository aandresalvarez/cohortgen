# Header Layout Fix - Run ID Always at Top

## 🐛 **Problem:**

The Run ID/Status header was appearing BELOW the final cohort definition:

```
✅ Stage 1 Complete: Cohort Definition
📋 Your Cohort Definition
🎯 Index Event: ...
✅ Inclusion Criteria: ...

🔄 Next: Stage 2 - Concept Discovery    ← End of definition
Scroll down to see live progress below.

---

Run ID: ... | Status: ... | Created: ... ← Header was HERE (too low!)

## 🔄 Stage 2: Concept Discovery
```

**Issues:**
- ❌ User had to scroll past the entire cohort definition to see the Run ID
- ❌ Confusing visual hierarchy - status should be at top
- ❌ Inconsistent - header location changed based on stage

## ✅ **Solution:**

### **1. Created Separate Header Component**

Added a new `run_header` component at the very top of the right panel:

```python
# Right panel: Run details
with gr.Column(scale=3):
    # Run header - ALWAYS at top
    run_header = gr.Markdown(
        "⬅️ Select a run from the list to view details",
        elem_classes=["run-display"],
    )
    
    # Stage 1 Interactive Clarification Chat
    stage1_chat_accordion = ...
    
    # Final cohort definition display
    stage1_final_def = gr.Markdown(visible=False)
    
    # Main run display (stages only, no header)
    run_display = gr.Markdown("")
```

### **2. Split Display Logic**

Created two separate functions:

```python
def get_run_header(run_id: Optional[str]) -> str:
    """Get just the run header (ID, status, created, duration)."""
    return f"**Run ID:** `{run_id}` | **Status:** ... | **Created:** ..."

def get_run_display(run_id: Optional[str]) -> Tuple[str, bool]:
    """Get formatted display for stages (no header)."""
    # Returns only the stages section
    return stages_text, stage4_complete
```

### **3. Updated All Event Handlers**

Modified all event handlers to update both `run_header` and `run_display`:

- `runs_table.select()` - Run selection
- `stage1_send_btn.click()` - Chat message send
- `stage1_input.submit()` - Chat Enter key
- `refresh_timer.tick()` - Auto-refresh
- `update_display_and_dashboard()` - Dashboard load
- `update_display_only()` - Timer refresh

## 🎯 **Result - Perfect Layout:**

### **After Fix:**
```
Run ID: ... | Status: ● Running | Created: ... ← ✅ ALWAYS AT TOP!

✅ Stage 1 Complete: Cohort Definition
📋 Your Cohort Definition
🎯 Index Event: ...
✅ Inclusion Criteria: ...

🔄 Next: Stage 2 - Concept Discovery
Scroll down to see live progress below.

---

## 🔄 Stage 2: Concept Discovery
*Discovering OMOP concepts...*

**Live Progress:**
```
[Step 1] Decomposing...
✅ Found 3 candidates
```
```

## 📊 **Benefits:**

✅ **Header Always Visible** - Run ID/Status always at the very top  
✅ **Clear Hierarchy** - Status first, then content  
✅ **Consistent Layout** - Header position never changes  
✅ **Better UX** - User immediately sees run status  
✅ **Professional** - Proper visual organization  

## 🧪 **Test It:**

**Refresh your browser** and select any run. You'll now see:

1. ✅ **Run ID/Status at the very top** (always)
2. ✅ Stage 1 chat (if active)
3. ✅ Final cohort definition (if Stage 1 complete)
4. ✅ Stage progress below

**Perfect layout!** 🎉

## 📝 **Technical Details:**

### **Component Order:**
1. `run_header` - Run ID/Status (always visible)
2. `stage1_chat_accordion` - Interactive chat (conditional)
3. `stage1_final_def` - Final definition (conditional)
4. `run_display` - Stage progress (always visible)
5. `analytics_dashboard_accordion` - Dashboard (conditional)

### **Data Flow:**
- All update functions return BOTH `header_text` and `display_text`
- Gradio components update independently
- Header updates on every state change
- Display updates with stage progress

**Clean separation of concerns!** ✅
