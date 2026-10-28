"""Shared test setup."""

from __future__ import annotations

import dataclasses

import pytest

from impactpilot.services.sources import registry


def stub_sources(monkeypatch: pytest.MonkeyPatch, **fns) -> None:
    """Replace registry searches: named keys get `fns[key]`, every other source returns []."""
    stubbed = {
        key: dataclasses.replace(spec, search=fns.get(key, lambda _q, _n: []))
        for key, spec in registry.SOURCES.items()
    }
    monkeypatch.setattr(registry, "SOURCES", stubbed)


@pytest.fixture(autouse=True)
def _offline_sources(monkeypatch):
    """No test reaches a live search API through the registry, and the guidance index never refreshes."""
    stub_sources(monkeypatch)
    monkeypatch.setenv("IMPACTPILOT_GUIDANCE_AUTOREFRESH", "0")
