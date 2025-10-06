WITH esrd_condition_concepts AS (
  SELECT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
    AND c.concept_id IN (193782, 37018886, 46273164, 43020455)
  UNION DISTINCT
  SELECT ca.descendant_concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (193782, 37018886, 46273164, 43020455)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
hf_condition_concepts AS (
  SELECT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
    AND c.concept_id IN (316139, 319835, 4023479, 4229440, 4242669, 44784442)
  UNION DISTINCT
  SELECT ca.descendant_concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (316139, 319835, 4023479, 4229440, 4242669, 44784442)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
first_esrd AS (
  SELECT
    co.person_id,
    MIN(co.condition_start_date) AS index_esrd_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  JOIN esrd_condition_concepts ec
    ON co.condition_concept_id = ec.concept_id
  GROUP BY co.person_id
),
hf_prior AS (
  SELECT DISTINCT co.person_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  JOIN hf_condition_concepts hc
    ON co.condition_concept_id = hc.concept_id
  JOIN first_esrd fe
    ON fe.person_id = co.person_id
  WHERE co.condition_start_date < fe.index_esrd_date
)
SELECT DISTINCT fe.person_id
FROM first_esrd fe
JOIN hf_prior hp
  ON hp.person_id = fe.person_id;