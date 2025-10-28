from google.cloud import bigquery
def generate_omop_presence_sql_from_table(schema: str, cohort_table: str) -> str:
    sql = f"""
    WITH cohort_person_ids AS (
        SELECT DISTINCT person_id
        FROM {cohort_table}
    ),

    observations AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.observation
        JOIN cohort_person_ids USING (person_id)
    ),

    conditions AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.condition_occurrence
        JOIN cohort_person_ids USING (person_id)
    ),

    procedures AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.procedure_occurrence
        JOIN cohort_person_ids USING (person_id)
    ),

    drug_exposures AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.drug_exposure
        JOIN cohort_person_ids USING (person_id)
    ),

    care_site AS (
        SELECT DISTINCT v.person_id, 1 AS has_record
        FROM {schema}.visit_occurrence v
        JOIN {schema}.care_site cs ON v.care_site_id = cs.care_site_id
        JOIN cohort_person_ids pid ON v.person_id = pid.person_id
    ),

    visit_occ AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.visit_occurrence
        JOIN cohort_person_ids USING (person_id)
    ),
    measurements AS (
        SELECT DISTINCT person_id, 1 AS has_record
        FROM {schema}.measurement
        JOIN cohort_person_ids USING (person_id)
    ),

    combined AS (
        SELECT pid.person_id,
               MAX(COALESCE(o.has_record, 0)) AS has_observation,
               MAX(COALESCE(c.has_record, 0)) AS has_condition,
               MAX(COALESCE(p.has_record, 0)) AS has_procedure,
               MAX(COALESCE(d.has_record, 0)) AS has_drug_exposure,
               MAX(COALESCE(cs.has_record, 0)) AS has_care_site,
               MAX(COALESCE(v.has_record, 0)) AS has_visit_occ,
               MAX(COALESCE(m.has_record, 0)) AS has_measurement

        FROM cohort_person_ids pid
        LEFT JOIN observations o ON pid.person_id = o.person_id
        LEFT JOIN conditions c ON pid.person_id = c.person_id
        LEFT JOIN procedures p ON pid.person_id = p.person_id
        LEFT JOIN drug_exposures d ON pid.person_id = d.person_id
        LEFT JOIN care_site cs ON pid.person_id = cs.person_id
        LEFT JOIN visit_occ v ON pid.person_id = v.person_id
        LEFT JOIN measurements m ON pid.person_id = m.person_id
        GROUP BY pid.person_id
    )

    SELECT person_id,
           has_observation,
           has_condition,
           has_procedure,
           has_drug_exposure,
           has_care_site,
           has_visit_occ
           has_measurement
    FROM combined
    """
    return sql.strip()


# === BigQuery Execution ===

# Initialize client (make sure your environment is authenticated)
client = bigquery.Client()

## This function scans omop tables for a given set of person ids and outputs a

## binary table to show omop table presence for each person id