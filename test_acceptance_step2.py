"""Integration test for auto-update query mechanism."""

import sys
sys.path.insert(0, '.')

from impactpilot.query_suggest import suggest_pubmed_query

print("\n" + "=" * 70)
print("STEP 2 ACCEPTANCE CHECKS - AUTO-UPDATE QUERY MECHANISM")
print("=" * 70)

# Test Case 1: Basic auto-update scenario
print("\n✓ Test 1: Basic Query Auto-Update")
print("-" * 70)
title = "Automated Quality Control System"
description = "Using computer vision for defect detection in manufacturing"
query = suggest_pubmed_query(title, description)
print(f"Idea Title: {title}")
print(f"Idea Description: {description}")
print(f"Auto-suggested Query: {query}")
assert query, "Query should not be empty"
assert "automated" in query.lower() or "quality" in query.lower()
print("✓ PASSED: Query auto-generates from idea input")

# Test Case 2: Query changes when title changes
print("\n✓ Test 2: Query Updates When Title Changes")
print("-" * 70)
title1 = "AI Drug Discovery"
desc = "Accelerating pharmaceutical research"
query1 = suggest_pubmed_query(title1, desc)
print(f"Original: '{title1}' → Query: '{query1}'")

title2 = "Machine Learning Medical Diagnosis"
query2 = suggest_pubmed_query(title2, desc)
print(f"Changed: '{title2}' → Query: '{query2}'")

assert query1 != query2, "Query should change when title changes"
print("✓ PASSED: Query updates when title changes")

# Test Case 3: Query changes when description changes
print("\n✓ Test 3: Query Updates When Description Changes")
print("-" * 70)
title = "Clinical Research"
desc1 = "Cancer treatment outcomes analysis"
query1 = suggest_pubmed_query(title, desc1)
print(f"Original desc: '{desc1}' → Query: '{query1}'")

desc2 = "Diabetes prevention strategies"
query2 = suggest_pubmed_query(title, desc2)
print(f"Changed desc: '{desc2}' → Query: '{query2}'")

assert query1 != query2, "Query should change when description changes"
print("✓ PASSED: Query updates when description changes")

# Test Case 4: Empty input fallback
print("\n✓ Test 4: Fallback Behavior for Empty Input")
print("-" * 70)
query = suggest_pubmed_query("", "")
print(f"Empty inputs → Query: '{query}'")
assert query, "Query should never be empty (fallback should apply)"
print("✓ PASSED: Fallback prevents empty queries")

# Test Case 5: Stopword filtering
print("\n✓ Test 5: Stopword Filtering")
print("-" * 70)
title = "The Impact of the New Approach"
desc = "This is a study on the effect of a method"
query = suggest_pubmed_query(title, desc)
print(f"Input with stopwords → Query: '{query}'")
tokens = query.lower().split()
assert "the" not in tokens, "Stopword 'the' should be filtered"
assert "is" not in tokens, "Stopword 'is' should be filtered"
assert "a" not in tokens, "Stopword 'a' should be filtered"
print("✓ PASSED: Common stopwords are filtered out")

print("\n" + "=" * 70)
print("ALL ACCEPTANCE CHECKS PASSED ✓")
print("=" * 70)
print("\nKey Features Verified:")
print("  • Query auto-generates from idea title and description")
print("  • Query updates automatically when title changes")
print("  • Query updates automatically when description changes")
print("  • Never returns empty query (has fallback)")
print("  • Filters common stopwords for cleaner queries")
print("=" * 70 + "\n")
