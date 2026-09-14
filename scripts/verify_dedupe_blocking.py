#!/usr/bin/env python3
"""Check that dedupe.py's blocked matching equals an unblocked brute-force scan.

    python3 scripts/verify_dedupe_blocking.py --n 1500
    python3 scripts/verify_dedupe_blocking.py --n 1500 --seed 31

WHY THIS EXISTS
---------------
`dedupe.py` passes 2 and 3 are blocked: they compare each record against a pruned
candidate set rather than against every other record. Unblocked, pass 3 alone is
O(n^2) SequenceMatcher calls, roughly two hours on the current corpus.

Blocking is where a dedup implementation quietly loses true matches, and a lost match
is an inflated corpus count that nothing downstream would flag. The blockers here are
exact necessary conditions rather than heuristics, so the claim is not "few matches are
lost" but "none are". That claim is testable, so it is tested.

Brute force is quadratic, so the check runs on a random subsample. Several seeds at
n=1500 is the practical compromise; the full corpus is not tractable as a reference.

Deviation D7 records the change this verifies. Released with the artefacts under
protocol.md §13.
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dedupe as D  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------- pass 2

def pass2_blocked(staged: list[dict]):
    """Mirrors dedupe.py pass 2."""
    kept: list[dict] = []
    index: dict[str, int] = {}
    by_len: dict[int, list[int]] = {}
    counters: list[Counter] = []
    dup = 0
    for src in staged:
        r = dict(src)
        nt = D.norm_title(r["title"])
        r["_nt"] = nt
        cnt = Counter(nt)
        hit = index.get(nt)
        if hit is None:
            for length in range(len(nt) - D.MAX_EDIT, len(nt) + D.MAX_EDIT + 1):
                for i in by_len.get(length, ()):
                    if hit is not None and i > hit:
                        continue
                    if D.counter_delta(cnt, counters[i]) > 2 * D.MAX_EDIT:
                        continue
                    if D.bounded_edit(nt, kept[i]["_nt"]) <= D.MAX_EDIT:
                        hit = i if hit is None else min(hit, i)
        if hit is not None:
            keeper, dropped = D.prefer(kept[hit], r)
            D.merge(keeper, dropped)
            kept[hit] = keeper
            counters[hit] = Counter(keeper["_nt"])
            index[keeper["_nt"]] = hit
            by_len.setdefault(len(keeper["_nt"]), []).append(hit)
            dup += 1
            continue
        index[nt] = len(kept)
        by_len.setdefault(len(nt), []).append(len(kept))
        kept.append(r)
        counters.append(cnt)
    return kept, dup, counters


def pass2_reference(staged: list[dict]):
    """Unblocked linear scan: first kept record within edit distance 3 wins."""
    kept: list[dict] = []
    index: dict[str, int] = {}
    dup = 0
    for src in staged:
        r = dict(src)
        nt = D.norm_title(r["title"])
        r["_nt"] = nt
        hit = index.get(nt)
        if hit is None:
            for i, k in enumerate(kept):
                if D.bounded_edit(nt, k["_nt"]) <= D.MAX_EDIT:
                    hit = i
                    break
        if hit is not None:
            keeper, dropped = D.prefer(kept[hit], r)
            D.merge(keeper, dropped)
            kept[hit] = keeper
            index[keeper["_nt"]] = hit
            dup += 1
            continue
        index[nt] = len(kept)
        kept.append(r)
    return kept, dup


# --------------------------------------------------------------- pass 3

def pass3_blocked(kept: list[dict], counters: list[Counter]) -> set[frozenset]:
    """Mirrors dedupe.py pass 3."""
    out: set[frozenset] = set()
    order = sorted(range(len(kept)), key=lambda i: len(kept[i]["_nt"]))
    for pos, i in enumerate(order):
        a = kept[i]["_nt"]
        la = len(a)
        if not la:
            continue
        limit = (11 * la) / 9
        for j in order[pos + 1:]:
            b = kept[j]["_nt"]
            lb = len(b)
            if lb > limit:
                break
            shared = sum((counters[i] & counters[j]).values())
            if 2 * shared < D.NEAR_RATIO * (la + lb):
                continue
            if SequenceMatcher(None, a, b).ratio() >= D.NEAR_RATIO:
                out.add(frozenset((i, j)))
    return out


def pass3_reference(kept: list[dict]) -> set[frozenset]:
    """Every pair, no blocking and no length skip."""
    out: set[frozenset] = set()
    for i in range(len(kept)):
        a = kept[i]["_nt"]
        if not a:
            continue
        for j in range(i + 1, len(kept)):
            b = kept[j]["_nt"]
            if not b:
                continue
            if SequenceMatcher(None, a, b).ratio() >= D.NEAR_RATIO:
                out.add(frozenset((i, j)))
    return out


def pass3_superseded(kept: list[dict]) -> set[frozenset]:
    """The pre-D7 implementation, with its abs-length-40 skip. Reported for contrast."""
    out: set[frozenset] = set()
    for i in range(len(kept)):
        for j in range(i + 1, len(kept)):
            a, b = kept[i]["_nt"], kept[j]["_nt"]
            if abs(len(a) - len(b)) > 40:
                continue
            if SequenceMatcher(None, a, b).ratio() >= D.NEAR_RATIO:
                out.add(frozenset((i, j)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--openalex", type=Path,
                    default=REPO / "data/raw/openalex_20260731.json")
    ap.add_argument("--arxiv", type=Path,
                    default=REPO / "data/raw/arxiv_20260731.json")
    ap.add_argument("--n", type=int, default=1500,
                    help="subsample size; brute force is quadratic, so keep it modest")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    pool: list[dict] = []
    if args.openalex.exists():
        recs, _ = D.load_openalex(args.openalex)
        pool += recs
    if args.arxiv.exists():
        pool += D.load_arxiv(args.arxiv)
    if not pool:
        print("no input records", file=sys.stderr)
        return 1

    n = min(args.n, len(pool))
    random.seed(args.seed)
    sample = random.sample(pool, n)
    print(f"sample n={n}  seed={args.seed}  (pool {len(pool)})")

    kb, db, counters = pass2_blocked(sample)
    kr, dr = pass2_reference(sample)
    pass2_ok = (
        len(kb) == len(kr)
        and db == dr
        and all(a["_nt"] == b["_nt"] for a, b in zip(kb, kr))
        and all(a["source_db"] == b["source_db"] for a, b in zip(kb, kr))
        and all(a.get("is_oa") == b.get("is_oa") for a, b in zip(kb, kr))
    )
    print(f"pass 2  blocked kept={len(kb)} dups={db} | "
          f"reference kept={len(kr)} dups={dr} -> "
          f"{'IDENTICAL' if pass2_ok else 'MISMATCH'}")

    pb = pass3_blocked(kb, counters)
    pr = pass3_reference(kb)
    ps = pass3_superseded(kb)
    pass3_ok = pb == pr
    print(f"pass 3  blocked pairs={len(pb)} | reference pairs={len(pr)} -> "
          f"{'IDENTICAL' if pass3_ok else 'MISMATCH'}")
    print(f"        pairs the superseded length-40 skip would have discarded: "
          f"{len(pr - ps)}")
    if not pass3_ok:
        for x in list(pr - pb)[:5]:
            i, j = tuple(x)
            print(f"  MISSED: {kb[i]['title'][:60]} || {kb[j]['title'][:60]}")
        for x in list(pb - pr)[:5]:
            i, j = tuple(x)
            print(f"  EXTRA:  {kb[i]['title'][:60]} || {kb[j]['title'][:60]}")

    ok = pass2_ok and pass3_ok
    print("RESULT:", "OK" if ok else "MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
