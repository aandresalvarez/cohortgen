"""
Pydantic AI tools for BigQuery SQL validation.
Uses google-cloud-bigquery directly for dry run validation.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import os

# Import BigQuery and secrets management
try:
    from google.cloud import bigquery
    from google.api_core import exceptions as google_exceptions
    BIGQUERY_AVAILABLE = True
except ImportError:
    bigquery = None  # type: ignore
    google_exceptions = None  # type: ignore
    BIGQUERY_AVAILABLE = False

# Try to import secrets management
try:
    import sys
    from pathlib import Path
    # Add shared to path
    shared_path = Path(__file__).parent.parent / "shared"
    if str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))
    from secrets import setup_bigquery_auth, get_secret
    SECRETS_AVAILABLE = True
except ImportError:
    setup_bigquery_auth = None  # type: ignore
    get_secret = None  # type: ignore
    SECRETS_AVAILABLE = False


class DryRunInput(BaseModel):
    """Input for BigQuery dry run validation."""
    sql: str = Field(..., description="The BigQuery SQL query to validate.")
    project_id: Optional[str] = Field(None, description="GCP project ID (optional).")
    default_dataset: Optional[str] = Field(None, description="Default dataset for unqualified table names.")
    location: Optional[str] = Field("US", description="BigQuery location/region.")
    credentials_path: Optional[str] = Field(None, description="Path to GCP service account JSON (optional).")


class DryRunResult(BaseModel):
    """Result from BigQuery dry run."""
    success: bool = Field(..., description="Whether the SQL is valid.")
    errors: List[str] = Field(default_factory=list, description="List of error messages if validation failed.")
    total_bytes_processed: int = Field(0, description="Estimated bytes to be processed.")
    estimated_cost_usd: Optional[float] = Field(None, description="Estimated query cost in USD.")
    summary: Optional[str] = Field(None, description="Human-readable summary of the validation result.")
    job_id: Optional[str] = Field(None, description="BigQuery job ID.")
    statistics: Optional[Dict[str, Any]] = Field(None, description="Raw BigQuery statistics.")


def validate_bigquery_sql(input: DryRunInput) -> DryRunResult:
    """
    Validate BigQuery SQL using dry run.
    
    This checks SQL syntax and estimates query cost without executing the query.
    """
    if not BIGQUERY_AVAILABLE:
        return DryRunResult(
            success=False,
            errors=["google-cloud-bigquery library not available. Install with: pip install google-cloud-bigquery"]
        )
    
    try:
        # Set up authentication if available
        if SECRETS_AVAILABLE and setup_bigquery_auth:
            setup_bigquery_auth()
        
        # Get project ID
        project_id = input.project_id
        if not project_id and SECRETS_AVAILABLE and get_secret:
            project_id = get_secret("GOOGLE_CLOUD_PROJECT", required=False)
        # Fallback: detect from ADC if still not set
        if not project_id:
            try:
                from google.auth import default as google_auth_default
                credentials, detected_project = google_auth_default()
                if detected_project:
                    project_id = detected_project
            except Exception:
                pass
        
        if not project_id:
            return DryRunResult(
                success=False,
                errors=["No GCP project ID provided. Set GOOGLE_CLOUD_PROJECT or pass project_id parameter."]
            )
        
        # Create BigQuery client
        client = bigquery.Client(
            project=project_id,
            location=input.location
        )
        
        # Configure job
        job_config = bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False
        )
        
        if input.default_dataset:
            job_config.default_dataset = input.default_dataset
        
        # Run dry run
        query_job = client.query(input.sql, job_config=job_config)
        
        # Extract statistics
        total_bytes = query_job.total_bytes_processed or 0
        
        # Estimate cost (BigQuery pricing: $5 per TB after 1 TB free tier per month)
        # This is a rough estimate
        estimated_cost = None
        if total_bytes > 0:
            tb_processed = total_bytes / (1024 ** 4)  # Convert bytes to TB
            estimated_cost = tb_processed * 5.0  # $5 per TB
        
        # Build summary
        if total_bytes > 0:
            if total_bytes < 1024:
                size_str = f"{total_bytes} bytes"
            elif total_bytes < 1024 ** 2:
                size_str = f"{total_bytes / 1024:.2f} KB"
            elif total_bytes < 1024 ** 3:
                size_str = f"{total_bytes / (1024 ** 2):.2f} MB"
            elif total_bytes < 1024 ** 4:
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
            job_id=query_job.job_id if hasattr(query_job, 'job_id') else None,
            statistics={
                "total_bytes_processed": total_bytes,
                "total_bytes_billed": total_bytes  # Dry run doesn't bill
            }
        )
        
    except google_exceptions.GoogleAPIError as e:
        # BigQuery API error (usually SQL syntax error)
        error_msg = str(e)
        if hasattr(e, 'message'):
            error_msg = e.message
        
        return DryRunResult(
            success=False,
            errors=[f"BigQuery API error: {error_msg}"],
            summary=f"❌ SQL validation failed: {error_msg}"
        )
    
    except Exception as e:
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
            summary=f"❌ Validation error: {error_msg}"
        )
