from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def _import_main_tools():
    import sys
    skills_dir = Path(__file__).resolve().parents[1] / "projects" / "main" / "skills"
    sys.path.insert(0, str(skills_dir))
    try:
        return importlib.import_module("custom_tools")
    finally:
        # Do not leave multiple duplicates; cleanup first occurrence we added
        try:
            sys.path.remove(str(skills_dir))
        except ValueError:
            pass


@pytest.mark.skip(reason="decide_stage removed in favor of declarative StateMachine transitions")
def test_decide_stage_flow():
    pass


@pytest.mark.asyncio
async def test_prepare_inputs_and_summary():
    tools = _import_main_tools()
    # Prepare concept discovery input
    ctx = {"scratchpad": {"cohort_definition": "My cohort definition"}}
    out = await tools.prepare_concept_discovery_input(context=ctx)
    assert out.get("cohort_definition") == "My cohort definition"
    assert "refinement_feedback" in out

    # Prepare query builder input
    ctx = {
        "scratchpad": {
            "cohort_definition": "My cohort definition",
            "concept_sets": {"concept_sets": [{"name": "A", "concept_ids": [1, 2]}]},
        }
    }
    out = await tools.prepare_query_builder_input(context=ctx)
    assert out["cohort_definition"] == "My cohort definition"
    assert isinstance(out["concept_sets"], dict)
    assert isinstance(out["concept_sets"].get("concept_sets"), list)

    # Summarize concept sets
    summary = await tools.summarize_concept_sets_brief(
        {"concept_sets": [{"name": "A", "concept_ids": [1, 2]}, {"name": "B", "concepts": [{"concept_id": 5}]}]}
    )
    assert "Concept sets summary:" in summary
    assert "A: 2 concepts" in summary
    assert "B: 1 concepts" in summary


@pytest.mark.asyncio
async def test_apply_concept_review_yes_and_json():
    tools = _import_main_tools()

    # Accept simple yes
    out = await tools.apply_concept_review("yes")
    assert out["scratchpad"]["concept_review_accepted"] is True

    # Provide JSON override
    payload = {"concept_sets": [{"name": "C", "concept_ids": [10]}]}
    out = await tools.apply_concept_review(payload)
    assert out["scratchpad"]["concept_review_accepted"] is True
    cs = out["scratchpad"].get("concept_sets")
    assert isinstance(cs, dict) and isinstance(cs.get("concept_sets"), list)

    # Invalid JSON should provide feedback and not accept
    out = await tools.apply_concept_review("{not json}")
    sp = out["scratchpad"]
    assert sp.get("concept_review_accepted") is False
    assert isinstance(sp.get("review_feedback"), str) and "could not be parsed" in sp.get("review_feedback")
    assert isinstance(sp.get("refinement_feedback"), str) and sp.get("refinement_feedback")

    # Natural language feedback should set refinement_feedback
    out = await tools.apply_concept_review("these sets include pregnancy; please exclude")
    sp = out["scratchpad"]
    assert sp.get("concept_review_accepted") is False
    assert isinstance(sp.get("refinement_feedback"), str) and "pregnancy" in sp.get("refinement_feedback")


@pytest.mark.asyncio
async def test_extract_assumptions_text():
    tools = _import_main_tools()
    ctx = {
        "scratchpad": {
            "cohort_definition": "Assumption: Using a 30-day washout.\nOther line.",
            "concept_sets": {"assumptions": ["Standard concepts only"]},
        }
    }
    out = await tools.extract_assumptions_text(context=ctx)
    assert "Assumptions to review:" in out
    assert "1. Assumption: Using a 30-day washout." in out
    assert "2. Assumption: Standard concepts only" in out
