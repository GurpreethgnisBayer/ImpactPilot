"""Disclaimer banner for Impact Estimate."""

import streamlit as st

DISCLAIMER_TEXT = "Disclaimer: This tool generates directional estimates. You must validate all inferred assumptions and evidence before using TCO or productivity numbers in decisions, submissions, or commitments."


def render_disclaimer():
    """Render the disclaimer banner on every step."""
    st.warning(DISCLAIMER_TEXT)
