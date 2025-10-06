"""
Compatibility BigQuery tools module used by tests.

Provides a minimal shim that can be monkeypatched by tests to inject
fake BigQuery clients, configs, and exceptions.
"""

from __future__ import annotations

from typing import Optional

try:
    from google.cloud import bigquery  # type: ignore
except Exception:  # pragma: no cover
    bigquery = None  # type: ignore

try:
    from google.api_core.exceptions import BadRequest  # type: ignore
except Exception:  # pragma: no cover
    class BadRequest(Exception):  # type: ignore
        pass


def _ensure_client(project_id: Optional[str] = None, credentials_path: Optional[str] = None):
    """Create a BigQuery client. Tests monkeypatch this function."""
    if bigquery is None:  # pragma: no cover
        raise RuntimeError("google-cloud-bigquery not installed")
    return bigquery.Client(project=project_id)

