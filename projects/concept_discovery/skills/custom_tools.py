from __future__ import annotations

import json
from typing import Any, Dict, List
try:
    from flujo.domain.models import PipelineContext  # type: ignore
except Exception:
    class PipelineContext:  # type: ignore
        pass


async def echo_tool(x: str) -> str:
    return x


async def ensure_concept_plan_dict(plan: Dict[str, Any] | str | object) -> Dict[str, Any]:
    if plan is None:
        return {}
    if isinstance(plan, dict):
        return plan
    try:
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
        return {"scratchpad": {"exploration_history": []}}
    text: str | None = None
    if isinstance(initial, str):
        s = initial.strip()
        # Guard against status/control strings accidentally passed as the definition
        lowered = s.lower()
        status_markers = [
            "definition ready",
            "concepts ready",
            "sql validated",
            "sub-pipeline",
            "parent_paused",
        ]
        control_tokens = {"ok", "continue", "no changes", "no_changes"}
        if s.startswith("✅") or any(m in lowered for m in status_markers) or lowered in control_tokens:
            s = ""
        if s.startswith("{") and s.endswith("}"):
            try:
                data = json.loads(s)
                if isinstance(data, dict):
                    cd = data.get("cohort_definition")
                    if isinstance(cd, str) and cd.strip():
                        text = cd.strip()
                    else:
                        # Fallback: accept generic {"value": "..."} wrapper
                        val = data.get("value")
                        if isinstance(val, str) and val.strip():
                            text = val.strip()
            except Exception:
                text = s
        else:
            text = s
    elif isinstance(initial, dict):
        cd = initial.get("cohort_definition")
        if isinstance(cd, str) and cd.strip():
            text = cd.strip()
        else:
            val = initial.get("value")
            if isinstance(val, str) and val.strip():
                text = val.strip()
    else:
        try:
            data = json.loads(json.dumps(initial, default=str))
            if isinstance(data, dict):
                cd = data.get("cohort_definition")
                if isinstance(cd, str) and cd.strip():
                    text = cd.strip()
                else:
                    val = data.get("value")
                    if isinstance(val, str) and val.strip():
                        text = val.strip()
        except Exception:
            text = None
    sp: Dict[str, Any] = {"exploration_history": []}
    if text:
        sp["cohort_definition"] = text
    # Also capture refinement feedback when included in the initial payload
    try:
        init_dict = initial if isinstance(initial, dict) else json.loads(initial) if isinstance(initial, str) and initial.strip().startswith("{") else {}
    except Exception:
        init_dict = {}
    fb = init_dict.get("refinement_feedback") if isinstance(init_dict, dict) else None
    if isinstance(fb, str) and fb.strip():
        sp["refinement_feedback"] = fb.strip()
    return {"scratchpad": sp}


async def execute_athena_tool(payload: Dict[str, Any], *, context: PipelineContext) -> Dict[str, Any]:
    """Execute a chosen Athena tool and log to exploration_history.

    Expects payload like {"tool_name": str, "tool_input": {...}}
    """
    from . import athena_tools  # local import

    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    result: Dict[str, Any]
    if not tool_name or not hasattr(athena_tools, tool_name):
        result = {"success": False, "error": f"Tool '{tool_name}' not found."}
    else:
        try:
            func = getattr(athena_tools, tool_name)
            result = func(tool_input)
        except Exception as e:
            result = {"success": False, "error": str(e)}

    sp = getattr(context, "scratchpad", {})
    hist: List[Dict[str, Any]] = []
    try:
        hist = list(sp.get("exploration_history") or [])  # type: ignore[arg-type]
    except Exception:
        hist = []
    hist.append({"action": {"tool_name": tool_name, "tool_input": tool_input}, "result": result})
    return {"scratchpad": {"exploration_history": hist}}


async def store_as_concept_sets(data: Dict[str, Any] | str | object) -> Dict[str, Any]:
    """Store concept sets into scratchpad.concept_sets.

    Accepts a dict or JSON string from a previous summarizer/normalizer step.
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


async def summarize_candidate_counts(data: Dict[str, Any] | str | object) -> str:
    """Summarize candidate counts per concept set, flagging empty sets.

    Accepts the output of athena_search_for_concept_plan / athena_expand_candidates /
    smart expansion: {"concept_sets": [{"name":..., "candidates":[{...}], ...}]}
    Returns a human-readable string.
    """
    # Normalize input to dict
    if isinstance(data, dict):
        payload = data
    else:
        try:
            if isinstance(data, str):
                s = data.strip()
                if s.startswith("{") and s.endswith("}"):
                    payload = json.loads(s)
                else:
                    payload = {"data": s}
            else:
                payload = json.loads(json.dumps(data, default=str))
                if not isinstance(payload, dict):
                    payload = {"data": str(data)}
        except Exception:
            payload = {"data": str(data)}

    sets = payload.get("concept_sets") if isinstance(payload, dict) else None
    if not isinstance(sets, list):
        return "No concept sets available for summary."

    lines: list[str] = ["Concept candidate summary:"]
    zeros: int = 0
    for cs in sets:
        name = cs.get("name") or "unnamed"
        cands = cs.get("candidates") or []
        if not isinstance(cands, list):
            cands = []
        total = len(cands)
        s_cnt = 0
        c_cnt = 0
        ns_cnt = 0
        for c in cands:
            sc = c.get("standard_concept")
            if sc == "S":
                s_cnt += 1
            elif sc == "C":
                c_cnt += 1
            else:
                ns_cnt += 1
        flag = " ⚠️ EMPTY" if total == 0 else ""
        if total == 0:
            zeros += 1
        lines.append(f"- {name}: {total} candidates (S:{s_cnt}, C:{c_cnt}, non-std:{ns_cnt}){flag}")

    if zeros:
        lines.append(f"\nNote: {zeros} concept set(s) are empty. Consider adding terms or enabling deeper search.")
    return "\n".join(lines)
