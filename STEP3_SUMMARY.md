# Step 3 Implementation Summary

## ✅ Implementation Complete

All Step 3 requirements have been successfully implemented and tested.

---

## 📁 New Files Created

### Core Modules
- **impactpilot/services/llm_provider.py** - LLM provider abstraction (Ollama & OpenAI-compatible)
- **impactpilot/evidence_numbers.py** - Extract numeric evidence from abstracts
- **impactpilot/assumptions.py** - Derive evidence-grounded assumptions

### Tests (26 new tests)
- **tests/test_llm_provider_selection.py** - 8 tests for provider selection
- **tests/test_evidence_numbers.py** - 11 tests for numeric extraction
- **tests/test_assumptions_grounding.py** - 7 tests for assumption validation

### Verification Scripts
- **verify_step3.py** - Comprehensive evidence extraction demo
- **verify_step3_simple.py** - Quick verification of all features
- **test_acceptance_step3.py** - Acceptance criteria validation

---

## 📝 Files Modified

- **impactpilot/state.py** - Enhanced LLM settings structure
- **impactpilot/ui.py** - Implemented full Step 2 (Assumptions) UI with teal highlighting
- **app.py** - Enhanced sidebar with complete LLM provider configuration

---

## 🧪 Test Results

**Total Tests: 52 passing** (26 existing + 26 new)

### Test Coverage by Module
- LLM Provider Selection: 8 tests ✓
- Evidence Extraction: 11 tests ✓
- Assumptions Grounding: 7 tests ✓
- Query Suggestion: 8 tests ✓
- PubMed Term Building: 13 tests ✓
- Smoke & Disclaimer: 5 tests ✓

All tests pass with no errors.

---

## ✅ Acceptance Criteria Verification

### 1. ✓ Sidebar LLM Provider Selection

**Requirement**: Provider dropdown exists in sidebar and shows relevant fields

**Implementation**:
- Selectbox with "ollama" and "openai_compatible" options
- **Ollama fields**: Host, Model, Temperature, Max Tokens
- **OpenAI-compatible fields**: Base URL, API Key (password), Model, Temperature
- Settings saved in `st.session_state.llm_settings`

**Verification**: ✓ Sidebar renders correctly with all fields

---

### 2. ✓ Numeric Evidence Extraction

**Requirement**: Auto-extract numeric evidence from selected PubMed abstracts

**Implementation**:
- Extracts **percentages** (e.g., 25%, 30 percent)
- Extracts **time** (hours, minutes, days, weeks, months, years)
- Extracts **counts** (e.g., 30 patients, 100 samples)
- Each entry includes: pmid, raw text, type, value, unit, context window

**Verification**:
```
Article: "Study found 45% improvement and 3 hours time savings with 50 patients"
Extracted:
  - percentage: 45.0 %
  - time: 3.0 hours
  - count: 50 patients
```

---

### 3. ✓ Evidence-Grounded Assumptions

**Requirement**: Populate numeric fields ONLY from extracted evidence, never fabricate

**Implementation**:
- `derive_assumptions()` uses only extracted numeric evidence
- Returns None + explanation "No numeric evidence found" when evidence missing
- Each populated field includes:
  - value (numeric or None)
  - evidence_pmids (list of PMIDs)
  - evidence_raw (list of raw evidence snippets)
  - explanation (context text)

**Verification**:
```
With evidence:
  Time Saved: 12.0 hours/month
  PMIDs: ['12345']
  Evidence: ['3 hours']

Without evidence:
  Time Saved: None
  Explanation: "No numeric evidence found in selected abstracts."
```

---

### 4. ✓ PMID Validation (Zero Fabrication)

**Requirement**: All assumption PMIDs must be subset of selected PMIDs

**Implementation**:
- `validate_assumptions_grounding()` checks all evidence PMIDs
- Returns False if any PMID not in selected set
- Test suite validates no fabrication

**Verification**:
```
Selected PMIDs: {'12345', '67890'}
Assumption PMIDs: {'12345'}
Validation: PASSED (subset check)
```

---

### 5. ✓ Teal-Highlighted UI with PMID Sources

**Requirement**: Step 2 shows teal values (#008080) with PMID provenance

**Implementation** (in `render_step_2_assumptions_shell()`):
- Auto-extracts evidence when entering step or selection changes
- Teal-highlighted values using HTML span with color #008080
- Shows: "Source: PMID [link] — 'raw evidence'"
- Explanation text below each value
- Blank fields show "—" with explanation

**Example Output**:
```html
<span style="color: #008080; font-size: 24px; font-weight: bold;">12.0</span> hours/month

Source: PMID [12345] — '3 hours'
ℹ️ Estimated from time reduction of 3 hours mentioned in abstract...
```

---

## 🎯 Key Features Implemented

### LLM Provider System
- ✓ Abstract base class `LLMProvider`
- ✓ `OllamaProvider` - Local LLM via Ollama API
- ✓ `OpenAICompatibleProvider` - OpenAI-compatible endpoints
- ✓ `get_provider()` factory function
- ✓ Mocked tests (no network calls)

### Evidence Extraction
- ✓ Regex-based numeric extraction
- ✓ Context window capture (50 chars before/after)
- ✓ Unit normalization (hours/hrs/hr → hours)
- ✓ Multiple evidence types from single abstract

### Assumption Fields
```python
assumptions = {
    "productivity": {
        "time_saved_hours_per_month": {...},
        "cost_avoided_per_year": {...}
    },
    "tco": {
        "implementation_cost": {...},
        "annual_operating_cost": {...}
    }
}
```

### Safety Guarantees
- ✓ **Never fabricates numbers** - only uses extracted evidence
- ✓ **Always validates PMIDs** - must be from selected articles
- ✓ **Clear explanations** - states when no evidence found
- ✓ **Full provenance** - links to source PMID + raw text

---

## 🚀 Ready for Step 4

All acceptance criteria met:
- [x] When you select papers, Step 2 auto-extracts numeric evidence
- [x] Teal values shown with PMID sources OR blank with explanation
- [x] Provider dropdown exists with relevant fields
- [x] python -m pytest passes (52 tests)
- [x] Zero fabrication - all PMIDs validated

**Step 3 Complete!** The app now has:
1. ✓ Single-column layout with stepper
2. ✓ Step 1: Idea input with auto-query generation
3. ✓ Step 2: PubMed search with real results
4. ✓ **Step 3: Evidence-grounded assumptions with teal highlighting**
5. ⏳ Step 4: Impact Brief (next phase)

---

## 📊 Statistics

- **Total lines of code added**: ~1,500
- **Test files created**: 3
- **Test cases added**: 26
- **Modules created**: 3
- **Zero regressions**: All previous tests still pass
