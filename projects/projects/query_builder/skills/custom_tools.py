from __future__ import annotations

import json
from typing import Any, Dict


def _ensure_dict(data: Any) -> Dict[str, Any]:
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            loaded = json.loads(data)
            return loaded if isinstance(loaded, dict) else {"input": loaded}
        except Exception:
            return {"input": data}
    try:
        return json.loads(json.dumps(data, default=str))
    except Exception:
        return {"input": str(data)}


async def parse_initial_payload(initial: Any) -> Dict[str, Any]:
    """Parse initial input into scratchpad values for non-interactive runs.

    Accepts either a JSON string or dict with optional keys:
      - cohort_definition: str
      - concept_sets: dict

    Returns {"scratchpad": {...}} for updates_context merge.
    """
    payload = _ensure_dict(initial)
    out: Dict[str, Any] = {}
    if "cohort_definition" in payload and isinstance(payload["cohort_definition"], str):
        out["cohort_definition"] = payload["cohort_definition"]
    if "concept_sets" in payload and isinstance(payload["concept_sets"], (dict, list)):
        out["concept_sets"] = payload["concept_sets"]
    if not out:
        return {"scratchpad": {}}
    return {"scratchpad": out}

