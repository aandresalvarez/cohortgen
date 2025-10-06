WITH dialysis_proc_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (4120120, 4324124, 4050863)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Procedure'
  UNION DISTINCT
  SELECT ca.descendant_concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` cdesc
    ON cdesc.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (4120120, 4324124, 4050863)
    AND cdesc.standard_concept = 'S'
    AND cdesc.domain_id = 'Procedure'
),
kidney_tx_proc_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (4021107, 4197300)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Procedure'
  UNION DISTINCT
  SELECT ca.descendant_concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` cdesc
    ON cdesc.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (4021107, 4197300)
    AND cdesc.standard_concept = 'S'
    AND cdesc.domain_id = 'Procedure'
),
esrd_condition_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (193782, 37018886, 43020455, 46273164)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT ca.descendant_concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` cdesc
    ON cdesc.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (193782, 37018886, 43020455, 46273164)
    AND cdesc.standard_concept = 'S'
    AND cdesc.domain_id = 'Condition'
),
heart_failure_condition_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (316139, 319835, 4023479)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT ca.descendant_concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` cdesc
    ON cdesc.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (316139, 319835, 4023479)
    AND cdesc.standard_concept = 'S'
    AND cdesc.domain_id = 'Condition'
),
esrd_condition_events AS (
  SELECT
    co.person_id,
    co.condition_start_date AS event_date,
    'ESRD_CONDITION' AS event_type
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  WHERE co.condition_concept_id IN (SELECT concept_id FROM esrd_condition_concepts)
),
dialysis_procedure_events AS (
  SELECT
    po.person_id,
    DATE(po.procedure_datetime) AS event_date,
    'DIALYSIS_PROCEDURE' AS event_type
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.procedure_occurrence` po
  WHERE po.procedure_concept_id IN (SELECT concept_id FROM dialysis_proc_concepts)
    AND po.procedure_datetime IS NOT NULL
),
kidney_transplant_events AS (
  SELECT
    po.person_id,
    DATE(po.procedure_datetime) AS event_date,
    'KIDNEY_TRANSPLANT' AS event_type
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.procedure_occurrence` po
  WHERE po.procedure_concept_id IN (SELECT concept_id FROM kidney_tx_proc_concepts)
    AND po.procedure_datetime IS NOT NULL
),
all_index_events AS (
  SELECT * FROM esrd_condition_events
  UNION ALL
  SELECT * FROM dialysis_procedure_events
  UNION ALL
  SELECT * FROM kidney_transplant_events
),
earliest_index AS (
  SELECT person_id, MIN(event_date) AS index_date
  FROM all_index_events
  GROUP BY person_id
),
hf_before_index AS (
  SELECT DISTINCT ei.person_id
  FROM earliest_index ei
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
    ON co.person_id = ei.person_id
  WHERE co.condition_concept_id IN (SELECT concept_id FROM heart_failure_condition_concepts)
    AND co.condition_start_date < ei.index_date
)
SELECT DISTINCT person_id
FROM hf_before_index;