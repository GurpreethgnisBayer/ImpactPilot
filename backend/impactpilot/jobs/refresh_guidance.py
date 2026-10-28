"""Download public guidance listings into the local guidance index.

    python -m impactpilot.jobs.refresh_guidance            # refresh all agencies
    python -m impactpilot.jobs.refresh_guidance --only ich # one agency

Each agency is replaced only when its own download succeeds, so one failing feed never
empties the others.
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import re
import threading
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import Any

import requests

from impactpilot.config_loader import _default_config_dir
from impactpilot.services import guidance_index

log = logging.getLogger(__name__)

FDA_GUIDANCE_URL = "https://www.fda.gov/files/api/datatables/static/search-for-guidance.json"
EMA_DOCUMENTS_URL = "https://www.ema.europa.eu/en/documents/report/documents-output-json-report_en.json"
# fda.gov rejects requests without a browser-like user agent.
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ImpactPilot guidance index)"}

# Food, veterinary, and tobacco guidance is outside R&D productivity questions.
_FDA_SKIP_CENTERS = {"Human Foods Program", "Center for Veterinary Medicine", "Center for Tobacco Products"}

# EMA document types worth citing: guidelines, reflection/committee reports, and EPAR material.
_EMA_TYPES = {
    "scientific-guideline": "Scientific guideline",
    "regulatory-procedural-guideline": "Regulatory and procedural guideline",
    "report": "Report",
    "committee-report": "Committee report",
    "public-statement": "Public statement",
    "assessment-report": "EPAR assessment report",
    "overview": "EPAR overview",
}


def _text(value: Any) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", str(value or ""))).split())


def _href(value: Any) -> str:
    m = re.search(r'href="([^"]+)"', str(value or ""))
    return m.group(1) if m else ""


def parse_fda(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        center = _text(row.get("field_center"))
        if center in _FDA_SKIP_CENTERS:
            continue
        title = _text(row.get("title"))
        href = _href(row.get("title"))
        if not title or not href:
            continue
        slug = href.rstrip("/").rsplit("/", 1)[-1]
        issued = _text(row.get("field_issue_datetime"))  # MM/DD/YYYY
        year = issued[-4:] if re.fullmatch(r"\d{2}/\d{2}/\d{4}", issued) else ""
        status = _text(row.get("field_final_guidance_1"))
        topics = ", ".join(
            t
            for t in dict.fromkeys(
                _text(row.get(k)) for k in ("topics-product", "field_topics", "field_regulated_product_field")
            )
            if t
        )
        kind = _text(row.get("field_communication_type")) or "Guidance"
        summary = f"FDA {kind.lower()} ({status or 'status unknown'}{', ' + year if year else ''}) from {center or 'FDA'}."
        if topics:
            summary += f" Topics: {topics}."
        out.append(
            {
                "id": f"FDAG:{slug}",
                "title": title,
                "summary": summary,
                "topic": topics,
                "status": status,
                "issued": year,
                "url": f"https://www.fda.gov{href}" if href.startswith("/") else href,
            }
        )
    return out


def parse_ema(payload: Any) -> list[dict[str, str]]:
    rows = payload.get("data") if isinstance(payload, dict) else payload
    out: list[dict[str, str]] = []
    for row in rows or []:
        kind = _EMA_TYPES.get(str(row.get("type") or ""))
        title = _text(row.get("name"))
        doc_id = str(row.get("id") or "").strip()
        if not kind or not title or not doc_id:
            continue
        medicine = _text(row.get("medicine_name"))
        status = _text(row.get("status"))
        status = "" if status == "unknown" else status
        published = str(row.get("first_published_date") or "")
        summary = f"EMA {kind.lower()}"
        if medicine:
            summary += f" for {medicine}"
        if status:
            summary += f" ({status})"
        if published[:4]:
            summary += f", first published {published[:4]}"
        ref = _text(row.get("reference_number"))
        summary += f". Reference {ref}." if ref else "."
        out.append(
            {
                "id": f"EMA:{doc_id}",
                "title": title,
                "summary": summary,
                "topic": " ".join(x for x in (kind, medicine) if x),
                "status": status,
                "issued": published[:4],
                "url": str(row.get("document_url") or ""),
            }
        )
    return out


def parse_ich(data: dict[str, Any]) -> list[dict[str, str]]:
    urls = data.get("series_urls") or {}
    series_names = {"E": "efficacy", "Q": "quality", "S": "safety", "M": "multidisciplinary"}
    out: list[dict[str, str]] = []
    for g in data.get("guidelines") or []:
        code = str(g.get("code") or "").strip()
        title = str(g.get("title") or "").strip()
        if not code or not title:
            continue
        series = code[0]
        out.append(
            {
                "id": f"ICH:{code}",
                "title": f"ICH {code}: {title}",
                "summary": f"ICH {series_names.get(series, '')} guideline {code}. {g.get('summary') or ''}".strip(),
                "topic": f"ICH {series_names.get(series, '')}",
                "status": "",
                "issued": "",
                "url": str(urls.get(series) or "https://www.ich.org/page/ich-guidelines"),
            }
        )
    return out


def fetch_fda(timeout: int = 60) -> list[dict[str, str]]:
    r = requests.get(FDA_GUIDANCE_URL, headers=_HEADERS, timeout=timeout)
    r.raise_for_status()
    return parse_fda(r.json())


def fetch_ema(timeout: int = 180) -> list[dict[str, str]]:
    r = requests.get(EMA_DOCUMENTS_URL, headers=_HEADERS, timeout=timeout)
    r.raise_for_status()
    return parse_ema(r.json())


_REPO_CONFIG = Path(__file__).resolve().parents[3] / "config"


def load_ich(path: Path | None = None) -> list[dict[str, str]]:
    p = path or (_default_config_dir() / "ich_guidelines.json")
    if not p.exists():
        p = _REPO_CONFIG / "ich_guidelines.json"
    return parse_ich(json.loads(p.read_text(encoding="utf-8")))


FETCHERS: dict[str, Callable[[], list[dict[str, str]]]] = {"FDA": fetch_fda, "EMA": fetch_ema, "ICH": load_ich}


def refresh(only: list[str] | None = None, path: Path | None = None) -> dict[str, Any]:
    """Returns {agency: document count} for successes and {agency: "error: ..."} for failures."""
    result: dict[str, Any] = {}
    with closing(guidance_index.connect(path)) as conn:
        for agency, fetch in FETCHERS.items():
            if only and agency.lower() not in {o.lower() for o in only}:
                continue
            try:
                rows = fetch()
                if not rows:
                    raise RuntimeError("feed returned no documents")
                result[agency] = guidance_index.replace_agency(conn, agency, rows)
            except Exception as exc:  # noqa: BLE001
                log.warning("Guidance refresh failed for %s: %s", agency, exc)
                result[agency] = f"error: {exc}"
    return result


_refresh_lock = threading.Lock()


def refresh_in_background_if_stale() -> bool:
    """Called at startup. Skipped when IMPACTPILOT_GUIDANCE_AUTOREFRESH=0 (tests, offline servers)."""
    if os.environ.get("IMPACTPILOT_GUIDANCE_AUTOREFRESH", "1") == "0" or not guidance_index.is_stale():
        return False

    def _run() -> None:
        if not _refresh_lock.acquire(blocking=False):
            return
        try:
            log.info("Guidance index refreshed: %s", refresh())
        finally:
            _refresh_lock.release()

    threading.Thread(target=_run, name="guidance-refresh", daemon=True).start()
    return True


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Refresh the local regulatory guidance index.")
    parser.add_argument("--only", nargs="*", help="Agencies to refresh: fda ema ich")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(refresh(args.only), indent=2))
    print(json.dumps(guidance_index.status(), indent=2))


if __name__ == "__main__":
    main()
