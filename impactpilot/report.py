"""Generate Impact Brief markdown report."""

from impactpilot.disclaimer import DISCLAIMER_TEXT


def build_brief_markdown(
    idea: dict,
    selected_articles: list[dict],
    extracted_numeric_evidence: list[dict],
    assumptions: dict,
    tco_out: dict,
    prod_out: dict,
    horizon_years: int
) -> str:
    """
    Build a structured Impact Brief in Markdown format.
    
    CRITICAL RULES:
    - Never fabricate numbers
    - Only show numeric values if they exist in assumptions with provenance
    - Clearly state when values cannot be computed
    
    Args:
        idea: R&D idea dict with title, description, etc.
        selected_articles: List of selected PubMed articles
        extracted_numeric_evidence: List of extracted numeric evidence
        assumptions: Evidence-derived assumptions dict
        tco_out: Output from compute_tco()
        prod_out: Output from compute_productivity()
        horizon_years: Planning horizon in years
        
    Returns:
        Markdown string for the Impact Brief
    """
    lines = []
    
    # Title and disclaimer
    title = idea.get("title", "R&D Impact Brief")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"> {DISCLAIMER_TEXT}")
    lines.append("")
    
    # Summary (4-6 bullets from idea only)
    lines.append("## Summary")
    lines.append("")
    description = idea.get("description", "")
    idea_type = idea.get("idea_type", "")
    rd_stage = idea.get("rd_stage", "")
    
    lines.append(f"- **Idea**: {description[:200] if description else 'No description provided'}")
    if idea_type:
        lines.append(f"- **Type**: {idea_type}")
    if rd_stage:
        lines.append(f"- **Stage**: {rd_stage}")
    lines.append(f"- **Evidence base**: {len(selected_articles)} selected PubMed articles")
    lines.append(f"- **Numeric evidence extracted**: {len(extracted_numeric_evidence)} data points")
    lines.append(f"- **Analysis horizon**: {horizon_years} years")
    lines.append("")
    
    # Evidence used (selected papers)
    lines.append("## Evidence used (selected PubMed papers)")
    lines.append("")
    if selected_articles:
        for article in selected_articles:
            pmid = article.get("pmid", "Unknown")
            title_text = article.get("title", "No title")
            year = article.get("year", "N/A")
            journal = article.get("journal", "Unknown")
            url = article.get("url", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            lines.append(f"- PMID [{pmid}]({url}): {title_text} ({year}, {journal})")
    else:
        lines.append("- No articles selected")
    lines.append("")
    
    # Evidence-derived assumptions
    lines.append("## Evidence-derived assumptions (must be traceable)")
    lines.append("")
    lines.append("All numeric assumptions below are derived ONLY from selected PubMed abstracts.")
    lines.append("")
    
    # Productivity assumptions
    lines.append("### Productivity Impact")
    lines.append("")
    
    time_saved = assumptions.get("productivity", {}).get("time_saved_hours_per_month", {})
    _render_assumption_field(lines, "Time saved (hours/month)", time_saved)
    
    cost_avoided = assumptions.get("productivity", {}).get("cost_avoided_per_year", {})
    _render_assumption_field(lines, "Cost avoided ($/year)", cost_avoided)
    
    # TCO assumptions
    lines.append("### Total Cost of Ownership")
    lines.append("")
    
    impl_cost = assumptions.get("tco", {}).get("implementation_cost", {})
    _render_assumption_field(lines, "Implementation cost", impl_cost)
    
    annual_cost = assumptions.get("tco", {}).get("annual_operating_cost", {})
    _render_assumption_field(lines, "Annual operating cost", annual_cost)
    
    lines.append("")
    
    # Computed TCO
    lines.append(f"## Computed TCO (horizon = {horizon_years} years)")
    lines.append("")
    
    if tco_out.get("horizon_cost") is not None:
        horizon_cost = tco_out["horizon_cost"]
        annual_run_cost = tco_out["annual_run_cost"]
        breakdown = tco_out["breakdown"]
        
        lines.append(f"**Total {horizon_years}-year TCO**: ${horizon_cost:,.2f}")
        lines.append(f"**Annual run cost**: ${annual_run_cost:,.2f}")
        lines.append("")
        lines.append("**Breakdown:**")
        lines.append("")
        lines.append(f"- Build cost (one-time): ${breakdown.get('build_cost_once', 0):,.2f}")
        lines.append(f"- Training cost (one-time): ${breakdown.get('training_cost_once', 0):,.2f}")
        lines.append(f"- Annual labor (run): ${breakdown.get('labor_run_cost_per_year', 0):,.2f}")
        lines.append(f"- Annual license: ${breakdown.get('license_cost_per_year', 0):,.2f}")
        lines.append(f"- Annual compute: ${breakdown.get('compute_cost_per_year', 0):,.2f}")
        lines.append(f"- Annual downtime: ${breakdown.get('downtime_cost_per_year', 0):,.2f}")
    else:
        explanation = tco_out.get("explanation", "Not computable from selected evidence-derived inputs; validate or provide inputs.")
        lines.append(f"**{explanation}**")
    
    lines.append("")
    
    # Computed productivity
    lines.append(f"## Computed R&D pipeline productivity impact (horizon = {horizon_years} years)")
    lines.append("")
    
    if prod_out.get("horizon_productivity_value") is not None:
        horizon_prod = prod_out["horizon_productivity_value"]
        annual_prod = prod_out["annual_productivity_value"]
        breakdown = prod_out["breakdown"]
        
        lines.append(f"**Total {horizon_years}-year productivity value**: ${horizon_prod:,.2f}")
        lines.append(f"**Annual productivity value**: ${annual_prod:,.2f}")
        lines.append("")
        lines.append("**Breakdown:**")
        lines.append("")
        lines.append(f"- Annual hours saved: {breakdown.get('annual_hours_saved', 0):,.1f} hours")
        lines.append(f"- Annual time value: ${breakdown.get('annual_time_value', 0):,.2f}")
        lines.append(f"- Annual cost avoided: ${breakdown.get('cost_avoided_per_year', 0):,.2f}")
    else:
        explanation = prod_out.get("explanation", "Not computable from selected evidence-derived inputs; validate or provide inputs.")
        lines.append(f"**{explanation}**")
    
    lines.append("")
    
    # Pipeline levers (directional)
    lines.append("### Pipeline levers (directional)")
    lines.append("")
    throughput = prod_out.get("throughput_delta_per_year")
    success_prob = prod_out.get("success_prob_delta")
    
    if throughput is not None or success_prob is not None:
        if throughput is not None:
            lines.append(f"- **Throughput delta**: {throughput} per year (directional, requires validation)")
        if success_prob is not None:
            lines.append(f"- **Success probability delta**: {success_prob} (directional, requires validation)")
    else:
        lines.append("- No directional pipeline levers derived from evidence")
    
    lines.append("")
    
    # Evidence mapping
    lines.append("## Evidence mapping (claims → PMIDs)")
    lines.append("")
    evidence_map = assumptions.get("evidence_map", {})
    if evidence_map:
        for claim, pmids in evidence_map.items():
            pmid_str = ", ".join(str(p) for p in pmids)
            lines.append(f"- {claim} — PMIDs: {pmid_str}")
    else:
        # Build simple evidence map from assumptions
        lines.append("### Assumptions backed by evidence:")
        lines.append("")
        for category_name, category in assumptions.items():
            if category_name in ["evidence_map", "open_questions"]:
                continue
            for field_name, field_data in category.items():
                if isinstance(field_data, dict) and field_data.get("value") is not None:
                    pmids = field_data.get("evidence_pmids", [])
                    if pmids:
                        pmid_str = ", ".join(str(p) for p in pmids)
                        lines.append(f"- {field_name}: PMIDs {pmid_str}")
    
    lines.append("")
    
    # Citations
    lines.append("## Citations")
    lines.append("")
    if selected_articles:
        for article in selected_articles:
            pmid = article.get("pmid", "Unknown")
            title_text = article.get("title", "No title")
            authors = article.get("authors", "Unknown authors")
            year = article.get("year", "N/A")
            journal = article.get("journal", "Unknown journal")
            url = article.get("url", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            
            lines.append(f"{authors}. {title_text}. *{journal}*. {year}. PMID: [{pmid}]({url})")
            lines.append("")
    else:
        lines.append("No citations available.")
        lines.append("")
    
    # Open questions
    lines.append("## Open questions / what to validate")
    lines.append("")
    open_questions = assumptions.get("open_questions", [])
    if open_questions:
        for q in open_questions:
            lines.append(f"- {q}")
    else:
        # Generic validation prompts
        lines.append("- Validate all numeric assumptions against organizational context")
        lines.append("- Confirm hourly rates and cost parameters match actual values")
        lines.append("- Review evidence relevance to your specific R&D domain")
        lines.append("- Consider regulatory, compliance, and organizational constraints")
        lines.append("- Verify that extracted evidence interpretations align with study contexts")
    
    lines.append("")
    
    return "\n".join(lines)


def _render_assumption_field(lines: list, field_label: str, field_data: dict):
    """Helper to render an assumption field with evidence or 'not found' message."""
    if isinstance(field_data, dict):
        value = field_data.get("value")
        if value is not None:
            # Evidence-derived value
            lines.append(f"**[Evidence-derived]** {field_label}: {value}")
            
            # Show sources
            pmids = field_data.get("evidence_pmids", [])
            raws = field_data.get("evidence_raw", [])
            for i, pmid in enumerate(pmids):
                raw = raws[i] if i < len(raws) else ""
                lines.append(f"  - Source: PMID [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/) — '{raw}'")
            
            # Show explanation
            explanation = field_data.get("explanation", "")
            if explanation:
                lines.append(f"  - {explanation[:150]}...")
        else:
            # No evidence found
            lines.append(f"**[Not found in selected evidence]** {field_label}: requires validation / input")
    else:
        lines.append(f"**[Not found in selected evidence]** {field_label}: requires validation / input")
    
    lines.append("")
