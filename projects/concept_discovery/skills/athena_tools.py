from __future__ import annotations

import json
from typing import Any, Dict, List, Union, Iterable
import time

try:
    from athena_client import Athena  # type: ignore
except Exception:
    Athena = None

# Allow-listed relationship names to reduce noise for the agent
RELATIONSHIP_ALLOW_LIST = {
    "Maps to",
    "Is a",
    "Has ingredient",
    "RxNorm has dose form",
    "Has tradename",
    "Constitutes",
    "Contains",
    "Form of",
    "Has mechanism of action",
    "Has physiologic effect",
    "Has clinical finding",
    "May treat",
    "May prevent",
    "Contraindication of",
    "Has finding site",
    "Causative agent of",
    "Has pathology",
    "Associated with",
    "Occurs in",
    "Variant of",
    "Subtype of",
    "Related to",
    "Same as",
    "Broader than",
}


def _normalize_domain(domain: str | None) -> str | None:
    if not domain:
        return None
    d = domain.strip().lower()
    mapping = {
        "condition": "Condition",
        "drug": "Drug",
        "procedure": "Procedure",
        "measurement": "Measurement",
        "observation": "Observation",
        "visit": "Visit",
        "device": "Device",
        "specimen": "Specimen",
        "note": "Note",
    }
    return mapping.get(d, domain)


def _safe_athena() -> Any:
    if Athena is None:
        raise RuntimeError("athena-client is not installed. pip install athena-client")
    return Athena()


def _retry(call, *args, attempts: int = 3, delay: float = 0.5, backoff: float = 2.0, **kwargs):
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return call(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if i == attempts - 1:
                break
            try:
                time.sleep(delay)
            except Exception:
                pass
            delay *= backoff
    if last_exc:
        raise last_exc
    raise RuntimeError("retry failed without exception")


def athena_search_for_concept_plan(plan: Union[str, Dict[str, Any]], top_k: int = 10) -> Dict[str, Any]:
    if isinstance(plan, str):
        try:
            plan_obj = json.loads(plan)
        except json.JSONDecodeError:
            start = plan.find("{")
            end = plan.rfind("}")
            if start != -1 and end != -1 and end > start:
                plan_obj = json.loads(plan[start : end + 1])
            else:
                raise
    else:
        plan_obj = plan
    concept_sets = plan_obj.get("concept_sets", []) if isinstance(plan_obj, dict) else []

    client = _safe_athena()
    out_sets: List[Dict[str, Any]] = []
    for item in concept_sets:
        name = item.get("name") or "unnamed_set"
        queries: List[str] = list(item.get("queries") or [])
        domain = _normalize_domain(item.get("domain"))
        vocab_prefs: List[str] = list(item.get("vocabulary") or [])
        include_desc = bool(item.get("include_descendants", True))
        standard_only = bool(item.get("standard_only", True))

        seen: set[int] = set()
        candidates: List[Dict[str, Any]] = []
        for q in queries:
            q = (q or "").strip()
            if not q:
                continue
            try:
                results = _retry(client.search, q)
            except Exception:
                continue
            try:
                raw = results.top(max(top_k * 3, 10))
                raw_list = raw if isinstance(raw, list) else getattr(raw, "all", lambda: [])()
            except Exception:
                try:
                    raw_list = _retry(results.all)
                except Exception:
                    raw_list = []
            # Use robust filter to handle field variations
            filtered = _filter_candidates(
                raw_list, domain=domain, vocabulary=vocab_prefs or None, standard_only=standard_only
            )
            for concept in filtered:
                cid = concept["concept_id"]
                if cid in seen:
                    continue
                seen.add(cid)
                candidates.append(concept)
                if len(candidates) >= top_k:
                    break
            if len(candidates) >= top_k:
                break
        out_sets.append(
            {
                "name": name,
                "candidates": candidates[:top_k],
                "include_descendants": include_desc,
                "standard_only": standard_only,
                "notes": item.get("intent") or "",
            }
        )
    # Return in scratchpad format for proper context storage when updates_context: true
    return {"scratchpad": {"concept_sets": out_sets}}


# === Minimal tool surface for the concept_refiner agent ===

def _as_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    try:
        import json

        if isinstance(obj, str):
            s = obj.strip()
            if s.startswith("{") and s.endswith("}"):
                return json.loads(s)
            return {"query": s}
        # Fallback to JSON round-trip
        data = json.loads(json.dumps(obj, default=str))
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {"data": str(obj)}


def _get_field(d: Dict[str, Any], *names: str) -> Any:
    for n in names:
        if n in d:
            return d.get(n)
    # Try case variants
    lowered = {k.lower(): v for k, v in d.items()}
    for n in names:
        v = lowered.get(n.lower())
        if v is not None:
            return v
    return None


def _to_plain_dict(obj: Any) -> Dict[str, Any]:
    """Best-effort conversion of client objects (e.g., Pydantic models) to plain dicts.

    Handles pydantic v1 (`.dict()` / `.json()`), pydantic v2 (`.model_dump()` / `.model_dump_json()`),
    and falls back to `__dict__` or stringification as a last resort.
    """
    if isinstance(obj, dict):
        return obj
    # Pydantic v2
    fn = getattr(obj, "model_dump", None)
    if callable(fn):
        try:
            data = fn()
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    # Pydantic v1
    fn = getattr(obj, "dict", None)
    if callable(fn):
        try:
            data = fn()
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    # Try JSON methods
    try:
        import json as _json

        fn = getattr(obj, "model_dump_json", None)
        if callable(fn):
            try:
                return _json.loads(fn())
            except Exception:
                pass
        fn = getattr(obj, "json", None)
        if callable(fn):
            try:
                return _json.loads(fn())
            except Exception:
                pass
    except Exception:
        pass
    # Fallback to __dict__
    d = getattr(obj, "__dict__", None)
    if isinstance(d, dict):
        return {k: v for k, v in d.items() if not k.startswith("_")}
    return {}


def _as_standard_flag(x: Any) -> str | None:
    # Accept 'S'/'C'/None or booleans
    if x is None:
        return None
    if isinstance(x, str):
        s = x.strip().upper()
        if s in ("S", "C"):
            return s
        # Some APIs might return 'Standard'/'Classification'
        if s.startswith("STANDARD"):
            return "S"
        if s.startswith("CLASS"):
            return "C"
        return None
    if isinstance(x, bool):
        return "S" if x else None
    # Handle Enum-like objects from clients (e.g., athena-client ConceptType)
    try:
        val = getattr(x, "value", x)
        s = str(val).strip().upper()
        if s in ("S", "C"):
            return s
        if "STANDARD" in s and "NON" not in s:
            return "S"
        if "CLASS" in s:
            return "C"
    except Exception:
        pass
    return None


def _filter_candidates(
    items: Iterable[Dict[str, Any]],
    *,
    domain: str | None,
    vocabulary: List[str] | None,
    standard_only: bool,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for raw in items:
        # Normalize possible Pydantic models or typed objects to dicts first
        c = _to_plain_dict(raw)
        if not c:
            continue
        # Pull fields with flexible naming
        cid_raw = _get_field(c, "concept_id", "conceptId", "id")
        try:
            cid = int(cid_raw)
        except Exception:
            continue
        sc_flag = _as_standard_flag(_get_field(c, "standard_concept", "standardConcept", "is_standard", "isStandard"))
        if standard_only and sc_flag not in ("S", "C"):
            continue
        c_domain = _get_field(c, "domain_id", "domainId", "domain")
        if domain and c_domain != domain:
            continue
        if vocabulary:
            c_vocab = _get_field(c, "vocabulary_id", "vocabularyId", "vocabulary")
            if c_vocab not in vocabulary:
                continue
        out.append(
            {
                "concept_id": cid,
                "concept_name": _get_field(c, "concept_name", "conceptName", "name"),
                "domain_id": c_domain,
                "vocabulary_id": _get_field(c, "vocabulary_id", "vocabularyId", "vocabulary"),
                "standard_concept": sc_flag,
                "concept_code": _get_field(c, "concept_code", "conceptCode", "code"),
            }
        )
    return out


def athena_search(payload: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Search Athena for a query with optional filters.

    Accepts:
      - String: treated as the query.
      - Dict: { query, top_k, domain, vocabulary:[], standard_only:bool }
    Returns: { success, query, candidates:[{concept_id,...}], note? }
    """
    cfg = _as_dict(payload)
    q: str = (cfg.get("query") or cfg.get("q") or cfg.get("term") or "").strip()
    if not q and isinstance(payload, str):
        q = payload.strip()
    top_k: int = int(cfg.get("top_k") or 20)
    domain = _normalize_domain(cfg.get("domain"))
    vocabulary = cfg.get("vocabulary") or cfg.get("vocab")
    if isinstance(vocabulary, str):
        vocabulary = [vocabulary]
    if vocabulary is not None:
        vocabulary = [str(v) for v in vocabulary]
    standard_only = bool(cfg.get("standard_only", True))

    if not q:
        return {"success": False, "query": q, "candidates": [], "error": "empty_query"}
    try:
        client = _safe_athena()
        results = _retry(client.search, q)
        try:
            raw: List[Dict[str, Any]] = results.top(max(top_k * 3, top_k))
        except Exception:
            try:
                raw = _retry(results.all)
            except Exception:
                raw = []
        candidates = _filter_candidates(
            raw, domain=domain, vocabulary=vocabulary, standard_only=standard_only
        )
        return {
            "success": True,
            "query": q,
            "candidates": candidates[:top_k],
            "filters": {
                "domain": domain,
                "vocabulary": vocabulary,
                "standard_only": standard_only,
            },
        }
    except Exception as e:
        return {"success": False, "query": q, "candidates": [], "error": str(e)}


def athena_details(payload: Union[int, List[int], Dict[str, Any], str]) -> Dict[str, Any]:
    """Fetch detailed metadata for one or more concept IDs.
    Accepts: int | [int] | { concept_id(s) } | JSON string.
    Returns: { success, concepts: [{...}] }
    """
    cfg = _as_dict(payload)
    ids: List[int] = []
    if isinstance(payload, int):
        ids = [payload]
    elif isinstance(payload, list):
        ids = [int(x) for x in payload]
    else:
        for key in ("concept_id", "concept_ids", "ids"):
            v = cfg.get(key)
            if v is None:
                continue
            if isinstance(v, list):
                ids = [int(x) for x in v]
            else:
                try:
                    ids = [int(v)]
                except Exception:
                    pass
            if ids:
                break
    if not ids:
        return {"success": False, "concepts": [], "error": "no_ids"}
    try:
        client = _safe_athena()
        out: List[Dict[str, Any]] = []
        for cid in ids:
            try:
                fn = getattr(client, "details", None) or getattr(client, "concept", None)
                data = _retry(fn, cid) if fn else {"concept_id": cid}
            except Exception:
                data = {"concept_id": cid}
            out.append(data)
        return {"success": True, "concepts": out}
    except Exception as e:
        return {"success": False, "concepts": [], "error": str(e)}


def athena_relationships(payload: Union[int, Dict[str, Any], str]) -> Dict[str, Any]:
    """Fetch relationships for a concept (e.g., 'Maps to').
    Returns: { success, concept_id, relationships:[{relationship_id, concept_id_2, ...}], maps_to:[int] }
    """
    cfg = _as_dict(payload)
    try:
        cid = int(cfg.get("concept_id") or cfg.get("id") or payload)  # type: ignore[arg-type]
    except Exception:
        return {"success": False, "relationships": [], "error": "invalid_id"}
    try:
        client = _safe_athena()
        fn = getattr(client, "relationships", None)
        rel_obj = None
        if fn:
            try:
                rel_obj = _retry(fn, cid)
            except Exception:
                rel_obj = None

        # Normalize and extract with allow-list filtering; also compute 'Maps to' IDs
        def _collect(obj: Any) -> tuple[list[dict[str, Any]], list[int]]:
            rels: List[Dict[str, Any]] = []
            maps_to: List[int] = []
            d = _to_plain_dict(obj) if obj is not None else {}
            groups = d.get("items") or d.get("relationships") or []
            if isinstance(groups, dict):
                groups = [groups]
            for g in groups:
                gd = _to_plain_dict(g)
                items = gd.get("relationships") or gd.get("items") or []
                if isinstance(items, dict):
                    items = [items]
                for r in items:
                    rd = _to_plain_dict(r)
                    rel_name = _get_field(rd, "relationship_id", "relationshipId", "relationshipName")
                    rel_name_str = (str(rel_name) if rel_name is not None else "").strip()
                    if rel_name_str in RELATIONSHIP_ALLOW_LIST:
                        rels.append(rd)
                    # also collect maps_to ids
                    if rel_name_str.lower() == "maps to":
                        cid2 = _get_field(rd, "concept_id_2", "conceptId2", "targetConceptId", "conceptId")
                        try:
                            maps_to.append(int(cid2))
                        except Exception:
                            pass
            return rels, maps_to

        rels_norm, maps_to_ids = _collect(rel_obj)
        return {"success": True, "concept_id": cid, "relationships": rels_norm, "maps_to": maps_to_ids}
    except Exception as e:
        return {"success": False, "relationships": [], "error": str(e)}


def athena_summary(payload: Union[int, Dict[str, Any], str]) -> Dict[str, Any]:
    """Fetch a summary for a concept if the client supports it.
    Returns: { success, concept_id, summary: {...}? }
    """
    cfg = _as_dict(payload)
    try:
        cid = int(cfg.get("concept_id") or cfg.get("id") or payload)  # type: ignore[arg-type]
    except Exception:
        return {"success": False, "error": "invalid_id"}
    try:
        client = _safe_athena()
        fn = getattr(client, "summary", None)
        if not fn:
            return {"success": True, "concept_id": cid, "summary": None}
        try:
            data = _retry(fn, cid)
        except Exception:
            data = None
        return {"success": True, "concept_id": cid, "summary": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def athena_graph(payload: Union[int, Dict[str, Any], str]) -> Dict[str, Any]:
    """Fetch a small relationship graph if supported.
    Returns: { success, concept_id, graph: {...}? }
    """
    cfg = _as_dict(payload)
    try:
        cid = int(cfg.get("concept_id") or cfg.get("id") or payload)  # type: ignore[arg-type]
    except Exception:
        return {"success": False, "error": "invalid_id"}
    try:
        client = _safe_athena()
        fn = getattr(client, "graph", None)
        if not fn:
            return {"success": True, "concept_id": cid, "graph": None}
        try:
            # Best-effort: depth or options may vary across clients
            data = _retry(fn, cid)
        except Exception:
            data = None
        return {"success": True, "concept_id": cid, "graph": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def athena_expand_candidates(search_results: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Expand Athena search candidates by following non-standard/"C" to 'Maps to' standard concepts.

    Input shape: { concept_sets: [ { name, candidates: [{...}], include_descendants, standard_only, ... } ] }
    Output shape: same as input, but 'candidates' per set is augmented with mapped standard concepts (deduped).
    """
    data = _as_dict(search_results)
    concept_sets = data.get("concept_sets") or []
    if not isinstance(concept_sets, list):
        return {"concept_sets": []}
    client = None
    try:
        client = _safe_athena()
    except Exception:
        client = None

    out_sets: List[Dict[str, Any]] = []
    for cs in concept_sets:
        name = cs.get("name") or "unnamed"
        raw_candidates: List[Dict[str, Any]] = list(cs.get("candidates") or [])
        include_desc = bool(cs.get("include_descendants", True))
        standard_only = bool(cs.get("standard_only", True))

        seen_ids: set[int] = set()
        expanded: List[Dict[str, Any]] = []

        # Helper to add a concept dict safely
        def add_concept(c: Dict[str, Any]) -> None:
            try:
                cid = int(c.get("concept_id"))
            except Exception:
                return
            if cid in seen_ids:
                return
            seen_ids.add(cid)
            expanded.append(
                {
                    "concept_id": cid,
                    "concept_name": c.get("concept_name"),
                    "domain_id": c.get("domain_id"),
                    "vocabulary_id": c.get("vocabulary_id"),
                    "standard_concept": c.get("standard_concept"),
                    "concept_code": c.get("concept_code"),
                }
            )

        # First, keep original standard concepts
        for c in raw_candidates:
            if (c.get("standard_concept") == "S") or not standard_only:
                add_concept(c)

        # For non-standard or classification candidates, try to fetch 'Maps to'
        for c in raw_candidates:
            sc = c.get("standard_concept")
            if sc == "S":
                continue
            try:
                cid = int(c.get("concept_id"))
            except Exception:
                continue
            # Follow relationships if client available
            maps_to_ids: List[int] = []
            if client is not None:
                try:
                    fn = getattr(client, "relationships", None)
                    rel_obj = _retry(fn, cid) if fn else None
                except Exception:
                    rel_obj = None
                # Extract 'Maps to' targets from possible pydantic structure
                d = _to_plain_dict(rel_obj) if rel_obj is not None else {}
                groups = d.get("items") or d.get("relationships") or []
                if isinstance(groups, dict):
                    groups = [groups]
                for g in groups:
                    gd = _to_plain_dict(g)
                    items = gd.get("relationships") or gd.get("items") or []
                    if isinstance(items, dict):
                        items = [items]
                    for r in items:
                        rd = _to_plain_dict(r)
                        rel_id = (
                            _get_field(rd, "relationship_id", "relationshipId", "relationshipName")
                            or ""
                        ).strip().lower()
                        if rel_id == "maps to":
                            cid2 = _get_field(rd, "concept_id_2", "conceptId2", "targetConceptId", "conceptId")
                            try:
                                maps_to_ids.append(int(cid2))
                            except Exception:
                                pass
                # Fetch details for mapped ids and add standard ones
                if maps_to_ids:
                    try:
                        df = getattr(client, "details", None) or getattr(client, "concept", None)
                        for mid in maps_to_ids:
                            try:
                                det_raw = _retry(df, mid) if df else {"concept_id": mid}
                            except Exception:
                                det_raw = {"concept_id": mid}
                            det = _to_plain_dict(det_raw)
                            sc = _as_standard_flag(
                                _get_field(det, "standard_concept", "standardConcept", "is_standard", "isStandard")
                            )
                            if sc == "S":
                                add_concept(
                                    {
                                        "concept_id": det.get("concept_id")
                                        or det.get("conceptId")
                                        or det.get("id"),
                                        "concept_name": det.get("concept_name")
                                        or det.get("conceptName")
                                        or det.get("name"),
                                        "domain_id": det.get("domain_id")
                                        or det.get("domainId")
                                        or det.get("domain"),
                                        "vocabulary_id": det.get("vocabulary_id")
                                        or det.get("vocabularyId")
                                        or det.get("vocabulary"),
                                        "standard_concept": "S",
                                        "concept_code": det.get("concept_code")
                                        or det.get("conceptCode")
                                        or det.get("code"),
                                    }
                                )
                    except Exception:
                        pass

        out_sets.append(
            {
                "name": name,
                "candidates": expanded if expanded else raw_candidates,
                "include_descendants": include_desc,
                "standard_only": standard_only,
            }
        )

    return {"concept_sets": out_sets}
