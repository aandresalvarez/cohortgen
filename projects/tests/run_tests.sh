#!/bin/bash
# Test runner for Pydantic AI implementations

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════╗
║     PYDANTIC AI TESTS - Complete Test Suite                    ║
╚═══════════════════════════════════════════════════════════════════╝

Testing:
  • Stage 1: Clinical Clarification (16 tests)
  • Stage 2: Concept Discovery (21 tests)
  • Stage 3: BigQuery SQL Generation (13 tests)
  • Integration: Cross-Stage Data Flow (11 tests)

EOF

cd "$PROJECT_ROOT"

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    uv pip install pytest pytest-asyncio
fi

echo "Running tests..."
echo ""

# Run all tests with verbose output
pytest projects/tests/ -v --tb=short

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ TESTS COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tips:"
echo "   • Run specific file: pytest projects/tests/test_clarification_agent.py -v"
echo "   • Run specific test: pytest projects/tests/test_integration.py::test_name -v"
echo "   • Run with coverage: pytest projects/tests/ --cov=projects/"
echo "   • Show test details: pytest projects/tests/ -vv"
echo ""

