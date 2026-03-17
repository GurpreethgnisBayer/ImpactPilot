"""Horizontal stepper component for ImpactPilot."""

import streamlit as st


def render_stepper(step: int, labels: list[str]):
    """
    Render a horizontal stepper at the top of the app.
    
    Args:
        step: Current step index (0-based)
        labels: List of step labels
    """
    # Build the stepper HTML with CSS styling
    stepper_items = []
    
    for i, label in enumerate(labels):
        if i == step:
            # Current step: bold + accent color
            stepper_items.append(f"**:blue[{i+1}) {label}]**")
        elif i < step:
            # Completed step: normal weight
            stepper_items.append(f"{i+1}) {label}")
        else:
            # Future step: muted
            stepper_items.append(f":gray[{i+1}) {label}]")
    
    # Join with separators
    stepper_html = " | ".join(stepper_items)
    
    # Render at the top
    st.markdown(stepper_html)
    st.markdown("---")  # Horizontal divider
