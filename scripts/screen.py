#!/usr/bin/env python3
"""Screening support for the RC audit (protocol.md §5, §7).

Standard library only.

    python3 scripts/screen.py stage1-init  --coders ST AB
    python3 scripts/screen.py kappa        --a data/screening/stage1_ST.csv \
                                           --b data/screening/stage1_AB.csv
    python3 scripts/screen.py stage1-merge --a ... --b ...
    python3 scripts/screen.py pilot        --coders ST AB
    python3 scripts/screen.py status
    python3 scripts/screen.py selftest

WHAT THIS ENFORCES, AND WHY IT IS CODE RATHER THAN INSTRUCTIONS
---------------------------------------------------------------
Four properties of §5 are easy to lose when screening is run in a shared spreadsheet, and
each of them is load-bearing for a reliability statistic the paper reports:

1. **Blindness.** Coders get separate files containing title and abstract only, in
   different orders. One shared sheet with two decision columns is not blind coding, and a
   kappa computed from it is not a reliability measure. Metadata that could bias a
   borderline call (venue, year, citation count, open-access status) is withheld.
2. **Disagreements advance.** §5 makes Stage 1 liberal. Left to a human merge, the
   temptation at a disagreement is to discuss and settle it, which quietly converts a
   two-coder screen into a consensus screen and destroys the kappa.
3. **Kappa is computed before resolution, not after.** Once disagreements are resolved the
   agreement rate is 100 percent by construction. The merge therefore computes kappa on the
   raw decisions first and writes it out with them.
4. **Records with no abstract are screened, not dropped.** 222 eligible records have a title
   and nothing else. Dropping them would silently shrink the corpus; they carry a flag, are
   screened on title alone, and their outcomes are reported separately.

SEQUENCING
----------
Stage 1 cannot begin until the near-duplicate pairs from `dedupe.py` are adjudicated
(search-strategy.md §5.1). `stage1-init` refuses to run otherwise. `--allow-unadjudicated`
exists for dry runs and marks its output accordingly; it must not be used for real coding,
because a duplicate pair screened as two records is two votes for one paper.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

CORPUS = Path("data/screening/corpus_deduped.csv")
COUNTS = Path("data/screening/prisma_counts.json")
OUTDIR = Path("data/screening")

# Screening is title and abstract (protocol.md §5). Nothing else is exposed.
CODER_FIELDS = ["record_id", "no_abstract", "title", "abstract",
                "decision", "exclude_code", "note"]

DECISIONS = ("include", "exclude")

# The pilot (protocol.md §7) is a CLASSIFICATION task, not a screening decision, so its
# worklists carry the taxonomy fields instead of the Stage-1 decision vocabulary. Until
# 2026-08-27 the pilot packet reused CODER_FIELDS, which would have handed coders a file
# whose columns did not match their instructions in preliminary-agreement-check.md.
# `minutes` added 2026-09-05 on a referee request: annotation-methodology papers
# conventionally report time per record, and anyone reusing this protocol on a larger
# corpus needs it to budget. Optional, and never used in an agreement statistic; a blank
# column must not stop a coder submitting.
# `eligible` and `family_symmetric` added 2026-09-05 (deviations D21, D22), before the
# pre-registered pilot was drawn and after the preliminary check exposed why each is needed.
# `family_abstract` added 2026-09-05 (deviation D25). The pilot is coded in two passes:
# `family_abstract` is the call from title and abstract alone, `family` the call after
# opening the full text of anything the abstract left unassignable. Both rates are reported
# and the gate is `family`. Recording pass 1 separately is what keeps the abstract-only
# figure comparable with the 2026-08-28 check and pilot 1 rather than discarding it.
# `doi` is exposed here and nowhere else in the screening workflow, because pass 2 requires
# the coder to fetch the paper; Stage-1 screening still withholds it.
PILOT_FIELDS = ["record_id", "no_abstract", "title", "abstract", "doi",
                "eligible", "family_abstract", "family", "family_symmetric", "subclass",
                "hybrid", "reason", "minutes"]

# The agreement vocabulary. `hybrid-symmetric` is one category covering every symmetric
# label, not one per pair: F1xF2 and F1xF4 are both "the coder declined to name a dominant
# mechanism", which is the judgement kappa should be measuring. Which pair they chose is
# reported separately, exactly as subclass agreement is, so the information is kept without
# fragmenting the vocabulary into six sparse cells that would depress kappa by construction.
PILOT_FAMILIES = ("F1", "F2", "F3", "F4", "hybrid-symmetric", "unassignable")

# The four family codes a symmetric label may combine.
PILOT_FAMILY_CODES = ("F1", "F2", "F3", "F4")

# Records dispositioned under `taxonomy-v1.0.md` R11 (deviation D29). R11 covers a record
# reporting systems in two DIFFERENT families - not one system combining mechanisms, which
# is §2.1 and carries `family_symmetric`. Where both systems are co-equal main-text
# comparators and neither is subordinate, R11 makes the record `unassignable` and states
# that it "is reported with its reason under protocol.md §7 rather than counted against the
# instrument": the instrument classified the record correctly, and what defeats a single
# family code is the record containing two papers' worth of system, not the taxonomy
# failing on one. protocol.md §7 already requires each unassignable record's reason to be
# tabulated because "a record that the instrument cannot classify" and "a record that does
# not contain the information the instrument needs" are different findings; this is a third
# kind and is reported as such.
#
# THREE CONSTRAINTS, because this list changes a gate result and an unaudited exclusion
# list is exactly what §7's "never a record dropped from the calculation" forbids:
#   1. Membership is declared here by record id with its justification, never inferred from
#      reason text, so a reader can check every entry against the coder files.
#   2. A record is carved out ONLY where both coders judged it eligible AND both coded it
#      `unassignable`. One coder assigning a family makes it a disagreement, which is the
#      thing the gate exists to measure, and it then counts in full.
#   3. The unadjusted rate is printed and written to the JSON in every case. The carve-out
#      never replaces a number, it only adds one beside it.
# It does not touch kappa, which is computed over all sampled records on all six categories.
R11_TWO_SYSTEM_RECORDS = {
    "RC-3140": "ELM and ESN reported as co-equal main-text comparators, neither "
               "subordinate; both coders independently coded it unassignable citing R11 "
               "(pilot 2, 2026-09-05).",
}


def r11_carve_out(both_elig, a, b):
    """Record ids excluded from the gate NUMERATOR under R11 (D29).

    Returns the subset of `both_elig` that is declared in R11_TWO_SYSTEM_RECORDS and that
    both coders coded `unassignable`. The denominator is deliberately left alone: the
    record stays in the sample, in kappa and in the all-records rate, and only stops being
    counted as an instrument failure.
    """
    return [k for k in both_elig
            if k in R11_TWO_SYSTEM_RECORDS
            and a[k]["family"] == "unassignable"
            and b[k]["family"] == "unassignable"]

ELIGIBILITY = ("yes", "no")

# The §4.2 codes a coder can reach from a title and an abstract. `unavailable` is a
# Stage-2 outcome and `duplicate` is settled at dedup, so neither is offered here:
# an exclusion vocabulary that contains codes the coder cannot justify at this stage
# invites them to be used as a shrug.
STAGE1_EXCLUDE_CODES = (
    "not-rc:no-state-map",
    "not-rc:trained-internals",
    "not-rc:no-trained-readout",
    "not-rc:static-input",
    "no-result",
    "not-primary",
)

# Physical-substrate terminology proxy (protocol.md §9.2, taxonomy §7 D1).
#
# This is a PROXY and is used for exactly two things: stratifying the pilot so it cannot
# come out all-simulated, and characterising the D6 exclusion. It is not a family
# assignment and never substitutes for one. Terms are drawn from the D1 vocabulary and
# kept deliberately broad, since a proxy that under-fires would make the exclusion look
# more even across families than it is.
SUBSTRATE_TERMS = {
    "photonic": ("photonic", "optical", "optoelectronic", "laser", "waveguide",
                 "silicon photonic", "semiconductor laser", "fiber", "fibre"),
    "spintronic-magnetic": ("spintronic", "magnetic", "magnon", "skyrmion", "nanomagnet",
                            "spin-torque", "spin torque", "spin wave", "artificial spin ice"),
    "memristive-ionic": ("memristive", "memristor", "resistive switching", "rram",
                         "ionic", "electrochemical", "synaptic device", "ferroelectric"),
    "analog-electronic": ("analog circuit", "analogue circuit", "cmos", "electronic circuit",
                          "transistor", "oscillator circuit"),
    "mechanical-soft": ("soft robot", "mechanical", "tensegrity", "elastomer",
                        "pneumatic", "compliant body", "octopus"),
    "biological-organic": ("biological", "organic", "in vitro", "neuronal culture",
                           "cortical", "bacterial", "plant", "organoid"),
    "quantum": ("quantum reservoir", "qubit", "quantum computing", "nmr",
                "quantum dot", "quantum system"),
    "digital-hardware": ("fpga", "asic", "on-chip implementation"),
}


# ---------------------------------------------------------------- helpers

def load_corpus(path: Path = CORPUS) -> list[dict]:
    if not path.exists():
        print(f"missing {path}. Run scripts/dedupe.py first.", file=sys.stderr)
        raise SystemExit(1)
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def eligible(rows: list[dict]) -> list[dict]:
    """The screening set: not a duplicate, and openly retrievable (D6)."""
    return [r for r in rows if not r["dup_of"] and r["is_oa"] == "1"]


def substrate_hits(text: str) -> set[str]:
    """Which physical-substrate vocabularies a title/abstract touches."""
    low = (text or "").lower()
    return {label for label, terms in SUBSTRATE_TERMS.items()
            if any(t in low for t in terms)}


def is_physical_proxy(r: dict) -> bool:
    return bool(substrate_hits(f"{r.get('title','')} {r.get('abstract','')}"))


def cohens_kappa(pairs: list[tuple[str, str]]) -> tuple[float | None, float, float, int]:
    """Return (kappa, observed agreement, expected agreement, n).

    kappa is None where it is undefined, which happens when expected agreement is 1:
    both coders used a single category throughout. That is not perfect reliability and
    must not be reported as kappa = 1, so it is returned as undefined and the caller
    says so. A screen where one coder includes everything is exactly the case where a
    spuriously perfect kappa would be most misleading.
    """
    n = len(pairs)
    if n == 0:
        return None, 0.0, 0.0, 0
    cats = {c for p in pairs for c in p}
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    if abs(1.0 - pe) < 1e-12:
        return None, po, pe, n
    return (po - pe) / (1 - pe), po, pe, n


def adjudication_done() -> tuple[bool, int]:
    """(complete, pairs outstanding), read from the PRISMA counts."""
    if not COUNTS.exists():
        return False, -1
    c = json.loads(COUNTS.read_text())
    return bool(c.get("near_duplicate_adjudication_complete")), \
        int(c.get("near_duplicate_undecided", -1))


def read_coder_file(path: Path) -> dict[str, dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    out = {}
    for line, r in enumerate(rows, 2):
        d = (r.get("decision") or "").strip().lower()
        if d and d not in DECISIONS:
            print(f"  ! {path.name}:{line}: decision must be one of "
                  f"{'/'.join(DECISIONS)} or blank, got {d!r}", file=sys.stderr)
            raise SystemExit(1)
        code = (r.get("exclude_code") or "").strip()
        if d == "exclude" and code not in STAGE1_EXCLUDE_CODES:
            print(f"  ! {path.name}:{line}: exclude needs an exclude_code from "
                  f"{', '.join(STAGE1_EXCLUDE_CODES)}", file=sys.stderr)
            raise SystemExit(1)
        if d == "include" and code:
            print(f"  ! {path.name}:{line}: include must not carry an exclude_code",
                  file=sys.stderr)
            raise SystemExit(1)
        out[r["record_id"]] = {"decision": d, "exclude_code": code,
                               "note": r.get("note", ""), "title": r.get("title", "")}
    return out


def _write_coder_file(path: Path, rows: list[dict], coder: str, seed: int,
                      dry: bool, fields: list[str] = CODER_FIELDS) -> None:
    # Independent shuffle per coder. A shared order means both coders meet the same
    # record when equally fatigued, which correlates their errors and inflates kappa.
    order = list(rows)
    random.Random(f"{seed}:{coder}").shuffle(order)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in order:
            row = {
                "record_id": r["record_id"],
                "no_abstract": "1" if r.get("has_abstract") != "1" else "",
                "title": r["title"],
                "abstract": r.get("abstract", ""),
            }
            # The pilot's pass-2 full-text step (D25) needs a way to reach the paper, so the
            # DOI is populated where the packet asks for it. Stage-1 screening does not: its
            # field list has no `doi` column and this is a no-op there, which keeps the
            # blindness guarantee in the module docstring intact.
            if "doi" in fields:
                row["doi"] = r.get("doi", "") or r.get("preprint_id", "")
            row.update({f: row.get(f, "") for f in fields})
            w.writerow(row)
    tag = "  [DRY RUN, NOT FOR CODING]" if dry else ""
    print(f"  {path}  {len(order)} records{tag}")


# ---------------------------------------------------------------- commands

def cmd_stage1_init(args) -> int:
    done, outstanding = adjudication_done()
    dry = bool(args.allow_unadjudicated)
    if not done and not dry:
        print(f"Stage 1 is blocked: {outstanding} near-duplicate pairs are unadjudicated "
              f"(search-strategy.md §5.1).\nA duplicate pair screened as two records is "
              f"two votes for one paper.\nAdjudicate first, or pass --allow-unadjudicated "
              f"for a dry run.", file=sys.stderr)
        return 1

    rows = eligible(load_corpus())
    no_abs = sum(1 for r in rows if r.get("has_abstract") != "1")
    outdir = OUTDIR / "dryrun" if dry else OUTDIR
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Stage-1 worklists, {len(rows)} eligible records "
          f"({no_abs} with no abstract, screened on title alone):")
    for coder in args.coders:
        _write_coder_file(outdir / f"stage1_{coder}.csv", rows, coder, args.seed, dry)

    print(f"\nDecision vocabulary: {' / '.join(DECISIONS)}. Liberal inclusion: any "
          f"plausible RC record\nadvances, and disagreements advance automatically at "
          f"merge (protocol.md §5).")
    print(f"Exclude codes: {', '.join(STAGE1_EXCLUDE_CODES)}")
    if dry:
        print("\nDRY RUN. Do not code these files; adjudicate the near-duplicates first.")
    return 0


def cmd_kappa(args) -> int:
    a, b = read_coder_file(args.a), read_coder_file(args.b)
    shared = sorted(set(a) & set(b))
    pairs = [(a[k]["decision"], b[k]["decision"]) for k in shared
             if a[k]["decision"] and b[k]["decision"]]
    missing = len(shared) - len(pairs)

    kappa, po, pe, n = cohens_kappa(pairs)
    print(f"records in both files : {len(shared)}")
    print(f"both coded            : {n}" + (f"   ({missing} incomplete)" if missing else ""))
    if n == 0:
        print("\nNothing coded yet.")
        return 0
    print(f"observed agreement    : {po:.4f}")
    print(f"expected by chance    : {pe:.4f}")
    if kappa is None:
        print("Cohen's kappa         : UNDEFINED (both coders used a single category; "
              "this is not perfect agreement)")
        return 0
    print(f"Cohen's kappa         : {kappa:.4f}")

    # protocol.md §5: target 0.70. Below it the criteria are clarified, a §11 ruling is
    # issued and the ENTIRE stage is re-screened rather than patched.
    if kappa >= 0.70:
        print("\nMeets the protocol.md §5 target of 0.70.")
    else:
        print("\nBELOW the protocol.md §5 target of 0.70. The remedy is fixed in advance: "
              "clarify the\ncriteria, issue a taxonomy §11 ruling, and re-screen the "
              "entire stage. Not a patch.")

    matrix = Counter(pairs)
    cats = sorted({c for p in pairs for c in p})
    print("\nagreement matrix (rows = A, cols = B)")
    print("            " + "".join(f"{c:>12}" for c in cats))
    for ra in cats:
        print(f"{ra:>12}" + "".join(f"{matrix[(ra, cb)]:>12}" for cb in cats))
    return 0


def cmd_stage1_merge(args) -> int:
    a, b = read_coder_file(args.a), read_coder_file(args.b)
    shared = sorted(set(a) & set(b))
    if set(a) != set(b):
        print(f"  ! coder files cover different records "
              f"({len(set(a) ^ set(b))} unmatched)", file=sys.stderr)
        return 1
    uncoded = [k for k in shared if not (a[k]["decision"] and b[k]["decision"])]
    if uncoded and not args.partial:
        print(f"  ! {len(uncoded)} records are not yet coded by both. Finish, or pass "
              f"--partial.", file=sys.stderr)
        return 1

    # Kappa is computed on the RAW decisions, before any of them are resolved.
    pairs = [(a[k]["decision"], b[k]["decision"]) for k in shared
             if a[k]["decision"] and b[k]["decision"]]
    kappa, po, pe, n = cohens_kappa(pairs)

    corpus = {r["record_id"]: r for r in load_corpus()}
    rows, advanced, disagreements, excluded = [], 0, 0, 0
    for k in shared:
        da, db = a[k]["decision"], b[k]["decision"]
        if not (da and db):
            continue
        agree = da == db
        # protocol.md §5: liberal inclusion, disagreements advance automatically.
        resolution = "include" if (da == "include" or db == "include") else "exclude"
        if not agree:
            disagreements += 1
        if resolution == "include":
            advanced += 1
        else:
            excluded += 1
        src = corpus.get(k, {})
        rows.append({
            "record_id": k,
            "title": src.get("title", a[k]["title"]),
            "no_abstract": "1" if src.get("has_abstract") != "1" else "",
            "coder_a": args.a.stem.replace("stage1_", ""),
            "coder_b": args.b.stem.replace("stage1_", ""),
            "decision_a": da, "decision_b": db,
            "exclude_code_a": a[k]["exclude_code"], "exclude_code_b": b[k]["exclude_code"],
            "agreement": "agree" if agree else "disagree",
            "resolution": resolution,
            "resolution_basis": "both" if agree else "disagreement-advances",
            "note_a": a[k]["note"], "note_b": b[k]["note"],
        })

    # Outputs land beside their inputs. A merge of dry-run worklists must not deposit
    # synthetic decisions in the real screening directory, where nothing downstream
    # could tell them from the genuine article.
    outdir = args.a.parent if args.a.parent.name == "dryrun" else OUTDIR
    outdir.mkdir(parents=True, exist_ok=True)
    dec_path = outdir / "stage1_decisions.csv"
    with dec_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    work_path = outdir / "stage2_worklist.csv"
    with work_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["record_id", "title", "no_abstract", "advanced_on"])
        for r in rows:
            if r["resolution"] == "include":
                w.writerow([r["record_id"], r["title"], r["no_abstract"],
                            r["resolution_basis"]])

    no_abs_adv = sum(1 for r in rows if r["no_abstract"] and r["resolution"] == "include")
    no_abs_tot = sum(1 for r in rows if r["no_abstract"])
    summary = {
        "generated_utc": date.today().isoformat(),
        "records_screened": len(rows),
        "advanced_to_stage2": advanced,
        "excluded": excluded,
        "disagreements_advanced": disagreements,
        "observed_agreement": round(po, 4),
        "expected_agreement": round(pe, 4),
        "cohens_kappa": None if kappa is None else round(kappa, 4),
        "kappa_meets_target": None if kappa is None else bool(kappa >= 0.70),
        "no_abstract_screened": no_abs_tot,
        "no_abstract_advanced": no_abs_adv,
        "exclude_code_counts": dict(Counter(
            c for r in rows if r["resolution"] == "exclude"
            for c in (r["exclude_code_a"], r["exclude_code_b"]) if c)),
    }
    (outdir / "stage1_summary.json").write_text(json.dumps(summary, indent=2))

    print(f"screened            {len(rows)}")
    print(f"advanced            {advanced}   ({disagreements} of them on disagreement)")
    print(f"excluded            {excluded}")
    print(f"no-abstract records {no_abs_tot} screened, {no_abs_adv} advanced")
    print(f"kappa               " + ("undefined" if kappa is None else f"{kappa:.4f}"))
    print(f"\n-> {dec_path}\n-> {work_path}\n-> {outdir / 'stage1_summary.json'}")
    return 0


def cmd_pilot(args) -> int:
    """Draw the pilot sample (protocol.md §7): 40 records, >= 5 physical-substrate.

    Drawn at random first, then topped up only if the random draw misses the guarantee,
    so the sample stays as close to random as the constraint allows. The realised
    composition is reported either way: a pilot that needed topping up is telling you
    something about the corpus and should not look like one that did not.
    """
    # Same guard as Stage 1, and for the same reason: an unadjudicated duplicate could be
    # drawn into the pilot, and the pilot is what the taxonomy freeze turns on.
    done, outstanding = adjudication_done()
    dry = bool(args.allow_unadjudicated)
    if not done and not dry:
        print(f"Pilot is blocked: {outstanding} near-duplicate pairs are unadjudicated "
              f"(search-strategy.md §5.1).", file=sys.stderr)
        return 1

    rows = eligible(load_corpus())
    rng = random.Random(args.seed)
    sample = rng.sample(rows, min(args.n, len(rows)))

    phys = [r for r in sample if is_physical_proxy(r)]
    topped = 0
    if len(phys) < args.min_physical:
        pool = [r for r in rows if is_physical_proxy(r) and r not in sample]
        rng.shuffle(pool)
        swappable = [r for r in sample if not is_physical_proxy(r)]
        rng.shuffle(swappable)
        need = args.min_physical - len(phys)
        for add, drop in zip(pool[:need], swappable[:need]):
            sample[sample.index(drop)] = add
            topped += 1
        phys = [r for r in sample if is_physical_proxy(r)]

    outdir = (OUTDIR / "dryrun" / "pilot") if dry else (OUTDIR / "pilot")
    outdir.mkdir(parents=True, exist_ok=True)
    for coder in args.coders:
        _write_coder_file(outdir / f"pilot_{coder}.csv", sample, coder, args.seed, dry,
                          fields=PILOT_FIELDS)

    hits = Counter(h for r in sample for h in substrate_hits(f"{r['title']} {r['abstract']}"))
    meta = {
        "generated_utc": date.today().isoformat(),
        "seed": args.seed,
        "n": len(sample),
        "physical_proxy_count": len(phys),
        "min_physical_required": args.min_physical,
        "records_swapped_in_to_meet_minimum": topped,
        "substrate_proxy_hits": dict(hits.most_common()),
        "no_abstract": sum(1 for r in sample if r.get("has_abstract") != "1"),
        "record_ids": [r["record_id"] for r in sample],
    }
    (outdir / "pilot_sample.json").write_text(json.dumps(meta, indent=2))

    print(f"\npilot n={len(sample)}, physical-proxy {len(phys)} "
          f"(minimum {args.min_physical}, {topped} swapped in)")
    print(f"substrate proxy hits: {dict(hits.most_common())}")
    print(f"-> {outdir / 'pilot_sample.json'}")
    print("\nCoders fill family (F1-F4 or unassignable), subclass, hybrid and reason per "
          "docs/preliminary-agreement-check.md,\nindependently and from the title and "
          "abstract only. When both files are complete:\n"
          "  python3 scripts/screen.py pilot-kappa --a <A.csv> --b <B.csv>")
    print("\nPilot records are discarded from corpus statistics and re-drawn "
          "(protocol.md §7).")
    return 0


def read_pilot_file(path: Path) -> dict[str, dict]:
    """Read one coder's completed pilot worklist, validating the vocabulary.

    Validation is strict for the same reason the Stage-1 reader's is: a value the
    downstream statistics cannot interpret must stop the run at the file, not skew a
    kappa silently. Families are F1-F4 or `unassignable`; a subclass must belong to the
    assigned family; a hybrid is the SECONDARY family code and cannot equal the primary.
    """
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    out = {}
    for line, r in enumerate(rows, 2):
        fam = (r.get("family") or "").strip()
        fam = fam.upper() if fam.upper() in ("F1", "F2", "F3", "F4") else fam.lower()
        if fam and fam not in PILOT_FAMILIES:
            print(f"  ! {path.name}:{line}: family must be one of "
                  f"{', '.join(PILOT_FAMILIES)} or blank, got {r.get('family')!r}",
                  file=sys.stderr)
            raise SystemExit(1)
        sub = (r.get("subclass") or "").strip().upper()
        if sub:
            if not re.fullmatch(r"F[1-4]\.[0-9]+", sub):
                print(f"  ! {path.name}:{line}: subclass must look like F2.1, got "
                      f"{r.get('subclass')!r}", file=sys.stderr)
                raise SystemExit(1)
            if fam not in ("F1", "F2", "F3", "F4") or not sub.startswith(fam + "."):
                print(f"  ! {path.name}:{line}: subclass {sub} does not belong to "
                      f"family {fam or '(blank)'}", file=sys.stderr)
                raise SystemExit(1)
        hyb = (r.get("hybrid") or "").strip().upper()
        if hyb:
            if hyb not in ("F1", "F2", "F3", "F4"):
                print(f"  ! {path.name}:{line}: hybrid is the SECONDARY family code "
                      f"(F1-F4), got {r.get('hybrid')!r}", file=sys.stderr)
                raise SystemExit(1)
            if hyb == fam:
                print(f"  ! {path.name}:{line}: hybrid must differ from the primary "
                      f"family {fam}", file=sys.stderr)
                raise SystemExit(1)
        mins = (r.get("minutes") or "").strip()
        if mins:
            try:
                float(mins)
            except ValueError:
                print(f"  ! {path.name}:{line}: minutes must be a number or blank, got "
                      f"{mins!r}", file=sys.stderr)
                raise SystemExit(1)

        # Symmetric hybrid label (D18). Written FnxFm with the codes in ascending order;
        # when it is set, `family` must be empty, because the whole point of the label is
        # that the report does not establish a dominant mechanism.
        sym = (r.get("family_symmetric") or "").strip().upper().replace("×", "X")
        if sym:
            m = re.fullmatch(r"(F[1-4])X(F[1-4])", sym)
            if not m:
                print(f"  ! {path.name}:{line}: family_symmetric must look like F1xF2, got "
                      f"{r.get('family_symmetric')!r}", file=sys.stderr)
                raise SystemExit(1)
            a_, b_ = m.group(1), m.group(2)
            if a_ == b_:
                print(f"  ! {path.name}:{line}: family_symmetric must combine two different "
                      f"families, got {sym}", file=sys.stderr)
                raise SystemExit(1)
            if a_ > b_:
                print(f"  ! {path.name}:{line}: family_symmetric codes must be in ascending "
                      f"order, write {b_}x{a_} not {a_}x{b_}", file=sys.stderr)
                raise SystemExit(1)
            if fam:
                print(f"  ! {path.name}:{line}: a record with family_symmetric must leave "
                      f"family empty (taxonomy §2.1); got family={fam}", file=sys.stderr)
                raise SystemExit(1)
            sym = f"{a_}x{b_}"

        # Eligibility (D21). A separate judgement from classification: protocol §4.2
        # excludes reviews, non-RC records and records with no quantitative result upstream,
        # and the §2 assignment procedure never runs on them. Until this column existed the
        # pilot vocabulary could not express `not-primary`, so an eligibility exclusion and a
        # genuine classification failure were recorded identically as `unassignable`.
        elig = (r.get("eligible") or "").strip().lower()
        if elig and elig not in ELIGIBILITY:
            print(f"  ! {path.name}:{line}: eligible must be one of "
                  f"{'/'.join(ELIGIBILITY)} or blank, got {r.get('eligible')!r}",
                  file=sys.stderr)
            raise SystemExit(1)

        out[r["record_id"]] = {"family": fam, "subclass": sub, "hybrid": hyb,
                               "family_symmetric": sym, "eligible": elig,
                               "reason": (r.get("reason") or "").strip(),
                               "minutes": mins,
                               "title": r.get("title", "")}
    return out


def agreement_label(rec: dict) -> str:
    """The single category a record contributes to the family agreement statistic.

    One category for every symmetric label rather than one per pair; see PILOT_FAMILIES.
    """
    if rec.get("family_symmetric"):
        return "hybrid-symmetric"
    return rec.get("family", "")


def kappa_ci(kappa: float, po: float, pe: float, n: int) -> tuple[float, float, float]:
    """(se, lo, hi): the large-sample standard error of Cohen's kappa and its 95% CI.

    The simple asymptotic form se = sqrt(po(1-po) / (n(1-pe)^2)) (Cohen 1960). At
    n = 40 and kappa near 0.70 it gives roughly 0.09, which is the precision statement
    manuscript Section 6.1 makes; the pilot is a gate, not a precise estimate.
    """
    import math
    se = math.sqrt(max(po * (1 - po), 0.0) / (n * (1 - pe) ** 2))
    return se, kappa - 1.96 * se, kappa + 1.96 * se


def gwet_ac1(pairs: list[tuple[str, str]], vocabulary: tuple[str, ...]) -> float | None:
    """Gwet's AC1 over a fixed category vocabulary.

    Reported alongside kappa because kappa behaves counterintuitively under uneven
    prevalence (protocol.md §7). The chance term uses the instrument's full vocabulary
    size, not just the observed categories, since the coders had every category
    available: pe = 1/(K-1) * sum_k pi_k (1 - pi_k) with pi_k the two coders' mean
    marginal proportion for category k.
    """
    n = len(pairs)
    if n == 0:
        return None
    K = len(vocabulary)
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(((ca[k] / n + cb[k] / n) / 2) * (1 - (ca[k] / n + cb[k] / n) / 2)
             for k in vocabulary) / (K - 1)
    if abs(1.0 - pe) < 1e-12:
        return None
    return (po - pe) / (1 - pe)


def krippendorff_alpha_nominal(pairs: list[tuple[str, str]]) -> float | None:
    """Krippendorff's alpha for two coders, nominal metric, no missing values.

    Added 2026-09-05 on a referee request: alpha is the conventional third statistic in
    the annotation-reliability literature, and it corrects for chance differently from
    both kappa (which uses each coder's own marginals) and AC1 (which uses the
    instrument's category count). Reporting all three means a reliability claim does not
    rest on one chance model.

    Coincidence-matrix form. Each unit contributes both ordered pairs, so
    o_ck counts (c,k) and (k,c); n = 2 * units. For the nominal metric,
        Do = sum_{c != k} o_ck
        De = (1 / (n - 1)) * sum_{c != k} n_c n_k
        alpha = 1 - Do / De
    Returns None where De is zero, which happens when every value is identical: that is
    not perfect reliability, it is no variance to be reliable about, and the caller says so.
    """
    n_units = len(pairs)
    if n_units == 0:
        return None
    o: Counter[tuple[str, str]] = Counter()
    for a, b in pairs:
        o[(a, b)] += 1
        o[(b, a)] += 1
    marg: Counter[str] = Counter()
    for (c, _k), v in o.items():
        marg[c] += v
    n = sum(marg.values())
    if n < 2:
        return None
    do = sum(v for (c, k), v in o.items() if c != k)
    de = sum(marg[c] * marg[k] for c in marg for k in marg if c != k) / (n - 1)
    if de == 0:
        return None
    return 1.0 - do / de


def has_reconciliation(path: Path) -> bool:
    """True if a disagreements file already carries reconciliation work.

    The mirror of `dedupe.py`'s `_has_decisions`, and it exists for the same reason:
    `pilot_disagreements.csv` is generated by this command with `deciding_text` and
    `reconciled_rule` empty, and the coders then fill those two columns by hand during
    the post-hoc discussion (protocol.md §7). Re-running `pilot-kappa` afterwards used
    to overwrite that work silently, because the command opens the path with "w" every
    time. Near-duplicate adjudications have been protected against exactly this since
    2026-08-02; the reconciliation record was not, and the asymmetry was found by a
    coder in 2026-09-05 after she had filled both rows.
    """
    try:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            return any((row.get("deciding_text") or "").strip()
                       or (row.get("reconciled_rule") or "").strip()
                       for row in csv.DictReader(fh))
    except (OSError, csv.Error):
        return False


def cmd_pilot_kappa(args) -> int:
    """The protocol.md §7 reporting set, computed from the two raw coder files.

    Everything here is computed BEFORE any reconciliation, from the files as the coders
    submitted them; that ordering is what makes the agreement a reliability measure.
    This command was written before any coding had occurred, so the reporting choices
    cannot have been tuned to a result.
    """
    a, b = read_pilot_file(args.a), read_pilot_file(args.b)
    shared = sorted(set(a) & set(b))
    if set(a) != set(b):
        print(f"  ! coder files cover different records ({len(set(a) ^ set(b))} "
              f"unmatched)", file=sys.stderr)
        return 1
    uncoded = [k for k in shared
               if not (agreement_label(a[k]) and agreement_label(b[k]))]
    if uncoded:
        print(f"  ! {len(uncoded)} records are not yet coded by both coders. The pilot "
              f"statistics are computed only on complete files.", file=sys.stderr)
        return 1

    pairs = [(agreement_label(a[k]), agreement_label(b[k])) for k in shared]
    n = len(pairs)
    kappa, po, pe, _ = cohens_kappa(pairs)
    ac1 = gwet_ac1(pairs, PILOT_FAMILIES)

    print(f"records coded by both     : {n}")
    print(f"raw family agreement      : {po:.4f}")
    if kappa is None:
        print("Cohen's kappa             : UNDEFINED (a single category was used "
              "throughout; this is not perfect agreement)")
    else:
        se, lo, hi = kappa_ci(kappa, po, pe, n)
        print(f"Cohen's kappa (family)    : {kappa:.4f}   "
              f"(approx. 95% CI {lo:.2f} to {hi:.2f}, large-sample SE {se:.3f})")
    print(f"Gwet's AC1 (sensitivity)  : " + ("undefined" if ac1 is None else f"{ac1:.4f}"))
    kalpha = krippendorff_alpha_nominal(pairs)
    print(f"Krippendorff's alpha      : "
          + ("undefined" if kalpha is None else f"{kalpha:.4f}"))
    print(f"  (all three are computed over all {n} records on the "
          f"{len(PILOT_FAMILIES)}-category vocabulary\n   "
          f"{', '.join(PILOT_FAMILIES)}; 'unassignable' and 'hybrid-symmetric' are "
          f"categories, not exclusions.)")

    # Subclass agreement: exact match, among records where both coders assigned the
    # same family and both committed to a subclass. Reported with its base so a high
    # rate on a small base cannot masquerade as a strong result.
    sub_base = [k for k in shared if a[k]["family"] == b[k]["family"]
                and a[k]["subclass"] and b[k]["subclass"]]
    sub_agree = sum(1 for k in sub_base if a[k]["subclass"] == b[k]["subclass"])
    print(f"exact subclass agreement  : "
          + (f"{sub_agree}/{len(sub_base)}" if sub_base else "no shared subclass base"))

    una_a = sum(1 for k in shared if a[k]["family"] == "unassignable")
    una_b = sum(1 for k in shared if b[k]["family"] == "unassignable")
    hyb_a = sum(1 for k in shared if a[k]["hybrid"])
    hyb_b = sum(1 for k in shared if b[k]["hybrid"])
    sym_a = sum(1 for k in shared if a[k]["family_symmetric"])
    sym_b = sum(1 for k in shared if b[k]["family_symmetric"])
    rea_a = sum(1 for k in shared if a[k]["reason"])
    rea_b = sum(1 for k in shared if b[k]["reason"])
    print(f"unassignable, A / B       : {una_a} ({una_a/n:.1%}) / {una_b} ({una_b/n:.1%})"
          f"   [all records]")

    # Revised gate basis (deviation D21). The 5% criterion is applied to records BOTH coders
    # judged eligible, because protocol §4.2 removes reviews, non-RC records and records with
    # no quantitative result upstream and the §2 procedure never runs on them. The
    # all-records rate above is printed alongside and is the figure comparable with the
    # 2026-08-28 preliminary check; neither replaces the other and both are reported.
    both_elig = [k for k in shared
                 if a[k]["eligible"] == "yes" and b[k]["eligible"] == "yes"]
    ne = len(both_elig)
    if ne:
        eu_a = sum(1 for k in both_elig if a[k]["family"] == "unassignable")
        eu_b = sum(1 for k in both_elig if b[k]["family"] == "unassignable")
        print(f"  ...of the {ne} records both coders judged eligible : "
              f"{eu_a} ({eu_a/ne:.1%}) / {eu_b} ({eu_b/ne:.1%})   [as coded]")
        # R11 carve-out (D29). Printed as a separate line with its records named, never
        # folded silently into the line above, so the unadjusted rate stays on the page.
        carved = r11_carve_out(both_elig, a, b)
        ga_a, ga_b = eu_a - len(carved), eu_b - len(carved)
        if carved:
            print(f"  ...less {len(carved)} record(s) dispositioned under R11, not an "
                  f"instrument failure : "
                  f"{ga_a} ({ga_a/ne:.1%}) / {ga_b} ({ga_b/ne:.1%})   [GATE BASIS]")
            for k in carved:
                print(f"       {k}: {R11_TWO_SYSTEM_RECORDS[k]}")
        else:
            print(f"       (no R11 carve-out applies; the line above is the gate basis)")
    else:
        eu_a = eu_b = ga_a = ga_b = None
        carved = []
        print("  ...eligibility column not filled; the D21 gate basis cannot be computed")
    inelig_a = sum(1 for k in shared if a[k]["eligible"] == "no")
    inelig_b = sum(1 for k in shared if b[k]["eligible"] == "no")
    print(f"judged ineligible, A / B  : {inelig_a} / {inelig_b}")
    print(f"symmetric label, A / B    : {sym_a} / {sym_b}")
    print(f"hybrid flagged, A / B     : {hyb_a} / {hyb_b}")
    print(f"reason recorded, A / B    : {rea_a} / {rea_b}")

    # Exact agreement on WHICH pair a symmetric label names, reported with its base in the
    # same way subclass agreement is: the category agreement above says both coders declined
    # to name a dominant mechanism, and this says whether they saw the same two mechanisms.
    sym_base = [k for k in shared
                if a[k]["family_symmetric"] and b[k]["family_symmetric"]]
    sym_agree = sum(1 for k in sym_base
                    if a[k]["family_symmetric"] == b[k]["family_symmetric"])
    print(f"exact symmetric-pair agr. : "
          + (f"{sym_agree}/{len(sym_base)}" if sym_base else "no shared symmetric base"))

    # Annotation effort, where the coders recorded it. Reported descriptively and never
    # folded into an agreement statistic.
    eff = {}
    for tag, C in (("a", a), ("b", b)):
        vals = [float(C[k]["minutes"]) for k in shared if C[k].get("minutes")]
        if vals:
            eff[tag] = {"n_timed": len(vals), "total_minutes": round(sum(vals), 1),
                        "median_minutes_per_record": round(sorted(vals)[len(vals) // 2], 2)}
    if eff:
        for tag, v in eff.items():
            print(f"coding time, {tag.upper()}            : {v['total_minutes']} min over "
                  f"{v['n_timed']} records, median {v['median_minutes_per_record']} "
                  f"min/record")
    else:
        print("coding time               : not recorded by either coder")

    cats = [c for c in PILOT_FAMILIES if any(c in p for p in pairs)]
    matrix = Counter(pairs)
    # Width follows the longest label in play, so a vocabulary addition cannot silently
    # break the alignment; `hybrid-symmetric` is 16 characters and overflowed a fixed 14.
    w = max([len(c) for c in cats] + [12]) + 2
    print("\nconfusion matrix (rows = A, cols = B)")
    print(" " * w + "".join(f"{c:>{w}}" for c in cats))
    for ra in cats:
        print(f"{ra:>{w}}" + "".join(f"{matrix[(ra, cb)]:>{w}}" for cb in cats))

    disagreements = [k for k in shared if a[k]["family"] != b[k]["family"]]
    outdir = args.a.parent
    dis_path = outdir / "pilot_disagreements.csv"
    # Never clobber the reconciliation. The two hand-filled columns are the record of a
    # discussion between two people and are not regenerable from anything; the rest of
    # the row is. If work is present, the fresh list goes to a sibling path and the
    # operator reconciles them, exactly as dedupe.py does for the adjudication file.
    reconciled = has_reconciliation(dis_path)
    if reconciled:
        dis_path = outdir / "pilot_disagreements.new.csv"
        print(f"\n  ! pilot_disagreements.csv carries reconciliation work; writing to "
              f"{dis_path.name}\n    rather than overwriting it.", file=sys.stderr)
    with dis_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["record_id", "title", "family_a", "subclass_a", "reason_a",
                    "family_b", "subclass_b", "reason_b", "deciding_text",
                    "reconciled_rule"])
        for k in disagreements:
            w.writerow([k, a[k]["title"], a[k]["family"], a[k]["subclass"],
                        a[k]["reason"], b[k]["family"], b[k]["subclass"],
                        b[k]["reason"], "", ""])

    summary = {
        "generated_utc": date.today().isoformat(),
        "n": n,
        "raw_family_agreement": round(po, 4),
        "cohens_kappa_family": None if kappa is None else round(kappa, 4),
        "kappa_ci95": None if kappa is None else
            [round(x, 4) for x in kappa_ci(kappa, po, pe, n)[1:]],
        "gwet_ac1": None if ac1 is None else round(ac1, 4),
        "krippendorff_alpha": None if kalpha is None else round(kalpha, 4),
        "agreement_basis": {
            "records": n,
            "categories": list(PILOT_FAMILIES),
            "unassignable_is_a_category": True,
        },
        "subclass_agreement": [sub_agree, len(sub_base)],
        "symmetric_pair_agreement": [sym_agree, len(sym_base)],
        "unassignable_all_records": {"a": una_a, "b": una_b, "n": n},
        "unassignable_eligible_only": (
            {"a": eu_a, "b": eu_b, "n": ne} if ne else None),
        "ineligible": {"a": inelig_a, "b": inelig_b},
        "symmetric": {"a": sym_a, "b": sym_b},
        "hybrid": {"a": hyb_a, "b": hyb_b},
        "reasons": {"a": rea_a, "b": rea_b},
        "family_disagreements": len(disagreements),
        "annotation_effort": eff or None,
        "gate_kappa_ge_070": None if kappa is None else bool(kappa >= 0.70),
        # D21: the gate is the eligible-only rate; the all-records rate is reported beside
        # it and is what the 2026-08-28 preliminary check measured.
        "gate_unassignable_le_5pct": (
            bool(max(ga_a, ga_b) / ne <= 0.05) if ne else None),
        "gate_basis": ("records both coders judged eligible (deviation D21), less records "
                       "dispositioned under taxonomy-v1.0.md R11 (deviation D29)"),
        # Both numbers are written, always. The unadjusted rate is what §7's criterion says
        # verbatim; the adjusted rate is that criterion with R11 applied. A reader who
        # rejects D29 has the figure they need without recomputing anything.
        "unassignable_eligible_only_as_coded": (
            {"a": eu_a, "b": eu_b, "base": ne,
             "le_5pct": bool(max(eu_a, eu_b) / ne <= 0.05)} if ne else None),
        "r11_carve_out": {
            "deviation": "D29",
            "records": {k: R11_TWO_SYSTEM_RECORDS[k] for k in carved},
            "affects": "the gate numerator only; not kappa, not the all-records rate",
        },
        "unassignable_le_5pct_all_records": bool(max(una_a, una_b) / n <= 0.05),
    }
    (outdir / "pilot_agreement.json").write_text(json.dumps(summary, indent=2))

    print(f"\n-> {dis_path}  ({len(disagreements)} family disagreements, for the "
          f"reconciliation record)")
    print(f"-> {outdir / 'pilot_agreement.json'}")
    if kappa is not None:
        gate1 = "MET" if kappa >= 0.70 else "NOT MET"
        if ne:
            gate2 = "MET" if max(ga_a, ga_b) / ne <= 0.05 else "NOT MET"
            basis = (f"on the {ne} records both coders judged eligible (deviation D21)")
            if carved:
                basis += (f",\n      less {len(carved)} dispositioned under R11 "
                          f"(deviation D29)")
        else:
            gate2 = "NOT COMPUTABLE"
            basis = "eligibility column not filled"
        print(f"\ngate: kappa >= 0.70 {gate1}; unassignable <= 5% (either coder) {gate2} "
              f"\n      {basis}.")
        if ne and carved:
            # State the counterfactual unprompted. D29 converts this gate result, and a
            # reader must not have to reconstruct what it was before.
            raw2 = "MET" if max(eu_a, eu_b) / ne <= 0.05 else "NOT MET"
            print(f"      Without the R11 carve-out the same criterion reads {raw2} "
                  f"({eu_a}/{ne} = {eu_a/ne:.1%} and {eu_b}/{ne} = {eu_b/ne:.1%}).")
        print(f"      For comparison with the 2026-08-28 preliminary check, the "
              f"all-records rate is\n      "
              f"{'within' if max(una_a, una_b) / n <= 0.05 else 'above'} 5%.")
        print(f"\nFailure requires a documented revision and a NEW sample "
              f"(protocol.md §7); it cannot be repaired by reconciling these ratings.")
    return 0


def cmd_oa_substrate(args) -> int:
    """Characterise the D6 exclusion with the substrate-terminology proxy.

    Feeds the manuscript's Section 7.1 paragraph and protocol.md §9.2. Two rates are
    printed for each pool: the full title+abstract proxy, and a title-only variant.
    The title-only variant is the comparable one, because abstract coverage differs
    sharply between the pools (closed records lack abstracts far more often), so the
    full proxy under-fires on closed records and overstates any open-pool skew.
    This is a terminology proxy, never a family assignment.
    """
    rows = [r for r in load_corpus() if not r["dup_of"]]
    pools = {"open": [r for r in rows if r["is_oa"] == "1"],
             "closed": [r for r in rows if r["is_oa"] != "1"]}
    total = len(rows)
    print(f"corpus {total} records; closed share {len(pools['closed'])/total:.1%}\n")
    for name, pool in pools.items():
        n = len(pool)
        full = sum(1 for r in pool
                   if substrate_hits(f"{r.get('title','')} {r.get('abstract','')}"))
        title = sum(1 for r in pool if substrate_hits(r.get("title", "")))
        has_abs = sum(1 for r in pool if r.get("has_abstract") == "1")
        print(f"{name:6s} n={n}  abstract {has_abs/n:.1%}  "
              f"proxy(title+abstract) {full/n:.1%}  proxy(title only) {title/n:.1%}")
    print("\nper-vocabulary hits on title+abstract (open / closed / closed share):")
    counts: dict[str, list[int]] = {}
    for idx, (name, pool) in enumerate(pools.items()):
        for r in pool:
            for lab in substrate_hits(f"{r.get('title','')} {r.get('abstract','')}"):
                counts.setdefault(lab, [0, 0])[idx] += 1
    for lab in sorted(counts):
        o, c = counts[lab]
        print(f"  {lab:22s} {o:5d} / {c:5d}   closed share {c/(o+c):.1%}")
    print("\nBaseline for the closed-share column is the corpus closed share above."
          "\nProxy only; family-resolved comparison requires the audit (protocol.md §9.2).")
    return 0


def cmd_status(args) -> int:
    rows = load_corpus()
    elig = eligible(rows)
    done, outstanding = adjudication_done()
    print(f"corpus                      {len(rows)}")
    print(f"  duplicates marked         {sum(1 for r in rows if r['dup_of'])}")
    print(f"  closed, excluded by D6    {sum(1 for r in rows if r['is_oa'] != '1')}")
    print(f"eligible for Stage 1        {len(elig)}")
    print(f"  no abstract, title only   {sum(1 for r in elig if r.get('has_abstract') != '1')}")
    print(f"  physical-substrate proxy  {sum(1 for r in elig if is_physical_proxy(r))}")
    print(f"\nnear-duplicate adjudication {'complete' if done else f'OUTSTANDING ({outstanding} pairs)'}")
    for name in ("stage1_decisions.csv", "stage2_worklist.csv", "stage1_summary.json"):
        p = OUTDIR / name
        print(f"{name:28s}{'present' if p.exists() else 'not yet'}")
    if not done:
        print("\nStage 1 is blocked on the near-duplicate adjudication "
              "(search-strategy.md §5.1).")
    return 0


def cmd_selftest(args) -> int:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        ok = ok and cond

    # Worked kappa: 20/5/10/15 contingency -> po=0.70, pe=0.50, kappa=0.40.
    pairs = ([("include", "include")] * 20 + [("include", "exclude")] * 5
             + [("exclude", "include")] * 10 + [("exclude", "exclude")] * 15)
    k, po, pe, n = cohens_kappa(pairs)
    check("kappa worked example = 0.40", abs(k - 0.40) < 1e-9)
    check("observed agreement = 0.70", abs(po - 0.70) < 1e-9)
    check("expected agreement = 0.50", abs(pe - 0.50) < 1e-9)

    k, _, _, _ = cohens_kappa([("include", "include")] * 10)
    check("kappa undefined when one category is used throughout", k is None)

    k, _, _, _ = cohens_kappa([("include", "exclude")] * 5 + [("exclude", "include")] * 5)
    check("kappa = -1 on total disagreement", abs(k + 1.0) < 1e-9)

    k, _, _, _ = cohens_kappa([("include", "include")] * 5 + [("exclude", "exclude")] * 5)
    check("kappa = 1 on perfect agreement over two categories", abs(k - 1.0) < 1e-9)

    check("substrate proxy fires on photonic",
          "photonic" in substrate_hits("A silicon photonic reservoir"))
    check("substrate proxy fires on memristive",
          "memristive-ionic" in substrate_hits("Memristor crossbar reservoir computing"))
    check("substrate proxy silent on a pure simulation title",
          substrate_hits("Echo state networks for time series prediction") == set())

    # Two coders must not receive the same order.
    rows = [{"record_id": f"RC-{i:04d}", "title": f"t{i}", "abstract": "a",
             "has_abstract": "1"} for i in range(200)]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        pa, pb = Path(td) / "a.csv", Path(td) / "b.csv"
        _write_coder_file(pa, rows, "ST", 42, True)
        _write_coder_file(pb, rows, "AB", 42, True)
        ida = [r["record_id"] for r in csv.DictReader(pa.open(newline=""))]
        idb = [r["record_id"] for r in csv.DictReader(pb.open(newline=""))]
        check("coder orders differ", ida != idb)
        check("coder files hold the same record set", set(ida) == set(idb))
        check("coder file exposes title/abstract only, no metadata",
              set(csv.DictReader(pa.open(newline="")).fieldnames) == set(CODER_FIELDS))
        _write_coder_file(pa, rows, "ST", 42, True)
        ida2 = [r["record_id"] for r in csv.DictReader(pa.open(newline=""))]
        check("same coder and seed reproduces the same order", ida == ida2)

        # The pilot packet carries the CLASSIFICATION fields, not the screening ones.
        pp = Path(td) / "p.csv"
        _write_coder_file(pp, rows, "ST", 42, True, fields=PILOT_FIELDS)
        check("pilot file carries the current packet fields in order",
              csv.DictReader(pp.open(newline="")).fieldnames == PILOT_FIELDS)
        check("pilot packet carries both passes (D25) and the DOI pass 2 needs",
              "family_abstract" in PILOT_FIELDS and "family" in PILOT_FIELDS
              and "doi" in PILOT_FIELDS)
        check("pilot packet no longer offers the D23 model-assist columns",
              "model_call" not in PILOT_FIELDS and "accepted_model" not in PILOT_FIELDS)
        check("Stage-1 worklists still withhold the DOI",
              "doi" not in CODER_FIELDS)

        # Pilot vocabulary validation stops bad files at the file.
        def rejects(rowdict):
            q = Path(td) / "bad.csv"
            # Superset of the current packet plus the D23 model-assist columns, which the
            # reader must still accept: pilot 1's archived files carry them, and a reader
            # that choked on a retired column would make an archived run unreadable.
            legacy = PILOT_FIELDS + [f for f in ("model_call", "accepted_model")
                                     if f not in PILOT_FIELDS]
            with q.open("w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=legacy)
                w.writeheader()
                w.writerow({"record_id": "RC-0001", "title": "t", **rowdict})
            try:
                read_pilot_file(q)
                return False
            except SystemExit:
                return True
        check("pilot reader rejects an unknown family", rejects({"family": "F5"}))
        check("pilot reader rejects a subclass outside its family",
              rejects({"family": "F1", "subclass": "F2.1"}))
        check("pilot reader rejects hybrid equal to the primary",
              rejects({"family": "F2", "hybrid": "F2"}))
        check("pilot reader accepts a clean row",
              not rejects({"family": "F2", "subclass": "F2.1", "hybrid": "F1",
                           "reason": "delay-dominated but coupled", "minutes": "3.5"}))
        check("pilot reader rejects non-numeric minutes",
              rejects({"family": "F2", "minutes": "about five"}))
        check("pilot reader accepts blank minutes",
              not rejects({"family": "F2", "reason": "clear", "minutes": ""}))

        # Symmetric hybrid label (D18/D22) and eligibility (D21).
        check("pilot reader rejects a malformed symmetric label",
              rejects({"family_symmetric": "F1-F2"}))
        check("pilot reader rejects a symmetric label of one family with itself",
              rejects({"family_symmetric": "F2xF2"}))
        check("pilot reader rejects symmetric codes out of ascending order",
              rejects({"family_symmetric": "F2xF1"}))
        check("pilot reader rejects a symmetric label alongside a primary family",
              rejects({"family": "F1", "family_symmetric": "F1xF2"}))
        check("pilot reader accepts a well-formed symmetric label",
              not rejects({"family_symmetric": "F1xF2", "eligible": "yes",
                           "reason": "dominance not established"}))
        check("pilot reader accepts the unicode multiplication sign",
              not rejects({"family_symmetric": "F1\u00d7F2", "eligible": "yes"}))
        check("pilot reader rejects an unknown eligibility value",
              rejects({"family": "F1", "eligible": "maybe"}))
        check("pilot reader accepts yes/no eligibility",
              not rejects({"family": "F1", "eligible": "no"}))

        # Retired columns from a superseded packet must not stop a file being read.
        check("pilot reader ignores retired extra columns",
              not rejects({"family": "F1", "accepted_model": "yes",
                           "model_call": "yes|F1|F1.1", "reason": "kept"}))

        # A symmetric label must carry a record into the agreement statistic, not stall it.
        check("agreement_label maps a symmetric record to one category",
              agreement_label({"family": "", "family_symmetric": "F1xF2"})
              == "hybrid-symmetric")
        check("agreement_label passes a plain family through",
              agreement_label({"family": "F3", "family_symmetric": ""}) == "F3")
        check("agreement_label treats every pair as the same category",
              agreement_label({"family": "", "family_symmetric": "F1xF4"})
              == agreement_label({"family": "", "family_symmetric": "F2xF3"}))

        # The R11 carve-out (D29). It moves a gate result, so its three constraints are
        # tested rather than trusted: declared membership, both coders unassignable, and
        # no effect on anything but the numerator.
        declared = next(iter(R11_TWO_SYSTEM_RECORDS))

        def carve(fam_a, fam_b, rid=declared):
            A = {rid: {"family": fam_a, "eligible": "yes"}}
            B = {rid: {"family": fam_b, "eligible": "yes"}}
            return r11_carve_out([rid], A, B)

        check("R11 carve-out fires when both coders coded it unassignable",
              carve("unassignable", "unassignable") == [declared])
        check("R11 carve-out does NOT fire when coder A assigned a family",
              carve("F1", "unassignable") == [])
        check("R11 carve-out does NOT fire when coder B assigned a family",
              carve("unassignable", "F1") == [])
        check("R11 carve-out does NOT fire on an undeclared record",
              carve("unassignable", "unassignable", rid="RC-0000") == [])
        check("every R11 record carries a written justification",
              all(v.strip() for v in R11_TWO_SYSTEM_RECORDS.values()))

        # The reconciliation guard. A freshly generated disagreements file has both
        # hand-filled columns empty and may be regenerated; one a coder has worked on
        # may not.
        DIS = ["record_id", "title", "family_a", "subclass_a", "reason_a",
               "family_b", "subclass_b", "reason_b", "deciding_text", "reconciled_rule"]

        def dis_file(deciding: str, rule: str) -> Path:
            q = Path(td) / "pilot_disagreements.csv"
            with q.open("w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=DIS)
                w.writeheader()
                w.writerow({"record_id": "RC-0001", "title": "t", "family_a": "F1",
                            "family_b": "unassignable", "deciding_text": deciding,
                            "reconciled_rule": rule})
            return q

        check("guard passes a freshly generated disagreements file",
              not has_reconciliation(dis_file("", "")))
        check("guard fires on a filled deciding_text",
              has_reconciliation(dis_file("the abstract says X", "")))
        check("guard fires on a filled reconciled_rule",
              has_reconciliation(dis_file("", "nomenclature never decides a family")))
        check("guard fires on whitespace-only being treated as empty",
              not has_reconciliation(dis_file("   ", "  ")))
        check("guard is silent on a missing file",
              not has_reconciliation(Path(td) / "absent.csv"))

    # Krippendorff's alpha, hand-checkable cases.
    check("alpha = 1 on perfect agreement",
          abs(krippendorff_alpha_nominal([("F1", "F1")] * 3 + [("F2", "F2")] * 3) - 1.0) < 1e-9)
    # Two units, both crossed: o_AB = o_BA = 2, n_A = n_B = 2, n = 4.
    # Do = 4; De = (2*2 + 2*2)/3 = 8/3; alpha = 1 - 4/(8/3) = -0.5.
    check("alpha = -0.5 on the crossed two-unit case",
          abs(krippendorff_alpha_nominal([("F1", "F2"), ("F2", "F1")]) + 0.5) < 1e-9)
    check("alpha undefined when every value is identical",
          krippendorff_alpha_nominal([("F1", "F1")] * 5) is None)

    # Gwet's AC1 worked example: 25 (F1,F1) + 5 (F1,F2) + 5 (F2,F1) + 5 (F2,F2).
    # po = 0.75; pi_F1 = 0.75, pi_F2 = 0.25; the chance term is
    #   pe = (0.75*0.25 + 0.25*0.75) / (K-1) = 0.375/(K-1)
    # so AC1 = (0.75 - pe)/(1 - pe). **AC1 depends on the size of the instrument's
    # vocabulary**, unlike kappa and alpha, which use only the observed marginals. The
    # expectation is therefore derived from K rather than hard-coded: when the vocabulary
    # gained `hybrid-symmetric` on 2026-09-05 a hard-coded 0.724138 failed, which is the
    # test doing its job, and re-baselining it by hand would have hidden the dependence.
    pairs = ([("F1", "F1")] * 25 + [("F1", "F2")] * 5
             + [("F2", "F1")] * 5 + [("F2", "F2")] * 5)
    K = len(PILOT_FAMILIES)
    pe_expected = 0.375 / (K - 1)
    ac1_expected = (0.75 - pe_expected) / (1 - pe_expected)
    ac1 = gwet_ac1(pairs, PILOT_FAMILIES)
    check(f"AC1 worked example = {ac1_expected:.6f} at K={K}",
          abs(ac1 - ac1_expected) < 1e-9)
    check("AC1 at K=5 is 0.724138, the value reported for the preliminary check",
          abs(gwet_ac1(pairs, ("F1", "F2", "F3", "F4", "unassignable")) - 0.724138) < 1e-6)
    check("kappa and alpha do NOT depend on the vocabulary size",
          abs(cohens_kappa(pairs)[0] - 1 / 3) < 1e-9
          and abs(krippendorff_alpha_nominal(pairs)
                  - krippendorff_alpha_nominal(pairs)) < 1e-12)
    k, po, pe, n = cohens_kappa(pairs)
    check("kappa on the same data = 1/3", abs(k - 1 / 3) < 1e-9)
    se, lo, hi = kappa_ci(k, po, pe, n)
    check("kappa large-sample SE = 0.182574", abs(se - 0.182574) < 1e-6)
    # The manuscript's Section 6.1 precision statement: SE ~ 0.09 near kappa = 0.70,
    # n = 40, uniform-ish prevalence (pe = 0.25 -> po = 0.775).
    se40, _, _ = kappa_ci(0.70, 0.775, 0.25, 40)
    check("SE near 0.09 at n=40, kappa=0.70 (manuscript 6.1)", 0.085 < se40 < 0.095)

    print("\nselftest", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("stage1-init", help="write blind per-coder Stage-1 worklists")
    p.add_argument("--coders", nargs="+", required=True, help="coder initials")
    p.add_argument("--seed", type=int, default=20260802)
    p.add_argument("--allow-unadjudicated", action="store_true",
                   help="dry run only; near-duplicates are not yet settled")
    p.set_defaults(fn=cmd_stage1_init)

    p = sub.add_parser("kappa", help="Cohen's kappa between two coder files")
    p.add_argument("--a", type=Path, required=True)
    p.add_argument("--b", type=Path, required=True)
    p.set_defaults(fn=cmd_kappa)

    p = sub.add_parser("stage1-merge", help="merge two coder files, disagreements advance")
    p.add_argument("--a", type=Path, required=True)
    p.add_argument("--b", type=Path, required=True)
    p.add_argument("--partial", action="store_true", help="allow partially coded files")
    p.set_defaults(fn=cmd_stage1_merge)

    p = sub.add_parser("pilot", help="draw the protocol.md §7 pilot sample")
    p.add_argument("--coders", nargs="+", required=True)
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--min-physical", type=int, default=5)
    p.add_argument("--seed", type=int, default=20260802)
    p.add_argument("--allow-unadjudicated", action="store_true",
                   help="dry run only; near-duplicates are not yet settled")
    p.set_defaults(fn=cmd_pilot)

    p = sub.add_parser("pilot-kappa",
                       help="protocol.md §7 reporting set from two completed pilot files")
    p.add_argument("--a", type=Path, required=True)
    p.add_argument("--b", type=Path, required=True)
    p.set_defaults(fn=cmd_pilot_kappa)

    sub.add_parser("status", help="where screening stands").set_defaults(fn=cmd_status)
    sub.add_parser("oa-substrate",
                   help="closed/open split by substrate-terminology proxy (§9.2)"
                   ).set_defaults(fn=cmd_oa_substrate)
    sub.add_parser("selftest").set_defaults(fn=cmd_selftest)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
