from __future__ import annotations

import json
from typing import Any, Dict, List, Union, Optional

try:
    from athena_client import Athena  # type: ignore
except Exception:  # pragma: no cover - import-time safety
    Athena = None  # Will be validated at runtime


def _normalize_domain(domain: str | None) -> str | None:
    if not domain:
        return None
    d = domain.strip().lower()
    # Common OMOP DomainId values normalization
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
        raise RuntimeError(
            "athena-client is not installed. Please install with: pip install athena-client"
        )
    return Athena()


def _get_attr(obj: Any, *names: str, default: Any = None) -> Any:
    """Try to read value by multiple candidate names from dict-like or attr object."""
    for name in names:
        try:
            if isinstance(obj, dict) and name in obj:
                return obj[name]
            if hasattr(obj, name):
                return getattr(obj, name)
        except Exception:
            pass
    # Try JSON serialization if available
    try:
        if hasattr(obj, "to_json"):
            data = json.loads(obj.to_json())
            for name in names:
                if name in data:
                    return data[name]
    except Exception:
        pass
    return default


def _concept_to_dict(concept: Any) -> Optional[Dict[str, Any]]:
    """Normalize a concept (dict or athena_client object) to a standard dict.

    Output keys: concept_id(int), concept_name, domain_id, vocabulary_id, standard_concept, concept_code
    """
    # Prefer OMOP-style keys; fall back to athena_client attrs
    cid = _get_attr(concept, "concept_id", "id")
    if cid is None:
        return None
    try:
        cid = int(cid)
    except Exception:
        return None

    return {
        "concept_id": cid,
        "concept_name": _get_attr(concept, "concept_name", "name"),
        "domain_id": _get_attr(concept, "domain_id", "domain"),
        "vocabulary_id": _get_attr(concept, "vocabulary_id", "vocabulary"),
        "standard_concept": _get_attr(concept, "standard_concept", "standardConcept"),
        "concept_code": _get_attr(concept, "concept_code", "code"),
    }


def athena_search_for_concept_plan(
    plan: Union[str, Dict[str, Any]],
    top_k: int = 10,
) -> Dict[str, Any]:
    """Search OMOP concepts in ATHENA for a concept plan.

    Parameters
    - plan: JSON string or dict with shape {"concept_sets": [{ name, queries[], domain?, vocabulary?, include_descendants?, standard_only? } ...]}
    - top_k: Max candidates per concept set to return.

    Returns
    - dict with {"concept_sets": [{"name": str, "candidates": [concept...], "include_descendants": bool, "standard_only": bool, "notes": str?}]}
    """
    if isinstance(plan, str):
        try:
            plan_obj = json.loads(plan)
        except json.JSONDecodeError:
            # If it's not pure JSON (some models add pre/post text), try to extract JSON substring
            start = plan.find("{")
            end = plan.rfind("}")
            if start != -1 and end != -1 and end > start:
                plan_obj = json.loads(plan[start : end + 1])
            else:
                raise
    else:
        plan_obj = plan

    concept_sets = (
        plan_obj.get("concept_sets", []) if isinstance(plan_obj, dict) else []
    )

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
                results = client.search(q)
            except Exception as e:  # network or API issue
                out_sets.append(
                    {
                        "name": name,
                        "candidates": [],
                        "include_descendants": include_desc,
                        "standard_only": standard_only,
                        "notes": f"Search failed for query '{q}': {e}",
                    }
                )
                continue

            # Pull more than top_k to allow filtering and dedup
            try:
                raw = results.top(max(top_k * 3, 10))
                raw_list = (
                    raw
                    if isinstance(raw, list)
                    else getattr(results, "all", lambda: [])()
                )
            except Exception:
                # Fallback, try to materialize results via .all()
                try:
                    raw_list = results.all()
                except Exception:
                    raw_list = []

            for concept in raw_list:
                norm = _concept_to_dict(concept)
                if not norm:
                    continue
                cid = norm["concept_id"]

                # Domain filter
                if domain and norm.get("domain_id") != domain:
                    continue

                # Vocabulary filter
                if vocab_prefs:
                    voc = norm.get("vocabulary_id")
                    if voc not in vocab_prefs:
                        continue

                if cid in seen:
                    continue
                seen.add(cid)

                candidates.append(norm)

                if len(candidates) >= top_k:
                    break
            # If we already reached top_k from this query, continue to next concept set
            if len(candidates) >= top_k:
                pass

        # Prefer standard 'S' first, then 'C', then non-standard
        def _std_rank(c: Dict[str, Any]) -> int:
            sc = (c.get("standard_concept") or "").upper()
            if sc == "S":
                return 0
            if sc == "C":
                return 1
            return 2

        candidates.sort(key=_std_rank)

        out_sets.append(
            {
                "name": name,
                "candidates": candidates[:top_k],
                "include_descendants": include_desc,
                "standard_only": standard_only,
                "notes": item.get("intent") or "",
            }
        )

    return {"concept_sets": out_sets}


# --- Agent-friendly thin wrappers over Athena client ---


def athena_search(query: str, top_k: int = 15) -> List[Dict[str, Any]]:
    """Search Athena for a free-text query and return lightweight concept dicts.

    Returns list of {concept_id, concept_name, domain_id, vocabulary_id, standard_concept, concept_code}.
    """
    client = _safe_athena()
    try:
        results = client.search(query)
        try:
            raw = results.top(max(top_k * 2, 10))
            items = (
                raw if isinstance(raw, list) else getattr(results, "all", lambda: [])()
            )
        except Exception:
            items = results.all()
    except Exception as e:
        return [{"error": f"search failed: {e}", "query": query}]

    out: List[Dict[str, Any]] = []
    seen: set[int] = set()
    for concept in items:
        norm = _concept_to_dict(concept)
        if not norm:
            continue
        cid = norm["concept_id"]
        if cid in seen:
            continue
        seen.add(cid)
        out.append(norm)
        if len(out) >= top_k:
            break
    # Rank with S first
    out.sort(
        key=lambda c: (
            0
            if (c.get("standard_concept") or "").upper() == "S"
            else (1 if (c.get("standard_concept") or "").upper() == "C" else 2)
        )
    )
    return out


def athena_details(concept_id: int) -> Dict[str, Any]:
    """Return detailed information for a specific concept.

    Mirrors: athena.details(concept_id=...). Returns a dict-like structure.
    """
    client = _safe_athena()
    try:
        details = client.details(concept_id=concept_id)
        if isinstance(details, dict):
            # Normalize keys
            out = {
                "concept_id": details.get("concept_id") or details.get("id"),
                "concept_name": details.get("concept_name") or details.get("name"),
                "domain_id": details.get("domain_id") or details.get("domainId"),
                "vocabulary_id": details.get("vocabulary_id")
                or details.get("vocabularyId"),
                "standard_concept": details.get("standard_concept")
                or details.get("standardConcept"),
                "concept_code": details.get("concept_code")
                or details.get("conceptCode"),
            }
            return out
        # athena_client returns a pydantic model with attributes
        attrs = getattr(details, "__dict__", {})
        sc = attrs.get("standardConcept")
        if hasattr(sc, "name"):
            sc_val = sc.name  # STANDARD, CLASSIFICATION, NON_STANDARD
        else:
            sc_val = str(sc)
        out = {
            "concept_id": attrs.get("id"),
            "concept_name": attrs.get("name"),
            "domain_id": attrs.get("domainId"),
            "vocabulary_id": attrs.get("vocabularyId"),
            "standard_concept": sc_val,
            "concept_code": attrs.get("conceptCode"),
        }
        return out
    except Exception as e:
        return {"error": f"details failed: {e}", "concept_id": concept_id}


def athena_relationships(concept_id: int) -> List[Dict[str, Any]]:
    """Return relationships for a concept (e.g., 'Maps to', 'Is a').

    Output: list of { relationship_id, relationship_name, to_concept_id, to_concept_name, to_vocabulary_id }
    """
    client = _safe_athena()
    try:
        rel = client.relationships(concept_id=concept_id)
        # athena_client returns ConceptRelationship with .items grouping
        items = getattr(rel, "items", None)
        rows: List[Dict[str, Any]] = []
        if items:
            for grp in items:
                rel_name = getattr(grp, "relationshipName", None)
                for it in getattr(grp, "relationships", []) or []:
                    rows.append(
                        {
                            "relationship_id": getattr(it, "relationshipId", None),
                            "relationship_name": rel_name
                            or getattr(it, "relationshipName", None),
                            "to_concept_id": getattr(it, "targetConceptId", None),
                            "to_concept_name": getattr(it, "targetConceptName", None),
                            "to_vocabulary_id": getattr(it, "targetVocabularyId", None),
                        }
                    )
            return rows
        # If it's already a list/dict
        if isinstance(rel, list):
            return rel  # assume normalized upstream
        if isinstance(rel, dict):
            return [rel]
        # Fallback to best-effort stringification
        return [{"raw": str(rel)}]
    except Exception as e:
        return [{"error": f"relationships failed: {e}", "concept_id": concept_id}]


def athena_summary(concept_id: int) -> Dict[str, Any]:
    """Return a comprehensive summary for a concept."""
    client = _safe_athena()
    try:
        summ = client.summary(concept_id=concept_id)
        if isinstance(summ, dict):
            return summ
        # Fallback to attribute dict
        return getattr(summ, "__dict__", {"raw": str(summ)})
    except Exception as e:
        return {"error": f"summary failed: {e}", "concept_id": concept_id}


def athena_graph(concept_id: int, depth: int = 3) -> Dict[str, Any]:
    """Return a concept graph for exploration (parents/children over depth)."""
    client = _safe_athena()
    try:
        graph = client.graph(concept_id=concept_id, depth=depth)
        if isinstance(graph, dict):
            return graph
        attrs = getattr(graph, "__dict__", {})
        return {
            "terms": attrs.get("terms"),
            "links": attrs.get("links"),
            "connections_count": attrs.get("connectionsCount"),
        }
    except Exception as e:
        return {"error": f"graph failed: {e}", "concept_id": concept_id, "depth": depth}
