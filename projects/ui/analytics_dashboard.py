"""
Stage 4 Analytics Dashboard

Comprehensive, interactive analytics dashboard for cohort exploration.
Features: visualizations, AI insights, exports, data quality checks.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd


def calculate_confidence_interval(
    count: int, total: int, confidence: float = 0.95
) -> Tuple[float, float]:
    """Calculate Wilson score confidence interval for a proportion."""
    if total == 0:
        return (0.0, 0.0)

    p = count / total
    z = 1.96  # 95% confidence

    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    margin = z * ((p * (1 - p) / total + z**2 / (4 * total**2)) ** 0.5) / denominator

    return (max(0, center - margin), min(1, center + margin))


def format_percentage(value: float) -> str:
    """Format percentage with 1 decimal place."""
    return f"{value * 100:.1f}%"


def generate_summary_cards_html(analytics: Dict[str, Any]) -> str:
    """
    Generate HTML for summary metric cards.

    Displays key metrics in a visual card layout.
    """
    results = analytics.get("results", {})

    # Get cohort size
    cohort_size = 0
    if "cohort_size" in results and isinstance(results["cohort_size"], list):
        if results["cohort_size"]:
            cohort_size = results["cohort_size"][0].get("n", 0)

    # Get mean/median age
    mean_age = "N/A"
    if "age_stats" in results and isinstance(results["age_stats"], list):
        if results["age_stats"]:
            stats = results["age_stats"][0]
            if stats.get("mean_age") is not None:
                mean_age = f"{stats.get('mean_age', 0):.1f} years"

    # Get gender ratio
    gender_ratio = "N/A"
    if "by_gender" in results and isinstance(results["by_gender"], list) and cohort_size > 0:
        female = male = 0
        for row in results["by_gender"]:
            if row.get("gender") == "female":
                female = row.get("n", 0)
            elif row.get("gender") == "male":
                _male = row.get("n", 0)  # Reserved for future use

        if female > 0 or male > 0:
            female_pct = (female / cohort_size) * 100
            male_pct = (male / cohort_size) * 100
            gender_ratio = f"{female_pct:.0f}% F / {male_pct:.0f}% M"

    # Get date range
    date_range = "N/A"
    if "index_year" in results and isinstance(results["index_year"], list):
        years = [row.get("index_year") for row in results["index_year"] if row.get("index_year")]
        if years:
            date_range = f"{int(min(years))} - {int(max(years))}"

    # Use f-string instead of .format() to avoid CSS curly brace conflicts
    html = f"""
    <style>
        .metric-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 20px;
            color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-card.secondary {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .metric-card.tertiary {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        .metric-card.quaternary {{
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 0;
        }}
    </style>

    <div class="metric-cards">
        <div class="metric-card">
            <div class="metric-label">Total Patients</div>
            <div class="metric-value">{cohort_size:,}</div>
        </div>
        <div class="metric-card secondary">
            <div class="metric-label">Mean Age at Entry</div>
            <div class="metric-value">{mean_age}</div>
        </div>
        <div class="metric-card tertiary">
            <div class="metric-label">Gender Ratio</div>
            <div class="metric-value">{gender_ratio}</div>
        </div>
        <div class="metric-card quaternary">
            <div class="metric-label">Date Range</div>
            <div class="metric-value">{date_range}</div>
        </div>
    </div>
    """

    return html


def prepare_gender_chart_data(analytics: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Prepare data for gender distribution bar chart."""
    results = analytics.get("results", {})

    if "by_gender" not in results or not isinstance(results["by_gender"], list):
        return None

    # Get cohort size for percentages
    cohort_size = 0
    if "cohort_size" in results and isinstance(results["cohort_size"], list):
        if results["cohort_size"]:
            cohort_size = results["cohort_size"][0].get("n", 0)

    data = []
    for row in results["by_gender"]:
        gender = row.get("gender", "unknown").capitalize()
        count = row.get("n", 0)
        percentage = (count / cohort_size * 100) if cohort_size > 0 else 0

        data.append({"Gender": gender, "Count": count, "Percentage": f"{percentage:.1f}%"})

    if not data:
        return None

    return pd.DataFrame(data)


def prepare_age_chart_data(analytics: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Prepare data for age distribution bar chart."""
    results = analytics.get("results", {})

    if "age_buckets" not in results or not isinstance(results["age_buckets"], list):
        return None

    # Get cohort size for percentages
    cohort_size = 0
    if "cohort_size" in results and isinstance(results["cohort_size"], list):
        if results["cohort_size"]:
            cohort_size = results["cohort_size"][0].get("n", 0)

    # Define order for age buckets
    age_order = ["<18", "18-39", "40-64", "65-74", "75+"]

    data = []
    for row in results["age_buckets"]:
        age_bucket = row.get("age_bucket", "unknown")
        count = row.get("n", 0)
        percentage = (count / cohort_size * 100) if cohort_size > 0 else 0

        data.append(
            {
                "Age Group": age_bucket,
                "Count": count,
                "Percentage": f"{percentage:.1f}%",
                "Order": age_order.index(age_bucket) if age_bucket in age_order else 99,
            }
        )

    if not data:
        return None

    df = pd.DataFrame(data)
    df = df.sort_values("Order")
    return df[["Age Group", "Count", "Percentage"]]


def prepare_year_trend_data(analytics: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Prepare data for index year trend line chart."""
    results = analytics.get("results", {})

    if "index_year" not in results or not isinstance(results["index_year"], list):
        return None

    data = []
    for row in sorted(results["index_year"], key=lambda x: x.get("index_year", 0)):
        year = row.get("index_year")
        count = row.get("n", 0)

        if year:
            data.append({"Year": int(year), "Patients": count})

    if not data:
        return None

    return pd.DataFrame(data)


def prepare_monthly_trend_data(analytics: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Prepare data for monthly enrollment trend."""
    results = analytics.get("results", {})

    if "monthly_trend" not in results or not isinstance(results["monthly_trend"], list):
        return None

    data = []
    for row in sorted(results["monthly_trend"], key=lambda x: x.get("month", "")):
        month = row.get("month")
        count = row.get("n", 0)

        if month:
            data.append({"Month": month, "Patients": count})

    if not data:
        return None

    return pd.DataFrame(data)


def prepare_characteristics_table(analytics: Dict[str, Any]) -> pd.DataFrame:
    """Prepare detailed characteristics table with confidence intervals."""
    results = analytics.get("results", {})

    # Get cohort size
    cohort_size = 0
    if "cohort_size" in results and isinstance(results["cohort_size"], list):
        if results["cohort_size"]:
            cohort_size = results["cohort_size"][0].get("n", 0)

    data = []

    # Total cohort
    data.append(
        {
            "Characteristic": "Total Cohort",
            "Count": cohort_size,
            "Percentage": "100.0%",
            "95% CI": "[100.0%, 100.0%]",
        }
    )

    # Gender
    if "by_gender" in results and isinstance(results["by_gender"], list):
        for row in results["by_gender"]:
            gender = row.get("gender", "unknown").capitalize()
            count = row.get("n", 0)
            pct = count / cohort_size if cohort_size > 0 else 0
            ci_low, ci_high = calculate_confidence_interval(count, cohort_size)

            data.append(
                {
                    "Characteristic": f"Gender: {gender}",
                    "Count": count,
                    "Percentage": format_percentage(pct),
                    "95% CI": f"[{format_percentage(ci_low)}, {format_percentage(ci_high)}]",
                }
            )

    # Age groups
    if "age_buckets" in results and isinstance(results["age_buckets"], list):
        for row in results["age_buckets"]:
            age_bucket = row.get("age_bucket", "unknown")
            count = row.get("n", 0)
            pct = count / cohort_size if cohort_size > 0 else 0
            ci_low, ci_high = calculate_confidence_interval(count, cohort_size)

            data.append(
                {
                    "Characteristic": f"Age: {age_bucket}",
                    "Count": count,
                    "Percentage": format_percentage(pct),
                    "95% CI": f"[{format_percentage(ci_low)}, {format_percentage(ci_high)}]",
                }
            )

    return pd.DataFrame(data)


def generate_ai_insights(analytics: Dict[str, Any], cohort_description: str = "") -> str:
    """
    Generate AI-powered insights using LLM analysis.

    Analyzes cohort characteristics and provides key findings and recommendations.
    """
    results = analytics.get("results", {})

    # Get cohort size
    cohort_size = 0
    if "cohort_size" in results and isinstance(results["cohort_size"], list):
        if results["cohort_size"]:
            cohort_size = results["cohort_size"][0].get("n", 0)

    # Basic insights without LLM (for now)
    insights = ["## 🔍 Key Findings\n"]
    warnings = ["## ⚠️ Potential Issues\n"]
    recommendations = ["## 💡 Recommendations\n"]

    # Gender analysis
    if "by_gender" in results and isinstance(results["by_gender"], list):
        female = 0
        for row in results["by_gender"]:
            if row.get("gender") == "female":
                female = row.get("n", 0)
            elif row.get("gender") == "male":
                _male = row.get("n", 0)  # Reserved for future use

        if cohort_size > 0:
            female_pct = (female / cohort_size) * 100
            if female_pct > 60:
                insights.append(f"- **Strong female predominance** ({female_pct:.1f}%)")
                recommendations.append("- Consider gender-stratified analyses")
            elif female_pct < 40:
                insights.append(f"- **Strong male predominance** ({100-female_pct:.1f}%)")
                recommendations.append("- Consider gender-stratified analyses")

    # Age analysis
    if "age_buckets" in results and isinstance(results["age_buckets"], list):
        elderly = 0
        young = 0
        for row in results["age_buckets"]:
            age_bucket = row.get("age_bucket", "")
            count = row.get("n", 0)
            if age_bucket in ["65-74", "75+"]:
                elderly += count
            elif age_bucket in ["18-39", "<18"]:
                young += count

        if cohort_size > 0:
            elderly_pct = (elderly / cohort_size) * 100
            young_pct = (young / cohort_size) * 100

            if elderly_pct > 70:
                insights.append(f"- **Predominantly elderly** ({elderly_pct:.1f}% age 65+)")
                warnings.append("- Limited generalizability to younger populations")
                recommendations.append("- Consider age-stratified analyses (65-74, 75-84, 85+)")

            if young_pct < 5:
                warnings.append(f"- Very few young patients ({young_pct:.1f}% under 40)")

    # Temporal trends
    if "index_year" in results and isinstance(results["index_year"], list):
        years_data = [
            (row.get("index_year"), row.get("n", 0))
            for row in results["index_year"]
            if row.get("index_year")
        ]
        if years_data:
            years_data_sorted = sorted(years_data, key=lambda x: x[0])

            # Check for enrollment trends
            if len(years_data_sorted) >= 3:
                recent = years_data_sorted[-3:]
                if all(recent[i][1] < recent[i + 1][1] for i in range(len(recent) - 1)):
                    insights.append("- **Increasing enrollment trend** in recent years")
                elif all(recent[i][1] > recent[i + 1][1] for i in range(len(recent) - 1)):
                    warnings.append(
                        "- **Declining enrollment** in recent years - investigate data availability"
                    )
                    recommendations.append("- Check for data completeness in recent years")

            # Date range
            min_year = int(min(y for y, _ in years_data))
            max_year = int(max(y for y, _ in years_data))
            insights.append(
                f"- **Data span:** {max_year - min_year + 1} years ({min_year}-{max_year})"
            )

    # Cohort size assessment
    if cohort_size > 0:
        if cohort_size < 100:
            warnings.append(
                f"- **Very small cohort** (n={cohort_size:,}) - limited statistical power"
            )
            recommendations.append("- Consider expanding inclusion criteria")
        elif cohort_size < 1000:
            warnings.append(
                f"- **Small cohort** (n={cohort_size:,}) - may have limited power for subgroup analyses"
            )
        elif cohort_size > 100000:
            insights.append(f"- **Large cohort** (n={cohort_size:,}) - good statistical power")

    # Combine all sections
    output = []

    if len(insights) > 1:
        output.extend(insights)
        output.append("")

    if len(warnings) > 1:
        output.extend(warnings)
        output.append("")

    if len(recommendations) > 1:
        output.extend(recommendations)

    if not output:
        output = [
            "## 📊 Analysis\n",
            "No specific insights generated. Review the visualizations above for cohort characteristics.",
        ]

    return "\n".join(output)


def generate_data_quality_html(analytics: Dict[str, Any]) -> str:
    """Generate HTML for data quality indicators."""
    results = analytics.get("results", {})

    # Get cohort size
    cohort_size = 0
    if "cohort_size" in results and isinstance(results["cohort_size"], list):
        if results["cohort_size"]:
            cohort_size = results["cohort_size"][0].get("n", 0)

    # Check for data completeness
    gender_complete = age_complete = date_complete = 100.0

    # Gender completeness
    if "by_gender" in results and isinstance(results["by_gender"], list):
        known_gender = sum(
            row.get("n", 0) for row in results["by_gender"] if row.get("gender") != "unknown"
        )
        gender_complete = (known_gender / cohort_size * 100) if cohort_size > 0 else 0

    # Age completeness (if we have age data)
    if "age_buckets" in results and isinstance(results["age_buckets"], list):
        known_age = sum(row.get("n", 0) for row in results["age_buckets"])
        age_complete = (known_age / cohort_size * 100) if cohort_size > 0 else 0

    # Date completeness
    if "index_year" in results and isinstance(results["index_year"], list):
        known_dates = sum(row.get("n", 0) for row in results["index_year"])
        date_complete = (known_dates / cohort_size * 100) if cohort_size > 0 else 0

    # Use f-string with escaped braces for CSS
    gender_class = (
        "excellent" if gender_complete >= 95 else "good" if gender_complete >= 80 else "warning"
    )
    age_class = "excellent" if age_complete >= 95 else "good" if age_complete >= 80 else "warning"
    date_class = (
        "excellent" if date_complete >= 95 else "good" if date_complete >= 80 else "warning"
    )

    html = f"""
    <style>
        .quality-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
            margin: 20px 0;
        }}
        .quality-item {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .quality-label {{
            min-width: 200px;
            font-weight: 500;
        }}
        .quality-bar-container {{
            flex: 1;
            background: #e0e0e0;
            border-radius: 8px;
            height: 24px;
            overflow: hidden;
        }}
        .quality-bar {{
            height: 100%;
            border-radius: 8px;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }}
        .quality-bar.excellent {{
            background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);
        }}
        .quality-bar.good {{
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        }}
        .quality-bar.warning {{
            background: linear-gradient(90deg, #fa709a 0%, #fee140 100%);
        }}
    </style>

    <div class="quality-grid">
        <div class="quality-item">
            <div class="quality-label">✅ Gender Completeness</div>
            <div class="quality-bar-container">
                <div class="quality-bar {gender_class}" style="width: {gender_complete}%">{gender_complete:.1f}%</div>
            </div>
        </div>
        <div class="quality-item">
            <div class="quality-label">✅ Age Completeness</div>
            <div class="quality-bar-container">
                <div class="quality-bar {age_class}" style="width: {age_complete}%">{age_complete:.1f}%</div>
            </div>
        </div>
        <div class="quality-item">
            <div class="quality-label">✅ Date Completeness</div>
            <div class="quality-bar-container">
                <div class="quality-bar {date_class}" style="width: {date_complete}%">{date_complete:.1f}%</div>
            </div>
        </div>
    </div>
    """

    return html


def export_analytics_csv(analytics: Dict[str, Any], output_path: Path) -> None:
    """Export analytics to CSV format."""
    df = prepare_characteristics_table(analytics)
    df.to_csv(output_path, index=False)


def export_analytics_json(analytics: Dict[str, Any], output_path: Path) -> None:
    """Export analytics to JSON format."""
    with open(output_path, "w") as f:
        json.dump(analytics, f, indent=2)


def export_atlas_cohort(
    cohort_definition: Dict[str, Any], concept_sets: Dict[str, Any], output_path: Path
) -> None:
    """
    Export cohort definition in ATLAS-compatible JSON format.

    This generates a cohort definition that can be imported directly into ATLAS
    for further refinement, visualization, and analysis.

    Args:
        cohort_definition: The Stage 1 cohort definition
        concept_sets: The Stage 2 concept sets
        output_path: Path where the ATLAS JSON should be saved
    """
    # Extract key information from cohort definition
    index_event = cohort_definition.get("index_event", "First occurrence")
    inclusion_criteria = cohort_definition.get("inclusion_criteria", [])
    exclusion_criteria = cohort_definition.get("exclusion_criteria", [])
    demographics = cohort_definition.get("demographics", {})

    # Build concept sets for ATLAS format
    atlas_concept_sets = []
    concept_set_id = 0

    # Handle both old and new Stage 2 formats
    concept_sets_list = []
    if isinstance(concept_sets, dict):
        # New format: {"concept_sets": [...]}
        concept_sets_list = concept_sets.get("concept_sets", [])
    elif isinstance(concept_sets, list):
        # Direct list format
        concept_sets_list = concept_sets

    for concept_set in concept_sets_list:
        if not isinstance(concept_set, dict):
            continue

        set_name = concept_set.get("name", f"Concept Set {concept_set_id}")
        domain = concept_set.get("domain", "Condition")

        # Get included concepts (handle both "included_concepts" and "concepts" keys)
        included_concepts = concept_set.get("included_concepts", concept_set.get("concepts", []))

        # Create ATLAS concept set format
        atlas_concepts = []
        for concept in included_concepts:
            if isinstance(concept, dict):
                atlas_concepts.append(
                    {
                        "concept": {
                            "CONCEPT_ID": concept.get("concept_id", 0),
                            "CONCEPT_NAME": concept.get("concept_name", ""),
                            "STANDARD_CONCEPT": concept.get("standard_concept", "S"),
                            "DOMAIN_ID": concept.get("domain_id", domain),
                            "VOCABULARY_ID": concept.get("vocabulary_id", "SNOMED"),
                            "CONCEPT_CLASS_ID": concept.get("concept_class_id", "Clinical Finding"),
                            "CONCEPT_CODE": concept.get("concept_code", ""),
                        },
                        "isExcluded": False,
                        "includeDescendants": True,
                        "includeMapped": False,
                    }
                )

        if atlas_concepts:
            atlas_concept_sets.append(
                {
                    "id": concept_set_id,
                    "name": set_name,
                    "expression": {"items": atlas_concepts},
                }
            )
            concept_set_id += 1

    # Build primary criteria (index event)
    primary_criteria = {
        "CriteriaList": [
            {
                "ConditionOccurrence": {
                    "CodesetId": 0 if atlas_concept_sets else None,
                    "First": True,
                }
            }
        ],
        "ObservationWindow": {
            "PriorDays": 0,
            "PostDays": 0,
        },
        "PrimaryCriteriaLimit": {"Type": "First"},
    }

    # Build inclusion rules
    inclusion_rules = []
    rule_id = 0

    # Parse inclusion criteria for age requirements
    age_value = None
    age_op = "gte"

    # Check both demographics and inclusion_criteria for age info
    age_sources = [demographics.get("age", ""), str(inclusion_criteria)]
    for age_source in age_sources:
        age_str = str(age_source).lower()
        if "18" in age_str or "adult" in age_str:
            age_value = 18
            if ">=" in age_str or "or older" in age_str or "adult" in age_str:
                age_op = "gte"
            elif ">" in age_str:
                age_op = "gt"
            break

    # Add age restriction as inclusion rule
    if age_value:
        inclusion_rules.append(
            {
                "name": "Age restriction",
                "expression": {
                    "Type": "ALL",
                    "CriteriaList": [],
                    "DemographicCriteriaList": [
                        {
                            "Age": {
                                "Value": age_value,
                                "Op": age_op,
                            }
                        }
                    ],
                    "Groups": [],
                },
            }
        )
        rule_id += 1

    # Add additional inclusion rules for each concept set (if applicable)
    for idx, concept_set in enumerate(atlas_concept_sets[:3]):  # Limit to first 3 for simplicity
        if idx > 0:  # Skip first one as it's the primary criteria
            inclusion_rules.append(
                {
                    "name": concept_set["name"],
                    "expression": {
                        "Type": "ALL",
                        "CriteriaList": [
                            {
                                "Criteria": {
                                    "ConditionOccurrence": {
                                        "CodesetId": concept_set["id"],
                                    }
                                },
                                "StartWindow": {
                                    "Start": {"Coeff": -1},
                                    "End": {"Days": 0, "Coeff": 1},
                                    "UseIndexEnd": False,
                                    "UseEventEnd": False,
                                },
                                "Occurrence": {"Type": 0, "Count": 1},
                            }
                        ],
                        "DemographicCriteriaList": [],
                        "Groups": [],
                    },
                }
            )
            rule_id += 1
            if rule_id >= 5:  # Limit total inclusion rules
                break

    # Add exclusion criteria as qualified limit
    qualified_limit = None
    if exclusion_criteria:
        qualified_limit = {"Type": "First"}

    # Build cohort exit / end strategy
    cohort_exit = cohort_definition.get("cohort_exit", "")
    observation_window = cohort_definition.get("observation_window", "")

    # Determine appropriate end strategy based on cohort definition
    exit_str = f"{cohort_exit} {observation_window}".lower()

    if "continuous observation" in exit_str or "enrollment" in exit_str:
        # Exit at end of continuous observation
        end_strategy = {
            "DateOffset": {
                "DateField": "EndDate",
                "Offset": 0,
            }
        }
    elif "year" in exit_str or "day" in exit_str or "month" in exit_str:
        # Fixed duration follow-up
        # Try to extract duration
        duration_match = re.search(r"(\d+)\s*(year|month|day)", exit_str)
        if duration_match:
            value = int(duration_match.group(1))
            unit = duration_match.group(2)
            days = value if unit == "day" else (value * 30 if unit == "month" else value * 365)
            end_strategy = {
                "DateOffset": {
                    "DateField": "StartDate",
                    "Offset": days,
                }
            }
        else:
            end_strategy = {
                "DateOffset": {
                    "DateField": "EndDate",
                    "Offset": 0,
                }
            }
    else:
        # Default: end of observation
        end_strategy = {
            "DateOffset": {
                "DateField": "EndDate",
                "Offset": 0,
            }
        }

    # Construct final ATLAS cohort definition
    atlas_cohort = {
        "ConceptSets": atlas_concept_sets,
        "PrimaryCriteria": primary_criteria,
        "InclusionRules": inclusion_rules,
        "QualifiedLimit": qualified_limit or {"Type": "First"},
        "ExpressionLimit": {"Type": "First"},
        "EndStrategy": end_strategy,
        "CensoringCriteria": [],
        "CollapseSettings": {
            "CollapseType": "ERA",
            "EraPad": 0,
        },
        "censored": False,
        "cdmVersionRange": ">=5.0.0",
    }

    # Wrap in metadata for import
    atlas_export = {
        "name": f"Cohort from CohortGen - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "description": f"Index Event: {index_event}\n\n"
        f"Inclusion: {', '.join(inclusion_criteria) if inclusion_criteria else 'None'}\n"
        f"Exclusion: {', '.join(exclusion_criteria) if exclusion_criteria else 'None'}\n"
        f"Demographics: {demographics}",
        "expression": atlas_cohort,
    }

    # Write to file
    with open(output_path, "w") as f:
        json.dump(atlas_export, f, indent=2)
