# UI Quick Start 🚀

## Launch in 3 Steps

### 1. Install
```bash
make install
```

### 2. Launch
```bash
make run-ui
```

### 3. Open Browser
Go to: **http://localhost:7860**

---

## First Run Tutorial

### Step 1: Create a New Run
1. Click **"+ New Run"** (green button at top of sidebar)
2. Enter cohort description:
   ```
   Male patients age 20-30 with positive flu test in 2020
   ```
3. Optionally: 
   - Give it a custom name
   - Expand "Advanced Settings" → enable "Fast Mode"
4. Click **"Create Run"**

### Step 2: Start the Run
1. Click on your new run in the list (it will highlight)
2. Click **"▶️ Start"** button at bottom
3. Watch the stages progress in real-time!

### Step 3: View Results
- Each stage shows ✅ when complete
- Click "Download Artifacts" to see outputs
- Stage 3 SQL tab has your BigQuery query

---

## What You'll See

```
Your run progresses through 4 stages:

⏸ → 🔄 → ✅  Stage 1: Clinical Clarification (1-2 min)
⏸ → 🔄 → ✅  Stage 2: Concept Discovery (1-3 min)
⏸ → 🔄 → ✅  Stage 3: SQL Generation (< 30 sec)
⏸ → 🔄 → ✅  Stage 4: Analytics (30 sec - 2 min)
```

**Total time:** 
- Normal mode: 5-10 minutes
- Fast mode: 2-5 minutes

---

## Tips

### Speed It Up
- Enable **Fast Mode** in Advanced Settings
- Reduces concept search depth for quicker results

### Multiple Runs
- You can create multiple runs
- Each run is independent and saved
- View history in the sidebar

### Compare Runs
- Create a run, then **Duplicate** it
- Modify the description slightly
- Compare the SQL outputs

---

## Troubleshooting

### UI Won't Start
```bash
# Check dependencies
make install

# Check for port conflicts
lsof -i :7860

# Kill conflicting process if needed
```

### Run Fails
- Check console output for errors
- View error details in the run display
- Common issues:
  - Missing OpenAI API key (check `.env`)
  - No BigQuery credentials (Stage 4 only)

### Slow Performance
- Enable Fast Mode
- Check network connection
- ATHENA API can be slow sometimes

---

## What's Next?

### Phase 1 (Current)
✅ Basic UI with run management
✅ Background execution
✅ Artifact downloads

### Phase 2 (Coming Soon)
- 📊 Analytics charts (Plotly)
- 💾 ATHENA result caching
- 🔍 Run search and filters
- 🔄 Run comparison/diff

### Phase 3 (Future)
- 💬 Slack integration
- 🗄️ Database storage option
- 👥 Multi-user support

---

## Get Help

- **Documentation**: See `README.md` in this directory
- **Implementation Details**: See `IMPLEMENTATION.md`
- **PRD**: See `/prd.md` for full specification

---

**Enjoy building cohorts! 🧬**

