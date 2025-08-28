from __future__ import annotations

import json
from typing import Any, Dict, List, Union

try:
    from athena_client import Athena  # type: ignore
except Exception:  # pragma: no cover - import-time safety
    Athena = None  # Will be validated at runtime


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
        raise RuntimeError(
            "athena-client is not installed. Please install with: pip install athena-client"
        )
    return Athena()


def athena_search_for_concept_plan(
    plan: Union[str, Dict[str, Any]],
    top_k: int = 10,
) -> Dict[str, Any]:
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
            except Exception as e:
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

            try:
                raw = results.top(max(top_k * 3, 10))
                raw_list = (
                    raw if isinstance(raw, list) else getattr(raw, "all", lambda: [])()
                )
            except Exception:
                try:
                    raw_list = results.all()
                except Exception:
                    raw_list = []

            for concept in raw_list:
                try:
                    cid = int(concept.get("concept_id"))
                except Exception:
                    continue
                if standard_only and concept.get("standard_concept") not in ("S", "C"):
                    continue
                if domain and concept.get("domain_id") != domain:
                    continue
                if vocab_prefs:
                    voc = concept.get("vocabulary_id")
                    if voc not in vocab_prefs:
                        continue
                if cid in seen:
                    continue
                seen.add(cid)
                candidates.append(
                    {
                        "concept_id": cid,
                        "concept_name": concept.get("concept_name"),
                        "domain_id": concept.get("domain_id"),
                        "vocabulary_id": concept.get("vocabulary_id"),
                        "standard_concept": concept.get("standard_concept"),
                        "concept_code": concept.get("concept_code"),
                    }
                )
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

    return {"concept_sets": out_sets}
