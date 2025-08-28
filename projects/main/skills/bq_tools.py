from __future__ import annotations

import json
from typing import Any, Dict, Optional
import os

try:
    from google.cloud import bigquery  # type: ignore
    from google.api_core.exceptions import BadRequest  # type: ignore
except Exception:  # pragma: no cover - import-time safety
    bigquery = None  # type: ignore
    BadRequest = Exception  # type: ignore


# Prefer env var if set; otherwise fall back to ADC
DEFAULT_SA_PATH: Optional[str] = None


def _ensure_client(
    project_id: Optional[str] = None,
    credentials_path: Optional[str] = None,
):
    if bigquery is None:
        raise RuntimeError(
            "google-cloud-bigquery is not installed. Please install it to use BigQuery skills."
        )
    # Choose explicit credentials if provided; else env var; else ADC
    candidate_path = (
        credentials_path
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or DEFAULT_SA_PATH
    )
    if candidate_path:
        return bigquery.Client.from_service_account_json(
            candidate_path, project=project_id
        )
    return bigquery.Client(project=project_id)


def bq_dry_run(payload: str | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload, str):
        try:
            cfg = json.loads(payload)
        except Exception:
            cfg = {"sql": payload}
    else:
        cfg = payload

    sql: str = (cfg.get("sql") or "").strip()
    if not sql:
        return {"success": False, "errors": ["Empty SQL"], "total_bytes_processed": 0}

    project_id: Optional[str] = cfg.get("project_id") or os.getenv("BIGQUERY_PROJECT_ID")
    credentials_path: Optional[str] = cfg.get("credentials_path") or None
    default_dataset: Optional[str] = cfg.get("default_dataset") or os.getenv("OMOP_DATASET_ID")
    location: Optional[str] = cfg.get("location") or os.getenv("BIGQUERY_LOCATION")

    client = _ensure_client(project_id=project_id, credentials_path=credentials_path)

    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    if default_dataset:
        job_config.default_dataset = default_dataset

    try:
        job = client.query(sql, job_config=job_config, location=location)
        stats = getattr(job, "_properties", {}).get("statistics", {})
        total = getattr(job, "total_bytes_processed", 0) or stats.get(
            "totalBytesProcessed", 0
        )
        return {
            "success": True,
            "errors": [],
            "total_bytes_processed": (
                int(total) if isinstance(total, (int, float)) else total
            ),
            "job_id": getattr(job, "job_id", ""),
            "statistics": stats,
        }
    except BadRequest as e:  # type: ignore[misc]
        errors = []
        try:
            errors = list(getattr(e, "errors", []) or [])
        except Exception:
            pass
        message = str(e)
        if not errors and message:
            errors = [message]
        return {
            "success": False,
            "errors": errors,
            "total_bytes_processed": 0,
        }
    except Exception as e:
        return {
            "success": False,
            "errors": [str(e)],
            "total_bytes_processed": 0,
        }
