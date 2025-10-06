WITH heart_failure_concepts AS (
  SELECT DISTINCT ca.descendant_concept_id AS concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (316139, 319835, 444031, 4023479, 4229440, 4311437)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
esrd_concepts AS (
  SELECT DISTINCT ca.descendant_concept_id AS concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (193782, 37018886, 43020455, 46273164, 45768813)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
hf_conditions AS (
  SELECT person_id, condition_start_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence`
  WHERE condition_concept_id IN (SELECT concept_id FROM heart_failure_concepts)
),
esrd_first AS (
  SELECT person_id, MIN(condition_start_date) AS first_esrd_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence`
  WHERE condition_concept_id IN (SELECT concept_id FROM esrd_concepts)
  GROUP BY person_id
)
SELECT DISTINCT e.person_id
FROM esrd_first e
JOIN hf_conditions h
  ON h.person_id = e.person_id
 AND h.condition_start_date < e.first_esrd_date;