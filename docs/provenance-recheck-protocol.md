# Provenance re-check and expansion: protocol

**Status:** Fixed at tag `prov-protocol-v1` (2026-10-25), written for the IEEE Access
resubmission (Reviewer 1, point 2). Not run: no statement had been enumerated or re-verified
when it was tagged. From that commit on, any change is a numbered deviation in
`docs/deviations.md`; its departures from the 2026-08-20 frame are deviation D33. It is
pre-specified and time-stamped by that commit; it is not registered and is not described as
preregistration.

**Why it exists.** The manuscript's provenance result rests on eight statements chosen
purposively and verified by one investigator, four of whose dispositions were later
reversed (§8.2). Reviewer 1 asked for an independent second verifier and a systematically
selected sample, and for the abstract's five-of-eight claim to be qualified. This protocol
supplies both, without changing what the eight-statement set is: a case series that shows
mechanisms, reported apart from any rate.

It has two parts. **Part A** is a blind second verification of the original eight. **Part B**
executes the expansion that `docs/provenance-expansion-frame.md` fixed on 2026-08-20, and is
written so that it holds under either option of project decision D3 (Section B.3).

---

## Part A. Blind second verification of the eight statements

### A.1 Verifier

One verifier who knows reservoir computing and took no part in the original verification,
the threshold record (`docs/benchmark-thresholds.md`) or the provenance-audit document.
Before starting, the verifier records what of the manuscript and the repository they have
already read. Exposure to §8.2 or Table 11 is recorded, not disqualifying, because the
pool of qualified co-authors is small; it is reported as a limitation.

### A.2 What the verifier receives

Only `data/provenance/recheck/packet-blind.csv` and
`data/provenance/recheck/INSTRUCTIONS.md`. Each row gives a statement **as it was recorded
during scoping**, where it was encountered, the source it was attributed to at that time, and
its intended use. The packet does not contain the original dispositions, the primary
sources the original pass eventually located, the corrections, or the manuscript's account of
them. The attributions are reproduced as encountered, including those later found to be
wrong, because recovering from a wrong attribution is what the check tests. The wording is
taken from the record the original pass kept (the "statement recorded during scoping" column of
Table 11, the anchor list of `docs/benchmark-thresholds.md` §5 and deviations D1-D4 and D10-D17).
Where that record kept only a label (P4-P6), the coordinator wrote the claim out in full; this
is stated here so that a disagreement on those three can be read in that light.

Until the verifier's file is submitted, they do not consult: manuscript §8.2, Table 11 and
the supplementary section on the NARMA-10 baselines; `docs/benchmark-thresholds.md`;
`docs/citation-provenance-audit.md`; deviation log entries D1-D4 and D10-D17.

### A.3 Procedure

The procedure of manuscript §6.2, unchanged: the attributed source first; then backward and
forward citation searches, including the references of any secondary source, and
exact-phrase searches, until a primary statement is located or the trail is exhausted.
Bibliographic metadata are checked against Crossref, arXiv or the publisher. Automated
retrieval may be used to locate and fetch documents; every disposition is entered only after
the verifier has read the quoted passage in the primary.

### A.4 What is recorded per statement

The primary located (or not) and its full reference; a locator (page, section, equation,
table or figure); the supporting excerpt; the value, metric, unit and conditions the primary
states; whether the attribution was correct; a disposition and, for a meaning-changing case, a
mechanism code; minutes spent.

| Code | Disposition |
|---|---|
| V | Verified: value, metric, conditions and source all match (rounding within the stated precision is acceptable) |
| B | Bibliographic only: wrong year, title, version or identifier, or cited through a secondary source, with the value undistorted. An attribution to a source that does not state the value, or states a different value or condition, is M4, not B (manuscript §8.2 applies the same rule to the original eight) |
| M | Meaning-changing, with one or more mechanisms: M1 wrong value; M2 metric conflation (for example NMSE against NRMSE); M3 a dropped condition that changes the scope (for example i.i.d. input); M4 the value belongs to a different task, system or source; M5 drift along a citation chain |
| U-a | Unlocatable: the source cannot be obtained |
| U-b | Unlocatable: the source was obtained and the value is not in it |

A statement with several parts (item P7) gets a disposition per part.

### A.5 Analysis and reporting

The verifier's dispositions are compared with the original final dispositions (the
coordinator holds them). Reported: agreement on the disposition category (V/B/M/U) and on the
binary meaning-changing-or-not coding, per statement and as counts out of eight; every
disagreement with both excerpts. No kappa is computed on eight items; agreement is reported
as counts. Disagreements are discussed against the primary text, and any that remain go to a
third person blinded to who said what. The manuscript then states the eight-statement
result as: original dispositions, second-verifier agreement [k of 8], and the adjudicated
result, still labelled as a purposive case series that shows mechanisms and not a rate.

---

## Part B. Systematic expansion over the eleven reviews

### B.1 Frame (fixed 2026-08-20, restated)

Every external quantitative benchmark or theoretical claim asserted with a numeric value in the
eleven reviews of manuscript Table 3. A unit is a sentence in the review's main text that
(a) states a number attributed to another work and (b) concerns benchmark performance,
capacity, dispersion, a threshold or an efficiency figure. A claim repeated across reviews is
recorded once per review. Excluded: the review's own results, publication years and
unattributed numbers.

Numbers that appear only in a table or figure annotation are enumerated as a **separate
stratum**. They are reported alongside the main-text frame and never pooled with it. This
stratum is an addition to the 2026-08-20 frame, logged as deviation D33.

### B.2 Enumeration

Before any statement is verified, the eleven reviews are enumerated. Two reviews, chosen as
the first two in Table 3 order whose full text is open, are enumerated independently by two
people, and the capture overlap is reported. The remaining nine are enumerated by one
person. The enumerated list, with a stable identifier per unit, is committed and frozen before
Part B verification begins.

### B.3 Census or sample (project decision D3: n = 60)

The 2026-08-20 frame specified a census and expected 20-40 units; a later feasibility count
estimated 250-450. The rule, fixed now:

- **If the frozen list holds 60 or fewer main-text units**, every unit is verified (census),
  as the frame specified.
- **Otherwise**, a stratified random sample is verified: strata are the reviews, allocation
  is proportional to size with at least two per review, and the draw uses seed **20261025**.
  The sample size is **n = 60** (project decision D3, 2026-10-25; the n = 30 alternative is
  not used). That sampling replaces the census when the list is long is deviation D33 from the
  2026-08-20 frame; whether the branch was taken is recorded when the list is frozen.
- No replacement: a unit found unlocatable is an outcome, not a reason to draw another.
- If the frame yields fewer than 15 main-text units, the expansion is reported as descriptive
  only and no rate is quoted (the frame's rule 4).

### B.4 Verifiers, calibration and blinding

Two verifiers, neither of whom enumerated the review being verified, work independently from
the review sentence, its citation and this procedure. Neither sees the other's file. Before
the main pass both code five calibration units from outside the frame (number-citation pairs
from the introductions of five corpus records, chosen by the coordinator with seed 20261025),
discuss them, and do not count them.

### B.5 Analysis and reporting (pre-committed)

- The denominator is the full verified set; unresolved units are reported as such, never
  dropped (frame rule 1).
- The primary estimate is the proportion of meaning-changing dispositions after adjudication,
  with a Wilson 95% interval and, when sampled, a finite-population correction. It is a rate
  **for this frame**, quantitative claims in eleven reservoir-computing reviews from 2009 to 2026,
  not for the literature at large (frame rule 2).
- Sensitivity analyses: each verifier alone; U-b counted as meaning-changing.
- Agreement: raw agreement, Cohen's kappa and Gwet's AC1 on the five categories and on the
  binary coding, with bootstrap intervals.
- How often a verifier's first-pass disposition changed after discussion is reported, so that
  revisions of the kind that marked the original pass become a measured quantity.
- The eight-statement set is never pooled with the frame (frame rule 3).

### B.6 What the manuscript says if Part B is not finished in time

The abstract and §9.3 use this wording, and quote no rate: "In a purposive set of eight
statements, five required a meaning-changing correction or removal; checked by one investigator
and re-checked blind by a second, these counts illustrate mechanisms and are not a rate."

---

## Effort

Part A: about 8-10 hours for one verifier. Part B: enumeration about 2-3 days; verification
at about 30-45 minutes per unit for each of two verifiers, so about 60-90 person-hours at
n = 60.
