"""Auto-suggest PubMed query keywords from R&D idea input."""

import re
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from impactpilot.services.llm_provider import LLMProvider

# Built-in stopwords to filter out
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "will", "with", "we", "our", "this", "these", "those"
}


def suggest_pubmed_query(title: str, description: str, provider: Optional["LLMProvider"] = None) -> str:
    """
    Generate a PubMed query string from idea title and description.

    If an LLM provider is supplied it is used to generate a properly structured
    PubMed boolean query.  Falls back to pure-Python keyword extraction when no
    provider is available or when the LLM call fails.

    Args:
        title: The idea title
        description: The idea description
        provider: Optional LLM provider to improve query quality

    Returns:
        A query string suitable for PubMed search (never empty)
    """
    if provider is not None:
        try:
            prompt = (
                "You are a biomedical literature search expert. "
                "Given an R&D idea, generate a concise PubMed boolean search query "
                "using AND/OR operators and MeSH-style terms. "
                "Return ONLY the query string, no explanation, no quotes around the whole string.\n\n"
                f"Idea title: {title}\n"
                f"Idea description: {description}\n\n"
                "PubMed query:"
            )
            result = provider.generate(prompt).strip()
            # Basic sanity check: must be non-empty and not an error message
            if result and not result.lower().startswith("error"):
                return result
        except Exception:
            pass  # Fall through to keyword extraction

    return _keyword_fallback(title, description)


def _keyword_fallback(title: str, description: str) -> str:
    """Pure-Python keyword extraction fallback."""
    # Tokenize title and description separately
    title_tokens = re.findall(r'\b[\w-]+\b', title.lower())
    desc_tokens = re.findall(r'\b[\w-]+\b', description.lower())
    
    # Filter stopwords and keep unique tokens
    def filter_tokens(tokens):
        unique = []
        seen = set()
        for token in tokens:
            if token not in STOPWORDS and token not in seen and len(token) > 1:
                unique.append(token)
                seen.add(token)
        return unique
    
    title_keywords = filter_tokens(title_tokens)
    desc_keywords = filter_tokens(desc_tokens)
    
    # Prioritize title, then add description keywords (max 5-6 total)
    final_keywords = []
    for kw in title_keywords[:4]:  # Take up to 4 from title
        final_keywords.append(kw)
    
    # Add description keywords to fill up to 5-6 total
    for kw in desc_keywords:
        if kw not in final_keywords:
            final_keywords.append(kw)
            if len(final_keywords) >= 6:
                break
    
    # Fallback: if no tokens found, use title as-is
    if not final_keywords:
        return title.strip() if title.strip() else "research"
    
    # Join with AND for explicit boolean logic
    return " AND ".join(final_keywords)
