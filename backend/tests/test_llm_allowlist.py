from impactpilot.services.llm_allowlist import host_allowed


def test_local_model_hosts_blocked():
    assert not host_allowed("http://localhost:11434")
    assert not host_allowed("http://127.0.0.1:11434")


def test_openai_official_allowed():
    assert host_allowed("https://api.openai.com/v1")


def test_azure_pattern_allowed():
    assert host_allowed("https://amlopenai.openai.azure.com")


def test_random_host_blocked():
    assert not host_allowed("https://evil.example.com/v1")
