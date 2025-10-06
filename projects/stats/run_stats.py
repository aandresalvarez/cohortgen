#!/usr/bin/env python3
"""
Stage 4: Cohort Analytics (BigQuery)

Reads Stage 1–3 outputs and computes basic analytics on the resulting cohort:
- Cohort size
- Gender distribution
- Age-at-index distribution (if index_date derivable)
- Index year distribution

Inputs:
  - projects/run/complete_cohort_output.json (clinical and concept sets)
  - projects/qb/generated_cohort_query.sql (final cohort SQL selecting person_id)

Environment:
  - BIGQUERY_PROJECT_ID (required)
  - OMOP_DATASET_ID (default: bigquery-public-data.cms_synthetic_patient_data_omop)
  - BIGQUERY_LOCATION (default: US)
"""

from __future__ import annotations

import json
import os

# Local analytics generators
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

project_root_for_stats = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root_for_stats / "projects" / "stats"))
from concept_freq import generate_concept_frequency_sql  # noqa: E402
from concept_scan import generate_concept_presence_sql  # noqa: E402
from omop_scan import generate_omop_presence_sql_from_table  # noqa: E402


def _clean_sql(sql: str) -> str:
    sql = sql.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        if lines[0].strip() in ("```sql", "```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        sql = "\n".join(lines)
    # drop trailing semicolon
    if sql.endswith(";"):
        sql = sql[:-1]
    return sql.strip()


def load_files(project_root: Path) -> tuple[str, Dict[str, Any]]:
    sql_path = project_root / "projects" / "qb" / "generated_cohort_query.sql"
    inp_path = project_root / "projects" / "run" / "complete_cohort_output.json"

    if not sql_path.exists():
        raise FileNotFoundError(f"Cohort SQL not found: {sql_path}")
    if not inp_path.exists():
        raise FileNotFoundError(f"Cohort input JSON not found: {inp_path}")

    sql = _clean_sql(sql_path.read_text())
    with open(inp_path, "r") as f:
        data = json.load(f)
    return sql, data


def extract_concept_ids(data: Dict[str, Any], name_contains: List[str]) -> List[int]:
    """Find concept IDs from the first concept set whose name includes any token."""
    concept_sets = data.get("concept_sets", [])
    ids: List[int] = []
    for cs in concept_sets:
        name = str(cs.get("name", "")).lower()
        if any(tok in name for tok in name_contains):
            included = cs.get("included_concepts", [])
            for c in included:
                cid = c.get("concept_id")
                if isinstance(cid, int):
                    ids.append(cid)
            break
    # Dedup
    seen = set()
    out: List[int] = []
    for x in ids:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def build_analytics_queries(
    cohort_sql: str,
    project_id: str,
    dataset: str,
    esrd_ids: Optional[List[int]] = None,
):
    """Return a dictionary of name->SQL queries for analytics."""
    person = f"`{dataset}.person`" if dataset.count(".") else f"`{project_id}.{dataset}.person`"
    cond = (
        f"`{dataset}.condition_occurrence`"
        if dataset.count(".")
        else f"`{project_id}.{dataset}.condition_occurrence`"
    )

    # We will try to reconstruct index_date from ESRD occurrences if ESRD concept IDs provided
    esrd_list = ", ".join(str(x) for x in (esrd_ids or []))
    index_cte = ""
    join_index = ""
    have_index = False
    if esrd_list:
        # Rewritten to use JOIN instead of correlated subquery (BigQuery requirement)
        index_cte = f"""
, index_dates AS (
  SELECT co.person_id, MIN(co.condition_start_date) AS index_date
  FROM {cond} co
  INNER JOIN cohort c ON c.person_id = co.person_id
  WHERE co.condition_concept_id IN ({esrd_list})
  GROUP BY co.person_id
)
"""
        join_index = "LEFT JOIN index_dates i USING(person_id)"
        have_index = True

    # Base cohort CTE
    base_cte = f"""
WITH cohort AS (
{cohort_sql}
)
{index_cte}
""".strip()

    queries = {}

    # 1) Cohort size
    queries["cohort_size"] = (
        f"""
{base_cte}
SELECT COUNT(DISTINCT person_id) AS n
FROM cohort
""".strip()
    )

    # 2) Gender distribution
    queries["by_gender"] = (
        f"""
{base_cte}
SELECT
  CASE p.gender_concept_id
    WHEN 8507 THEN 'male'
    WHEN 8532 THEN 'female'
    ELSE 'unknown'
  END AS gender,
  COUNT(DISTINCT c.person_id) AS n
FROM cohort c
JOIN {person} p ON p.person_id = c.person_id
GROUP BY 1
ORDER BY 1
""".strip()
    )

    # 3) Age-at-index buckets (if index_date available)
    if have_index:
        queries["age_buckets"] = (
            f"""
{base_cte}
SELECT
  CASE
    WHEN EXTRACT(YEAR FROM i.index_date) - p.year_of_birth < 18 THEN '<18'
    WHEN EXTRACT(YEAR FROM i.index_date) - p.year_of_birth BETWEEN 18 AND 39 THEN '18-39'
    WHEN EXTRACT(YEAR FROM i.index_date) - p.year_of_birth BETWEEN 40 AND 64 THEN '40-64'
    WHEN EXTRACT(YEAR FROM i.index_date) - p.year_of_birth BETWEEN 65 AND 74 THEN '65-74'
    ELSE '75+'
  END AS age_bucket,
  COUNT(DISTINCT c.person_id) AS n
FROM cohort c
{join_index}
JOIN {person} p ON p.person_id = c.person_id
GROUP BY 1
ORDER BY 1
""".strip()
        )

        # 4) Index year distribution
        queries["index_year"] = (
            f"""
{base_cte}
SELECT EXTRACT(YEAR FROM i.index_date) AS index_year, COUNT(DISTINCT c.person_id) AS n
FROM cohort c
{join_index}
GROUP BY 1
ORDER BY 1
""".strip()
        )
        
        # 5) Age statistics (for summary cards)
        queries["age_stats"] = (
            f"""
{base_cte}
SELECT
  AVG(EXTRACT(YEAR FROM i.index_date) - p.year_of_birth) AS mean_age,
  APPROX_QUANTILES(EXTRACT(YEAR FROM i.index_date) - p.year_of_birth, 100)[OFFSET(50)] AS median_age,
  STDDEV(EXTRACT(YEAR FROM i.index_date) - p.year_of_birth) AS std_age,
  MIN(EXTRACT(YEAR FROM i.index_date) - p.year_of_birth) AS min_age,
  MAX(EXTRACT(YEAR FROM i.index_date) - p.year_of_birth) AS max_age
FROM cohort c
{join_index}
JOIN {person} p ON p.person_id = c.person_id
""".strip()
        )
        
        # 6) Monthly enrollment trend
        queries["monthly_trend"] = (
            f"""
{base_cte}
SELECT
  FORMAT_DATE('%Y-%m', i.index_date) AS month,
  COUNT(DISTINCT c.person_id) AS n
FROM cohort c
{join_index}
GROUP BY 1
ORDER BY 1
LIMIT 100
""".strip()
        )

    return queries


def main():
    import sys

    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root / "projects" / "shared"))
    from secrets import setup_bigquery_auth  # type: ignore

    try:
        setup_bigquery_auth()
    except Exception:
        pass

    project_root = Path(__file__).parent.parent.parent
    print("\n╔═══════════════════════════════════════════════════════════════════╗")
    print("║                      STAGE 4: ANALYTICS                         ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")

    # Load inputs
    cohort_sql, input_data = load_files(project_root)

    # Env
    project_id = os.getenv("BIGQUERY_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset = os.getenv("OMOP_DATASET_ID", "bigquery-public-data.cms_synthetic_patient_data_omop")
    location = os.getenv("BIGQUERY_LOCATION", "US")

    if not project_id:
        raise RuntimeError("BIGQUERY_PROJECT_ID/GOOGLE_CLOUD_PROJECT not set")

    print(f"Project: {project_id}")
    print(f"Dataset: {dataset}")
    print(f"Location: {location}")

    # Extract ESRD concept IDs for index-date derivation
    esrd_ids = extract_concept_ids(input_data, ["end-stage renal disease", "esrd"]) or []
    if esrd_ids:
        print(f"Found ESRD concept IDs for index derivation: {esrd_ids}\n")
    else:
        print("No ESRD concept IDs found; age/index-year analytics will be skipped.\n")

    # Prepare built-in analytics queries
    queries = build_analytics_queries(cohort_sql, project_id, dataset, esrd_ids)

    # Run queries
    from google.cloud import bigquery  # type: ignore

    client = bigquery.Client(project=project_id, location=location)

    results: Dict[str, Any] = {}

    for name, sql in queries.items():
        print(f"[Run] {name}...")
        job = client.query(sql)
        rows = list(job.result())
        # Convert to simple Python structures
        items = []
        for r in rows:
            items.append({k: r[k] for k in r.keys()})
        results[name] = items
        # Echo
        print(f"  → {items}")

    # Discover existing tables to avoid referencing non-existent ones (e.g., measurement may be missing)
    print("\n[Info] Inspecting dataset tables...")
    ds_id = dataset if "." in dataset else f"{project_id}.{dataset}"
    try:

        proj, dset = ds_id.split(".", 1)
        ds_ref = client.dataset(dset, project=proj)
        existing = {t.table_id for t in client.list_tables(ds_ref)}
    except Exception:
        existing = set()
    # Default domain table map
    domain_tables = [
        ("condition_occurrence", "condition_concept_id"),
        ("observation", "observation_concept_id"),
        ("procedure_occurrence", "procedure_concept_id"),
        ("drug_exposure", "drug_concept_id"),
        ("measurement", "measurement_concept_id"),
    ]
    filtered_domain_tables = [(t, c) for (t, c) in domain_tables if (not existing or t in existing)]

    # Stage 4a: Concept frequency across domains for this cohort (top 25 per domain)
    schema = dataset if "." in dataset else f"{project_id}.{dataset}"
    cohort_from = f"({cohort_sql}) AS cohort_src"
    print("\n[Run] concept_frequency (top 25 per domain)...")
    cf_sql_base = generate_concept_frequency_sql(
        schema=schema,
        cohort_table=cohort_from,
        min_persons=1,
        tables=filtered_domain_tables,
    )
    cf_sql = f"""
    WITH cf AS (
    {cf_sql_base}
    )
    SELECT *
    FROM (
      SELECT cf.*, ROW_NUMBER() OVER (PARTITION BY domain ORDER BY person_count DESC) AS rn
      FROM cf
    )
    WHERE rn <= 25
    ORDER BY domain, person_count DESC
    """.strip()
    cf_rows = list(client.query(cf_sql).result())
    cf_items = [{k: r[k] for k in r.keys()} for r in cf_rows]
    results["concept_frequency_top25"] = cf_items
    print(f"  → {len(cf_items)} rows")

    # Stage 4b: Concept presence summaries for anchor concept IDs (HF + ESRD)
    print("\n[Run] concept_presence (HF + ESRD anchors)...")
    # Extract HF IDs
    hf_ids = extract_concept_ids(input_data, ["heart failure"]) or []
    anchors = []
    for cid in esrd_ids + hf_ids:
        if cid not in anchors:
            anchors.append(cid)
    presence_summaries: List[Dict[str, Any]] = []
    for cid in anchors[:12]:  # cap to avoid very long runs
        inc_tables = [t for (t, _) in filtered_domain_tables]
        pres_sql = generate_concept_presence_sql(
            schema=schema,
            concept_id=cid,
            cohort_table=cohort_from,
            include_tables=inc_tables,
        )

        # Build dynamic aggregation columns based on included tables
        col_map = {
            "condition_occurrence": ("in_condition", "n_condition"),
            "observation": ("in_observation", "n_observation"),
            "procedure_occurrence": ("in_procedure", "n_procedure"),
            "drug_exposure": ("in_drug_exposure", "n_drug_exposure"),
            "measurement": ("in_measurement", "n_measurement"),
        }
        agg_cols = []
        for t in inc_tables:
            col = col_map.get(t)
            if not col:
                continue
            src, alias = col
            agg_cols.append(f"SUM({src}) AS {alias}")
        agg_select = (
            ",\n          ".join(agg_cols + ["COUNT(*) AS n_total"]) or "COUNT(*) AS n_total"
        )

        agg_sql = f"""
        WITH base AS (
        {pres_sql}
        )
        SELECT
          {cid} AS concept_id,
          {agg_select}
        FROM base
        """.strip()
        p_row = list(client.query(agg_sql).result())
        if p_row:
            presence_summaries.append({k: p_row[0][k] for k in p_row[0].keys()})
    results["concept_presence_summary"] = presence_summaries
    print(f"  → {len(presence_summaries)} concepts summarized")

    # Stage 4c: OMOP table presence summary for the cohort (aggregate)
    print("\n[Run] omop_presence_summary...")
    include_tables_for_omop = (
        list(existing)
        if existing
        else [
            "observation",
            "condition_occurrence",
            "procedure_occurrence",
            "drug_exposure",
            "care_site",
            "visit_occurrence",
            "measurement",
        ]
    )
    # care_site summary depends on visit_occurrence; if missing, drop care_site
    if "care_site" in include_tables_for_omop and "visit_occurrence" not in include_tables_for_omop:
        include_tables_for_omop = [t for t in include_tables_for_omop if t != "care_site"]
    omop_sql_base = generate_omop_presence_sql_from_table(
        schema=schema,
        cohort_table=cohort_from,
        include_tables=include_tables_for_omop,
    )
    flag_map = {
        "observation": ("has_observation", "n_observation"),
        "condition_occurrence": ("has_condition", "n_condition"),
        "procedure_occurrence": ("has_procedure", "n_procedure"),
        "drug_exposure": ("has_drug_exposure", "n_drug_exposure"),
        "care_site": ("has_care_site", "n_care_site"),
        "visit_occurrence": ("has_visit_occ", "n_visit_occ"),
        "measurement": ("has_measurement", "n_measurement"),
    }
    omop_agg_cols = []
    for t in include_tables_for_omop:
        col = flag_map.get(t)
        if not col:
            continue
        src, alias = col
        omop_agg_cols.append(f"SUM({src}) AS {alias}")
    omop_agg_select = (
        ",\n      ".join(omop_agg_cols + ["COUNT(*) AS n_total"]) or "COUNT(*) AS n_total"
    )

    omop_sql = f"""
    WITH base AS (
    {omop_sql_base}
    )
    SELECT
      {omop_agg_select}
    FROM base
    """.strip()
    om_rows = list(client.query(omop_sql).result())
    if om_rows:
        results["omop_presence_summary"] = {k: om_rows[0][k] for k in om_rows[0].keys()}
        print("  → summary ready")

    # Save outputs
    out_dir = project_root / "projects" / "stats"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "analytics_summary.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Analytics summary saved to: {out_file}")

    print("\n════════════════════════════════════════════════════════════════════")
    print("✅ ANALYTICS COMPLETE")
    print("════════════════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
