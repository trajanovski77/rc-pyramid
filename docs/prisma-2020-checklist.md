# PRISMA 2020 checklist

**Prepared:** 2026-09-05, on a referee request.
**Applies to:** the manuscript *A Critical Review of Reservoir Computing Classification Schemes
and an Architecture-Based Framework for Evaluating Reported Systems* and the prospective audit specified in
`protocol.md`.

## How to read this

The manuscript states that it follows PRISMA 2020 and PRISMA-P **reporting principles**
(§7) for a review whose identification and deduplication stages are complete and whose
screening, extraction and synthesis stages have not been run. A checklist for a
partly-executed pipeline is only useful if it says which is which, so every item carries one
of four statuses and nothing is left to inference:

| Status | Meaning |
|---|---|
| **Reported** | Done and located in the manuscript or a released file. |
| **Planned** | Pre-specified in `protocol.md`; not executed. The location given is the specification, not a result. |
| **Not applicable** | The item concerns a synthesis stage this study has not reached, or a meta-analytic construct this design excludes. |
| **Open** | Required before submission and not yet supplied. |

An item marked Planned is **not** a partial credit. It means the manuscript reports a
commitment, and the corresponding result does not exist. 11 of the 39
checklist rows are in that state, and a further 10 concern stages this
study has not reached or an item that does not apply to a report of this type; together that
is the honest summary of where it stands. The 27 numbered PRISMA items expand to 39 rows
because several carry sub-items. (Until 2026-10-25 this paragraph and the summary below said
37 rows, 9 of them planned; a recount of the table gave 39 and 11.)

## Checklist

| # | Item | Status | Location or reason |
|---|---|---|---|
| 1 | Title | Not applicable, stated | PRISMA 2020 item 1 asks a report to identify itself as a systematic review. This report is not one: it is a critical review of classification schemes with a framework, and it reports the audit's protocol and completed stages. The abstract, §1 and §7 say so in those terms, and the audit is described as a protocol in PRISMA-P language (PRISMA-P item 1a). The title is not phrased as a systematic review. (Until 2026-10-25 this row said the title names "a prospective evaluation", which it does not.) |
| 2 | Abstract | Reported | States that the pilot passed both criteria, that its sample reached only two of the four families and that those two are tested by a separately specified study, that the provenance set does not estimate prevalence, and that the paper is not a systematic review. (The failed first pilot attempt was cut from the abstract when it was shortened to the 250-word limit; it is reported in §8.4 and Table 20. This row claimed otherwise until 2026-10-25.) |
| 3 | Rationale | Reported | §1: substrate-first organisation does not determine computational architecture; no existing review states a comparability procedure. |
| 4 | Objectives | Reported | §1 states the review's research questions RQ1-RQ3 and the contributions (i)-(iv), with Table 1 carrying the evidence status of each. The audit's own questions are RQ1-RQ7 in `protocol.md` §1. |
| 5 | Eligibility criteria | Reported | `protocol.md` §4; manuscript §7. Includes the open-access restriction (deviation D6) and its stated cost (§9.4). |
| 6 | Information sources | Reported | `search-strategy.md` §1 and §6; manuscript §7. OpenAlex and arXiv as primary, Semantic Scholar and Crossref as checks, all dated. The supplementary leg of `search-strategy.md` §2.6 adds forward and backward citation searching (deviation D31); executed 2026-10-25 (`search-strategy.md` §6.4): 802 new records after deduplication and the adjudication of 11 near-duplicate pairs. |
| 7 | Search strategy | Reported | `search-strategy.md` §2, all strings verbatim, including §2.5 for the OpenAlex filter actually executed and its 2026-10-24 correction. Superseded subscription strings retained. The supplementary blocks are in §2.6 and `scripts/fetch_supplementary.py` (Planned). |
| 8 | Selection process | Planned | `protocol.md` §5: two independent coders, blind, disagreements advance, κ before resolution. Enforced by `scripts/screen.py`, which refuses to run until the near-duplicate adjudication is complete. No record has been screened. |
| 9 | Data collection process | Planned | `protocol.md` §6 and `codebook.md`: one coder, random 20% double-extracted, per-field reliability reported. Not executed. |
| 10a | Data items: outcomes | Planned | `codebook.md` §4-§12. The reporting-completeness, benchmark, efficiency and reproduction fields. |
| 10b | Data items: other variables | Planned | `codebook.md` §1-§3: bibliographic, membership, family, subclass, and the six evaluation dimensions. |
| 11 | Study risk of bias assessment | Not applicable, with a substitute | This review assesses reporting sufficiency, not effect estimates, so per-study risk of bias in the clinical sense does not apply. The corresponding construct is the evidence level of §4.1 and the reporting-completeness fields of `codebook.md` §4-§7, both of which are coded per record and are Planned. |
| 12 | Effect measures | Not applicable | No effect sizes are pooled. `protocol.md` §2 and §10 state that effect sizes across reservoir-computing tasks and metrics are not commensurable and will not be pooled. |
| 13a | Synthesis: eligibility for each synthesis | Planned | `protocol.md` §9, analyses A1-A7, each with its own inclusion rule; A1's pairing key and A6's contingency construction are fixed in `scripts/analyses.py`. |
| 13b | Synthesis: data preparation | Planned | `scripts/analyses.py`, written before the data exists. Conversions between metrics are explicitly forbidden (`codebook.md` §8). |
| 13c | Synthesis: tabulation and visual display | Planned | `scripts/figures.py`; the data-dependent figures refuse to render without extraction data rather than emitting an empty plot. |
| 13d | Synthesis methods | Planned | `protocol.md` §9. Descriptive and contingency-based; A6 carries pre-committed decision thresholds. |
| 13e | Heterogeneity exploration | Planned | Stratification by family, substrate and evidence level, pre-specified in `protocol.md` §9 supporting descriptives. |
| 13f | Sensitivity analyses | Planned | Pre-specified: all analyses reported with and without the F3 coverage class (`taxonomy-v1.0.md` §5); grade-C benchmark thresholds reported only as labelled sensitivity values (`benchmark-thresholds.md` §2). |
| 14 | Reporting bias assessment | Reported in part; otherwise Planned | The open-access exclusion is characterised rather than assumed harmless, on a substrate-terminology proxy, in manuscript §7.1 and `protocol.md` §9.2. Publication-bias assessment over the screened corpus is Planned. |
| 15 | Certainty assessment | Not applicable, with a substitute | No GRADE-style certainty rating applies to a reporting audit. The evidence-level scale of §4.1 and the A/B/C threshold grades of §5.1 are the corresponding constructs and are defined in the manuscript. |
| 16a | Study selection flow | Reported for the completed stages | Manuscript Table 10 and Figure 6. Identification and deduplication are populated; the screening stages are drawn dashed and labelled pending, because zero records have been screened. Identification via other methods (the supplementary leg) is Planned and will get its own box. |
| 16b | Excluded studies | Planned | No study has been excluded at screening. The 106 flagged near-duplicate pairs were adjudicated individually on 2026-09-05, 46 merged and 60 kept distinct, with the deciding registry field recorded per pair in the released adjudication file; merged records are marked rather than deleted. The closed-access records excluded under D6 are retained as metadata rather than discarded. (This row still described the pairs as unadjudicated until 2026-09-09.) |
| 17 | Study characteristics | Not applicable yet | Requires screening. The candidate corpus is characterised by year and access status (§8.1, Figure 7), which is not the same as characterising included studies. |
| 18 | Risk of bias in studies | Not applicable yet | See item 11. |
| 19 | Results of individual studies | Not applicable yet | No study has been extracted. Manuscript Tables 6 and 9 report fourteen worked examples classified by the authors, labelled as illustrations that carry no inter-rater information. The independent evaluation on records drawn by rule is specified in §6.1 and `validation-study-2.md` (Planned). |
| 20a-20d | Results of syntheses | Not applicable yet | No synthesis has been performed. |
| 21 | Reporting biases | Not applicable yet | Requires the screened corpus. |
| 22 | Certainty of evidence | Not applicable yet | See item 15. |
| 23a | Interpretation | Reported | §9.1-§9.4, scoped to what the framework and the provenance study support. |
| 23b | Limitations of the evidence | Reported | §9 and Table 23, which groups the threats by the kind of inference each bears on. |
| 23c | Limitations of review processes | Reported | §6.2, §8.2, §8.3 and §9.3: single-investigator provenance verification, four of eight dispositions reversed on re-reading, designer-performed worked examples (§3.4), one preliminary agreement check that does not pass its gate. |
| 23d | Implications | Reported | §9.2 and Table 24, the reporting recommendations, each tied to a comparison the framework requires. |
| 24a | Registration | Reported, negatively | The protocol is public and **not registered**. The manuscript states this in §6.3 and does not describe repository release as preregistration. Registration follows a passing pilot and precedes extraction. |
| 24b | Where the protocol can be accessed | Reported | `docs/protocol.md` in the released repository, released under CC BY 4.0 with the code under MIT, at the address given in the data availability statement. No archival DOI is minted. |
| 24c | Amendments | Reported | `docs/deviations.md`, published with the manuscript, records every instrument change with its date, reason, and whether it preceded the affected results. Thirty-six entries at this revision, including the two failed and revised pilot attempts, the supplementary search leg (D31), ruling R14 (D32), the provenance expansion protocol (D33), and Validation Study 2's coding procedure (D34) and record replacement (D35). |
| 25 | Support and funding | Reported | Manuscript title footnote and acknowledgements: Ministry of Education and Science of the Republic of North Macedonia (project "Utilizing AI and National Large Language Models to Advance Macedonian Language Capabilities"), co-funded by EC/EuroHPC JU, the Ministry of Digital Transformation of the Republic of North Macedonia, and FCSE, Ss. Cyril and Methodius University in Skopje, through the VEZILKA project, Grant Agreement No. 101263128. |
| 26 | Competing interests | Reported | Manuscript postamble: the authors declare no conflict of interest, and any author-affiliated record entering the audit will be coded by an investigator who did not author it. Manuscript §9 states that no provenance statement or worked example concerns the authors' own work. |
| 27 | Availability of data, code and other materials | Reported | Data-availability statement in the manuscript end matter; released repository holds the protocol, taxonomy, codebook, search strategy, thresholds, deviations, scripts, dated exports, corpus and flow counts. The repository carries a dual licence, MIT for code and CC BY 4.0 for text and data; no archival DOI is minted. (This row named the licence as open until 2026-09-09, contradicting item 24b on the same page.) |

## Summary

| Status | Rows |
|---|---:|
| Reported | 18 |
| Planned, pre-specified and not executed | 11 |
| Not applicable, or not applicable yet | 10 |
| Open before submission | 0 |
| **Total rows** | **39** |

Updated 2026-09-05, after the pilot passed and version 1.0 of the taxonomy was fixed for coding;
locations re-checked against the restructured manuscript on 2026-10-25. Items 25 and 26,
the two author declarations that had been Open, are now reported in the manuscript end
matter. **Two open points remain and neither is a checklist row.** Item 24a stays
*reported, negatively*: the protocol is public and still not registered, and registration
must be filed after the pilot gate and before screening. Item 24b states that no archival
DOI is minted.
Everything else is either reported or explicitly deferred to the
prospective audit, and no item is claimed as complete on the strength of a specification.
