from impactpilot.config_loader import load_config, reload_config


def test_load_config():
    cfg = reload_config()
    assert cfg.value_chain.get("phases")
    assert cfg.dimensions.get("dimensions")
    assert len(cfg.focus_areas.get("focus_areas") or []) >= 4
    assert "approved_endpoints" in cfg.llm_endpoints
