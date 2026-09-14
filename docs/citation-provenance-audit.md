# Citation and provenance audit

**Audit date:** 2026-08-13  
**Manuscript:** `paper/PAPER1.md`  
**Purpose:** Verify that important historical, theoretical, architectural, and quantitative
claims are attached to an appropriate source, with primary sources used where the claim is
about an original result.

## Procedure

1. Every manuscript citation key was checked against `paper/references.bib`.
2. Every cited entry was required to carry a provenance note recording its verification
   source and any qualification.
3. Original architectures, theorems, benchmark definitions, and numerical values were checked
   against primary papers rather than review articles where a primary source was available.
4. Reviews were used for claims about review organization, field synthesis, and reported
   implementation barriers.
5. Unsupported absolute claims about absence in the literature were removed or rewritten as
   bounded search findings.

The executable check is `python3 scripts/audit_manuscript.py`.

## Claim-level audit

| Claim group | Source type | Principal sources | Status and qualification |
|---|---|---|---|
| Origins of echo state networks and liquid state machines | Primary | [Jaeger2001], [Maass2002] | Verified; described as independent origins rather than a single invention |
| Early chaotic prediction and channel equalization | Primary | [JaegerHaas2004] | Verified |
| Physical implementation categories and deployment barriers | Review/synthesis | [Tanaka2019], [Yan2024], [Liang2024] | Attributed to the reviews rather than presented as an exhaustive field measurement |
| Delay-based and coupled-waveguide photonic architectures | Primary | [Brunner2013], [Vandoorne2014] | Verified; used to distinguish architecture within one substrate |
| Fading-memory origin | Primary | [BoydChua1985] | Verified |
| Spectral-radius qualification for the echo state property | Primary | [Yildiz2012], [BuehnerYoung2006], [Manjunath2013] | Claim narrowed: radius below one is a heuristic, not a general necessary-and-sufficient condition |
| Linear memory-capacity bound | Primary | [Jaeger2002] | i.i.d. input and linear-output conditions retained explicitly. UPDATED 2026-08-27 (sweep): Proposition 2 read from the rasterized report; both conditions stated as necessary in the primary |
| Information-processing-capacity bound | Primary | [Dambre2012] | Fading-memory and independent-state qualifications retained |
| Fading-memory universality | Primary | [Grigoryeva2018], [Gonon2021], [GrigoryevaOrtega2018b], [GononOrtega2020] | Existence result distinguished from constructive design guidance |
| Classical and quantum universality | Primary | [Universality2025] | Verified bibliographically and limited to the theorem's scope |
| Ordered-to-chaotic transition and rank measures | Primary | [Bertschinger2004], [Legenstein2006], [Legenstein2007] | Model-specific origin retained; no universal substrate claim |
| Structured state-space architecture and complexity | Primary | [Gu2022], [GuDao2023] | Cited for trained architecture and linear sequence scaling, not for an experimental comparison with reservoir computing |
| CHARC characterization method | Primary | [Dale2019] | Object, input, and output distinguished from paper-level classification |
| Recurrent-network and deep-reservoir exemplars | Primary | [Du2017], [Zhong2021], [GallicchioMicheliPedrelli2017], [GallicchioMicheli2017] | Verified |
| Delay-reservoir architecture and implementations | Primary | [Appeltant2011], [Larger2012], [Paquot2012], [Duport2012], [Brunner2013], [Larger2017] | Founding implementation correctly identified as analogue electronic rather than photonic |
| Explicit polynomial-feature architecture | Primary | [Gauthier2021] | Described as a flagged coverage class because it lacks dynamical state |
| Distributed-medium examples | Primary | [Torrejon2017], [Nakane2018], [Gartside2022], [Dawidek2021], [Milano2022], [Midya2019], [Hauser2011], [Nakajima2015], [Cucchi2021], [Sumi2023], [Cai2023], [MillerDowning2002], [Dale2016], [Fernando2003] | Examples retained without generalizing one substrate's behavior to the family |
| NARMA origin and input-dependent pathology | Primary | [AtiyaParlos2000], [Kubota2021] | Verified; lack of canonical parameterization stated as literature variation, not a property of the original task alone |
| NARMA trivial predictor | Primary chain | [Appeltant2011], [Vinckier2015], [Vidamour2023] | 0.4 NRMSE = 0.16 NMSE (Appeltant; converted by Vinckier). UPDATED 2026-08-27 (D16): Vidamour et al. state ~0.434 NMSE, without citation, as their own shift-register baseline for a NARMA-N variant with autocorrelated inputs; the earlier "relabelled ~0.4" reading was this project's misquotation and is withdrawn |
| NARMA dispersion near low error | Primary | [Vinckier2015] | 0.05 NMSE retained only as a grade-C sensitivity value from one implementation |
| Chaotic benchmark definitions | Primary | [MackeyGlass1977], [Lorenz1963], [Rossler1976], [Kuramoto1976], [Sivashinsky1977] | Verified historical sources |
| Valid prediction time | Primary | [Pathak2018], [PathakHybrid2018], [Vlachas2020], [Racca2021], [HurleyShaheen2025] | UPDATED 2026-08-20 (D15): the "~2.6 Lyapunov times" baseline was removed; its bibliography entry had fused two papers and the sentence is unlocated in any candidate primary. [Racca2021] corrected to the real Neural Networks 2021 paper and cited only for the 0.2 validity threshold. Heterogeneous thresholds prevent a confirmatory cutoff |
| Spoken-digit task provenance | Primary | [Doddington1981], [Lyon1982], [Brunner2013] | Verified. UPDATED 2026-08-27 (D17): the 0.014% error is stated in [Brunner2013] as (0.014+0.051/-0.014)% at one operating point; retained as a saturation illustration with its interval |
| Nonlinear channel equalization provenance | Primary | [MathewsLee1994], [JaegerHaas2004] | Verified |
| Benchmark taxonomy and software tooling | Review/tool paper | [Wringe2025], [RCbench2026] | Corrected authorship retained in bibliography notes |
| PRISMA reporting approach | Guideline | [PRISMA2020], [PRISMAP2015] | Verified; manuscript does not claim the prospective audit has been executed |
| Broader reproducibility mechanisms | Primary empirical study | [Dacrema2019], [Recht2019], [KapoorNarayanan2023] | Claims limited to the cited study settings |

## Quantitative statements

The verification of eight recorded statements is reported in Section 7 and in
`docs/benchmark-thresholds.md`. UPDATED 2026-08-27: the eight statements concern eight distinct
quantities (the earlier merger of two NARMA-10 statements was itself an error, D16). Two were
verified without substantive change, five required a meaning-changing correction or removal,
and one retained its content after a bibliographic correction; four of the eight dispositions
recorded in the first two passes were later reversed by a primary read. The manuscript
explicitly states that this purposive set does not estimate a corpus-wide rate.

## Automated results

At the audit date, the manuscript contains 81 unique cited sources. All citation keys resolve,
all cited bibliography entries carry provenance notes, the three figure references and eleven
table references are complete, and no obsolete framework brand or second-paper dependency
remains in the assembled manuscript.

## Addendum, 2026-08-20

An internal review triggered re-verification of four entries. Racca2021 was found to be two
papers fused (right authors, wrong title and arXiv identifier) and was corrected, with the
dependent VPT baseline removed (deviation D15). GuDao2023 gained its COLM 2024 venue,
Recht2019 its ICML/PMLR record, and HurleyShaheen2025 a refreshed preprint-status check.
After the same-day restructuring the manuscript carries five figure references and eleven
table references, and `python3 scripts/audit_manuscript.py` passes. The reviews' request
for an entry-by-entry second-reader sweep before submission stands: D15 demonstrates that a
dated verification note can coexist with a fused entry.

## Addendum, 2026-08-27

Verifying primaries for the round-2 additions reversed two more dispositions. Vidamour et al.
(2023) state "~0.434" NMSE, without citation, for their own shift register on a NARMA-N variant
with autocorrelated inputs; this document's 2026-08-13 row "later approximately 0.4 NMSE label
identified as inconsistent" and the manuscript's relabelling claim rested on a misquotation and
are withdrawn (deviation D16). The 0.014% spoken-digit error, recorded as unlocated, is stated
with its interval in Brunner et al. (2013), the primary that Yan et al. (2024) cite for it
(deviation D17). Du et al. (2017) and Torrejon et al. (2017) were re-read for the Table 11
boundary notes: the memristor devices "function independently in the reservoir" with no
inter-device coupling, and the spin-torque oscillator is a single node time-multiplexed at
about one fifth of its relaxation time with no feedback loop. Paquot et al. (2012) and Vinckier
et al. (2015) were read for the NARMA-10 values in Table 9. Kubota et al. (arXiv v5) and Dambre
et al. (2012) were re-read and stand. The Yan et al. (2024) Author Correction was re-checked:
it changes reference numbers only, and the 0.014% sentence it does not touch cites Brunner et
al. correctly. The Jaeger (2002) GMD report could not be read (the available PDF has no
extractable text); its i.i.d. condition remains corroborated from secondary sources and the
manuscript says so. After the revision the manuscript carries 82 cited sources, eight figure
references and twelve table references; `python3 scripts/audit_manuscript.py` passes. The
second-reader bibliography sweep remains open and is now more urgent, not less.

## Addendum, 2026-08-27 (round-3 revision): evidence-level and efficiency readings

The round-3 review asked for the evidence and efficiency dimensions to be demonstrated on
the twelve worked examples (manuscript Table 13). Every physical-system cell was coded from
a same-day re-read of the cited primary; the deciding sentences are recorded here so each
coding is checkable. The passages were located and quoted first; the dispositions below
were entered after reading the quoted text, and every row requires author sign-off exactly
as Table 12 does. The four software systems
(Jaeger 2001; Maass 2002; Gallicchio et al. 2017; Gauthier et al. 2021) are Level 0 by the
architecture already recorded in Table 12 (numerical studies; no device) and are not
repeated below.

| System | Deciding text read on 2026-08-27 | Coding |
|---|---|---|
| Du et al. 2017 (PMC5736649) | "During the reservoir operation, we apply one pulse stream to one device at a time"; "The device states after the pulse trains were measured and recorded"; "The readout function was implemented in software using Matlab". 88 devices (MNIST) and 90 (second-order task) selected from a 32x32 crossbar. No quantified energy, power, throughput or latency figure located. | Level 2 (states measured separately, assembled offline); no quantified efficiency claim |
| Appeltant et al. 2011 (PMC3195233) | "Through an electronic implementation, we experimentally and numerically demonstrate excellent performance in a speech recognition benchmark. Complementary numerical studies also show excellent performance for a time series prediction benchmark"; "We now present results from numerical simulations ... for a second task ... dynamical system modelling" (NARMA); "a WER as low as 0.2% in experiments"; "The delay loop is implemented digitally by means of Analog to Digital and Digital to Analog Converters". No quantified efficiency figure. | Level 3 for the spoken-digit claim; the NARMA-10 result is numerical only (Level 0); no quantified efficiency claim |
| Brunner et al. 2013 (PMC3562454) | "each cycle of length T2 data of the cochleagram's 86 frequency channels were injected into the system with 8 bit resolution, corresponding to a rate of 1.1 Gbyte/s"; "data preprocessing and readout are carried out off-line"; "The calculated energy consumption ... including all-optical data input and readout hardware, would be of the order of 10 mJ per digit, compared with 2 J per digit required by a standard desktop computer" ("The energy consumption for a system, entirely realized in hardware, was calculated using off-the-shelf components"). | Level 3 (task-order injection at the stated rate; offline readout); quantified throughput at the injection stage; energy as a calculated estimate for a projected hardware system with named components |
| Vandoorne et al. 2014 (nature.com/ncomms4541) | "The periodic patterns of the different outputs were detected sequentially ... A specific header sequence allowed us to temporally realign the different output channels before processing them in a computer"; "we measure the response at the 11 nodes marked with a red dot. The other five nodes had output powers below the noise floor"; "the reservoir processing itself does not consume any power in the nodes" (qualitative); higher speeds "possible" stated as projections. | Level 2 (sequential per-node detection over a repeated input, realigned in software); qualitative passive-core power statement only |
| Torrejon et al. 2017 (arXiv:1701.07715) | "Each input value is consecutively applied to the oscillator as a constant current for a theta of about 100 ns"; "The output signal is then recorded by a real time oscilloscope"; "The amplitude of the ac voltage across the oscillator is recorded for off-line post-processing". Power figure ("reduced down to one microwatt") is cited for the device class from another work, not measured here. | Level 3; no efficiency claim for the demonstrated system |
| Milano et al. 2022 (accepted manuscript, IRIS/Polimi bitstream via Wayback) | Pattern task: "Each input stream was applied to different pads of the multiterminal NW network reservoir"; "classified by means of a simple one-layer neural network readout function implemented in hardware in a ReRAM array"; "offline trained through supervised learning". MNIST: "assessed by simulating an extended NW network"; "modelling the NW network as a grid graph with 29 x 29 nodes, where the properties of memristive edges were extrapolated from experimental measurements"; "with a software readout function". Efficiency: qualitative only in the accessible text ("the power consumption of our NW-based physical reservoir is higher than state-of-the-art ..."), quantitative detail deferred to a supplementary note not contained in the accessible file. | Level 3 for the pattern task (live multiterminal operation, hardware readout, offline-trained weights); the MNIST result is a device-calibrated simulation (Level 1); no quantified efficiency claim in the accessible text |
| Nakajima et al. 2015 (nature.com/srep10487, PMC cross-checked) | "The motor commands sent from the PC control the position of the base rotation"; "we continue running the arm ... and the actual experiment begins. By collecting the sensory time series ... we train the linear readouts"; timestep "about 0.03 [s] in physical time". No closed-loop experiment in this paper (closed-loop control is prior work, their ref. 24). No quantified efficiency figure. | Level 3 (live actuation and sensing loop); no efficiency claim |
| Sumi et al. 2023 (PMC10288593) | "Stimulation of cultured neuronal networks was performed using optogenetics by activating ChrimsonR with patterned light"; "The output layer was implemented offline in a custom Python script"; "N (=60) neurons ... were manually selected from a single network, and their somas were defined as regions of interest". The paper uses no electrodes; recording is fluorescence calcium imaging at 20 frames/s. No quantified efficiency figure. | Level 3 (live patterned stimulation, responses imaged during stimulation, offline readout); no efficiency claim. **Corrects Table 12's earlier "observed at electrodes / electrode channels", which the primary does not support** |

Two findings from this pass beyond the codings themselves. First, Appeltant et al.'s
NARMA-10 results are numerical only, and the experimental system's delay loop is digital
(ADC/DAC) around the analogue node; both facts are now stated in Table 13. Second, the
0.168 re-read note of the earlier 2026-08-27 pass had been filed on the Brunner2013
bibliography entry although PMC3286854 and the quoted text belong to Paquot2012; both
entries now carry the correct notes with a placement-correction remark (see
`docs/response-to-review-round3-20260827.md`). The manuscript's citations were correct
throughout; the error lived only in the private notes.

## Addendum, 2026-08-27 (round-3 revision): dimension-coverage matrix bases

Manuscript Table 3 marks, for each of the eleven Table 2 reviews, which comparison
dimensions the review uses as its principal organizing axis or records systematically. The
per-review bases (section titles, tables, and quoted sentences, gathered from the full
texts where open and from the accessible text and supplementary material of the two
closed-access reviews) are held in the round-3 response record and summarized here; every
cell requires author sign-off.

- Lukosevicius and Jaeger 2009: readout and adaptation are co-principal ("This review
  systematically surveys both current ways of generating/adapting the reservoirs and
  training different types of readouts"); substrate is a single enumerating subsection
  (3.6, borderline); tasks are explicitly out of scope.
- Tanaka et al. 2019: substrate principal ("classifying them according to the type of the
  physical phenomenon utilized for the reservoir"); architecture systematic (Section 3 and
  the Section 10 classification into network, single-node delayed-feedback, and excitable
  medium); tasks tabulated (Tables 1-2). Explicitly declares cross-technology performance
  comparison "premature ... because these characteristics highly depend on the
  implementation method".
- Nakajima 2020: conceptual essay; substrate recorded systematically (Section 3, Figure 3,
  Phase-1 property mapping); the Phase 0/1/2 scheme classifies substrate purpose, not
  evidence level.
- Cucchi et al. 2022: workflow principal; architecture dichotomies (2.4.3-2.4.5),
  substrate (Section 4), readout and training (3.3-3.4), and optimization (3.5) each have
  dedicated sections; applications recorded narratively per substrate (borderline for the
  task column).
- Zhang and Vargas 2023: application principal (Section 5 and Table 3); architecture
  (Section 4 including single-node delayed feedback and NG-RC), substrate (4.5 and Table
  2), training (Section 3 and Table 1) and adaptation (3.4-3.5, 7.1) systematic; Table 4
  juxtaposes accuracies without comparability criteria and without marking simulated
  against physical entries.
- Yan et al. 2024: organized by research modality; records a three-way topological-
  structure split of physical reservoirs, substrate and energy-efficiency columns (Table
  1), and an application-benchmark section; flags non-comparable values in Figure 3
  "denote error values that are not directly comparable with other works" without stating
  criteria.
- Liang et al. 2024 (main text closed; assessed from the abstract, figure titles, and the
  full supplementary file): substrate principal; an "eRC architecture taxonomy" (Figure
  2), input/output layers (Figure 4 and supplementary columns), tasks, and a per-system
  "*Simulation only" flag (Supplementary Table 3) are recorded; the simulation-only flag
  is the only per-system evidence attribute found in any of the eleven reviews.
- Everschor-Sitte et al. 2024 (published version closed; assessed from the arXiv preprint
  under the earlier title and the published figure captions): substrate principal
  (magnetic and ferroelectric sections); readout modes systematized (Figure 4); the
  preprint names "the evaluation of a fair and reliable comparison of the performance of
  different reservoirs" as requiring further research.
- Wringe et al. 2025: task taxonomy principal (five classes, Sections 4-8); operating mode
  recorded per benchmark (driven against free-running, Section 3.1.2 and Figure 3);
  Section 9 gives per-benchmark reporting requirements and the review performs worked
  parameter-comparability checks (e.g. "timescale rescaling shows they are comparable"),
  the closest any of the eleven comes to a comparability procedure, scoped to benchmark
  parameters rather than architecture or evidence.
- Liu et al. 2026 (full text read from the authors' institutional repository after MDPI
  returned HTTP 403): despite the review-style title, the paper is organized as an
  ESN-against-LSM benchmarking study with review background; architecture is the principal
  axis, readout/training is a compared attribute (their Table 1: ridge solve against Adam
  over 500 epochs), and benchmarks are sectioned (Mackey-Glass, NARMA-10). Its explicit
  fair-comparison protocol (Section 4.1) governs the authors' own two models, not published
  results, so the procedure cell stays empty. **This read corrected manuscript Table 2's
  row, which had recorded "Chronology / General foundations" from metadata alone while the
  full text was 403-blocked at scoping.**
- Abdalla et al. 2026 (abstract, all top-level headings, and both comparison tables read
  from the IOP page; PDF downloads bot-gated): the principal axis is architecture within
  the photonic substrate (time-delay against spatially-distributed, Section 2), with
  substrate variants as the second level; readout/training (Sections 4-5), benchmarks
  (Section 6, Table 1), a per-result numerical-against-experimental distinction, and a
  qualitative per-scheme "Energy bottleneck" column (Table 2) are recorded; no quantitative
  energy figures, no defined measurement boundary, and no comparability procedure located
  in the accessible text. **This read corrected manuscript Table 2's row from "Substrate /
  Photonic integration" to "Architecture within photonics".**

The two Table 2 corrections are themselves instances of the paper's subject: one
characterization had been made from metadata while a 403 blocked the full text, and one
recorded the review's scope as its organizing axis. Both were caught only by reading the
texts, both are visible in the corrected Table 2, and the introduction's list of
substrate-organized reviews was narrowed accordingly.

## Addendum, 2026-08-27 (pre-submission bibliography sweep)

All 104 bibliography entries were checked one by one against live authoritative records
(Crossref for every DOI; the arXiv API for every eprint, with arXiv-side DOIs compared
against ours as a fused-entry test; targeted authoritative pages for the four entries with
neither identifier). No hallucinated, fused, or misattributed reference was found; the
eight comparison flags all resolved to registry-side quirks or documented entry decisions.
Two substantive upgrades came out of the sweep: anchor 5 (the memory-capacity bound) is now
verified against GMD Report 152 itself, read by rasterizing the text-layer-less PDF
(Proposition 2, p. 16, with both conditions stated as necessary; "generically MC = N" for
linear networks, p. 18), and Raff (2019) is upgraded to its NeurIPS 2019 proceedings venue
after verification against the official proceedings listing. One inconsistency in the wild
is documented: the author's own publications page dates Report 152 to 2001 against the
report imprint's 2002, and that circulating year had leaked into two of this project's own
documents, now corrected. Full method, per-entry table, and dispositions:
`docs/bibliography-sweep-20260827.md`. The sweep was single-investigator; the
checklist's human second-reader requirement remains open.
