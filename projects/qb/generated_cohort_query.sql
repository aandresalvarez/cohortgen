WITH
esrd_concepts AS (
  SELECT DISTINCT ca.descendant_concept_id AS concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON ca.descendant_concept_id = c.concept_id
  WHERE ca.ancestor_concept_id IN (193782, 37018886, 43020455)
    AND c.standard_concept = 'S'
  UNION DISTINCT
  SELECT concept_id FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept`
  WHERE concept_id IN (193782, 37018886, 43020455) AND standard_concept = 'S'
),
heart_failure_concepts AS (
  SELECT DISTINCT ca.descendant_concept_id AS concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON ca.descendant_concept_id = c.concept_id
  WHERE ca.ancestor_concept_id IN (316139, 319835, 4229440)
    AND c.standard_concept = 'S'
  UNION DISTINCT
  SELECT concept_id FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept`
  WHERE concept_id IN (316139, 319835, 4229440) AND standard_concept = 'S'
),
ckd_concepts AS (
  SELECT DISTINCT ca.descendant_concept_id AS concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON ca.descendant_concept_id = c.concept_id
  WHERE ca.ancestor_concept_id IN (46271022, 443601, 443614)
    AND c.standard_concept = 'S'
  UNION DISTINCT
  SELECT concept_id FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept`
  WHERE concept_id IN (46271022, 443601, 443614) AND standard_concept = 'S'
),
dialysis_concepts AS (
  SELECT DISTINCT ca.descendant_concept_id AS concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON ca.descendant_concept_id = c.concept_id
  WHERE ca.ancestor_concept_id IN (4032243, 4120120, 4050863)
    AND c.standard_concept = 'S'
  UNION DISTINCT
  SELECT concept_id FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept`
  WHERE concept_id IN (4032243, 4120120, 4050863) AND standard_concept = 'S'
),
transplant_concepts AS (
  SELECT DISTINCT ca.descendant_concept_id AS concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON ca.descendant_concept_id = c.concept_id
  WHERE ca.ancestor_concept_id IN (4197300, 36717743)
    AND c.standard_concept = 'S'
  UNION DISTINCT
  SELECT concept_id FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept`
  WHERE concept_id IN (4197300, 36717743) AND standard_concept = 'S'
),
esrd_events AS (
  SELECT co.person_id, co.condition_occurrence_id, co.condition_start_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  WHERE co.condition_concept_id IN (SELECT concept_id FROM esrd_concepts)
),
index_per_person AS (
  SELECT person_id, MIN(condition_start_date) AS index_date
  FROM esrd_events
  GROUP BY person_id
),
valid_observation AS (
  SELECT ip.person_id, ip.index_date
  FROM index_per_person ip
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.observation_period` op
    ON ip.person_id = op.person_id
   AND op.observation_period_start_date <= DATE_SUB(ip.index_date, INTERVAL 365 DAY)
   AND op.observation_period_end_date >= ip.index_date
),
heart_failure_prior AS (
  SELECT DISTINCT ip.person_id
  FROM valid_observation ip
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` ch
    ON ch.person_id = ip.person_id
   AND ch.condition_start_date < ip.index_date
  JOIN heart_failure_concepts hfc
    ON ch.condition_concept_id = hfc.concept_id
)
SELECT DISTINCT vo.person_id
FROM valid_observation vo
JOIN heart_failure_prior hf ON vo.person_id = hf.person_id;