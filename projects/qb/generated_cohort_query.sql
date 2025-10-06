WITH
-- Ancestor lists provided
heart_ancestor_ids AS (
  SELECT 316139 AS concept_id UNION ALL SELECT 319835 UNION ALL SELECT 4229440
),
esrd_ancestor_ids AS (
  SELECT 193782 AS concept_id UNION ALL SELECT 37018886 UNION ALL SELECT 43020455
),
dialysis_ancestor_ids AS (
  SELECT 4120120 AS concept_id UNION ALL SELECT 46273700 UNION ALL SELECT 4050863
),
transplant_ancestor_ids AS (
  SELECT 4322471 AS concept_id UNION ALL SELECT 4021107
),

-- Expand to descendant standard concepts using concept_ancestor and concept (include descendants; standard only)
heart_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON ca.descendant_concept_id = c.concept_id
  WHERE ca.ancestor_concept_id IN (SELECT concept_id FROM heart_ancestor_ids)
    AND c.standard_concept = 'S'
  UNION DISTINCT
  SELECT concept_id FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept`
  WHERE concept_id IN (SELECT concept_id FROM heart_ancestor_ids) AND standard_concept = 'S'
),

esrd_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON ca.descendant_concept_id = c.concept_id
  WHERE ca.ancestor_concept_id IN (SELECT concept_id FROM esrd_ancestor_ids)
    AND c.standard_concept = 'S'
  UNION DISTINCT
  SELECT concept_id FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept`
  WHERE concept_id IN (SELECT concept_id FROM esrd_ancestor_ids) AND standard_concept = 'S'
),

dialysis_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON ca.descendant_concept_id = c.concept_id
  WHERE ca.ancestor_concept_id IN (SELECT concept_id FROM dialysis_ancestor_ids)
    AND c.standard_concept = 'S'
  UNION DISTINCT
  SELECT concept_id FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept`
  WHERE concept_id IN (SELECT concept_id FROM dialysis_ancestor_ids) AND standard_concept = 'S'
),

transplant_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON ca.descendant_concept_id = c.concept_id
  WHERE ca.ancestor_concept_id IN (SELECT concept_id FROM transplant_ancestor_ids)
    AND c.standard_concept = 'S'
  UNION DISTINCT
  SELECT concept_id FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept`
  WHERE concept_id IN (SELECT concept_id FROM transplant_ancestor_ids) AND standard_concept = 'S'
),

-- Condition occurrences for heart failure and ESRD
heart_occurrences AS (
  SELECT person_id, condition_start_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence`
  WHERE condition_concept_id IN (SELECT concept_id FROM heart_concepts)
),

esrd_occurrences AS (
  SELECT person_id, condition_start_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence`
  WHERE condition_concept_id IN (SELECT concept_id FROM esrd_concepts)
),

-- Procedure occurrences for dialysis and transplant (captured but not required for cohort entry)
dialysis_occurrences AS (
  SELECT person_id, procedure_datetime AS procedure_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.procedure_occurrence`
  WHERE procedure_concept_id IN (SELECT concept_id FROM dialysis_concepts)
),

transplant_occurrences AS (
  SELECT person_id, procedure_datetime AS procedure_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.procedure_occurrence`
  WHERE procedure_concept_id IN (SELECT concept_id FROM transplant_concepts)
),

-- ESRD occurrences that have at least one prior heart failure diagnosis (heart failure at any time before ESRD)
esrd_after_prior_heart AS (
  SELECT e.person_id, e.condition_start_date AS index_date
  FROM esrd_occurrences e
  WHERE EXISTS (
    SELECT 1
    FROM heart_occurrences h
    WHERE h.person_id = e.person_id
      AND h.condition_start_date < e.condition_start_date
  )
),

-- For each person, take the first ESRD occurrence that occurs after an earlier heart failure diagnosis
first_esrd_after_heart AS (
  SELECT person_id, index_date,
    ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY index_date) AS rn
  FROM esrd_after_prior_heart
)

-- Final cohort: persons with the first ESRD after prior heart failure; include only persons present in person table (use pre-extracted demographics)
SELECT p.person_id, fe.index_date AS cohort_entry_date
FROM first_esrd_after_heart fe
JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.person` p
  ON p.person_id = fe.person_id
WHERE fe.rn = 1;