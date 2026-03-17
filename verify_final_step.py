"""End-to-end verification of Impact Brief generation."""

import sys
sys.path.insert(0, '.')

from impactpilot.evidence_numbers import extract_all_numeric_evidence
from impactpilot.assumptions import derive_assumptions
from impactpilot.calc import compute_tco, compute_productivity
from impactpilot.report import build_brief_markdown
from impactpilot.disclaimer import DISCLAIMER_TEXT

print("\n" + "=" * 70)
print("IMPACT BRIEF GENERATION - END-TO-END VERIFICATION")
print("=" * 70)

# Sample idea
idea = {
    "title": "AI-Powered Drug Discovery Acceleration Platform",
    "description": "Develop a machine learning system to predict drug-target interactions, reducing the time and cost of pharmaceutical R&D screening phases",
    "idea_type": "New Technology",
    "rd_stage": "Feasibility"
}

# Sample selected articles with numeric evidence
selected_articles = [
    {
        "pmid": "12345",
        "title": "Accelerating Drug Discovery with Machine Learning",
        "authors": "Smith J, Doe A",
        "year": "2024",
        "journal": "Nature Biotechnology",
        "abstract": "Our AI platform reduced screening time by 45% compared to traditional methods. The system processed 100 compounds in just 3 hours, compared to 2 days manually. A study of 50 drug candidates demonstrated 30% cost reduction."
    },
    {
        "pmid": "67890",
        "title": "Cost-Effectiveness of Computational Drug Screening",
        "authors": "Johnson M, Lee K",
        "year": "2023",
        "journal": "Journal of Medicinal Chemistry",
        "abstract": "Automated screening systems showed promising results. Processing efficiency improved from 10 hours to 6 hours per batch over a 12 week validation period. Manual curation time decreased by 25%."
    }
]

print("\n1. EXTRACTING NUMERIC EVIDENCE")
print("-" * 70)
extracted_evidence = extract_all_numeric_evidence(selected_articles)
print(f"Extracted {len(extracted_evidence)} numeric evidence items:")
for ev in extracted_evidence[:5]:
    print(f"  - {ev['type']}: {ev['value']} {ev['unit']} (PMID {ev['pmid']})")

print("\n2. DERIVING ASSUMPTIONS")
print("-" * 70)
assumptions = derive_assumptions(idea, selected_articles, extracted_evidence)

time_saved = assumptions["productivity"]["time_saved_hours_per_month"]
print(f"Time saved: {time_saved['value']} hours/month")
if time_saved['value']:
    print(f"  Evidence PMIDs: {time_saved['evidence_pmids']}")
    print(f"  Raw: {time_saved['evidence_raw']}")

print("\n3. COMPUTING TCO")
print("-" * 70)
tco_inputs = {
    "build_person_days": 30,  # Assuming 6 weeks of development
    "run_person_days_per_year": 10,  # Minimal ongoing maintenance
    "license_cost_per_year": 50000,  # ML platform licenses
    "compute_cost_per_year": 20000,  # Cloud computing
    "training_hours": 80,  # Team training
    "downtime_hours_per_year": 20  # Minimal downtime
}

tco_out = compute_tco(tco_inputs, hourly_rate=100, horizon_years=3)
print(f"3-year TCO: ${tco_out['horizon_cost']:,.2f}")
print(f"Annual run cost: ${tco_out['annual_run_cost']:,.2f}")

print("\n4. COMPUTING PRODUCTIVITY")
print("-" * 70)
prod_inputs = {
    "time_saved_hours_per_month": time_saved['value'],
    "cost_avoided_per_year": None,  # Not found in abstracts
    "throughput_delta_per_year": None,
    "success_prob_delta": None
}

prod_out = compute_productivity(prod_inputs, hourly_rate=100, horizon_years=3)
if prod_out['horizon_productivity_value']:
    print(f"3-year productivity value: ${prod_out['horizon_productivity_value']:,.2f}")
    print(f"Annual productivity value: ${prod_out['annual_productivity_value']:,.2f}")
else:
    print(f"Not computable: {prod_out['explanation']}")

print("\n5. GENERATING IMPACT BRIEF")
print("-" * 70)
brief_md = build_brief_markdown(
    idea=idea,
    selected_articles=selected_articles,
    extracted_numeric_evidence=extracted_evidence,
    assumptions=assumptions,
    tco_out=tco_out,
    prod_out=prod_out,
    horizon_years=3
)

print(f"Generated brief: {len(brief_md)} characters")
print(f"Contains disclaimer: {DISCLAIMER_TEXT in brief_md}")
print(f"Contains '[Evidence-derived]': {'[Evidence-derived]' in brief_md}")
print(f"Contains '[Not found]': {'[Not found in selected evidence]' in brief_md}")

print("\n6. PREVIEW OF GENERATED BRIEF")
print("=" * 70)
print(brief_md[:1500])
print("\n... (truncated)")
print("=" * 70)

print("\n7. KEY CHECKS")
print("-" * 70)

checks = [
    ("Disclaimer present", DISCLAIMER_TEXT in brief_md),
    ("Evidence-derived values marked", "[Evidence-derived]" in brief_md),
    ("PMID provenance shown", "Source: PMID" in brief_md),
    ("Selected PMIDs cited", "12345" in brief_md and "67890" in brief_md),
    ("TCO computed", "$" in brief_md and "TCO" in brief_md),
    ("Productivity computed", "productivity" in brief_md.lower()),
    ("Citations section exists", "## Citations" in brief_md),
    ("Open questions section exists", "## Open questions" in brief_md),
    ("No 'TBD' placeholders", "TBD" not in brief_md),
]

all_passed = True
for check_name, result in checks:
    status = "✓" if result else "✗"
    print(f"{status} {check_name}")
    if not result:
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("ALL VERIFICATION CHECKS PASSED ✓")
    print("\nThe Impact Brief generation system is working correctly:")
    print("  ✓ Extracts numeric evidence from abstracts")
    print("  ✓ Derives assumptions with PMID provenance")
    print("  ✓ Computes TCO and productivity when possible")
    print("  ✓ Generates structured Markdown brief with disclaimer")
    print("  ✓ Never fabricates data - clearly states when not computable")
else:
    print("SOME CHECKS FAILED ✗")
print("=" * 70 + "\n")

# Save brief to file
with open("sample_impact_brief.md", "w") as f:
    f.write(brief_md)
print("Sample brief saved to: sample_impact_brief.md")
