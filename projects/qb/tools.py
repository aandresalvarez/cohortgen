"""
Pydantic AI tools for BigQuery SQL validation.
Uses google-cloud-bigquery directly for dry run validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Import BigQuery and secrets management
try:
    from google.api_core import exceptions as google_exceptions
    from google.cloud import bigquery

    BIGQUERY_AVAILABLE = True
except ImportError:
    bigquery = None  # type: ignore
    google_exceptions = None  # type: ignore
    BIGQUERY_AVAILABLE = False

# Import secrets management (typed import via package path)
try:
    from projects.shared.secrets import get_secret, setup_bigquery_auth  # type: ignore

    SECRETS_AVAILABLE = True
except Exception:
    setup_bigquery_auth = None  # type: ignore
    get_secret = None  # type: ignore
    SECRETS_AVAILABLE = False

# Optional shim used by tests for monkeypatching
try:  # pragma: no cover
    import bq_tools as _bq_tools  # type: ignore
except Exception:  # pragma: no cover
    _bq_tools = None  # type: ignore


class DryRunInput(BaseModel):
    """Input for BigQuery dry run validation."""

    sql: str = Field(..., description="The BigQuery SQL query to validate.")
    project_id: Optional[str] = Field(None, description="GCP project ID (optional).")
    default_dataset: Optional[str] = Field(
        None, description="Default dataset for unqualified table names."
    )
    location: Optional[str] = Field("US", description="BigQuery location/region.")
    credentials_path: Optional[str] = Field(
        None, description="Path to GCP service account JSON (optional)."
    )


class DryRunResult(BaseModel):
    """Result from BigQuery dry run."""

    success: bool = Field(..., description="Whether the SQL is valid.")
    errors: List[str] = Field(
        default_factory=list, description="List of error messages if validation failed."
    )
    total_bytes_processed: int = Field(0, description="Estimated bytes to be processed.")
    estimated_cost_usd: Optional[float] = Field(None, description="Estimated query cost in USD.")
    summary: Optional[str] = Field(
        None, description="Human-readable summary of the validation result."
    )
    job_id: Optional[str] = Field(None, description="BigQuery job ID.")
    statistics: Optional[Dict[str, Any]] = Field(None, description="Raw BigQuery statistics.")


def validate_bigquery_sql(input: DryRunInput) -> DryRunResult:
    """
    Validate BigQuery SQL using dry run.

    This checks SQL syntax and estimates query cost without executing the query.
    """
    # Empty SQL handling per tests
    if not input.sql or not str(input.sql).strip():
        return DryRunResult(
            success=False,
            errors=["Empty SQL"],
            total_bytes_processed=0,
            estimated_cost_usd=None,
            summary="❌ Validation error: Empty SQL",
            job_id=None,
            statistics=None,
        )

    # Library availability (or shim). Import shim lazily so tests that
    # add it to sys.path after importing this module still work.
    bq_shim = _bq_tools
    if bq_shim is None:  # try lazy import
        try:  # pragma: no cover
            import bq_tools as bq_shim  # type: ignore
        except Exception:
            bq_shim = None  # type: ignore
    use_shim = bq_shim is not None and hasattr(bq_shim, "_ensure_client")
    if not BIGQUERY_AVAILABLE and not use_shim:
        return DryRunResult(
            success=False,
            errors=[
                "google-cloud-bigquery library not available. Install with: pip install google-cloud-bigquery"
            ],
            total_bytes_processed=0,
            estimated_cost_usd=None,
            summary="❌ Validation error: Missing google-cloud-bigquery",
            job_id=None,
            statistics=None,
        )

    try:
        # Set up authentication if available
        if SECRETS_AVAILABLE and setup_bigquery_auth is not None:
            setup_bigquery_auth()

        # Get project ID
        project_id = input.project_id
        if not project_id and SECRETS_AVAILABLE and get_secret is not None:
            project_id = get_secret("GOOGLE_CLOUD_PROJECT", required=False)
        # Fallback: detect from ADC if still not set (only when not using shim)
        if not project_id and not use_shim:
            try:
                from google.auth import default as google_auth_default

                credentials, detected_project = google_auth_default()
                if detected_project:
                    project_id = detected_project
            except Exception:
                pass

        # Create BigQuery client (via shim if available so tests can inject fakes)
        if use_shim:
            client = bq_shim._ensure_client(project_id=project_id, credentials_path=input.credentials_path)  # type: ignore[attr-defined]
            BQ = getattr(bq_shim, "bigquery", None)
            if BQ is None:  # pragma: no cover
                raise RuntimeError("Shim bigquery module not available")
        else:
            if not project_id:
                return DryRunResult(
                    success=False,
                    errors=[
                        "No GCP project ID provided. Set GOOGLE_CLOUD_PROJECT or pass project_id parameter."
                    ],
                    total_bytes_processed=0,
                    estimated_cost_usd=None,
                    summary="❌ Validation error: Missing project id",
                    job_id=None,
                    statistics=None,
                )
            client = bigquery.Client(project=project_id, location=input.location)
            BQ = bigquery

        # Configure job
        job_config = BQ.QueryJobConfig(dry_run=True, use_query_cache=False)

        if input.default_dataset:
            job_config.default_dataset = input.default_dataset

        # Run dry run
        query_job = client.query(input.sql, job_config=job_config, location=input.location)

        # Extract statistics
        total_bytes = query_job.total_bytes_processed or 0

        # Estimate cost using on-demand pricing $5 per TB
        if total_bytes > 0:
            tb_processed = total_bytes / (1024**4)  # Convert bytes to TB
            estimated_cost = tb_processed * 5.0
        else:
            estimated_cost = 0.0

        # Build summary
        if total_bytes > 0:
            if total_bytes < 1024:
                size_str = f"{total_bytes} bytes"
            elif total_bytes < 1024**2:
                size_str = f"{total_bytes / 1024:.2f} KB"
            elif total_bytes < 1024**3:
                size_str = f"{total_bytes / (1024 ** 2):.2f} MB"
            elif total_bytes < 1024**4:
                size_str = f"{total_bytes / (1024 ** 3):.2f} GB"
            else:
                size_str = f"{total_bytes / (1024 ** 4):.4f} TB"

            summary = f"✅ SQL is valid. Estimated to process {size_str}"
            if estimated_cost:
                summary += f" (≈${estimated_cost:.4f})"
        else:
            summary = "✅ SQL is valid (no data to process)"

        return DryRunResult(
            success=True,
            errors=[],
            total_bytes_processed=total_bytes,
            estimated_cost_usd=estimated_cost,
            summary=summary,
            job_id=query_job.job_id if hasattr(query_job, "job_id") else None,
            statistics={
                "total_bytes_processed": total_bytes,
                "total_bytes_billed": total_bytes,  # Dry run doesn't bill
            },
        )

    except Exception as e:
        # Tests may inject a BadRequest via shim
        BadReq = getattr(bq_shim, "BadRequest", None) if bq_shim else None
        if BadReq and isinstance(e, BadReq):
            # Prefer detailed messages from e.errors if available
            messages: List[str] = []
            try:
                errs = getattr(e, "errors", None)
                if isinstance(errs, list) and errs:
                    for item in errs:
                        if isinstance(item, dict) and "message" in item:
                            messages.append(str(item["message"]))
                        else:
                            messages.append(str(item))
            except Exception:
                pass
            if not messages:
                messages = [str(e)]
            primary = messages[0]
            return DryRunResult(
                success=False,
                errors=messages,
                total_bytes_processed=0,
                estimated_cost_usd=None,
                summary=f"❌ SQL validation failed: {primary}",
                job_id=None,
                statistics=None,
            )
        # Real Google API error
        if google_exceptions is not None and isinstance(e, google_exceptions.GoogleAPIError):
            error_msg = getattr(e, "message", str(e))
            return DryRunResult(
                success=False,
                errors=[f"BigQuery API error: {error_msg}"],
                total_bytes_processed=0,
                estimated_cost_usd=None,
                summary=f"❌ SQL validation failed: {error_msg}",
                job_id=None,
                statistics=None,
            )
        # Other errors (auth, network, etc.)
        error_msg = str(e)

        # Check for common auth errors
        if "credentials" in error_msg.lower() or "authenticate" in error_msg.lower():
            error_msg = (
                f"{error_msg}. "
                "Run 'gcloud auth application-default login' or set GOOGLE_APPLICATION_CREDENTIALS"
            )

        return DryRunResult(
            success=False,
            errors=[error_msg],
            total_bytes_processed=0,
            estimated_cost_usd=None,
            summary=f"❌ Validation error: {error_msg}",
            job_id=None,
            statistics=None,
        )
