"""Final acceptance test - verify all requirements."""

import sys
sys.path.insert(0, '.')

print("\n" + "=" * 70)
print("FINAL ACCEPTANCE TEST - ALL REQUIREMENTS")
print("=" * 70)

passed = []
failed = []

# 1. Test modules exist and import correctly
print("\n1. Module Imports")
print("-" * 70)
try:
    from impactpilot.calc import compute_tco, compute_productivity
    from impactpilot.report import build_brief_markdown
    from impactpilot.disclaimer import DISCLAIMER_TEXT
    passed.append("All modules import successfully")
    print("✓ All modules import successfully")
except Exception as e:
    failed.append(f"Module imports failed: {e}")
    print(f"✗ Import failed: {e}")

# 2. Test DISCLAIMER_TEXT exact match
print("\n2. DISCLAIMER_TEXT Exact Match")
print("-" * 70)
expected_disclaimer = "Disclaimer: This tool generates directional estimates. You must validate all inferred assumptions and evidence before using TCO or productivity numbers in decisions, submissions, or commitments."
if DISCLAIMER_TEXT == expected_disclaimer:
    passed.append("DISCLAIMER_TEXT exact match")
    print("✓ DISCLAIMER_TEXT matches specification")
else:
    failed.append("DISCLAIMER_TEXT does not match")
    print("✗ DISCLAIMER_TEXT does not match")

# 3. Test compute_tco returns None when inputs missing
print("\n3. compute_tco Returns None When Inputs Missing")
print("-" * 70)
tco_inputs = {
    "build_person_days": None,
    "run_person_days_per_year": 5,
    "license_cost_per_year": 5000,
    "compute_cost_per_year": 2000,
    "training_hours": 40,
    "downtime_hours_per_year": 10
}
result = compute_tco(tco_inputs, hourly_rate=100, horizon_years=3)
if result["horizon_cost"] is None and "Insufficient" in result["explanation"]:
    passed.append("compute_tco returns None correctly")
    print("✓ Returns None with 'Insufficient' explanation")
else:
    failed.append("compute_tco does not handle missing inputs correctly")
    print("✗ Does not handle missing inputs correctly")

# 4. Test compute_tco computes correctly with complete inputs
print("\n4. compute_tco Computes With Complete Inputs")
print("-" * 70)
tco_inputs_complete = {
    "build_person_days": 10,
    "run_person_days_per_year": 5,
    "license_cost_per_year": 5000,
    "compute_cost_per_year": 2000,
    "training_hours": 40,
    "downtime_hours_per_year": 10
}
result = compute_tco(tco_inputs_complete, hourly_rate=100, horizon_years=3)
expected_horizon = 48000
if result["horizon_cost"] == expected_horizon:
    passed.append("compute_tco computes correctly")
    print(f"✓ Computes correctly: ${result['horizon_cost']:,.2f}")
else:
    failed.append(f"compute_tco incorrect: expected {expected_horizon}, got {result['horizon_cost']}")
    print(f"✗ Expected ${expected_horizon:,.2f}, got ${result['horizon_cost']:,.2f}")

# 5. Test compute_productivity returns None when both inputs missing
print("\n5. compute_productivity Returns None When Both Inputs Missing")
print("-" * 70)
prod_inputs = {
    "time_saved_hours_per_month": None,
    "cost_avoided_per_year": None,
    "throughput_delta_per_year": None,
    "success_prob_delta": None
}
result = compute_productivity(prod_inputs, hourly_rate=100, horizon_years=3)
if result["horizon_productivity_value"] is None and "Insufficient" in result["explanation"]:
    passed.append("compute_productivity returns None correctly")
    print("✓ Returns None with 'Insufficient' explanation")
else:
    failed.append("compute_productivity does not handle missing inputs correctly")
    print("✗ Does not handle missing inputs correctly")

# 6. Test build_brief_markdown contains disclaimer
print("\n6. build_brief_markdown Contains DISCLAIMER_TEXT")
print("-" * 70)
idea = {"title": "Test", "description": "Test", "idea_type": "", "rd_stage": ""}
selected_articles = [{"pmid": "12345", "title": "Test", "authors": "Test", 
                     "year": "2024", "journal": "Test", "url": "https://test.com"}]
assumptions = {
    "productivity": {
        "time_saved_hours_per_month": {"value": None, "evidence_pmids": [], "evidence_raw": [], "explanation": "No evidence"},
        "cost_avoided_per_year": {"value": None, "evidence_pmids": [], "evidence_raw": [], "explanation": "No evidence"}
    },
    "tco": {
        "implementation_cost": {"value": None, "evidence_pmids": [], "evidence_raw": [], "explanation": "No evidence"},
        "annual_operating_cost": {"value": None, "evidence_pmids": [], "evidence_raw": [], "explanation": "No evidence"}
    }
}
tco_out = {"horizon_cost": None, "annual_run_cost": None, "breakdown": {}, "explanation": "Insufficient"}
prod_out = {"horizon_productivity_value": None, "annual_productivity_value": None, "breakdown": {}, 
            "throughput_delta_per_year": None, "success_prob_delta": None, "explanation": "Insufficient"}

brief = build_brief_markdown(idea, selected_articles, [], assumptions, tco_out, prod_out, 3)

if DISCLAIMER_TEXT in brief:
    passed.append("Brief contains DISCLAIMER_TEXT")
    print("✓ Brief contains DISCLAIMER_TEXT")
else:
    failed.append("Brief does not contain DISCLAIMER_TEXT")
    print("✗ Brief does not contain DISCLAIMER_TEXT")

# 7. Test brief shows "[Not found in selected evidence]" when assumptions missing
print("\n7. Brief Shows '[Not found in selected evidence]' When Missing")
print("-" * 70)
if "[Not found in selected evidence]" in brief:
    count = brief.count("[Not found in selected evidence]")
    passed.append(f"Brief shows '[Not found]' markers ({count} times)")
    print(f"✓ Shows '[Not found in selected evidence]' {count} times")
else:
    failed.append("Brief does not show '[Not found]' markers")
    print("✗ Does not show '[Not found]' markers")

# 8. Test brief does not contain "TBD" placeholders
print("\n8. Brief Does Not Contain 'TBD' Placeholders")
print("-" * 70)
if "TBD" not in brief:
    passed.append("No 'TBD' placeholders")
    print("✓ No 'TBD' placeholders found")
else:
    failed.append("Brief contains 'TBD' placeholders")
    print("✗ Brief contains 'TBD' placeholders")

# 9. Test brief has all required sections
print("\n9. Brief Has All Required Sections")
print("-" * 70)
required_sections = [
    "## Summary",
    "## Evidence used",
    "## Evidence-derived assumptions",
    "## Computed TCO",
    "## Computed R&D pipeline productivity",
    "## Evidence mapping",
    "## Citations",
    "## Open questions"
]
missing_sections = []
for section in required_sections:
    if section not in brief:
        missing_sections.append(section)

if not missing_sections:
    passed.append("All required sections present")
    print(f"✓ All {len(required_sections)} sections present")
else:
    failed.append(f"Missing sections: {missing_sections}")
    print(f"✗ Missing sections: {missing_sections}")

# 10. Run pytest
print("\n10. pytest Execution")
print("-" * 70)
import subprocess
try:
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tests/test_calc.py', 
         'tests/test_report_disclaimer_and_citations.py', 
         'tests/test_report_no_fabrication.py', '-q', '--tb=no'],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        summary = lines[-1] if lines else ""
        passed.append(f"pytest passes: {summary}")
        print(f"✓ pytest passes: {summary}")
    else:
        failed.append(f"pytest failed: return code {result.returncode}")
        print(f"✗ pytest failed: return code {result.returncode}")
except Exception as e:
    failed.append(f"pytest execution error: {e}")
    print(f"✗ pytest execution error: {e}")

# Summary
print("\n" + "=" * 70)
print("ACCEPTANCE TEST SUMMARY")
print("=" * 70)
print(f"\nPassed: {len(passed)}/{len(passed) + len(failed)}")
print(f"Failed: {len(failed)}/{len(passed) + len(failed)}")

if failed:
    print("\n❌ FAILED CHECKS:")
    for fail in failed:
        print(f"  - {fail}")
else:
    print("\n✅ ALL ACCEPTANCE CHECKS PASSED!")
    print("\nVerified:")
    for p in passed:
        print(f"  ✓ {p}")

print("\n" + "=" * 70)
print("READY FOR PRODUCTION" if not failed else "NEEDS FIXES")
print("=" * 70 + "\n")
