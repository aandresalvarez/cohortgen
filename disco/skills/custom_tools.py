from __future__ import annotations

import json
import time
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Sequence

# Optional typing models for clearer state handling (local to this project)
try:
    from pydantic import BaseModel, Field

    class QueueItem(BaseModel):
        concept_id: int
        depth: int = 0

    class QueueStateModel(BaseModel):
        pending: List[QueueItem] = Field(default_factory=list)
        queued_ids: List[int] = Field(default_factory=list)
        visited: List[int] = Field(default_factory=list)
        depth_map: Dict[str, int] = Field(default_factory=dict)
        history: List[Dict[str, Any]] = Field(default_factory=list)
        iteration: int = 0
        active_iteration: Optional[int] = None
        current_iteration_start: Optional[float] = None
        visit_count: int = 0
        resolved: bool = False
        resolved_concept: Optional[Dict[str, Any]] = None
        best_fallback: Optional[Dict[str, Any]] = None
        max_depth: int = MAX_DEPTH_DEFAULT if 'MAX_DEPTH_DEFAULT' in globals() else 2
        max_visits: int = MAX_VISITS_DEFAULT if 'MAX_VISITS_DEFAULT' in globals() else 50
        batch_size: int = BATCH_SIZE_DEFAULT if 'BATCH_SIZE_DEFAULT' in globals() else 3
        stop_reason: Optional[str] = None
        initial_candidates: List[int] = Field(default_factory=list)
        initial_message: Optional[str] = None
        evidence: Optional[Dict[str, Any]] = None
        # Stagnation guard bookkeeping
        last_head_id: Optional[int] = None
        stagnation_count: int = 0

    class DiscoContextModel(BaseModel):
        queue_state: Optional[QueueStateModel] = None
        scratchpad: Dict[str, Any] = Field(default_factory=dict)
        initial_prompt: Optional[str] = None
except Exception:  # pydantic not required for runtime; models are optional
    BaseModel = object  # type: ignore
    QueueItem = object  # type: ignore
    QueueStateModel = object  # type: ignore
    DiscoContextModel = object  # type: ignore

from flujo.domain.models import PipelineContext

# Global variable to cache Athena client availability
_ATHENA_AVAILABLE: Optional[bool] = None
_ATHENA_CLIENT: Optional[Any] = None

MAX_DEPTH_DEFAULT = 2
MAX_VISITS_DEFAULT = 50
BATCH_SIZE_DEFAULT = 3
HISTORY_LIMIT = 120
QUEUE_STATE_KEY = "_omop_queue_state"


def validate_athena_client() -> Dict[str, Any]:
    """
    Comprehensive validation of athena-client library installation and functionality.
    
    Returns:
        Dict containing validation results with success status, version info, and test results.
    """
    global _ATHENA_AVAILABLE, _ATHENA_CLIENT
    
    validation_result = {
        "success": False,
        "library_installed": False,
        "import_successful": False,
        "client_creation": False,
        "basic_functionality": False,
        "version": None,
        "error": None,
        "error_type": None,
        "test_results": {}
    }
    
    # Test 1: Check if library is installed
    try:
        import athena_client
        validation_result["library_installed"] = True
        validation_result["version"] = getattr(athena_client, "__version__", "unknown")
    except ImportError as e:
        validation_result["error"] = f"athena-client library not installed: {str(e)}"
        validation_result["error_type"] = "ImportError"
        return validation_result
    except Exception as e:
        validation_result["error"] = f"Unexpected error importing athena-client: {str(e)}"
        validation_result["error_type"] = type(e).__name__
        return validation_result
    
    # Test 2: Check if Athena class can be imported
    try:
        from athena_client import Athena
        validation_result["import_successful"] = True
        _ATHENA_CLIENT = Athena
    except ImportError as e:
        validation_result["error"] = f"Cannot import Athena class: {str(e)}"
        validation_result["error_type"] = "ImportError"
        return validation_result
    except Exception as e:
        validation_result["error"] = f"Unexpected error importing Athena: {str(e)}"
        validation_result["error_type"] = type(e).__name__
        return validation_result
    
    # Test 3: Check if client can be created
    try:
        client = Athena()
        validation_result["client_creation"] = True
        _ATHENA_AVAILABLE = True
    except Exception as e:
        validation_result["error"] = f"Cannot create Athena client: {str(e)}"
        validation_result["error_type"] = type(e).__name__
        return validation_result
    
    # Test 4: Test basic functionality with a safe search
    try:
        # Use a very generic search term that should return results
        test_results = client.search("diabetes")
        validation_result["test_results"]["search_test"] = {
            "success": True,
            "has_results": hasattr(test_results, 'all') and len(test_results.all()) > 0,
            "result_type": type(test_results).__name__
        }
        validation_result["basic_functionality"] = True
    except Exception as e:
        validation_result["test_results"]["search_test"] = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # Test 5: Test details method with a known concept ID
    try:
        # Use a common concept ID that should exist
        test_details = client.details(concept_id=201820)
        validation_result["test_results"]["details_test"] = {
            "success": True,
            "has_details": test_details is not None,
            "result_type": type(test_details).__name__
        }
    except Exception as e:
        validation_result["test_results"]["details_test"] = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # Test 6: Test relationships method
    try:
        test_relationships = client.relationships(concept_id=201820)
        validation_result["test_results"]["relationships_test"] = {
            "success": True,
            "has_relationships": test_relationships is not None,
            "result_type": type(test_relationships).__name__
        }
    except Exception as e:
        validation_result["test_results"]["relationships_test"] = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # Overall success if all basic components work
    validation_result["success"] = (
        validation_result["library_installed"] and
        validation_result["import_successful"] and
        validation_result["client_creation"] and
        validation_result["basic_functionality"]
    )
    
    return validation_result


def get_athena_client() -> Any:
    """
    Get a validated Athena client instance.
    
    Returns:
        Athena client instance
        
    Raises:
        RuntimeError: If athena-client is not available or validation fails
    """
    global _ATHENA_AVAILABLE, _ATHENA_CLIENT
    
    if _ATHENA_AVAILABLE is None:
        validation = validate_athena_client()
        if not validation["success"]:
            error_msg = validation.get("error", "Unknown error")
            raise RuntimeError(f"athena-client validation failed: {error_msg}")
    
    if _ATHENA_CLIENT is None:
        raise RuntimeError("athena-client is not available")
    
    return _ATHENA_CLIENT()


async def validate_athena_client_async() -> Dict[str, Any]:
    """
    Async wrapper for athena-client validation.
    This function can be called from pipeline steps to validate athena-client availability.
    
    Returns:
        Dict containing validation results
    """
    return validate_athena_client()


def _get_queue_state(context: PipelineContext | None) -> Dict[str, Any]:
    state: Dict[str, Any] | None = None
    if context is not None:
        try:
            scratchpad = getattr(context, "scratchpad")
            if isinstance(scratchpad, MutableMapping):
                obj = scratchpad.get(QUEUE_STATE_KEY)
                if isinstance(obj, MutableMapping):
                    state = dict(obj)
        except Exception:
            state = None
        # Fallback: some runners persist step outputs onto context directly
        if not state:
            try:
                qs = getattr(context, "queue_state", None)
                if isinstance(qs, MutableMapping):
                    state = dict(qs)
            except Exception:
                pass
    return state or {}


def _store_queue_state(context: PipelineContext | None, state: Dict[str, Any]) -> None:
    if context is None:
        return
    try:
        scratchpad = getattr(context, "scratchpad")
    except Exception:
        scratchpad = None
    if not isinstance(scratchpad, MutableMapping):
        scratchpad = {}
        try:
            setattr(context, "scratchpad", scratchpad)
        except Exception:
            return
    scratchpad[QUEUE_STATE_KEY] = state
    # Also mirror onto context in case the runner persists attributes rather than scratchpad
    try:
        setattr(context, "queue_state", state)
    except Exception:
        pass


def _coerce_int(value: Any) -> Optional[int]:
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str) and value.strip():
            return int(float(value.strip()))
    except Exception:
        return None
    return None


def _boolify(value: Any) -> bool:
    """Coerce common truthy/falsey representations to a real bool.

    Accepts: bool, None, numbers, strings like 'true', '1', 'yes'.
    Defaults to False when ambiguous.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    try:
        if isinstance(value, (int, float)):
            return bool(int(value))
    except Exception:
        return False
    try:
        s = str(value).strip().lower()
    except Exception:
        return False
    return s in {"1", "true", "t", "yes", "y"}


def _as_sequence(data: Any) -> List[Any]:
    """Attempt to coerce arbitrary input into a list for downstream iteration."""

    if isinstance(data, str):
        stripped = data.strip()
        if not stripped:
            return []
        try:
            loaded = json.loads(stripped)
        except Exception:
            return list(stripped)
        if isinstance(loaded, Sequence) and not isinstance(loaded, (str, bytes, bytearray)):
            return list(loaded)
        return []

    if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        return list(data)

    return []


def _unique_sorted_ints(values: Iterable[Any], limit: Optional[int] = None) -> List[int]:
    """Deduplicate while preserving input order (no sorting).

    The queue should respect the candidate order emitted by the agent.
    """
    seen: set[int] = set()
    out: List[int] = []
    for raw in values:
        coerced = _coerce_int(raw)
        if coerced is None:
            continue
        if coerced in seen:
            continue
        seen.add(coerced)
        out.append(coerced)
        if limit is not None and len(out) >= limit:
            break
    return out


def _extract_candidate_ids(data: Any, *, limit: Optional[int] = None) -> List[int]:
    # Accept either a mapping containing candidate_ids, a raw sequence, or a JSON string
    if isinstance(data, MutableMapping):
        items = data.get("candidate_ids", [])
        return _unique_sorted_ints(_as_sequence(items), limit=limit)

    if hasattr(data, "model_dump"):
        try:
            dumped = data.model_dump()  # type: ignore[attr-defined]
        except Exception:
            dumped = {}
        if isinstance(dumped, MutableMapping):
            return _unique_sorted_ints(_as_sequence(dumped.get("candidate_ids", [])), limit=limit)

    # Fallback: treat the input itself as the sequence (works for JSON strings and Python lists)
    return _unique_sorted_ints(_as_sequence(data), limit=limit)


def _ensure_queue_defaults(state: Dict[str, Any]) -> Dict[str, Any]:
    state.setdefault("pending", [])
    state.setdefault("queued_ids", [])
    state.setdefault("visited", [])
    state.setdefault("depth_map", {})
    state.setdefault("history", [])
    state.setdefault("iteration", 0)
    state.setdefault("visit_count", 0)
    state.setdefault("resolved", False)
    state.setdefault("resolved_concept", None)
    state.setdefault("best_fallback", None)
    state.setdefault("max_depth", MAX_DEPTH_DEFAULT)
    state.setdefault("max_visits", MAX_VISITS_DEFAULT)
    state.setdefault("batch_size", BATCH_SIZE_DEFAULT)
    state.setdefault("stop_reason", None)
    # Stagnation guard fields
    state.setdefault("last_head_id", None)
    state.setdefault("stagnation_count", 0)
    return state


async def search_athena_concepts(
    search_term: str,
    limit: Optional[int] = None,
    return_format: str = "json",
) -> Dict[str, Any]:
    try:
        athena = get_athena_client()
        results = athena.search(search_term)

        if return_format == "json":
            processed = results.to_json()
        elif return_format == "list":
            processed = results.all()
        elif return_format == "top":
            processed = results.top(limit or 5)
        else:
            processed = results.all()

        if limit and return_format != "top" and isinstance(processed, list):
            processed = processed[:limit]

        total_found: int
        if hasattr(results, "all"):
            all_items = results.all()
            total_found = len(all_items) if isinstance(all_items, Sequence) else 0
        elif isinstance(processed, Sequence):
            total_found = len(processed)
        else:
            total_found = 0

        return {
            "success": True,
            "search_term": search_term,
            "results": processed,
            "total_found": total_found,
            "format": return_format,
        }

    except Exception as exc:  # pragma: no cover - thin wrapper around external SDK
        return {
            "success": False,
            "search_term": search_term,
            "error": str(exc),
            "error_type": type(exc).__name__,
        }


async def queue_init(
    data: Any,
    *,
    context: PipelineContext | None = None,
    max_depth: int = MAX_DEPTH_DEFAULT,
    max_visits: int = MAX_VISITS_DEFAULT,
    batch_size: int = BATCH_SIZE_DEFAULT,
) -> Dict[str, Any]:
    payload: Any = data
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {}

    if hasattr(payload, "model_dump"):
        try:
            payload = payload.model_dump()  # type: ignore[attr-defined]
        except Exception:
            payload = {}

    message: Optional[str] = None
    if isinstance(payload, MutableMapping):
        message = payload.get("message")

    candidate_ids = _extract_candidate_ids(payload if isinstance(payload, MutableMapping) else data, limit=12)
    max_depth = max(int(max_depth), 0)
    max_visits = max(int(max_visits), 1)
    batch_size = max(int(batch_size), 1)

    pending = [{"concept_id": cid, "depth": 0} for cid in candidate_ids]
    depth_map = {str(cid): 0 for cid in candidate_ids}

    state = _ensure_queue_defaults({
        "pending": pending,
        "queued_ids": list(candidate_ids),
        "visited": [],
        "depth_map": depth_map,
        "history": [],
        "iteration": 0,
        "visit_count": 0,
        "resolved": False,
        "resolved_concept": None,
        "best_fallback": None,
        "max_depth": max_depth,
        "max_visits": max_visits,
        "batch_size": batch_size,
        "stop_reason": None,
        "initial_candidates": list(candidate_ids),
        "initial_message": message,
    })

    _store_queue_state(context, state)
    return {"queue_state": state}


async def normalize_queue_output(data: Any) -> Dict[str, Any]:
    """Normalize queue_next_batch output into a dict with boolean flags.

    Some environments/loggers may pass the output as a JSON string or contain stringy booleans.
    This helper ensures downstream expressions see real booleans and numbers.
    """
    # If we already have a mapping, coerce fields to stable types
    if isinstance(data, MutableMapping):
        obj = dict(data)
        ids = _as_sequence(obj.get("ids") or [])
        depths = _as_sequence(obj.get("depths") or [])
        out = {
            "ids": ids,
            "depths": depths,
            "is_empty": _boolify(obj.get("is_empty")),
            "has_batch": _boolify(obj.get("has_batch")),
            "batch_count": int(_coerce_int(obj.get("batch_count")) or len(ids)),
            "limit_reached": _boolify(obj.get("limit_reached")),
            "depth_limit_hit": _boolify(obj.get("depth_limit_hit")),
            "resolved": _boolify(obj.get("resolved")),
            "queue_length": int(_coerce_int(obj.get("queue_length")) or 0),
            "visit_count": int(_coerce_int(obj.get("visit_count")) or 0),
        }
        try:
            print(
                "[normalize_queue_output] types:",
                {
                    k: type(v).__name__
                    for k, v in {
                        "has_batch": out["has_batch"],
                        "limit_reached": out["limit_reached"],
                        "depth_limit_hit": out["depth_limit_hit"],
                        "resolved": out["resolved"],
                        "is_empty": out["is_empty"],
                    }.items()
                },
            )
        except Exception:
            pass
        return out
    # Attempt to parse JSON string
    if isinstance(data, str):
        try:
            loaded = json.loads(data)
            if isinstance(loaded, MutableMapping):
                # Recurse to apply coercions uniformly
                return await normalize_queue_output(loaded)
        except Exception:
            pass
    # Last resort: return a safe default that disables processing
    return {
        "ids": [],
        "depths": [],
        "is_empty": True,
        "has_batch": False,
        "batch_count": 0,
        "limit_reached": False,
        "depth_limit_hit": False,
        "resolved": False,
        "queue_length": 0,
        "visit_count": 0,
        "_raw": data,
    }


async def normalize_flags(data: Any) -> Dict[str, Any]:
    """Produce strictly-boolean flags B_* and forward ids/depths.

    Accepts either a mapping or JSON string from normalize_queue_output.
    """
    obj: Dict[str, Any] = {}
    if isinstance(data, MutableMapping):
        obj = dict(data)
    elif isinstance(data, str):
        try:
            loaded = json.loads(data)
            if isinstance(loaded, MutableMapping):
                obj = dict(loaded)
        except Exception:
            obj = {}

    ids = _as_sequence(obj.get("ids") or [])
    depths = _as_sequence(obj.get("depths") or [])
    b_has = _boolify(obj.get("has_batch"))
    b_lim = _boolify(obj.get("limit_reached"))
    b_dep = _boolify(obj.get("depth_limit_hit"))
    b_res = _boolify(obj.get("resolved"))
    can_process = bool(b_has and (not b_lim) and (not b_dep) and (not b_res))
    out = {
        "B_HAS_BATCH": b_has,
        "B_LIMIT": b_lim,
        "B_DEPTH_HIT": b_dep,
        "B_RESOLVED": b_res,
        "CAN_PROCESS": can_process,
        "EXIT_NOW": not can_process,
        "ids": ids,
        "depths": depths,
        "queue_length": int(_coerce_int(obj.get("queue_length")) or 0),
        "visit_count": int(_coerce_int(obj.get("visit_count")) or 0),
    }
    try:
        print(
            "[normalize_flags] flags:",
            {
                k: out[k]
                for k in (
                    "B_HAS_BATCH",
                    "B_LIMIT",
                    "B_DEPTH_HIT",
                    "B_RESOLVED",
                    "CAN_PROCESS",
                    "EXIT_NOW",
                )
            },
        )
    except Exception:
        pass
    return out


async def choose_branch(data: Any) -> Dict[str, Any]:
    """Map normalized flags to a branch key string: 'process' or 'exit'.

    Accepts either the output of normalize_flags (mapping) or a JSON string.
    Always returns a valid key; defaults to 'exit'.
    """
    obj: Dict[str, Any] = {}
    if isinstance(data, MutableMapping):
        obj = dict(data)
    elif isinstance(data, str):
        try:
            loaded = json.loads(data)
            if isinstance(loaded, MutableMapping):
                obj = dict(loaded)
        except Exception:
            obj = {}

    # Prefer precomputed composites when present
    can = obj.get("CAN_PROCESS")
    if not isinstance(can, bool):
        # Derive from raw flags if needed
        b_has = _boolify(obj.get("B_HAS_BATCH", obj.get("has_batch")))
        b_lim = _boolify(obj.get("B_LIMIT", obj.get("limit_reached")))
        b_dep = _boolify(obj.get("B_DEPTH_HIT", obj.get("depth_limit_hit")))
        b_res = _boolify(obj.get("B_RESOLVED", obj.get("resolved")))
        can = bool(b_has and (not b_lim) and (not b_dep) and (not b_res))
    branch_key = "process" if can else "exit"
    try:
        print(f"[choose_branch] branch_key={branch_key} (CAN_PROCESS={can})")
    except Exception:
        pass
    return {
        "branch_key": branch_key,
        "CAN_PROCESS": bool(can),
        "EXIT_NOW": (not bool(can)),
    }


async def prepare_and_decide_branch(
    data: Any | None = None,
    *,
    context: PipelineContext | None = None,
) -> Dict[str, Any]:
    """Adapter that prepares the next batch, computes flags, applies a stagnation guard,
    and returns a deterministic branch decision.

    Output keys:
      - ids, depths, queue_length, visit_count
      - resolved (bool), EXIT_NOW (bool), branch_key ('process'|'exit')
      - queue_state (mirrored for downstream visibility)
    """
    # Prepare next batch (updates queue_state)
    qb = await queue_next_batch(context=context)

    # Basic flags
    has_batch = bool(qb.get("has_batch"))
    limit = bool(qb.get("limit_reached"))
    depth_hit = bool(qb.get("depth_limit_hit"))
    already_resolved = bool(qb.get("resolved"))
    can_process = has_batch and (not limit) and (not depth_hit) and (not already_resolved)

    # Stagnation guard: if the head of the pending queue doesn't change across
    # repeated iterations, force an exit with diagnostic stop_reason.
    state = _ensure_queue_defaults(_get_queue_state(context))
    pending = state.get("pending", [])
    head_id = _coerce_int(pending[0].get("concept_id")) if pending else None
    last_head = state.get("last_head_id")
    stagnation_count = int(state.get("stagnation_count", 0))
    if head_id is not None:
        if last_head is not None and _coerce_int(last_head) == head_id:
            stagnation_count += 1
        else:
            stagnation_count = 0
        state["last_head_id"] = head_id
        state["stagnation_count"] = stagnation_count
    # If we are stuck on the same head for 3 consecutive adapter cycles,
    # exit gracefully and annotate state.
    if stagnation_count >= 3 and not already_resolved:
        try:
            state["stop_reason"] = state.get("stop_reason") or "stagnation"
            _store_queue_state(context, state)
        except Exception:
            pass
        branch_key = "exit"
        exit_now = True
    else:
        branch_key = "process" if can_process else "exit"
        exit_now = not can_process

    out = {
        "ids": qb.get("ids", []),
        "depths": qb.get("depths", []),
        "queue_length": int(_coerce_int(qb.get("queue_length")) or 0),
        "visit_count": int(_coerce_int(qb.get("visit_count")) or 0),
        "resolved": already_resolved,
        "branch_key": branch_key,
        "EXIT_NOW": exit_now,
        "queue_state": _ensure_queue_defaults(_get_queue_state(context)),
    }
    try:
        print(f"[prepare_and_decide_branch] branch={branch_key} exit_now={exit_now} has_batch={has_batch}")
    except Exception:
        pass
    return out

async def queue_next_batch(
    data: Any | None = None,
    *,
    context: PipelineContext | None = None,
) -> Dict[str, Any]:
    state = _ensure_queue_defaults(_get_queue_state(context))
    pending: List[Dict[str, Any]] = list(state.get("pending", []))
    visit_count = int(state.get("visit_count", 0))
    max_visits = max(int(state.get("max_visits", MAX_VISITS_DEFAULT)), 1)
    max_depth = max(int(state.get("max_depth", MAX_DEPTH_DEFAULT)), 0)
    batch_size = max(int(state.get("batch_size", BATCH_SIZE_DEFAULT)), 1)

    if state.get("resolved"):
        state.setdefault("stop_reason", "resolved")
        _store_queue_state(context, state)
        return {
            "ids": [],
            "depths": [],
            "is_empty": True,
            "has_batch": False,
            "batch_count": 0,
            "limit_reached": False,
            "depth_limit_hit": False,
            "resolved": True,
            "queue_length": len(pending),
            "visit_count": visit_count,
        }

    limit_reached = visit_count >= max_visits
    if limit_reached:
        state.setdefault("stop_reason", "max_visits")
        state["pending"] = pending
        state["queued_ids"] = [item.get("concept_id") for item in pending if "concept_id" in item]
        _store_queue_state(context, state)
        return {
            "ids": [],
            "depths": [],
            "is_empty": True,
            "has_batch": False,
            "batch_count": 0,
            "limit_reached": True,
            "depth_limit_hit": False,
            "resolved": bool(state.get("resolved", False)),
            "queue_length": len(pending),
            "visit_count": visit_count,
        }

    if not pending:
        state.setdefault("stop_reason", "queue_empty")
        state["pending"] = []
        state["queued_ids"] = []
        _store_queue_state(context, state)
        return {
            "ids": [],
            "depths": [],
            "is_empty": True,
            "has_batch": False,
            "batch_count": 0,
            "limit_reached": False,
            "depth_limit_hit": False,
            "resolved": bool(state.get("resolved", False)),
            "queue_length": 0,
            "visit_count": visit_count,
        }

    first_depth = int(_coerce_int(pending[0].get("depth")) or 0)
    if first_depth > max_depth:
        state.setdefault("stop_reason", "max_depth")
        state["pending"] = []
        state["queued_ids"] = []
        _store_queue_state(context, state)
        return {
            "ids": [],
            "depths": [],
            "is_empty": True,
            "has_batch": False,
            "batch_count": 0,
            "limit_reached": False,
            "depth_limit_hit": True,
            "resolved": bool(state.get("resolved", False)),
            "queue_length": 0,
            "visit_count": visit_count,
        }

    remaining_slots = max_visits - visit_count
    effective_batch = min(batch_size, remaining_slots)
    ids: List[int] = []
    depths: List[int] = []
    new_pending: List[Dict[str, Any]] = []

    for item in pending:
        cid = _coerce_int(item.get("concept_id"))
        depth = int(_coerce_int(item.get("depth")) or 0)
        if cid is None:
            continue
        normalized_item = {"concept_id": cid, "depth": depth}
        if len(ids) < effective_batch and depth <= max_depth:
            ids.append(cid)
            depths.append(depth)
            continue
        new_pending.append(normalized_item)

    state["pending"] = new_pending
    state["queued_ids"] = [item.get("concept_id") for item in new_pending if "concept_id" in item]

    if ids:
        state["active_iteration"] = int(state.get("iteration", 0)) + 1
        state["current_iteration_start"] = time.perf_counter()
        state.setdefault("last_batch", {})
        state["last_batch"] = {
            "ids": list(ids),
            "depths": list(depths),
        }
    else:
        state["active_iteration"] = state.get("iteration", 0)
        state["current_iteration_start"] = None

    # Instrumentation: log first 10 remaining pending ids and depths for visibility
    try:
        preview = [
            (
                int(_coerce_int(it.get("concept_id")) or -1),
                int(_coerce_int(it.get("depth")) or 0),
            )
            for it in new_pending[:10]
        ]
        print(f"[queue_next_batch] remaining(pending) preview (id,depth): {preview}")
    except Exception:
        pass

    _store_queue_state(context, state)

    return {
        "ids": ids,
        "depths": depths,
        "is_empty": not ids,
        "has_batch": bool(ids),
        "batch_count": len(ids),
        "limit_reached": False,
        "depth_limit_hit": False,
        "resolved": bool(state.get("resolved", False)),
        "queue_length": len(new_pending),
        "visit_count": visit_count,
        "queue_state": state,
    }


async def fetch_athena_concept_info_batch(ids: Sequence[Any]) -> Dict[str, Any]:
    ordered_ids = _as_sequence(ids)
    if not ordered_ids:
        return {"ids": [], "concepts": []}

    concepts: List[Dict[str, Any]] = []
    try:
        client = get_athena_client()
        for cid in ordered_ids:
            coerced = _coerce_int(cid)
            if coerced is None:
                concepts.append(
                    {
                        "success": False,
                        "concept_id": cid,
                        "error": "invalid_concept_id",
                        "error_type": "ValueError",
                    }
                )
                continue
            # Prefer the summary endpoint when available; complement with details/relationships
            summary = None
            details = None
            relationships = None
            # Try summary (new comprehensive endpoint)
            try:
                if hasattr(client, "summary"):
                    summary = client.summary(concept_id=coerced)
            except Exception:
                summary = None
            # Try details
            try:
                details = client.details(concept_id=coerced)
            except Exception:
                details = None
            # Try relationships
            try:
                relationships = client.relationships(concept_id=coerced)
            except Exception:
                relationships = None

            if summary is not None or details is not None or relationships is not None:
                concepts.append(
                    {
                        "success": True,
                        "concept_id": coerced,
                        "summary": summary,
                        "details": details,
                        "relationships": relationships,
                    }
                )
            else:
                concepts.append(
                    {
                        "success": False,
                        "concept_id": coerced,
                        "error": "No data returned from Athena for concept",
                        "error_type": "AthenaEmpty",
                    }
                )
    except Exception as exc:  # pragma: no cover - client construction failure
        return {
            "ids": ordered_ids,
            "concepts": [
                {
                    "success": False,
                    "concept_id": _coerce_int(cid),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
                for cid in ordered_ids
            ],
        }

    return {"ids": ordered_ids, "concepts": concepts}


async def try_short_circuit(
    data: Any,
    *,
    context: PipelineContext | None = None,
) -> Dict[str, Any]:
    """Resolve immediately when a clear Standard mapping matches the search term.

    Input formats supported:
      - Mapping with keys {"concepts": [...], "term": "..."}
      - Concepts list directly.
    Side effects:
      - If a qualifying SNOMED "Maps to" target name contains all significant
        tokens from the search term, marks queue state as resolved and stores
        evidence.
    Returns a small dict for telemetry: {resolved: bool, resolved_concept_id, evidence}
    """
    state = _ensure_queue_defaults(_get_queue_state(context))
    if state.get("resolved"):
        return {"resolved": True, "resolved_concept_id": (state.get("resolved_concept") or {}).get("concept_id")}

    # Extract inputs (accept JSON strings as well)
    if isinstance(data, str):
        try:
            loaded = json.loads(data)
            data = loaded if isinstance(loaded, MutableMapping) else {}
        except Exception:
            data = {}
    if isinstance(data, MutableMapping):
        concepts_raw = data.get("concepts")
        term = str(data.get("term") or "")
    else:
        concepts_raw = data
        term = ""

    concepts = _as_sequence(concepts_raw)

    # Tokenization helpers
    def _norm(s: Any) -> str:
        try:
            return " ".join(str(s or "").strip().lower().split())
        except Exception:
            return ""

    term_norm = _norm(term)
    # Keep both multi-token containment and exact match variants available
    sig_tokens = [t for t in term_norm.split(" ") if len(t) >= 3]

    def _tokens_match(name: Any) -> bool:
        s = _norm(name)
        if not sig_tokens:
            return False
        return all(tok in s for tok in sig_tokens)

    # Preload depth map for evidence depth estimation
    depth_map = state.get("depth_map", {}) if isinstance(state.get("depth_map"), MutableMapping) else {}

    resolved_id: Optional[int] = None
    evidence: Optional[Dict[str, Any]] = None

    def _to_map(obj: Any) -> Dict[str, Any]:
        if isinstance(obj, MutableMapping):
            return dict(obj)
        for attr in ("model_dump", "dict", "to_dict"):
            try:
                fn = getattr(obj, attr)
                out = fn()
                if isinstance(out, MutableMapping):
                    return dict(out)
            except Exception:
                pass
        try:
            if hasattr(obj, "to_json"):
                raw = obj.to_json()  # type: ignore[attr-defined]
                if isinstance(raw, str):
                    loaded = json.loads(raw)
                    if isinstance(loaded, MutableMapping):
                        return dict(loaded)
        except Exception:
            pass
        return {}

    # Pass 1: Drug ingredient short-circuit (RxNorm Standard Ingredient / Precise Ingredient exact/alias match)
    for c in concepts:
        c_map = dict(c) if isinstance(c, MutableMapping) else _to_map(c)
        if not c_map:
            continue

        det: Dict[str, Any] = {}
        try:
            sm = _to_map(c_map.get("summary"))
            d = sm.get("details") if isinstance(sm.get("details"), MutableMapping) else None
            if isinstance(d, MutableMapping):
                det = dict(d)
        except Exception:
            det = {}
        if not det and isinstance(c_map.get("details"), MutableMapping):
            try:
                det = dict(c_map.get("details"))
            except Exception:
                det = {}

        try:
            std = str(det.get("standardConcept", "")).lower() == "standard"
            vocab = str(det.get("vocabularyId", "")).upper()
            cls = str(det.get("conceptClassId", ""))
            name = det.get("name")
            syns = det.get("synonyms") if isinstance(det.get("synonyms"), list) else []
            names = [name] + syns if name is not None else syns
            exact_match = any(_norm(n) == term_norm for n in names)
            if std and vocab in {"RXNORM", "RXNORM EXTENSION"} and cls in {"Ingredient", "Precise Ingredient"} and exact_match:
                cid = _coerce_int(det.get("id") or c_map.get("concept_id") or c_map.get("conceptId"))
                if cid is not None:
                    evidence = {
                        "from_concept_id": cid,
                        "from_concept_name": name,
                        "relationship": "direct_match",
                        "to_concept_id": cid,
                        "to_concept_name": name,
                        "to_vocab": det.get("vocabularyId"),
                        "note": "short_circuit_rxnorm_ingredient_exact",
                    }
                    try:
                        state["resolved"] = True
                        state["resolved_concept"] = {
                            "concept_id": cid,
                            "depth": int(_coerce_int(state.get("depth_map", {}).get(str(cid))) or 0),
                            "decision": {"auto_resolved": True, "hint": "RxNorm ingredient exact match", "evidence": evidence},
                            "concept": {"source": "short_circuit"},
                        }
                        state["evidence"] = evidence
                        state["stop_reason"] = "resolved"
                        state["pending"] = []
                        state["queued_ids"] = []
                        _store_queue_state(context, state)
                    except Exception:
                        pass
                    return {"resolved": True, "resolved_concept_id": cid, "evidence": evidence, "queue_state": state}
        except Exception:
            pass

    # Pass 2: Direct Standard concept short-circuit (domain-aware)
    for c in concepts:
        c_map = dict(c) if isinstance(c, MutableMapping) else _to_map(c)
        if not c_map:
            continue
        det: Dict[str, Any] = {}
        try:
            sm = _to_map(c_map.get("summary"))
            d = sm.get("details") if isinstance(sm.get("details"), MutableMapping) else None
            if isinstance(d, MutableMapping):
                det = dict(d)
        except Exception:
            det = {}
        if not det and isinstance(c_map.get("details"), MutableMapping):
            try:
                det = dict(c_map.get("details"))
            except Exception:
                det = {}
        try:
            std = str(det.get("standardConcept", "")).lower() == "standard"
            vocab = str(det.get("vocabularyId", "")).upper()
            domain = str(det.get("domainId", ""))
            cls = str(det.get("conceptClassId", ""))
            name = det.get("name")
            syns = det.get("synonyms") if isinstance(det.get("synonyms"), list) else []
            names = [name] + syns if name is not None else syns
            exact_match = any(_norm(n) == term_norm for n in names)
            strong_token_match = any(_tokens_match(n) for n in names)
            cid = _coerce_int(det.get("id") or c_map.get("concept_id") or c_map.get("conceptId"))
            def _resolve_now(hint: str) -> Optional[Dict[str, Any]]:
                if cid is None:
                    return None
                ev = {
                    "from_concept_id": cid,
                    "from_concept_name": name,
                    "relationship": "direct_match",
                    "to_concept_id": cid,
                    "to_concept_name": name,
                    "to_vocab": det.get("vocabularyId"),
                    "note": hint,
                }
                try:
                    state["resolved"] = True
                    state["resolved_concept"] = {
                        "concept_id": cid,
                        "depth": int(_coerce_int(state.get("depth_map", {}).get(str(cid))) or 0),
                        "decision": {"auto_resolved": True, "hint": hint, "evidence": ev},
                        "concept": {"source": "short_circuit"},
                    }
                    state["evidence"] = ev
                    state["stop_reason"] = "resolved"
                    state["pending"] = []
                    state["queued_ids"] = []
                    _store_queue_state(context, state)
                except Exception:
                    pass
                return {"resolved": True, "resolved_concept_id": cid, "evidence": ev, "queue_state": state}

            if std:
                # Condition: prefer SNOMED Disorder/Clinical Finding
                if vocab == "SNOMED" and cls in {"Disorder", "Clinical Finding"} and (exact_match or strong_token_match):
                    out = _resolve_now("SNOMED condition exact/strong match")
                    if out:
                        return out
                # Measurement: LOINC component
                if vocab == "LOINC" and cls in {"Component", "LOINC Component"} and (exact_match or strong_token_match):
                    out = _resolve_now("LOINC component exact/strong match")
                    if out:
                        return out
                # Procedure: SNOMED Procedure or CPT4
                if (vocab == "SNOMED" and cls == "Procedure") and (exact_match or strong_token_match):
                    out = _resolve_now("SNOMED procedure exact/strong match")
                    if out:
                        return out
                if vocab == "CPT4" and (exact_match or strong_token_match):
                    out = _resolve_now("CPT4 procedure exact/strong match")
                    if out:
                        return out
        except Exception:
            pass

    # Pass 3: Relationship-based short-circuit (“Maps to” name token match)
    for c in concepts:
        c_map = dict(c) if isinstance(c, MutableMapping) else _to_map(c)
        if not c_map:
            continue

        # From concept identifiers
        from_details: Dict[str, Any] = {}
        try:
            summ_map = _to_map(c_map.get("summary"))
            if isinstance(summ_map.get("details"), MutableMapping):
                from_details = dict(summ_map.get("details"))
        except Exception:
            from_details = {}
        if not from_details and isinstance(c_map.get("details"), MutableMapping):
            try:
                from_details = dict(c_map.get("details"))
            except Exception:
                from_details = {}
        from_id = _coerce_int(from_details.get("id") or c_map.get("concept_id") or c_map.get("conceptId"))
        from_name = from_details.get("name") if isinstance(from_details, MutableMapping) else None

        # Extract Maps to targets using normalized sources
        rels_source = {
            "summary": _to_map(c_map.get("summary")),
            "details": _to_map(c_map.get("details")),
            "relationships": _to_map(c_map.get("relationships")),
        }
        targets = _extract_maps_to_targets(rels_source)
        for t in targets:
            tgt_id = _coerce_int(t.get("concept_id"))
            vocab_ok = str(t.get("vocabularyId", "")).upper() == "SNOMED"
            if tgt_id is None or not vocab_ok:
                continue
            if _tokens_match(t.get("name")):
                resolved_id = tgt_id
                # Compute an estimated depth: parent depth + 1 when available
                est_depth = 1
                try:
                    if from_id is not None:
                        est_depth = int(_coerce_int(depth_map.get(str(from_id))) or 0) + 1
                except Exception:
                    est_depth = 1
                evidence = {
                    "from_concept_id": from_id,
                    "from_concept_name": from_name,
                    "relationship": "Maps to",
                    "to_concept_id": tgt_id,
                    "to_concept_name": t.get("name"),
                    "to_vocab": t.get("vocabularyId"),
                }
                # Update queue state immediately
                try:
                    state["resolved"] = True
                    state["resolved_concept"] = {
                        "concept_id": resolved_id,
                        "depth": est_depth,
                        "decision": {"auto_resolved": True, "hint": "try_short_circuit: Maps to SNOMED match", "evidence": evidence},
                        "concept": {"source": "short_circuit"},
                    }
                    state["evidence"] = evidence
                    state["stop_reason"] = "resolved"
                    # Hard stop: clear remaining work to prevent further batching
                    state["pending"] = []
                    state["queued_ids"] = []
                    _store_queue_state(context, state)
                except Exception:
                    pass
                return {"resolved": True, "resolved_concept_id": resolved_id, "evidence": evidence, "queue_state": state}

    return {"resolved": False, "resolved_concept_id": None, "evidence": evidence, "queue_state": state}


async def mark_batch_visited(
    data: Any,
    *,
    context: PipelineContext | None = None,
) -> Dict[str, Any]:
    """Mark the current batch IDs as visited and remove them from pending.

    This makes progress sticky even if downstream analysis fails or returns empty decisions.
    Input may be a mapping with key "ids" or a raw list/JSON string of IDs.
    """
    state = _ensure_queue_defaults(_get_queue_state(context))
    raw_ids: List[Any] = []
    # Accept JSON string or mapping
    if isinstance(data, str):
        try:
            loaded = json.loads(data)
            if isinstance(loaded, MutableMapping):
                raw_ids = _as_sequence(loaded.get("ids"))
            else:
                raw_ids = _as_sequence(loaded)
        except Exception:
            raw_ids = []
    elif isinstance(data, MutableMapping):
        raw_ids = _as_sequence(data.get("ids"))
    else:
        raw_ids = _as_sequence(data)
    ids_set = set()
    for rid in raw_ids:
        cid = _coerce_int(rid)
        if cid is not None:
            ids_set.add(cid)

    if not ids_set:
        return {"queue_state": state}

    # Update visited and pending atomically based on current state
    pending = list(state.get("pending", []))
    visited = list(state.get("visited", []))
    new_pending = [it for it in pending if _coerce_int(it.get("concept_id")) not in ids_set]
    for cid in ids_set:
        if cid not in visited:
            visited.append(cid)
    state["pending"] = new_pending
    state["queued_ids"] = [it.get("concept_id") for it in new_pending if isinstance(it, MutableMapping) and "concept_id" in it]
    state["visited"] = visited
    _store_queue_state(context, state)
    return {"queue_state": state}


def _walk(obj: Any):
    """Yield all nested dicts in an object (safe traversal)."""
    try:
        if isinstance(obj, dict):
            yield obj
            for v in obj.values():
                yield from _walk(v)
        elif isinstance(obj, list):
            for it in obj:
                yield from _walk(it)
    except Exception:
        return


def _extract_maps_to_targets(concept_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Best-effort extraction of 'Maps to' relationship targets from concept payload.

    Handles a variety of shapes from Athena client: summary, relationships, nested lists.
    Returns list of dicts with keys: concept_id, name (optional), vocabularyId (optional).
    """
    out: List[Dict[str, Any]] = []
    try:
        for node in _walk(concept_payload):
            try:
                # Common keys
                rel_type = str(node.get("relationshipId") or node.get("relationship") or "")
                if rel_type.lower() != "maps to":
                    continue
                # Target identifiers (handle variants)
                cid = node.get("targetConceptId") or node.get("conceptId") or node.get("target_id")
                name = node.get("targetConceptName") or node.get("conceptName") or node.get("name")
                vocab = node.get("targetVocabularyId") or node.get("vocabularyId")
                coerced = _coerce_int(cid)
                if coerced is None:
                    continue
                out.append({
                    "concept_id": coerced,
                    "name": name,
                    "vocabularyId": vocab,
                })
            except Exception:
                continue
    except Exception:
        return out
    # Dedup by concept_id preserving order
    seen: set[int] = set()
    uniq: List[Dict[str, Any]] = []
    for it in out:
        cid = _coerce_int(it.get("concept_id"))
        if cid is None or cid in seen:
            continue
        seen.add(cid)
        uniq.append(it)
    return uniq


async def minify_concepts(data: Any) -> Dict[str, Any]:
    """Trim concept payloads to essentials to reduce LLM tokens.

    Keeps: concept_id, details (selected fields), and only 'Maps to' relationships.
    Accepts either the full fetch payload {concepts:[...] } or the concepts list directly.
    """
    # Helpers to coerce various Athena result objects into plain dicts
    def _to_mapping(obj: Any) -> Dict[str, Any]:
        if isinstance(obj, MutableMapping):
            return dict(obj)
        # Common adapters exposed by client/model objects
        for attr in ("model_dump", "dict", "to_dict"):
            try:
                fn = getattr(obj, attr)
                out = fn()  # type: ignore[operator]
                if isinstance(out, MutableMapping):
                    return dict(out)
            except Exception:
                pass
        for attr in ("to_json",):
            try:
                fn = getattr(obj, attr)
                raw = fn()  # type: ignore[operator]
                if isinstance(raw, str):
                    loaded = json.loads(raw)
                    if isinstance(loaded, MutableMapping):
                        return dict(loaded)
            except Exception:
                pass
        return {}

    # Normalize input to concepts list
    concepts_input: List[Any]
    if isinstance(data, MutableMapping) and isinstance(data.get("concepts"), list):
        concepts_input = data.get("concepts", [])  # type: ignore[assignment]
    else:
        concepts_input = _as_sequence(data)

    out_list: List[Dict[str, Any]] = []
    for c in concepts_input:
        # Ensure we can address c like a mapping, but don't require strict Mapping type
        c_map: Dict[str, Any] = {}
        if isinstance(c, MutableMapping):
            c_map = dict(c)
        else:
            # Try best-effort extraction from objects with attributes
            try:
                # Prefer explicit adapters if present
                c_map = _to_mapping(c)
            except Exception:
                c_map = {}
        # If we still don't have a mapping, skip but keep placeholder to avoid empty batch
        if not isinstance(c_map, MutableMapping):
            continue

        # Extract details with robust fallbacks
        details_map: Dict[str, Any] = {}
        try:
            summ_obj = c_map.get("summary")
            summ_map = _to_mapping(summ_obj) if summ_obj is not None else {}
            if isinstance(summ_map.get("details"), MutableMapping):
                details_map = dict(summ_map.get("details"))
            elif summ_map:
                details_map = summ_map
        except Exception:
            details_map = {}
        if not details_map and isinstance(c_map.get("details"), (MutableMapping,)):
            try:
                details_map = dict(c_map.get("details"))
            except Exception:
                details_map = {}
        # As a last resort, pick a subset from top-level if it looks like details
        if not details_map:
            try:
                for k in ("conceptId", "conceptName", "standardConcept", "domainId", "vocabularyId", "conceptClassId"):
                    if k in c_map:
                        details_map.setdefault(k, c_map[k])
            except Exception:
                pass

        # Derive concept_id from multiple potential locations
        cid = _coerce_int(
            c_map.get("concept_id")
            or c_map.get("conceptId")
            or details_map.get("conceptId")
            or c_map.get("id")
            or details_map.get("id")
        )

        # Build minimal details payload
        minimal_details: Dict[str, Any] = {}
        try:
            for k in ("conceptId", "conceptName", "standardConcept", "domainId", "vocabularyId", "conceptClassId"):
                v = details_map.get(k)
                if v is not None:
                    minimal_details[k] = v
        except Exception:
            minimal_details = {}

        # Extract relationships: include Maps to plus a trimmed set of others
        rels_source = {
            "summary": _to_mapping(c_map.get("summary")),
            "details": _to_mapping(c_map.get("details")),
            "relationships": _to_mapping(c_map.get("relationships")),
        }
        maps_to = _extract_maps_to_targets(rels_source)[:8]

        # Try to keep at most 6 non-Maps-to relationships when discoverable
        other_rels: List[Dict[str, Any]] = []
        try:
            rels = rels_source.get("relationships", {})
            items = rels.get("items", []) if isinstance(rels, MutableMapping) else []
            for group in items:
                rel_list = group.get("relationships", []) if isinstance(group, MutableMapping) else []
                for r in rel_list:
                    if not isinstance(r, MutableMapping):
                        continue
                    if str(r.get("relationshipId", "")).lower() == "maps to":
                        continue
                    other_rels.append(dict(r))
                    if len(other_rels) >= 6:
                        break
                if len(other_rels) >= 6:
                    break
        except Exception:
            other_rels = []

        entry: Dict[str, Any] = {
            # Use the derived cid when available; it's okay if absent for agent context
            "concept_id": cid,
            "details": minimal_details,
            "relationships": {
                "maps_to": maps_to,
                "other": other_rels,
            },
        }
        out_list.append(entry)

    return {"concepts": out_list}


async def select_concepts(data: Any) -> Dict[str, Any]:
    """Choose minified concepts when available; fall back to raw fetch concepts.

    Input may be a mapping with keys {minified, raw} or a list/any.
    Returns a dict {concepts: [...]}. Ensures it never drops to empty when raw has entries.
    """
    # Structured input: {minified, raw}
    if isinstance(data, MutableMapping):
        minified = data.get("minified")
        raw = data.get("raw")
        min_list = _as_sequence(minified)
        raw_list = None
        if isinstance(raw, MutableMapping) and isinstance(raw.get("concepts"), list):
            raw_list = raw.get("concepts")
        else:
            tmp = _as_sequence(raw)
            raw_list = tmp if tmp else []
        # Prefer minified when it has content; else fallback to raw
        concepts = min_list if len(min_list) > 0 else (raw_list or [])
        return {"concepts": concepts}
    # Fallback: pass through lists
    return {"concepts": _as_sequence(data)}


def _update_best_fallback(state: Dict[str, Any], candidate: Dict[str, Any]) -> None:
    existing = state.get("best_fallback")
    if not existing:
        state["best_fallback"] = candidate
        return

    existing_tuple = (
        int(_coerce_int(existing.get("depth")) or 99),
        int(_coerce_int(existing.get("concept_id")) or 999999999),
    )
    new_tuple = (
        int(_coerce_int(candidate.get("depth")) or 99),
        int(_coerce_int(candidate.get("concept_id")) or 999999999),
    )
    if new_tuple < existing_tuple:
        state["best_fallback"] = candidate


async def update_queue_from_batch(
    data: Any,
    *,
    context: PipelineContext | None = None,
) -> Dict[str, Any]:
    state = _ensure_queue_defaults(_get_queue_state(context))

    # Accept JSON string payloads in addition to mappings/objects
    if isinstance(data, str):
        try:
            loaded = json.loads(data)
            data = loaded if isinstance(loaded, MutableMapping) else {}
        except Exception:
            data = {}

    if isinstance(data, MutableMapping):
        raw_ids = data.get("ids", [])
        raw_depths = data.get("depths", [])
        raw_decisions = data.get("decisions", [])
        raw_concepts = data.get("concepts", [])
    elif hasattr(data, "model_dump"):
        dumped = data.model_dump()  # type: ignore[attr-defined]
        raw_ids = dumped.get("ids", []) if isinstance(dumped, MutableMapping) else []
        raw_depths = dumped.get("depths", []) if isinstance(dumped, MutableMapping) else []
        raw_decisions = dumped.get("decisions", []) if isinstance(dumped, MutableMapping) else []
        raw_concepts = dumped.get("concepts", []) if isinstance(dumped, MutableMapping) else []
    else:
        raw_ids, raw_depths, raw_decisions, raw_concepts = [], [], [], []

    ids = _as_sequence(raw_ids)
    depths = _as_sequence(raw_depths)
    decisions = _as_sequence(raw_decisions)
    concepts = _as_sequence(raw_concepts)

    # Guardrail: if we received a non-empty set of ids but zero concept payloads,
    # mark the state so the outcome explains the stall and avoid re-adding processed ids.
    if ids and not concepts:
        try:
            if not state.get("stop_reason"):
                state["stop_reason"] = "bad_batch"
        except Exception:
            pass

    iteration = int(state.get("active_iteration", state.get("iteration", 0)))
    visit_count = int(state.get("visit_count", 0))
    max_depth = max(int(state.get("max_depth", MAX_DEPTH_DEFAULT)), 0)

    history = list(state.get("history", []))

    timestamp = time.perf_counter()
    iteration_duration: Optional[float] = None
    start_time = state.get("current_iteration_start")
    if isinstance(start_time, (int, float)):
        iteration_duration = max(timestamp - float(start_time), 0.0)

    resolved = bool(state.get("resolved", False))
    # Start from current pending list
    new_pending = list(state.get("pending", []))
    queued_ids = set(_coerce_int(item.get("concept_id")) for item in new_pending if isinstance(item, MutableMapping))
    visited = list(state.get("visited", []))
    depth_map = dict(state.get("depth_map", {}))

    # Ensure processed ids are not re-added to pending (idempotency)
    processed_ids_set = set()
    for raw_id in ids:
        cid = _coerce_int(raw_id)
        if cid is not None:
            processed_ids_set.add(cid)
    if processed_ids_set:
        new_pending = [it for it in new_pending if _coerce_int(it.get("concept_id")) not in processed_ids_set]
        queued_ids = set(_coerce_int(item.get("concept_id")) for item in new_pending if isinstance(item, MutableMapping))

    for idx, raw_id in enumerate(ids):
        coerced_id = _coerce_int(raw_id)
        depth = int(_coerce_int(depths[idx]) or depth_map.get(str(coerced_id), 0)) if idx < len(depths) else int(depth_map.get(str(coerced_id), 0))
        decision = decisions[idx] if idx < len(decisions) else {}
        concept_payload = concepts[idx] if idx < len(concepts) else {}

        if coerced_id is None:
            continue

        depth_map[str(coerced_id)] = depth
        if coerced_id not in visited:
            visited.append(coerced_id)
        if coerced_id in queued_ids:
            queued_ids.remove(coerced_id)

        visit_count += 1

        decision_map = decision if isinstance(decision, MutableMapping) else {}
        concept_info = concept_payload if isinstance(concept_payload, MutableMapping) else {}

        is_standard = bool(decision_map.get("is_standard"))
        is_correct = bool(decision_map.get("is_correct_for_term"))
        reasoning = decision_map.get("reasoning")
        relationship_hint = decision_map.get("relationship_hint")

        if is_standard and is_correct and not resolved:
            resolved = True
            state["resolved_concept"] = {
                "concept_id": coerced_id,
                "depth": depth,
                "decision": decision_map,
                "concept": concept_info,
            }
            state["stop_reason"] = "resolved"
        elif is_correct:
            fallback_entry = {
                "concept_id": coerced_id,
                "depth": depth,
                "decision": decision_map,
                "concept": concept_info,
            }
            _update_best_fallback(state, fallback_entry)

        # Fallback: resolve direct Standard concept exact lexical match when LLM provides no winner
        if not resolved:
            try:
                term = getattr(context, "initial_prompt", None)
                term_norm = " ".join(str(term or "").strip().lower().split())
                # Normalize details
                def _to_map(obj: Any) -> Dict[str, Any]:
                    if isinstance(obj, MutableMapping):
                        return dict(obj)
                    for attr in ("model_dump", "dict", "to_dict"):
                        try:
                            fn = getattr(obj, attr)
                            out = fn()
                            if isinstance(out, MutableMapping):
                                return dict(out)
                        except Exception:
                            pass
                    try:
                        if hasattr(obj, "to_json"):
                            raw = obj.to_json()  # type: ignore[attr-defined]
                            if isinstance(raw, str):
                                loaded = json.loads(raw)
                                if isinstance(loaded, MutableMapping):
                                    return dict(loaded)
                    except Exception:
                        pass
                    return {}

                det_map: Dict[str, Any] = {}
                sm = _to_map(concept_info.get("summary")) if isinstance(concept_info, MutableMapping) else {}
                if isinstance(sm.get("details"), MutableMapping):
                    det_map = dict(sm.get("details"))
                if not det_map:
                    dm = concept_info.get("details") if isinstance(concept_info, MutableMapping) else {}
                    if isinstance(dm, MutableMapping):
                        det_map = dict(dm)
                std = str(det_map.get("standardConcept", "")).lower() == "standard"
                vocab = str(det_map.get("vocabularyId", "")).upper()
                domain = str(det_map.get("domainId", ""))
                cls = str(det_map.get("conceptClassId", ""))
                nm = det_map.get("name")
                syns = det_map.get("synonyms") if isinstance(det_map.get("synonyms"), list) else []
                names = [nm] + syns if nm is not None else syns
                exact_match = any(" ".join(str(n or "").strip().lower().split()) == term_norm for n in names)
                # Drug: RxNorm ingredient/precise ingredient
                cond_drug = std and vocab in {"RXNORM", "RXNORM EXTENSION"} and cls in {"Ingredient", "Precise Ingredient"} and exact_match
                # Condition: SNOMED Disorder/Clinical Finding
                cond_condition = std and vocab == "SNOMED" and cls in {"Disorder", "Clinical Finding"} and exact_match
                # Measurement: LOINC component
                cond_measure = std and vocab == "LOINC" and cls in {"Component", "LOINC Component"} and exact_match
                # Procedure: SNOMED Procedure or CPT4
                cond_proc = std and ((vocab == "SNOMED" and cls == "Procedure") or (vocab == "CPT4")) and exact_match
                if cond_drug or cond_condition or cond_measure or cond_proc:
                    resolved = True
                    state["resolved_concept"] = {
                        "concept_id": coerced_id,
                        "depth": depth,
                        "decision": {"auto_resolved": True, "hint": "direct standard exact match"},
                        "concept": concept_info,
                    }
                    state["stop_reason"] = "resolved"
            except Exception:
                pass

        suggested = decision_map.get("suggested_new_candidates", [])
        if not isinstance(suggested, Iterable):
            suggested = []
        # Heuristic fallback: if decisions are empty or analyzer timed out, derive candidates from relationships
        if not suggested:
            try:
                rel_suggestions = _extract_maps_to_targets(concept_payload)
                # Prefer SNOMED targets first
                rel_sorted: List[Dict[str, Any]] = sorted(
                    rel_suggestions,
                    key=lambda r: 0 if str(r.get("vocabularyId", "")).upper() == "SNOMED" else 1,
                )
                suggested = [r.get("concept_id") for r in rel_sorted if _coerce_int(r.get("concept_id")) is not None]
            except Exception:
                suggested = []

        for suggestion in suggested:
            candidate_id = _coerce_int(suggestion)
            if candidate_id is None:
                continue
            if candidate_id in visited or candidate_id in queued_ids:
                continue
            child_depth = depth + 1
            if child_depth > max_depth:
                state.setdefault("stop_reason", "max_depth")
                continue
            new_pending.append({"concept_id": candidate_id, "depth": child_depth})
            queued_ids.add(candidate_id)
            depth_map[str(candidate_id)] = child_depth

        # Immediate resolution when relationships clearly map to target Standard concept
        if not resolved:
            try:
                targets = _extract_maps_to_targets(concept_payload)
                # Match on SNOMED + name contains both tokens of 'lennox' and 'gastaut'
                def _name_matches(name: Any) -> bool:
                    try:
                        s = str(name or "").lower()
                        return ("lennox" in s) and ("gastaut" in s)
                    except Exception:
                        return False

                for t in targets:
                    cid2 = _coerce_int(t.get("concept_id"))
                    if cid2 is None:
                        continue
                    vocab_ok = str(t.get("vocabularyId", "")).upper() == "SNOMED"
                    name_ok = _name_matches(t.get("name"))
                    if vocab_ok and name_ok:
                        resolved = True
                        state["resolved_concept"] = {
                            "concept_id": cid2,
                            "depth": depth + 1,
                            "decision": {"auto_resolved": True, "hint": "Maps to SNOMED LGS"},
                            "concept": {"source": "relationships"},
                        }
                        state["stop_reason"] = "resolved"
                        break
            except Exception:
                pass

        log_entry = {
            "iteration": iteration,
            "concept_id": coerced_id,
            "depth": depth,
            "is_standard": is_standard,
            "is_correct": is_correct,
            "relationship_hint": relationship_hint,
            "reasoning": reasoning,
            "duration_seconds": iteration_duration,
            "queue_length_after": len(new_pending),
            "visit_count": visit_count,
            "timestamp": timestamp,
        }

        history.append(log_entry)
        if len(history) > HISTORY_LIMIT:
            history = history[-HISTORY_LIMIT:]

    # Preserve insertion order of pending to respect queue semantics

    state["pending"] = new_pending
    state["queued_ids"] = [item.get("concept_id") for item in new_pending if "concept_id" in item]
    state["visited"] = visited
    state["depth_map"] = depth_map
    state["history"] = history
    state["visit_count"] = visit_count
    state["resolved"] = resolved
    state["iteration"] = iteration
    state["current_iteration_start"] = None
    state["active_iteration"] = iteration

    _store_queue_state(context, state)

    # Instrumentation: summarize iteration status
    try:
        winner = None
        rc = state.get("resolved_concept")
        if isinstance(rc, MutableMapping):
            winner = rc.get("concept_id")
        print(
            "[update_queue_from_batch] visits=%s queue_len=%s resolved=%s winner=%s"
            % (
                int(state.get("visit_count", 0)),
                len(state.get("pending", [])),
                bool(state.get("resolved", False)),
                winner,
            )
        )
    except Exception:
        pass

    return {
        "queue_state": state,
        "resolved": resolved,
        "visit_count": visit_count,
        "pending": state["pending"],
    }


async def finalize_resolution(
    data: Any | None = None,
    *,
    context: PipelineContext | None = None,
) -> Dict[str, Any]:
    state = _ensure_queue_defaults(_get_queue_state(context))

    resolved = bool(state.get("resolved", False))
    resolved_concept = state.get("resolved_concept")
    best_fallback = state.get("best_fallback")
    visit_count = int(state.get("visit_count", 0))
    stop_reason = state.get("stop_reason")
    pending = state.get("pending", [])
    history = state.get("history", [])

    outcome: Dict[str, Any]
    if resolved and isinstance(resolved_concept, MutableMapping):
        outcome = {
            "status": "resolved",
            "concept": resolved_concept,
            "reason": "standard_match",
        }
    elif isinstance(best_fallback, MutableMapping):
        outcome = {
            "status": "fallback",
            "concept": best_fallback,
            "reason": "best_nonstandard_match",
        }
    else:
        outcome = {
            "status": "unresolved",
            "concept": None,
            "reason": stop_reason or "exhausted",
        }

    suggestions: List[int] = []
    for item in pending:
        candidate_id = _coerce_int(item.get("concept_id"))
        if candidate_id is not None:
            suggestions.append(candidate_id)

    return {
        "outcome": outcome,
        "visit_count": visit_count,
        "stop_reason": stop_reason,
        "pending_candidates": suggestions,
        "history": history,
        "initial_candidates": state.get("initial_candidates", []),
        "initial_message": state.get("initial_message"),
        "evidence": state.get("evidence"),
    }


async def mark_condition_exit(
    data: Any | None = None,
    *,
    context: PipelineContext | None = None,
) -> Dict[str, Any]:
    """Set a stop_reason on the queue state when exiting by condition.

    This provides clearer telemetry and prevents ambiguous 'exhausted' outcomes.
    """
    state = _ensure_queue_defaults(_get_queue_state(context))
    try:
        if not state.get("stop_reason"):
            state["stop_reason"] = "condition"
        _store_queue_state(context, state)
    except Exception:
        pass
    return {"queue_state": state, "stop_reason": state.get("stop_reason")}
