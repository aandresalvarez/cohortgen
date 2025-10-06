"""
Comprehensive tests for Stage 1: Clinical Clarification Agent (Pydantic AI version).

Tests the Pydantic models and data structures for the clarification workflow.
These tests focus on model validation, serialization, and structure without requiring API calls.
"""

from __future__ import annotations

from typing import Literal
import pytest
from pydantic import BaseModel, Field, ValidationError


# Define the models locally (copy from hitl_clarification_working.py)
class CohortDefinition(BaseModel):
    """Complete OMOP cohort definition components."""
    index_event: str = ""
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    observation_window: str = ""
    demographics: dict[str, str] = Field(default_factory=dict)
    prior_observation: str = ""
    cohort_exit: str = ""


class ClarificationDecision(BaseModel):
    """Agent decides whether to ask more questions or finish."""
    action: Literal["ask", "finish"]
    question: str = ""
    cohort_components: CohortDefinition = Field(default_factory=CohortDefinition)


# ============================================================================
# Test: Pydantic Models
# ============================================================================

def test_cohort_definition_model():
    """Test that CohortDefinition model validates correctly."""
    # Valid cohort definition
    cohort = CohortDefinition(
        index_event="first diagnosis of diabetes",
        inclusion_criteria=["age 18+", "no prior insulin use"],
        exclusion_criteria=["type 1 diabetes"],
        observation_window="365 days before index",
        demographics={"age": "18+", "gender": "any"},
        prior_observation="180 days",
        cohort_exit="end of enrollment"
    )
    
    assert cohort.index_event == "first diagnosis of diabetes"
    assert len(cohort.inclusion_criteria) == 2
    assert cohort.demographics["age"] == "18+"
    
    # Empty cohort definition (defaults)
    empty_cohort = CohortDefinition()
    assert empty_cohort.index_event == ""
    assert len(empty_cohort.inclusion_criteria) == 0
    assert len(empty_cohort.demographics) == 0


def test_clarification_decision_model():
    """Test that ClarificationDecision model validates correctly."""
    # Ask decision
    ask_decision = ClarificationDecision(
        action="ask",
        question="What is the index event?",
        cohort_components=CohortDefinition()
    )
    
    assert ask_decision.action == "ask"
    assert ask_decision.question != ""
    
    # Finish decision
    finish_decision = ClarificationDecision(
        action="finish",
        question="",
        cohort_components=CohortDefinition(index_event="flu test")
    )
    
    assert finish_decision.action == "finish"
    assert finish_decision.cohort_components.index_event == "flu test"


# ============================================================================
# Test: Essential Components
# ============================================================================

def test_has_essential_components():
    """Test checking if cohort definition has essential components."""
    # Complete cohort
    complete = CohortDefinition(
        index_event="diabetes diagnosis",
        inclusion_criteria=["age 18+"]
    )
    
    # Incomplete cohort (no index event)
    incomplete = CohortDefinition(
        inclusion_criteria=["age 18+"]
    )
    
    # Check that index_event is essential
    assert complete.index_event != ""
    assert incomplete.index_event == ""


# ============================================================================
# Test: Model Field Defaults
# ============================================================================

def test_cohort_definition_defaults():
    """Test that CohortDefinition has correct default values."""
    cohort = CohortDefinition()
    
    # String fields default to empty string
    assert cohort.index_event == ""
    assert cohort.observation_window == ""
    assert cohort.prior_observation == ""
    assert cohort.cohort_exit == ""
    
    # List fields default to empty list
    assert isinstance(cohort.inclusion_criteria, list)
    assert len(cohort.inclusion_criteria) == 0
    assert isinstance(cohort.exclusion_criteria, list)
    assert len(cohort.exclusion_criteria) == 0
    
    # Dict fields default to empty dict
    assert isinstance(cohort.demographics, dict)
    assert len(cohort.demographics) == 0


def test_clarification_decision_defaults():
    """Test that ClarificationDecision has correct defaults."""
    # Decision with minimal fields
    decision = ClarificationDecision(action="ask")
    
    assert decision.action == "ask"
    assert decision.question == ""
    assert isinstance(decision.cohort_components, CohortDefinition)


# ============================================================================
# Test: Demographic Parsing
# ============================================================================

def test_demographics_structure():
    """Test that demographics are stored as structured dict."""
    cohort = CohortDefinition(
        demographics={
            "age": "20-30",
            "gender": "male",
            "ethnicity": "any"
        }
    )
    
    assert "age" in cohort.demographics
    assert "gender" in cohort.demographics
    assert cohort.demographics["age"] == "20-30"
    assert cohort.demographics["gender"] == "male"


# ============================================================================
# Test: Multiple Criteria
# ============================================================================

def test_multiple_inclusion_criteria():
    """Test handling multiple inclusion criteria."""
    cohort = CohortDefinition(
        inclusion_criteria=[
            "age 18 and older",
            "continuous enrollment 365 days",
            "no prior diabetes diagnosis"
        ]
    )
    
    assert len(cohort.inclusion_criteria) == 3
    assert "age 18 and older" in cohort.inclusion_criteria
    assert "continuous enrollment 365 days" in cohort.inclusion_criteria


def test_multiple_exclusion_criteria():
    """Test handling multiple exclusion criteria."""
    cohort = CohortDefinition(
        exclusion_criteria=[
            "type 1 diabetes",
            "pregnancy",
            "prior insulin use"
        ]
    )
    
    assert len(cohort.exclusion_criteria) == 3
    assert "type 1 diabetes" in cohort.exclusion_criteria


# ============================================================================
# Test: Model Serialization
# ============================================================================

def test_cohort_definition_to_dict():
    """Test converting CohortDefinition to dict."""
    cohort = CohortDefinition(
        index_event="flu test",
        demographics={"age": "20-30"}
    )
    
    cohort_dict = cohort.model_dump()
    
    assert isinstance(cohort_dict, dict)
    assert "index_event" in cohort_dict
    assert cohort_dict["index_event"] == "flu test"
    assert "demographics" in cohort_dict
    assert cohort_dict["demographics"]["age"] == "20-30"


def test_clarification_decision_to_dict():
    """Test converting ClarificationDecision to dict."""
    decision = ClarificationDecision(
        action="ask",
        question="What is the index event?",
        cohort_components=CohortDefinition(index_event="test")
    )
    
    decision_dict = decision.model_dump()
    
    assert isinstance(decision_dict, dict)
    assert decision_dict["action"] == "ask"
    assert "cohort_components" in decision_dict
    assert decision_dict["cohort_components"]["index_event"] == "test"


# ============================================================================
# Test: Edge Cases
# ============================================================================

def test_empty_demographics():
    """Test cohort definition with no demographics."""
    cohort = CohortDefinition(
        index_event="diabetes diagnosis",
        demographics={}
    )
    
    assert len(cohort.demographics) == 0
    assert isinstance(cohort.demographics, dict)


def test_empty_criteria_lists():
    """Test cohort definition with empty criteria lists."""
    cohort = CohortDefinition(
        index_event="test",
        inclusion_criteria=[],
        exclusion_criteria=[]
    )
    
    assert len(cohort.inclusion_criteria) == 0
    assert len(cohort.exclusion_criteria) == 0


def test_finish_with_empty_question():
    """Test finish decision can have empty question."""
    decision = ClarificationDecision(
        action="finish",
        question="",
        cohort_components=CohortDefinition(index_event="test")
    )
    
    assert decision.action == "finish"
    assert decision.question == ""


# ============================================================================
# Test: Complex Cohort Definitions
# ============================================================================

def test_complete_cohort_definition():
    """Test a complete, realistic cohort definition."""
    cohort = CohortDefinition(
        index_event="first diagnosis of type 2 diabetes",
        inclusion_criteria=[
            "age 18 and older at index",
            "continuous enrollment 365 days before index",
            "no prior type 1 diabetes"
        ],
        exclusion_criteria=[
            "pregnancy at index",
            "hospice care in prior 90 days"
        ],
        observation_window="365 days before index to 730 days after",
        demographics={
            "age": "18+",
            "gender": "any"
        },
        prior_observation="365 days continuous",
        cohort_exit="death or end of enrollment"
    )
    
    # Verify all components are populated
    assert cohort.index_event != ""
    assert len(cohort.inclusion_criteria) >= 3
    assert len(cohort.exclusion_criteria) >= 2
    assert cohort.observation_window != ""
    assert len(cohort.demographics) >= 2
    assert cohort.prior_observation != ""
    assert cohort.cohort_exit != ""


def test_minimal_cohort_definition():
    """Test a minimal but valid cohort definition."""
    cohort = CohortDefinition(
        index_event="positive COVID-19 test"
    )
    
    assert cohort.index_event != ""
    # Other fields can be empty for minimal definition
    assert len(cohort.inclusion_criteria) == 0
    assert len(cohort.exclusion_criteria) == 0


# ============================================================================
# Test: Model Validation
# ============================================================================

def test_action_literal_validation():
    """Test that action field only accepts 'ask' or 'finish'."""
    # Valid actions
    ask_decision = ClarificationDecision(action="ask")
    assert ask_decision.action == "ask"
    
    finish_decision = ClarificationDecision(action="finish")
    assert finish_decision.action == "finish"
    
    # Invalid action should raise ValidationError
    with pytest.raises(ValidationError):
        ClarificationDecision(action="invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

