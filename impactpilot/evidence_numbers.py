"""Extract numeric evidence from PubMed abstracts."""

import re
from typing import Optional


def extract_numeric_evidence(article: dict) -> list[dict]:
    """
    Extract numeric mentions from article abstract with context.
    
    Args:
        article: Article dict with pmid and abstract
        
    Returns:
        List of numeric evidence entries with:
        - pmid: PubMed ID
        - raw: Raw text snippet containing the number
        - type: Evidence type (percentage, time, count)
        - value: Numeric value
        - unit: Unit of measurement
        - context: Surrounding context text
    """
    pmid = article.get("pmid", "Unknown")
    abstract = article.get("abstract", "")
    
    if not abstract or abstract == "No abstract available":
        return []
    
    evidence = []
    
    # Extract percentages (e.g., 25%, 50 percent)
    percentage_pattern = r'(\d+(?:\.\d+)?)\s*(?:%|percent)'
    for match in re.finditer(percentage_pattern, abstract, re.IGNORECASE):
        value = float(match.group(1))
        # Get context window (50 chars before and after)
        start = max(0, match.start() - 50)
        end = min(len(abstract), match.end() + 50)
        context = abstract[start:end].strip()
        
        evidence.append({
            "pmid": pmid,
            "raw": match.group(0),
            "type": "percentage",
            "value": value,
            "unit": "%",
            "context": context
        })
    
    # Extract time durations (e.g., 2 hours, 10 min, 6 weeks, 3 days, 1 month, 5 years)
    time_pattern = r'(\d+(?:\.\d+)?)\s*(hours?|hrs?|minutes?|mins?|days?|weeks?|months?|years?)'
    for match in re.finditer(time_pattern, abstract, re.IGNORECASE):
        value = float(match.group(1))
        unit = match.group(2).lower()
        
        # Normalize units
        if unit in ['hr', 'hrs', 'hour', 'hours']:
            unit = 'hours'
        elif unit in ['min', 'mins', 'minute', 'minutes']:
            unit = 'minutes'
        elif unit in ['day', 'days']:
            unit = 'days'
        elif unit in ['week', 'weeks']:
            unit = 'weeks'
        elif unit in ['month', 'months']:
            unit = 'months'
        elif unit in ['year', 'years']:
            unit = 'years'
        
        # Get context window
        start = max(0, match.start() - 50)
        end = min(len(abstract), match.end() + 50)
        context = abstract[start:end].strip()
        
        evidence.append({
            "pmid": pmid,
            "raw": match.group(0),
            "type": "time",
            "value": value,
            "unit": unit,
            "context": context
        })
    
    # Extract counts with common nouns (e.g., 30 patients, 100 samples)
    count_pattern = r'(\d+)\s*(patients?|subjects?|participants?|samples?|cases?|studies?)'
    for match in re.finditer(count_pattern, abstract, re.IGNORECASE):
        value = int(match.group(1))
        unit = match.group(2).lower()
        
        # Get context window
        start = max(0, match.start() - 50)
        end = min(len(abstract), match.end() + 50)
        context = abstract[start:end].strip()
        
        evidence.append({
            "pmid": pmid,
            "raw": match.group(0),
            "type": "count",
            "value": value,
            "unit": unit,
            "context": context
        })
    
    return evidence


def extract_all_numeric_evidence(selected_articles: list[dict]) -> list[dict]:
    """
    Extract numeric evidence from all selected articles.
    
    Args:
        selected_articles: List of article dictionaries
        
    Returns:
        Combined list of all numeric evidence
    """
    all_evidence = []
    for article in selected_articles:
        evidence = extract_numeric_evidence(article)
        all_evidence.extend(evidence)
    return all_evidence
