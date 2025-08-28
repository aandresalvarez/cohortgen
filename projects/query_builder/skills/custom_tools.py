from __future__ import annotations

import json
from typing import Any, Dict


# Example custom tool function
async def echo_tool(x: str) -> str:
    return x


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
