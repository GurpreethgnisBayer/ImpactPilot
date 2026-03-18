"""Extract numeric evidence from PubMed article abstracts."""

import re
from typing import Optional


def extract_numeric_evidence(article: dict) -> list[dict]:
    """
    Extract numeric mentions from an article abstract.
    
    Args:
        article: Dictionary with 'pmid', 'abstract', etc.
    
    Returns:
        List of evidence entries with pmid, raw text, type, value, unit, and context
    """
    entries = []
    abstract = article.get("abstract", "")
    pmid = article.get("pmid", "unknown")
    
    if not abstract:
        return entries
    
    # Pattern for percentages: "25%", "25 %", "25 percent"
    percent_pattern = r'(\d+(?:\.\d+)?)\s*(%|percent)'
    for match in re.finditer(percent_pattern, abstract, re.IGNORECASE):
        value_str = match.group(1)
        context = _extract_context(abstract, match.start(), match.end())
        
        entries.append({
            "pmid": pmid,
            "raw": match.group(0),
            "type": "percentage",
            "value": float(value_str),
            "unit": "%",
            "context": context,
        })
    
    # Pattern for time durations: "2 hours", "3.5 days", "10 minutes"
    time_pattern = r'(\d+(?:\.\d+)?)\s*(hours?|days?|weeks?|months?|years?|minutes?|mins?)'
    for match in re.finditer(time_pattern, abstract, re.IGNORECASE):
        value_str = match.group(1)
        unit = match.group(2).lower()
        context = _extract_context(abstract, match.start(), match.end())
        
        entries.append({
            "pmid": pmid,
            "raw": match.group(0),
            "type": "time_duration",
            "value": float(value_str),
            "unit": unit,
            "context": context,
        })
    
    # Pattern for counts/numbers with units: "100 patients", "50 samples"
    count_pattern = r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(patients?|samples?|cases?|trials?|studies?)'
    for match in re.finditer(count_pattern, abstract, re.IGNORECASE):
        value_str = match.group(1).replace(",", "")
        unit = match.group(2).lower()
        context = _extract_context(abstract, match.start(), match.end())
        
        entries.append({
            "pmid": pmid,
            "raw": match.group(0),
            "type": "count",
            "value": float(value_str),
            "unit": unit,
            "context": context,
        })
    
    return entries


def _extract_context(text: str, start: int, end: int, window: int = 80) -> str:
    """
    Extract surrounding context for a matched numeric value.
    
    Args:
        text: Full text
        start: Start position of match
        end: End position of match
        window: Characters to include before and after
    
    Returns:
        Context string with "..." markers if truncated
    """
    context_start = max(0, start - window)
    context_end = min(len(text), end + window)
    
    context = text[context_start:context_end]
    
    # Add ellipsis if truncated
    if context_start > 0:
        context = "..." + context
    if context_end < len(text):
        context = context + "..."
    
    return context.strip()
