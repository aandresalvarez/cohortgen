"""
Test script to simulate creating and executing a run.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

# Now import service
from projects.ui.service import CohortService

def test_execution():
    """Test creating and executing a run."""
    print("=" * 60)
    print("Testing Run Execution")
    print("=" * 60)
    
    service = CohortService()
    
    # Create a test run
    print("\n1. Creating run...")
    run_id = service.create_run(
        cohort_description="Diabetes patients",
        name="Test Execution",
        fast_mode=True,
    )
    print(f"✓ Created run: {run_id}")
    
    # Start the run (Stage 1 only for now)
    print("\n2. Starting Stage 1...")
    service.start_run(run_id, stages=[1])
    
    # Wait and monitor
    print("\n3. Monitoring progress...")
    for i in range(60):  # Wait up to 60 seconds
        time.sleep(1)
        run = service.get_run(run_id)
        if not run:
            print("✗ Run not found!")
            break
            
        print(f"  [{i+1}s] Status: {run.status.value}", end="")
        if run.stages:
            stage = run.stages[-1]
            print(f" | Stage {stage.stage}: {stage.status.value}", end="")
        print()
        
        if run.status.value in ("succeeded", "failed"):
            break
    
    # Final status
    print("\n" + "=" * 60)
    run = service.get_run(run_id)
    if run:
        print(f"Final Status: {run.status.value}")
        if run.error:
            print(f"\nError:\n{run.error}")
        if run.stages:
            for stage in run.stages:
                print(f"\n  Stage {stage.stage}: {stage.status.value}")
                if stage.metrics.error_message:
                    print(f"    Error: {stage.metrics.error_message}")
    
    # Cleanup
    print("\n4. Cleaning up...")
    service.delete_run(run_id)
    print("✓ Done")
    print("=" * 60)


if __name__ == "__main__":
    test_execution()

