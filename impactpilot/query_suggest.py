"""LLM-powered PubMed MeSH query suggestion from idea title and description."""

import re
from typing import Optional


# Small built-in stopword list for fallback
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "will", "with", "this", "these", "those", "their",
    "can", "or", "but", "we", "our", "they", "them", "us", "you",
}


def suggest_pubmed_query_with_llm(
    title: str,
    description: str,
    llm_provider
) -> str:
    """
    Generate a PubMed MeSH query using LLM.
    
    Args:
        title: The idea title
        description: The idea description
        llm_provider: Configured LLM provider instance
    
    Returns:
        A MeSH-formatted PubMed query string
    """
    prompt = f"""Generate a PubMed search query using MeSH (Medical Subject Headings) terms for the following R&D idea.

Idea Title: {title}
Description: {description}

Instructions:
1. Identify the most relevant MeSH terms for this research topic
2. Use proper PubMed search syntax with MeSH terms in brackets: [MeSH]
3. Combine terms with AND/OR operators as appropriate
4. Keep the query focused and relevant (3-5 main MeSH terms)
5. Return ONLY the query string, no explanation

Example format: "Machine Learning"[MeSH] AND "Drug Discovery"[MeSH] AND "Pharmaceutical Preparations"[MeSH]

Generate the PubMed MeSH query now:"""
    
    try:
        response = llm_provider.generate(prompt)
        # Clean up the response
        query = response.strip()
        
        # Remove any markdown formatting
        if query.startswith("```"):
            lines = query.split("\n")
            query = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            query = query.strip()
        
        # If query is empty or too short, fall back
        if not query or len(query) < 10:
            return _fallback_query(title, description)
        
        return query
    
    except Exception as e:
        # Fall back to deterministic approach if LLM fails
        print(f"LLM query generation failed: {e}, using fallback")
        return _fallback_query(title, description)


def suggest_pubmed_query(title: str, description: str) -> str:
    """
    Generate a PubMed query from title and description using deterministic approach.
    This is the fallback method when LLM is not available.
    
    Args:
        title: The idea title
        description: The idea description
    
    Returns:
        A query string with up to 10 unique tokens, space-separated
    """
    return _fallback_query(title, description)


def _fallback_query(title: str, description: str) -> str:
    """Deterministic fallback query generation."""
    # Combine title and description
    combined_text = f"{title} {description}"
    
    # Tokenize: split by non-alphanumeric characters
    tokens = re.findall(r'\b[a-zA-Z0-9]+\b', combined_text)
    
    # Lowercase and filter stopwords
    unique_tokens = []
    seen = set()
    
    for token in tokens:
        token_lower = token.lower()
        # Keep if not stopword, not already seen, and not a single character
        if token_lower not in STOPWORDS and token_lower not in seen and len(token_lower) > 1:
            unique_tokens.append(token_lower)
            seen.add(token_lower)
        
        # Stop after collecting 10 unique tokens
        if len(unique_tokens) >= 10:
            break
    
    # Fallback: if no tokens left, use stripped title
    if not unique_tokens:
        return title.strip() if title.strip() else "research"
    
    return " ".join(unique_tokens)

