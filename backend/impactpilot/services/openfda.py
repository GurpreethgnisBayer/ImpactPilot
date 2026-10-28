"""openFDA search: drug labels, device clearances and classifications, and recalls/enforcement.

OPENFDA_API_KEY is optional; it raises the daily request limit.
"""

from __future__ import annotations

import os
import re
from typing import Any

import requests

OPENFDA_BASE = "https://api.fda.gov"
OPENFDA_URL = f"{OPENFDA_BASE}/drug/label.json"
_MAX = 8


def _first(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def _clip(text: str, limit: int = 700) -> str:
    return " ".join((text or "").split())[:limit]


def _clean_query(query: str) -> str:
    return " ".join(re.sub(r"[^\w\s\-]", " ", query or "").split())


def _get(endpoint: str, query: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    """`endpoint` is e.g. "drug/label" or "device/510k". A 404 means no matches."""
    params: dict[str, Any] = {"search": query, "limit": max(1, min(limit, _MAX))}
    key = os.environ.get("OPENFDA_API_KEY", "").strip()
    if key:
        params["api_key"] = key
    r = requests.get(f"{OPENFDA_BASE}/{endpoint}.json", params=params, timeout=timeout)
    if r.status_code == 404:
        return []
    if r.status_code == 429:
        raise RuntimeError("openFDA rate limited (HTTP 429). Set OPENFDA_API_KEY to raise the limit.")
    r.raise_for_status()
    return r.json().get("results") or []


def _api_url(endpoint: str, field: str, value: str) -> str:
    return f"{OPENFDA_BASE}/{endpoint}.json?search={field}:%22{value}%22"


def search_openfda(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    """Drug labels."""
    q = _clean_query(query)
    if not q:
        return []
    out: list[dict[str, Any]] = []
    for label in _get("drug/label", q, max_results, timeout):
        openfda = label.get("openfda") or {}
        name = _first(openfda.get("brand_name")) or _first(openfda.get("generic_name")) or "Drug label"
        indications = _clip(_first(label.get("indications_and_usage")))
        studies = _clip(_first(label.get("clinical_studies")), 500)
        parts = [p for p in (indications, studies) if p]
        if not parts:
            continue
        set_id = str(label.get("set_id") or label.get("id") or "").strip()
        if not set_id:
            continue
        effective = str(label.get("effective_time") or "")
        url = (
            f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}"
            if label.get("set_id")
            else _api_url("drug/label", "id", set_id)
        )
        out.append(
            {
                "source_id": f"FDA:{set_id}",
                "database": "openfda",
                "title": name,
                "abstract": " ".join(parts)[:1200],
                "year": effective[:4],
                "venue": _first(openfda.get("manufacturer_name")) or "openFDA",
                "type": "label",
                "url": url,
            }
        )
    return out


def search_openfda_devices(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    """510(k) clearances plus device classifications, split roughly evenly."""
    q = _clean_query(query)
    if not q:
        return []
    half = max(1, max_results // 2)
    out: list[dict[str, Any]] = []
    for row in _get("device/510k", q, max_results - half or 1, timeout):
        k_number = str(row.get("k_number") or "").strip()
        device = _clip(str(row.get("device_name") or ""), 200)
        if not k_number or not device:
            continue
        decision = str(row.get("decision_date") or "")
        panel = row.get("advisory_committee_description") or ""
        abstract = (
            f"510(k) {k_number}: {row.get('decision_description') or 'decision'} on {decision or 'unknown date'} "
            f"for {device}, submitted by {row.get('applicant') or 'unknown applicant'}. "
            f"Product code {row.get('product_code') or '?'}"
            f"{'; review panel ' + panel if panel and panel != 'Unknown' else ''}. "
            f"Clearance type: {row.get('clearance_type') or 'not stated'}."
        )
        out.append(
            {
                "source_id": f"FDADEV:{k_number}",
                "database": "openfda_devices",
                "title": f"510(k) {k_number}: {device.title()}",
                "abstract": abstract,
                "year": decision[:4],
                "venue": str(row.get("applicant") or "FDA CDRH"),
                "type": "device clearance",
                "url": f"https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID={k_number}",
            }
        )
    for row in _get("device/classification", q, half, timeout):
        code = str(row.get("product_code") or "").strip()
        device = _clip(str(row.get("device_name") or ""), 200)
        if not code or not device:
            continue
        definition = _clip(str(row.get("definition") or ""), 800)
        abstract = (
            f"Class {row.get('device_class') or '?'} device, {row.get('medical_specialty_description') or 'specialty not stated'}"
            f"{', regulation 21 CFR ' + str(row['regulation_number']) if row.get('regulation_number') else ''}. "
            f"{definition}"
        ).strip()
        out.append(
            {
                "source_id": f"FDADEV:class-{code}",
                "database": "openfda_devices",
                "title": f"Device classification {code}: {device}",
                "abstract": abstract,
                "year": "",
                "venue": "FDA device classification",
                "type": "device classification",
                "url": _api_url("device/classification", "product_code", code),
            }
        )
    return out


def search_openfda_enforcement(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    """Drug and device recalls (enforcement reports)."""
    q = _clean_query(query)
    if not q:
        return []
    half = max(1, max_results // 2)
    out: list[dict[str, Any]] = []
    for endpoint, n in (("drug/enforcement", max_results - half or 1), ("device/enforcement", half)):
        for row in _get(endpoint, q, n, timeout):
            recall = str(row.get("recall_number") or "").strip()
            product = _clip(str(row.get("product_description") or ""), 400)
            reason = _clip(str(row.get("reason_for_recall") or ""), 500)
            if not recall or not (product or reason):
                continue
            kind = str(row.get("product_type") or endpoint.split("/")[0]).lower()
            abstract = (
                f"{row.get('classification') or 'Unclassified'} {kind} recall ({row.get('status') or 'status unknown'}) "
                f"by {row.get('recalling_firm') or 'unknown firm'}. Reason: {reason or 'not stated'}. Product: {product}"
            )
            out.append(
                {
                    "source_id": f"FDAREC:{recall}",
                    "database": "openfda_enforcement",
                    "title": f"Recall {recall}: {product[:120] or reason[:120]}",
                    "abstract": abstract[:1200],
                    "year": str(row.get("report_date") or "")[:4],
                    "venue": str(row.get("recalling_firm") or "FDA enforcement report"),
                    "type": "recall",
                    "url": _api_url(endpoint, "recall_number", recall),
                }
            )
    return out
