from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Dict, List

import pytest


def _load_custom_tools_module():
    """Load the disco custom_tools module by path to avoid package import issues."""
    mod_path = Path(__file__).resolve().parent / "skills" / "custom_tools.py"
    assert mod_path.is_file(), f"custom_tools.py not found at {mod_path}"
    spec = importlib.util.spec_from_file_location("disco_custom_tools", str(mod_path))
    assert spec and spec.loader, "Failed to create import spec for custom_tools.py"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    return mod


def _make_lgs_payload() -> Dict[str, Any]:
    """Create a minimal concept payload for Lennox-Gastaut mapping tests."""
    return {
        "success": True,
        "concept_id": 46256077,
        "summary": {
            "details": {
                "id": 46256077,
                "name": "Lennox Gastaut Syndrome",
                "domainId": "Condition",
                "vocabularyId": "MeSH",
                "conceptClassId": "Main Heading",
                "standardConcept": "Non-standard",
            },
            "relationships": {
                "count": 1,
                "items": [
                    {
                        "relationshipName": "Non-standard to Standard map (OMOP)",
                        "relationships": [
                            {
                                "targetConceptId": 4046213,
                                "targetConceptName": "Lennox-Gastaut syndrome",
                                "targetVocabularyId": "SNOMED",
                                "relationshipId": "Maps to",
                                "relationshipName": "Non-standard to Standard map (OMOP)",
                            }
                        ],
                    }
                ],
            },
        },
    }


@pytest.mark.asyncio
async def test_try_short_circuit_resolves_lgs() -> None:
    ct = _load_custom_tools_module()
    payload = _make_lgs_payload()
    out = await ct.try_short_circuit({"concepts": [payload], "term": "Lennox Gastaut Syndrome"})
    assert out["resolved"] is True
    assert out["resolved_concept_id"] == 4046213
    ev = out.get("evidence", {})
    assert ev.get("from_concept_id") == 46256077
    assert ev.get("relationship") == "Maps to"


@pytest.mark.asyncio
async def test_minify_concepts_keeps_maps_to_and_id() -> None:
    ct = _load_custom_tools_module()
    payload = _make_lgs_payload()
    out = await ct.minify_concepts({"concepts": [payload]})
    concepts: List[Dict[str, Any]] = out.get("concepts", [])
    assert len(concepts) == 1
    entry = concepts[0]
    # concept_id should be derived and preserved
    assert entry.get("concept_id") == 46256077
    # relationships.maps_to should include the SNOMED mapping
    maps_to = entry.get("relationships", {}).get("maps_to", [])
    assert any(mt.get("concept_id") == 4046213 for mt in maps_to)


@pytest.mark.asyncio
async def test_minify_concepts_handles_none() -> None:
    ct = _load_custom_tools_module()
    out = await ct.minify_concepts(None)
    assert out == {"concepts": []}


class _Ctx:
    def __init__(self) -> None:
        self.scratchpad = {}


@pytest.mark.asyncio
async def test_mark_batch_visited_updates_state() -> None:
    ct = _load_custom_tools_module()
    ctx = _Ctx()
    # Initialize queue state with candidate ids [1,2,3]
    await ct.queue_init([1, 2, 3], context=ctx, batch_size=2, max_depth=2, max_visits=10)
    # Mark [1,2] visited
    await ct.mark_batch_visited([1, 2], context=ctx)
    state = ctx.scratchpad.get(ct.QUEUE_STATE_KEY, {})
    visited = state.get("visited", [])
    pending = state.get("pending", [])
    assert 1 in visited and 2 in visited
    assert all(item.get("concept_id") not in {1, 2} for item in pending)


@pytest.mark.asyncio
async def test_update_queue_marks_bad_batch_on_empty_concepts() -> None:
    ct = _load_custom_tools_module()
    out = await ct.update_queue_from_batch({
        "ids": [111, 222],
        "depths": [0, 0],
        "concepts": [],
        "decisions": [],
    })
    qs = out.get("queue_state", {})
    assert qs.get("stop_reason") == "bad_batch"


@pytest.mark.asyncio
async def test_try_short_circuit_rxnorm_ingredient_exact() -> None:
    ct = _load_custom_tools_module()
    payload = {
        "success": True,
        "concept_id": 1112807,
        "summary": {
            "details": {
                "id": 1112807,
                "name": "aspirin",
                "domainId": "Drug",
                "vocabularyId": "RxNorm",
                "conceptClassId": "Ingredient",
                "standardConcept": "Standard",
                "synonyms": ["Acetylsalicylic acid"],
            }
        }
    }
    out = await ct.try_short_circuit({"concepts": [payload], "term": "aspirin"})
    assert out["resolved"] is True
    assert out["resolved_concept_id"] == 1112807


@pytest.mark.asyncio
async def test_try_short_circuit_snomed_condition_exact() -> None:
    ct = _load_custom_tools_module()
    payload = {
        "success": True,
        "concept_id": 12345,
        "summary": {
            "details": {
                "id": 12345,
                "name": "Appendicitis",
                "domainId": "Condition",
                "vocabularyId": "SNOMED",
                "conceptClassId": "Disorder",
                "standardConcept": "Standard",
                "synonyms": ["Inflammation of appendix"],
            }
        }
    }
    out = await ct.try_short_circuit({"concepts": [payload], "term": "appendicitis"})
    assert out["resolved"] is True and out["resolved_concept_id"] == 12345


@pytest.mark.asyncio
async def test_try_short_circuit_loinc_component_exact() -> None:
    ct = _load_custom_tools_module()
    payload = {
        "success": True,
        "concept_id": 67890,
        "summary": {
            "details": {
                "id": 67890,
                "name": "Hemoglobin A1c",
                "domainId": "Measurement",
                "vocabularyId": "LOINC",
                "conceptClassId": "Component",
                "standardConcept": "Standard",
            }
        }
    }
    out = await ct.try_short_circuit({"concepts": [payload], "term": "Hemoglobin A1c"})
    assert out["resolved"] is True and out["resolved_concept_id"] == 67890


@pytest.mark.asyncio
async def test_try_short_circuit_cpt4_procedure_exact() -> None:
    ct = _load_custom_tools_module()
    payload = {
        "success": True,
        "concept_id": 24680,
        "summary": {
            "details": {
                "id": 24680,
                "name": "Appendectomy",
                "domainId": "Procedure",
                "vocabularyId": "CPT4",
                "conceptClassId": "CPT4",
                "standardConcept": "Standard",
            }
        }
    }
    out = await ct.try_short_circuit({"concepts": [payload], "term": "Appendectomy"})
    assert out["resolved"] is True and out["resolved_concept_id"] == 24680


class _Ctx2:
    def __init__(self, term: str) -> None:
        self.scratchpad = {}
        self.initial_prompt = term


@pytest.mark.asyncio
async def test_update_queue_fallback_resolves_snomed_condition_exact() -> None:
    ct = _load_custom_tools_module()
    ctx = _Ctx2("Appendicitis")
    # Seed queue
    await ct.queue_init([12345], context=ctx, batch_size=1, max_depth=2, max_visits=10)
    concepts = [{
        "success": True,
        "concept_id": 12345,
        "summary": {"details": {
            "id": 12345,
            "name": "Appendicitis",
            "domainId": "Condition",
            "vocabularyId": "SNOMED",
            "conceptClassId": "Disorder",
            "standardConcept": "Standard",
        }}
    }]
    out = await ct.update_queue_from_batch({
        "ids": [12345],
        "depths": [0],
        "concepts": concepts,
        "decisions": [{}],  # no winner
    }, context=ctx)
    qs = out.get("queue_state", {})
    assert qs.get("resolved") is True
    rc = qs.get("resolved_concept", {})
    assert rc.get("concept_id") == 12345

