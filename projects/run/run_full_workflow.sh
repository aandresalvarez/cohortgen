#!/bin/bash
# Complete OMOP Cohort Definition Workflow
# Run from: /Users/alvaro1/Documents/Coral/Code/cohortgen/projects/run/

set -e

cd "$(dirname "$0")"
PROJECT_ROOT="$(cd ../.. && pwd)"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║     OMOP COHORT DEFINITION WORKFLOW - FULL SYSTEM                ║"
echo "║                                                                   ║"
echo "║  Stage 1: Clinical Clarification (plain text)                    ║"
echo "║  Stage 2: Concept Discovery (OMOP IDs)                           ║"
echo "║  Stage 3: BigQuery SQL Generation (executable query)             ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Running from: $(pwd)"
echo ""

# Check for .env file
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  Warning: .env file not found at $PROJECT_ROOT/.env"
    echo "Make sure OPENAI_API_KEY is set in your environment"
    echo ""
fi

# Load environment
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Check for API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not set"
    echo "Please create a .env file at $PROJECT_ROOT/.env with:"
    echo "  OPENAI_API_KEY=your-key-here"
    exit 1
fi

echo "✅ Environment loaded"
echo "✅ Project root: $PROJECT_ROOT"
echo ""

# Ask user which mode
echo "Choose a mode:"
echo "  1) Run all 3 stages (complete workflow: text → concepts → SQL)"
echo "  2) Run Stage 1 + 2 only (clinical clarification + concept discovery)"
echo "  3) Run Stage 1 only (clinical clarification)"
echo "  4) Run Stage 2 only (concept discovery)"
echo "  5) Run Stage 3 only (BigQuery SQL generation)"
echo "  6) Run demo (Stage 2 with test data)"
echo "  7) Run Stage 4 only (Analytics)"
echo ""
read -p "Enter choice [1-7]: " choice

case $choice in
    1)
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "COMPLETE WORKFLOW: ALL 3 STAGES"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        echo "This will run:"
        echo "  Stage 1: Clinical Clarification (interactive)"
        echo "  Stage 2: Concept Discovery (automatic)"
        echo "  Stage 3: BigQuery SQL Generation (automatic)"
        echo ""
        
        # Run Stage 1 + 2
        cd "$PROJECT_ROOT/projects/run"
        uv run python run_complete_workflow.py
        
        # Run Stage 3
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "Proceeding to Stage 3: BigQuery SQL Generation..."
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        cd "$PROJECT_ROOT/projects/qb"
        uv run python create_bigquery_sql.py

        # Offer Stage 4 analytics
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "Proceeding to Stage 4: Analytics..."
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        cd "$PROJECT_ROOT"
        make run-stats
        ;;
        
    2)
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "STAGE 1 + 2: CLINICAL + CONCEPT DISCOVERY"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        echo "Running integrated workflow..."
        echo "Stage 1 output will automatically feed into Stage 2"
        echo ""
        cd "$PROJECT_ROOT/projects/run"
        uv run python run_complete_workflow.py
        ;;
        
    3)
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "STAGE 1: CLINICAL CLARIFICATION"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        cd "$PROJECT_ROOT/projects/clar"
        uv run python hitl_clarification_working.py
        ;;
        
    4)
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "STAGE 2: CONCEPT DISCOVERY"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        cd "$PROJECT_ROOT/projects/cd"
        uv run python find_concepts.py
        ;;
        
    5)
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "STAGE 3: BIGQUERY SQL GENERATION"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        
        # Check if input exists
        if [ ! -f "$PROJECT_ROOT/projects/run/complete_cohort_output.json" ]; then
            echo "❌ Error: No cohort definition found."
            echo ""
            echo "💡 Run Stage 1 + 2 first (option 2)"
            exit 1
        fi
        
        cd "$PROJECT_ROOT/projects/qb"
        uv run python create_bigquery_sql.py
        ;;
        
    6)
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "DEMO MODE: AUTOMATED WORKFLOW"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        echo "Running Stage 2 with demo cohort definition..."
        echo ""
        cd "$PROJECT_ROOT/projects/cd"
        echo "demo" | uv run python find_concepts.py
        
        echo ""
        echo "✅ Demo complete!"
        echo ""
        echo "For a full demo with Stage 1 clarification, run Stage 1 manually"
        echo "and answer the interactive questions."
        ;;

    7)
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "STAGE 4: ANALYTICS"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
        cd "$PROJECT_ROOT"
        make run-stats
        ;;
        
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ WORKFLOW COMPLETE"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
