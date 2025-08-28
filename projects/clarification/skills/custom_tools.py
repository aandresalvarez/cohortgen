from __future__ import annotations
from typing import Any, Dict


# Example custom tool function
async def echo_tool(x: str) -> str:
    return x


async def wrap_in_scratchpad(data: Any, *, key: str = "value") -> Dict[str, Any]:
    """Wrap arbitrary data under context.scratchpad[key] for updates_context merge.

    Returns a mapping suitable for YAML steps with `updates_context: true`.
    """
    return {"scratchpad": {key: data}}
