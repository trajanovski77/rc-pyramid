#!/usr/bin/env python3
"""Validation Study 2: frame, draw, statistics and design simulation.

    python3 scripts/validation.py frame                      # pool, strata, exclusions
    python3 scripts/validation.py draw [--design reduced]    # seeded sample + packets
    python3 scripts/validation.py stats --a A.csv --b B.csv  # after both files are in
    python3 scripts/validation.py simulate [--design reduced]
    python3 scripts/validation.py selftest

Implements docs/validation-study-2.md; section numbers below refer to it. Standard library
only. Everything a reader needs to audit the selection is fixed in this file before the
draw: the stratum rules (`STRATA`), their precedence, the exclusion lists, the allocation,
the shortfall rules, the seed and the order in which records are sampled.

WHY A STRATIFIED DRAW, AND WHAT IT CAN AND CANNOT ESTIMATE
---------------------------------------------------------
The pilot drew 40 records at random and every assigned record fell in F1 or F2, so it says
nothing about F3, F4 or their boundaries. F3 and F4 are a few per cent of the corpus; at 2%
a random draw finds about 3 of a family per 160 records, and 30 would need about 1,500.
So the draw is enriched by keyword strata. The rules read bibliographic text only, never a
family judgement, and coders never see them. Every pool record has a positive inclusion
probability (§3.3), so design-weighted estimates for the pool exist; but the primary target
is reliability **under the specified enriched allocation** (§5.1), and conclusions are
restricted to it.

WHAT THE STATISTICS TREAT AS A CODE
-----------------------------------
§4.3 fixes the mapping, and `op_label` / `families` implement it. Every sampled record is
kept: an ineligible record is negative for every family, as is an unassignable one; a
symmetric hybrid FaxFb counts as positive for both Fa and Fb. The pilot-comparable labels
(`pilot_label`) fold ineligible into unassignable, as the pilot's coders did.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import shutil
import sys
import tempfile
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screen  # noqa: E402
from dedupe import norm_arxiv_id, norm_doi, norm_title  # noqa: E402

csv.field_size_limit(10 ** 8)

SEED = 20261024
CORPUS = Path("data/screening/corpus_deduped.csv")
SUPPLEMENTARY = Path("data/screening/corpus_supplementary.csv")
SUPP_COUNTS = Path("data/screening/prisma_counts_supplementary.json")
OUTDIR = Path("data/screening/validation2")
PILOT_SAMPLES = [
    Path("data/screening/dryrun/pilot/pilot_sample.json"),          # preliminary check
    Path("data/screening/pilot-01-failed-20260905/pilot_sample.json"),
    Path("data/screening/pilot/pilot_sample.json"),
]

# §3.1(3). Exactly the publication objects protocol.md §4.2 lists as outside §4.1. Types it
# does not list (review, editorial, other, supplementary-materials) stay in the pool and are
# judged on their content by the coders: bibliographic type is not eligibility.
DROP_TYPES = {"dissertation", "book", "conference-abstract", "dataset", "software", "report",
              "erratum", "retraction", "peer-review", "paratext", "reference-entry"}

# §3.1(5). Systems the manuscript uses as worked examples (Tables 6 and 9, and the two
# device rows of WS4), matched on DOI, arXiv id or normalized title so that a preprint or
# a supplementary copy of the same work is excluded too. Jaeger 2001 is a technical report
# with no identifier and outside the window.
WORKED_EXAMPLES = [
    ("Maass 2002", "10.1162/089976602760407955", "", ""),
    ("Gallicchio 2017", "10.1016/j.neucom.2016.12.089", "", ""),
    ("Du 2017", "10.1038/s41467-017-02337-y", "", ""),
    ("Appeltant 2011", "10.1038/ncomms1476", "", ""),
    ("Brunner 2013", "10.1038/ncomms2368", "", ""),
    ("Vandoorne 2014", "10.1038/ncomms4541", "", ""),
    ("Gauthier 2021", "10.1038/s41467-021-25801-2", "2106.07688",
     "Next generation reservoir computing"),
    ("Torrejon 2017", "10.1038/nature23011", "", ""),
    ("Milano 2022", "10.1038/s41563-021-01099-9", "",
     "In materia reservoir computing with a fully memristive architecture based on "
     "self-organizing nanowire networks"),
    ("Nakajima 2015", "10.1038/srep10487", "", ""),
    ("Sumi 2023", "10.1073/pnas.2217008120", "",
     "Biological neurons act as generalization filters in reservoir computing"),
    ("Zhong 2022", "10.1038/s41928-022-00838-3", "",
     "A memristor-based analogue reservoir computing system for real-time and "
     "power-efficient signal processing"),
    ("Zhong 2022 preprint", "10.21203/rs.3.rs-1592701/v1", "", ""),
    ("Duran 2026", "10.1088/2634-4386/ae66b2", "2509.17355", ""),
]


# ---------------------------------------------------------------- strata (§3.2, Appendix A)

def rx(*alts: str) -> re.Pattern:
    return re.compile("(?:%s)" % "|".join(alts), re.I)


# S4 sub-strata, in precedence order: a record matching several goes to the first.
S4_SUB = {
    "S4a": rx(r"\bnanowire", r"atomic[- ]switch", r"carbon nanotube", r"\bcnts?\b",
              r"nanoparticle (?:network|array|film)", r"self[- ]assembl", r"percolat",
              r"in[- ]materi[oa]", r"dopant network", r"polymer network", r"ionic liquid",
              r"electrochemical (?:network|cell)"),
    "S4b": rx(r"spin[- ]waves?", r"\bmagnons?\b", r"magnonic", r"skyrmion", r"spin ice",
              r"\bspeckle", r"scattering medi", r"multimode fib(?:er|re)", r"\bacoustic wave",
              r"surface acoustic", r"ultrasound"),
    "S4c": rx(r"soft[- ]robot", r"soft body", r"soft material", r"tensegrity",
              r"morphological computation", r"compliant body", r"origami", r"mass[- ]spring",
              r"octopus", r"physical body"),
    "S4d": rx(r"neuronal culture", r"cultured neuron", r"neural culture", r"organoid",
              r"in vitro neuron", r"dissociated (?:cortical )?neuron", r"living neuron",
              r"bacteri", r"\bfungal", r"slime mou?ld", r"physarum", r"living (?:cells?|tissue)"),
    "S4e": rx(r"water (?:tank|bucket|surface|wave)", r"fluidic", r"\bbucket\b", r"liquid crystal",
              r"cellular automat", r"coupled map lattice", r"\bbz reaction", r"belousov",
              r"chemical reaction network", r"molecular (?:system|reservoir)",
              r"dna (?:computing|reservoir|strand)", r"\bgel\b"),
}
MEDIUM = rx(*(p.pattern for p in S4_SUB.values()))
STRATA = {
    "F3": rx(r"next[- ]generation reservoir", r"\bng[- ]?rcs?\b", r"nonlinear vector auto[- ]?regress",
             r"\bnvars?\b"),
    # The wider explicit-feature vocabulary of taxonomy §5's subclasses: random features and
    # projections (F3.2), orthogonal bases (F3.3), Kolmogorov-Arnold constructions (F3.4).
    "F3T": rx(r"extreme learning machine", r"\belms?\b", r"random features?", r"random fourier",
              r"random projections?", r"polynomial features?", r"volterra series",
              r"time[- ]delay embedding", r"legendre", r"chebyshev",
              r"orthogonal (?:basis|polynomial)", r"kolmogorov[- ]arnold"),
    "DELAY": rx(r"\bdelay(?:ed)?[- ](?:based|loop|line|feedback|system|reservoir)",
                r"time[- ]multiplex", r"virtual nodes?", r"single (?:dynamical |nonlinear )?node",
                r"delay[- ]coupled"),
    "ARRAY": rx(r"memristor (?:array|crossbar)", r"memristive (?:array|crossbar)", r"crossbar",
                r"coupled oscillators?", r"oscillator (?:network|array)s?",
                r"spatial light modulator", r"\bslm\b", r"diffractive"),
    "ESN": rx(r"echo[- ]state network", r"\besns?\b"),
    "EXPLICIT": rx(r"nonlinear vector auto[- ]?regress", r"\bnvar", r"polynomial features?",
                   r"linear (?:reservoir|echo state)", r"next[- ]generation",
                   r"explicit (?:feature|nonlinear)"),
}
STRATUM_ORDER = ["SB", "S3", "S4a", "S4b", "S4c", "S4d", "S4e", "S3T", "S0"]


def text_of(r: dict) -> str:
    """The only text a stratum rule reads: NFKC title + abstract."""
    return unicodedata.normalize("NFKC", f"{r.get('title', '')} {r.get('abstract', '')}")


def rule_hits(t: str) -> dict[str, bool]:
    h = {k: bool(p.search(t)) for k, p in STRATA.items()}
    h["MEDIUM"] = bool(MEDIUM.search(t))
    return h


def stratum_of(r: dict) -> str:
    """SB, S3, S4a-S4e, S3T or S0: the first rule matched, in that order (§3.2).

    SB catches records whose text names mechanisms of two families: a medium with delay or
    time-multiplexing (F2-F4), a medium with an addressed array or oscillator (F1-F4), an
    ESN with an explicit-feature term (F1-F3), or an array with delay (F1-F2). SB goes first
    because a boundary record is the scarcest thing the study needs; that is an allocation
    choice, and the weights correct for it.
    """
    t = text_of(r)
    h = rule_hits(t)
    if ((h["MEDIUM"] and h["DELAY"]) or (h["MEDIUM"] and h["ARRAY"])
            or (h["ESN"] and h["EXPLICIT"]) or (h["ARRAY"] and h["DELAY"])):
        return "SB"
    if h["F3"]:
        return "S3"
    for k, p in S4_SUB.items():
        if p.search(t):
            return k
    if h["F3T"]:
        return "S3T"
    return "S0"


# ---------------------------------------------------------------- allocation (§3.3)

ALLOCATION = {
    "full": {"SB": 30, "S3": 47, "S4a": 12, "S4b": 12, "S4c": 12, "S4d": 12, "S4e": 12,
             "S3T": 10, "S0": 13},
    "reduced": {"SB": 15, "S3": 47, "S4a": 5, "S4b": 5, "S4c": 5, "S4d": 5, "S4e": 5,
                "S3T": 5, "S0": 8},
}
# The information condition of §5.3: records at least one coder assigned to the family.
INFO_MIN = {"full": 30, "reduced": 20}
# Where a stratum's shortfall goes when it is smaller than its allocation (§3.3).
SHORTFALL_TO = {"S3": ["S3T"], "S3T": ["S0"], "SB": ["S0"],
                **{k: [s for s in S4_SUB if s != k] for k in S4_SUB}}
# Bootstrap: a stratum with a single sampled record is merged with this partner (§5.4).
COLLAPSE = {"S4a": "S4b", "S4b": "S4a", "S4c": "S4b", "S4d": "S4c", "S4e": "S4d",
            "S3T": "S3", "S3": "S3T", "SB": "S0", "S0": "SB"}


def allocate(sizes: dict[str, int], design: str) -> dict[str, int]:
    """n_h per stratum: the allocation, capped at N_h, shortfalls moved by SHORTFALL_TO.

    S4 shortfalls go to the S4 sub-stratum with the most unsampled records, ties broken by
    precedence order, one record at a time, so the rule is deterministic and auditable.
    """
    alloc = dict(ALLOCATION[design])
    n = {h: min(alloc[h], sizes.get(h, 0)) for h in STRATUM_ORDER}
    for h in STRATUM_ORDER:
        short = alloc[h] - n[h]
        while short > 0:
            room = [t for t in SHORTFALL_TO.get(h, []) if sizes.get(t, 0) > n[t]]
            if not room:
                break
            t = max(room, key=lambda s: (sizes[s] - n[s], -STRATUM_ORDER.index(s)))
            n[t] += 1
            short -= 1
    return n


# ---------------------------------------------------------------- frame (§3.1)

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def identifiers(r: dict) -> set[str]:
    ids = set()
    if r.get("doi"):
        ids.add("doi:" + norm_doi(r["doi"]))
        a = norm_arxiv_id(r["doi"])
        if a:
            ids.add("arxiv:" + a)
    if r.get("preprint_id"):
        ids.add("arxiv:" + norm_arxiv_id(r["preprint_id"]))
    if r.get("openalex_id"):
        ids.add("openalex:" + r["openalex_id"])
    nt = norm_title(r.get("title", ""))
    if nt:
        ids.add("title:" + nt)
    return ids - {"arxiv:"}


def worked_example_ids() -> dict[str, str]:
    out = {}
    for label, doi, arx, title in WORKED_EXAMPLES:
        if doi:
            out["doi:" + norm_doi(doi)] = label
        if arx:
            out["arxiv:" + norm_arxiv_id(arx)] = label
        if title:
            out["title:" + norm_title(title)] = label
    return out


def build_frame(corpus: list[dict], supp: list[dict], pilot_ids: set[str]) -> dict:
    """Pool, exclusions with reasons, and strata. Pure: no file is read or written."""
    rows = [dict(r, _source="corpus") for r in corpus] + [dict(r, _source="supplementary")
                                                         for r in supp]
    wex = worked_example_ids()
    pilot_identities = set().union(*(identifiers(r) for r in rows
                                     if r["record_id"] in pilot_ids)) if pilot_ids else set()
    excluded: dict[str, list[str]] = {k: [] for k in
                                      ("duplicate", "closed", "publication-type", "pilot",
                                       "pilot-alternate-identifier", "worked-example")}
    pool = []
    for r in rows:
        rid = r["record_id"]
        if r.get("dup_of"):
            excluded["duplicate"].append(rid)
        elif r.get("is_oa") != "1":
            excluded["closed"].append(rid)
        elif r.get("venue_type") in DROP_TYPES:
            excluded["publication-type"].append(rid)
        elif rid in pilot_ids:
            excluded["pilot"].append(rid)
        elif identifiers(r) & pilot_identities:
            excluded["pilot-alternate-identifier"].append(rid)
        elif identifiers(r) & set(wex):
            excluded["worked-example"].append(rid)
        else:
            pool.append(r)
    strata: dict[str, list[str]] = {h: [] for h in STRATUM_ORDER}
    hits = Counter()
    for r in pool:
        strata[stratum_of(r)].append(r["record_id"])
        h = rule_hits(text_of(r))
        hits.update(k for k, v in h.items() if v)
        s4 = [k for k, p in S4_SUB.items() if p.search(text_of(r))]
        if len(s4) > 1:
            hits["S4-multiple-sub-strata"] += 1
    for h in strata:
        strata[h].sort(key=lambda x: int(x.split("-")[1]))
    return {"pool_size": len(pool), "excluded": {k: sorted(v) for k, v in excluded.items()},
            "strata": strata, "sizes": {h: len(v) for h, v in strata.items()},
            "rule_hits": dict(sorted(hits.items()))}


def pilot_record_ids() -> set[str]:
    ids = set()
    for p in PILOT_SAMPLES:
        ids |= set(json.loads(p.read_text())["record_ids"])
    return ids


def cmd_frame(args) -> int:
    out = args.outdir / "frame.json"
    if (args.outdir / "sample.json").exists():
        print(f"{args.outdir / 'sample.json'} exists: the sample has been drawn and its frame "
              f"is fixed. Refusing to rebuild the frame.", file=sys.stderr)
        return 1
    corpus = read_rows(CORPUS)
    supp, supp_note = [], "absent"
    if SUPPLEMENTARY.exists() and SUPP_COUNTS.exists():
        complete = json.loads(SUPP_COUNTS.read_text()).get("near_duplicate_adjudication_complete")
        if complete:
            supp, supp_note = read_rows(SUPPLEMENTARY), "included (adjudication complete)"
        else:
            supp_note = "excluded: near-duplicate adjudication incomplete"
    pilot = pilot_record_ids()
    frame = build_frame(corpus, supp, pilot)
    frame = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {"corpus": {"path": str(CORPUS), "sha256": sha256(CORPUS)},
                   "supplementary": ({"path": str(SUPPLEMENTARY), "sha256": sha256(SUPPLEMENTARY)}
                                     if supp else None),
                   "supplementary_status": supp_note,
                   "pilot_samples": [{"path": str(p), "sha256": sha256(p)} for p in PILOT_SAMPLES],
                   "script_sha256": sha256(Path(__file__))},
        "drop_types": sorted(DROP_TYPES),
        "worked_examples": [list(w) for w in WORKED_EXAMPLES],
        "stratum_rules": {**{k: p.pattern for k, p in STRATA.items()},
                          **{k: p.pattern for k, p in S4_SUB.items()}},
        **frame,
    }
    args.outdir.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(frame, indent=2, ensure_ascii=False))
    print(f"pool {frame['pool_size']}  (supplementary: {supp_note})")
    for k, v in frame["excluded"].items():
        print(f"  excluded {k:28s} {len(v):5d}")
    for h in STRATUM_ORDER:
        print(f"  {h:4s} {frame['sizes'][h]:5d}")
    print(f"-> {out}")
    return 0


# ---------------------------------------------------------------- draw (§3.3, §4.2)

PACKET_FIELDS = screen.PILOT_FIELDS
ADDON_FIELDS = ["evidence", "state_unit"]


def draw(frame: dict, design: str, seed: int = SEED) -> list[dict]:
    """Seeded simple random sampling without replacement within each stratum."""
    n = allocate(frame["sizes"], design)
    out = []
    for h in STRATUM_ORDER:
        ids = frame["strata"][h]                       # already in record-number order
        N = len(ids)
        if not n[h]:
            continue
        rng = random.Random(f"{seed}:{h}")
        for rid in sorted(rng.sample(ids, n[h]), key=lambda x: int(x.split("-")[1])):
            out.append({"record_id": rid, "stratum": h, "N_h": N, "n_h": n[h],
                        "pi": n[h] / N, "weight": N / n[h]})
    return out


def repaired_authors(s: str) -> str:
    """Undo dedupe.load_openalex's character-wise join (known issue D-A) where it applies."""
    if len(s) >= 4 and all(s[i:i + 2] == "; " for i in range(1, len(s) - 1, 3)):
        return s[::3]
    return s


def cmd_draw(args) -> int:
    frame_path = args.outdir / "frame.json"
    sample_path = args.outdir / "sample.json"
    if sample_path.exists():
        print(f"{sample_path} exists; a drawn sample is never redrawn.", file=sys.stderr)
        return 1
    frame = json.loads(frame_path.read_text())
    if frame["inputs"]["corpus"]["sha256"] != sha256(CORPUS):
        print("corpus changed since the frame was built; rebuild the frame first",
              file=sys.stderr)
        return 1
    sample = draw(frame, args.design, args.seed)
    by_id = {r["record_id"]: r for r in read_rows(CORPUS)}
    if frame["inputs"]["supplementary"]:
        by_id.update({r["record_id"]: r for r in read_rows(SUPPLEMENTARY)})
    fields = PACKET_FIELDS + (ADDON_FIELDS if args.addon else [])
    for coder in ("A", "B"):
        rows = [by_id[s["record_id"]] for s in sample]
        random.Random(f"{args.seed}:packet:{coder}").shuffle(rows)
        with (args.outdir / f"vs2_coder{coder}.packet-blank.csv").open("w", newline="",
                                                                        encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow({"record_id": r["record_id"],
                            "no_abstract": "" if r.get("has_abstract") == "1" else "1",
                            "title": r["title"], "abstract": r.get("abstract", ""),
                            "doi": r.get("doi", "")})
    # The coordinator's sheet (§4.2): one full text per record, retrieved once, before
    # coding, and supplied identically to both coders.
    with (args.outdir / "retrieval_log.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["record_id", "doi", "preprint_id", "openalex_id", "title", "year", "venue",
                    "authors", "oa_basis", "file_name", "retrieved", "source", "attempts",
                    "notes"])
        for s in sample:
            r = by_id[s["record_id"]]
            w.writerow([r["record_id"], r.get("doi", ""), r.get("preprint_id", ""),
                        r.get("openalex_id", ""), r["title"], r.get("year", ""),
                        r.get("venue", ""), repaired_authors(r.get("authors", "")),
                        r.get("oa_basis", ""), f"{r['record_id']}.pdf", "", "", "", ""])
    meta = {"generated_utc": datetime.now(timezone.utc).isoformat(), "seed": args.seed,
            "design": args.design, "addon": bool(args.addon),
            "frame_sha256": sha256(frame_path), "allocation": allocate(frame["sizes"], args.design),
            "sizes": frame["sizes"], "n": len(sample), "records": sample}
    sample_path.write_text(json.dumps(meta, indent=2))
    print(f"drew {len(sample)} records ({args.design})")
    for h in STRATUM_ORDER:
        print(f"  {h:4s} {meta['allocation'][h]:3d} of {frame['sizes'][h]:5d}")
    print(f"-> {sample_path}\n-> packets and retrieval_log.csv in {args.outdir}")
    return 0


# ---------------------------------------------------------------- coder files (§4.3)

class InputError(RuntimeError):
    pass


def read_coder(path: Path, manifest_ids: list[str], addon: bool) -> dict[str, dict]:
    """One coder's file, checked against the frozen manifest (exactly one complete row each).

    Vocabulary checks are screen.read_pilot_file's, so the pilot and this study accept the
    same codes. Added here: duplicate, missing and unknown ids abort; eligibility and reason
    are required on every row; an eligible record needs a family or symmetric label; the
    abstract-pass call is kept and validated, not discarded.
    """
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        cols = reader.fieldnames or []
    need = PACKET_FIELDS + (ADDON_FIELDS if addon else [])
    if set(need) - set(cols):
        raise InputError(f"{path.name}: missing columns {sorted(set(need) - set(cols))}")
    ids = [r["record_id"] for r in rows]
    dup = sorted(k for k, v in Counter(ids).items() if v > 1)
    if dup:
        raise InputError(f"{path.name}: records appear more than once: {dup[:5]}")
    if set(ids) != set(manifest_ids):
        raise InputError(f"{path.name}: rows do not match the sample "
                         f"(missing {sorted(set(manifest_ids) - set(ids))[:5]}, "
                         f"unknown {sorted(set(ids) - set(manifest_ids))[:5]})")
    try:
        parsed = screen.read_pilot_file(path)
    except SystemExit:
        raise InputError(f"{path.name}: a code failed the pilot vocabulary check "
                         f"(message above)") from None
    for line, r in enumerate(rows, 2):
        rec = parsed[r["record_id"]]
        if rec["eligible"] not in ("yes", "no"):
            raise InputError(f"{path.name}:{line}: eligible must be yes or no")
        if not rec["reason"]:
            raise InputError(f"{path.name}:{line}: reason is required on every row")
        if rec["eligible"] == "yes" and not (rec["family"] or rec["family_symmetric"]):
            raise InputError(f"{path.name}:{line}: an eligible record needs family or "
                             f"family_symmetric")
        fa = (r.get("family_abstract") or "").strip()
        fa_norm = fa.upper().replace("×", "X") if fa.upper()[:1] == "F" else fa.lower()
        if fa_norm and not (fa_norm in ("F1", "F2", "F3", "F4", "unassignable")
                            or re.fullmatch(r"F([1-4])XF([1-4])", fa_norm)):
            raise InputError(f"{path.name}:{line}: family_abstract {fa!r} is not a code")
        rec["family_abstract"] = fa_norm.replace("X", "x") if fa_norm.startswith("F") else fa_norm
        if addon:
            ev = (r.get("evidence") or "").strip().upper()
            su = (r.get("state_unit") or "").strip().lower()
            if rec["eligible"] == "yes" and ev not in {f"E{i}" for i in range(6)}:
                raise InputError(f"{path.name}:{line}: evidence must be E0-E5")
            if rec["eligible"] == "yes" and su not in ("physical", "virtual", "probe", "n/a"):
                raise InputError(f"{path.name}:{line}: state_unit must be physical, virtual, "
                                 f"probe or n/a")
            rec["evidence"], rec["state_unit"] = ev, su
    return parsed


# ---------------------------------------------------------------- labels (§4.3)

FAMILIES = ("F1", "F2", "F3", "F4")
OP_LABELS = ("F1", "F2", "F3", "F4", "hybrid-symmetric", "unassignable", "ineligible")


def op_label(rec: dict) -> str:
    if rec["eligible"] == "no":
        return "ineligible"
    return screen.agreement_label(rec)


def pilot_label(rec: dict) -> str:
    """The pilot's convention: ineligible records were coded unassignable."""
    lab = op_label(rec)
    return "unassignable" if lab == "ineligible" else lab


def expanded_label(rec: dict) -> str:
    """Each symmetric pair its own category (sensitivity analysis)."""
    lab = op_label(rec)
    return rec["family_symmetric"] if lab == "hybrid-symmetric" else lab


def families(rec: dict) -> set[str]:
    """Primary families: one for a single label, both for a symmetric pair, none otherwise."""
    lab = op_label(rec)
    if lab == "hybrid-symmetric":
        return set(rec["family_symmetric"].split("x"))
    return {lab} if lab in FAMILIES else set()


# ---------------------------------------------------------------- statistics (§5)

def table(units: list[tuple], j: str, strict: bool = False) -> tuple[float, float, float, float]:
    """Weighted (a, b, c, d) for family j: a both positive, b A only, c B only, d neither.

    units are (fams_a, fams_b, weight, ...) tuples; strict=True counts only single-family j.
    """
    a = b = c = d = 0.0
    for fa, fb, w, *_ in units:
        pa = (fa == {j}) if strict else (j in fa)
        pb = (fb == {j}) if strict else (j in fb)
        if pa and pb:
            a += w
        elif pa:
            b += w
        elif pb:
            c += w
        else:
            d += w
    return a, b, c, d


def psa(a, b, c, d=None):
    den = 2 * a + b + c
    return None if den == 0 else 2 * a / den


def kappa_bin(a, b, c, d):
    n = a + b + c + d
    if n == 0:
        return None
    po = (a + d) / n
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / n ** 2
    return None if abs(1 - pe) < 1e-12 else (po - pe) / (1 - pe)


def alpha_bin(a, b, c, d):
    """Krippendorff's alpha, nominal, two coders, from the 2 x 2 table.

    Weighted tables use the convention of §5.2: n is the weighted number of pairable values,
    so the estimate is the alpha that coding the whole pool would give.
    """
    n = 2 * (a + b + c + d)
    n1, n0 = 2 * a + b + c, 2 * d + b + c
    if n < 2:
        return None
    de = 2 * n1 * n0 / (n - 1)
    return None if de == 0 else 1 - 2 * (b + c) / de


def byrt(a, b, c, d):
    n = a + b + c + d
    return (None, None) if n == 0 else ((a - d) / n, (b - c) / n)


def cat_stats(pairs: list[tuple[str, str, float]], vocab: tuple[str, ...]) -> dict:
    """Weighted Cohen's kappa, Gwet's AC1 and Krippendorff's alpha over a vocabulary."""
    n = sum(w for *_, w in pairs)
    if n == 0:
        return {"kappa": None, "ac1": None, "alpha": None, "po": None}
    po = sum(w for x, y, w in pairs if x == y) / n
    ca, cb = Counter(), Counter()
    for x, y, w in pairs:
        ca[x] += w
        cb[y] += w
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    kappa = None if abs(1 - pe) < 1e-12 else (po - pe) / (1 - pe)
    K = len(vocab)
    pe1 = sum(((ca[k] + cb[k]) / (2 * n)) * (1 - (ca[k] + cb[k]) / (2 * n)) for k in vocab) / (K - 1)
    ac1 = None if abs(1 - pe1) < 1e-12 else (po - pe1) / (1 - pe1)
    marg = Counter()
    for k in set(ca) | set(cb):
        marg[k] = ca[k] + cb[k]
    nv = 2 * n
    do = 2 * sum(w for x, y, w in pairs if x != y)
    de = sum(marg[x] * marg[y] for x in marg for y in marg if x != y) / (nv - 1) if nv > 1 else 0
    alpha = None if de == 0 else 1 - do / de
    return {"kappa": kappa, "ac1": ac1, "alpha": alpha, "po": po}


def family_stats(units: list[tuple], j: str, strict: bool = False) -> dict:
    a, b, c, d = table(units, j, strict)
    pi, bi = byrt(a, b, c, d)
    return {"a": a, "b": b, "c": c, "d": d, "coder_a_positive": a + b,
            "coder_b_positive": a + c, "union_positive": a + b + c,
            "psa": psa(a, b, c), "kappa": kappa_bin(a, b, c, d),
            "alpha": alpha_bin(a, b, c, d), "byrt_prevalence": pi, "byrt_bias": bi}


def binom_cdf(x: int, n: int, p: float) -> float:
    return sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(x + 1))


def clopper_pearson_upper(x: int, n: int, level: float = 0.95) -> float:
    """Exact one-sided upper bound on a binomial proportion (bisection)."""
    if n == 0:
        return 1.0
    if x >= n:
        return 1.0
    lo, hi = x / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if binom_cdf(x, n, mid) > 1 - level:
            lo = mid
        else:
            hi = mid
    return hi


def conditional_alpha_bound(a: float, b: float, c: float, d: float) -> dict:
    """§5.4: the labelled substitute when the bootstrap is degenerate (no disagreement).

    q_U is the exact upper bound on the probability that a record either coder assigned to
    the family is a disagreement. Putting ceil(q_U * u) disagreements into the observed
    table, split evenly and with the total held fixed, gives a worst-case alpha *conditional
    on the observed prevalence*. It is not a design-based interval and is never reported as
    one.
    """
    u = int(round(a + b + c))
    x = int(round(b + c))
    q = clopper_pearson_upper(x, u)
    k = math.ceil(q * u)
    bb = cc = k / 2
    aa = max(a + b + c - k, 0.0)
    return {"q_upper": q, "psa_lower_from_q": 2 * (1 - q) / (2 - q) if q < 1 else 0.0,
            "alpha_conditional_worst_case": alpha_bin(aa, bb, cc, d),
            "label": "conditional binomial bound (not a design-based interval)"}


# ---------------------------------------------------------------- resampling (§5.4)

def bootstrap_strata(units: list[tuple]) -> dict[str, list[int]]:
    """Unit indices per bootstrap stratum, merging singleton strata by COLLAPSE."""
    by: dict[str, list[int]] = {}
    for i, u in enumerate(units):
        by.setdefault(u[3], []).append(i)
    for h in sorted(by, key=STRATUM_ORDER.index):
        if h in by and len(by[h]) == 1:
            partner = COLLAPSE.get(h)
            while partner and partner not in by:
                partner = COLLAPSE.get(partner)
            if partner and partner != h:
                by[partner].extend(by.pop(h))
    return by


def bootstrap(units: list[tuple], stat, B: int, seed: int, rao_wu: bool = False) -> dict:
    """Percentile 95% interval of stat(units) under stratified resampling.

    rao_wu=False: records resampled with replacement within strata (n_h draws), unweighted;
    the target is the fixed-allocation superpopulation (§5.4). rao_wu=True: the Rao-Wu
    rescaled bootstrap with finite-population correction for the HT-weighted pool estimate;
    a censused stratum (f_h = 1) contributes no variance, as it should.
    """
    rng = random.Random(f"{seed}:bootstrap")
    by = bootstrap_strata(units)
    vals, undefined = [], 0
    for _ in range(B):
        rep = []
        for h, idx in by.items():
            nh = len(idx)
            if not rao_wu:
                rep.extend(units[rng.choice(idx)] for _ in range(nh))
                continue
            if nh < 2:
                rep.extend(units[i] for i in idx)
                continue
            mh = nh - 1
            f = min(units[idx[0]][4], 1.0)       # sampling fraction n_h / N_h
            lam = math.sqrt(mh * (1 - f) / (nh - 1))
            r = Counter(rng.choice(idx) for _ in range(mh))
            for i in idx:
                u = units[i]
                w = u[2] * (1 - lam + lam * (nh / mh) * r[i])
                rep.append((u[0], u[1], w, u[3], u[4]) + tuple(u[5:]))
        v = stat(rep)
        if v is None:
            undefined += 1
        else:
            vals.append(v)
    if not vals or undefined > 0.01 * B:
        return {"lo": None, "hi": None, "undefined_replicates": undefined, "B": B,
                "status": "not evaluable"}
    vals.sort()
    lo, hi = vals[int(0.025 * (len(vals) - 1))], vals[int(math.ceil(0.975 * (len(vals) - 1)))]
    return {"lo": lo, "hi": hi, "undefined_replicates": undefined, "B": B,
            "status": "degenerate" if lo == hi else "ok"}


# ---------------------------------------------------------------- verdicts (§5.5)

def family_verdict(fs: dict, ci: dict, info_min: int, cond: dict | None) -> dict:
    """pass / criterion not met / insufficient information, with the reasons."""
    if fs["union_positive"] < info_min:
        return {"verdict": "insufficient information",
                "why": f"union-positive {fs['union_positive']:.0f} < {info_min}"}
    reasons = []
    if fs["psa"] is None or fs["psa"] < 0.80:
        reasons.append("PSA < 0.80")
    if fs["alpha"] is None or fs["alpha"] < 0.80:
        reasons.append("alpha < 0.80")
    if ci["status"] == "ok":
        if ci["lo"] < 0.667:
            reasons.append("alpha lower bound < 0.667")
        basis = "bootstrap"
    elif ci["status"] == "degenerate" and cond is not None:
        wc = cond["alpha_conditional_worst_case"]
        if wc is None or wc < 0.667:
            reasons.append("conditional alpha bound < 0.667")
        basis = cond["label"]
    else:
        return {"verdict": "insufficient information", "why": "alpha interval not evaluable"}
    return {"verdict": "pass" if not reasons else "criterion not met",
            "why": "; ".join(reasons) or "all criteria met", "lower_bound_basis": basis}


# ---------------------------------------------------------------- stats command

def analyse(sample: dict, A: dict, B: dict, B_reps: int = 10_000, seed: int = SEED) -> dict:
    recs = sample["records"]
    info_min = INFO_MIN[sample["design"]]
    units = [(families(A[s["record_id"]]), families(B[s["record_id"]]), 1.0, s["stratum"],
              s["pi"], s["record_id"]) for s in recs]
    wunits = [(u[0], u[1], s["weight"]) + u[3:] for u, s in zip(units, recs)]
    out: dict = {"n": len(recs), "design": sample["design"], "families": {}, "weighted": {}}
    for j in FAMILIES:
        fs = family_stats(units, j)
        fs["strict_single_family"] = family_stats(units, j, strict=True)
        elig = [u for u in units if A[u[5]]["eligible"] == B[u[5]]["eligible"] == "yes"]
        fs["mutually_eligible"] = family_stats(elig, j)
        cis = {}
        for name, fn in (("psa", lambda us, j=j: psa(*table(us, j))),
                         ("kappa", lambda us, j=j: kappa_bin(*table(us, j))),
                         ("alpha", lambda us, j=j: alpha_bin(*table(us, j)))):
            cis[name] = bootstrap(units, fn, B_reps, seed)
        fs["ci"] = cis
        cond = (conditional_alpha_bound(fs["a"], fs["b"], fs["c"], fs["d"])
                if fs["b"] + fs["c"] == 0 else None)
        fs["conditional_bound"] = cond
        if j in ("F3", "F4"):
            fs["verdict"] = family_verdict(fs, cis["alpha"], info_min, cond)
        out["families"][j] = fs
        wf = family_stats(wunits, j)
        wf["ci_alpha_rao_wu"] = bootstrap(wunits, lambda us, j=j: alpha_bin(*table(us, j)),
                                          B_reps, seed, rao_wu=True)
        out["weighted"][j] = wf

    pairs_pilot = [(pilot_label(A[s["record_id"]]), pilot_label(B[s["record_id"]]), 1.0)
                   for s in recs]
    pairs_op = [(op_label(A[s["record_id"]]), op_label(B[s["record_id"]]), 1.0) for s in recs]
    pairs_exp = [(expanded_label(A[s["record_id"]]), expanded_label(B[s["record_id"]]), 1.0)
                 for s in recs]
    exp_vocab = tuple(sorted({x for p in pairs_exp for x in p[:2]} | set(OP_LABELS)))
    out["overall"] = {
        "pilot_convention": cat_stats(pairs_pilot, screen.PILOT_FAMILIES),
        "operational": cat_stats(pairs_op, OP_LABELS),
        "expanded": cat_stats(pairs_exp, exp_vocab),
        "pilot_convention_weighted": cat_stats(
            [(x, y, s["weight"]) for (x, y, _), s in zip(pairs_pilot, recs)],
            screen.PILOT_FAMILIES),
    }
    k, po, pe, n = screen.cohens_kappa([(x, y) for x, y, _ in pairs_pilot])
    out["overall"]["legacy_kappa_ci"] = (dict(zip(("se", "lo", "hi"), screen.kappa_ci(k, po, pe, n)))
                                         if k is not None else None)
    out["overall"]["kappa_ci_bootstrap"] = bootstrap(
        [(x, y, 1.0, s["stratum"], s["pi"]) for (x, y, _), s in zip(pairs_pilot, recs)],
        lambda us: cat_stats([(u[0], u[1], 1.0) for u in us], screen.PILOT_FAMILIES)["kappa"],
        B_reps, seed)

    conf = Counter((x, y) for x, y, _ in pairs_op)
    out["confusion"] = {f"{x}|{y}": v for (x, y), v in sorted(conf.items())}
    rowtot = Counter(x for x, _, _ in pairs_op)
    out["conditional_b_given_a"] = {f"{x}->{y}": v / rowtot[x] for (x, y), v in conf.items()}
    mix = {}
    for i, x in enumerate(OP_LABELS):
        for y in OP_LABELS[i + 1:]:
            num = conf[(x, y)] + conf[(y, x)]
            den = sum(1 for p, q, _ in pairs_op if p in (x, y) or q in (x, y))
            if den:
                mix[f"{x}~{y}"] = {"disagreements": num, "records_either_coder_used_either": den,
                                   "rate": num / den}
    out["mix_up"] = mix

    both_sym = [(A[s["record_id"]]["family_symmetric"], B[s["record_id"]]["family_symmetric"])
                for s in recs if A[s["record_id"]]["family_symmetric"]
                and B[s["record_id"]]["family_symmetric"]]
    out["symmetric_pair_exact"] = {"both_symmetric": len(both_sym),
                                   "same_pair": sum(1 for x, y in both_sym if x == y)}
    k_e = screen.cohens_kappa([(A[s["record_id"]]["eligible"], B[s["record_id"]]["eligible"])
                               for s in recs])
    out["eligibility"] = {"kappa": k_e[0], "po": k_e[1],
                          "disagreements": sum(1 for s in recs if A[s["record_id"]]["eligible"]
                                               != B[s["record_id"]]["eligible"])}
    both = [s["record_id"] for s in recs
            if A[s["record_id"]]["eligible"] == B[s["record_id"]]["eligible"] == "yes"]
    ua = sum(1 for k_ in both if A[k_]["family"] == "unassignable")
    ub = sum(1 for k_ in both if B[k_]["family"] == "unassignable")
    out["unassignable"] = {"mutually_eligible": len(both),
                           "coder_a": ua, "coder_b": ub,
                           "rate_a": ua / len(both) if both else None,
                           "rate_b": ub / len(both) if both else None}
    per = {}
    for h in STRATUM_ORDER:
        ps = [(x, y, 1.0) for (x, y, _), s in zip(pairs_op, recs) if s["stratum"] == h]
        if ps:
            st = cat_stats(ps, OP_LABELS)
            per[h] = {"n": len(ps), "po": st["po"], "kappa": st["kappa"]}
    out["per_stratum"] = per
    abs_pairs = [(A[s["record_id"]].get("family_abstract", ""),
                  B[s["record_id"]].get("family_abstract", ""), 1.0) for s in recs
                 if A[s["record_id"]]["eligible"] == B[s["record_id"]]["eligible"] == "yes"]
    out["abstract_pass"] = cat_stats(abs_pairs, screen.PILOT_FAMILIES) if abs_pairs else None

    kappa_gate = out["overall"]["pilot_convention"]["kappa"]
    ra, rb = out["unassignable"]["rate_a"], out["unassignable"]["rate_b"]
    gates = {"overall_kappa_ge_0.70": kappa_gate is not None and kappa_gate >= 0.70,
             "unassignable_le_5pct_each_coder": ra is not None and rb is not None
             and max(ra, rb) <= 0.05}
    v3, v4 = out["families"]["F3"]["verdict"], out["families"]["F4"]["verdict"]
    joint = all(gates.values()) and v3["verdict"] == v4["verdict"] == "pass"
    if joint:
        jv = "joint success"
    elif "insufficient information" in (v3["verdict"], v4["verdict"]) and all(gates.values()) \
            and "criterion not met" not in (v3["verdict"], v4["verdict"]):
        jv = "insufficient information"
    else:
        jv = "joint criterion not met"
    out["gates"] = gates
    out["joint"] = {"verdict": jv, "F3": v3["verdict"], "F4": v4["verdict"]}
    return out


def cmd_stats(args) -> int:
    sample = json.loads((args.outdir / "sample.json").read_text())
    ids = [s["record_id"] for s in sample["records"]]
    try:
        A = read_coder(args.a, ids, sample["addon"])
        B = read_coder(args.b, ids, sample["addon"])
    except InputError as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 1
    res = analyse(sample, A, B, args.replicates, args.seed)
    res["inputs"] = {"a": {"path": str(args.a), "sha256": sha256(args.a)},
                     "b": {"path": str(args.b), "sha256": sha256(args.b)},
                     "sample_sha256": sha256(args.outdir / "sample.json")}
    res["generated_utc"] = datetime.now(timezone.utc).isoformat()
    (args.outdir / "vs2_statistics.json").write_text(json.dumps(res, indent=2))
    dis_path = args.outdir / "vs2_disagreements.csv"
    if dis_path.exists() and screen.has_reconciliation(dis_path):
        dis_path = dis_path.with_suffix(".new.csv")
    with dis_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["record_id", "stratum", "label_a", "label_b", "reason_a", "reason_b",
                    "deciding_text", "reconciled_rule"])
        for s in sample["records"]:
            a, b = A[s["record_id"]], B[s["record_id"]]
            if expanded_label(a) != expanded_label(b):
                w.writerow([s["record_id"], s["stratum"], expanded_label(a), expanded_label(b),
                            a["reason"], b["reason"], "", ""])
    for j in FAMILIES:
        f = res["families"][j]
        psa_txt = "n/a" if f["psa"] is None else f"{f['psa']:.3f}"
        alpha_txt = "n/a" if f["alpha"] is None else f"{f['alpha']:.3f}"
        print(f"  {j}: a={f['a']:.0f} b={f['b']:.0f} c={f['c']:.0f} d={f['d']:.0f}  "
              f"PSA {psa_txt}  alpha {alpha_txt}  {f.get('verdict', {}).get('verdict', '')}")
    print(f"  gates {res['gates']}\n  joint: {res['joint']['verdict']}\n"
          f"-> {args.outdir / 'vs2_statistics.json'}\n-> {dis_path}")
    return 0


# ---------------------------------------------------------------- simulation (§3.4)

# Assumed category yields per stratum (central scenario). These are guesses stated in
# advance, not estimates; the simulation varies them. Order: F1 F2 F3 F4 sym unassignable
# ineligible.
YIELDS = {
    "SB":  (0.30, 0.15, 0.08, 0.22, 0.05, 0.05, 0.15),
    "S3":  (0.15, 0.05, 0.55, 0.00, 0.02, 0.05, 0.18),
    "S4":  (0.20, 0.08, 0.00, 0.45, 0.02, 0.05, 0.20),
    "S3T": (0.35, 0.05, 0.15, 0.00, 0.00, 0.10, 0.35),
    "S0":  (0.60, 0.10, 0.02, 0.02, 0.01, 0.05, 0.20),
}
SIM_CATS = ("F1", "F2", "F3", "F4", "F1xF2", "unassignable", "ineligible")


def _scale(y: tuple, factor: float) -> tuple:
    """Multiply the F3 and F4 yields by factor and rescale the rest to sum to one."""
    f3, f4 = y[2] * factor, y[3] * factor
    rest = 1 - f3 - f4
    other = [v for i, v in enumerate(y) if i not in (2, 3)]
    s = sum(other)
    other = [v * rest / s for v in other]
    return (other[0], other[1], f3, f4, other[2], other[3], other[4])


def _code(true: str, err: float, rng: random.Random) -> dict:
    """One coder's code: the true category with probability 1 - err, else a confusion."""
    lab = true
    if rng.random() < err:
        lab = rng.choice([c for c in SIM_CATS if c != true])
    if lab == "ineligible":
        return {"eligible": "no", "family": "", "family_symmetric": ""}
    if lab == "F1xF2":
        return {"eligible": "yes", "family": "", "family_symmetric": "F1xF2"}
    return {"eligible": "yes", "family": lab, "family_symmetric": ""}


def simulate(design: str, sizes: dict, factor: float, err: float, sims: int, B: int,
             seed: int) -> dict:
    """Probability of adequate information and of passing, under assumed yields and error."""
    rng = random.Random(f"{seed}:sim:{design}:{factor}:{err}")
    n = allocate(sizes, design)
    info_min = INFO_MIN[design]
    tally = Counter()
    for s in range(sims):
        recs, A, B_ = [], {}, {}
        for h in STRATUM_ORDER:
            y = _scale(YIELDS["S4" if h.startswith("S4") else h], factor)
            for i in range(n[h]):
                rid = f"RC-{len(recs) + 1:04d}"
                true = rng.choices(SIM_CATS, weights=y)[0]
                A[rid], B_[rid] = _code(true, err, rng), _code(true, err, rng)
                recs.append({"record_id": rid, "stratum": h, "pi": n[h] / sizes[h],
                             "weight": sizes[h] / n[h]})
        units = [(families(A[r["record_id"]]), families(B_[r["record_id"]]), 1.0, r["stratum"],
                  r["pi"]) for r in recs]
        verdicts = []
        for j in ("F3", "F4"):
            fs = family_stats(units, j)
            if fs["union_positive"] >= info_min:
                tally[f"{j}_information"] += 1
            ci = bootstrap(units, lambda us, j=j: alpha_bin(*table(us, j)), B, seed + s)
            cond = (conditional_alpha_bound(fs["a"], fs["b"], fs["c"], fs["d"])
                    if fs["b"] + fs["c"] == 0 else None)
            v = family_verdict(fs, ci, info_min, cond)["verdict"]
            tally[f"{j}_{v}"] += 1
            verdicts.append(v)
        if verdicts == ["pass", "pass"]:
            tally["both_pass"] += 1
    return {k: v / sims for k, v in sorted(tally.items())}


def cmd_simulate(args) -> int:
    frame_path = args.outdir / "frame.json"
    sizes = json.loads(frame_path.read_text())["sizes"] if frame_path.exists() else None
    if not sizes:
        print("no frame.json; run `frame` first", file=sys.stderr)
        return 1
    print(f"design {args.design}: n = {allocate(sizes, args.design)}  "
          f"(sims {args.sims}, bootstrap B {args.replicates})")
    print(f"{'F3/F4 yield':>11s} {'error':>6s}  P(F3 info) P(F3 pass) P(F4 info) "
          f"P(F4 pass) P(both pass)")
    rows = []
    for factor in (0.6, 1.0, 1.3):
        for err in (0.05, 0.10, 0.15):
            p = simulate(args.design, sizes, factor, err, args.sims, args.replicates, args.seed)
            rows.append({"yield_factor": factor, "error": err, **p})
            print(f"{factor:>11.1f} {err:>6.2f}  {p.get('F3_information', 0):10.2f} "
                  f"{p.get('F3_pass', 0):10.2f} {p.get('F4_information', 0):10.2f} "
                  f"{p.get('F4_pass', 0):10.2f} {p.get('both_pass', 0):12.2f}")
    out = args.outdir / f"simulation_{args.design}.json"
    out.write_text(json.dumps({"generated_utc": datetime.now(timezone.utc).isoformat(),
                               "design": args.design, "sizes": sizes, "yields": YIELDS,
                               "sims": args.sims, "B": args.replicates, "rows": rows}, indent=2))
    print(f"-> {out}")
    return 0


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    ok = True

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        ok = ok and cond

    def rec(rid, title, abstract="", **kw):
        r = {"record_id": rid, "title": title, "abstract": abstract, "doi": "", "preprint_id": "",
             "openalex_id": "", "is_oa": "1", "venue_type": "article", "dup_of": "",
             "has_abstract": "1"}
        r.update(kw)
        return r

    # strata and precedence
    check("NG-RC text goes to S3", stratum_of(rec("RC-1", "Next generation reservoir computing "
                                                          "for weather")) == "S3")
    check("an ESN with an explicit-feature term goes to SB (F1-F3 boundary)",
          stratum_of(rec("RC-1", "Echo state network versus NVAR")) == "SB")
    check("a medium with delay goes to SB (F2-F4 boundary)",
          stratum_of(rec("RC-1", "Spin waves with delayed feedback loop")) == "SB")
    check("S4 sub-strata follow precedence a before b",
          stratum_of(rec("RC-1", "Nanowire networks and spin waves")) == "S4a")
    check("each S4 sub-stratum is reachable",
          [stratum_of(rec("RC-1", t)) for t in ("Atomic switch network", "Skyrmion fabric",
                                                "Soft robot arm", "Cultured neurons on MEA",
                                                "Water tank computing")]
          == ["S4a", "S4b", "S4c", "S4d", "S4e"])
    check("extreme learning machine goes to S3T", stratum_of(rec("RC-1", "An extreme learning "
                                                                         "machine")) == "S3T")
    check("anything else goes to S0", stratum_of(rec("RC-1", "Echo state networks for EEG")) == "S0")
    check("the stratum order is the documented one",
          STRATUM_ORDER == ["SB", "S3", "S4a", "S4b", "S4c", "S4d", "S4e", "S3T", "S0"])

    # frame exclusions
    corpus = [
        rec("RC-0001", "Echo state networks for EEG"),
        rec("RC-0002", "Echo state networks for ECG", dup_of="RC-0001"),
        rec("RC-0003", "Closed paper on ESNs", is_oa="0"),
        rec("RC-0004", "A thesis on reservoirs", venue_type="dissertation"),
        rec("RC-0005", "A review of reservoirs", venue_type="review"),
        rec("RC-0006", "Piloted paper", doi="10.1/p"),
        rec("RC-0007", "Next generation reservoir computing", doi="10.9/other-version"),
        rec("RC-0008", "Spin waves with delayed feedback loop"),
    ]
    supp = [rec("RC-0009", "Supplementary copy of the piloted paper", doi="10.1/P"),
            rec("RC-0010", "Duran preprint", preprint_id="2509.17355")]
    fr = build_frame(corpus, supp, {"RC-0006"})
    ex = fr["excluded"]
    check("duplicates, closed records and listed publication types are excluded",
          ex["duplicate"] == ["RC-0002"] and ex["closed"] == ["RC-0003"]
          and ex["publication-type"] == ["RC-0004"])
    check("an ambiguous type (review) stays in the pool for the coders",
          "RC-0005" in fr["strata"]["S0"])
    check("pilot records are excluded, and so are their other versions",
          ex["pilot"] == ["RC-0006"] and ex["pilot-alternate-identifier"] == ["RC-0009"])
    check("worked examples are excluded by title and by arXiv id",
          ex["worked-example"] == ["RC-0007", "RC-0010"])
    check("pool and strata", fr["pool_size"] == 3 and fr["strata"]["SB"] == ["RC-0008"])

    # allocation and draw
    sizes = {"SB": 60, "S3": 20, "S4a": 100, "S4b": 75, "S4c": 48, "S4d": 5, "S4e": 51,
             "S3T": 67, "S0": 2757}
    n = allocate(sizes, "full")
    check("a stratum smaller than its allocation is censused, shortfall moved by rule",
          n["S3"] == 20 and n["S3T"] == 10 + 27 and n["S4d"] == 5
          and n["S4a"] + n["S4b"] + n["S4c"] + n["S4e"] == 48 + 7)
    check("the full design draws 160", sum(allocate({**sizes, "S3": 47, "S4d": 21}, "full").values())
          == 160)
    check("the reduced design draws 100", sum(allocate({**sizes, "S3": 47, "S4d": 21},
                                                       "reduced").values()) == 100)
    check("every stratum has a positive inclusion probability",
          all(v > 0 for v in allocate({**sizes, "S3": 47, "S4d": 21}, "full").values()))
    big = {"strata": {h: [f"RC-{1000 * (i + 1) + k:04d}" for k in range(sizes[h])]
                      for i, h in enumerate(STRATUM_ORDER)}, "sizes": sizes}
    d1, d2 = draw(big, "full"), draw(big, "full")
    check("the draw is deterministic", d1 == d2)
    check("weights are N_h / n_h and inclusion probabilities n_h / N_h",
          all(abs(s["weight"] * s["pi"] - 1) < 1e-12 for s in d1))
    check("a different seed gives a different sample", draw(big, "full", seed=1) != d1)

    # labels
    def code(fam="", sym="", elig="yes", reason="r", fa=""):
        return {"family": fam, "family_symmetric": sym, "eligible": elig, "reason": reason,
                "subclass": "", "hybrid": "", "minutes": "", "title": "", "family_abstract": fa}

    check("an ineligible record is negative for every family and pilot-unassignable",
          families(code("F4", elig="no")) == set() and pilot_label(code("", elig="no"))
          == "unassignable" and op_label(code("", elig="no")) == "ineligible")
    check("a symmetric label is positive for both families",
          families(code(sym="F1xF4")) == {"F1", "F4"}
          and expanded_label(code(sym="F1xF4")) == "F1xF4")

    # statistics on the critique's worked table
    t = (30, 5, 5, 120)
    check("PSA = 2a / (2a + b + c)", abs(psa(*t) - 60 / 70) < 1e-12)
    check("binary alpha matches the critique's value (0.818)", abs(alpha_bin(*t) - 0.8177) < 1e-3)
    pairs = ([("F", "F")] * 30 + [("F", "N")] * 5 + [("N", "F")] * 5 + [("N", "N")] * 120)
    check("binary alpha equals screen.krippendorff_alpha_nominal",
          abs(alpha_bin(*t) - screen.krippendorff_alpha_nominal(pairs)) < 1e-12)
    check("binary kappa equals screen.cohens_kappa",
          abs(kappa_bin(*t) - screen.cohens_kappa(pairs)[0]) < 1e-12)
    rng = random.Random(3)
    cats = screen.PILOT_FAMILIES
    cp = [(rng.choice(cats), rng.choice(cats)) for _ in range(80)]
    cp += [(x, x) for x, _ in cp[:40]]
    cs = cat_stats([(x, y, 1.0) for x, y in cp], cats)
    check("unit-weight categorical kappa, AC1 and alpha equal screen.py's",
          abs(cs["kappa"] - screen.cohens_kappa(cp)[0]) < 1e-12
          and abs(cs["ac1"] - screen.gwet_ac1(cp, cats)) < 1e-12
          and abs(cs["alpha"] - screen.krippendorff_alpha_nominal(cp)) < 1e-12)
    cs2 = cat_stats([(x, y, 2.5) for x, y in cp], cats)
    check("a constant weight leaves kappa and AC1 unchanged",
          abs(cs2["kappa"] - cs["kappa"]) < 1e-12 and abs(cs2["ac1"] - cs["ac1"]) < 1e-12)
    check("Byrt indices are (a - d)/n and (b - c)/n", byrt(30, 7, 3, 120) == (-90 / 160, 4 / 160))
    check("Clopper-Pearson with zero events is 1 - 0.05^(1/n)",
          abs(clopper_pearson_upper(0, 30) - (1 - 0.05 ** (1 / 30))) < 1e-9)
    cb = conditional_alpha_bound(30, 0, 0, 130)
    q = cb["q_upper"]
    check("the q to PSA mapping is 2(1-q)/(2-q)", abs(cb["psa_lower_from_q"] - 2 * (1 - q) / (2 - q))
          < 1e-12 and cb["alpha_conditional_worst_case"] < 1)

    # bootstrap
    units = []
    for i in range(60):
        h = "S3" if i < 30 else "S0"
        pos = i % 3 != 0
        units.append(({"F3"} if pos else set(), {"F3"} if (pos and i % 7) else set(), 1.0, h,
                      0.5 if h == "S3" else 0.01, f"RC-{i:04d}"))
    stat = lambda us: alpha_bin(*table(us, "F3"))  # noqa: E731
    b1, b2 = bootstrap(units, stat, 300, 1), bootstrap(units, stat, 300, 1)
    check("the bootstrap is deterministic and brackets the estimate",
          b1 == b2 and b1["lo"] <= stat(units) <= b1["hi"] and b1["status"] == "ok")
    census = [(u[0], u[1], 1.0, u[3], 1.0, u[5]) for u in units]
    rw = bootstrap(census, stat, 200, 1, rao_wu=True)
    check("Rao-Wu on censused strata has no variance", rw["lo"] == rw["hi"] == stat(census))
    single = units[:30] + [units[45]]
    single = [u if u[5] != units[45][5] else u[:3] + ("S3T",) + u[4:] for u in single]
    check("a singleton stratum is merged with its partner",
          sorted(len(v) for v in bootstrap_strata(single).values()) == [31])
    perfect = [({"F3"}, {"F3"}, 1.0, "S3", 0.5, f"RC-{i}") for i in range(32)] + \
              [(set(), set(), 1.0, "S0", 0.01, f"RC-x{i}") for i in range(100)]
    fs = family_stats(perfect, "F3")
    ci = bootstrap(perfect, stat, 200, 1)
    cond = conditional_alpha_bound(fs["a"], fs["b"], fs["c"], fs["d"])
    v = family_verdict(fs, ci, 30, cond)
    check("zero disagreement uses the labelled conditional bound, never [1, 1] alone",
          ci["status"] == "degenerate" and v["lower_bound_basis"] == cond["label"])
    check("fewer than the minimum union-positive records is insufficient information",
          family_verdict(family_stats(perfect[:20] + perfect[32:], "F3"), ci, 30, cond)["verdict"]
          == "insufficient information")
    bad = [({"F3"}, {"F3"} if i % 2 else set(), 1.0, "S3", 0.5, f"RC-{i}") for i in range(40)]
    check("poor agreement on enough records is 'criterion not met', not a pass",
          family_verdict(family_stats(bad, "F3"), bootstrap(bad, stat, 200, 1), 30, None)["verdict"]
          == "criterion not met")

    # coder-file reader
    tmp = Path(tempfile.mkdtemp(prefix="vs2-selftest-"))
    try:
        def write(name, rows, fields=PACKET_FIELDS):
            p = tmp / name
            with p.open("w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=fields)
                w.writeheader()
                for r in rows:
                    w.writerow({f: r.get(f, "") for f in fields})
            return p

        good = [{"record_id": "RC-0001", "eligible": "yes", "family_abstract": "unassignable",
                 "family": "F4", "reason": "medium", "title": "t"},
                {"record_id": "RC-0002", "eligible": "no", "family": "unassignable",
                 "reason": "review", "title": "t"}]
        man = ["RC-0001", "RC-0002"]

        def fails(rows) -> bool:
            try:
                read_coder(write("x.csv", rows), man, False)
            except InputError:
                return True
            return False

        got = read_coder(write("g.csv", good), man, False)
        check("a complete file reads, keeping the abstract-pass call",
              got["RC-0001"]["family_abstract"] == "unassignable" and got["RC-0001"]["family"] == "F4")
        check("a duplicated record aborts", fails(good + [good[0]]))
        check("a missing record aborts", fails(good[:1]))
        check("an unknown record aborts", fails(good + [{**good[0], "record_id": "RC-0099"}]))
        check("blank eligibility aborts", fails([{**good[0], "eligible": ""}, good[1]]))
        check("a blank reason aborts", fails([{**good[0], "reason": ""}, good[1]]))
        check("an eligible record with no label aborts", fails([{**good[0], "family": ""}, good[1]]))
        check("a bad abstract-pass code aborts", fails([{**good[0], "family_abstract": "F5"}, good[1]]))
        import io
        import contextlib
        with contextlib.redirect_stderr(io.StringIO()):
            check("a code failing the pilot vocabulary aborts",
                  fails([{**good[0], "family": "F9"}, good[1]]))

        # end to end on a fabricated pair of files
        sample = {"design": "full", "addon": False,
                  "records": [{"record_id": r["record_id"], "stratum": "S4a", "pi": 0.1,
                               "weight": 10.0} for r in good]}
        A = read_coder(write("a.csv", good), man, False)
        B = read_coder(write("b.csv", good), man, False)
        res = analyse(sample, A, B, B_reps=50)
        check("analysis runs end to end and reports both conventions",
              res["overall"]["operational"]["po"] == 1.0
              and res["families"]["F4"]["verdict"]["verdict"] == "insufficient information")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    check("authors scrambled by dedupe are repaired exactly",
          repaired_authors("; ".join("Doan, NAK; Magri, L")) == "Doan, NAK; Magri, L"
          and repaired_authors("Zhou Zhou; Lizhong Zheng") == "Zhou Zhou; Lizhong Zheng")

    sim = simulate("full", {"SB": 60, "S3": 47, "S4a": 100, "S4b": 75, "S4c": 48, "S4d": 21,
                            "S4e": 51, "S3T": 67, "S0": 2757}, 1.0, 0.05, 5, 20, 1)
    check("the simulation returns probabilities", all(0 <= v <= 1 for v in sim.values()))

    print("\nselftest", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("frame")
    d = sub.add_parser("draw")
    d.add_argument("--design", choices=sorted(ALLOCATION), default="full")
    d.add_argument("--addon", action="store_true", help="add evidence and state_unit columns")
    s = sub.add_parser("stats")
    s.add_argument("--a", type=Path, required=True)
    s.add_argument("--b", type=Path, required=True)
    s.add_argument("--replicates", type=int, default=10_000)
    m = sub.add_parser("simulate")
    m.add_argument("--design", choices=sorted(ALLOCATION), default="full")
    m.add_argument("--sims", type=int, default=400)
    m.add_argument("--replicates", type=int, default=400)
    for p in (f, d, s, m):
        p.add_argument("--outdir", type=Path, default=OUTDIR)
        p.add_argument("--seed", type=int, default=SEED)
    sub.add_parser("selftest")
    args = ap.parse_args()
    if args.cmd == "selftest":
        return selftest()
    return {"frame": cmd_frame, "draw": cmd_draw, "stats": cmd_stats,
            "simulate": cmd_simulate}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
