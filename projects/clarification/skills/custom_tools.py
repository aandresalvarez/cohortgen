from __future__ import annotations
from typing import Any, Dict


async def echo_tool(x: str) -> str:
    return x


async def wrap_in_scratchpad(data: Any, *, key: str = "value") -> Dict[str, Any]:
    return {"scratchpad": {key: data}}


async def store_as_cohort_definition(text: Any) -> Dict[str, Any]:
    """Store plain-text cohort definition into scratchpad.cohort_definition."""
    if text is None:
        text = ""
    return {"scratchpad": {"cohort_definition": text}}
