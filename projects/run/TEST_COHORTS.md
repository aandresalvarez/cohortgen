# Test Cohort Descriptions

Quick reference of test cohorts for manual testing. Copy and paste any of these when running the system.

---

## ⭐ RECOMMENDED (Start Here)

### Influenza Cohort - Medium Complexity

```
Male patients between 20 and 30 years old who had a positive influenza test in 2020, with at least 365 days of continuous enrollment before the test, excluding immunocompromised patients and those with prior hospitalization for respiratory failure.
```

**Expected Results**:
- Demographics: age 20-30, male
- Index event: positive flu test (LOINC codes)
- Time period: 2020
- Continuous enrollment: 365 days
- Exclusions: immunocompromised (SNOMED), respiratory failure (SNOMED)

---

## 🏥 SIMPLE COHORTS

### 1. Type 2 Diabetes - Basic

```
Adult patients diagnosed with type 2 diabetes
```

**Good for**: Quick testing, basic flow validation

### 2. Hypertension - Simple with Age

```
Patients 18 years or older with a diagnosis of hypertension
```

**Good for**: Testing demographics parsing

### 3. COVID-19 - Simple with Time

```
Patients with a positive COVID-19 test in 2020
```

**Good for**: Testing time period extraction

---

## 🔬 MEDIUM COMPLEXITY

### 4. Heart Failure with Medications

```
Patients diagnosed with heart failure who are currently on ACE inhibitors or beta-blockers, excluding those with end-stage renal disease
```

**Good for**: Testing drug concepts and exclusion criteria

### 5. New Hypertension - Research Scenario

```
Patients with newly diagnosed hypertension who are 18 years or older, have no prior diagnosis of cardiovascular disease, with at least one year of continuous enrollment before their first hypertension diagnosis
```

**Good for**: Testing "no prior" logic and observation windows

### 6. Asthma with Medications

```
Adult patients with asthma who have been prescribed inhaled corticosteroids, excluding patients with COPD or those who are pregnant
```

**Good for**: Testing medication concepts and multiple exclusions

---

## 🏗️ COMPLEX COHORTS

### 7. Heart Failure - Full Criteria

```
Female patients aged 65 and older diagnosed with heart failure between 2018 and 2020, with at least 180 days of continuous enrollment before diagnosis, currently on ACE inhibitors or beta-blockers, excluding patients with end-stage renal disease, prior heart transplant, or those in hospice care within 90 days before diagnosis.
```

**Good for**: Full system stress test, multiple criteria

### 8. Diabetes Onset Study

```
Patients between 40 and 65 years old with first diagnosis of type 2 diabetes, with at least 365 days of continuous enrollment before diagnosis, no prior type 1 diabetes or gestational diabetes, not on insulin at index, excluding patients with pregnancy in the prior year or active cancer diagnosis
```

**Good for**: Testing complex temporal logic and multiple exclusions

### 9. Post-Surgical Complications

```
Patients who underwent coronary artery bypass graft surgery, aged 50 years or older, with 90 days continuous enrollment before surgery and at least 30 days after, excluding patients who died within 30 days of surgery or had prior open heart surgery
```

**Good for**: Testing procedure concepts and post-index observation

---

## 🧬 SPECIALTY COHORTS

### 10. Oncology - Breast Cancer

```
Female patients aged 40 and older with newly diagnosed breast cancer, stage I-III, with at least 180 days continuous enrollment before diagnosis, excluding patients with metastatic disease or prior cancer diagnosis
```

**Good for**: Testing oncology concepts and staging

### 11. Pediatric - Asthma

```
Pediatric patients aged 5 to 17 years with a diagnosis of asthma, with at least two prescriptions for asthma medications in the past year, excluding patients with cystic fibrosis or primary immunodeficiency
```

**Good for**: Testing pediatric age ranges and medication frequency

### 12. Chronic Kidney Disease Progression

```
Patients with stage 3 chronic kidney disease who progressed to stage 4 or 5, aged 18 years or older, with at least 365 days of continuous enrollment and two eGFR measurements showing decline, excluding patients on dialysis at baseline or with kidney transplant
```

**Good for**: Testing lab measurements and disease progression

---

## 🔥 EDGE CASES

### 13. Minimal Information

```
Patients with diabetes
```

**Good for**: Testing how agent handles minimal input and asks clarifying questions

### 14. Highly Specific

```
Male patients exactly 65 years old on their first diagnosis of type 2 diabetes mellitus with HbA1c > 9% on January 1, 2020
```

**Good for**: Testing very specific constraints

### 15. Multiple Medications

```
Patients on statin, ACE inhibitor, and metformin simultaneously for at least 90 days, excluding patients with liver disease or creatinine > 1.5
```

**Good for**: Testing multiple drug exposure and lab values

---

## 📋 QUICK COPY-PASTE READY

### Simple Test
```
Adult patients diagnosed with type 2 diabetes
```

### Recommended Test
```
Male patients between 20 and 30 years old who had a positive influenza test in 2020, with at least 365 days of continuous enrollment before the test, excluding immunocompromised patients and those with prior hospitalization for respiratory failure.
```

### Complex Test
```
Female patients aged 65 and older diagnosed with heart failure between 2018 and 2020, with at least 180 days of continuous enrollment before diagnosis, currently on ACE inhibitors or beta-blockers, excluding patients with end-stage renal disease, prior heart transplant, or those in hospice care within 90 days before diagnosis.
```

---

## 💡 Testing Strategy

1. **Start Simple**: Use "Adult patients diagnosed with type 2 diabetes"
2. **Test Core Features**: Use the recommended influenza cohort
3. **Stress Test**: Use the complex heart failure cohort
4. **Validate Edge Cases**: Try the minimal information cohort

---

## 🎯 What to Check After Each Run

✅ **Stage 1 Output**:
- All demographics captured?
- Index event clearly defined?
- Inclusion/exclusion criteria complete?

✅ **Stage 2 Output**:
- Relevant OMOP concept IDs found?
- Correct domains (Condition, Drug, Procedure, Measurement)?
- Standard concepts only?

✅ **Stage 3 Output**:
- Valid SQL syntax?
- Correct table references?
- Dry-run successful?
- Cost estimate reasonable?

---

**File Location**: `/Users/alvaro1/Documents/Coral/Code/cohortgen/projects/run/TEST_COHORTS.md`

**Usage**: Copy any cohort description above and paste it when prompted by the system.

