WITH hf_seeds AS (
  SELECT concept_id
  FROM UNNEST([316139, 319835, 4229440]) AS concept_id
),
esrd_seeds AS (
  SELECT concept_id
  FROM UNNEST([193782, 37018886, 46273164, 43020455]) AS concept_id
),
hf_concepts AS (
  SELECT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  JOIN hf_seeds s ON c.concept_id = s.concept_id
  WHERE c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT c2.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN hf_seeds s ON ca.ancestor_concept_id = s.concept_id
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c2
    ON ca.descendant_concept_id = c2.concept_id
  WHERE c2.standard_concept = 'S'
    AND c2.domain_id = 'Condition'
),
esrd_concepts AS (
  SELECT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  JOIN esrd_seeds s ON c.concept_id = s.concept_id
  WHERE c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT c2.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN esrd_seeds s ON ca.ancestor_concept_id = s.concept_id
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c2
    ON ca.descendant_concept_id = c2.concept_id
  WHERE c2.standard_concept = 'S'
    AND c2.domain_id = 'Condition'
),
hf_dx AS (
  SELECT co.person_id, MIN(co.condition_start_date) AS first_hf_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  JOIN hf_concepts hc
    ON co.condition_concept_id = hc.concept_id
  GROUP BY co.person_id
),
esrd_dx AS (
  SELECT co.person_id, MIN(co.condition_start_date) AS first_esrd_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  JOIN esrd_concepts ec
    ON co.condition_concept_id = ec.concept_id
  GROUP BY co.person_id
)
SELECT DISTINCT e.person_id
FROM esrd_dx e
JOIN hf_dx h
  ON h.person_id = e.person_id
WHERE h.first_hf_date < e.first_esrd_date;