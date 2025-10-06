#!/bin/bash
# Quick test runner - runs full workflow with pre-filled test cohort
# Uses the existing run_complete_workflow.py to avoid import issues

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

cd "$PROJECT_ROOT"

# Ensure dependencies
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════╗
║     QUICK TEST - FULL WORKFLOW (Interactive)                     ║
╚═══════════════════════════════════════════════════════════════════╝

This will run the complete workflow with a test cohort.
You will still need to answer clarification questions (that's the HITL loop!).

Test cohort:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Male patients age 20-30 with positive flu test in 2020,
 365 days continuous enrollment, excluding immunocompromised"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When prompted, just press Enter to use this test cohort,
or type your own cohort description.

Press Enter to start...
EOF

read -r

echo ""
echo "🚀 Starting workflow..."
echo ""

# Run the complete workflow script with test input
cd "$PROJECT_ROOT/projects/run"
uv run python run_complete_workflow.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ QUICK TEST COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Check outputs in: $PROJECT_ROOT/projects/run/"
echo "   • complete_cohort_output.json"
echo "   • generated_cohort_query.sql"
echo "   • sql_generation_result.json"
echo ""
