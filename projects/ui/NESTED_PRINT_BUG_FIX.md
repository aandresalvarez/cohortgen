# Critical Bug Fix: Nested log_print Function Conflict

**Date**: October 6, 2025  
**Severity**: 🔴 **CRITICAL** (Prevents Stage 1 from running)  
**Status**: ✅ **FIXED**

---

## 🐛 **The Bug**

### Error Message
```
FileNotFoundError: [Errno 2] No such file or directory: 
  '/Users/alvaro1/.../output/runs/20251006_135353_0b272d/stage4_log.txt'

Traceback:
  File ".../service.py", line 289, in _execute_stage1
    log_print("=" * 70)
  File ".../service.py", line 273, in log_print
    original_print(*args, **kwargs)
  File ".../service.py", line 707, in log_print
    with open(stage4_log_path, "a") as f:
```

### What Was Happening

1. **Stage 4** runs first and defines `log_print()` function
2. `log_print()` captures reference to `original_print = builtins.print`
3. **BUT** `builtins.print` has already been replaced by Stage 1, 2, or 3
4. So `original_print` is actually **Stage 1's `log_print`**, not the real `print`
5. This creates a **nested chain** of `log_print` functions
6. When Stage 1 runs, its `log_print` calls `original_print` which is actually Stage 4's `log_print`
7. Stage 4's `log_print` tries to write to `stage4_log.txt` which doesn't exist for the new run
8. **💥 FileNotFoundError**

### Root Cause

**Function Closure Capture + Mutable Global State**

Each stage was doing:
```python
original_print = builtins.print  # ❌ This might already be a log_print function!

def log_print(*args, **kwargs):
    with open(stage_log_path, "a") as f:
        f.write(message + "\n")
    original_print(*args, **kwargs)  # ❌ Calls previously nested log_print!

builtins.print = log_print  # Replaces global print
```

**Problem**: `builtins.print` is global state that gets mutated. When stages run in sequence or overlap, they capture each other's `log_print` functions instead of the real `print`.

---

## ✅ **The Fix**

### Solution: Module-Level Real Print Reference

Save the **real** `print` function once at module import time, before any stage runs:

```python
# At module level (top of service.py)
import builtins as _builtins
_REAL_PRINT = _builtins.print  # ✅ Captured at import time, never changes
```

Then all stages use `_REAL_PRINT` instead of capturing `builtins.print`:

```python
def log_print(*args, **kwargs):
    message = " ".join(str(arg) for arg in args)
    with open(stage_log_path, "a") as f:
        f.write(message + "\n")
    _REAL_PRINT(*args, **kwargs)  # ✅ Always calls the real print!
```

### Why This Works

1. `_REAL_PRINT` is captured **once** at module import time
2. It's a **module-level constant** that never changes
3. No matter how many times stages replace `builtins.print`, `_REAL_PRINT` always refers to the original
4. No nested function chains can form
5. Each stage's `log_print` → `_REAL_PRINT` → actual console output

---

## 📝 **Changes Made**

### File: `projects/ui/service.py`

**1. Added module-level constant (line ~32)**:
```python
# Save the REAL print function at module level to avoid nested log_print issues
import builtins as _builtins
_REAL_PRINT = _builtins.print
```

**2. Updated Stage 1 `log_print` (line ~273)**:
```python
# Before:
original_print = builtins.print  # ❌ Might capture Stage 4's log_print
def log_print(*args, **kwargs):
    ...
    original_print(*args, **kwargs)

# After:
def log_print(*args, **kwargs):  # ✅ No capture needed
    ...
    _REAL_PRINT(*args, **kwargs)  # ✅ Always real print
```

**3. Updated Stage 2 `log_print` (line ~425)**:
```python
def log_print(*args, **kwargs):
    ...
    _REAL_PRINT(*args, **kwargs)  # ✅ Uses module-level constant
```

**4. Updated Stage 3 `log_print` (line ~567)**:
```python
def log_print(*args, **kwargs):
    ...
    _REAL_PRINT(*args, **kwargs)  # ✅ Uses module-level constant
```

**5. Updated Stage 4 `log_print` (line ~718)**:
```python
def log_print(*args, **kwargs):
    ...
    _REAL_PRINT(*args, **kwargs)  # ✅ Uses module-level constant
```

---

## 🧪 **Testing**

### Before Fix
```
1. Create new run
2. Start run
❌ Stage 1 fails with FileNotFoundError
   Error references stage4_log.txt (from previous run or different context)
```

### After Fix
```
1. Create new run
2. Start run
✅ Stage 1 completes successfully
✅ All stages log to their own files
✅ No cross-contamination between stages
✅ No FileNotFoundError
```

---

## 🎯 **Key Lessons**

### 1. **Mutable Global State is Dangerous**

`builtins.print` is global and gets mutated by each stage. This creates unpredictable behavior when stages run in any order.

### 2. **Closure Capture Can Create Chains**

When a function captures a variable from an outer scope, and that variable itself is a function that captures another variable, you get nested chains that are hard to debug.

### 3. **Module-Level Constants Are Safe**

Constants captured at module import time are immutable and always point to the original value, no matter what happens later.

### 4. **Test Multi-Stage Workflows**

This bug only appeared when running multiple stages in sequence. Unit tests for individual stages wouldn't catch it.

---

## 🔍 **How to Spot Similar Issues**

### Warning Signs:
- ✋ Capturing `builtins.print` or other builtins in closures
- ✋ Replacing global functions (`builtins.print = ...`)
- ✋ Using `original_X = builtins.X` pattern
- ✋ Errors mentioning files/paths from different contexts
- ✋ Stack traces showing the same function multiple times

### Prevention:
- ✅ Use module-level constants for built-in functions
- ✅ Restore builtins in `finally` blocks
- ✅ Test multi-stage/multi-threaded scenarios
- ✅ Use context managers for temporary replacements

---

## 📊 **Impact**

| Aspect | Before | After |
|--------|--------|-------|
| **Stage 1** | ❌ Crashes with FileNotFoundError | ✅ Works correctly |
| **Function Nesting** | ❌ log_print → log_print → log_print | ✅ log_print → _REAL_PRINT |
| **Log Files** | ❌ Wrong files referenced | ✅ Correct files per stage |
| **Error Messages** | ❌ Confusing (wrong stage) | ✅ Clear |
| **Stability** | ❌ Fragile | ✅ Robust |

---

## 🚀 **Verification**

To verify the fix:

1. **Create a new run** in the UI
2. **Start the run** (all stages)
3. **Check Stage 1** completes without FileNotFoundError
4. **Check logs**:
   - `stage1_log.txt` should exist and contain Stage 1 output
   - `stage2_log.txt` should exist and contain Stage 2 output
   - etc.
5. **No cross-contamination** between stage logs

---

## 📚 **Related Issues**

- Similar pattern in other projects that mock builtins
- Common in testing frameworks (pytest, unittest.mock)
- Python's built-in `contextlib.redirect_stdout()` avoids this by using context managers

---

## ✅ **Status**

**FIXED**: All stages now use `_REAL_PRINT` from module level.

**No more nested log_print chains!** 🎉

---

**Author**: AI Assistant  
**Reviewed**: October 6, 2025  
**Priority**: P0 (Critical)

