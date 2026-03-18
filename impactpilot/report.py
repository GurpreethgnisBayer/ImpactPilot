"""Generate markdown Impact Brief with disclaimer and citations."""

from impactpilot.disclaimer import DISCLAIMER_TEXT


def build_brief_markdown(
    idea: dict,
    selected_articles: list[dict],
    assumptions: dict,
    tco_out: dict,
    prod_out: dict,
    horizon_years: int = 3
) -> str:
    """
    Build a complete markdown Impact Brief.
    
    Args:
        idea: Idea details (title, description, type, stage)
        selected_articles: List of selected PubMed articles
        assumptions: Inference output with ranges and support levels
        tco_out: Computed TCO metrics
        prod_out: Computed productivity metrics
        horizon_years: Time horizon used
    
    Returns:
        Complete markdown document as string
    """
    md = []
    
    # Title
    md.append(f"# Impact Estimate: {idea.get('title', 'Untitled')}\n")
    
    # Disclaimer
    md.append(f"> **Disclaimer:** {DISCLAIMER_TEXT}\n")
    
    # Summary
    md.append("## Summary\n")
    md.append(f"**Idea Type:** {idea.get('idea_type', 'N/A')}\n")
    md.append(f"**R&D Stage:** {idea.get('rd_stage', 'N/A')}\n")
    if idea.get('description'):
        md.append(f"\n{idea['description']}\n")
    
    # Evidence Used
    md.append("## Evidence Used\n")
    if selected_articles:
        md.append(f"This estimate is based on {len(selected_articles)} selected PubMed articles:\n")
        for article in selected_articles:
            md.append(f"- PMID: {article['pmid']} - {article['title']}\n")
    else:
        md.append("No evidence articles were selected.\n")
    
    # Assumptions
    md.append("## Key Assumptions\n")
    
    if "productivity" in assumptions:
        md.append("### Productivity Gains\n")
        prod = assumptions["productivity"]
        
        if "time_saved_hours_per_month" in prod:
            _append_assumption_field(
                md,
                "Time Saved per Month",
                prod["time_saved_hours_per_month"],
                "hours"
            )
        
        if "cost_avoided_per_year" in prod:
            _append_assumption_field(
                md,
                "Cost Avoided per Year",
                prod["cost_avoided_per_year"],
                "USD"
            )
    
    if "tco" in assumptions:
        md.append("### Total Cost of Ownership\n")
        tco = assumptions["tco"]
        
        if "build_person_days" in tco:
            _append_assumption_field(
                md,
                "Build Time",
                tco["build_person_days"],
                "person-days"
            )
        
        if "run_person_days_per_year" in tco:
            _append_assumption_field(
                md,
                "Annual Operational Cost",
                tco["run_person_days_per_year"],
                "person-days/year"
            )
    
    # Overall confidence
    if "overall_confidence" in assumptions:
        md.append(f"\n**Overall Confidence:** {assumptions['overall_confidence'].upper()}\n")
    
    # Key assumptions list
    if assumptions.get("assumptions"):
        md.append("\n**Key Assumptions:**\n")
        for assumption in assumptions["assumptions"]:
            md.append(f"- {assumption}\n")
    
    # Computed TCO
    md.append(f"## Computed Total Cost of Ownership ({horizon_years}-Year Horizon)\n")
    md.append("*Calculations use midpoint values from assumption ranges and are directional.*\n\n")
    md.append(f"- **Build Cost:** ${tco_out['build_cost_usd']:,.0f}\n")
    md.append(f"  - Based on {tco_out['build_person_days_midpoint']:.1f} person-days at ${tco_out['hourly_rate']}/hour\n")
    md.append(f"- **Annual Operational Cost:** ${tco_out['run_cost_per_year_usd']:,.0f}/year\n")
    md.append(f"  - Based on {tco_out['run_person_days_per_year_midpoint']:.1f} person-days/year\n")
    md.append(f"- **Total {horizon_years}-Year Operational Cost:** ${tco_out['total_run_cost_usd']:,.0f}\n")
    md.append(f"- **Total {horizon_years}-Year TCO:** ${tco_out['total_tco_usd']:,.0f}\n")
    
    # Computed Productivity
    md.append(f"\n## Computed Productivity Gains ({horizon_years}-Year Horizon)\n")
    md.append("*Calculations use midpoint values from assumption ranges and are directional.*\n\n")
    md.append(f"- **Time Saved:** {prod_out['time_saved_hours_per_month_midpoint']:.1f} hours/month\n")
    md.append(f"  - Annual: {prod_out['time_saved_hours_per_year']:.0f} hours/year\n")
    md.append(f"  - {horizon_years}-Year Total: {prod_out['total_time_saved_hours']:.0f} hours\n")
    md.append(f"- **Value of Time Saved:** ${prod_out['time_value_per_year_usd']:,.0f}/year\n")
    md.append(f"  - {horizon_years}-Year Total: ${prod_out['total_time_value_usd']:,.0f}\n")
    md.append(f"- **Additional Cost Avoided:** ${prod_out['cost_avoided_per_year_midpoint']:,.0f}/year\n")
    md.append(f"  - {horizon_years}-Year Total: ${prod_out['total_cost_avoided_usd']:,.0f}\n")
    md.append(f"- **Total Productivity Gain:** ${prod_out['total_productivity_gain_usd']:,.0f}\n")
    
    # Net Impact
    net_impact = prod_out['total_productivity_gain_usd'] - tco_out['total_tco_usd']
    md.append(f"\n## Net Impact ({horizon_years}-Year)\n")
    if net_impact > 0:
        md.append(f"**Net Positive:** ${net_impact:,.0f}\n")
    else:
        md.append(f"**Net Negative:** ${abs(net_impact):,.0f}\n")
    md.append(f"\n*(Total Productivity Gain - Total TCO)*\n")
    
    # Citations
    md.append("\n## Citations\n")
    if selected_articles:
        for i, article in enumerate(selected_articles, 1):
            authors_str = ""
            if article.get("authors"):
                authors_str = ", ".join(article["authors"][:3])
                if len(article["authors"]) > 3:
                    authors_str += " et al."
                authors_str += ". "
            
            md.append(f"{i}. {authors_str}{article['title']}. ")
            md.append(f"*{article['journal']}*. {article['year']}. ")
            md.append(f"PMID: {article['pmid']}. {article['url']}\n")
    else:
        md.append("No citations available.\n")
    
    # Open Questions
    if assumptions.get("open_questions"):
        md.append("\n## Open Questions\n")
        for question in assumptions["open_questions"]:
            md.append(f"- {question}\n")
    
    # Footer
    md.append(f"\n---\n*Generated: {_get_current_date()}*\n")
    
    return "".join(md)


def _append_assumption_field(md: list, label: str, field_data: dict, unit: str):
    """Helper to append assumption field with range and support level."""
    range_min = field_data.get("range_min", 0)
    range_max = field_data.get("range_max", 0)
    support_level = field_data.get("support_level", "unknown")
    explanation = field_data.get("explanation", "")
    evidence_pmids = field_data.get("evidence_pmids", [])
    evidence_quotes = field_data.get("evidence_quotes", [])
    
    md.append(f"\n**{label}:** {range_min}–{range_max} {unit}\n")
    
    if support_level == "evidence_supported":
        md.append(f"- *Support Level:* Evidence-supported\n")
        if evidence_pmids:
            md.append(f"- *Evidence PMIDs:* {', '.join(evidence_pmids)}\n")
        if evidence_quotes:
            md.append(f"- *Evidence Quotes:*\n")
            for quote in evidence_quotes:
                md.append(f"  - \"{quote}\"\n")
    elif support_level == "heuristic_ballpark":
        md.append(f"- *Support Level:* Heuristic/Ballpark\n")
    
    if explanation:
        md.append(f"- *Explanation:* {explanation}\n")


def _get_current_date() -> str:
    """Get current date for report footer."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")
