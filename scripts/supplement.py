#!/usr/bin/env python3
"""Merge the supplementary search leg into a separate candidate file.

    python3 scripts/supplement.py merge --supplementary data/raw/supplementary_YYYYMMDD.json
    python3 scripts/supplement.py merge --supplementary ... \
        --adjudications data/screening/supplementary_near_duplicates_for_review.csv
    python3 scripts/supplement.py selftest

Implements docs/search-strategy.md §2.6. Standard library only. Reads the frozen corpus
and one or more exports from scripts/fetch_supplementary.py; writes, in --out-dir:

    corpus_supplementary.csv                       the new records only, dedupe.FIELDS +
                                                   supp_blocks, supp_engine, matches_orig_literal
    supplementary_near_duplicates_for_review.csv   pairs a human must decide
    supplementary_corpus_matches.csv               every candidate already in the corpus, and why
    prisma_counts_supplementary.json               the leg's PRISMA counts, reconciled
    supplementary_id_ledger.csv                    identity -> record id, persistent

THE FROZEN CORPUS IS NEVER WRITTEN
----------------------------------
`corpus_deduped.csv` is reproducible byte for byte by dedupe.py from the two frozen
exports, and the pilot and Stage-1 samples were drawn from it with fixed seeds. Appending
rows to it, or to anything screen.py reads by default, would silently change those
populations. So the supplement lives in its own file, read only by the tools that ask for
it (scripts/validation.py), and corpus rows are not updated even where the supplement
knows more about them: a corpus record whose supplementary copy is openly retrievable is
listed as an `oa_upgrade` in supplementary_corpus_matches.csv, not changed.

RECORD IDS ARE ISSUED ONCE
--------------------------
Corpus ids are positional (dedupe numbers its output), which is safe only because the
corpus is frozen. Supplementary ids cannot be positional: a second export, or a work that
drops out of the index, would renumber everything after it. So ids come from a ledger
mapping each identity (OpenAlex work id, or version-stripped arXiv id) to the id it was
first given. New ids are allocated above the maximum of the corpus and the ledger; an id
is never reused, and a ledger id that collides with a corpus id aborts the run. A record
that later disappears keeps its ledger row with a status saying why. When a later export
links two identities that had separate ids (a preprint and its article), the record keeps
the lower id and the other is marked merged. The reverse, one ledger id now covering two
separate records, cannot be resolved automatically and aborts.

DEDUPLICATION
-------------
Within the leg, the same passes as dedupe.py in the same order (exact DOI, exact arXiv id,
normalized title within edit distance 3) with dedupe's own `prefer` and `merge`, so the
precedence rules are identical. `source_db` stays canonical (`openalex`, `arxiv`) during
these passes because `prefer` tests `source_db == "arxiv"`; provenance goes in
`supp_blocks` and `supp_engine`. Two deliberate differences: rows are sorted by identity
before the passes, so the result does not depend on block or export order; and titles are
keyed by `title_key`, which is dedupe's `norm_title` except that a title it reduces to
nothing (a non-Latin script) keeps a Unicode key instead. dedupe.py's pass 2 treats every
empty normalized title as one title, which in the frozen corpus folded six untitled
journal-issue records and two copies of a Japanese-titled paper into RC-0349. Untitled
records (OpenAlex `paratext`: covers and issue blurbs) cannot be deduplicated or screened
on title, so they are removed before the passes and listed in the counts.

Against the corpus, every identity a collapsed candidate carries (all members' DOIs,
arXiv ids, OpenAlex ids and normalized titles) is compared with every corpus row,
including rows already marked `dup_of`, which resolve to their surviving record. The
basis is recorded in the order openalex_id, doi, arxiv_id, title.

Near-duplicates reproduce dedupe.py pass 3 exactly (rows ordered by normalized title
length, `SequenceMatcher(None, shorter, longer)`, the 11/9 length bound and the
shared-character bound, threshold applied before rounding), restricted to pairs with at
least one new record. They are never merged automatically.

ADJUDICATION
------------
The review file must match the generated pair set exactly: one row per flagged pair, with
the titles as generated. A missing, unexpected, duplicated or retitled row aborts, so a
file made against a different run cannot be applied, and a header-only file cannot pass
for a finished one. `same` decisions are applied by connected component: a component
holding one corpus record makes it canonical, and every new member is marked `dup_of` it;
a component holding none keeps the record dedupe.prefer would keep; a component joining
two different corpus records is an error, because the corpus is frozen and only a human
can say what that means. Duplicates are marked, not deleted, as in dedupe.py.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import random
import shutil
import sys
import tempfile
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dedupe  # noqa: E402
import fetch_arxiv  # noqa: E402
import fetch_openalex  # noqa: E402
from dedupe import (FIELDS, MAX_EDIT, NEAR_RATIO, bounded_edit, counter_delta,  # noqa: E402
                    merge, norm_arxiv_id, norm_doi, norm_title, prefer)
from fetch_supplementary import BLOCK_IDS  # noqa: E402

CORPUS = Path("data/screening/corpus_deduped.csv")
OUT_DIR = Path("data/screening")

SUPP_FIELDS = FIELDS + ["supp_blocks", "supp_engine", "matches_orig_literal"]
LEDGER_FIELDS = ["record_id", "identity_key", "first_seen_export", "status"]
MATCH_FIELDS = ["identity", "title", "supp_blocks", "matched_record_id", "basis",
                "supp_is_oa", "corpus_is_oa", "oa_upgrade"]
REVIEW_FIELDS = [
    "ratio", "decision", "adjudicated_by", "note",
    "record_id_a", "title_a", "year_a", "venue_a", "doi_a", "source_db_a",
    "record_id_b", "title_b", "year_b", "venue_b", "doi_b", "source_db_b",
]
# The executed phrases of both primary legs. A new record carrying one of them literally
# was missed through index drift, not vocabulary, and is counted apart.
ORIG_PHRASES = sorted({norm_title(t) for t in fetch_openalex.TERMS + fetch_arxiv.TERMS})
BASES = ("openalex_id", "doi", "arxiv_id", "title")


class MergeError(RuntimeError):
    """An input condition under which nothing may be written."""


# ---------------------------------------------------------------- rows

def row_from_openalex(e: dict) -> dict:
    """Same field logic as dedupe.load_openalex (checked against it in the selftest)."""
    doi = norm_doi(e.get("doi", ""))
    abstract = e.get("abstract", "") or ""
    r = dedupe._blank()
    r.update({
        "source_db": "openalex",
        "doi": doi,
        "preprint_id": norm_arxiv_id(doi),
        "openalex_id": e.get("openalex_id", ""),
        "title": e.get("title", "") or "",
        "abstract": abstract,
        "has_abstract": "1" if abstract else "0",
        "authors": e.get("authors", "") if isinstance(e.get("authors"), str)
        else "; ".join(e.get("authors", []) or []),
        "year": str(e.get("year") or ""),
        "venue": e.get("venue", "") or "",
        "venue_type": e.get("venue_type", "") or "",
        "is_oa": "1" if e.get("is_oa") else "0",
        "oa_basis": "openalex" if e.get("is_oa") else "",
        "oa_status": e.get("oa_status", "") or "",
        "cited_by_count": str(e.get("cited_by_count") or ""),
    })
    return r


def row_from_arxiv(e: dict) -> dict:
    """Same field logic as dedupe.load_arxiv (checked against it in the selftest)."""
    abstract = e.get("abstract", "") or ""
    r = dedupe._blank()
    r.update({
        "source_db": "arxiv",
        "doi": norm_doi(e.get("doi", "")),
        "preprint_id": norm_arxiv_id(e.get("arxiv_id", "")),
        "title": e.get("title", ""),
        "abstract": abstract,
        "has_abstract": "1" if abstract else "0",
        "authors": "; ".join(e.get("authors", [])),
        "year": (e.get("published_v1", "") or "")[:4],
        "venue": e.get("journal_ref", "") or "arXiv",
        "venue_type": "preprint" if not e.get("journal_ref") else "published-unspecified",
        "is_oa": "1",
        "oa_basis": "arxiv",
        "oa_status": "",
    })
    return r


def title_key(t: str) -> str:
    """norm_title, or a Unicode key for a title norm_title reduces to nothing."""
    nt = norm_title(t)
    if nt or not (t or "").strip():
        return nt
    u = unicodedata.normalize("NFKC", t).casefold()
    return "u:" + "".join(c for c in u if c.isalnum())


def identity(engine: str, e: dict) -> str:
    if engine == "openalex":
        return f"openalex:{e.get('openalex_id', '')}"
    return f"arxiv:{norm_arxiv_id(e.get('arxiv_id', ''))}"


def attach(r: dict, key: str, engine: str, blocks: list[str], export: str) -> dict:
    r["_keys"] = {key: export}
    r["_blocks"] = set(blocks)
    r["_engines"] = {engine}
    r["_dois"] = {r["doi"]} - {""}
    r["_arxiv"] = {r["preprint_id"]} - {""}
    r["_oaids"] = {r["openalex_id"]} - {""}
    r["_titles"] = {title_key(r["title"])} - {""}
    return r


def absorb(keeper: dict, dropped: dict) -> None:
    """dedupe.merge plus the union of every identity the two rows carry."""
    merge(keeper, dropped)
    for k, v in dropped["_keys"].items():
        keeper["_keys"].setdefault(k, v)
    for f in ("_blocks", "_engines", "_dois", "_arxiv", "_oaids", "_titles"):
        keeper[f] |= dropped[f]


def first_block(r: dict) -> int:
    return min(BLOCK_IDS.index(b) for b in r["_blocks"])


def literal_orig(r: dict) -> bool:
    text = f" {norm_title(r.get('title', ''))} {norm_title(r.get('abstract', ''))} "
    return any(f" {p} " in text for p in ORIG_PHRASES)


# ---------------------------------------------------------------- within the leg

def collapse_within(rows: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """dedupe.py passes 1, 1b and 2 over the leg's own rows (see the docstring)."""
    removed = {"doi": 0, "arxiv_id": 0, "title": 0}
    rows = sorted(rows, key=lambda r: min(r["_keys"]))

    def exact(rows: list[dict], field: str, basis: str) -> list[dict]:
        by: dict[str, dict] = {}
        rest: list[dict] = []
        for r in rows:
            v = r.get(field, "")
            if v and v in by:
                keeper, dropped = prefer(by[v], r)
                absorb(keeper, dropped)
                by[v] = keeper
                removed[basis] += 1
            elif v:
                by[v] = r
            else:
                rest.append(r)
        return rest + list(by.values())

    staged = exact(exact(rows, "doi", "doi"), "preprint_id", "arxiv_id")

    kept: list[dict] = []
    index: dict[str, int] = {}
    by_len: dict[int, list[int]] = {}
    counters: list[Counter] = []
    for r in staged:
        nt = title_key(r["title"])
        r["_nt"] = nt
        cnt = Counter(nt)
        hit = index.get(nt) if nt else None
        if hit is None and nt:
            for length in range(len(nt) - MAX_EDIT, len(nt) + MAX_EDIT + 1):
                for i in by_len.get(length, ()):
                    if hit is not None and i > hit:
                        continue
                    if counter_delta(cnt, counters[i]) > 2 * MAX_EDIT:
                        continue
                    if bounded_edit(nt, kept[i]["_nt"]) <= MAX_EDIT:
                        hit = i if hit is None else min(hit, i)
        if hit is not None:
            keeper, dropped = prefer(kept[hit], r)
            absorb(keeper, dropped)
            kept[hit] = keeper
            counters[hit] = Counter(keeper["_nt"])
            index[keeper["_nt"]] = hit
            by_len.setdefault(len(keeper["_nt"]), []).append(hit)
            removed["title"] += 1
            continue
        if nt:
            index[nt] = len(kept)
            by_len.setdefault(len(nt), []).append(len(kept))
        kept.append(r)
        counters.append(cnt)
    for r in kept:
        r["_nt"] = title_key(r["title"])
    return kept, removed


# ---------------------------------------------------------------- against the corpus

def survivor_map(corpus: list[dict]) -> dict[str, str]:
    """record id -> the id of the record it survives as, following dup_of chains."""
    by_id = {r["record_id"]: r for r in corpus}
    out = {}
    for r in corpus:
        out[r["record_id"]] = dedupe._surviving(r, by_id)["record_id"]
    return out


class CorpusIndex:
    def __init__(self, corpus: list[dict]):
        self.surv = survivor_map(corpus)
        self.by = {b: {} for b in ("openalex_id", "doi", "arxiv_id")}
        self.by_title: dict[str, set[str]] = {}
        self.by_len: dict[int, list[tuple[str, Counter, str]]] = {}
        self.is_oa = {r["record_id"]: r.get("is_oa", "") for r in corpus}
        for r in corpus:
            s = self.surv[r["record_id"]]
            for basis, v in (("openalex_id", r.get("openalex_id", "")),
                             ("doi", norm_doi(r.get("doi", ""))),
                             ("arxiv_id", norm_arxiv_id(r.get("preprint_id", "")))):
                if v:
                    self.by[basis].setdefault(v, set()).add(s)
            # OpenAlex registers preprints under 10.48550/arxiv.<id>; index that id too.
            a = norm_arxiv_id(r.get("doi", ""))
            if a:
                self.by["arxiv_id"].setdefault(a, set()).add(s)
            nt = title_key(r.get("title", ""))
            if nt:
                self.by_title.setdefault(nt, set()).add(s)
                self.by_len.setdefault(len(nt), []).append((nt, Counter(nt), s))

    def match(self, r: dict) -> tuple[str, list[str]]:
        """(basis, sorted survivor ids) of the first basis that matches, else ("", [])."""
        for basis, values in (("openalex_id", r["_oaids"]),
                              ("doi", r["_dois"] | {norm_doi(d) for d in r["_dois"]}),
                              ("arxiv_id", r["_arxiv"])):
            hits = set().union(*(self.by[basis].get(v, set()) for v in values)) if values else set()
            if hits:
                return basis, sorted(hits)
        hits: set[str] = set()
        for nt in r["_titles"]:
            hits |= self.by_title.get(nt, set())
            cnt = Counter(nt)
            for length in range(len(nt) - MAX_EDIT, len(nt) + MAX_EDIT + 1):
                for ct, cc, s in self.by_len.get(length, ()):
                    if s in hits or counter_delta(cnt, cc) > 2 * MAX_EDIT:
                        continue
                    if bounded_edit(nt, ct) <= MAX_EDIT:
                        hits.add(s)
        return ("title", sorted(hits)) if hits else ("", [])


# ---------------------------------------------------------------- ids

def read_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if rows and set(rows[0]) != set(LEDGER_FIELDS):
        raise MergeError(f"{path}: unexpected ledger columns {sorted(rows[0])}")
    seen = set()
    for r in rows:
        if r["identity_key"] in seen:
            raise MergeError(f"{path}: identity {r['identity_key']} appears twice")
        seen.add(r["identity_key"])
    return rows


def id_num(rid: str) -> int:
    return int(rid.split("-", 1)[1])


def assign_ids(new: list[dict], ledger: list[dict], corpus_max: int) -> tuple[list[dict], dict]:
    """Give every new record its ledger id, or a fresh one above every issued id."""
    key_to_id = {r["identity_key"]: r["record_id"] for r in ledger}
    clash = sorted({r["record_id"] for r in ledger if id_num(r["record_id"]) <= corpus_max})
    if clash:
        raise MergeError(f"ledger ids {clash[:5]} collide with corpus ids (corpus max "
                         f"RC-{corpus_max:04d}); the ledger belongs to a different corpus")
    new.sort(key=lambda r: (first_block(r), r["_nt"], sorted(r["_keys"])))
    merged_into: dict[str, str] = {}
    taken: dict[str, int] = {}
    for n, r in enumerate(new):
        ids = sorted({key_to_id[k] for k in r["_keys"] if k in key_to_id}, key=id_num)
        if not ids:
            continue
        r["record_id"] = ids[0]
        for other in ids[1:]:
            merged_into[other] = ids[0]
        for rid in ids:
            if rid in taken:
                raise MergeError(
                    f"ledger id {rid} now covers two separate records "
                    f"({sorted(new[taken[rid]]['_keys'])} and {sorted(r['_keys'])}); this "
                    f"cannot be resolved automatically. Inspect the exports.")
            taken[rid] = n
    issued = [id_num(r["record_id"]) for r in ledger]
    nxt = max([corpus_max] + issued) + 1
    fresh = 0
    for r in new:
        if not r.get("record_id"):
            r["record_id"] = f"RC-{nxt:04d}"
            nxt += 1
            fresh += 1
    new.sort(key=lambda r: id_num(r["record_id"]))
    return new, {"merged_into": merged_into, "allocated_this_run": fresh,
                 "reused_from_ledger": len(new) - fresh}


def update_ledger(ledger: list[dict], new: list[dict], merged_into: dict[str, str],
                  matched: dict[str, str]) -> list[dict]:
    """Add every identity seen this run; recompute each row's status. Never drop a row."""
    rows = {r["identity_key"]: dict(r) for r in ledger}
    status_of: dict[str, str] = {}
    for r in new:
        status_of[r["record_id"]] = (f"adjudicated-duplicate-of:{r['dup_of']}"
                                     if r.get("dup_of") else "active")
        for k, exp in sorted(r["_keys"].items()):
            if k not in rows:
                rows[k] = {"record_id": r["record_id"], "identity_key": k,
                           "first_seen_export": exp, "status": ""}
    for k, row in rows.items():
        rid = row["record_id"]
        if rid in merged_into:
            row["status"] = f"merged-into:{merged_into[rid]}"
        elif rid in status_of:
            row["status"] = status_of[rid]
        elif k in matched:
            row["status"] = f"matched-corpus:{matched[k]}"
        else:
            row["status"] = "absent-from-exports"
    return sorted(rows.values(), key=lambda r: (id_num(r["record_id"]), r["identity_key"]))


# ---------------------------------------------------------------- near-duplicates

def near_pairs(titles: list[str], is_new: list[bool]) -> list[tuple[int, int, float]]:
    """dedupe.py pass 3 over `titles`, restricted to pairs with at least one new row."""
    counters = [Counter(t) for t in titles]
    order = sorted(range(len(titles)), key=lambda i: len(titles[i]))
    new_pos = [p for p, i in enumerate(order) if is_new[i]]
    out = []
    for pos, i in enumerate(order):
        a = titles[i]
        la = len(a)
        if not la:
            continue
        limit = (11 * la) / 9
        cands = (order[pos + 1:] if is_new[i]
                 else (order[p] for p in new_pos[bisect.bisect_right(new_pos, pos):]))
        for j in cands:
            b = titles[j]
            lb = len(b)
            if lb > limit:
                break
            shared = sum((counters[i] & counters[j]).values())
            if 2 * shared < NEAR_RATIO * (la + lb):
                continue
            ratio = SequenceMatcher(None, a, b).ratio()
            if ratio >= NEAR_RATIO:
                out.append((min(i, j), max(i, j), round(ratio, 4)))
    return sorted(out)


def near_pairs_brute(titles: list[str], is_new: list[bool]) -> list[tuple[int, int, float]]:
    """Every pair, no blocking; the selftest's reference for near_pairs."""
    order = sorted(range(len(titles)), key=lambda i: len(titles[i]))
    out = []
    for p, i in enumerate(order):
        for j in order[p + 1:]:
            if not (is_new[i] or is_new[j]) or not titles[i]:
                continue
            ratio = SequenceMatcher(None, titles[i], titles[j]).ratio()
            if ratio >= NEAR_RATIO:
                out.append((min(i, j), max(i, j), round(ratio, 4)))
    return sorted(out)


# ---------------------------------------------------------------- adjudication

def read_adjudications(path: Path, expected: dict[tuple[str, str], tuple[str, str]]
                       ) -> tuple[list[tuple[str, str]], int, int]:
    """(same pairs, decided different, undecided). Aborts unless the file matches exactly."""
    same, different, undecided = [], 0, 0
    seen: set[tuple[str, str]] = set()
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing_cols = set(REVIEW_FIELDS) - set(reader.fieldnames or [])
        if missing_cols:
            raise MergeError(f"{path.name}: missing columns {sorted(missing_cols)}")
        for line, row in enumerate(reader, 2):
            key = (row["record_id_a"], row["record_id_b"])
            if key not in expected:
                raise MergeError(f"{path.name}:{line}: pair {key} was not flagged by this "
                                 f"run; the file belongs to a different run")
            if key in seen:
                raise MergeError(f"{path.name}:{line}: pair {key} appears twice")
            seen.add(key)
            if (row["title_a"], row["title_b"]) != expected[key]:
                raise MergeError(f"{path.name}:{line}: titles do not match this run; "
                                 f"re-adjudicate rather than apply it")
            decision = (row.get("decision") or "").strip().lower()
            if decision == "same":
                same.append(key)
            elif decision == "different":
                different += 1
            elif decision == "":
                undecided += 1
            else:
                raise MergeError(f"{path.name}:{line}: decision must be 'same', "
                                 f"'different' or blank, got {decision!r}")
    missing = sorted(set(expected) - seen)
    if missing:
        raise MergeError(f"{path.name}: {len(missing)} flagged pairs have no row "
                         f"(first: {missing[0]}); the file belongs to a different run")
    return same, different, undecided


def apply_same(same: list[tuple[str, str]], new_by_id: dict[str, dict],
               surv: dict[str, str]) -> int:
    """Union-find over `same` pairs; mark every non-canonical new member. Returns marks."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def node(rid: str) -> str:
        return surv.get(rid, rid)          # a corpus id resolves to its surviving record

    for a, b in same:
        ra, rb = find(node(a)), find(node(b))
        if ra != rb:
            parent[max(ra, rb, key=id_num)] = min(ra, rb, key=id_num)
    comps: dict[str, list[str]] = {}
    for x in list(parent):
        comps.setdefault(find(x), []).append(x)
    marked = 0
    for members in comps.values():
        members.sort(key=id_num)
        in_corpus = [m for m in members if m in surv]
        if len(set(in_corpus)) > 1:
            raise MergeError(f"adjudications join corpus records {sorted(set(in_corpus))} "
                             f"through {sorted(m for m in members if m in new_by_id)}; "
                             f"the corpus is frozen, so a human must resolve this")
        new_members = [new_by_id[m] for m in members if m in new_by_id]
        if in_corpus:
            canon = in_corpus[0]
        else:
            keeper = new_members[0]
            for m in new_members[1:]:
                keeper, dropped = prefer(keeper, m)
                absorb(keeper, dropped)
            canon = keeper["record_id"]
        for r in new_members:
            if r["record_id"] != canon:
                r["dup_of"], r["dup_basis"] = canon, "manual-adjudication"
                marked += 1
    return marked


# ---------------------------------------------------------------- merge

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_exports(paths: list[Path]) -> tuple[list[dict], list[dict], int, list[str]]:
    """(rows, export metadata, records identified, identities removed as untitled)."""
    rows: dict[str, dict] = {}
    untitled: dict[str, None] = {}
    meta, total = [], 0
    for p in paths:
        payload = json.loads(p.read_text(encoding="utf-8"))
        if payload.get("source") != "supplementary" or payload.get("count_only"):
            raise MergeError(f"{p}: not a supplementary export (or a --count-only run)")
        meta.append({"path": str(p), "sha256": sha256(p),
                     "retrieved_utc": payload.get("retrieved_utc"),
                     "script_sha256": payload.get("script_sha256"),
                     "records": len(payload.get("records", []))})
        for e in payload.get("records", []):
            total += 1
            engine = e.get("engine")
            if engine not in ("openalex", "arxiv"):
                raise MergeError(f"{p}: record with unknown engine {engine!r}")
            key = identity(engine, e)
            if key in untitled:
                continue
            if key in rows:
                rows[key]["_blocks"] |= set(e.get("blocks", []))
                continue
            if not (e.get("title") or "").strip():
                untitled[key] = None
                continue
            r = row_from_openalex(e) if engine == "openalex" else row_from_arxiv(e)
            rows[key] = attach(r, key, engine, e.get("blocks", []), p.name)
    return list(rows.values()), meta, total, sorted(untitled)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def cmd_merge(corpus_path: Path, exports: list[Path], out_dir: Path,
              adjudications: Path | None, ledger_path: Path | None = None,
              quiet: bool = False) -> dict:
    """Run the merge and write the outputs. Raises MergeError before writing anything."""
    ledger_path = ledger_path or out_dir / "supplementary_id_ledger.csv"
    supp_path = out_dir / "corpus_supplementary.csv"
    matches_path = out_dir / "supplementary_corpus_matches.csv"
    counts_path = out_dir / "prisma_counts_supplementary.json"
    review_path = out_dir / "supplementary_near_duplicates_for_review.csv"
    inputs = {corpus_path.resolve(), *(p.resolve() for p in exports)}
    if any(p.resolve() in inputs for p in (supp_path, matches_path, counts_path, ledger_path)):
        raise MergeError("an output path coincides with an input; refusing to overwrite it")

    with corpus_path.open(newline="", encoding="utf-8") as fh:
        corpus = list(csv.DictReader(fh))
    if not corpus or set(FIELDS) - set(corpus[0]):
        raise MergeError(f"{corpus_path}: not a dedupe.py corpus")
    corpus_max = max(id_num(r["record_id"]) for r in corpus)
    ledger = read_ledger(ledger_path)

    rows, export_meta, identified, untitled = load_exports(exports)
    cross_export_repeats = identified - len(rows) - len(untitled)
    per_block = Counter(b for r in rows for b in r["_blocks"])

    cands, removed_within = collapse_within(rows)
    cidx = CorpusIndex(corpus)
    new, matches, matched_keys = [], [], {}
    known = Counter()
    for r in cands:
        basis, hits = cidx.match(r)
        if not basis:
            new.append(r)
            continue
        known[basis] += 1
        corpus_oa = "1" if any(cidx.is_oa.get(h) == "1" for h in hits) else "0"
        for k in r["_keys"]:
            matched_keys[k] = hits[0]
        matches.append({
            "identity": "|".join(sorted(r["_keys"])), "title": r["title"],
            "supp_blocks": "|".join(sorted(r["_blocks"], key=BLOCK_IDS.index)),
            "matched_record_id": "|".join(hits), "basis": basis,
            "supp_is_oa": r.get("is_oa", ""), "corpus_is_oa": corpus_oa,
            "oa_upgrade": "1" if r.get("is_oa") == "1" and corpus_oa != "1" else "0",
        })
    matches.sort(key=lambda m: (m["matched_record_id"], m["identity"]))

    new, id_info = assign_ids(new, ledger, corpus_max)
    for r in new:
        r["dup_of"], r["dup_basis"] = "", ""
        r["supp_blocks"] = "|".join(sorted(r["_blocks"], key=BLOCK_IDS.index))
        r["supp_engine"] = "|".join(sorted(r["_engines"]))
        r["matches_orig_literal"] = "1" if literal_orig(r) else "0"

    titles = [title_key(r["title"]) for r in corpus] + [r["_nt"] for r in new]
    is_new = [False] * len(corpus) + [True] * len(new)
    everyone = corpus + new
    pairs = near_pairs(titles, is_new)
    expected = {(everyone[i]["record_id"], everyone[j]["record_id"]):
                (everyone[i]["title"], everyone[j]["title"]) for i, j, _ in pairs}

    same, decided_different, undecided = [], 0, len(pairs)
    marked = 0
    if adjudications:
        same, decided_different, undecided = read_adjudications(adjudications, expected)
        marked = apply_same(same, {r["record_id"]: r for r in new}, cidx.surv)

    active = [r for r in new if not r["dup_of"]]
    total_removed = (cross_export_repeats + len(untitled) + sum(removed_within.values())
                     + sum(known.values()) + marked)
    if identified - total_removed != len(active):
        raise MergeError(f"counts do not reconcile: {identified} identified - {total_removed} "
                         f"removed != {len(active)} active")

    counts = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "corpus": {"path": str(corpus_path), "sha256": sha256(corpus_path),
                       "rows": len(corpus)},
            "exports": export_meta,
            "ledger_before": {"path": str(ledger_path), "rows": len(ledger),
                              "sha256": sha256(ledger_path) if ledger_path.exists() else None},
            "adjudications": ({"path": str(adjudications), "sha256": sha256(adjudications)}
                              if adjudications else None),
        },
        "per_block_identified": {b: per_block[b] for b in BLOCK_IDS if per_block[b]},
        "identified_records": identified,
        "cross_export_repeats": cross_export_repeats,
        "identified_unique": len(rows) + len(untitled),
        "removed_untitled": {"count": len(untitled), "identities": untitled},
        "removed_within_leg": removed_within,
        "candidates_after_within_leg": len(cands),
        "already_in_corpus": {b: known[b] for b in BASES},
        "corpus_oa_upgrades": sum(1 for m in matches if m["oa_upgrade"] == "1"),
        "new_records": len(new),
        "near_duplicate_pairs_flagged": len(pairs),
        "near_duplicate_pairs_with_corpus": sum(1 for i, j, _ in pairs if not is_new[i]),
        "near_duplicate_decided_same": len(same),
        "near_duplicate_decided_different": decided_different,
        "near_duplicate_undecided": undecided,
        "near_duplicate_adjudication_complete": (not pairs) or bool(adjudications
                                                                    and not undecided),
        "removed_manual_adjudication": marked,
        "new_active": len(active),
        "new_active_per_block": {b: sum(1 for r in active if b in r["_blocks"])
                                 for b in BLOCK_IDS if per_block[b]},
        "new_active_with_orig_phrase_literal": sum(1 for r in active
                                                   if r["matches_orig_literal"] == "1"),
        "new_active_without_orig_phrase": sum(1 for r in active
                                              if r["matches_orig_literal"] == "0"),
        "open_access_eligible": sum(1 for r in active if r.get("is_oa") == "1"),
        "closed": sum(1 for r in active if r.get("is_oa") != "1"),
        "open_access_basis": dict(sorted(Counter(r.get("oa_basis", "") or "closed"
                                                 for r in active).items())),
        "open_without_abstract": sum(1 for r in active if r.get("is_oa") == "1"
                                     and r.get("has_abstract") != "1"),
        "ids": {"first": new[0]["record_id"] if new else None,
                "last": new[-1]["record_id"] if new else None,
                **{k: v for k, v in id_info.items() if k != "merged_into"},
                "merged_into": id_info["merged_into"]},
        "reconciliation": f"{identified} identified - {cross_export_repeats} cross-export - "
                          f"{len(untitled)} untitled - {sum(removed_within.values())} within leg - "
                          f"{sum(known.values())} in corpus - {marked} adjudicated = "
                          f"{len(active)} new active",
    }

    # Everything is computed and checked; only now is anything written.
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(supp_path, SUPP_FIELDS, new)
    write_csv(matches_path, MATCH_FIELDS, matches)
    write_csv(ledger_path, LEDGER_FIELDS,
              update_ledger(ledger, new, id_info["merged_into"], matched_keys))
    if adjudications and adjudications.resolve() == review_path.resolve():
        review_path = review_path.with_suffix(".new.csv")
    elif review_path.exists() and dedupe._has_decisions(review_path):
        review_path = review_path.with_suffix(".new.csv")
        if not quiet:
            print(f"  ! existing review file carries decisions; writing {review_path.name}",
                  file=sys.stderr)
    with review_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(REVIEW_FIELDS)
        for i, j, ratio in sorted(pairs, key=lambda t: (-t[2], everyone[t[0]]["record_id"],
                                                         everyone[t[1]]["record_id"])):
            a, b = everyone[i], everyone[j]
            w.writerow([ratio, "", "", "",
                        a["record_id"], a["title"], a["year"], a["venue"], a["doi"], a["source_db"],
                        b["record_id"], b["title"], b["year"], b["venue"], b["doi"], b["source_db"]])
    counts["review_file"] = review_path.name
    counts_path.write_text(json.dumps(counts, indent=2, ensure_ascii=False))

    if not quiet:
        print(f"\n{counts['reconciliation']}\n"
              f"  within leg  {removed_within}\n  in corpus   {dict(known)}\n"
              f"  near-duplicate pairs {len(pairs)} ({undecided} undecided)\n"
              f"  open access {counts['open_access_eligible']} of {len(active)} new active\n"
              f"-> {supp_path}\n-> {review_path}\n-> {counts_path}")
    return counts


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    """Offline, in a temporary directory, on a fixture built here."""
    ok = True

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        ok = ok and cond

    def crow(rid, title, *, doi="", pre="", oaid="", is_oa="1", dup_of=""):
        r = {f: "" for f in FIELDS}
        r.update({"record_id": rid, "source_db": "openalex", "doi": doi, "preprint_id": pre,
                  "openalex_id": oaid, "title": title, "abstract": "a", "has_abstract": "1",
                  "year": "2022", "venue": "J", "venue_type": "article", "is_oa": is_oa,
                  "oa_basis": "openalex" if is_oa == "1" else "", "dup_of": dup_of,
                  "dup_basis": "manual-adjudication" if dup_of else ""})
        return r

    corpus_rows = [
        crow("RC-0001", "Physical reservoir computing with memristors", doi="10.1/a",
             oaid="W100"),
        crow("RC-0002", "Delay based photonic reservoir for speech", pre="2101.00001"),
        crow("RC-0003", "Spin torque oscillator reservoir for spoken digit recognition",
             oaid="W300", is_oa="0"),
        crow("RC-0004", "Echo state networks for chaotic time series forecasting", oaid="W400"),
        crow("RC-0005", "Echo state network for chaotic time-series forecasting (preprint)",
             doi="10.1/e", dup_of="RC-0004"),
        crow("RC-0006", "A dopant network processing unit for temporal pattern "
                        "classification tasks", oaid="W600"),
    ]

    def oa(n, title, blocks, doi="", abstract="An abstract.", vtype="article", is_oa=True):
        return {"openalex_id": f"W{n}", "doi": doi, "title": title, "abstract": abstract,
                "has_abstract": bool(abstract), "authors": "A. Author; B. Author",
                "year": 2023, "venue": "Journal", "venue_type": vtype, "is_oa": is_oa,
                "oa_status": "gold" if is_oa else "closed", "oa_url": "",
                "cited_by_count": 2, "engine": "openalex", "blocks": blocks}

    def ax(aid, title, blocks):
        return {"arxiv_id": aid, "title": title, "abstract": "Preprint abstract.",
                "authors": ["A. Author"], "published_v1": "2023-02-01T00:00:00Z", "doi": "",
                "journal_ref": "", "categories": ["cs.ET"], "primary_category": "cs.ET",
                "window_flag": "in-window", "engine": "arxiv", "blocks": blocks}

    ex1 = [
        oa(1001, "Memristor reservoirs", ["A"], doi="10.1/A"),
        oa(1002, "Something else entirely", ["A"], doi="10.48550/arXiv.2101.00001",
           vtype="preprint"),
        oa(1003, "Spin-torque oscillator reservoir for spoken digit recognitio", ["A"]),
        oa(400, "Whatever OpenAlex calls it now", ["E"]),
        oa(1005, "Unrelated title of a known preprint", ["G"], doi="10.1/e"),
        oa(1006, "A dopant network processing unit for temporal pattern classification", ["C"]),
        oa(2000, "Volatile memristor arrays for temporal signal classification", ["B1"],
           doi="10.48550/arxiv.2203.00002", vtype="preprint"),
        ax("2203.00002v2", "Volatile memristor arrays for temporal signal classification",
           ["xB"]),
        oa(2100, "Mixed signal spiking network for time series", ["D"], doi="10.9/dupe"),
        oa(2101, "Mixed-signal spiking network for time series", ["D"], doi="10.9/dupe"),
        oa(2200, "Analog CMOS reservoir chip for ECG", ["D"]),
        ax("2204.00003", "Analog CMOS reservoir chips for ECG", ["xA"]),
        oa(3000, "Ferroelectric transistor short-term memory for gesture recognition", ["B3"]),
        oa(3001, "In materio computing with carbon nanotube networks for classification",
           ["C"]),
        oa(3002, "Temporal processing in a disordered film", ["E"],
           abstract="We build a physical reservoir from a film."),
        oa(3004, "In materio computing with carbon nanotube networks for the classification",
           ["F4"]),
        oa(1999, "", ["A"], abstract="Cover: this issue features...", vtype="paratext"),
    ]
    ex2 = [oa(3000, "Ferroelectric transistor short-term memory for gesture recognition",
              ["E"])]

    tmp = Path(tempfile.mkdtemp(prefix="supplement-selftest-"))
    try:
        corpus_path = tmp / "corpus.csv"
        write_csv(corpus_path, FIELDS, corpus_rows)
        corpus_hash = sha256(corpus_path)

        def export(name, recs, **extra):
            p = tmp / name
            p.write_text(json.dumps({"source": "supplementary", "retrieved_utc": "2026-10-25",
                                     "records": recs, **extra}))
            return p

        e1, e2 = export("s1.json", ex1), export("s2.json", ex2)
        out = tmp / "out"

        # field logic is dedupe's own
        oa_only = [r for r in ex1 if r["engine"] == "openalex"]
        (tmp / "oa.json").write_text(json.dumps({"records": [
            {**r, "authors": r["authors"].split("; ")} for r in oa_only]}))
        ref_oa, _ = dedupe.load_openalex(tmp / "oa.json")
        (tmp / "ax.json").write_text(json.dumps({"records": [r for r in ex1
                                                              if r["engine"] == "arxiv"]}))
        ref_ax = dedupe.load_arxiv(tmp / "ax.json")
        check("OpenAlex rows match dedupe.load_openalex field for field",
              [row_from_openalex(r) for r in oa_only] == ref_oa)
        check("arXiv rows match dedupe.load_arxiv field for field",
              [row_from_arxiv(r) for r in ex1 if r["engine"] == "arxiv"] == ref_ax)

        c = cmd_merge(corpus_path, [e1, e2], out, None, quiet=True)
        supp = list(csv.DictReader((out / "corpus_supplementary.csv").open()))
        by_oa = {r["openalex_id"]: r for r in supp}
        ids = {r["openalex_id"]: r["record_id"] for r in supp}

        check("the corpus file is unchanged", sha256(corpus_path) == corpus_hash)
        check("counts: identified, cross-export repeat, unique",
              (c["identified_records"], c["cross_export_repeats"], c["identified_unique"])
              == (18, 1, 17))
        check("an untitled record is removed before dedup and listed",
              c["removed_untitled"] == {"count": 1, "identities": ["openalex:W1999"]})
        check("within-leg removals by basis", c["removed_within_leg"]
              == {"doi": 1, "arxiv_id": 1, "title": 1})
        check("already in corpus by basis (dup_of rows resolve to their survivor)",
              c["already_in_corpus"] == {"openalex_id": 1, "doi": 2, "arxiv_id": 1, "title": 1})
        check("eight new records", c["new_records"] == 8 and len(supp) == 8)
        check("new ids start above the corpus and follow block, title, identity order",
              ids == {"W2000": "RC-0007", "W3000": "RC-0008", "W1006": "RC-0009",
                      "W3001": "RC-0010", "W2200": "RC-0011", "W2100": "RC-0012",
                      "W3004": "RC-0013", "W3002": "RC-0014"})
        check("OpenAlex beats arXiv in a within-leg merge (canonical source_db)",
              by_oa["W2000"]["source_db"] == "arxiv|openalex"
              and by_oa["W2000"]["preprint_id"] == "2203.00002"
              and by_oa["W2000"]["supp_blocks"] == "B1|xB"
              and by_oa["W2000"]["supp_engine"] == "arxiv|openalex")
        check("blocks from a second export are unioned", by_oa["W3000"]["supp_blocks"] == "B3|E")
        check("matches_orig_literal flags a literal executed phrase",
              [r["openalex_id"] for r in supp if r["matches_orig_literal"] == "1"] == ["W3002"])
        m = list(csv.DictReader((out / "supplementary_corpus_matches.csv").open()))
        check("corpus matches list every known work with its basis",
              sorted((x["matched_record_id"], x["basis"]) for x in m)
              == [("RC-0001", "doi"), ("RC-0002", "arxiv_id"), ("RC-0003", "title"),
                  ("RC-0004", "doi"), ("RC-0004", "openalex_id")])
        check("an open copy of a closed corpus record is an oa_upgrade, not applied",
              [x["matched_record_id"] for x in m if x["oa_upgrade"] == "1"] == ["RC-0003"]
              and c["corpus_oa_upgrades"] == 1)
        rv = list(csv.DictReader((out / "supplementary_near_duplicates_for_review.csv").open()))
        check("near-duplicates flagged, not merged (one with the corpus, one within the leg)",
              sorted((r["record_id_a"], r["record_id_b"]) for r in rv)
              == [("RC-0006", "RC-0009"), ("RC-0010", "RC-0013")]
              and c["near_duplicate_pairs_with_corpus"] == 1)
        check("review file has dedupe's columns", list(rv[0]) == REVIEW_FIELDS)
        check("adjudication is incomplete until decided",
              c["near_duplicate_adjudication_complete"] is False
              and c["near_duplicate_undecided"] == 2)
        check("counts reconcile", c["new_active"] == 8 and "= 8 new active" in c["reconciliation"])

        # determinism and id stability
        before = {p.name: p.read_bytes() for p in out.iterdir() if p.suffix == ".csv"}
        c2 = cmd_merge(corpus_path, [e2, e1], out, None, quiet=True)
        after = {p.name: p.read_bytes() for p in out.iterdir() if p.suffix == ".csv"}
        check("a rerun (exports in the other order) is byte-identical", before == after)
        volatile = ("generated_utc", "inputs", "ids")
        check("counts are identical apart from the timestamp, inputs and id provenance",
              {k: v for k, v in c2.items() if k not in volatile}
              == {k: v for k, v in c.items() if k not in volatile})
        check("the rerun reuses every id from the ledger",
              (c["ids"]["allocated_this_run"], c2["ids"]["allocated_this_run"],
               c2["ids"]["reused_from_ledger"]) == (8, 0, 8))

        # adjudication
        rv_path = out / "supplementary_near_duplicates_for_review.csv"

        def adjudicate(rows, name="adj.csv"):
            p = tmp / name
            with p.open("w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=REVIEW_FIELDS)
                w.writeheader()
                w.writerows(rows)
            return p

        def aborts(fn) -> bool:
            try:
                fn()
            except MergeError:
                return True
            return False

        decided = [{**r, "decision": "same"} for r in rv]
        snap = {p.name: p.read_bytes() for p in out.iterdir()}
        c3 = cmd_merge(corpus_path, [e1, e2], out, adjudicate(decided), quiet=True)
        supp3 = {r["record_id"]: r for r in csv.DictReader((out / "corpus_supplementary.csv").open())}
        check("a 'same' with a corpus record marks the new record dup_of it",
              supp3["RC-0009"]["dup_of"] == "RC-0006"
              and supp3["RC-0009"]["dup_basis"] == "manual-adjudication")
        check("a 'same' between new records keeps the dedupe.prefer keeper",
              supp3["RC-0013"]["dup_of"] == "RC-0010" and supp3["RC-0010"]["dup_of"] == "")
        check("adjudicated counts reconcile", c3["removed_manual_adjudication"] == 2
              and c3["new_active"] == 6 and c3["near_duplicate_adjudication_complete"] is True)
        check("the corpus is still unchanged", sha256(corpus_path) == corpus_hash)
        ledger = {r["identity_key"]: r for r in
                  csv.DictReader((out / "supplementary_id_ledger.csv").open())}
        check("ledger records adjudicated duplicates",
              ledger["openalex:W1006"]["status"] == "adjudicated-duplicate-of:RC-0006")
        check("ledger keeps every identity of a merged record",
              ledger["openalex:W2000"]["record_id"] == ledger["arxiv:2203.00002"]["record_id"]
              == "RC-0007")

        check("a header-only adjudication file aborts",
              aborts(lambda: cmd_merge(corpus_path, [e1, e2], out, adjudicate([], "h.csv"),
                                       quiet=True)))
        check("a retitled row aborts",
              aborts(lambda: cmd_merge(corpus_path, [e1, e2], out, adjudicate(
                  [{**decided[0], "title_a": "x"}, decided[1]], "t.csv"), quiet=True)))
        check("an unexpected pair aborts",
              aborts(lambda: cmd_merge(corpus_path, [e1, e2], out, adjudicate(
                  decided + [{**decided[0], "record_id_b": "RC-0011"}], "u.csv"), quiet=True)))
        check("a duplicated row aborts",
              aborts(lambda: cmd_merge(corpus_path, [e1, e2], out, adjudicate(
                  decided + [decided[0]], "d.csv"), quiet=True)))
        check("an invalid decision aborts",
              aborts(lambda: cmd_merge(corpus_path, [e1, e2], out, adjudicate(
                  [{**decided[0], "decision": "yes"}, decided[1]], "i.csv"), quiet=True)))
        blank = cmd_merge(corpus_path, [e1, e2], out, adjudicate(
            [{**r, "decision": ""} for r in rv], "b.csv"), quiet=True)
        check("blank decisions leave the gate closed",
              blank["near_duplicate_adjudication_complete"] is False
              and blank["near_duplicate_undecided"] == 2)
        new_by_id = {"RC-0009": {"record_id": "RC-0009", "dup_of": ""}}
        check("a component joining two corpus records aborts",
              aborts(lambda: apply_same([("RC-0006", "RC-0009"), ("RC-0009", "RC-0001")],
                                        new_by_id, survivor_map(corpus_rows))))
        check("a corpus dup_of row resolves to its survivor in a component",
              apply_same([("RC-0005", "RC-0009")], new_by_id, survivor_map(corpus_rows)) == 1
              and new_by_id["RC-0009"]["dup_of"] == "RC-0004")

        # review-file guard: a file with decisions is never overwritten
        rv_path.write_text(adjudicate(decided, "keep.csv").read_text())
        guarded = rv_path.read_bytes()
        cmd_merge(corpus_path, [e1, e2], out, None, quiet=True)
        check("a review file carrying decisions is not overwritten",
              rv_path.read_bytes() == guarded
              and rv_path.with_suffix(".new.csv").exists())

        # ledger: an id is issued once
        e3 = export("s3.json", [r for r in ex1 if r.get("openalex_id") != "W3000"]
                    + [oa(3005, "Aardvark reservoir", ["A"])])
        out2 = tmp / "out2"
        out2.mkdir()
        shutil.copy(out / "supplementary_id_ledger.csv", out2 / "supplementary_id_ledger.csv")
        c4 = cmd_merge(corpus_path, [e3], out2, None, quiet=True)
        ids4 = {r["openalex_id"]: r["record_id"]
                for r in csv.DictReader((out2 / "corpus_supplementary.csv").open())}
        led4 = {r["identity_key"]: r for r in
                csv.DictReader((out2 / "supplementary_id_ledger.csv").open())}
        check("ids survive a later export; a new work gets the next unissued id",
              ids4["W2000"] == "RC-0007" and ids4["W3002"] == "RC-0014"
              and ids4["W3005"] == "RC-0015" and c4["ids"]["allocated_this_run"] == 1)
        check("a work that drops out keeps its ledger row and id",
              led4["openalex:W3000"]["record_id"] == "RC-0008"
              and led4["openalex:W3000"]["status"] == "absent-from-exports"
              and "RC-0008" not in ids4.values())

        bad = [dict(r) for r in csv.DictReader((out / "supplementary_id_ledger.csv").open())]
        for r in bad:
            if r["identity_key"] == "openalex:W2100":
                r["record_id"] = "RC-0011"
        out3 = tmp / "out3"
        out3.mkdir()
        write_csv(out3 / "supplementary_id_ledger.csv", LEDGER_FIELDS, bad)
        check("one ledger id covering two separate records aborts",
              aborts(lambda: cmd_merge(corpus_path, [e1], out3, None, quiet=True)))
        write_csv(out3 / "supplementary_id_ledger.csv", LEDGER_FIELDS,
                  [{"record_id": "RC-0003", "identity_key": "openalex:W9",
                    "first_seen_export": "x", "status": "active"}])
        check("a ledger id colliding with a corpus id aborts",
              aborts(lambda: cmd_merge(corpus_path, [e1], out3, None, quiet=True)))
        merged_ledger = [dict(r) for r in csv.DictReader((out / "supplementary_id_ledger.csv").open())
                         if r["identity_key"] != "arxiv:2203.00002"]
        merged_ledger.append({"record_id": "RC-0099", "identity_key": "arxiv:2203.00002",
                              "first_seen_export": "s0.json", "status": "active"})
        out4 = tmp / "out4"
        out4.mkdir()
        write_csv(out4 / "supplementary_id_ledger.csv", LEDGER_FIELDS, merged_ledger)
        c5 = cmd_merge(corpus_path, [e1, e2], out4, None, quiet=True)
        led5 = {r["identity_key"]: r for r in
                csv.DictReader((out4 / "supplementary_id_ledger.csv").open())}
        check("two ledger ids linked by a later export keep the lower; the other is retired",
              c5["ids"]["merged_into"] == {"RC-0099": "RC-0007"}
              and led5["arxiv:2203.00002"]["status"] == "merged-into:RC-0007")

        # empty export
        e0 = export("s0.json", [])
        c0 = cmd_merge(corpus_path, [e0], tmp / "out0", None, quiet=True)
        check("an empty export gives a header-only file and zero counts",
              (tmp / "out0" / "corpus_supplementary.csv").read_text().strip()
              == ",".join(SUPP_FIELDS) and c0["new_active"] == 0
              and c0["near_duplicate_adjudication_complete"] is True)
        check("a --count-only export is refused",
              aborts(lambda: cmd_merge(corpus_path, [export("sc.json", [], count_only=True)],
                                       tmp / "outc", None, quiet=True)))
        check("an output path equal to an input is refused",
              aborts(lambda: cmd_merge(tmp / "out" / "corpus_supplementary.csv", [e1],
                                       tmp / "out", None, quiet=True)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # non-Latin titles: dedupe's norm_title reduces them to nothing
    jp = "完全カオス光学ビリヤードの普遍則と物理リザバーコンピューティングへの応用"
    cand = attach(row_from_openalex(oa(5, jp, ["A"])), "openalex:W5", "openalex", ["A"], "x")
    check("a non-Latin title keeps a Unicode key", title_key(jp).startswith("u:")
          and norm_title(jp) == "" and title_key("") == "")
    check("a non-Latin title matches the same title in the corpus",
          CorpusIndex([crow("RC-0100", jp, oaid="W1")]).match(cand) == ("title", ["RC-0100"]))
    check("a non-Latin title does not match a different one",
          CorpusIndex([crow("RC-0100", "別の論文の題名", oaid="W1")]).match(cand) == ("", []))

    # blocked near-duplicate search equals the brute-force scan
    rng = random.Random(20261024)
    words = ("reservoir memristor photonic network temporal spiking device array delay "
             "computing classification signal").split()
    titles = []
    for _ in range(160):
        t = " ".join(rng.choice(words) for _ in range(rng.randint(2, 6)))
        titles.append(t)
        if rng.random() < 0.4:
            titles.append(t + rng.choice(["", " a", " the x", "s", " new"]))
    titles.append("")
    flags = [rng.random() < 0.4 for _ in titles]
    check("blocked near-duplicate search equals brute force on a random fixture",
          near_pairs(titles, flags) == near_pairs_brute(titles, flags))
    check("pairs between two corpus rows are never flagged",
          all(flags[i] or flags[j] for i, j, _ in near_pairs(titles, flags)))

    print("\nselftest", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--corpus", type=Path, default=CORPUS)
    m.add_argument("--supplementary", type=Path, nargs="+", required=True)
    m.add_argument("--adjudications", type=Path, default=None)
    m.add_argument("--out-dir", type=Path, default=OUT_DIR)
    m.add_argument("--ledger", type=Path, default=None,
                   help="default: <out-dir>/supplementary_id_ledger.csv")
    sub.add_parser("selftest")
    args = ap.parse_args()
    if args.cmd == "selftest":
        return selftest()
    try:
        cmd_merge(args.corpus, args.supplementary, args.out_dir, args.adjudications,
                  args.ledger)
    except MergeError as exc:
        print(f"ABORT: {exc}\nNothing was written.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
