# Pre-Registration Protocol

**Study:** Does Reservoir Computing Reproduce? A Substrate-Independent Taxonomy and
Systematic Audit of Algorithms, Benchmarks, and Physical Implementations

**Protocol version:** 1.0 (DRAFT, not yet registered)
**Registration target:** OSF Registries, "Systematic Review" template
**Registration date:** _pending_
**Search cutoff:** 2026-06-30 (frozen)

> **This document must be registered before any full-text extraction begins.** Screening
> may proceed in parallel with registration; extraction may not. The registration DOI must
> be cited in the manuscript methods section.

---

## 1. Research questions

**RQ1 (structure).** Can the RC literature be partitioned by state-generation principle
into families that are substrate-independent, mutually exclusive, and assignable by
independent coders?

**RQ2 (reporting).** What proportion of the RC corpus reports the information required to
re-execute its results, reservoir specification, protocol, statistics, baselines, and
artefacts?

**RQ3 (reproduction).** Of a stratified sample of algorithmically reproducible results,
what proportion reproduce, and where reproduction fails, why?

**RQ4 (benchmarks).** Which benchmark tasks dominate the corpus, and do reported results
still fall within the range where those benchmarks discriminate between systems?

**RQ5 (realization gap).** For architecturally matched pairs differing only in substrate,
what is the performance difference between simulated and physical realizations?

**RQ6 (evidence).** How is the corpus distributed over evidence-maturity tiers (E0-E5), and
does the language used to describe results track the tier actually demonstrated?

**RQ7 (efficiency).** At what system boundary are efficiency claims computed, and how do
they change when re-normalized to a common full-system boundary?

---

## 2. Design

Systematic review with a quantitative reporting-compliance audit and a nested reproduction
study. Reported per PRISMA 2020. Not a meta-analysis: effect sizes across RC tasks are not
commensurable and will not be pooled.

---

## 3. Search strategy

Full strings, databases, and deduplication procedure are specified in
`search-strategy.md` and are part of this registration by reference.

**Window:** 2019-01-01 to 2026-06-30.

**Justification for the start date.** January 2019 precedes Tanaka et al.'s canonical
physical-RC review (Neural Networks, July 2019). The window therefore covers the entire
period the field has had a shared map of itself. It also postdates the general adoption of
code-sharing norms in ML venues, so compliance findings cannot be dismissed as an artefact
of auditing a pre-open-science era, a limitation that would apply to a window reaching
back to the 2001-2012 foundational papers.

**Cutoff is frozen.** Records published after 2026-06-30 are excluded even if encountered.
Late-breaking work is discussed in the narrative but never enters the corpus statistics.

---

## 4. Eligibility

### 4.1 Inclusion

- Satisfies the RC Contract membership test (`taxonomy-v1.0.md` §1).
- Reports at least one quantitative performance or capacity result.
- Peer-reviewed article, conference paper, book chapter reporting primary research, or
  preprint with a stable identifier. **Widened 2026-09-05**: 37 book chapters in the
  open-access corpus include primary research, and excluding them on form would drop real
  work; review and tutorial chapters remain `not-primary` on their content.
- English full text available.
- **Openly retrievable** (deviation D6, 2026-07-31). Full text obtainable without a paid
  subscription, via an open-access publication, a repository deposit, or a preprint.

The last criterion narrows the study's claims to the openly accessible reservoir computing
literature. It follows from the study's own logic as well as from access constraints: an
auditor cannot assess whether a paper reports enough to be re-executed if the auditor cannot
read the paper. Including unreadable records would measure our access rather than the
literature's reporting.

It is nonetheless a real limitation and is treated as one (manuscript §9, and
the manuscript's limitations section), not as a neutral scope decision.

### 4.2 Exclusion

| Code | Criterion |
|---|---|
| `not-rc:no-state-map` | No multidimensional nonlinear state map. |
| `not-rc:trained-internals` | Task error reaches state-map parameters. |
| `not-rc:no-trained-readout` | Readout not fit to a task. |
| `not-rc:static-input` | No input-history dependence. |
| `no-result` | No quantitative result reported (pure theory, pure position). |
| `not-primary` | Review, survey, tutorial, editorial. **Collected separately** for the review-of-reviews table; not in the audit corpus. |
| `unavailable` | Full text not obtainable after two attempts including interlibrary request. |
| `duplicate` | Same study as an already-included record (preprint/journal pairs resolved to the journal version, preprint ID retained). |
| `not-eligible:publication-type` | The publication **object** is outside §4.1's list: dissertation, book, conference abstract, dataset or code deposit, software, report, erratum, retraction, peer review, paratext, reference entry. Applies to the object, not its content, so a review *article* remains `not-primary`. Added 2026-09-05: 276 records (7.8%) of the open-access non-duplicate corpus carry such a `venue_type` and had no code, dissertations (107) being the bulk. Triggering records RC-5337 and RC-0387, pilot 2. |
| `not-english` | No English full text available (§4.1). Added 2026-09-05; §4.1 has required it since the protocol was written and §4.2 could not express it. Triggering record RC-0387, pilot 2. |

### 4.3 Reviews are corpus-adjacent, not corpus

Reviews and tutorials are excluded from the audit corpus but retained in a separate table
feeding manuscript §3. This avoids the circularity of auditing reviews for reproducibility.

---

## 5. Screening

**Input.** Screening operates on `data/screening/corpus_deduped.csv` filtered to
`dup_of == ""` and, under D6, to `is_oa == "1"`. Both filters are properties of the corpus
file rather than separate datasets, so the excluded records stay available to the §9.2
characterisation. Stage 1 cannot begin until the §5 step 3 near-duplicate pairs are
adjudicated (`search-strategy.md` §5.1).

**Records with no abstract.** 215 of the eligible records carry a title but no abstract, so they cannot be screened normally. (222 before the 2026-09-05 near-duplicate adjudication; corrected 2026-09-09.) They are flagged, not dropped, and the count is reported.

**Stage 1: title/abstract.** Two independent coders, blind to each other. Liberal
inclusion: any plausible RC record advances. Disagreements advance automatically.

**Stage 2: full text.** Two independent coders apply §4 in full. Disagreements resolved by
discussion; if unresolved, a third coder adjudicates and the case is added to
`taxonomy-v1.0.md` §11 as a ruling.

**Reliability.** Cohen's κ reported for both stages. Target κ ≥ 0.70. If Stage-1 κ < 0.70,
the criteria are clarified, a §11 ruling is issued, and **the entire stage is re-screened**
, not patched.

---

## 6. Data extraction

Per `codebook.md`, which is part of this registration by reference.

- All records extracted by one coder.
- A random 20% double-extracted by a second coder; κ (categorical) and ICC (continuous)
  reported per field.
- Fields with κ < 0.60 on the double-extracted subset are reported as low-reliability and
  excluded from headline claims.

---

## 7. Pilot pass (required, before freeze)

A random 40 records (stratified to guarantee ≥5 physical-substrate records) are coded by
two coders using taxonomy v1.0-draft.

**Information basis, fixed 2026-09-05 after two failed runs (deviation D25).** This section
never stated one, and both the 2026-08-28 check and pilot 1 were coded from title and
abstract alone. That basis was inherited from `preliminary-agreement-check.md`, which
describes a deliberately *reduced* trial, and it does not match the instrument under test:
`codebook.md` §0 codes from "the text, tables, figures, captions, or supplement", and
classification is applied at extraction, which follows the Stage-2 full-text screen. Both
runs therefore measured whether a record can be classified from its abstract, which is not
what the taxonomy claims.

The pilot is coded in **two passes over the same 40 records**:

1. **Abstract pass.** Title and abstract only. Record the call in `family_abstract`. Where
   the abstract does not determine the family, record `unassignable`.
2. **Full-text pass.** For every record left `unassignable` at pass 1, open the full text and
   code it again into `family`. Records resolved at pass 1 carry their pass-1 call forward
   unchanged; the coder does not revisit them, so the extra effort falls only on the
   remainder.

**Both unassignable rates are reported.** The pass-1 rate is a measurement of the literature,
comparable with the two earlier runs and interesting in its own right. **The gate is the
pass-2 rate**: a record that no coder can classify with the full paper in front of them is
the only kind that indicts the instrument. Cohen's kappa is computed on the pass-2 `family`
column over all sampled records, unchanged in every other respect.

**The pilot has three outputs:**

1. Completion of the Tier-2 subclass lists.
2. Initial §11 edge-case rulings.
3. The assignability test (`taxonomy-v1.0.md` §10). The other two validation tests require
   the screened corpus and are run after screening.

**Reporting (added 2026-08-27, before any coding; extended 2026-09-05).** Cohen's κ is
reported with raw agreement, a 95% confidence interval, and **Gwet's AC1 and Krippendorff's
alpha** as sensitivity statistics, because κ behaves counterintuitively under uneven family
prevalence and the three corrections model chance differently. **All three are computed over
every sampled record on the five-category vocabulary (F1-F4 and `unassignable`).
`unassignable` is a category a coder may choose, never a record dropped from the
calculation**: excluding it would remove the assignable-versus-unassignable disagreement that
the second half of the gate exists to measure, and would report a reliability figure for the
easy half of the task. Subclass agreement, the hybrid, symmetric-label, ambiguity and
unassignable rates, and the full coder confusion matrix are reported with it. **The reason
recorded for each unassignable record is tabulated**, separating a record that the instrument
cannot classify from a record that does not contain the information the instrument needs;
these are different findings and a single unassignable rate conflates them. At n = 40 the
large-sample standard error of κ near 0.70 is roughly 0.09-0.10, so the pilot is a gate
against gross disagreement, not a precise estimate; n = 40 was fixed as a gate size and no
target confidence-interval half-width was pre-specified.

**Gate basis, revised 2026-09-05 before the pilot was drawn (deviation D21).** The <=5%
unassignable criterion is applied to the records **both coders judged eligible** under §4.2,
and the all-records rate is reported beside it. The packet carries an explicit `eligible`
column so that judgement is made separately from classification. The reason is that §4.2
removes reviews, non-RC records and records with no quantitative result upstream and the §2
procedure never runs on them, so a gate meant to detect an unusable instrument was otherwise
measuring the composition of an unscreened corpus; the 2026-08-28 preliminary check
established that empirically, its whole 25-30% falling on absent abstracts, abstracts that do
not describe the mechanism, and records screening removes, with **no** record unassignable
because two families were both defensible. Both rates are reported in every case, because
reporting only the narrower one after a preliminary check exceeded the criterion would be
moving a goalpost rather than correcting a basis. Cohen's kappa is unchanged and is still
computed over **all** sampled records, so it stays comparable with the preliminary check.

**Symmetric hybrid labels in the statistic (deviation D22).** A record whose report does not
establish a dominant mechanism carries `family_symmetric` and an empty `family` (taxonomy
§2.1). Every such record contributes the single category `hybrid-symmetric` to the agreement
vocabulary, which is therefore six categories; which pair the coder named is reported
separately with its base, as subclass agreement is. Excluding these records would repeat the
error this section already rejects for `unassignable`.

**Two-system records in the gate numerator (deviation D29).** A record reporting systems in
two *different* families, where both are co-equal main-text comparators and neither is
subordinate, is `unassignable` under `taxonomy-v1.0.md` R11 and is reported here with its
reason rather than counted in the gate numerator. This is the third kind of unassignable
record the tabulation requirement above separates: not a record the instrument cannot
classify, and not a record missing the information the instrument needs, but a record
containing two systems, where a single family code is defeated by the record and not by the
taxonomy. **The carve-out touches the gate numerator and nothing else.** The record stays in
the sample, in Cohen's kappa, AC1 and Krippendorff's alpha over all six categories, in the
confusion matrix, in the all-records rate and in the gate denominator; it is never dropped
from the calculation, which the paragraph above forbids. It applies only where **both** coders
judged the record eligible and **both** coded it `unassignable` - one coder assigning a family
makes it a disagreement, which is what the gate exists to measure, and it then counts in full.
Membership is a declared list of record ids in `scripts/screen.py`, each with its
justification, never inferred from reason text. **The rate without the carve-out is reported
in every case, beside the rate with it**, for the same reason both the eligible-only and
all-records rates are reported under D21: narrowing a basis and reporting only the narrower
number would be moving a goalpost rather than correcting one.

**Gate.** If the assignability test fails, the taxonomy is revised and the pilot re-run on a
fresh sample. Only after it passes is v1.0 frozen, the freeze date recorded, and this protocol
registered. The later validation tests can reject the frozen taxonomy but cannot license a
silent revision.

**Pilot records are discarded from the main corpus statistics** and re-drawn, to avoid
tuning the instrument on records that then contribute to results.

---

## 8. Reproduction sub-study

### 8.1 Sampling

Stratified random sample of **n = 24** records, drawn from those coded
`reproducible_in_principle = true` (i.e. E0-E2, no proprietary data, no hardware
requirement). Strata: family (F1-F4) × artefact availability (code released / not),
allocated proportionally with a minimum of 2 per non-empty cell.

**n = 24 is a pre-committed floor, not a target.** If resources permit more, the increase
must be pre-registered as an amendment before additional records are drawn.

### 8.2 Effort cap

**4 hours per record**, wall-clock, single attempt, logged. On expiry the record is coded at
whatever tier was reached. The cap is part of the finding: a result that cannot be recovered
in four hours by a competent independent implementer with the paper in hand is, operationally,
not reproducible. This framing must appear in the manuscript.

### 8.3 Author contact

**No author contact during the reproduction attempt.** Contacting authors measures author
responsiveness, not paper sufficiency. Authors of records coded R0/R1 will be notified after
coding is complete and before submission, and any correction they supply will be reported in
a separate column, never merged into the primary outcome.

### 8.4 Outcome scale

| Code | Meaning |
|---|---|
| **R0** | Not attemptable, insufficient information, or data/hardware unobtainable. |
| **R1** | Attemptable, failed, sufficient information in principle; result not recovered within cap. |
| **R2** | Qualitatively reproduced, same ordering/conclusion, quantitatively different. |
| **R3** | Quantitatively reproduced, within tolerance (§8.5) of the reported figure. |
| **R4** | Reproduced from released artefacts, authors' own code runs and yields the reported result. |

### 8.5 Tolerance: pre-committed

**R3 requires the recovered value to fall within ±20% relative** of the reported point
value on the paper's own primary metric, **or** within the paper's own reported dispersion
interval where one is given.

This threshold is deliberately generous: the claim under test is "does the result hold,"
not "does it match to three decimals." A tight threshold would manufacture failures
attributable to seed and floating-point variation rather than to reporting deficiency.
**The threshold is fixed now and will not be adjusted after seeing results.**

### 8.6 Failure attribution

Every R0/R1 record is coded for primary cause, one of: `missing-hyperparameters` ·
`missing-seed` · `ambiguous-preprocessing` · `undefined-metric` · `unavailable-data` ·
`ambiguous-split` · `code-does-not-run` · `other`. This distribution is what makes the
reporting checklist evidence-based, and it is the bridge from results to recommendations.

---

## 9. Pre-specified analyses

Registered in advance. Anything not listed here is exploratory and will be labelled as such
in the manuscript.

| ID | Analysis | Primary output |
|---|---|---|
| **A1** | Matched-pair simulated-vs-physical performance, within family × benchmark × metric | Paired difference with CI |
| **A2** | Efficiency claims re-normalized to boundary B3 | Reported vs B3 spread, log scale, with per-record assumption notes |
| **A3** | Abstract language coded against evidence tier D6 | Rhetoric-evidence contingency table |
| **A4** | Benchmark discrimination, fraction of reported errors below the discriminating threshold | Per-benchmark saturation curve over time |
| **A5** | Reproduction outcomes with failure attribution | R0-R4 distribution + cause breakdown |
| **A6** | Architecture-vs-substrate association over the screened corpus | Family x substrate contingency table with Cramer's V (bias-corrected), normalized mutual information, and both conditional entropies |
| **A7** | Reported state dimension against effective state dimension | Ratio distribution by family and by `state_dim_kind`, with the share of records for which no effective dimension is recoverable |

**A6 and A7 added 2026-09-05**, before any classification or extraction data existed, after
three review rounds asked for a quantitative form of the architecture-versus-substrate claim
and for empirical support for the effective-dimension argument. Their decision rules are
fixed in `scripts/analyses.py` and reproduced here: A6 rejects "architecture is reducible to
substrate" when the bias-corrected Cramér's V is below 0.70 **and** normalized mutual
information is below 0.70, and rejects "architecture is unrelated to substrate" when V
exceeds 0.20; between those it reports an intermediate association, which is what the
framework predicts and is therefore **not** counted as confirmation on its own. A6 is
reported with its contingency table and an underpowered flag whenever any expected cell count
falls below 5. A7 never estimates an effective dimension the source does not supply; the
share of records for which the question cannot be answered is part of its result.

**Supporting descriptives (also pre-specified):** corpus composition by family × substrate ×
year; reporting-completeness rates per codebook item, stratified by family, substrate, and
evidence tier; hybrid rate; membership-flag rates.

### 9.2 Exclusion characterisation (added with D6, pre-specified)

Because the harvest retains metadata for the closed-access records excluded by §4.1, the
exclusion is described rather than assumed harmless. The manuscript reports the included open
set against the excluded closed set on:

- publication year distribution
- venue and venue type distribution
- citation count distribution
- share of records whose title or abstract matches physical-substrate terminology, as a proxy
  for whether the exclusion falls unevenly across the taxonomy's families

Direction and magnitude are reported whatever they show. A finding that closed-access work
skews toward particular venues or years is a real constraint on the study's generality and is
stated as such in §11 rather than minimised.

This analysis uses metadata only. No closed record is screened, coded, or counted in the
corpus statistics.

### 9.1 A3 coding rule: fixed in advance

Abstract sentences describing the reported system are coded for the highest maturity
claim implied, using a closed keyword-anchored rubric defined in `codebook.md` §9. Coding is
done **blind to the record's D6 tier**: the coder sees the abstract only. This blinding is
what defends A3 against the charge of subjectivity and is mandatory.

---

## 10. Analyses explicitly NOT performed

- No pooled meta-analytic effect size.
- No ranking of individual papers, authors, groups, or venues. Per-record outcomes are
  reported de-identified in the main text; the identified dataset is released only if the
  ethics position in §12 is satisfied.
- No claim that a failed reproduction implies error or misconduct. R0/R1 measure
  **reporting sufficiency**, not correctness. This distinction must be stated in the
  abstract, the results section, and the limitations section.

---

## 11. Deviations

Any departure from this protocol is logged in `docs/deviations.md` with date, reason, and
whether it was made before or after seeing the affected results. The deviation log is
published with the manuscript. Undisclosed deviation is the single failure mode that would
invalidate the study's central claim to rigour.

---

## 12. Ethics and fairness position

The audit measures reporting practice, not competence. Three commitments:

1. **No naming in the main text.** Aggregate statistics only; per-record outcomes
   de-identified.
2. **Right of reply.** Authors of R0/R1 records are notified before submission (§8.3).
3. **Self-inclusion.** Any of our own group's work meeting the eligibility criteria is
   included and coded by the coder who did not author it.

The identified per-record dataset will be released **only** if it can be published without
functioning as a league table, most likely as a coded dataset keyed to DOIs with outcome
fields, released alongside, not inside, the manuscript. If that cannot be done fairly, the
de-identified dataset is released and the identified one withheld, with the reason stated.

---

## 13. Artefact release

On submission: this protocol, `taxonomy-v1.0.md` (frozen), `codebook.md`,
`search-strategy.md`, `deviations.md`, all search exports with retrieval dates, the
screening decisions including the manual near-duplicate adjudications, the extraction
dataset, all retrieval and analysis scripts, the scripts that verify them
(`verify_dedupe_blocking.py`, `verify_search_matching.py`), and the reproduction attempt logs
including failed ones.

A study auditing reproducibility that is not itself reproducible has no standing. This is
non-negotiable and should be stated as such in the manuscript.
