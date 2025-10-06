"""
Stage 4 Analytics Dashboard

Comprehensive, interactive analytics dashboard for cohort exploration.
Features: visualizations, AI insights, exports, data quality checks.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def calculate_confidence_interval(count: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate Wilson score confidence interval for a proportion."""
    if total == 0:
        return (0.0, 0.0)
    
    p = count / total
    z = 1.96  # 95% confidence
    
    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    margin = z * ((p * (1 - p) / total + z**2 / (4 * total**2))**0.5) / denominator
    
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
    mean_age = median_age = "N/A"
    if "age_stats" in results and isinstance(results["age_stats"], list):
        if results["age_stats"]:
            stats = results["age_stats"][0]
            mean_age = f"{stats.get('mean_age', 0):.1f} years"
            median_age = f"{stats.get('median_age', 0):.0f} years"
    
    # Get gender ratio
    gender_ratio = "N/A"
    if "by_gender" in results and isinstance(results["by_gender"], list):
        female = male = 0
        for row in results["by_gender"]:
            if row.get("gender") == "female":
                female = row.get("n", 0)
            elif row.get("gender") == "male":
                male = row.get("n", 0)
        
        if cohort_size > 0:
            female_pct = (female / cohort_size) * 100
            male_pct = (male / cohort_size) * 100
            gender_ratio = f"{female_pct:.0f}% F / {male_pct:.0f}% M"
    
    # Get date range
    date_range = "N/A"
    if "index_year" in results and isinstance(results["index_year"], list):
        years = [row.get("index_year") for row in results["index_year"] if row.get("index_year")]
        if years:
            date_range = f"{int(min(years))} - {int(max(years))}"
    
    html = """
    <style>
        .metric-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 20px;
            color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metric-card.secondary {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .metric-card.tertiary {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        .metric-card.quaternary {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
        .metric-label {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 0;
        }
    </style>
    
    <div class="metric-cards">
        <div class="metric-card">
            <div class="metric-label">Total Patients</div>
            <div class="metric-value">{:,}</div>
        </div>
        <div class="metric-card secondary">
            <div class="metric-label">Mean Age at Entry</div>
            <div class="metric-value">{}</div>
        </div>
        <div class="metric-card tertiary">
            <div class="metric-label">Gender Ratio</div>
            <div class="metric-value">{}</div>
        </div>
        <div class="metric-card quaternary">
            <div class="metric-label">Date Range</div>
            <div class="metric-value">{}</div>
        </div>
    </div>
    """.format(cohort_size, mean_age, gender_ratio, date_range)
    
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
        
        data.append({
            "Gender": gender,
            "Count": count,
            "Percentage": f"{percentage:.1f}%"
        })
    
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
        
        data.append({
            "Age Group": age_bucket,
            "Count": count,
            "Percentage": f"{percentage:.1f}%",
            "Order": age_order.index(age_bucket) if age_bucket in age_order else 99
        })
    
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
            data.append({
                "Year": int(year),
                "Patients": count
            })
    
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
            data.append({
                "Month": month,
                "Patients": count
            })
    
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
    data.append({
        "Characteristic": "Total Cohort",
        "Count": cohort_size,
        "Percentage": "100.0%",
        "95% CI": "[100.0%, 100.0%]"
    })
    
    # Gender
    if "by_gender" in results and isinstance(results["by_gender"], list):
        for row in results["by_gender"]:
            gender = row.get("gender", "unknown").capitalize()
            count = row.get("n", 0)
            pct = count / cohort_size if cohort_size > 0 else 0
            ci_low, ci_high = calculate_confidence_interval(count, cohort_size)
            
            data.append({
                "Characteristic": f"Gender: {gender}",
                "Count": count,
                "Percentage": format_percentage(pct),
                "95% CI": f"[{format_percentage(ci_low)}, {format_percentage(ci_high)}]"
            })
    
    # Age groups
    if "age_buckets" in results and isinstance(results["age_buckets"], list):
        for row in results["age_buckets"]:
            age_bucket = row.get("age_bucket", "unknown")
            count = row.get("n", 0)
            pct = count / cohort_size if cohort_size > 0 else 0
            ci_low, ci_high = calculate_confidence_interval(count, cohort_size)
            
            data.append({
                "Characteristic": f"Age: {age_bucket}",
                "Count": count,
                "Percentage": format_percentage(pct),
                "95% CI": f"[{format_percentage(ci_low)}, {format_percentage(ci_high)}]"
            })
    
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
        female = male = 0
        for row in results["by_gender"]:
            if row.get("gender") == "female":
                female = row.get("n", 0)
            elif row.get("gender") == "male":
                male = row.get("n", 0)
        
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
        years_data = [(row.get("index_year"), row.get("n", 0)) for row in results["index_year"] if row.get("index_year")]
        if years_data:
            years_data_sorted = sorted(years_data, key=lambda x: x[0])
            
            # Check for enrollment trends
            if len(years_data_sorted) >= 3:
                recent = years_data_sorted[-3:]
                if all(recent[i][1] < recent[i+1][1] for i in range(len(recent)-1)):
                    insights.append("- **Increasing enrollment trend** in recent years")
                elif all(recent[i][1] > recent[i+1][1] for i in range(len(recent)-1)):
                    warnings.append("- **Declining enrollment** in recent years - investigate data availability")
                    recommendations.append("- Check for data completeness in recent years")
            
            # Date range
            min_year = int(min(y for y, _ in years_data))
            max_year = int(max(y for y, _ in years_data))
            insights.append(f"- **Data span:** {max_year - min_year + 1} years ({min_year}-{max_year})")
    
    # Cohort size assessment
    if cohort_size > 0:
        if cohort_size < 100:
            warnings.append(f"- **Very small cohort** (n={cohort_size:,}) - limited statistical power")
            recommendations.append("- Consider expanding inclusion criteria")
        elif cohort_size < 1000:
            warnings.append(f"- **Small cohort** (n={cohort_size:,}) - may have limited power for subgroup analyses")
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
        output = ["## 📊 Analysis\n", "No specific insights generated. Review the visualizations above for cohort characteristics."]
    
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
        known_gender = sum(row.get("n", 0) for row in results["by_gender"] if row.get("gender") != "unknown")
        gender_complete = (known_gender / cohort_size * 100) if cohort_size > 0 else 0
    
    # Age completeness (if we have age data)
    if "age_buckets" in results and isinstance(results["age_buckets"], list):
        known_age = sum(row.get("n", 0) for row in results["age_buckets"])
        age_complete = (known_age / cohort_size * 100) if cohort_size > 0 else 0
    
    # Date completeness
    if "index_year" in results and isinstance(results["index_year"], list):
        known_dates = sum(row.get("n", 0) for row in results["index_year"])
        date_complete = (known_dates / cohort_size * 100) if cohort_size > 0 else 0
    
    html = """
    <style>
        .quality-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
            margin: 20px 0;
        }
        .quality-item {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .quality-label {
            min-width: 200px;
            font-weight: 500;
        }
        .quality-bar-container {
            flex: 1;
            background: #e0e0e0;
            border-radius: 8px;
            height: 24px;
            overflow: hidden;
        }
        .quality-bar {
            height: 100%;
            border-radius: 8px;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }
        .quality-bar.excellent {
            background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);
        }
        .quality-bar.good {
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        }
        .quality-bar.warning {
            background: linear-gradient(90deg, #fa709a 0%, #fee140 100%);
        }
    </style>
    
    <div class="quality-grid">
        <div class="quality-item">
            <div class="quality-label">✅ Gender Completeness</div>
            <div class="quality-bar-container">
                <div class="quality-bar {}" style="width: {}%">{:.1f}%</div>
            </div>
        </div>
        <div class="quality-item">
            <div class="quality-label">✅ Age Completeness</div>
            <div class="quality-bar-container">
                <div class="quality-bar {}" style="width: {}%">{:.1f}%</div>
            </div>
        </div>
        <div class="quality-item">
            <div class="quality-label">✅ Date Completeness</div>
            <div class="quality-bar-container">
                <div class="quality-bar {}" style="width: {}%">{:.1f}%</div>
            </div>
        </div>
    </div>
    """.format(
        "excellent" if gender_complete >= 95 else "good" if gender_complete >= 80 else "warning",
        gender_complete, gender_complete,
        "excellent" if age_complete >= 95 else "good" if age_complete >= 80 else "warning",
        age_complete, age_complete,
        "excellent" if date_complete >= 95 else "good" if date_complete >= 80 else "warning",
        date_complete, date_complete
    )
    
    return html


def export_analytics_csv(analytics: Dict[str, Any], output_path: Path) -> None:
    """Export analytics to CSV format."""
    df = prepare_characteristics_table(analytics)
    df.to_csv(output_path, index=False)


def export_analytics_json(analytics: Dict[str, Any], output_path: Path) -> None:
    """Export analytics to JSON format."""
    with open(output_path, 'w') as f:
        json.dump(analytics, f, indent=2)

