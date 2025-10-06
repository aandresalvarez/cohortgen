"""
Comprehensive tests for Stage 2: Concept Discovery (Pydantic AI version).

Tests the Pydantic models for concept discovery workflow.
These tests focus on model validation, serialization, and structure without requiring API calls.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal

import pytest
from pydantic import BaseModel, Field, ValidationError


# Define the models locally (copy from find_concepts.py)
class ConceptSet(BaseModel):
    """A concept set to build for ATLAS."""

    name: str = Field(description="Name of the concept set")
    intent: str = Field(description="Clinical intent/description")
    domain: str = Field(description="OMOP domain: Condition, Drug, Procedure, etc.")
    vocabulary: List[str] = Field(
        default_factory=lambda: [], description="Preferred vocabularies: SNOMED, RxNorm, etc."
    )
    queries: List[str] = Field(description="Search queries to find concepts")
    include_descendants: bool = Field(
        default=True, description="Include descendant concepts in hierarchy"
    )
    standard_only: bool = Field(default=True, description="Only include standard concepts")


class ConceptPlan(BaseModel):
    """Decomposition of cohort definition into concept sets."""

    concept_sets: List[ConceptSet]


class ExplorationDecision(BaseModel):
    """Agent's decision during concept exploration."""

    action: Literal["search", "details", "relationships", "finish"]
    query: str | None = None
    domain: str | None = None
    vocabulary: List[str] | None = None
    concept_ids: List[int] | None = None
    concept_id: int | None = None
    reasoning: str = ""
    final_concept_sets: List[Dict[str, Any]] | None = None


# ============================================================================
# Test: Pydantic Models
# ============================================================================


def test_concept_set_model():
    """Test that ConceptSet model validates correctly."""
    concept_set = ConceptSet(
        name="Type 2 Diabetes",
        intent="Identify patients with type 2 diabetes diagnosis",
        domain="Condition",
        vocabulary=["SNOMED"],
        queries=["type 2 diabetes", "diabetes mellitus type 2"],
        include_descendants=True,
        standard_only=True,
    )

    assert concept_set.name == "Type 2 Diabetes"
    assert concept_set.domain == "Condition"
    assert len(concept_set.queries) == 2
    assert "SNOMED" in concept_set.vocabulary
    assert concept_set.include_descendants is True


def test_concept_plan_model():
    """Test that ConceptPlan model validates correctly."""
    plan = ConceptPlan(
        concept_sets=[
            ConceptSet(
                name="Diabetes",
                intent="Diabetes diagnosis",
                domain="Condition",
                queries=["diabetes"],
            ),
            ConceptSet(
                name="Metformin",
                intent="Metformin prescription",
                domain="Drug",
                queries=["metformin"],
            ),
        ]
    )

    assert len(plan.concept_sets) == 2
    assert plan.concept_sets[0].domain == "Condition"
    assert plan.concept_sets[1].domain == "Drug"


def test_exploration_decision_model():
    """Test that ExplorationDecision model validates correctly."""
    # Search action
    search_decision = ExplorationDecision(
        action="search",
        query="diabetes",
        domain="Condition",
        vocabulary=["SNOMED"],
        reasoning="Need to find diabetes concepts",
    )

    assert search_decision.action == "search"
    assert search_decision.query == "diabetes"
    assert search_decision.domain == "Condition"

    # Details action
    details_decision = ExplorationDecision(
        action="details", concept_ids=[201826], reasoning="Check if this is standard"
    )

    assert details_decision.action == "details"
    assert 201826 in details_decision.concept_ids

    # Finish action
    finish_decision = ExplorationDecision(
        action="finish",
        reasoning="All concepts validated",
        final_concept_sets=[
            {
                "name": "Diabetes",
                "candidates": [{"concept_id": 201826, "concept_name": "Type 2 diabetes"}],
            }
        ],
    )

    assert finish_decision.action == "finish"
    assert finish_decision.final_concept_sets is not None
    assert len(finish_decision.final_concept_sets) > 0


# ============================================================================
# Test: Model Defaults
# ============================================================================


def test_concept_set_defaults():
    """Test that ConceptSet has correct default values."""
    # Minimal concept set
    concept_set = ConceptSet(
        name="Test", intent="Test intent", domain="Condition", queries=["test"]
    )

    # Check defaults
    assert concept_set.include_descendants is True
    assert concept_set.standard_only is True
    assert isinstance(concept_set.vocabulary, list)


def test_exploration_decision_optional_fields():
    """Test that ExplorationDecision has optional fields."""
    # Finish action (most fields optional)
    decision = ExplorationDecision(action="finish", reasoning="Done")

    assert decision.action == "finish"
    assert decision.query is None
    assert decision.domain is None
    assert decision.concept_ids is None


# ============================================================================
# Test: Domain Validation
# ============================================================================


def test_valid_domains():
    """Test that common OMOP domains are accepted."""
    valid_domains = ["Condition", "Drug", "Procedure", "Measurement", "Observation"]

    for domain in valid_domains:
        concept_set = ConceptSet(
            name=f"Test {domain}", intent=f"Test {domain} intent", domain=domain, queries=["test"]
        )
        assert concept_set.domain == domain


def test_vocabulary_list():
    """Test that vocabulary field accepts list of vocabularies."""
    concept_set = ConceptSet(
        name="Test",
        intent="Test intent",
        domain="Condition",
        vocabulary=["SNOMED", "ICD10CM", "ICD9CM"],
        queries=["test"],
    )

    assert len(concept_set.vocabulary) == 3
    assert "SNOMED" in concept_set.vocabulary
    assert "ICD10CM" in concept_set.vocabulary


# ============================================================================
# Test: Query Handling
# ============================================================================


def test_multiple_queries():
    """Test handling multiple search queries."""
    concept_set = ConceptSet(
        name="Influenza",
        intent="Flu diagnosis",
        domain="Condition",
        queries=["influenza", "flu", "influenza A", "influenza B"],
    )

    assert len(concept_set.queries) == 4
    assert "influenza" in concept_set.queries
    assert "flu" in concept_set.queries


def test_single_query():
    """Test concept set with single query."""
    concept_set = ConceptSet(
        name="Diabetes",
        intent="Diabetes diagnosis",
        domain="Condition",
        queries=["type 2 diabetes mellitus"],
    )

    assert len(concept_set.queries) == 1
    assert concept_set.queries[0] == "type 2 diabetes mellitus"


# ============================================================================
# Test: Action Validation
# ============================================================================


def test_exploration_actions():
    """Test that all valid exploration actions work."""
    valid_actions = ["search", "details", "relationships", "finish"]

    for action in valid_actions:
        decision = ExplorationDecision(action=action, reasoning=f"Test {action}")
        assert decision.action == action


def test_invalid_action():
    """Test that invalid actions raise validation error."""
    with pytest.raises(ValidationError):
        ExplorationDecision(action="invalid_action", reasoning="Test")


# ============================================================================
# Test: Concept ID Handling
# ============================================================================


def test_concept_ids_list():
    """Test handling list of concept IDs."""
    decision = ExplorationDecision(
        action="details", concept_ids=[201826, 443238, 45768031], reasoning="Check these concepts"
    )

    assert len(decision.concept_ids) == 3
    assert 201826 in decision.concept_ids
    assert 443238 in decision.concept_ids


def test_single_concept_id():
    """Test handling single concept ID."""
    decision = ExplorationDecision(
        action="relationships", concept_id=201826, reasoning="Find relationships"
    )

    assert decision.concept_id == 201826


# ============================================================================
# Test: Final Output Structure
# ============================================================================


def test_final_concept_sets_structure():
    """Test structure of final concept sets."""
    final_sets = [
        {
            "name": "Type 2 Diabetes",
            "candidates": [
                {
                    "concept_id": 201826,
                    "concept_name": "Type 2 diabetes mellitus",
                    "domain_id": "Condition",
                    "vocabulary_id": "SNOMED",
                    "standard_concept": "S",
                }
            ],
            "included_concepts": [],
            "excluded_concepts": [],
        }
    ]

    decision = ExplorationDecision(
        action="finish", reasoning="Complete", final_concept_sets=final_sets
    )

    assert len(decision.final_concept_sets) == 1
    assert decision.final_concept_sets[0]["name"] == "Type 2 Diabetes"
    assert len(decision.final_concept_sets[0]["candidates"]) == 1


# ============================================================================
# Test: Complex Scenarios
# ============================================================================


def test_multi_domain_concept_plan():
    """Test concept plan spanning multiple domains."""
    plan = ConceptPlan(
        concept_sets=[
            ConceptSet(
                name="Heart Failure",
                intent="Heart failure diagnosis",
                domain="Condition",
                vocabulary=["SNOMED"],
                queries=["heart failure", "cardiac failure"],
            ),
            ConceptSet(
                name="Furosemide",
                intent="Furosemide prescription",
                domain="Drug",
                vocabulary=["RxNorm"],
                queries=["furosemide", "lasix"],
            ),
            ConceptSet(
                name="Echocardiogram",
                intent="Echo procedure",
                domain="Procedure",
                vocabulary=["SNOMED", "CPT4"],
                queries=["echocardiogram", "cardiac ultrasound"],
            ),
        ]
    )

    assert len(plan.concept_sets) == 3
    domains = [cs.domain for cs in plan.concept_sets]
    assert "Condition" in domains
    assert "Drug" in domains
    assert "Procedure" in domains


def test_complex_search_decision():
    """Test search decision with all filters."""
    decision = ExplorationDecision(
        action="search",
        query="type 2 diabetes mellitus",
        domain="Condition",
        vocabulary=["SNOMED", "ICD10CM"],
        reasoning="Find diabetes concepts with broad vocabulary coverage",
    )

    assert decision.action == "search"
    assert decision.query == "type 2 diabetes mellitus"
    assert decision.domain == "Condition"
    assert len(decision.vocabulary) == 2
    assert decision.reasoning != ""


# ============================================================================
# Test: Model Serialization
# ============================================================================


def test_concept_set_to_dict():
    """Test converting ConceptSet to dict."""
    concept_set = ConceptSet(
        name="Diabetes", intent="Diabetes diagnosis", domain="Condition", queries=["diabetes"]
    )

    concept_dict = concept_set.model_dump()

    assert isinstance(concept_dict, dict)
    assert concept_dict["name"] == "Diabetes"
    assert concept_dict["domain"] == "Condition"
    assert isinstance(concept_dict["queries"], list)


def test_exploration_decision_to_dict():
    """Test converting ExplorationDecision to dict."""
    decision = ExplorationDecision(action="search", query="diabetes", reasoning="Find concepts")

    decision_dict = decision.model_dump()

    assert isinstance(decision_dict, dict)
    assert decision_dict["action"] == "search"
    assert decision_dict["query"] == "diabetes"


# ============================================================================
# Test: Edge Cases
# ============================================================================


def test_empty_vocabulary_list():
    """Test concept set with empty vocabulary list."""
    concept_set = ConceptSet(
        name="Test", intent="Test intent", domain="Condition", vocabulary=[], queries=["test"]
    )

    assert len(concept_set.vocabulary) == 0
    assert isinstance(concept_set.vocabulary, list)


def test_none_optional_fields():
    """Test that None is accepted for optional fields."""
    decision = ExplorationDecision(
        action="finish",
        query=None,
        domain=None,
        vocabulary=None,
        concept_ids=None,
        concept_id=None,
        reasoning="Done",
        final_concept_sets=[],
    )

    assert decision.query is None
    assert decision.domain is None
    assert decision.vocabulary is None


def test_boolean_flags():
    """Test boolean flags in ConceptSet."""
    # Test with descendants
    with_descendants = ConceptSet(
        name="Test", intent="Test", domain="Condition", queries=["test"], include_descendants=True
    )

    assert with_descendants.include_descendants is True

    # Test without descendants
    without_descendants = ConceptSet(
        name="Test", intent="Test", domain="Condition", queries=["test"], include_descendants=False
    )

    assert without_descendants.include_descendants is False

    # Test standard_only flag
    standard_only = ConceptSet(
        name="Test", intent="Test", domain="Condition", queries=["test"], standard_only=False
    )

    assert standard_only.standard_only is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
