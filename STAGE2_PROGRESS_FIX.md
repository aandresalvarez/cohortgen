# Stage 2 Progress Display Fix

## 🐛 Problem

After Stage 1 completion, the user saw:
```
### 🔄 Next: Stage 2 - Concept Discovery
*Now searching OMOP vocabulary... This may take 1-2 minutes.*
*Scroll down to see live progress below.*
```

**BUT:** No live progress was actually shown! 😞

## 🔍 Root Cause

The `send_clarification_message_handler` function was NOT updating the `run_display` component when Stage 1 completed. So even though Stage 2 started, the display didn't refresh to show it.

**Before Fix:**
```python
# Handler returned only:
return (
    chat_history,           # ✅ Updated
    "",                     # ✅ Clear input
    stage1_final_def,       # ✅ Show definition
    stage1_chat_accordion,  # ✅ Hide chat
)
# ❌ run_display was NOT updated!
```

## ✅ Solution Implemented

### 1. **Added `run_display` to Handler Return**

```python
def send_clarification_message_handler(...) -> tuple[list, str, gr.update, gr.update, str]:
    # ... when completion happens ...
    
    # Start Stage 2
    service.start_run(run_id, stages=[2, 3, 4])
    
    # ✅ NEW: Wait briefly and get updated display
    import time
    time.sleep(0.5)  # Let Stage 2 start
    display_text, _ = get_run_display(run_id)
    
    return (
        chat_history,
        "",
        gr.update(value=final_def_md, visible=True),
        gr.update(visible=False),
        display_text  # ✅ NOW INCLUDES Stage 2 progress!
    )
```

### 2. **Added `run_display` to Event Outputs**

```python
stage1_send_btn.click(
    send_clarification_message_handler,
    inputs=[selected_run_id, stage1_input, stage1_chatbot],
    outputs=[
        stage1_chatbot,
        stage1_input,
        stage1_final_def,
        stage1_chat_accordion,
        run_display,  # ✅ NEW: Display updates!
    ],
)
```

### 3. **Bonus: Added Enter Key Support**

```python
# Also support pressing Enter in textbox
stage1_input.submit(
    send_clarification_message_handler,
    inputs=[selected_run_id, stage1_input, stage1_chatbot],
    outputs=[stage1_chatbot, stage1_input, stage1_final_def, stage1_chat_accordion, run_display],
)
```

## 🎯 Result - What You'll Now See

After completing Stage 1:

```
┌─────────────────────────────────────────────┐
│ ✅ Stage 1 Complete: Cohort Definition      │
│                                             │
│ 📋 Your Cohort Definition                   │
│ 🎯 Index Event: [your event]                │
│ ✅ Inclusion Criteria: [criteria]           │
│ 👥 Demographics: [demographics]             │
│                                             │
│ ### 🔄 Next: Stage 2 - Concept Discovery   │
│ *Now searching OMOP vocabulary...*          │
│ *Scroll down to see live progress below.*   │
├─────────────────────────────────────────────┤
│                                             │
│ ## 🔄 Stage 2: Concept Discovery            │ ← ✅ NOW VISIBLE!
│ *Discovering OMOP concepts...*              │
│                                             │
│ **Live Progress:**                          │
│ ✅ Found 1 candidates                       │
│ Searching: constipation                     │
│ ✅ Found 5 candidates                       │
│ 🤖 LLM candidate selection...               │
│ ✅ Selected 5 candidates                    │
│ [Step 3] Queue-based exploration...         │
│ [Iteration 1] Processing batch...           │
│ ...                                         │
└─────────────────────────────────────────────┘
```

## 🧪 Test It

1. **Create New Run:** "patients with diabetes"
2. **Complete Stage 1:** Answer all questions
3. **Submit Last Answer:** Click Send or press Enter
4. **Watch:**
   - ✅ Completion message in chat
   - ✅ Chat closes
   - ✅ Final definition shows
   - ✅ **Stage 2 progress immediately visible below!** 🎉

## 🎉 Benefits

✅ **Live Progress Visible:** See Stage 2 working in real-time  
✅ **No Confusion:** Progress appears exactly where promised  
✅ **Better UX:** Smooth transition with immediate feedback  
✅ **Enter Key Works:** Can submit answers with Enter  

**Problem solved!** 🚀
