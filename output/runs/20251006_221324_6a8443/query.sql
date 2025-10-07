WITH esrd_concepts AS (
  SELECT DISTINCT ca.descendant_concept_id AS concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (193782, 37018886, 43020455, 46273164)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (193782, 37018886, 43020455, 46273164)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
hf_concepts AS (
  SELECT DISTINCT ca.descendant_concept_id AS concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (316139, 319835, 4023479, 4229440, 4111554, 4108244)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (316139, 319835, 4023479, 4229440, 4111554, 4108244)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
hf_conditions AS (
  SELECT person_id, condition_start_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence`
  WHERE condition_concept_id IN (SELECT concept_id FROM hf_concepts)
),
esrd_conditions AS (
  SELECT person_id, condition_start_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence`
  WHERE condition_concept_id IN (SELECT concept_id FROM esrd_concepts)
),
same_day AS (
  SELECT DISTINCT hf.person_id, hf.condition_start_date AS index_date
  FROM hf_conditions hf
  JOIN esrd_conditions esrd
    ON esrd.person_id = hf.person_id
   AND esrd.condition_start_date = hf.condition_start_date
),
first_index AS (
  SELECT person_id, MIN(index_date) AS index_date
  FROM same_day
  GROUP BY person_id
),
inclusion AS (
  SELECT DISTINCT fi.person_id
  FROM first_index fi
  JOIN hf_conditions hf
    ON hf.person_id = fi.person_id
   AND hf.condition_start_date <= fi.index_date
  JOIN esrd_conditions esrd
    ON esrd.person_id = fi.person_id
   AND esrd.condition_start_date <= fi.index_date
)
SELECT DISTINCT person_id
FROM inclusion;