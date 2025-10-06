#!/bin/bash
# Quick start script for OMOP Concept Discovery

set -e

cd "$(dirname "$0")"

echo "🔍 OMOP Concept Discovery - Pydantic AI"
echo "========================================"
echo ""

# Check for .env file
if [ ! -f "../../.env" ]; then
    echo "⚠️  Warning: ../../.env not found"
    echo "Make sure OPENAI_API_KEY is set in your environment"
    echo ""
fi

# Load environment from project root if exists
if [ -f "../../.env" ]; then
    export $(grep -v '^#' ../../.env | xargs)
fi

# Check for API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not set"
    echo "Please set it in ../../.env or export it"
    exit 1
fi

echo "✅ Environment loaded"
echo ""

# Run the script
uv run python find_concepts.py

