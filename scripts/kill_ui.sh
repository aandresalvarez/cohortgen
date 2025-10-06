#!/bin/bash
# Kill the Gradio UI process if it's running

echo "Checking for Gradio UI process on port 7860..."

if lsof -ti:7860 > /dev/null 2>&1; then
    echo "Found process on port 7860. Killing..."
    lsof -ti:7860 | xargs kill -9 2>/dev/null
    echo "✓ Process killed"
else
    echo "✓ No process found on port 7860"
fi

