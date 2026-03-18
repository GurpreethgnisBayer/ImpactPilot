"""Smoke test: verify all modules can be imported."""


def test_import_app():
    """Test that app module can be imported."""
    import app
    assert app is not None


def test_import_state():
    """Test that state module can be imported."""
    from impactpilot import state
    assert state is not None
    assert hasattr(state, "init_state")


def test_import_ui():
    """Test that ui module can be imported."""
    from impactpilot import ui
    assert ui is not None
    assert hasattr(ui, "render_step_0_idea")


def test_import_stepper():
    """Test that stepper module can be imported."""
    from impactpilot import stepper
    assert stepper is not None
    assert hasattr(stepper, "render_stepper")


def test_import_disclaimer():
    """Test that disclaimer module can be imported."""
    from impactpilot import disclaimer
    assert disclaimer is not None
    assert hasattr(disclaimer, "render_disclaimer")


def test_import_constants():
    """Test that constants module can be imported."""
    from impactpilot import constants
    assert constants is not None
    assert hasattr(constants, "IDEA_TYPE_OPTIONS")
    assert hasattr(constants, "RD_STAGE_OPTIONS")
