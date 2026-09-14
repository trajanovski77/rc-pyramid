# Benchmark Discrimination Thresholds

**Version:** 1.0 (DRAFT, freezes with `taxonomy-v1.0.md`)
**Feeds:** analysis A4; the derived field `below_discrimination` in `codebook.md` §8.

> **These thresholds are set from published anchors, never from the extracted
> distribution.** Deriving a discrimination threshold from the corpus and then reporting
> what fraction of the corpus falls below it is circular. Every value below is traceable to
> a source that is independent of this audit, and every value is fixed before extraction
> begins.

---

## 1. What "discrimination" means here

A benchmark discriminates between two systems when the difference in their reported scores
carries information about the systems rather than about noise or about the task's floor.
Three distinct ways a benchmark stops discriminating, which the literature routinely
conflates:

| Concept | Symbol | Meaning |
|---|---|---|
| **Triviality ceiling** | `T_triv` | Score achievable by a trivial or purely linear system. A result *worse* than this demonstrates no nonlinear computation, whatever else it demonstrates. |
| **Resolution floor** | `T_res` | Score below which typical run-to-run dispersion exceeds typical between-system differences. Differences here rank noise, not systems. |
| **Saturation** | `T_sat` | Score at which the achievable range has collapsed so far that the metric no longer separates methods at all. Where defined, `T_sat` is reported descriptively; it is not used in the coding rule. |

### Coding rule for `below_discrimination`

```
below_discrimination = (value < T_res) OR (value > T_triv)      # error-type metrics
below_discrimination = (value > T_res) OR (value < T_triv)      # score-type metrics
```

Where either threshold is `unset`, the benchmark is **excluded from A4** and the exclusion
is reported. Excluding is correct; inventing a threshold to achieve coverage is not.

**Both directions are reported.** A result above `T_triv` is as informative a finding as one
below `T_res`, and reporting only the latter would make the analysis one-sided.

---

## 2. Confidence grades

| Grade | Meaning |
|---|---|
| **A** | Anchor is an analytic bound or an explicitly reported baseline in a primary source. |
| **B** | Anchor is inferred from consistently reported values across ≥2 independent primary sources. |
| **C** | Anchor is a working estimate. **Excluded from headline A4 claims**; reported in a sensitivity appendix only. |

---

## 3. Thresholds

### 3.1 NARMA-10: `narma-10`

| | Value | Grade |
|---|---|---|
| Metric | NMSE (normalized by target variance) | |
| `T_triv` | **0.16 NMSE**, equivalently **0.4 NRMSE**, restored 2026-08-02 | B |
| `T_res` | **0.05** | C (sensitivity only) |
| `T_sat` | ~0.04 | C |

> **Anchor 1 recovered, 2026-08-02, with a metric correction.** `T_triv` is restored. The
> 0.16 figure is real and traceable; what failed on 2026-07-31 was its *attribution*, not
> the number. Two primary sources, read directly:
>
> - **Appeltant et al., *Nat. Commun.* 2, 468 (2011)**, read from the open-access primary
>   (PMC3195233): "If the reservoir is replaced by a shift register that contains the input,
>   the minimal NRMSE is 0.4." The paper reports **NRMSE**, and its own best result is
>   "NRMSE=0.15".
> - **Vinckier et al., *Optica* 2(5), 438-446 (2015)**, §4.B, read from the primary PDF:
>   "The value NMSE=0.16 in fact corresponds to the best that can be obtained with a linear
>   shift register [12]", where [12] is Appeltant 2011. Vinckier's NMSE (their eq. 6) is a
>   squared-error ratio.
>
> **0.4 NRMSE and 0.16 NMSE are the same result.** 0.4² = 0.16. One quantity, two metrics,
> and the field cites whichever it happens to have met.
>
> **This is the cleanest instance of the thesis found so far, and it should be in §5.3.**
> A reader who encounters "0.16" in one paper and "~0.4" in another has every reason to
> believe two different baselines exist, because neither figure travels with its metric
> attached. Our own draft carried both, recorded them as two separate anchors (1 and 2),
> and concluded on 2026-07-31 that one had failed and the other needed its scope narrowed.
> Both conclusions were artefacts of the same unstated square root. The audit's instrument
> caught the unsourced attribution and still missed the metric collision for two days; that
> is worth reporting rather than tidying away.
>
> **Scope, stated precisely, because this is where the claim degrades.** The 0.4/0.16 figure
> is for a **linear shift register**, a pure delay line with no reservoir at all. It is not
> "the best achievable with no nonlinearity in the reservoir", which is the paraphrase that
> circulates and which our draft used. A shift register and a linear reservoir are not the
> same system. `T_triv` is therefore a **trivial-predictor ceiling**, which is what the A4
> rule needs, and it is labelled as such rather than as a linear-reservoir bound.
>
> Grade B rather than A: Appeltant was read via PMC and Vinckier via the arXiv PDF, both
> primary, but the two state the figure in different metrics and only Vinckier performs the
> conversion.

> **The original verification failure, 2026-07-31, retained for the record.** `T_triv = 0.16`
> was recorded at v1.0 draft as grade A
> on the basis of a claim that "the best performance achievable with no nonlinearity in the
> reservoir is NMSE = 0.16". On reading the traced source (Vidamour et al., *Reconfigurable
> reservoir computing in a magnetic metamaterial*, Commun. Phys. 2023), **that statement does
> not appear in the paper.** The figure came from a search-engine summary, not from a primary
> text. It is unset rather than downgraded, because an anchor with no located source is not a
> weak anchor, it is not an anchor.
>
> The companion figure was also wrong in detail. The primary text says a shift register
> "can only achieve normalised means squared errors (NMSE) of ~0.4", not 0.434, and states it
> for NARMA tasks generally rather than NARMA-10 specifically. The spurious precision of
> "0.434" was introduced somewhere between the paper and the summary.
>
> This is the verification step doing its job. A paper about unverifiable numbers cannot
> itself run on numbers traced to search snippets, and the same standard now applies to every
> remaining anchor in §5.
>
> *Retained unedited. The conclusion it reaches, that the anchor is unset, was superseded six
> days later by the recovery recorded above. The reasoning was sound on the evidence then
> available and the record is more useful intact than tidied: what it shows is that an
> unsourced attribution and a false negative can look identical until someone reads a third
> paper.*

**Superseded 2026-08-02: the "shift-register reference point" was never a separate quantity.**
This section previously carried "~0.4 NMSE, grade C" as a context-only reference distinct from
`T_triv`, on the reasoning that it describes a shift register rather than a linear reservoir
and is stated for the NARMA family rather than for order ten. The first half of that reasoning
was right and is now folded into `T_triv` above. The second half was the error: 0.4 and 0.16
are one measurement in two metrics, so anchors 1 and 2 were never two anchors.

**And there is a third reading of the same number, which makes the point sharper.** Vidamour
et al. (2023) write that a shift register "can only achieve normalised means squared errors
(NMSE) of ~0.4". Appeltant et al. (2011), the source of that value, report it as **NRMSE**.
Vidamour's figure is numerically Appeltant's and its metric label is not. So the same
underlying result now appears in the literature as:

| Source | Stated as | Value |
|---|---|---|
| Appeltant 2011 (primary) | NRMSE | 0.4 |
| Vinckier 2015 | NMSE | 0.16 |
| Vidamour 2023 | "NMSE" | ~0.4 |

Two of those three cannot both be right, and a reader has no way to tell which from the text.
This is not a criticism of any author; it is the measurement the audit exists to make, and it
arrived unbidden from a routine anchor check. It belongs in §5.3 with the table above.

*Third row and its reading superseded 2026-08-27 (D16): the primary states ~0.434, without
citation, for a NARMA-N variant with autocorrelated inputs. See the block below.*

> **Anchor 2, third reading, 2026-08-27 (deviation D16): the primary says ~0.434, not ~0.4,
> and it is Vidamour's own baseline.** Re-reading the published PDF and arXiv:2206.04446 gives
> the sentence as: "For this problem, a system with perfect linear memory of equal degree to
> the autocorrelation (i.e., a shift-register of length N) can only achieve normalised means
> squared errors (NMSE) of ~0.434. To improve upon this, a system needs to store nonlinear
> representations of past inputs." No citation is attached. The task is NARMA-N "of input
> signals with varying degrees of autocorrelation"; the authors' peak NARMA-10 NMSE is 0.359
> (NARMA-5: 0.265), inside the region "outperforming the score of a shift register with equal
> degree to the NARMA problem".
>
> Three consequences. (1) D2's reasoning was wrong: the precision "0.434" came from the
> primary, and the "~0.4" quoted in this document on 2026-07-31 and 2026-08-02 was a
> misquotation. (2) The three-source table above is wrong in its third row and in its reading:
> Vidamour's figure is not "numerically Appeltant's"; it is a different baseline for a
> different input distribution, stated in the authors' own NMSE. Anchors 1 and 2 are two
> quantities after all, and the merger is reversed. (3) `T_triv` is unaffected: 0.16 NMSE =
> 0.4 NRMSE stands on Appeltant and Vinckier; the 0.434 value is excluded from thresholds
> because its input distribution differs.
>
> What survives of the comparability point is stronger than the relabelling story it replaces.
> Two published shift-register NMSE baselines for "NARMA-10" differ by a factor of 2.7, and a
> reader cannot tell from the numbers which one applies. Paquot et al., Sci. Rep. 2, 287
> (2012), read from PMC3286854: "For a network of 50 nodes, both in simulations and experiment,
> we obtain a NMSE = 0.168 +/- 0.015", which sits at the 0.16 ceiling (Vinckier et al. say so
> in the passage quoted above) and would look 2.6 times better than trivial against 0.434;
> Vidamour's 0.359 sits below their own baseline and above the standard one. Manuscript
> Table 9 reports these verdicts. The earlier blocks are retained unedited; the misquotation is
> part of the record.

**`T_res` = 0.05, grade C (sensitivity only).** Anchor 3 verified. The
dispersion estimate is now read from the primary: Vinckier et al. (2015) §4.B report
"NMSE=0.0484±0.0095 in experiment, and NMSE=0.0463±0.0142 in simulation" at N=300. Those are
19.6% and 30.7% relative, which is the "roughly twenty to thirty percent" the draft had
estimated, now sourced rather than assumed.

Read the qualifier with it: "The standard deviation was evaluated by repeating this procedure
10 times." The dispersion is **run-to-run variation of one system on ten input series**, not
variation between laboratories or implementations. It may underestimate the spread in
cross-paper comparisons, but one implementation at one reservoir size cannot establish a
general resolution floor. Two papers reporting 0.045 and 0.050 should therefore not be ranked
without their own dispersion estimates.

**Consequence for A4.** With `T_triv` restored, NARMA-10 can be scored against the
trivial-predictor ceiling. The 0.05 value is reported only as a grade-C sensitivity analysis.

What does not change: the requirement that every NARMA-10 result be read together with the
metric it is reported in. Where a paper states "NRMSE", compare against 0.4; where it states
"NMSE", compare against 0.16; where it defines neither, set `metric_defined = false`
(`codebook.md` §8) and exclude the record from the A4 numerator rather than guessing which
convention was meant. Guessing carries a factor-of-2.5 error, and on the three sources in the
table above it would be wrong at least a third of the time.

The codebook already anticipated this: `metric_defined` carries the note that "`nmse` and
`nrmse` are used inconsistently across this literature". The anchor pass has now turned that
from a reasonable expectation into a documented instance, on the field's most-cited baseline
figure. No new field is needed; the existing one has acquired its evidence.

**Additional NARMA-10 flags** (coded separately, not folded into `below_discrimination`):

- `narma_params_stated`, the (α, β, γ, δ) parameterization and input range. NARMA-10's
  information processing capacity **varies with the input range**, so a result without a
  stated range is not comparable to one with a different range.
- `narma_divergence_handled`, NARMA-10 contains an unstable region in phase space and can
  diverge depending on input range and initial conditions. Whether the paper acknowledges
  or handles this is coded.

These two flags are expected to be the most damning simple statistics in the paper: they
measure whether the field's single most-used benchmark is being used in a comparable way at
all.

### 3.2 NARMA-N, N ≠ 10: `narma-n`

**`T_triv`, `T_res`: unset. Excluded from A4.**

Parameter values for NARMA-N vary across the literature with no canonical set, and there is
no consistent performance trend across N from which to derive an anchor. Record `N` and the
stated parameters; report the *variety* of parameterizations encountered as a descriptive
finding rather than scoring against a threshold.

### 3.3 Memory capacity: `memory-capacity`

| | Value | Grade |
|---|---|---|
| Metric | MC (sum of squared correlations over delays) | |
| `T_triv` | (see below) | |
| `T_res` | unset; 0.05 of claimed dimension retained for sensitivity analysis | C |

**The analytic bound is `MC ≤ N`**, where N is the number of linearly independent state
variables available to the readout; generically `MC = N` for a linear reservoir. This gives a
**validity check rather than a discrimination threshold**:

- `mc_exceeds_bound`, flag any record reporting `MC > state_dim`. This is either a
  measurement artefact, a different `state_dim` definition than the one coded, or an error.
  Do not adjudicate which; flag and report the rate.
- Finite-sample estimation inflates MC. Long input sequences are required to suppress it, 
  published practice runs to tens of thousands of samples. Code `mc_sequence_length_stated`
  and treat MC reported without a sequence length as **not comparable**.

**Cross-family warning, restated from `taxonomy-v1.0.md` §4 and §6.** MC normalized by
"number of nodes" is not comparable across families. F2's virtual node count and F4's probe
count are not F1's N. A1 and A4 must compare MC only within a family, or against the
absolute bound. This is one of the concrete places where substrate-first taxonomies produce
invalid comparisons, and it should be cited as such in the manuscript.

### 3.4 Information processing capacity: `ipc`

**`T_res`: unset. Excluded from A4.** Used as a validity check only.

Total IPC is bounded by the number of linearly independent state variables for a
fading-memory system (Dambre et al. 2012). Flag `ipc_exceeds_bound` as for MC. IPC is the
most principled property measure in the field and its *low adoption rate* relative to
NARMA-10 is a descriptive finding worth reporting on its own.

### 3.5 Chaotic-system prediction: `lorenz`, `rossler`, `mackey-glass`, `kuramoto-sivashinsky`

| | Value | Grade |
|---|---|---|
| Metric | Valid prediction time (VPT), in Lyapunov times | |
| `T_triv` | unset; 0.5 λt retained for sensitivity analysis | C |
| `T_res` | 1.0 λt difference, sensitivity only | C |

Reported VPTs span an extraordinary range, reaching above 30 λt for noiseless systems where
overfitting helps. No sourced baseline value is carried: both previously recorded baselines
failed verification (see the anchor history below).

> **Anchor 7, partially verified 2026-08-02, with a unit error corrected.**
>
> - **Upper end, VERIFIED.** Hurley and Shaheen, arXiv:2508.06730 (2025), abstract: "We
>   report high VPT values (>30 Lyapunov times)", for a noiseless Lorenz system.
> - **The "~2.87 λt baseline" was a UNIT ERROR and is corrected to ~2.6 λt.** Read from the
>   primary PDF text of Racca and Magri, arXiv:2106.09780: "The NRMSE remains below the
>   threshold of 0.2 until t ≈ 2.87, which corresponds to approximately 2.6 Lyapunov times
>   (leading Lyapunov exponent of approximately 0.9)." **2.87 is in model time units, not
>   Lyapunov times.** Our draft carried it as 2.87 λt, which is the same figure divided by
>   the very quantity that makes VPT comparable across systems.
> - **Lower end, 0.03 λt: NOT LOCATED.** No primary source found. The claim is weakened to
>   "well below 1 λt", which the sources above support, rather than retained at a precision
>   nothing establishes.

> **Anchor 7, second failure, 2026-08-20 (deviation D15): the "~2.6 λt baseline" is
> REMOVED. The 2026-08-02 unit correction above was performed against a misidentified
> primary.** An internal pre-submission review flagged the `Racca2021` bibliography entry,
> and re-verification established that the entry had fused two real papers: Racca and
> Magri's author pair was attached to the title and arXiv identifier of **Huhn and Magri**,
> *Gradient-free optimization of chaotic acoustics with reservoir computing*, Phys. Rev.
> Fluids 7, 014402 (2022), arXiv:2106.09780. That paper studies a Rijke tube (leading
> Lyapunov exponent ~0.12), contains no Lorenz case, and does not contain the quoted
> sentence. Racca and Magri's actual paper (*Robust Optimization and Validation of Echo
> State Networks for learning chaotic dynamics*, Neural Networks 142, 252-268 (2021),
> arXiv:2103.03174) matches the sentence's parameters (error threshold 0.2, Lorenz LT ≈
> 1.1, so 2.87 time units ≈ 2.6 λt) but does not contain the sentence in its arXiv text
> either; nor do Doan, Polifke and Magri's physics-informed ESN papers (arXiv:1906.11122,
> arXiv:2011.02280, Lorenz, λ = 0.934, threshold 0.2). The sentence's source is unlocated,
> so under §5's rule the value is unset, not downgraded. The block above is retained
> unedited on the same principle as the anchor-1 record: the sequence is the evidence. What
> it now shows is sharper than the anchor-1 lesson: **a quantity can pass a verification
> pass, acquire a documented correction, and still be unsourced, because the verification
> itself can be run against the wrong primary.** What remains usable from this anchor:
> the >30 λt upper end, and the verified fact that validity thresholds differ across
> studies (0.2 in Racca and Magri; 0.4 in Hurley and Shaheen), which is the comparability
> point §3.5 needs.
>
> **The two verified endpoints do not share a definition, and that is the finding.** Hurley
> and Shaheen threshold VPT at a normalized squared difference of 0.4; Racca and Magri
> threshold at NRMSE 0.2. The headline "0.03 to 30+ λt range" is therefore partly an
> artefact of inconsistent thresholds rather than a pure statement about reservoir quality.
> This is direct evidence for the `vpt_threshold_stated` companion code below, and for
> specifying `T_res` as a minimum resolvable *difference* rather than an absolute level.
>
> One further concept worth carrying into §5: Hurley and Shaheen define a **Valid Ground
> Truth Time**, the period over which independent numerical solvers still agree, and note
> that "a VPT exceeding the VGTT is not meaningful". That is a saturation ceiling set by the
> integrator rather than by the reservoir, and it belongs in the saturation discussion.

**This spread is the point.** A range spanning three orders of magnitude on the same nominal
task means VPT differences below about one Lyapunov time carry no information without
reported dispersion. `T_res` is therefore specified as a **minimum resolvable difference**,
not an absolute level: for these tasks, `below_discrimination` is set when a paper claims
superiority over a comparison on a VPT margin under 1.0 λt **without reporting dispersion**.

`T_triv = 0.5 λt` marks predictions that barely outlast the system's own error-doubling
time.

**Required companion codes**, without which VPT is uninterpretable:

- `vpt_threshold_stated`, the error level defining "valid" (definitions differ, and a
  looser threshold mechanically yields a longer VPT).
- `vpt_lyapunov_stated`, the λ used for normalization.
- `vpt_n_trials`, VPT is highly variable across initial conditions; a single-trajectory VPT
  is not a measurement.

**Where a paper reports NMSE at a fixed horizon instead of VPT**, code the metric as reported
and set both thresholds `unset`. Fixed-horizon errors on chaotic systems are not comparable
across papers using different horizons, and manufacturing a conversion would be worse than
excluding.

### 3.6 Spoken digit recognition: `spoken-digit`

| | Value | Grade |
|---|---|---|
| Metric | WER / classification error | |
| `T_res` | 0.5% WER, sensitivity only | C |
| `T_sat` | ~0.1% | B |

Reported WERs on the standard small-vocabulary setup run to a few hundredths of a percent,
which is effectively perfect. The widely circulated 0.014% figure is sourced to Brunner et
al. 2013, which states it as (0.014 +0.051/-0.014)% at one operating point (§5, anchor 8,
recovered 2026-08-27 under D17); other sourced values are 0.04%, 0.2% and 0.4%. At that
level, differences between systems reflect preprocessing choices (commonly a Lyon ear-model
front end) and dataset split rather than reservoir quality.

*This paragraph read "could not be located in any primary source" until 2026-09-05. That
statement was correct when written on 2026-07-31 and false from 2026-08-27, when the D17
block below located the figure; it is corrected here because a live sentence contradicting
a superseding block on the same page is the documentation failure this project reports.*

> **Anchor 8 recovered, 2026-08-27 (deviation D17).** The 0.014% figure is in Brunner et al.,
> Nat. Commun. 4, 1364 (2013), read from PMC3562454: "we achieved a very low classification
> error of (0.014+0.051/-0.014)% for I_b=7.7 mA ((0.64+/-0.17)%, I_b=7.6 mA) for optical
> (electrical) injection at a laser bias current close to the laser threshold. A classification
> error of 0.014% corresponds to one misclassification per ~7,000 digits, with an uncertainty
> that was limited by the size of the database", and in the discussion "the lowest reported
> error rate (0.014%)". Yan et al. (2024) cite exactly this paper (their ref. 58) for "WER is
> reaching near-perfect levels (0.014%)"; the 2026-07-31 pass consulted the review's sentence
> and did not follow its reference, although the primary was already in `references.bib` as an
> F2 exemplar. Status: the value is sourced. Its qualifiers are an asymmetric interval three to
> four times the value and a single operating point, so it is a saturation illustration
> (`T_sat` context) and not a threshold; `T_sat ~0.1%` (B) and `T_res 0.5%` (C) are unchanged.
> The sentence above stands with 0.014% added as the lowest sourced value.

**`T_triv`: unset**, because a trivial baseline depends on class balance and vocabulary size.
Code `base_trivial_present` instead, on a saturated benchmark, absence of a trivial baseline
is the more informative measurement.

**Flag `preprocessing_stated`.** Where a frequency-domain front end does most of the work,
the reservoir's contribution is not separable from the preprocessing, and the paper cannot
support a claim about the reservoir. Expected to be a common and consequential gap.

### 3.7 Channel equalization: `channel-equalization`

**`T_triv`, `T_res`: unset. Excluded from A4.**

Multiple incompatible formulations circulate under this name, differing in channel model,
SNR, and symbol alphabet. Record the formulation; report formulation diversity as a
descriptive finding. This is the same failure mode as NARMA-N and should be presented
alongside it: two of the field's standard tasks are not single tasks.

### 3.8 Kernel rank / generalization rank: `kernel-rank`, `generalization-rank`

**Excluded from A4.** Both are bounded above by the state dimension. Use as validity checks
(`kr_exceeds_bound`, `gr_exceeds_bound`) and report the KR−GR separation descriptively where
both are given. RCbench implements both; a record using RCbench inherits its definitions,
which should be coded in `metric_defined`.

### 3.9 Santa Fe laser, MNIST variants, NLT, real-world tasks

**Excluded from A4.**

- `santa-fe`, no established triviality anchor in the RC literature; report usage rate only.
- `mnist-variant`, image classification is not a temporal task; its use in RC is itself
  worth reporting descriptively, and comparison against the broader ML literature is out of
  scope.
- `nlt`, RCbench-defined; inherits its definitions.
- `real-world`, heterogeneous by construction. **The share of the corpus using any
  real-world task is a headline descriptive statistic** and connects directly to the
  deployment argument in §8.

---

## 4. Summary

| Benchmark | `T_triv` | `T_res` | In A4 | Grade |
|---|---|---|---|---|
| `narma-10` | **0.16 NMSE** = 0.4 NRMSE | 0.05 NMSE, sensitivity only | ceiling only | B / C |
| `narma-n` | unset | unset | ❌ | n/a |
| `memory-capacity` | bound check | unset | bound check only | A |
| `ipc` | bound check | unset | ❌ | n/a |
| `lorenz`, `rossler`, `mackey-glass`, `kuramoto-sivashinsky` | unset | 1.0 λt, sensitivity only | sensitivity only | C |
| `spoken-digit` | unset | 0.5% WER, sensitivity only | sensitivity only | C |
| `channel-equalization` | unset | unset | ❌ | n/a |
| `kernel-rank`, `generalization-rank` | bound check | unset | ❌ | n/a |
| `santa-fe`, `mnist-variant`, `nlt`, `real-world` | unset | unset | ❌ | n/a |

**Confirmatory coverage is deliberately narrow.** NARMA-10 is scored against its grade-B
triviality ceiling, and memory-capacity results are checked against the analytic bound. The
remaining values appear only in labelled sensitivity analyses.

Partial coverage honestly reported beats full coverage built on unsourced anchors. The reason
several standard tasks cannot be given a threshold, which is that no canonical
parameterization exists, is itself one of the paper's findings. So, now, is the fact that the
most-used benchmark of all circulates with inconsistent metric labels despite having a
traceable trivial baseline.

---

## 5. Before freeze: required verification

Every anchor in §3 was established from secondary summaries during scoping. **Each must be
confirmed against the primary source before this document freezes**, and the citation
recorded inline. Anchors that fail verification are downgraded to grade C or unset, not
retained on the strength of having been convenient.

| # | Anchor | Status | Notes |
|---|---|---|---|
| 1 | NARMA-10 trivial-predictor ceiling, 0.16 NMSE = 0.4 NRMSE | **RECOVERED 2026-08-02** | The attribution failed, not the number. Sourced to Appeltant 2011 (as NRMSE 0.4) via Vinckier 2015 (as NMSE 0.16). Shift register, not linear reservoir. Grade B. See §3.1. |
| 2 | Shift-register NARMA bound ≈ 0.434 | **RE-SEPARATED 2026-08-27 (D16)** | The primary (Vidamour et al. 2023) does say ~0.434: the authors' own shift-register NMSE for a NARMA-N variant with autocorrelated inputs, no citation. Not Appeltant's value; not merged with anchor 1; excluded from thresholds. The 2026-07-31 "~0.4" quotation and the 2026-08-02 merger were this project's errors. |
| 3 | NARMA-10 dispersions (±0.0095 at 0.0484; ±0.0142 at 0.0463) | **VERIFIED** | Exact match in Vinckier et al., *Optica* 2015 §4.B, at N=300. Dispersion is over 10 repetitions of one system. `T_res` upgraded to B. |
| 4 | NARMA-10 divergence and input-range dependence of IPC | **VERIFIED** | Kubota, Takahashi & Nakajima, arXiv:1906.04608v5. See below. |
| 5 | `MC ≤ N`; `MC = N` for linear activation | **CORROBORATED, condition added; then VERIFIED 2026-08-27** | Jaeger (2002), GMD Report 152. Multiple independent secondary sources agree, and each states a condition our draft omitted: the bound holds for i.i.d. input. The primary was read on 2026-08-27 by rasterizing the author-hosted PDF (no text layer); see the sweep block below. This row previously attributed the report to 2001, the year the author's own publications page circulates; the report imprint says 2002. |
| 6 | IPC totality for fading-memory systems | **VERIFIED** | Dambre et al., *Sci. Rep.* 2, 514 (2012). Read from the open-access primary. See below. |
| 7 | VPT range 0.03-30+ λt, ~2.87 λt baseline | **PARTIAL, then baseline REMOVED 2026-08-20 (D15)** | >30 λt verified (arXiv:2508.06730). The "2.87 → ~2.6 λt" unit correction of 2026-08-02 was made against a misidentified primary (a fused bibliography entry); the sentence is unlocated in any candidate primary and the baseline is unset. 0.03 λt not locatable. The two verified sources use different VPT thresholds (0.2 vs 0.4). See §3.5. |
| 8 | Spoken-digit WER 0.014% | **RECOVERED 2026-08-27 (D17)** | Stated in Brunner et al. 2013 as (0.014+0.051/-0.014)% at one operating point, one error in ~7,000 digits; Yan 2024 ref. 58. The 2026-07-31 "not locatable" was a false negative. Saturation illustration only; see §3.6. |

### Anchor 4, verified

Read from the primary text (arXiv:1906.04608v5, 28 May 2021). Note the **title correction**:
the paper is *A Unifying Framework for Information Processing in Stochastically Driven
Dynamical Systems*, by Kubota, Takahashi and Nakajima. "Dynamical Anatomy of NARMA10
Benchmark Task" was the v1 title and still circulates on indexing sites, which is how the
wrong title entered our draft. Any published-version details remain to be checked.

Supported claims, with the wording found in the text:

- Divergence: "y_t in the vicinity of the fixed-point can diverge depending on the input",
  and it "can potentially diverge depending on the initial values, input time-series, and
  parameter settings".
- Input-range dependence: Figure 2 reports "the IPC breakdown relative to σ and the
  probability that y_t does not diverge, p", for input ranges [−σ, σ] and [0, σ].
- A replacement is proposed: Appendix E, Figure E1, "The proposed model for the benchmark
  task", compares NARMA10 against the authors' model across both input ranges.

Also useful and consistent with §3.4: "Since the NARMA10 model is a one-dimensional system,
the total capacity is one."

### Anchor 6, verified

Read from the open-access primary (PMC3400147). Theorem 4: "the sum of the capacities for
these functions is bounded by the number N of output functions". Theorem 7 gives the equality
condition: for a system with fading memory and linearly independent internal variables, "the
sum of the capacities for the sets Y_L tends towards the number N of output functions".

Note the bound is stated in terms of **output functions**, meaning the state variables
actually read out. That is the quantity §3.3 and §3.4 use, and it is not the same as a node
count, a virtual node count, or a probe count.

### Anchor 8, failed

*Superseded 2026-08-27 (D17): located in Brunner et al. 2013; see §3.6. Retained unedited.*

The figure of 0.014% word error rate on spoken digit recognition could not be located in any
primary source. It entered our draft via a description of a figure in Yan et al. (2024).
Sourced values on the standard TI-46 setup are 0.04%, 0.2% and 0.4%, none of them yet read in
their own primary texts.

The saturation argument in §3.6 survives this: an error rate of a few hundredths of a percent
saturates a benchmark just as thoroughly as 0.014% does. Only the number changes, and
The provisional `T_res = 0.5% WER` is unaffected, but remains grade C. The specific figure must be removed from the manuscript
rather than retained because it is more striking.

### A note on the 0.16 claim

Worth recording because it bears on the paper's own thesis. Repeated searching continues to
return the assertion that "the best performance achievable with no nonlinearity in the
reservoir is NMSE = 0.16", phrased almost identically each time. Checking the source it is
attributed to found no such statement (§3.1).

A quantity that circulates widely, is repeated in consistent wording, and cannot be traced to
a primary text is a small instance of exactly the condition this audit is designed to measure.
It should not be cited, and it may be worth a sentence in §5.3 as an illustration rather than
merely a gap.

### Anchor 3, verified

Read from the primary PDF of Vinckier, Duport, Smerieri, Vandoorne, Bienstman, Haelterman and
Massar, *High performance photonic reservoir computer based on a coherently driven passive
cavity*, **Optica 2(5), 438-446 (2015)**, arXiv:1501.03024. Section 4.B:

> "The performance for the NARMA10 task strongly depends on the number of internal variables.
> Upon increasing the number of internal variables to N=300, we obtained NMSE=0.0484±0.0095 in
> experiment, and NMSE=0.0463±0.0142 in simulation. These results were obtained with α=0.806
> and Δφ scanned in the range [0.26,2.35]rad."

Both pairs match the anchor exactly. Three qualifiers travel with them and are recorded
because omitting any one would overstate the anchor:

1. **N=300**, not the N=50 used for most of that paper's other results. Dispersion is
   reservoir-size dependent, so this is not a general NARMA-10 dispersion.
2. **"The standard deviation was evaluated by repeating this procedure 10 times."** Ten
   input series, one system. This is run-to-run dispersion, not between-implementation
   dispersion, and therefore a lower bound on cross-paper spread.
3. The paper defines its NMSE explicitly at eq. (6) as a squared-error ratio. That definition
   is what makes the anchor-1 conversion above checkable, and it is the exception rather than
   the rule in this literature.

### Anchor 7, partially verified, baseline later removed

Detail in §3.5. In summary: the >30 λt upper end is verified from arXiv:2508.06730; the
"~2.87 λt" baseline was first corrected as a unit error to ~2.6 λt (2026-08-02) and then
removed entirely (2026-08-20, D15) when the attributed primary turned out to be a fused
bibliography entry and the sentence could not be located in any candidate primary; the
0.03 λt lower end could not be located and the claim has been weakened accordingly. The two
verified sources use different VPT thresholds, which is itself recorded as a finding.

### Status, as recorded on 2026-08-02

> **Superseded 2026-08-27 by D15, D16 and D17; see "Standing after the third pass" below.**
> Retained unedited on this document's standing principle: the sequence is the evidence.
> Three of the dispositions summarised here were later reversed by a primary read, so the
> tallies in this subsection are the *superseded* ones and must not be quoted.

**Seven of eight anchors resolved as of 2026-08-02.** One remains: the 0.03 λt lower end of
anchor 7, now excluded from the text rather than carried unsourced.

| Outcome | Anchors |
|---|---|
| Verified against a primary source | 3, 4, 6, and the upper end of 7 |
| Corroborated with a condition added | 5 |
| Recovered after a failed attribution | 1 (with a metric correction), 2 (merged into 1) |
| Corrected, then removed on re-verification | the 2.87 figure in 7 (unit error 2026-08-02; source unlocated 2026-08-20, D15) |
| Failed, not locatable | 8, and both the 0.03 λt end and the ~2.6 λt baseline of 7 |

**What the completed pass shows.** Of eight anchors, **one was correct as recorded**
(anchor 3). Four were substantially right but wrong in a detail that changes their meaning:
a metric (1 and 2), a unit (7), a missing condition (5). Two were verified as stated (4, 6).
One could not be sourced at all (8). Restating that as the rate that matters: **five of eight
anchors required correction before they could be used, and every one of those five was a
number our own draft had recorded as established.**

The correction rate is the point, and the shape of the corrections is more interesting than
the count. None of the five was fabricated. Each was a real measurement that had lost the
qualifier making it interpretable, somewhere between the primary text and us: the metric it
was computed in, the unit it was expressed in, the input distribution it assumed. That is a
more specific and more damaging claim than "the literature contains errors", and it is the
claim §5.3 should make, with these eight anchors as the worked evidence.

**Standing after the third pass, 2026-08-27 (D16, D17).** Eight statements, eight distinct
quantities. Anchors 1 and 2 are separate after all, and anchor 8 has a primary.

| Outcome | Anchors |
|---|---|
| Verified against a primary source | 3, 4, 5 (from 2026-08-27, see below), 6, the upper end of 7, and 8 (with its interval and operating condition restored) |
| Recovered after a false negative | 1 (2026-08-02), 8 (2026-08-27) |
| Un-merged and excluded from thresholds after a false correction | 2 (2026-08-27) |
| Corrected, then removed on re-verification | the baseline in 7 |

> **Anchor 5 verified, 2026-08-27 (pre-submission bibliography sweep).** The GMD Report 152
> PDF has no extractable text layer, which is why the 2026-08-02 pass recorded the anchor as
> corroborated from secondary statements with the primary unread. Rasterizing the
> author-hosted PDF makes it readable. Page 13: "Our fist goal is to show that if the input
> signal is i.i.d., then MC ≤ N" [sic "fist"]. Proposition 2 (p. 16): "The memory capacity
> for recalling an i.i.d. input by a N-unit RNN with linear output units is bounded by N",
> followed directly by "Both conditions (i.i.d. input and linear output units) are necessary
> for this bound", a constant-input counterexample, and a demonstration that an ESN reaches
> MC = 25.5 > 20 = N on input with temporal dependencies (p. 17). Page 18, for a network
> linear throughout: "the forgetting curve is monotonically decreasing, and that generically
> MC = N", again under i.i.d. input. Every element of the anchor as recorded (the bound, the
> equality case, and the i.i.d. condition our draft had omitted) is stated in the primary.
> The disposition category is unchanged: the meaning-changing correction was the restored
> condition, and that stands; only the verification basis improves from corroboration to a
> primary read. Also recorded: the author's own publications page lists Report 152 under
> 2001 while the report imprint reads "Publication date March 28, 2002", which explains the
> 2001 citations circulating in the literature, and which had leaked into two of this
> project's own documents before this sweep corrected them.

Five of eight quantities required a meaning-changing correction or removal (1, 2, 5, 7, 8), two
were verified as stated (3, 6) and one needed only a bibliographic correction (4). Four of the
eight dispositions recorded in the first two passes (1, 2, 7, 8) were later reversed by reading
a primary text. That second number is the one this document exists to keep visible: the
verification record failed at the same rate as the statements it verified, and every reversal
came from a primary read rather than from re-reading the record.

This document remains **draft** and the freeze still waits on `codebook.md` §14 item 2, which
closes at the pilot.
