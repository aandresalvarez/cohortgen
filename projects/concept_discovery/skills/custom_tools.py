from __future__ import annotations

import json
from typing import Any, Dict

try:  # Prefer pydantic BaseModel if available for model_dump
    from pydantic import BaseModel as PydanticBaseModel  # type: ignore
except Exception:  # pragma: no cover - fallback when pydantic not present
    PydanticBaseModel = object  # type: ignore


# Example custom tool function
async def echo_tool(x: str) -> str:
    return x


async def ensure_concept_plan_dict(
    plan: Dict[str, Any] | str | PydanticBaseModel,
) -> Dict[str, Any]:
    """Normalize a concept plan into a dict[str, Any].

    Accepts a pydantic model, plain dict, or JSON string from the decomposer.
    Returns a mapping suitable for skills expecting Dict[str, Any].
    """
    if plan is None:
        return {}
    # If it's already a mapping
    if isinstance(plan, dict):
        return plan
    # If it's a pydantic model (v2 preferred via model_dump)
    try:
        if isinstance(plan, PydanticBaseModel):  # type: ignore[isinstance]
            try:
                return plan.model_dump()  # type: ignore[attr-defined]
            except Exception:
                # Fallback to json then load
                return json.loads(plan.model_dump_json())  # type: ignore[attr-defined]
    except Exception:
        pass
    # If it's a JSON string
    if isinstance(plan, str):
        try:
            loaded = json.loads(plan)
            if isinstance(loaded, dict):
                return loaded
            # If it parses but isn't a dict, wrap
            return {"data": loaded}
        except Exception:
            # Not valid JSON, wrap raw
            return {"data": plan}
    # Last resort: attempt JSON round-trip or stringify
    try:
        return json.loads(json.dumps(plan, default=str))
    except Exception:
        return {"data": str(plan)}
