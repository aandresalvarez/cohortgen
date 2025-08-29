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


async def ensure_dict(data: Dict[str, Any] | str | object) -> Dict[str, Any]:
    """Normalize a JSON-like input into a dict[str, Any].

    Accepts a plain dict, JSON string, or arbitrary object. Falls back to wrapping
    non-JSON inputs under {"data": ...}.
    """
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


async def parse_initial_payload(initial: Any) -> Dict[str, Any]:
    """Parse initial input into scratchpad.cohort_definition when provided.

    Accepts plain text or a JSON string/dict with key 'cohort_definition'.
    """
    if initial is None:
        return {"scratchpad": {}}
    text: str | None = None
    if isinstance(initial, str):
        s = initial.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                data = json.loads(s)
                if isinstance(data, dict):
                    cd = data.get("cohort_definition")
                    if isinstance(cd, str) and cd.strip():
                        text = cd.strip()
                else:
                    text = None
            except Exception:
                text = s
        else:
            text = s
    elif isinstance(initial, dict):
        cd = initial.get("cohort_definition")
        if isinstance(cd, str) and cd.strip():
            text = cd.strip()
    else:
        try:
            data = json.loads(json.dumps(initial, default=str))
            if isinstance(data, dict):
                cd = data.get("cohort_definition")
                if isinstance(cd, str) and cd.strip():
                    text = cd.strip()
        except Exception:
            text = None
    if text:
        return {"scratchpad": {"cohort_definition": text}}
    return {"scratchpad": {}}
