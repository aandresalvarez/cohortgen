from __future__ import annotations

import json
from typing import Any, Dict, List
try:
    from flujo.domain.models import PipelineContext  # type: ignore
except Exception:  # Fallback for test environments without Flujo
    class PipelineContext:  # type: ignore
        pass


async def _to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        s = obj.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                loaded = json.loads(s)
                return loaded if isinstance(loaded, dict) else {"value": obj}
            except Exception:
                return {"value": obj}
        return {"value": obj}
    return {"value": str(obj)}


async def get_cohort_definition_text(value: Any) -> str:
    """Return a robust plain-text cohort definition from various wrappers.

    Accepts: plain string, {"cohort_definition": str}, {"value": str}, Pydantic-like.
    """
    d = await _to_dict(value)  # type: ignore[arg-type]
    # Prefer explicit key
    text = d.get("cohort_definition")
    if isinstance(text, str) and text.strip():
        return text.strip()
    # Common wrapper
    text = d.get("value")
    if isinstance(text, str) and text.strip():
        return text.strip()
    # Fallback to stringify
    if isinstance(value, str) and value.strip():
        return value.strip()
    return ""


async def get_concept_sets_obj(value: Any) -> Dict[str, Any]:
    """Return a dict with a top-level 'concept_sets' list if present or empty.

    Accepts: dict with concept_sets, JSON string, or generic object.
    """
    d = await _to_dict(value)  # type: ignore[arg-type]
    cs = d.get("concept_sets")
    if isinstance(cs, list):
        return {"concept_sets": cs}
    # Some flows use the value directly as a list
    if isinstance(value, list):
        return {"concept_sets": value}
    # Otherwise return empty
    return {"concept_sets": []}


"""State control helpers removed in favor of declarative transitions."""


async def prepare_concept_discovery_input(_: Any = None, *, context: PipelineContext) -> Dict[str, Any]:
    """Prepare input for concept_discovery sub-pipeline using shared context.

    Ignores direct payload and reads from context.scratchpad.
    """
    sp = getattr(context, "scratchpad", None)
    if sp is None and isinstance(context, dict):
        sp = context.get("scratchpad", {})
    if sp is None:
        sp = {}
    definition = await get_cohort_definition_text(sp.get("cohort_definition"))
    feedback = sp.get("refinement_feedback") or ""
    return {"cohort_definition": definition, "refinement_feedback": feedback}


async def prepare_query_builder_input(_: Any = None, *, context: PipelineContext) -> Dict[str, Any]:
    """Prepare input for query_builder sub-pipeline using shared context."""
    sp = getattr(context, "scratchpad", None)
    if sp is None and isinstance(context, dict):
        sp = context.get("scratchpad", {})
    if sp is None:
        sp = {}
    definition = await get_cohort_definition_text(sp.get("cohort_definition"))
    concepts = await get_concept_sets_obj(sp.get("concept_sets"))
    return {"cohort_definition": definition, "concept_sets": concepts}


async def apply_concept_review(payload: Any) -> Dict[str, Any]:
    # Accept simple yes/ok or allow JSON override for concept_sets
    text: str = ""
    if isinstance(payload, str):
        text = payload.strip()
    else:
        try:
            text = json.dumps(payload)
        except Exception:
            text = str(payload)
    accepted = False
    updated: Dict[str, Any] | None = None
    if text:
        low = text.lower().strip()
        if low in {"y", "yes", "ok", "okay", "accept", "approved"}:
            accepted = True
        else:
            try:
                data = json.loads(text)
                if isinstance(data, dict) and isinstance(data.get("concept_sets"), list):
                    updated = {"concept_sets": data["concept_sets"]}
                    accepted = True
                elif isinstance(data, list):
                    updated = {"concept_sets": data}
                    accepted = True
            except json.JSONDecodeError as e:  # type: ignore[name-defined]
                feedback = (
                    "Your input was not 'yes' and could not be parsed as valid JSON. "
                    "We'll treat it as refinement feedback to re-run concept discovery. "
                    f"Error: {e}"
                )
                return {
                    "scratchpad": {
                        "concept_review_accepted": False,
                        "review_feedback": feedback,
                        "refinement_feedback": text,
                    }
                }
            except Exception:
                accepted = False
    out: Dict[str, Any] = {"scratchpad": {"concept_review_accepted": accepted}}
    if updated is not None:
        out["scratchpad"]["concept_sets"] = updated  # type: ignore[index]
    if accepted:
        # Clear any previous feedback on success
        out["scratchpad"]["review_feedback"] = ""
        out["scratchpad"]["refinement_feedback"] = ""
    return out


async def summarize_concept_sets_brief(data: Dict[str, Any] | str | object) -> str:
    # Normalize
    obj: Dict[str, Any]
    if isinstance(data, dict):
        obj = data
    elif isinstance(data, str):
        try:
            obj = json.loads(data) if data.strip().startswith("{") else {"data": data}
        except Exception:
            obj = {"data": data}
    else:
        try:
            obj = json.loads(json.dumps(data, default=str))
            if not isinstance(obj, dict):
                obj = {"data": str(data)}
        except Exception:
            obj = {"data": str(data)}
    sets = obj.get("concept_sets")
    if not isinstance(sets, list) or not sets:
        return (
            "No valid concept sets were discovered. You can provide feedback to try again, "
            "or paste a valid JSON structure for the concept sets."
        )
    lines: List[str] = ["Concept sets summary:"]
    for cs in sets:
        if not isinstance(cs, dict):
            continue
        name = cs.get("name") or "unnamed"
        concepts = cs.get("concepts")
        ids = cs.get("concept_ids")
        n = len(concepts) if isinstance(concepts, list) else (len(ids) if isinstance(ids, list) else 0)
        lines.append(f"- {name}: {n} concepts")
    return "\n".join(lines)


async def clear_refinement_feedback(_: Any = None) -> Dict[str, Any]:
    return {"scratchpad": {"refinement_feedback": ""}}


async def parse_yes_flag(payload: Any) -> Dict[str, Any]:
    text = ""
    if isinstance(payload, str):
        text = payload.strip().lower()
    else:
        try:
            text = str(payload).strip().lower()
        except Exception:
            text = ""
    ack = text in {"y", "yes"}
    return {"scratchpad": {"assumptions_ack": ack}}


async def generate_final_report(_: Any = None, *, context: PipelineContext) -> str:
    sp = getattr(context, "scratchpad", {})
    cd = sp.get("cohort_definition") or "(no cohort definition)"
    assumptions = await extract_assumptions_text(context=context)
    cs = sp.get("concept_sets") or {}
    final_sql = sp.get("final_sql") or ""
    dry = sp.get("dry_run_result") or {}
    cost = None
    summary = None
    try:
        cost = dry.get("estimated_cost_usd")
        summary = dry.get("summary")
    except Exception:
        pass
    num_sets = 0
    if isinstance(cs, dict) and isinstance(cs.get("concept_sets"), list):
        num_sets = len(cs["concept_sets"])
    parts: List[str] = []
    parts.append("# Cohort Generation Run Summary\n")
    parts.append("## Final Cohort Definition\n")
    parts.append(str(cd) + "\n")
    parts.append("## Assumptions\n")
    parts.append(str(assumptions) + "\n")
    parts.append(f"## Concept Sets\nTotal sets: {num_sets}\n")
    parts.append("## SQL (first 80 chars)\n")
    parts.append((final_sql[:80] + ("..." if len(final_sql) > 80 else "")) + "\n")
    if summary or cost is not None:
        parts.append("## BigQuery Dry Run\n")
        if summary:
            parts.append(str(summary) + "\n")
        if cost is not None:
            parts.append(f"Estimated cost (USD): {cost}\n")
    return "\n".join(parts)


async def save_final_outputs(payload: Any) -> Dict[str, Any]:
    d: Dict[str, Any]
    if isinstance(payload, dict):
        d = payload
    else:
        try:
            d = json.loads(json.dumps(payload))
        except Exception:
            d = {}
    report = d.get("report") or ""
    sql = d.get("sql") or ""
    import os
    out_dir = os.path.join("output")
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "final_report.md")
    sql_path = os.path.join(out_dir, "final_query.sql")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(str(report))
    except Exception:
        pass
    try:
        with open(sql_path, "w", encoding="utf-8") as f:
            f.write(str(sql))
    except Exception:
        pass
    return {"scratchpad": {"final_report_path": report_path, "final_sql_path": sql_path}}


async def extract_assumptions_text(_: Any = None, *, context: PipelineContext) -> str:
    # Pull assumptions from cohort_definition text and concept_sets assumptions
    sp = getattr(context, "scratchpad", None)
    if sp is None and isinstance(context, dict):
        sp = context.get("scratchpad", {})
    if sp is None:
        sp = {}
    lines: List[str] = []
    # From cohort definition
    cd = sp.get("cohort_definition")
    if isinstance(cd, str):
        for line in cd.splitlines():
            if line.strip().lower().startswith("assumption:"):
                lines.append(line.strip())
    # From concept sets (optional field assumptions)
    cs = sp.get("concept_sets")
    if isinstance(cs, dict):
        arr = cs.get("assumptions")
        if isinstance(arr, list):
            for a in arr:
                s = str(a).strip()
                if s:
                    if not s.lower().startswith("assumption:"):
                        s = f"Assumption: {s}"
                    lines.append(s)
    # Deduplicate while preserving order
    seen = set()
    ordered: List[str] = []
    for s in lines:
        if s not in seen:
            ordered.append(s)
            seen.add(s)
    if not ordered:
        return "No explicit assumptions were detected."
    out = ["Assumptions to review:"]
    for i, s in enumerate(ordered, start=1):
        out.append(f"{i}. {s}")
    return "\n".join(out)
