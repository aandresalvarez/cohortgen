#!/usr/bin/env python3
"""
Quick test of the intelligent concept discovery implementation.
"""

import sys
import os
sys.path.append('projects/cd')

from find_concepts import run_intelligent_concept_discovery

def test_intelligent_discovery():
    """Test the intelligent concept discovery with a simple cohort."""
    print("🧪 Testing Intelligent Concept Discovery")
    print("=" * 50)
    
    # Simple test cohort
    cohort_definition = "Adults with heart failure"
    
    try:
        result = run_intelligent_concept_discovery(
            cohort_definition,
            max_visits=10,  # Limit for testing
            max_depth=1,    # Limit for testing
            batch_size=2    # Small batches for testing
        )
        
        print("\n✅ Test completed successfully!")
        print(f"Found {len(result.get('concept_sets', []))} concept sets")
        
        for cs in result.get('concept_sets', []):
            print(f"  - {cs.get('name', 'Unknown')}: {len(cs.get('included_concepts', []))} concepts")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_intelligent_discovery()
    sys.exit(0 if success else 1)
