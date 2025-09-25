
from google.cloud import bigquery
def generate_concept_frequency_sql(schema: str, cohort_table: str, min_persons: int = 1) -> str:
    """
    Generate SQL to get most common concept_ids across OMOP tables for a given cohort.

    Args:
        schema (str): Full BigQuery schema path (e.g., 'project.dataset').
        cohort_table (str): Table or subquery containing person_id (must already be aliased).
        min_persons (int): Optional filter to include only concepts with at least this many unique persons.

    Returns:
        str: SQL query.
    """
    tables = [
        ("condition_occurrence", "condition_concept_id"),
        ("observation", "observation_concept_id"),
        ("procedure_occurrence", "procedure_concept_id"),
        ("drug_exposure", "drug_concept_id"),
        ("measurement", "measurement_concept_id")
    ]

    union_queries = []
    for table, concept_field in tables:
        q = f"""
        SELECT
            {concept_field} AS concept_id,
            '{table}' AS domain,
            COUNT(DISTINCT t.person_id) AS person_count
        FROM {schema}.{table} t
        JOIN cohort AS cohort_table ON t.person_id = cohort_table.person_id
        WHERE {concept_field} IS NOT NULL
        GROUP BY {concept_field}
        """
        union_queries.append(q.strip())

    all_domains_union = "\nUNION ALL\n".join(union_queries)

    final_sql = f"""
    WITH cohort AS (
        SELECT DISTINCT person_id
        FROM {cohort_table}
    ),

    concept_counts AS (
        {all_domains_union}
    )

    SELECT
        cc.concept_id,
        d.concept_name,
        cc.domain,
        cc.person_count
    FROM concept_counts cc
    LEFT JOIN {schema}.concept d ON cc.concept_id = d.concept_id
    WHERE cc.person_count >= {min_persons}
    ORDER BY cc.domain, cc.person_count DESC
    """
    return final_sql.strip()
