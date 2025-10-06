"""
Comprehensive tests for BigQuery tools (Pydantic AI version).

Tests the dry run validation tool that checks SQL syntax and estimates cost
without executing queries against BigQuery.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Optional

import pytest


def _import_qb_tools():
    """Import the BigQuery tools module from projects/qb/."""
    qb_dir = Path(__file__).resolve().parents[2] / "projects" / "qb"
    if str(qb_dir) not in sys.path:
        sys.path.insert(0, str(qb_dir))
    try:
        return importlib.import_module("tools")
    finally:
        pass  # Keep in path for subsequent imports


# ============================================================================
# Mock BigQuery Client
# ============================================================================


class FakeQueryJobConfig:
    """Mock BigQuery QueryJobConfig."""

    def __init__(self, dry_run=False, use_query_cache=False):
        self.dry_run = dry_run
        self.use_query_cache = use_query_cache
        self.default_dataset = None


class FakeBigQueryJob:
    """Mock BigQuery query job for testing."""

    def __init__(
        self,
        total_bytes_processed: int = 0,
        job_id: str = "fake-job-123",
        errors: Optional[list] = None,
        raise_error: bool = False,
    ):
        self.total_bytes_processed = total_bytes_processed
        self.job_id = job_id
        self._properties = {"statistics": {"totalBytesProcessed": str(total_bytes_processed)}}
        self._errors = errors or []
        self._raise_error = raise_error

    def result(self):
        """Mock result method."""
        if self._raise_error:
            raise Exception("Query execution failed")
        return self


class FakeBadRequest(Exception):
    """Mock BadRequest exception from google.api_core."""

    def __init__(self, message: str, errors: Optional[list] = None):
        super().__init__(message)
        self.errors = errors or []


class FakeBigQueryClient:
    """Mock BigQuery client for testing."""

    def __init__(
        self,
        total_bytes: int = 0,
        errors: Optional[list] = None,
        raise_bad_request: bool = False,
        raise_generic_error: bool = False,
    ):
        self.total_bytes = total_bytes
        self.errors = errors or []
        self.raise_bad_request = raise_bad_request
        self.raise_generic_error = raise_generic_error
        from typing import Any as _Any
        from typing import Optional as _Optional

        self.last_sql: _Optional[str] = None
        self.last_config: _Any = None
        self.last_location: _Optional[str] = None

    def query(self, sql: str, job_config=None, location=None):
        """Mock query method."""
        self.last_sql = sql
        self.last_config = job_config
        self.last_location = location

        if self.raise_generic_error:
            raise Exception("Generic BigQuery error")

        if self.raise_bad_request:
            raise FakeBadRequest(
                "Invalid SQL syntax", errors=self.errors or [{"message": "Syntax error at line 1"}]
            )

        return FakeBigQueryJob(total_bytes_processed=self.total_bytes, errors=self.errors)

    @classmethod
    def from_service_account_json(cls, credentials_path, project=None):
        """Mock class method for service account credentials."""
        return cls()


class FakeBigQueryModule:
    """Mock bigquery module."""

    Client = FakeBigQueryClient
    QueryJobConfig = FakeQueryJobConfig


def _setup_bq_mocks(monkeypatch, fake_client):
    """Helper function to set up BigQuery mocks for all tests."""

    def mock_ensure_client(project_id=None, credentials_path=None):
        return fake_client

    # Patch the bq_tools module
    import sys

    bq_tools_path = Path(__file__).resolve().parents[2] / "projects" / "query_builder" / "skills"
    sys.path.insert(0, str(bq_tools_path))
    bq_tools = importlib.import_module("bq_tools")
    monkeypatch.setattr(bq_tools, "bigquery", FakeBigQueryModule())
    monkeypatch.setattr(bq_tools, "_ensure_client", mock_ensure_client)
    monkeypatch.setattr(bq_tools, "BadRequest", FakeBadRequest)


# ============================================================================
# Test: Valid SQL
# ============================================================================


def test_validate_bigquery_sql_success(monkeypatch):
    """Test successful SQL validation with cost estimation."""
    tools = _import_qb_tools()

    # Mock the bigquery module
    fake_client = FakeBigQueryClient(total_bytes=1024**3)  # 1 GB
    _setup_bq_mocks(monkeypatch, fake_client)

    # Test input
    sql = """
    SELECT person_id
    FROM `project.dataset.person`
    WHERE gender_concept_id = 8507
    LIMIT 100;
    """

    input_data = tools.DryRunInput(
        sql=sql,
        default_dataset="bigquery-public-data.cms_synthetic_patient_data_omop",
        location="US",
    )

    # Run validation
    result = tools.validate_bigquery_sql(input_data)

    # Assertions
    assert result.success is True
    assert len(result.errors) == 0
    assert result.total_bytes_processed == 1024**3  # 1 GB
    assert result.estimated_cost_usd is not None
    assert result.estimated_cost_usd > 0  # Should have some cost for 1 GB
    assert result.summary is not None
    assert "valid" in result.summary.lower()

    # Check that SQL was passed to client
    assert fake_client.last_sql.strip() == sql.strip()
    assert fake_client.last_location == "US"


def test_validate_bigquery_sql_zero_bytes(monkeypatch):
    """Test validation with zero bytes processed (e.g., empty result)."""
    tools = _import_qb_tools()

    fake_client = FakeBigQueryClient(total_bytes=0)
    _setup_bq_mocks(monkeypatch, fake_client)

    sql = "SELECT 1;"
    input_data = tools.DryRunInput(sql=sql)

    result = tools.validate_bigquery_sql(input_data)

    assert result.success is True
    assert result.total_bytes_processed == 0
    assert result.estimated_cost_usd == 0.0


# ============================================================================
# Test: Invalid SQL (Syntax Errors)
# ============================================================================


def test_validate_bigquery_sql_syntax_error(monkeypatch):
    """Test validation with SQL syntax error."""
    tools = _import_qb_tools()

    fake_client = FakeBigQueryClient(
        raise_bad_request=True,
        errors=[
            {"message": "Syntax error: Expected end of input but got identifier 'FORM'"},
            {"location": {"line": 2, "column": 5}},
        ],
    )
    _setup_bq_mocks(monkeypatch, fake_client)

    # Invalid SQL with typo
    sql = """
    SELECT person_id
    FORM `project.dataset.person`
    WHERE gender_concept_id = 8507;
    """

    input_data = tools.DryRunInput(sql=sql)

    result = tools.validate_bigquery_sql(input_data)

    # Assertions
    assert result.success is False
    assert len(result.errors) > 0
    assert any("Syntax error" in str(err) for err in result.errors)
    assert result.total_bytes_processed == 0
    assert result.estimated_cost_usd is None or result.estimated_cost_usd == 0


def test_validate_bigquery_sql_table_not_found(monkeypatch):
    """Test validation with table not found error."""
    tools = _import_qb_tools()

    fake_client = FakeBigQueryClient(
        raise_bad_request=True,
        errors=[{"message": "Table 'project.dataset.nonexistent_table' not found"}],
    )
    _setup_bq_mocks(monkeypatch, fake_client)

    sql = "SELECT * FROM `project.dataset.nonexistent_table`;"
    input_data = tools.DryRunInput(sql=sql)

    result = tools.validate_bigquery_sql(input_data)

    assert result.success is False
    assert any("not found" in str(err).lower() for err in result.errors)


# ============================================================================
# Test: Configuration Options
# ============================================================================


def test_validate_bigquery_sql_with_project_and_credentials(monkeypatch):
    """Test validation with custom project ID and credentials."""
    tools = _import_qb_tools()

    fake_client = FakeBigQueryClient(total_bytes=2048)
    _setup_bq_mocks(monkeypatch, fake_client)

    sql = "SELECT 1;"
    input_data = tools.DryRunInput(
        sql=sql,
        project_id="my-project",
        credentials_path="/path/to/creds.json",
        default_dataset="my-dataset",
        location="EU",
    )

    result = tools.validate_bigquery_sql(input_data)

    assert result.success is True
    assert fake_client.last_location == "EU"


# ============================================================================
# Test: Edge Cases
# ============================================================================


def test_validate_bigquery_sql_empty_string(monkeypatch):
    """Test validation with empty SQL string."""
    tools = _import_qb_tools()

    fake_client = FakeBigQueryClient()

    def mock_ensure_client(project_id=None, credentials_path=None):
        return fake_client

    import sys

    bq_tools_path = Path(__file__).resolve().parents[2] / "projects" / "query_builder" / "skills"
    sys.path.insert(0, str(bq_tools_path))
    bq_tools = importlib.import_module("bq_tools")
    monkeypatch.setattr(bq_tools, "_ensure_client", mock_ensure_client)
    monkeypatch.setattr(bq_tools, "BadRequest", FakeBadRequest)

    input_data = tools.DryRunInput(sql="")

    result = tools.validate_bigquery_sql(input_data)

    assert result.success is False
    assert any("Empty SQL" in str(err) for err in result.errors)


def test_validate_bigquery_sql_whitespace_only(monkeypatch):
    """Test validation with whitespace-only SQL."""
    tools = _import_qb_tools()

    fake_client = FakeBigQueryClient()

    def mock_ensure_client(project_id=None, credentials_path=None):
        return fake_client

    import sys

    bq_tools_path = Path(__file__).resolve().parents[2] / "projects" / "query_builder" / "skills"
    sys.path.insert(0, str(bq_tools_path))
    bq_tools = importlib.import_module("bq_tools")
    monkeypatch.setattr(bq_tools, "_ensure_client", mock_ensure_client)
    monkeypatch.setattr(bq_tools, "BadRequest", FakeBadRequest)

    input_data = tools.DryRunInput(sql="   \n   \t   ")

    result = tools.validate_bigquery_sql(input_data)

    assert result.success is False
    assert any("Empty SQL" in str(err) for err in result.errors)


def test_validate_bigquery_sql_generic_exception(monkeypatch):
    """Test handling of generic exceptions from BigQuery."""
    tools = _import_qb_tools()

    fake_client = FakeBigQueryClient(raise_generic_error=True)
    _setup_bq_mocks(monkeypatch, fake_client)

    sql = "SELECT 1;"
    input_data = tools.DryRunInput(sql=sql)

    result = tools.validate_bigquery_sql(input_data)

    assert result.success is False
    assert len(result.errors) > 0
    assert any("Generic BigQuery error" in str(err) for err in result.errors)


# ============================================================================
# Test: Cost Estimation
# ============================================================================


def test_validate_bigquery_sql_cost_calculation(monkeypatch):
    """Test that cost is calculated correctly based on bytes processed."""
    tools = _import_qb_tools()

    # Test with 1 TB (exactly)
    fake_client = FakeBigQueryClient(total_bytes=1024**4)  # 1 TB
    _setup_bq_mocks(monkeypatch, fake_client)

    sql = "SELECT * FROM big_table;"
    input_data = tools.DryRunInput(sql=sql)

    result = tools.validate_bigquery_sql(input_data)

    assert result.success is True
    assert result.total_bytes_processed == 1024**4
    # Cost should be ~$5 for 1 TB (BigQuery pricing)
    assert result.estimated_cost_usd is not None
    assert 4.9 <= result.estimated_cost_usd <= 5.1  # Allow small floating point variance


def test_validate_bigquery_sql_multiple_gb(monkeypatch):
    """Test cost estimation for queries processing multiple GB."""
    tools = _import_qb_tools()

    # Test with 500 GB
    fake_client = FakeBigQueryClient(total_bytes=500 * (1024**3))
    _setup_bq_mocks(monkeypatch, fake_client)

    sql = "SELECT * FROM medium_table;"
    input_data = tools.DryRunInput(sql=sql)

    result = tools.validate_bigquery_sql(input_data)

    assert result.success is True
    # Cost should be ~$2.5 for 500 GB (half of 1 TB)
    assert 2.4 <= result.estimated_cost_usd <= 2.6


# ============================================================================
# Test: Integration with Pydantic Models
# ============================================================================


def test_dry_run_input_model_validation():
    """Test that DryRunInput model validates correctly."""
    tools = _import_qb_tools()

    # Valid input
    valid_input = tools.DryRunInput(
        sql="SELECT 1", project_id="my-project", default_dataset="my-dataset", location="US"
    )

    assert valid_input.sql == "SELECT 1"
    assert valid_input.project_id == "my-project"
    assert valid_input.default_dataset == "my-dataset"
    assert valid_input.location == "US"

    # Optional fields should have defaults
    minimal_input = tools.DryRunInput(sql="SELECT 1")
    assert minimal_input.location == "US"  # Default
    assert minimal_input.project_id is None
    assert minimal_input.credentials_path is None


def test_dry_run_result_model():
    """Test that DryRunResult model works correctly."""
    tools = _import_qb_tools()

    # Success result
    success_result = tools.DryRunResult(
        success=True,
        errors=[],
        total_bytes_processed=1024,
        estimated_cost_usd=0.0001,
        summary="Query is valid",
    )

    assert success_result.success is True
    assert len(success_result.errors) == 0
    assert success_result.total_bytes_processed == 1024

    # Error result
    error_result = tools.DryRunResult(
        success=False, errors=["Syntax error", "Table not found"], total_bytes_processed=0
    )

    assert error_result.success is False
    assert len(error_result.errors) == 2
    assert error_result.estimated_cost_usd is None


# ============================================================================
# Test: Real-world SQL Examples
# ============================================================================


def test_validate_complex_omop_query(monkeypatch):
    """Test validation with a complex OMOP CDM query."""
    tools = _import_qb_tools()

    fake_client = FakeBigQueryClient(total_bytes=5 * (1024**3))  # 5 GB
    _setup_bq_mocks(monkeypatch, fake_client)

    # Complex OMOP query with CTEs
    sql = """
    WITH cohort_base AS (
      SELECT DISTINCT m.person_id
      FROM `bigquery-public-data.cms_synthetic_patient_data_omop.measurement` m
      WHERE m.measurement_concept_id IN (4171852, 4171853)
        AND EXTRACT(YEAR FROM m.measurement_date) = 2020
    ),
    demographics_filter AS (
      SELECT p.person_id
      FROM `bigquery-public-data.cms_synthetic_patient_data_omop.person` p
      WHERE p.gender_concept_id = 8507
        AND EXTRACT(YEAR FROM CURRENT_DATE()) - p.year_of_birth BETWEEN 20 AND 30
    )
    SELECT DISTINCT cb.person_id
    FROM cohort_base cb
    INNER JOIN demographics_filter df ON cb.person_id = df.person_id;
    """

    input_data = tools.DryRunInput(
        sql=sql,
        default_dataset="bigquery-public-data.cms_synthetic_patient_data_omop",
        location="US",
    )

    result = tools.validate_bigquery_sql(input_data)

    assert result.success is True
    assert result.total_bytes_processed == 5 * (1024**3)
    assert result.estimated_cost_usd is not None
    assert result.estimated_cost_usd > 0
    assert "valid" in result.summary.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
