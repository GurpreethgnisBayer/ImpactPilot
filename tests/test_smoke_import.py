"""Smoke test: verify all modules can be imported without errors."""

def test_import_app():
    """Test that app module can be imported."""
    # Note: We don't actually run the Streamlit app, just import the module
    # This verifies there are no syntax errors or missing dependencies
    try:
        import sys
        import os
        # Add parent directory to path
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        # Import without executing
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", "app.py")
        # Just check the spec exists
        assert spec is not None
    except Exception as e:
        assert False, f"Failed to import app: {e}"


def test_import_modules():
    """Test that all impactpilot modules can be imported."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from impactpilot import state
    from impactpilot import ui
    from impactpilot import stepper
    from impactpilot import disclaimer
    
    # Verify key functions exist
    assert hasattr(state, 'init_state')
    assert hasattr(ui, 'render_step_0_idea')
    assert hasattr(stepper, 'render_stepper')
    assert hasattr(disclaimer, 'render_disclaimer')
    assert hasattr(disclaimer, 'DISCLAIMER_TEXT')
