from google.cloud import bigquery  # optional; execution handled by caller
from typing import List, Optional


def generate_omop_presence_sql_from_table(
    schema: str,
    cohort_table: str,
    include_tables: Optional[List[str]] = None,
) -> str:
    if include_tables is None:
        include_tables = [
            "observation",
            "condition_occurrence",
            "procedure_occurrence",
            "drug_exposure",
            "care_site",
            "visit_occurrence",
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

    if "observation" in include_tables:
        ctes.append(
            f"""
    observations AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.observation
        JOIN cohort_person_ids USING (person_id)
    )
            """.strip()
        )
        joins.append("LEFT JOIN observations o ON pid.person_id = o.person_id")
        selects.append("MAX(COALESCE(o.has_record, 0)) AS has_observation")

    if "condition_occurrence" in include_tables:
        ctes.append(
            f"""
    conditions AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.condition_occurrence
        JOIN cohort_person_ids USING (person_id)
    )
            """.strip()
        )
        joins.append("LEFT JOIN conditions c ON pid.person_id = c.person_id")
        selects.append("MAX(COALESCE(c.has_record, 0)) AS has_condition")

    if "procedure_occurrence" in include_tables:
        ctes.append(
            f"""
    procedures AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.procedure_occurrence
        JOIN cohort_person_ids USING (person_id)
    )
            """.strip()
        )
        joins.append("LEFT JOIN procedures p ON pid.person_id = p.person_id")
        selects.append("MAX(COALESCE(p.has_record, 0)) AS has_procedure")

    if "drug_exposure" in include_tables:
        ctes.append(
            f"""
    drug_exposures AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.drug_exposure
        JOIN cohort_person_ids USING (person_id)
    )
            """.strip()
        )
        joins.append("LEFT JOIN drug_exposures d ON pid.person_id = d.person_id")
        selects.append("MAX(COALESCE(d.has_record, 0)) AS has_drug_exposure")

    if "care_site" in include_tables and "visit_occurrence" in include_tables:
        ctes.append(
            f"""
    care_site AS (
        SELECT DISTINCT v.person_id, 1 AS has_record
        FROM {schema}.visit_occurrence v
        JOIN {schema}.care_site cs ON v.care_site_id = cs.care_site_id
        JOIN cohort_person_ids pid ON v.person_id = pid.person_id
    )
            """.strip()
        )
        joins.append("LEFT JOIN care_site cs ON pid.person_id = cs.person_id")
        selects.append("MAX(COALESCE(cs.has_record, 0)) AS has_care_site")

    if "visit_occurrence" in include_tables:
        ctes.append(
            f"""
    visit_occ AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.visit_occurrence
        JOIN cohort_person_ids USING (person_id)
    )
            """.strip()
        )
        joins.append("LEFT JOIN visit_occ v ON pid.person_id = v.person_id")
        selects.append("MAX(COALESCE(v.has_record, 0)) AS has_visit_occ")

    if "measurement" in include_tables:
        ctes.append(
            f"""
    measurements AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.measurement
        JOIN cohort_person_ids USING (person_id)
    )
            """.strip()
        )
        joins.append("LEFT JOIN measurements m ON pid.person_id = m.person_id")
        selects.append("MAX(COALESCE(m.has_record, 0)) AS has_measurement")

    ctes_sql = ",\n\n    ".join(ctes)
    joins_sql = "\n        ".join(joins)
    selects_sql = ",\n           ".join(selects)

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


## This function scans OMOP tables for a given set of person IDs and outputs a
## binary presence table per person. Execution is handled by caller.
