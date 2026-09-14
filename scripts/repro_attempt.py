#!/usr/bin/env python3
"""Harness for reproduction attempts (protocol.md §8, codebook.md §12).

    python3 scripts/repro_attempt.py init  RC-0123 --stratum F1/code --coder ST \
        --metric nmse --reported 0.048 --dispersion 0.0095
    python3 scripts/repro_attempt.py note  RC-0123 "installed deps, no version pins given"
    python3 scripts/repro_attempt.py close RC-0123 --outcome R1 --cause missing-hyperparameters
    python3 scripts/repro_attempt.py status
    python3 scripts/repro_attempt.py export

Why a harness rather than a spreadsheet
---------------------------------------
Three things have to be true for the reproduction sub-study to mean anything, and all three
are easy to lose by hand:

1. Elapsed time must be wall-clock and recorded as it happens. Reconstructed afterwards it
   becomes an estimate, and the 4-hour cap stops being a measurement.
2. The tolerance test must be applied mechanically. Deciding case by case whether a recovered
   value is "close enough" is the single easiest place for the study's conclusion to drift.
3. Every attempt must be logged, INCLUDING the failures. A directory that only contains
   successes is not evidence.

Timestamps come from the filesystem and the clock at the moment each subcommand runs, so a
forgotten `close` shows up as an implausible duration rather than passing silently.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RUNS = Path("runs")
EXPORT = Path("data/extraction/reproduction.csv")

CAP_HOURS = 4.0                 # protocol.md §8.2
TOLERANCE_REL = 0.20            # protocol.md §8.5

OUTCOMES = {
    "R0": "Not attemptable: insufficient information, or data/hardware unobtainable",
    "R1": "Attemptable, failed: sufficient information in principle, not recovered in cap",
    "R2": "Qualitatively reproduced: same ordering/conclusion, quantitatively different",
    "R3": "Quantitatively reproduced: within tolerance",
    "R4": "Reproduced from released artefacts: authors' own code runs and gives the result",
}

CAUSES = [
    "missing-hyperparameters", "missing-seed", "ambiguous-preprocessing",
    "undefined-metric", "unavailable-data", "ambiguous-split",
    "code-does-not-run", "other",
]

TEMPLATE = """# Reproduction attempt: {rid}

Opened {opened} UTC by {coder}. Stratum {stratum}.

Protocol: `docs/protocol.md` §8. Effort cap {cap} h wall-clock, single attempt.
**No author contact during the attempt** (§8.3). Network access limited to retrieving this
paper's own artefacts.

## Target

| | |
|---|---|
| Primary metric | {metric} |
| Reported value | {reported} |
| Reported dispersion | {dispersion} |
| Tolerance for R3 | +/- {tolpct:.0f}% relative, or inside the reported dispersion |

## Pre-flight

Tick before starting the clock in earnest. Anything unticked is itself a finding.

- [ ] Full text obtained
- [ ] Code artefact located (or confirmed absent)
- [ ] Data obtainable (or confirmed unobtainable)
- [ ] Reservoir parameters located in text or supplement
- [ ] Train/test split and washout stated
- [ ] Error metric normalisation defined

## Running log

Append with `repro_attempt.py note {rid} "..."`. Record dead ends: the failure causes are
the point of this sub-study, not a by-product of it.

## Outcome

Filled by `repro_attempt.py close`.
"""


def now() -> datetime:
    return datetime.now(timezone.utc)


def d(rid: str) -> Path:
    return RUNS / f"repro_{rid}"


def meta_path(rid: str) -> Path:
    return d(rid) / "meta.json"


def load(rid: str) -> dict:
    p = meta_path(rid)
    if not p.exists():
        sys.exit(f"no open attempt for {rid}. Run `init` first.")
    return json.loads(p.read_text())


def save(rid: str, m: dict) -> None:
    meta_path(rid).write_text(json.dumps(m, indent=2))


def cmd_init(a) -> int:
    if meta_path(a.record).exists():
        sys.exit(f"{a.record} already initialised. Attempts are single-shot (§8.2); "
                 f"delete {d(a.record)} deliberately if you really mean to restart.")
    d(a.record).mkdir(parents=True, exist_ok=True)
    m = {
        "record_id": a.record,
        "repro_stratum": a.stratum,
        "coder": a.coder,
        "repro_target_metric": a.metric,
        "repro_reported_value": a.reported,
        "reported_dispersion": a.dispersion,
        "opened_utc": now().isoformat(),
        "closed_utc": None,
    }
    save(a.record, m)
    (d(a.record) / "log.md").write_text(TEMPLATE.format(
        rid=a.record, opened=m["opened_utc"], coder=a.coder, stratum=a.stratum,
        cap=CAP_HOURS, metric=a.metric, reported=a.reported,
        dispersion=a.dispersion if a.dispersion is not None else "not reported",
        tolpct=TOLERANCE_REL * 100,
    ))
    print(f"opened {a.record}\n  {d(a.record)/'log.md'}\n  clock running, cap {CAP_HOURS} h")
    return 0


def cmd_note(a) -> int:
    m = load(a.record)
    if m["closed_utc"]:
        sys.exit(f"{a.record} is closed. Notes after closing would be reconstruction.")
    stamp = now()
    hrs = (stamp - datetime.fromisoformat(m["opened_utc"])).total_seconds() / 3600
    with (d(a.record) / "log.md").open("a") as fh:
        fh.write(f"\n- `+{hrs:5.2f}h` {a.text}\n")
    flag = "  ** PAST CAP **" if hrs > CAP_HOURS else ""
    print(f"+{hrs:.2f}h noted{flag}")
    return 0


def within_tolerance(reported: float | None, recovered: float | None,
                     dispersion: float | None) -> bool | None:
    """protocol.md §8.5, applied mechanically and never by judgement."""
    if reported is None or recovered is None:
        return None
    if dispersion is not None and abs(recovered - reported) <= abs(dispersion):
        return True
    if reported == 0:
        return recovered == 0
    return abs(recovered - reported) / abs(reported) <= TOLERANCE_REL


def cmd_close(a) -> int:
    m = load(a.record)
    if m["closed_utc"]:
        sys.exit(f"{a.record} already closed at {m['closed_utc']}")
    if a.outcome in {"R0", "R1"} and not a.cause:
        sys.exit(f"{a.outcome} requires --cause (protocol.md §8.6). "
                 f"The failure-cause distribution is what justifies RC-REPORT.")
    if a.cause and a.cause not in CAUSES:
        sys.exit(f"unknown cause {a.cause!r}. One of: {', '.join(CAUSES)}")

    closed = now()
    hrs = (closed - datetime.fromisoformat(m["opened_utc"])).total_seconds() / 3600
    tol = within_tolerance(m["repro_reported_value"], a.recovered,
                           m.get("reported_dispersion"))

    m.update({
        "closed_utc": closed.isoformat(),
        "repro_outcome": a.outcome,
        "repro_recovered_value": a.recovered,
        "repro_within_tolerance": tol,
        "repro_hours": round(hrs, 3),
        "repro_cap_hit": hrs >= CAP_HOURS,
        "repro_failure_cause": a.cause or "",
        "repro_log_path": str(d(a.record) / "log.md"),
        "repro_author_correction": "",
    })
    save(a.record, m)

    with (d(a.record) / "log.md").open("a") as fh:
        fh.write(
            f"\n## Outcome\n\n"
            f"- **{a.outcome}**: {OUTCOMES[a.outcome]}\n"
            f"- Recovered value: {a.recovered}\n"
            f"- Within tolerance: {tol}\n"
            f"- Elapsed: {hrs:.2f} h (cap {'HIT' if hrs >= CAP_HOURS else 'not hit'})\n"
            f"- Failure cause: {a.cause or 'n/a'}\n"
            f"\nClosed {closed.isoformat()} UTC.\n"
        )

    # Consistency warnings. These do not block: the coder's judgement stands, but a
    # mismatch between the outcome and the mechanical tolerance test must be visible.
    if a.outcome == "R3" and tol is False:
        print("  WARNING: coded R3 but the recovered value is outside tolerance.", file=sys.stderr)
    if a.outcome in {"R2", "R3", "R4"} and a.recovered is None:
        print("  WARNING: reproduction coded without a recovered value.", file=sys.stderr)
    if hrs > CAP_HOURS * 1.5:
        print(f"  WARNING: {hrs:.1f} h exceeds the cap by more than half again. "
              f"Was `close` forgotten?", file=sys.stderr)

    print(f"closed {a.record}: {a.outcome}, {hrs:.2f} h, within_tolerance={tol}")
    return 0


def all_meta() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(RUNS.glob("repro_*/meta.json"))]


def cmd_status(a) -> int:
    rows = all_meta()
    if not rows:
        print("no attempts yet.")
        print(f"\nTarget n = 24 (protocol.md §8.1). Sample cannot be drawn until extraction\n"
              f"codes `reproducible_in_principle`.")
        return 0
    openn = [r for r in rows if not r["closed_utc"]]
    done = [r for r in rows if r["closed_utc"]]
    print(f"{len(rows)} attempts: {len(done)} closed, {len(openn)} open\n")
    for r in rows:
        if r["closed_utc"]:
            print(f"  {r['record_id']}  {r['repro_outcome']}  {r['repro_hours']:.2f}h  "
                  f"{r['repro_stratum']}  {r.get('repro_failure_cause','')}")
        else:
            el = (now() - datetime.fromisoformat(r["opened_utc"])).total_seconds() / 3600
            print(f"  {r['record_id']}  OPEN  {el:.2f}h elapsed  {r['repro_stratum']}")
    if done:
        from collections import Counter
        c = Counter(r["repro_outcome"] for r in done)
        print("\n  " + "  ".join(f"{k}={c.get(k,0)}" for k in OUTCOMES))
    print(f"\n  {len(done)}/24 toward target")
    return 0


def cmd_export(a) -> int:
    rows = [r for r in all_meta() if r["closed_utc"]]
    if not rows:
        sys.exit("no closed attempts to export.")
    cols = ["record_id", "repro_selected", "repro_stratum", "repro_outcome",
            "repro_target_metric", "repro_reported_value", "repro_recovered_value",
            "repro_within_tolerance", "repro_hours", "repro_cap_hit",
            "repro_failure_cause", "repro_log_path", "repro_author_correction"]
    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    with EXPORT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            r = dict(r, repro_selected="true")
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"{len(rows)} attempts -> {EXPORT}\n"
          f"Feeds analysis A5: python3 scripts/analyses.py a5")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init"); i.set_defaults(fn=cmd_init)
    i.add_argument("record"); i.add_argument("--stratum", required=True)
    i.add_argument("--coder", required=True); i.add_argument("--metric", required=True)
    i.add_argument("--reported", type=float, required=True)
    i.add_argument("--dispersion", type=float, default=None)

    n = sub.add_parser("note"); n.set_defaults(fn=cmd_note)
    n.add_argument("record"); n.add_argument("text")

    c = sub.add_parser("close"); c.set_defaults(fn=cmd_close)
    c.add_argument("record"); c.add_argument("--outcome", required=True, choices=sorted(OUTCOMES))
    c.add_argument("--recovered", type=float, default=None)
    c.add_argument("--cause", default=None)

    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("export").set_defaults(fn=cmd_export)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
