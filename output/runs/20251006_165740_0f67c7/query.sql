WITH esrd_condition_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (193782, 37018886, 46273164, 43020455)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (193782, 37018886, 46273164, 43020455)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
esrd_observation_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (4019967, 40482357, 46269984, 46269985, 765776)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Observation'
  UNION DISTINCT
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (4019967, 40482357, 46269984, 46269985, 765776)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Observation'
),
dialysis_procedure_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (4120120, 4146536, 4050863, 4051326, 4238836)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Procedure'
  UNION DISTINCT
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (4120120, 4146536, 4050863, 4051326, 4238836)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Procedure'
),
heart_failure_concepts AS (
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept_ancestor` ca
  JOIN `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
    ON c.concept_id = ca.descendant_concept_id
  WHERE ca.ancestor_concept_id IN (316139, 319835, 4023479, 4229440, 4242669, 44784442)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
  UNION DISTINCT
  SELECT DISTINCT c.concept_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.concept` c
  WHERE c.concept_id IN (316139, 319835, 4023479, 4229440, 4242669, 44784442)
    AND c.standard_concept = 'S'
    AND c.domain_id = 'Condition'
),
esrd_condition_events AS (
  SELECT co.person_id, co.condition_start_date AS event_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  JOIN esrd_condition_concepts ecc
    ON co.condition_concept_id = ecc.concept_id
),
esrd_observation_events AS (
  SELECT o.person_id, o.observation_date AS event_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.observation` o
  JOIN esrd_observation_concepts eoc
    ON o.observation_concept_id = eoc.concept_id
),
dialysis_procedure_events AS (
  SELECT po.person_id, DATE(po.procedure_datetime) AS event_date
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.procedure_occurrence` po
  JOIN dialysis_procedure_concepts dpc
    ON po.procedure_concept_id = dpc.concept_id
  WHERE po.procedure_datetime IS NOT NULL
),
index_events AS (
  SELECT person_id, event_date FROM esrd_condition_events
  UNION ALL
  SELECT person_id, event_date FROM esrd_observation_events
  UNION ALL
  SELECT person_id, event_date FROM dialysis_procedure_events
),
earliest_index AS (
  SELECT person_id, MIN(event_date) AS index_date
  FROM index_events
  GROUP BY person_id
),
hf_prior_to_index AS (
  SELECT DISTINCT co.person_id
  FROM `bigquery-public-data.cms_synthetic_patient_data_omop.condition_occurrence` co
  JOIN heart_failure_concepts hfc
    ON co.condition_concept_id = hfc.concept_id
  JOIN earliest_index ei
    ON ei.person_id = co.person_id
   AND co.condition_start_date < ei.index_date
)
SELECT DISTINCT ei.person_id
FROM earliest_index ei
JOIN hf_prior_to_index hf
  ON hf.person_id = ei.person_id;