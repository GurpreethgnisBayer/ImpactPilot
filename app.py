"""Main entry point for Impact Estimate Streamlit app."""

import streamlit as st
from impactpilot.state import init_state
from impactpilot.disclaimer import render_disclaimer
from impactpilot.stepper import render_stepper
from impactpilot.ui import (
    render_step_0_idea,
    render_step_1_evidence_shell,
    render_step_2_assumptions_shell,
    render_step_3_brief_shell,
)
from impactpilot.services.llm_health import validate_llm_settings, check_llm_connection

# Page configuration
st.set_page_config(
    page_title="Impact Estimate",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Initialize session state
init_state()

# Main app title
st.title("🔬 Impact Estimate")
st.write("Turn your R&D idea into a structured impact estimate grounded in PubMed evidence.")

# Render disclaimer banner
render_disclaimer()

# Render stepper
step_labels = ["Idea", "Evidence", "Assumptions", "Brief"]
render_stepper(st.session_state.step, step_labels)

# Render the current step
if st.session_state.step == 0:
    render_step_0_idea()
elif st.session_state.step == 1:
    render_step_1_evidence_shell()
elif st.session_state.step == 2:
    render_step_2_assumptions_shell()
elif st.session_state.step == 3:
    render_step_3_brief_shell()
else:
    st.error(f"Invalid step: {st.session_state.step}")

# Sidebar - LLM Provider Settings
with st.sidebar:
    st.header("⚙️ LLM Settings")
    
    # Provider selection
    provider = st.selectbox(
        "Provider",
        options=["ollama", "openai_compatible", "azure"],
        index=["ollama", "openai_compatible", "azure"].index(
            st.session_state.llm_settings.get("provider", "ollama")
        ) if st.session_state.llm_settings.get("provider") in ["ollama", "openai_compatible", "azure"] else 0,
        help="Select the LLM provider to use for inference"
    )
    st.session_state.llm_settings["provider"] = provider
    
    # Provider-specific configuration
    if provider == "ollama":
        st.subheader("Ollama Configuration")
        
        ollama_host = st.text_input(
            "Ollama Host",
            value=st.session_state.llm_settings.get("ollama_host", "http://localhost:11434"),
            placeholder="http://localhost:11434",
            help="URL of the Ollama server"
        )
        st.session_state.llm_settings["ollama_host"] = ollama_host
        
        ollama_model = st.text_input(
            "Ollama Model",
            value=st.session_state.llm_settings.get("ollama_model", "llama3.1:8b"),
            placeholder="llama3.1:8b",
            help="Name of the Ollama model to use"
        )
        st.session_state.llm_settings["ollama_model"] = ollama_model
    
    elif provider == "azure":
        st.subheader("Azure OpenAI Configuration")
        
        azure_endpoint = st.text_input(
            "Azure Endpoint",
            value=st.session_state.llm_settings.get("azure_endpoint", ""),
            placeholder="https://your-resource.openai.azure.com",
            help="Azure OpenAI endpoint URL"
        )
        st.session_state.llm_settings["azure_endpoint"] = azure_endpoint
        
        azure_api_key = st.text_input(
            "API Key",
            value=st.session_state.llm_settings.get("azure_api_key", ""),
            type="password",
            placeholder="Your Azure API key",
            help="Azure OpenAI API key"
        )
        st.session_state.llm_settings["azure_api_key"] = azure_api_key
        
        azure_deployment = st.text_input(
            "Deployment Name",
            value=st.session_state.llm_settings.get("azure_deployment", ""),
            placeholder="gpt-4",
            help="Azure OpenAI deployment name"
        )
        st.session_state.llm_settings["azure_deployment"] = azure_deployment
        
        azure_api_version = st.text_input(
            "API Version",
            value=st.session_state.llm_settings.get("azure_api_version", "2024-02-15-preview"),
            placeholder="2024-02-15-preview",
            help="Azure OpenAI API version"
        )
        st.session_state.llm_settings["azure_api_version"] = azure_api_version
    
    elif provider == "openai_compatible":
        st.subheader("OpenAI-Compatible Configuration")
        
        openai_base_url = st.text_input(
            "Base URL",
            value=st.session_state.llm_settings.get("openai_base_url", ""),
            placeholder="https://api.openai.com",
            help="Base URL for the OpenAI-compatible API"
        )
        st.session_state.llm_settings["openai_base_url"] = openai_base_url
        
        openai_api_key = st.text_input(
            "API Key",
            value=st.session_state.llm_settings.get("openai_api_key", ""),
            type="password",
            placeholder="sk-...",
            help="API key for authentication"
        )
        st.session_state.llm_settings["openai_api_key"] = openai_api_key
        
        openai_model = st.text_input(
            "Model",
            value=st.session_state.llm_settings.get("openai_model", "gpt-4"),
            placeholder="gpt-4",
            help="Model name to use"
        )
        st.session_state.llm_settings["openai_model"] = openai_model
    
    # Configuration status
    st.write("---")
    st.subheader("Configuration Status")
    
    validation_errors = validate_llm_settings(st.session_state.llm_settings)
    
    if validation_errors:
        st.error("⚠️ Configuration Errors:")
        for error in validation_errors:
            st.error(f"• {error}")
    else:
        st.success("✓ Configuration is valid")
    
    # Test connection button
    if st.button("🔌 Test Connection", use_container_width=True, disabled=bool(validation_errors)):
        with st.spinner("Testing connection..."):
            ok, message = check_llm_connection(st.session_state.llm_settings)
            if ok:
                st.success(message)
            else:
                st.error(f"❌ {message}")
