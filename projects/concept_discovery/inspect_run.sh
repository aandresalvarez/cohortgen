#!/bin/bash
# Helper script to inspect Flujo runs directly from SQLite
# Workaround for: flujo lens show <run_id> hanging bug

set -e

DB=".flujo/flujo_ops.db"

if [ ! -f "$DB" ]; then
    echo "Error: Database not found at $DB"
    echo "Make sure you're in the project directory with state_uri='sqlite:///.flujo/flujo_ops.db'"
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to list recent runs
list_runs() {
    echo -e "${BLUE}=== Recent Runs ===${NC}"
    sqlite3 -header -column "$DB" \
        "SELECT 
            substr(run_id, 1, 25) || '...' as run_id,
            substr(pipeline_name, 1, 20) as pipeline,
            status,
            datetime(created_at) as created
         FROM runs 
         ORDER BY created_at DESC 
         LIMIT 10;"
}

# Function to show run details
show_run() {
    local RUN_ID=$1
    
    if [ -z "$RUN_ID" ]; then
        echo "Error: Please provide a run_id"
        echo "Usage: $0 show <run_id>"
        exit 1
    fi
    
    # Try to find full run_id if partial provided
    FULL_ID=$(sqlite3 "$DB" "SELECT run_id FROM runs WHERE run_id LIKE '$RUN_ID%' LIMIT 1;")
    
    if [ -z "$FULL_ID" ]; then
        echo "Error: Run not found for id: $RUN_ID"
        exit 1
    fi
    
    echo -e "${BLUE}=== Run Details ===${NC}"
    sqlite3 -header -column "$DB" \
        "SELECT run_id, status, datetime(created_at) as created 
         FROM runs 
         WHERE run_id='$FULL_ID';"
    
    echo ""
    echo -e "${BLUE}=== Steps ===${NC}"
    sqlite3 -header -column "$DB" \
        "SELECT 
            step_index as '#',
            step_name,
            status,
            CASE 
                WHEN cost_usd IS NOT NULL THEN printf('$%.4f', cost_usd)
                ELSE '-'
            END as cost,
            CASE 
                WHEN token_counts IS NOT NULL THEN token_counts
                ELSE '-'
            END as tokens,
            CASE 
                WHEN execution_time_ms IS NOT NULL THEN printf('%.2fs', execution_time_ms/1000.0)
                ELSE '-'
            END as time
         FROM steps 
         WHERE run_id='$FULL_ID' 
         ORDER BY step_index;"
    
    echo ""
    echo -e "${YELLOW}Tip: To see step output, use:${NC}"
    echo "  $0 output $FULL_ID <step_name>"
}

# Function to get step output
get_output() {
    local RUN_ID=$1
    local STEP_NAME=$2
    
    if [ -z "$RUN_ID" ] || [ -z "$STEP_NAME" ]; then
        echo "Error: Please provide run_id and step_name"
        echo "Usage: $0 output <run_id> <step_name>"
        exit 1
    fi
    
    # Try to find full run_id if partial provided
    FULL_ID=$(sqlite3 "$DB" "SELECT run_id FROM runs WHERE run_id LIKE '$RUN_ID%' LIMIT 1;")
    
    if [ -z "$FULL_ID" ]; then
        echo "Error: Run not found for id: $RUN_ID"
        exit 1
    fi
    
    echo -e "${BLUE}=== Output for step: $STEP_NAME ===${NC}"
    OUTPUT=$(sqlite3 "$DB" "SELECT output FROM steps WHERE run_id='$FULL_ID' AND step_name='$STEP_NAME';")
    
    if [ -z "$OUTPUT" ]; then
        echo "No output found for step: $STEP_NAME"
        echo ""
        echo "Available steps:"
        sqlite3 "$DB" "SELECT step_name FROM steps WHERE run_id='$FULL_ID' ORDER BY step_index;"
        exit 1
    fi
    
    # Try to pretty-print JSON
    if command -v python3 &> /dev/null; then
        echo "$OUTPUT" | python3 -m json.tool 2>/dev/null || echo "$OUTPUT"
    else
        echo "$OUTPUT"
    fi
}

# Function to get final output
get_final() {
    local RUN_ID=$1
    
    if [ -z "$RUN_ID" ]; then
        echo "Error: Please provide a run_id"
        echo "Usage: $0 final <run_id>"
        exit 1
    fi
    
    # Try to find full run_id if partial provided
    FULL_ID=$(sqlite3 "$DB" "SELECT run_id FROM runs WHERE run_id LIKE '$RUN_ID%' LIMIT 1;")
    
    if [ -z "$FULL_ID" ]; then
        echo "Error: Run not found for id: $RUN_ID"
        exit 1
    fi
    
    echo -e "${BLUE}=== Final Output ===${NC}"
    
    # Try common final step names
    for STEP in "emit_for_parent" "finalize" "output" "result"; do
        OUTPUT=$(sqlite3 "$DB" "SELECT output FROM steps WHERE run_id='$FULL_ID' AND step_name='$STEP';")
        if [ -n "$OUTPUT" ]; then
            if command -v python3 &> /dev/null; then
                echo "$OUTPUT" | python3 -m json.tool 2>/dev/null || echo "$OUTPUT"
            else
                echo "$OUTPUT"
            fi
            return
        fi
    done
    
    # If no known final step, get last step
    echo -e "${YELLOW}No known final step found, showing last step output:${NC}"
    LAST_STEP=$(sqlite3 "$DB" "SELECT step_name FROM steps WHERE run_id='$FULL_ID' ORDER BY step_index DESC LIMIT 1;")
    get_output "$FULL_ID" "$LAST_STEP"
}

# Main command dispatcher
case "${1:-list}" in
    list)
        list_runs
        ;;
    show)
        show_run "$2"
        ;;
    output)
        get_output "$2" "$3"
        ;;
    final)
        get_final "$2"
        ;;
    help|--help|-h)
        echo "Flujo Run Inspector - Workaround for 'flujo lens show' bug"
        echo ""
        echo "Usage:"
        echo "  $0 [command] [args]"
        echo ""
        echo "Commands:"
        echo "  list              List recent runs (default)"
        echo "  show <run_id>     Show run details and steps"
        echo "  output <run_id> <step_name>  Show output for specific step"
        echo "  final <run_id>    Show final output of run"
        echo "  help              Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 show run_ec00798feed049"
        echo "  $0 output run_ec00798feed049 decompose_concept_sets"
        echo "  $0 final run_ec00798feed049"
        echo ""
        echo "Note: Partial run_ids are supported (prefix matching)"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

