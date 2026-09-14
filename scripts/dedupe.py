#!/usr/bin/env python3
"""Merge and deduplicate database exports into the screening corpus.

Implements docs/search-strategy.md §5. Standard library only.

    python3 scripts/dedupe.py \
        --openalex data/raw/openalex_YYYYMMDD.json \
        --arxiv    data/raw/arxiv_YYYYMMDD.json \
        --out      data/screening/corpus_deduped.csv

Every input is optional so the pipeline can be run incrementally as exports arrive.
The subscription legs (--scopus, --wos, --ieee) are retained and still work; under
deviation D5 they are no longer primary sources, so a normal run supplies neither.

Dedup order (search-strategy.md §5):
  1. exact DOI
  1b. exact arXiv identifier, for the preprint pairs DOI cannot reach (see below)
  2. normalized title, edit distance <= 3
  3. near-matches at ratio >= 0.90 written to a review file for MANUAL adjudication
Preprint/journal pairs resolve to the journal version; the arXiv id is retained.

Step 3 is a two-part loop. The first run writes near_duplicates_for_review.csv with the
identifiers a human needs to decide and an empty `decision` column. Fill that column with
`same` or `different` and re-run with --adjudications to apply it:

    python3 scripts/dedupe.py --openalex ... --arxiv ... \
        --adjudications data/screening/near_duplicates_for_review.csv

Adjudicated duplicates are MARKED, not deleted: the row stays in the corpus and gains
`dup_of` and `dup_basis`, so screening filters on `dup_of == ""` while a reader can still
see what was merged and why. A completed review file is never overwritten; a fresh list
goes to near_duplicates_for_review.new.csv instead.

Step 1b exists because the two primary legs disagree about what a preprint's DOI is.
OpenAlex assigns arXiv preprints the registered DataCite DOI 10.48550/arxiv.<id>; the
arXiv API reports the *journal* DOI where the author supplied one and nothing otherwise,
so 825 of 1,234 arXiv records carry no DOI at all. Without an identifier pass those pairs
fall through to fuzzy title matching, which is the weaker instrument. Matching on the
identifier both sources actually agree on is exact, so it belongs above the title pass.

OPEN ACCESS IS CARRIED, NOT APPLIED (deviation D6, search-strategy.md §1.3)
--------------------------------------------------------------------------
The harvest is the whole corpus; only the open subset enters screening. That restriction
is a screening step, not a dedup step, so this script never drops a closed record. It
carries `is_oa`, `oa_basis`, `oa_status`, `venue_type`, `year` and `cited_by_count`
through to the corpus so that §9.2 can characterise what the restriction excluded, and it
reports the open/closed split in the PRISMA counts.

`oa_basis` records *why* a record counts as openly retrievable, because the merge can
change the answer: a closed journal article with an arXiv preprint is retrievable even
though OpenAlex marks the article closed. That is the D6 criterion ("openly retrievable"),
not OpenAlex's `is_oa` flag, and conflating the two would silently shrink the corpus.

Counts are written to data/screening/prisma_counts.json and feed the PRISMA figure.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

FIELDS = [
    "record_id", "source_db", "doi", "preprint_id", "openalex_id",
    "title", "abstract", "has_abstract", "authors", "year", "venue", "venue_type",
    "is_oa", "oa_basis", "oa_status", "cited_by_count",
    "dup_of", "dup_basis",
]

NEAR_RATIO = 0.90
MAX_EDIT = 3


# ---------------------------------------------------------------- normalisation

def norm_title(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def norm_doi(d: str) -> str:
    d = (d or "").strip().lower()
    d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d)
    return d.strip()


def norm_arxiv_id(s: str) -> str:
    """Canonical, version-stripped arXiv identifier, or "" if there is not one.

    Accepts a bare id (2012.02974v2), an abs/pdf URL, or the DataCite DOI OpenAlex
    assigns preprints (10.48550/arXiv.2012.02974). Old-style ids (cond-mat/0402594)
    are handled too. The version suffix is dropped: v1 and v3 of a preprint are the
    same record for corpus purposes.
    """
    s = (s or "").strip().lower()
    if not s:
        return ""
    s = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", s)
    s = re.sub(r"^10\.48550/arxiv\.", "", s)
    s = re.sub(r"^(https?://)?arxiv\.org/(abs|pdf)/", "", s)
    s = re.sub(r"^arxiv:", "", s)
    s = re.sub(r"\.pdf$", "", s)
    m = re.match(r"^(\d{4}\.\d{4,5}|[a-z-]+(\.[a-z]{2})?/\d{7})(v\d+)?$", s)
    return m.group(1) if m else ""


def bounded_edit(a: str, b: str, cap: int = MAX_EDIT) -> int:
    """Levenshtein distance, early-exit above `cap`. Returns cap+1 if exceeded."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > cap:
            return cap + 1
        prev = cur
    return prev[-1]


def counter_delta(a: Counter, b: Counter) -> int:
    """Sum over the alphabet of |count_a(c) - count_b(c)|."""
    total = 0
    for c in a.keys() | b.keys():
        total += abs(a.get(c, 0) - b.get(c, 0))
    return total


# ---------------------------------------------------------------- loaders

def _first(row: dict, *names: str) -> str:
    lowered = {(k or "").strip().lower(): (v or "") for k, v in row.items()}
    for n in names:
        v = lowered.get(n.lower())
        if v:
            return v.strip()
    return ""


def _blank() -> dict:
    """Field defaults, so every loader emits the same shape."""
    return {
        "source_db": "", "doi": "", "preprint_id": "", "openalex_id": "",
        "title": "", "abstract": "", "has_abstract": "", "authors": "", "year": "",
        "venue": "", "venue_type": "", "is_oa": "", "oa_basis": "",
        "oa_status": "", "cited_by_count": "",
    }


def load_csv(path: Path, source: str) -> list[dict]:
    """Scopus and IEEE exports. Column names differ; probe a few aliases."""
    out = []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh):
            title = _first(row, "Title", "Document Title")
            if not title:
                continue
            r = _blank()
            abstract = _first(row, "Abstract")
            r.update({
                "source_db": source,
                "doi": norm_doi(_first(row, "DOI")),
                "title": title,
                "abstract": abstract,
                "has_abstract": "1" if abstract else "0",
                "authors": _first(row, "Authors", "Author"),
                "year": _first(row, "Year", "Publication Year"),
                "venue": _first(row, "Source title", "Publication Title", "Journal"),
            })
            out.append(r)
    return out


def load_wos(path: Path) -> list[dict]:
    """Web of Science tab-delimited export."""
    out = []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            title = _first(row, "TI", "Article Title")
            if not title:
                continue
            r = _blank()
            abstract = _first(row, "AB", "Abstract")
            r.update({
                "source_db": "wos",
                "doi": norm_doi(_first(row, "DI", "DOI")),
                "title": title,
                "abstract": abstract,
                "has_abstract": "1" if abstract else "0",
                "authors": _first(row, "AF", "AU", "Authors"),
                "year": _first(row, "PY", "Publication Year"),
                "venue": _first(row, "SO", "Source Title"),
            })
            out.append(r)
    return out


def load_arxiv(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for e in payload.get("records", []):
        r = _blank()
        abstract = e.get("abstract", "") or ""
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
            # journal_ref present => a published version exists; the pair is
            # resolved to the journal version at dedup, per search-strategy.md §5.
            #
            # `published-unspecified` rather than `journal`: a journal_ref string only
            # says a published version exists, not that its venue is a journal, and
            # plenty of them are conference proceedings. Where the record also matched
            # OpenAlex the merge supplies the real type; the label survives only on
            # arXiv-only records, where the type genuinely is not known. Inventing
            # `journal` here would put a second vocabulary into the field §9.2
            # characterises venue type on.
            "venue_type": "preprint" if not e.get("journal_ref") else "published-unspecified",
            # Every arXiv record is by construction openly retrievable, which is the
            # D6 eligibility criterion regardless of what a publisher's OA flag says.
            "is_oa": "1",
            "oa_basis": "arxiv",
            "oa_status": "",
        })
        out.append(r)
    return out


def load_openalex(path: Path) -> tuple[list[dict], int]:
    """OpenAlex harvest. Returns (records, paging_duplicates_removed).

    The harvester pages through the API, and a work whose page boundary shifts between
    requests can be delivered twice. Those repeats are an artefact of retrieval, not
    two records, so they are collapsed on `openalex_id` here and counted separately:
    PRISMA "records identified" should be the number of distinct works the source
    returned, and folding retrieval noise into the duplicate-removal count would
    overstate cross-database overlap.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    seen: dict[str, dict] = {}
    repeats = 0
    for e in payload.get("records", []):
        oid = e.get("openalex_id", "")
        if oid and oid in seen:
            repeats += 1
            continue
        doi = norm_doi(e.get("doi", ""))
        abstract = e.get("abstract", "") or ""
        r = _blank()
        r.update({
            "source_db": "openalex",
            "doi": doi,
            # OpenAlex registers preprints under 10.48550/arXiv.<id>, which is the only
            # place a bare arXiv identifier appears in its metadata.
            "preprint_id": norm_arxiv_id(doi),
            "openalex_id": oid,
            "title": e.get("title", "") or "",
            "abstract": abstract,
            "has_abstract": "1" if abstract else "0",
            "authors": "; ".join(e.get("authors", []) or []),
            "year": str(e.get("year") or ""),
            "venue": e.get("venue", "") or "",
            "venue_type": e.get("venue_type", "") or "",
            "is_oa": "1" if e.get("is_oa") else "0",
            "oa_basis": "openalex" if e.get("is_oa") else "",
            "oa_status": e.get("oa_status", "") or "",
            "cited_by_count": str(e.get("cited_by_count") or ""),
        })
        if oid:
            seen[oid] = r
        else:
            seen[f"_noid_{len(seen)}"] = r
    return list(seen.values()), repeats


# ---------------------------------------------------------------- dedup

def is_preprint(r: dict) -> bool:
    """Any source's preprint record, not just the arXiv leg's.

    OpenAlex returns 1,048 records typed `preprint`, many of them the same works the
    arXiv leg supplies. Keying this on source_db alone would let an OpenAlex preprint
    outrank the published article it should be merged into.
    """
    return (r.get("venue_type") or "") == "preprint"


def prefer(a: dict, b: dict) -> tuple[dict, dict]:
    """Return (keeper, dropped).

    Precedence, in order:
      1. A journal version beats a preprint (search-strategy.md §5).
      2. A bibliographic database beats arXiv. OpenAlex/Scopus/WoS/IEEE carry the
         canonical publication year and venue name; an arXiv record's year is its v1
         submission date, which for a preprint/journal pair is the *wrong* year for the
         included version.
      3. Otherwise the fuller abstract.
    """
    if is_preprint(a) != is_preprint(b):
        return (b, a) if is_preprint(a) else (a, b)
    a_arx, b_arx = a["source_db"] == "arxiv", b["source_db"] == "arxiv"
    if a_arx != b_arx:
        return (b, a) if a_arx else (a, b)
    return (a, b) if len(a.get("abstract", "")) >= len(b.get("abstract", "")) else (b, a)


def merge(keeper: dict, dropped: dict) -> None:
    srcs = set(keeper["source_db"].split("|")) | set(dropped["source_db"].split("|"))
    keeper["source_db"] = "|".join(sorted(s for s in srcs if s))
    # Retain the arXiv id on the journal record (search-strategy.md §2.4).
    if not keeper.get("preprint_id") and dropped.get("preprint_id"):
        keeper["preprint_id"] = dropped["preprint_id"]
    for f in ("doi", "openalex_id", "venue", "year", "authors", "venue_type",
              "oa_status", "cited_by_count"):
        if not keeper.get(f) and dropped.get(f):
            keeper[f] = dropped[f]
    # Abstracts are for screening, so take the fullest one regardless of which
    # record won on bibliographic grounds.
    if len(dropped.get("abstract", "")) > len(keeper.get("abstract", "")):
        keeper["abstract"] = dropped["abstract"]
    keeper["has_abstract"] = "1" if keeper.get("abstract") else "0"
    # Openness is a property of the *work*, and it survives the merge. A closed journal
    # article with an arXiv preprint is retrievable, which is what D6 eligibility turns
    # on. Recording the basis keeps the two senses of "open" distinguishable downstream.
    if "1" in (keeper.get("is_oa"), dropped.get("is_oa")):
        bases = set(keeper.get("oa_basis", "").split("|"))
        bases |= set(dropped.get("oa_basis", "").split("|"))
        bases.discard("")
        keeper["is_oa"] = "1"
        keeper["oa_basis"] = "|".join(sorted(bases))


def _surviving(r: dict, by_id: dict[str, dict]) -> dict:
    """Follow `dup_of` to the record that survived, for chained adjudications."""
    seen = set()
    while r.get("dup_of") and r["dup_of"] not in seen:
        seen.add(r["dup_of"])
        r = by_id[r["dup_of"]]
    return r


def _has_decisions(path: Path) -> bool:
    """True if a review file already carries at least one adjudication."""
    try:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            return any((row.get("decision") or "").strip() for row in csv.DictReader(fh))
    except (OSError, csv.Error):
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    # Each flag takes one or more files. Web of Science caps a single export at ~1,000
    # records and IEEE Xplore caps lower still, so a real search usually arrives as
    # several batch files per source. Accepting a list avoids hand-concatenating CSVs,
    # which is where header rows get duplicated into the data.
    ap.add_argument("--openalex", type=Path, nargs="*", default=[])
    ap.add_argument("--arxiv", type=Path, nargs="*", default=[])
    # Superseded as primary sources by deviation D5; kept so that a supplementary
    # coverage check can be run without editing this script.
    ap.add_argument("--scopus", type=Path, nargs="*", default=[])
    ap.add_argument("--wos", type=Path, nargs="*", default=[])
    ap.add_argument("--ieee", type=Path, nargs="*", default=[])
    ap.add_argument("--out", type=Path, default=Path("data/screening/corpus_deduped.csv"))
    ap.add_argument(
        "--adjudications", type=Path, default=None,
        help="completed near_duplicates_for_review.csv; applies the `same` decisions",
    )
    args = ap.parse_args()

    records: list[dict] = []
    per_source: dict[str, int] = {}
    paging_repeats = 0

    def _openalex_loader(p: Path) -> list[dict]:
        nonlocal paging_repeats
        got, repeats = load_openalex(p)
        paging_repeats += repeats
        return got

    for paths, loader, name in (
        (args.openalex, _openalex_loader, "openalex"),
        (args.scopus, lambda p: load_csv(p, "scopus"), "scopus"),
        (args.ieee, lambda p: load_csv(p, "ieee"), "ieee"),
        (args.wos, load_wos, "wos"),
        (args.arxiv, load_arxiv, "arxiv"),
    ):
        total = 0
        for path in paths:
            if not path.exists():
                print(f"  ! missing: {path}", file=sys.stderr)
                continue
            got = loader(path)
            total += len(got)
            records.extend(got)
            if len(paths) > 1:
                print(f"  {name:8s} {len(got):5d}  ({path.name})")
        if total:
            per_source[name] = total
            print(f"  {name:8s} {total:5d}" + ("  TOTAL" if len(paths) > 1 else ""))

    if not records:
        print("no input records — supply at least one export", file=sys.stderr)
        return 1

    if paging_repeats:
        print(f"  {'(paging)':8s} {paging_repeats:5d}  OpenAlex rows delivered twice, "
              f"collapsed on openalex_id before dedup")

    raw_total = len(records)

    # pass 1 — exact DOI
    by_doi: dict[str, dict] = {}
    staged: list[dict] = []
    dup_doi = 0
    for r in records:
        d = r["doi"]
        if d and d in by_doi:
            keeper, dropped = prefer(by_doi[d], r)
            merge(keeper, dropped)
            by_doi[d] = keeper
            dup_doi += 1
        elif d:
            by_doi[d] = r
        else:
            staged.append(r)
    staged.extend(by_doi.values())

    # pass 1b — exact arXiv identifier (see module docstring)
    by_arx: dict[str, dict] = {}
    staged2: list[dict] = []
    dup_arxiv = 0
    for r in staged:
        a = r.get("preprint_id", "")
        if a and a in by_arx:
            keeper, dropped = prefer(by_arx[a], r)
            merge(keeper, dropped)
            by_arx[a] = keeper
            dup_arxiv += 1
        elif a:
            by_arx[a] = r
        else:
            staged2.append(r)
    staged2.extend(by_arx.values())

    # pass 2 — normalized title, bounded edit distance
    #
    # Blocked rather than scanned linearly. Two exact necessary conditions for an edit
    # distance <= 3 prune the candidate set without discarding any true match:
    #   (i)  the lengths differ by at most 3;
    #   (ii) the per-character count vectors differ by at most 6 in L1, since each of
    #        the <= 3 edits changes that sum by at most 2.
    # Where several candidates survive, the lowest kept index wins, which is the record
    # the original linear scan would have found first. Both conditions are necessary,
    # not heuristic, so the output is identical to the unblocked scan.
    kept: list[dict] = []
    index: dict[str, int] = {}
    by_len: dict[int, list[int]] = {}
    counters: list[Counter] = []
    near_review: list[tuple[str, str]] = []
    dup_title = 0

    def _register(i: int, nt: str, cnt: Counter) -> None:
        index[nt] = i
        by_len.setdefault(len(nt), []).append(i)

    for r in staged2:
        nt = norm_title(r["title"])
        r["_nt"] = nt
        cnt = Counter(nt)
        hit = index.get(nt)
        if hit is None:
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
            merge(keeper, dropped)
            kept[hit] = keeper
            counters[hit] = Counter(keeper["_nt"])
            _register(hit, keeper["_nt"], counters[hit])
            dup_title += 1
            continue
        _register(len(kept), nt, cnt)
        kept.append(r)
        counters.append(cnt)

    # pass 3 — near matches flagged for MANUAL adjudication, never auto-merged
    #
    # Same blocking argument. SequenceMatcher.ratio is 2M/T for M matched characters
    # across T = len(a) + len(b), so with len(a) <= len(b):
    #   (i)  M <= len(a) gives ratio <= 2*len(a)/T, hence len(b) <= (11/9)*len(a) at 0.90;
    #   (ii) M <= sum_c min(count_a(c), count_b(c)) gives the character-count bound.
    # Both are upper bounds on the true ratio, so nothing above threshold is skipped.
    # This replaces an earlier `abs(len(a) - len(b)) > 40` skip, which was a heuristic
    # and did discard true pairs among long titles. Logged as deviation D7.
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
            if 2 * shared < NEAR_RATIO * (la + lb):
                continue
            ratio = SequenceMatcher(None, a, b).ratio()
            if ratio >= NEAR_RATIO:
                near_review.append((min(i, j), max(i, j), round(ratio, 4)))

    for n, r in enumerate(kept, 1):
        r["record_id"] = f"RC-{n:04d}"
        r["dup_of"] = ""
        r["dup_basis"] = ""
        r.pop("_nt", None)

    # ---- manual adjudications, if a completed review file was supplied
    #
    # Applied here rather than by hand-editing the corpus, and applied by MARKING rather
    # than by deleting: an adjudicated duplicate keeps its row and gains `dup_of` and
    # `dup_basis`, so screening filters on `dup_of == ""` and the decision stays visible
    # to a reader. A silently vanished row is indistinguishable from a row that was never
    # retrieved, which is not a distinction this study can afford to lose.
    manual_merges = 0
    decided_same = decided_different = undecided = 0
    if args.adjudications:
        by_id = {r["record_id"]: r for r in kept}
        with args.adjudications.open(newline="", encoding="utf-8-sig") as fh:
            for line, row in enumerate(csv.DictReader(fh), 2):
                decision = (row.get("decision") or "").strip().lower()
                if decision == "":
                    undecided += 1
                    continue
                if decision == "different":
                    decided_different += 1
                    continue
                decided_same += 1
                if decision != "same":
                    print(f"  ! {args.adjudications.name}:{line}: decision must be "
                          f"'same', 'different' or blank, got {decision!r}",
                          file=sys.stderr)
                    return 1
                ra, rb = by_id.get(row["record_id_a"]), by_id.get(row["record_id_b"])
                if ra is None or rb is None:
                    print(f"  ! {args.adjudications.name}:{line}: unknown record id",
                          file=sys.stderr)
                    return 1
                # Record ids are positional, so an adjudication file made against a
                # different harvest would point at the wrong records while looking
                # perfectly valid. Verify the titles still match before acting.
                if (ra["title"], rb["title"]) != (row["title_a"], row["title_b"]):
                    print(f"  ! {args.adjudications.name}:{line}: titles do not match "
                          f"the corpus. This file was adjudicated against a different "
                          f"harvest; re-adjudicate rather than apply it.", file=sys.stderr)
                    return 1
                # Decisions can chain: A~B and B~C are both plausible adjudications of the
                # same work, and they must resolve to one surviving record rather than
                # two. Follow each side to its surviving record first. Skipping a pair
                # whose sides were already folded in would silently drop C.
                ra, rb = _surviving(ra, by_id), _surviving(rb, by_id)
                if ra is rb:
                    continue          # already the same record via an earlier pair
                keeper, dropped = prefer(ra, rb)
                merge(keeper, dropped)
                dropped["dup_of"] = keeper["record_id"]
                dropped["dup_basis"] = "manual-adjudication"
                manual_merges += 1
        print(f"  adjudications: {decided_same} same, {decided_different} different, "
              f"{undecided} undecided -> {manual_merges} merges applied")
        if undecided:
            print(f"  ! {undecided} pairs are still undecided; the corpus is not final",
                  file=sys.stderr)

    active = [r for r in kept if not r["dup_of"]]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(kept)

    # The review file is a working file, not a report: it carries the identifiers an
    # adjudicator needs to decide and an empty `decision` column to fill in. Titles alone
    # cannot settle these. "Photonic" against "Photovoltaic Reservoir Computing" are two
    # papers; "conn2res: A toolbox..." against "<tt>conn2res</tt>: A toolbox..." is one
    # paper and a markup artefact. Both sit at ratio >= 0.90, which is exactly why the
    # threshold routes them to a human instead of merging them.
    review_path = args.out.parent / "near_duplicates_for_review.csv"
    # Never clobber human work. A completed review file is hours of adjudication and it
    # is not regenerable, so if one is present the fresh list goes to a sibling path and
    # the operator reconciles them.
    if args.adjudications and args.adjudications.resolve() == review_path.resolve():
        review_path = args.out.parent / "near_duplicates_for_review.new.csv"
    elif review_path.exists() and _has_decisions(review_path):
        review_path = args.out.parent / "near_duplicates_for_review.new.csv"
        print(f"  ! existing review file carries decisions; writing to {review_path.name} "
              f"rather than overwriting it", file=sys.stderr)

    sorted_review = sorted(near_review, key=lambda t: -t[2])
    with review_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([
            "ratio", "decision", "adjudicated_by", "note",
            "record_id_a", "title_a", "year_a", "venue_a", "doi_a", "source_db_a",
            "record_id_b", "title_b", "year_b", "venue_b", "doi_b", "source_db_b",
        ])
        for i, j, ratio in sorted_review:
            a, b = kept[i], kept[j]
            w.writerow([
                ratio, "", "", "",
                a["record_id"], a["title"], a["year"], a["venue"], a["doi"], a["source_db"],
                b["record_id"], b["title"], b["year"], b["venue"], b["doi"], b["source_db"],
            ])

    # Open/closed split, reported here so the PRISMA figure and the §9.2 exclusion
    # characterisation read the same numbers from the same file. Computed over `active`,
    # which excludes records folded in by manual adjudication.
    oa_open = sum(1 for r in active if r.get("is_oa") == "1")
    oa_by_basis = Counter(r.get("oa_basis", "") or "closed" for r in active)
    no_abstract_open = sum(
        1 for r in active if r.get("is_oa") == "1" and r.get("has_abstract") != "1"
    )

    counts = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "per_source": per_source,
        "openalex_paging_repeats_collapsed": paging_repeats,
        "raw_total": raw_total,
        "removed_doi_exact": dup_doi,
        "removed_arxiv_id_exact": dup_arxiv,
        "removed_title_match": dup_title,
        "removed_manual_adjudication": manual_merges,
        "deduped_total": len(active),
        "near_duplicate_pairs_flagged": len(near_review),
        "near_duplicate_decided_same": decided_same,
        "near_duplicate_decided_different": decided_different,
        "near_duplicate_undecided": (
            len(near_review) if not args.adjudications else undecided
        ),
        "near_duplicate_adjudication_complete": bool(
            args.adjudications and not undecided
        ),
        "open_access_eligible": oa_open,
        "closed_excluded_d6": len(active) - oa_open,
        "open_access_basis": dict(sorted(oa_by_basis.items())),
        "open_without_abstract": no_abstract_open,
    }
    counts_path = args.out.parent / "prisma_counts.json"
    counts_path.write_text(json.dumps(counts, indent=2))

    pending = "" if args.adjudications else " (PENDING, not yet applied)"
    print(
        f"\nraw               {raw_total}\n"
        f"- doi duplicates  {dup_doi}\n"
        f"- arxiv id dups   {dup_arxiv}\n"
        f"- title matches   {dup_title}\n"
        f"- manual merges   {manual_merges}\n"
        f"= corpus          {len(active)}\n"
        f"\nopen access (D6 eligible for screening)  {oa_open}\n"
        f"closed, retained as metadata only        {len(active) - oa_open}\n"
        f"open but no abstract, flag at Stage 1    {no_abstract_open}\n"
        f"\nnear-duplicate pairs at ratio >= {NEAR_RATIO}: {len(near_review)}{pending}\n"
        f"  -> {review_path}\n"
        f"     fill the `decision` column with same/different, then re-run with\n"
        f"     --adjudications {review_path}\n"
        f"counts -> {counts_path}\n"
        f"corpus -> {args.out}\n\n"
        f"Record raw and deduped totals in docs/search-strategy.md §6."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
