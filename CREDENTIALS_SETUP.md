# Credentials Setup Guide

This guide explains how to set up credentials for the OMOP Cohort Workflow in different environments.

---

## 📋 Required Credentials

| Credential | Required? | Purpose |
|------------|-----------|---------|
| `OPENAI_API_KEY` | ✅ Yes | Powers all AI agents (GPT-5-mini) |
| `GOOGLE_CLOUD_PROJECT` | ⚠️ Optional | Required for BigQuery SQL validation |
| `GOOGLE_APPLICATION_CREDENTIALS` | ⚠️ Optional | Required for BigQuery access |

**Note**: The workflow can run without BigQuery credentials, but SQL validation will be skipped.

---

## 🏠 Local Development Setup

### **Option A: Using `.env` File** (Recommended)

1. Create a `.env` file in the project root:

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen
touch .env
```

2. Add your credentials:

```env
# Required
OPENAI_API_KEY=sk-proj-...your-key...

# Optional (for BigQuery)
GOOGLE_CLOUD_PROJECT=your-project-id
```

3. For BigQuery, authenticate with gcloud:

```bash
gcloud auth application-default login
```

This creates credentials at `~/.config/gcloud/application_default_credentials.json`

### **Option B: Using Environment Variables**

```bash
export OPENAI_API_KEY="sk-proj-...your-key..."
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### **Verify Setup**

```bash
python projects/shared/secrets.py
```

Expected output:
```
🔐 Checking credentials (environment: local)

✅ OPENAI_API_KEY: sk-p...key
✓  GOOGLE_CLOUD_PROJECT: your-project-id
ℹ️  GOOGLE_APPLICATION_CREDENTIALS: Not found

✅ All required credentials available!
```

---

## ☁️ Google Cloud Run Setup

### **Step 1: Create Secrets in Secret Manager**

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Create OpenAI API key secret
echo 'sk-proj-...your-key...' | gcloud secrets create OPENAI_API_KEY --data-file=-

# Verify
gcloud secrets list
```

### **Step 2: Grant Cloud Run Access to Secrets**

```bash
# Get the service account email
SERVICE_ACCOUNT=$(gcloud run services describe YOUR_SERVICE_NAME \
  --region YOUR_REGION \
  --format 'value(spec.template.spec.serviceAccountName)')

# Grant access to the secret
gcloud secrets add-iam-policy-binding OPENAI_API_KEY \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

### **Step 3: Configure Cloud Run Service**

```bash
gcloud run services update YOUR_SERVICE_NAME \
  --region YOUR_REGION \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID \
  --update-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest
```

### **Step 4: (Optional) Enable BigQuery API**

```bash
gcloud services enable bigquery.googleapis.com

# Grant BigQuery permissions to service account
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/bigquery.jobUser"
```

### **Deploy to Cloud Run**

```bash
# Build and deploy
gcloud run deploy cohort-builder \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 🔄 Replit Setup

### **Step 1: Add Secrets via Replit UI**

1. Open your Repl
2. Click on the **"Secrets"** tab (lock icon) in the left sidebar
3. Add secrets:

```
Key:   OPENAI_API_KEY
Value: sk-proj-...your-key...
```

```
Key:   GOOGLE_CLOUD_PROJECT
Value: your-project-id
```

### **Step 2: (Optional) Add Google Cloud Service Account**

For BigQuery access:

1. Create a service account key in Google Cloud:

```bash
gcloud iam service-accounts create replit-cohort-builder \
  --display-name="Replit Cohort Builder"

gcloud iam service-accounts keys create service-account.json \
  --iam-account=replit-cohort-builder@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:replit-cohort-builder@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

2. Upload `service-account.json` to Replit:
   - Click "Files" tab
   - Upload the JSON file
   - Note the path (e.g., `/home/runner/YourRepl/service-account.json`)

3. Add secret in Replit:
```
Key:   GOOGLE_APPLICATION_CREDENTIALS
Value: /home/runner/YourRepl/service-account.json
```

### **Verify Setup in Replit**

Run in the Replit shell:
```bash
python projects/shared/secrets.py
```

---

## 🐳 Docker / Container Setup

### **Using Environment Variables**

```bash
docker run -e OPENAI_API_KEY="sk-proj-..." \
           -e GOOGLE_CLOUD_PROJECT="your-project" \
           cohort-builder
```

### **Using `.env` File**

```bash
docker run --env-file .env cohort-builder
```

### **Using Google Cloud Credentials File**

```bash
docker run -v /path/to/service-account.json:/creds/sa.json \
           -e GOOGLE_APPLICATION_CREDENTIALS=/creds/sa.json \
           -e OPENAI_API_KEY="sk-proj-..." \
           cohort-builder
```

---

## 🔧 Advanced Configuration

### **Multiple Alternative Names**

The secrets manager tries multiple environment variable names:

```python
# These all work for OpenAI key:
OPENAI_API_KEY=sk-...
OPENAI_KEY=sk-...

# These all work for Google Cloud project:
GOOGLE_CLOUD_PROJECT=my-project
GCP_PROJECT_ID=my-project
GCLOUD_PROJECT=my-project
```

### **Custom Secrets Location**

If your `.env` file is in a non-standard location:

```python
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("/custom/path/.env"))
```

### **Programmatic Access**

```python
from shared.secrets import get_secret, check_credentials

# Get a secret
openai_key = get_secret("OPENAI_API_KEY")

# Check if optional secret exists
project = get_secret("GOOGLE_CLOUD_PROJECT", required=False)

# Check all credentials
status = check_credentials(verbose=True)
if status["OPENAI_API_KEY"]:
    print("OpenAI is ready!")
```

---

## 🧪 Testing Your Setup

### **Quick Check**

```bash
python projects/shared/secrets.py
```

### **Test OpenAI Connection**

```python
from shared.secrets import get_secret
import openai

openai.api_key = get_secret("OPENAI_API_KEY")
response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}]
)
print("OpenAI OK:", response.choices[0].message.content)
```

### **Test BigQuery Connection**

```python
from shared.secrets import setup_bigquery_auth
from google.cloud import bigquery

if setup_bigquery_auth():
    client = bigquery.Client()
    query = "SELECT 1 as test"
    result = list(client.query(query).result())
    print("BigQuery OK:", result)
else:
    print("BigQuery auth not available")
```

---

## 🔒 Security Best Practices

### **DO:**
- ✅ Use `.env` files for local development (add to `.gitignore`)
- ✅ Use Secret Manager for cloud deployments
- ✅ Use service accounts with minimal permissions
- ✅ Rotate API keys regularly
- ✅ Use environment-specific keys (dev/staging/prod)

### **DON'T:**
- ❌ Commit API keys to Git
- ❌ Share API keys in chat/email
- ❌ Use production keys in development
- ❌ Give service accounts unnecessary permissions
- ❌ Hard-code secrets in source code

---

## 🐛 Troubleshooting

### **"Required secret 'OPENAI_API_KEY' not found"**

**Solution**: Check that your `.env` file exists or environment variable is set:
```bash
echo $OPENAI_API_KEY
```

If empty, set it:
```bash
export OPENAI_API_KEY="sk-proj-..."
```

### **"BigQuery authentication not available"**

**Solution**: Run gcloud auth:
```bash
gcloud auth application-default login
```

Or set service account path:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

### **"No module named 'dotenv'"**

**Solution**: Install python-dotenv:
```bash
pip install python-dotenv
```

Or in project:
```bash
uv pip install python-dotenv
```

### **Secrets work locally but not in Cloud Run**

**Solution**: Verify Secret Manager setup:
```bash
# Check secret exists
gcloud secrets describe OPENAI_API_KEY

# Check service account has access
gcloud secrets get-iam-policy OPENAI_API_KEY
```

### **Replit can't find service account file**

**Solution**: Use absolute path:
```bash
# In Replit shell, find the path:
pwd
# Then use: /home/runner/YourRepl/service-account.json
```

---

## 📚 Environment-Specific Examples

### **Local Development**

```bash
# .env file
OPENAI_API_KEY=sk-proj-abc123...
GOOGLE_CLOUD_PROJECT=dev-project-123

# Run
python projects/run/run_full_workflow.sh
```

### **Cloud Run**

```bash
# Secrets in Secret Manager
gcloud secrets create OPENAI_API_KEY --data-file=-

# Environment variable
gcloud run services update cohort-builder \
  --set-env-vars GOOGLE_CLOUD_PROJECT=prod-project-456

# Deploy
gcloud run deploy cohort-builder --source .
```

### **Replit**

```
# Secrets tab
OPENAI_API_KEY: sk-proj-def456...
GOOGLE_CLOUD_PROJECT: replit-project-789

# Run button or shell
python main.py
```

---

## ✅ Verification Checklist

Before running the workflow, verify:

- [ ] `OPENAI_API_KEY` is set and valid
- [ ] `python projects/shared/secrets.py` shows ✅
- [ ] Test cohort can be entered
- [ ] Stage 1 (Clarification) runs without error
- [ ] Stage 2 (Concept Discovery) finds OMOP concepts
- [ ] Stage 3 (SQL Generation) creates SQL
- [ ] (Optional) BigQuery validation works

---

## 🆘 Getting Help

If you're still having issues:

1. Run the credential checker:
   ```bash
   python projects/shared/secrets.py
   ```

2. Check the environment:
   ```python
   from shared.secrets import get_runtime_info
   print(get_runtime_info())
   ```

3. Verify file locations:
   ```bash
   ls -la .env
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ls -la $GOOGLE_APPLICATION_CREDENTIALS
   ```

4. Test minimal setup:
   ```python
   from shared.secrets import get_secret
   print(get_secret("OPENAI_API_KEY"))
   ```

---

**Need more help?** Check the main README or create an issue with the output of `python projects/shared/secrets.py`.

