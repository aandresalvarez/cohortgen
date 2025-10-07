"""
Service layer for cohort run management.

This module provides the core API for creating and managing cohort runs.
It can be used by Gradio UI, Slack bot, or any other interface.
"""

import json
import logging
import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Optional

from dotenv import load_dotenv

from projects.ui.models import (
    CohortRun,
    RunStatus,
    StageMetrics,
    StageResult,
    StageStatus,
    UserInputs,
)
from projects.ui.storage import RunStorage

# Save the REAL print function at module level to avoid nested log_print issues
import builtins as _builtins
_REAL_PRINT = _builtins.print

# Load environment variables from project root .env file
_project_root = Path(__file__).parent.parent.parent
_env_path = _project_root / ".env"
load_dotenv(dotenv_path=_env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread pool for background runs
_executor = ThreadPoolExecutor(max_workers=4)


class CohortService:
    """Service for managing cohort runs."""

    def __init__(self, storage: Optional[RunStorage] = None):
        """Initialize the service."""
        self.storage = storage or RunStorage()
        self._project_root = Path(__file__).parent.parent.parent
        self._setup_paths()

    def _setup_paths(self) -> None:
        """Add project paths for imports."""
        paths_to_add = [
            self._project_root / "projects" / "clar",
            self._project_root / "projects" / "cd",
            self._project_root / "projects" / "qb",
            self._project_root / "projects" / "stats",
        ]
        for path in paths_to_add:
            path_str = str(path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)

    def create_run(
        self,
        cohort_description: str,
        name: Optional[str] = None,
        fast_mode: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Create a new cohort run.

        Args:
            cohort_description: Plain text description of the cohort
            name: Optional display name for the run
            fast_mode: Whether to use fast mode (reduced quality for speed)
            **kwargs: Additional configuration (max_concept_sets, etc.)

        Returns:
            run_id: Unique identifier for the run
        """
        # Generate run_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(3).hex()
        run_id = f"{timestamp}_{random_suffix}"

        # Auto-generate name if not provided
        if not name:
            # Extract first few words from description
            words = cohort_description.split()[:3]
            name = " ".join(words)
            if len(cohort_description.split()) > 3:
                name += "..."

        # Apply fast mode defaults
        if fast_mode:
            kwargs.setdefault("max_concept_sets", 3)
            kwargs.setdefault("max_queries_per_set", 2)
            kwargs.setdefault("search_top_k", 5)
            kwargs.setdefault("per_set_time_limit_sec", 10)
            kwargs.setdefault("max_accepted_per_set", 3)

        # Create user inputs
        user_inputs = UserInputs(
            cohort_description=cohort_description,
            fast_mode=fast_mode,
            max_concept_sets=kwargs.get("max_concept_sets", 5),
            max_queries_per_set=kwargs.get("max_queries_per_set", 3),
            search_top_k=kwargs.get("search_top_k", 10),
            per_set_time_limit_sec=kwargs.get("per_set_time_limit_sec", 30),
            max_accepted_per_set=kwargs.get("max_accepted_per_set", 5),
            bigquery_project_id=kwargs.get("bigquery_project_id", ""),
            omop_dataset_id=kwargs.get("omop_dataset_id", ""),
            bigquery_location=kwargs.get("bigquery_location", "US"),
        )

        # Create run
        run = CohortRun(
            run_id=run_id,
            name=name,
            created_at=datetime.now().isoformat(),
            status=RunStatus.PENDING,
            user_inputs=user_inputs,
        )

        # Save run
        self.storage.save_run(run)

        logger.info(f"Created run {run_id}: {name}")
        return run_id

    def get_run(self, run_id: str) -> Optional[CohortRun]:
        """Get a run by ID."""
        return self.storage.load_run(run_id)

    def list_runs(self) -> list[dict[str, str]]:
        """List all runs."""
        return self.storage.list_runs()

    def delete_run(self, run_id: str) -> bool:
        """Delete a run."""
        logger.info(f"Deleting run {run_id}")
        return self.storage.delete_run(run_id)

    def start_run(
        self, run_id: str, stages: list[int] = [1, 2, 3, 4]
    ) -> None:
        """
        Start executing a run in the background.

        Args:
            run_id: The run to execute
            stages: Which stages to run (default: all 4)
        """
        logger.info(f"Starting run {run_id} with stages {stages}")

        # Submit to thread pool
        _executor.submit(self._execute_run, run_id, stages)

    def _execute_run(self, run_id: str, stages: list[int]) -> None:
        """
        Execute a run (runs in background thread).

        This is the main orchestration logic.
        """
        run = self.get_run(run_id)
        if not run:
            logger.error(f"Run {run_id} not found")
            return

        # Update status
        run.status = RunStatus.RUNNING
        self.storage.save_run(run)

        start_time = datetime.now()

        try:
            # Execute each stage
            for stage_num in stages:
                if stage_num == 1:
                    self._execute_stage1(run)
                elif stage_num == 2:
                    self._execute_stage2(run)
                elif stage_num == 3:
                    self._execute_stage3(run)
                elif stage_num == 4:
                    self._execute_stage4(run)

                # Check if any stage failed
                if run.status == RunStatus.FAILED:
                    break

            # Mark as succeeded if all stages passed
            if run.status == RunStatus.RUNNING:
                run.status = RunStatus.SUCCEEDED

        except Exception as e:
            logger.error(f"Run {run_id} failed: {e}")
            run.status = RunStatus.FAILED
            run.error = f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"

        finally:
            # Calculate total duration
            end_time = datetime.now()
            run.total_duration_seconds = (end_time - start_time).total_seconds()

            # Save final state
            self.storage.save_run(run)

            logger.info(
                f"Run {run_id} finished with status {run.status.value} "
                f"in {run.total_duration_seconds:.1f}s"
            )

    def _execute_stage1(self, run: CohortRun) -> None:
        """Execute Stage 1: Clinical Clarification."""
        logger.info(f"[{run.run_id}] Starting Stage 1: Clinical Clarification")

        stage_result = StageResult(
            stage=1,
            status=StageStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        run.stages.append(stage_result)
        self.storage.save_run(run)

        start_time = datetime.now()

        try:
            # Reload environment variables in this thread (thread-safe)
            load_dotenv(dotenv_path=_env_path, override=True)
            
            # Ensure environment variables are loaded before importing
            # (some modules initialize agents at import time)
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error(f"[{run.run_id}] OPENAI_API_KEY not found in environment")
                logger.error(f"[{run.run_id}] .env path: {_env_path}")
                logger.error(f"[{run.run_id}] .env exists: {_env_path.exists()}")
                raise ValueError(
                    "OPENAI_API_KEY not found in environment. "
                    "Please ensure .env file exists in project root with OPENAI_API_KEY set."
                )
            
            logger.info(f"[{run.run_id}] Environment loaded, API key present: {api_key[:10]}...")
            
            # Set up log file for capturing Stage 1 conversation
            stage1_log_path = self.storage.get_artifact_path(run.run_id, "stage1_log.txt")
            
            # Import stage 1 module
            from hitl_clarification_working import run_clarification_loop
            import builtins
            
            # Conversation log buffer
            conversation_log = []
            
            # Create a custom print function that logs to file
            # Use the REAL print function saved at module level to avoid nesting
            def log_print(*args, **kwargs):
                """Custom print that captures output and saves to log file."""
                # Convert args to string
                message = " ".join(str(arg) for arg in args)
                conversation_log.append(message)
                
                # Write to log file
                with open(stage1_log_path, "a") as f:
                    f.write(message + "\n")
                
                # Also print to original output
                _REAL_PRINT(*args, **kwargs)
            
            # Mock input() for non-interactive mode
            # Returns empty string to auto-proceed with agent's best guess
            def mock_input(prompt=""):
                """Mock input that auto-responds and logs the interaction."""
                log_print(f"👤 You: [auto-proceeding with defaults]")
                return ""  # Empty response = proceed with defaults
            
            # Save current builtins before replacing
            original_print = builtins.print
            original_input = builtins.input
            
            try:
                # Replace print and input
                builtins.print = log_print
                builtins.input = mock_input
                
                # Log start
                log_print("=" * 70)
                log_print(f"Stage 1: Clinical Clarification")
                log_print(f"Run ID: {run.run_id}")
                log_print(f"Input: {run.user_inputs.cohort_description}")
                log_print("=" * 70)
                log_print("")
                
                # Run clarification with limited questions for non-interactive mode
                cohort_def = run_clarification_loop(
                    run.user_inputs.cohort_description,
                    max_questions=3 if run.user_inputs.fast_mode else 5
                )
                
                log_print("")
                log_print("=" * 70)
                log_print("Stage 1 Complete")
                log_print("=" * 70)
                
            finally:
                # Restore original functions
                builtins.print = original_print
                builtins.input = original_input

            # Format output
            output = {
                "index_event": cohort_def.index_event,
                "demographics": cohort_def.demographics,
                "inclusion_criteria": cohort_def.inclusion_criteria,
                "exclusion_criteria": cohort_def.exclusion_criteria,
                "observation_window": cohort_def.observation_window,
                "prior_observation": cohort_def.prior_observation,
                "cohort_exit": cohort_def.cohort_exit,
            }

            # Save artifact
            artifact_path = self.storage.save_artifact(
                run.run_id, "stage1.json", json.dumps(output, indent=2)
            )
            run.stage1_path = artifact_path
            run.stage1_log_path = stage1_log_path

            # Update stage result
            stage_result.status = StageStatus.COMPLETE
            stage_result.completed_at = datetime.now().isoformat()
            stage_result.artifact_path = artifact_path
            stage_result.metrics.duration_seconds = (
                datetime.now() - start_time
            ).total_seconds()

            logger.info(
                f"[{run.run_id}] Stage 1 complete in "
                f"{stage_result.metrics.duration_seconds:.1f}s"
            )

        except Exception as e:
            logger.error(f"[{run.run_id}] Stage 1 failed: {e}")
            stage_result.status = StageStatus.FAILED
            stage_result.metrics.error_message = str(e)
            run.status = RunStatus.FAILED
            run.error = traceback.format_exc()

        finally:
            self.storage.save_run(run)

    def _execute_stage2(self, run: CohortRun) -> None:
        """Execute Stage 2: Concept Discovery."""
        logger.info(f"[{run.run_id}] Starting Stage 2: Concept Discovery")

        stage_result = StageResult(
            stage=2,
            status=StageStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        run.stages.append(stage_result)
        self.storage.save_run(run)

        start_time = datetime.now()

        try:
            # Reload environment variables
            load_dotenv(dotenv_path=_env_path, override=True)
            
            # Load stage 1 output
            if not run.stage1_path:
                raise ValueError("Stage 1 output not found")

            stage1_output = json.loads(
                self.storage.load_artifact(run.run_id, "stage1.json") or "{}"
            )

            # Format for stage 2
            formatted_text = self._format_cohort_for_stage2(stage1_output)

            # Set environment variables for knobs
            os.environ["MAX_CONCEPT_SETS"] = str(
                run.user_inputs.max_concept_sets
            )
            os.environ["MAX_QUERIES_PER_SET"] = str(
                run.user_inputs.max_queries_per_set
            )
            os.environ["SEARCH_TOP_K"] = str(run.user_inputs.search_top_k)
            os.environ["PER_SET_TIME_LIMIT_SEC"] = str(
                run.user_inputs.per_set_time_limit_sec
            )
            os.environ["MAX_ACCEPTED_PER_SET"] = str(
                run.user_inputs.max_accepted_per_set
            )

            # Save current sys.path and temporarily prioritize cd directory
            original_path = sys.path.copy()
            cd_path = str(self._project_root / "projects" / "cd")
            
            # Insert cd path at the beginning to ensure its tools.py is found first
            if cd_path in sys.path:
                sys.path.remove(cd_path)
            sys.path.insert(0, cd_path)
            
            # Set up log file for Stage 2
            stage2_log_path = self.storage.get_artifact_path(run.run_id, "stage2_log.txt")
            
            try:
                # Import Stage 2 modules
                import builtins
                from find_concepts import run_concept_discovery
                
                # Set up logging to capture concept discovery progress
                # Use the REAL print function saved at module level
                def log_print(*args, **kwargs):
                    message = " ".join(str(arg) for arg in args)
                    with open(stage2_log_path, "a") as f:
                        f.write(message + "\n")
                        f.flush()  # Flush immediately for real-time log updates
                    _REAL_PRINT(*args, **kwargs)
                
                original_print = builtins.print
                
                try:
                    builtins.print = log_print
                    
                    log_print("=" * 70)
                    log_print("Stage 2: Concept Discovery")
                    log_print(f"Run ID: {run.run_id}")
                    log_print("=" * 70)
                    log_print("")
                    
                    concept_sets = run_concept_discovery(formatted_text)
                    
                    log_print("")
                    log_print("=" * 70)
                    log_print("Stage 2 Complete")
                    log_print("=" * 70)
                finally:
                    builtins.print = original_print
            finally:
                # Restore original sys.path and clear module cache
                sys.path[:] = original_path
                
                # Clear imported modules from this stage to prevent conflicts
                modules_to_clear = [
                    mod for mod in sys.modules.keys()
                    if mod.startswith('tools') or mod == 'find_concepts'
                ]
                for mod in modules_to_clear:
                    del sys.modules[mod]

            # Save artifact
            artifact_path = self.storage.save_artifact(
                run.run_id, "stage2.json", json.dumps(concept_sets, indent=2)
            )
            run.stage2_path = artifact_path
            run.stage2_log_path = stage2_log_path

            # Update metrics
            stage_result.status = StageStatus.COMPLETE
            stage_result.completed_at = datetime.now().isoformat()
            stage_result.artifact_path = artifact_path
            stage_result.metrics.duration_seconds = (
                datetime.now() - start_time
            ).total_seconds()
            stage_result.metrics.concepts_found = sum(
                len(cs.get("included_concepts", []))
                for cs in concept_sets.get("concept_sets", [])
            )

            logger.info(
                f"[{run.run_id}] Stage 2 complete in "
                f"{stage_result.metrics.duration_seconds:.1f}s"
            )

        except Exception as e:
            logger.error(f"[{run.run_id}] Stage 2 failed: {e}")
            stage_result.status = StageStatus.FAILED
            stage_result.metrics.error_message = str(e)
            run.status = RunStatus.FAILED
            run.error = traceback.format_exc()

        finally:
            self.storage.save_run(run)

    def _execute_stage3(self, run: CohortRun) -> None:
        """Execute Stage 3: BigQuery SQL Generation."""
        logger.info(f"[{run.run_id}] Starting Stage 3: SQL Generation")

        stage_result = StageResult(
            stage=3,
            status=StageStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        run.stages.append(stage_result)
        self.storage.save_run(run)

        start_time = datetime.now()

        try:
            # Reload environment variables
            load_dotenv(dotenv_path=_env_path, override=True)
            
            # Load stage 1 and 2 outputs
            if not run.stage1_path or not run.stage2_path:
                raise ValueError("Stage 1 or 2 output not found")

            stage1_output = json.loads(
                self.storage.load_artifact(run.run_id, "stage1.json") or "{}"
            )
            stage2_output = json.loads(
                self.storage.load_artifact(run.run_id, "stage2.json") or "{}"
            )

            # Combine for stage 3
            complete_output = {
                "clinical_definition": stage1_output,
                "concept_sets": stage2_output.get("concept_sets", []),
            }

            # Save temporary complete output for stage 3
            temp_path = self.storage.save_artifact(
                run.run_id,
                "complete_cohort_output.json",
                json.dumps(complete_output, indent=2),
            )

            # Save current sys.path and temporarily prioritize qb directory
            original_path = sys.path.copy()
            qb_path = str(self._project_root / "projects" / "qb")
            
            # Clear any cached tools module from previous stages
            modules_to_clear = []
            for mod in list(sys.modules.keys()):
                if 'tools' in mod:
                    modules_to_clear.append(mod)
            for mod in modules_to_clear:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            # Insert qb path at the beginning
            if qb_path in sys.path:
                sys.path.remove(qb_path)
            sys.path.insert(0, qb_path)
            
            # Set up log file for Stage 3
            stage3_log_path = self.storage.get_artifact_path(run.run_id, "stage3_log.txt")
            
            try:
                # Import Stage 3 modules
                import json as json_lib
                import builtins
                from create_bigquery_sql import run_bigquery_sql_generation, CohortInput
                
                # Set up logging
                # Use the REAL print function saved at module level
                def log_print(*args, **kwargs):
                    message = " ".join(str(arg) for arg in args)
                    with open(stage3_log_path, "a") as f:
                        f.write(message + "\n")
                        f.flush()  # Flush immediately for real-time log updates
                    _REAL_PRINT(*args, **kwargs)
                
                original_print = builtins.print
                
                try:
                    builtins.print = log_print
                    
                    # Load the complete output
                    with open(temp_path) as f:
                        complete_data = json_lib.load(f)
                    
                    # Create CohortInput object
                    cohort_input = CohortInput(**complete_data)
                    
                    # Configure OMOP dataset
                    omop_dataset = run.user_inputs.omop_dataset_id or os.getenv("OMOP_DATASET_ID", "bigquery-public-data.cms_synthetic_patient_data_omop")
                    project_id = run.user_inputs.bigquery_project_id or os.getenv("BIGQUERY_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
                    location = run.user_inputs.bigquery_location or "US"
                    
                    log_print(f"BigQuery Configuration:")
                    log_print(f"  Project: {project_id}")
                    log_print(f"  Dataset: {omop_dataset}")
                    log_print(f"  Location: {location}")
                    log_print("")
                    
                    sql_result = run_bigquery_sql_generation(
                        cohort_input,
                        omop_dataset=omop_dataset,
                        project_id=project_id,
                        location=location
                    )
                    
                    # Convert to dict for storage
                    sql_output = {
                        "sql": sql_result.sql,
                        "is_valid": sql_result.is_valid,
                        "errors": sql_result.errors,
                        "estimated_cost_usd": sql_result.estimated_cost_usd,
                        "total_bytes_processed": sql_result.total_bytes_processed,
                        "summary": sql_result.summary,
                    }
                finally:
                    builtins.print = original_print
            finally:
                # Restore original sys.path and clear module cache
                sys.path[:] = original_path
                
                # Clear imported modules from this stage
                modules_to_clear = [
                    mod for mod in sys.modules.keys()
                    if mod.startswith('tools') or mod == 'create_bigquery_sql'
                ]
                for mod in modules_to_clear:
                    del sys.modules[mod]

            # Save SQL artifact
            sql_path = self.storage.save_artifact(
                run.run_id, "query.sql", sql_output.get("sql", "")
            )
            run.stage3_sql_path = sql_path
            run.stage3_log_path = stage3_log_path

            # Save validation artifact (sql_output already contains all validation info)
            validation_path = self.storage.save_artifact(
                run.run_id,
                "sql_validation.json",
                json.dumps(sql_output, indent=2),
            )
            run.stage3_validation_path = validation_path

            # Update metrics
            stage_result.status = StageStatus.COMPLETE
            stage_result.completed_at = datetime.now().isoformat()
            stage_result.artifact_path = sql_path
            stage_result.metrics.duration_seconds = (
                datetime.now() - start_time
            ).total_seconds()

            logger.info(
                f"[{run.run_id}] Stage 3 complete in "
                f"{stage_result.metrics.duration_seconds:.1f}s"
            )

        except Exception as e:
            logger.error(f"[{run.run_id}] Stage 3 failed: {e}")
            stage_result.status = StageStatus.FAILED
            stage_result.metrics.error_message = str(e)
            run.status = RunStatus.FAILED
            run.error = traceback.format_exc()

        finally:
            self.storage.save_run(run)

    def _execute_stage4(self, run: CohortRun) -> None:
        """Execute Stage 4: Analytics."""
        logger.info(f"[{run.run_id}] Starting Stage 4: Analytics")

        stage_result = StageResult(
            stage=4,
            status=StageStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        run.stages.append(stage_result)
        self.storage.save_run(run)

        start_time = datetime.now()

        try:
            # Reload environment variables
            load_dotenv(dotenv_path=_env_path, override=True)
            
            # Load stage 3 SQL
            if not run.stage3_sql_path:
                raise ValueError("Stage 3 SQL not found")

            sql_content = self.storage.load_artifact(run.run_id, "query.sql")
            if not sql_content:
                raise ValueError("SQL content is empty")

            # Save current sys.path and temporarily prioritize stats directory
            original_path = sys.path.copy()
            stats_path = str(self._project_root / "projects" / "stats")
            
            # Clear any cached modules from previous stages
            modules_to_clear = [
                mod for mod in list(sys.modules.keys())
                if 'tools' in mod
            ]
            for mod in modules_to_clear:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            # Insert stats path at the beginning
            if stats_path in sys.path:
                sys.path.remove(stats_path)
            sys.path.insert(0, stats_path)
            
            try:
                # Import Stage 4 modules
                import builtins
                from run_stats import build_analytics_queries, load_files, extract_concept_ids
                from google.cloud import bigquery
                
                # Set up logging
                # Use the REAL print function saved at module level
                stage4_log_path = self.storage.get_artifact_path(run.run_id, "stage4_log.txt")
                
                def log_print(*args, **kwargs):
                    message = " ".join(str(arg) for arg in args)
                    with open(stage4_log_path, "a") as f:
                        f.write(message + "\n")
                    _REAL_PRINT(*args, **kwargs)
                
                original_print = builtins.print
                
                try:
                    builtins.print = log_print
                    
                    log_print("=" * 70)
                    log_print("Stage 4: Analytics")
                    log_print(f"Run ID: {run.run_id}")
                    log_print("=" * 70)
                    log_print("")
                    
                    # Get BigQuery configuration
                    project_id = run.user_inputs.bigquery_project_id or os.getenv("BIGQUERY_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
                    dataset = run.user_inputs.omop_dataset_id or os.getenv("OMOP_DATASET_ID", "bigquery-public-data.cms_synthetic_patient_data_omop")
                    location = run.user_inputs.bigquery_location or "US"
                    
                    if not project_id:
                        log_print("⚠️  No BigQuery project configured")
                        log_print("   Set GOOGLE_CLOUD_PROJECT in .env or configure in UI")
                        analytics_output = {
                            "status": "skipped",
                            "message": "BigQuery project not configured"
                        }
                    else:
                        log_print(f"BigQuery Configuration:")
                        log_print(f"  Project: {project_id}")
                        log_print(f"  Dataset: {dataset}")
                        log_print(f"  Location: {location}")
                        log_print("")
                        
                        # Load cohort input data
                        import json
                        with open(run.stage2_path) as f:
                            input_data = json.load(f)
                        
                        # Extract ESRD concept IDs for index-date derivation
                        esrd_ids = extract_concept_ids(input_data, ["end-stage renal disease", "esrd"]) or []
                        if esrd_ids:
                            log_print(f"Found ESRD concept IDs for index derivation: {esrd_ids}")
                        else:
                            log_print("No ESRD concept IDs found; age/index-year analytics will be skipped")
                        log_print("")
                        
                        # Build analytics queries
                        log_print("Building analytics queries...")
                        
                        # Remove trailing semicolon from SQL if present (breaks CTE wrapping)
                        sql_for_analytics = sql_content.strip()
                        if sql_for_analytics.endswith(';'):
                            sql_for_analytics = sql_for_analytics[:-1]
                            log_print("  ✓ Removed trailing semicolon from SQL")
                        
                        queries = build_analytics_queries(sql_for_analytics, project_id, dataset, esrd_ids)
                        log_print(f"  ✓ Built {len(queries)} analytics queries")
                        log_print("")
                        
                        # Run queries
                        client = bigquery.Client(project=project_id, location=location)
                        results = {}
                        
                        for name, sql in queries.items():
                            log_print(f"[Run] {name}...")
                            try:
                                job = client.query(sql)
                                rows = list(job.result())
                                items = [{k: r[k] for k in r.keys()} for r in rows]
                                results[name] = items
                                log_print(f"  ✓ {len(items)} rows")
                            except Exception as query_error:
                                log_print(f"  ✗ Error: {str(query_error)}")
                                results[name] = {"error": str(query_error)}
                        
                        analytics_output = {
                            "status": "complete",
                            "project_id": project_id,
                            "dataset": dataset,
                            "results": results
                        }
                        
                        log_print("")
                        log_print("=" * 70)
                        log_print("✅ Analytics Complete")
                        log_print("=" * 70)
                    
                finally:
                    builtins.print = original_print
            finally:
                # Restore original sys.path and clear module cache
                sys.path[:] = original_path
                
                # Clear imported modules from this stage
                modules_to_clear = [
                    mod for mod in sys.modules.keys()
                    if mod == 'run_stats'
                ]
                for mod in modules_to_clear:
                    del sys.modules[mod]

            # Save artifact
            artifact_path = self.storage.save_artifact(
                run.run_id,
                "analytics.json",
                json.dumps(analytics_output, indent=2),
            )
            run.stage4_path = artifact_path

            # Update metrics
            stage_result.status = StageStatus.COMPLETE
            stage_result.completed_at = datetime.now().isoformat()
            stage_result.artifact_path = artifact_path
            stage_result.metrics.duration_seconds = (
                datetime.now() - start_time
            ).total_seconds()

            logger.info(
                f"[{run.run_id}] Stage 4 complete in "
                f"{stage_result.metrics.duration_seconds:.1f}s"
            )

        except Exception as e:
            logger.error(f"[{run.run_id}] Stage 4 failed: {e}")
            stage_result.status = StageStatus.FAILED
            stage_result.metrics.error_message = str(e)
            run.status = RunStatus.FAILED
            run.error = traceback.format_exc()

        finally:
            self.storage.save_run(run)

    def _format_cohort_for_stage2(self, stage1_output: dict[str, Any]) -> str:
        """Format stage 1 output for stage 2 input."""
        parts = []

        if stage1_output.get("index_event"):
            parts.append(f"Index Event: {stage1_output['index_event']}")

        if stage1_output.get("demographics"):
            demo_str = ", ".join(
                f"{k}: {v}" for k, v in stage1_output["demographics"].items()
            )
            parts.append(f"Demographics: {demo_str}")

        if stage1_output.get("inclusion_criteria"):
            parts.append(
                f"Inclusion Criteria: {', '.join(stage1_output['inclusion_criteria'])}"
            )

        if stage1_output.get("exclusion_criteria"):
            parts.append(
                f"Exclusion Criteria: {', '.join(stage1_output['exclusion_criteria'])}"
            )

        if stage1_output.get("observation_window"):
            parts.append(
                f"Observation Window: {stage1_output['observation_window']}"
            )

        if stage1_output.get("prior_observation"):
            parts.append(
                f"Prior Observation: {stage1_output['prior_observation']}"
            )

        if stage1_output.get("cohort_exit"):
            parts.append(f"Cohort Exit: {stage1_output['cohort_exit']}")

        return "\n".join(parts) if parts else "No cohort definition provided"

    def duplicate_run(self, run_id: str, new_name: Optional[str] = None) -> str:
        """
        Duplicate a run with the same inputs.

        Args:
            run_id: The run to duplicate
            new_name: Optional new name (default: "Copy of {original}")

        Returns:
            new_run_id: The ID of the new run
        """
        original = self.get_run(run_id)
        if not original:
            raise ValueError(f"Run {run_id} not found")

        # Create new run with same inputs
        new_name = new_name or f"Copy of {original.name}"
        return self.create_run(
            cohort_description=original.user_inputs.cohort_description,
            name=new_name,
            fast_mode=original.user_inputs.fast_mode,
            max_concept_sets=original.user_inputs.max_concept_sets,
            max_queries_per_set=original.user_inputs.max_queries_per_set,
            search_top_k=original.user_inputs.search_top_k,
            per_set_time_limit_sec=original.user_inputs.per_set_time_limit_sec,
            max_accepted_per_set=original.user_inputs.max_accepted_per_set,
            bigquery_project_id=original.user_inputs.bigquery_project_id,
            omop_dataset_id=original.user_inputs.omop_dataset_id,
            bigquery_location=original.user_inputs.bigquery_location,
        )
    
    # Interactive Clarification Methods
    _clarification_sessions: dict[str, Any] = {}  # Store active sessions
    
    def start_interactive_clarification(self, run_id: str) -> tuple[str, bool]:
        """
        Start an interactive clarification session for Stage 1.
        
        Args:
            run_id: The run ID
            
        Returns:
            Tuple of (first_question, is_complete)
        """
        from projects.ui.interactive_clarification import InteractiveClarificationSession
        from projects.ui.models import ClarificationSession, StageStatus
        
        run = self.get_run(run_id)
        if not run:
            return "Error: Run not found", True
        
        # Create interactive session
        session = InteractiveClarificationSession(
            run_id=run_id,
            initial_description=run.user_inputs.cohort_description
        )
        
        # Store in memory
        self._clarification_sessions[run_id] = session
        
        # Update run status
        run.status = RunStatus.RUNNING
        
        # Create/update Stage 1
        if not run.stages or run.stages[0].stage != 1:
            stage_result = StageResult(
                stage=1,
                status=StageStatus.WAITING_FOR_INPUT,
                started_at=datetime.now().isoformat(),
            )
            run.stages.insert(0, stage_result)
        else:
            run.stages[0].status = StageStatus.WAITING_FOR_INPUT
        
        # Save session state to run
        run.clarification_session = ClarificationSession(
            run_id=run_id,
            conversation_history=session.get_conversation_history(),
            is_complete=session.is_complete,
            cohort_definition=session.cohort_definition,
        )
        
        self.storage.save_run(run)
        
        # Get first question
        history = session.get_conversation_history()
        if history:
            first_question = history[-1]["content"]
            return first_question, False
        
        return "Ready to start clarification", False
    
    def send_clarification_message(self, run_id: str, message: str) -> tuple[Optional[str], bool, Optional[dict]]:
        """
        Send a message in the clarification chat and get response.
        
        Args:
            run_id: The run ID
            message: User's message/answer
            
        Returns:
            Tuple of (next_question, is_complete, cohort_definition)
        """
        from projects.ui.models import ClarificationSession
        from projects.ui.interactive_clarification import InteractiveClarificationSession
        
        # Get session (or restore from saved state)
        session = self._clarification_sessions.get(run_id)
        if not session:
            # Try to restore from saved run state
            run = self.get_run(run_id)
            if run and run.clarification_session and not run.clarification_session.is_complete:
                # Recreate session from saved state
                session = InteractiveClarificationSession(
                    run_id=run_id,
                    initial_description=run.user_inputs.cohort_description
                )
                # Restore conversation history
                session.conversation_history = run.clarification_session.conversation_history.copy()
                session.is_complete = run.clarification_session.is_complete
                session.cohort_definition = run.clarification_session.cohort_definition
                session.question_count = len([msg for msg in session.conversation_history if msg["role"] == "assistant"])
                
                # Store in memory
                self._clarification_sessions[run_id] = session
            else:
                return "Error: Session not found. Please start clarification first.", False, None
        
        # Send message
        next_question, is_complete, cohort_def = session.send_message(message)
        
        # Update run
        run = self.get_run(run_id)
        if run:
            run.clarification_session = ClarificationSession(
                run_id=run_id,
                conversation_history=session.get_conversation_history(),
                is_complete=is_complete,
                cohort_definition=cohort_def,
            )
            
            if is_complete:
                # Mark Stage 1 as complete
                if run.stages and run.stages[0].stage == 1:
                    run.stages[0].status = StageStatus.COMPLETE
                    run.stages[0].completed_at = datetime.now().isoformat()
                    
                    # Save cohort definition as artifact
                    if cohort_def:
                        artifact_path = self.storage.save_artifact(
                            run_id, "stage1.json", json.dumps(cohort_def, indent=2)
                        )
                        run.stage1_path = artifact_path
                        run.stages[0].artifact_path = artifact_path
            
            self.storage.save_run(run)
        
        return next_question, is_complete, cohort_def
    
    def get_clarification_state(self, run_id: str) -> Optional[dict]:
        """
        Get the current clarification session state.
        
        Args:
            run_id: The run ID
            
        Returns:
            Session state dict or None
        """
        session = self._clarification_sessions.get(run_id)
        if session:
            return session.get_state()
        
        # Check if saved in run
        run = self.get_run(run_id)
        if run and run.clarification_session:
            from dataclasses import asdict
            return asdict(run.clarification_session)
        
        return None

