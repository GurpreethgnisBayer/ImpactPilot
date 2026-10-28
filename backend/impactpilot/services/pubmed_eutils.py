"""NCBI E-utilities client for PubMed (esearch + efetch)."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlencode

import requests

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def build_term(
    base_query: str,
    journal: str = "",
    author: str = "",
    language: str = "",
    has_abstract: bool = False,
    publication_types: str = "",
    field_restriction: str = "all",
) -> str:
    """
    Combine a free-text base query with optional PubMed-style qualifiers using AND.
    field_restriction: all | title | title_abstract
    publication_types: comma-separated publication type labels (e.g. "Review,Clinical Trial").
    """
    base = base_query.strip()
    parts: list[str] = []

    if base:
        if field_restriction == "title":
            parts.append(f"({base})[ti]")
        elif field_restriction == "title_abstract":
            parts.append(f"({base})[tiab]")
        else:
            parts.append(f"({base})")

    j = journal.strip()
    if j:
        parts.append(f'({j})[ta]')

    a = author.strip()
    if a:
        parts.append(f"({a})[au]")

    lang = language.strip()
    if lang:
        parts.append(f"({lang})[la]")

    if has_abstract:
        parts.append("hasabstract")

    pt = publication_types.strip()
    if pt:
        for chunk in pt.split(","):
            label = chunk.strip()
            if label:
                parts.append(f'({label})[Publication Type]')

    return " AND ".join(parts) if parts else "(research)"


def esearch(
    term: str,
    retmax: int,
    sort: str,
    *,
    mindate: str | None = None,
    maxdate: str | None = None,
    reldate: int | None = None,
    datetype: str = "pdat",
    timeout: int = 60,
) -> list[str]:
    """
    Run esearch on PubMed; return list of PMIDs (may be shorter than retmax).
    Use either (mindate, maxdate) or reldate with datetype=pdat.
    """
    params: dict[str, Any] = {
        "db": "pubmed",
        "term": term,
        "retmax": str(max(1, min(retmax, 10000))),
        "retmode": "json",
        "datetype": datetype,
        "tool": os.environ.get("IMPACTPILOT_NCBI_TOOL", "impactpilot"),
        "email": os.environ.get("IMPACTPILOT_NCBI_EMAIL", "impactpilot@example.com"),
    }
    if sort == "pub_date":
        params["sort"] = "pub+date"
    else:
        params["sort"] = "relevance"

    if reldate is not None:
        params["reldate"] = str(reldate)
    elif mindate and maxdate:
        params["mindate"] = mindate
        params["maxdate"] = maxdate

    url = f"{EUTILS_BASE}/esearch.fcgi?{urlencode(params)}"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    idlist = data.get("esearchresult", {}).get("idlist", [])
    return [str(x) for x in idlist]


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    parts: list[str] = []
    if el.text:
        parts.append(el.text)
    for child in el:
        parts.append(_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts).strip()


def _find_child(parent: ET.Element, name: str) -> ET.Element | None:
    for ch in parent:
        if _strip_ns(ch.tag) == name:
            return ch
    return None


def _find_all(parent: ET.Element, name: str) -> list[ET.Element]:
    return [ch for ch in parent if _strip_ns(ch.tag) == name]


def efetch(pmids: list[str], timeout: int = 120) -> list[dict[str, Any]]:
    """Fetch PubMed records by PMID; return structured dicts."""
    if not pmids:
        return []

    out: list[dict[str, Any]] = []
    batch_size = 200
    for i in range(0, len(pmids), batch_size):
        chunk = pmids[i : i + batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(chunk),
            "retmode": "xml",
            "tool": os.environ.get("IMPACTPILOT_NCBI_TOOL", "impactpilot"),
            "email": os.environ.get("IMPACTPILOT_NCBI_EMAIL", "impactpilot@example.com"),
        }
        url = f"{EUTILS_BASE}/efetch.fcgi?{urlencode(params)}"
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        root = ET.fromstring(r.content)

        for article in root.iter():
            if _strip_ns(article.tag) != "PubmedArticle":
                continue
            medline = _find_child(article, "MedlineCitation")
            if medline is None:
                continue
            pmid_el = _find_child(medline, "PMID")
            pmid = _text(pmid_el) if pmid_el is not None else ""
            article_el = _find_child(medline, "Article")
            if article_el is None:
                continue
            title_el = _find_child(article_el, "ArticleTitle")
            title = _text(title_el)

            abstract_parts: list[str] = []
            abstract_el = _find_child(article_el, "Abstract")
            if abstract_el is not None:
                for ab in _find_all(abstract_el, "AbstractText"):
                    abstract_parts.append(_text(ab))
            abstract = "\n".join(p for p in abstract_parts if p)

            journal_title = ""
            year = ""
            journal_el = _find_child(article_el, "Journal")
            if journal_el is not None:
                jt = _find_child(journal_el, "Title")
                iso = _find_child(journal_el, "ISOAbbreviation")
                journal_title = _text(iso) or _text(jt)
                ji = _find_child(journal_el, "JournalIssue")
                if ji is not None:
                    pd = _find_child(ji, "PubDate")
                    if pd is not None:
                        y = _find_child(pd, "Year")
                        med = _find_child(pd, "MedlineDate")
                        year = _text(y) or (_text(med).split()[0] if _text(med) else "")

            authors: list[str] = []
            alist = _find_child(article_el, "AuthorList")
            if alist is not None:
                for auth in _find_all(alist, "Author"):
                    coll = _find_child(auth, "CollectiveName")
                    if coll is not None:
                        authors.append(_text(coll))
                        continue
                    ln = _find_child(auth, "LastName")
                    fn = _find_child(auth, "ForeName")
                    initials = _find_child(auth, "Initials")
                    name = " ".join(
                        p
                        for p in (_text(fn), _text(initials), _text(ln))
                        if p
                    ).strip()
                    if not name:
                        name = _text(ln)
                    if name:
                        authors.append(name)

            url_pubmed = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
            out.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "journal": journal_title,
                    "year": year,
                    "authors": authors,
                    "url": url_pubmed,
                }
            )

    # Preserve input PMID order (efetch order may differ)
    by_pmid = {d["pmid"]: d for d in out}
    ordered: list[dict[str, Any]] = []
    for pid in pmids:
        row = by_pmid.get(pid)
        if row:
            ordered.append(row)
    return ordered


def search_pubmed(
    *,
    base_query: str,
    journal: str = "",
    author: str = "",
    language: str = "",
    has_abstract: bool = False,
    publication_types: str = "",
    field_restriction: str = "all",
    max_results: int = 25,
    sort: str = "relevance",
    date_preset: str = "5y",
    custom_mindate: str = "",
    custom_maxdate: str = "",
    timeout: int = 60,
) -> list[dict[str, Any]]:
    """
    build_term -> esearch -> efetch; return list of article dicts.
    date_preset: 2y | 5y | 10y | custom | any
    sort: relevance | pub_date
    """
    term = build_term(
        base_query,
        journal=journal,
        author=author,
        language=language,
        has_abstract=has_abstract,
        publication_types=publication_types,
        field_restriction=field_restriction,
    )

    reldate: int | None = None
    mindate: str | None = None
    maxdate: str | None = None

    if date_preset == "2y":
        reldate = 730
    elif date_preset == "5y":
        reldate = 1825
    elif date_preset == "10y":
        reldate = 3650
    elif date_preset == "custom" and custom_mindate.strip() and custom_maxdate.strip():
        mindate = custom_mindate.strip().replace("-", "/")
        maxdate = custom_maxdate.strip().replace("-", "/")
    # any: no date filter

    pmids = esearch(
        term,
        retmax=max_results,
        sort=sort,
        mindate=mindate,
        maxdate=maxdate,
        reldate=reldate,
        datetype="pdat",
        timeout=timeout,
    )
    return efetch(pmids, timeout=timeout)
