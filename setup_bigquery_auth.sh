#!/bin/bash
# Setup BigQuery authentication for cohort workflow

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║        🔑 BigQuery Authentication Setup                          ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed"
    echo ""
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✅ gcloud CLI is installed"
echo ""

# Get current project
PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -n "$PROJECT" ]; then
    echo "✅ Current GCP project: $PROJECT"
else
    echo "⚠️  No GCP project configured"
    echo ""
    echo "Set project with: gcloud config set project YOUR_PROJECT_ID"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Checking current authentication status..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if gcloud auth application-default print-access-token &>/dev/null; then
    echo "✅ Application default credentials are valid"
    echo ""
    echo "You're all set! BigQuery validation will work."
    exit 0
else
    echo "❌ Application default credentials are missing or expired"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Setting up authentication..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "This will:"
    echo "  1. Open your browser"
    echo "  2. Ask you to log in with your Google account"
    echo "  3. Grant permissions for BigQuery access"
    echo "  4. Save credentials locally"
    echo ""
    read -p "Continue? [Y/n] " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        echo ""
        echo "Running: gcloud auth application-default login"
        echo ""
        
        gcloud auth application-default login
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "✅ Authentication successful!"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "BigQuery validation is now enabled."
            echo ""
            echo "Test with: make run-log"
        else
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "❌ Authentication failed"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "Please try again or check your Google account permissions."
            exit 1
        fi
    else
        echo ""
        echo "Authentication cancelled."
        exit 0
    fi
fi
