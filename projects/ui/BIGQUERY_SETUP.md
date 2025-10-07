# BigQuery Setup Guide

This guide helps you configure BigQuery access for SQL validation and analytics.

---

## ✅ What Works WITHOUT BigQuery

You can use the UI for **Stages 1-2 without any BigQuery setup**:

- ✅ **Stage 1**: Clinical Clarification (OpenAI only)
- ✅ **Stage 2**: Concept Discovery (OpenAI + Athena API)

SQL will still be **generated** in Stage 3, but validation will be skipped.

---

## 🔧 BigQuery Setup (for Stages 3-4)

### Step 1: Authenticate with Google Cloud

**Option A: Using gcloud CLI** (recommended for local development):

```bash
# Install gcloud CLI if needed
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login

# Set your project
gcloud config set project YOUR-PROJECT-ID
```

**Option B: Using Service Account**:

1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```

### Step 2: Verify Access

```bash
make check-credentials
```

You should see:
```
✅ GOOGLE_CLOUD_PROJECT: your-project-id
✅ BigQuery authentication: OK
```

---

## 🗄️ OMOP Dataset Configuration

### Using the Public Demo Dataset (Default)

The workflow uses `bigquery-public-data.cms_synthetic_patient_data_omop` by default.

**⚠️ Limitations**:
- Missing some OMOP tables (e.g., `measurement`)
- Synthetic data only
- Limited to demo use cases

**✅ What works**: Most condition-based cohorts (heart failure, diabetes, etc.)

### Using Your Own OMOP Dataset

**Recommended for production use.**

1. **Set up your OMOP CDM dataset** in BigQuery
   - Must follow OMOP CDM v5.x schema
   - Tables: `person`, `condition_occurrence`, `procedure_occurrence`, etc.

2. **Configure in `.env`**:
   ```bash
   GOOGLE_CLOUD_PROJECT=your-project-id
   OMOP_DATASET_ID=your-project.your_omop_dataset
   BIGQUERY_LOCATION=US
   ```

3. **Or configure per-run in the UI**:
   - Click "New Run"
   - Expand "Advanced Settings"
   - Scroll to "BigQuery Configuration"
   - Enter your dataset: `your-project.your_omop_dataset`

---

## 🔍 Table Discovery

**Stage 3 now automatically discovers available tables** before generating SQL.

When you start a run, Stage 3 will:
1. ✅ List all tables in your OMOP dataset
2. ⚠️ Warn about missing tables for your concept sets
3. 🔧 Generate SQL only for available tables

**Example output**:
```
[Step 0] Discovering available OMOP tables...
✅ Found 24 tables in bigquery-public-data.cms_synthetic_patient_data_omop
   Available domain tables: condition_occurrence, drug_exposure, observation, procedure_occurrence

⚠️  Warning: Some concept sets reference tables that don't exist:
   - Lab Values (Domain: Measurement → measurement)
   These concepts will be excluded from the generated SQL.
```

---

## 🧪 Testing BigQuery Access

### Quick Test

```bash
# List your datasets
uv run python3 -c "from google.cloud import bigquery; \
  client = bigquery.Client(); \
  [print(d.dataset_id) for d in client.list_datasets()]"

# Check public OMOP dataset
uv run python3 -c "from google.cloud import bigquery; \
  client = bigquery.Client(); \
  tables = list(client.list_tables('bigquery-public-data.cms_synthetic_patient_data_omop')); \
  print(f'Found {len(tables)} tables'); \
  [print(f'  {t.table_id}') for t in sorted(tables, key=lambda x: x.table_id)]"
```

### Full Workflow Test

```bash
# Run complete workflow (includes BigQuery stages)
make run
```

---

## 🎯 Common Issues

### Issue: "Not found: Table ... was not found"

**Cause**: The OMOP dataset or specific tables don't exist.

**Solution**:
1. Verify your dataset exists:
   ```bash
   bq ls --project_id=YOUR-PROJECT-ID
   ```
2. Check table availability (see output from Stage 3)
3. Use a different dataset or configure your own OMOP CDM

### Issue: "Access Denied"

**Cause**: Insufficient permissions.

**Solution**:
1. Verify authentication: `gcloud auth list`
2. Check IAM permissions:
   - `bigquery.jobs.create`
   - `bigquery.tables.getData`
   - `bigquery.datasets.get`
3. For public datasets: Some tables may have restricted access

### Issue: "Measurement table not found"

**Cause**: The public demo dataset doesn't include all OMOP tables.

**Solution**:
- **Option 1**: Avoid cohorts requiring lab values/measurements
- **Option 2**: Use your own complete OMOP CDM dataset
- **Option 3**: Stage 3 will now automatically skip missing tables

---

## 📚 Additional Resources

- [BigQuery OMOP Documentation](https://cloud.google.com/healthcare/docs/how-tos/omop)
- [OHDSI CDM Documentation](https://ohdsi.github.io/CommonDataModel/)
- [Google Cloud IAM Guide](https://cloud.google.com/iam/docs/overview)

---

## ✅ Recommended Setup Checklist

- [ ] Authenticate with `gcloud auth application-default login`
- [ ] Run `make check-credentials` - verify OpenAI and BigQuery access
- [ ] Set `OMOP_DATASET_ID` in `.env` (if using custom dataset)
- [ ] Test with a simple cohort (e.g., heart failure patients)
- [ ] Review Stage 3 output for table discovery warnings
- [ ] Check generated SQL in "Download Artifacts" tab

**You're ready to build cohorts! 🚀**

