"""Deterministic PubMed query suggestions from idea title and description."""

from __future__ import annotations

import re

_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "but",
        "by",
        "can",
        "for",
        "from",
        "in",
        "into",
        "is",
        "it",
        "its",
        "may",
        "not",
        "of",
        "on",
        "or",
        "our",
        "that",
        "the",
        "these",
        "this",
        "those",
        "to",
        "using",
        "via",
        "was",
        "we",
        "were",
        "will",
        "with",
    }
)


def suggest_pubmed_query(title: str, description: str) -> str:
    """
    Tokenize title + description, lowercase, drop stopwords, keep first 10 unique
    tokens in order, join with spaces. Never returns empty (fallback: stripped title).
    """
    combined = f"{title} {description}".lower()
    raw_tokens = re.findall(r"[a-z0-9]+", combined.replace("'", ""))
    seen: set[str] = set()
    out: list[str] = []
    for tok in raw_tokens:
        if tok in _STOPWORDS:
            continue
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
        if len(out) >= 10:
            break
    result = " ".join(out).strip()
    if result:
        return result
    fallback = title.strip()
    if fallback:
        return fallback
    return "research"
