# Validation Study 2: targeted reliability of F3, F4 and the family boundaries

**Status:** Fixed at tag `vs2-protocol-v1` (2026-10-25), written 2026-10-24 for the IEEE Access
resubmission and revised the same day after a methods critique (Appendix C). Not run: the
frame was built and the allocation computed at the tag, and no record had been drawn. From
that commit on, any change is a numbered deviation in `docs/deviations.md`; the departures
from the pilot's procedure are deviation D34. Decisions recorded at the tag: the full design
of 160 records (project decision D1), a full-text pass on every record (D8) and the
coordinator (D9, §4.2). The coders are named before training begins (D2); the rule of §4.1
binds whoever they are. It is pre-specified and time-stamped by that commit; it is **not**
registered, and it is not described as preregistration anywhere.

**Why it exists.** The pilot of `protocol.md` §7 passed (kappa 0.954; 3.2% unassignable) on 40
records drawn at random, and every assigned record fell in F1 or F2. Both reviewers of the IEEE
Access submission (Access-2026-46897) pointed out that the result therefore says nothing about
F3, F4 or the boundaries around them. A random draw cannot fix that at any affordable size: if F3
or F4 makes up about 2% of the corpus, a random 160 records contains about 3 of it, and 30 would
need about 1,500 records. This study enriches the sample for those families instead, by rules
fixed in advance and applied to bibliographic text, never to a family judgement.

All computation is in `scripts/validation.py` (`frame`, `draw`, `stats`, `simulate`,
`selftest`); the script is authoritative where this text summarizes it.

---

## 1. Question, estimand and outcomes

**Primary question.** Do two independent coders, applying `taxonomy-v1.0.md` to the full text,
assign records to F3 and to F4, and separate those families from the others, reliably enough to
support the framework's use on them?

**Estimand.** The primary target is reliability **under the enriched allocation of §3.3**: the
agreement two coders reach on a sample with this mix of strata. Agreement coefficients depend on
the mix, so the primary results are not corpus-level reliability, and the manuscript says so.
Design-weighted estimates for the frame (§5.3) are secondary and are the only basis for any
statement about the frame as a whole. The frame itself is a held-out set (§3.1): claims do not
extend to records outside it.

**Primary outcomes, per family j in F1-F4.** From the binary table of §5.1 (both positive *a*,
coder A only *b*, coder B only *c*, neither *d*): positive specific agreement
PSA_j = 2a / (2a + b + c), and Krippendorff's alpha and Cohen's kappa on the j-versus-not-j
coding, each with a 95% interval. All four cells, both coders' positive counts and the
union-positive count u_j = a + b + c are reported with them.

**Secondary outcomes.** Overall kappa, Gwet's AC1 and alpha under three label conventions
(§5.2); the confusion matrix with conditional probabilities and pairwise mix-up rates with their
denominators; exact agreement on symmetric pairs; eligibility agreement; the unassignable rate;
per-stratum agreement; abstract-pass agreement; design-weighted estimates; and, if the add-on of
§4.4 is coded, agreement on evidence level and on the kind of counted state unit.

**Claim structure.** The study makes one confirmatory claim: **joint success**, meaning F3 and F4
each meet every criterion of §5.5 *and* both overall gates are met. A single all-must-pass claim
needs no multiplicity adjustment. A family may be described as passing on its own only together
with the joint result. Every other comparison (F1 and F2, boundary cells, strata, sensitivity
analyses) is exploratory and reported with pointwise intervals.

## 2. Instrument and procedure, fixed for the duration of coding

- `docs/taxonomy-v1.0.md` with its §11 rulings as they stand at the tagged commit (R1-R14; R14,
  adopted 2026-10-25 under deviation D32, governs arrays of time-multiplexed devices), and `docs/codebook.md`
  §0-§3. The instrument is **locked** for the coding run: no ruling is issued, no definition
  clarified and no coder instruction changed between the draw and the computation of the
  statistics. A problem a coder finds is written in the record's reason field and handled after
  the statistics (§7). Rulings made later are versioned separately and never applied to this
  sample.
- **Precedence, stated before coding.** Where a §11 ruling and the literal §2 cascade differ,
  the ruling governs. In particular R13 overrides §2 step 2's wording on propagation delay: a
  single element sampled at many points within an input interval is F2.1 whatever supplies its
  memory.
- **Two passes, both recorded, full text for every record.** Pass 1 is an abstract-only call,
  recorded in `family_abstract`. Pass 2 is a full-text coding of **every** record, recorded in
  `family` and the other fields; it is the basis of every primary statistic. This departs from
  the pilot's procedure (deviation D25), where only records the abstract left unassignable were
  read in full. Under D25 a confident abstract call was never checked, so a shared abstract-level
  mistake stayed invisible and two coders could judge one record from different information. The
  departure is deviation D34. Abstract-pass agreement is reported as a
  secondary result, comparable with the pilot's.
- Eligibility (`protocol.md` §4.1-§4.2) is recorded separately in `eligible`, as in the pilot
  (D21).

## 3. Frame, strata and draw

### 3.1 Frame

The frame is fixed at the tagged commit, which records the SHA-256 of every input
(`validation.py frame` writes them to `frame.json`, and `draw` refuses to run if the corpus has
changed since). It consists of the frozen corpus `data/screening/corpus_deduped.csv` and, **only
if** at the tag its near-duplicate adjudication is complete, the supplementary candidates
`data/screening/corpus_supplementary.csv` (search-strategy §2.6). Otherwise the frozen corpus
alone. A record enters the pool when it satisfies all of:

1. not a duplicate (`dup_of` empty);
2. openly retrievable (`is_oa = 1`, deviation D6);
3. not a publication object `protocol.md` §4.2 lists as outside §4.1: dissertation, book,
   conference abstract, dataset, software, report, erratum, retraction, peer review, paratext,
   reference entry. Bibliographic type is not eligibility, so types §4.2 does not list (review,
   editorial, other, supplementary materials) **stay in the pool** and are judged on their
   content by the coders;
4. not one of the records coded in the preliminary check, pilot attempt 1 or pilot attempt 2
   (`record_ids` in the three `pilot_sample.json` files), and not another version of one of
   them: a record sharing a DOI, arXiv id, OpenAlex id or normalized title with a piloted record
   is excluded too;
5. not a system the manuscript uses as a worked example (Tables 6 and 9 and the two device rows
   added for Reviewer 1 point 4), matched on DOI, arXiv id or normalized title
   (`WORKED_EXAMPLES` in the script).

Every excluded id is listed by reason in `frame.json` and the counts are reported. **At the tag
(2026-10-25)** the supplementary candidates' near-duplicate adjudication was complete (11 pairs,
6 same and 5 different, signed off by an author), so the frame is the frozen corpus plus
`corpus_supplementary.csv`, and the pool is **3,699** records: 52 duplicates, 3,230 closed, 237
excluded publication objects, 117 piloted records and 5 worked examples were removed. On the
frozen corpus alone (2026-10-24) it had been 3,221. Groups
of records from one laboratory or project are not modelled as clusters; this is stated as a
limitation.

### 3.2 Strata

Each pool record goes to the first stratum whose rule its NFKC-normalized title-plus-abstract
text matches, in the order **SB, S3, S4a, S4b, S4c, S4d, S4e, S3T, S0**. Rules are
case-insensitive regular expressions (Appendix A, `STRATA` and `S4_SUB` in the script). They are
proxies for where F3, F4 and boundary cases are likely to be, not family assignments. Coders
never see them, and no record is moved between strata by hand for any reason.

| Stratum | Purpose | Rule, in words |
|---|---|---|
| **SB** boundary | records likely to sit on a family boundary | medium term AND delay or time-multiplexing term (F2-F4); medium term AND array, crossbar, oscillator or SLM term (F1-F4); echo state network AND explicit-feature term (F1-F3); array term AND delay term (F1-F2) |
| **S3** explicit feature | F3 candidates | next-generation reservoir computing, NG-RC, nonlinear vector autoregression, NVAR |
| **S4a-S4e** distributed medium | F4 candidates | S4a material networks; S4b wave, field and spin media; S4c mechanical and morphological; S4d biological; S4e fluidic, chemical, lattice and other media. A record matching several goes to the first |
| **S3T** wider explicit feature | further F3 candidates | the vocabulary of taxonomy §5's subclasses: extreme learning machine, random features and projections, polynomial features, Volterra series, time-delay embedding (F3.2); Legendre, Chebyshev and other orthogonal bases (F3.3); Kolmogorov-Arnold constructions (F3.4) |
| **S0** residual | everything else | no rule matched; catches F3 and F4 records the rules miss |

The order is an allocation choice. SB comes first because boundary records are the scarcest
thing the study needs. One consequence is that an F3 or F4 record whose abstract mentions a
comparator architecture is sampled at SB's rate rather than S3's or S4's; the weights of §5.3
correct for that, and it changes nothing for the coders. `frame.json` reports how many pool
records each rule group matches and how many match several S4 sub-strata, so the overlap can be
inspected without any family rating.

### 3.3 Allocation and draw

Seed **20261024**. Simple random sampling without replacement within each stratum, by
`random.Random(f"{seed}:{stratum}").sample` over the stratum's record ids in record-number
order. Every stratum receives a positive allocation, so every pool record has a positive
inclusion probability n_h / N_h.

| Stratum | N_h at the tag (2026-10-25) | n_h, full design (adopted, D1) | N_h, corpus only (2026-10-24) | Reduced design n_h (not used) |
|---|---:|---:|---:|---:|
| SB | 68 | 30 | 60 | 15 |
| S3 | 47 | 47 (census) | 46 | 46 (census) |
| S4a / S4b / S4c / S4d / S4e | 126 / 90 / 53 / 21 / 58 | 12 each | 99 / 75 / 48 / 20 / 51 | 5 each |
| S3T | 96 | 10 | 89 | 6 |
| S0 | 3,140 | 13 | 2,733 | 8 |
| **Total** | **3,699** | **160** | **3,221** | **100** |

The allocation fixes 47 for S3. At the tag S3 holds exactly 47, so it is taken whole with no
shortfall and S3T receives its base allocation of 10 (on the corpus-only frame S3 held 46 and the
one-record shortfall moved to S3T). **Shortfall rules**, all deterministic: a stratum smaller than its allocation is taken
whole; an S3 shortfall goes to S3T; an S3T or SB shortfall goes to S0; an S4 sub-stratum's
shortfall goes, one record at a time, to the S4 sub-stratum with the most unsampled records, ties
broken by precedence order. N_h will change if the supplementary candidates join the frame; the
allocation and rules do not, and the tag records the realised N_h and n_h.

`validation.py draw` writes the sample with each record's stratum, N_h, n_h, inclusion
probability and weight; two coder packets in independently shuffled orders; and the
coordinator's retrieval log (§4.2). It refuses to draw twice.

**The full design (160 records) was chosen by the authors (project decision D1, 2026-10-25)** and
is recorded in the tagged commit, before the draw. The simulation of §3.4 was run on the
corpus-only sizes; the realised allocation differs from them only in S3 (47, not 46) and S3T
(10, not 11).

### 3.4 Is the design adequate? A simulation, not an assertion

Thirty union-positive records give no fixed precision guarantee by themselves, so
`validation.py simulate` runs the complete design, including the bootstrap and the verdict
rules of §5.5, under stated assumptions. Category yields per stratum (central scenario) are
written in the script (`YIELDS`); the F3 and F4 yields are scaled by 0.6 (pessimistic), 1.0 and
1.3, and each coder independently miscodes a record with probability 0.05, 0.10 or 0.15, the
wrong code drawn uniformly from the other categories. These yields are guesses made before any
coding, not estimates, and the table shows how the conclusion depends on them.

Probability over 400 simulated studies (bootstrap B = 400 inside each) that a family reaches the
information condition ("info") and that it passes; "both" is joint success on the two families.

**Full design (160 records).**

| F3/F4 yield | Coder error | F3 info | F3 pass | F4 info | F4 pass | Both pass |
|---|---:|---:|---:|---:|---:|---:|
| pessimistic (x0.6) | 0.05 | 0.01 | 0.01 | 0.04 | 0.04 | 0.00 |
| pessimistic (x0.6) | 0.10 | 0.04 | 0.01 | 0.13 | 0.01 | 0.00 |
| pessimistic (x0.6) | 0.15 | 0.10 | 0.00 | 0.26 | 0.00 | 0.00 |
| central | 0.05 | 0.69 | 0.66 | 0.95 | 0.91 | 0.60 |
| central | 0.10 | 0.82 | 0.37 | 0.95 | 0.47 | 0.19 |
| central | 0.15 | 0.92 | 0.06 | 0.98 | 0.07 | 0.01 |
| optimistic (x1.3) | 0.05 | 0.99 | 0.98 | 1.00 | 0.99 | 0.97 |
| optimistic (x1.3) | 0.10 | 1.00 | 0.57 | 1.00 | 0.59 | 0.36 |
| optimistic (x1.3) | 0.15 | 1.00 | 0.08 | 1.00 | 0.09 | 0.01 |

**Reduced design (100 records, information condition 20).**

| F3/F4 yield | Coder error | F3 info | F3 pass | F4 info | F4 pass | Both pass |
|---|---:|---:|---:|---:|---:|---:|
| pessimistic (x0.6) | 0.05 | 0.37 | 0.30 | 0.00 | 0.00 | 0.00 |
| central | 0.05 | 1.00 | 0.93 | 0.16 | 0.12 | 0.11 |
| central | 0.10 | 1.00 | 0.53 | 0.27 | 0.09 | 0.06 |
| optimistic (x1.3) | 0.05 | 1.00 | 0.95 | 0.60 | 0.54 | 0.52 |

The full reduced-design grid is reproduced by `validation.py simulate --design reduced`. Three things follow, and
they are stated here so that no result can be explained afterwards by the design.

- **The reduced design cannot test F4.** With five records per S4 sub-stratum, F4 reaches 20
  union-positive records in 16% of simulated studies at central yields. The full design is
  needed for a two-family claim.
- **F3 is limited by the frame, not the allocation.** S3 is taken whole (46 records) and
  still supplies only about 25 expected F3 records at central yields. Reaching 30 therefore
  depends on F3 records turning up in SB, S3T and S0. "Insufficient information" for F3 is a
  realistic outcome, and it will be reported as that and not as a pass.
- **The criteria are demanding by design.** Pilot 2's agreement (raw agreement 0.975, one
  family disagreement in 40) corresponds to a per-coder error of about 0.01-0.02, on F1 and F2.
  F3 and F4 are harder, so 0.05 is taken as the central case; there the full design passes both
  families 60% of the time at central yields, and at 0.10 only 19%. The study can fail, and a
  pass carries information for that reason.

### 3.5 No outcome-dependent top-up

An earlier draft drew further batches when the number of agreed F3 or F4 records fell short.
That made the sample size depend on observed agreement, which neither the weights nor the
bootstrap account for, so it is removed. The fixed initial sample is the only basis of every
confirmatory result. If the authors later code further records, these are an exploratory
supplement, reported separately, and cannot change the verdict of §5.5.

## 4. Coding

### 4.1 Coders and their preparation

Two coders working independently, at least one of whom took no part in designing the taxonomy
or writing its rulings: designers may agree because they share the intent (Krippendorff 2019).
Before starting, each coder records their field and years of experience, their familiarity with
reservoir computing, and any prior exposure to the taxonomy, the pilot or its coder files. Both
read `taxonomy-v1.0.md` §1-§11 and `codebook.md` §0-§3 and record the reading time. Both then
code the same **ten training records** drawn from the piloted records (excluded from the frame,
§3.1(4)), see the pilot's reconciled answers, and discuss them with each other; training ends
before the packets are released. **Coding is unaided:** the coders use no automated tools to retrieve papers,
draft reasons, or make or check calls, and they retrieve nothing themselves: full texts come from
the coordinator (§4.2). Each coder signs a short attestation with their file:
coded independently, no discussion of sampled records before both files were submitted, no
automated assistance. Results generalize to coders like these working this way, and the manuscript says so.

### 4.2 Retrieval, blinding and submission

- **The coordinator (project decision D9)** is not a coder and works under the PI's
  supervision. The coordinator builds the frame, runs the draw, retrieves the full texts and
  writes the retrieval log and the two packets, makes no coding judgement, does not see either
  coder file before both are submitted, and does not communicate strata to the coders. The
  second retrieval attempt below, the publisher's page through institutional access, needs
  institutional credentials, so the PI makes it.
- **Retrieval is fixed before coding.** A coordinator who is not a coder retrieves one full text
  per sampled record, following the retrieval log `draw` writes. The sources are the open
  version first, then the publisher's page through institutional access, up to two attempts per
  record. Every attempt is logged. Both coders receive **identical** files. A record whose full
  text cannot be obtained this way is marked `retrieval-failed` in the log before coding starts.
  Coders then code it on title and abstract, give `retrieval failed` as the reason, and it is
  analysed like any other record. Nothing is retrieved, supplied or re-coded after a coder file
  has been submitted.
- This differs from the pilot. There, a full text was supplied for RC-1144 after the agreement
  result was known, and Coder A re-coded it (deviation D29's sequence). The manuscript states the
  difference.
- **Allocation masking.** Each coder receives a CSV containing only `record_id`, `no_abstract`,
  `title`, `abstract` and `doi`, the empty fill columns of the pilot packet, and the add-on
  columns if §4.4 is in use. Stratum, inclusion probability and the existence of strata are not
  shown. Orders are shuffled independently per coder. This is masking, not blinding: titles carry
  architectural clues, and the coders see them.
- **Submission.** Each coder submits once. The coordinator saves the file as submitted, and
  `validation.py stats` reads only that file and records its SHA-256. A file is accepted only if
  it holds exactly one complete row per sampled record: eligibility and a reason on every row, and
  a family or symmetric label on every eligible row. Any other file is returned for completion
  before statistics are computed. No coder sees the other's file, or any statistic, before both
  are in.

### 4.3 Vocabulary and the analytic mapping

The coder vocabulary is the pilot's (`screen.py read_pilot_file`): families F1-F4 or
`unassignable`; symmetric hybrid labels `FaxFb` in ascending order with `family` empty;
subclasses that belong to the assigned family; the secondary hybrid family; yes/no eligibility;
a reason on every row. For an ineligible record `family` may be left blank or `unassignable`.

How a code enters the statistics is fixed here (`op_label` and `families` in the script):

| Coder's record | Operational label | Positive for family j? |
|---|---|---|
| `eligible = no` | ineligible | no, for every j |
| family Fj | Fj | yes for j only |
| symmetric FaxFb | hybrid-symmetric | yes for both Fa and Fb |
| `unassignable` | unassignable | no, for every j |

Every sampled record stays in every primary analysis. Pre-specified sensitivity analyses:
(i) mutually eligible records only; (ii) a strict mapping in which only a single-family label
counts as positive; (iii) an expanded vocabulary in which each symmetric pair is its own
category; (iv) exact agreement on the pair among records both coders labelled symmetric.
Eligibility agreement is reported separately. Records dispositioned under R11 (one record, two
co-equal systems in different families) stay in every reliability statistic.

### 4.4 Optional add-on (decided before the draw)

For each record judged eligible, `evidence` (E0-E5, `taxonomy-v1.0.md` §8: the highest level the
paper's own reported method demonstrates for its headline claim) and `state_unit` (`physical`,
`virtual`, `probe` or `n/a`: the kind of unit the reported state count enumerates, ruling R4).
About 3-5 extra minutes per record. It gives the first inter-rater evidence for the evaluation
dimensions. If not adopted, the columns are absent and nothing is reported.

## 5. Statistics

Computed by `scripts/validation.py stats` on the files as submitted, before any reconciliation.

### 5.1 Per family

For each j: the cells a, b, c, d; PSA_j = 2a / (2a + b + c); binary kappa and binary
Krippendorff's alpha from the full table (never from agreed records alone); Byrt's signed
prevalence index (a - d)/n and bias index (b - c)/n; both coders' positive counts and u_j.
Sensitivity analyses (i) and (ii) of §4.3 are reported in the same table.

### 5.2 Overall and boundaries

- Kappa, AC1 and alpha under three conventions: the **pilot convention** (six categories,
  ineligible counted as unassignable, as the pilot's coders recorded it), which carries the
  overall gate; the **operational** seven-category convention of §4.3; and the **expanded**
  convention with each symmetric pair its own category.
- The confusion matrix of operational labels; P(coder B = k | coder A = j); and for every pair of
  categories the mix-up rate, reported as its numerator (records the coders split between the two
  categories) over its denominator (records where either coder used either category), with the
  F1-F3, F1-F4, F2-F4 and F3-F4 cells discussed in the text.
- The unassignable rate among records both coders judged eligible, per coder. The gate uses the
  **unadjusted** rate. An R11-adjusted rate is reported beside it as a secondary figure and never
  decides the gate.
- Per stratum: raw agreement and kappa. Abstract pass: the pilot-convention statistics on
  `family_abstract` among mutually eligible records.

### 5.3 Design-weighted (secondary)

Horvitz-Thompson weights w_h = N_h / n_h. Weighted cell totals are estimated first and the
coefficients computed from them; the coefficients are nonlinear in the totals, so the result is
a consistent plug-in estimate, not an unbiased Horvitz-Thompson estimator. Weighted alpha uses the
weighted number of pairable values in its small-sample term, so it estimates the alpha that coding
the whole frame would give. Weighted results are reported beside the unweighted ones, never in
their place. The 40-record pilot is reported separately and not pooled.

### 5.4 Intervals

- **Primary (fixed allocation).** A stratified percentile bootstrap: records are resampled with
  replacement within strata, S4 sub-strata as separate strata, each record keeping both coders'
  codes together; B = 10,000, seed 20261024. It targets the fixed-allocation superpopulation and
  is applied even to a censused stratum.
- **Weighted (finite frame).** The Rao-Wu rescaled bootstrap with finite-population correction
  (m_h = n_h - 1); a censused stratum contributes no variance.
- **Exceptional cases.** A stratum with one sampled record is merged with a fixed partner before
  resampling (`COLLAPSE` in the script). A replicate on which a statistic is undefined is
  dropped and counted. If more than 1% of replicates are undefined, the interval is reported as
  not evaluable.
- **Zero disagreement.** If a family has b = c = 0, every replicate gives alpha = 1 and the
  bootstrap interval collapses to [1, 1], which carries no information about the lower bound.
  The lower-bound criterion is then judged on a **separately labelled conditional bound**. q_U is
  the exact one-sided 95% Clopper-Pearson upper bound on the probability that a union-positive
  record is a disagreement. ceil(q_U * u_j) disagreements are placed in the observed table, split
  evenly, with prevalence held fixed, and alpha is recomputed. The bound is conditional on the
  observed prevalence, is not a design-based interval, and is reported as such. The same q_U gives
  a PSA bound of 2(1 - q_U) / (2 - q_U).
- The pilot's large-sample kappa interval is reported once more, labelled as a legacy comparison,
  because it treats the expected agreement as fixed.

### 5.5 Criteria and verdicts, fixed now

For each family j in {F3, F4}, one of three verdicts:

- **Insufficient information** if u_j < 30 (20 in the reduced design). The condition counts
  records at least one coder assigned to j, not records the coders agreed on, so poor agreement
  cannot turn a failure into "insufficient information".
- Otherwise **pass** if both:
  1. PSA_j >= 0.80 and binary alpha_j >= 0.80 (point estimates), and
  2. the lower bound of the primary 95% interval for binary alpha_j is >= 0.667 (Krippendorff's
     floor for tentative conclusions), or, under zero disagreement, the labelled conditional
     bound of §5.4 is.
- Otherwise **criterion not met**, with the criteria that failed.

**Overall gates**, the pilot's, both required: kappa >= 0.70 under the pilot convention, and an
unadjusted unassignable rate <= 5% among mutually eligible records for each coder.

**Joint success** requires both families to pass and both gates to be met. Neither "criterion
not met" nor "insufficient information" licenses a pass. What a pass shows is stated in these
terms: observed agreement above the thresholds, and evidence against alpha below 0.667. It is
not proof that alpha in any population exceeds 0.80.

### 5.6 Failure

A family that fails is reported as failing, in the manuscript and here. The remedy is a
documented revision to taxonomy v1.1 with a change log, followed by a test on **fresh** records;
the same sample is never re-coded to a better number and no record is dropped from the
calculation. Reconciliation (§7) cannot change a reported statistic.

## 6. Reporting

Manuscript §8.5 (new) reports: the frame, its exclusions and stratum sizes; the realised draw;
coder preparation and retrieval outcomes; the per-family table of §5.1 with sensitivity
analyses; the confusion matrix, conditional probabilities and mix-up rates with denominators;
the overall statistics under all three conventions; the unassignable rate; the design-weighted
estimates; the verdicts of §5.5; and what every disagreement concerned. Released files go in
`data/screening/validation2/`: frame, sample, retrieval log, both coder files as submitted, the
statistics JSON, the simulation output and the reconciliation record.

## 7. After the statistics

Disagreements (`vs2_disagreements.csv`) are reconciled by the two coders and recorded
(`deciding_text`, `reconciled_rule`); the file is never overwritten once reconciliation has
begun. Proposed edge-case rulings are listed and, if accepted, appended to `taxonomy-v1.0.md` §11
with this study as their trigger; they take effect for later coding only.

## 8. Effort

Pilot 2 took a median of 9-10 minutes per record per coder with full texts. With a full-text pass
on every record, the full design is about 27-32 hours per coder, plus 8-13 hours if the add-on
is adopted; the reduced design about 17-20 hours. Training adds about two hours, and retrieval
falls to the coordinator.

---

## Appendix A. Stratum rules

From `scripts/validation.py` at the tagged commit; the code is authoritative. Text is
`unicodedata.normalize("NFKC", title + " " + abstract)`, matched case-insensitively with
`re.search`.

| Rule | Pattern |
|---|---|
| `F3` | `(?:next[- ]generation reservoir\|\bng[- ]?rcs?\b\|nonlinear vector auto[- ]?regress\|\bnvars?\b)` |
| `F3T` | `(?:extreme learning machine\|\belms?\b\|random features?\|random fourier\|random projections?\|polynomial features?\|volterra series\|time[- ]delay embedding\|legendre\|chebyshev\|orthogonal (?:basis\|polynomial)\|kolmogorov[- ]arnold)` |
| `DELAY` | `(?:\bdelay(?:ed)?[- ](?:based\|loop\|line\|feedback\|system\|reservoir)\|time[- ]multiplex\|virtual nodes?\|single (?:dynamical \|nonlinear )?node\|delay[- ]coupled)` |
| `ARRAY` | `(?:memristor (?:array\|crossbar)\|memristive (?:array\|crossbar)\|crossbar\|coupled oscillators?\|oscillator (?:network\|array)s?\|spatial light modulator\|\bslm\b\|diffractive)` |
| `ESN` | `(?:echo[- ]state network\|\besns?\b)` |
| `EXPLICIT` | `(?:nonlinear vector auto[- ]?regress\|\bnvar\|polynomial features?\|linear (?:reservoir\|echo state)\|next[- ]generation\|explicit (?:feature\|nonlinear))` |
| `S4a` | `(?:\bnanowire\|atomic[- ]switch\|carbon nanotube\|\bcnts?\b\|nanoparticle (?:network\|array\|film)\|self[- ]assembl\|percolat\|in[- ]materi[oa]\|dopant network\|polymer network\|ionic liquid\|electrochemical (?:network\|cell))` |
| `S4b` | `(?:spin[- ]waves?\|\bmagnons?\b\|magnonic\|skyrmion\|spin ice\|\bspeckle\|scattering medi\|multimode fib(?:er\|re)\|\bacoustic wave\|surface acoustic\|ultrasound)` |
| `S4c` | `(?:soft[- ]robot\|soft body\|soft material\|tensegrity\|morphological computation\|compliant body\|origami\|mass[- ]spring\|octopus\|physical body)` |
| `S4d` | `(?:neuronal culture\|cultured neuron\|neural culture\|organoid\|in vitro neuron\|dissociated (?:cortical )?neuron\|living neuron\|bacteri\|\bfungal\|slime mou?ld\|physarum\|living (?:cells?\|tissue))` |
| `S4e` | `(?:water (?:tank\|bucket\|surface\|wave)\|fluidic\|\bbucket\b\|liquid crystal\|cellular automat\|coupled map lattice\|\bbz reaction\|belousov\|chemical reaction network\|molecular (?:system\|reservoir)\|dna (?:computing\|reservoir\|strand)\|\bgel\b)` |

MEDIUM is the union of S4a-S4e. Assignment, in order: **SB** if (MEDIUM and DELAY) or
(MEDIUM and ARRAY) or (ESN and EXPLICIT) or (ARRAY and DELAY); else **S3** if F3; else the
first of **S4a-S4e** that matches; else **S3T** if F3T; else **S0**.

## Appendix B. References for the design

Krippendorff, K. (2019) *Content Analysis* (4th ed.); Artstein and Poesio (2008) Comput.
Linguist. 34:555; Hayes and Krippendorff (2007) Commun. Methods Meas. 1:77; Donner and Eliasziw
(1992) Stat. Med. 11:1511; Cicchetti and Feinstein (1990) J. Clin. Epidemiol. 43:551; Byrt,
Bishop and Carlin (1993) J. Clin. Epidemiol. 46:423; de Vet, Mullender and Eekhout (2018)
J. Clin. Epidemiol. 96:47; Pickles, Dunn and Vazquez-Barquero (1995) Stat. Methods Med. Res.
4:73; Horvitz and Thompson (1952) J. Am. Stat. Assoc. 47:663; Rao and Wu (1988) J. Am. Stat.
Assoc. 83:231; Clopper and Pearson (1934) Biometrika 26:404; Nickerson, Varshney and Muntermann
(2013) Eur. J. Inf. Syst. 22:336; Kundisch et al. (2022) Bus. Inf. Syst. Eng. 64:421. Each to be
verified against its primary before citation in the manuscript.

## Appendix C. Changes after the methods critique (2026-10-24)

A read-only methods critique of the first draft returned fifteen points. Each was taken up as follows.

| # | Point | Change |
|---|---|---|
| 1 | S3T had zero inclusion probability | every stratum has a positive allocation (§3.3) |
| 2 | Top-ups depended on observed agreement | removed; any later batch is exploratory (§3.5) |
| 3 | Clopper-Pearson cannot stand in for an alpha interval | used only as a labelled conditional bound under zero disagreement; PSA mapping corrected (§5.4) |
| 4 | Estimand underspecified | primary target is the enriched allocation; weighted cell totals first (§1, §5.3) |
| 5 | "Consensus" named agreement selection | cells a, b, c, d and u_j defined and reported (§1, §5.1) |
| 6 | Sample size asserted, not shown | design simulation (§3.4); 1,400 claim replaced by arithmetic |
| 7 | No fixed retrieval stopping point | coordinator retrieval before coding, defined failure, no later retrieval (§4.2) |
| 8 | Two-pass procedure mixed information | full-text pass on every record; abstract pass kept as secondary (§2) |
| 9 | Labels and eligibility lacked a mapping | mapping table and four sensitivity analyses (§4.3) |
| 10 | Bootstrap target and exceptional cases | superpopulation and Rao-Wu targets, collapse, undefined replicates (§5.4) |
| 11 | Selection could not be audited | rules, precedence, order and shortfalls fixed in code and Appendix A (§3.2-§3.3) |
| 12 | Metadata exclusions redefined the population | only §4.2's listed objects dropped; alternate identifiers; IDs published (§3.1) |
| 13 | Inherited reader did not enforce the analysis | strict reader against the manifest; both passes kept (§4.2, script `read_coder`) |
| 14 | Claim structure and multiplicity | joint success defined; three verdicts (§1, §5.5) |
| 15 | Coder preparation and instrument precedence | backgrounds, training, attestation, masking wording, R13 precedence (§2, §4.1) |
