#!/usr/bin/env python3
"""Retrieve arXiv records for the RC audit corpus.

Implements the arXiv leg of docs/search-strategy.md §2.4. Standard library only.

Window membership uses the **v1 submission date** (search-strategy.md §2.4), not the
latest version date, so a 2018 preprint revised in 2020 is correctly excluded.

Usage:
    python3 scripts/fetch_arxiv.py --out data/raw/arxiv_$(date +%Y%m%d).json

The output is a frozen search export. Never edit it by hand; re-run and re-date instead.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path

API = "http://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

# docs/search-strategy.md §2.4 — keep in sync with that file.
TERMS = [
    "reservoir computing",
    "echo state network",
    "liquid state machine",
    "physical reservoir",
    "next generation reservoir computing",
]

WINDOW_START = date(2019, 1, 1)
WINDOW_END = date(2026, 6, 30)  # frozen cutoff, protocol.md §3

PAGE = 100
# arXiv asks for >=3s between requests. Do not lower this; being rate-limited
# mid-harvest produces a partial export that looks complete.
DELAY_S = 3.0


def build_query() -> str:
    """Terms AND a server-side submittedDate range.

    The date range is not merely an optimisation. Results are sorted ascending by
    submission date, so without it the harvest pages through two decades of pre-window
    records first; if the safety ceiling were reached before 2019 the run would exit
    reporting zero in-window records while appearing to have succeeded. Filtering
    server-side makes that failure mode impossible.

    The client-side v1 check in main() is retained as defence in depth and to catch
    records with unparseable dates.
    """
    terms = " OR ".join(f'all:"{t}"' for t in TERMS)
    lo = WINDOW_START.strftime("%Y%m%d") + "0000"
    hi = WINDOW_END.strftime("%Y%m%d") + "2359"
    return f"({terms}) AND submittedDate:[{lo} TO {hi}]"


def fetch_page(query: str, start: int, retries: int = 3) -> bytes:
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": start,
            "max_results": PAGE,
            "sortBy": "submittedDate",
            "sortOrder": "ascending",
        }
    )
    url = f"{API}?{params}"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001 - network layer, report and retry
            last = exc
            wait = DELAY_S * (attempt + 2)
            print(f"  ! {exc} — retry in {wait:.0f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"failed after {retries} attempts: {last}")


def parse_entries(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    out: list[dict] = []
    for e in root.findall("a:entry", NS):
        raw_id = (e.findtext("a:id", default="", namespaces=NS) or "").strip()
        # https://arxiv.org/abs/2405.06561v2 -> 2405.06561
        arxiv_id = raw_id.rsplit("/abs/", 1)[-1].split("v")[0] if raw_id else ""
        published = (e.findtext("a:published", default="", namespaces=NS) or "").strip()
        doi = e.findtext("arxiv:doi", default="", namespaces=NS) or ""
        jref = e.findtext("arxiv:journal_ref", default="", namespaces=NS) or ""
        cats = [c.get("term", "") for c in e.findall("a:category", NS)]
        out.append(
            {
                "arxiv_id": arxiv_id,
                "title": " ".join((e.findtext("a:title", "", NS) or "").split()),
                "abstract": " ".join((e.findtext("a:summary", "", NS) or "").split()),
                "authors": [
                    (a.findtext("a:name", "", NS) or "").strip()
                    for a in e.findall("a:author", NS)
                ],
                "published_v1": published,
                "doi": doi.strip(),
                "journal_ref": jref.strip(),
                "categories": cats,
                "primary_category": cats[0] if cats else "",
            }
        )
    return out


def v1_date(entry: dict) -> date | None:
    raw = entry.get("published_v1") or ""
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").date()
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--max", type=int, default=6000, help="safety ceiling on records")
    args = ap.parse_args()

    query = build_query()
    print(f"query: {query}\nwindow: {WINDOW_START} .. {WINDOW_END}\n")

    seen: dict[str, dict] = {}
    start, empty_pages = 0, 0

    while start < args.max:
        print(f"  fetching {start}..{start + PAGE}", file=sys.stderr)
        entries = parse_entries(fetch_page(query, start))
        if not entries:
            empty_pages += 1
            if empty_pages >= 2:
                break
        else:
            empty_pages = 0
            for e in entries:
                if e["arxiv_id"]:
                    seen.setdefault(e["arxiv_id"], e)
        start += PAGE
        time.sleep(DELAY_S)

    all_records = list(seen.values())

    in_window, out_window, undated = [], 0, 0
    for e in all_records:
        d = v1_date(e)
        if d is None:
            undated += 1
            # Keep undated records and flag them: silently dropping records is
            # exactly the kind of invisible truncation this project exists to criticise.
            e["window_flag"] = "undated-manual-check"
            in_window.append(e)
        elif WINDOW_START <= d <= WINDOW_END:
            e["window_flag"] = "in-window"
            in_window.append(e)
        else:
            out_window += 1

    payload = {
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "terms": TERMS,
        "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()},
        "counts": {
            "unique_returned": len(all_records),
            "in_window": len(in_window),
            "out_of_window": out_window,
            "undated_kept_for_check": undated,
        },
        "records": in_window,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    c = payload["counts"]
    print(
        f"\nunique returned : {c['unique_returned']}\n"
        f"in window       : {c['in_window']}\n"
        f"out of window   : {c['out_of_window']}\n"
        f"undated (check) : {c['undated_kept_for_check']}\n"
        f"-> {args.out}\n\n"
        f"Record the in-window count in docs/search-strategy.md §6."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
