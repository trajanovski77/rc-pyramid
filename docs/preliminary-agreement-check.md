# Preliminary agreement check: packet and reporting protocol

**Status:** EXECUTED 2026-08-28 by two independent human coders (Coder A and Coder B); completed files and computed statistics in `data/screening/dryrun/pilot/`.
Results below; reported in manuscript §7.4. **The pre-registered pilot has since been run and
passed** (2026-09-05); it is a separate exercise on a separate sample and is reported in
manuscript §7.5 and `data/screening/pilot/`.

**On the labels.** The two coders are identified throughout the released record as Coder A and
Coder B and are not named. Both are authors of the manuscript, and which author did which
coding is not published. The same two labels denote the same two people in the pilot record,
so the two checks can be compared coder-for-coder.
**Origin:** Internal review of 2026-08-20 identified taxonomy validation as the submission's
binding weakness and proposed a reduced two-coder trial as the cheapest honest remedy.

## What this is, and what it is not

A reduced-scale two-coder classification trial whose results may be reported in the
manuscript **only** under the explicit framing: *a preliminary agreement check ahead of the
pre-registered pilot (Section 6.1), not the pre-registered pilot itself*. It does not freeze
the taxonomy, does not satisfy the registration gate, and does not replace the 40-record
pilot with its κ ≥ 0.70 / ≤5% unassignable pass condition.

**Non-negotiable integrity rules:**

1. Both coders are humans, independent, and do not discuss records before their files are
   merged. Agreement between two readers who are not independent measures self-consistency,
   not codebook clarity, and would void the statistic.
2. Kappa is computed on raw decisions before any reconciliation.
3. No value derived from this check is entered into the manuscript before both coder files
   exist and the computation is reproducible from them.
4. The records used are discarded from later corpus statistics, exactly as protocol.md §7
   requires for the pilot, and for the same reason.

## Recommendation: run the full 40-record pilot instead, if at all possible

The incremental coder effort between 18 and 40 records is roughly one additional afternoon
per coder, and the full pilot is what the pre-registration specifies, what the internal
reviews explicitly request, and what permits the taxonomy freeze and OSF registration. A
reduced check spends 18 records and two coders' attention to buy a number the paper must
immediately qualify; the full pilot buys the number the paper actually needs. The reduced
option exists for the case where coder time genuinely cannot cover 40 records before the
submission deadline.

Either way, the near-duplicate adjudication (106 pairs) should be completed first so the
sample is drawn from the final corpus; `screen.py` enforces this and
`--allow-unadjudicated` exists only for dry runs.

## Generating the packet

Full pilot (preferred), after adjudication:

```bash
python3 scripts/screen.py pilot --coders <A> <B> --n 40 --min-physical 5 --seed 20260820
```

Reduced preliminary check (fallback), after adjudication:

```bash
python3 scripts/screen.py pilot --coders <A> <B> --n 18 --min-physical 4 --seed 20260820
```

Use the coders' real initials. Do not reuse the 2026-08-13 dry-run files in
`data/screening/dryrun/pilot/`; they are labelled NOT FOR CODING and were generated before
adjudication.

## What each coder does

Each coder receives their own CSV (`pilot_<initials>.csv`), in their own random order,
containing only `record_id`, `no_abstract`, `title`, `abstract` and the empty columns to
fill. `tools/pilot_coder.html` can load and export the CSV in a browser, but **it predates
deviations D21 and D22 and does not show `eligible` or `family_symmetric`**; until it is
updated, edit the CSV directly. For every record, using
`docs/taxonomy-v1.0.md` §1-§11 and only the title and abstract provided:

- `eligible`: `yes` or `no`, on every record, applying `protocol.md` §4.2. Mark `no` for a
  review, survey, tutorial or editorial (R8), a record reporting no quantitative result, a
  record that is not a reservoir system, or a journal issue cover feature (R9: repeats an
  article's title, reads as a cover blurb, sometimes carries an issue tag such as
  "(Adv. Sci. 3/2024)"). Say which in the reason. This is a judgement **separate from**
  classification, and it is the basis the unassignable gate is now computed on (D21).
- `family`: `F1`, `F2`, `F3`, `F4`, or `unassignable`. Apply the §2 procedure in order and
  stop at the first decisive step; never shortcut from the substrate (a photonic paper is
  not automatically F2, a memristor paper not automatically F1) and never from nomenclature
  (R7: a bare "reservoir computing" with no stated mechanism is `unassignable`, never F1 by
  default). `unassignable` is a valid answer, not a failure. Record a family on every row,
  including a row you marked ineligible, where `unassignable` is the correct value: the
  §2 procedure never ran, and `pilot-kappa` refuses a file with an empty category.
- `family_symmetric`: where a system genuinely combines two mechanisms and the report does
  not establish which dominates, write the pair in ascending order (`F1xF2`) and **leave
  `family` empty** (D18/D22). Do not force a primary family the text will not support.
- `subclass`: e.g. `F2.1`, only where determinable from the abstract; it must belong to
  the assigned family. Leave blank rather than guess. F1 is now **Addressable-Node
  Reservoirs** and carries a subclass F1.6 for uncoupled dynamic nodes (D19, R6).
- `hybrid`: blank, or the SECONDARY family code (e.g. `F1` on a record whose primary is
  `F2`) where one mechanism does dominate and another is present.
- `reason`: free text, required on **every** row. This is not bookkeeping: the 2026-08-28
  check's one substantive finding came out of tabulating these, not out of kappa. If
  something in the instrument feels wrong while you are coding, write that in the reason
  rather than working around it — R7, R8 and R9 all exist because a coder did.
- `minutes`: optional wall-clock time for the record. Never enters an agreement statistic.

Coders read §1-§11 of the taxonomy before starting and record their reading time. §11
carries the edge-case rulings and is load-bearing; a file this document previously sent
coders to §1-§9, which is the efficiency-boundary section. The worked examples in
manuscript Section 7.3 may be read as training material; none of those twelve systems may
be replaced into the sample. Do not open the papers and do not search the web: the
instrument under test is the codebook applied to a title and abstract. `screen.py`
validates the vocabulary on read and refuses a file it cannot interpret.

## Computing the report (after BOTH files are complete, before any discussion)

```bash
python3 scripts/screen.py pilot-kappa --a data/screening/pilot/pilot_<A>.csv \
                                      --b data/screening/pilot/pilot_<B>.csv
```

This emits the full protocol.md §7 reporting set from the raw files: raw family agreement,
Cohen's κ with its approximate 95% CI, Gwet's AC1 over the five-category vocabulary, exact
subclass agreement with its base, per-coder unassignable/hybrid/reason rates, the coder
confusion matrix, a `pilot_disagreements.csv` for the reconciliation record (fill
`deciding_text` and `reconciled_rule` per row during the post-hoc discussion), a
`pilot_agreement.json` summary, and the two gate verdicts. The command was written and
selftested before any coding occurred.

## Reporting template (fill only from the two coder files)

| Quantity | Value |
|---|---|
| n records, coders | |
| Raw percentage agreement, family level | |
| Cohen's κ, family level (and 95% CI if n permits) | |
| Exact subclass agreement | |
| Unassignable, coder A / coder B | |
| Hybrid assignments, coder A / coder B | |
| Disagreements: record id, both assignments, deciding text | |

Report Gwet's AC1 alongside κ as a sensitivity statistic (internal review 1's suggestion:
κ behaves counterintuitively under uneven family prevalence, which this corpus likely has).

## Where the results go in the manuscript

A new short subsection at the end of Section 7 ("Preliminary agreement check"), opening
with: "As a preliminary check ahead of the pre-registered pilot (Section 6.1), two
independent coders classified N records..." and reporting the table above plus a
disagreement discussion. Section 6.1, Section 9 (Limitations), and the Conclusion keep
their statements that the pre-registered pilot has not run. If the full 40-record pilot is
run instead, it is reported as the pilot, the taxonomy freeze decision follows protocol.md
§7, and the registration path opens.


## Results, 2026-08-28

Contrary to the packet instruction above, the delivered files used the 2026-08-13 dry-run
sample (n = 40, seed 20260813, drawn before the near-duplicate adjudication). Checked and
disclosed rather than concealed: two sampled records (RC-1082, RC-3677) sit in flagged
near-duplicate pairs, but neither pair has both members in the sample, so no work was coded
twice. Coder files arrived in different orders with zero verbatim-shared reasons; every
record carries a reason from both coders.

Computed with `python3 scripts/screen.py pilot-kappa` on the raw files, before any
discussion (outputs `pilot_agreement.json`, `pilot_disagreements.csv`):

| Quantity | Value |
|---|---|
| n records, coders | 40; Coder A and Coder B |
| Raw percentage agreement, family level | 95.0% |
| Cohen's kappa, family level (95% CI) | 0.92 (approx. 0.82 to 1.00) |
| Gwet's AC1 | 0.94 |
| Exact subclass agreement | 21/21 |
| Unassignable, coder A / coder B | 10 (25.0%) / 12 (30.0%) |
| Hybrid assignments, A / B | 0 / 0 |
| Family disagreements | 2, both family-versus-unassignable; 0 between assigned families |

Reading: among the 28 records both coders assigned to a family, agreement was 28/28 at
family level and 21/21 where both committed to a subclass, so the assignment procedure
discriminated cleanly wherever the abstract described the state-generating system. The
unassignable rate, however, is five to six times the pilot criterion (<=5%). The ten mutual
unassignables decompose as: two title-only records; three abstracts naming reservoir
computing without describing the system; and five records both coders independently judged
unlikely to satisfy eligibility at all (a review, a control-theory paper listing ESNs among
admissible model classes, a non-reservoir forecasting method, two single-device
characterisation studies). The binding constraint is therefore prior screening, not the
family boundaries: the sample came from the unscreened candidate corpus, and the pilot's
unassignable criterion was implicitly calibrated for eligible records.

**Decision taken 2026-09-05: option (b), with both rates reported.** The options were
(a) run the official pilot as specified and accept that the unassignable gate partly measures
screening; (b) add an explicit screen-out step and apply the <=5% gate to records the coders
deem eligible; (c) code the official pilot from full text. Option (b) is adopted, logged as
deviation **D21**, and made before the pilot was drawn.

The reasoning, so it can be argued with. The gate exists to detect an instrument that cannot
classify; this check established that none of the 25-30% was that, because no record was
unassignable on the ground that two families were both defensible. Applying an instrument
gate to records `protocol.md` §4.2 removes upstream, on which the §2 procedure never runs, is
a category error. Option (c) was rejected as changing what is being tested: the taxonomy
claims to classify from a paper-level description, and moving the pilot to full text would
validate a different instrument from the one the manuscript describes, at several times the
coder cost. **Both rates are reported in every case**, because publishing only the narrower
one after a check exceeded the criterion would be moving a goalpost rather than correcting a
basis, and because the all-records rate is what makes the pilot comparable with this check.
Cohen's kappa is unchanged and still computed over every sampled record.

The two disagreements are the evidence that this narrows the gate without emptying it:
RC-3293 is an eligibility artefact that a screen-out removes, and **RC-1648 survives an
eligibility screen and is still unassignable**. Nobody should expect the eligible-only rate
to be zero.

## Reconciliation and the D18/D19 re-read, 2026-09-05

Both are coder work on the completed check, done after the round-4 instrument changes and
recorded here because neither alters a statistic.

**Reconciliation: complete, and a joint record.** Coder A filled `deciding_text` and
`reconciled_rule` for both rows of `pilot_disagreements.csv`, both resolving against her own
call and adopting Coder B's; he read the deciding texts against the abstracts and
countersigned both on 2026-09-05. The countersign was not a formality, which is the point of
requiring one: he checked each deciding text's quotations and term counts against the source
and **found an error in one of them**. Coder A's RC-3293 deciding text called its quoted Japanese
sentence the final sentence of the abstract; it is the penultimate one, and the actual final
sentence carries a further review-register marker (議論する, "we discuss"), so the correction
strengthens the not-primary reading rather than weakening it. The verbatim-quotation and
term-occurrence checks behind the countersign were performed mechanically, with the reading
and the agreement the coders' own.

Two candidate §11 rulings came out of it and **both were accepted on 2026-09-05** and
appended to `taxonomy-v1.0.md` §11 as rulings **R7** and **R8**. Appending rulings before the
freeze is explicitly permitted by the change policy, both follow from rules the codebook
already states rather than adding new ones, and both bear on exactly the cases that produced
this check's only two disagreements, so having them in force before the pilot is better than
rediscovering them during it:

- **RC-1648.** A bare "reservoir computing" or "traditional reservoir computing", with no
  stated state-generation mechanism, is unassignable and never F1 by default. An NG-RC (F3)
  paper contrasts itself with "traditional reservoir computing" in the same words, so the
  phrase does not discriminate F1 from F3. Nomenclature alone never decides a family, on the
  same grounds that substrate alone never does.
- **RC-3293.** Where a review, survey, tutorial or commentary reaches a classification
  packet, code the record, never the systems the review describes, however determinate they
  are. Coder A had classified the systems inside the review, which is a unit-of-analysis
  error against `codebook.md`'s stated unit.

A second instrument gap sits beside the open decision and must be settled with it. D18
tells a coder who cannot establish dominance to leave `family` empty and record a symmetric
`F1xF2` label in a `family_symmetric` field. That field is not in the pilot packet and not in
`codebook.md`, and `pilot-kappa` rejects any file with an empty `family`, so the instruction
is currently unexecutable. Deciding how to carry it is not mechanical: a symmetric label can
be a sixth category in the agreement vocabulary, a record excluded from the statistic, or a
disagreement against any primary assignment, and the three compute different kappas over
different denominators. Settle it before the packet goes out; details in `deviations.md`.

RC-3293 also exposes an instrument gap that bears directly on the open decision above: the
pilot vocabulary (F1--F4, `unassignable`) cannot express `not-primary`, so an eligibility
exclusion and a genuine classification failure are recorded identically. The two records
split on this, which is the useful part: RC-3293 is an eligibility artefact that option (b)
would remove, while **RC-1648 would survive an eligibility screen and still be
unassignable**. Option (b) therefore shrinks the unassignable rate without taking it to zero.

A third finding is procedural and belongs with them. RC-1648's countersign records that
"delay" occurs once in the record, inside "stochastic delay differential equations", which
names a target system and not a reservoir loop, so a later reader grepping for the term should
not read the deciding text as contradicted. That is the right instinct about a shipping
artefact and it is the sort of note the reconciliation record exists to carry.

**AC1 and the widened vocabulary, recorded so a re-run does not look like an error.** The
figures in the table above were computed on the five-category vocabulary in force on
2026-08-28. Deviation D22 added `hybrid-symmetric` as a sixth category for the pilot, and
Gwet's AC1 divides its chance term by `K-1`, so re-running `pilot-kappa` on these same coder
files today returns AC1 **0.9424** rather than the **0.9401** recorded here. Both round to
0.94, which is how the manuscript reports it, so no published figure moves; Cohen's kappa and
Krippendorff's alpha do not move at all, because they use only the observed marginals. The
instrument changed, not the data.

**The D18/D19 re-read found one live record.** The hybrid change (D18) is inert: both coders
recorded zero hybrids. The F1 rename and the new subclass F1.6 (D19) have one candidate,
RC-5476, which is not re-coded and is an open author decision. The full check, the reasons
for holding, and the parallel-ensemble reading that may make this a subclass gap rather than
a missing assignment are recorded in `deviations.md` under "Completion of D19's impact
assessment". No agreement statistic moves.
