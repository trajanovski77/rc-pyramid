#!/usr/bin/env python3
"""Retrieve the supplementary search leg (docs/search-strategy.md §2.6).

    python3 scripts/fetch_supplementary.py --count-only                 # per-block totals
    python3 scripts/fetch_supplementary.py --out data/raw/supplementary_$(date +%Y%m%d).json
    python3 scripts/fetch_supplementary.py --out ... --blocks A E        # a subset
    python3 scripts/fetch_supplementary.py selftest                      # offline checks

Standard library only. The output is a frozen search export, like the two primary ones:
never edit it by hand; re-run and re-date instead. `scripts/supplement.py` merges it into
a *separate* candidate file; the frozen corpus is never touched.

WHY THIS LEG EXISTS
-------------------
IEEE Reviewer 1 (point 4b) asked whether the six executed phrases miss device-level work
that does not call itself "reservoir computing". It does. On 2026-10-24 an OpenAlex probe
found 192 in-window works carrying the phrase "reservoir computer" without any of the six
executed phrases, and 133 of them are absent from the frozen corpus; none of 19 device
papers found by a citation search was retrievable by the six phrases. The §2.5 conclusion
that stemming covered the gap was drawn from single-record probes and does not hold for
the population. This leg is the correction, reported as "identification via other
methods" in the PRISMA 2020 flow.

WHAT IS RETRIEVED
-----------------
`BLOCKS` below, each a positive query:
  A-D, F4   vocabulary searches (device and physical-computing terms the six phrases lack)
  E         works citing eight seed papers of physical reservoir computing, AND a temporal
            clause
  G         works citing the reservoir-computing toolkits
  H         OpenAlex-linked backward search: the works the 11 reviews of Table 3 cite
  xA-xC     the arXiv counterparts of A-C
Every block applies the frozen window (2019-01-01 .. 2026-06-30) and, in OpenAlex,
`language:en`, exactly as the primary legs do.

WHY THERE IS NO "NOT <original phrases>" CLAUSE
-----------------------------------------------
The first draft excluded the six phrases server-side. That is unreliable: the OpenAlex
index drifts (the same six-phrase filter returned 6,501 works on 2026-07-31 and 7,064 on
2026-10-24), so a server-side NOT would silently decide which drifted records count as
"found by the supplement". Instead every block is retrieved positively, and
`supplement.py` removes works already in the frozen corpus locally and flags each new one
with `matches_orig_literal`, so index-drift additions and vocabulary additions are reported
separately.

FAILURE RULES
-------------
A partial export that looks complete is the failure this project studies, so:
  * HTTP 429 (budget or rate limit) aborts the run and writes nothing.
  * Any other 4xx aborts (a malformed query is not a transient error).
  * 5xx and network errors are retried with backoff, then abort.
  * A block larger than --max-per-block aborts before paging.
  * Every seed DOI must resolve to an OpenAlex work, or the run aborts.
  * arXiv: an error entry in the feed aborts; retrieved records are reconciled with the
    feed's totalResults before the client-side date check, and an unexplained gap aborts.

OPENALEX BUDGET AND KEY
-----------------------
OpenAlex meters its API. Without a key the shared daily budget is small, and cursor paging
past the first page needs a key, so a block that needs more than one page aborts cleanly
when no key is set. The key is read from the environment only (`OPENALEX_API_KEY`, the same
variable as fetch_openalex.py), sent as the `api_key` parameter, and never printed, logged or
written into the export: the export records only whether a key was used. The last
`X-RateLimit-*` headers seen are recorded so the budget a run consumed is visible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_arxiv  # noqa: E402
import fetch_openalex  # noqa: E402
from fetch_arxiv import NS, parse_entries, v1_date  # noqa: E402
from fetch_openalex import WINDOW_END, WINDOW_START, flatten  # noqa: E402

OPENALEX_API = fetch_openalex.API
ARXIV_API = fetch_arxiv.API
OPENSEARCH_NS = "http://a9.com/-/spec/opensearch/1.1/"

PER_PAGE = 100            # the metered API's page size; 200 is no longer accepted keyless
OPENALEX_DELAY_S = 0.25   # pace every request, keyed or not
ARXIV_PAGE = 100
ARXIV_DELAY_S = 3.0       # arXiv's stated floor. Do not lower it (see fetch_arxiv.py).
ID_BATCH = 50             # OpenAlex accepts up to 100 OR-values per filter; stay well under
MAX_URL_BYTES = 4094      # OpenAlex rejects longer request lines
SHORT_PAGE_RETRIES = 3

MAILTO = fetch_openalex.MAILTO

# Only the fields `fetch_openalex.flatten` reads, so the records are identical in shape to
# the primary harvest's while the responses stay small.
SELECT = ("id,doi,display_name,abstract_inverted_index,authorships,publication_year,"
          "primary_location,type,open_access,cited_by_count")

# Keep in sync with docs/search-strategy.md §2.6. Each block is a positive query; see the
# module docstring for why none of them excludes the original phrases server-side.
BLOCKS: list[dict] = [
    {"id": "A", "engine": "openalex", "kind": "search",
     "query": '"reservoir computer" OR "reservoir computers" OR "delay-based reservoir" OR '
              '"time-delay reservoir" OR "delayed feedback reservoir" OR '
              '"single dynamical node" OR "single nonlinear node" OR "memristive reservoir" OR '
              '"memristor reservoir" OR "photonic reservoir" OR "spintronic reservoir" OR '
              '"optoelectronic reservoir" OR "simple cycle reservoir" OR "cyclic reservoir" OR '
              '"spiking reservoir"'},
    {"id": "B1", "engine": "openalex", "kind": "search",
     "query": '("volatile memristor" OR "diffusive memristor" OR "dynamic memristor" OR '
              '"threshold switching memristor" OR "volatile resistive switching" OR '
              '"volatile threshold switching") AND (temporal OR "time series" OR '
              'spatiotemporal OR sequential)'},
    {"id": "B2", "engine": "openalex", "kind": "search",
     "query": '("short-term plasticity" OR "short-term memory" OR "fading memory") AND '
              '(memristor OR memristive OR "synaptic transistor" OR "synaptic device" OR '
              'ferroelectric OR "electrolyte-gated" OR "electrochemical transistor" OR '
              'spintronic OR "magnetic tunnel junction") AND (temporal OR "time series" OR '
              'spatiotemporal) AND (classification OR recognition OR forecasting OR '
              'prediction)'},
    {"id": "B3", "engine": "openalex", "kind": "search",
     "query": '(FeFET OR "ferroelectric field-effect transistor" OR "ferroelectric transistor" '
              'OR ECRAM OR "electrochemical random-access memory" OR "charge-trap transistor" '
              'OR "floating-gate") AND ("short-term" OR volatile OR "fading memory" OR '
              '"temporal dynamics") AND (temporal OR "time series" OR spatiotemporal)'},
    {"id": "C", "engine": "openalex", "kind": "search",
     "query": '("in-materio computing" OR "in materio computing" OR "in-materia computing" OR '
              '"in materia computing" OR "dopant network" OR "physical neural network" OR '
              '"physical neural networks" OR "physical computing") AND (temporal OR '
              '"time series" OR spatiotemporal OR "short-term memory" OR "fading memory") AND '
              '(device OR devices OR hardware OR memristor OR memristive OR material OR '
              'materials OR photonic OR spintronic OR nanowire)'},
    {"id": "D", "engine": "openalex", "kind": "search",
     "query": '("analog CMOS" OR "analogue CMOS" OR "mixed-signal" OR subthreshold OR '
              '"analog circuit" OR "analogue circuit") AND ("temporal signal processing" OR '
              '"time series" OR "time-series" OR spatiotemporal) AND (neuromorphic OR '
              '"neural network" OR spiking)'},
    {"id": "F4", "engine": "openalex", "kind": "search",
     "query": '("in materio" OR "in-materio" OR "morphological computation" OR '
              '"physical learning") AND (reservoir OR "temporal processing")'},
    # Fixed seeds stand in for search-strategy.md §4's "five most-cited included records per
    # family", which cannot exist before screening (deviation D31).
    {"id": "E", "engine": "openalex", "kind": "cites",
     "seeds_doi": ["10.1038/ncomms1476", "10.1038/s41467-017-02337-y", "10.1038/nature23011",
                   "10.1038/s41928-019-0313-3", "10.1038/s41467-020-20692-1",
                   "10.1038/s41563-021-01099-9", "10.1038/s41928-022-00838-3",
                   "10.1038/s41467-022-29260-1"],
     "and_query": 'temporal OR "time series" OR spatiotemporal OR "short-term memory" OR '
                  '"fading memory"'},
    {"id": "G", "engine": "openalex", "kind": "cites",
     "seeds_doi": ["10.1007/978-3-030-61616-8_40", "10.1016/j.engappai.2022.104964",
                   "10.1088/2634-4386/ae441f", "10.1038/s41467-024-44900-4",
                   "10.48550/arxiv.2204.05117"]},
    # The 11 reviews of manuscript Table 3. Backward search through OpenAlex's
    # `referenced_works` links, so a reference OpenAlex did not link is not found.
    {"id": "H", "engine": "openalex", "kind": "references",
     "seeds_doi": ["10.1016/j.cosrev.2009.03.005", "10.1016/j.neunet.2019.03.005",
                   "10.35848/1347-4065/ab8d4f", "10.1088/2634-4386/ac7db7",
                   "10.1109/access.2023.3299296", "10.1038/s41467-024-45187-1",
                   "10.1038/s41928-024-01133-z", "10.1038/s42254-024-00729-w",
                   "10.1080/17445760.2025.2472211", "10.3390/ai7020070",
                   "10.1088/2515-7647/ae2e67"]},
    {"id": "xA", "engine": "arxiv", "kind": "search",
     "query": 'all:"reservoir computer" OR all:"delay-based reservoir" OR '
              'all:"time-delay reservoir" OR all:"delayed feedback reservoir" OR '
              'all:"memristive reservoir" OR all:"photonic reservoir" OR '
              'all:"spintronic reservoir" OR all:"spiking reservoir"'},
    {"id": "xB", "engine": "arxiv", "kind": "search",
     "query": '(all:"volatile memristor" OR all:"diffusive memristor" OR '
              'all:"dynamic memristor" OR all:"short-term plasticity") AND '
              '(all:temporal OR all:"time series")'},
    {"id": "xC", "engine": "arxiv", "kind": "search",
     "query": '(all:"in materio" OR all:"physical neural network" OR '
              'all:"morphological computation" OR all:"physical learning") AND '
              '(all:temporal OR all:"time series" OR all:reservoir)'},
]
BLOCK_IDS = [b["id"] for b in BLOCKS]


class Abort(RuntimeError):
    """A condition under which the run must stop and write nothing."""


# ---------------------------------------------------------------- filters (pure)

def base_filter() -> str:
    return (f"from_publication_date:{WINDOW_START.isoformat()},"
            f"to_publication_date:{WINDOW_END.isoformat()},language:en")


def search_filter(query: str) -> str:
    return f"{base_filter()},title_and_abstract.search:{query}"


def cites_filter(ids: list[str], and_query: str | None) -> str:
    f = f"{base_filter()},cites:{'|'.join(ids)}"
    return f + (f",title_and_abstract.search:{and_query}" if and_query else "")


def ids_filter(ids: list[str]) -> str:
    return f"{base_filter()},openalex:{'|'.join(ids)}"


def arxiv_query(query: str) -> str:
    lo = WINDOW_START.strftime("%Y%m%d") + "0000"
    hi = WINDOW_END.strftime("%Y%m%d") + "2359"
    return f"({query}) AND submittedDate:[{lo} TO {hi}]"


def batches(items: list[str], size: int = ID_BATCH) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def short_id(url_or_id: str) -> str:
    return (url_or_id or "").rsplit("/", 1)[-1]


# ---------------------------------------------------------------- network

class OpenAlexClient:
    """One place where requests are made, so the key is added and redacted in one place.

    `_fetch` is the only method that touches the network; the selftest overrides it.
    """

    def __init__(self, api_key: str = "", delay: float = OPENALEX_DELAY_S):
        self.api_key = api_key
        self.delay = delay
        self.requests: list[dict] = []
        self.ratelimit: dict[str, str] = {}

    def redact(self, text: str) -> str:
        return text.replace(self.api_key, "***") if self.api_key else text

    def url(self, params: dict) -> str:
        full = {**params, "mailto": MAILTO}
        if self.api_key:
            full["api_key"] = self.api_key
        return OPENALEX_API + "?" + urllib.parse.urlencode(full)

    def _fetch(self, url: str) -> tuple[dict, dict]:
        req = urllib.request.Request(url, headers={"User-Agent": f"rc-audit/0.1 (mailto:{MAILTO})"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read()), dict(r.headers.items())

    def get(self, params: dict, label: str, retries: int = 4) -> dict:
        url = self.url(params)
        if len(url.encode()) > MAX_URL_BYTES:
            raise Abort(f"{label}: request line is {len(url.encode())} bytes, over the "
                        f"{MAX_URL_BYTES}-byte limit; use a smaller id batch")
        last = ""
        for attempt in range(retries):
            try:
                data, headers = self._fetch(url)
            except urllib.error.HTTPError as exc:
                body = ""
                try:
                    body = exc.read().decode("utf-8", "replace")[:300]
                except Exception:  # noqa: BLE001 - diagnostics only
                    pass
                if exc.code == 429:
                    raise Abort(f"{label}: HTTP 429 from OpenAlex (budget or rate limit "
                                f"exhausted). Nothing was written. Set OPENALEX_API_KEY or "
                                f"wait for the daily reset. {self.redact(body)}") from None
                if 400 <= exc.code < 500:
                    raise Abort(f"{label}: HTTP {exc.code} from OpenAlex, which is not "
                                f"transient: {self.redact(body)}") from None
                last = f"HTTP {exc.code}"
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as exc:
                last = self.redact(str(exc))
            else:
                for k, v in headers.items():
                    if k.lower().startswith("x-ratelimit"):
                        self.ratelimit[k.lower()] = v
                time.sleep(self.delay)
                return data
            wait = 2 ** attempt
            print(f"  ! {label}: {last}; retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
        raise Abort(f"{label}: failed after {retries} attempts ({last})")

    def log(self, block: str, n: int, reported: int | None, returned: int) -> None:
        self.requests.append({"block": block, "request": n, "reported": reported,
                              "returned": returned})

    def resolve_dois(self, block: str, dois: list[str]) -> dict[str, list[str]]:
        """DOI -> OpenAlex work ids, plus each work's referenced_works (for block H).

        Returns {doi: [W...]} and stores the references on `self.references`. Every seed
        must resolve: a cites or references block built on a silently missing seed is a
        smaller search that reports itself as the specified one.
        """
        self.references: dict[str, list[str]] = {}
        out: dict[str, list[str]] = {d: [] for d in dois}
        for n, batch in enumerate(batches(sorted(dois)), 1):
            d = self.get({"filter": "doi:" + "|".join(batch), "per-page": PER_PAGE,
                          "select": "id,doi,referenced_works"}, f"{block} seeds")
            self.log(block + ":seeds", n, d["meta"].get("count"), len(d["results"]))
            for w in d["results"]:
                doi = fetch_openalex_norm_doi(w.get("doi") or "")
                wid = short_id(w.get("id") or "")
                if doi in out and wid:
                    out[doi].append(wid)
                    self.references[wid] = sorted(short_id(r) for r in
                                                  (w.get("referenced_works") or []))
        missing = [doi for doi, ids in out.items() if not ids]
        if missing:
            raise Abort(f"{block}: seed DOIs did not resolve in OpenAlex: {missing}")
        return {doi: sorted(set(ids)) for doi, ids in sorted(out.items())}

    def harvest(self, block: str, filt: str, max_records: int) -> tuple[list[dict], int]:
        """Cursor-page one filter. Returns (raw works, reported total)."""
        out: list[dict] = []
        cursor, total, n = "*", None, 0
        while cursor:
            n += 1
            d = self.get({"filter": filt, "per-page": PER_PAGE, "cursor": cursor,
                          "select": SELECT}, f"{block} page {n}")
            if total is None:
                total = int(d["meta"]["count"])
                if total > max_records:
                    raise Abort(f"{block}: {total} works exceed --max-per-block "
                                f"{max_records}; narrow the block or raise the ceiling")
                if total > PER_PAGE and not self.api_key:
                    raise Abort(f"{block}: {total} works need cursor paging, which the "
                                f"metered OpenAlex API allows only with a key. Set "
                                f"OPENALEX_API_KEY and re-run. Nothing was written.")
            self.log(block, n, total, len(d["results"]))
            out.extend(d["results"])
            if not d["results"]:
                break
            cursor = d["meta"].get("next_cursor")
        return out, (total or 0)


def fetch_openalex_norm_doi(d: str) -> str:
    d = (d or "").strip().lower()
    return re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d).strip()


class ArxivClient:
    """arXiv paging with feed validation. `_fetch` is overridden by the selftest."""

    def __init__(self, delay: float = ARXIV_DELAY_S):
        self.delay = delay
        self.requests: list[dict] = []

    def _fetch(self, params: dict) -> bytes:
        url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()

    def page(self, query: str, start: int, label: str, retries: int = 3) -> tuple[list[dict], int]:
        params = {"search_query": query, "start": start, "max_results": ARXIV_PAGE,
                  "sortBy": "submittedDate", "sortOrder": "ascending"}
        last = ""
        for attempt in range(retries):
            try:
                raw = self._fetch(params)
            except urllib.error.HTTPError as exc:
                if exc.code == 429 or 400 <= exc.code < 500:
                    raise Abort(f"{label}: HTTP {exc.code} from arXiv. Nothing was "
                                f"written.") from None
                last = f"HTTP {exc.code}"
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as exc:
                last = str(exc)
            else:
                time.sleep(self.delay)
                return parse_feed(raw, label)
            wait = self.delay * (attempt + 2)
            print(f"  ! {label}: {last}; retry in {wait:.0f}s", file=sys.stderr)
            time.sleep(wait)
        raise Abort(f"{label}: failed after {retries} attempts ({last})")


def parse_feed(raw: bytes, label: str) -> tuple[list[dict], int]:
    """Entries and totalResults of one arXiv Atom page; an API error entry aborts."""
    root = ET.fromstring(raw)
    for e in root.findall("a:entry", NS):
        eid = e.findtext("a:id", default="", namespaces=NS) or ""
        if "api/errors" in eid:
            summary = " ".join((e.findtext("a:summary", "", NS) or "").split())
            raise Abort(f"{label}: arXiv API error: {summary}")
    total_txt = root.findtext(f"{{{OPENSEARCH_NS}}}totalResults")
    if total_txt is None or not total_txt.strip().isdigit():
        raise Abort(f"{label}: arXiv feed carries no totalResults; cannot reconcile")
    return parse_entries(raw), int(total_txt)


# ---------------------------------------------------------------- blocks

def run_openalex_block(client: OpenAlexClient, block: dict, max_records: int,
                       count_only: bool) -> tuple[list[dict], dict, dict]:
    """Returns (flattened records, resolved snapshot data, counts)."""
    bid, kind = block["id"], block["kind"]
    resolved: dict = {}
    if kind == "search":
        filters = [search_filter(block["query"])]
    elif kind == "cites":
        seeds = client.resolve_dois(bid, block["seeds_doi"])
        ids = sorted({w for ws in seeds.values() for w in ws})
        resolved["seed_ids"] = seeds
        filters = [cites_filter(ids, block.get("and_query"))]
    elif kind == "references":
        seeds = client.resolve_dois(bid, block["seeds_doi"])
        refs = sorted({r for ws in seeds.values() for w in ws for r in client.references[w]})
        resolved["seed_ids"] = seeds
        resolved["reference_ids"] = refs
        filters = [ids_filter(b) for b in batches(refs)]
    else:
        raise ValueError(f"unknown kind {kind!r}")
    resolved["filters"] = filters

    works: list[dict] = []
    reported = 0
    for n, f in enumerate(filters, 1):
        label = bid if len(filters) == 1 else f"{bid} batch {n}/{len(filters)}"
        if count_only:
            d = client.get({"filter": f, "per-page": 1, "select": "id"}, label)
            reported += int(d["meta"]["count"])
            client.log(bid, n, int(d["meta"]["count"]), 0)
            continue
        got, total = client.harvest(label, f, max_records - len(works))
        works.extend(got)
        reported += total
    recs: dict[str, dict] = {}
    for w in works:
        r = flatten(w)
        if r["openalex_id"]:
            recs.setdefault(r["openalex_id"], r)
    counts = {"reported_total": reported, "retrieved_rows": len(works),
              "retrieved_unique": len(recs)}
    if not count_only and len(recs) != reported:
        # Page boundaries can shift while a cursor is open and the index changes under it.
        # Recorded, not fatal: the counts are in the export for anyone to reconcile.
        print(f"  ! {bid}: reported {reported}, retrieved {len(recs)} unique", file=sys.stderr)
    return list(recs.values()), resolved, counts


def run_arxiv_block(client: ArxivClient, block: dict, max_records: int, count_only: bool,
                    gap_tolerance: int) -> tuple[list[dict], dict, dict]:
    bid = block["id"]
    query = arxiv_query(block["query"])
    entries, total = client.page(query, 0, f"{bid} start 0")
    client.requests.append({"block": bid, "start": 0, "reported": total,
                            "returned": len(entries)})
    if total > max_records:
        raise Abort(f"{bid}: {total} records exceed --max-per-block {max_records}")
    if count_only:
        return [], {"query": query}, {"reported_total": total}
    seen: dict[str, dict] = {}
    start = 0
    while True:
        expected = min(ARXIV_PAGE, max(total - start, 0))
        tries = 0
        while len(entries) < expected and tries < SHORT_PAGE_RETRIES:
            tries += 1
            entries, total = client.page(query, start, f"{bid} start {start} retry {tries}")
            client.requests.append({"block": bid, "start": start, "reported": total,
                                    "returned": len(entries)})
            expected = min(ARXIV_PAGE, max(total - start, 0))
        for e in entries:
            if e["arxiv_id"]:
                seen.setdefault(e["arxiv_id"], e)
        start += ARXIV_PAGE
        if start >= total:
            break
        entries, total = client.page(query, start, f"{bid} start {start}")
        client.requests.append({"block": bid, "start": start, "reported": total,
                                "returned": len(entries)})
    gap = total - len(seen)
    if gap > gap_tolerance:
        raise Abort(f"{bid}: arXiv reported {total} records but {len(seen)} were retrieved "
                    f"after retries; a gap of {gap} is over the tolerance of {gap_tolerance}. "
                    f"Nothing was written.")
    in_window, out_window, undated = [], 0, 0
    for e in seen.values():
        d = v1_date(e)
        if d is None:
            e["window_flag"] = "undated-manual-check"
            in_window.append(e)
        elif WINDOW_START <= d <= WINDOW_END:
            e["window_flag"] = "in-window"
            in_window.append(e)
        else:
            out_window += 1
    counts = {"reported_total": total, "retrieved_unique": len(seen), "gap": gap,
              "in_window": len(in_window), "out_of_window": out_window,
              "undated_kept_for_check": undated}
    return in_window, {"query": query}, counts


def collect(per_block: list[tuple[dict, list[dict]]]) -> list[dict]:
    """Merge records across blocks by identity; each keeps its blocks in BLOCKS order."""
    order = {b: i for i, b in enumerate(BLOCK_IDS)}
    merged: dict[tuple[str, str], dict] = {}
    for block, recs in per_block:
        for r in recs:
            key = ("openalex", r["openalex_id"]) if block["engine"] == "openalex" \
                else ("arxiv", r["arxiv_id"])
            if key not in merged:
                merged[key] = {**r, "engine": block["engine"], "blocks": []}
            if block["id"] not in merged[key]["blocks"]:
                merged[key]["blocks"].append(block["id"])
    for r in merged.values():
        r["blocks"].sort(key=order.__getitem__)
    return [merged[k] for k in sorted(merged)]


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def run(selected: list[str], oa: OpenAlexClient, ax: ArxivClient, max_per_block: int,
        count_only: bool, gap_tolerance: int) -> dict:
    """Execute the selected blocks and return the export payload. Raises Abort."""
    per_block: list[tuple[dict, list[dict]]] = []
    snap_blocks, counts = [], {}
    for block in BLOCKS:
        if block["id"] not in selected:
            continue
        print(f"  block {block['id']} ({block['engine']}, {block['kind']})", file=sys.stderr)
        if block["engine"] == "openalex":
            recs, resolved, c = run_openalex_block(oa, block, max_per_block, count_only)
        else:
            recs, resolved, c = run_arxiv_block(ax, block, max_per_block, count_only,
                                                gap_tolerance)
        per_block.append((block, recs))
        snap_blocks.append({**block, "resolved": resolved})
        counts[block["id"]] = c
        print(f"    {c}", file=sys.stderr)
    records = collect(per_block)
    return {
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "source": "supplementary",
        "script_sha256": script_sha256(),
        "count_only": count_only,
        "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()},
        "openalex_per_page": PER_PAGE,
        "openalex_api_key_used": bool(oa.api_key),
        "orig_terms": {"openalex": list(fetch_openalex.TERMS), "arxiv": list(fetch_arxiv.TERMS)},
        "blocks": snap_blocks,
        "counts": counts,
        "requests": {"openalex": oa.requests, "arxiv": ax.requests},
        "openalex_ratelimit_last": oa.ratelimit,
        "records": records,
    }


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    """Offline only: the network layer is replaced by canned responses."""
    ok = True

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        ok = ok and cond

    def work(n: int, title: str, doi: str = "", refs: list[str] | None = None) -> dict:
        return {"id": f"https://openalex.org/W{n}", "doi": f"https://doi.org/{doi}" if doi else None,
                "display_name": title, "abstract_inverted_index": {"time": [0], "series": [1]},
                "authorships": [{"author": {"display_name": "A. Author"}}],
                "publication_year": 2022, "primary_location": {"source": {"display_name": "J"}},
                "type": "article", "open_access": {"is_oa": True, "oa_status": "gold"},
                "cited_by_count": 3,
                "referenced_works": [f"https://openalex.org/{r}" for r in (refs or [])]}

    SECRET = "SECRETKEY-do-not-leak-123"

    class FakeOA(OpenAlexClient):
        def __init__(self, pages, key=SECRET, fail=None):
            super().__init__(api_key=key, delay=0)
            self.pages, self.fail, self.seen_urls = pages, fail, []

        def _fetch(self, url):
            self.seen_urls.append(url)
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            if self.fail:
                raise self.fail
            return self.pages(q), {"X-RateLimit-Remaining": "99", "Content-Type": "json"}

    # filters
    base = "from_publication_date:2019-01-01,to_publication_date:2026-06-30,language:en"
    check("base filter applies the frozen window and language", base_filter() == base)
    check("search filter is positive (no server-side NOT)",
          all(" NOT " not in search_filter(b["query"]) for b in BLOCKS if b["kind"] == "search"))
    check("cites filter ORs the seeds and adds the temporal clause",
          cites_filter(["W1", "W2"], "temporal") ==
          base + ",cites:W1|W2,title_and_abstract.search:temporal")
    check("cites filter without and_query has no search clause",
          cites_filter(["W1"], None) == base + ",cites:W1")
    check("arXiv query applies the window server-side",
          arxiv_query('all:"x"') == '(all:"x") AND submittedDate:[201901010000 TO 202606302359]')
    check("no filter value contains a comma inside a query",
          all("," not in b.get("query", "") + b.get("and_query", "") for b in BLOCKS))
    big = [f"W{4_000_000_000 + i}" for i in range(2000)]
    bs = batches(big)
    url_len = max(len(OpenAlexClient(api_key="k" * 40).url(
        {"filter": ids_filter(b), "per-page": PER_PAGE, "cursor": "*", "select": SELECT}
    ).encode()) for b in bs)
    check("id batches hold at most 50 values and cover every id",
          all(len(b) <= 50 for b in bs) and sum(bs, []) == big)
    check(f"worst-case id-batch request is under {MAX_URL_BYTES} bytes ({url_len})",
          url_len < MAX_URL_BYTES)
    check("block ids are unique and seeds are lower-case DOIs",
          len(set(BLOCK_IDS)) == len(BLOCK_IDS)
          and all(d == d.lower() for b in BLOCKS for d in b.get("seeds_doi", [])))
    check("arXiv delay respects the API's stated 3s floor", ARXIV_DELAY_S >= 3.0)

    # search block, two pages, with a key
    def pages_search(q):
        if q.get("cursor") == ["*"]:
            return {"meta": {"count": 150, "next_cursor": "c2"},
                    "results": [work(i, f"Title {i}") for i in range(1, 101)]}
        if q.get("cursor") == ["c2"]:
            return {"meta": {"count": 150, "next_cursor": "c3"},
                    "results": [work(i, f"Title {i}") for i in range(101, 151)]}
        return {"meta": {"count": 150, "next_cursor": None}, "results": []}

    oa = FakeOA(pages_search)
    recs, _res, c = run_openalex_block(oa, BLOCKS[0], 5000, False)
    check("cursor paging retrieves every work across pages",
          len(recs) == 150 and c == {"reported_total": 150, "retrieved_rows": 150,
                                     "retrieved_unique": 150})
    check("records have exactly the primary harvest's fields",
          set(recs[0]) == set(flatten(work(1, "t"))))
    check("per-page is 100 and select is sent",
          all("per-page=100" in u and "select=" in u for u in oa.seen_urls))
    check("rate-limit headers are recorded", oa.ratelimit.get("x-ratelimit-remaining") == "99")

    # paging without a key aborts before page 2
    oa_nokey = FakeOA(pages_search, key="")
    try:
        run_openalex_block(oa_nokey, BLOCKS[0], 5000, False)
        aborted = False
    except Abort as exc:
        aborted = "OPENALEX_API_KEY" in str(exc)
    check("a multi-page block without a key aborts with a clear message",
          aborted and len(oa_nokey.seen_urls) == 1)

    # ceiling
    try:
        run_openalex_block(FakeOA(pages_search), BLOCKS[0], 100, False)
        aborted = False
    except Abort:
        aborted = True
    check("a block over --max-per-block aborts", aborted)

    # 429 aborts, other 4xx aborts, nothing retried
    def http(code):
        return urllib.error.HTTPError("u", code, "x", {}, None)

    for code in (429, 400):
        oa_err = FakeOA(pages_search, fail=http(code))
        try:
            run_openalex_block(oa_err, BLOCKS[0], 5000, False)
            aborted = False
        except Abort as exc:
            aborted = f"{code}" in str(exc) and SECRET not in str(exc)
        check(f"HTTP {code} aborts without retrying and without leaking the key",
              aborted and len(oa_err.seen_urls) == 1)

    # cites block: seeds resolve, unresolved seed aborts
    e_block = next(b for b in BLOCKS if b["id"] == "E")

    def pages_cites(q):
        f = q["filter"][0]
        if f.startswith("doi:"):
            dois = f[4:].split("|")
            return {"meta": {"count": len(dois)},
                    "results": [work(9000 + i, "seed", d) for i, d in enumerate(dois)]}
        return {"meta": {"count": 2, "next_cursor": None},
                "results": [work(1, "Title 1"), work(77, "Cites a seed")]}

    oa = FakeOA(pages_cites)
    recs, res, _c = run_openalex_block(oa, e_block, 5000, False)
    check("every cites seed resolves to an OpenAlex id",
          sorted(res["seed_ids"]) == sorted(e_block["seeds_doi"])
          and all(len(v) == 1 for v in res["seed_ids"].values()))
    check("cites filter carries all resolved seeds and the temporal clause",
          res["filters"][0].count("|") == len(e_block["seeds_doi"]) - 1
          and "title_and_abstract.search:" in res["filters"][0])

    def pages_missing(q):
        f = q["filter"][0]
        dois = f[4:].split("|")[1:]
        return {"meta": {"count": len(dois)},
                "results": [work(9000 + i, "seed", d) for i, d in enumerate(dois)]}

    try:
        run_openalex_block(FakeOA(pages_missing), e_block, 5000, False)
        aborted = False
    except Abort as exc:
        aborted = "did not resolve" in str(exc)
    check("an unresolved seed aborts the run", aborted)

    # references block
    h_block = next(b for b in BLOCKS if b["id"] == "H")
    ref_ids = [f"W{500 + i}" for i in range(120)]

    def pages_refs(q):
        f = q["filter"][0]
        if f.startswith("doi:"):
            dois = f[4:].split("|")
            return {"meta": {"count": len(dois)},
                    "results": [work(9000 + i, "review", d, ref_ids[i * 10:(i + 1) * 10 + 5])
                                for i, d in enumerate(dois)]}
        ids = f.split(",openalex:")[1].split("|")
        keep = [i for i in ids if int(i[1:]) % 2 == 0]   # the window drops half
        return {"meta": {"count": len(keep), "next_cursor": None},
                "results": [work(int(i[1:]), f"Ref {i}") for i in keep]}

    oa = FakeOA(pages_refs)
    recs, res, c = run_openalex_block(oa, h_block, 5000, False)
    check("H unions the reviews' references and freezes the id set",
          res["reference_ids"] == sorted(set(ref_ids[:115])))
    check("H fetches references in id batches with the window applied",
          all(f.startswith(base + ",openalex:") for f in res["filters"])
          and len(res["filters"]) == len(batches(res["reference_ids"])))
    check("H keeps only in-window references",
          len(recs) == sum(1 for i in res["reference_ids"] if int(i[1:]) % 2 == 0))

    # arXiv
    def feed(total: int, ids: list[int], error: str = "") -> bytes:
        ents = "".join(
            f"<entry><id>http://arxiv.org/abs/2101.{i:05d}v1</id><title>T {i}</title>"
            f"<summary>s</summary><published>2021-01-0{1 + i % 8}T00:00:00Z</published>"
            f"<author><name>A</name></author></entry>" for i in ids)
        if error:
            ents = (f"<entry><id>http://arxiv.org/api/errors#x</id><title>Error</title>"
                    f"<summary>{error}</summary></entry>")
        return (f'<feed xmlns="http://www.w3.org/2005/Atom" '
                f'xmlns:opensearch="{OPENSEARCH_NS}"><opensearch:totalResults>{total}'
                f"</opensearch:totalResults>{ents}</feed>").encode()

    class FakeAX(ArxivClient):
        def __init__(self, responder):
            super().__init__(delay=0)
            self.responder, self.calls = responder, 0

        def _fetch(self, params):
            self.calls += 1
            return self.responder(params["start"], self.calls)

    xa = next(b for b in BLOCKS if b["id"] == "xA")
    ax = FakeAX(lambda s, _n: feed(150, list(range(s, min(s + 100, 150)))))
    recs, res, c = run_arxiv_block(ax, xa, 5000, False, 0)
    check("arXiv pages until totalResults and reconciles", c["retrieved_unique"] == 150
          and c["gap"] == 0 and len(recs) == 150)
    check("arXiv records carry window_flag as the primary leg does",
          all(r["window_flag"] == "in-window" for r in recs))

    # a short page is retried; a persistent gap aborts
    ax = FakeAX(lambda s, n: feed(150, list(range(s, min(s + 100, 150)))
                                   if not (s == 100 and n == 2) else list(range(100, 120))))
    recs, _res, c = run_arxiv_block(ax, xa, 5000, False, 0)
    check("a transiently short arXiv page is retried", c["retrieved_unique"] == 150)
    ax = FakeAX(lambda s, _n: feed(150, list(range(s, min(s + 100, 140)))))
    try:
        run_arxiv_block(ax, xa, 5000, False, 0)
        aborted = False
    except Abort as exc:
        aborted = "gap" in str(exc)
    check("a persistent arXiv gap aborts", aborted)
    try:
        run_arxiv_block(FakeAX(lambda s, _n: feed(0, [], error="bad query")), xa, 5000, False, 0)
        aborted = False
    except Abort as exc:
        aborted = "bad query" in str(exc)
    check("an arXiv API error entry aborts", aborted)

    # merge across blocks, ordering, key never in the export
    a_block, e_block = BLOCKS[0], next(b for b in BLOCKS if b["id"] == "E")
    r1, r2 = flatten(work(5, "Same work")), flatten(work(3, "Other"))
    merged = collect([(e_block, [r1]), (a_block, [r1, r2])])
    check("a work found by two blocks is one record listing both, in BLOCKS order",
          len(merged) == 2 and [m["blocks"] for m in merged if m["openalex_id"] == "W5"]
          == [["A", "E"]])
    check("records are ordered deterministically by engine and id",
          [m["openalex_id"] for m in merged] == ["W3", "W5"])

    oa = FakeOA(pages_cites)
    payload = run(["E"], oa, FakeAX(lambda s, n: feed(0, [])), 5000, False, 0)
    blob = json.dumps(payload)
    check("the API key never appears in the export", SECRET not in blob
          and payload["openalex_api_key_used"] is True)
    check("the key is sent on the wire, but redacted in diagnostics",
          all(SECRET in u for u in oa.seen_urls) and oa.redact("x" + SECRET) == "x***")
    check("export freezes the resolved seeds, filters and request log",
          payload["blocks"][0]["resolved"]["seed_ids"] and payload["requests"]["openalex"])

    print("\nselftest", "OK" if ok else "FAILED")
    return 0 if ok else 1


# ---------------------------------------------------------------- main

def main() -> int:
    if sys.argv[1:2] == ["selftest"]:
        return selftest()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path)
    ap.add_argument("--count-only", action="store_true", help="per-block totals only")
    ap.add_argument("--blocks", nargs="+", choices=BLOCK_IDS, default=BLOCK_IDS)
    ap.add_argument("--max-per-block", type=int, default=5000, help="abort above this")
    ap.add_argument("--arxiv-gap-tolerance", type=int, default=0,
                    help="records arXiv may report but not deliver before the run aborts")
    args = ap.parse_args()
    if not args.count_only and not args.out:
        ap.error("--out is required unless --count-only")
    if args.out and args.out.exists():
        ap.error(f"{args.out} exists; a frozen export is never overwritten. Re-date it.")

    oa = OpenAlexClient(api_key=os.environ.get("OPENALEX_API_KEY", ""))
    print(f"OpenAlex key: {'set' if oa.api_key else 'not set'}", file=sys.stderr)
    try:
        payload = run(args.blocks, oa, ArxivClient(), args.max_per_block, args.count_only,
                      args.arxiv_gap_tolerance)
    except Abort as exc:
        print(f"ABORT: {oa.redact(str(exc))}", file=sys.stderr)
        return 2

    if args.count_only:
        for bid, c in payload["counts"].items():
            print(f"  {bid:4s} {c['reported_total']:6d}")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\n{len(payload['records'])} unique records from {len(args.blocks)} blocks\n"
          f"-> {args.out}\n\nNext: python3 scripts/supplement.py merge --supplementary "
          f"{args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
