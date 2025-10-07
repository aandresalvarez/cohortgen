WITH hf_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (316139, 319835, 4023479, 4229440, 4242669, 44784442)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT DISTINCT ca.descendant_concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (316139, 319835, 4023479, 4229440, 4242669, 44784442)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
esrd_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (193782, 37018886, 43020455)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT DISTINCT ca.descendant_concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (193782, 37018886, 43020455)
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
cooccurrence_dates AS (
  SELECT
    h.person_id,
    h.condition_start_date AS co_date
  FROM hf_conditions h
  JOIN esrd_conditions e
    ON e.person_id = h.person_id
   AND e.condition_start_date = h.condition_start_date
),
first_index AS (
  SELECT person_id, MIN(co_date) AS index_date
  FROM cooccurrence_dates
  GROUP BY person_id
),
eligible_prior_hf AS (
  SELECT fi.person_id, fi.index_date
  FROM first_index fi
  WHERE EXISTS (
    SELECT 1
    FROM hf_conditions h2
    WHERE h2.person_id = fi.person_id
      AND h2.condition_start_date < fi.index_date
  )
),
age_filtered AS (
  SELECT ep.person_id, ep.index_date
  FROM eligible_prior_hf ep
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.person` p
    ON p.person_id = ep.person_id
  WHERE EXTRACT(YEAR FROM ep.index_date) - p.year_of_birth >= 18
),
obs_filtered AS (
  SELECT DISTINCT af.person_id
  FROM age_filtered af
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.observation_period` op
    ON op.person_id = af.person_id
   AND af.index_date BETWEEN op.observation_period_start_date AND op.observation_period_end_date
)
SELECT DISTINCT person_id
FROM obs_filtered;