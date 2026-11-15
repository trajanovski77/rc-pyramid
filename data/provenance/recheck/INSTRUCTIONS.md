# Provenance re-check: instructions for the verifier

You are checking eight quantitative statements against their primary sources. Each row of
`packet-blind.csv` gives a statement as it was written down during an early literature scan,
where it was found, the source it was attributed to at the time, and what it was going to be
used for. Some attributions may be wrong. Your job is to find out what the primary source
actually says.

**Until you submit your file, please do not read** manuscript Section 8.2, its Table 11, or
the supplementary section on the NARMA-10 baselines; `docs/benchmark-thresholds.md`;
`docs/citation-provenance-audit.md`; or entries D1-D4 and D10-D17 of `docs/deviations.md`.
At the start, write down in `notes` of a first, extra row which of these, and which other
parts of the manuscript, you have already read.

## For each statement

1. Check the attributed source first.
2. If it does not contain the statement, follow citations backward (the source's own
   references, and the references of any secondary source the statement came through) and
   forward (works citing the source), and search for exact phrases, until you locate a primary
   statement or run out of trail.
3. Check the bibliographic details against Crossref, arXiv or the publisher.
4. Read the passage yourself before you enter a disposition. Tools may help you find and
   fetch documents; they may not make the call.

## What to fill in

`primary_located` (yes/no), `primary_reference` (full reference), `locator` (page, section,
equation, table or figure), `excerpt` (the supporting text, verbatim), `value_in_primary`,
`metric`, `unit`, `conditions` (input distribution, operating point, thresholds, anything
that limits the value), `attribution_correct` (yes/no), `disposition`, `mechanism`, `notes`,
`minutes`.

| `disposition` | Meaning |
|---|---|
| V | Value, metric, conditions and source all match (rounding within the stated precision is fine) |
| B | Only a bibliographic error (year, title, version, identifier) or cited through a secondary source; the value is undistorted. If the attributed source does not state the value, or states a different value or condition, use M4, not B |
| M | The meaning changes; give one or more `mechanism` codes |
| U-a | The source cannot be obtained |
| U-b | The source was obtained and the value is not in it |

| `mechanism` | Meaning |
|---|---|
| M1 | Wrong value |
| M2 | Metric conflated (for example NMSE against NRMSE) |
| M3 | A condition dropped that changes the scope (for example i.i.d. input) |
| M4 | The value belongs to a different task, system or source |
| M5 | Drift along a citation chain |

Item P7 has three parts: give each part its own disposition in `notes` and the worst of them in
`disposition`.

Work alone and do not discuss the items with anyone until the file is submitted. Send the
completed file to the coordinator, who saves it unchanged before anything is compared.
