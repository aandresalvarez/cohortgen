from __future__ import annotations

import json
from typing import Any, Dict


async def echo_tool(x: str) -> str:
    return x


async def ensure_dict(data: Dict[str, Any] | str | object) -> Dict[str, Any]:
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
    return {"scratchpad": {key: data}}


async def parse_initial_payload(initial: Any) -> Dict[str, Any]:
    if initial is None:
        return {"scratchpad": {}}
    if isinstance(initial, str):
        try:
            data = json.loads(initial)
        except Exception:
            data = {}
    elif isinstance(initial, dict):
        data = initial
    else:
        try:
            data = json.loads(json.dumps(initial, default=str))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
    out: Dict[str, Any] = {}
    cd = data.get("cohort_definition")
    if isinstance(cd, str) and cd.strip():
        out["cohort_definition"] = cd
    cs = data.get("concept_sets")
    if isinstance(cs, (dict, list)):
        out["concept_sets"] = cs
    return {"scratchpad": out}


async def store_final_sql(sql: Any) -> Dict[str, Any]:
    if sql is None:
        sql = ""
    return {"scratchpad": {"final_sql": sql}}


async def store_current_sql(sql: Any) -> Dict[str, Any]:
    if sql is None:
        sql = ""
    return {"scratchpad": {"current_sql": sql}}


async def store_dry_run_result(result: Any) -> Dict[str, Any]:
    return {"scratchpad": {"dry_run_result": result or {}}}
