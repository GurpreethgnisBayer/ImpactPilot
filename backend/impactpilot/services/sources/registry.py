"""Registry of every source a brief can search.

Adding a source is one client module plus one `SourceSpec` here. Order matters: it is the
dedupe priority, so a later source's hit is dropped when it repeats an earlier PMID, DOI, or title.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from impactpilot.services import (
    clinicaltrials,
    core_api,
    ctis,
    europepmc,
    guidance_index,
    isrctn,
    openaire,
    openalex,
    openfda,
    pubmed_eutils,
    semantic_scholar,
    web_search,
)

SearchFn = Callable[[str, int], list[dict[str, Any]]]

GROUPS: dict[str, str] = {
    "literature": "Literature",
    "grey": "Grey literature and reports",
    "trials": "Clinical trials",
    "regulatory": "Regulatory",
}


@dataclass(frozen=True)
class SourceSpec:
    key: str
    label: str
    group: str
    search: SearchFn
    # Hits per search. None means the caller's max_per_source (the journal searches).
    cap: int | None = 8
    # The source is unavailable unless at least one of these env vars is set.
    env_keys: tuple[str, ...] = ()
    # Key under compendium["queries"]. OpenAlex keeps "keyword" so saved briefs still render.
    query_key: str = ""
    pubmed_syntax: bool = False
    # Start from the short title-based query instead of the long LLM keyword query. Structured
    # records (guidance titles, labels, registry entries) match poorly on long, wordy queries.
    short_query: bool = False
    default_on: bool = True
    note: str = ""
    # source_id prefixes this source emits (e.g. "NCT"), used to recover `database` from an id.
    id_prefixes: tuple[str, ...] = ()

    @property
    def available(self) -> bool:
        return not self.env_keys or any(os.environ.get(k, "").strip() for k in self.env_keys)

    def public(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "group": self.group,
            "group_label": GROUPS.get(self.group, self.group),
            "available": self.available,
            "needs": "" if self.available else " or ".join(self.env_keys),
            "default_on": self.default_on,
            "note": self.note,
        }


def _pubmed(q: str, n: int) -> list[dict[str, Any]]:
    return pubmed_eutils.search_pubmed(base_query=q, max_results=n, date_preset="10y", has_abstract=True)


def _openalex(q: str, n: int) -> list[dict[str, Any]]:
    return openalex.search_openalex(q, max_results=n)


def _europepmc(q: str, n: int) -> list[dict[str, Any]]:
    return europepmc.search_europepmc(q, max_results=n)


def _semanticscholar(q: str, n: int) -> list[dict[str, Any]]:
    return semantic_scholar.search_semanticscholar(q, max_results=n)


def _core(q: str, n: int) -> list[dict[str, Any]]:
    return core_api.search_core(q, max_results=n)


def _openaire(q: str, n: int) -> list[dict[str, Any]]:
    return openaire.search_openaire(q, max_results=n)


def _clinicaltrials(q: str, n: int) -> list[dict[str, Any]]:
    return clinicaltrials.search_clinicaltrials(q, max_results=n)


def _isrctn(q: str, n: int) -> list[dict[str, Any]]:
    return isrctn.search_isrctn(q, max_results=n)


def _ctis(q: str, n: int) -> list[dict[str, Any]]:
    return ctis.search_ctis(q, max_results=n)


def _openfda(q: str, n: int) -> list[dict[str, Any]]:
    return openfda.search_openfda(q, max_results=n)


def _openfda_devices(q: str, n: int) -> list[dict[str, Any]]:
    return openfda.search_openfda_devices(q, max_results=n)


def _openfda_enforcement(q: str, n: int) -> list[dict[str, Any]]:
    return openfda.search_openfda_enforcement(q, max_results=n)


def _guidance(q: str, n: int) -> list[dict[str, Any]]:
    return guidance_index.search_guidance(q, max_results=n)


def _web(q: str, n: int) -> list[dict[str, Any]]:
    return web_search.search_web(q, max_results=n)


SOURCES: dict[str, SourceSpec] = {
    s.key: s
    for s in (
        SourceSpec(
            "pubmed", "PubMed", "literature", _pubmed, cap=None, pubmed_syntax=True, id_prefixes=("PMID",)
        ),
        SourceSpec(
            "openalex", "OpenAlex", "literature", _openalex, cap=None, query_key="keyword", id_prefixes=("OA",)
        ),
        SourceSpec("europepmc", "Europe PMC", "literature", _europepmc, id_prefixes=("PMC", "EPMC")),
        SourceSpec(
            "semanticscholar",
            "Semantic Scholar",
            "literature",
            _semanticscholar,
            note="Set SEMANTIC_SCHOLAR_API_KEY to avoid rate limits.",
            id_prefixes=("S2",),
        ),
        SourceSpec(
            "core",
            "CORE",
            "grey",
            _core,
            env_keys=("CORE_API_KEY",),
            note="Open-access reports, theses, and repository papers.",
            id_prefixes=("CORE",),
        ),
        SourceSpec(
            "openaire",
            "OpenAIRE",
            "grey",
            _openaire,
            note="Institutional repository outputs, including reports.",
            id_prefixes=("OAIRE",),
        ),
        SourceSpec("clinicaltrials", "ClinicalTrials.gov", "trials", _clinicaltrials, id_prefixes=("NCT",)),
        SourceSpec(
            "isrctn",
            "ISRCTN",
            "trials",
            _isrctn,
            short_query=True,
            note="UK-led and international trials.",
            id_prefixes=("ISRCTN",),
        ),
        SourceSpec(
            "ctis",
            "EU CTIS",
            "trials",
            _ctis,
            short_query=True,
            note="EU trials. Best-effort: uses the public CTIS search, which is not a documented API.",
            id_prefixes=("EUCT",),
        ),
        SourceSpec(
            "guidance",
            "FDA, EMA and ICH guidance",
            "regulatory",
            _guidance,
            short_query=True,
            note="Local index of FDA guidance, EMA guidelines and EPARs, and ICH guidelines; refreshed weekly.",
            id_prefixes=("FDAG", "EMA", "ICH"),
        ),
        SourceSpec(
            "openfda", "openFDA drug labels", "regulatory", _openfda, short_query=True, id_prefixes=("FDA",)
        ),
        SourceSpec(
            "openfda_devices",
            "openFDA devices",
            "regulatory",
            _openfda_devices,
            short_query=True,
            note="510(k) clearances and device classifications.",
            id_prefixes=("FDADEV",),
        ),
        SourceSpec(
            "openfda_enforcement",
            "openFDA recalls",
            "regulatory",
            _openfda_enforcement,
            short_query=True,
            note="Drug and device recalls and enforcement reports.",
            id_prefixes=("FDAREC",),
        ),
        # Last, so any paper or record found elsewhere wins the dedupe.
        SourceSpec(
            "web",
            "Web white papers",
            "grey",
            _web,
            env_keys=("TAVILY_API_KEY", "BRAVE_SEARCH_API_KEY"),
            note="White papers and reports from allowlisted agency, consortium, analyst, and consultancy sites.",
            id_prefixes=("WEB",),
        ),
    )
}


def get(key: str) -> SourceSpec | None:
    return SOURCES.get(key)


def default_keys() -> list[str]:
    return [k for k, s in SOURCES.items() if s.default_on and s.available]


def group_of(database: str | None) -> str:
    spec = SOURCES.get(database or "")
    return spec.group if spec else "literature"


def database_for_id(source_id: str) -> str:
    prefix = source_id.split(":", 1)[0].upper()
    for spec in SOURCES.values():
        if prefix in spec.id_prefixes:
            return spec.key
    return "openalex"
