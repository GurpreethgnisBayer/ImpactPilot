"""LLM inference engine for generating directional estimates."""

import json
from impactpilot.services.llm_health import validate_llm_settings
from impactpilot.services.llm_provider import build_provider
from impactpilot.evidence_numbers import extract_numeric_evidence


def run_inference_pipeline(
    idea: dict,
    selected_articles: list[dict],
    llm_settings: dict
) -> dict:
    """
    Run the complete inference pipeline to generate directional estimates.
    
    Args:
        idea: Dictionary with title, description, idea_type, rd_stage
        selected_articles: List of selected PubMed articles
        llm_settings: LLM provider configuration
    
    Returns:
        Dictionary with 'inference' (parsed LLM output) and 'numeric_evidence' (extracted numbers)
    
    Raises:
        ValueError: If validation fails or LLM output cannot be parsed
    """
    # Step a: Validate LLM settings
    validation_errors = validate_llm_settings(llm_settings)
    if validation_errors:
        raise ValueError(f"Invalid LLM settings: {'; '.join(validation_errors)}")
    
    # Step b: Build provider
    provider = build_provider(llm_settings)
    
    # Step c: Extract numeric evidence
    numeric_evidence = []
    for article in selected_articles:
        numeric_evidence.extend(extract_numeric_evidence(article))
    
    # Step d: Build prompt
    prompt = _build_inference_prompt(idea, selected_articles, numeric_evidence)
    
    # Step e: Call LLM (exactly once)
    llm_response = provider.generate(prompt)
    
    # Step f: Parse JSON
    try:
        # Try to extract JSON from response (handle markdown code blocks)
        json_str = llm_response.strip()
        
        # Remove markdown code blocks if present
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            json_str = "\n".join(lines)
        
        parsed_json = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
    
    # Step g: Return result
    return {
        "inference": parsed_json,
        "numeric_evidence": numeric_evidence,
    }


def _build_inference_prompt(
    idea: dict,
    selected_articles: list[dict],
    numeric_evidence: list[dict]
) -> str:
    """Build the prompt for the LLM."""
    
    # Build evidence context
    evidence_context = ""
    if selected_articles:
        evidence_context = "SELECTED SCIENTIFIC EVIDENCE:\n\n"
        for i, article in enumerate(selected_articles, 1):
            evidence_context += f"[PMID: {article['pmid']}]\n"
            evidence_context += f"Title: {article['title']}\n"
            if article.get('abstract'):
                evidence_context += f"Abstract: {article['abstract'][:500]}...\n"
            evidence_context += "\n"
    
    # Build numeric evidence context
    numeric_context = ""
    if numeric_evidence:
        numeric_context = "EXTRACTED NUMERIC EVIDENCE:\n\n"
        for entry in numeric_evidence[:20]:  # Limit to first 20
            numeric_context += f"- From PMID {entry['pmid']}: {entry['raw']} (context: {entry['context'][:100]}...)\n"
        numeric_context += "\n"
    
    prompt = f"""You are an expert analyst generating directional impact estimates for R&D ideas.

IDEA TO ANALYZE:
Title: {idea.get('title', 'N/A')}
Description: {idea.get('description', 'N/A')}
Type: {idea.get('idea_type', 'N/A')}
Stage: {idea.get('rd_stage', 'N/A')}

{evidence_context}

{numeric_context}

TASK:
Generate directional estimates for productivity gains and TCO (Total Cost of Ownership).

CRITICAL RULES:
1. You MUST always provide numeric ranges (range_min and range_max) for EVERY field. Never return null or omit values.
2. If a value is supported by the selected papers above, set support_level="evidence_supported" AND include:
   - At least one PMID in evidence_pmids
   - At least one verbatim quote snippet from that abstract in evidence_quotes
3. If supporting evidence quotes are NOT found in the selected abstracts, still provide a ballpark range but:
   - Set support_level="heuristic_ballpark"
   - Set evidence_pmids=[]
   - Set evidence_quotes=[]
   - Start explanation with EXACTLY: "No supporting evidence found in selected abstracts; directional estimate — user must verify."
4. NEVER mark evidence_supported without at least one evidence_quote.

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown, no explanations) with this exact schema:

{{
  "productivity": {{
    "time_saved_hours_per_month": {{
      "range_min": <number>,
      "range_max": <number>,
      "support_level": "evidence_supported" or "heuristic_ballpark",
      "evidence_pmids": ["PMID1", "PMID2"] or [],
      "evidence_quotes": ["exact quote from abstract"] or [],
      "explanation": "..."
    }},
    "cost_avoided_per_year": {{
      "range_min": <number>,
      "range_max": <number>,
      "support_level": "evidence_supported" or "heuristic_ballpark",
      "evidence_pmids": ["PMID1"] or [],
      "evidence_quotes": ["exact quote"] or [],
      "explanation": "..."
    }}
  }},
  "tco": {{
    "build_person_days": {{
      "range_min": <number>,
      "range_max": <number>,
      "support_level": "evidence_supported" or "heuristic_ballpark",
      "evidence_pmids": [] or ["PMID1"],
      "evidence_quotes": [] or ["exact quote"],
      "explanation": "..."
    }},
    "run_person_days_per_year": {{
      "range_min": <number>,
      "range_max": <number>,
      "support_level": "evidence_supported" or "heuristic_ballpark",
      "evidence_pmids": [] or ["PMID1"],
      "evidence_quotes": [] or ["exact quote"],
      "explanation": "..."
    }}
  }},
  "overall_confidence": "low" or "medium" or "high",
  "assumptions": ["assumption 1", "assumption 2"],
  "open_questions": ["question 1", "question 2"]
}}

Generate the JSON now:"""
    
    return prompt
