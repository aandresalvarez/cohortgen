WITH t2dm_concepts AS (
  SELECT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (201826, 4063043, 4130162)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT ca.descendant_concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (201826, 4063043, 4130162)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
t1dm_concepts AS (
  SELECT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (201254, 4063042, 3661732)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT ca.descendant_concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (201254, 4063042, 3661732)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
first_t2dm AS (
  SELECT
    co.person_id,
    MIN(co.condition_start_date) AS index_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  WHERE co.condition_concept_id IN (SELECT concept_id FROM t2dm_concepts)
  GROUP BY co.person_id
),
eligible AS (
  SELECT ft.person_id, ft.index_date
  FROM first_t2dm ft
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.person` p
    ON p.person_id = ft.person_id
  WHERE EXTRACT(YEAR FROM ft.index_date) - p.year_of_birth >= 18
),
excluded AS (
  SELECT DISTINCT e.person_id
  FROM eligible e
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
    ON co.person_id = e.person_id
  WHERE co.condition_concept_id IN (SELECT concept_id FROM t1dm_concepts)
    AND co.condition_start_date < e.index_date
)
SELECT DISTINCT e.person_id
FROM eligible e
LEFT JOIN excluded x
  ON x.person_id = e.person_id
WHERE x.person_id IS NULL;