from __future__ import annotations

from typing import Any, Dict, List

import importlib


def _make_fake_results(items: List[Dict[str, Any]]):
    class FakeResults:
        def top(self, k: int):
            return items[:k]

        def all(self):
            return list(items)

    return FakeResults()


class FakeAthena:
    def __init__(self, mapping: Dict[str, List[Dict[str, Any]]]):
        self.mapping = mapping

    def search(self, q: str):
        return _make_fake_results(self.mapping.get(q, []))


def test_athena_search_for_concept_plan_filters_and_limits(monkeypatch):
    import sys
    from pathlib import Path

    skills_dir = (
        Path(__file__).resolve().parents[1]
        / "projects"
        / "concept_discovery"
        / "skills"
    )
    sys.path.insert(0, str(skills_dir))
    athena_tools = importlib.import_module("athena_tools")

    # Build a fake dataset returned by Athena
    items = [
        # Valid: standard 'S', correct domain/vocab
        {
            "concept_id": 1,
            "concept_name": "COVID-19",
            "domain_id": "Condition",
            "vocabulary_id": "SNOMED",
            "standard_concept": "S",
            "concept_code": "111",
        },
        # Excluded: wrong domain
        {
            "concept_id": 2,
            "concept_name": "Some drug",
            "domain_id": "Drug",
            "vocabulary_id": "RxNorm",
            "standard_concept": "S",
            "concept_code": "222",
        },
        # Excluded when standard_only: non-standard
        {
            "concept_id": 3,
            "concept_name": "COVID-NonStd",
            "domain_id": "Condition",
            "vocabulary_id": "SNOMED",
            "standard_concept": None,
            "concept_code": "333",
        },
        # Allowed by search filter stage: classification 'C'
        {
            "concept_id": 4,
            "concept_name": "COVID-19 class",
            "domain_id": "Condition",
            "vocabulary_id": "SNOMED",
            "standard_concept": "C",
            "concept_code": "444",
        },
    ]

    fake = FakeAthena({"COVID": items})

    # Patch the internal factory to use our fake client
    monkeypatch.setattr(athena_tools, "_safe_athena", lambda: fake)

    plan = {
        "concept_sets": [
            {
                "name": "Index condition",
                "intent": "Primary COVID-19",
                "domain": "Condition",
                "vocabulary": ["SNOMED"],
                "include_descendants": True,
                "standard_only": True,
                "queries": ["COVID"],
            }
        ]
    }

    out = athena_tools.athena_search_for_concept_plan(plan, top_k=2)

    # Function now returns scratchpad format for Flujo context updates
    assert "scratchpad" in out and "concept_sets" in out["scratchpad"]
    assert len(out["scratchpad"]["concept_sets"]) == 1
    cs = out["scratchpad"]["concept_sets"][0]
    # Enforces top_k limit
    assert len(cs["candidates"]) <= 2
    # Ensure only domain+vocab-matching and standard-only (S or C) make it through
    ids = {c["concept_id"] for c in cs["candidates"]}
    assert 1 in ids  # S, Condition, SNOMED
    # 2 excluded (Drug)
    assert 2 not in ids
    # 3 excluded (non-standard)
    assert 3 not in ids
    # 4 allowed at this stage (classification 'C'); later stages may filter to 'S' only
    assert 4 in ids


def test_athena_search_accepts_camel_case_and_bools(monkeypatch):
    import sys
    from pathlib import Path
    skills_dir = (
        Path(__file__).resolve().parents[1]
        / "projects"
        / "concept_discovery"
        / "skills"
    )
    sys.path.insert(0, str(skills_dir))
    athena_tools = importlib.import_module("athena_tools")

    items = [
        {
            "conceptId": 10,
            "conceptName": "Influenza",
            "domainId": "Condition",
            "vocabularyId": "SNOMED",
            "isStandard": True,
            "conceptCode": "X1",
        },
        {
            "conceptId": 11,
            "conceptName": "Flu lab test",
            "domainId": "Measurement",
            "vocabularyId": "LOINC",
            "isStandard": True,
            "conceptCode": "X2",
        },
    ]

    fake = FakeAthena({"Influenza": items})
    # Patch factory
    monkeypatch.setattr(athena_tools, "_safe_athena", lambda: fake)

    plan = {
        "concept_sets": [
            {
                "name": "Influenza",
                "domain": "Condition",
                "vocabulary": ["SNOMED"],
                "include_descendants": True,
                "standard_only": True,
                "queries": ["Influenza"],
            }
        ]
    }
    out = athena_tools.athena_search_for_concept_plan(plan, top_k=5)
    # Function now returns scratchpad format for Flujo context updates
    cs = out["scratchpad"]["concept_sets"][0]
    assert len(cs["candidates"]) == 1
    c = cs["candidates"][0]
    assert c["concept_id"] == 10
    assert c["domain_id"] == "Condition"
    assert c["vocabulary_id"] == "SNOMED"
