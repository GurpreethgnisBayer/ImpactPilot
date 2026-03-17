"""Auto-suggest PubMed query keywords from R&D idea input."""

import re

# Built-in stopwords to filter out
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "will", "with", "we", "our", "this", "these", "those"
}


def suggest_pubmed_query(title: str, description: str) -> str:
    """
    Generate a PubMed query string from idea title and description.
    
    Improved approach for better PubMed results:
    1. Prioritize title words over description words
    2. Keep only 5-6 key terms (broader results)
    3. Join with AND for explicit boolean logic
    
    Args:
        title: The idea title
        description: The idea description
        
    Returns:
        A query string suitable for PubMed search (never empty)
    """
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
