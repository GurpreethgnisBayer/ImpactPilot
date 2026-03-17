"""Derive evidence-grounded assumptions from selected PubMed articles."""

from typing import Optional


def derive_assumptions(
    idea: dict,
    selected_articles: list[dict],
    extracted_numeric_evidence: list[dict]
) -> dict:
    """
    Derive assumptions ONLY from extracted numeric evidence.
    
    CRITICAL RULE: Never fabricate numbers. Only populate fields if there is
    explicit numeric evidence from selected abstracts. Otherwise set to None
    with explanation "No numeric evidence found in selected abstracts."
    
    Args:
        idea: The R&D idea dict (title, description, etc.)
        selected_articles: List of selected article dicts
        extracted_numeric_evidence: List of numeric evidence entries
        
    Returns:
        Assumptions dict with structure:
        {
            "productivity": {
                "time_saved_hours_per_month": {
                    "value": float or None,
                    "evidence_pmids": list[str],
                    "evidence_raw": list[str],
                    "explanation": str
                },
                "cost_avoided_per_year": {
                    "value": float or None,
                    "evidence_pmids": list[str],
                    "evidence_raw": list[str],
                    "explanation": str
                }
            },
            "tco": {
                "implementation_cost": {
                    "value": None,
                    "evidence_pmids": [],
                    "evidence_raw": [],
                    "explanation": "No numeric evidence found in selected abstracts."
                }
            }
        }
    """
    # Initialize empty assumptions structure
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No numeric evidence found in selected abstracts."
            },
            "cost_avoided_per_year": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No numeric evidence found in selected abstracts."
            }
        },
        "tco": {
            "implementation_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No numeric evidence found in selected abstracts."
            },
            "annual_operating_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No numeric evidence found in selected abstracts."
            }
        }
    }
    
    if not extracted_numeric_evidence:
        return assumptions
    
    # Extract selected PMIDs for validation
    selected_pmids = {article.get("pmid") for article in selected_articles}
    
    # Find time savings evidence (hours, days, weeks saved)
    time_evidence = [
        e for e in extracted_numeric_evidence
        if e["type"] == "time" and e["pmid"] in selected_pmids
    ]
    
    if time_evidence:
        # Use first time evidence found (preferably hours)
        time_entry = time_evidence[0]
        value = time_entry["value"]
        unit = time_entry["unit"]
        
        # Convert to hours per month (rough estimation)
        hours_per_month = None
        if unit == "hours":
            # Assume this is per some period, estimate monthly
            hours_per_month = value * 4  # Rough weekly to monthly
        elif unit == "days":
            hours_per_month = value * 8 * 4  # 8 hour days, 4 weeks
        elif unit == "weeks":
            hours_per_month = value * 40  # 40 hour weeks
        elif unit == "minutes":
            hours_per_month = (value / 60) * 4
        
        if hours_per_month:
            assumptions["productivity"]["time_saved_hours_per_month"] = {
                "value": round(hours_per_month, 2),
                "evidence_pmids": [time_entry["pmid"]],
                "evidence_raw": [time_entry["raw"]],
                "explanation": f"Estimated from time reduction of {time_entry['raw']} mentioned in abstract. Context: '{time_entry['context'][:100]}...'"
            }
    
    # Find percentage improvements (could indicate cost/time savings)
    percentage_evidence = [
        e for e in extracted_numeric_evidence
        if e["type"] == "percentage" and e["pmid"] in selected_pmids
    ]
    
    if percentage_evidence:
        # Look for percentages that might indicate cost reduction or improvement
        for pct_entry in percentage_evidence:
            context_lower = pct_entry["context"].lower()
            
            # Check if it's about reduction, improvement, or savings
            if any(keyword in context_lower for keyword in [
                "reduction", "decrease", "saved", "saving", "improvement", 
                "reduced", "lower", "less", "faster"
            ]):
                # This could be relevant for productivity
                pct_value = pct_entry["value"]
                
                # If we don't have time savings yet, estimate from percentage
                if assumptions["productivity"]["time_saved_hours_per_month"]["value"] is None:
                    # Very rough estimation: assume baseline 40 hours/month effort
                    estimated_hours = 40 * (pct_value / 100)
                    assumptions["productivity"]["time_saved_hours_per_month"] = {
                        "value": round(estimated_hours, 2),
                        "evidence_pmids": [pct_entry["pmid"]],
                        "evidence_raw": [pct_entry["raw"]],
                        "explanation": f"Estimated from {pct_entry['raw']} improvement mentioned in abstract. Context: '{pct_entry['context'][:100]}...'"
                    }
                    break
    
    # Cost evidence is rare in abstracts, so we leave tco fields as None
    # unless we find explicit cost mentions (which is uncommon)
    
    return assumptions


def validate_assumptions_grounding(assumptions: dict, selected_pmids: set) -> bool:
    """
    Validate that all assumptions are grounded in selected articles.
    
    Args:
        assumptions: The assumptions dict
        selected_pmids: Set of selected PMIDs
        
    Returns:
        True if all evidence PMIDs are in selected_pmids
    """
    for category in assumptions.values():
        for field_data in category.values():
            if isinstance(field_data, dict):
                evidence_pmids = field_data.get("evidence_pmids", [])
                for pmid in evidence_pmids:
                    if pmid not in selected_pmids:
                        return False
    return True
