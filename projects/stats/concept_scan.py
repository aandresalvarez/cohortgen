
from google.cloud import bigquery  # optional; execution by caller
from typing import List, Optional


def generate_concept_presence_sql(
    schema: str,
    concept_id: int,
    cohort_table: str,
    include_tables: Optional[List[str]] = None,
) -> str:
    """
    Generate SQL to check for presence of a specific concept_id across OMOP tables for a cohort.

    Args:
        schema (str): BigQuery schema path (e.g., 'project.dataset').
        concept_id (int): Concept ID to search for.
        cohort_table (str): Full table or subquery (with alias) containing person_id (e.g. 'project.dataset.my_cohort' or '(SELECT ...) AS cohort_table').

    Returns:
        str: SQL query string.
    """
    if include_tables is None:
        include_tables = [
            "condition_occurrence",
            "observation",
            "procedure_occurrence",
            "drug_exposure",
            "measurement",
        ]

    ctes = [
        f"""
    cohort_person_ids AS (
        SELECT DISTINCT person_id
        FROM {cohort_table}
    )
        """.strip()
    ]

    joins = []
    selects = ["pid.person_id"]

    if "condition_occurrence" in include_tables:
        ctes.append(
            f"""
    condition_match AS (
        SELECT DISTINCT person_id, 1 AS in_condition
        FROM {schema}.condition_occurrence
        WHERE condition_concept_id = {concept_id}
          AND person_id IN (SELECT person_id FROM cohort_person_ids)
    )
            """.strip()
        )
        joins.append("LEFT JOIN condition_match   c ON pid.person_id = c.person_id")
        selects.append("MAX(COALESCE(c.in_condition, 0))     AS in_condition")

    if "observation" in include_tables:
        ctes.append(
            f"""
    observation_match AS (
        SELECT DISTINCT person_id, 1 AS in_observation
        FROM {schema}.observation
        WHERE observation_concept_id = {concept_id}
          AND person_id IN (SELECT person_id FROM cohort_person_ids)
    )
            """.strip()
        )
        joins.append("LEFT JOIN observation_match o ON pid.person_id = o.person_id")
        selects.append("MAX(COALESCE(o.in_observation, 0))   AS in_observation")

    if "procedure_occurrence" in include_tables:
        ctes.append(
            f"""
    procedure_match AS (
        SELECT DISTINCT person_id, 1 AS in_procedure
        FROM {schema}.procedure_occurrence
        WHERE procedure_concept_id = {concept_id}
          AND person_id IN (SELECT person_id FROM cohort_person_ids)
    )
            """.strip()
        )
        joins.append("LEFT JOIN procedure_match   p ON pid.person_id = p.person_id")
        selects.append("MAX(COALESCE(p.in_procedure, 0))     AS in_procedure")

    if "drug_exposure" in include_tables:
        ctes.append(
            f"""
    drug_match AS (
        SELECT DISTINCT person_id, 1 AS in_drug_exposure
        FROM {schema}.drug_exposure
        WHERE drug_concept_id = {concept_id}
          AND person_id IN (SELECT person_id FROM cohort_person_ids)
    )
            """.strip()
        )
        joins.append("LEFT JOIN drug_match        d ON pid.person_id = d.person_id")
        selects.append("MAX(COALESCE(d.in_drug_exposure, 0)) AS in_drug_exposure")

    if "measurement" in include_tables:
        ctes.append(
            f"""
    measurement_match AS (
        SELECT DISTINCT person_id, 1 AS in_measurement
        FROM {schema}.measurement
        WHERE measurement_concept_id = {concept_id}
          AND person_id IN (SELECT person_id FROM cohort_person_ids)
    )
            """.strip()
        )
        joins.append("LEFT JOIN measurement_match m ON pid.person_id = m.person_id")
        selects.append("MAX(COALESCE(m.in_measurement, 0))   AS in_measurement")

    ctes_sql = ",\n\n    ".join(ctes)
    joins_sql = "\n        ".join(joins)
    selects_sql = ",\n               ".join(selects)

    sql = f"""
    WITH {ctes_sql}

    , combined AS (
        SELECT {selects_sql}
        FROM cohort_person_ids pid
        {joins_sql}
        GROUP BY pid.person_id
    )

    SELECT *
    FROM combined
    """
    return sql.strip()

## This function:

## Accepts a concept_id (e.g., 4014295)

## Searches that concept ID across key OMOP tables (condition_occurrence, observation, procedure_occurrence, drug_exposure, measurement, etc.)

## Returns a binary indicator (1 if the person had that concept ID in that table, 0 otherwise)

##Outputs one row per person with flags for which tables contained the concept
