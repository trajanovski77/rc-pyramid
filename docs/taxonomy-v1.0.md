# RC-PYRAMID: Master Taxonomy Specification

**Version:** 1.0 (FROZEN)
**Status:** Frozen. The `protocol.md` §7 pilot was run on 2026-09-05 and **passed both
criteria**: Cohen's kappa 0.9542 on family over 40 records and the six-category vocabulary
(raw agreement 97.5%, Gwet's AC1 0.9719, Krippendorff's alpha 0.9548), and an unassignable
rate among mutually-eligible records of 3.2% for each coder against the <=5% criterion. The
gate is met on §7's criterion as written; the D29 carve-out is applied and is not required
for the result. An earlier attempt on a separate sample failed and is recorded under D23 and D24. Full result: `data/screening/pilot/pilot_agreement.json`.
**Freeze date:** 2026-09-05
**Change policy after freeze:** No changes to Tier 0-2 definitions, the assignment
procedure, or facet controlled vocabularies. Additions to the Tier-3 exemplar lists and
to §11 (edge-case rulings) are permitted and must be appended with a date and the
triggering record ID. Any change requiring a Tier 0-2 edit invalidates the freeze and
forces a re-code of all records processed to that point.

---

## 0. Purpose and scope

This document defines the classification instrument used throughout the audit. It has
two jobs, and they must not be confused:

1. **Membership**: deciding whether a record belongs to the strict RC core or to an explicit
   coverage exception (§1). This is the audit's inclusion criterion.
2. **Classification**: assigning an included record to exactly one family and subclass
   (§2-§6), plus a facet vector (§7).

The instrument is designed to be applied *mechanically by two independent coders*. Every
definition below is written to be checkable against a paper's own reported methods. Where
a judgement call is unavoidable, §11 gives a ruling.

**Design principle.** The hierarchy uses a single axis: *the state-generation principle*,
i.e. the mechanism by which the reservoir produces a high-dimensional state carrying
input history. Substrate, readout method, adaptation scheme, operating mode, task, and
evidence maturity are **not** levels of the hierarchy. They are orthogonal facets (§7).
This is the specific correction relative to prior taxonomies, which split at the top level
on substrate (Tanaka et al. 2019; Liang et al. 2024), application domain (Zhang & Vargas
2023), or task class (Wringe et al. 2025).

---

## 1. Tier 0: the RC Contract (membership test)

A system belongs to the **strict RC core** if and only if it satisfies all three invariants.
The audit additionally includes the flagged coverage exceptions in §1.2 so that its corpus
matches the field's usage. Those exceptions are not described as satisfying the strict core.

> **I1: State map.** There exists a state vector `x(t)` of dimension `N > 1` that depends
> on the input history `u(≤t)` through a nonlinear map.
>
> **I2: Untrained by task error.** The parameters governing that map are not adjusted
> using the task's error/loss signal. They may be random, hand-designed, physically
> determined, hyperparameter-searched, or adapted by a task-agnostic (e.g. unsupervised)
> rule, but no gradient or error signal from the target output may flow into them.
>
> **I3: Trained readout.** An output is produced by a map from `x(t)` whose parameters
> *are* fit to the task, typically by linear regression.

### 1.1 Membership decision procedure

Apply in order to assign strict-core membership. A record excluded here is checked against
the explicit coverage exceptions in §1.2 before final audit exclusion.

1. **Is there a state vector of dimension > 1 that depends nonlinearly on input history?**
   No → **EXCLUDE** (`not-rc:no-state-map`).
2. **Does any task error signal reach the state-map parameters** (backpropagation through
   the reservoir, joint end-to-end training, error-driven weight updates inside the
   reservoir)? Yes → **EXCLUDE** (`not-rc:trained-internals`).
3. **Are readout parameters fit to the task?** No → **EXCLUDE**
   (`not-rc:no-trained-readout`).
4. Otherwise → **INCLUDE, strict core**.

### 1.2 Rulings on recurring membership disputes

| Case | Ruling | Reason |
|---|---|---|
| Hyperparameter search over spectral radius, leak rate, input scaling | **INCLUDE** | Search over a scalar design space is not error-driven parameter training. Code `D3 = hp-optimized`. |
| Intrinsic plasticity / unsupervised pre-shaping of reservoir weights | **INCLUDE** | Task-agnostic adaptation. Code `D3 = unsupervised`. |
| Evolutionary/genetic optimization of the reservoir **using task fitness** | **INCLUDE, flagged** | Contested: task fitness is an error signal, but is not backpropagated and the field treats these as RC. Code `D3 = evolved` and set `membership_flag = contested-evolved`. Report separately. |
| Backpropagation-through-time into reservoir weights | **EXCLUDE** | Violates I2. This is an RNN. |
| Extreme Learning Machine, no temporal input | **INCLUDE if temporal, else EXCLUDE** | An ELM applied to static input has no input *history*, failing I1's history dependence. Code `not-rc:static-input`. |
| Next-Generation RC (NG-RC) | **INCLUDE, flagged** | See §5; rulings are appended in §11. Set `membership_flag = f3-weak-i1`. |
| Quantum reservoir computing | **INCLUDE** | Satisfies all three invariants. Not a family, see §11 ruling R5. |
| Deep RC where **only** readouts of each layer are trained | **INCLUDE** | Satisfies I2. |
| "Deep RC" where inter-layer weights are trained by task error | **EXCLUDE** | Violates I2. |
| Physical system where an internal bias/control is tuned to improve task accuracy | **INCLUDE, flagged** | Code `D3 = physically-tuned`, `membership_flag = contested-insitu`. |

**Coding rule.** `membership_flag` is a required field. Flagged records are included in the
main corpus and reported separately in every analysis, so a reader who disagrees with a
ruling can subtract them.

---

## 2. Tier 1: family assignment procedure

Apply in order. Stop at the first decisive answer. Assign exactly one **primary** family.

1. **Does the state depend on any internal variable carried across time steps?**
   If **no**, meaning the state is a function of an explicit finite window of inputs
   only, assign **F3** (Explicit-Feature).
2. **Is the dominant memory mechanism a propagation delay, with the state vector obtained
   by sampling one or few physical nodes across a delay interval** (time-, frequency-, or
   wavelength-multiplexed "virtual nodes")? If **yes**, assign **F2** (Delay-Embedded).
3. **Are the state variables individually addressable units with a specified coupling
   structure** (a weight matrix, a designed network topology, a fabricated array)?
   If **yes**, assign **F1** (Recurrent-Network).
4. **Otherwise**: the state is sampled at probe positions in a medium whose internal
   coupling is not designed, not individually addressable, or not fully known, assign
   **F4** (Distributed-Medium).

### 2.1 Hybrids

**Revised 2026-09-05 (deviation D18).** The rule below replaces one that assigned the
primary family to "the component that generates most of the state dimension". That rule
contradicted §4 and §6 of this document and the manuscript's own central argument: a
nominal state dimension is not the same object across families, so it cannot be used to
rank two components against each other. The superseded wording is recorded in the deviation
log. No record had been coded under it; the preliminary check of 2026-08-28 recorded zero
hybrids, so nothing requires re-coding.

Where a system genuinely combines mechanisms, the **primary** family is the one whose
mechanism dominates state generation. Dominance is judged from the reported memory
mechanism and never from a reported count: the dominant component is the one whose removal
would eliminate the system's dependence on input history. Record the other component as a
**secondary** family in `family_secondary`.

Where the report does not establish dominance, **do not assign a primary family**. Record a
symmetric hybrid label in `family_symmetric`, written `F1×F2` with the codes in ascending
order, leave `family` empty, and set `family_ambiguous = true` with a note. Forcing a
primary family on a system whose report does not support one manufactures a precision the
source does not contain, which is the failure this instrument exists to detect.

The hybrid rate and the symmetric-label rate are both reported findings.

### 2.2 Discriminators at a glance

| | Internal state across steps | State dimension comes from | Nodes individually addressable |
|---|---|---|---|
| **F1** | yes | individually addressable units, coupled or independently dynamic | yes |
| **F2** | yes | time/frequency multiplexing of few nodes | few, repeatedly sampled |
| **F3** | **no** | explicit delay window + fixed feature map | n/a |
| **F4** | yes | spatial probes in a medium | no / not by design |

---

## 3. F1: Addressable-Node Reservoirs

**Renamed 2026-09-05 (deviation D19); previously "Recurrent-Network Reservoirs".** The
family's discriminator in the §2 procedure is that state variables are individually
addressable units with a specified coupling structure, not that they are recurrently
coupled. A fabricated array of individually driven dynamic devices with no inter-device
coupling satisfies the discriminator and fails the old name, which the memristor-array
worked example in the manuscript exposed. Recurrent networks remain the family's dominant
members and its original motivation; the name now states the discriminator instead of the
dominant subclass.

**Definition.** The state is a vector of individually addressable units whose
interconnection structure is specified. Memory arises either from recurrent coupling among
those units or from the units' own internal dynamics, or from both.

**Memory mechanism.** Recurrent feedback through a coupling matrix, with fading memory from
contractive dynamics; or, where the units are not coupled to one another, relaxation
internal to each unit. Which of the two applies is recorded in the subclass.

**Capacity scaling.** Linear memory capacity is bounded by the number of independent state
variables (`MC ≤ N`, Jaeger 2002; generalized by Dambre et al. 2012, whose total
information processing capacity equals the number of linearly independent state variables
for a fading-memory system). This bound is the family's defining constraint and should be
used in the audit to check reported capacities for plausibility.

**Typical failure modes.** Loss of echo state property at high spectral radius; capacity
saturation; ill-conditioned readout regression at large `N`.

### Subclasses

| ID | Name | Discriminating criterion |
|---|---|---|
| **F1.1** | Rate-based / analog-state | Continuous-valued node activations; leaky-integrator or tanh-type update. The default ESN. |
| **F1.2** | Spiking / event-driven | Node state is a spike train; readout operates on spike counts, rates, or filtered traces. The LSM lineage. |
| **F1.3** | Hierarchical & multi-timescale | Two or more reservoir stages in sequence, each with its own state, readouts taken per layer or from the concatenation. |
| **F1.4** | Structured-topology | Coupling matrix is deliberately constrained rather than random: simple cycle, delay-line, small-world, modular, block-diagonal, locally-connected. |
| **F1.5** | Coupled-oscillator / phase-encoded | Node state is a phase or oscillation amplitude; coupling is oscillatory. Includes spin-torque oscillator arrays and ring-oscillator arrays. |
| **F1.6** | Uncoupled dynamic nodes | Individually addressed units with **no** inter-unit coupling; each unit's own relaxation or short-term memory supplies the input-history dependence, and the state vector is the collection of their responses. Added 2026-09-05, D19. |

**Note on F1.6 vs F1.1 and F4.** F1.6 requires that the units be individually addressed and
their arrangement specified, and that no coupling between them is reported. If the units are
coupled, code the coupling-based subclass. If the units are not individually addressable, or
the interconnection is not designed or not known, the record is F4, not F1.6: the F1/F4
boundary remains addressability and a specified structure, unchanged by this subclass.

**Note on F1.4 vs F1.1.** A randomly generated sparse matrix is **F1.1** (sparsity is an
initialization detail). **F1.4** requires that the topology be the paper's object of study
or an explicit design claim.

**Note on F1.5 vs F2.** An *array* of coupled oscillators, each separately read, is F1.5.
A *single* oscillator sampled across a delay line is F2.1.

---

## 4. F2: Delay-Embedded Reservoirs

**Definition.** Memory arises from propagation delay around a feedback loop. The physical
system has few nodes (often one); the state vector is constructed by sampling that node at
`N` points across one delay period, the "virtual node" construction.

**Memory mechanism.** Signal transit time in the delay line; the ratio of delay `τ` to node
response time `θ` sets the number of resolvable virtual nodes.

**Capacity scaling.** With `N = τ/θ`. Capacity is governed by the delay-to-response-time
ratio rather than by a node count, which is why F2 systems can present very large nominal
state dimensions from a single physical element, and why comparing an F2 "500-node"
result against an F1 "500-node" result is not like-for-like. **This is a central point for
the audit's benchmark-comparability analysis.**

**Typical failure modes.** Virtual-node crosstalk when `θ` is not well separated;
sensitivity to delay-line stability and drift; the state is not simultaneously available,
which constrains real-time readout.

### Subclasses

| ID | Name | Discriminating criterion |
|---|---|---|
| **F2.1** | Single-node time-multiplexed | One nonlinear element, one delay loop, virtual nodes by time multiplexing. |
| **F2.2** | Multi-delay / multi-loop | Two or more distinct delay paths or loop lengths. |
| **F2.3** | Frequency- / wavelength-multiplexed | Virtual nodes separated in frequency or wavelength rather than (or in addition to) time. |
| **F2.4** | Deep / cascaded delay stages | Two or more delay reservoirs in sequence, state taken per stage or concatenated. |

---

## 5. F3: Explicit-Feature Reservoirs

**Definition.** No internal dynamical state is carried across time steps. The state is an
explicit, fixed nonlinear function of a finite window of past inputs.

**Memory mechanism.** The delay window itself. There is **no fading memory**: every input
inside the window is weighted by the feature map, every input outside it is invisible.

**Capacity scaling.** Set by window length `k` and feature-map order. Grows combinatorially
with polynomial order, which is the family's practical constraint.

**Theoretical note: record this in the paper.** The known criticisms of NG-RC (that it
weights all in-window history equally, is sensitive to sampling rate, and degrades sharply
under small errors in feature construction) are *predicted* by the family definition rather
than being incidental empirical observations. A taxonomy that derives a known critique from its own structural definition is evidence the cut is the right one; §10 falsification test 1 is the form in which that claim can be made to fail.

**Membership caveat.** F3 satisfies I1 only in a weakened form (state depends on input
history, but not through internal dynamics). All F3 records carry
`membership_flag = f3-weak-i1` and are reported separately throughout. This decision is
pre-registered and must not be revisited after seeing results.

### Subclasses

| ID | Name | Discriminating criterion |
|---|---|---|
| **F3.1** | Polynomial-feature | Monomials/products of delayed inputs. NG-RC proper. |
| **F3.2** | Random-feature / kernel-approximating | Random projections + fixed nonlinearity; random Fourier features; temporal ELM. |
| **F3.3** | Orthogonal-basis expansion | Legendre, Chebyshev, or similar basis over the delay window. |
| **F3.4** | Learned-basis hybrid | Basis functions themselves parameterized and fit, but **not** by task error (else excluded by I2). Includes KAN-type constructions where the fitted part is the readout. |

---

## 6. F4: Distributed-Medium Reservoirs

**Definition.** Memory arises from spatial propagation, diffusion, or relaxation in a
continuum or an unengineered mesh. The state is sampled at probe positions, not at designed
nodes.

**Memory mechanism.** Wave propagation, charge/ion transport, mechanical compliance, or
lattice update, depending on medium.

**Capacity scaling.** Governed by probe count and by the medium's spatial correlation
length; adding probes yields diminishing returns once probes fall within one correlation
length. **Probe count is not node count** and must not be compared with F1's `N`.

**Typical failure modes.** Probe placement sensitivity; strong device-to-device variability;
drift and ageing; state not reproducible across fabrication runs, all of which bear
directly on the reproducibility audit.

### Subclasses

| ID | Name | Discriminating criterion |
|---|---|---|
| **F4.1** | Random material networks | Self-assembled or percolating conductive meshes: nanowire networks, CNT-polymer composites, percolating films. |
| **F4.2** | Wave & field media | Computation in a propagating field: reverberant chambers, acoustic media, spin waves, optical scattering/speckle. |
| **F4.3** | Lattice & automata | Discrete spatial lattice with local update rules: cellular automata reservoirs, coupled map lattices. |
| **F4.4** | Mechanical / morphological | Compliant physical bodies: soft robot limbs, tensegrity structures, granular media, mass-spring systems. |

**Note on F4.1 vs F1.** A *fabricated* crossbar array with addressable devices at known
positions is **F1** (individually addressable, designed coupling). A *self-assembled*
nanowire mesh with probes placed on an unknown internal topology is **F4.1**. The
discriminator is whether the coupling structure is designed and known, not what the
material is.

---

## 7. Facets (orthogonal coding dimensions)

Every included record carries a value on each facet. Controlled vocabularies are closed;
`other` is permitted but requires a free-text note and triggers a §11 ruling if it recurs.

### D1: Substrate
`digital-simulated` · `digital-hardware` (FPGA/ASIC/GPU as the reservoir itself) ·
`analog-electronic` · `photonic` · `spintronic-magnetic` · `memristive-ionic` ·
`mechanical-soft` · `biological-organic` · `quantum` · `other`

### D2: Readout & training
`offline-linear` (ridge / least squares / pseudoinverse) · `online-recursive` (RLS, LMS,
FORCE) · `nonlinear-readout` (MLP or other nonlinear map) · `sparse-selected` (feature
selection or L1) · `in-hardware-readout` · `other`

### D3: Reservoir adaptation
`random-fixed` · `hp-optimized` · `unsupervised` (intrinsic plasticity, Hebbian,
task-agnostic) · `evolved` · `physically-tuned` · `other`

### D4: Operating mode
`open-loop` (input-driven filtering/classification) · `closed-loop` (autonomous
free-running generation/prediction) · `control-in-loop` · `hybrid-physics-informed`

### D5: Task class *(adopted from Wringe et al. 2025: cite on first use)*
`imitation` · `prediction` · `computation` · `classification` · `property-measure`

### D6: Evidence tier
`E0`-`E5`, see §8.

**Multi-valued facets.** D2, D4 and D5 may take multiple values where a paper genuinely
reports several. D1 and D6 are single-valued: where a paper reports both a simulation and a
device, split it into two records sharing a `record_group_id`. **This split rule is what
makes analysis A1 (matched-pair sim-vs-physical) possible** and must be applied
consistently.

---

## 8. RC-LADDER: evidence maturity (facet D6)

Assign the **highest tier fully supported by the paper's own reported methods**, not by its
claims. Where a paper is ambiguous between two tiers, code the **lower** and set
`evidence_ambiguous = true`. The ambiguity rate is a reported finding.

| Tier | Name | Inclusion criteria |
|---|---|---|
| **E0** | Numerical simulation | Reservoir is a mathematical model integrated numerically. No device, no device-specific model. |
| **E1** | Substrate-model simulation | Physics-based model of a specific device class. No physical device in the loop. |
| **E2** | Measured-trace emulation | A real device is measured; responses stored; the reservoir computation assembled offline from recorded traces. Includes virtual nodes composed post hoc from separate measurements. |
| **E3** | Benchtop physical reservoir | Device operates in the loop under lab conditions; readout in software; bounded session. |
| **E4** | Integrated system | Packaged or on-chip; readout integrated or co-located; sustained operation; drift/recalibration explicitly addressed and reported. |
| **E5** | Field deployment | Operating on a real task outside the lab; performance reported over an extended period; compared against an incumbent method. |

**The E2/E3 boundary is the most consequential and the most often blurred.** Decision rule:
if the input sequence used for the reported result was ever presented to the device *in the
order and at the rate* implied by the task, it is E3. If states were measured separately
and later assembled into a state matrix, it is E2.

---

## 9. RC-BOUND: efficiency measurement boundary

Applies only to records reporting energy, power, throughput-per-watt, or latency claims.
Code the boundary the claim was computed at.

| Tier | Includes |
|---|---|
| **B0** | Reservoir core only, substrate dissipation during state evolution. |
| **B1** | + input encoding, modulation, drive electronics. |
| **B2** | + state acquisition: probes, ADCs, sampling at the required bandwidth. |
| **B3** | + readout computation, pre/post-processing, amortized calibration. |

Record `efficiency_boundary` and `efficiency_boundary_stated` (whether the paper states its
boundary at all, versus the coder inferring it). The second field is the more damning
measurement and must be coded conservatively: `stated` requires an explicit sentence, not
an inference from a system diagram.

---

## 10. Falsification tests

The taxonomy is presented as an empirical instrument and must be able to fail. Assignability
is the pilot gate. Behavioural coherence and substrate crossing require the screened corpus
and are reported later as prospective validation tests.

1. **Behavioural coherence.** Members of a family should share memory-capacity scaling and
   failure modes. Run only when comparable definitions and at least three usable records per
   family are available; otherwise report the test as underpowered. *Fails if* within-family
   variance in reported capacity-vs-size scaling is not lower than between-family variance.
2. **Substrate-crossing.** Every family must have members in ≥3 distinct D1 values. *Fails
   if* any family is confined to ≤2 substrates, that family is a disguised substrate label.
   **Quantitative form, added 2026-09-05 (deviation D20).** The count above detects a family
   confined to one material but says nothing about the strength of the association in
   between, which is what the framework's claim is actually about. Analysis A6
   (`protocol.md` §9) therefore also computes the family × substrate association. *Fails if*
   the bias-corrected Cramér's V is ≥ 0.70 **and** normalized mutual information is ≥ 0.70,
   which would mean substrate very nearly determines family and the architecture axis
   carries little independent information. An intermediate association is what the framework
   predicts; it is reported as consistent with the claim and is **not** treated as
   confirmation of it, because a null result has the same signature. Both thresholds are
   fixed before any classification data exists and are recorded in `analyses.py`.
3. **Assignability.** Two independent coders applying §2 should agree. *Fails if* Cohen's κ
   on family assignment < 0.70 over the pilot sample, or if >5% of records are unassignable.
   **Basis revised 2026-09-05 (deviations D21 and D25).** κ is computed over every sampled
   record, unchanged. Two clarifications to the >5% unassignable clause, neither of which
   moves the 5% threshold:
   - **D21:** it is evaluated on the records both coders judged eligible under
     `protocol.md` §4.2, because the §2 procedure never runs on records §4.2 excludes. The
     all-records rate is reported alongside it.
   - **D25:** it is evaluated on the **full-text** pass. `protocol.md` §7 never stated an
     information basis, and two runs were coded from the abstract alone, which measures
     whether a record can be classified from its abstract rather than whether this
     instrument can classify it. `codebook.md` §0 codes from the text, tables, figures,
     captions and supplement. The abstract-pass rate is reported too, and across three runs
     it sits near a quarter of eligible records; that is a finding about reporting practice,
     not about the taxonomy.

**If assignability fails, the taxonomy is revised and the pilot re-run.** A later failure of
behavioural coherence or substrate crossing rejects the frozen taxonomy and is reported as a
negative result; it does not trigger post-hoc revision. See the change policy above.

---

## 11. Edge-case rulings

Append new rulings here with date and triggering record ID. Do not amend rulings already
issued; supersede them explicitly if genuinely wrong, and re-code affected records.

| # | Case | Ruling | Date |
|---|---|---|---|
| R1 | Paper reports both a simulation and a hardware demo | Split into two records with a shared `record_group_id`; code D1 and D6 separately. | 2026-07-31 |
| R2 | "Deep" used loosely for a single reservoir with a multilayer readout | Not F1.3. Code F1.1 with `D2 = nonlinear-readout`. Depth must be in the *state map*, not the readout. | 2026-07-31 |
| R3 | Spatially extended photonic system with designed waveguide topology | F1 if node positions and couplings are designed and addressable; F4.2 if computation is in a scattering/speckle field. | 2026-07-31 |
| R4 | Reservoir size reported as virtual node count in an F2 system | Record in `state_dim` with `state_dim_kind = virtual`. Never compare directly with F1 `state_dim_kind = physical`. | 2026-07-31 |
| R5 | Quantum RC | Not a family. Code by §2 procedure on the state map (usually F1 or F4) with `D1 = quantum`. | 2026-07-31 |
| R6 | Bank of individually addressed dynamic devices with no inter-device coupling, each contributing its own short-term memory | F1, subclass **F1.6**. Step 3 turns on addressability and a specified structure, which such an array satisfies; the absence of coupling is a subclass property, not a family boundary. Not F1.4, because the arrangement is not an object of design or analysis. Not F4, because the units are addressable and the structure is known. | 2026-09-05 |
| R7 | A record whose only architectural statement is the bare term "reservoir computing" or "traditional reservoir computing", with no stated state-generation mechanism | **Unassignable**, and never F1 by default. A next-generation RC paper describes itself against "traditional reservoir computing" in the same words, so the phrase does not discriminate F1 from F3 and cannot carry the §2 cascade. Reading it as a term of art for a random recurrent network is inference from convention, which `codebook.md` §0.1 forbids. **Nomenclature alone never decides a family, on the same grounds that substrate alone never does.** Triggering record RC-1648, from the 2026-08-28 two-coder check; both coders' reconciliation, countersigned 2026-09-05. | 2026-09-05 |
| R8 | A review, survey, tutorial or commentary reaches a classification packet | Code **the record**, never the systems the review describes, however determinate they are. Such a record is `not-primary` under `protocol.md` §4.2 and corpus-adjacent under §4.3, so it is excluded at screening and the §2 procedure never runs on it; where it does reach a packet, mark it ineligible and record the review status in the reason. Classifying the systems inside it is a unit-of-analysis error, the unit being one record. Triggering record RC-3293; same reconciliation. | 2026-09-05 |
| R9 | A journal issue **cover feature**: a record repeating an article's title and authors, in the same journal, volume and issue, sometimes with an issue tag appended to the title such as "(Adv. Sci. 3/2024)", and whose abstract reads as a cover blurb rather than as the article's abstract | **Exclude at Stage 1 with `not-primary`.** A cover feature is a distinct publication object with its own DOI, so it is **not** a duplicate and is not merged at dedup; it is carried into screening and excluded there with a stated code, which keeps it visible in the flow instead of vanishing. Recognise it from the title and abstract, which is all a Stage-1 coder is shown. **Do not test for it by reference count.** That shortcut was proposed and measured on this corpus on 2026-09-05: 15.9% of eligible records carry zero references at Crossref, most of them ordinary research articles whose publisher never deposited a reference list, and a 90-record sample of zero-reference records contained no cover feature at all. Eight such pairs were identified in the near-duplicate adjudication. | 2026-09-05 |
| R10 | A record whose only architectural statement is a **named architecture** - "echo state network", "liquid state machine" - with no further description of the state map | **Assign the family the name denotes**: ESN gives F1 / F1.1, LSM gives F1 / F1.2. R7 is unaffected and still makes the bare terms "reservoir computing" and "traditional reservoir computing" unassignable. The distinction is R7's own ground: "reservoir computing" fails because an NG-RC paper uses the identical phrase and so cannot separate F1 from F3, whereas no F2, F3 or F4 system is reported as an ESN or an LSM, and §3 already names "the default ESN" as F1.1's exemplar and F1.2 as "the LSM lineage". Where the record says more than the bare name and the addition is unresolved ("multi-reservoir", "enhanced ESN"), the family stands and the subclass is left blank. The contrary reading, that `codebook.md` §0.1 forbids any inference from a name, is recorded and rejected on scope: §0.1 governs a **field value** the paper leaves unstated, whereas an architecture name is itself a statement by the authors. That is a judgement about §0.1's reach and not a claim that §0.1 says nothing here, so a reader who reads §0.1 more broadly should expect six of pilot 2's records to move to `unassignable`, which raises that coder's eligible-only rate from 3.2% to 25.8%. Triggering records RC-0057, RC-2087, RC-2208, RC-1110, RC-2290, RC-5348, pilot 2. | 2026-09-05 |
| R11 | One record reports systems in **two different families** - not one system combining mechanisms, which is §2.1 | **Split as under R1**: two records with a shared `record_group_id`, each coded on its own system. Where a fixed sample is already drawn and the split would change n, code the record on the system whose results the **main text** reports and record the second in the reason; where both appear in the main text as co-equal comparators and neither is subordinate, the record is `unassignable` and is reported with its reason under `protocol.md` §7 rather than counted against the instrument. R1 already covers the sub-case where the two systems differ by simulation versus device; this extends it to systems differing by architecture. `family_symmetric` does not apply, because it is for a single system whose mechanisms combine and whose report does not establish dominance. Triggering records RC-0541, which resolves to F2.1, and RC-3140, which stays unassignable, pilot 2. | 2026-09-05 |
| R12 | The map from `x(t)` to the output is **unsupervised** - k-means or another clustering over the reservoir states, a self-organising map, a distance or reconstruction-error threshold - and no parameters anywhere are fit to a target output | **EXCLUDE**, `not-rc:no-trained-readout`, §1.1 step 3. I3 requires a map "whose parameters *are* fit to the task", and a clustering has no target to be fit to: its parameters are fit to the distribution of `x(t)`. The contrary reading, that cluster centroids are parameters fit to the task because they are derived from the states and produce a scored result, is recorded and rejected on the document's own vocabulary: I2 already names an "adapted by a task-agnostic (e.g. unsupervised) rule" parameter as *not* trained, and a term cannot mean untrained in I2 and trained in I3. The exclusion is about I3 alone. **It does not disturb the §1.2 ruling that unsupervised pre-shaping of the reservoir is INCLUDE**, which is an I2 question, and the common case in this literature - "only the output weights are trained" after unsupervised pre-training - keeps its trained readout and stays included. Where a record's output map is unsupervised but a separate supervised head is also fit, I3 is satisfied by the head and the record is included. Sized against the corpus: a clustering/unsupervised/anomaly-detection proxy with no supervised-readout language matches **175 records, 2.7%**, but that is an upper bound the proxy inflates - of ten sampled, most either train a readout or use the unsupervised method on the reservoir rather than the readout, so the true rate is well under 1%. Triggering record RC-1684, pilot 2, whose §2 states "since the objective of this paper is unsupervised learning, we omit the output layer, together with the regression computation"; the reading it displaces is recorded in that record's coder B reason. | 2026-09-05 |
| R13 | A system whose state vector is built by sampling **one** physical element at many points within an input interval, where the input-history dependence comes from that element's own relaxation rather than from propagation around a feedback loop | **F2**, subclass **F2.1**. Step 2's discriminator is the *sampling construction* - few physical nodes, resolved in time - and "propagation delay" names its canonical mechanism rather than a necessary one. **F4 is excluded on the axis of multiplexing, not on the mechanism**: F4 requires a spatial medium sampled at several probe positions, whereas here one element is sampled at several times, so §6's "probe count is not node count" has nothing to count. This supersedes the F2/F4 tension recorded against the Torrejon et al. (2017) worked example, which is assigned F2.1 without qualification. Triggering case: the Torrejon et al. (2017) worked example of the manuscript's Table 6, not a corpus record; no screened record exists yet, and this is recorded so the ruling's origin is not mistaken for a coding decision. Tier 0-2 definitions are untouched: §4 already defines F2 by the virtual-node construction and gives tau/theta as the resolution limit, not as the memory source. | 2026-09-15 |

---

## 12. Provenance

**Open subclass question carried to the pilot, recorded 2026-09-05.** The 2026-08-28 check
produced one record, RC-5476, that no Tier-2 list fits: an ensemble of complete
continuous-time chaotic reservoirs read out by one linear map. It is **not** F1.6, whose unit
is a node whose own relaxation carries input history and which additionally requires
individually addressed units in a specified arrangement, and it is not F1.3, which is two or
more stages **in sequence**. Whether the ensemble members are nodes or complete reservoirs is
not stated in the source. No subclass is added and no record is re-coded on the strength of
one observation: completing the Tier-2 lists is a declared output of the pilot (`protocol.md`
§7), and this is named here so the pilot does not have to rediscover it.

Families and subclasses were drawn from the literature reviewed during scoping, in two working documents that are part of the development record rather than of the released artefact; the reviews themselves are the eleven in the manuscript's Table 3. Subclass lists are **not claimed
exhaustive at v1.0**: completion is an explicit output of the pilot pass. D5 is adopted
from Wringe et al. (2025) unchanged and must be cited as such on first use in the manuscript.
The `MC ≤ N` bound is Jaeger (2002), GMD Report 152; the information-processing-capacity
generalization is Dambre et al. (2012). Both are now verified against primary sources
(Dambre on 2026-08-02; Jaeger on 2026-08-27, read from the rasterized author-hosted report,
Proposition 2 with both conditions stated as necessary). This section previously dated the
report 2001, the year the author's own publications page circulates; the report imprint
says 2002 (`benchmark-thresholds.md` §5, anchor 5).

**Cross-reference correction, 2026-09-05.** Five references in this document pointed at §9
for edge-case rulings: the §0 change policy, the §0 statement that "where a judgement call is
unavoidable, §11 gives a ruling", the NG-RC and quantum-RC rows of §1.2, and §7's rule for a
recurring `other` value. Rulings are in **§11**; §9 is the efficiency-measurement boundary, so
a coder following any of them landed on the wrong table. `protocol.md`, `codebook.md` and
`deviations.md` all cite §11 correctly, so this file was the only one misdirecting, and it is
the one the coders read. Not a deviation under `deviations.md`'s own list, which exempts a
broken path fixed with outputs regenerated, but recorded here because an instrument's
navigation is part of the instrument.

**Second cross-reference correction, 2026-09-05.** §11 R7 cites `codebook.md` §0.1, and `deviations.md` cites §0.5 twice, but `codebook.md` §0 carried its six conventions as an unnumbered list, so neither citation resolved in the file it pointed at. The conventions are now numbered §0.1-§0.6 in `codebook.md` and both citations land. Same class as the correction above and recorded for the same reason. Found while coding pilot 2.
