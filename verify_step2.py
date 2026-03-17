"""Manual verification script for Step 2 features."""

import sys
sys.path.insert(0, '.')

from impactpilot.query_suggest import suggest_pubmed_query
from impactpilot.services.pubmed_eutils import build_term, search_pubmed

print("=" * 60)
print("ImpactPilot Step 2 - Manual Verification")
print("=" * 60)

# Test 1: Query suggestion
print("\n1. Testing Query Suggestion")
print("-" * 60)
title = "AI-Powered Drug Discovery Platform"
description = "Develop machine learning models to predict drug-target interactions and accelerate pharmaceutical R&D"
suggested_query = suggest_pubmed_query(title, description)
print(f"Title: {title}")
print(f"Description: {description}")
print(f"Suggested Query: {suggested_query}")

# Test 2: Term building
print("\n2. Testing Term Building")
print("-" * 60)
term = build_term(
    base_query="machine learning drug discovery",
    has_abstract=True,
    publication_types=["Review"]
)
print(f"Built Term: {term}")

# Test 3: PubMed search (real API call)
print("\n3. Testing Real PubMed Search")
print("-" * 60)
print("Searching PubMed for 'machine learning drug discovery'...")
try:
    results = search_pubmed(
        query="machine learning drug discovery",
        date_preset="2years",
        max_results=3,
        sort="relevance"
    )
    print(f"Found {len(results)} articles")
    if results:
        print("\nFirst result:")
        article = results[0]
        print(f"  PMID: {article['pmid']}")
        print(f"  Title: {article['title'][:80]}...")
        print(f"  Journal: {article['journal']}")
        print(f"  Year: {article['year']}")
        print(f"  URL: {article['url']}")
except Exception as e:
    print(f"Error during search: {e}")

print("\n" + "=" * 60)
print("Verification Complete!")
print("=" * 60)
