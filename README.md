# ImpactPilot

A reproducible Streamlit app that turns a plain-language R&D idea into a structured Impact Brief grounded in PubMed evidence.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

## Testing

```bash
python -m pytest -q
```

## Architecture

- **Single-column layout** with top stepper (no right-side panels)
- **4 steps**: Idea → Evidence → Assumptions → Brief
- **Settings**: Sidebar only (Ollama or OpenAI-compatible endpoint)
- **Evidence-grounded**: Only extracts numeric assumptions from selected PubMed abstracts

## Disclaimer

This tool generates directional estimates. You must validate all inferred assumptions and evidence before using TCO or productivity numbers in decisions, submissions, or commitments.
