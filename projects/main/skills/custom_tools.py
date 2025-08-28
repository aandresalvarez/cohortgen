from __future__ import annotations

import json
from typing import Any, Dict


# Example custom tool function
async def echo_tool(x: str) -> str:
    return x


async def ensure_concept_plan_dict(
    plan: Dict[str, Any] | str | object,
) -> Dict[str, Any]:
    """Normalize a concept plan into a dict[str, Any].

    Mirrors the implementation used in the concept_discovery project.
    """
    if plan is None:
        return {}
    if isinstance(plan, dict):
        return plan
    try:
        # pydantic v2 model support via model_dump/model_dump_json if present
        from pydantic import BaseModel as PydanticBaseModel  # type: ignore

        if isinstance(plan, PydanticBaseModel):  # type: ignore[isinstance]
            try:
                return plan.model_dump()  # type: ignore[attr-defined]
            except Exception:
                return json.loads(plan.model_dump_json())  # type: ignore[attr-defined]
    except Exception:
        pass
    if isinstance(plan, str):
        try:
            loaded = json.loads(plan)
            if isinstance(loaded, dict):
                return loaded
            return {"data": loaded}
        except Exception:
            return {"data": plan}
    try:
        return json.loads(json.dumps(plan, default=str))
    except Exception:
        return {"data": str(plan)}


async def ensure_dict(data: Dict[str, Any] | str | object) -> Dict[str, Any]:
    """Normalize a JSON-like input into a dict[str, Any]."""
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            loaded = json.loads(data)
            return loaded if isinstance(loaded, dict) else {"data": loaded}
        except Exception:
            return {"data": data}
    try:
        return json.loads(json.dumps(data, default=str))
    except Exception:
        return {"data": str(data)}


async def wrap_in_scratchpad(data: Any, *, key: str = "value") -> Dict[str, Any]:
    """Wrap arbitrary data under context.scratchpad[key] for updates_context merge."""
    return {"scratchpad": {key: data}}


async def store_as_cohort_definition(text: Any) -> Dict[str, Any]:
    """Store plain-text cohort definition to context.scratchpad.cohort_definition."""
    if text is None:
        text = ""
    return {"scratchpad": {"cohort_definition": text}}


async def store_as_concept_sets(data: Dict[str, Any] | str | object) -> Dict[str, Any]:
    """Store concept sets (parsed) to context.scratchpad.concept_sets.

    Accepts a dict or JSON string and writes the parsed mapping under
    scratchpad.concept_sets.
    """
    parsed: Dict[str, Any]
    if data is None:
        parsed = {"concept_sets": []}
    elif isinstance(data, dict):
        parsed = data
    elif isinstance(data, str):
        try:
            loaded = json.loads(data)
            parsed = loaded if isinstance(loaded, dict) else {"concept_sets": []}
        except Exception:
            parsed = {"concept_sets": []}
    else:
        try:
            parsed = json.loads(json.dumps(data, default=str))
            if not isinstance(parsed, dict):
                parsed = {"concept_sets": []}
        except Exception:
            parsed = {"concept_sets": []}
    return {"scratchpad": {"concept_sets": parsed}}


async def default_influenza_concept_plan() -> Dict[str, Any]:
    """Emit a minimal concept plan for Influenza conditions.

    This plan is consumed by the Athena search tool to look up standard
    OMOP concepts for Influenza and descendants.
    """
    return {
        "concept_sets": [
            {
                "name": "Influenza (diagnosis)",
                "intent": "diagnosed influenza",
                "domain": "Condition",
                "vocabulary": ["SNOMED"],
                "include_descendants": True,
                "standard_only": True,
                "queries": ["Influenza", "Flu", "Influenza virus infection"],
            }
        ]
    }
