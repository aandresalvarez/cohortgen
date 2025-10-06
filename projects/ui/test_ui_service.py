"""
Quick test script for the UI service layer.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from projects.ui.service import CohortService


def test_service():
    """Test basic service functionality."""
    print("Testing CohortService...")
    print("-" * 60)

    service = CohortService()

    # Test 1: Create a run
    print("\n1. Creating a new run...")
    run_id = service.create_run(
        cohort_description="Male patients age 20-30 with flu",
        name="Test Flu Cohort",
        fast_mode=True,
    )
    print(f"✓ Created run: {run_id}")

    # Test 2: Get run
    print("\n2. Retrieving run...")
    run = service.get_run(run_id)
    assert run is not None
    assert run.run_id == run_id
    assert run.name == "Test Flu Cohort"
    assert run.user_inputs.fast_mode is True
    print(f"✓ Retrieved run: {run.name}")
    print(f"  Status: {run.status.value}")
    print(f"  Fast mode: {run.user_inputs.fast_mode}")
    print(f"  Max concept sets: {run.user_inputs.max_concept_sets}")

    # Test 3: List runs
    print("\n3. Listing all runs...")
    runs = service.list_runs()
    print(f"✓ Found {len(runs)} run(s)")
    if runs:
        print(f"  Latest: {runs[0]['name']} ({runs[0]['status']})")

    # Test 4: Duplicate run
    print("\n4. Duplicating run...")
    dup_run_id = service.duplicate_run(run_id)
    print(f"✓ Duplicated as: {dup_run_id}")

    # Test 5: Verify duplicate
    dup_run = service.get_run(dup_run_id)
    assert dup_run is not None
    assert "Copy of" in dup_run.name
    assert dup_run.user_inputs.cohort_description == run.user_inputs.cohort_description
    print(f"  Name: {dup_run.name}")
    print(f"  Description: {dup_run.user_inputs.cohort_description[:40]}...")

    # Test 6: Delete runs
    print("\n5. Cleaning up...")
    service.delete_run(run_id)
    service.delete_run(dup_run_id)
    print(f"✓ Deleted test runs")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_service()

