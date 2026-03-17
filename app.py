"""ImpactPilot: Main Streamlit application entry point."""

import streamlit as st
from impactpilot.state import init_state
from impactpilot.disclaimer import render_disclaimer
from impactpilot.stepper import render_stepper
from impactpilot import ui

# Page configuration
st.set_page_config(
    page_title="ImpactPilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
init_state()

# Sidebar: LLM settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    provider = st.selectbox(
        "LLM Provider",
        options=["ollama", "openai_compatible"],
        index=0 if st.session_state.llm_settings["provider"] == "ollama" else 1,
        key="llm_provider_select",
        format_func=lambda x: "Ollama (Local)" if x == "ollama" else "OpenAI-Compatible API"
    )
    st.session_state.llm_settings["provider"] = provider
    
    if provider == "ollama":
        st.text_input(
            "Ollama Host",
            value=st.session_state.llm_settings["ollama_host"],
            key="ollama_host_input",
            help="e.g., http://localhost:11434"
        )
        st.session_state.llm_settings["ollama_host"] = st.session_state.ollama_host_input
        
        st.text_input(
            "Ollama Model",
            value=st.session_state.llm_settings["ollama_model"],
            key="ollama_model_input",
            help="e.g., llama2, mistral, codellama"
        )
        st.session_state.llm_settings["ollama_model"] = st.session_state.ollama_model_input
        
        st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.llm_settings["temperature"],
            step=0.1,
            key="ollama_temperature_slider",
            help="Higher = more creative, Lower = more focused"
        )
        st.session_state.llm_settings["temperature"] = st.session_state.ollama_temperature_slider
        
        st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=4000,
            value=st.session_state.llm_settings["max_tokens"],
            step=100,
            key="ollama_max_tokens_input"
        )
        st.session_state.llm_settings["max_tokens"] = st.session_state.ollama_max_tokens_input
        
    else:  # openai_compatible
        st.text_input(
            "API Base URL",
            value=st.session_state.llm_settings["openai_base_url"],
            key="openai_base_url_input",
            help="e.g., https://api.openai.com/v1"
        )
        st.session_state.llm_settings["openai_base_url"] = st.session_state.openai_base_url_input
        
        st.text_input(
            "API Key",
            value=st.session_state.llm_settings["openai_api_key"],
            type="password",
            key="openai_api_key_input"
        )
        st.session_state.llm_settings["openai_api_key"] = st.session_state.openai_api_key_input
        
        st.text_input(
            "Model Name",
            value=st.session_state.llm_settings["openai_model"],
            key="openai_model_input",
            help="e.g., gpt-3.5-turbo, gpt-4"
        )
        st.session_state.llm_settings["openai_model"] = st.session_state.openai_model_input
        
        st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.llm_settings["temperature"],
            step=0.1,
            key="openai_temperature_slider",
            help="Higher = more creative, Lower = more focused"
        )
        st.session_state.llm_settings["temperature"] = st.session_state.openai_temperature_slider

# Main content area (single column)
st.title("🚀 ImpactPilot")
st.caption("Turn R&D ideas into structured Impact Briefs grounded in PubMed evidence")

# Render disclaimer banner at the top
render_disclaimer()

# Render stepper
step_labels = ["Idea", "Evidence", "Assumptions", "Brief"]
render_stepper(st.session_state.step, step_labels)

# Render current step
if st.session_state.step == 0:
    ui.render_step_0_idea()
elif st.session_state.step == 1:
    ui.render_step_1_evidence_shell()
elif st.session_state.step == 2:
    ui.render_step_2_assumptions_shell()
elif st.session_state.step == 3:
    ui.render_step_3_brief_shell()

# Render navigation buttons
st.markdown("---")
ui.render_navigation()
