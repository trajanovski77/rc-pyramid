#!/usr/bin/env python3
"""Retrieve OpenAlex records for the RC audit corpus.

Replacement for the Scopus / Web of Science / IEEE Xplore leg, which requires paid
institutional access. Standard library only, no API key, no account.

    python3 scripts/fetch_openalex.py --out data/raw/openalex_$(date +%Y%m%d).json
    python3 scripts/fetch_openalex.py --out ... --oa-only     # open-access records only
    python3 scripts/fetch_openalex.py --count-only            # just report the totals

WHY OPENALEX
------------
Two reasons, and the second is the stronger one.

Practical: it is free and scriptable, so the search leg no longer depends on a subscription
somebody may not have.

Methodological: a reproducibility audit whose own literature search cannot be re-run without
a paid subscription is, by its own standard, under-reproducible. Anyone can re-execute this
script. Nobody outside a subscribing institution can re-execute a Scopus export.

Known-item recall was checked before adopting this: 9 of 9 reference papers known to be in
scope (Tanaka 2019, Yan 2024, Liang 2024, Dale 2025, Cucchi 2022, Dambre 2012, Gauthier 2021,
Vidamour 2023, and the Nature Reviews Physics topological review) are retrievable by DOI.

ABSTRACTS
---------
OpenAlex stores abstracts as an inverted index, which this script reconstructs. Coverage is
not complete, and it is noticeably worse for closed-access records: of the nine known items,
both records lacking an abstract were paywalled. Since Stage-1 screening is title and
abstract, a record with no abstract cannot be screened normally and is flagged rather than
silently dropped. Restricting to open access largely removes this problem, which is one of
several arguments for doing so.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

API = "https://api.openalex.org/works"

# Keep in sync with docs/search-strategy.md §2.5.
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

PER_PAGE = 200                       # OpenAlex maximum
DELAY_S = 0.2                        # polite pool; be a good citizen
# Polite-pool contact. Both APIs ask for an address so they can reach the operator of a
# script that misbehaves; it is sent in the query string and the User-Agent on every
# request. It defaults to the manuscript's corresponding-author address, which is already
# public, rather than to a private one, and any re-runner should set their own:
#     export RC_AUDIT_MAILTO="you@example.org"
MAILTO = os.environ.get("RC_AUDIT_MAILTO", "stefan.trajanovski@students.finki.ukim.mk")


def build_filter(oa_only: bool) -> str:
    q = " OR ".join(f'"{t}"' for t in TERMS)
    parts = [
        f"from_publication_date:{WINDOW_START.isoformat()}",
        f"to_publication_date:{WINDOW_END.isoformat()}",
        "language:en",
        f"title_and_abstract.search:{q}",
    ]
    if oa_only:
        parts.append("open_access.is_oa:true")
    return ",".join(parts)


def get(url: str, retries: int = 4) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": f"rc-audit/0.1 (mailto:{MAILTO})"})
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as exc:  # noqa: BLE001
            last = exc
            wait = 2 ** attempt
            print(f"  ! {exc} — retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"failed after {retries} attempts: {last}")


def reconstruct_abstract(inv: dict | None) -> str:
    """OpenAlex stores abstracts as {token: [positions]}. Invert it back to text."""
    if not inv:
        return ""
    pos: dict[int, str] = {}
    for token, idxs in inv.items():
        for i in idxs:
            pos[i] = token
    return " ".join(pos[i] for i in sorted(pos))


def flatten(w: dict) -> dict:
    loc = (w.get("primary_location") or {}) or {}
    src = (loc.get("source") or {}) or {}
    oa = w.get("open_access") or {}
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    abstract = reconstruct_abstract(w.get("abstract_inverted_index"))
    return {
        "openalex_id": (w.get("id") or "").rsplit("/", 1)[-1],
        "doi": doi,
        "title": w.get("display_name") or "",
        "abstract": abstract,
        "has_abstract": bool(abstract),
        "authors": "; ".join(
            (a.get("author") or {}).get("display_name", "")
            for a in (w.get("authorships") or [])
        ),
        "year": w.get("publication_year"),
        "venue": src.get("display_name") or "",
        "venue_type": w.get("type") or "",
        "is_oa": bool(oa.get("is_oa")),
        "oa_status": oa.get("oa_status") or "",
        "oa_url": oa.get("oa_url") or "",
        "cited_by_count": w.get("cited_by_count"),
    }


def harvest(oa_only: bool, cap: int) -> tuple[list[dict], int]:
    filt = build_filter(oa_only)
    cursor, out = "*", []
    total = None
    while cursor and len(out) < cap:
        url = API + "?" + urllib.parse.urlencode(
            {"filter": filt, "per-page": PER_PAGE, "cursor": cursor, "mailto": MAILTO}
        )
        d = get(url)
        if total is None:
            total = d["meta"]["count"]
            print(f"  total matching: {total}", file=sys.stderr)
        out.extend(flatten(w) for w in d["results"])
        cursor = d["meta"].get("next_cursor")
        print(f"  fetched {len(out)}/{total}", file=sys.stderr)
        if not d["results"]:
            break
        time.sleep(DELAY_S)
    return out, (total or 0)


def counts_only() -> int:
    for label, oa in (("all", False), ("open access only", True)):
        url = API + "?" + urllib.parse.urlencode(
            {"filter": build_filter(oa), "per-page": 1, "mailto": MAILTO}
        )
        print(f"  {label:18s} {get(url)['meta']['count']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    ap.add_argument("--oa-only", action="store_true",
                    help="restrict to open-access records (see docs/search-strategy.md §1.2)")
    ap.add_argument("--count-only", action="store_true")
    ap.add_argument("--max", type=int, default=12000, help="safety ceiling")
    args = ap.parse_args()

    if args.count_only:
        return counts_only()
    if not args.out:
        ap.error("--out is required unless --count-only")

    recs, total = harvest(args.oa_only, args.max)

    no_abs = sum(1 for r in recs if not r["has_abstract"])
    n_oa = sum(1 for r in recs if r["is_oa"])

    payload = {
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "source": "openalex",
        "filter": build_filter(args.oa_only),
        "terms": TERMS,
        "oa_only": args.oa_only,
        "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()},
        "counts": {
            "reported_total": total,
            "retrieved": len(recs),
            "open_access": n_oa,
            "without_abstract": no_abs,
        },
        "records": recs,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    print(
        f"\nreported total    : {total}\n"
        f"retrieved         : {len(recs)}\n"
        f"open access       : {n_oa}\n"
        f"without abstract  : {no_abs}   <- cannot be screened on title+abstract\n"
        f"-> {args.out}\n\n"
        f"Record counts in docs/search-strategy.md §6."
    )
    if len(recs) < total:
        print(f"WARNING: hit the {args.max} safety ceiling before exhausting the result set.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
