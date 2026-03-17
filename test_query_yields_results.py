"""Test if auto-generated queries yield actual PubMed results."""

import sys
sys.path.insert(0, '.')

print("\n" + "=" * 70)
print("TESTING: AUTO-GENERATED QUERY → PUBMED RESULTS")
print("=" * 70)

# Test 1: Generate query from idea
print("\n1. Generate PubMed query from sample idea")
print("-" * 70)
from impactpilot.query_suggest import suggest_pubmed_query

test_ideas = [
    {
        "title": "CRISPR gene editing for cancer therapy",
        "description": "Novel approach to target oncogenes using CRISPR-Cas9"
    },
    {
        "title": "AI-powered drug discovery platform",
        "description": "Machine learning tool to predict drug-target interactions and accelerate screening"
    },
    {
        "title": "Point-of-care diagnostic for malaria",
        "description": "Rapid blood test device for detecting malaria parasites in field settings"
    }
]

for i, idea in enumerate(test_ideas, 1):
    query = suggest_pubmed_query(idea["title"], idea["description"])
    print(f"\n{i}. Idea: {idea['title']}")
    print(f"   Query: {query}")

# Test 2: Search PubMed with generated queries
print("\n" + "=" * 70)
print("2. Search PubMed API with generated queries")
print("-" * 70)

from impactpilot.services.pubmed_eutils import search_pubmed

for i, idea in enumerate(test_ideas, 1):
    query = suggest_pubmed_query(idea["title"], idea["description"])
    print(f"\n{i}. Testing: {idea['title']}")
    print(f"   Query: {query}")
    
    try:
        results = search_pubmed(
            query=query,
            max_results=5,
            date_preset="5years"
        )
        
        if results:
            print(f"   ✓ SUCCESS: Found {len(results)} results")
            print(f"   First result: {results[0].get('title', 'N/A')[:80]}...")
        else:
            print(f"   ⚠ WARNING: Query returned 0 results")
            print(f"   This query may be too specific or use terminology not in PubMed")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")

# Test 3: Test with minimal query
print("\n" + "=" * 70)
print("3. Test fallback with minimal input")
print("-" * 70)

minimal_idea = {
    "title": "Cancer research",
    "description": ""
}

query = suggest_pubmed_query(minimal_idea["title"], minimal_idea["description"])
print(f"Minimal idea: {minimal_idea['title']}")
print(f"Generated query: {query}")

try:
    results = search_pubmed(query=query, max_results=5)
    if results:
        print(f"✓ Found {len(results)} results even with minimal input")
    else:
        print(f"⚠ No results with minimal input")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
If all test ideas returned results: ✓ Auto-generate feature works!
If some returned 0 results: The query generation may need tuning
If errors occurred: Check internet connection or NCBI E-utilities API status

RECOMMENDATIONS:
- If queries are too specific, consider using fewer/broader terms
- If no results, the app should show a message to users to manually edit the query
- Users can always override the auto-generated query in Step 2
""")
print("=" * 70 + "\n")
