#!/usr/bin/env python3
"""Pre-specified analyses A1-A5 plus descriptives for the RC audit.

Implements docs/protocol.md §9 against the schema in docs/codebook.md.
Standard library only.

    python3 scripts/analyses.py all --extraction data/extraction --out runs/analysis
    python3 scripts/analyses.py a1  --extraction data/extraction
    python3 scripts/analyses.py selftest

WHY THIS EXISTS BEFORE THE DATA DOES
------------------------------------
These analyses are pre-registered. Writing the code before the extraction data exists
means the operational choices (which records enter A1, how a matched pair is defined,
how dispersion is computed) are fixed independently of what the results turn out to be.
Writing analysis code after seeing data invites unconscious tuning toward a preferred
answer. If any function here changes after extraction begins, that is a protocol
deviation and belongs in docs/deviations.md.

Every analysis reports its own exclusions. Silent truncation is the failure mode this
project studies; reproducing it here would be indefensible.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

# --- facet groupings for A1 -------------------------------------------------
# digital-hardware (an FPGA/ASIC *as* the reservoir) is deliberately in neither
# group: it is a digital computation running on dedicated silicon, so it is not a
# clean instance of either "simulated" or "physical substrate dynamics". It is
# excluded from A1 and the exclusion is reported rather than resolved by fiat.
SIM_SUBSTRATES = {"digital-simulated"}
PHYS_SUBSTRATES = {
    "analog-electronic", "photonic", "spintronic-magnetic", "memristive-ionic",
    "mechanical-soft", "biological-organic", "quantum",
}

BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 20260731  # fixed so CIs are reproducible

REPRO_CODES = ["R0", "R1", "R2", "R3", "R4"]
LANG_CODES = ["L0", "L1", "L2", "L3", "L4", "L5"]
EVID_CODES = ["E0", "E1", "E2", "E3", "E4", "E5"]


# --- io ---------------------------------------------------------------------

def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def truthy(v: str | None) -> bool:
    return str(v or "").strip().lower() in {"true", "1", "yes", "y"}


def num(v: str | None) -> float | None:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def rank(code: str, scale: list[str]) -> int | None:
    c = (code or "").strip().upper()
    return scale.index(c) if c in scale else None


# --- statistics -------------------------------------------------------------

def bootstrap_ci(vals: list[float], conf: float = 0.95) -> tuple[float, float] | None:
    """Percentile bootstrap CI of the mean. None when n < 3 (a CI from two
    points would imply a precision the data does not have)."""
    if len(vals) < 3:
        return None
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(vals)
    means = []
    for _ in range(BOOTSTRAP_N):
        means.append(sum(rng.choice(vals) for _ in range(n)) / n)
    means.sort()
    lo = means[int((1 - conf) / 2 * BOOTSTRAP_N)]
    hi = means[int((1 + conf) / 2 * BOOTSTRAP_N) - 1]
    return lo, hi


def summarize(vals: list[float]) -> dict:
    if not vals:
        return {"n": 0}
    out = {
        "n": len(vals),
        "mean": st.mean(vals),
        "median": st.median(vals),
        "min": min(vals),
        "max": max(vals),
        "sd": st.stdev(vals) if len(vals) > 1 else None,
    }
    ci = bootstrap_ci(vals)
    if ci:
        out["ci95"] = list(ci)
    return out


# --- A1: matched-pair simulated vs physical ---------------------------------

def a1(records: list[dict], benches: list[dict]) -> dict:
    """Pair records sharing (subclass, benchmark, metric) but differing in
    substrate group. This analysis is impossible under a substrate-first
    taxonomy: the pairing key requires an architecture field to sort on.
    """
    by_id = {r["record_id"]: r for r in records}
    groups: dict[tuple, dict[str, list]] = defaultdict(lambda: {"sim": [], "phys": []})
    skipped = Counter()

    for b in benches:
        rec = by_id.get(b.get("record_id", ""))
        if rec is None:
            skipped["no-parent-record"] += 1
            continue
        v = num(b.get("value"))
        if v is None:
            skipped["no-value"] += 1
            continue
        if not truthy(b.get("metric_defined")):
            # An undefined normalisation makes a value non-comparable
            # (codebook.md §8). Excluding is correct; assuming is not.
            skipped["metric-undefined"] += 1
            continue
        sub = rec.get("d1_substrate", "")
        if sub in SIM_SUBSTRATES:
            side = "sim"
        elif sub in PHYS_SUBSTRATES:
            side = "phys"
        else:
            skipped[f"substrate-not-grouped:{sub or 'blank'}"] += 1
            continue
        key = (rec.get("subclass", ""), b.get("benchmark", ""), b.get("metric", ""))
        groups[key][side].append((rec["record_id"], v))

    pairs = []
    for key, sides in sorted(groups.items()):
        if not sides["sim"] or not sides["phys"]:
            continue
        sim_vals = [v for _, v in sides["sim"]]
        phys_vals = [v for _, v in sides["phys"]]
        sim_m, phys_m = st.median(sim_vals), st.median(phys_vals)
        pairs.append({
            "subclass": key[0], "benchmark": key[1], "metric": key[2],
            "n_sim": len(sim_vals), "n_phys": len(phys_vals),
            "sim_median": sim_m, "phys_median": phys_m,
            "abs_diff": phys_m - sim_m,
            "rel_diff": (phys_m - sim_m) / sim_m if sim_m else None,
        })

    rels = [p["rel_diff"] for p in pairs if p["rel_diff"] is not None]
    return {
        "analysis": "A1 matched-pair simulated vs physical",
        "n_matched_cells": len(pairs),
        "pairs": pairs,
        "relative_difference": summarize(rels),
        "excluded": dict(skipped),
        "note": (
            "Compares REPORTED values across substrates. It is not a re-execution "
            "of either side. See limitations_and_framing.md §3."
        ),
    }


# --- A2: efficiency re-normalised to B3 -------------------------------------

def a2(records: list[dict]) -> dict:
    claims = [r for r in records if truthy(r.get("eff_claim_present"))]
    boundary = Counter(r.get("eff_boundary", "unset") or "unset" for r in claims)
    stated = sum(1 for r in claims if truthy(r.get("eff_boundary_stated")))
    renormable = [r for r in claims if truthy(r.get("eff_renorm_possible"))]
    return {
        "analysis": "A2 efficiency boundary and re-normalisation",
        "n_claims": len(claims),
        "boundary_distribution": dict(boundary),
        "n_boundary_explicitly_stated": stated,
        "frac_boundary_explicitly_stated": (stated / len(claims)) if claims else None,
        "n_renormalisable_to_b3": len(renormable),
        "n_excluded_cannot_renormalise": len(claims) - len(renormable),
        "note": (
            "Re-normalised values are computed per record with published assumptions "
            "and are not produced by this script. Records that cannot be re-normalised "
            "from the paper alone are EXCLUDED, never estimated."
        ),
    }


# --- A3: rhetoric vs evidence ----------------------------------------------

def a3(records: list[dict]) -> dict:
    deltas, cross, skipped = [], Counter(), Counter()
    for r in records:
        li = rank(r.get("lang_max_claim", ""), LANG_CODES)
        ei = rank(r.get("d6_evidence", ""), EVID_CODES)
        if li is None or ei is None:
            skipped["missing-lang-or-evidence"] += 1
            continue
        deltas.append(float(li - ei))
        cross[(r["lang_max_claim"].upper(), r["d6_evidence"].upper())] += 1

    over = sum(1 for d in deltas if d > 0)
    under = sum(1 for d in deltas if d < 0)
    return {
        "analysis": "A3 abstract language vs coded evidence tier",
        "n": len(deltas),
        "delta": summarize(deltas),
        "n_claim_exceeds_evidence": over,
        "n_evidence_exceeds_claim": under,
        "n_aligned": len(deltas) - over - under,
        "contingency": {f"{k[0]}|{k[1]}": v for k, v in sorted(cross.items())},
        "excluded": dict(skipped),
        "note": (
            "Language coded BLIND to evidence tier (protocol.md §9.1). Both "
            "directions reported: understatement is as informative as overstatement."
        ),
    }


# --- A4: benchmark discrimination ------------------------------------------

def a4(benches: list[dict]) -> dict:
    per: dict[str, Counter] = defaultdict(Counter)
    for b in benches:
        name = b.get("benchmark", "") or "unspecified"
        flag = (b.get("below_discrimination", "") or "").strip().lower()
        if flag in {"true", "1", "yes"}:
            per[name]["below"] += 1
        elif flag in {"false", "0", "no"}:
            per[name]["within"] += 1
        else:
            per[name]["excluded_no_threshold"] += 1
        if not truthy(b.get("benchmark_params_stated")):
            per[name]["params_not_stated"] += 1
        if not truthy(b.get("metric_defined")):
            per[name]["metric_undefined"] += 1

    out = {}
    for name, c in sorted(per.items()):
        scored = c["below"] + c["within"]
        out[name] = {
            "n_total": scored + c["excluded_no_threshold"],
            "n_scored": scored,
            "n_below_discrimination": c["below"],
            "frac_below": (c["below"] / scored) if scored else None,
            "n_excluded_no_threshold": c["excluded_no_threshold"],
            "n_params_not_stated": c["params_not_stated"],
            "n_metric_undefined": c["metric_undefined"],
        }
    return {
        "analysis": "A4 benchmark discrimination",
        "per_benchmark": out,
        "note": (
            "Thresholds fixed in docs/benchmark-thresholds.md BEFORE extraction. "
            "Benchmarks without a defensible anchor are excluded and the exclusion "
            "is reported rather than papered over with an invented threshold."
        ),
    }


# --- A5: reproduction outcomes ---------------------------------------------

def a5(repro: list[dict]) -> dict:
    outcomes = Counter()
    causes = Counter()
    by_stratum: dict[str, Counter] = defaultdict(Counter)
    hours, cap_hits = [], 0

    for r in repro:
        o = (r.get("repro_outcome", "") or "").strip().upper()
        if o not in REPRO_CODES:
            outcomes["unscored"] += 1
            continue
        outcomes[o] += 1
        by_stratum[r.get("repro_stratum", "") or "unspecified"][o] += 1
        if o in {"R0", "R1"}:
            causes[r.get("repro_failure_cause", "") or "unrecorded"] += 1
        h = num(r.get("repro_hours"))
        if h is not None:
            hours.append(h)
        if truthy(r.get("repro_cap_hit")):
            cap_hits += 1

    scored = sum(outcomes[c] for c in REPRO_CODES)
    reproduced = outcomes["R2"] + outcomes["R3"] + outcomes["R4"]
    return {
        "analysis": "A5 reproduction outcomes",
        "n_attempted": scored,
        "outcomes": {c: outcomes[c] for c in REPRO_CODES},
        "n_reproduced_any": reproduced,
        "frac_reproduced_any": (reproduced / scored) if scored else None,
        "frac_quantitative_or_better": (
            (outcomes["R3"] + outcomes["R4"]) / scored if scored else None
        ),
        "failure_causes": dict(causes),
        "by_stratum": {k: dict(v) for k, v in sorted(by_stratum.items())},
        "effort_hours": summarize(hours),
        "n_hit_effort_cap": cap_hits,
        "note": (
            "R0/R1 measure REPORTING SUFFICIENCY, not correctness. A correct result "
            "can be irreproducible from its write-up."
        ),
    }


# --- A6: architecture-vs-substrate association ------------------------------
#
# Pre-specified 2026-09-05, before any classification data exists, in response to a
# referee request repeated across three review rounds. The manuscript's central claim is
# that architecture is related to but not reducible to substrate. Stated that way it is
# testable, and the ">= 3 substrates per family" heuristic of the falsification tests is a
# weak form of the test: it detects a family confined to one material but says nothing
# about the strength of the association in between.
#
# The decision rule is fixed here, before the data, so it cannot be tuned to an outcome:
#   * "reducible to substrate" is rejected when the bias-corrected Cramer's V is below
#     0.70 AND the normalized mutual information is below 0.70. Both are scaled to [0, 1]
#     and equal 1 only when substrate determines family exactly.
#   * "unrelated to substrate" is rejected when V_corrected exceeds 0.20.
#   * Between those, the association is reported as intermediate, which is what the
#     manuscript predicts and what a null result would also look like: the test is
#     therefore reported with its cell counts, never as a bare coefficient.
# A contingency table with any expected cell count below 5 is reported as underpowered and
# the coefficients are labelled accordingly rather than withheld.

MIN_EXPECTED_CELL = 5.0
A6_REDUCIBLE_V = 0.70
A6_REDUCIBLE_NMI = 0.70
A6_UNRELATED_V = 0.20


def _entropy(counts: list[float]) -> float:
    total = sum(counts)
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log(p)
    return h


def cramers_v(table: dict[tuple[str, str], int]) -> dict:
    """Cramer's V with the Bergsma (2013) bias correction, plus chi-square and n.

    V = sqrt((chi2 / n) / (min(r, c) - 1)). The correction matters here because the
    expected corpus has many substrate levels and few family levels, which inflates the
    uncorrected coefficient at small n.
    """
    rows = sorted({r for r, _ in table})
    cols = sorted({c for _, c in table})
    n = sum(table.values())
    if n == 0 or len(rows) < 2 or len(cols) < 2:
        return {"n": n, "cramers_v": None, "cramers_v_corrected": None,
                "chi2": None, "underpowered": True,
                "note": "fewer than two levels on an axis; V undefined"}
    rt = {r: sum(v for (a, _b), v in table.items() if a == r) for r in rows}
    ct = {c: sum(v for (_a, b), v in table.items() if b == c) for c in cols}
    chi2 = 0.0
    small = 0
    for r in rows:
        for c in cols:
            exp = rt[r] * ct[c] / n
            if exp < MIN_EXPECTED_CELL:
                small += 1
            if exp > 0:
                chi2 += (table.get((r, c), 0) - exp) ** 2 / exp
    phi2 = chi2 / n
    k = min(len(rows), len(cols))
    v = math.sqrt(phi2 / (k - 1))
    r_, c_ = len(rows), len(cols)
    phi2c = max(0.0, phi2 - (r_ - 1) * (c_ - 1) / (n - 1)) if n > 1 else 0.0
    rc = r_ - (r_ - 1) ** 2 / (n - 1) if n > 1 else r_
    cc = c_ - (c_ - 1) ** 2 / (n - 1) if n > 1 else c_
    kc = min(rc, cc)
    vc = math.sqrt(phi2c / (kc - 1)) if kc > 1 else None
    return {"n": n, "rows": r_, "cols": c_, "chi2": chi2,
            "cramers_v": v, "cramers_v_corrected": vc,
            "cells_with_expected_below_5": small,
            "underpowered": small > 0}


def a6(records: list[dict]) -> dict:
    """Architecture family against substrate: association, not identity."""
    table: Counter = Counter()
    skipped = Counter()
    for r in records:
        fam, sub = (r.get("family") or "").strip(), (r.get("d1_substrate") or "").strip()
        if not fam or not sub:
            skipped["missing-family-or-substrate"] += 1
            continue
        table[(fam, sub)] += 1
    assoc = cramers_v(table)

    fams = sorted({f for f, _ in table})
    subs = sorted({s for _, s in table})
    n = sum(table.values())
    h_fam = _entropy([sum(v for (f, _s), v in table.items() if f == fa) for fa in fams])
    h_sub = _entropy([sum(v for (_f, s), v in table.items() if s == su) for su in subs])
    h_joint = _entropy(list(table.values()))
    mi = h_fam + h_sub - h_joint
    nmi = (2 * mi / (h_fam + h_sub)) if (h_fam + h_sub) > 0 else None

    verdict = "not computed"
    vc = assoc.get("cramers_v_corrected")
    if vc is not None and nmi is not None:
        if vc >= A6_REDUCIBLE_V and nmi >= A6_REDUCIBLE_NMI:
            verdict = "architecture is close to reducible to substrate in this corpus"
        elif vc <= A6_UNRELATED_V:
            verdict = "architecture is close to independent of substrate in this corpus"
        else:
            verdict = "intermediate: related to but not reducible to substrate"

    return {
        "analysis": "A6 architecture-substrate association",
        "contingency": {f"{k[0]}|{k[1]}": v for k, v in sorted(table.items())},
        "association": assoc,
        "entropy_nats": {"family": h_fam, "substrate": h_sub, "joint": h_joint},
        "mutual_information_nats": mi,
        "normalized_mutual_information": nmi,
        "conditional_entropy_family_given_substrate": h_joint - h_sub,
        "conditional_entropy_substrate_given_family": h_joint - h_fam,
        "substrates_per_family": {
            fa: sorted({s for (f, s) in table if f == fa}) for fa in fams
        },
        "n_substrates_per_family": {
            fa: len({s for (f, s) in table if f == fa}) for fa in fams
        },
        "verdict": verdict,
        "decision_rule": {
            "reducible_if": f"V_corrected >= {A6_REDUCIBLE_V} and NMI >= {A6_REDUCIBLE_NMI}",
            "unrelated_if": f"V_corrected <= {A6_UNRELATED_V}",
            "fixed": "2026-09-05, before any classification data existed",
        },
        "excluded": dict(skipped),
        "note": (
            "NMI uses the arithmetic-mean normalisation, 2I/(H(X)+H(Y)). Coefficients are "
            "reported with the contingency table and the underpowered flag; a coefficient "
            "quoted without its cell counts is not interpretable at this corpus size."
        ),
    }


# --- A7: reported state count against effective state dimension -------------
#
# Pre-specified 2026-09-05. Section 2.2 argues that a reported count of 400 need not be
# 400 independent state variables. That argument is currently theoretical; this analysis
# is where it becomes measurable, for the subset of records that report enough to compute
# or quote an effective dimension. Records that do not are counted, not estimated: the
# share of the corpus for which the question cannot be answered is itself the finding.


def participation_ratio(eigenvalues: list[float]) -> float | None:
    """D_PR = (sum lambda)^2 / sum lambda^2, the standard participation ratio.

    Equals the number of eigenvalues when all are equal, and tends to 1 when one
    dominates, so it estimates how many directions of the state covariance actually
    carry variance. Negative eigenvalues are a numerical artefact of a covariance
    estimate and are clipped at zero; an all-zero spectrum returns None.
    """
    lam = [max(0.0, float(x)) for x in eigenvalues]
    s1 = sum(lam)
    s2 = sum(x * x for x in lam)
    if s1 <= 0 or s2 <= 0:
        return None
    return (s1 * s1) / s2


def a7(records: list[dict]) -> dict:
    """Reported state dimension against effective state dimension, by family."""
    rows, skipped = [], Counter()
    for r in records:
        nominal = num(r.get("state_dim"))
        eff = num(r.get("eff_dim_value"))
        if nominal is None:
            skipped["no-reported-state-dim"] += 1
            continue
        if eff is None:
            skipped["no-effective-dimension-reported"] += 1
            continue
        if nominal <= 0:
            skipped["non-positive-state-dim"] += 1
            continue
        rows.append({
            "record_id": r.get("record_id", ""),
            "family": r.get("family", ""),
            "state_dim_kind": r.get("state_dim_kind", ""),
            "nominal": nominal,
            "effective": eff,
            "method": r.get("eff_dim_method", "not-stated"),
            "ratio": eff / nominal,
        })
    by_family: dict[str, list[float]] = defaultdict(list)
    by_kind: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_family[row["family"] or "unassigned"].append(row["ratio"])
        by_kind[row["state_dim_kind"] or "unstated"].append(row["ratio"])
    return {
        "analysis": "A7 reported against effective state dimension",
        "n_with_both": len(rows),
        "records": rows,
        "ratio_overall": summarize([r["ratio"] for r in rows]),
        "ratio_by_family": {k: summarize(v) for k, v in sorted(by_family.items())},
        "ratio_by_state_dim_kind": {k: summarize(v) for k, v in sorted(by_kind.items())},
        "methods_used": dict(Counter(r["method"] for r in rows)),
        "excluded": dict(skipped),
        "note": (
            "The ratio is effective / reported. A value near 1 means the reported count "
            "approximates the independent state dimension; a value well below 1 means it "
            "does not. Effective dimensions are taken as reported or computed from a "
            "reported spectrum with participation_ratio(); none is estimated where the "
            "source does not supply one, and that exclusion count is part of the result."
        ),
    }


# --- descriptives -----------------------------------------------------------

SPEC_PREFIXES = ("spec_", "proto_", "stat_", "art_")


def descriptives(records: list[dict]) -> dict:
    fam = Counter(r.get("family", "") or "unassigned" for r in records)
    sub = Counter(r.get("d1_substrate", "") or "unstated" for r in records)
    year = Counter(r.get("year", "") or "unstated" for r in records)
    evid = Counter(r.get("d6_evidence", "") or "unstated" for r in records)
    flags = Counter(r.get("membership_flag", "") or "none" for r in records)
    hybrid = sum(1 for r in records if (r.get("family_secondary") or "").strip())
    ambiguous = sum(1 for r in records if truthy(r.get("family_ambiguous")))
    evid_amb = sum(1 for r in records if truthy(r.get("evidence_ambiguous")))

    cross: Counter = Counter()
    for r in records:
        cross[(r.get("family", "") or "?", r.get("d1_substrate", "") or "?")] += 1

    # substrate-crossing falsification test (s3-pyramid.md §3.6)
    fam_substrates = defaultdict(set)
    for r in records:
        if r.get("family") and r.get("d1_substrate"):
            fam_substrates[r["family"]].add(r["d1_substrate"])
    crossing = {f: sorted(s) for f, s in sorted(fam_substrates.items())}
    crossing_pass = {f: (len(s) >= 3) for f, s in sorted(fam_substrates.items())}

    completeness = {}
    if records:
        for field in sorted(records[0]):
            if not field.startswith(SPEC_PREFIXES):
                continue
            vals = [(r.get(field) or "").strip().lower() for r in records]
            applicable = [v for v in vals if v not in {"n/a", "na", ""}]
            if not applicable:
                continue
            stated = sum(1 for v in applicable if v.startswith("stated") or v in {"true", "1", "yes"})
            completeness[field] = {
                "n_applicable": len(applicable),
                "n_stated": stated,
                "frac_stated": stated / len(applicable),
            }

    return {
        "analysis": "descriptives",
        "n_records": len(records),
        "family": dict(fam),
        "substrate": dict(sub),
        "year": dict(sorted(year.items())),
        "evidence_tier": dict(evid),
        "membership_flags": dict(flags),
        "n_hybrid": hybrid,
        "n_family_ambiguous": ambiguous,
        "n_evidence_ambiguous": evid_amb,
        "family_x_substrate": {f"{k[0]}|{k[1]}": v for k, v in sorted(cross.items())},
        "substrate_crossing_test": {
            "substrates_per_family": crossing,
            "passes_3_substrate_rule": crossing_pass,
        },
        "reporting_completeness": completeness,
    }


# --- driver -----------------------------------------------------------------

ANALYSES = {"a1", "a2", "a3", "a4", "a5", "a6", "a7", "descriptives"}


def load(extraction: Path) -> tuple[list[dict], list[dict], list[dict]]:
    return (
        read_csv(extraction / "records.csv"),
        read_csv(extraction / "benchmarks.csv"),
        read_csv(extraction / "reproduction.csv"),
    )


def run(which: str, extraction: Path) -> dict:
    records, benches, repro = load(extraction)

    # A4 and A5 read only their own tables, so they run without the record corpus.
    # This matters for calibration: reproduction attempts made before extraction (to
    # test whether the 4-hour cap is realistic) must be analysable on their own, and
    # gating them behind records.csv would prevent exactly that. Such runs are
    # methodological piloting, not study data, and must be labelled so.
    if which == "a5":
        if not repro:
            return {"error": "no reproduction attempts found",
                    "looked_in": str(extraction / "reproduction.csv"),
                    "hint": "Run scripts/repro_attempt.py export first."}
        return a5(repro)
    if which == "a4":
        if not benches:
            return {"error": "no benchmark rows found",
                    "looked_in": str(extraction / "benchmarks.csv")}
        return a4(benches)

    if not records:
        return {
            "error": "no records found",
            "looked_in": str(extraction / "records.csv"),
            "hint": "Extraction has not run. See README.md status table.",
        }
    if which == "a1":
        return a1(records, benches)
    if which == "a2":
        return a2(records)
    if which == "a3":
        return a3(records)
    if which == "a6":
        return a6(records)
    if which == "a7":
        return a7(records)
    return descriptives(records)


def selftest() -> int:
    """Exercise every analysis on a synthetic fixture.

    The fixture proves the code runs and that the arithmetic is right. It is NOT
    data and never becomes data: nothing here may be reported.
    """
    import tempfile

    recs = [
        # matched pair on F1.1 / narma-10 / nmse, sim vs photonic
        {"record_id": "RC-0001", "family": "F1", "subclass": "F1.1", "family_secondary": "",
         "d1_substrate": "digital-simulated", "d6_evidence": "E0", "lang_max_claim": "L0",
         "membership_flag": "none", "year": "2021", "family_ambiguous": "false",
         "evidence_ambiguous": "false", "eff_claim_present": "false",
         "spec_state_dim": "stated", "proto_washout_stated": "not-stated"},
        {"record_id": "RC-0002", "family": "F1", "subclass": "F1.1", "family_secondary": "",
         "d1_substrate": "photonic", "d6_evidence": "E2", "lang_max_claim": "L4",
         "membership_flag": "none", "year": "2023", "family_ambiguous": "false",
         "evidence_ambiguous": "true", "eff_claim_present": "true", "eff_boundary": "B0",
         "eff_boundary_stated": "false", "eff_renorm_possible": "true",
         "spec_state_dim": "stated", "proto_washout_stated": "stated"},
        {"record_id": "RC-0003", "family": "F4", "subclass": "F4.1", "family_secondary": "F1",
         "d1_substrate": "memristive-ionic", "d6_evidence": "E3", "lang_max_claim": "L3",
         "membership_flag": "none", "year": "2024", "family_ambiguous": "true",
         "evidence_ambiguous": "false", "eff_claim_present": "true", "eff_boundary": "indeterminable",
         "eff_boundary_stated": "false", "eff_renorm_possible": "false",
         "spec_state_dim": "not-stated", "proto_washout_stated": "n/a"},
    ]
    bench = [
        {"record_id": "RC-0001", "benchmark": "narma-10", "metric": "nmse", "value": "0.05",
         "metric_defined": "true", "benchmark_params_stated": "true", "below_discrimination": "false"},
        {"record_id": "RC-0002", "benchmark": "narma-10", "metric": "nmse", "value": "0.10",
         "metric_defined": "true", "benchmark_params_stated": "false", "below_discrimination": "false"},
        {"record_id": "RC-0003", "benchmark": "narma-10", "metric": "nmse", "value": "0.02",
         "metric_defined": "false", "benchmark_params_stated": "false", "below_discrimination": "true"},
    ]
    rep = [
        {"record_id": "RC-0001", "repro_outcome": "R3", "repro_stratum": "F1/code",
         "repro_hours": "2.5", "repro_cap_hit": "false", "repro_failure_cause": ""},
        {"record_id": "RC-0002", "repro_outcome": "R1", "repro_stratum": "F1/no-code",
         "repro_hours": "4.0", "repro_cap_hit": "true", "repro_failure_cause": "missing-hyperparameters"},
    ]

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for name, rows in (("records", recs), ("benchmarks", bench), ("reproduction", rep)):
            keys = sorted({k for r in rows for k in r})
            with (d / f"{name}.csv").open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=keys)
                w.writeheader()
                for r in rows:
                    w.writerow({k: r.get(k, "") for k in keys})

        fails = []
        r1 = run("a1", d)
        # RC-0003 must be excluded: metric_defined is false.
        if r1["n_matched_cells"] != 1:
            fails.append(f"A1 matched cells {r1['n_matched_cells']} != 1")
        p = r1["pairs"][0]
        if abs(p["abs_diff"] - 0.05) > 1e-9:
            fails.append(f"A1 abs_diff {p['abs_diff']} != 0.05")
        if "metric-undefined" not in r1["excluded"]:
            fails.append("A1 did not report metric-undefined exclusion")

        r3 = run("a3", d)
        if r3["n_claim_exceeds_evidence"] != 1:  # RC-0002 L4 vs E2
            fails.append(f"A3 over-claims {r3['n_claim_exceeds_evidence']} != 1")
        if abs(r3["delta"]["mean"] - (0 + 2 + 0) / 3) > 1e-9:
            fails.append(f"A3 mean delta {r3['delta']['mean']} unexpected")

        r5 = run("a5", d)
        if r5["frac_reproduced_any"] != 0.5:
            fails.append(f"A5 frac {r5['frac_reproduced_any']} != 0.5")
        if r5["n_hit_effort_cap"] != 1:
            fails.append("A5 cap hit miscounted")

        r2 = run("a2", d)
        if r2["n_claims"] != 2 or r2["n_excluded_cannot_renormalise"] != 1:
            fails.append("A2 claim/exclusion counts wrong")
        if r2["frac_boundary_explicitly_stated"] != 0.0:
            fails.append("A2 stated-boundary fraction wrong")

        de = run("descriptives", d)
        if de["n_hybrid"] != 1 or de["n_family_ambiguous"] != 1:
            fails.append("descriptives hybrid/ambiguous counts wrong")
        # F1 has 2 substrates in the fixture, so it must FAIL the 3-substrate rule.
        if de["substrate_crossing_test"]["passes_3_substrate_rule"].get("F1") is not False:
            fails.append("substrate-crossing test did not fail as expected on fixture")

        r4 = run("a4", d)
        nb = r4["per_benchmark"]["narma-10"]
        if nb["n_metric_undefined"] != 1 or nb["n_params_not_stated"] != 2:
            fails.append("A4 hygiene counts wrong")

        # A6: hand-checkable association cases, computed on synthetic tables so the
        # decision rule is exercised in both directions before any real data exists.
        perfect = {("F1", "photonic"): 10, ("F2", "spintronic-magnetic"): 10}
        cv = cramers_v(perfect)
        if abs(cv["cramers_v"] - 1.0) > 1e-9:
            fails.append(f"A6 Cramer's V on perfect association = {cv['cramers_v']}, want 1")
        independent = {("F1", "photonic"): 5, ("F1", "quantum"): 5,
                       ("F2", "photonic"): 5, ("F2", "quantum"): 5}
        ci = cramers_v(independent)
        if abs(ci["cramers_v"]) > 1e-9:
            fails.append(f"A6 Cramer's V on independence = {ci['cramers_v']}, want 0")
        recs6 = ([{"family": "F1", "d1_substrate": "photonic"}] * 10
                 + [{"family": "F2", "d1_substrate": "spintronic-magnetic"}] * 10)
        r6 = a6(recs6)
        if abs(r6["normalized_mutual_information"] - 1.0) > 1e-9:
            fails.append("A6 NMI on perfect association != 1")
        if abs(r6["conditional_entropy_family_given_substrate"]) > 1e-9:
            fails.append("A6 H(family|substrate) on perfect association != 0")
        if "reducible" not in r6["verdict"]:
            fails.append(f"A6 verdict on perfect association: {r6['verdict']}")
        recs6b = ([{"family": "F1", "d1_substrate": "photonic"}] * 5
                  + [{"family": "F1", "d1_substrate": "quantum"}] * 5
                  + [{"family": "F2", "d1_substrate": "photonic"}] * 5
                  + [{"family": "F2", "d1_substrate": "quantum"}] * 5)
        if "independent" not in a6(recs6b)["verdict"]:
            fails.append("A6 verdict on independence is not the independence branch")

        # A7 and the participation ratio.
        if abs(participation_ratio([1, 1, 1, 1]) - 4.0) > 1e-9:
            fails.append("participation ratio of a flat spectrum != n")
        if abs(participation_ratio([1, 0, 0, 0]) - 1.0) > 1e-9:
            fails.append("participation ratio of a rank-1 spectrum != 1")
        if abs(participation_ratio([2, 1, 1]) - 16 / 6) > 1e-9:
            fails.append("participation ratio worked example wrong")
        if participation_ratio([0, 0]) is not None:
            fails.append("participation ratio of a zero spectrum is not None")
        recs7 = [
            {"record_id": "RC-1", "family": "F2", "state_dim": "400",
             "state_dim_kind": "virtual", "eff_dim_value": "40",
             "eff_dim_method": "participation-ratio"},
            {"record_id": "RC-2", "family": "F1", "state_dim": "100",
             "state_dim_kind": "physical", "eff_dim_value": "95",
             "eff_dim_method": "covariance-rank"},
            {"record_id": "RC-3", "family": "F1", "state_dim": "50",
             "state_dim_kind": "physical"},
        ]
        r7 = a7(recs7)
        if r7["n_with_both"] != 2:
            fails.append(f"A7 paired {r7['n_with_both']} records, want 2")
        if r7["excluded"].get("no-effective-dimension-reported") != 1:
            fails.append("A7 did not report the missing-effective-dimension exclusion")
        if abs(r7["records"][0]["ratio"] - 0.1) > 1e-9:
            fails.append("A7 ratio wrong")

    if fails:
        print("SELFTEST FAILED", file=sys.stderr)
        for f in fails:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("selftest passed: A1-A7 + descriptives")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=sorted(ANALYSES | {"all", "selftest"}))
    ap.add_argument("--extraction", type=Path, default=Path("data/extraction"))
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    if args.which == "selftest":
        return selftest()

    todo = sorted(ANALYSES) if args.which == "all" else [args.which]
    results = {name: run(name, args.extraction) for name in todo}
    text = json.dumps(results, indent=2, default=str)

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "results.json").write_text(text)
        print(f"-> {args.out / 'results.json'}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
