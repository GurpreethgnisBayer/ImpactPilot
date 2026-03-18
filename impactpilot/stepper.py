"""Horizontal stepper component for Impact Estimate."""

import streamlit as st


def render_stepper(step: int, labels: list[str]):
    """
    Render a horizontal stepper at the top of the page.
    
    Args:
        step: Current step index (0-based)
        labels: List of step labels
    """
    steps_html = []
    for i, label in enumerate(labels):
        if i == step:
            # Current step - bold and accent color
            steps_html.append(
                f'<span style="font-weight: bold; color: #FF4B4B; margin: 0 15px;">'
                f'▶ {i + 1}. {label}</span>'
            )
        elif i < step:
            # Completed step
            steps_html.append(
                f'<span style="color: #31333F; margin: 0 15px;">✓ {i + 1}. {label}</span>'
            )
        else:
            # Future step
            steps_html.append(
                f'<span style="color: #808495; margin: 0 15px;">{i + 1}. {label}</span>'
            )
    
    stepper_html = f'''
    <div style="padding: 20px 0; border-bottom: 1px solid #e0e0e0; margin-bottom: 20px;">
        <div style="display: flex; justify-content: center; align-items: center;">
            {"".join(steps_html)}
        </div>
    </div>
    '''
    
    st.markdown(stepper_html, unsafe_allow_html=True)
