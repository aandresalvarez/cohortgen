"""
Pydantic AI Tools for ATHENA Concept Discovery

This module wraps the athena-client library to provide tool functions
for Pydantic AI agents to search and explore OMOP concepts.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from pydantic import Field
from pydantic_ai import RunContext

# Import athena-client library directly
try:
    from athena_client import AthenaClient
    from athena_client.models import ConceptType
    ATHENA_AVAILABLE = True
except ImportError:
    AthenaClient = None  # type: ignore[assignment, misc]
    ConceptType = None  # type: ignore[assignment, misc]
    ATHENA_AVAILABLE = False


# ============================================================================
# Pydantic AI Tool Functions
# ============================================================================

def _concept_to_dict(concept) -> Dict[str, Any]:
    """Convert athena-client Concept/ConceptDetails to snake_case dict used in search results."""
    standard_concept = None
    if hasattr(concept, 'standardConcept') and concept.standardConcept:
        if concept.standardConcept == ConceptType.STANDARD:
            standard_concept = "S"
        elif concept.standardConcept == ConceptType.CLASSIFICATION:
            standard_concept = "C"
        else:
            standard_concept = None

    if hasattr(concept, 'domainId'):
        # ConceptDetails object
        return {
            "concept_id": concept.id,
            "concept_name": concept.name,
            "domain_id": getattr(concept, 'domainId', None),
            "vocabulary_id": getattr(concept, 'vocabularyId', None),
            "standard_concept": standard_concept,
            "concept_code": getattr(concept, 'conceptCode', None),
            "concept_class_id": getattr(concept, 'conceptClassId', None),
        }
    else:
        # Concept (search result)
        return {
            "concept_id": concept.id,
            "concept_name": concept.name,
            "domain_id": getattr(concept, 'domain', None),
            "vocabulary_id": getattr(concept, 'vocabulary', None),
            "standard_concept": standard_concept,
            "concept_code": getattr(concept, 'code', None),
            "concept_class_id": getattr(concept, 'className', None),
        }


def _concept_to_camel_details(concept) -> Dict[str, Any]:
    """Convert athena-client Concept/ConceptDetails to CamelCase keys expected by find_concepts."""
    # Map standardConcept to readable label for downstream (expects 'Standard' string)
    std_label = None
    if hasattr(concept, 'standardConcept') and concept.standardConcept:
        if concept.standardConcept == ConceptType.STANDARD:
            std_label = "Standard"
        elif concept.standardConcept == ConceptType.CLASSIFICATION:
            std_label = "Classification"

    # Prefer ConceptDetails attributes; fall back to Concept attributes
    domain = getattr(concept, 'domainId', getattr(concept, 'domain', None))
    vocabulary = getattr(concept, 'vocabularyId', getattr(concept, 'vocabulary', None))
    concept_code = getattr(concept, 'conceptCode', getattr(concept, 'code', None))
    concept_class = getattr(concept, 'conceptClassId', getattr(concept, 'className', None))

    cid = int(getattr(concept, 'id'))
    name = getattr(concept, 'name', None)

    return {
        "id": cid,
        "conceptId": cid,           # provide both for downstream compatibility
        "name": name,
        "conceptName": name,        # provide both keys
        "standardConcept": std_label,
        "domainId": domain,
        "vocabularyId": vocabulary,
        "conceptCode": concept_code,
        "conceptClassId": concept_class,
    }


def _map_to_standard_ids(client: "AthenaClient", concept_id: int) -> List[int]:
    """Return standard concept_ids this concept maps to via 'Maps to'."""
    try:
        rels = client.relationships(concept_id)
        mapped: List[int] = []
        for rel in rels:
            rel_name = getattr(rel, "name", str(rel))
            target_id = getattr(rel, "targetId", None)
            if rel_name == "Maps to" and target_id:
                mapped.append(int(target_id))
        return mapped
    except Exception:
        return []


def search_athena(
    ctx: RunContext[Dict[str, Any]],
    query: str,
    domain: str | None = None,
    vocabulary: List[str] | None = None,
    standard_only: bool = True,
    top_k: int = 20
) -> Dict[str, Any]:
    """
    Search ATHENA for OMOP concepts matching a query.
    
    Returns: 
        {
            "success": bool,
            "query": str,
            "candidates": [{concept_id, concept_name, domain_id, vocabulary_id, standard_concept, concept_code}],
            "filters": {...}
        }
    
    Example:
        search_athena("type 2 diabetes", domain="Condition", vocabulary=["SNOMED"])
    """
    if not ATHENA_AVAILABLE:
        return {"success": False, "error": "athena-client not installed", "candidates": []}
    
    try:
        client = AthenaClient()
        
        # Search for concepts
        results = client.search(query)
        
        # Filter results with standard mapping fallback
        candidates = []
        for concept in results:
            # Apply domain filter
            if domain and concept.domain != domain:
                continue

            # Apply vocabulary filter
            if vocabulary:
                vocab_list = vocabulary if isinstance(vocabulary, list) else [vocabulary]
                if concept.vocabulary not in vocab_list:
                    continue

            # If standard-only requested and this is non-standard, try to map to standard
            if standard_only and concept.standardConcept != ConceptType.STANDARD:
                mapped_ids = _map_to_standard_ids(client, int(concept.id))
                for mid in mapped_ids:
                    try:
                        det = client.details(mid)
                        det_dict = _concept_to_dict(det)
                        # Domain filter on mapped
                        if domain and det_dict.get("domain_id") != domain:
                            continue
                        candidates.append(det_dict)
                        if len(candidates) >= top_k:
                            break
                    except Exception:
                        continue
                if len(candidates) >= top_k:
                    break
                continue  # skip adding the non-standard original

            # Otherwise accept the concept (standard or standard_only==False)
            candidates.append(_concept_to_dict(concept))
            if len(candidates) >= top_k:
                break
        
        return {
            "success": True,
            "query": query,
            "candidates": candidates,
            "filters": {
                "domain": domain,
                "vocabulary": vocabulary,
                "standard_only": standard_only
            }
        }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "candidates": [],
            "error": str(e)
        }


def get_concept_details(
    ctx: RunContext[Dict[str, Any]],
    concept_ids: List[int]
) -> Dict[str, Any]:
    """
    Fetch detailed metadata for one or more OMOP concept IDs.
    
    Returns:
        {
            "success": bool,
            "concepts": [{concept_id, concept_name, domain_id, vocabulary_id, standard_concept, ...}]
        }
    
    Use this to verify:
    - Whether a concept is standard (standard_concept = 'S')
    - The concept's domain and vocabulary
    - Full metadata for validation
    
    Example:
        get_concept_details([201826, 201254])
    """
    if not ATHENA_AVAILABLE:
        return {"success": False, "error": "athena-client not installed", "concepts": []}
    
    try:
        client = AthenaClient()
        concepts = []

        for concept_id in concept_ids:
            try:
                result = client.details(concept_id)
                if result:
                    # Return CamelCase keys inside details to satisfy downstream expectations
                    concepts.append(_concept_to_camel_details(result))
            except Exception as e:
                print(f"Warning: Could not fetch details for concept {concept_id}: {e}")
                continue

        return {"success": True, "concepts": concepts}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "concepts": []
        }


def get_concept_relationships(
    ctx: RunContext[Dict[str, Any]],
    concept_id: int
) -> Dict[str, Any]:
    """
    Fetch relationships for a concept (e.g., 'Maps to', 'Is a').
    
    Returns:
        {
            "success": bool,
            "concept_id": int,
            "relationships": [{relationship_id, concept_id_2, ...}],
            "maps_to": [int]  # IDs of standard concepts this maps to
        }
    
    Critical for:
    - Finding standard concepts from non-standard ones (follow "Maps to")
    - Exploring hierarchies ("Is a")
    - Understanding concept connections
    
    Example:
        get_concept_relationships(40481087)  # Non-standard concept
        # Returns: {"maps_to": [201826]}  # Standard SNOMED concept
    """
    if not ATHENA_AVAILABLE:
        return {"success": False, "error": "athena-client not installed", "relationships": [], "maps_to": []}
    
    try:
        client = AthenaClient()
        relationships = client.relationships(concept_id)

        # Convert relationships to dicts (CamelCase keys)
        rel_list = []
        maps_to = []

        for rel in relationships:
            relationship_id = rel.name if hasattr(rel, 'name') else str(rel)
            source_id = rel.sourceId if hasattr(rel, 'sourceId') else concept_id
            target_id = rel.targetId if hasattr(rel, 'targetId') else None

            rel_dict = {
                "relationshipId": relationship_id,
                "sourceConceptId": source_id,
                "targetConceptId": target_id,
            }
            rel_list.append(rel_dict)

            if relationship_id == "Maps to" and target_id:
                maps_to.append(int(target_id))

        return {"success": True, "concept_id": concept_id, "relationships": rel_list, "maps_to": maps_to}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "concept_id": concept_id,
            "relationships": [],
            "maps_to": []
        }


def get_concept_summary(
    ctx: RunContext[Dict[str, Any]],
    concept_id: int
) -> Dict[str, Any]:
    """
    Fetch a summary for a concept if the client supports it.
    
    Returns:
        {
            "success": bool,
            "concept_id": int,
            "summary": str or dict
        }
    """
    if not ATHENA_AVAILABLE:
        return {"success": False, "error": "athena-client not installed", "concept_id": concept_id, "summary": None}
    
    try:
        # Get basic details as summary
        client = AthenaClient()
        concept = client.details(concept_id)

        if concept:
            summary = {"details": _concept_to_camel_details(concept)}
            return {"success": True, "concept_id": concept_id, "summary": summary}
        else:
            return {
                "success": False,
                "concept_id": concept_id,
                "error": "Concept not found"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "concept_id": concept_id,
            "summary": None
        }


def get_concept_graph(
    ctx: RunContext[Dict[str, Any]],
    concept_id: int
) -> Dict[str, Any]:
    """
    Fetch concept hierarchy/graph (ancestors and descendants).
    
    Note: This is a simplified version that uses relationships.
    For full hierarchy traversal, use get_concept_relationships repeatedly.
    
    Returns:
        {
            "success": bool,
            "concept_id": int,
            "ancestors": [int],
            "descendants": [int]
        }
    """
    if not ATHENA_AVAILABLE:
        return {"success": False, "error": "athena-client not installed", "concept_id": concept_id, "ancestors": [], "descendants": []}
    
    try:
        client = AthenaClient()
        relationships = client.relationships(concept_id)  # Fixed: use relationships() not get_relationships()
        
        ancestors = []
        descendants = []
        
        for rel in relationships:
            rel_name = rel.name if hasattr(rel, 'name') else str(rel)
            target_id = rel.targetId if hasattr(rel, 'targetId') else None
            
            if rel_name == "Is a" and target_id:
                # This concept "Is a" target, so target is an ancestor
                ancestors.append(target_id)
            elif rel_name == "Subsumes" and target_id:
                # This concept "Subsumes" target, so target is a descendant
                descendants.append(target_id)
        
        return {
            "success": True,
            "concept_id": concept_id,
            "ancestors": ancestors,
            "descendants": descendants
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "concept_id": concept_id,
            "ancestors": [],
            "descendants": []
        }


def search_initial_candidates(concept_sets: List[Dict[str, Any]], top_k: int = 20) -> List[Dict[str, Any]]:
    """
    Search for initial concept candidates for each concept set.
    
    Args:
        concept_sets: List of concept sets with queries to search
        top_k: Maximum number of candidates to return per query (default: 20)
        
    Returns:
        Updated concept sets with initial candidates
    """
    if not ATHENA_AVAILABLE:
        print("⚠️  Athena not available, skipping initial candidate search")
        return concept_sets
    
    try:
        client = AthenaClient()
        
        for concept_set in concept_sets:
            queries = concept_set.get("queries", [])
            all_candidates = []
            
            for query in queries:
                try:
                    results = client.search(query)
                    
                    # Filter by domain if specified
                    domain = concept_set.get("domain")
                    
                    for concept in results[:top_k]:  # Limit to top_k per query
                        # Apply domain filter
                        if domain and concept.domain != domain:
                            continue
                        
                        # If non-standard, try to map to standard via relationships
                        if concept.standardConcept != ConceptType.STANDARD:
                            mapped_ids = _map_to_standard_ids(client, int(concept.id))
                            for mid in mapped_ids:
                                try:
                                    det = client.details(mid)
                                    det_dict = _concept_to_dict(det)
                                    if domain and det_dict.get("domain_id") != domain:
                                        continue
                                    all_candidates.append(det_dict)
                                except Exception:
                                    continue
                            continue

                        # Standard concept - accept
                        all_candidates.append(_concept_to_dict(concept))
                        
                except Exception as e:
                    print(f"Warning: Search failed for query '{query}': {e}")
                    continue
            
            # Remove duplicates based on concept_id
            seen = set()
            unique_candidates = []
            for candidate in all_candidates:
                concept_id = candidate.get("concept_id")
                if concept_id and concept_id not in seen:
                    seen.add(concept_id)
                    unique_candidates.append(candidate)
            
            concept_set["initial_candidates"] = unique_candidates
        
        return concept_sets
    except Exception as e:
        print(f"Error in search_initial_candidates: {e}")
        return concept_sets


def format_for_atlas(concept_sets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format concept sets for ATLAS import.
    
    Args:
        concept_sets: List of concept sets with included_concepts
        
    Returns:
        {
            "concept_sets": [...],  # ATLAS-compatible format
            "summary": {...}
        }
    """
    formatted_sets = []
    
    for cs in concept_sets:
        formatted_set = {
            "name": cs.get("name", "Unnamed Concept Set"),
            "expression": {
                "items": []
            }
        }
        
        # Add included concepts
        for concept in cs.get("included_concepts", []):
            formatted_set["expression"]["items"].append({
                "concept": {
                    "CONCEPT_ID": concept.get("concept_id"),
                    "CONCEPT_NAME": concept.get("concept_name"),
                    "DOMAIN_ID": concept.get("domain_id"),
                    "VOCABULARY_ID": concept.get("vocabulary_id"),
                    "STANDARD_CONCEPT": concept.get("standard_concept"),
                    "CONCEPT_CODE": concept.get("concept_code")
                },
                "isExcluded": False,
                "includeDescendants": cs.get("include_descendants", True),
                "includeMapped": False
            })
        
        # Add excluded concepts
        for concept in cs.get("excluded_concepts", []):
            formatted_set["expression"]["items"].append({
                "concept": {
                    "CONCEPT_ID": concept.get("concept_id"),
                    "CONCEPT_NAME": concept.get("concept_name"),
                    "DOMAIN_ID": concept.get("domain_id"),
                    "VOCABULARY_ID": concept.get("vocabulary_id"),
                    "STANDARD_CONCEPT": concept.get("standard_concept"),
                    "CONCEPT_CODE": concept.get("concept_code")
                },
                "isExcluded": True,
                "includeDescendants": cs.get("include_descendants", True),
                "includeMapped": False
            })
        
        formatted_sets.append(formatted_set)
    
    # Calculate summary statistics
    total_concepts = sum(len(cs.get("included_concepts", [])) for cs in concept_sets)
    total_excluded = sum(len(cs.get("excluded_concepts", [])) for cs in concept_sets)
    
    return {
        "concept_sets": formatted_sets,
        "summary": {
            "total_concept_sets": len(formatted_sets),
            "total_included_concepts": total_concepts,
            "total_excluded_concepts": total_excluded
        }
    }
