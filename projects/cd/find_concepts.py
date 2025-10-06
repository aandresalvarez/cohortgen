"""
OMOP Concept Discovery - Intelligent Pydantic AI Version

This script maps clinical cohort definitions to OMOP standard concepts using ATHENA.

Intelligent Workflow:
1. Takes a cohort definition (from Stage 1 clarification or manual input)
2. Decomposes it into concept sets (conditions, drugs, procedures, etc.)
3. LLM intelligently seeds candidate_ids from ATHENA search results
4. Bounded queue-based exploration with relationship-driven refinement
5. Batch concept analysis with suggested_new_candidates
6. Early resolution for exact/strong Standard concept matches
7. Outputs final concept sets in ATLAS-compatible format

Key Features:
- LLM candidate aggregation: Smart selection of up to 12 candidates per concept set
- Queue-based exploration: Bounded depth/visits with stagnation guard
- Relationship intelligence: Maps to, Is a, Subsumes, Replaced by, etc.
- Batch analysis: Agent evaluates concepts in batches with suggestions
- Early resolution: Short-circuit on exact Standard matches
- Domain-aware gating: Conditions→SNOMED, Drugs→RxNorm, Measurements→LOINC
- Concept minification: Reduces LLM tokens while preserving essentials
- Deterministic outcomes: resolved/fallback/unresolved with evidence
"""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent

# Import tools
from tools import (
    format_for_atlas,
    get_concept_details,
    get_concept_relationships,
    search_athena,
)

# Load environment variables
load_dotenv()


# ============================================================================
# Constants
# ============================================================================

MAX_DEPTH_DEFAULT = 2
MAX_VISITS_DEFAULT = 50
BATCH_SIZE_DEFAULT = 3
HISTORY_LIMIT = 120

# Runtime knobs (tunable via env for speed)
MAX_CONCEPT_SETS = int(os.getenv("MAX_CONCEPT_SETS", "5"))
MAX_QUERIES_PER_SET = int(os.getenv("MAX_QUERIES_PER_SET", "3"))
SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", "8"))
PER_SET_TIME_LIMIT_SEC = int(os.getenv("PER_SET_TIME_LIMIT_SEC", "15"))
MAX_ACCEPTED_PER_SET = int(os.getenv("MAX_ACCEPTED_PER_SET", "3"))
PARALLEL_CONCEPT_SETS = int(os.getenv("PARALLEL_CONCEPT_SETS", "5"))  # Phase 1: Parallelization

# Phase 1 Optimization: Smart vocabulary filtering by domain
DOMAIN_VOCAB_MAP = {
    "Condition": ["SNOMED"],  # Focus on SNOMED for conditions
    "Drug": ["RxNorm"],  # Focus on RxNorm for drugs
    "Procedure": ["SNOMED", "CPT4"],  # SNOMED and CPT for procedures
    "Measurement": ["LOINC"],  # LOINC for measurements
    "Observation": ["SNOMED"],  # SNOMED for observations
}


# ============================================================================
# Pydantic Models
# ============================================================================


class ConceptSet(BaseModel):
    """A concept set to build for ATLAS."""

    name: str = Field(description="Name of the concept set")
    intent: str = Field(description="Clinical intent/description")
    domain: str = Field(description="OMOP domain: Condition, Drug, Procedure, etc.")
    vocabulary: List[str] = Field(
        default_factory=lambda: [], description="Preferred vocabularies: SNOMED, RxNorm, etc."
    )
    queries: List[str] = Field(description="Search queries to find concepts")
    include_descendants: bool = Field(
        default=True, description="Include descendant concepts in hierarchy"
    )
    standard_only: bool = Field(default=True, description="Only include standard concepts")


class ConceptPlan(BaseModel):
    """Decomposition of cohort definition into concept sets."""

    concept_sets: List[ConceptSet]


class CandidateSelection(BaseModel):
    """LLM's intelligent selection of candidate concept IDs."""

    message: str = Field(description="Reasoning for candidate selection")
    candidate_ids: List[int] = Field(
        max_length=12, description="Ordered list of candidate concept IDs"
    )


class ConceptDecision(BaseModel):
    """Agent's decision for a single concept."""

    concept_id: int
    is_standard: bool
    is_correct_for_term: bool
    suggested_new_candidates: List[int] = Field(default_factory=list)
    relationship_hint: str = ""
    reasoning: str


class BatchAnalysis(BaseModel):
    """Agent's analysis of a batch of concepts."""

    decisions: List[ConceptDecision] = Field(max_length=3)


class QueueItem(BaseModel):
    """Item in the exploration queue."""

    concept_id: int
    depth: int = 0


class QueueState(BaseModel):
    """State of the exploration queue."""

    pending: List[QueueItem] = Field(default_factory=list)
    visited: List[int] = Field(default_factory=list)
    depth_map: Dict[str, int] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    iteration: int = 0
    visit_count: int = 0
    resolved: bool = False
    resolved_concept: Optional[Dict[str, Any]] = None
    best_fallback: Optional[Dict[str, Any]] = None
    max_depth: int = MAX_DEPTH_DEFAULT
    max_visits: int = MAX_VISITS_DEFAULT
    batch_size: int = BATCH_SIZE_DEFAULT
    stop_reason: Optional[str] = None
    initial_candidates: List[int] = Field(default_factory=list)
    initial_message: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    last_head_id: Optional[int] = None
    stagnation_count: int = 0
    accepted_concepts: List[Dict[str, Any]] = Field(default_factory=list)


class ResolutionOutcome(BaseModel):
    """Final resolution outcome."""

    status: Literal["resolved", "fallback", "unresolved"]
    concept: Optional[Dict[str, Any]] = None
    reason: str
    visit_count: int
    stop_reason: Optional[str] = None
    pending_candidates: List[int] = Field(default_factory=list)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: Optional[Dict[str, Any]] = None
    accepted_concepts: List[Dict[str, Any]] = Field(default_factory=list)


class FinalConceptSets(BaseModel):
    """Final output: ATLAS-compatible concept sets."""

    concept_sets: List[Dict[str, Any]]


# ============================================================================
# Agents
# ============================================================================

# Phase 2C: Use gpt-5-mini for decomposition (faster than gpt-5, good quality)
DECOMPOSER_MODEL = os.getenv("DECOMPOSER_MODEL", "gpt-5-mini")

# Decomposer Agent: Breaks down cohort definition into concept sets
decomposer_agent = Agent(  # type: ignore[call-overload]
    f"openai:{DECOMPOSER_MODEL}",
    output_type=ConceptPlan,
    model_settings={"reasoning": {"effort": "medium"}},
    system_prompt="""
You are an expert OMOP/ATLAS cohort designer.

Task: Read the cohort definition and produce a structured plan of concept sets to build in ATHENA.

Strict requirements:
- **No placeholders**: Do NOT emit generic tokens like <CONDITION_NAME> or "TBD"
- **Concrete queries**: Derive actual search terms directly from the cohort definition
- **Domain mapping**: Map clinical concepts to OMOP domains:
  * Conditions/Diagnoses → "Condition" domain (SNOMED vocabulary)
  * Medications → "Drug" domain (RxNorm vocabulary)
  * Procedures → "Procedure" domain (SNOMED, CPT4 vocabularies)
  * Lab tests/measurements → "Measurement" domain (LOINC vocabulary)
  * Observations → "Observation" domain
- **Standard concepts**: Prefer standard_only: true (standard concepts marked 'S')
- **Include descendants**: Set include_descendants: true by default (includes concept hierarchy)
- **Multiple queries**: Provide multiple search query variants for robustness

IMPORTANT FOR LAB TESTS:
- Domain should be "Measurement"
- Primary vocabulary is LOINC
- Include specific test names (e.g., "Influenza virus A RNA", "Influenza virus B RNA")
- Include method variants (e.g., "PCR", "rapid test", "culture")
- DO NOT include just generic "positive test" - be specific about the test type

Output a valid ConceptPlan with concrete, actionable concept sets.
""",
)

# Candidate Aggregator Agent: Intelligently selects candidate IDs from ATHENA search results
# Phase 2C: Use gpt-5-mini for candidate aggregation
AGGREGATOR_MODEL = os.getenv("AGGREGATOR_MODEL", "gpt-5-mini")

candidate_aggregator_agent = Agent(  # type: ignore[call-overload]
    f"openai:{AGGREGATOR_MODEL}",
    output_type=CandidateSelection,
    model_settings={"reasoning": {"effort": "medium"}},
    system_prompt="""
You are a meticulous OMOP concept scout. Review the Athena search payload
and pick up to 12 promising candidate concept IDs.

Ordering rules for `candidate_ids`:
1. Exact or very close lexical match to the search term.
2. Prefer Standard over Non-standard when equally plausible.
3. Vocabulary alignment with the search term's domain.
4. Semantic closeness (synonyms, mappings, clinical equivalence).
5. Deterministic tie breaker: ascending concept_id.

Requirements:
- Remove duplicates and ignore irrelevant or noisy hits (locations, races,
  unrelated conditions, staging codes, etc.).
- Always explain the reasoning for the ordering in `message` using concise,
  evidence-based statements. Do not use numeric scores.
- Return only integers in `candidate_ids`.
- If the Athena response indicates an error or is missing, still produce a best-effort
  non-empty `candidate_ids` list using domain knowledge of OMOP and common SNOMED standards.
  Prefer Standard concepts when possible. Never refuse; provide your best single top candidate
  when uncertain and justify it in `message`.

Output JSON fields:
- `message`: short reasoning summary (mention top candidates explicitly).
- `candidate_ids`: ordered list following the rules above.
""",
)

# Concept Analyzer Agent: Evaluates concepts in batches
concept_analyzer_agent = Agent(  # type: ignore[call-overload]
    "openai:gpt-5-mini",
    output_type=BatchAnalysis,
    model_settings={"reasoning": {"effort": "medium"}},
    system_prompt="""
You are an OMOP domain expert evaluating candidate concepts in batches.

Input format:
- Search term with intent notes.
- Up to three candidate concept JSON objects. If a `summary` object is present, use it as the
  primary source of truth for attributes and relationships. Otherwise, rely on `details` and
  `relationships` fields.
- Depth indicators show how many relationship hops away the candidate is.

For each candidate (preserve input order):
- Determine if the concept is Standard (`is_standard`).
- Judge whether it correctly represents the search term (`is_correct_for_term`).
- Provide explicit reasoning—cite evidence from concept attributes,
  relationships, and the search term. No numeric scores.
- If the concept suggests following relationships (e.g., "Maps to",
  "Is a"), list new candidate concept_ids in `suggested_new_candidates`.
  Only include justified, Standard prospects. Deduplicate locally.
- Set `relationship_hint` to the key relationship/path you followed.

🚀 PHASE 1 OPTIMIZATION - FAST EXIT RULE:
If you find a concept that is:
- Standard concept (standard_concept = 'S')
- Correct domain (matches search intent)
- Name matches perfectly or near-perfectly (e.g., "Type 2 diabetes mellitus" for "type 2 diabetes")
→ Mark is_correct_for_term = TRUE and is_standard = TRUE
→ The system will collect this as an accepted match and may stop exploration early

DO NOT suggest additional candidates or relationships if you already have a perfect standard match!
Focus on quality over exploration depth.

Return `decisions` in the exact same order as the input candidates.
When a candidate is Non-standard and shows a 'Non-standard to Standard map (OMOP)' relationship,
include the mapped Standard concept_id in `suggested_new_candidates` and mention it in `relationship_hint`
(e.g., "Maps to SNOMED 4046213").

Terminate early in your reasoning when you identify a definitive Standard
match, but still return structured decisions for every concept in the batch.
""",
)


# ============================================================================
# Intelligent Workflow Functions
# ============================================================================


def _coerce_int(value: Any) -> Optional[int]:
    """Coerce value to int safely."""
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


def _unique_sorted_ints(values: List[Any], limit: Optional[int] = None) -> List[int]:
    """Deduplicate while preserving input order."""
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


def _extract_maps_to_targets(concept_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract 'Maps to' relationship targets from concept payload."""
    out: List[Dict[str, Any]] = []
    try:
        # Walk through nested structures
        def _walk(obj: Any):
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

        for node in _walk(concept_payload):
            try:
                # Common keys for relationship type
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

                out.append(
                    {
                        "concept_id": coerced,
                        "name": name,
                        "vocabularyId": vocab,
                    }
                )
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


def _minify_concept(concept_data: Dict[str, Any]) -> Dict[str, Any]:
    """Minify concept payload to reduce LLM tokens."""
    # Extract concept ID
    cid = _coerce_int(
        concept_data.get("concept_id") or concept_data.get("conceptId") or concept_data.get("id")
    )

    # Extract minimal details
    minimal_details: Dict[str, Any] = {}
    details_source = concept_data.get("details") or concept_data.get("summary", {}).get(
        "details", {}
    )

    for k in (
        "conceptId",
        "conceptName",
        "standardConcept",
        "domainId",
        "vocabularyId",
        "conceptClassId",
    ):
        v = details_source.get(k)
        if v is not None:
            minimal_details[k] = v

    # Extract Maps to relationships
    maps_to = _extract_maps_to_targets(concept_data)[:8]

    return {
        "concept_id": cid,
        "details": minimal_details,
        "relationships": {
            "maps_to": maps_to,
        },
    }


def _included_from_details(
    concept_id: Optional[int], details: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Build an included_concepts entry from CamelCase details.

    Provides the fields expected downstream by Stage 3.
    """
    try:
        cid = _coerce_int(details.get("conceptId") or concept_id)
        if cid is None:
            return None
        return {
            "concept_id": cid,
            "concept_name": details.get("conceptName", ""),
            "domain_id": details.get("domainId", ""),
            "vocabulary_id": details.get("vocabularyId", ""),
            "standard_concept": details.get("standardConcept", ""),
            "concept_code": details.get("conceptCode", ""),
        }
    except Exception:
        return None


def _try_short_circuit_resolution(
    concepts: List[Dict[str, Any]], search_term: str, queue_state: QueueState
) -> Optional[Dict[str, Any]]:
    """Try to resolve immediately with short-circuit logic."""

    # Normalize search term
    def _norm(s: Any) -> str:
        try:
            return " ".join(str(s or "").strip().lower().split())
        except Exception:
            return ""

    term_norm = _norm(search_term)
    sig_tokens = [t for t in term_norm.split(" ") if len(t) >= 3]

    def _tokens_match(name: Any) -> bool:
        s = _norm(name)
        if not sig_tokens:
            return False
        return all(tok in s for tok in sig_tokens)

    # Check for exact/strong Standard matches
    for concept in concepts:
        concept_map = concept if isinstance(concept, dict) else {}
        details = concept_map.get("details") or concept_map.get("summary", {}).get("details", {})

        if not isinstance(details, dict):
            continue

        std = str(details.get("standardConcept", "")).lower() == "standard"
        vocab = str(details.get("vocabularyId", "")).upper()
        str(details.get("domainId", ""))
        cls = str(details.get("conceptClassId", ""))
        name = details.get("name")
        tmp_syns = details.get("synonyms")
        if isinstance(tmp_syns, list):
            raw_syns = tmp_syns
        else:
            raw_syns = []
        syns: List[str] = [str(x) for x in raw_syns]
        names: List[str]
        if name is not None:
            names = [str(name)] + syns
        else:
            names = syns

        exact_match = any(_norm(n) == term_norm for n in names)
        strong_token_match = any(_tokens_match(n) for n in names)
        cid = _coerce_int(details.get("id") or concept_map.get("concept_id"))

        if std and (exact_match or strong_token_match):
            # Domain-specific short-circuit rules
            if vocab == "SNOMED" and cls in {"Disorder", "Clinical Finding"}:
                return {
                    "concept_id": cid,
                    "reason": "SNOMED condition exact/strong match",
                    "evidence": {"match_type": "exact" if exact_match else "strong_token"},
                }
            elif vocab == "LOINC" and cls in {"Component", "LOINC Component"}:
                return {
                    "concept_id": cid,
                    "reason": "LOINC component exact/strong match",
                    "evidence": {"match_type": "exact" if exact_match else "strong_token"},
                }
            elif vocab == "CPT4":
                return {
                    "concept_id": cid,
                    "reason": "CPT4 procedure exact/strong match",
                    "evidence": {"match_type": "exact" if exact_match else "strong_token"},
                }
            elif vocab in {"RXNORM", "RXNORM EXTENSION"} and cls in {
                "Ingredient",
                "Precise Ingredient",
            }:
                return {
                    "concept_id": cid,
                    "reason": "RxNorm ingredient exact/strong match",
                    "evidence": {"match_type": "exact" if exact_match else "strong_token"},
                }

    return None


def _queue_next_batch(queue_state: QueueState) -> Dict[str, Any]:
    """Get next batch from queue."""
    pending = queue_state.pending
    visit_count = queue_state.visit_count
    max_visits = queue_state.max_visits
    max_depth = queue_state.max_depth
    batch_size = queue_state.batch_size

    if queue_state.resolved:
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
        return {
            "ids": [],
            "depths": [],
            "is_empty": True,
            "has_batch": False,
            "batch_count": 0,
            "limit_reached": True,
            "depth_limit_hit": False,
            "resolved": queue_state.resolved,
            "queue_length": len(pending),
            "visit_count": visit_count,
        }

    if not pending:
        return {
            "ids": [],
            "depths": [],
            "is_empty": True,
            "has_batch": False,
            "batch_count": 0,
            "limit_reached": False,
            "depth_limit_hit": False,
            "resolved": queue_state.resolved,
            "queue_length": 0,
            "visit_count": visit_count,
        }

    first_depth = pending[0].depth if pending else 0
    if first_depth > max_depth:
        return {
            "ids": [],
            "depths": [],
            "is_empty": True,
            "has_batch": False,
            "batch_count": 0,
            "limit_reached": False,
            "depth_limit_hit": True,
            "resolved": queue_state.resolved,
            "queue_length": 0,
            "visit_count": visit_count,
        }

    remaining_slots = max_visits - visit_count
    effective_batch = min(batch_size, remaining_slots)
    ids: List[int] = []
    depths: List[int] = []
    new_pending: List[QueueItem] = []

    for item in pending:
        if len(ids) < effective_batch and item.depth <= max_depth:
            ids.append(item.concept_id)
            depths.append(item.depth)
            continue
        new_pending.append(item)

    queue_state.pending = new_pending
    queue_state.iteration += 1

    return {
        "ids": ids,
        "depths": depths,
        "is_empty": not ids,
        "has_batch": bool(ids),
        "batch_count": len(ids),
        "limit_reached": False,
        "depth_limit_hit": False,
        "resolved": queue_state.resolved,
        "queue_length": len(new_pending),
        "visit_count": visit_count,
    }


def _update_queue_from_batch(
    queue_state: QueueState,
    ids: List[int],
    depths: List[int],
    concepts: List[Dict[str, Any]],
    decisions: List[ConceptDecision],
) -> None:
    """Update queue state from batch analysis."""
    # Mark as visited
    for cid in ids:
        if cid not in queue_state.visited:
            queue_state.visited.append(cid)
        queue_state.visit_count += 1

    # Remove processed items from pending
    processed_ids = set(ids)
    queue_state.pending = [
        item for item in queue_state.pending if item.concept_id not in processed_ids
    ]

    # Collect accepted anchors (multiple)
    for i, decision in enumerate(decisions):
        if decision.is_standard and decision.is_correct_for_term:
            concept_map = concepts[i] if i < len(concepts) else {}
            details = concept_map.get("details", {})
            inc = _included_from_details(decision.concept_id, details)
            if inc is None:
                continue
            # Deduplicate by concept_id
            if all(
                (_coerce_int(x.get("concept_id")) != decision.concept_id)
                for x in queue_state.accepted_concepts
            ):
                queue_state.accepted_concepts.append(inc)

    # Add suggested candidates
    for i, decision in enumerate(decisions):
        depth = depths[i] if i < len(depths) else 0
        for suggested_id in decision.suggested_new_candidates:
            if suggested_id not in queue_state.visited and suggested_id not in [
                item.concept_id for item in queue_state.pending
            ]:
                child_depth = depth + 1
                if child_depth <= queue_state.max_depth:
                    queue_state.pending.append(
                        QueueItem(concept_id=suggested_id, depth=child_depth)
                    )
                    queue_state.depth_map[str(suggested_id)] = child_depth


def _finalize_resolution(queue_state: QueueState) -> ResolutionOutcome:
    """Finalize resolution outcome."""
    if queue_state.accepted_concepts:
        return ResolutionOutcome(
            status="resolved",
            concept=None,
            reason=queue_state.stop_reason or "accepted_matches",
            visit_count=queue_state.visit_count,
            stop_reason=queue_state.stop_reason,
            pending_candidates=[item.concept_id for item in queue_state.pending],
            history=queue_state.history,
            evidence=queue_state.evidence,
            accepted_concepts=queue_state.accepted_concepts,
        )
    elif queue_state.best_fallback:
        return ResolutionOutcome(
            status="fallback",
            concept=queue_state.best_fallback,
            reason="best_nonstandard_match",
            visit_count=queue_state.visit_count,
            stop_reason=queue_state.stop_reason,
            pending_candidates=[item.concept_id for item in queue_state.pending],
            history=queue_state.history,
            evidence=queue_state.evidence,
        )
    else:
        return ResolutionOutcome(
            status="unresolved",
            concept=None,
            reason=queue_state.stop_reason or "exhausted",
            visit_count=queue_state.visit_count,
            stop_reason=queue_state.stop_reason,
            pending_candidates=[item.concept_id for item in queue_state.pending],
            history=queue_state.history,
            evidence=queue_state.evidence,
        )


# ============================================================================
# Main Workflow
# ============================================================================


def _process_single_concept_set(
    concept_set,
    max_visits: int,
    max_depth: int,
    batch_size: int,
    max_queries: int = MAX_QUERIES_PER_SET,
) -> Dict[str, Any]:
    """
    Process a single concept set (extracted for Phase 1 parallelization).
    
    This function contains the logic for searching, seeding, and exploring
    a single concept set. It's extracted to enable ThreadPoolExecutor parallelization.
    
    Phase 2B: Added max_queries parameter for fast mode support.
    """
    print(f"\nProcessing: {concept_set.name}")

    # Search ATHENA for each query
    all_search_results = []
    for query in concept_set.queries[:max_queries]:
        print(f"    Searching: {query}")
        try:
            # Phase 1: Smart vocabulary filtering by domain
            smart_vocab = DOMAIN_VOCAB_MAP.get(concept_set.domain, concept_set.vocabulary)
            search_result = search_athena(
                ctx={},
                query=query,
                domain=concept_set.domain,
                vocabulary=smart_vocab if smart_vocab else concept_set.vocabulary,
                standard_only=concept_set.standard_only,
                top_k=SEARCH_TOP_K,
            )
            if search_result.get("success") and search_result.get("candidates"):
                all_search_results.extend(search_result["candidates"])
                print(f"      ✅ Found {len(search_result['candidates'])} candidates")
            else:
                print(
                    f"      ⚠️  No candidates found: {search_result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            print(f"      ❌ Search failed: {e}")
            continue

    if not all_search_results:
        print(f"  ⚠️  No search results for {concept_set.name}")
        return {
            "name": concept_set.name,
            "intent": concept_set.intent,
            "domain": concept_set.domain,
            "included_concepts": [],
            "excluded_concepts": [],
        }

    # LLM intelligently selects candidate IDs
    print("  🤖 LLM candidate selection...")
    try:
        selection_result = candidate_aggregator_agent.run_sync(
            f"Search term: {concept_set.name}\nIntent: {concept_set.intent}\nDomain: {concept_set.domain}\nAthena results: {json.dumps(all_search_results, indent=2)}"
        )
        selection = selection_result.output
    except Exception as e:
        print(f"  ❌ LLM selection failed: {e}")
        selection = CandidateSelection(
            message="Fallback selection due to LLM error",
            candidate_ids=[
                c.get("concept_id") for c in all_search_results[:5] if c.get("concept_id")
            ],
        )

    print(f"  ✅ Selected {len(selection.candidate_ids)} candidates: {selection.message}")

    # Initialize queue with selected candidates
    queue_state = QueueState(
        pending=[QueueItem(concept_id=cid, depth=0) for cid in selection.candidate_ids],
        visited=[],
        depth_map={str(cid): 0 for cid in selection.candidate_ids},
        max_depth=max_depth,
        max_visits=max_visits,
        batch_size=batch_size,
        initial_candidates=selection.candidate_ids,
        initial_message=selection.message,
    )

    # Queue-based exploration
    print(
        f"  [Step 3] Queue-based exploration (max_depth={max_depth}, max_visits={max_visits})"
    )

    iteration = 0
    start_time = time.time()
    max_iteration_time = PER_SET_TIME_LIMIT_SEC

    while (
        not queue_state.resolved
        and queue_state.visit_count < max_visits
        and queue_state.pending
    ):
        iteration += 1

        if time.time() - start_time > max_iteration_time:
            print(f"    ⏰ Timeout reached ({max_iteration_time}s), exiting")
            queue_state.stop_reason = "timeout"
            break

        batch_info = _queue_next_batch(queue_state)
        if not batch_info["has_batch"]:
            break

        ids = batch_info["ids"]
        depths = batch_info["depths"]

        print(f"    [Iteration {iteration}] Processing batch: {ids} (depths: {depths})")

        # Phase 1: Batch fetch concept details
        print(f"      Fetching details for {len(ids)} concepts (batched)...")
        all_details = {}
        try:
            batch_details_result = get_concept_details(ctx={}, concept_ids=ids)
            if batch_details_result.get("success"):
                all_details = {
                    c["concept_id"]: c 
                    for c in batch_details_result.get("concepts", [])
                }
        except Exception as e:
            print(f"        ⚠️  Batch details failed: {e}, falling back to individual")

        concepts = []
        for cid in ids:
            try:
                details = all_details.get(cid, {})
                if not details:
                    details_result = get_concept_details(ctx={}, concept_ids=[cid])
                    details = (
                        details_result.get("concepts", [{}])[0]
                        if details_result.get("success")
                        else {}
                    )
                
                relationships_result = get_concept_relationships(ctx={}, concept_id=cid)

                concept_data = {
                    "concept_id": cid,
                    "details": details,
                    "relationships": (
                        relationships_result.get("relationships", [])
                        if relationships_result.get("success")
                        else []
                    ),
                }
                concepts.append(concept_data)
            except Exception as e:
                print(f"        ❌ Failed to fetch concept {cid}: {e}")
                concepts.append({"concept_id": cid, "details": {}, "relationships": []})

        short_circuit = _try_short_circuit_resolution(concepts, concept_set.name, queue_state)
        if short_circuit:
            print(f"    ✅ Found strong match candidate: {short_circuit['reason']}")
            sc_id = _coerce_int(short_circuit.get("concept_id"))
            if sc_id is not None:
                matched = next(
                    (c for c in concepts if _coerce_int(c.get("concept_id")) == sc_id), None
                )
                if matched:
                    inc = _included_from_details(sc_id, matched.get("details", {}))
                    if inc and all(
                        (_coerce_int(x.get("concept_id")) != sc_id)
                        for x in queue_state.accepted_concepts
                    ):
                        queue_state.accepted_concepts.append(inc)
            if len(queue_state.accepted_concepts) >= MAX_ACCEPTED_PER_SET:
                queue_state.stop_reason = "enough_matches"
                break

        minified_concepts = [_minify_concept(c) for c in concepts]

        print("      🤖 LLM batch analysis...")
        try:
            analysis_prompt = f"""
Search term: {concept_set.name}
Intent: {concept_set.intent}
Domain: {concept_set.domain}
Queue depths: {depths}
Candidate concepts (aligned with the queue order):
{json.dumps(minified_concepts, indent=2)}
"""
            analysis_result = concept_analyzer_agent.run_sync(analysis_prompt)
            decisions = analysis_result.output.decisions
        except Exception as e:
            print(f"        ❌ LLM analysis failed: {e}")
            decisions = []
            for _i, cid in enumerate(ids):
                decisions.append(
                    ConceptDecision(
                        concept_id=cid,
                        is_standard=False,
                        is_correct_for_term=False,
                        reasoning=f"Fallback decision due to LLM error: {e}",
                    )
                )

        print(f"    ✅ Batch analysis complete: {len(decisions)} decisions")
        for decision in decisions:
            print(
                f"      - {decision.concept_id}: {'✅' if decision.is_standard and decision.is_correct_for_term else '❌'} {decision.reasoning[:100]}..."
            )

        _update_queue_from_batch(queue_state, ids, depths, concepts, decisions)

        if len(queue_state.accepted_concepts) >= MAX_ACCEPTED_PER_SET:
            print(
                f"    ✅ Collected {len(queue_state.accepted_concepts)} accepted anchors; stopping exploration"
            )
            queue_state.stop_reason = "enough_matches"
            break

        if queue_state.pending:
            head_id = queue_state.pending[0].concept_id
            if queue_state.last_head_id == head_id:
                queue_state.stagnation_count += 1
                if queue_state.stagnation_count >= 3:
                    print("    ⚠️  Stagnation detected, exiting")
                    queue_state.stop_reason = "stagnation"
                    break
            else:
                queue_state.stagnation_count = 0
            queue_state.last_head_id = head_id

    # Finalize resolution
    outcome = _finalize_resolution(queue_state)
    print(
        f"  ✅ Resolution: {outcome.status} ({outcome.reason}) after {outcome.visit_count} visits"
    )

    # Build final concept set
    included_concepts = []
    if outcome.status == "resolved" and outcome.accepted_concepts:
        included_concepts = outcome.accepted_concepts

    return {
        "name": concept_set.name,
        "intent": concept_set.intent,
        "domain": concept_set.domain,
        "included_concepts": included_concepts,
        "excluded_concepts": [],
        "resolution_outcome": outcome.model_dump(),
    }


def run_intelligent_concept_discovery(
    cohort_definition: str,
    max_visits: int = MAX_VISITS_DEFAULT,
    max_depth: int = MAX_DEPTH_DEFAULT,
    batch_size: int = BATCH_SIZE_DEFAULT,
    fast_mode: bool = False,
) -> Dict[str, Any]:
    """
    Run intelligent concept discovery workflow with LLM seeding and queue-based exploration.
    
    Phase 2B: Fast mode support for 40-60% faster execution with minimal quality loss.

    Args:
        cohort_definition: Clinical description of the cohort (from Stage 1 or manual)
        max_visits: Maximum concept visits
        max_depth: Maximum exploration depth
        batch_size: Batch size for analysis
        fast_mode: Enable fast mode (reduced depth/visits, fewer concept sets)

    Returns:
        ATLAS-compatible concept sets: {"concept_sets": [{name, included_concepts, excluded_concepts}]}
    """
    # Phase 2B: Apply fast mode settings
    if fast_mode or os.getenv("FAST_MODE") == "1":
        max_concept_sets_limit = 3  # Reduced from 5
        max_queries = 2  # Reduced from 3
        max_visits = 20  # Reduced from 50
        max_depth = 1  # Reduced from 2
        batch_size = 5  # Increased from 3
        mode_label = "FAST MODE"
        print("⚡ FAST MODE ENABLED - Optimized for speed")
    else:
        max_concept_sets_limit = MAX_CONCEPT_SETS
        max_queries = MAX_QUERIES_PER_SET
        mode_label = "NORMAL MODE"
    
    print("\n" + "=" * 70)
    print(f"OMOP CONCEPT DISCOVERY - {mode_label}")
    print("=" * 70)
    print(f"\nCohort Definition:\n{cohort_definition}\n")

    # STEP 1: Decompose cohort definition into concept sets
    print("[Step 1] Decomposing cohort definition into concept sets...")
    decompose_result = decomposer_agent.run_sync(cohort_definition)
    plan = decompose_result.output
    # Trim number of concept sets for speed
    plan.concept_sets = plan.concept_sets[:max_concept_sets_limit]

    print(f"\n✅ Decomposed into {len(plan.concept_sets)} concept sets:")
    for i, cs in enumerate(plan.concept_sets, 1):
        print(f"  {i}. {cs.name} ({cs.domain})")
        print(f"     Intent: {cs.intent}")
        print(f"     Queries: {', '.join(cs.queries[:3])}{'...' if len(cs.queries) > 3 else ''}")

    # STEP 2: Intelligent candidate seeding for each concept set
    print("\n[Step 2] Intelligent candidate seeding...")
    print(f"🚀 Phase 1 Optimization: Processing {len(plan.concept_sets)} concept sets in parallel (max_workers={PARALLEL_CONCEPT_SETS})")
    final_concept_sets = []

    # Phase 1: Parallel concept set processing
    with ThreadPoolExecutor(max_workers=PARALLEL_CONCEPT_SETS) as executor:
        futures = {
            executor.submit(
                _process_single_concept_set,
                cs,
                max_visits,
                max_depth,
                batch_size,
                max_queries  # Phase 2B: Pass max_queries for fast mode
            ): cs
            for cs in plan.concept_sets
        }
        
        for future in as_completed(futures):
            concept_set = futures[future]
            try:
                result = future.result()
                final_concept_sets.append(result)
                print(f"✅ Completed: {concept_set.name}")
            except Exception as e:
                print(f"❌ Failed to process {concept_set.name}: {e}")
                # Add empty concept set as fallback
                final_concept_sets.append({
                    "name": concept_set.name,
                    "intent": concept_set.intent,
                    "domain": concept_set.domain,
                    "included_concepts": [],
                    "excluded_concepts": [],
                })


    # Format for ATLAS (separate key) and show counts from raw sets
    atlas_formatted = format_for_atlas(final_concept_sets)

    print("\n[Final Concept Sets]")
    for cs in final_concept_sets:
        included = cs.get("included_concepts", [])
        print(f"  - {cs['name']}: {len(included)} concepts")

    print("\n" + "=" * 70)
    print("✅ INTELLIGENT CONCEPT DISCOVERY COMPLETE")
    print("=" * 70)
    print("\nOutput is ready for ATLAS import!")
    print("Intelligent exploration with LLM seeding and queue-based refinement! 🎉")

    return {"concept_sets": final_concept_sets, "atlas": atlas_formatted}


def run_concept_discovery(cohort_definition: str, max_exploration_steps: int = 5, fast_mode: bool = False) -> Dict[str, Any]:
    """
    Legacy wrapper for backward compatibility.

    Args:
        cohort_definition: Clinical description of the cohort (from Stage 1 or manual)
        max_exploration_steps: Maximum exploration iterations (ignored, uses intelligent workflow)
        fast_mode: Enable fast mode (Phase 2B)

    Returns:
        ATLAS-compatible concept sets: {"concept_sets": [{name, included_concepts, excluded_concepts}]}
    """
    return run_intelligent_concept_discovery(cohort_definition, fast_mode=fast_mode)


def main():
    """Main entry point for interactive concept discovery."""
    print("\n" + "=" * 70)
    print("OMOP CONCEPT DISCOVERY - Pydantic AI Version")
    print("=" * 70)
    print("\nThis tool maps clinical cohort definitions to OMOP standard concepts.")
    print("It uses ATHENA to search and explore OMOP vocabularies.")
    print("\nWorkflow:")
    print("  1. Enter your cohort definition (from Stage 1 or manual)")
    print("  2. Agent decomposes it into concept sets")
    print("  3. Search ATHENA for candidates")
    print("  4. Agent explores and validates")
    print("  5. Get ATLAS-compatible concept sets")

    print("\n" + "-" * 70)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY not found in environment!")
        print("Please set it in your .env file or export it.")
        return

    # Get cohort definition
    print("\nEnter your cohort definition (paste and press Enter):")
    print("(Or type 'demo' for a test run)")
    print("-" * 70)

    user_input = input("> ").strip()

    if user_input.lower() == "demo":
        cohort_definition = """
Adults (18+) with newly diagnosed type 2 diabetes, defined as:
- First diagnosis of type 2 diabetes (SNOMED)
- No prior diagnosis of type 1 diabetes or secondary diabetes
- Age 18 or older at index
- At least 365 days of continuous enrollment before index
- Exclude patients with gestational diabetes
- Exclude patients with prior insulin use (before index)
"""
        print(f"\n[Using demo cohort definition]\n{cohort_definition}")
    else:
        cohort_definition = user_input

    if not cohort_definition:
        print("\n⚠️  No cohort definition provided. Exiting.")
        return

    # Run discovery
    try:
        result = run_concept_discovery(cohort_definition, max_exploration_steps=5)

        # Pretty print result
        print("\n" + "=" * 70)
        print("FINAL OUTPUT (ATLAS-Compatible JSON)")
        print("=" * 70)
        print(json.dumps(result, indent=2))

        # Save to file
        output_file = "concept_sets_output.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Error during concept discovery: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
