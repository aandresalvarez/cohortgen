#!/usr/bin/env python3
"""
Complete OMOP Cohort Definition Workflow
Runs Stage 1 → Stage 2 with automatic data passing
"""

import json
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "projects" / "clar"))
sys.path.insert(0, str(project_root / "projects" / "cd"))

from hitl_clarification_working import run_clarification_loop
from find_concepts import run_concept_discovery


def format_cohort_for_stage2(cohort_def) -> str:
    """Format CohortDefinition for Stage 2 input with all relevant details."""
    
    parts = []
    
    # Index Event (required)
    if cohort_def.index_event:
        parts.append(f"Index Event: {cohort_def.index_event}")
    
    # Demographics (important for completeness)
    if cohort_def.demographics:
        demo_str = ", ".join(f"{k}: {v}" for k, v in cohort_def.demographics.items())
        parts.append(f"Demographics: {demo_str}")
    
    # Inclusion Criteria
    if cohort_def.inclusion_criteria:
        parts.append(f"Inclusion Criteria: {', '.join(cohort_def.inclusion_criteria)}")
    
    # Exclusion Criteria
    if cohort_def.exclusion_criteria:
        parts.append(f"Exclusion Criteria: {', '.join(cohort_def.exclusion_criteria)}")
    
    # Observation Window (includes time constraints)
    if cohort_def.observation_window:
        parts.append(f"Observation Window: {cohort_def.observation_window}")
    
    # Prior Observation
    if cohort_def.prior_observation:
        parts.append(f"Prior Observation: {cohort_def.prior_observation}")
    
    # Cohort Exit
    if cohort_def.cohort_exit:
        parts.append(f"Cohort Exit: {cohort_def.cohort_exit}")
    
    return "\n".join(parts) if parts else "No cohort definition provided"


def main():
    print("\n" + "="*70)
    print("COMPLETE OMOP COHORT WORKFLOW")
    print("="*70)
    print("\nThis will run both stages:")
    print("  Stage 1: Clinical Clarification (interactive)")
    print("  Stage 2: Concept Discovery (automatic)")
    print()
    print("The output from Stage 1 will automatically feed into Stage 2.")
    print("="*70)
    print()
    
    try:
        # STAGE 1: Clinical Clarification
        print("\n" + "="*70)
        print("STAGE 1: CLINICAL CLARIFICATION")
        print("="*70)
        print()
        
        # Get initial cohort description
        print("Enter your initial cohort description:")
        print("(e.g., 'patients with diabetes who had a stroke')")
        print("-"*70)
        initial_description = input("> ").strip()
        
        if not initial_description:
            print("\n⚠️  No description provided. Exiting.")
            return
        
        # Run Stage 1
        cohort_def = run_clarification_loop(initial_description)
        
        # Format for Stage 2
        formatted_text = format_cohort_for_stage2(cohort_def)
        
        print("\n" + "="*70)
        print("✅ STAGE 1 COMPLETE - COHORT DEFINITION READY")
        print("="*70)
        print("\nFormatted cohort definition:")
        print("-"*70)
        print(formatted_text)
        print("-"*70)
        
        # Ask if user wants to continue
        print("\n" + "="*70)
        print("READY FOR STAGE 2: CONCEPT DISCOVERY")
        print("="*70)
        print()
        print("This will search ATHENA and map the cohort definition")
        print("to OMOP standard concepts.")
        print()
        
        response = input("Continue to Stage 2? [Y/n]: ").strip().lower()
        if response and response not in ('y', 'yes'):
            print("\n✅ Stopping after Stage 1.")
            print(f"\nYour cohort definition:\n{formatted_text}")
            return
        
        # STAGE 2: Concept Discovery
        print("\n" + "="*70)
        print("STAGE 2: CONCEPT DISCOVERY")
        print("="*70)
        print()
        print("Automatically using cohort definition from Stage 1...")
        print()
        
        # Run Stage 2 with the formatted text
        concept_sets = run_concept_discovery(formatted_text, max_exploration_steps=5)
        
        # Save complete output
        output_file = project_root / "projects" / "run" / "complete_cohort_output.json"
        complete_output = {
            "clinical_definition": {
                "index_event": cohort_def.index_event,
                "inclusion_criteria": cohort_def.inclusion_criteria,
                "exclusion_criteria": cohort_def.exclusion_criteria,
                "observation_window": cohort_def.observation_window,
                "demographics": cohort_def.demographics,
                "prior_observation": cohort_def.prior_observation,
                "cohort_exit": cohort_def.cohort_exit
            },
            "concept_sets": concept_sets["concept_sets"]
        }
        
        with open(output_file, "w") as f:
            json.dump(complete_output, f, indent=2)
        
        print("\n" + "="*70)
        print("✅ COMPLETE WORKFLOW FINISHED")
        print("="*70)
        print()
        print(f"Complete output saved to: {output_file}")
        print()
        print("Output includes:")
        print("  ✓ Clinical definition (plain text)")
        print("  ✓ OMOP concept sets (with IDs)")
        print()
        print("🎉 Ready for ATLAS import!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during workflow: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

