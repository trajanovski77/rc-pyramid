#!/usr/bin/env python3
"""Crossref leg: DOI-level metadata completeness, and exact dates where a leg lacks them.

Implements the Crossref row of docs/search-strategy.md §1. Standard library only, no key.

    python3 scripts/fetch_crossref.py completeness --sample 400
    python3 scripts/fetch_crossref.py resolve-dates --from data/raw/s2_20260802.json
    python3 scripts/fetch_crossref.py selftest

TWO JOBS
--------
**completeness** answers the question §1 assigns this leg: is our corpus metadata missing
things the registration record has? It samples corpus DOIs, pulls the Crossref record, and
compares field by field. The one that matters most is the abstract: Stage-1 screening is
title and abstract, 222 eligible records have no abstract from OpenAlex, and if Crossref
holds abstracts for some of them those records become screenable normally instead of on
title alone.

**resolve-dates** closes a gap the Semantic Scholar leg cannot close by itself. That API
exposes a publication *year*, while the protocol's window ends 2026-06-30. Of the records
S2 returns that our corpus lacks, 323 are dated 2026 and could be either genuinely missing
or simply published after the cutoff. Reporting them as a coverage gap without checking
would overstate what the search missed; ignoring them would understate it. Crossref has the
exact date, so the question is answerable rather than arguable.

WHY THIS MATTERS FOR THE PAPER
------------------------------
A coverage check whose own uncertainty is larger than the effect it reports is not evidence.
Resolving the dates is what makes the Semantic Scholar overlap figure quotable.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
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

API = "https://api.crossref.org/works/"
# Polite-pool contact. Both APIs ask for an address so they can reach the operator of a
# script that misbehaves; it is sent in the query string and the User-Agent on every
# request. It defaults to the manuscript's corresponding-author address, which is already
# public, rather than to a private one, and any re-runner should set their own:
#     export RC_AUDIT_MAILTO="you@example.org"
MAILTO = os.environ.get("RC_AUDIT_MAILTO", "stefan.trajanovski@students.finki.ukim.mk")
DELAY_S = 0.12

WINDOW_START = date(2019, 1, 1)
WINDOW_END = date(2026, 6, 30)              # frozen cutoff, protocol.md §3


def get(doi: str, retries: int = 4) -> dict | None:
    """Return the Crossref message for a DOI, or None if it is not registered there."""
    url = API + urllib.parse.quote(doi, safe="") + f"?mailto={MAILTO}"
    req = urllib.request.Request(url, headers={"User-Agent": f"rc-audit/0.1 (mailto:{MAILTO})"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read()).get("message")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(min(30, 2 ** attempt))
        except Exception:  # noqa: BLE001
            time.sleep(min(30, 2 ** attempt))
    return None


def issued_date(msg: dict) -> date | None:
    """Earliest date Crossref records for the work.

    `issued` is the registrant's publication date and is the field the window is defined
    on. Where a work was posted online before formal issue, `created` can be earlier;
    taking the earlier of the two is the inclusive reading, and inclusive is the right
    default for a coverage check, whose job is to find what a search missed.
    """
    cands = []
    for key in ("issued", "created", "published-print", "published-online"):
        parts = ((msg.get(key) or {}).get("date-parts") or [[]])[0]
        if parts and parts[0]:
            y = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 and parts[1] else 1
            d = int(parts[2]) if len(parts) > 2 and parts[2] else 1
            try:
                cands.append(date(y, m, d))
            except ValueError:
                continue
    return min(cands) if cands else None


def norm_title(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t.lower()).split())


def strip_jats(s: str) -> str:
    """Crossref abstracts are JATS XML fragments."""
    s = re.sub(r"<[^>]+>", " ", s or "")
    return " ".join(s.split())


# ---------------------------------------------------------------- completeness

def cmd_completeness(args) -> int:
    with args.corpus.open(newline="", encoding="utf-8") as fh:
        corpus = [r for r in csv.DictReader(fh) if not r["dup_of"]]
    withdoi = [r for r in corpus if r["doi"]]
    print(f"corpus {len(corpus)} records, {len(withdoi)} with a DOI "
          f"({len(corpus) - len(withdoi)} without)")

    if args.only_missing_abstract:
        # The actionable question, rather than the general one. A random sample of the
        # whole corpus mostly re-checks records that already have abstracts. What matters
        # for Stage 1 is whether the records that CANNOT currently be screened normally
        # can be rescued, so those are censused rather than sampled.
        pool = [r for r in withdoi
                if r["is_oa"] == "1" and r.get("has_abstract") != "1"]
        print(f"restricting to eligible records with no abstract and a DOI: {len(pool)}")
        sample = pool
    else:
        rng = random.Random(args.seed)
        pool = withdoi
        sample = rng.sample(pool, min(args.sample, len(pool)))
    print(f"checking {len(sample)} DOIs (seed {args.seed})\n")

    found = notfound = 0
    gained_abstract = gained_abstract_oa = 0
    title_mismatch = year_mismatch = 0
    types: Counter = Counter()
    rows = []
    for i, r in enumerate(sample, 1):
        if i % 50 == 0:
            print(f"  {i}/{len(sample)}")
        msg = get(r["doi"])
        time.sleep(DELAY_S)
        if msg is None:
            notfound += 1
            rows.append({"record_id": r["record_id"], "doi": r["doi"],
                         "crossref": "not-registered"})
            continue
        found += 1
        types[msg.get("type", "")] += 1
        cr_abs = strip_jats(msg.get("abstract", ""))
        ours_abs = r.get("abstract", "")
        gain = bool(cr_abs) and not ours_abs
        if gain:
            gained_abstract += 1
            if r["is_oa"] == "1":
                gained_abstract_oa += 1
        cr_title = (msg.get("title") or [""])[0]
        tmm = bool(cr_title) and norm_title(cr_title) != norm_title(r["title"])
        if tmm:
            title_mismatch += 1
        d = issued_date(msg)
        ymm = bool(d) and r["year"] and str(d.year) != r["year"]
        if ymm:
            year_mismatch += 1
        rows.append({
            "record_id": r["record_id"], "doi": r["doi"], "crossref": "found",
            "crossref_type": msg.get("type", ""),
            "abstract_gained": "1" if gain else "",
            "title_mismatch": "1" if tmm else "",
            "year_mismatch": "1" if ymm else "",
            "crossref_date": d.isoformat() if d else "",
            "our_year": r["year"],
        })

    out = args.out or Path("data/raw/crossref_completeness_"
                           f"{datetime.now(timezone.utc):%Y%m%d}.json")
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "DOI-level metadata completeness check (search-strategy.md §1)",
        "corpus": str(args.corpus),
        "seed": args.seed,
        "sampled": len(sample),
        "registered_at_crossref": found,
        "not_registered": notfound,
        "abstract_present_at_crossref_but_missing_from_ours": gained_abstract,
        "  of_those_open_access": gained_abstract_oa,
        "title_mismatch": title_mismatch,
        "year_mismatch": year_mismatch,
        "crossref_types": dict(types.most_common()),
        "rows": rows,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1))

    print(f"\nregistered at Crossref              {found}/{len(sample)}")
    print(f"not registered                      {notfound}")
    print(f"abstract we lack but Crossref has   {gained_abstract} "
          f"({gained_abstract_oa} of them open access)")
    print(f"title mismatch                      {title_mismatch}")
    print(f"year mismatch                       {year_mismatch}")
    print(f"\n-> {out}")
    return 0


# ---------------------------------------------------------------- resolve-dates

def cmd_resolve_dates(args) -> int:
    payload = json.loads(args.source.read_text())
    recs = payload.get("records", [])
    corpus_path = args.corpus
    with corpus_path.open(newline="", encoding="utf-8") as fh:
        corpus = list(csv.DictReader(fh))
    dois = {(r["doi"] or "").lower() for r in corpus if r["doi"]}
    titles = {norm_title(r["title"]) for r in corpus if r["title"]}
    arx = {re.sub(r"v\d+$", "", (r["preprint_id"] or "").lower())
           for r in corpus if r["preprint_id"]}

    unmatched = [
        r for r in recs
        if not ((r.get("doi") and r["doi"] in dois)
                or (r.get("arxiv_id") and re.sub(r"v\d+$", "", r["arxiv_id"].lower()) in arx)
                or norm_title(r.get("title", "")) in titles)
    ]
    targets = [r for r in unmatched if r.get("doi")]
    print(f"{len(unmatched)} records in {args.source.name} are absent from the corpus")
    print(f"{len(targets)} of them carry a DOI and can be date-resolved "
          f"({len(unmatched) - len(targets)} cannot)\n")

    in_window = after_cutoff = before_window = unresolved = 0
    resolved_rows = []
    for i, r in enumerate(targets, 1):
        if i % 50 == 0:
            print(f"  {i}/{len(targets)}")
        msg = get(r["doi"])
        time.sleep(DELAY_S)
        d = issued_date(msg) if msg else None
        if d is None:
            unresolved += 1
            bucket = "unresolved"
        elif d > WINDOW_END:
            after_cutoff += 1
            bucket = "after-cutoff"
        elif d < WINDOW_START:
            before_window += 1
            bucket = "before-window"
        else:
            in_window += 1
            bucket = "in-window"
        resolved_rows.append({"doi": r["doi"], "title": r.get("title", ""),
                              "s2_year": r.get("year"),
                              "crossref_date": d.isoformat() if d else "",
                              "bucket": bucket})

    core = ("reservoir computing", "echo state", "liquid state machine",
            "physical reservoir")
    genuine = [r for r in resolved_rows if r["bucket"] == "in-window"
               and any(k in r["title"].lower() for k in core)]

    out = args.out or Path("data/raw/crossref_dateresolve_"
                           f"{datetime.now(timezone.utc):%Y%m%d}.json")
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "resolve year-granularity records from the Semantic Scholar leg "
                   "against the frozen window (search-strategy.md §1)",
        "source": str(args.source),
        "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()},
        "unmatched_total": len(unmatched),
        "unmatched_without_doi": len(unmatched) - len(targets),
        "date_resolved": {
            "in_window": in_window,
            "after_cutoff": after_cutoff,
            "before_window": before_window,
            "unresolved": unresolved,
        },
        "in_window_with_core_rc_phrase_in_title": len(genuine),
        "rows": resolved_rows,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1))

    print(f"\nunmatched with a DOI       {len(targets)}")
    print(f"  in window                {in_window}")
    print(f"  after the 2026-06-30 cut {after_cutoff}")
    print(f"  before the window        {before_window}")
    print(f"  unresolved               {unresolved}")
    print(f"\nin-window and carrying a core RC phrase in the title: {len(genuine)}")
    print(f"-> {out}")
    return 0


def cmd_selftest(args) -> int:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        ok = ok and cond

    check("JATS stripped",
          strip_jats("<jats:p>Hello <jats:italic>world</jats:italic></jats:p>")
          == "Hello world")
    check("issued date parsed",
          issued_date({"issued": {"date-parts": [[2021, 5, 3]]}}) == date(2021, 5, 3))
    check("partial date defaults to Jan 1",
          issued_date({"issued": {"date-parts": [[2021]]}}) == date(2021, 1, 1))
    check("earliest of issued/created wins",
          issued_date({"issued": {"date-parts": [[2021, 5, 3]]},
                       "created": {"date-parts": [[2020, 11, 1]]}}) == date(2020, 11, 1))
    check("no date -> None", issued_date({}) is None)
    check("invalid date ignored",
          issued_date({"issued": {"date-parts": [[2021, 13, 45]]}}) is None)
    check("title normalisation", norm_title("A  Réview: of Things!") == "a review of things")
    print("\nselftest", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("completeness", help="sample corpus DOIs, compare against Crossref")
    p.add_argument("--corpus", type=Path,
                   default=Path("data/screening/corpus_deduped.csv"))
    p.add_argument("--sample", type=int, default=400)
    p.add_argument("--seed", type=int, default=20260802)
    p.add_argument("--only-missing-abstract", action="store_true",
                   help="census the eligible records that currently have no abstract")
    p.add_argument("--out", type=Path, default=None)
    p.set_defaults(fn=cmd_completeness)

    p = sub.add_parser("resolve-dates",
                       help="date-resolve records another leg reports as unmatched")
    p.add_argument("--from", dest="source", type=Path, required=True)
    p.add_argument("--corpus", type=Path,
                   default=Path("data/screening/corpus_deduped.csv"))
    p.add_argument("--out", type=Path, default=None)
    p.set_defaults(fn=cmd_resolve_dates)

    sub.add_parser("selftest").set_defaults(fn=cmd_selftest)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
