#!/usr/bin/env python3
"""Semantic Scholar leg: an overlap check on the OpenAlex harvest.

Implements the Semantic Scholar row of docs/search-strategy.md §1. Standard library only,
no API key, no account.

    python3 scripts/fetch_semanticscholar.py --out data/raw/s2_$(date +%Y%m%d).json
    python3 scripts/fetch_semanticscholar.py --out ... --overlap data/screening/corpus_deduped.csv
    python3 scripts/fetch_semanticscholar.py --count-only

WHAT THIS LEG IS FOR
--------------------
It is a **coverage check, not a primary source**. §1 lists Semantic Scholar for overlap
against OpenAlex, on the grounds that it indexes CS venues more strongly. The question it
answers is narrow and worth stating precisely:

    Of the records Semantic Scholar returns for the same query in the same window, what
    fraction is already in our corpus, and what does the remainder look like?

A high overlap supports the claim that the OpenAlex-led search is not missing a systematic
slice of the literature. A low overlap is a finding about the search, not a reason to
quietly merge the difference in: any additional yield is reported separately (§1), because
a coverage check that silently becomes a harvest is no longer a check.

Nothing here writes to the screening corpus. The output is a dated export plus an overlap
report.

RATE LIMITS
-----------
The unauthenticated Graph API is shared and throttled hard, and it answers 429 rather than
queueing. Requests are spaced and retried with exponential backoff; a run that cannot
complete says so and exits non-zero rather than reporting a partial set as if it were the
whole. A truncated coverage check that looks complete would overstate overlap, which is the
direction that flatters us.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

API = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

# Keep in sync with docs/search-strategy.md §2 and the other fetchers.
TERMS = [
    "reservoir computing",
    "echo state network",
    "echo state machine",
    "liquid state machine",
    "physical reservoir",
    "next generation reservoir computing",
]

WINDOW_START = date(2019, 1, 1)
WINDOW_END = date(2026, 6, 30)      # frozen cutoff, protocol.md §3

FIELDS = "title,abstract,year,externalIds,venue,publicationTypes,openAccessPdf,citationCount"
DELAY_S = 1.2                        # unauthenticated pool is ~1 rps
MAX_PAGES = 60                       # safety ceiling; 1000 records per page


def build_query() -> str:
    """Bulk search accepts a boolean query with quoted phrases."""
    return " | ".join(f'"{t}"' for t in TERMS)


def get(url: str, retries: int = 6) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "rc-audit/0.1"})
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in (429, 500, 502, 503, 504):
                raise
            wait = min(60, 3 * 2 ** attempt)
            print(f"  ! HTTP {exc.code} — retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            last = exc
            wait = min(60, 3 * 2 ** attempt)
            print(f"  ! {exc} — retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"failed after {retries} attempts: {last}")


def flatten(p: dict) -> dict:
    ext = p.get("externalIds") or {}
    oa = p.get("openAccessPdf") or {}
    abstract = p.get("abstract") or ""
    return {
        "s2_id": p.get("paperId", ""),
        "doi": (ext.get("DOI") or "").lower(),
        "arxiv_id": ext.get("ArXiv") or "",
        "title": p.get("title") or "",
        "abstract": abstract,
        "has_abstract": bool(abstract),
        "year": p.get("year"),
        "venue": p.get("venue") or "",
        "publication_types": p.get("publicationTypes") or [],
        "is_oa": bool(oa.get("url")),
        "cited_by_count": p.get("citationCount"),
    }


def harvest(count_only: bool) -> tuple[list[dict], int]:
    params = {
        "query": build_query(),
        "fields": FIELDS,
        "year": f"{WINDOW_START.year}-{WINDOW_END.year}",
    }
    url = f"{API}?{urllib.parse.urlencode(params)}"
    records: list[dict] = []
    reported_total = -1
    token = None
    for page in range(MAX_PAGES):
        u = url if token is None else f"{url}&token={urllib.parse.quote(token)}"
        payload = get(u)
        if reported_total < 0:
            reported_total = int(payload.get("total") or 0)
            print(f"  reported total: {reported_total}")
            if count_only:
                return [], reported_total
        batch = payload.get("data") or []
        records.extend(flatten(p) for p in batch)
        print(f"  page {page + 1}: +{len(batch)}  (running {len(records)})")
        token = payload.get("token")
        if not token or not batch:
            break
        time.sleep(DELAY_S)
    else:
        raise RuntimeError(
            f"hit the {MAX_PAGES}-page ceiling with a continuation token still open. "
            f"The harvest is incomplete and must not be reported as a coverage check."
        )
    return records, reported_total


# ---------------------------------------------------------------- window + overlap

def in_window(r: dict) -> bool:
    """Year-granularity membership.

    The bulk endpoint exposes a publication year, not a date, so the frozen 2026-06-30
    cutoff cannot be applied exactly on this leg. Records dated 2026 are kept and the
    imprecision is reported rather than hidden: for an overlap check the consequence is a
    slightly generous denominator, which understates overlap. That is the safe direction.
    """
    y = r.get("year")
    return y is not None and WINDOW_START.year <= int(y) <= WINDOW_END.year


def norm_title(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t.lower()).split())


def norm_arxiv(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"^10\.48550/arxiv\.", "", s)
    m = re.match(r"^(\d{4}\.\d{4,5}|[a-z-]+(\.[a-z]{2})?/\d{7})(v\d+)?$", s)
    return m.group(1) if m else ""


def overlap_report(records: list[dict], corpus_path: Path) -> dict:
    with corpus_path.open(newline="", encoding="utf-8") as fh:
        corpus = list(csv.DictReader(fh))
    dois = {(r["doi"] or "").lower() for r in corpus if r["doi"]}
    arx = {norm_arxiv(r["preprint_id"]) for r in corpus if r["preprint_id"]}
    titles = {norm_title(r["title"]) for r in corpus if r["title"]}

    matched_doi = matched_arxiv = matched_title = 0
    unmatched: list[dict] = []
    for r in records:
        if r["doi"] and r["doi"] in dois:
            matched_doi += 1
        elif norm_arxiv(r["arxiv_id"]) and norm_arxiv(r["arxiv_id"]) in arx:
            matched_arxiv += 1
        elif norm_title(r["title"]) in titles:
            matched_title += 1
        else:
            unmatched.append(r)

    matched = matched_doi + matched_arxiv + matched_title
    n = len(records)
    return {
        "corpus_records": len(corpus),
        "s2_in_window": n,
        "matched_total": matched,
        "matched_by_doi": matched_doi,
        "matched_by_arxiv_id": matched_arxiv,
        "matched_by_title": matched_title,
        "unmatched": len(unmatched),
        "overlap_rate": round(matched / n, 4) if n else None,
        "unmatched_by_year": dict(sorted(Counter(
            r["year"] for r in unmatched).items(), key=lambda kv: (kv[0] or 0))),
        "unmatched_open_access": sum(1 for r in unmatched if r["is_oa"]),
        "unmatched_with_abstract": sum(1 for r in unmatched if r["has_abstract"]),
        "unmatched_sample_titles": [r["title"] for r in unmatched[:25]],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--overlap", type=Path,
                    default=Path("data/screening/corpus_deduped.csv"))
    ap.add_argument("--count-only", action="store_true")
    args = ap.parse_args()

    print(f"Semantic Scholar bulk search, window {WINDOW_START.year}-{WINDOW_END.year}")
    records, reported = harvest(args.count_only)
    if args.count_only:
        return 0

    windowed = [r for r in records if in_window(r)]
    dropped = len(records) - len(windowed)
    # Deduplicate the leg against itself before comparing, so paging repeats do not
    # inflate the denominator (the same failure OpenAlex showed at 6 records).
    seen: dict[str, dict] = {}
    repeats = 0
    for r in windowed:
        key = r["s2_id"] or r["doi"] or norm_title(r["title"])
        if key in seen:
            repeats += 1
            continue
        seen[key] = r
    unique = list(seen.values())

    print(f"\nretrieved      {len(records)}")
    print(f"in window      {len(windowed)}   ({dropped} out of window)")
    print(f"unique         {len(unique)}   ({repeats} paging repeats collapsed)")

    payload = {
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "source": "semanticscholar-graph-bulk",
        "purpose": "coverage/overlap check on OpenAlex, not a primary source "
                   "(search-strategy.md §1)",
        "query": build_query(),
        "terms": TERMS,
        "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat(),
                   "granularity": "year (the bulk endpoint exposes no publication date)"},
        "counts": {
            "reported_total": reported,
            "retrieved": len(records),
            "in_window": len(windowed),
            "unique": len(unique),
            "paging_repeats_collapsed": repeats,
        },
        "records": unique,
    }

    if args.overlap and args.overlap.exists():
        rep = overlap_report(unique, args.overlap)
        payload["overlap"] = rep
        print(f"\noverlap against {args.overlap}")
        print(f"  matched      {rep['matched_total']}/{rep['s2_in_window']} "
              f"= {rep['overlap_rate']:.1%}")
        print(f"    by DOI     {rep['matched_by_doi']}")
        print(f"    by arXiv   {rep['matched_by_arxiv_id']}")
        print(f"    by title   {rep['matched_by_title']}")
        print(f"  unmatched    {rep['unmatched']}  "
              f"({rep['unmatched_open_access']} open access)")
    elif args.overlap:
        print(f"\n! {args.overlap} not found; skipping the overlap report",
              file=sys.stderr)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=1))
        print(f"\n-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
