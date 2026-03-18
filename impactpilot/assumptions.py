"""Assumption normalization and validation."""


def normalize_and_validate(inference: dict, selected_pmids: set) -> dict:
    """
    Validate and normalize inference results.
    
    Args:
        inference: The inference dict from LLM
        selected_pmids: Set of PMIDs that were provided as evidence
    
    Returns:
        Normalized inference dict
    
    Raises:
        ValueError: If validation fails
    """
    errors = []
    
    # Check top-level structure
    if "productivity" not in inference:
        errors.append("Missing 'productivity' section")
    if "tco" not in inference:
        errors.append("Missing 'tco' section")
    
    if errors:
        raise ValueError(f"Validation errors: {'; '.join(errors)}")
    
    # Validate each numeric field
    for section_name in ["productivity", "tco"]:
        section = inference.get(section_name, {})
        
        for field_name, field_data in section.items():
            if not isinstance(field_data, dict):
                continue
            
            support_level = field_data.get("support_level", "")
            evidence_pmids = field_data.get("evidence_pmids", [])
            evidence_quotes = field_data.get("evidence_quotes", [])
            explanation = field_data.get("explanation", "")
            
            # Validate evidence_supported fields
            if support_level == "evidence_supported":
                # Must have at least one PMID
                if not evidence_pmids:
                    errors.append(
                        f"{section_name}.{field_name}: evidence_supported requires at least one PMID"
                    )
                
                # Must have at least one quote
                if not evidence_quotes:
                    errors.append(
                        f"{section_name}.{field_name}: evidence_supported requires at least one quote"
                    )
                
                # PMIDs must be subset of selected
                for pmid in evidence_pmids:
                    if pmid not in selected_pmids:
                        errors.append(
                            f"{section_name}.{field_name}: PMID {pmid} not in selected articles"
                        )
            
            # Validate heuristic_ballpark fields
            elif support_level == "heuristic_ballpark":
                # Must have empty PMIDs
                if evidence_pmids:
                    errors.append(
                        f"{section_name}.{field_name}: heuristic_ballpark must have empty evidence_pmids"
                    )
                
                # Must have empty quotes
                if evidence_quotes:
                    errors.append(
                        f"{section_name}.{field_name}: heuristic_ballpark must have empty evidence_quotes"
                    )
                
                # Explanation must start with required prefix
                required_prefix = "No supporting evidence found in selected abstracts; directional estimate — user must verify."
                if not explanation.startswith(required_prefix):
                    errors.append(
                        f"{section_name}.{field_name}: heuristic_ballpark explanation must start with: '{required_prefix}'"
                    )
    
    if errors:
        raise ValueError(f"Validation errors: {'; '.join(errors)}")
    
    return inference
