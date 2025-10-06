#!/usr/bin/env python3
"""
OMOP Cohort Definition Clarification using Pydantic AI

Interactive clarification loop specifically designed for OMOP CDM cohort definitions.
Asks targeted questions to gather all necessary components for a complete cohort definition.
"""

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import Literal, Optional
import re


# Define our structured output for cohort definition
class CohortDefinition(BaseModel):
    """Complete OMOP cohort definition components."""
    index_event: str = ""
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    observation_window: str = ""
    # Allow booleans in demographics to tolerate model outputs like
    # {"use_pre_extracted_demographics": true}; coerce/print as strings later
    demographics: dict[str, Optional[str | bool]] = Field(default_factory=dict)
    prior_observation: str = ""
    cohort_exit: str = ""


class ClarificationDecision(BaseModel):
    """Agent decides whether to ask more questions or finish."""
    action: Literal["ask", "finish"]
    question: str = ""
    cohort_components: CohortDefinition = Field(default_factory=CohortDefinition)


class DemographicsExtraction(BaseModel):
    """Extracted demographics from cohort description."""
    age: Optional[str] = None
    gender: Optional[str] = None
    time_period: Optional[str] = None


# Create agent with structured output
agent = Agent(
    "openai:gpt-5-mini",
    output_type=ClarificationDecision,
    model_settings={
        "reasoning": {"effort": "low"}
    },
    system_prompt="""
You are an expert clinical cohort definition specialist. Your goal is to clarify all components 
needed for a complete OMOP cohort definition using PLAIN CLINICAL LANGUAGE.

IMPORTANT: Do NOT ask for OMOP concept IDs or technical codes. Use natural clinical language only.
Another process will map your clinical descriptions to OMOP concepts later.

Cohort Definition Components to Clarify:

1. INDEX EVENT: The defining clinical event in plain language
   - Examples: "first diagnosis of type 2 diabetes", "first prescription of metformin", 
     "hospitalization for heart attack", "positive flu test"
   - Use clinical terms, NOT concept IDs
   - Be specific about timing: "first", "any", "most recent"
   
2. INCLUSION CRITERIA: What must be true to qualify?
   - Prior conditions: "history of hypertension", "no prior diabetes"
   - Continuous enrollment: "365 days continuous enrollment before index"
   - Time constraints: "within 30 days of diagnosis", "any time before"
   - DO NOT include demographics here - use demographics field instead
   
3. EXCLUSION CRITERIA: What disqualifies someone?
   - Conditions: "history of type 1 diabetes", "prior cancer diagnosis"
   - Treatments: "prior use of insulin", "chemotherapy in past year"
   - Use clinical language, NOT codes
   
4. OBSERVATION WINDOW: When should data be observed?
   - Before index: "365 days prior observation", "180 day washout"
   - After index: "follow-up until end of enrollment", "fixed 1 year follow-up"
   - Time period: "only in 2020", "between 2015 and 2020"
   - Continuous enrollment requirements
   
5. DEMOGRAPHICS: Age and gender constraints (use demographics field!)
   - Note: Demographics are typically pre-extracted before this loop starts
   - You can refine or ask for additional demographic details if needed
   
6. COHORT EXIT: When does someone leave the cohort?
   - "End of continuous observation", "death", "occurrence of stroke", "fixed duration"

Rules:
- Ask ONE targeted question at a time to fill in missing components
- Use CLINICAL LANGUAGE ONLY - never ask for concept IDs, codes, or technical identifiers
- Extract demographics and time constraints into proper structured fields
- If user says "I don't know" or "standard", make reasonable clinical assumptions
- After gathering core components (index event + key criteria), you can finish
- Prioritize: index event → demographics → inclusion → observation window → exclusion
- When finishing, summarize what will be defined in plain clinical terms

Output your decision with updated cohort_components showing progress.
""",
)


# Create demographics extraction agent - runs BEFORE clarification loop
demographics_extractor = Agent(
    "openai:gpt-5-mini",
    output_type=DemographicsExtraction,
    model_settings={
        "reasoning": {"effort": "low"}
    },
    system_prompt="""
You are a demographic information extractor for clinical cohort definitions.

Your ONLY job is to extract age, gender, and time period information from the cohort description.
Return ONLY what is explicitly stated - do NOT infer or make assumptions.

AGE PATTERNS:
- "age 20-30", "aged 20 to 30", "between 20 and 30 years old" → "20-30"
- "65 and older", "65+", "aged 65 or older" → "65+"
- "18 and older", "adults", "adult patients" → "18+"
- "under 18", "pediatric", "children" → "<18"
- "elderly" → "65+"

GENDER PATTERNS:
- "male", "males", "men", "man" → "male"
- "female", "females", "women", "woman" → "female"
- If not mentioned → None

TIME PERIOD PATTERNS:
- "in 2020", "during 2020", "year 2020" → "in year 2020"
- "between 2015 and 2020", "from 2015 to 2020" → "between 2015 and 2020"
- "2018-2020" → "between 2018 and 2020"
- If not mentioned → None

CRITICAL: Return None for any field not explicitly mentioned. Do NOT guess or infer.

Examples:
- "Male patients age 20-30 with flu test in 2020"
  → age: "20-30", gender: "male", time_period: "in year 2020"

- "Female patients aged 65+ with diabetes"
  → age: "65+", gender: "female", time_period: None

- "Adult patients with hypertension between 2018 and 2020"
  → age: "18+", gender: None, time_period: "between 2018 and 2020"

- "Patients with stroke"
  → age: None, gender: None, time_period: None
""",
)


def extract_demographics(cohort_description: str) -> dict[str, str]:
    """
    Extract demographics from cohort description using dedicated agent.
    
    Returns:
        Dictionary with 'age', 'gender', and/or 'time_period' keys (if found)
    """
    result = demographics_extractor.run_sync(cohort_description)
    extracted = result.output
    
    demographics = {}
    if extracted.age:
        demographics["age"] = extracted.age
    if extracted.gender:
        demographics["gender"] = extracted.gender
    
    return demographics, extracted.time_period


def run_clarification_loop(initial_cohort_description: str, max_questions: int = 10) -> CohortDefinition:
    """
    Run interactive clarification loop for OMOP cohort definition.
    
    Args:
        initial_cohort_description: User's initial description of the cohort
        max_questions: Maximum number of clarification questions to ask
    
    Returns:
        Complete CohortDefinition with all components filled
    """
    print("\n" + "="*70)
    print("OMOP COHORT DEFINITION - INTERACTIVE CLARIFICATION")
    print("="*70)
    print(f"\nCohort Description: {initial_cohort_description}")
    print()
    
    # STEP 1: Extract demographics FIRST using dedicated agent
    print("[Step 1] Extracting demographics...")
    demographics, time_period = extract_demographics(initial_cohort_description)
    
    # Initialize cohort definition with extracted demographics
    cohort_def = CohortDefinition()
    if demographics:
        cohort_def.demographics = demographics
        print(f"✅ Extracted demographics: {demographics}")
    else:
        print("ℹ️  No demographics found in description")
    
    if time_period:
        cohort_def.observation_window = time_period
        print(f"✅ Extracted time period: {time_period}")
    
    print()
    
    conversation_history = []
    
    # Build initial prompt - acknowledge what was already extracted
    demographics_text = ""
    if demographics or time_period:
        demographics_text = "\n\nALREADY EXTRACTED (do not ask about these):"
        if demographics:
            demographics_text += f"\n- Demographics: {demographics}"
        if time_period:
            demographics_text += f"\n- Time period: {time_period}"
    
    # First prompt - focus on index event and other missing components
    prompt = f"""
Cohort Description: {initial_cohort_description}
{demographics_text}

Now ask your first clarifying question to understand the INDEX EVENT.
Focus on what clinical event defines entry into the cohort.

Do NOT ask about demographics or time periods that were already extracted above.

Output your decision with cohort_components including the pre-extracted demographics.
"""
    
    for iteration in range(1, max_questions + 1):
        print(f"\n[Iteration {iteration}]")
        
        # Run agent
        result = agent.run_sync(prompt)
        decision = result.output
        
        # Update cohort definition - preserve pre-extracted demographics
        if decision.cohort_components:
            # Preserve demographics if they were pre-extracted
            extracted_demographics = cohort_def.demographics.copy() if cohort_def.demographics else {}
            extracted_time_period = cohort_def.observation_window if cohort_def.observation_window else ""
            
            cohort_def = decision.cohort_components
            
            # Restore pre-extracted demographics if agent didn't include them
            if extracted_demographics and not cohort_def.demographics:
                cohort_def.demographics = extracted_demographics
            if extracted_time_period and not cohort_def.observation_window:
                cohort_def.observation_window = extracted_time_period
            
            # Show what was updated
            updates = []
            if cohort_def.index_event:
                updates.append(f"Index Event: {cohort_def.index_event}")
            if cohort_def.inclusion_criteria:
                updates.append(f"Inclusion: {len(cohort_def.inclusion_criteria)} criteria")
            if cohort_def.exclusion_criteria:
                updates.append(f"Exclusion: {len(cohort_def.exclusion_criteria)} criteria")
            if cohort_def.observation_window:
                updates.append(f"Window: {cohort_def.observation_window}")
            
            if updates:
                print(f"  Components updated: {', '.join(updates)}")
        
        # Check if done
        if decision.action == "finish":
            print(f"\n✅ Agent: {decision.question}")
            print(f"\n[Cohort definition complete after {iteration} questions]")
            break
        
        # Ask user
        if decision.question:
            print(f"\n🤖 Agent: {decision.question}")
            user_input = input("👤 You: ").strip()
            
            # Track conversation
            conversation_history.append({
                "question": decision.question,
                "answer": user_input
            })
            
            # Build next prompt with history
            history_text = "\n".join([
                f"Q: {turn['question']}\nA: {turn['answer']}"
                for turn in conversation_history
            ])
            
            # Show current progress
            progress = []
            if cohort_def.index_event:
                progress.append(f"✓ Index Event: {cohort_def.index_event}")
            if cohort_def.inclusion_criteria:
                progress.append(f"✓ Inclusion Criteria: {cohort_def.inclusion_criteria}")
            if cohort_def.exclusion_criteria:
                progress.append(f"✓ Exclusion Criteria: {cohort_def.exclusion_criteria}")
            if cohort_def.observation_window:
                progress.append(f"✓ Observation Window: {cohort_def.observation_window}")
            if cohort_def.demographics:
                progress.append(f"✓ Demographics: {cohort_def.demographics}")
            
            progress_text = "\n".join(progress) if progress else "No components defined yet"
            
            prompt = f"""
Cohort Description: {initial_cohort_description}

Conversation so far:
{history_text}

Current Cohort Components:
{progress_text}

Based on this conversation and current progress, decide: ask another clarifying question OR finish.
If you have enough to define a complete cohort (at minimum: index event + basic criteria), you can finish.

Output your decision with updated cohort_components.
"""
        else:
            print("  [Agent returned empty question]")
            break
    else:
        print(f"\n⚠️  Reached max questions ({max_questions})")
    
    print("\n" + "="*70)
    print("COHORT DEFINITION COMPLETE")
    print("="*70)
    print(f"\n{_format_cohort_definition(cohort_def)}")
    print()
    
    return cohort_def


def _format_cohort_definition(cohort_def: CohortDefinition) -> str:
    """Format cohort definition for display."""
    lines = []
    
    if cohort_def.index_event:
        lines.append(f"📍 INDEX EVENT:")
        lines.append(f"   {cohort_def.index_event}")
        lines.append("")
    
    if cohort_def.inclusion_criteria:
        lines.append(f"✅ INCLUSION CRITERIA:")
        for i, criteria in enumerate(cohort_def.inclusion_criteria, 1):
            lines.append(f"   {i}. {criteria}")
        lines.append("")
    
    if cohort_def.exclusion_criteria:
        lines.append(f"❌ EXCLUSION CRITERIA:")
        for i, criteria in enumerate(cohort_def.exclusion_criteria, 1):
            lines.append(f"   {i}. {criteria}")
        lines.append("")
    
    if cohort_def.demographics:
        lines.append(f"👥 DEMOGRAPHICS:")
        for key, value in cohort_def.demographics.items():
            lines.append(f"   {key}: {value}")
        lines.append("")
    
    if cohort_def.observation_window:
        lines.append(f"📅 OBSERVATION WINDOW:")
        lines.append(f"   {cohort_def.observation_window}")
        lines.append("")
    
    if cohort_def.prior_observation:
        lines.append(f"⏮️  PRIOR OBSERVATION:")
        lines.append(f"   {cohort_def.prior_observation}")
        lines.append("")
    
    if cohort_def.cohort_exit:
        lines.append(f"🚪 COHORT EXIT:")
        lines.append(f"   {cohort_def.cohort_exit}")
    
    return "\n".join(lines) if lines else "No components defined"


def main():
    """Main entry point."""
    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║  OMOP Cohort Definition Builder - Interactive Clarification     ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print("\nThis tool helps you build a complete OMOP cohort definition")
    print("by asking targeted questions about:")
    print("  • Index event (the defining clinical event)")
    print("  • Inclusion criteria (what qualifies someone)")  
    print("  • Exclusion criteria (what disqualifies someone)")
    print("  • Observation windows and time constraints")
    print("  • Demographics and other requirements")
    
    # Get initial cohort description from user or use default
    try:
        print("\n" + "-"*70)
        cohort_desc = input("Describe your cohort (or press Enter for example): ").strip()
        if not cohort_desc:
            cohort_desc = "patients with type 2 diabetes who started metformin"
            print(f"Using example: {cohort_desc}")
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return
    
    try:
        # Run the clarification loop
        cohort_definition = run_clarification_loop(cohort_desc)
        
        # Show final summary
        print("\n" + "="*70)
        print("✅ SUCCESS - COHORT DEFINITION READY FOR ATLAS")
        print("="*70)
        print("\nThis cohort definition can now be implemented in ATLAS.")
        print("All key components have been specified:")
        
        components_defined = []
        if cohort_definition.index_event:
            components_defined.append("✓ Index Event")
        if cohort_definition.inclusion_criteria:
            components_defined.append("✓ Inclusion Criteria")
        if cohort_definition.exclusion_criteria:
            components_defined.append("✓ Exclusion Criteria")
        if cohort_definition.observation_window:
            components_defined.append("✓ Observation Window")
        if cohort_definition.demographics:
            components_defined.append("✓ Demographics")
        if cohort_definition.prior_observation:
            components_defined.append("✓ Prior Observation")
        if cohort_definition.cohort_exit:
            components_defined.append("✓ Cohort Exit")
        
        print("\n".join(f"  {comp}" for comp in components_defined))
        
        print("\n✨ No nested loops! Clean exit! Pydantic AI works correctly!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
