
from google.cloud import bigquery
def generate_concept_presence_sql(schema: str, concept_id: int, cohort_table: str) -> str:
    """
    Generate SQL to check for presence of a specific concept_id across OMOP tables for a cohort.

    Args:
        schema (str): BigQuery schema path (e.g., 'project.dataset').
        concept_id (int): Concept ID to search for.
        cohort_table (str): Full table or subquery (with alias) containing person_id (e.g. 'project.dataset.my_cohort' or '(SELECT ...) AS cohort_table').

    Returns:
        str: SQL query string.
    """
    sql = f"""
    WITH cohort_person_ids AS (
        SELECT DISTINCT person_id
        FROM {cohort_table}
    ),

    -- Check each domain for the given concept_id
    condition_match AS (
        SELECT DISTINCT person_id, 1 AS in_condition
        FROM {schema}.condition_occurrence
        WHERE condition_concept_id = {concept_id}
          AND person_id IN (SELECT person_id FROM cohort_person_ids)
    ),

    observation_match AS (
        SELECT DISTINCT person_id, 1 AS in_observation
        FROM {schema}.observation
        WHERE observation_concept_id = {concept_id}
          AND person_id IN (SELECT person_id FROM cohort_person_ids)
    ),

    procedure_match AS (
        SELECT DISTINCT person_id, 1 AS in_procedure
        FROM {schema}.procedure_occurrence
        WHERE procedure_concept_id = {concept_id}
          AND person_id IN (SELECT person_id FROM cohort_person_ids)
    ),

    drug_match AS (
        SELECT DISTINCT person_id, 1 AS in_drug_exposure
        FROM {schema}.drug_exposure
        WHERE drug_concept_id = {concept_id}
          AND person_id IN (SELECT person_id FROM cohort_person_ids)
    ),

    measurement_match AS (
        SELECT DISTINCT person_id, 1 AS in_measurement
        FROM {schema}.measurement
        WHERE measurement_concept_id = {concept_id}
          AND person_id IN (SELECT person_id FROM cohort_person_ids)
    ),

    -- Combine all into one table
    combined AS (
        SELECT pid.person_id,
               MAX(COALESCE(c.in_condition, 0))     AS in_condition,
               MAX(COALESCE(o.in_observation, 0))   AS in_observation,
               MAX(COALESCE(p.in_procedure, 0))     AS in_procedure,
               MAX(COALESCE(d.in_drug_exposure, 0)) AS in_drug_exposure,
               MAX(COALESCE(m.in_measurement, 0))   AS in_measurement
        FROM cohort_person_ids pid
        LEFT JOIN condition_match   c ON pid.person_id = c.person_id
        LEFT JOIN observation_match o ON pid.person_id = o.person_id
        LEFT JOIN procedure_match   p ON pid.person_id = p.person_id
        LEFT JOIN drug_match        d ON pid.person_id = d.person_id
        LEFT JOIN measurement_match m ON pid.person_id = m.person_id
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