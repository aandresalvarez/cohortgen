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
    "openai:gpt-5",
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
    "openai:gpt-5",  # Use more powerful model for fixing
    output_type=str,
    model_settings={"reasoning": {"effort": "medium"}},
    system_prompt="""
You are an expert BigQuery SQL debugger specializing in OMOP CDM schemas.

Your task: Fix BigQuery Standard SQL based on the exact error message provided.

CRITICAL RULES:
1. **Read the error carefully** - BigQuery errors are precise (e.g., "Name procedure_date not found at [57:12]")
2. **Use ONLY columns from provided schema** - Do NOT guess or invent column names
3. **Common OMOP schema variations**:
   - Some datasets have typos (e.g., "procedure_dat" instead of "procedure_date")
   - Date columns might be DATE or DATETIME type
   - Always check the schema for exact column names
4. **Fix strategies**:
   - Column not found → Check schema, use correct column name
   - Table not found → Verify project.dataset.table path
   - Type mismatch → Cast or convert as needed
   - Syntax error → Follow BigQuery Standard SQL syntax
5. **Preserve logic**: Only change what's needed to fix the error
6. **Output format**: SQL ONLY (no markdown, no explanations, no code blocks)

Example fix:
Error: "Name procedure_date not found"
Schema shows: procedure_dat, procedure_datetime
Fix: Replace procedure_date with procedure_datetime (or CAST(procedure_dat AS DATE))
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
    max_fix_iterations: int = 5,
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
    
    # Step 0: Discover available tables and their schemas
    print("\n[Step 0] Discovering available OMOP tables and schemas...")
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project_id, location=location)
        
        # Parse dataset identifier
        if "." in omop_dataset:
            dataset_parts = omop_dataset.split(".", 1)
            ds_project = dataset_parts[0]
            ds_name = dataset_parts[1]
        else:
            ds_project = project_id
            ds_name = omop_dataset
        
        dataset_ref = client.dataset(ds_name, project=ds_project)
        available_tables = {table.table_id for table in client.list_tables(dataset_ref)}
        
        print(f"✅ Found {len(available_tables)} tables in {omop_dataset}")
        print(f"   Available domain tables: {', '.join(sorted(t for t in available_tables if t in ['condition_occurrence', 'procedure_occurrence', 'drug_exposure', 'measurement', 'observation']))}")
        
        # Get schema information for domain tables
        domain_tables = ['condition_occurrence', 'procedure_occurrence', 'drug_exposure', 'measurement', 'observation']
        table_schemas = {}
        
        for table_name in domain_tables:
            if table_name in available_tables:
                try:
                    full_table_id = f"{ds_project}.{ds_name}.{table_name}"
                    table = client.get_table(full_table_id)
                    # Store relevant columns (person_id, concept_id, date columns)
                    columns = [field.name for field in table.schema]
                    date_columns = [col for col in columns if 'date' in col.lower() or 'datetime' in col.lower()]
                    table_schemas[table_name] = {
                        "all_columns": columns,
                        "date_columns": date_columns
                    }
                except Exception as schema_error:
                    print(f"⚠️  Could not fetch schema for {table_name}: {schema_error}")
        
        if table_schemas:
            print(f"\n📋 Schema Discovery:")
            for table_name, schema_info in table_schemas.items():
                date_cols = ', '.join(schema_info['date_columns'][:3])
                print(f"   {table_name}: date columns = {date_cols}")
        
        # Check which concept sets have tables available
        domain_table_map = {
            "Condition": "condition_occurrence",
            "Procedure": "procedure_occurrence",
            "Drug": "drug_exposure",
            "Measurement": "measurement",
            "Observation": "observation",
        }
        
        missing_tables = []
        for concept_set in cohort_input.concept_sets:
            # ConceptSet is a Pydantic model, use attribute access
            domain = getattr(concept_set, "domain", "") if hasattr(concept_set, "domain") else ""
            if not domain and concept_set.included_concepts:
                # Extract domain from first concept
                domain = concept_set.included_concepts[0].get("domain_id", "") if isinstance(concept_set.included_concepts[0], dict) else ""
            
            table_name = domain_table_map.get(domain, "")
            if table_name and table_name not in available_tables:
                concept_set_name = concept_set.name if hasattr(concept_set, "name") else str(concept_set)
                missing_tables.append(f"{concept_set_name} (Domain: {domain} → {table_name})")
        
        if missing_tables:
            print(f"\n⚠️  Warning: Some concept sets reference tables that don't exist:")
            for item in missing_tables:
                print(f"   - {item}")
            print(f"   These concepts will be excluded from the generated SQL.\n")
        
        available_tables_list = list(available_tables)
        
    except Exception as e:
        print(f"⚠️  Could not discover tables: {e}")
        print(f"   Proceeding with default OMOP table assumptions...")
        available_tables_list = []  # Empty means "assume all tables exist"
        table_schemas = {}

    # Format input for agent
    clinical_text = _format_clinical_definition(cohort_input.clinical_definition)
    concept_sets_text = _format_concept_sets(cohort_input.concept_sets, available_tables_list)

    # Add schema information to prompt if available
    schema_hint = ""
    if table_schemas:
        schema_hint = "\n\nIMPORTANT - Actual Table Schemas (use these exact column names):\n"
        for table_name, schema_info in table_schemas.items():
            schema_hint += f"\n{table_name}:\n"
            schema_hint += f"  - Date columns: {', '.join(schema_info['date_columns'])}\n"
            schema_hint += f"  - All columns: {', '.join(schema_info['all_columns'][:20])}{'...' if len(schema_info['all_columns']) > 20 else ''}\n"
    
    prompt = f"""
Cohort Definition:
{clinical_text}

Concept Sets:
{concept_sets_text}

BigQuery OMOP Dataset: {omop_dataset}
{schema_hint}

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
        
        # Add schema context to fix prompt if available
        schema_context = ""
        if table_schemas:
            schema_context = "\n\nAvailable Table Schemas (use ONLY these column names):\n"
            for table_name, schema_info in table_schemas.items():
                schema_context += f"\n{table_name} columns: {', '.join(schema_info['all_columns'])}\n"

        fix_prompt = f"""
Original SQL:
{current_sql}

BigQuery Errors:
{json.dumps(validation_result.errors, indent=2)}
{schema_context}

Instructions:
1. Read the error message carefully - it tells you the exact issue
2. If error mentions "Name X not found", check the table schema above for the correct column name
3. If error mentions missing table, verify the full table path
4. Do NOT invent column names - use ONLY columns from the schema above
5. For date filtering in procedure_occurrence, use the available date columns from schema

Output ONLY the corrected SQL.
"""

        fix_result = sql_fixer_agent.run_sync(fix_prompt)
        current_sql = _clean_sql(fix_result.output.strip())

        print(f"   SQL updated ({len(current_sql)} characters)")
        print(f"   Retrying validation...")

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


def _format_concept_sets(concept_sets: List[ConceptSet], available_tables: List[str] = None) -> str:
    """Format concept sets for prompt with domain information, filtering by available tables."""
    lines = []
    
    domain_table_map = {
        "Condition": "condition_occurrence",
        "Procedure": "procedure_occurrence",
        "Drug": "drug_exposure",
        "Measurement": "measurement",
        "Observation": "observation",
    }

    for cs in concept_sets:
        concept_ids = [c.get("concept_id") for c in cs.included_concepts if c.get("concept_id")]

        # Extract domain from first concept (all should be same domain)
        domain = "Unknown"
        if cs.included_concepts and len(cs.included_concepts) > 0:
            domain = cs.included_concepts[0].get("domain_id", "Unknown")
        
        # Skip concept sets whose domain tables don't exist (if table discovery was successful)
        if available_tables is not None and len(available_tables) > 0:
            table_name = domain_table_map.get(domain, "")
            if table_name and table_name not in available_tables:
                continue  # Skip this concept set

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
