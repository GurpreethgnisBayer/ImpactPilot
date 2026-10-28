"""Impact compendium: simple idea in, literature search + LLM synthesis out."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timezone
from typing import Any

from impactpilot.config_loader import get_config
from impactpilot.domain.models import (
    Cadence,
    Confidence,
    DimensionEstimate,
    Direction,
    EvidenceItem,
    EvidenceKind,
    InitiativeRecord,
    KpiPlan,
    MaturityTier,
    RangeValue,
    ValueSource,
)
from impactpilot.domain.quality import check_statement
from impactpilot.domain.scoring import build_scorecard, suggest_impact_score
from impactpilot.domain.statement import build_impact_statement
from impactpilot.services.evidence_numbers import extract_numeric_evidence
from impactpilot.services.llm_allowlist import assert_host_allowed
from impactpilot.services.llm_health import validate_llm_settings
from impactpilot.services.llm_provider import build_provider
from impactpilot.services.query_suggest import suggest_pubmed_query
from impactpilot.services.sources import registry

GenerateFn = Callable[[str], str]

QUERY_PROMPT = """You help R&D teams find evidence for the impact of an initiative.
Write search queries for the idea below.

Title: {title}
Description: {description}

Return ONLY JSON:
{{"pubmed_query": "<PubMed query, 3-6 key concepts joined with AND/OR, no field tags>",
  "keyword_query": "<plain keyword query for a general scholarly search engine>"}}
"""

CURATION_PROMPT = """You help disambiguate which sources actually match an R&D idea, before
anyone estimates impact from it. Sources may be papers, trial records, drug or device records,
regulatory guidance, recalls, or reports.
Keyword search is noisy, so check each candidate carefully.

Idea
Title: {title}
Description: {description}

Candidate sources found by keyword search (some may be about a different technology,
disease area, or process step than the idea describes):
{sources}

For each candidate, decide if it plausibly informs an impact estimate for THIS idea.

Return ONLY JSON:
{{
  "interpretation": "1-2 sentences on how you read this idea, so the user can confirm or correct scope",
  "recommended_ids": ["<source id exactly as shown in brackets>", "..."],
  "notes": {{"<source id>": "one short sentence: why relevant, or why not"}}
}}
"""

# How many candidates the ranking screen and the curation prompt will see.
MAX_MERGED_SOURCES = 30
# Each source group keeps up to this many relevant hits before the rest compete on rank,
# so high-volume journal searches cannot crowd out trials, guidance, and reports.
GROUP_MIN_SHARE = 3
# Wall-clock limit for one source; a slower source becomes a warning.
SOURCE_TIMEOUT_S = 45

SYNTHESIS_PROMPT = """You are an R&D impact analyst writing an evidence-based impact compendium.

Initiative
Title: {title}
Description: {description}
Value-chain phase hint: {phase_hint}

Allowed value-chain phase ids: {phase_ids}
Allowed productivity dimension ids: {dimension_ids}

Sources (cite ONLY these ids):
{sources}

Numbers found in abstracts:
{numbers}

Rules:
- Use only the sources above. Cite them by id, e.g. "PMID:12345" or "OA:W123".
- A source may include "User relevance: high|medium|low". That is the user's judgment, not a keyword score.
  Weight high above medium, and medium above low. Cite higher-ranked sources first.
  A low-ranked source is supporting context only and must not override a higher-ranked source.
  Sources with no relevance line count equally.
- Every quantitative range must say low <= base <= high and be a plausible process-level effect,
  not a portfolio-level number. Prefer ranges reported in the sources.
- When you cite a source for a number, at least one of "low" or "high" must equal a figure that
  source actually reports (from "Numbers found in abstracts" or the abstract text) — not a value
  you invented around it. If a source reports only one figure, use it as "low" or "high" and say
  in the rationale that the other edge and "base" are your estimate, not a reported number.
- If no source supports a number, still give a cautious range but leave citations empty.
- Describe business impact in plain language. Do not make competitiveness claims.
- Suggest maturity: "exploratory" (still testing whether a gain exists), "emerging_local"
  (local effect known), or "mature" (benchmarks/data support a realistic range).

Return ONLY JSON:
{{
  "executive_summary": "3-5 sentences",
  "value_chain_phase": "<one allowed phase id>",
  "process_step": "<short process step name>",
  "mechanism": "<how the approach produces the change>",
  "key_findings": [{{"finding": "...", "citations": ["PMID:..."]}}],
  "dimensions": [{{
      "dimension_id": "<allowed dimension id>",
      "direction": "up|down|flat",
      "low": 0, "base": 0, "high": 0,
      "unit": "...",
      "confidence": "low|medium|high",
      "rationale": "...",
      "citations": ["PMID:..."],
      "quotes": ["short verbatim snippet from a cited abstract"]
  }}],
  "suggested_maturity": "exploratory|emerging_local|mature",
  "maturity_rationale": "...",
  "suggested_kpis": [{{"name": "...", "definition": "...", "cadence": "monthly|quarterly|semiannual"}}],
  "risks_and_caveats": ["..."],
  "open_questions": ["..."]
}}
"""


def parse_llm_json(text: str) -> dict[str, Any]:
    """Parse JSON from an LLM reply, tolerating code fences and surrounding prose."""
    cleaned = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("LLM reply did not contain JSON") from None
        data = json.loads(cleaned[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("LLM reply JSON is not an object")
    return data


def llm_configured(settings: dict[str, Any] | None) -> bool:
    return bool(settings) and not validate_llm_settings(settings or {})


def build_generate_fn(settings: dict[str, Any], timeout: int = 180) -> GenerateFn:
    provider_id = settings.get("provider")
    host_field = {
        "openai_compatible": "openai_base_url",
        "azure_openai": "azure_openai_endpoint",
    }.get(str(provider_id))
    if host_field:
        assert_host_allowed(str(settings.get(host_field) or ""))
    provider = build_provider(settings)

    def _generate(prompt: str) -> str:
        return provider.generate(prompt, timeout=timeout)  # type: ignore[call-arg]

    return _generate


def _fallback_query(title: str, description: str) -> str:
    tokens = suggest_pubmed_query(title, description).split()
    return " ".join(tokens[:5])


def _broadening_queries(
    first: str, title: str, description: str, *, pubmed_tags: bool = False
) -> list[str]:
    """Primary query, then progressively broader keyword queries (deduplicated, in order)."""
    title_tokens = suggest_pubmed_query(title, "").split()
    all_tokens = suggest_pubmed_query(title, description).split()

    def join(tokens: list[str]) -> str:
        if pubmed_tags:
            return " AND ".join(f"{t}[tiab]" for t in tokens)
        return " ".join(tokens)

    candidates = [
        first,
        join(title_tokens[:5]),
        join(title_tokens[:4]),
        join(title_tokens[:3]),
        join(all_tokens[:3]),
        join(title_tokens[:2]),
    ]
    out: list[str] = []
    for c in candidates:
        c = c.strip()
        if c and c not in out:
            out.append(c)
    return out


def _search_until_hits(
    fn: Callable[[str], list[dict[str, Any]]], queries: list[str]
) -> tuple[list[dict[str, Any]], str]:
    for q in queries:
        hits = fn(q)
        if hits:
            return hits, q
    return [], queries[0] if queries else ""


def _source_id(item: dict[str, Any]) -> str:
    if item.get("source_id"):
        return str(item["source_id"])
    if item.get("pmid"):
        return f"PMID:{item['pmid']}"
    if item.get("openalex_id"):
        return f"OA:{item['openalex_id']}"
    return ""


def _norm_pmid(value: Any) -> str:
    text = re.sub(r"^PMID:?", "", str(value or "").strip(), flags=re.IGNORECASE)
    return text if text.isdigit() else ""


def _norm_doi(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", text)


# Common words that match almost any biomedical abstract and should not count as relevance.
_WEAK_TOKENS = frozenset(
    {
        "clinical", "trial", "trials", "study", "patient", "patients", "data", "using",
        "based", "model", "models", "learning", "machine", "drug", "drugs", "time",
        "high", "selection", "automated", "automation", "review", "analysis",
        "phase", "iii", "goal", "faster", "lower", "fewer", "reduce", "reduced", "less",
    }
)

_UK_US = (
    (re.compile(r"(\w{3,})is(e|ed|es|ing|ation|ations)\b"), r"\1iz\2"),
    (re.compile(r"\benrolment"), "enrollment"),
    (re.compile(r"\bpaediatric"), "pediatric"),
    (re.compile(r"\bprogramme"), "program"),
    (re.compile(r"\btumour"), "tumor"),
    (re.compile(r"\bhaemat"), "hemat"),
)


def _us_spelling(text: str) -> str:
    """Fold UK spellings to US so "decentralised" matches "decentralized"."""
    for pattern, repl in _UK_US:
        text = pattern.sub(repl, text)
    return text


def _relevance_score(item: dict[str, Any], tokens: list[str]) -> int:
    title = _us_spelling((item.get("title") or "").lower())
    abstract = _us_spelling((item.get("abstract") or "").lower())
    tokens = [_us_spelling(t) for t in tokens]
    score = 0
    for tok in tokens:
        weak = tok in _WEAK_TOKENS
        if tok in title:
            score += 1 if weak else 3
        elif tok in abstract and not weak:
            score += 2
    return score


def _dedupe(groups: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Drop a later hit that repeats an earlier PMID, DOI, or title. PubMed is passed first."""
    seen_pmids: set[str] = set()
    seen_dois: set[str] = set()
    seen_titles: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in (hit for group in groups for hit in group):
        pmid = _norm_pmid(item.get("pmid"))
        doi = _norm_doi(item.get("doi"))
        title = re.sub(r"\W+", "", (item.get("title") or "").lower())[:120]
        if pmid and pmid in seen_pmids:
            continue
        if doi and doi in seen_dois:
            continue
        if title and title in seen_titles:
            continue
        if pmid:
            seen_pmids.add(pmid)
        if doi:
            seen_dois.add(doi)
        if title:
            seen_titles.add(title)
        out.append(item)
    return out


def _rank_and_cap(sources: list[dict[str, Any]], title: str, description: str) -> list[dict[str, Any]]:
    """Relevance-filter and cap the merged list with a per-group quota.

    Every group (literature, grey, trials, regulatory) first keeps up to GROUP_MIN_SHARE of its
    best hits. Strong matches (score >= 3) qualify; a group with no strong match may fill its
    share with moderate ones (score >= 2). Remaining slots go to the best strong matches overall.
    With no strong match anywhere, everything is kept in rank order, as before.
    """
    tokens = [t for t in suggest_pubmed_query(title, description).split() if len(t) > 2][:8]
    scored = [(_relevance_score(s, tokens) if tokens else 0, i, s) for i, s in enumerate(sources)]
    by_rank = sorted(scored, key=lambda x: (-x[0], x[1]))
    if not any(sc >= 3 for sc, _, _ in scored):
        return [s for _, _, s in by_rank][:MAX_MERGED_SOURCES]

    by_group: dict[str, list[tuple[int, int, dict[str, Any]]]] = {}
    for item in by_rank:
        by_group.setdefault(registry.group_of(item[2].get("database")), []).append(item)

    picked: dict[int, tuple[int, int, dict[str, Any]]] = {}
    for items in by_group.values():
        strong = [x for x in items if x[0] >= 3]
        share = strong or [x for x in items if x[0] >= 2]
        for x in share[:GROUP_MIN_SHARE]:
            picked[x[1]] = x
    for x in by_rank:
        if len(picked) >= MAX_MERGED_SOURCES:
            break
        if x[0] >= 3:
            picked.setdefault(x[1], x)
    return [s for _, _, s in sorted(picked.values(), key=lambda x: (-x[0], x[1]))][:MAX_MERGED_SOURCES]


_RELEVANCE_WORDS = {
    "high": "high",
    "primary": "high",
    "3": "high",
    "medium": "medium",
    "med": "medium",
    "2": "medium",
    "low": "low",
    "supporting": "low",
    "1": "low",
}
_RELEVANCE_SCORE = {"high": 3, "medium": 2, "low": 1}


def _relevance_label(value: Any) -> str | None:
    """Map a user rank to high/medium/low. None means the source was not ranked."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return {1: "low", 2: "medium", 3: "high"}.get(int(value))
    if isinstance(value, str):
        return _RELEVANCE_WORDS.get(value.strip().lower())
    return None


def _is_excluded_rank(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return int(value) <= 0
    if isinstance(value, str):
        return value.strip().lower() in {"0", "off", "none", "exclude", "excluded"}
    return False


def _apply_user_relevance(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop sources the user ranked Off, normalize the rest, and put higher ranks first."""
    kept: list[dict[str, Any]] = []
    for raw in sources:
        source = dict(raw)
        if "relevance" in source and _is_excluded_rank(source.get("relevance")):
            continue
        label = _relevance_label(source.get("relevance"))
        if label:
            source["relevance"] = label
        else:
            source.pop("relevance", None)
        kept.append(source)
    if not kept:
        raise ValueError("Rank at least one source above Off before generating the brief.")
    if any(s.get("relevance") for s in kept):
        kept.sort(key=lambda s: _RELEVANCE_SCORE.get(s.get("relevance") or "", 0), reverse=True)
    return kept


def _public_source(source: dict[str, Any]) -> dict[str, Any]:
    item = {k: source.get(k) for k in ("source_id", "database", "title", "year", "venue", "url", "type")}
    if source.get("relevance") in _RELEVANCE_SCORE:
        item["relevance"] = source["relevance"]
    item["abstract"] = (source.get("abstract") or "")[:1200]
    return item


def _evidence_summary(source: dict[str, Any]) -> str:
    abstract = (source.get("abstract") or "")[:400]
    if source.get("relevance") in _RELEVANCE_SCORE:
        return f"User relevance: {source['relevance']}. {abstract}"[:400]
    return abstract


def _format_sources(sources: list[dict[str, Any]], limit_chars: int = 700) -> str:
    lines = []
    for s in sources:
        abstract = (s.get("abstract") or "").replace("\n", " ")
        header = f"[{s['source_id']}] {s.get('title','')} ({s.get('year','')}, {s.get('venue','')})"
        if s.get("relevance") in _RELEVANCE_SCORE:
            header += f"\nUser relevance: {s['relevance']}"
        lines.append(f"{header}\n{abstract[:limit_chars]}")
    return "\n\n".join(lines) or "(no sources found)"


def _clean_range(item: dict[str, Any]) -> tuple[float, float, float] | None:
    try:
        vals = sorted([float(item["low"]), float(item["base"]), float(item["high"])])
    except (KeyError, TypeError, ValueError):
        return None
    return vals[0], vals[1], vals[2]


def _numbers_close(candidate: float, reported: float) -> bool:
    """True when `candidate` plausibly refers to the same figure as `reported`."""
    return abs(candidate - reported) <= max(0.6, abs(reported) * 0.12)


def _dimension_is_grounded(dim: dict[str, Any], sources_by_id: dict[str, dict[str, Any]]) -> bool:
    """True when the low or high edge of the range matches a number actually reported in a
    cited source's abstract. A `base` that merely interpolates between two real edges still
    counts as grounded; a range with no edge traceable to any cited source does not — that is
    the model inventing a band around nothing (or around a single disconnected data point).
    """
    citations = [c for c in (dim.get("citations") or []) if c in sources_by_id]
    low, high = dim.get("low"), dim.get("high")
    if not citations or low is None or high is None:
        return False
    text = " ".join(sources_by_id[c].get("abstract") or "" for c in citations)
    if not text.strip():
        return False
    reported = [n["value"] for n in extract_numeric_evidence({"pmid": "", "abstract": text})]
    if not reported:
        return False
    for edge in (float(low), float(high)):
        # Also compare %<->fraction forms (e.g. 0.5 vs "50%") since units vary across dimensions.
        for candidate in (edge, edge * 100, edge / 100):
            if any(_numbers_close(candidate, value) for value in reported):
                return True
    return False


def _enum(value: Any, enum_cls: type, default: Any) -> Any:
    try:
        return enum_cls(str(value))
    except ValueError:
        return default


LegacyArgs = dict[str, Any]


def _adapt_legacy_fn(key: str, fn: Callable[..., list[dict[str, Any]]]) -> registry.SearchFn:
    """Old `<key>_fn` callables: PubMed took keyword args, the rest took (query, max_results=)."""
    if key == "pubmed":
        return lambda q, n: fn(base_query=q, max_results=n, date_preset="10y", has_abstract=True)
    return lambda q, n: fn(q, max_results=n)


def _select_sources(
    sources: Iterable[str] | None,
    overrides: dict[str, registry.SearchFn] | None,
    legacy: LegacyArgs,
) -> tuple[list[str], dict[str, registry.SearchFn]]:
    """Resolve which source keys to run, in registry (dedupe-priority) order.

    `sources=None` means every default, available source. Older callers pass
    `include_<key>=bool` and `<key>_fn=callable`; those still work for any registered key.
    """
    enabled = set(sources) if sources is not None else set(registry.default_keys())
    resolved = dict(overrides or {})
    unknown: list[str] = []
    for name, value in legacy.items():
        if name.startswith("include_") and registry.get(name[len("include_"):]):
            if value is not None:
                key = name[len("include_"):]
                (enabled.add if value else enabled.discard)(key)
        elif name.endswith("_fn") and registry.get(name[: -len("_fn")]):
            if value is not None:
                resolved[name[: -len("_fn")]] = _adapt_legacy_fn(name[: -len("_fn")], value)
        else:
            unknown.append(name)
    if unknown:
        raise TypeError(f"Unexpected arguments: {', '.join(sorted(unknown))}")
    return [k for k in registry.SOURCES if k in enabled], resolved


def _search_sources(
    *,
    title: str,
    description: str,
    generate_fn: GenerateFn | None,
    enabled: list[str],
    overrides: dict[str, registry.SearchFn] | None = None,
    max_per_source: int = 12,
) -> tuple[list[dict[str, Any]], dict[str, str], list[str]]:
    """Search every enabled source in parallel, then dedupe, relevance-filter and cap.

    Returns (sources, queries, warnings). Each source gets source_id and database set.
    A source that errors, times out, or lacks its API key is reported in warnings and does not
    block the others.
    """
    overrides = overrides or {}
    warnings: list[str] = []
    pubmed_query = " AND ".join(f"{t}[tiab]" for t in suggest_pubmed_query(title, "").split()[:5])
    keyword_query = " ".join(suggest_pubmed_query(title, "").split()[:5])
    if generate_fn:
        try:
            q = parse_llm_json(generate_fn(QUERY_PROMPT.format(title=title, description=description)))
            pubmed_query = str(q.get("pubmed_query") or pubmed_query)
            keyword_query = str(q.get("keyword_query") or keyword_query)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"LLM query generation failed, used keyword query instead: {exc}")

    keyword_queries = _broadening_queries(keyword_query, title, description)
    pubmed_queries = _broadening_queries(pubmed_query, title, description, pubmed_tags=True)

    jobs: list[tuple[registry.SourceSpec, Callable[[], tuple[list[dict[str, Any]], str]]]] = []
    for key in enabled:
        spec = registry.get(key)
        if spec is None:
            warnings.append(f"Unknown source '{key}' skipped.")
            continue
        search = overrides.get(key)
        if search is None:
            if not spec.available:
                warnings.append(f"{spec.label} skipped: set {' or '.join(spec.env_keys)} in the server .env.")
                continue
            search = spec.search
        cap = spec.cap or max_per_source
        if spec.pubmed_syntax:
            queries = pubmed_queries
        elif spec.short_query:
            queries = keyword_queries[1:] or keyword_queries
        else:
            queries = keyword_queries
        jobs.append((spec, lambda s=search, c=cap, qs=queries: _search_until_hits(lambda q: s(q, c), qs)))

    results: dict[str, tuple[list[dict[str, Any]], str]] = {}
    if jobs:
        pool = ThreadPoolExecutor(max_workers=min(8, len(jobs)))
        futures = {pool.submit(call): spec for spec, call in jobs}
        done, pending = wait(futures, timeout=SOURCE_TIMEOUT_S)
        for future in done:
            spec = futures[future]
            try:
                results[spec.key] = future.result()
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{spec.label} search failed: {exc}")
        for future in pending:
            warnings.append(f"{futures[future].label} search timed out after {SOURCE_TIMEOUT_S}s.")
        pool.shutdown(wait=False, cancel_futures=True)

    queries_out: dict[str, str] = {}
    groups: list[list[dict[str, Any]]] = []
    for spec, _ in jobs:
        if spec.key not in results:
            continue
        hits, used = results[spec.key]
        queries_out[spec.query_key or spec.key] = used
        for hit in hits:
            hit.setdefault("database", spec.key)
        groups.append(hits)

    sources = _rank_and_cap(_dedupe(groups), title, description)
    for s in sources:
        s["source_id"] = _source_id(s)
    return sources, queries_out, warnings


def _curate_sources(
    title: str,
    description: str,
    sources: list[dict[str, Any]],
    generate_fn: GenerateFn | None,
) -> tuple[str, list[dict[str, Any]], list[str]]:
    """Ask the LLM which candidate sources actually match the idea (disambiguation step).

    Mutates and returns `sources` with "recommended" (bool) and "note" (str) set on each item.
    Falls back to keeping everything recommended when there is no LLM or the call fails.
    """
    warnings: list[str] = []
    if not sources:
        return "", sources, warnings
    if not generate_fn:
        for s in sources:
            s["recommended"] = True
            s.setdefault("note", "")
        return "", sources, warnings

    prompt = CURATION_PROMPT.format(
        title=title, description=description, sources=_format_sources(sources[:20], limit_chars=400)
    )
    try:
        data = parse_llm_json(generate_fn(prompt))
        recommended_ids = {str(x) for x in data.get("recommended_ids") or []}
        notes = data.get("notes") if isinstance(data.get("notes"), dict) else {}
        interpretation = str(data.get("interpretation") or "")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"LLM paper review failed, keeping keyword relevance order: {exc}")
        for s in sources:
            s["recommended"] = True
            s.setdefault("note", "")
        return "", sources, warnings

    for s in sources:
        s["recommended"] = s["source_id"] in recommended_ids if recommended_ids else True
        note = notes.get(s["source_id"])
        s["note"] = str(note) if note else ""
    return interpretation, sources, warnings


def _run_llm_synthesis(
    *,
    title: str,
    description: str,
    phase_hint: str,
    sources: list[dict[str, Any]],
    generate_fn: GenerateFn | None,
    compendium: dict[str, Any],
    phase_ids: list[str],
    dimension_ids: list[str],
    numbers: list[dict[str, Any]],
    valid_ids: set[str],
) -> dict[str, Any]:
    """Call the synthesis prompt and merge results into `compendium` (mutated and returned)."""
    if not generate_fn:
        compendium["executive_summary"] = (
            f"Found {len(sources)} sources. No LLM is configured, so this compendium lists the "
            "literature and numeric snippets without a synthesis. Configure an LLM in Settings "
            "to get cited estimates."
        )
        return compendium

    prompt = SYNTHESIS_PROMPT.format(
        title=title,
        description=description,
        phase_hint=phase_hint or "(not given)",
        phase_ids=", ".join(phase_ids),
        dimension_ids=", ".join(dimension_ids),
        sources=_format_sources(sources[:20]),
        numbers="\n".join(f"[{n['pmid']}] {n['raw']} — {n['context'][:90]}" for n in numbers[:25])
        or "(none)",
    )
    try:
        data = parse_llm_json(generate_fn(prompt))
    except Exception as exc:  # noqa: BLE001
        compendium["warnings"].append(f"LLM synthesis failed; showing literature only: {exc}")
        compendium["executive_summary"] = (
            f"Found {len(sources)} sources, but the LLM synthesis failed. See warnings."
        )
        return compendium

    def _valid(cites: Any) -> list[str]:
        return [c for c in (cites or []) if isinstance(c, str) and c in valid_ids]

    sources_by_id = {s.get("source_id"): s for s in sources if s.get("source_id")}
    dims: list[dict[str, Any]] = []
    for d in data.get("dimensions") or []:
        if not isinstance(d, dict) or d.get("dimension_id") not in dimension_ids:
            continue
        rng = _clean_range(d)
        cites = _valid(d.get("citations"))
        row = {
            "dimension_id": d["dimension_id"],
            "direction": _enum(d.get("direction"), Direction, Direction.flat).value,
            "low": rng[0] if rng else None,
            "base": rng[1] if rng else None,
            "high": rng[2] if rng else None,
            "unit": str(d.get("unit") or ""),
            "confidence": _enum(d.get("confidence"), Confidence, Confidence.low).value,
            "rationale": str(d.get("rationale") or ""),
            "citations": cites,
            "quotes": [str(q) for q in (d.get("quotes") or [])][:3] if cites else [],
            "evidence_backed": bool(cites),
        }
        # `evidence_backed` only means "cited something"; `grounded` means the range's low/high
        # edge is a number that actually appears in that citation's abstract, not just invented
        # around it. Ungrounded ranges can't count as "high confidence" toward the impact score.
        row["grounded"] = bool(cites) and _dimension_is_grounded(row, sources_by_id)
        if not row["grounded"] and row["confidence"] == Confidence.high.value:
            row["confidence"] = Confidence.medium.value
        dims.append(row)

    phase = str(data.get("value_chain_phase") or phase_hint)
    compendium.update(
        {
            "llm_used": True,
            "executive_summary": str(data.get("executive_summary") or ""),
            "value_chain_phase": phase if phase in phase_ids else phase_hint,
            "process_step": str(data.get("process_step") or ""),
            "mechanism": str(data.get("mechanism") or ""),
            "key_findings": [
                {"finding": str(f.get("finding") or ""), "citations": _valid(f.get("citations"))}
                for f in data.get("key_findings") or []
                if isinstance(f, dict) and f.get("finding")
            ],
            "dimensions": dims,
            "suggested_maturity": _enum(
                data.get("suggested_maturity"), MaturityTier, MaturityTier.exploratory
            ).value,
            "maturity_rationale": str(data.get("maturity_rationale") or ""),
            "suggested_kpis": [
                k for k in data.get("suggested_kpis") or [] if isinstance(k, dict) and k.get("name")
            ],
            "risks_and_caveats": [str(x) for x in data.get("risks_and_caveats") or []],
            "open_questions": [str(x) for x in data.get("open_questions") or []],
        }
    )
    return compendium


def _extract_numbers(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numbers: list[dict[str, Any]] = []
    for s in sources:
        for n in extract_numeric_evidence({"pmid": s["source_id"], "abstract": s.get("abstract", "")}):
            if n["type"] in ("percent", "time"):
                numbers.append(n)
    return numbers


def generate_compendium(
    *,
    title: str,
    description: str,
    phase_hint: str = "",
    llm_settings: dict[str, Any] | None = None,
    sources: Iterable[str] | None = None,
    overrides: dict[str, registry.SearchFn] | None = None,
    max_per_source: int = 12,
    generate_fn: GenerateFn | None = None,
    **legacy: Any,
) -> dict[str, Any]:
    """One-shot search + synthesis (no in-between review step).

    Never raises for LLM or search failures; reports them in the returned "warnings" instead.
    Prefer `search_literature` + `synthesize_from_sources` for the guided, multi-step flow where
    the user reviews candidate papers before synthesis runs.
    """
    enabled, overrides = _select_sources(sources, overrides, legacy)
    cfg = get_config()
    phase_ids = [p["id"] for p in cfg.value_chain.get("phases") or []]
    dimension_ids = [d["id"] for d in cfg.dimensions.get("dimensions") or []]
    warnings: list[str] = []

    if generate_fn is None and llm_configured(llm_settings):
        try:
            generate_fn = build_generate_fn(llm_settings or {})
        except (PermissionError, ValueError) as exc:
            warnings.append(f"LLM not used: {exc}")

    sources, queries, search_warnings = _search_sources(
        title=title,
        description=description,
        generate_fn=generate_fn,
        enabled=enabled,
        overrides=overrides,
        max_per_source=max_per_source,
    )
    warnings += search_warnings
    valid_ids = {s["source_id"] for s in sources}
    numbers = _extract_numbers(sources)

    compendium: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "llm_used": False,
        "queries": queries,
        "sources": [
            {k: s.get(k) for k in ("source_id", "database", "title", "year", "venue", "url", "type")}
            | {"abstract": (s.get("abstract") or "")[:1200]}
            for s in sources
        ],
        "executive_summary": "",
        "value_chain_phase": phase_hint,
        "process_step": "",
        "mechanism": "",
        "key_findings": [],
        "dimensions": [],
        "suggested_maturity": "exploratory",
        "maturity_rationale": "No synthesis available; defaulting to exploratory.",
        "suggested_kpis": [],
        "risks_and_caveats": [],
        "open_questions": [],
        "numeric_snippets": numbers[:30],
        "warnings": warnings,
    }
    return _run_llm_synthesis(
        title=title,
        description=description,
        phase_hint=phase_hint,
        sources=sources,
        generate_fn=generate_fn,
        compendium=compendium,
        phase_ids=phase_ids,
        dimension_ids=dimension_ids,
        numbers=numbers,
        valid_ids=valid_ids,
    )


def search_literature(
    *,
    title: str,
    description: str,
    phase_hint: str = "",
    llm_settings: dict[str, Any] | None = None,
    sources: Iterable[str] | None = None,
    overrides: dict[str, registry.SearchFn] | None = None,
    max_per_source: int = 12,
    generate_fn: GenerateFn | None = None,
    **legacy: Any,
) -> dict[str, Any]:
    """Step 1 of the guided flow: search the enabled sources, then let the LLM flag which
    candidates plausibly match the idea so the user can pick before synthesis runs.
    """
    enabled, overrides = _select_sources(sources, overrides, legacy)
    warnings: list[str] = []

    if generate_fn is None and llm_configured(llm_settings):
        try:
            generate_fn = build_generate_fn(llm_settings or {})
        except (PermissionError, ValueError) as exc:
            warnings.append(f"LLM not used: {exc}")
    llm_used = generate_fn is not None

    sources, queries, search_warnings = _search_sources(
        title=title,
        description=description,
        generate_fn=generate_fn,
        enabled=enabled,
        overrides=overrides,
        max_per_source=max_per_source,
    )
    warnings += search_warnings

    interpretation, sources, curation_warnings = _curate_sources(title, description, sources, generate_fn)
    warnings += curation_warnings

    return {
        "sources": [
            {
                k: s.get(k)
                for k in (
                    "source_id",
                    "database",
                    "title",
                    "year",
                    "venue",
                    "url",
                    "type",
                    "recommended",
                    "note",
                )
            }
            | {"abstract": (s.get("abstract") or "")[:1200]}
            for s in sources
        ],
        "queries": queries,
        "interpretation": interpretation,
        "llm_used": llm_used,
        "warnings": warnings,
    }


def synthesize_from_sources(
    *,
    title: str,
    description: str,
    phase_hint: str = "",
    sources: list[dict[str, Any]],
    llm_settings: dict[str, Any] | None = None,
    generate_fn: GenerateFn | None = None,
) -> dict[str, Any]:
    """Step 2 of the guided flow: numeric extraction + LLM synthesis against a source list the
    user has already reviewed and chosen (from `search_literature`'s output).
    """
    cfg = get_config()
    phase_ids = [p["id"] for p in cfg.value_chain.get("phases") or []]
    dimension_ids = [d["id"] for d in cfg.dimensions.get("dimensions") or []]
    warnings: list[str] = []

    if generate_fn is None and llm_configured(llm_settings):
        try:
            generate_fn = build_generate_fn(llm_settings or {})
        except (PermissionError, ValueError) as exc:
            warnings.append(f"LLM not used: {exc}")

    prepared: list[dict[str, Any]] = []
    for raw in sources:
        s = dict(raw)
        if not s.get("source_id"):
            s["source_id"] = _source_id(s)
        if not s.get("database"):
            s["database"] = registry.database_for_id(str(s["source_id"]))
        prepared.append(s)
    norm_sources = _apply_user_relevance(prepared)
    valid_ids = {s["source_id"] for s in norm_sources if s.get("source_id")}
    numbers = _extract_numbers(norm_sources)

    compendium: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "llm_used": False,
        "queries": {"pubmed": "", "keyword": ""},
        "sources": [_public_source(s) for s in norm_sources],
        "executive_summary": "",
        "value_chain_phase": phase_hint,
        "process_step": "",
        "mechanism": "",
        "key_findings": [],
        "dimensions": [],
        "suggested_maturity": "exploratory",
        "maturity_rationale": "No synthesis available; defaulting to exploratory.",
        "suggested_kpis": [],
        "risks_and_caveats": [],
        "open_questions": [],
        "numeric_snippets": numbers[:30],
        "warnings": warnings,
    }
    return _run_llm_synthesis(
        title=title,
        description=description,
        phase_hint=phase_hint,
        sources=norm_sources,
        generate_fn=generate_fn,
        compendium=compendium,
        phase_ids=phase_ids,
        dimension_ids=dimension_ids,
        numbers=numbers,
        valid_ids=valid_ids,
    )


def apply_compendium(
    record: InitiativeRecord,
    compendium: dict[str, Any],
    *,
    title: str,
    description: str,
    focus_area_code: str = "",
) -> InitiativeRecord:
    """Pre-fill an initiative with compendium output. Numbers stay llm_suggested and unconfirmed."""
    record.initiative.title = title
    record.initiative.description = description
    if focus_area_code:
        record.initiative.focus_area_code = focus_area_code
    record.scope.phase_id = compendium.get("value_chain_phase") or record.scope.phase_id
    record.scope.process_step = compendium.get("process_step") or record.scope.process_step

    evidence_by_source: dict[str, str] = {}
    record.evidence = [e for e in record.evidence if e.kind not in (EvidenceKind.pubmed, EvidenceKind.literature)]
    for s in compendium.get("sources") or []:
        item = EvidenceItem(
            kind=EvidenceKind.pubmed if s.get("database") == "pubmed" else EvidenceKind.literature,
            title=s.get("title") or "",
            source_or_link=s.get("url") or "",
            summary=_evidence_summary(s),
            pmid=s["source_id"].split(":", 1)[1] if s.get("database") == "pubmed" else None,
        )
        evidence_by_source[s["source_id"]] = item.id
        record.evidence.append(item)

    estimates: list[DimensionEstimate] = []
    for d in compendium.get("dimensions") or []:
        ev_ids = [evidence_by_source[c] for c in d.get("citations") or [] if c in evidence_by_source]
        rv = None
        if d.get("low") is not None:
            rv = RangeValue(
                low=d["low"],
                base=d["base"],
                high=d["high"],
                unit=d.get("unit") or "",
                source=ValueSource.llm_suggested,
                confirmed=False,
                evidence_ids=ev_ids,
                rationale=d.get("rationale") or "",
            )
        estimates.append(
            DimensionEstimate(
                dimension_id=d["dimension_id"],
                direction=Direction(d.get("direction") or "flat"),
                estimate=rv,
                confidence=Confidence(d.get("confidence") or "low"),
                mechanism=compendium.get("mechanism") or "",
                linked_evidence_ids=ev_ids,
            )
        )
    if estimates:
        record.estimates = estimates
        record.change.affected_dimension_ids = [e.dimension_id for e in estimates]
    if compendium.get("mechanism"):
        record.change.what_changes = compendium["mechanism"]

    if compendium.get("llm_used"):
        record.maturity.tier = MaturityTier(compendium.get("suggested_maturity") or "exploratory")
        record.maturity.rationale = f"LLM-suggested: {compendium.get('maturity_rationale') or ''}".strip()

    kpis = []
    for k in compendium.get("suggested_kpis") or []:
        kpis.append(
            KpiPlan(
                name=str(k.get("name")),
                definition=str(k.get("definition") or ""),
                cadence=_enum(k.get("cadence"), Cadence, Cadence.quarterly),
            )
        )
    if kpis and not record.measurement_plan:
        record.measurement_plan = kpis

    # Keep source ids -> evidence ids so the UI can link citations to evidence records.
    compendium["evidence_map"] = evidence_by_source
    record.compendium = compendium

    record.impact_statement = build_impact_statement(record)
    record.quality_warnings = check_statement(record.impact_statement, record)
    record.scorecard = build_scorecard(record)
    record.impact_score = suggest_impact_score(record)
    return record
