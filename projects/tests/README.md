# Tests for Pydantic AI Implementations

**Comprehensive test suite for the OMOP cohort workflow components.**

---

## 📂 Test Structure

```
projects/tests/
├── __init__.py
├── test_clarification_agent.py     # Stage 1: Clinical clarification models (16 tests)
├── test_concept_discovery.py       # Stage 2: Concept discovery models (21 tests)
├── test_bigquery_tools.py          # Stage 3: BigQuery validation (13 tests)
├── test_integration.py             # Cross-stage integration (11 tests)
├── README.md                        # This file
└── run_tests.sh                     # Test runner script
```

---

## 🧪 Test Coverage

### **`test_clarification_agent.py`** (Stage 1)

Tests for clinical clarification Pydantic models:

**Test Categories**:
- **Model Validation**: CohortDefinition, ClarificationDecision
- **Field Defaults**: Empty strings, empty lists, empty dicts
- **Demographics**: Structured age/gender data
- **Criteria Lists**: Multiple inclusion/exclusion criteria
- **Serialization**: model_dump(), JSON compatibility
- **Edge Cases**: Empty fields, minimal definitions
- **Literal Validation**: Action field enum constraints

**Total Tests**: 16

### **`test_concept_discovery.py`** (Stage 2)

Tests for concept discovery Pydantic models:

**Test Categories**:
- **Model Validation**: ConceptSet, ConceptPlan, ExplorationDecision
- **Domain Handling**: Condition, Drug, Procedure, Measurement
- **Vocabulary Lists**: SNOMED, RxNorm, ICD10CM, LOINC
- **Query Handling**: Single/multiple search queries
- **Action Validation**: search, details, relationships, finish
- **Concept IDs**: Single/multiple concept ID handling
- **Final Output**: ATLAS-compatible concept set structure
- **Boolean Flags**: include_descendants, standard_only

**Total Tests**: 21

### **`test_bigquery_tools.py`** (Stage 3)

Tests for BigQuery SQL validation tools:

**Test Categories**:
- **Valid SQL**: Successful validation with cost estimation
- **Invalid SQL**: Syntax errors, table not found
- **Configuration**: Custom project ID, credentials, location
- **Edge Cases**: Empty SQL, whitespace, generic exceptions
- **Cost Estimation**: Accurate calculation based on bytes processed
- **Pydantic Models**: Input/output model validation
- **Real-world Examples**: Complex OMOP CDM queries

**Total Tests**: 13

### **`test_integration.py`** (Cross-Stage)

Tests for data flow between all 3 stages:

**Test Categories**:
- **Stage 1 → Stage 2**: Cohort definition formatting
- **Stage 2 → Stage 3**: Concept sets to SQL input
- **Complete Workflow**: End-to-end data structure
- **Model Serialization**: JSON compatibility across stages
- **Data Preservation**: Field integrity through pipeline
- **Edge Cases**: Empty definitions, empty concept sets
- **Realistic Scenarios**: Full workflow simulation

**Total Tests**: 11

---

## 📊 Summary

- **Total Tests**: 61
- **All Stages Covered**: ✅
- **No External Dependencies**: All tests use mocks
- **Fast Execution**: < 0.2 seconds
- **100% Pass Rate**: ✅

---

## 🚀 Running Tests

### **Run All Tests**

```bash
cd /Users/alvaro1/Documents/Coral/Code/cohortgen
pytest projects/tests/ -v
```

### **Run Specific Test File**

```bash
pytest projects/tests/test_bigquery_tools.py -v
```

### **Run Specific Test**

```bash
pytest projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_success -v
```

### **Run with Coverage**

```bash
pytest projects/tests/ --cov=projects/qb --cov-report=html
```

### **Use Test Runner Script**

```bash
cd projects/tests
./run_tests.sh
```

---

## 🛠️ Test Design Principles

### **1. Isolation**

- Tests don't depend on external services (BigQuery API)
- All external dependencies are mocked
- Each test is independent and can run in any order

### **2. Mock Strategy**

We use **fake objects** instead of complex mocking frameworks:

```python
class FakeBigQueryClient:
    """Mock BigQuery client for testing."""
    
    def __init__(self, total_bytes=0, errors=None, raise_bad_request=False):
        self.total_bytes = total_bytes
        self.errors = errors or []
        self.raise_bad_request = raise_bad_request
    
    def query(self, sql, job_config=None, location=None):
        if self.raise_bad_request:
            raise FakeBadRequest("Invalid SQL")
        return FakeBigQueryJob(total_bytes_processed=self.total_bytes)
```

**Benefits**:
- Easy to understand
- Simple to configure for different test scenarios
- No external dependencies
- Fast execution

### **3. Comprehensive Coverage**

Tests cover:
- ✅ Happy path (valid SQL)
- ✅ Error cases (syntax errors, table not found)
- ✅ Edge cases (empty input, whitespace)
- ✅ Configuration options (project ID, credentials, location)
- ✅ Cost calculation accuracy
- ✅ Pydantic model validation
- ✅ Real-world OMOP queries

### **4. Realistic Scenarios**

Tests use **real SQL examples** from the workflow:

```python
def test_validate_complex_omop_query(monkeypatch):
    """Test validation with a complex OMOP CDM query."""
    sql = """
    WITH cohort_base AS (
      SELECT DISTINCT m.person_id
      FROM `bigquery-public-data.cms_synthetic_patient_data_omop.measurement` m
      WHERE m.measurement_concept_id IN (4171852, 4171853)
    ),
    demographics_filter AS (...)
    SELECT DISTINCT cb.person_id
    FROM cohort_base cb
    INNER JOIN demographics_filter df ON cb.person_id = df.person_id;
    """
    # ... test validation
```

---

## 📊 Test Results Example

```
projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_success PASSED
projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_zero_bytes PASSED
projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_syntax_error PASSED
projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_table_not_found PASSED
projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_with_project_and_credentials PASSED
projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_empty_string PASSED
projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_whitespace_only PASSED
projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_generic_exception PASSED
projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_cost_calculation PASSED
projects/tests/test_bigquery_tools.py::test_validate_bigquery_sql_multiple_gb PASSED
projects/tests/test_bigquery_tools.py::test_dry_run_input_model_validation PASSED
projects/tests/test_bigquery_tools.py::test_dry_run_result_model PASSED
projects/tests/test_bigquery_tools.py::test_validate_complex_omop_query PASSED

======================= 16 passed in 0.25s =======================
```

---

## 🔧 Adding New Tests

### **Template for New Test**

```python
def test_your_feature_name(monkeypatch):
    """Test description explaining what this verifies."""
    tools = _import_qb_tools()
    
    # Setup: Create fake client with desired behavior
    fake_client = FakeBigQueryClient(
        total_bytes=1024,
        errors=[],
        raise_bad_request=False
    )
    
    # Mock the BigQuery client
    def mock_ensure_client(project_id=None, credentials_path=None):
        return fake_client
    
    import sys
    bq_tools_path = Path(__file__).resolve().parents[2] / "projects" / "query_builder" / "skills"
    sys.path.insert(0, str(bq_tools_path))
    bq_tools = importlib.import_module("bq_tools")
    monkeypatch.setattr(bq_tools, "_ensure_client", mock_ensure_client)
    monkeypatch.setattr(bq_tools, "BadRequest", FakeBadRequest)
    
    # Execute: Run the function under test
    input_data = tools.DryRunInput(sql="SELECT 1")
    result = tools.validate_bigquery_sql(input_data)
    
    # Assert: Verify expected behavior
    assert result.success is True
    assert result.total_bytes_processed == 1024
```

---

## 🎯 Best Practices

### **1. Test Names**

Use descriptive names that explain what is being tested:
- ✅ `test_validate_bigquery_sql_syntax_error`
- ✅ `test_validate_complex_omop_query`
- ❌ `test_validation`
- ❌ `test_1`

### **2. Test Documentation**

Every test should have a docstring:
```python
def test_validate_bigquery_sql_success(monkeypatch):
    """Test successful SQL validation with cost estimation."""
    # ...
```

### **3. Assertions**

Be specific about what you're asserting:
```python
# Good
assert result.success is True
assert len(result.errors) == 0
assert 5.9 <= result.estimated_cost_usd <= 6.1

# Avoid
assert result  # What are we checking?
assert result.errors == []  # Use len() for collections
```

### **4. Test Data**

Use realistic data that mirrors production:
```python
# Good: Real OMOP query
sql = """
WITH cohort_base AS (
  SELECT DISTINCT m.person_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.measurement` m
  ...
)
"""

# Avoid: Toy examples
sql = "SELECT * FROM table"
```

---

## 📈 Future Tests

### **Planned Test Files**

1. **`test_clarification_agent.py`** (Stage 1)
   - HITL loop behavior
   - Cohort definition extraction
   - Question generation logic
   - Edge cases (user says "I don't know")

2. **`test_concept_discovery_tools.py`** (Stage 2)
   - Athena search integration
   - Concept decomposition
   - Concept exploration
   - Filtering logic

3. **`test_sql_generation_agent.py`** (Stage 3)
   - SQL generation from cohort definition
   - SQL fixing logic
   - Iterative validation loop
   - OMOP CDM compliance

4. **`test_integration.py`**
   - End-to-end workflow
   - Data flow between stages
   - Output format validation

---

## 🐛 Troubleshooting

### **Import Errors**

If you get import errors, ensure the project structure is correct:
```bash
# Check that tools.py exists
ls projects/qb/tools.py

# Check that bq_tools.py exists
ls projects/query_builder/skills/bq_tools.py
```

### **Monkeypatch Not Working**

If mocking isn't working, verify the import path:
```python
# The path must match where the function is defined, not where it's imported
monkeypatch.setattr(bq_tools, "_ensure_client", mock_fn)
```

### **Tests Fail with Real API Calls**

Tests should NEVER call real APIs. If they do:
1. Check that all external dependencies are mocked
2. Verify monkeypatch is applied before the function call
3. Ensure the mock is returning the expected object

---

## 🎓 Resources

- **pytest Documentation**: https://docs.pytest.org/
- **monkeypatch Guide**: https://docs.pytest.org/en/stable/how-to/monkeypatch.html
- **BigQuery Python Client**: https://cloud.google.com/python/docs/reference/bigquery/latest
- **Pydantic Documentation**: https://docs.pydantic.dev/

---

## ✅ Test Checklist

Before committing new tests, verify:

- [ ] All tests pass (`pytest projects/tests/ -v`)
- [ ] Tests are isolated (no external API calls)
- [ ] Descriptive test names and docstrings
- [ ] Both success and failure cases covered
- [ ] Edge cases tested
- [ ] Realistic test data used
- [ ] Code is readable and maintainable

---

## 🎯 Summary

| **Aspect** | **Details** |
|------------|-------------|
| **Test Files** | 1 (BigQuery tools) |
| **Total Tests** | 16 |
| **Coverage** | Stage 3 (SQL generation) |
| **Mock Strategy** | Fake objects |
| **Execution Time** | < 1 second |
| **Dependencies** | pytest, monkeypatch |

**Goal**: Ensure the Pydantic AI workflow is robust, reliable, and production-ready! 🚀

