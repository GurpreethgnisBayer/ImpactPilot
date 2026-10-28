"""Local full-text index of regulatory guidance (FDA guidance, EMA guidelines/EPARs, ICH).

These agencies have no live search API, so `impactpilot.jobs.refresh_guidance` downloads their
public listings into a small SQLite FTS5 database and briefs search it locally.
"""

from __future__ import annotations

import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

STALE_AFTER = timedelta(days=7)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS guidance_docs (
    id TEXT PRIMARY KEY,
    agency TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    topic TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    issued TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT ''
);
CREATE VIRTUAL TABLE IF NOT EXISTS guidance_fts USING fts5(
    title, summary, topic, content='guidance_docs', content_rowid='rowid'
);
CREATE TABLE IF NOT EXISTS guidance_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

_AGENCY_LABEL = {"FDA": "FDA guidance", "EMA": "EMA", "ICH": "ICH guideline"}
_STOP = frozenset(
    {
        "and", "for", "the", "with", "from", "into", "using", "based", "via", "of", "in", "on",
        # Present in thousands of guidance titles; they drown out the distinctive terms.
        "phase", "iii", "clinical", "trial", "trials", "study", "studies", "drug", "drugs", "guidance",
        "goal", "faster", "lower", "fewer", "less", "reduce", "reduced", "improve", "better",
    }
)


def index_path() -> Path:
    env = os.environ.get("IMPACTPILOT_GUIDANCE_DB")
    if env:
        return Path(env)
    data_dir = Path(__file__).resolve().parents[3] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "guidance_index.db"


def connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path or index_path()))
    conn.executescript(_SCHEMA)
    return conn


def replace_agency(conn: sqlite3.Connection, agency: str, rows: list[dict[str, str]]) -> int:
    """Swap one agency's documents for a fresh download, leaving the other agencies untouched."""
    with conn:
        conn.execute("DELETE FROM guidance_docs WHERE agency = ?", (agency,))
        conn.executemany(
            "INSERT OR REPLACE INTO guidance_docs (id, agency, title, summary, topic, status, issued, url) "
            "VALUES (:id, :agency, :title, :summary, :topic, :status, :issued, :url)",
            [{"summary": "", "topic": "", "status": "", "issued": "", "url": "", **r, "agency": agency} for r in rows],
        )
        conn.execute("INSERT INTO guidance_fts(guidance_fts) VALUES ('rebuild')")
        conn.execute(
            "INSERT OR REPLACE INTO guidance_meta (key, value) VALUES (?, ?)",
            (f"refreshed:{agency}", datetime.now(timezone.utc).isoformat()),
        )
    return len(rows)


def status(path: Path | None = None) -> dict[str, Any]:
    p = path or index_path()
    if not p.exists():
        return {"documents": 0, "agencies": {}, "refreshed": {}}
    with closing(connect(p)) as conn:
        counts = dict(conn.execute("SELECT agency, COUNT(*) FROM guidance_docs GROUP BY agency").fetchall())
        refreshed = {
            k.split(":", 1)[1]: v
            for k, v in conn.execute("SELECT key, value FROM guidance_meta WHERE key LIKE 'refreshed:%'")
        }
    return {"documents": sum(counts.values()), "agencies": counts, "refreshed": refreshed}


def is_stale(path: Path | None = None) -> bool:
    info = status(path)
    if not info["documents"] or not info["refreshed"]:
        return True
    oldest = min(datetime.fromisoformat(v) for v in info["refreshed"].values())
    return datetime.now(timezone.utc) - oldest > STALE_AFTER


def _fts_term(word: str) -> str:
    """Long words become prefix queries so spelling and inflection variants match
    (decentralised/decentralized, enrolment/enrollment, nursing/nurse)."""
    if len(word) >= 7:
        return f'"{word[: max(5, len(word) - 3)]}"*'
    return f'"{word}"'


def _fts_query(query: str) -> str:
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", query or "") if len(w) > 2]
    words = [w for w in dict.fromkeys(words) if w not in _STOP]
    return " OR ".join(_fts_term(w) for w in words[:10])


def search_guidance(
    query: str, *, max_results: int = 8, path: Path | None = None
) -> list[dict[str, Any]]:
    """BM25-ranked search over title (weighted highest), summary, and topic."""
    match = _fts_query(query)
    if not match:
        return []
    p = path or index_path()
    if not p.exists() or not status(p)["documents"]:
        raise RuntimeError(
            "Guidance index is empty. Run `python -m impactpilot.jobs.refresh_guidance` on the server."
        )
    with closing(connect(p)) as conn:
        rows = conn.execute(
            "SELECT d.id, d.agency, d.title, d.summary, d.topic, d.status, d.issued, d.url "
            "FROM guidance_fts JOIN guidance_docs d ON d.rowid = guidance_fts.rowid "
            "WHERE guidance_fts MATCH ? ORDER BY bm25(guidance_fts, 10.0, 1.0, 2.0) LIMIT ?",
            (match, max(1, max_results)),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for doc_id, agency, title, summary, topic, doc_status, issued, url in rows:
        out.append(
            {
                "source_id": doc_id,
                "database": "guidance",
                "title": title,
                "abstract": summary or title,
                "year": issued[:4],
                "venue": " · ".join(x for x in (_AGENCY_LABEL.get(agency, agency), doc_status) if x),
                "type": "guidance",
                "url": url,
            }
        )
    return out
