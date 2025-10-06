"""
Stage 3: BigQuery SQL Generation for OMOP Cohorts
Pydantic AI implementation

Takes cohort definition + OMOP concept sets → generates validated BigQuery SQL
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "projects" / "qb"))

from tools import DryRunInput, DryRunResult, validate_bigquery_sql  # noqa: E402

# ============================================================================
# Pydantic Models
# ============================================================================


class ConceptSet(BaseModel):
    """OMOP concept set for cohort definition."""

    name: str
    included_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    excluded_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    include_descendants: bool = True
    standard_only: bool = True
    notes: str = ""


class CohortInput(BaseModel):
    """Input for BigQuery SQL generation."""

    clinical_definition: Dict[str, Any]
    concept_sets: List[ConceptSet]


class SQLGenerationResult(BaseModel):
    """Final SQL generation result."""

    sql: str
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    estimated_cost_usd: Optional[float] = None
    total_bytes_processed: int = 0
    summary: str = ""


# ============================================================================
# Agents
# ============================================================================

# SQL Generator Agent
sql_generator_agent = Agent(  # type: ignore[call-overload]
    "openai:gpt-5-mini",
    output_type=str,
    model_settings={"reasoning": {"effort": "medium"}},
    system_prompt="""
You are an expert OMOP CDM (v5.x) SQL developer targeting BigQuery Standard SQL.

Your task: Generate a single, runnable BigQuery SQL query that implements the provided cohort definition using the supplied concept sets.

REQUIREMENTS:
1. **BigQuery Standard SQL only** (not Legacy SQL)
2. **Fully qualified table names**: Use `project.dataset.table` format
   - Example: `bigquery-public-data.cms_synthetic_patient_data_omop.person`
3. **CRITICAL - Use CORRECT table based on Domain**:
   - Domain "Measurement" → `measurement` table (join on measurement_concept_id, filter on measurement_date)
   - Domain "Condition" → `condition_occurrence` table (join on condition_concept_id, filter on condition_start_date)
   - Domain "Drug" → `drug_exposure` table (join on drug_concept_id, filter on drug_exposure_start_date)
   - Domain "Procedure" → `procedure_occurrence` table (join on procedure_concept_id, filter on procedure_date)
4. **Demographics from concept sets**: Look at the Domain field in each concept set to determine the correct table
5. **Other OMOP tables**:
   - person (demographics: age, gender)
   - observation_period (enrollment periods)
   - concept_ancestor (for descendants)
6. **Concept ID filtering**: Use ALL provided concept_ids to filter records for each relevant domain. Do not drop any listed IDs. If there are multiple concept sets for the same domain, union their IDs before filtering.
7. **Include descendants**: If `include_descendants=true`, use `concept_ancestor` table to expand to descendant concepts
8. **Standard concepts**: Prefer `standard_concept='S'` unless specified otherwise
9. **Demographics filtering**: ALWAYS include age/gender filters from clinical definition if specified
10. **Single SELECT statement**: Use CTEs if needed, but end with one final SELECT
11. **No commentary**: Output ONLY SQL, no markdown or explanations

EXAMPLE STRUCTURE (for Measurement domain):
```sql
WITH measurement_concepts AS (
  -- For Measurement domain, use measurement table
  SELECT DISTINCT m.person_id
  FROM `project.dataset.measurement` m
  WHERE m.measurement_concept_id IN (/* concept IDs */)
  AND EXTRACT(YEAR FROM m.measurement_date) = 2020
),
demographics AS (
  SELECT person_id
  FROM `project.dataset.person` p
  WHERE EXTRACT(YEAR FROM CURRENT_DATE()) - p.year_of_birth BETWEEN 20 AND 30
  AND p.gender_concept_id = 8507  -- Male
)
SELECT DISTINCT mc.person_id
FROM measurement_concepts mc
INNER JOIN demographics d ON mc.person_id = d.person_id;
```

OUTPUT FORMAT:
- Only SQL code
- No backticks, no markdown
- No explanations or comments outside the SQL
""",
)

# SQL Fixer Agent
sql_fixer_agent = Agent(  # type: ignore[call-overload]
    "openai:gpt-5-mini",
    output_type=str,
    model_settings={"reasoning": {"effort": "medium"}},
    system_prompt="""
You fix BigQuery Standard SQL queries.

Given:
- Original SQL
- BigQuery dry-run error message

Task:
- Return corrected SQL that resolves the error
- Preserve the original logic and intent
- Keep all project.dataset prefixes
- Maintain OMOP CDM field names

RULES:
- Only output SQL (no markdown, no explanations)
- Do not remove table qualifiers
- Do not change the query logic unless needed to fix the error
- If the error is about missing tables, verify the project.dataset path is correct
""",
)


# ============================================================================
# Main Workflow
# ============================================================================


def run_bigquery_sql_generation(
    cohort_input: CohortInput,
    omop_dataset: str = "bigquery-public-data.cms_synthetic_patient_data_omop",
    project_id: Optional[str] = None,
    location: str = "US",
    max_fix_iterations: int = 3,
) -> SQLGenerationResult:
    """
    Generate and validate BigQuery SQL for OMOP cohort definition.

    Args:
        cohort_input: Clinical definition + concept sets from previous stages
        omop_dataset: BigQuery dataset with OMOP CDM tables
        project_id: GCP project ID (optional)
        location: BigQuery location/region
        max_fix_iterations: Maximum attempts to fix SQL syntax errors

    Returns:
        SQLGenerationResult with validated SQL and metadata
    """

    print("\n" + "=" * 70)
    print("STAGE 3: BIGQUERY SQL GENERATION")
    print("=" * 70)

    # Format input for agent
    clinical_text = _format_clinical_definition(cohort_input.clinical_definition)
    concept_sets_text = _format_concept_sets(cohort_input.concept_sets)

    prompt = f"""
Cohort Definition:
{clinical_text}

Concept Sets:
{concept_sets_text}

BigQuery OMOP Dataset: {omop_dataset}

Generate BigQuery Standard SQL to identify the cohort members (person_id).
"""

    print("\n[Step 1] Generating initial SQL...\n")

    # Generate initial SQL
    result = sql_generator_agent.run_sync(prompt)
    current_sql = result.output.strip()

    # Remove markdown code blocks if present
    current_sql = _clean_sql(current_sql)

    print(f"Generated SQL ({len(current_sql)} characters)")
    print(f"\nSQL Preview:\n{current_sql[:300]}...\n")

    # Iteratively validate and fix SQL
    for iteration in range(1, max_fix_iterations + 1):
        print(f"[Step {iteration + 1}] Validating SQL (dry run)...")

        dry_run_input = DryRunInput(
            sql=current_sql, project_id=project_id, default_dataset=omop_dataset, location=location
        )

        try:
            validation_result = validate_bigquery_sql(dry_run_input)
        except Exception as e:
            print(f"⚠️  Dry run failed: {e}")
            validation_result = DryRunResult(
                success=False, errors=[str(e)], total_bytes_processed=0
            )

        if validation_result.success:
            print("✅ SQL is valid!")
            print(f"   Estimated cost: ${validation_result.estimated_cost_usd:.4f}")
            print(
                f"   Bytes to process: {validation_result.total_bytes_processed / (1024**3):.2f} GB"
            )

            return SQLGenerationResult(
                sql=current_sql,
                is_valid=True,
                errors=[],
                estimated_cost_usd=validation_result.estimated_cost_usd,
                total_bytes_processed=validation_result.total_bytes_processed,
                summary=validation_result.summary or "SQL validated successfully",
            )

        # SQL has errors - try to fix
        print(f"❌ SQL validation failed (attempt {iteration}/{max_fix_iterations})")
        print(f"   Errors: {validation_result.errors}")

        if iteration >= max_fix_iterations:
            print("\n⚠️  Max fix iterations reached. Returning SQL with errors.")
            return SQLGenerationResult(
                sql=current_sql,
                is_valid=False,
                errors=validation_result.errors,
                summary=f"SQL validation failed after {max_fix_iterations} attempts",
            )

        # Attempt to fix SQL
        print(f"\n[Step {iteration + 2}] Attempting to fix SQL...")

        fix_prompt = f"""
Original SQL:
{current_sql}

BigQuery Errors:
{json.dumps(validation_result.errors, indent=2)}

Output ONLY the corrected SQL.
"""

        fix_result = sql_fixer_agent.run_sync(fix_prompt)
        current_sql = _clean_sql(fix_result.output.strip())

        print(f"   SQL updated ({len(current_sql)} characters)")

    # Should never reach here, but just in case
    return SQLGenerationResult(
        sql=current_sql, is_valid=False, errors=["Unknown error"], summary="Unexpected completion"
    )


def _format_clinical_definition(clinical_def: Dict[str, Any]) -> str:
    """Format clinical definition for prompt."""
    parts = []

    if clinical_def.get("index_event"):
        parts.append(f"Index Event: {clinical_def['index_event']}")

    if clinical_def.get("demographics"):
        demo_str = ", ".join(f"{k}: {v}" for k, v in clinical_def["demographics"].items())
        parts.append(f"Demographics: {demo_str}")

    if clinical_def.get("inclusion_criteria"):
        criteria = clinical_def["inclusion_criteria"]
        if isinstance(criteria, list):
            parts.append(f"Inclusion: {'; '.join(criteria)}")
        else:
            parts.append(f"Inclusion: {criteria}")

    if clinical_def.get("exclusion_criteria"):
        criteria = clinical_def["exclusion_criteria"]
        if isinstance(criteria, list):
            parts.append(f"Exclusion: {'; '.join(criteria)}")
        else:
            parts.append(f"Exclusion: {criteria}")

    if clinical_def.get("observation_window"):
        parts.append(f"Observation Window: {clinical_def['observation_window']}")

    return "\n".join(parts) if parts else "No clinical definition provided"


def _format_concept_sets(concept_sets: List[ConceptSet]) -> str:
    """Format concept sets for prompt with domain information."""
    lines = []

    for cs in concept_sets:
        concept_ids = [c.get("concept_id") for c in cs.included_concepts if c.get("concept_id")]

        # Extract domain from first concept (all should be same domain)
        domain = "Unknown"
        if cs.included_concepts and len(cs.included_concepts) > 0:
            domain = cs.included_concepts[0].get("domain_id", "Unknown")

        lines.append(f"\nConcept Set: {cs.name}")
        lines.append(f"  Domain: {domain}")
        lines.append(f"  Concept IDs: {concept_ids}")
        lines.append(f"  Include Descendants: {cs.include_descendants}")
        lines.append(f"  Standard Only: {cs.standard_only}")

        if cs.included_concepts:
            lines.append("  Sample Concepts:")
            for concept in cs.included_concepts[:3]:  # Show first 3
                lines.append(
                    f"    - {concept.get('concept_id')}: {concept.get('concept_name')} (Domain: {concept.get('domain_id', 'N/A')})"
                )

    return "\n".join(lines) if lines else "No concept sets provided"


def _clean_sql(sql: str) -> str:
    """Remove markdown code blocks from SQL."""
    sql = sql.strip()

    # Remove ```sql and ``` markers
    if sql.startswith("```"):
        lines = sql.split("\n")
        # Remove first line if it's ```sql or ```
        if lines[0].strip() in ["```sql", "```"]:
            lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        sql = "\n".join(lines)

    return sql.strip()


# ============================================================================
# CLI Interface
# ============================================================================


def main():
    """
    Run BigQuery SQL generation from Stage 1 + Stage 2 output.

    Reads from: projects/run/complete_cohort_output.json
    Outputs: SQL to console and file
    """

    # Load output from previous stages
    input_file = project_root / "projects" / "run" / "complete_cohort_output.json"

    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        print("\n💡 Run Stage 1 + Stage 2 first:")
        print(f"   cd {project_root / 'projects' / 'run'}")
        print("   ./run_integrated.sh")
        return

    print(f"📂 Loading cohort definition from: {input_file}")

    with open(input_file, "r") as f:
        data = json.load(f)

    # Parse input
    clinical_definition = data.get("clinical_definition", {})
    concept_sets_raw = data.get("concept_sets", [])

    # Convert to Pydantic models
    concept_sets = [ConceptSet(**cs) for cs in concept_sets_raw]

    cohort_input = CohortInput(clinical_definition=clinical_definition, concept_sets=concept_sets)

    # Get OMOP dataset from environment or use default
    omop_dataset = os.getenv(
        "OMOP_DATASET_ID", "bigquery-public-data.cms_synthetic_patient_data_omop"
    )
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    location = os.getenv("BIGQUERY_LOCATION", "US")

    print(f"🗄️  OMOP Dataset: {omop_dataset}")
    if project_id:
        print(f"🔑 GCP Project: {project_id}")
    print(f"🌎 Location: {location}")

    # Optional: warn if ADC project differs from env
    try:
        from google.auth import default as google_auth_default  # type: ignore

        _, detected_project = google_auth_default()
        if detected_project and project_id and detected_project != project_id:
            print(
                f"⚠️  Warning: ADC default project '{detected_project}' differs from BIGQUERY_PROJECT_ID '{project_id}'. "
                "Dry-run will use BIGQUERY_PROJECT_ID; run 'gcloud config set project <id>' to align if needed."
            )
    except Exception:
        pass

    # Run SQL generation
    result = run_bigquery_sql_generation(
        cohort_input=cohort_input,
        omop_dataset=omop_dataset,
        project_id=project_id,
        location=location,
        max_fix_iterations=3,
    )

    # Display results
    print("\n" + "=" * 70)
    print("✅ SQL GENERATION COMPLETE")
    print("=" * 70)

    if result.is_valid:
        print("\n✅ Status: Valid SQL")
        print(f"💰 Estimated Cost: ${result.estimated_cost_usd:.4f}")
        print(f"📊 Data to Process: {result.total_bytes_processed / (1024**3):.2f} GB")
    else:
        print("\n⚠️  Status: SQL has validation errors")
        print(f"❌ Errors: {result.errors}")

    print("\n📝 Generated SQL:")
    print("-" * 70)
    print(result.sql)
    print("-" * 70)

    # Save SQL to file
    output_sql_file = project_root / "projects" / "qb" / "generated_cohort_query.sql"
    with open(output_sql_file, "w") as f:
        f.write(result.sql)

    print(f"\n💾 SQL saved to: {output_sql_file}")

    # Save full result as JSON
    output_json_file = project_root / "projects" / "qb" / "sql_generation_result.json"
    with open(output_json_file, "w") as f:
        json.dump(result.model_dump(), f, indent=2)

    print(f"💾 Full result saved to: {output_json_file}")

    print("\n" + "=" * 70)
    print("🎉 Stage 3 Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
