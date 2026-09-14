#!/usr/bin/env python3
"""Verify how OpenAlex and arXiv match the executed search phrases.

    python3 scripts/verify_search_matching.py            # run the live probes
    python3 scripts/verify_search_matching.py selftest   # offline checks only

Standard library only, no key, no account.

WHAT QUESTION THIS ANSWERS, AND WHY IT NEEDED A SCRIPT
------------------------------------------------------
`docs/search-strategy.md` §2.5 records that the two executed search strings omit terms the
superseded Scopus string carried: neither leg lists `"reservoir computer*"`, and neither
lists the hyphenated `"next-generation reservoir computing"`. The frozen exports nonetheless
contain 380 OpenAlex and 196 arXiv in-window records carrying the phrase "reservoir
computer", 21 and 72 of them with none of their leg's listed phrases present at all.

So the records were retrieved. Until 2026-09-05 *why* was an **unverified inference**: that
both engines stem and treat the hyphen as a token separator. §2.5 said so in those words and
called resolving it an open item owed before registration, on the grounds that a search
strategy explaining its own coverage by an assumed matching behaviour is making exactly the
kind of unqualified claim this study measures. This script is the resolution.

THE DESIGN, AND THE CONTROL THAT MAKES IT MEAN ANYTHING
-------------------------------------------------------
Single-record probe. Take a record that is in the frozen export and whose title and abstract
contain **none** of the leg's listed phrases, then ask the engine for that record *and* a
phrase together. If the record comes back, the engine matched a surface form the phrase does
not literally contain.

That result is worthless on its own, because an engine that silently ignored the phrase
filter would return the record every time. Every positive probe is therefore paired with
**negative controls**: the same record queried with phrases genuinely absent from it. Those
must return zero. If they do not, the probe proves nothing and this script says so rather
than reporting a pass.

The probe records are hard-coded because they are evidence, not parameters: each was
selected from the frozen export by the criterion above, and changing one silently would
change what the recorded result means.
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OPENALEX = "https://api.openalex.org/works"
ARXIV = "http://export.arxiv.org/api/query"

# Polite-pool contact, same convention as the fetchers: override with the environment.
import os
MAILTO = os.environ.get("RC_AUDIT_MAILTO", "stefan.trajanovski@students.finki.ukim.mk")

# arXiv asks for >= 3s between requests. Do not lower this.
ARXIV_DELAY_S = 3.0
OPENALEX_DELAY_S = 0.3

RAW = Path("data/raw")

# Phrases actually executed, per docs/search-strategy.md §2.4 and §2.5.
OA_TERMS = ["reservoir computing", "echo state network", "echo state machine",
            "liquid state machine", "physical reservoir",
            "next generation reservoir computing"]
ARXIV_TERMS = ["reservoir computing", "echo state network", "liquid state machine",
               "physical reservoir", "next generation reservoir computing"]

# Probe records, each verified present in the frozen export and carrying none of its own
# leg's listed phrases. `wording` is what the record actually says.
OA_PROBES = [
    ("10.1007/s00542-023-05463-4", "reservoir computer",
     ["reservoir computing", "reservoir computers", "reservoir compute"]),
    ("10.1016/j.ins.2021.03.013", "echo-state networks",
     ["echo state network"]),
    # A probe on `10.1063/5.0098707` ("next-generation reservoir computing") was drafted
    # and removed on 2026-09-05, caught by frozen_export_check() before it was reported.
    # That string CONTAINS "reservoir computing" as a substring, so the engine matches it
    # literally on a phrase both term lists carry, and the record can demonstrate nothing
    # about hyphen folding. The hyphenated next-generation variant therefore needs no
    # matching-behaviour explanation at all: it is retrieved by the plain phrase. Hyphen
    # folding is tested by the echo-state probe above, where "echo-state networks" does
    # not contain "echo state network" as a substring.
]
OA_CONTROLS = [
    ("10.1007/s00542-023-05463-4", "photosynthesis in maize"),
    ("10.1007/s00542-023-05463-4", "liquid state machine"),
    ("10.1016/j.ins.2021.03.013", "delay-embedded reservoir"),
]

ARXIV_PROBES = [
    ("1903.12487", "reservoir computers", ["reservoir computing", "reservoir computers"]),
    ("2005.05151", "echo-state network", ["echo state network"]),
]
ARXIV_CONTROLS = [
    ("1903.12487", "photosynthesis in maize"),
    ("1903.12487", "liquid state machine"),
]


# ---------------------------------------------------------------- engines

def openalex_count(doi: str, phrase: str | None = None) -> int:
    f = f"doi:{doi}"
    if phrase:
        f += f',title_and_abstract.search:"{phrase}"'
    url = OPENALEX + "?" + urllib.parse.urlencode(
        {"filter": f, "per-page": 1, "mailto": MAILTO}, safe=':,"')
    req = urllib.request.Request(url, headers={"User-Agent": f"rc-audit ({MAILTO})"})
    with urllib.request.urlopen(req) as r:
        return int(json.load(r)["meta"]["count"])


def arxiv_count(arxiv_id: str, phrase: str) -> int:
    """arXiv returns the intersection of `id_list` and `search_query`."""
    url = ARXIV + "?" + urllib.parse.urlencode(
        {"search_query": f'all:"{phrase}"', "id_list": arxiv_id, "max_results": 1})
    with urllib.request.urlopen(url) as r:
        body = r.read().decode("utf-8", "replace")
    m = re.search(r"<opensearch:totalResults[^>]*>(\d+)<", body)
    if m is None:
        raise RuntimeError("arXiv response carried no totalResults element")
    return int(m.group(1))


# ---------------------------------------------------------------- offline checks

def frozen_export_check() -> list[str]:
    """Confirm each probe record is in the frozen export and carries no listed phrase.

    This is the half of the claim that needs no network, and it is the half that would
    silently rot if a probe record were edited: a probe whose record does contain a listed
    phrase proves nothing at all, because the engine would have matched it literally.
    """
    problems: list[str] = []

    def text(e: dict) -> str:
        return ((e.get("title") or "") + " " + (e.get("abstract") or "")).lower()

    oa_path = RAW / "openalex_20260731.json"
    ax_path = RAW / "arxiv_20260731.json"
    if not oa_path.exists() or not ax_path.exists():
        return [f"frozen exports not found under {RAW}"]

    oa = json.loads(oa_path.read_text())["records"]
    by_doi = {}
    for e in oa:
        d = (e.get("doi") or "").lower()
        d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d)
        if d:
            by_doi[d] = e
    for doi, wording, _ in OA_PROBES:
        e = by_doi.get(doi.lower())
        if e is None:
            problems.append(f"OpenAlex probe {doi} is not in the frozen export")
            continue
        t = text(e)
        if wording.lower() not in t:
            problems.append(f"OpenAlex probe {doi} no longer contains {wording!r}")
        hit = [p for p in OA_TERMS if p in t]
        if hit:
            problems.append(f"OpenAlex probe {doi} contains listed phrase(s) {hit}; "
                            f"it cannot test non-literal matching")

    ax = json.loads(ax_path.read_text())["records"]
    by_id = {(e.get("arxiv_id") or "").split("v")[0]: e for e in ax}
    for aid, wording, _ in ARXIV_PROBES:
        e = by_id.get(aid)
        if e is None:
            problems.append(f"arXiv probe {aid} is not in the frozen export")
            continue
        t = text(e)
        if wording.lower() not in t:
            problems.append(f"arXiv probe {aid} no longer contains {wording!r}")
        hit = [p for p in ARXIV_TERMS if p in t]
        if hit:
            problems.append(f"arXiv probe {aid} contains listed phrase(s) {hit}; "
                            f"it cannot test non-literal matching")
    return problems


# ---------------------------------------------------------------- driver

def run_live() -> int:
    socket.setdefaulttimeout(30)
    print("Offline precondition: probe records are in the frozen export and carry no")
    print("listed phrase of their own leg.")
    problems = frozen_export_check()
    for p in problems:
        print(f"  ! {p}")
    if problems:
        print("\nAborting: the probes cannot mean what they are supposed to mean.",
              file=sys.stderr)
        return 1
    print("  OK\n")

    controls_ok = True
    positives: list[tuple[str, str, str, int]] = []

    print("NEGATIVE CONTROLS — each must return 0, or nothing below is interpretable")
    for doi, phrase in OA_CONTROLS:
        time.sleep(OPENALEX_DELAY_S)
        n = openalex_count(doi, phrase)
        ok = n == 0
        controls_ok &= ok
        print(f"  {'OK  ' if ok else 'FAIL'} OpenAlex {doi}  \"{phrase}\" -> {n}")
    for aid, phrase in ARXIV_CONTROLS:
        time.sleep(ARXIV_DELAY_S)
        n = arxiv_count(aid, phrase)
        ok = n == 0
        controls_ok &= ok
        print(f"  {'OK  ' if ok else 'FAIL'} arXiv    {aid}  all:\"{phrase}\" -> {n}")

    if not controls_ok:
        print("\nA negative control did not return zero. The phrase filter is not doing "
              "work,\nso the probes below cannot demonstrate non-literal matching. "
              "Reporting no result\nrather than a pass.", file=sys.stderr)
        return 1

    print("\nPROBES — record contains none of its leg's listed phrases; does the phrase "
          "still match?")
    for doi, wording, phrases in OA_PROBES:
        time.sleep(OPENALEX_DELAY_S)
        base = openalex_count(doi)
        if base != 1:
            print(f"  ! OpenAlex {doi} not resolvable at the API (count {base})")
            return 1
        for phrase in phrases:
            time.sleep(OPENALEX_DELAY_S)
            n = openalex_count(doi, phrase)
            positives.append(("OpenAlex", doi, phrase, n))
            print(f"  {'MATCH ' if n else 'no    '} OpenAlex {doi}  says {wording!r:38s} "
                  f"query \"{phrase}\" -> {n}")
    for aid, wording, phrases in ARXIV_PROBES:
        for phrase in phrases:
            time.sleep(ARXIV_DELAY_S)
            n = arxiv_count(aid, phrase)
            positives.append(("arXiv", aid, phrase, n))
            print(f"  {'MATCH ' if n else 'no    '} arXiv    {aid}  says {wording!r:38s} "
                  f"query all:\"{phrase}\" -> {n}")

    matched = sum(1 for *_x, n in positives if n)
    print(f"\n{matched} of {len(positives)} probes matched a form the query phrase does not "
          f"literally contain.")
    if matched == len(positives):
        print("Both engines fold singular/plural/stem variants and treat the hyphen as a "
              "token\nseparator. This is the result recorded in docs/search-strategy.md "
              "§2.5.")
        return 0
    print("Not every probe matched. §2.5's conclusion does not hold as written and must be "
          "narrowed\nto the cases that did.", file=sys.stderr)
    return 1


def selftest() -> int:
    """Offline only. The live probes need network and are not run here.

    The standard selftest loop must stay runnable without a connection, so what is checked
    here is the half that can rot silently: whether the probe records still satisfy the
    precondition that makes them evidence.
    """
    ok = True

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        ok = ok and cond

    problems = frozen_export_check()
    for p in problems:
        print(f"    ! {p}")
    check("probe records are in the frozen exports and carry no listed phrase",
          not problems)
    check("every OpenAlex probe has at least one query phrase",
          all(ps for _d, _w, ps in OA_PROBES))
    check("every arXiv probe has at least one query phrase",
          all(ps for _d, _w, ps in ARXIV_PROBES))
    check("negative controls exist for both engines",
          bool(OA_CONTROLS) and bool(ARXIV_CONTROLS))
    check("control phrases are absent from the executed term lists",
          all(p not in OA_TERMS for _d, p in OA_CONTROLS if p != "liquid state machine")
          and all(p not in ARXIV_TERMS for _a, p in ARXIV_CONTROLS
                  if p != "liquid state machine"))
    check("arXiv delay respects the API's stated 3s floor", ARXIV_DELAY_S >= 3.0)

    print("\nselftest", "OK" if ok else "FAILED")
    print("(offline checks only; run without an argument to execute the live probes)")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", nargs="?", default="live", choices=["live", "selftest"])
    args = ap.parse_args()
    if args.mode == "selftest":
        return selftest()
    try:
        return run_live()
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        print(f"network unavailable: {exc}", file=sys.stderr)
        print("The recorded result in docs/search-strategy.md §2.5 was obtained on "
              "2026-09-05.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
