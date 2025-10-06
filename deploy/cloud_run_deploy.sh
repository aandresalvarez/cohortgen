#!/bin/bash
# Deploy OMOP Cohort Workflow to Google Cloud Run

set -e

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
SERVICE_NAME="${SERVICE_NAME:-cohort-builder}"
REGION="${REGION:-us-central1}"
OPENAI_API_KEY_SECRET="${OPENAI_API_KEY_SECRET:-OPENAI_API_KEY}"

# ============================================================================
# Colors for output
# ============================================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo_success() { echo -e "${GREEN}✓${NC} $1"; }
echo_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
echo_error() { echo -e "${RED}✗${NC} $1"; }

# ============================================================================
# Pre-flight Checks
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Google Cloud Run Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Project:  $PROJECT_ID"
echo "Service:  $SERVICE_NAME"
echo "Region:   $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo_error "gcloud CLI not found. Install from: https://cloud.google.com/sdk/install"
    exit 1
fi

echo_success "gcloud CLI found"

# Set project
gcloud config set project "$PROJECT_ID"

# ============================================================================
# Enable Required APIs
# ============================================================================

echo ""
echo "Enabling required Google Cloud APIs..."

REQUIRED_APIS=(
    "run.googleapis.com"
    "secretmanager.googleapis.com"
    "cloudbuild.googleapis.com"
    "bigquery.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo_success "$api already enabled"
    else
        echo "  Enabling $api..."
        gcloud services enable "$api"
        echo_success "$api enabled"
    fi
done

# ============================================================================
# Create/Verify Secrets in Secret Manager
# ============================================================================

echo ""
echo "Checking secrets..."

# Check if OpenAI API key secret exists
if gcloud secrets describe "$OPENAI_API_KEY_SECRET" &> /dev/null; then
    echo_success "Secret $OPENAI_API_KEY_SECRET exists"
else
    echo_warning "Secret $OPENAI_API_KEY_SECRET not found"
    echo ""
    echo "Create it with:"
    echo "  echo 'sk-proj-YOUR-KEY' | gcloud secrets create $OPENAI_API_KEY_SECRET --data-file=-"
    echo ""
    read -p "Do you want to create it now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -n "Enter your OpenAI API key: "
        read -s OPENAI_KEY
        echo
        echo "$OPENAI_KEY" | gcloud secrets create "$OPENAI_API_KEY_SECRET" --data-file=-
        echo_success "Secret $OPENAI_API_KEY_SECRET created"
    else
        echo_error "Cannot proceed without OpenAI API key"
        exit 1
    fi
fi

# ============================================================================
# Deploy to Cloud Run
# ============================================================================

echo ""
echo "Deploying to Cloud Run..."

gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
    --update-secrets "OPENAI_API_KEY=$OPENAI_API_KEY_SECRET:latest" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 10 \
    --min-instances 0

# ============================================================================
# Grant Permissions
# ============================================================================

echo ""
echo "Configuring permissions..."

# Get the service account
SERVICE_ACCOUNT=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --format 'value(spec.template.spec.serviceAccountName)')

echo "Service account: $SERVICE_ACCOUNT"

# Grant Secret Manager access
gcloud secrets add-iam-policy-binding "$OPENAI_API_KEY_SECRET" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    &> /dev/null

echo_success "Secret Manager access granted"

# Grant BigQuery access
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/bigquery.jobUser" \
    &> /dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/bigquery.dataViewer" \
    &> /dev/null

echo_success "BigQuery access granted"

# ============================================================================
# Get Service URL
# ============================================================================

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --format 'value(status.url)')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo_success "Deployment complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Service URL: $SERVICE_URL"
echo ""
echo "Test with:"
echo "  curl $SERVICE_URL"
echo ""
echo "View logs:"
echo "  gcloud run services logs read $SERVICE_NAME --region $REGION"
echo ""
echo "Update service:"
echo "  ./deploy/cloud_run_deploy.sh"
echo ""

