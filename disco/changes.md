 
Below are focused fixes so the analyzer actually reads concept pages, discovers the map, and returns the Standard concept.

---

# What’s wrong (from your run)

1. **Queue never produced a batch**
   `visit_count: 0` + `history: []` → `queue_next_batch` returned `has_batch: false` (or a limit flag flipped) on the very first loop, so `fetch_batch` and `analyze_batch` never ran.

2. **Likely root causes (very common)**

   * `queue_init` got an input shape it didn’t expect. You pass the **entire** `{message, candidate_ids}` object; many queue tools expect **just** the array.
   * Seed depths aren’t initialized (e.g., `depth = 0`), so a depth check may treat them as invalid and flip `depth_limit_hit = true`.
   * `queue_next_batch` doesn’t set `has_batch` correctly when seeds exist.
   * The loop’s `condition_expression` depends on flags that were never set up by the tool.

---

# Minimal, surgical fixes (drop-in)

## 1) Feed the queue the array, not the whole object

Change:

```yaml
- kind: step
  name: queue_init
  uses: "skills.custom_tools:queue_init"
  input: "{{ steps.collect_candidates.output }}"
```

to:

```yaml
- kind: step
  name: queue_init
  uses: "skills.custom_tools:queue_init"
  input: "{{ steps.collect_candidates.output.candidate_ids | tojson }}"
  updates_context: true
  config:
    max_depth: 2
    max_visits: 50
    batch_size: 3
```

**Contract for `queue_init`** (make sure your skill does this):

* Saves `frontier.queue = [{id, depth:0}, …]` in insertion order.
* Sets `frontier.visited = []`, `frontier.visits = 0`, `resolved = false`.
* No priority magic here—just depth=0 and FIFO (deterministic).

## 2) Make `queue_next_batch` output explicit

Your loop predicates rely on these flags; the tool must emit them. Ensure the tool returns:

```json
{
  "has_batch": true,
  "ids": [46256077, 45893370, 37083370],
  "depths": [0, 0, 0],
  "limit_reached": false,
  "depth_limit_hit": false,
  "resolved": false
}
```

Seed depths **must be 0**. If your tool currently leaves them undefined/None, some validators flip `depth_limit_hit = true`, short-circuiting the loop.

## 3) Keep the loop guard but add timeouts

```yaml
- kind: loop
  name: resolve_queue
  loop:
    max_loops: 60
    body:
      - kind: step
        name: queue_next_batch
        uses: "skills.custom_tools:queue_next_batch"
        updates_context: true

      - kind: conditional
        name: process_batch
        condition_expression: "steps.queue_next_batch.output.has_batch and not steps.queue_next_batch.output.limit_reached and not steps.queue_next_batch.output.depth_limit_hit and not steps.queue_next_batch.output.resolved"
        branches:
          true:
            - kind: step
              name: fetch_batch
              uses: "skills.custom_tools:fetch_athena_concept_info_batch"
              input: "{{ steps.queue_next_batch.output.ids | tojson }}"
              config:
                timeout_ms: 12000
                max_retries: 0

            - kind: step
              name: analyze_batch
              uses: "agents.concept_analyzer_batch"
              input: |
                Search term: {{ context.initial_prompt }}
                Queue depths: {{ steps.queue_next_batch.output.depths | tojson }}
                Candidate concepts (aligned with the queue order):
                {{ steps.fetch_batch.output.concepts | tojson }}
              processing:
                structured_output: openai_json
                schema:  # (keep your schema)
              config:
                timeout_ms: 12000

            - kind: step
              name: update_queue
              uses: "skills.custom_tools:update_queue_from_batch"
              input: |
                {
                  "ids": {{ steps.queue_next_batch.output.ids | tojson }},
                  "depths": {{ steps.queue_next_batch.output.depths | tojson }},
                  "concepts": {{ steps.fetch_batch.output.concepts | tojson }},
                  "decisions": {{ steps.analyze_batch.output.decisions | tojson }}
                }
              updates_context: true

          false:
            - kind: step
              name: skip_batch
              agent:
                id: "flujo.builtins.passthrough"
              input: "{{ steps.queue_next_batch.output }}"

    exit_expression: "not steps.queue_next_batch.output.has_batch or steps.queue_next_batch.output.limit_reached or steps.queue_next_batch.output.depth_limit_hit or steps.queue_next_batch.output.resolved"
```

## 4) Analyzer must propose the Standard via “Maps to”

You already ask for `suggested_new_candidates` based on relationships. Keep that, but add one sentence to the analyzer prompt so it **always** pushes the Standard when it sees a Non-standard → Standard map:

> “When a candidate is Non-standard and shows a ‘Non-standard to Standard map (OMOP)’ relationship, **include the mapped Standard concept\_id in `suggested_new_candidates`**, and explain it in `relationship_hint` (e.g., ‘Maps to SNOMED 4046213’).”

## 5) `update_queue_from_batch` must recognize a winner

Make sure the tool sets `resolved=true` when any decision in the batch satisfies:

* `is_standard == true` **and**
* `is_correct_for_term == true`

Also, for any Non-standard analyzed (e.g., **46256077**), when the analyzer returns a Standard suggestion (e.g., **4046213**) the tool should enqueue it at `depth + 1` unless already visited/queued.

**Deterministic enqueue rule** (no scores): `(depth ASC, concept_id ASC)` is enough here, because the agent already reasons which to add.

## 6) Add basic instrumentation (helps verify)

* In `queue_next_batch` log the first 10 `ids` remaining and their `depths`.
* After `update_queue_from_batch`, log: `visits`, `queue_length`, `resolved`, and **which** concept resolved it.

---

# Sanity check for your specific case

With the fixes above, a healthy first two iterations should look like:

1. **Batch 1 popped:** `[46256077, …]` (depth 0)

   * Fetch returns MeSH 46256077 details including **Non-standard → Standard map** to **SNOMED 4046213** (as in your screenshot).
   * Analyzer decision for 46256077 (example):

     ```json
     {
       "concept_id": 46256077,
       "is_standard": false,
       "is_correct_for_term": true,
       "suggested_new_candidates": [4046213],
       "relationship_hint": "Non-standard to Standard map (OMOP) → 4046213",
       "reasoning": "Exact lexical match to term in MeSH; page shows direct OMOP map to SNOMED Standard 4046213 Lennox-Gastaut syndrome."
     }
     ```
   * `update_queue_from_batch` enqueues **4046213** at depth 1.

2. **Next batch contains 4046213**

   * Analyzer returns:

     ```json
     {
       "concept_id": 4046213,
       "is_standard": true,
       "is_correct_for_term": true,
       "suggested_new_candidates": [],
       "relationship_hint": "Standard exact match",
       "reasoning": "SNOMED Standard concept ‘Lennox-Gastaut syndrome’ directly represents the search term."
     }
     ```
   * `update_queue_from_batch` sets `resolved=true` and stores `winner=4046213`.
   * Loop exits; `finalize_resolution` returns that concept.

If you still see `visit_count: 0` after these changes, the issue is 100% in `queue_init` / `queue_next_batch` contract (input shape, missing depths, or flags). Fix those and you’ll get the expected Standard concept.

---

# Tiny prompt tweak (optional but useful)

**`concept_analyzer_batch` — add:**

* “Return `decisions` in the **exact same order** as the input candidates.”
* “When a Non-standard concept has a direct map to a Standard concept, add that Standard concept\_id to `suggested_new_candidates` and note it in `relationship_hint`.”

 