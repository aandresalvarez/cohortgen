# Log Content Cleanup - Removed Stage Headers

## 🐛 **Problem:**

Stage 2 (and other stages) showed redundant headers in the log output:

```
## 🔄 Stage 2: Concept Discovery              ← UI heading (good!)

*Discovering OMOP concepts...*

**Live Progress:**
```
Stage 2: Concept Discovery Run ID: 2025...   ← REDUNDANT in log!
==================================================== ← REDUNDANT
OMOP CONCEPT DISCOVERY - NORMAL MODE          ← REDUNDANT
Cohort Definition: Index Event: ...           ← REDUNDANT (very long)

[Step 1] Decomposing...                       ← Actual content starts here
```
```

**Issues:**
- ❌ "Stage 2: Concept Discovery" shown twice (UI heading + log content)
- ❌ Run ID repeated in log (already in header)
- ❌ Separator lines (`====`) clutter the display
- ❌ Very long cohort definition repeated in log
- ❌ Confusing and redundant

## ✅ **Solution:**

### **Created Log Cleaning Function**

```python
def clean_log_content(log_content: str, stage_num: int) -> str:
    """Remove redundant stage headers from log content."""
    lines = log_content.strip().split("\n")
    cleaned_lines = []
    skip_header = True
    
    for line in lines:
        if skip_header:
            # Skip redundant header lines
            if (f"Stage {stage_num}:" in line or 
                line.strip().startswith("====") or 
                line.strip().startswith("Run ID:") or
                "OMOP CONCEPT DISCOVERY" in line or
                "SQL GENERATION" in line or
                (line.startswith("Cohort Definition:") and len(line) > 100)):
                continue
            else:
                skip_header = False  # Found actual content
        
        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)
```

### **Applied to All Stage Logs**

- ✅ Stage 2 running logs
- ✅ Stage 2 complete logs  
- ✅ Stage 3 running logs
- ✅ Stage 3 complete logs

## 🎯 **Result - Clean Log Display:**

### **Before:**
```
## 🔄 Stage 2: Concept Discovery

*Discovering OMOP concepts...*

**Live Progress:**
```
Stage 2: Concept Discovery Run ID: 20251006_200835_ec66ce
======================================================================
OMOP CONCEPT DISCOVERY - NORMAL MODE
Cohort Definition: Index Event: First recorded diagnosis of influenza...

[Step 1] Decomposing cohort definition into concept sets...
```
```

### **After:**
```
## 🔄 Stage 2: Concept Discovery

*Discovering OMOP concepts...*

**Live Progress:**
```
[Step 1] Decomposing cohort definition into concept sets...
✅ Found 3 candidates
Searching: influenza diagnosis
✅ Found 15 candidates
🤖 LLM candidate selection...
```
```

## 📊 **Benefits:**

✅ **No More Duplication** - Stage name shown once in UI, not in logs  
✅ **Cleaner Display** - No redundant separators or headers  
✅ **Faster Reading** - Get straight to the actual progress  
✅ **Less Scrolling** - Compact, focused log output  
✅ **Professional** - Clean, modern log display  

## 🧪 **Test It:**

**Refresh your browser** and look at any running stage. You'll now see:

1. ✅ Stage heading (once, in UI)
2. ✅ Brief status message
3. ✅ **Clean log content starting with actual progress**
4. ✅ No redundant headers or separators

**Much cleaner!** 🎉

## 📝 **What Gets Removed:**

The following patterns are automatically stripped from log display:
- `Stage X: ...` lines
- `Run ID: ...` lines  
- `====` separator lines
- `---` separator lines
- `OMOP CONCEPT DISCOVERY` mode headers
- `SQL GENERATION` mode headers
- Very long `Cohort Definition:` lines (>100 chars)

Only the **actual progress content** is shown!
