"""
Gradio UI for OMOP Cohort Builder.

Dashboard-style interface with run list and chat-style execution view.
"""

import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import gradio as gr
import pandas as pd
from dotenv import load_dotenv

# Add project root to path first
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from project root .env file
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

from projects.ui.models import RunStatus, StageStatus
from projects.ui.service import CohortService
from projects.ui.analytics_dashboard import (
    export_analytics_csv,
    export_analytics_json,
    generate_ai_insights,
    generate_data_quality_html,
    generate_summary_cards_html,
    prepare_age_chart_data,
    prepare_characteristics_table,
    prepare_gender_chart_data,
    prepare_monthly_trend_data,
    prepare_year_trend_data,
)

# Initialize service
service = CohortService()


def format_run_status(status: str) -> str:
    """Format run status with emoji."""
    status_map = {
        "pending": "⏸ Pending",
        "running": "● Running",
        "succeeded": "✓ Complete",
        "failed": "⚠ Failed",
        "cancelled": "✕ Cancelled",
    }
    return status_map.get(status, status)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds / 3600:.1f}h"


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to human-readable format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        now = datetime.now()

        # If today, show time
        if dt.date() == now.date():
            return dt.strftime("Today %I:%M %p")

        # If yesterday
        if (now - dt).days == 1:
            return dt.strftime("Yesterday %I:%M %p")

        # Otherwise show date
        return dt.strftime("%b %d, %Y")
    except Exception:
        return iso_timestamp


def get_runs_list() -> list[list[str]]:
    """Get formatted runs list for display."""
    runs = service.list_runs()

    if not runs:
        return []

    formatted = []
    for r in runs:
        formatted.append(
            [
                r["run_id"],
                r["name"],
                format_run_status(r["status"]),
                format_timestamp(r["created_at"]),
            ]
        )

    return formatted


def create_new_run(
    description: str,
    name: str,
    fast_mode: bool,
    max_concept_sets: int,
    max_queries_per_set: int,
    search_top_k: int,
    bigquery_project: str,
    omop_dataset: str,
    bigquery_location: str,
) -> tuple[str, list[list[str]]]:
    """Create a new run and return updated run list."""
    if not description.strip():
        return "⚠️ Please enter a cohort description", get_runs_list()

    try:
        run_id = service.create_run(
            cohort_description=description.strip(),
            name=name.strip() if name.strip() else None,
            fast_mode=fast_mode,
            max_concept_sets=max_concept_sets,
            max_queries_per_set=max_queries_per_set,
            search_top_k=search_top_k,
            bigquery_project_id=bigquery_project.strip() if bigquery_project.strip() else "",
            omop_dataset_id=omop_dataset.strip() if omop_dataset.strip() else "",
            bigquery_location=bigquery_location.strip() if bigquery_location.strip() else "US",
        )

        return f"✅ Created run #{run_id[:6]}", get_runs_list()

    except Exception as e:
        return f"❌ Error: {str(e)}", get_runs_list()


def start_selected_run(selected_run_id: str) -> str:
    """Start executing the selected run."""
    if not selected_run_id:
        return "⚠️ Please select a run first"

    try:
        service.start_run(selected_run_id)
        return f"▶️ Started run #{selected_run_id[:6]}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def delete_selected_run(selected_run_id: str) -> tuple[str, list[list[str]]]:
    """Delete the selected run."""
    if not selected_run_id:
        return "⚠️ Please select a run first", get_runs_list()

    try:
        success = service.delete_run(selected_run_id)
        if success:
            return f"🗑️ Deleted run #{selected_run_id[:6]}", get_runs_list()
        else:
            return f"⚠️ Run not found", get_runs_list()
    except Exception as e:
        return f"❌ Error: {str(e)}", get_runs_list()


def duplicate_selected_run(selected_run_id: str) -> tuple[str, list[list[str]]]:
    """Duplicate the selected run."""
    if not selected_run_id:
        return "⚠️ Please select a run first", get_runs_list()

    try:
        new_run_id = service.duplicate_run(selected_run_id)
        return f"📋 Duplicated as #{new_run_id[:6]}", get_runs_list()
    except Exception as e:
        return f"❌ Error: {str(e)}", get_runs_list()


def test_individual_stage(run_id: str, stage_num: int) -> str:
    """Run a single stage for testing purposes."""
    if not run_id:
        return "⚠️ No run selected"
    
    try:
        run = service.storage.load_run(run_id)
        if not run:
            return f"❌ Run {run_id} not found"
        
        stage_methods = {
            1: service._execute_stage1,
            2: service._execute_stage2,
            3: service._execute_stage3,
            4: service._execute_stage4,
        }
        
        method = stage_methods.get(stage_num)
        if not method:
            return f"❌ Invalid stage number: {stage_num}"
        
        # Run the stage in background
        import threading
        def run_stage():
            try:
                method(run)
            except Exception as e:
                print(f"Error in stage {stage_num}: {e}")
        
        thread = threading.Thread(target=run_stage, daemon=True)
        thread.start()
        
        return f"✅ Stage {stage_num} started! Refresh to see results (auto-refresh will show progress)."
    
    except Exception as e:
        return f"❌ Stage {stage_num} failed: {str(e)}"


def get_run_display(run_id: Optional[str]) -> Tuple[str, bool]:
    """Get formatted display for a run and whether Stage 4 is complete."""
    if not run_id:
        return "⬅️ Select a run from the list to view details", False

    run = service.get_run(run_id)
    if not run:
        return f"⚠️ Run {run_id} not found", False

    # Build display
    output = []

    # Header
    output.append(f"# {run.name}")
    output.append(
        f"**Run ID:** `{run.run_id}` | **Status:** {format_run_status(run.status.value)} | "
        f"**Created:** {format_timestamp(run.created_at)}"
    )
    if run.total_duration_seconds > 0:
        output.append(f"**Duration:** {format_duration(run.total_duration_seconds)}")
    output.append("\n---\n")

    # Input
    output.append("## 📝 Input")
    output.append(f"> {run.user_inputs.cohort_description}")
    output.append("")

    if run.user_inputs.fast_mode:
        output.append("⚡ **Fast Mode:** ON")
        output.append("")

    # Stages
    output.append("\n---\n")

    stage4_complete = False
    if not run.stages:
        output.append("*No stages started yet. Click 'Start Run' to begin.*")
    else:
        for stage in run.stages:
            if stage.stage == 4 and stage.status == StageStatus.COMPLETE:
                stage4_complete = True
            output.append(render_stage(stage, run))
            output.append("")

    # Error if failed
    if run.error:
        output.append("\n---\n")
        output.append("## ❌ Error")
        output.append(f"```\n{run.error}\n```")

    return "\n".join(output), stage4_complete


def update_display_and_dashboard(run_id):
    """Update run display and auto-load dashboard if Stage 4 complete."""
    display_text, stage4_complete = get_run_display(run_id)
    
    # Auto-load dashboard data if Stage 4 is complete
    if stage4_complete and run_id:
        dashboard_data = load_stage4_dashboard(run_id)
        return (display_text, gr.update(visible=True, open=True)) + dashboard_data
    else:
        # Return empty dashboard data when not visible
        empty_df = pd.DataFrame()
        return (display_text, gr.update(visible=False)) + ("", "", "", "", empty_df, empty_df, empty_df, empty_df, empty_df, "")


def update_display_only(run_id):
    """Update ONLY run display and accordion visibility (for timer refresh)."""
    display_text, stage4_complete = get_run_display(run_id)
    
    # Only update visibility, don't touch dashboard data
    if stage4_complete:
        return display_text, gr.update(visible=True, open=True)
    else:
        return display_text, gr.update(visible=False)


def format_sql(sql_text: str) -> str:
    """Format SQL for display with basic syntax highlighting using HTML."""
    if not sql_text:
        return ""
    
    # Add line numbers and basic formatting
    lines = sql_text.strip().split('\n')
    formatted_lines = []
    
    for i, line in enumerate(lines, 1):
        # Basic keyword highlighting
        line_html = line
        keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'INNER JOIN', 'RIGHT JOIN',
                   'GROUP BY', 'ORDER BY', 'HAVING', 'WITH', 'AS', 'DISTINCT', 'COUNT', 'SUM',
                   'AVG', 'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'AND', 'OR',
                   'IN', 'NOT', 'NULL', 'IS', 'LIKE', 'BETWEEN', 'UNION', 'UNION ALL']
        
        for keyword in keywords:
            # Case-insensitive replacement but preserve original case for non-keywords
            import re
            line_html = re.sub(
                r'\b(' + keyword + r')\b',
                r'<span style="color: #0066CC; font-weight: bold;">\1</span>',
                line_html,
                flags=re.IGNORECASE
            )
        
        formatted_lines.append(f'<span style="color: #888;">{i:3d}|</span> {line_html}')
    
    return '<div style="font-family: monospace; white-space: pre; background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">' + '\n'.join(formatted_lines) + '</div>'


def render_stage(stage_result, run) -> str:
    """Render a stage result as markdown."""
    stage_names = {
        1: "Clinical Clarification",
        2: "Concept Discovery",
        3: "SQL Generation",
        4: "Analytics",
    }

    stage_name = stage_names.get(stage_result.stage, f"Stage {stage_result.stage}")

    # Status icon
    if stage_result.status == StageStatus.COMPLETE:
        icon = "✅"
    elif stage_result.status == StageStatus.RUNNING:
        icon = "🔄"
    elif stage_result.status == StageStatus.FAILED:
        icon = "❌"
    else:
        icon = "⏸"

    # Build stage display
    output = []
    duration = (
        f" ({format_duration(stage_result.metrics.duration_seconds)})"
        if stage_result.metrics.duration_seconds > 0
        else ""
    )

    output.append(f"## {icon} Stage {stage_result.stage}: {stage_name}{duration}")

    # Stage-specific content
    if stage_result.status == StageStatus.COMPLETE:
        if stage_result.stage == 1:
            # Show clinical definition and conversation log
            if run.stage1_path:
                output.append("")
                output.append("**Clinical Definition Complete**")
                
                # Show conversation log if available
                if run.stage1_log_path:
                    log_content = get_stage1_log(run.run_id)
                    if log_content:
                        output.append("")
                        output.append("**Conversation Log:**")
                        output.append("```")
                        # Show last 30 lines or so
                        lines = log_content.strip().split("\n")
                        if len(lines) > 30:
                            output.append("...")
                            output.extend(lines[-30:])
                        else:
                            output.extend(lines)
                        output.append("```")
                
        elif stage_result.stage == 2:
            # Show concept sets found
            if stage_result.metrics.concepts_found > 0:
                output.append("")
                output.append(
                    f"**Found {stage_result.metrics.concepts_found} OMOP concepts**"
                )
            
            # Show log if available
            if run.stage2_log_path:
                log_content = get_stage_log(run.run_id, 2)
                if log_content:
                    output.append("")
                    output.append("**Discovery Log:**")
                    output.append("```")
                    lines = log_content.strip().split("\n")
                    if len(lines) > 30:
                        output.append("...")
                        output.extend(lines[-30:])
                    else:
                        output.extend(lines)
                    output.append("```")
                    
        elif stage_result.stage == 3:
            # Show SQL generated with FINAL validation status prominently
            output.append("")
            
            # Show validation if available - THIS IS THE FINAL RESULT
            validation_shown = False
            if run.stage3_validation_path:
                try:
                    import json
                    with open(run.stage3_validation_path) as f:
                        validation = json.load(f)
                    
                    if validation.get("is_valid"):
                        output.append("## ✅ **SQL GENERATION SUCCESSFUL**")
                        output.append("")
                        output.append("**BigQuery Validation:** ✅ Passed (dry run successful)")
                        
                        # Check if fixes were needed by looking at the log
                        fixes_needed = False
                        if run.stage3_log_path:
                            try:
                                log_content = get_stage_log(run.run_id, 3)
                                if "validation failed (attempt" in log_content.lower():
                                    fixes_needed = True
                            except Exception:
                                pass
                        
                        if fixes_needed:
                            output.append("**Note:** SQL was automatically fixed after initial validation errors")
                        
                        if validation.get("estimated_cost_usd") is not None:
                            output.append(f"- **Estimated query cost:** ${validation['estimated_cost_usd']:.4f}")
                        if validation.get("total_bytes_processed"):
                            gb = validation["total_bytes_processed"] / (1024**3)
                            output.append(f"- **Data to process:** {gb:.2f} GB")
                        validation_shown = True
                    else:
                        output.append("## ❌ **SQL GENERATION FAILED**")
                        output.append("")
                        output.append("**BigQuery Validation:** ❌ Failed after all fix attempts")
                        if validation.get("errors"):
                            output.append("")
                            output.append("**Errors:**")
                            for error in validation.get("errors", [])[:3]:  # Show up to 3 errors
                                output.append(f"- {error}")
                        validation_shown = True
                except Exception:
                    pass
            
            if not validation_shown:
                output.append("**BigQuery SQL Generated**")
            
            # Show formatted SQL automatically
            if run.stage3_sql_path:
                try:
                    with open(run.stage3_sql_path) as f:
                        sql = f.read()
                    
                    output.append("")
                    output.append("**Generated SQL:**")
                    output.append("```sql")
                    
                    # Show full SQL with line numbers (first 50 lines)
                    lines = sql.split('\n')
                    for i, line in enumerate(lines[:50], 1):
                        output.append(f"{i:3d} | {line}")
                    
                    if len(lines) > 50:
                        output.append(f"... ({len(lines) - 50} more lines)")
                    
                    output.append("```")
                    output.append(f"*Total: {len(lines)} lines, {len(sql)} characters*")
                    output.append("")
                    output.append("💡 *Full formatted SQL with syntax highlighting available in 'Download Artifacts & Logs' → 'Stage 3 (SQL)' → 'Format SQL' button*")
                except Exception:
                    pass
            
            # Show log summary (collapsed by default in user's mind - just show key info)
            if run.stage3_log_path:
                log_content = get_stage_log(run.run_id, 3)
                if log_content:
                    # Count validation attempts
                    attempts = log_content.count("Validating SQL (dry run)")
                    fixes = log_content.count("Attempting to fix SQL")
                    
                    output.append("")
                    output.append("**Process Summary:**")
                    if attempts > 1:
                        output.append(f"- Generated SQL and validated in {attempts} iterations")
                        output.append(f"- Applied {fixes} automatic fix{'es' if fixes != 1 else ''}")
                    else:
                        output.append("- Generated SQL and validated successfully on first attempt")
                    
                    output.append("")
                    output.append("*💡 View full generation log in 'Download Artifacts & Logs' section below for detailed fix history*")
        elif stage_result.stage == 4:
            # Show analytics complete with link to dashboard
            output.append("")
            output.append("**✅ Analytics Complete**")
            output.append(f"- Duration: {format_duration(stage_result.metrics.duration_seconds)}")
            output.append("")
            output.append("📊 **View the interactive dashboard below** ⬇️")
            output.append("")
            output.append("*The full analytics dashboard with visualizations, AI insights, and exports is available in the 'Analytics Dashboard' section below this summary.*")

    elif stage_result.status == StageStatus.RUNNING:
        output.append("")
        if stage_result.stage == 1:
            output.append("*Running clarification (watching agent conversation...)*")
            
            # Show live log if available
            log_content = get_stage1_log(run.run_id)
            if log_content:
                output.append("")
                output.append("**Live Conversation:**")
                output.append("```")
                # Show last 20 lines for running stage
                lines = log_content.strip().split("\n")
                if len(lines) > 20:
                    output.append("...")
                    output.extend(lines[-20:])
                else:
                    output.extend(lines)
                output.append("```")
        elif stage_result.stage == 2:
            output.append("*Discovering OMOP concepts...*")
            
            # Show live log if available
            log_content = get_stage_log(run.run_id, 2)
            if log_content:
                output.append("")
                output.append("**Live Progress:**")
                output.append("```")
                lines = log_content.strip().split("\n")
                if len(lines) > 20:
                    output.append("...")
                    output.extend(lines[-20:])
                else:
                    output.extend(lines)
                output.append("```")
        elif stage_result.stage == 3:
            output.append("*Generating SQL...*")
            
            # Show live log if available
            log_content = get_stage_log(run.run_id, 3)
            if log_content:
                output.append("")
                output.append("**Live Progress:**")
                output.append("```")
                lines = log_content.strip().split("\n")
                if len(lines) > 15:
                    output.append("...")
                    output.extend(lines[-15:])
                else:
                    output.extend(lines)
                output.append("```")
        else:
            output.append("*In progress...*")

    elif stage_result.status == StageStatus.FAILED:
        output.append("")
        output.append(f"**Error:** {stage_result.metrics.error_message}")

    else:
        output.append("")
        output.append("*Waiting...*")

    return "\n".join(output)


def get_stage1_log(run_id: str) -> str:
    """Get the Stage 1 conversation log if it exists."""
    if not run_id:
        return ""
    
    try:
        content = service.storage.load_artifact(run_id, "stage1_log.txt")
        return content or ""
    except Exception:
        return ""


def get_stage_log(run_id: str, stage: int) -> str:
    """Get the log for a specific stage if it exists."""
    if not run_id:
        return ""
    
    try:
        content = service.storage.load_artifact(run_id, f"stage{stage}_log.txt")
        return content or ""
    except Exception:
        return ""


def load_artifact(run_id: str, artifact_type: str) -> str:
    """Load an artifact file for display."""
    if not run_id:
        return "⚠️ No run selected"

    run = service.get_run(run_id)
    if not run:
        return "⚠️ Run not found"

    artifact_map = {
        "stage1": "stage1.json",
        "stage2": "stage2.json",
        "sql": "query.sql",
        "analytics": "analytics.json",
    }

    filename = artifact_map.get(artifact_type)
    if not filename:
        return "⚠️ Invalid artifact type"

    content = service.storage.load_artifact(run_id, filename)
    if not content:
        return "⚠️ Artifact not found (stage may not be complete yet)"

    return content


def load_stage4_dashboard(run_id: str) -> Tuple[str, str, str, str, Any, Any, Any, Any, Any, str]:
    """
    Load and prepare Stage 4 analytics dashboard.
    
    Returns: (summary_cards_html, quick_stats, quality_html, insights_md, 
              gender_chart_df, age_chart_df, year_chart_df, monthly_chart_df, 
              characteristics_table_df, raw_json)
    """
    if not run_id:
        empty_df = pd.DataFrame()
        return ("", "*No run selected*", "", "*No run selected*", 
                empty_df, empty_df, empty_df, empty_df, empty_df, "")
    
    run = service.get_run(run_id)
    if not run or not run.stage4_path:
        empty_df = pd.DataFrame()
        return ("", "*Analytics not available yet*", "", "*Analytics not available yet*", 
                empty_df, empty_df, empty_df, empty_df, empty_df, "")
    
    try:
        # Load analytics JSON
        with open(run.stage4_path) as f:
            analytics = json.load(f)
        
        if analytics.get("status") != "complete":
            empty_df = pd.DataFrame()
            return ("", "*Analytics incomplete*", "", "*Analytics incomplete*", 
                    empty_df, empty_df, empty_df, empty_df, empty_df, 
                    json.dumps(analytics, indent=2))
        
        # Generate all dashboard components
        summary_html = generate_summary_cards_html(analytics)
        quality_html = generate_data_quality_html(analytics)
        # Get description from user_inputs if available
        cohort_description = ""
        if hasattr(run, 'user_inputs') and run.user_inputs:
            cohort_description = run.user_inputs.cohort_description
        insights = generate_ai_insights(analytics, cohort_description)
        
        # Prepare chart data (use 'is None' to avoid DataFrame ambiguity)
        gender_df = prepare_gender_chart_data(analytics)
        if gender_df is None:
            gender_df = pd.DataFrame()
        
        age_df = prepare_age_chart_data(analytics)
        if age_df is None:
            age_df = pd.DataFrame()
        
        year_df = prepare_year_trend_data(analytics)
        if year_df is None:
            year_df = pd.DataFrame()
        
        monthly_df = prepare_monthly_trend_data(analytics)
        if monthly_df is None:
            monthly_df = pd.DataFrame()
        
        char_df = prepare_characteristics_table(analytics)
        
        # Generate quick stats text
        results = analytics.get("results", {})
        cohort_size = 0
        if "cohort_size" in results and isinstance(results["cohort_size"], list):
            if results["cohort_size"]:
                cohort_size = results["cohort_size"][0].get("n", 0)
        
        quick_stats = f"**Total Patients:** {cohort_size:,}"
        
        raw_json = json.dumps(analytics, indent=2)
        
        return (summary_html, quick_stats, quality_html, insights, 
                gender_df, age_df, year_df, monthly_df, char_df, raw_json)
    
    except Exception as e:
        empty_df = pd.DataFrame()
        return ("", f"*Error loading dashboard: {str(e)}*", "", f"*Error: {str(e)}*", 
                empty_df, empty_df, empty_df, empty_df, empty_df, "")


# Build Gradio interface
with gr.Blocks(
    title="OMOP Cohort Builder", theme=gr.themes.Soft(), css="""
    .run-list { font-family: monospace; }
    .status-indicator { font-weight: bold; }
"""
) as app:
    gr.Markdown("# 🧬 OMOP Cohort Builder")

    with gr.Row():
        # Left sidebar: Run list
        with gr.Column(scale=1, min_width=300):
            gr.Markdown("## 📋 Runs")

            new_run_btn = gr.Button("+ New Run", variant="primary", size="lg")

            # Search/filter (future enhancement)
            # run_search = gr.Textbox(placeholder="Search runs...", show_label=False)

            runs_table = gr.Dataframe(
                headers=["ID", "Name", "Status", "Created"],
                datatype=["str", "str", "str", "str"],
                col_count=(4, "fixed"),
                value=get_runs_list(),
                interactive=False,
                wrap=True,
            )

            selected_run_id = gr.State(value=None)

            # Action buttons
            with gr.Row():
                start_btn = gr.Button("▶️ Start", size="sm")
                duplicate_btn = gr.Button("📋 Dup", size="sm")

            with gr.Row():
                delete_btn = gr.Button("🗑️ Delete", size="sm", variant="stop")

            action_status = gr.Textbox(
                label="Status", interactive=False, show_label=False
            )

        # Right panel: Run details
        with gr.Column(scale=3):
            run_display = gr.Markdown(
                "⬅️ Select a run from the list to view details",
                elem_classes=["run-display"],
            )
            
            # Analytics Dashboard - Only visible when Stage 4 is complete
            analytics_dashboard_accordion = gr.Accordion("📊 Analytics Dashboard", open=True, visible=False)
            with analytics_dashboard_accordion:
                with gr.Row():
                    gr.Markdown("### Interactive Cohort Analytics")
                    refresh_dashboard_btn = gr.Button("🔄 Refresh", size="sm", scale=0, min_width=100)
                
                with gr.Tabs():
                    with gr.Tab("📈 Overview"):
                        # Summary cards
                        stage4_summary_cards_main = gr.HTML(label="Summary Metrics")
                        
                        # Quick stats
                        stage4_quick_stats_main = gr.Markdown(value="*Click 'Load Dashboard' button below*")
                        
                        # Data quality indicators
                        gr.Markdown("#### Data Quality")
                        stage4_quality_main = gr.HTML(label="Quality Indicators")
                    
                    with gr.Tab("👥 Demographics"):
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("#### Gender Distribution")
                                stage4_gender_chart_main = gr.BarPlot(
                                    x="Gender",
                                    y="Count",
                                    title="Gender Distribution",
                                    tooltip=["Gender", "Count", "Percentage"],
                                    y_title="Number of Patients",
                                    height=300,
                                    show_label=False
                                )
                            
                            with gr.Column():
                                gr.Markdown("#### Age Distribution")
                                stage4_age_chart_main = gr.BarPlot(
                                    x="Age Group",
                                    y="Count",
                                    title="Age Distribution",
                                    tooltip=["Age Group", "Count", "Percentage"],
                                    y_title="Number of Patients",
                                    height=300,
                                    show_label=False
                                )
                        
                        gr.Markdown("#### Detailed Characteristics")
                        stage4_characteristics_table_main = gr.DataFrame(
                            headers=["Characteristic", "Count", "Percentage", "95% CI"],
                            label="Cohort Characteristics with Confidence Intervals",
                            interactive=False
                        )
                    
                    with gr.Tab("📅 Temporal Trends"):
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("#### Annual Enrollment")
                                stage4_year_chart_main = gr.LinePlot(
                                    x="Year",
                                    y="Patients",
                                    title="Patients by Index Year",
                                    tooltip=["Year", "Patients"],
                                    height=300,
                                    show_label=False
                                )
                            
                            with gr.Column():
                                gr.Markdown("#### Monthly Trend")
                                stage4_monthly_chart_main = gr.LinePlot(
                                    x="Month",
                                    y="Patients",
                                    title="Monthly Enrollment Pattern",
                                    tooltip=["Month", "Patients"],
                                    height=300,
                                    show_label=False
                                )
                    
                    with gr.Tab("🔍 AI Insights"):
                        gr.Markdown("### AI-Powered Analysis")
                        stage4_insights_main = gr.Markdown(
                            value="*Click 'Load Dashboard' button below*"
                        )
                    
                    with gr.Tab("💾 Export & Raw Data"):
                        gr.Markdown("#### Export Options")
                        
                        with gr.Row():
                            export_csv_btn_main = gr.Button("📥 Download CSV (Characteristics)", size="sm")
                            export_json_btn_main = gr.Button("📥 Download JSON (Full Analytics)", size="sm")
                        
                        stage4_csv_download_main = gr.File(label="CSV Download", visible=False)
                        stage4_json_download_main = gr.File(label="JSON Download", visible=False)
                        
                        gr.Markdown("#### Raw JSON Data")
                        stage4_output_main = gr.Code(
                            language="json", interactive=False, lines=10
                        )
            
            # Individual stage testing
            with gr.Accordion("🔬 Individual Stage Testing", open=False):
                gr.Markdown("Run or re-run individual stages for debugging (requires existing run)")
                with gr.Row():
                    test_stage1_btn = gr.Button("Test Stage 1")
                    test_stage2_btn = gr.Button("Test Stage 2")
                    test_stage3_btn = gr.Button("Test Stage 3")
                    test_stage4_btn = gr.Button("Test Stage 4")
                test_stage_status = gr.Markdown("")

            with gr.Accordion("📥 Download Artifacts & Logs", open=False):
                with gr.Tabs():
                    with gr.Tab("Stage 1 Conversation"):
                        stage1_log_output = gr.Textbox(
                            interactive=False, lines=15, max_lines=30, show_label=False
                        )
                        load_stage1_log_btn = gr.Button("Load Stage 1 Conversation Log")
                    
                    with gr.Tab("Stage 2 Discovery Log"):
                        stage2_log_output = gr.Textbox(
                            interactive=False, lines=15, max_lines=30, show_label=False
                        )
                        load_stage2_log_btn = gr.Button("Load Stage 2 Discovery Log")
                    
                    with gr.Tab("Stage 3 SQL Log"):
                        stage3_log_output = gr.Textbox(
                            interactive=False, lines=15, max_lines=30, show_label=False
                        )
                        load_stage3_log_btn = gr.Button("Load Stage 3 SQL Generation Log")
                    
                    with gr.Tab("Stage 1 (JSON)"):
                        stage1_output = gr.Code(
                            language="json", interactive=False, lines=10
                        )
                        load_stage1_btn = gr.Button("Load Stage 1 Output")

                    with gr.Tab("Stage 2 (JSON)"):
                        stage2_output = gr.Code(
                            language="json", interactive=False, lines=10
                        )
                        load_stage2_btn = gr.Button("Load Stage 2 Output")

                    with gr.Tab("Stage 3 (SQL)"):
                        stage3_output = gr.Code(
                            language="sql", interactive=False, lines=10
                        )
                        load_stage3_btn = gr.Button("Load Stage 3 SQL")
                        
                        gr.Markdown("### Formatted SQL Preview")
                        stage3_sql_formatted = gr.HTML(label="Formatted SQL")
                        format_sql_btn = gr.Button("🎨 Format SQL with Syntax Highlighting")

                    with gr.Tab("📊 Stage 4 Analytics Dashboard"):
                        gr.Markdown("### Interactive Cohort Analytics")
                        
                        with gr.Tabs():
                            with gr.Tab("📈 Overview"):
                                # Summary cards
                                stage4_summary_cards = gr.HTML(label="Summary Metrics")
                                
                                # Quick stats
                                stage4_quick_stats = gr.Markdown(value="*Load analytics to view dashboard*")
                                
                                # Data quality indicators
                                gr.Markdown("#### Data Quality")
                                stage4_quality = gr.HTML(label="Quality Indicators")
                            
                            with gr.Tab("👥 Demographics"):
                                with gr.Row():
                                    with gr.Column():
                                        gr.Markdown("#### Gender Distribution")
                                        stage4_gender_chart = gr.BarPlot(
                                            x="Gender",
                                            y="Count",
                                            title="Gender Distribution",
                                            tooltip=["Gender", "Count", "Percentage"],
                                            y_title="Number of Patients",
                                            height=300,
                                            show_label=False
                                        )
                                    
                                    with gr.Column():
                                        gr.Markdown("#### Age Distribution")
                                        stage4_age_chart = gr.BarPlot(
                                            x="Age Group",
                                            y="Count",
                                            title="Age Distribution",
                                            tooltip=["Age Group", "Count", "Percentage"],
                                            y_title="Number of Patients",
                                            height=300,
                                            show_label=False
                                        )
                                
                                gr.Markdown("#### Detailed Characteristics")
                                stage4_characteristics_table = gr.DataFrame(
                                    headers=["Characteristic", "Count", "Percentage", "95% CI"],
                                    label="Cohort Characteristics with Confidence Intervals",
                                    interactive=False
                                )
                            
                            with gr.Tab("📅 Temporal Trends"):
                                with gr.Row():
                                    with gr.Column():
                                        gr.Markdown("#### Annual Enrollment")
                                        stage4_year_chart = gr.LinePlot(
                                            x="Year",
                                            y="Patients",
                                            title="Patients by Index Year",
                                            tooltip=["Year", "Patients"],
                                            height=300,
                                            show_label=False
                                        )
                                    
                                    with gr.Column():
                                        gr.Markdown("#### Monthly Trend")
                                        stage4_monthly_chart = gr.LinePlot(
                                            x="Month",
                                            y="Patients",
                                            title="Monthly Enrollment Pattern",
                                            tooltip=["Month", "Patients"],
                                            height=300,
                                            show_label=False
                                        )
                            
                            with gr.Tab("🔍 AI Insights"):
                                gr.Markdown("### AI-Powered Analysis")
                                stage4_insights = gr.Markdown(
                                    value="*Load analytics to generate insights*"
                                )
                            
                            with gr.Tab("💾 Export & Raw Data"):
                                gr.Markdown("#### Export Options")
                                
                                with gr.Row():
                                    export_csv_btn = gr.Button("📥 Download CSV (Characteristics)", size="sm")
                                    export_json_btn = gr.Button("📥 Download JSON (Full Analytics)", size="sm")
                                
                                stage4_csv_download = gr.File(label="CSV Download", visible=False)
                                stage4_json_download = gr.File(label="JSON Download", visible=False)
                                
                                gr.Markdown("#### Raw JSON Data")
                                stage4_output = gr.Code(
                                    language="json", interactive=False, lines=10
                                )
                        
                        load_stage4_btn = gr.Button("🔄 Load/Refresh Dashboard", variant="primary")

    # New run modal
    with gr.Row(visible=False) as new_run_panel:
        with gr.Column():
            gr.Markdown("## 📝 New Cohort Run")

            description_input = gr.Textbox(
                label="Cohort Description",
                placeholder="Male patients age 20-30 with positive flu test in 2020",
                lines=3,
            )

            name_input = gr.Textbox(
                label="Run Name (optional)",
                placeholder="Auto-generated if empty",
            )

            with gr.Accordion("⚙️ Advanced Settings", open=False):
                fast_mode_toggle = gr.Checkbox(
                    label="Fast Mode (lower quality, faster results)",
                    value=False,
                )

                max_concept_sets = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="Max Concept Sets",
                )

                max_queries_per_set = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=3,
                    step=1,
                    label="Max Queries Per Set",
                )

                search_top_k = gr.Slider(
                    minimum=5,
                    maximum=50,
                    value=10,
                    step=5,
                    label="Search Top K",
                )
                
                gr.Markdown("### BigQuery Configuration (Optional)")
                
                bigquery_project = gr.Textbox(
                    label="BigQuery Project ID",
                    placeholder="Leave empty to use GOOGLE_CLOUD_PROJECT from .env",
                    value=""
                )
                
                omop_dataset = gr.Textbox(
                    label="OMOP Dataset ID",
                    placeholder="e.g., your-project.your_omop_dataset",
                    value=""
                )
                
                bigquery_location = gr.Textbox(
                    label="BigQuery Location",
                    placeholder="US",
                    value="US"
                )

            with gr.Row():
                create_run_btn = gr.Button("Create Run", variant="primary")
                cancel_run_btn = gr.Button("Cancel")

            create_status = gr.Textbox(
                label="Status", interactive=False, show_label=False
            )

    # Auto-refresh for running runs
    refresh_timer = gr.Timer(value=2.0, active=True)

    # Event handlers

    def select_run(evt: gr.SelectData):
        """Handle run selection from table."""
        if evt.index[0] >= 0:
            runs = service.list_runs()
            if evt.index[0] < len(runs):
                return runs[evt.index[0]]["run_id"]
        return None

    runs_table.select(select_run, outputs=selected_run_id).then(
        update_display_and_dashboard,
        inputs=selected_run_id,
        outputs=[
            run_display,
            analytics_dashboard_accordion,
            stage4_summary_cards_main,
            stage4_quick_stats_main,
            stage4_quality_main,
            stage4_insights_main,
            stage4_gender_chart_main,
            stage4_age_chart_main,
            stage4_year_chart_main,
            stage4_monthly_chart_main,
            stage4_characteristics_table_main,
            stage4_output_main,
        ],
    )
    
    # Manual refresh button for analytics dashboard
    refresh_dashboard_btn.click(
        load_stage4_dashboard,
        inputs=selected_run_id,
        outputs=[
            stage4_summary_cards_main,
            stage4_quick_stats_main,
            stage4_quality_main,
            stage4_insights_main,
            stage4_gender_chart_main,
            stage4_age_chart_main,
            stage4_year_chart_main,
            stage4_monthly_chart_main,
            stage4_characteristics_table_main,
            stage4_output_main,
        ],
    )

    # New run button shows the form
    new_run_btn.click(
        lambda: gr.update(visible=True),
        outputs=new_run_panel,
    )

    # Create run
    create_run_btn.click(
        create_new_run,
        inputs=[
            description_input,
            name_input,
            fast_mode_toggle,
            max_concept_sets,
            max_queries_per_set,
            search_top_k,
            bigquery_project,
            omop_dataset,
            bigquery_location,
        ],
        outputs=[create_status, runs_table],
    ).then(
        lambda: gr.update(visible=False),
        outputs=new_run_panel,
    )

    # Cancel new run
    cancel_run_btn.click(
        lambda: gr.update(visible=False),
        outputs=new_run_panel,
    )

    # Start run
    start_btn.click(
        start_selected_run,
        inputs=selected_run_id,
        outputs=action_status,
    )

    # Delete run
    delete_btn.click(
        delete_selected_run,
        inputs=selected_run_id,
        outputs=[action_status, runs_table],
    )
    
    # Individual stage testing
    test_stage1_btn.click(
        lambda run_id: test_individual_stage(run_id, 1),
        inputs=selected_run_id,
        outputs=test_stage_status,
    )
    
    test_stage2_btn.click(
        lambda run_id: test_individual_stage(run_id, 2),
        inputs=selected_run_id,
        outputs=test_stage_status,
    )
    
    test_stage3_btn.click(
        lambda run_id: test_individual_stage(run_id, 3),
        inputs=selected_run_id,
        outputs=test_stage_status,
    )
    
    test_stage4_btn.click(
        lambda run_id: test_individual_stage(run_id, 4),
        inputs=selected_run_id,
        outputs=test_stage_status,
    ).then(
        lambda: None,
        outputs=selected_run_id,
    ).then(
        get_run_display,
        inputs=selected_run_id,
        outputs=run_display,
    )

    # Duplicate run
    duplicate_btn.click(
        duplicate_selected_run,
        inputs=selected_run_id,
        outputs=[action_status, runs_table],
    )

    # Helper functions for loading logs
    def load_stage_log(run_id: str, stage: int) -> str:
        """Load a stage log file."""
        if not run_id:
            return "⚠️ No run selected"
        
        run = service.get_run(run_id)
        if not run:
            return "⚠️ Run not found"
        
        # Get the appropriate log path
        log_path = None
        if stage == 1 and run.stage1_log_path:
            log_path = run.stage1_log_path
        elif stage == 2 and run.stage2_log_path:
            log_path = run.stage2_log_path
        elif stage == 3 and run.stage3_log_path:
            log_path = run.stage3_log_path
        
        if not log_path or not os.path.exists(log_path):
            return f"⚠️ Stage {stage} log not available yet"
        
        try:
            with open(log_path, 'r') as f:
                content = f.read()
            return content if content else f"⚠️ Stage {stage} log is empty"
        except Exception as e:
            return f"❌ Error loading Stage {stage} log: {str(e)}"
    
    # Load artifacts
    load_stage1_log_btn.click(
        lambda run_id: load_stage_log(run_id, 1),
        inputs=selected_run_id,
        outputs=stage1_log_output,
    )
    
    load_stage2_log_btn.click(
        lambda run_id: load_stage_log(run_id, 2),
        inputs=selected_run_id,
        outputs=stage2_log_output,
    )
    
    load_stage3_log_btn.click(
        lambda run_id: load_stage_log(run_id, 3),
        inputs=selected_run_id,
        outputs=stage3_log_output,
    )
    
    load_stage1_btn.click(
        load_artifact,
        inputs=[selected_run_id, gr.State("stage1")],
        outputs=stage1_output,
    )

    load_stage2_btn.click(
        load_artifact,
        inputs=[selected_run_id, gr.State("stage2")],
        outputs=stage2_output,
    )

    load_stage3_btn.click(
        load_artifact,
        inputs=[selected_run_id, gr.State("sql")],
        outputs=stage3_output,
    )
    
    # Format SQL
    def format_and_display_sql(run_id):
        artifact_path = service.storage.get_artifact_path(run_id, "query.sql")
        if not artifact_path or not os.path.exists(artifact_path):
            return "<p style='color: #888;'>No SQL available</p>"
        
        with open(artifact_path) as f:
            sql_content = f.read()
        
        if sql_content:
            return format_sql(sql_content)
        return "<p style='color: #888;'>No SQL available</p>"
    
    format_sql_btn.click(
        format_and_display_sql,
        inputs=selected_run_id,
        outputs=stage3_sql_formatted,
    )

    # Export buttons for main dashboard (no manual load button needed - auto-loads)
    export_csv_btn_main.click(
        lambda run_id: export_csv_handler(run_id),
        inputs=selected_run_id,
        outputs=stage4_csv_download_main,
    )
    
    export_json_btn_main.click(
        lambda run_id: export_json_handler(run_id),
        inputs=selected_run_id,
        outputs=stage4_json_download_main,
    )
    
    # Simple JSON loader for artifacts section
    load_stage4_btn.click(
        load_artifact,
        inputs=[selected_run_id, gr.State("analytics")],
        outputs=stage4_output,
    )

    # Auto-refresh runs list and run display ONLY (dashboard data untouched)
    refresh_timer.tick(
        lambda: get_runs_list(),
        outputs=runs_table,
    ).then(
        update_display_only,
        inputs=selected_run_id,
        outputs=[run_display, analytics_dashboard_accordion],
    )


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)

