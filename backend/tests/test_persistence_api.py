"""Persistence + FastAPI round-trip tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from impactpilot.domain.models import (
    DimensionEstimate,
    Direction,
    InitiativeRecord,
    MaturityTier,
    RangeValue,
    ValueSource,
)
from impactpilot.main import app
from impactpilot.persistence.db import Base, get_engine, init_db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("IMPACTPILOT_DB_URL", db_url)
    # Reset engine singleton
    import impactpilot.persistence.db as dbmod

    dbmod._ENGINE = None
    dbmod._SessionLocal = None
    init_db(db_url)
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_config_loaded(client):
    r = client.get("/api/config")
    assert r.status_code == 200
    body = r.json()
    assert "value_chain" in body
    assert "dimensions" in body


def test_crud_json_roundtrip(client):
    r = client.post("/api/initiatives", json={"initiative": {"title": "Image QC"}})
    assert r.status_code == 201
    rec = r.json()
    iid = rec["id"]
    assert rec["initiative"]["title"] == "Image QC"

    rec["initiative"]["description"] = "Automate QC"
    rec["scope"]["phase_id"] = "preclinical"
    rec["maturity"]["tier"] = "emerging_local"
    rec["estimates"] = [
        {
            "dimension_id": "cycle_time",
            "direction": "down",
            "estimate": {
                "low": 5,
                "base": 7,
                "high": 10,
                "unit": "days",
                "source": "user",
                "confirmed": True,
            },
            "confidence": "medium",
            "mechanism": "automation",
            "linked_evidence_ids": [],
        }
    ]
    r2 = client.put(f"/api/initiatives/{iid}", json=rec)
    assert r2.status_code == 200

    r3 = client.post(f"/api/initiatives/{iid}/statement")
    assert r3.status_code == 200
    assert r3.json()["impact_statement"]

    r4 = client.post(f"/api/initiatives/{iid}/scorecard")
    assert r4.status_code == 200
    assert r4.json()["impact_score"]["score"] >= 0

    # Export JSON
    r5 = client.get(f"/api/initiatives/{iid}/export.json")
    assert r5.status_code == 200
    exported = r5.json()

    # Import
    r6 = client.post("/api/import", json=exported)
    assert r6.status_code == 200
    assert r6.json()["id"] == iid

    # Versions + audit
    assert client.get(f"/api/initiatives/{iid}/versions").status_code == 200
    assert client.get(f"/api/initiatives/{iid}/audit").status_code == 200


def test_exploratory_never_shows_eur_in_gated(client):
    r = client.post("/api/initiatives", json={})
    iid = r.json()["id"]
    rec = r.json()
    rec["maturity"]["tier"] = "exploratory"
    # Try to sneak monetization in
    rec["monetization"] = [
        {
            "dimension_id": "cycle_time",
            "formula": "x",
            "inputs_trace": ["t"],
            "amount_eur": {
                "low": 1,
                "base": 2,
                "high": 3,
                "unit": "EUR",
                "source": "config",
                "confirmed": True,
            },
            "label": "indicative",
        }
    ]
    client.put(f"/api/initiatives/{iid}", json=rec)
    gated = client.get(f"/api/initiatives/{iid}/gated").json()
    assert gated["monetization"] == []


def test_export_marks_unconfirmed_llm_as_draft(client):
    r = client.post("/api/initiatives", json={"initiative": {"title": "X"}})
    iid = r.json()["id"]
    rec = r.json()
    rec["estimates"] = [
        {
            "dimension_id": "cost",
            "direction": "down",
            "estimate": {
                "low": 1,
                "base": 2,
                "high": 3,
                "unit": "EUR",
                "source": "llm_suggested",
                "confirmed": False,
            },
            "confidence": "low",
            "mechanism": "",
            "linked_evidence_ids": [],
        }
    ]
    client.put(f"/api/initiatives/{iid}", json=rec)
    r2 = client.get(f"/api/initiatives/{iid}/export.json")
    assert r2.status_code == 200
    meta = r2.json()["_export"]
    assert meta["export_status"] == "draft"
    assert any("estimates[0]" in f for f in meta["unconfirmed_fields"])

    pdf = client.get(f"/api/initiatives/{iid}/export.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    pptx = client.get(f"/api/initiatives/{iid}/export.pptx")
    assert pptx.status_code == 200 and pptx.content[:2] == b"PK"
    md = client.get(f"/api/initiatives/{iid}/export.md")
    assert md.status_code == 200 and "DRAFT" in md.text
    # Exploratory maturity: the local range stays withheld even in a draft.
    assert "1–3 EUR" not in md.text and "Withheld (exploratory)" in md.text
    for resp in (r2, pdf, pptx, md):
        assert "attachment;" in resp.headers["content-disposition"]
        assert "-draft." in resp.headers["content-disposition"]

    # Drafts still round-trip through import.
    assert client.post("/api/import", json=r2.json()).status_code == 200


def test_portfolio_csv(client):
    client.post("/api/initiatives", json={"initiative": {"title": "A"}})
    r = client.get("/api/portfolio/export.csv")
    assert r.status_code == 200
    assert "title" in r.text


def test_llm_off_manual_path(client):
    """Full intake without LLM: create, estimate, statement, scorecard, export."""
    r = client.post(
        "/api/initiatives",
        json={
            "initiative": {
                "title": "Manual path",
                "description": "No LLM",
                "focus_area_code": "FA1",
                "roles": {
                    "project_lead_name": "Ada",
                    "business_owner_name": "Bob",
                    "business_owner_signoff_status": "confirmed",
                },
            },
            "scope": {"phase_id": "clinical", "process_step": "screening"},
            "maturity": {"tier": "mature", "rationale": "benchmarks exist"},
            "change": {
                "what_changes": "faster screening",
                "lever_type": "faster",
                "affected_dimension_ids": ["cycle_time"],
            },
            "baselines": [
                {
                    "metric": "cycle days",
                    "value": {
                        "low": 30,
                        "base": 30,
                        "high": 30,
                        "unit": "days",
                        "source": "user",
                        "confirmed": True,
                    },
                    "unit": "days",
                    "unknown": False,
                }
            ],
            "estimates": [
                {
                    "dimension_id": "cycle_time",
                    "direction": "down",
                    "estimate": {
                        "low": 5,
                        "base": 10,
                        "high": 15,
                        "unit": "days",
                        "source": "user",
                        "confirmed": True,
                    },
                    "confidence": "high",
                    "mechanism": "automated triage",
                    "linked_evidence_ids": [],
                }
            ],
            "measurement_plan": [
                {
                    "name": "Days per screen",
                    "definition": "Elapsed days",
                    "data_source": "LIMS",
                    "owner": "Bob",
                    "cadence": "quarterly",
                }
            ],
        },
    )
    assert r.status_code == 201
    iid = r.json()["id"]
    assert client.post(f"/api/initiatives/{iid}/statement").status_code == 200
    assert client.post(f"/api/initiatives/{iid}/scorecard").status_code == 200
    assert client.post(f"/api/initiatives/{iid}/monetize").status_code == 200
    assert client.get(f"/api/initiatives/{iid}/export.md").status_code == 200
    assert client.get(f"/api/initiatives/{iid}/export.pptx").status_code == 200
