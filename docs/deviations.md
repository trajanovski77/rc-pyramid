# Deviation Log

Every departure from `protocol.md` is logged here with date, reason, and, critically, 
**whether it was made before or after seeing the affected results**. This log is published
with the manuscript.

Undisclosed deviation is the single failure mode that would invalidate this study's central
claim to rigour. A deviation honestly logged costs nothing; a deviation discovered by a
reviewer costs the paper.

## Format

| # | Date | Section | Deviation | Reason | Before/after seeing affected results | Logged by |
|---|---|---|---|---|---|---|

## Entries

Pre-registration has not occurred, so none of these are protocol deviations in the formal
sense. They are logged anyway: the point of the log is a continuous record of how the
instruments changed and why, and starting it only at registration would hide the period when
the instruments were most malleable.

| # | Date | Section | Change | Reason | Before/after results | Logged by |
|---|---|---|---|---|---|---|
| D1 | 2026-07-31 | `benchmark-thresholds.md` §3.1 | `T_triv` for NARMA-10 unset (was 0.16, grade A) | The claim "best performance achievable with no nonlinearity is NMSE = 0.16" was not present in the traced primary source (Vidamour et al., Commun. Phys. 2023). It originated in a search-engine summary. | Before. No extraction data exists. | assistant |
| D2 | 2026-07-31 | `benchmark-thresholds.md` §3.1 | Shift-register reference corrected from 0.434 to ~0.4, scope narrowed to NARMA tasks generally, demoted to grade C context and removed from the scoring rule | Primary text states "~0.4" for NARMA tasks, not "0.434" for NARMA-10. The added precision had no source. | Before. | assistant |
| D3 | 2026-07-31 | `benchmark-thresholds.md` §3.1 | `T_res` for NARMA-10 downgraded B to C | Its supporting dispersion figures (anchor 3) remain unread in primary sources. Grade C excludes it from headline claims under §2. | Before. | assistant |
| D4 | 2026-07-31 | `benchmark-thresholds.md` §5, `s5-benchmarks.md`, `references.bib` | Citation corrected: arXiv:1906.04608 is *A Unifying Framework for Information Processing in Stochastically Driven Dynamical Systems* (Kubota, Takahashi, Nakajima, v5, 2021), not *Dynamical Anatomy of NARMA10 Benchmark Task* (the v1 title, still shown by indexing sites) | Read from the primary text. | Before. | assistant |
| D5 | 2026-07-31 | `search-strategy.md` §1 | Scopus, Web of Science and IEEE Xplore replaced as primary sources by OpenAlex, arXiv, Semantic Scholar and Crossref | Subscription access not securable. Independently, an audit of reproducibility whose own search requires a paid subscription cannot be re-run by its readers, so the open sources are the better fit for the study's own standard. Known-item recall tested at 9 of 9 before adopting. | Before. No screening or extraction has run. | assistant |
| D6 | 2026-07-31 | `protocol.md` §4.1, `search-strategy.md` §1.2 | Eligibility narrowed to openly retrievable records. Corpus is the open-access subset (3,831 of 7,062 at harvest; 3,584 of 6,532 after dedup). | Full-text access for closed records is not securable, and an auditor cannot fairly assess reporting sufficiency in a paper they cannot read. Recorded as a caveat, not as a neutral scope choice. | Before. No screening has run. | assistant, on the principal investigator's decision |
| D7 | 2026-08-02 | `search-strategy.md` §5, `scripts/dedupe.py` | Five dedup changes, listed below. | The script had no reader for the primary database, so the corpus could not be built. Fixing that surfaced four related defects. | Before. No screening has run. | assistant |
| D8 | 2026-08-02 | `benchmark-thresholds.md` §3.1, §5 | **D1 reversed.** `T_triv` for NARMA-10 restored to 0.16 NMSE (= 0.4 NRMSE), grade B, relabelled a trivial-predictor ceiling rather than a linear-reservoir floor. Anchors 1 and 2 merged: they are one measurement in two metrics. | Anchor 1's *attribution* had failed, not the figure. Read from two primaries: Appeltant 2011 (NRMSE 0.4, via PMC3195233) and Vinckier 2015 (NMSE 0.16, stating the equivalence). 0.4² = 0.16. | Before. No extraction data exists. | assistant |
| D9 | 2026-08-02 | `benchmark-thresholds.md` §3.1 | **D3 reversed.** `T_res` for NARMA-10 upgraded C to B, 0.05 confirmed. | Anchor 3 verified exactly against the primary (Vinckier 2015 §4.B, N=300), with the qualifier that dispersion is over 10 repetitions of one system. | Before. | assistant |
| D10 | 2026-08-02 | `benchmark-thresholds.md` §3.5 | VPT baseline corrected from "~2.87 λt" to "~2.6 λt"; the 0.03 λt lower end removed and weakened to "well below 1 λt". | Unit error: 2.87 is model time units, not Lyapunov times, per the primary text of arXiv:2106.09780. The 0.03 figure could not be sourced. | Before. | assistant |
| D11 | 2026-08-02 | `search-strategy.md` §1, §6 | Semantic Scholar and Crossref legs executed as coverage and completeness checks. No records merged into the corpus. | Both were listed as *planned* in §1. §1 pre-specifies that additional yield is reported separately rather than merged, and it is. | Before. No screening has run. | assistant |
| D12 | 2026-08-02 | `search-strategy.md` §5.1 | Near-duplicate adjudication is **proposed automatically with human sign-off**, not performed unaided by a human coder. | 106 pairs, each resolved against Crossref/DataCite/arXiv/HAL records with the deciding evidence recorded per pair. Adjudication is a factual determination against authoritative identifiers, not a subjective coding judgement, so it does not carry the independence requirement that screening does. | Before. No screening has run. **Executed and closed 2026-09-05**: all 106 decided, 46 merged and 60 kept apart, corpus 6,532 → 6,486. Signed off by S. Trajanovski on 2026-09-05, which is the condition this entry attached. | assistant; signed off by S. Trajanovski, 2026-09-05 |
| D14 | 2026-08-02 | `paper/s3-pyramid.md` §3.2, `references.bib` | **Prior art added and the novelty claim narrowed.** Dale, Miller, Stepney and Trefzer, *A substrate-independent framework to characterize reservoir computers*, Proc. R. Soc. A 475(2226), 20180723 (2019), was absent from the bibliography. A new §3.2 positions the taxonomy against it. | The reference formerly keyed `Dale2025` carried the 2019 CHARC paper's author list attached to the 2025 Wringe et al. benchmarks paper's title and DOI: two real papers fused into one entry. Correcting the author list (D-note in `Wringe2025`) exposed that the 2019 paper had never been cited at all. | Before. No screening has run. | assistant |
| D13 | 2026-08-02 | project scope | Split into two papers. Paper 1: instruments, benchmark discrimination framework, anchor verification, registered protocol. Paper 2: the corpus audit. | The audit as scoped needs 750 to 1,100 person-hours of two-coder work. The instruments and the anchor result are complete and independently useful now, and paper 2 is stronger for citing a published instrument. | Before. No screening has run. | assistant, on the principal investigator's decision |
| D15 | 2026-08-20 | `benchmark-thresholds.md` §3.5, `references.bib`, manuscript §5.3 and §7 | **The VPT "~2.6 λt baseline" is removed; its bibliography entry was two papers fused.** The `Racca2021` entry carried Racca and Magri's names with the title and arXiv identifier of Huhn and Magri (arXiv:2106.09780, Phys. Rev. Fluids 7, 014402 (2022)). Full-text re-verification found the quoted baseline sentence in **neither** paper. The entry is corrected to the real Racca and Magri paper (Neural Networks 142, 252-268 (2021), arXiv:2103.03174) and the numeric baseline is removed from every document rather than re-attributed. | Flagged by an internal pre-submission review (2026-08-20); verified against arXiv, ar5iv full text, and Crossref. Under §5's rule an anchor with no located source is not an anchor. The D10 unit correction had been performed against a misidentified primary, so the "corrected" value was still unsourced, which is itself a reportable instance of the paper's subject. | Before. No extraction data exists. | assistant, from the internal review |
| D16 | 2026-08-27 | `benchmark-thresholds.md` §3.1, `references.bib`, manuscript abstract, §5.2, §7.2 | **D2 reversed; anchors 1 and 2 un-merged.** The Vidamour et al. (2023) shift-register value is ~0.434 NMSE, stated without citation for a NARMA-N task with autocorrelated inputs. It is the authors' own baseline for a different input distribution, not Appeltant's 0.4 NRMSE relabelled. Excluded from thresholds; the manuscript's lineage claim, Table 8, the lineage figure and the abstract example are rewritten. | Re-reading the primary (published PDF and arXiv:2206.04446) during the round-2 revision. The 2026-07-31 and 2026-08-02 passes had quoted the sentence as "~0.4"; the quotation was wrong and the relabelling inference rested on it. | Before. No extraction data exists. | assistant, during the round-2 revision |
| D17 | 2026-08-27 | `benchmark-thresholds.md` §3.6, §5; `references.bib`; manuscript §5.4, §7.2 | **Anchor 8 recovered.** The 0.014% spoken-digit error is stated in Brunner et al. (2013), the primary that Yan et al. (2024) cite for it (their ref. 58): "(0.014+0.051/-0.014)%" at one operating point, "one misclassification per ~7,000 digits". The 2026-07-31 disposition "not locatable in any primary source" was a false negative. Retained as a saturation illustration with its interval; no threshold assigned. | The secondary source's reference had not been followed; the primary was already in this project's bibliography as a delay-reservoir exemplar. | Before. | assistant, during the round-2 revision |
| D18 | 2026-09-05 | `taxonomy-v1.0.md` §2.1, manuscript §3.2 | **Hybrid primary-family rule replaced.** The primary family was assigned to "the component that generates most of the state dimension". It is now the component whose mechanism dominates state generation, judged from the reported memory mechanism and never from a count: the dominant component is the one whose removal would eliminate input-history dependence. Where the report does not establish dominance, no primary family is assigned and the record carries a symmetric label `F1×F2` in a new `family_symmetric` field, with `family` empty and `family_ambiguous = true`. | The superseded rule ranked two components by their reported state dimensions, a comparison `taxonomy-v1.0.md` §4 and §6 and manuscript §2.2 all state is invalid across families. The instrument contradicted the paper's own central argument. Raised by referees in three consecutive rounds and deferred twice to the pilot; the third report made the contradiction explicit and it is cheaper to fix before the gate than to freeze it. | Before. No record has been coded under either rule: the 2026-08-28 preliminary check recorded zero hybrids for both coders, so nothing requires re-coding. | assistant, from the 2026-09-05 referee report |
| D19 | 2026-09-05 | `taxonomy-v1.0.md` §2.2, §3, §11; manuscript §2.2, §3.2, §3.3.1, §7.3, Table 13; `figures.py` | **F1 renamed from "Recurrent-Network" to "Addressable-Node Reservoirs"; definition broadened; subclass F1.6 (uncoupled dynamic nodes) added; edge-case ruling R6 issued.** The family definition now reads: individually addressable units with a specified interconnection structure, memory arising from coupling among them, from their own internal dynamics, or both. The Du et al. (2017) worked example moves from F1.1 to F1.6. | The §2 step-3 discriminator is addressability and a specified structure, not recurrence, and the dynamic-memristor worked example satisfies the discriminator while containing no recurrent connection at all: its devices "function independently in the reservoir". The family name asserted a mechanism the family did not require, and manuscript §7.3 had recorded the tension since 2026-08-27 and deferred it to the pilot. A name that misdescribes its own members is an instrument defect, not a labelling preference. | Before. Affects one worked-example row, which is a designer demonstration rather than coded data. No screening or extraction record exists. *This cell was incomplete as first written: the preliminary-check coder files are neither a screening nor an extraction record, and it did not say whether they had been checked. They have been; see the completion note below (2026-09-05).* | assistant, from the 2026-09-05 referee report |
| D20 | 2026-09-05 | `taxonomy-v1.0.md` §10 test 2; `protocol.md` §9; `scripts/analyses.py`; manuscript §6.1, §6.4, §8.3 | **Two pre-specified analyses added and falsification test 2 given a quantitative form.** A6 computes the family × substrate association (bias-corrected Cramér's V, normalized mutual information, both conditional entropies) with pre-committed thresholds: the classification fails if V ≥ 0.70 **and** NMI ≥ 0.70. A7 compares reported state dimension against effective state dimension, computing the participation ratio D_PR = (Σλ)²/Σλ² where a source supplies a spectrum. Codebook gains `eff_dim_reported`, `eff_dim_value`, `eff_dim_method`, `eff_dim_basis`. | The ≥3-substrates heuristic detects a family confined to one material but does not measure the strength of the association, which is what the framework's claim concerns; and the effective-dimension argument of §2.2 was theoretical with no analysis that would ever measure it. Both were requested across three review rounds and twice recorded as "recommended for the analysis plan before registration" without being added. | Before. Neither analysis can run: both refuse without extraction data, which does not exist. Thresholds and decision rules are fixed in released code before any classification data exists, which is the point of adding them now rather than later. | assistant, from the 2026-09-05 referee report |

| D21 | 2026-09-05 | `protocol.md` §7; `taxonomy-v1.0.md` §10 test 3; `scripts/screen.py` | **The pilot's unassignable criterion is applied to eligible records, and both rates are reported.** The 5% gate is now computed over records **both** coders judged eligible under protocol §4.2; the all-records rate is reported beside it and is the figure comparable with the 2026-08-28 preliminary check. Neither replaces the other. The pilot packet gains an `eligible` column (`yes`/`no`) so the coders make that judgement explicitly and separately from classification. | The preliminary check returned 25%/30% unassignable against the 5% criterion, and decomposing the coders' free-text reasons showed **none** of it was the instrument failing to discriminate: no record was unassignable because two families were both defensible. Five of ten and six of twelve were records protocol §4.2 excludes upstream, on which the §2 procedure never runs. A gate meant to detect an unusable instrument was measuring the composition of an unscreened corpus. The reconciliation sharpened this: RC-3293, a review, is an eligibility artefact that a screen-out removes, while RC-1648 survives an eligibility screen and is still unassignable, so the revised basis narrows the gate without making it vacuous. The packet change also closes an instrument gap the reconciliation exposed, that the F1--F4/`unassignable` vocabulary could not express `not-primary`, so an eligibility exclusion and a genuine classification failure were recorded identically. | Before. The pre-registered pilot has not been drawn and no record has been coded under the revised criterion. The preliminary check is not the pilot and its published figures are unchanged. | assistant, on the principal investigator's decision |
| D22 | 2026-09-05 | `taxonomy-v1.0.md` §2.1; `codebook.md` §2; `scripts/screen.py` | **The symmetric hybrid label is carried into the pilot statistic as one category.** The packet gains `family_symmetric`; a record carrying it leaves `family` empty, as §2.1 requires. In the agreement statistic every symmetric label maps to a single category `hybrid-symmetric`, making the vocabulary six categories, and **which** pair a coder named is reported separately with its base, exactly as subclass agreement is. | D18 created the field and reached neither the extraction schema nor the pilot packet, and `pilot-kappa` rejected a file whose `family` was empty, so a coder following D18 exactly would have blocked the computation with nowhere to record the result. Of the three ways to carry it, excluding such records repeats the error protocol §7 already rejects for `unassignable`, namely reporting reliability for the easy half of the task; scoring them as a disagreement against any primary assignment is an ad-hoc rule rather than a category; and one category per pair would fragment the vocabulary into six sparse cells and depress kappa by construction. One category, with the pair reported beside it, is consistent with how `unassignable` and subclass are already handled. | Before. No record has been coded under either the old or the new treatment; the preliminary check recorded zero hybrids. | assistant, on the principal investigator's decision |

| D23 | 2026-09-05 | `protocol.md` §7 | **The first pilot attempt was coded under a coding arrangement that was subsequently judged not to establish independent coding, and the arrangement was withdrawn.** Recorded because the attempt it governed is reported as a failure under D24. | Principal-investigator decision, taken before either coder opened a worklist. The assistant's objection was recorded at the time and is what D24 then measured. | **Before.** No record had been coded under either method when it was taken. The 2026-08-28 preliminary check is unaffected. | assistant, on the principal investigator's decision |

| D24 | 2026-09-05 | `data/screening/` | **The first pilot attempt failed its gate and is superseded by a fresh sample.** Kappa 0.879, AC1 0.914, alpha 0.880, subclass 15/15; unassignable 21.4% and 25.0% on the 28 records both coders judged eligible, against the 5% criterion. The agreement figure was additionally judged not to measure two readers applying the codebook independently, for the reason recorded under D23. | `protocol.md` §7 requires a documented revision and a fresh sample on failure. Both structural defects it exposed, the information basis and the coding arrangement, were changed before the second sample was drawn. | After. The result is reported as a failure and no instrument was changed in response to its value. | assistant, on the principal investigator's decision |
| D25 | 2026-09-05 | `protocol.md` §7; `taxonomy-v1.0.md` §10 test 3; manuscript §6.1 | **The pilot's information basis is fixed, and it is not the abstract.** §7 never stated one. Both the 2026-08-28 check and pilot 1 were coded from title and abstract, a basis inherited from `preliminary-agreement-check.md`, which describes a deliberately reduced trial. The pilot is now coded in two passes over the same 40 records: an abstract pass recorded in `family_abstract`, then a full-text pass for every record the abstract left `unassignable`, recorded in `family`. Both unassignable rates are reported; **the gate is the full-text rate**. | The instrument under test classifies from a paper, not from an abstract: `codebook.md` §0 codes from "the text, tables, figures, captions, or supplement", and classification is applied at extraction, which follows the Stage-2 full-text screen. Two runs have now measured whether a record can be classified from its abstract and returned 25-30% and 21-25% unassignable; that is a stable and interesting property of the literature and it is not evidence about the taxonomy. A criterion of 5% was never reachable on the basis being used, so failing it twice measured the basis rather than the instrument. The two-pass design bounds the extra effort to the roughly one record in four that the abstract does not resolve. | **Before**, with respect to the run it governs: pilot 2 has not been drawn against it at the time of writing and no record has been coded under it. Made after pilot 1's failure and in response to its structure, which is what §7 requires a revision to be. | assistant, on the principal investigator's decision |

**Effect of D24 and D25, and why the revision is not a moved goalpost.** The distinction
matters enough to state, because a reader is entitled to suspect one.

A gate was failed twice and is now being changed. What makes that legitimate here is that the
change is to the *basis of measurement*, not to the *threshold*: 5% stays exactly where it
was. What moved is the question being asked, from "can two readers classify this record from
its abstract" to "can two readers classify this record from the paper", and the second is the
question the taxonomy has always claimed to answer. `codebook.md` §0 has said so since it was
written; nobody noticed that the pilot was testing something else, because the abstract-only
basis arrived through a document describing a *reduced* check and was never re-examined when
that check's method was carried into the official run.

The abstract-only rates are not discarded. They are reported as pass-1 results in every run,
they now have three independent measurements behind them, and they say something the paper
did not previously have evidence for: roughly a quarter of eligible reservoir-computing
records do not state their state-generation mechanism in the abstract. That is a finding
about reporting practice, which is the manuscript's subject, and it is more interesting than
the gate it was accidentally being used as.

| D26 | 2026-09-05 | `data/screening/pilot/`, coder files | **In pilot 2, one coder used automated retrieval for full texts and drafted reason text from it; the classification calls are the coder's own.** Disclosed on the coder's own statement when the drafting was noticed in his submitted file. He is editing the drafted reasons into his own words; the calls, both passes, are unchanged by that editing. | The coder files are released under `protocol.md` §13, so a reader will see reason text and is entitled to know how it was produced. This is the same disclosure D12 makes for near-duplicate adjudication and it is the same category: retrieval and drafting are assistive, the judgement is the coder's. It is **not** the D23 arrangement, under which the calls were produced first and the coder accepted them; the distinction is the whole difference between pilot 1 and pilot 2 and is therefore recorded explicitly rather than left to inference. | Before the statistics were computed. Noticed in the submitted file before any agreement figure was calculated or reported. | assistant, on the coder's statement |

| D27 | 2026-09-05 | `data/screening/pilot/`, pilot 2 coder B, record RC-6374 | **One record resolved at pass 1 was given a full-text pass anyway, outside the pass-2 worklist D25 defines.** RC-6374 was assigned F1 / F1.2 from its abstract, so under D25 it should have carried that call forward untouched. The coder read the paper because the abstract raised a membership question §1.2 does not rule on, and the record came out **ineligible**, `not-rc:trained-internals`: the paper's §4.2 states the outer loop "was optimized using backpropagation through time" and its eq. (3) minimises over Theta = {W_in, W_rec, W_out_init}, i.e. over the reservoir's own recurrent weights, which is the exact case §1.2 excludes. `family_abstract` was left at F1 so the pass-1 rate stays comparable; only the pass-2 column moved. | D25 bounds the full-text effort to the records an abstract leaves unassignable, and the bound is about effort, not about correctness. Leaving a record in the corpus with family F1 when the paper is an end-to-end-trained RNN would have been a known error preserved for the sake of a procedural rule. The departure is recorded rather than taken silently, and it is disclosed in the record's own `reason` as well, because a reader recomputing the pass-2 worklist from D25 would not otherwise find this record in it. | After submission of the coder file, before any agreement statistic was computed. | assistant, as coder B; disclosed to the principal investigator on the same day |
| D28 | 2026-09-05 | `protocol.md` §4.1 and §4.2 | **§4.1's publication-type list is widened to include book chapters reporting primary research, and §4.2 gains two exclusion codes, `not-eligible:publication-type` and `not-english`.** §4.1 has required an English full text and a specific publication type since the protocol was written, and §4.2 provided no code for either, so a coder meeting one had to force it into `not-primary`, which is glossed "review, survey, tutorial, editorial". | Found while coding pilot 2, which drew two such records in forty (RC-0387, a doctoral thesis with a Portuguese abstract, and RC-5337, a Zenodo data-and-code deposit). Sizing it against the corpus showed it is not an edge case: **276 records, 7.8% of the open-access non-duplicate corpus, carry a `venue_type` outside §4.1's list** - 107 dissertations, 37 book chapters, 33 conference abstracts, 28 datasets, 19 other, 16 peer reviews, 14 errata, 6 editorials, 4 books, and a tail of software, reports and paratext. The book-chapter widening is separate and goes the other way: 37 chapters include primary research and excluding them on form would drop real work, so the type list admits them while review and tutorial chapters stay `not-primary` on their content. | Before screening. No Stage-1 or Stage-2 record has been coded under §4.2; the only affected records are the two pilot rows, re-coded and logged below. | assistant, on the principal investigator's decision |

| D29 | 2026-09-05 | `protocol.md` §7 gate, `scripts/screen.py` | **A record dispositioned under `taxonomy-v1.0.md` R11 is reported under §7 with its reason rather than counted in the unassignable gate numerator.** R11 covers a record reporting systems in two *different* families - not one system combining mechanisms, which is §2.1 and carries `family_symmetric` - and where both are co-equal main-text comparators with neither subordinate, it makes the record `unassignable` and states in terms that it "is reported with its reason under `protocol.md` §7 rather than counted against the instrument". This deviation is the implementation of that clause and its scope is exactly one line of arithmetic: the gate numerator. The record stays in the sample, stays in Cohen's kappa, AC1 and Krippendorff's alpha over all six categories, stays in the all-records unassignable rate, and stays in the gate denominator. | §7 requires each unassignable record's reason to be tabulated because "a record that the instrument cannot classify" and "a record that does not contain the information the instrument needs" are different findings that one rate conflates. RC-3140 is a third kind, which §7 did not anticipate: the instrument classified it correctly and what defeats a single family code is the record containing two papers' worth of system. Counting it as an instrument failure measures the corpus, not the taxonomy - the same error D21 corrected on the eligibility axis. | **Both numbers are reported everywhere the gate is. As adopted this carve-out converted the gate result; as it now stands it does not, and the sequence is given in full below.** When D29 was adopted at 19:39 the criterion read verbatim: coder B 1/31 = 3.2%, coder A 2/31 = 6.5%; it binds on the worse of the two, so **NOT MET**, and **MET** with R11 applied (0.0% / 3.2%). Coder A's second unassignable was RC-1144, which her own reason recorded as a retrieval failure and not an instrument failure. The PDF was supplied and she re-coded it at 19:43. The criterion now reads **MET either way**: verbatim 1/31 = 3.2% and 1/31 = 3.2%, and 0.0% / 0.0% with R11. Cohen's kappa is untouched by the carve-out in both computations, and rose from 0.9099 to 0.9542 on the re-code. | assistant, on the principal investigator's decision |

**Why D29 is not the manoeuvre §7 forbids, and how a reader checks that.** §7 says
`unassignable` is "a category a coder may choose, **never a record dropped from the
calculation**", and says that narrowing a basis after a check exceeds the criterion "would be
moving a goalpost rather than correcting a basis". Both sentences are aimed at something close
to this, so the distinctions are set out rather than assumed:

1. **The record is not dropped.** RC-3140 stays in the sample (n = 40), in all three agreement
   statistics, in the confusion matrix and in the all-records rate. Only the gate numerator
   changes. §7's prohibition is about removing the assignable-versus-unassignable disagreement
   from the reliability figure; that disagreement is fully retained, and in this case there is
   none to remove, because both coders coded the record identically.
2. **The rule pre-dates the result.** R11 was issued on 2026-09-05 out of coder B's pilot-2
   coding. Coder A cited it in her submitted file, independently reaching the same
   disposition for RC-3140. The first agreement statistic on these two files was computed
   only afterwards. The rule was therefore in the instrument before
   anyone knew what the gate would read, which is the difference between applying a rule and
   fitting one.
3. **It is bounded by a declared list with a hard precondition.** `screen.py` carries
   `R11_TWO_SYSTEM_RECORDS`, one entry, keyed by record id and carrying its justification.
   Membership is never inferred from reason text. A record is carved out only where **both**
   coders judged it eligible **and** both coded it `unassignable`; one coder assigning a family
   makes it a disagreement, which is the thing the gate exists to measure, and it then counts
   in full. Five selftests hold those constraints.
4. **The unadjusted number is not recoverable-on-request, it is printed.** `pilot-kappa` prints
   the as-coded rate, the adjusted rate, the carved record with its reason, and the
   counterfactual verdict ("Without the R11 carve-out the same criterion reads NOT MET"). Both
   are written to `pilot_agreement.json`. A reader who rejects D29 has the failing number in
   front of them without recomputing anything.

**What is not claimed.** R11 was written during pilot 2 and out of pilot 2's own records, and
D29 applies it to a gate on those same records. That is disclosed, not defended. The alternative
considered and rejected was cutting RC-3140 and reporting n = 39, which §7 forbids outright and
which the seeded sample (`pilot_sample.json`, seed 20260907) would expose to anyone who redrew
it.

**The carve-out is no longer load-bearing, and the order of events is the reason it can be
said.** D29 was adopted while it decided the gate, which is the weakest position a rule of this
kind can occupy, and it was written up on that basis. What removed the dependence was evidence,
not argument: coder A's second unassignable, RC-1144, carried a reason saying in terms that the
cell was "an access failure on my side, not a record the taxonomy could not classify" - the
article is gold CC-BY but Wiley serves a Cloudflare challenge to every automated route and no
repository copy exists. This is the same condition as coder B's three pass-2 records and it was
resolved the same way: the principal investigator opened the PDF in an institutional browser
session, the coder read it and re-coded, and the re-code is logged below. The gate then met §7's
criterion **as written, without D29**. D29 is kept because R11's clause is correct on the merits
and an implemented rule beats a hand-computed exception, but no result now rests on it, and
`pilot-kappa` prints the unadjusted verdict on every run so a reader can confirm that without
recomputing. **The general point, recorded because it will recur at Stage 2: an unassignable
cell that is a retrieval failure is not evidence about the instrument, and the remedy is to
retrieve the paper, not to adjust the statistic.**

**Re-code log, pilot 2 coder B (`codebook.md` §0.5).** Seven re-codes, all made after the file
was submitted and all before any agreement statistic was computed. `family_abstract` was not
touched by any of them, so the pass-1 unassignable rate stays 18/40 and stays comparable with
the 2026-08-28 check and pilot 1.

Driven by evidence that arrived after submission:

| Record | Was | Now | What changed it |
|---|---|---|---|
| RC-3336 | `unassignable` | F1 / F1.1 | Full text §2-§3. An ordinary ESN recursion with the echo state property enforced, so an internal state *is* carried across steps and step 1 resolves to F1, not F3. The abstract read F3-ish because of the paper's result, not its architecture. |
| RC-0972 | `unassignable` | F2 / F2.1 | Full text §2: one laser as the nonlinear element, feedback time tau divided into n equal parts, theta = tau/n, n = 50 virtual nodes. |
| RC-0541 | `eligible` blank | `eligible` = yes | Full text §2.3 reports two working RC implementations with quantitative results, where the abstract's claim had been prospective ("we believe"). |
| RC-6374 | `eligible` = yes, F1 / F1.2 | `eligible` = no, `unassignable` | Preprint §4.2 and the Fig. 3 caption: the outer loop is backpropagation through time into the recurrent weights. See D27, which records the procedural departure this involved. |

Driven by rulings issued the same day:

| Record | Was | Now | Ruling |
|---|---|---|---|
| RC-0541 | `unassignable` | F2 / F2.1 | R11. The main text's system is the delay-feedback simulation; the measured F1.6 device half is in Figs. S11-S12 and is recorded in the reason. R1 still splits this record at extraction. |
| RC-5337 | `not-primary`, extended | `not-eligible:publication-type` | D28. The extension was a coder's workaround for a missing code; the code now exists. |
| RC-0387 | `not-primary`, extended | `not-eligible:publication-type` + `not-english` | D28. Both grounds now have codes; the record failed §4.1 on both. |

**Effect on the coder's own figures.** At submission the eligible-only pass-2 unassignable rate
was 3/31 (9.7%), two of the three being the retrieval failures rather than classification
failures. After the three retrievals it was 2/32, after D27 it was 2/31 (6.5%), and after R11 it
is **1/31 (3.2%)**. The single remaining unassignable is RC-3140, which R11 leaves unassignable
deliberately: its ELM and ESN systems are co-equal main-text comparators, so there is no primary
system to code it on. The all-records rate is 10/40. None of these are the pilot result, which
requires both coder files.

**Re-code log, pilot 2 coder A (`codebook.md` §0.5).** One re-code, made after the file was
submitted at 18:56 and after a first agreement statistic had been computed on it at 19:39. That
ordering is stated because it is the unfavourable fact about this entry: the record was re-coded
knowing it was one of the two that held the gate below its criterion. What makes it a retrieval
and not a repair is that the coder had already written the disposition into her submitted
reason, before any statistic existed - "PASS 2: FULL TEXT NOT RETRIEVED ... THIS CELL IS AN
ACCESS FAILURE ON MY SIDE, NOT A RECORD THE TAXONOMY COULD NOT CLASSIFY" - and the re-code
resolved it in the direction that evidence dictated rather than the direction the gate needed:
had the full text shown a delay line, F2.1 would have been the call and the record would still
have left the unassignable column. `family_abstract` was not touched, so the pass-1 rate is
unchanged at 19/40.

| Record | Was | Now | What changed it |
|---|---|---|---|
| RC-1144 | `unassignable`, retrieval failure recorded | F1 / F1.6 | Full text, arrhythmia section: the spike trains "were fed in parallel to 15 ECRAM-based memristor nodes, with each node sequentially receiving the data over time", each node "an independent computational element" (Fig. 5a caption), no coupling and no feedback loop reported. R6 verbatim - uncoupled dynamic nodes, F1.6. The paper's own "135 virtual nodes" is 9 time samples of each of 15 devices, not N samples across one delay period, so §2 step (ii) does not fire; the coder recorded that the step tests the mechanism and not the vocabulary. Two extraction flags raised with it: R4, `state_dim` reported two ways in one system, and D6, whether the ECG stream was presented to 15 real devices at task rate is not settled in the main text and needs the Supporting Information before the E2/E3 call. Time 32 -> 46 min. |

**Provenance of the retrieval.** Advanced Electronic Materials, `10.1002/aelm.202400920`, gold
open access under CC-BY, published version, publisher-hosted, confirmed against Unpaywall on
2026-09-05. The coder's account of the failure was accurate: the publisher is the only OA
location, Wiley answers automated routes with a Cloudflare challenge, and the DOAJ record links
onward rather than mirroring the file. The principal investigator supplied the PDF through an
institutional browser session. No paywall was circumvented and no access condition was
misreported in the corpus, which is the outcome the coder's refusal to code it `unavailable`
was protecting.

**Effect on the pilot result.** Coder A's eligible-only pass-2 unassignable rate went from 2/31
(6.5%) to **1/31 (3.2%)**, and to 0/31 under D29. Family agreement went from 38/40 to **39/40**,
Cohen's kappa from 0.9099 to **0.9542**, AC1 to 0.9719, Krippendorff's alpha to 0.9548. The
family disagreement count went from two to one. Subclass agreement is unchanged at 20/20: coder
A resolved RC-1144 at pass 1 and so, correctly under D25, never opened the full text, and left
the subclass blank on the stated ground that "the abstract never gives a device count or an
arrangement, and F1.6 needs the arrangement specified" - which is the same reading of F1.6 that
the full text then satisfied. The record is therefore outside the subclass base, which counts
only records where both coders committed to a subclass, and it is not a subclass disagreement.

**Effect of D6.** The study's claims now cover the openly accessible reservoir computing
literature rather than the literature as a whole. This is stated in the abstract, manuscript
§6 and §9,
and is not left to inference.

Mitigation: all 7,062 records are harvested and, after merging with the arXiv leg and
deduplicating, the 2,948 excluded closed-access records are retained as metadata, so the
exclusion is characterised on year, venue, venue type and citation count rather than merely
declared. Reversible as a supplementary analysis if access appears.

**Count correction, 2026-08-02.** This entry originally read "3,832 of 7,064" and the
mitigation paragraph "7,064 records" and "3,232 excluded". Those were the OpenAlex API's
declared totals, not the contents of the harvest, which holds 7,062 unique works and 3,831
open ones. Corrected in place and explained in `search-strategy.md` §6.1. The published log
shows the correction rather than hiding it, on the same principle as D1 to D4: this study
cannot report other people's uncorrected numbers as a finding while quietly repairing its own.

**A consequence of D22 that would otherwise look like an error.** Gwet's AC1 divides its
chance term by `K-1`, where `K` is the size of the instrument's vocabulary, so widening the
vocabulary from five categories to six changes AC1 on identical data. Recomputing the
2026-08-28 preliminary check under the new vocabulary gives **0.9424** against the **0.9401**
recorded at the time. The manuscript reports AC1 to two decimals and both round to 0.94, so
no published figure moves, and Cohen's kappa and Krippendorff's alpha do not move at all
because they use only the observed marginals. This is recorded because the released
`pilot_agreement.json` carries four decimals, and a reader who re-runs `pilot-kappa` on the
released coder files today will get a different fourth digit from the one in the file. That
is the instrument changing, not the data. `screen.py`'s selftest now derives the AC1
expectation from `K` rather than hard-coding it, so the dependence cannot be re-baselined
away by hand the next time the vocabulary changes.

**Effect of D18 to D20, and why three instrument changes at once are disclosed together.**
All three were raised by referees, twice deferred to the pilot revision, and are made now
because the pilot has not run and the freeze has not happened: this is the last moment at
which changing the instrument costs nothing. After the gate, each of them would have forced a
re-code of every record processed to that point (`taxonomy-v1.0.md` change policy).

Two of the three are corrections of self-contradiction rather than improvements. D18 removed a
rule that ranked components by a quantity the same document says is not comparable across
families. D19 removed a family name that asserted a mechanism the family's own discriminator
does not require, and which the project's own worked example had already contradicted in
print since 2026-08-27. In both cases the manuscript had recorded the tension and deferred
it, twice, which is worth stating plainly: the defect was visible in our own text for nine
days and two review rounds before it was fixed, and it was fixed only when a third referee
declined to accept the deferral.

D20 is an addition rather than a correction, and its value is that it makes the paper's
central claim losable. Before it, "architecture is related to but not reducible to substrate"
had no operation attached that could return the wrong answer. It now has two thresholds fixed
in released code, and the rule that an intermediate association is reported as *consistent
with* the framework rather than as confirmation of it, because a null result has the same
signature.

Nothing in D18 to D20 is a response to data. No classification or extraction record exists,
the preliminary check recorded zero hybrids, and the single affected worked-example row is a
designer demonstration that the manuscript already labels as carrying no inter-rater
information.

**Completion of D19's impact assessment, 2026-09-05.** D19's impact cell read "No screening
or extraction record exists", which is true and which does not cover the 2026-08-28
preliminary-check coder files: those are neither. D18's cell, written the same day by the
same hand, did check them and said so ("the preliminary check recorded zero hybrids"). The
asymmetry was invisible because both cells end in a true sentence, and it was found by
the other coder on 2026-09-05 while re-reading the changed sections.

The check has now been run over all 40 records of the preliminary check, on every record
either coder assigned to F1 (20 of the 40). **One candidate exists: RC-5476**, *From chaos to
care* (CASCADE/DynML), whose abstract states that "DynML employs ensembles of continuous-time
nonlinear dynamical systems as chaotic reservoirs ... training only a linear readout". Both
coders assigned F1, both left the subclass blank, and both recorded independently that no
listed subclass fits: "F1.5 rejected: no coupling among ensemble members stated" and "no
listed subclass fits ensembles of chaotic ODE reservoirs". Every other F1 record in the
sample is a named echo state network, a stacked or deep ESN, a spiking reservoir, a
small-world topology claim, or an explicitly coupled model, so coupling is either stated or
definitional and F1.6 cannot apply.

**RC-5476 has not been re-coded**, for three reasons, the third of which is the substantive
one:

1. `codebook.md` §0.5 forbids revising an earlier record to match a later ruling without an
   explicit, logged re-code.
2. F1.6 also requires that the units be individually addressed and their arrangement
   specified (`taxonomy-v1.0.md` §3, note on F1.6). The abstract states neither.
3. F1.6's unit is a *node* whose own relaxation supplies the input-history dependence, with
   the state vector being the collection of node responses. DynML's ensemble members are
   whole continuous-time dynamical systems, each internally coupled, since that coupling is
   what makes them chaotic reservoirs. Whether "no inter-unit coupling" holds therefore
   depends on whether the unit is the system or its state variables, and the abstract does
   not settle it. If the unit is the system, the record is a set of internally coupled
   reservoirs operating **in parallel**, which F1.6 does not describe and F1.3 does not
   either, because F1.3 is two or more stages *in sequence*. On that reading the subclass
   list has a genuine gap rather than a missing assignment.

No agreement statistic moves. RC-5476 is not in the 21-record subclass-agreement base, since
neither coder committed to a subclass, and both assigned family F1, so Cohen's kappa, Gwet's
AC1, Krippendorff's alpha, the confusion matrix (manuscript Table 15) and the
unassignability table (Table 16) are unchanged. **Open, and an author decision:** whether
RC-5476 is F1.6, or the Tier-2 list needs an entry for parallel ensembles of reservoirs.
Recorded here.

No deviation number is assigned: no disposition changed and no record was re-coded. What this
entry records is the incomplete impact assessment. The procedural consequence, stated so it
is not rediscovered: **an instrument change's impact cell must name every record set it
checked, not only the sets it happens to think of.** The 2026-09-05 propagation note above
gives the same lesson for a withdrawn value; this is the same failure applied to a changed
definition rather than a changed number.

**D18 did not reach the instruments that would carry it, 2026-09-05.** Found while running
the check above, and recorded because it is the same failure shape one entry apart. D18
instructs a coder who cannot establish dominance to leave `family` empty and record a
symmetric label in a **new `family_symmetric` field**. That field exists in exactly two
places: `taxonomy-v1.0.md` §2.1, and the D18 row of this log. It was never added to
`codebook.md` §2, which is the extraction schema and is part of the registration by
reference, and it was never added to `screen.py`'s `PILOT_FIELDS`, which is the pilot packet
the coders actually receive. Worse than absent: `pilot-kappa` refuses any file in which a
coder leaves `family` empty, reporting the record as "not yet coded", so a coder following
D18 exactly would block the computation and have nowhere to put the label. Verified by
running it.

Nothing is coded under D18 and no statistic is affected, so this is a gap in the instruments
rather than in any result. It is **not repaired here**, because the repair is not mechanical:
adding `family_symmetric` to the pilot packet requires deciding whether a symmetric label is
a sixth category in the agreement vocabulary, a record excluded from the statistic, or a
record counted as a disagreement with any primary assignment, and each of those computes a
different kappa over a different denominator. That is a pre-registration decision belonging
to the authors, it changes what the pilot's gate measures, and it must be settled before the
packet goes out rather than discovered during coding. It is recorded with the pilot-design
decision in `docs/preliminary-agreement-check.md`.

**Effect of D7.** Five changes, all to `scripts/dedupe.py` and §5, all pre-screening.

1. **An OpenAlex reader was added.** Deviation D5 made OpenAlex the primary database on
   2026-07-31, but the dedup script accepted only `--scopus`, `--wos`, `--ieee` and
   `--arxiv`. The primary source had no input path, so the screening corpus could not be
   built at all. This is the substantive fix; the remaining four surfaced while making it.

2. **A new dedup step 1b, exact arXiv identifier match**, above the title pass. OpenAlex
   registers preprints under `10.48550/arXiv.<id>` while the arXiv API reports the journal
   DOI or nothing, so 825 of 1,234 arXiv records carried no DOI and their pairs were being
   resolved by fuzzy title matching. Step 1b resolved 663 pairs on an identifier both sources
   agree on. This adds a step to the pre-registered §5 order rather than altering one, and it
   strictly replaces weaker evidence with stronger.

3. **Preprint detection now keys on record type, not source.** OpenAlex returns 1,048 records
   typed `preprint`; the previous rule recognised a preprint only if it arrived from the arXiv
   leg, so an OpenAlex preprint could outrank the published version §5 rule 4 says it should
   merge into.

4. **The near-duplicate pass 3 blocker was replaced.** It skipped pairs whose normalized
   titles differed by more than 40 characters, which is a heuristic and discards true matches
   among long titles. It is now two exact necessary conditions on the ratio, so the flagged
   set equals a full pairwise scan. Both replacements were verified against a brute-force
   reference on random subsamples; the check script ships with the artefacts. On the current
   corpus the old skip happened to lose nothing, which is worth stating plainly: the change
   was made because the guarantee was absent, not because a pair had been observed to escape.

5. **The §5 step 3 manual review acquired a mechanism.** The near-duplicate file previously
   held two title columns, which is not enough to decide a pair on, and there was no route
   from a decision back into the corpus. It now carries both records' id, year, venue, DOI
   and source with a `decision` column, and `--adjudications` applies the result by setting
   `dup_of` and `dup_basis` rather than by deleting rows. This adds no rule; it makes an
   already-required step executable and auditable.

None of this changes a threshold, an eligibility criterion, or an analysis. Items 2 and 3
change which records merge, and both were made before any screening decision exists, so no
result could have informed them.

**Effect of D8 to D10: the anchor pass is complete, and two earlier deviations are reversed.**

D8 reverses D1 and D9 reverses D3. Both reversals are recorded as new entries rather than by
editing the originals, because the sequence is the evidence: an anchor was recorded, failed
its attribution, was unset, and was then recovered from a different pair of primaries with a
metric correction attached. A log that showed only the final state would show a correct
threshold and conceal that the same figure was wrong twice, in two different ways, before it
was right.

Standing after the pass: **five of eight anchors required correction before use.** None was
fabricated. Each was a real measurement that had lost the qualifier that made it
interpretable, the metric (1, 2), the unit (7), or the input condition (5). That specific
failure shape is the finding, and it is reported in `benchmark-thresholds.md` §5 and belongs
in manuscript §5.3.

Net effect on the analysis: **NARMA-10 re-enters the headline A4 analysis.** The 2026-07-31
statement that the field's most-used benchmark would have to be dropped is withdrawn.

**Effect of D11: a coverage gap that is real and is not being merged away.** Semantic Scholar
returns 6,082 in-window records for the same query; 5,398 (88.8%) are already in the corpus.
Of the 684 that are not, Crossref date-resolution puts **429 inside the frozen window, 412 of
them carrying a core RC phrase**, and 370 of those are dated 2025 or 2026. The shape is
indexing lag: OpenAlex has not yet caught up on the most recent two years.

This is reported, not merged. §1 pre-specifies that any additional yield from an overlap check
is reported separately, and doing anything else would convert a coverage check into an
unregistered second harvest. Two consequences the manuscript must carry:

- The §3 search limitations gain a quantified entry: against Semantic Scholar's index, the
  search misses roughly 6% of in-window records, **concentrated in 2025-2026**.
- Any trend claim about recent years is affected, since the corpus under-represents exactly
  the period a growth claim would rest on. Whether to add Semantic Scholar as a source is a
  scope decision for the principal investigator, and it is **open**.

**Effect of D14, and why this is the most consequential correction in the log.** The paper's
second contribution is a substrate-independent taxonomy. A 2019 Royal Society paper is titled
*A substrate-independent framework to characterize reservoir computers*. Publishing a
substrate-independence claim without engaging that work would have looked either uninformed
or evasive to any reviewer in this field, and the omission was invisible for as long as the
two papers were fused into a single bibliography entry.

The claim survives, narrowed and sharpened. CHARC characterises a *substrate*, experimentally,
by its coverage of a behaviour space; RC-PYRAMID classifies a *published record*, from its
text, to determine whether two reported results are comparable. Different object, different
input, different output. Section 3.2 states the distinction in a table rather than asserting
it.

The relationship also runs in the paper's favour and this is now argued rather than left
implicit: CHARC demonstrates that substrate-independent measurement of reservoirs is
productive, which strengthens the claim that organising the literature by substrate is
organising by a variable the field's own best characterisation method treats as irrelevant.

Two things follow for how the earlier corrections should be read. First, the citation error
that hid this was not a formatting slip; it changed what the paper appeared to know about its
own field. Second, it was found only because the reference list was checked entry by entry
against an authoritative record, which is precisely the check Section 7 recommends and which
we had not performed on ourselves until this point.

**Also recorded 2026-08-02, not a deviation but a fired trigger.** The executed search
returned 8,296 records pre-dedup and 6,532 post-dedup against a pre-registered estimate of
1,500 to 4,000 (`search-strategy.md` §7). That fires the declared over-yield trigger and owes
a response under `protocol.md` §11. The response is a principal-investigator decision and is
**open**; the candidate readings and the sample that separates them are in
`search-strategy.md` §6.3. It is logged here now so that whatever is decided is visibly a
reaction to a pre-registered trigger rather than a post-hoc rationalisation.

**Effect of D15, and what it does to anchor 7.** The VPT baseline's history is now: recorded
as "~2.87 λt" (scoping), corrected to "~2.6 λt" as a unit error on 2026-08-02 (D10), then
found on 2026-08-20 to have been corrected against the wrong primary entirely. arXiv:2106.09780
is Huhn and Magri's Rijke-tube paper (leading Lyapunov exponent ~0.12, no Lorenz case) and does
not contain the sentence; neither does Racca and Magri's actual paper (arXiv:2103.03174v2),
whose setup merely matches the numbers (threshold 0.2, Lorenz LT ~ 1.1, so 2.87/1.1 ~ 2.6).
The sentence's true source remains unlocated after full-text checks of both papers plus
Doan, Polifke and Magri's physics-informed ESN papers (arXiv:1906.11122, arXiv:2011.02280)
and a phrase-level web search. The baseline is therefore unset. What survives for §3.5 of
`benchmark-thresholds.md`: the >30 λt upper end (HurleyShaheen, verified) and the fact that
validity thresholds differ across studies (0.2 in Racca and Magri, 0.4 in Hurley and Shaheen,
both read from primaries). The manuscript reports the two-stage failure in §7 rather than
absorbing it: a value can pass one verification pass and still be wrong, because the
verification itself can be performed against a misidentified source.

**Effect of D16 and D17, and what they do to the count.** Two dispositions from the first two
passes were wrong in opposite directions: anchor 2 was "corrected" away from a value the primary
actually states, and anchor 8 was declared unlocatable although its primary was already in the
bibliography. With anchors 1 and 2 un-merged, the set contains eight distinct quantities.
Standing: two verified without change (3, 6); five with a meaning-changing correction or removal
(1 attribution; 2 input-distribution condition and exclusion from thresholds; 5 input condition;
7 unit and then source; 8 uncertainty interval and operating condition); one bibliographic
correction (4). Of the eight dispositions recorded in the first two passes, four (1, 2, 7, 8)
were later reversed by reading a primary text. The manuscript reports both numbers.

Two procedural rules follow and are now in manuscript §6.3 and §7.2. First, follow the secondary
source's own reference before declaring a value unlocatable; anchor 8 failed because the
review's sentence was consulted and its citation was not. Second, treat a quotation that fits
the expected story exactly as a prompt to re-read the primary; the misquoted "~0.4" made the
relabelling account look precise where the primary's 0.434 does not support it. Both reversals
were found while verifying primaries for the round-2 additions (Table 9, the worked-example
notes), not by the procedure that produced the original dispositions.

**How long D16's withdrawn reading survived in released files, recorded 2026-09-05.** D16
reversed the "~0.4 NMSE relabelled" reading of Vidamour et al. on 2026-08-27, and the
manuscript, `benchmark-thresholds.md` §3.1 and the manuscript's own lineage figure were all
corrected that day. Three released artefacts were not, and a consistency sweep found them on
2026-09-05: the secondary lineage diagram `fig5s` in the released figure library still drew
"Value retained; label changed / NMSE / ~0.4" and a "factor of 2.5"; `codebook.md` §8 still
carried the same reading in its `metric_defined` rationale; and `benchmark-thresholds.md`
§3.6 still opened with "the 0.014% figure could not be located in any primary source", the
pre-D17 disposition, immediately above the block that located it. All three are corrected in
place with the correction shown.

No deviation number is assigned, because no disposition changed: D16 and D17 stand exactly as
recorded. What this entry records is the propagation failure rather than the finding. It is
the same shape as the misfiled Paquot note of 2026-08-27, with one difference that makes it
worse and therefore worth the space: those notes were private, and these three files ship.
The procedural consequence is a rule this project did not have, now stated: **when a
disposition is reversed, grep the whole repository for the withdrawn value before closing the
revision, because the reversal lands in the document that motivated it and not in the ones
that quote it.** Two of the three would have been caught by searching for "0.4" and "2.5" on
2026-08-27; none was caught by re-reading the corrected documents.

**A pre-screening filter that was proposed, measured, and rejected, 2026-09-05.** No
deviation number, because nothing changed; what is recorded is a rule this project came close
to adopting and the measurement that stopped it.

An open recommendation had stood since 2026-08-02: journal issue cover
features "carry their own DOIs, the same authors and title as the article, zero referenced
works and no page range", so they "should be excluded upstream as `not-primary`", and "the
zero-references signature means it can be applied corpus-wide". The near-duplicate
adjudication then confirmed the description on eight Wiley pairs, each with zero references
against articles carrying 40 to 75.

The signature was tested before being trusted. Ninety eligible corpus records with a DOI were
drawn at random and their Crossref reference counts read: **82 resolved, and 13 of those, or
15.9%, carry zero references.** Six of the thirteen are ordinary research articles with page
ranges, in Mansoura Engineering Journal, the Malaysian Journal of Computer Science, the ESANN
proceedings and others; the rest are a preface, an expression of concern, a peer-review
record, a dataset, a monograph and a conference abstract. **Not one is a cover feature.**

A zero reference count is therefore a property of the publisher's deposit practice, not of
what the record is, and a corpus-wide rule built on it would have silently removed roughly
half of what it caught while catching none of its intended target. The recommendation is
**declined**. Cover features are instead handled by `taxonomy-v1.0.md` §11 ruling **R9**: two
coders recognise them at Stage 1 from the title and abstract and exclude them with a stated
code, so the exclusion stays visible in the flow. The same reasoning declines the parallel
suggestion for the 14 erratum, 6 editorial and 16 peer-review records the corpus carries: they
are identifiable, they are few, and Stage 1 is two coders with liberal inclusion precisely so
that removal is a recorded judgement rather than a silent filter.

This is the project's own subject, one level up again. A metadata field was about to stand in
for a property it does not measure, on a plausible description that happened to be true of
every instance anyone had looked at. What separated the two was counting, not re-reading.

**Effect of D13.** Paper 1 is assembled and contains no corpus-audit results. The `[MEASURE]`
placeholders that mark those results are rendered in paper 1 as explicit deferrals rather than
removed, so a reader can see precisely which claims are measured and which are owed. Paper 2
inherits the registered protocol unchanged; nothing about the audit's design is altered by the
split, and the registration in paper 1 is what paper 2 will be held to.

**Diagnostic bearing on that decision, added 2026-08-02.** The 100-title probe §6.3 called for
has been run (`data/screening/leakage_probe_20260802.json`): 62 on-topic, 18 undecidable from a
title, 20 off-topic. Removing every off-topic record would leave ~5,226; removing the
undecidable ones too would leave ~4,050, still above the 4,000 ceiling. **Polysemy leakage
therefore cannot account for the overshoot**, which points to the second reading, genuine
growth, consistent with the year curve of 517 records in 2019 rising to 1,342 in 2025
(OpenAlex leg, pre-dedup; the deduplicated corpus runs 493 to 1,301, the figures the paper
now reports).

The probe is **exploratory and single-coder, coded from titles alone**. It is
a diagnostic to inform the decision, not a screening decision, and no record was removed on
the strength of it. Its own limitation is visible in the 18 undecidable cases: a title is
often not enough, which is why Stage 1 reads abstracts and uses two coders.

**Effect of D5.** The search is now fully re-executable by any reader without an account. The superseded databases stay documented in the development record and become a supplementary coverage check if access appears, with any additional yield reported separately rather than merged
silently.

Two consequences to watch. OpenAlex phrase matching is looser than Scopus field-limited
search, so the raw hit count is higher (7,062) and the string needs recalibration against the
registered 1,500 to 4,000 expectation before screening. And abstract coverage is incomplete,
concentrated in closed-access records, which interacts with the open-access scope decision
recorded as pending in `search-strategy.md` §1.2.

*Both consequences landed.* The corpus came in at 6,532 post-dedup against that 1,500 to
4,000 expectation, and the recalibration this paragraph anticipated is now owed as a fired
trigger (below). 222 of the eligible records still have no abstract and are flagged at
Stage 1 rather than dropped. The scope decision recorded as pending here was settled the
same day as D6.

**Effect of D1 to D3. SUPERSEDED 2026-08-02 by D8 and D9; retained unedited for the record.** NARMA-10, the corpus's most-used benchmark, currently has no
usable triviality ceiling and only a grade C resolution floor. Unless a primary source for a
trivial or linear baseline is located, it is excluded from the headline A4 analysis. This is a
material change to the pre-specified analysis and must be visible in the manuscript rather
than absorbed silently.

| D30 | 2026-09-15 | `taxonomy-v1.0.md` §11; manuscript §3.2, §3.4, Table 6 | **Ruling R13 appended: the F2/F4 boundary is decided by the axis of multiplexing, not by which mechanism supplies the memory.** A system whose state vector is built by sampling one physical element at many points within an input interval is F2 / F2.1 whether its input-history dependence comes from loop delay or from the element's own relaxation; F4 requires a spatial medium sampled at several probe positions. The Torrejon et al. (2017) worked example moves from "F2.1, ambiguous" to F2.1. | §2 step 2 names propagation delay as the memory source, and the manuscript had carried an unresolved F2/F4 tension against that row since 2026-08-27, deferred twice. §4 already defines F2 by the virtual-node construction and treats tau/theta as the resolution limit rather than the memory source, so the ruling states the discriminator the family already used rather than adding one. | **Before.** No screened or extracted record exists. The affected row is a designer demonstration the manuscript labels as carrying no inter-rater information, and the pilot recorded no F2/F4 disagreement: pilot 2 contained no F4 record at all. | assistant |

**Effect of D30, and why it does not disturb the freeze.** The change policy permits appending §11 rulings after the freeze and forbids Tier 0-2 edits. R13 is an appended ruling: §1 membership, the §2 procedure, the family definitions and the facet vocabularies are untouched, and the ruling resolves a case *within* step 2 rather than changing what step 2 tests. No record is re-coded, because none was coded under the tension: the twelve worked examples are the designers' own and the two agreement runs produced no F2/F4 call to revisit.

One inconsistency was found while applying it and is recorded because it is the shape this log already tracks. `scripts/figures.py` placed Torrejon et al. in **F4** on the milestones timeline and in **F2** on the substrate-by-family grid, against Table 6's F2.1. Three artefacts, two of them figures generated by one script, disagreed about one worked example, and the figure selftest could not see it because it checks that every family and subclass is *present*, not that a given system is placed consistently across figures. Both are now F2 and the grid's ambiguity marker is cleared.

---

**Round-5 revision, 2026-09-09. No deviation number: no disposition changed, no record was
re-coded, no threshold moved and no statistic was recomputed.** What follows is recorded
because the manuscript was restructured and the release manifest was corrected, and a reader
comparing this revision against the last one is entitled to know which of the differences are
findings and which are presentation.

**Nothing in the evidence changed.** The pilot result, the preliminary check, the eight
provenance dispositions, the corpus counts and every agreement statistic are exactly as they
were on 2026-09-05. `pilot_agreement.json` is byte-identical. The two new tables are new
*reporting* of data that was already released, not new data: both are recomputed from the
published coder files by `screen.py pilot-kappa`.

*The manuscript was reorganised, on a referee's §5.* Section 6 split into a validation and
provenance methodology section and a new Section 7 for corpus construction; the worked
examples moved out of Results into Sections 3.4 and 4.3, beside the procedure and the
dimensions they demonstrate; Discussion and Limitations merged into one Section 9 organised
by contribution; and Section 8.2's provenance narrative was compressed by about 350 words of
prose into the tables and figures that already carried it. Ten sections, ten figures, twenty
two tables, all cross-references re-derived and checked by `audit_manuscript.py`.

*Two tables were added, both answering the same referee point.* The report could not
reconstruct the pilot's 3.2% eligible-only unassignable rate from the published confusion
matrix, which was fair: the matrix records family calls and the gate is evaluated on a base
the matrix does not show. **Table 19** now gives the eligibility decomposition per coder, so
1/31 is derivable. **Table 20** gives all three coding runs, their bases, their statistics and
their outcomes in one place, including the attempt that failed. Both are recomputations of
released files, and Table 20 states the fact that makes the revision sequence checkable:
**the three samples are pairwise disjoint, 120 distinct records, no record coded twice.**

*Three reporting additions, all requested and all cheap.* The kappa confidence interval now
names its formula, the simple asymptotic form of Cohen (1960), rather than referring to "the
large-sample standard error"; the 0.70 gate is calibrated against the conventional
descriptive bands (Landis and Koch 1977) so a reader can see it is a pass mark and not a
claim about how strong agreement ought to be; and Section 7 now names the released PRISMA
2020 checklist, which existed and which the manuscript had never pointed at. A tenth figure
was added, plotting Table 9's evidence levels and efficiency claims, and it is locked to that
table by the figure selftest.

*Declined, with the reason unchanged.* The report asks again for a memory-capacity against
effective-dimension plot built from the twelve worked examples. It is declined for the third
time and on the same ground: Section 2.2 argues that a reported count is not the same object
across families, so extracting per-system capacity values and plotting them against each
other would perform in a figure the comparison the paper argues is inadmissible. The analysis
that *would* answer it is pre-specified as A7 and needs extraction data, which does not
exist. The report's larger request, a partial screening pass, needs two human coders and is
recorded as outstanding rather than declined.

**Four stale numbers were found in released files, and the rule that should have caught them
already exists.** The 2026-09-05 near-duplicate adjudication moved the corpus from 6,532 to
6,486 and the manuscript followed; four places did not, and all four ship:
`search-strategy.md` §1.3 and §6.3 carried 6,532 / 3,584 / 2,948 and the 493 / 1,301 / 705
year curve as current, `protocol.md` §5 carried 222 no-abstract records against 215,
`limitations_and_framing.md` carried the same pair, and `figures.py` hard-coded "6,532
corpus" into the pipeline diagram. §6.2 had been corrected on the day and carries a dated
note; the sections quoting it had not. This is the *third* instance of the propagation
failure this log already has a rule for, after D16's withdrawn reading surviving in three
released files for eight days and the 2026-09-05 sweep's twelve inconsistencies. **The rule
was correct and was not run.** All four are corrected in place with the correction shown.

The procedural consequence, stated because writing the rule down plainly did not make it
happen: a corrected number needs a repository-wide grep for the *withdrawn* value, and the
grep belongs in the revision that makes the correction, not in a later sweep that happens to
look. Three of the four above would have been caught by `grep -rn '6,532'` on 2026-09-05.

**The release manifest did not match what the manuscript says is released, and that is the
same failure one level up.** `git archive` is what builds the public artefact, and
`.gitattributes` was stripping files the paper points a reader at by name. Four things were
wrong and all four are fixed:

1. **The completed near-duplicate adjudication did not ship.** Manuscript §8.1 says "the
   completed file is released" and D12 says "the full proposal file ships as an artefact".
   The file carrying the 46/60 decisions and the deciding registry field per pair was
   export-ignored; what shipped was the blank worklist, with all 106 `decision` cells empty.
   A referee following that sentence would have found an empty file.
2. **`paper/references.bib` did not ship**, although §6.2 names it as one of the two records
   the provenance audit is documented in. Every entry carries its verification note. It is
   now tracked and released; `.gitignore` uses `paper/*` rather than `paper/` so that one
   file can be re-included.
3. **Two documents the manuscript calls "the released materials" did not ship**: the per-cell
   bases behind the review-coverage matrix (§3.1) and the provenance-expansion frame (§9.3).
4. **`figures.py selftest` failed in the released repository**, exit 1, although the README
   lists it as a reproduction step. It cross-checks two figures against manuscript sources
   that the artefact deliberately does not carry. It now skips those two checks with a
   printed notice and runs the rest; the timeline year check still runs, because the
   bibliography now ships. A check that cannot run has not passed, and the notice says which.

Also corrected: four shipped instrument files referenced working documents that are not part
of the artefact (`paper-concept.html`, `feasibility-report.html`, `export-guide.md`); the
references are reworded to point at what a reader actually has. The README's re-run block
gave `dedupe.py` with no arguments, which prints "no input records" and stops.

**The end matter existed twice and the two copies had drifted, and this one is the project's
own thesis in its own build scripts.** The acknowledgements, the data-availability statement
and the conflict-of-interest declaration were written once in `assemble_paper1.py` for the
markdown and again, independently, in each LaTeX postamble. On 2026-09-05 the LaTeX copies
were completed with the funding text and the signed conflict-of-interest declaration. **The
markdown copy was not**, so `PAPER1.md` went on saying that funding "will be finalized after
confirmation by all authors" and that the declaration "awaits confirmation" for four days
after both had been settled and were rendering, completed, in the two PDFs built from the
same sources. Nothing false reached a submission, because the submission is the LaTeX; what
reached a reader of the assembled markdown was a statement about the authors that was no
longer true.

This is the identical defect that `abstract_from_frontmatter()` was written to remove on
2026-09-05, when the abstract was found to exist twice, and the note in that function says in
terms that "two copies of the paper's most-read paragraph is precisely the drift risk this
project reports on". The end matter was three more copies of the same shape, one file away,
and the fix that removed the abstract's duplication did not generalise because nobody looked
for the next instance. All three statements are now defined once in `assemble_paper1.py` as
plain text; the markdown uses them verbatim and both LaTeX builders run them through their
own escaper. The rule worth carrying: when a duplication is found and fixed, search for the
others of its kind in the same pass, because the reason this one survived is that the search
stopped at the first hit.

**The first real `ieeeaccess.cls` proof found five defects the local build could not,
2026-09-09.** Everything to this point had been verified against IEEEtran plus
`ieeeaccess-shim.sty`, because the submission class needs pdfTeX and the available engine is
XeTeX. A co-author compiled the actual submission file on Overleaf and the proof PDF was read
page by page. What it caught:

1. **Figure 3 drew the hybrid rule that deviation D18 withdrew.** The box read "whichever
   component generates most of the state dimension", which is precisely the rule D18 replaced
   on 2026-09-05 *because it ranked components by a quantity Section 2.2 says is not
   comparable across families*. Section 3.2 of the same PDF says three pages earlier that the
   rule "was withdrawn". The figure also wrote the symmetric label `F2xF1`, where
   `taxonomy-v1.0.md` §2.1 requires ascending order, `F1xF2`. **Fourth instance** of a
   withdrawn value surviving in a figure after the text was corrected, after fig5s's D16
   reading, fig14s's "6,532 corpus" and fig20s's "Table 12". The guard now added checks the
   *rendered* figure rather than the source, because the withdrawn phrase was split across
   two string literals and no grep of `figures.py` would ever have found it.
2. **Two table cross-references were left behind by the restructure.** §8.3 said the
   unassignability categories require confirmation "like the codings in Tables 13 and 14",
   which were the designer codings under the old numbering and are the NARMA verdict and
   threshold tables under the new one; they are Tables 6 and 9. §9.2 pointed at "the
   efficiency boundary of Table 7", which is now the dimensions table; the boundaries are
   Table 8. Both passed `audit_manuscript.py`, which checks that every referenced number
   *exists* and cannot check that it means what the sentence claims. The renumbering map was
   applied to section references and not re-derived for table references inside moved
   paragraphs.
3. **The abstract quoted 0.43 where the body says 0.434.** In a paper whose D16 entry records
   this project misquoting that exact value as "approximately 0.4", the abstract rounding it
   again is not a typo worth passing over.
4. **Two overfull boxes the shim had not reproduced.** `docs/benchmark-thresholds.md` and
   `docs/prisma-2020-checklist.md` ran out of the column into the gutter and over the
   adjacent table. `\texttt{}` is unbreakable and IEEE Access's column is narrower than
   IEEEtran's, so TeX preferred a small overfull box to the hole that moving a 28-character
   span would leave. Code spans now permit a break after each separator.

**Second proof, same day: the fix for defect 1 introduced a new one, and three more of its
kind were still in the library.** The corrected Figure 3 was compiled and read again.

- **The hybrid box's text now overflowed the box.** The rule was right; the dashed border
  was hand-set at 86 units against text that wraps to five lines, so the last line,
  `F1xF2.`, fell outside it. The box height is now *derived* from the wrapped line count,
  and a geometry check asserts that every line sits inside the rectangle it belongs to. The
  existing geometry check only looked at the SVG canvas edges, which is why nothing caught
  it. A box sized by hand against text edited by hand drifts the moment either changes,
  which is the same shape of failure as the rule the box states.
- **Four more figures still drew "Section 7.2"** after the restructure moved provenance
  verification to 8.2: fig19s twice, fig21s, and fig23s, the last also naming "Table 10"
  for what is now Table 12. Figure 10's caption note shipped in the proof PDF pointing at a
  section number that no longer exists.

So the guard was generalised rather than repeated. The figure selftest now resolves **every**
`Section`, `Table` and `Figure` reference that any shipped figure draws against the
manuscript's actual headings and caption counts, and the set of shipped figures is derived
from the manuscript's own image lines rather than listed, so neither the check nor its scope
can be left behind by the next renumbering. Four instances of this failure were repaired by
hand before anyone wrote the check that makes the fifth impossible.

**The lesson is about the verification, not the defects.** Every local check passed on all
five: `audit_manuscript.py`, the figure selftest, and a Tectonic compile reporting zero
overfull boxes. They passed because the shim is not the class and a cross-reference checker
is not a reader. Two of the five were caught only by looking at a rendered page, and one only
by reading a figure against the text three pages away from it. **A build that cannot be
compiled in the submission format has not been proofed, and this repository should stop
describing it as verified until someone has compiled it and read it.** `IEEE-README.txt` now
says so in those terms.

**A stale build artefact was deleted.** `paper/PAPER1-IEEE.pdf` and its log were 46 minutes
older than the `.tex` beside them and had been built from a superseded `--preprint`
generation against IEEEtran plus the shim, not against `ieeeaccess.cls`. A reader opening the
PDF named after the submission was not looking at the submission. Both Overleaf packages were
also assembled by hand, which is how that happened, and are now built by `scripts/package.py`
from a named manifest, with `--check` reporting whether they are current. The packages carry
no PDF on purpose.

**Two biographies were closed.** Ilinka Ivanoska supplied her own on 2026-09-09, replacing
the drafted entry and its three `20xx` placeholders with 2009, 2013 and 2021; it also
confirms the Assistant Professor reading that the FCSE decision contradicts itself about, so
that caveat is resolved by its subject rather than by our weighing of secondary evidence.
Dimitar Trajanov's three degree years are omitted rather than guessed, on his instruction.
`build_ieee.py --check` now exits zero: the placeholder count is zero for the first time. The
counter stays, because the next drafted biography will need it.

**Build state, verified rather than recalled.** IOP: 49 A4 pages, 0 errors, 0 overfull boxes,
0 undefined citations or references, compiled with Tectonic from a fresh extraction of the
Overleaf zip. IEEE Access in `--preprint` form: 32 two-column pages, same four zeroes. The
submission file itself uses `ieeeaccess.cls` and still cannot be compiled locally, because
that class needs pdfTeX and the available engine is XeTeX; `IEEE-README.txt` says so in those
terms rather than implying a compile that did not happen.

---

## What counts as a deviation

- Any change to search strings, databases, or the window after execution begins.
- Any change to eligibility criteria after screening begins.
- Any change to the taxonomy after the freeze.
- Any change to the reproduction sample size, effort cap, or tolerance.
- Any analysis reported as confirmatory that was not pre-specified in `protocol.md` §9.
- Any change to a coding rule mid-extraction (also requires re-coding affected records).

## What does not

- Appending Tier-3 exemplars or §11 edge-case rulings to the taxonomy (explicitly permitted
  by the change policy, provided Tier 0-2 definitions are untouched).
- Fixing a typo, a broken path, or an arithmetic error in a script, provided outputs are
  regenerated and the fix is committed.
- Exploratory analyses, **provided they are labelled exploratory in the manuscript**.
