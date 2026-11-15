# RC-PYRAMID

Classification and evaluation framework for reservoir computing. Companion repository to
"A Critical Review of Reservoir Computing Classification Schemes and an
Architecture-Based Framework for Evaluating Reported Systems".

Stefan Trajanovski, Ema Pandilova, Marko Petrov, Ivan Kitanovski, Ivan Chorbev,
Ivica Dimitrovski, Dimitar Trajanov and Ilinka Ivanoska.
Faculty of Computer Science and Engineering, Ss. Cyril and Methodius University in Skopje.

The manuscript is in revision at IEEE Access. The protocols are public, pre-specified and
**not registered**.

## Contents

```
docs/taxonomy-v1.0.md                  classification instrument, version 1.0, fixed for coding 2026-09-05
docs/validation-study-2.md             targeted reliability study of F3, F4 and the family boundaries
docs/provenance-recheck-protocol.md    blind second verification of the eight provenance statements
docs/protocol.md                       audit protocol
docs/codebook.md                       extraction fields and coding rules
docs/search-strategy.md                queries, dates, per-source counts, supplementary search leg
docs/benchmark-thresholds.md           benchmark and theory anchors, with provenance
docs/deviations.md                     every instrument change, dated
docs/prisma-2020-checklist.md
data/screening/                        candidate corpus, flow counts, pilot record
data/screening/validation2/            targeted study: frame, sample, retrieval log, coder files, statistics
data/provenance/recheck/               blind packet and instructions for the second verifier
scripts/                               search, dedupe, screening, validation, analysis, figures
```

## Status

| | |
|---|---|
| Taxonomy | version 1.0, fixed for coding 2026-09-05; edge-case rulings appended with date and trigger |
| Two-coder pilot | passed: kappa 0.954, unassignable 3.2% per coder; reached F1 and F2 only |
| Targeted study (160 records) | F3 passed; F4 insufficient information (23 records, 30 required); unassignable gate not met (10.8% / 9.0%); joint criterion not met |
| Provenance (8 statements) | blind second verification agrees with all eight final dispositions; systematic expansion specified, not run |
| Candidate corpus | 6,486 records after deduplication, all 106 near-duplicate pairs adjudicated; supplementary leg adds 802 (503 openly retrievable) as a separate tagged source |
| Screening, extraction, reproduction | not started |
| Protocol registration, archival DOI | neither filed |

The pilot sample reached only two of the four families. The targeted study then tested F3, F4
and their boundaries on records drawn by a fixed rule; see `docs/validation-study-2.md` and
`data/screening/validation2/`. Every coding run, including the failed first pilot attempt, is
recorded with its statistics in `docs/deviations.md`; a failed run is evidence.

## Reproducing

Python 3.11+, standard library only. Every analysis script has a selftest.

```
python3 scripts/screen.py selftest
python3 scripts/validation.py selftest
python3 scripts/analyses.py selftest
python3 scripts/figures.py selftest
```

Two of `figures.py`'s checks cross-validate a figure against the manuscript sources, which
are authored outside this repository; they report themselves as SKIPPED here rather than
passing silently. The pilot and the targeted-study results reproduce from the released coder
files:

```
python3 scripts/screen.py pilot-kappa --a data/screening/pilot/pilot_coderA.csv \
                                      --b data/screening/pilot/pilot_coderB.csv
mkdir out && cp data/screening/validation2/sample.json out/
python3 scripts/validation.py stats --a data/screening/validation2/vs2_coderA.csv \
                                    --b data/screening/validation2/vs2_coderB.csv --outdir out
```

`stats` reads the sample from `--outdir` and writes its results there, so a fresh folder leaves
the released files untouched.

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
