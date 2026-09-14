# RC-PYRAMID

Classification and evaluation framework for reservoir computing. Companion repository to
"A Review of Reservoir Computing Classification Schemes and an Architecture-Based
Framework for Evaluating Reported Systems".

Stefan Trajanovski, Ema Pandilova, Marko Petrov, Ivan Kitanovski, Ivan Chorbev,
Ivica Dimitrovski, Dimitar Trajanov and Ilinka Ivanoska.
Faculty of Computer Science and Engineering, Ss. Cyril and Methodius University in Skopje.

The manuscript is pre-submission. The protocol is public and **not registered**.

## Contents

```
docs/taxonomy-v1.0.md        classification instrument, frozen 2026-09-05
docs/protocol.md             audit protocol
docs/codebook.md             extraction fields and coding rules
docs/search-strategy.md      queries, dates, per-source counts
docs/benchmark-thresholds.md benchmark and theory anchors, with provenance
docs/deviations.md           every instrument change, dated
docs/prisma-2020-checklist.md
data/screening/              candidate corpus, flow counts, pilot record
scripts/                     search, dedupe, screening, analysis, figures
```

## Status

| | |
|---|---|
| Taxonomy v1.0 | frozen 2026-09-05 |
| Two-coder pilot | passed: kappa 0.954, unassignable 3.2% per coder |
| Coding runs behind that | three, on pairwise disjoint samples, 120 distinct records |
| Candidate corpus | 6,486 records after deduplication, all 106 near-duplicate pairs adjudicated |
| Screening, extraction, reproduction | not started |
| Protocol registration, archival DOI | neither filed |

The pilot sample reached only two of the four families, so F3 and F4 have no inter-rater
evidence. See `data/screening/pilot/README.md`. The first pilot attempt failed and is kept in
full at `data/screening/pilot-01-failed-20260905/`; a failed run is evidence.

## Reproducing

Python 3.11+, standard library only. Every analysis script has a selftest.

```
python3 scripts/screen.py selftest
python3 scripts/analyses.py selftest
python3 scripts/figures.py selftest
```

Two of `figures.py`'s checks cross-validate a figure against the manuscript sources, which
are authored outside this repository; they report themselves as SKIPPED here rather than
passing silently. The pilot result reproduces from the released coder files:

```
python3 scripts/screen.py pilot-kappa --a data/screening/pilot/pilot_coderA.csv \
                                      --b data/screening/pilot/pilot_coderB.csv
```

Search exports in `data/raw/` are frozen. To re-run the search rather than reuse them:

```
python3 scripts/fetch_openalex.py
python3 scripts/fetch_arxiv.py
python3 scripts/dedupe.py --openalex data/raw/openalex_20260731.json \
                         --arxiv    data/raw/arxiv_20260731.json \
                         --out      data/screening/corpus_deduped.csv
```

## Licence

Code MIT, text and data CC BY 4.0. See `LICENSE` for third-party material.
