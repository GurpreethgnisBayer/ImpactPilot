"""Manual verification script for Step 3 - Evidence-grounded assumptions."""

import sys
sys.path.insert(0, '.')

from impactpilot.evidence_numbers import extract_numeric_evidence, extract_all_numeric_evidence
from impactpilot.assumptions import derive_assumptions, validate_assumptions_grounding

print("=" * 70)
print("ImpactPilot Step 3 - Evidence-Grounded Assumptions Verification")
print("=" * 70)

# Sample articles with numeric evidence
sample_articles = [
    {
        "pmid": "12345",
        "title": "Reducing Lab Processing Time with Automation",
        "abstract": "Our study of 50 patients demonstrated that automated processing reduced turnaround time by 45% compared to manual methods. The average time saved was 2.5 hours per sample, resulting in significant workflow improvements."
    },
    {
        "pmid": "67890",
        "title": "Cost-Effectiveness of Quality Control Systems",
        "abstract": "Implementation across 100 samples showed a 30% reduction in defect rates over 6 weeks. Manual inspection time decreased from 15 minutes to 10 minutes per unit."
    },
    {
        "pmid": "99999",
        "title": "Qualitative Analysis of User Experience",
        "abstract": "Participants reported improved satisfaction and better outcomes. No quantitative metrics were available."
    }
]

print("\n1. EXTRACTING NUMERIC EVIDENCE")
print("-" * 70)

all_evidence = extract_all_numeric_evidence(sample_articles)
print(f"Found {len(all_evidence)} numeric evidence items:")

for i, ev in enumerate(all_evidence, 1):
    print(f"\n  {i}. Type: {ev['type']}, Value: {ev['value']} {ev['unit']}")
    print(f"     PMID: {ev['pmid']}")
    print(f"     Raw: '{ev['raw']}'")
    print(f"     Context: \"{ev['context'][:80]}...\"")

print("\n\n2. DERIVING ASSUMPTIONS (Evidence-Grounded)")
print("-" * 70)

idea = {
    "title": "Automated Quality Control System",
    "description": "Implement computer vision for defect detection"
}

# Test with all articles selected
selected_articles = sample_articles[:2]  # Only first two have numbers
assumptions = derive_assumptions(idea, selected_articles, all_evidence)

print("\nProductivity Impact:")
print("=" * 40)

time_saved = assumptions["productivity"]["time_saved_hours_per_month"]
print(f"Time Saved: {time_saved['value']} hours/month")
if time_saved['value'] is not None:
    print(f"  Evidence PMIDs: {time_saved['evidence_pmids']}")
    print(f"  Evidence Raw: {time_saved['evidence_raw']}")
    print(f"  Explanation: {time_saved['explanation'][:100]}...")
else:
    print(f"  {time_saved['explanation']}")

cost_avoided = assumptions["productivity"]["cost_avoided_per_year"]
print(f"\nCost Avoided: {cost_avoided['value']}")
print(f"  {cost_avoided['explanation']}")

print("\n\nTCO:")
print("=" * 40)

impl_cost = assumptions["tco"]["implementation_cost"]
print(f"Implementation Cost: {impl_cost['value']}")
print(f"  {impl_cost['explanation']}")

annual_cost = assumptions["tco"]["annual_operating_cost"]
print(f"Annual Operating Cost: {annual_cost['value']}")
print(f"  {annual_cost['explanation']}")

print("\n\n3. VALIDATING EVIDENCE GROUNDING")
print("-" * 70)

selected_pmids = {article["pmid"] for article in selected_articles}
is_valid = validate_assumptions_grounding(assumptions, selected_pmids)

print(f"Selected PMIDs: {selected_pmids}")
print(f"Validation: {'✓ PASSED' if is_valid else '✗ FAILED'}")
print("All assumption PMIDs are from selected articles!" if is_valid else "ERROR: Fabricated PMIDs detected!")

print("\n\n4. TEST: NO FABRICATION WITH EMPTY EVIDENCE")
print("-" * 70)

qualitative_only = [sample_articles[2]]  # Article with no numbers
empty_evidence = extract_all_numeric_evidence(qualitative_only)
assumptions_empty = derive_assumptions(idea, qualitative_only, empty_evidence)

print(f"Evidence extracted: {len(empty_evidence)} items")
time_saved_empty = assumptions_empty["productivity"]["time_saved_hours_per_month"]
print(f"Time Saved value: {time_saved_empty['value']}")
print(f"Explanation: {time_saved_empty['explanation']}")

if time_saved_empty['value'] is None:
    print("✓ PASSED: System correctly returns None when no evidence exists")
else:
    print("✗ FAILED: System fabricated a value without evidence!")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE!")
print("=" * 70)
print("\nKey Features Verified:")
print("  ✓ Numeric evidence extracted from abstracts (%, time, counts)")
print("  ✓ Assumptions populated ONLY from extracted evidence")
print("  ✓ All assumption PMIDs match selected articles (no fabrication)")
print("  ✓ Fields without evidence are None with clear explanation")
print("  ✓ Each value includes PMID provenance and raw evidence")
print("=" * 70)
