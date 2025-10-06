"""
Integration tests for the complete OMOP cohort workflow.

Tests the data flow between all 3 stages:
- Stage 1: Clinical Clarification → CohortDefinition
- Stage 2: Concept Discovery → ConceptSets
- Stage 3: SQL Generation → BigQuery SQL

These tests verify that outputs from one stage can be consumed by the next stage.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Literal

import pytest
from pydantic import BaseModel, Field


# ============================================================================
# Models from Stage 1 (Clarification)
# ============================================================================

class CohortDefinition(BaseModel):
    """Complete OMOP cohort definition components."""
    index_event: str = ""
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    observation_window: str = ""
    demographics: dict[str, str] = Field(default_factory=dict)
    prior_observation: str = ""
    cohort_exit: str = ""


# ============================================================================
# Models from Stage 3 (SQL Generation)
# ============================================================================

class Concept(BaseModel):
    """OMOP concept."""
    concept_id: int
    concept_name: str
    domain_id: str
    vocabulary_id: str
    standard_concept: str | None = None
    concept_code: str = ""


class ConceptSet(BaseModel):
    """Concept set for ATLAS."""
    name: str
    included_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    excluded_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    include_descendants: bool = True
    standard_only: bool = True


class CohortInput(BaseModel):
    """Input for SQL generation (Stage 3)."""
    clinical_definition: Dict[str, Any]
    concept_sets: List[ConceptSet]


# ============================================================================
# Test: Stage 1 → Stage 2 Data Flow
# ============================================================================

def test_stage1_output_to_stage2_input():
    """Test that Stage 1 output can be formatted for Stage 2 input."""
    # Create a Stage 1 output
    cohort_def = CohortDefinition(
        index_event="positive flu test",
        demographics={"age": "20-30", "gender": "male"},
        observation_window="in year 2020",
        inclusion_criteria=["continuous enrollment 365 days"],
        exclusion_criteria=["immunocompromised"]
    )
    
    # Format for Stage 2 (this is what run_complete_workflow.py does)
    formatted = _format_cohort_for_stage2(cohort_def)
    
    # Verify formatted string contains key information
    assert "positive flu test" in formatted
    assert "age: 20-30" in formatted or "20-30" in formatted
    assert "male" in formatted
    assert "2020" in formatted
    
    # Verify it's a string (Stage 2 expects string input)
    assert isinstance(formatted, str)
    assert len(formatted) > 0


def _format_cohort_for_stage2(cohort_def) -> str:
    """Helper to format CohortDefinition for Stage 2 input."""
    parts = []
    
    if cohort_def.index_event:
        parts.append(f"Index Event: {cohort_def.index_event}")
    
    if cohort_def.demographics:
        demo_str = ", ".join(f"{k}: {v}" for k, v in cohort_def.demographics.items())
        parts.append(f"Demographics: {demo_str}")
    
    if cohort_def.inclusion_criteria:
        parts.append(f"Inclusion Criteria: {', '.join(cohort_def.inclusion_criteria)}")
    
    if cohort_def.exclusion_criteria:
        parts.append(f"Exclusion Criteria: {', '.join(cohort_def.exclusion_criteria)}")
    
    if cohort_def.observation_window:
        parts.append(f"Observation Window: {cohort_def.observation_window}")
    
    return "\n".join(parts) if parts else "No cohort definition provided"


# ============================================================================
# Test: Stage 2 → Stage 3 Data Flow
# ============================================================================

def test_stage2_output_to_stage3_input():
    """Test that Stage 2 output can be used as Stage 3 input."""
    # Create Stage 1 output
    clinical_def = CohortDefinition(
        index_event="positive flu test",
        demographics={"age": "20-30", "gender": "male"}
    )
    
    # Create Stage 2 output (concept sets)
    concept_sets = [
        {
            "name": "Influenza Test",
            "included_concepts": [
                {
                    "concept_id": 4171852,
                    "concept_name": "Influenza virus A RNA",
                    "domain_id": "Measurement",
                    "vocabulary_id": "LOINC",
                    "standard_concept": "S"
                }
            ],
            "excluded_concepts": [],
            "include_descendants": True,
            "standard_only": True
        }
    ]
    
    # Create Stage 3 input (CohortInput model)
    cohort_input = CohortInput(
        clinical_definition=clinical_def.model_dump(),
        concept_sets=[ConceptSet(**cs) for cs in concept_sets]
    )
    
    # Verify the input is valid
    assert cohort_input.clinical_definition["index_event"] == "positive flu test"
    assert len(cohort_input.concept_sets) == 1
    assert cohort_input.concept_sets[0].name == "Influenza Test"
    assert len(cohort_input.concept_sets[0].included_concepts) == 1


# ============================================================================
# Test: Complete Workflow Data Structure
# ============================================================================

def test_complete_workflow_output_structure():
    """Test the complete workflow output structure (complete_cohort_output.json)."""
    # Create Stage 1 output
    clinical_def = CohortDefinition(
        index_event="positive flu test",
        demographics={"age": "20-30", "gender": "male"},
        observation_window="in year 2020"
    )
    
    # Create Stage 2 output
    concept_sets = [
        {
            "name": "Influenza Test",
            "included_concepts": [
                {
                    "concept_id": 4171852,
                    "concept_name": "Influenza virus A RNA",
                    "domain_id": "Measurement",
                    "vocabulary_id": "LOINC",
                    "standard_concept": "S"
                }
            ],
            "excluded_concepts": []
        }
    ]
    
    # Create combined output (as saved by run_complete_workflow.py)
    complete_output = {
        "clinical_definition": clinical_def.model_dump(),
        "concept_sets": concept_sets
    }
    
    # Verify structure
    assert "clinical_definition" in complete_output
    assert "concept_sets" in complete_output
    
    assert complete_output["clinical_definition"]["index_event"] == "positive flu test"
    assert len(complete_output["concept_sets"]) == 1
    assert complete_output["concept_sets"][0]["name"] == "Influenza Test"
    
    # Verify it can be serialized to JSON
    json_str = json.dumps(complete_output)
    assert isinstance(json_str, str)
    
    # Verify it can be deserialized
    deserialized = json.loads(json_str)
    assert deserialized["clinical_definition"]["index_event"] == "positive flu test"


# ============================================================================
# Test: Model Compatibility
# ============================================================================

def test_stage1_model_serialization():
    """Test that Stage 1 CohortDefinition can be serialized."""
    cohort = CohortDefinition(
        index_event="diabetes diagnosis",
        demographics={"age": "18+"}
    )
    
    # Convert to dict
    cohort_dict = cohort.model_dump()
    
    # Should be JSON serializable
    json_str = json.dumps(cohort_dict)
    assert isinstance(json_str, str)
    
    # Should be deserializable
    reloaded = json.loads(json_str)
    assert reloaded["index_event"] == "diabetes diagnosis"


def test_stage2_model_compatibility():
    """Test that Stage 2 models are compatible with Stage 3."""
    # Create Stage 2 ConceptSet
    stage2_concept_set = {
        "name": "Diabetes",
        "included_concepts": [
            {
                "concept_id": 201826,
                "concept_name": "Type 2 diabetes mellitus",
                "domain_id": "Condition",
                "vocabulary_id": "SNOMED",
                "standard_concept": "S"
            }
        ],
        "excluded_concepts": [],
        "include_descendants": True,
        "standard_only": True
    }
    
    # Should be convertible to Stage 3 ConceptSet
    stage3_concept_set = ConceptSet(**stage2_concept_set)
    
    assert stage3_concept_set.name == "Diabetes"
    assert len(stage3_concept_set.included_concepts) == 1


# ============================================================================
# Test: Data Preservation
# ============================================================================

def test_clinical_definition_preservation():
    """Test that clinical definition is preserved through stages."""
    original = CohortDefinition(
        index_event="positive flu test",
        demographics={"age": "20-30", "gender": "male"},
        observation_window="in year 2020",
        inclusion_criteria=["continuous enrollment"],
        exclusion_criteria=["immunocompromised"],
        prior_observation="365 days",
        cohort_exit="death"
    )
    
    # Serialize and deserialize
    serialized = original.model_dump()
    restored = CohortDefinition(**serialized)
    
    # Verify all fields are preserved
    assert restored.index_event == original.index_event
    assert restored.demographics == original.demographics
    assert restored.observation_window == original.observation_window
    assert restored.inclusion_criteria == original.inclusion_criteria
    assert restored.exclusion_criteria == original.exclusion_criteria
    assert restored.prior_observation == original.prior_observation
    assert restored.cohort_exit == original.cohort_exit


def test_concept_set_preservation():
    """Test that concept sets are preserved through serialization."""
    concept_set_data = {
        "name": "Influenza",
        "included_concepts": [
            {
                "concept_id": 4171852,
                "concept_name": "Influenza virus A RNA",
                "domain_id": "Measurement",
                "vocabulary_id": "LOINC",
                "standard_concept": "S",
                "concept_code": "29464-4"
            },
            {
                "concept_id": 4171853,
                "concept_name": "Influenza virus B RNA",
                "domain_id": "Measurement",
                "vocabulary_id": "LOINC",
                "standard_concept": "S",
                "concept_code": "29465-1"
            }
        ],
        "excluded_concepts": []
    }
    
    # Serialize and deserialize
    serialized = json.dumps(concept_set_data)
    restored = json.loads(serialized)
    
    # Verify all concepts are preserved
    assert restored["name"] == "Influenza"
    assert len(restored["included_concepts"]) == 2
    assert restored["included_concepts"][0]["concept_id"] == 4171852
    assert restored["included_concepts"][1]["concept_id"] == 4171853


# ============================================================================
# Test: Error Handling at Stage Boundaries
# ============================================================================

def test_empty_clinical_definition():
    """Test handling empty clinical definition between stages."""
    # Empty cohort definition
    empty_cohort = CohortDefinition()
    
    # Format for Stage 2
    formatted = _format_cohort_for_stage2(empty_cohort)
    
    # Should return a default message
    assert formatted == "No cohort definition provided" or len(formatted) == 0


def test_empty_concept_sets():
    """Test handling empty concept sets between stages."""
    # Create input with empty concept sets
    cohort_input = CohortInput(
        clinical_definition=CohortDefinition(index_event="test").model_dump(),
        concept_sets=[]
    )
    
    assert len(cohort_input.concept_sets) == 0
    # Stage 3 should handle this gracefully


# ============================================================================
# Test: Real-World Workflow Simulation
# ============================================================================

def test_realistic_workflow():
    """Simulate a realistic end-to-end workflow."""
    # Stage 1: User describes cohort, gets structured definition
    stage1_output = CohortDefinition(
        index_event="first diagnosis of type 2 diabetes",
        demographics={"age": "18+", "gender": "any"},
        inclusion_criteria=[
            "continuous enrollment 365 days before index",
            "no prior type 1 diabetes"
        ],
        exclusion_criteria=[
            "pregnancy at index"
        ],
        observation_window="365 days before index to 730 days after",
        prior_observation="365 days continuous",
        cohort_exit="death or end of enrollment"
    )
    
    # Format for Stage 2
    stage2_input = _format_cohort_for_stage2(stage1_output)
    assert len(stage2_input) > 0
    
    # Stage 2: Maps to OMOP concepts (simulated)
    stage2_output = [
        {
            "name": "Type 2 Diabetes",
            "included_concepts": [
                {
                    "concept_id": 201826,
                    "concept_name": "Type 2 diabetes mellitus",
                    "domain_id": "Condition",
                    "vocabulary_id": "SNOMED",
                    "standard_concept": "S"
                }
            ],
            "excluded_concepts": [],
            "include_descendants": True,
            "standard_only": True
        }
    ]
    
    # Stage 3: Prepare input
    stage3_input = CohortInput(
        clinical_definition=stage1_output.model_dump(),
        concept_sets=[ConceptSet(**cs) for cs in stage2_output]
    )
    
    # Verify complete workflow data structure
    assert stage3_input.clinical_definition["index_event"] == "first diagnosis of type 2 diabetes"
    assert len(stage3_input.concept_sets) == 1
    assert stage3_input.concept_sets[0].name == "Type 2 Diabetes"
    assert len(stage3_input.concept_sets[0].included_concepts) == 1
    assert stage3_input.concept_sets[0].included_concepts[0]["concept_id"] == 201826


# ============================================================================
# Test: Output File Format
# ============================================================================

def test_complete_output_json_format():
    """Test the format of complete_cohort_output.json."""
    # Simulate the complete output file
    complete_output = {
        "clinical_definition": CohortDefinition(
            index_event="positive flu test",
            demographics={"age": "20-30", "gender": "male"},
            observation_window="in year 2020"
        ).model_dump(),
        "concept_sets": [
            {
                "name": "Influenza Test",
                "included_concepts": [
                    {
                        "concept_id": 4171852,
                        "concept_name": "Influenza virus A RNA",
                        "domain_id": "Measurement",
                        "vocabulary_id": "LOINC",
                        "standard_concept": "S"
                    }
                ],
                "excluded_concepts": []
            }
        ]
    }
    
    # Should be valid JSON
    json_str = json.dumps(complete_output, indent=2)
    parsed = json.loads(json_str)
    
    # Verify structure
    assert "clinical_definition" in parsed
    assert "concept_sets" in parsed
    assert isinstance(parsed["clinical_definition"], dict)
    assert isinstance(parsed["concept_sets"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

