"""Parsing tests for the grey-literature, registry, regulatory, and web source clients (HTTP mocked)."""

from __future__ import annotations

import pytest

from impactpilot.services.sources import registry


class Response:
    def __init__(self, payload=None, *, status_code=200, text=""):
        self._payload = payload
        self.status_code = status_code
        self.text = text
        self.content = text.encode()

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_core_parses_works_and_needs_a_key(monkeypatch):
    from impactpilot.services.core_api import search_core

    seen = {}

    def fake_get(_url, params, headers, **_kw):
        seen["headers"] = headers
        return Response(
            {
                "results": [
                    {
                        "id": 42,
                        "title": "Decentralised trials: an NHS report",
                        "abstract": "",
                        "fullText": "Executive summary. Remote visits cut travel by 40%.",
                        "yearPublished": 2023,
                        "doi": "10.5/core",
                        "documentType": "report",
                        "publisher": "NHS",
                        "links": [{"type": "display", "url": "https://core.ac.uk/works/42"}],
                    },
                    {"id": 43, "title": "No text at all"},
                ]
            }
        )

    monkeypatch.setattr("impactpilot.services.core_api.requests.get", fake_get)
    monkeypatch.delenv("CORE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="CORE_API_KEY"):
        search_core("trials")
    assert registry.SOURCES["core"].available is False

    monkeypatch.setenv("CORE_API_KEY", "k")
    hits = search_core("trials")
    assert seen["headers"]["Authorization"] == "Bearer k"
    assert len(hits) == 1
    h = hits[0]
    assert h["source_id"] == "CORE:42" and h["database"] == "core" and h["type"] == "report"
    assert "40%" in h["abstract"] and h["doi"] == "10.5/core" and h["year"] == "2023"
    assert registry.SOURCES["core"].available is True


FDA_ROWS = [
    {
        "title": '<a href="/regulatory-information/search-fda-guidance-documents/conducting-dct">'
        "Conducting Clinical Trials With Decentralized Elements</a>",
        "field_issue_datetime": "09/17/2024",
        "field_center": "Center for Drug Evaluation and Research",
        "field_final_guidance_1": "Final",
        "topics-product": "Clinical - Medical",
        "field_topics": "",
        "field_regulated_product_field": "Drugs, Biologics",
        "field_communication_type": "Guidance Document",
    },
    {
        "title": '<a href="/x/eggs">Egg labeling</a>',
        "field_center": "Human Foods Program",
        "field_final_guidance_1": "Final",
    },
]
EMA_PAYLOAD = {
    "data": [
        {
            "id": "100",
            "name": "Reflection paper on AI in the medicinal product lifecycle",
            "type": "scientific-guideline",
            "status": "adopted",
            "first_published_date": "2024-09-09T00:00:00Z",
            "reference_number": "EMA/CHMP/1/2024",
            "document_url": "https://www.ema.europa.eu/doc100.pdf",
        },
        {"id": "101", "name": "Committee agenda", "type": "agenda"},
    ]
}


def test_guidance_parsers_keep_relevant_documents():
    from impactpilot.jobs.refresh_guidance import load_ich, parse_ema, parse_fda

    fda = parse_fda(FDA_ROWS)
    assert len(fda) == 1
    assert fda[0]["id"] == "FDAG:conducting-dct" and fda[0]["status"] == "Final" and fda[0]["issued"] == "2024"
    assert fda[0]["url"].startswith("https://www.fda.gov/regulatory-information/")

    ema = parse_ema(EMA_PAYLOAD)
    assert [e["id"] for e in ema] == ["EMA:100"]
    assert "scientific guideline" in ema[0]["summary"] and ema[0]["issued"] == "2024"

    ich = load_ich()
    assert len(ich) > 60
    e6 = next(g for g in ich if g["id"] == "ICH:E6(R3)")
    assert "Good Clinical Practice" in e6["title"] and e6["url"].endswith("efficacy-guidelines")


def test_guidance_index_search_and_isolated_refresh(tmp_path, monkeypatch):
    from impactpilot.jobs import refresh_guidance as job
    from impactpilot.services import guidance_index

    db = tmp_path / "guidance.db"
    monkeypatch.setenv("IMPACTPILOT_GUIDANCE_DB", str(db))
    with pytest.raises(RuntimeError, match="refresh_guidance"):
        guidance_index.search_guidance("decentralized trials")
    assert guidance_index.is_stale()

    def ema_down():
        raise RuntimeError("EMA unreachable")

    monkeypatch.setattr(
        job, "FETCHERS", {"FDA": lambda: job.parse_fda(FDA_ROWS), "EMA": ema_down, "ICH": job.load_ich}
    )
    result = job.refresh()
    assert result["FDA"] == 1 and result["ICH"] > 60 and str(result["EMA"]).startswith("error")

    hits = guidance_index.search_guidance("decentralized clinical trials")
    assert hits[0]["source_id"] == "FDAG:conducting-dct"
    assert hits[0]["database"] == "guidance" and hits[0]["type"] == "guidance"
    assert hits[0]["venue"] == "FDA guidance · Final"
    gcp = guidance_index.search_guidance("good clinical practice monitoring")
    assert any(h["source_id"] == "ICH:E6(R3)" for h in gcp)

    # A later EMA success adds EMA without touching FDA.
    monkeypatch.setattr(job, "FETCHERS", {"EMA": lambda: job.parse_ema(EMA_PAYLOAD)})
    job.refresh()
    assert guidance_index.status()["agencies"] == {"FDA": 1, "EMA": 1, "ICH": result["ICH"]}
    assert registry.database_for_id("EMA:100") == "guidance"


def test_autorefresh_is_disabled_in_tests():
    from impactpilot.jobs.refresh_guidance import refresh_in_background_if_stale

    assert refresh_in_background_if_stale() is False


def test_openfda_devices_and_enforcement(monkeypatch):
    from impactpilot.services import openfda

    seen: list[tuple[str, dict]] = []
    payloads = {
        "device/510k": [
            {
                "k_number": "K201",
                "device_name": "AI SPINE ANALYZER",
                "decision_description": "Substantially Equivalent",
                "decision_date": "2021-03-04",
                "applicant": "Medco",
                "product_code": "LLZ",
                "advisory_committee_description": "Radiology",
                "clearance_type": "Traditional",
            }
        ],
        "device/classification": [
            {
                "product_code": "QIH",
                "device_name": "Radiological computer aided triage software",
                "device_class": "2",
                "medical_specialty_description": "Radiology",
                "regulation_number": "892.2080",
                "definition": "Software that flags suspected findings for prioritised review.",
            }
        ],
        "drug/enforcement": [
            {
                "recall_number": "D-1",
                "product_description": "Tablets 10 mg",
                "reason_for_recall": "Failed dissolution",
                "classification": "Class II",
                "status": "Ongoing",
                "recalling_firm": "Pharma Co",
                "product_type": "Drugs",
                "report_date": "20240101",
            }
        ],
        "device/enforcement": [],
    }

    def fake_get(url, params, **_kw):
        endpoint = url.split("api.fda.gov/", 1)[1].removesuffix(".json")
        seen.append((endpoint, params))
        if not payloads.get(endpoint):
            return Response({}, status_code=404)
        return Response({"results": payloads[endpoint]})

    monkeypatch.setattr("impactpilot.services.openfda.requests.get", fake_get)
    monkeypatch.setenv("OPENFDA_API_KEY", "fda-key")

    devices = openfda.search_openfda_devices("triage software")
    assert [d["source_id"] for d in devices] == ["FDADEV:K201", "FDADEV:class-QIH"]
    assert devices[0]["database"] == "openfda_devices" and devices[0]["year"] == "2021"
    assert "Substantially Equivalent" in devices[0]["abstract"] and "pmn.cfm?ID=K201" in devices[0]["url"]
    assert "21 CFR 892.2080" in devices[1]["abstract"]

    recalls = openfda.search_openfda_enforcement("tablets")
    assert [r["source_id"] for r in recalls] == ["FDAREC:D-1"]
    assert recalls[0]["type"] == "recall" and "Failed dissolution" in recalls[0]["abstract"]
    assert all(p.get("api_key") == "fda-key" for _, p in seen)
    assert registry.database_for_id("FDAREC:D-1") == "openfda_enforcement"
    assert registry.database_for_id("FDA:abc") == "openfda"


ISRCTN_XML = """<allTrials totalCount="1" xmlns="http://www.67bricks.com/isrctn"><fullTrial>
  <trial><isrctn>16126004</isrctn>
    <trialDescription><title>Decentralised trial of an AI tool</title>
      <plainEnglishSummary>Background. Aim is to reduce non-use by 25%.</plainEnglishSummary></trialDescription>
    <externalRefs><doi>10.1186/ISRCTN16126004</doi></externalRefs>
    <participants><recruitmentStart>2026-11-23T00:00:00.000Z</recruitmentStart></participants>
  </trial>
  <sponsor><organisation>NHS Trust</organisation></sponsor>
</fullTrial></allTrials>"""


def test_isrctn_parses_xml(monkeypatch):
    from impactpilot.services.isrctn import search_isrctn

    monkeypatch.setattr(
        "impactpilot.services.isrctn.requests.get", lambda *_a, **_k: Response(text=ISRCTN_XML)
    )
    h = search_isrctn("decentralised")[0]
    assert h["source_id"] == "ISRCTN:16126004" and h["database"] == "isrctn" and h["type"] == "trial"
    assert h["year"] == "2026" and h["venue"] == "NHS Trust" and "25%" in h["abstract"]
    assert h["doi"] == "10.1186/ISRCTN16126004" and h["url"].endswith("ISRCTN16126004")


def test_ctis_parses_and_disables_itself_on_schema_change(monkeypatch):
    from impactpilot.services import ctis

    ctis.reset()
    good = {
        "data": [
            {
                "ctNumber": "2022-500449-26-00",
                "ctTitle": "Decentralised vs conventional trial approaches in type 2 diabetes",
                "trialPhase": "Therapeutic use (Phase IV)",
                "conditions": "Type 2 diabetes mellitus",
                "primaryEndPoint": "Time to enrolment from site activation",
                "sponsor": "UMC Utrecht",
                "startDateEU": "03/08/2023",
                "resultsFirstReceived": "Yes",
            }
        ]
    }
    responses = iter([Response(good), Response({"unexpected": True})])
    calls = []

    def fake_post(*_a, **_k):
        calls.append(1)
        return next(responses)

    monkeypatch.setattr("impactpilot.services.ctis.requests.post", fake_post)
    h = ctis.search_ctis("decentralised")[0]
    assert h["source_id"] == "EUCT:2022-500449-26-00" and h["database"] == "ctis" and h["year"] == "2023"
    assert h["abstract"].startswith("Therapeutic use (Phase IV) trial in Type 2 diabetes mellitus.")
    assert "Results have been posted" in h["abstract"]

    with pytest.raises(RuntimeError, match="unexpected response format"):
        ctis.search_ctis("decentralised")
    with pytest.raises(RuntimeError, match="disabled"):
        ctis.search_ctis("decentralised")
    assert len(calls) == 2
    ctis.reset()


def _clear_web_keys(monkeypatch):
    for k in ("WEB_SEARCH_PROVIDER", "TAVILY_API_KEY", "BRAVE_SEARCH_API_KEY"):
        monkeypatch.delenv(k, raising=False)


def test_web_search_tavily_restricts_to_allowlist(monkeypatch):
    from impactpilot.services import web_search

    _clear_web_keys(monkeypatch)
    assert registry.SOURCES["web"].available is False
    with pytest.raises(RuntimeError, match="TAVILY_API_KEY"):
        web_search.search_web("decentralised trials")

    seen = {}

    def fake_post(_url, json, headers, **_kw):
        seen.update(json=json, headers=headers)
        return Response(
            {
                "results": [
                    {
                        "title": "Decentralised trials white paper",
                        "url": "https://www.ctti-clinicaltrials.org/dct-report.pdf",
                        "content": "Sponsors reported 20% faster enrolment.",
                        "published_date": "2023-04-02",
                    },
                    {"title": "Blog", "url": "https://random-blog.example/post", "content": "Opinion."},
                ]
            }
        )

    monkeypatch.setattr("impactpilot.services.web_search.requests.post", fake_post)
    monkeypatch.setenv("TAVILY_API_KEY", "tv")
    assert registry.SOURCES["web"].available is True
    hits = web_search.search_web("decentralised trials")
    assert seen["headers"]["Authorization"] == "Bearer tv"
    assert "ctti-clinicaltrials.org" in seen["json"]["include_domains"]
    assert seen["json"]["query"].endswith("white paper OR report")
    assert len(hits) == 1
    h = hits[0]
    assert h["source_id"].startswith("WEB:") and h["database"] == "web" and h["type"] == "report"
    assert h["venue"] == "ctti-clinicaltrials.org" and h["year"] == "2023"


def test_web_search_brave_filters_by_domain(monkeypatch):
    from impactpilot.services import web_search

    _clear_web_keys(monkeypatch)
    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "brave")
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "bk")
    payload = {
        "web": {
            "results": [
                {"title": "Off list", "url": "https://example.com/a", "description": "x"},
                {
                    "title": "<strong>CSDD</strong> impact report",
                    "url": "https://csdd.tufts.edu/impact-reports",
                    "description": "Cycle times fell.",
                    "extra_snippets": ["Median 30 days."],
                    "page_age": "2022-01-01T00:00:00",
                },
            ]
        }
    }
    seen = {}

    def fake_get(_url, params, headers, **_kw):
        seen.update(params=params, headers=headers)
        return Response(payload)

    monkeypatch.setattr("impactpilot.services.web_search.requests.get", fake_get)
    hits = web_search.search_web("cycle time")
    assert seen["headers"]["X-Subscription-Token"] == "bk"
    assert [h["venue"] for h in hits] == ["csdd.tufts.edu"]
    assert hits[0]["title"] == "CSDD impact report" and "30 days" in hits[0]["abstract"]

    monkeypatch.setenv("WEB_SEARCH_PROVIDER", "tavily")
    with pytest.raises(RuntimeError, match="tavily"):
        web_search.search_web("cycle time")


def test_openaire_parses_research_products(monkeypatch):
    from impactpilot.services.openaire import search_openaire

    payload = {
        "results": [
            {
                "id": "doi_::abc",
                "mainTitle": "Remote monitoring in trials",
                "descriptions": ["<jats:p>Monitoring visits fell by 30% &amp; costs dropped.</jats:p>"],
                "publicationDate": "2022-05-01",
                "type": "publication",
                "pids": [{"scheme": "doi", "value": "10.9/oa"}],
                "instances": [{"type": "Report", "urls": ["https://repo.example/1"]}],
                "container": {"name": "Repository"},
            }
        ]
    }
    monkeypatch.setattr("impactpilot.services.openaire.requests.get", lambda *_a, **_k: Response(payload))
    h = search_openaire("monitoring")[0]
    assert h["source_id"] == "OAIRE:doi_::abc" and h["database"] == "openaire"
    assert h["abstract"] == "Monitoring visits fell by 30% & costs dropped."
    assert h["type"] == "report" and h["doi"] == "10.9/oa" and h["year"] == "2022"
    assert h["url"] == "https://repo.example/1"
