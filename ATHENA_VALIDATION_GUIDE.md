# Athena-Client Validation Guide

This guide explains how to validate that the `athena-client` library is properly installed and can be used in the cohortgen project.

## Overview

The `athena-client` library is used to interact with the OHDSI Athena API for concept discovery and medical terminology queries. The project includes comprehensive validation functions to ensure the library is properly installed and functioning.

## Validation Functions

### 1. `validate_athena_client()`

Synchronous function that performs comprehensive validation of the athena-client library.

**Returns:** Dictionary with validation results including:
- `success`: Overall validation success
- `library_installed`: Whether the library can be imported
- `import_successful`: Whether the Athena class can be imported
- `client_creation`: Whether a client instance can be created
- `basic_functionality`: Whether basic operations work
- `version`: Library version
- `test_results`: Detailed test results for each operation

**Example:**
```python
from disco.skills.custom_tools import validate_athena_client

validation = validate_athena_client()
if validation["success"]:
    print(f"✅ athena-client {validation['version']} is working!")
else:
    print(f"❌ Validation failed: {validation['error']}")
```

### 2. `validate_athena_client_async()`

Async wrapper for the validation function, suitable for use in pipeline steps.

**Returns:** Same as `validate_athena_client()`

**Example:**
```python
from disco.skills.custom_tools import validate_athena_client_async

validation = await validate_athena_client_async()
```

### 3. `get_athena_client()`

Returns a validated Athena client instance. This function will automatically validate the library if not already done.

**Returns:** Athena client instance

**Raises:** `RuntimeError` if validation fails

**Example:**
```python
from disco.skills.custom_tools import get_athena_client

try:
    client = get_athena_client()
    results = client.search("diabetes")
except RuntimeError as e:
    print(f"athena-client not available: {e}")
```

## Testing Scripts

### 1. Basic Validation Test

Run the basic validation test:
```bash
# Activate virtual environment
source .venv/bin/activate

# Run basic validation
python test_athena_validation.py
```

### 2. Comprehensive Test Suite

Run the comprehensive test suite that validates all functionality:
```bash
# Activate virtual environment
source .venv/bin/activate

# Run comprehensive tests
python comprehensive_athena_test.py
```

## Installation

The `athena-client` library is already listed as a dependency in `pyproject.toml`:

```toml
dependencies = [
    "athena-client==1.0.27",
    # ... other dependencies
]
```

To install/update dependencies:
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## Integration in Pipeline

The validation functions are designed to be used in pipeline steps. Here's an example of how to integrate validation into a pipeline:

```python
async def validate_athena_step(data: Any) -> Dict[str, Any]:
    """Pipeline step to validate athena-client availability."""
    validation = await validate_athena_client_async()
    
    if not validation["success"]:
        return {
            "error": "athena-client validation failed",
            "details": validation,
            "recommendation": "Please install athena-client: pip install athena-client==1.0.27"
        }
    
    return {
        "success": True,
        "athena_version": validation["version"],
        "validation_details": validation
    }
```

## Error Handling

The validation functions provide detailed error information:

- **ImportError**: Library not installed
- **RuntimeError**: Client creation failed
- **API Errors**: Network or API-related issues

All errors include:
- `error`: Human-readable error message
- `error_type`: Exception type name
- `test_results`: Detailed results for each test

## Best Practices

1. **Always validate before use**: Call `validate_athena_client()` before using athena-client functionality
2. **Use the safe client getter**: Use `get_athena_client()` instead of direct imports
3. **Handle errors gracefully**: Check validation results and provide meaningful error messages
4. **Cache validation results**: The validation results are cached globally to avoid repeated checks

## Troubleshooting

### Common Issues

1. **"No module named 'athena_client'"**
   - Solution: Install the library with `pip install athena-client==1.0.27`

2. **"Cannot create Athena client"**
   - Solution: Check network connectivity and API availability

3. **"Search test failed"**
   - Solution: Verify API access and search terms

### Debug Information

The validation functions provide comprehensive debug information. Check the `test_results` field for detailed information about each test:

```python
validation = validate_athena_client()
for test_name, result in validation["test_results"].items():
    print(f"{test_name}: {result}")
```
