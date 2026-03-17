"""Disclaimer banner for ImpactPilot."""

import streamlit as st

DISCLAIMER_TEXT = "Disclaimer: This tool generates directional estimates. You must validate all inferred assumptions and evidence before using TCO or productivity numbers in decisions, submissions, or commitments."


def render_disclaimer():
    """Render the disclaimer banner at the top of the app."""
    st.warning(DISCLAIMER_TEXT)
