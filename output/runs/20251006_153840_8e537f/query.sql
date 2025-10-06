WITH esrd_input AS (
  SELECT 193782 AS concept_id UNION ALL
  SELECT 37018886 UNION ALL
  SELECT 43020455 UNION ALL
  SELECT 46273164
),
hf_input AS (
  SELECT 316139 AS concept_id UNION ALL
  SELECT 319835 UNION ALL
  SELECT 4023479 UNION ALL
  SELECT 4229440 UNION ALL
  SELECT 4242669 UNION ALL
  SELECT 44784442
),
dialysis_input AS (
  SELECT 4120120 AS concept_id UNION ALL
  SELECT 4146536 UNION ALL
  SELECT 4050863
),
esrd_condition_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM esrd_input i
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = i.concept_id
  WHERE c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT DISTINCT c2.concept_id
  FROM esrd_input i
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
    ON ca.ancestor_concept_id = i.concept_id
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c2
    ON c2.concept_id = ca.descendant_concept_id
  WHERE c2.standard_concept = 'S'
    AND c2.domain_id = 'Condition'
),
hf_condition_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM hf_input i
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = i.concept_id
  WHERE c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT DISTINCT c2.concept_id
  FROM hf_input i
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
    ON ca.ancestor_concept_id = i.concept_id
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c2
    ON c2.concept_id = ca.descendant_concept_id
  WHERE c2.standard_concept = 'S'
    AND c2.domain_id = 'Condition'
),
dialysis_procedure_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM dialysis_input i
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = i.concept_id
  WHERE c.standard_concept = 'S'
    AND c.domain_id = 'Procedure'
  UNION DISTINCT
  SELECT DISTINCT c2.concept_id
  FROM dialysis_input i
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
    ON ca.ancestor_concept_id = i.concept_id
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c2
    ON c2.concept_id = ca.descendant_concept_id
  WHERE c2.standard_concept = 'S'
    AND c2.domain_id = 'Procedure'
),
esrd_condition_events AS (
  SELECT
    co.person_id,
    co.condition_start_date AS index_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  WHERE co.condition_concept_id IN (SELECT concept_id FROM esrd_condition_concepts)
),
dialysis_events AS (
  SELECT
    po.person_id,
    DATE(po.procedure_datetime) AS index_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.procedure_occurrence` po
  WHERE po.procedure_concept_id IN (SELECT concept_id FROM dialysis_procedure_concepts)
    AND po.procedure_datetime IS NOT NULL
),
esrd_index AS (
  SELECT
    person_id,
    MIN(index_date) AS esrd_index_date
  FROM (
    SELECT person_id, index_date FROM esrd_condition_events
    UNION ALL
    SELECT person_id, index_date FROM dialysis_events
  )
  GROUP BY person_id
),
heart_failure_events AS (
  SELECT
    co.person_id,
    co.condition_start_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  WHERE co.condition_concept_id IN (SELECT concept_id FROM hf_condition_concepts)
),
cohort AS (
  SELECT DISTINCT ei.person_id
  FROM esrd_index ei
  JOIN heart_failure_events hf
    ON hf.person_id = ei.person_id
   AND hf.condition_start_date < ei.esrd_index_date
)
SELECT person_id
FROM cohort
ORDER BY person_id;