# Extraction Codebook

**Version:** 1.0 (DRAFT, freezes with `taxonomy-v1.0.md`)
**Part of the pre-registration by reference** (`protocol.md` §6).
**Unit of analysis:** one record. A paper reporting both a simulation and a device becomes
two records sharing `record_group_id` (`taxonomy-v1.0.md` §11, R1).

---

## 0. Coding conventions

These apply to every field below and override any local convention.

Cited elsewhere as §0.1-§0.6; the numbering is made explicit here on 2026-09-05 because
`taxonomy-v1.0.md` §11 R7 and `deviations.md` already cite these conventions that way and
this file was the only one not carrying the numbers.

1. **§0.1 Code what the paper reports, not what it implies or what you infer is standard.** If a
   value is not stated in the text, tables, figures, captions, or supplement, it is
   `not-stated`. Widespread convention is not a substitute for a stated value, the whole
   point of the audit is to measure how often convention is relied upon instead of
   specification.
2. **§0.2 `not-stated` ≠ `not-applicable`.** Use `n/a` only where the field is meaningless for
   the record (e.g. washout for an F3 record). Conflating these destroys the compliance
   statistics.
3. **§0.3 Search the supplement.** A value in supplementary material counts as stated, coded
   `stated-supplement` where the field offers that distinction.
4. **§0.4 Code conservatively at boundaries.** Where two codes are defensible, take the lower /
   less favourable one and set the corresponding `*_ambiguous` flag.
5. **§0.5 Never revise an earlier record to match a later ruling without re-coding it
   explicitly.** Log the re-code in `docs/deviations.md`.
6. **§0.6 One free-text note field per group** (`*_note`) for anything that does not fit. Notes
   are read during synthesis; they are where new §11 rulings come from.

---

## 1. Bibliographic and provenance

| Field | Type | Values / rule |
|---|---|---|
| `record_id` | string | `RC-####`, assigned sequentially at dedup. Immutable. |
| `record_group_id` | string | Shared across records split from one paper; else equals `record_id`. |
| `doi` | string | Empty if none. |
| `preprint_id` | string | arXiv ID where the record also exists as a preprint. |
| `year` | int | Publication year of the included version. |
| `venue` | string | Journal or conference name, unabbreviated. |
| `venue_type` | enum | As delivered by OpenAlex: `article` · `conference-paper` · `preprint` · `dissertation` · `book-chapter` · `review` · `other`, plus `published-unspecified` for arXiv-only records whose `journal_ref` names no typed venue. The corpus carries the source vocabulary rather than a re-mapping, so §9.2 characterises what was actually indexed. |
| `source_db` | enum[] | Which searches retrieved it: `openalex` · `arxiv` · `semanticscholar` · `crossref` · `supplementary`. Multi-valued, pipe-separated as written by `dedupe.py`. (`scopus` · `wos` · `ieee` remain valid but were superseded as primary sources by deviation D5 and returned nothing.) |
| `coder` | string | Initials. |
| `coding_date` | date | ISO-8601. |
| `double_coded` | bool | True if in the 20% reliability subset. |

---

## 2. Membership and taxonomy

| Field | Type | Values / rule |
|---|---|---|
| `included` | bool | Result of `taxonomy-v1.0.md` §1.1. |
| `exclusion_code` | enum | Required if `included = false`. See `protocol.md` §4.2. |
| `membership_flag` | enum | `none` · `f3-weak-i1` · `contested-evolved` · `contested-insitu` |
| `family` | enum | `F1` · `F2` · `F3` · `F4`. **Empty where `family_symmetric` is set**; see below. |
| `family_secondary` | enum | Hybrids with an established dominant mechanism only; else empty. |
| `family_symmetric` | enum | Symmetric hybrid label, e.g. `F1xF2`, codes in ascending order. Set **only** where the report combines mechanisms and does not establish which dominates; `family` is then empty and `family_ambiguous = true`. Added 2026-09-05 for deviation D18. |
| `subclass` | enum | e.g. `F1.4`, `F2.1`. Must be a child of `family`. |
| `family_ambiguous` | bool | True if the §2 procedure did not resolve cleanly. |
| `family_note` | text | Required when `family_ambiguous = true`. |

**Coding rule for `family`.** Apply `taxonomy-v1.0.md` §2 in order. Do not shortcut from the
substrate, a photonic paper is not automatically F2, and a memristor paper is not
automatically F1. Shortcutting from substrate is the specific error the taxonomy exists to
prevent, and it is the error a coder is most likely to make.

**Coding rule for `family_symmetric` (D18).** The primary family is the component whose
mechanism dominates state generation, judged from the reported memory mechanism and **never**
from a reported count: the dominant component is the one whose removal would eliminate the
system's dependence on input history. Where the report does not establish dominance, do not
force a primary family. Leave `family` empty, write the symmetric label in
`family_symmetric`, and set `family_ambiguous = true` with a note. Forcing a primary family
on a system whose report does not support one manufactures a precision the source does not
contain, which is the failure this instrument exists to detect.

*Schema completion, 2026-09-05.* D18 named this field on 2026-09-05 and added it to
`taxonomy-v1.0.md` §2.1 only; it reached neither this schema nor the pilot packet, so a rule
existed with nowhere to record its result. The extraction schema is completed here because
that half is mechanical. **The pilot half is not**, and is deliberately still open: a
symmetric label can be a sixth category in the pilot's agreement vocabulary, a record
excluded from the statistic, or a disagreement against any primary assignment, and the three
compute different kappas over different denominators. That changes what the pilot gate measures, so it was a pre-registration decision, recorded in `preliminary-agreement-check.md` and `deviations.md`. **Taken 2026-09-05 as deviation D22**: a symmetric label contributes the single category `hybrid-symmetric` to a six-category agreement vocabulary, and which pair the coder named is reported separately, as subclass agreement is. `screen.py`'s `PILOT_FIELDS` carries `family_symmetric` accordingly. (This paragraph still described the decision as outstanding, and named `deviations.md` twice where the first should have been `preliminary-agreement-check.md`, until 2026-09-09.)

---

## 3. Facets

| Field | Type | Values |
|---|---|---|
| `d1_substrate` | enum | `taxonomy-v1.0.md` §7 D1. Single-valued. |
| `d2_readout` | enum[] | D2. Multi-valued. |
| `d3_adaptation` | enum | D3. Single-valued; code the *most* adapted mechanism present. |
| `d4_mode` | enum[] | D4. Multi-valued. |
| `d5_task` | enum[] | D5 (Wringe et al. 2025). Multi-valued. |
| `d6_evidence` | enum | `E0`-`E5`. §8 of the taxonomy. |
| `evidence_ambiguous` | bool | True where two tiers were defensible; the lower was coded. |
| `evidence_note` | text | Required when `evidence_ambiguous = true`. |

**E2/E3 decision (the one that matters most).** If the input sequence used for the reported
result was presented to the device *in task order at task rate*, code E3. If states were
measured separately and later assembled into a state matrix, code E2. Where the paper does
not make this determinable, code **E2** and set `evidence_ambiguous = true`. The rate at
which this is indeterminable is itself a headline finding.

---

## 4. Reservoir specification completeness

Each field is coded `stated` · `stated-supplement` · `not-stated` · `n/a`, with the value
recorded separately where stated and numeric.

| Field | Applies to | Notes |
|---|---|---|
| `spec_state_dim` | all | Plus `state_dim` (int) and `state_dim_kind` ∈ `physical` · `virtual` · `probe`. See R4. |
| `spec_spectral_radius` | F1 | `n/a` for F2/F3/F4. |
| `spec_input_scaling` | all | |
| `spec_leak_rate` | F1 | |
| `spec_connectivity` | F1 | Sparsity or density. |
| `spec_activation` | F1, F3 | |
| `spec_regularization` | all | Ridge parameter or equivalent; `n/a` if readout is not regularized-linear. |
| `spec_delay_ratio` | F2 | τ/θ or equivalent. **The F2 analogue of state dimension**: its absence makes an F2 result uninterpretable. |
| `spec_probe_count` | F4 | |
| `spec_probe_placement` | F4 | Whether placement is described well enough to be repeated. |
| `spec_window_length` | F3 | |
| `spec_feature_order` | F3 | Polynomial order or basis order. |
| `eff_dim_reported` | all | `stated` · `stated-supplement` · `not-stated`. Whether the paper reports any measure of the *effective* state dimension, as distinct from the counted one. Added 2026-09-05 for analysis A7. |
| `eff_dim_value` | all | Float, where stated. Never estimated by the coder: if the paper does not supply it or a spectrum to compute it from, this is empty and `eff_dim_reported = not-stated`. |
| `eff_dim_method` | all | `participation-ratio` · `covariance-rank` · `pca-variance-threshold` · `memory-capacity` · `ipc` · `kernel-rank` · `other` · `n/a`. What the reported number measures; these are not interchangeable and A7 reports them separately. |
| `eff_dim_basis` | all | Free text: what was diagonalised or measured (state covariance over which inputs, how many samples). A participation ratio without its basis is not comparable. |
| `spec_note` | | |

**Derived:** `spec_completeness` = proportion of applicable fields coded `stated` or
`stated-supplement`. Computed, never hand-entered.

**On the effective-dimension fields.** Section 2.2 of the manuscript argues that a reported
count of 400 need not be 400 independent state variables. These four fields are where that
argument becomes measurable rather than theoretical, and they are deliberately conservative:
the coder records what the paper supplies and nothing else. Where a paper reports an
eigenvalue spectrum, `scripts/analyses.py` computes the participation ratio
D_PR = (Σλ)² / Σλ² from it; where it does not, the record contributes to the count of
papers for which the question cannot be answered, which is the finding A7 exists to produce.
Do not substitute memory capacity for an effective dimension without setting
`eff_dim_method = memory-capacity`: the two are related but are not the same quantity, and
A7 reports them separately for that reason.

---

## 5. Protocol completeness

| Field | Type | Rule |
|---|---|---|
| `proto_washout_stated` | enum | `stated` · `not-stated` · `n/a` (F3 has no transient). |
| `proto_washout_justified` | bool | Whether a reason is given, not merely a number. |
| `proto_split_stated` | enum | Train/test sizes. |
| `proto_split_contiguous` | enum | `contiguous` · `shuffled` · `not-stated`. **`shuffled` on a temporal task is a validity problem, not merely a reporting one**: flag in `proto_note`. |
| `proto_val_distinct` | enum | `distinct` · `same-as-test` · `not-stated`. Whether hyperparameters were selected on data separate from the reported test set. |
| `proto_data_source` | enum | `generated-described` · `generated-underspecified` · `public-dataset` · `private-data` |
| `proto_note` | text | |

---

## 6. Statistics

| Field | Type | Rule |
|---|---|---|
| `stat_n_runs` | int | Number of random initializations / repeats. `1` if explicitly single-run; `not-stated` where absent. |
| `stat_dispersion` | enum | `sd` · `ci` · `range` · `iqr` · `none` |
| `stat_reports_best` | bool | True where the headline figure is a best-of-N rather than a central tendency. |
| `stat_significance` | enum | `test-reported` · `none` |
| `stat_seed_stated` | bool | Whether seeds are given. |
| `stat_note` | text | |

**Coding rule for `stat_reports_best`.** Requires explicit evidence ("best result",
"optimal reservoir", a max over trials). Where a paper reports a single number from multiple
runs without specifying which statistic, code `stat_dispersion = none` and note it, do not
assume best-of.

---

## 7. Baselines

| Field | Type | Rule |
|---|---|---|
| `base_present` | bool | Any comparison method at all. |
| `base_types` | enum[] | `linear-ar` · `persistence` · `other-rc` · `rnn-lstm-gru` · `ssm` · `transformer` · `classical-ml` · `published-number` · `other` |
| `base_trivial_present` | bool | Whether a trivial baseline (persistence, linear AR, mean) is included. Its absence is the cheapest and most common validity gap. |
| `base_tuning_comparable` | enum | `explicitly-comparable` · `asymmetric` · `not-stated`. Code `explicitly-comparable` only where the paper states the baseline received comparable tuning effort. |
| `base_note` | text | |

**Rationale for `base_tuning_comparable`.** Asymmetric tuning is the failure mode that
dissolved the claimed advantage in quantum RC when tested. Coding it corpus-wide is a
pre-specified contribution, and `not-stated` is expected to dominate, which is the finding.

---

## 8. Benchmarks

One row per (record, benchmark) pair in `data/extraction/benchmarks.csv`, keyed by
`record_id`.

| Field | Type | Rule |
|---|---|---|
| `benchmark` | enum | `narma-10` · `narma-n` · `mackey-glass` · `lorenz` · `rossler` · `kuramoto-sivashinsky` · `santa-fe` · `spoken-digit` · `mnist-variant` · `channel-equalization` · `memory-capacity` · `ipc` · `kernel-rank` · `generalization-rank` · `nlt` · `real-world` · `other` |
| `benchmark_params_stated` | bool | Full task parameterization given (order, coefficients, input range, sequence length). |
| `metric` | enum | `nmse` · `nrmse` · `rmse` · `mse` · `mae` · `accuracy` · `wer` · `ser` · `valid-time` · `capacity` · `other` |
| `metric_defined` | bool | Whether the normalization is stated. **`nmse` and `nrmse` are used inconsistently across this literature**; an undefined normalization makes a reported number non-comparable. See the note below: this is now evidenced, not just expected. |
| `value` | float | As reported. |
| `value_kind` | enum | `mean` · `best` · `median` · `single-run` · `not-stated` |
| `horizon` | string | Prediction horizon where applicable. |

**Derived for A4:** `below_discrimination` (bool), set against per-benchmark thresholds
defined in `docs/benchmark-thresholds.md`. **Those thresholds must be fixed and justified
before extraction begins**: deriving them from the extracted distribution would be
circular.

**Why `metric_defined` is not a formality (added 2026-08-02; corrected 2026-09-05, D16).**
The anchor verification pass found the field's most-cited NARMA-10 baseline stated in two
metrics without either travelling with its normalization: Appeltant 2011 reports NRMSE 0.4
and Vinckier 2015 restates the same result as NMSE 0.16 (0.4² = 0.16, and they say so). A
coder who takes a bare "NMSE = 0.4" at face value is off by a factor of 2.5 against the
threshold.

A third published shift-register value compounds the problem without being the same
quantity: Vidamour 2023 states ~0.434 NMSE for **their own** shift register on a NARMA-N
variant with autocorrelated inputs. Read as bare NMSE numbers the two published baselines
differ by a factor of 2.7, and nothing in either number says which task it belongs to.
*This paragraph previously reported the third value as "~0.4 labelled NMSE" and read it as
Appeltant's figure relabelled. That was this project's misquotation of the primary, reversed
as deviation D16; the correction is recorded here rather than applied silently.*

Coding guidance that follows:

- `metric_defined = true` requires the paper to state the **normalization**, not merely the
  metric's name. "We report NMSE" is `false`. "We report NMSE, defined as
  Σ(y*−y)²/Σ(y*−ȳ)²" is `true`.
- Where a value is quoted from another paper rather than measured, code the value and set
  `value_kind = not-stated` unless the quoting paper states which it is. Anchor 1 shows how
  fast a quoted figure loses its metric, and anchor 2 shows how fast a coder's own
  transcription can lose a digit that carries the distinction.
- Do **not** silently convert between `nmse` and `nrmse` to make records comparable. Code
  what the paper says and let A4 exclude the ambiguous ones. The conversion is the error.

---

## 9. Abstract-language rubric (analysis A3)

Coded **blind to `d6_evidence`** by a coder who has seen only the abstract
(`protocol.md` §9.1). Mandatory blinding.

| Field | Type | Rule |
|---|---|---|
| `lang_max_claim` | enum | `L0`-`L5`, below. |
| `lang_evidence` | text | The specific phrase triggering the code. Required. |

| Code | Implied maturity | Anchor phrasing |
|---|---|---|
| `L0` | Model / theory | "we simulate", "numerical study", "we model" |
| `L1` | Device-informed model | "based on a model of", "simulated device" |
| `L2` | Measured device | "we measure", "device characterization" |
| `L3` | Working demonstration | "we demonstrate", "experimentally demonstrated", "implemented" |
| `L4` | Integrated / operational | "on-chip system", "real-time operation", "integrated processor" |
| `L5` | Deployed / practical | "deployed", "in the field", "practical application", "production" |

**A3 statistic:** the distribution of `lang_max_claim − d6_evidence`. Positive values are
claims running ahead of demonstrated evidence. Report the full distribution, not just the
mean, and report both directions, since papers understating their evidence are also
informative and their existence is what shows the instrument is not one-sided.

---

## 10. Efficiency (RC-BOUND)

Applies only where an energy, power, throughput-per-watt, or latency claim is made.

| Field | Type | Rule |
|---|---|---|
| `eff_claim_present` | bool | |
| `eff_value` | float | As reported. |
| `eff_unit` | string | Verbatim. |
| `eff_boundary` | enum | `B0` · `B1` · `B2` · `B3` · `indeterminable` |
| `eff_boundary_stated` | bool | **Requires an explicit sentence.** Inference from a system diagram is `false`. Code conservatively, this is the field most likely to be coded generously by mistake. |
| `eff_comparison_target` | string | What the claim is measured against, verbatim. |
| `eff_renorm_possible` | bool | Whether the paper supplies enough component information to re-normalize to B3. |
| `eff_note` | text | Assumptions required for re-normalization. Required when `eff_renorm_possible = true`. |

---

## 11. Artefacts

| Field | Type | Rule |
|---|---|---|
| `art_code_stated` | bool | A code availability statement exists. |
| `art_code_url` | string | |
| `art_code_resolves` | enum | `resolves` · `dead` · `on-request` · `none`. Checked at coding date; record the date. |
| `art_data_stated` | bool | |
| `art_data_url` | string | |
| `art_data_resolves` | enum | as above |
| `art_env_spec` | bool | Dependency/environment specification present. |
| `art_license` | string | |

**`on-request` is coded as its own value, not as available.** Whether it functions as
availability is an empirical question this study does not test (`protocol.md` §8.3 forbids
author contact during reproduction), and conflating it with `resolves` would overstate
compliance.

---

## 12. Reproduction sub-study

Populated only for the n = 24 sample. One row per attempted record in
`data/extraction/reproduction.csv`.

| Field | Type | Rule |
|---|---|---|
| `repro_selected` | bool | In the stratified sample. |
| `repro_stratum` | string | `family × artefact-availability` cell. |
| `repro_outcome` | enum | `R0` · `R1` · `R2` · `R3` · `R4` |
| `repro_target_metric` | string | The paper's own primary metric. |
| `repro_reported_value` | float | |
| `repro_recovered_value` | float | Empty for R0. |
| `repro_within_tolerance` | bool | ±20% relative, or inside the paper's stated dispersion (`protocol.md` §8.5). |
| `repro_hours` | float | Wall-clock to the 4h cap. |
| `repro_cap_hit` | bool | |
| `repro_failure_cause` | enum | `protocol.md` §8.6 list. Required for R0/R1. |
| `repro_log_path` | string | Path to the attempt log. **Every attempt is logged, including failures.** |
| `repro_author_correction` | text | Post-hoc, from §8.3 notification. **Reported in a separate column, never merged into `repro_outcome`.** |

---

## 13. Field summary

| Group | Fields | Feeds |
|---|---|---|
| Bibliographic | 11 | Descriptives, PRISMA |
| Membership & taxonomy | 9 | RQ1, falsification tests |
| Facets | 8 | All analyses; A3 |
| Reservoir spec | 14 | RQ2, A5 attribution |
| Protocol | 7 | RQ2 |
| Statistics | 6 | RQ2 |
| Baselines | 5 | RQ2 |
| Benchmarks | 9 (per pair) | RQ4, A4 |
| Language rubric | 2 | A3 |
| Efficiency | 9 | RQ7, A2 |
| Artefacts | 8 | RQ2, A5 sampling |
| Reproduction | 12 | RQ3, A5 |

Roughly 88 fields per record, of which ~55 apply to a typical simulated record. At an estimated 30-45 minutes per record this is consistent with the scoping effort budget, and with the pilot's own measured median of 9 to 10 minutes for the narrower task of family assignment alone.

---

## 14. Open items before freeze

Status as of 2026-07-31.

**1. Benchmark discrimination thresholds. CLOSED 2026-08-02.**
`docs/benchmark-thresholds.md` fixes thresholds from published anchors rather than from the
extracted distribution, and the anchor verification pass is complete. Seven of eight anchors
are resolved; the eighth, the 0.03 λt lower end of the VPT range, could not be sourced and has
been removed from the text rather than carried.

Net effect on scoring: NARMA-10 **re-enters** the headline A4 analysis with `T_triv` restored
to 0.16 NMSE (= 0.4 NRMSE) at grade B. `T_res` = 0.05 remains grade C and may be used only
as a labelled sensitivity value because it is based on one implementation. Spoken-digit
keeps its thresholds, which anchor 8's failure does not disturb. Five of the eight anchors
needed correction before use, and the pattern in those corrections (a lost metric, a lost
unit, a lost condition) is reported in §5.3 rather than repaired silently.

**2. Subclass lists are provisional. OPEN, closes at the pilot.**
Unchanged (`taxonomy-v1.0.md` §12). The pilot completes the Tier-2 lists and reports residual
gaps.

**3. A3 rubric reliability. CLOSED as a plan; execution pending.**
The procedure is now fixed and needs no further design work. `lang_max_claim` is coded by a
coder who sees the abstract only, blind to `d6_evidence`, using the closed keyword-anchored
rubric in §9. In the pilot, both coders code the same forty abstracts and Cohen's kappa is
computed on the six-level scale.

If kappa is at least 0.70, A3 is reported as a confirmatory analysis. If it falls below 0.70,
A3 is demoted to exploratory and labelled as such wherever it appears, rather than dropped.
That rule is fixed now, before any coding, because a rubric abandoned after it disagrees with
a preferred conclusion is precisely the practice this paper examines.

Where the two coders differ by exactly one level, the lower is recorded, matching the
conservative default used for `d6_evidence`. Differences of two or more levels go to
adjudication and become §11 rulings in the taxonomy.

**4. `d3_adaptation` "most adapted mechanism" rule. CLOSED.**
The facet is single-valued, so records combining several adaptation mechanisms need an
ordering. The ordering below runs from least to most adapted, and the coder records the
highest present:

`random-fixed` < `hp-optimized` < `unsupervised` < `physically-tuned` < `evolved`

The rationale is how much of the reservoir's configuration is determined by something other
than its own construction. Hyperparameter search sets a handful of scalars. Unsupervised
adaptation reshapes individual weights but without reference to the task. In-situ physical
tuning adjusts the device itself while the task is in view. Evolutionary optimization
searches the configuration space against task fitness and is the most adapted case, which is
also why it is the one flagged as contested membership.

Worked examples:

| Record | Coded | Reason |
|---|---|---|
| ESN with spectral radius and leak rate grid-searched | `hp-optimized` | Scalar design space only. |
| ESN with intrinsic plasticity applied, then spectral radius searched | `unsupervised` | Unsupervised outranks hyperparameter search. |
| Memristor array where bias voltages are swept to improve task accuracy, with ridge parameter also searched | `physically-tuned` | In-situ device adjustment outranks both. |
| Nanowire mesh where probe positions are selected by a genetic algorithm scored on task error | `evolved` | Highest in the ordering. Also set `membership_flag = contested-evolved`. |
| Photonic delay loop run at fixed operating point, readout ridge parameter cross-validated | `random-fixed` | Fitting the readout regulariser is part of training the readout, not adapting the reservoir. |

The last row is the one coders get wrong most readily. Selecting a ridge parameter is readout
training under I3 and says nothing about reservoir adaptation.
