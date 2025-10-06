#!/bin/bash
# Run the workflow and capture all output to a log file

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="run_log_${TIMESTAMP}.txt"

echo "════════════════════════════════════════════════════════════════"
echo "OMOP Cohort Workflow - Logging Run"
echo "Log file: $LOG_FILE"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Run make and capture all output (stdout + stderr)
make run 2>&1 | tee "$LOG_FILE"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Log saved to: $LOG_FILE"
echo "════════════════════════════════════════════════════════════════"
