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


async def debug_log_state(data: Any, *, context: PipelineContext) -> Dict[str, Any]:
    """Debug helper to log current pipeline state.
    
    Returns the data unchanged but prints debug information about context.
    """
    import sys
    
    sp = getattr(context, "scratchpad", {})
    concept_sets = sp.get("concept_sets", [])
    exploration_history = sp.get("exploration_history", [])
    
    print("=" * 80, file=sys.stderr)
    print("🔍 DEBUG: Current Pipeline State", file=sys.stderr)
    print(f"  Concept Sets Count: {len(concept_sets) if isinstance(concept_sets, list) else 'N/A'}", file=sys.stderr)
    print(f"  Exploration History Length: {len(exploration_history) if isinstance(exploration_history, list) else 'N/A'}", file=sys.stderr)
    
    if isinstance(concept_sets, list):
        for i, cs in enumerate(concept_sets):
            if isinstance(cs, dict):
                name = cs.get("name", "unknown")
                candidates = cs.get("candidates", [])
                print(f"    Set {i+1}: {name} - {len(candidates) if isinstance(candidates, list) else 0} candidates", file=sys.stderr)
    
    print("=" * 80, file=sys.stderr)
    
    # Pass through the data unchanged
    return data if isinstance(data, dict) else {"data": data}


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


async def execute_athena_tool(payload: Dict[str, Any] | str, *, context: PipelineContext) -> Dict[str, Any]:
    """Execute a chosen Athena tool and log to exploration_history.

    Expects payload like {"tool_name": str, "tool_input": {...}}
    Accepts dict or JSON string for flexibility.
    """
    from . import athena_tools  # local import

    # Normalize input to dict
    data = await ensure_dict(payload)
    
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input")
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


async def store_as_concept_sets(data: Dict[str, Any] | str | object, *, context: PipelineContext) -> Dict[str, Any]:
    """Store concept sets into scratchpad.concept_sets.

    Accepts a dict or JSON string from a previous summarizer/normalizer step.
    If data is None or empty, falls back to using current concept_sets from context.
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
    
    # FALLBACK: If agent returned empty final_sets, use current candidates from context
    if not parsed.get("concept_sets"):
        sp = getattr(context, "scratchpad", {})
        current_sets = sp.get("concept_sets", [])
        
        if isinstance(current_sets, list) and len(current_sets) > 0:
            # Convert current candidates to final format
            final_sets = []
            for cs in current_sets:
                if not isinstance(cs, dict):
                    continue
                
                candidates = cs.get("candidates", [])
                # Filter to keep only good candidates (standard SNOMED concepts)
                included = []
                for cand in candidates:
                    if isinstance(cand, dict):
                        # Keep if it's a standard SNOMED concept
                        if (cand.get("vocabulary_id") == "SNOMED" and 
                            cand.get("standard_concept") == "S"):
                            included.append({
                                "concept_id": cand.get("concept_id"),
                                "concept_name": cand.get("concept_name"),
                                "domain_id": cand.get("domain_id"),
                                "vocabulary_id": cand.get("vocabulary_id"),
                                "standard_concept": cand.get("standard_concept"),
                                "concept_code": cand.get("concept_code")
                            })
                
                if included:  # Only include sets with valid concepts
                    final_sets.append({
                        "name": cs.get("name", "Unnamed Set"),
                        "included_concepts": included,
                        "excluded_concepts": []
                    })
            
            if final_sets:
                parsed = {"concept_sets": final_sets}
    return {"scratchpad": {"concept_sets": parsed}}


async def format_final_output(data: Dict[str, Any] | str | object) -> Dict[str, Any]:
    """Format final concept sets for output.
    
    Ensures output is in proper ATLAS-compatible JSON format.
    """
    if isinstance(data, dict):
        # If it's already properly formatted, return as-is
        if "concept_sets" in data:
            return data
        # If it's wrapped, unwrap it
        return data
    elif isinstance(data, str):
        try:
            loaded = json.loads(data)
            if isinstance(loaded, dict):
                return loaded
        except Exception:
            pass
    
    # Fallback to empty structure
    return {"concept_sets": []}


async def summarize_candidate_counts(data: Dict[str, Any] | str | object) -> str:
    """Summarize candidate counts per concept set, flagging empty sets.

    Accepts the output of athena_search_for_concept_plan / athena_expand_candidates /
    smart expansion. Handles both formats:
    - {"concept_sets": [...]} (direct format)
    - {"scratchpad": {"concept_sets": [...]}} (Flujo context format)
    
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

    # Handle both direct and scratchpad-wrapped formats
    if isinstance(payload, dict):
        if "scratchpad" in payload and isinstance(payload["scratchpad"], dict):
            sets = payload["scratchpad"].get("concept_sets")
        else:
            sets = payload.get("concept_sets")
    else:
        sets = None
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


# ============================================================================
# PIPELINE V2: Helper functions for modular validation architecture
# ============================================================================

async def aggregate_validation_results(
    concept_sets: List[Dict[str, Any]], validations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Aggregate validation results from parallel concept set validations.
    
    Combines individual validation scores and issues into a summary.
    Stores in scratchpad.validation_summary for decision making.
    """
    if not isinstance(validations, list):
        validations = [validations] if validations else []
    
    if not isinstance(concept_sets, list):
        concept_sets = []
    
    # Calculate aggregate metrics
    total_sets = len(validations)
    if total_sets == 0:
        return {
            "scratchpad": {
                "validation_summary": {
                    "average_quality": 0,
                    "total_sets": 0,
                    "ready_to_finalize": False,
                    "details": []
                }
            }
        }
    
    scores = []
    all_issues = []
    details = []
    
    for i, validation in enumerate(validations):
        if not isinstance(validation, dict):
            continue
            
        score = validation.get("quality_score", 0)
        issues = validation.get("issues", [])
        recommendations = validation.get("recommendations", "")
        
        scores.append(score)
        all_issues.extend(issues)
        
        # Get corresponding concept set name
        set_name = concept_sets[i].get("name", f"Set {i+1}") if i < len(concept_sets) else f"Set {i+1}"
        
        details.append({
            "name": set_name,
            "quality_score": score,
            "issues": issues,
            "recommendations": recommendations,
            "exclude_concepts": validation.get("exclude_concepts", []),
            "missing_concepts": validation.get("missing_concepts", [])
        })
    
    avg_quality = sum(scores) / len(scores) if scores else 0
    ready = avg_quality >= 8 and len(all_issues) == 0
    
    return {
        "scratchpad": {
            "validation_summary": {
                "average_quality": round(avg_quality, 2),
                "total_sets": total_sets,
                "ready_to_finalize": ready,
                "all_issues": all_issues,
                "details": details
            }
        }
    }


async def apply_concept_refinements(
    concept_sets: List[Dict[str, Any]], validations: Dict[str, Any]
) -> Dict[str, Any]:
    """Apply refinements based on validation feedback.
    
    Removes exclude_concepts and marks missing_concepts for addition.
    """
    if not isinstance(concept_sets, list):
        concept_sets = []
    
    if not isinstance(validations, dict):
        validations = {}
    
    details = validations.get("details", [])
    refined_sets = []
    
    for i, concept_set in enumerate(concept_sets):
        if i >= len(details):
            refined_sets.append(concept_set)
            continue
        
        validation = details[i]
        exclude_ids = set(validation.get("exclude_concepts", []))
        
        # Filter out excluded candidates
        candidates = concept_set.get("candidates", [])
        filtered_candidates = [
            c for c in candidates
            if c.get("concept_id") not in exclude_ids
        ]
        
        refined_set = {
            **concept_set,
            "candidates": filtered_candidates,
            "refinement_applied": True,
            "excluded_count": len(candidates) - len(filtered_candidates)
        }
        
        refined_sets.append(refined_set)
    
    return {
        "scratchpad": {
            "concept_sets": refined_sets
        }
    }


async def increment_counter(current: int) -> Dict[str, Any]:
    """Increment a counter value. Used for tracking refinement iterations."""
    return {
        "scratchpad": {
            "refinement_count": (current if isinstance(current, int) else 0) + 1
        }
    }


async def extract_concept_sets_for_map(data: Any, *, context: PipelineContext) -> List[Dict[str, Any]]:
    """Extract concept_sets from context.scratchpad for use in map steps.
    
    Returns the list directly (not wrapped in scratchpad) so map can iterate over it.
    The data parameter is ignored - we always read from context.
    """
    sp = getattr(context, "scratchpad", {})
    concept_sets = sp.get("concept_sets", [])
    
    if not isinstance(concept_sets, list):
        return []
    
    return concept_sets


async def finalize_concept_sets(
    concept_sets: List[Dict[str, Any]], validations: Dict[str, Any]
) -> Dict[str, Any]:
    """Convert validated concept sets into final OHDSI-compatible format.
    
    Output format matches ATLAS concept set structure:
    {
      "concept_sets": [
        {
          "name": str,
          "included_concepts": [{concept_id, concept_name, domain_id, ...}],
          "excluded_concepts": []
        }
      ]
    }
    """
    if not isinstance(concept_sets, list):
        concept_sets = []
    
    final_sets = []
    
    for concept_set in concept_sets:
        name = concept_set.get("name", "Unnamed Set")
        candidates = concept_set.get("candidates", [])
        
        # Convert candidates to included_concepts format
        included = []
        for cand in candidates:
            included.append({
                "concept_id": cand.get("concept_id"),
                "concept_name": cand.get("concept_name"),
                "domain_id": cand.get("domain_id"),
                "vocabulary_id": cand.get("vocabulary_id"),
                "standard_concept": cand.get("standard_concept"),
                "concept_code": cand.get("concept_code")
            })
        
        final_sets.append({
            "name": name,
            "included_concepts": included,
            "excluded_concepts": []  # Could be populated from validation if needed
        })
    
    return {
        "scratchpad": {
            "final_concept_sets": {
                "concept_sets": final_sets
            }
        }
    }
