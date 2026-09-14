# Search Strategy

**Version:** 1.0 · Part of the pre-registration by reference (`protocol.md` §3).
**Window:** 2019-01-01 → 2026-06-30 (cutoff frozen).
**Retrieval dates:** record per database in the table at §6 when executed.

---

## 1. Databases

**Amended 2026-07-31 (deviation D5).** The subscription databases were replaced with open
sources. Rationale in §1.1.

| Database | Rationale | Access | Export |
|---|---|---|---|
| **OpenAlex** (API) | Primary source. Broad coverage across applied physics, materials and CS; carries DOI, venue, abstract and open-access status. | free, no key | JSON via `scripts/fetch_openalex.py` |
| **arXiv** (API) | Preprints, and the only route to much recent quantum and photonic RC. Categories: `cs.LG`, `cs.NE`, `cs.ET`, `physics.app-ph`, `physics.optics`, `nlin.CD`, `quant-ph`. | free | JSON via `scripts/fetch_arxiv.py` |
| **Semantic Scholar** (API) | Overlap check on OpenAlex, stronger in CS venues. | free | JSON via `scripts/fetch_semanticscholar.py`, **executed 2026-08-02** |
| **Crossref** (API) | DOI-level metadata completeness check; catches records the others index poorly. | free | JSON via `scripts/fetch_crossref.py`, **executed 2026-08-02** |

**Superseded:** Scopus, Web of Science Core Collection, IEEE Xplore. Retained in the development record in case institutional access becomes available, in which case they are run
as a supplementary coverage check rather than as the primary source, and the additional yield
is reported separately.

### 1.1 Why open sources, and why this is an improvement

The practical reason is that the subscription databases require institutional access that may
not be available.

The methodological reason is stronger, and it should be stated in the manuscript rather than
buried here. **A reproducibility audit whose own literature search cannot be re-run without a
paid subscription is, by its own standard, under-reproducible.** Any reader can execute
`scripts/fetch_openalex.py`. No reader outside a subscribing institution can reproduce a
Scopus export. Since this paper's central claim concerns whether published work can be
independently checked, its search leg should meet the standard it asks of others.

**Known-item recall was tested before adopting the substitution.** Nine reference papers known
to be in scope were checked by DOI: Tanaka 2019, Yan 2024, Liang 2024, Dale 2025, Cucchi 2022,
Dambre 2012, Gauthier 2021, Vidamour 2023, and the Nature Reviews Physics topological review.
All nine are retrievable. That is a small test and not a coverage study, but a source missing
several of them would have been disqualified on the spot.

**Honest trade-offs.** OpenAlex phrase matching is looser than Scopus field-limited search, so
the string needs recalibration (§2.5) and the raw hit count is higher. Curated venue lists and
conference-versus-journal deduplication are weaker. Some reviewers expect Scopus or Web of
Science and will want the paragraph above. Abstract coverage is incomplete and noticeably
worse for closed-access records, which bears directly on the scope question in §1.2.

### 1.2 Scope decision, pending: restrict to open access?

The OpenAlex harvest holds 7,062 unique in-window works, of which 3,831 are open access.
(The API declares 7,064; see §6.1 for why the two differ and why 7,062 is the figure used.)

Restricting the corpus to openly retrievable records is a **scope decision, not a
convenience**, and there is a real argument for it beyond feasibility: *you cannot fault a
paper for irreproducibility if you cannot obtain it*. An audit that includes records the
auditors could not read would be measuring its own access, not the literature's reporting.
Restricting to what any independent researcher can actually retrieve makes the study's premise
coherent, and it makes every corpus record something a reader could in principle re-check.

It also solves the abstract-coverage problem, since missing abstracts concentrate in
closed-access records.

The cost is a possible open-access bias: openly published work may differ systematically in
funding, venue and field. This is **measurable rather than merely declarable**. Metadata is
available for both groups, so the manuscript reports the open and closed sets compared on
year, venue type and citation count, characterising the bias instead of waving at it.

**Status: DECIDED 2026-07-31, open access only.** Logged as deviation D6. Recorded as a
caveat, not as a neutral scope choice, and carried into the abstract, §6 and §11.

### 1.3 How the restriction is implemented, and why we harvest more than we screen

The harvest retrieves **all 7,062 matching works**, not just the 3,831 open ones. Only the
open subset enters screening. The closed records are retained as metadata and never screened.

After merging with the arXiv leg and deduplicating, those figures become **6,486** works, of which **3,555** are openly retrievable and **2,931** are closed (§6.2). *This paragraph read 6,532 / 3,584 / 2,948 until 2026-09-09: those are the pre-adjudication figures, which §6.2 corrected on 2026-09-05 and this section did not. Same class of failure as the §6.1 and §6.3 count corrections recorded below, and the reason `deviations.md` carries the rule about grepping the repository for a withdrawn value.* The corpus-level numbers are
the ones that reach the PRISMA diagram.

This is deliberate and it is what makes the caveat unusually strong. Most reviews that
restrict scope can only assert that their exclusion was harmless, because they never saw what
they excluded. We hold metadata for every excluded record, so the manuscript reports what was
left out on year, venue, venue type and citation count, and states the direction and size of
any imbalance rather than gesturing at it.

An exclusion you can describe precisely is a much smaller problem than one you cannot.

### 1.4 Revisiting

The decision is reversible in one direction at low cost. If institutional access becomes
available, the closed records are already identified by DOI and can be screened as a
**supplementary analysis**, reported separately from the primary corpus rather than merged
into it. Nothing in the pipeline needs rebuilding for that; the harvest already holds them.


**Deliberately not searched as primary sources:** Google Scholar (not reproducibly
exportable, no stable result set, disqualifying for a pre-registered protocol) and
PubMed (RC biomedical work is well covered by Scopus; a spot check will confirm).

---

## 2. Search strings

Terms cover the paradigm name, the two founding model families, the physical-implementation
phrase, and the NG-RC variant spellings. Wildcards handle singular/plural.

### 2.1 Scopus

```
TITLE-ABS-KEY (
    "reservoir computing"
 OR "reservoir computer*"
 OR "echo state network*"
 OR "echo state machine*"
 OR "liquid state machine*"
 OR "physical reservoir*"
 OR "next generation reservoir computing"
 OR "next-generation reservoir computing"
)
AND PUBYEAR > 2018
AND PUBYEAR < 2027
AND ( LIMIT-TO ( LANGUAGE , "English" ) )
```

### 2.2 Web of Science

```
TS=(
    "reservoir computing"
 OR "reservoir computer*"
 OR "echo state network*"
 OR "echo state machine*"
 OR "liquid state machine*"
 OR "physical reservoir*"
 OR "next generation reservoir computing"
 OR "next-generation reservoir computing"
)
```
Refined by: Publication Years 2019-2026; Language = English.

### 2.3 IEEE Xplore (command search)

```
("All Metadata":"reservoir computing")
OR ("All Metadata":"echo state network")
OR ("All Metadata":"liquid state machine")
OR ("All Metadata":"physical reservoir")
OR ("All Metadata":"next generation reservoir computing")
```
Filters: 2019-2026.

### 2.4 arXiv (API)

Paged `all:` query with a **server-side** `submittedDate` range, plus a client-side v1
date check as defence in depth. Implemented in `scripts/fetch_arxiv.py`.

```
(all:"reservoir computing" OR all:"echo state network" OR all:"liquid state machine"
 OR all:"physical reservoir" OR all:"next generation reservoir computing")
AND submittedDate:[201901010000 TO 202606302359]
```

**Why the range is server-side.** Results sort ascending by submission date. Filtering
only client-side means paging through two decades of pre-window records first; if the
harvest's safety ceiling were reached before 2019 the run would report zero in-window
records while appearing to have completed normally. Server-side filtering makes that
silent-truncation failure impossible. Verified 2026-07-31: 200/200 sampled records fall
in window.

**Undated records are kept and flagged** (`window_flag = undated-manual-check`) rather
than dropped. Silent exclusion is the failure mode this project exists to criticise.

**arXiv versioning rule.** Use the **v1 submission date** for window membership. Where a
record also exists as a journal article inside the window, the journal version is the
included record and the arXiv ID is retained in `preprint_id` (`protocol.md` §4.2,
`duplicate`).

### 2.5 OpenAlex (API)

**Added 2026-09-05.** §1.1, §1.2 and `scripts/fetch_openalex.py` had all referenced a §2.5
that did not exist: deviation D5 made OpenAlex the primary database on 2026-07-31, and the
executed string was never written into §2 alongside the three superseded ones. That is the
string this project actually ran, so its absence here was the more serious gap of the two.

Implemented in `scripts/fetch_openalex.py`, which builds a comma-separated OpenAlex filter:

```
from_publication_date:2019-01-01,
to_publication_date:2026-06-30,
language:en,
title_and_abstract.search:"reservoir computing" OR "echo state network"
 OR "echo state machine" OR "liquid state machine" OR "physical reservoir"
 OR "next generation reservoir computing"
```

`--oa-only` appends `open_access.is_oa:true`. It is **not** used for the primary harvest:
under D6 the open-access restriction is a screening step, not a retrieval step, so the
harvest retrieves all 7,062 in-window works and screening filters them (§1.3). The flag
exists for a supplementary run and is documented in §1.2.

**Term-list differences between the three strings, stated as measured.** The superseded
Scopus string (§2.1) lists eight wildcarded terms, the executed OpenAlex filter six explicit
phrases, and the executed arXiv query (§2.4) five. Neither executed leg carries
`"reservoir computer*"` or the hyphenated `"next-generation reservoir computing"`. What the
frozen exports show about that, counted over title and abstract:

| Phrase, in title or abstract | OpenAlex leg | arXiv leg |
|---|---:|---:|
| `reservoir computer` present | 380 | 196 |
| ...and none of the leg's own listed phrases present | 21 | 72 |
| `echo state machine` present | 2 | 1 |
| ...and none of the leg's other listed phrases present | 1 | 0 |

Two things follow, and the second is an open item rather than a finding.

- **The records were retrieved anyway.** Every row counted above is *in* the frozen export,
  so dropping `"reservoir computer*"` did not cost those records. `"echo state machine"`
  earns its place in the OpenAlex list by exactly one record and nothing in the arXiv list,
  which is why the arXiv leg carries five phrases and OpenAlex six.
- **Why they were retrieved is now established, by controlled query (2026-09-05).** Until
  this date the paragraph here recorded an *unverified inference*: that both engines stem and
  treat the hyphen as a token separator, which was consistent with the counts above without
  being demonstrated by them. That inference is now tested and holds. The design is a
  single-record probe: take a record known to be in the frozen export whose title and
  abstract contain **none** of the leg's listed phrases, then ask the engine for that record
  *and* the phrase together. If the record comes back, the engine matched a form the phrase
  does not literally contain.

  | Engine | Probe record | Record's actual wording | Query phrase | Returned |
  |---|---|---|---|---:|
  | OpenAlex | `10.1007/s00542-023-05463-4` | "reservoir computer" | `"reservoir computing"` | 1 |
  | OpenAlex | same | same | `"reservoir computers"` | 1 |
  | OpenAlex | same | same | `"reservoir compute"` | 1 |
  | OpenAlex | `10.1016/j.ins.2021.03.013` | "echo-state networks" | `"echo state network"` | 1 |
  | arXiv | `1903.12487` | "reservoir computers" | `all:"reservoir computing"` | 1 |
  | arXiv | same | same | `all:"reservoir computers"` | 1 |
  | arXiv | `2005.05151` | "echo-state network" | `all:"echo state network"` | 1 |

  **Negative controls, run because a filter that never returns zero would prove nothing.**
  On the same records: OpenAlex returned 0 for `"photosynthesis in maize"`, 0 for
  `"liquid state machine"` and 0 for `"delay-embedded reservoir"`; arXiv returned 0 for
  `all:"photosynthesis in maize"` and 0 for `all:"liquid state machine"`. Both engines are
  therefore capable of returning zero for the same record under the same query shape, so the
  positive results above are matches and not an ignored filter.

  **A probe that was drafted and discarded, recorded because discarding it is the result.**
  An eighth row was written for `10.1063/5.0098707`, "Learning spatiotemporal chaos using
  next-generation reservoir computing", to test the hyphen in the next-generation variant. It
  is not evidence and it was removed before it was reported: the string
  "next-generation reservoir computing" **contains** "reservoir computing" as a substring, so
  the engine matches that record literally on a phrase both term lists already carry, and the
  record can demonstrate nothing about hyphenation. The script's own precondition check
  caught it, not a re-reading of the draft. The consequence is that the hyphenated
  next-generation variant needs no matching-behaviour explanation at all, which is a simpler
  answer than the one this section was looking for; hyphen folding is established instead by
  the echo-state probes, where "echo-state networks" does not contain "echo state network" as
  a substring.

  **Conclusion.** Both engines fold singular, plural and stem variants, and both treat the
  hyphen as a token separator. Dropping `"reservoir computer*"` from the executed strings
  therefore cost no records, and the hyphenated `"next-generation reservoir computing"` was
  never needed because the plain phrase matches it as a substring. That is what the frozen
  exports already showed and what this now explains. **The open item this section carried
  into registration is closed.** Reproducible with `python3 scripts/verify_search_matching.py`,
  which refuses to report a result if any negative control fails or if a probe record turns
  out to contain a listed phrase.

**Known-item recall was tested before this string was adopted**, not after: nine reference
papers known to be in scope were retrieved by DOI, 9 of 9 (§1.1). That is a smoke test, not
a coverage study; the coverage measurement is the Semantic Scholar overlap in §6.2a.

---

---

## 3. Known limitations of this string: declare these in the manuscript

Stated now, before results, so they cannot be presented later as post-hoc caveats.

1. **Substrate-only phrasing is missed.** A paper describing what is functionally a
   reservoir but never using any of the §2 search phrases, some in-materio, morphological,
   and spin-wave computing work, will not be retrieved. Partially mitigated by §4 supplementary
   searching, not eliminated. **This is the strategy's principal known weakness and the most
   likely source of an under-representation of F4.**
2. **English-only.** Notable Japanese-language applied-physics RC work is excluded.
3. **"Reservoir" is polysemous.** Hydrology, petroleum engineering, and epidemiology use it
   heavily. The quoted multi-word phrases suppress most of this; residual noise is removed at
   Stage-1 screening and the false-positive rate is reported.
4. **NG-RC boundary.** Papers presenting NG-RC purely as "nonlinear vector autoregression"
   without the RC framing are missed. Accepted: if a paper does not situate itself in RC,
   auditing it as RC is arguably wrong anyway.

---

## 4. Supplementary searching

Executed after database screening, and reported separately in the PRISMA flow so its
contribution is visible:

- **Backward citation chasing** on the eleven reviews in the review-of-reviews table.
- **Forward citation chasing** on the five most-cited included records per family.
- **Toolkit reverse-lookup:** records citing ReservoirPy, PyRCN, or RCbench, an efficient
  route to papers that share artefacts and therefore matter disproportionately to the
  reproduction sub-study.
- **Targeted F4 sweep:** if F4 representation after database screening is below 8% of the
  corpus, run a supplementary search on `("in materio" OR "in-materio" OR "morphological
  computation" OR "physical learning") AND (reservoir OR "temporal processing")` and report
  it as a declared amendment under `protocol.md` §11. The 8% trigger is set now.

---

## 5. Deduplication

1. Exact DOI match.
1b. **Exact arXiv identifier match** (added 2026-08-02, deviation D7).
2. Normalized title match (lowercase, punctuation and whitespace stripped, Levenshtein ≤ 3).
3. Manual review of near-matches at ratio ≥ 0.90.
4. Preprint/journal pairs resolved to the journal version; both identifiers retained.

Implemented in `scripts/dedupe.py`. The pre-dedup and post-dedup counts feed the PRISMA
flow diagram directly.

**Why step 1b.** The two primary legs disagree about what a preprint's DOI is. OpenAlex
assigns arXiv preprints the registered DataCite DOI `10.48550/arXiv.<id>`; the arXiv API
reports the *journal* DOI where an author supplied one and nothing at all otherwise, so 825
of the 1,234 arXiv records carry no DOI. Without an identifier pass those pairs fell through
to fuzzy title matching, which is the weaker instrument. Step 1b matches on the identifier
both sources do agree on, and it resolved 663 pairs on execution.

**Preprint detection is not source detection.** OpenAlex returns 1,048 records typed
`preprint`, many of them the same works the arXiv leg supplies. Rule 4 is therefore applied
on record type from any source, not on whether a record came from the arXiv leg.

**Open access is carried through dedup, not applied at it.** The D6 restriction is a
screening step (§1.3), so no closed record is dropped here. `is_oa`, `oa_status`,
`venue_type`, `year` and `cited_by_count` reach the corpus so that the §9.2 exclusion
characterisation has something to characterise. One consequence deserves stating: openness
is a property of the work and survives the merge, so a closed journal article with an arXiv
preprint counts as openly retrievable, which is what D6 turns on. The corpus records
`oa_basis` for every open record so the two senses of "open" stay distinguishable.

**Blocking.** Passes 2 and 3 are blocked rather than scanned pairwise, which is what makes
them tractable at this corpus size: unblocked, pass 3 alone is roughly two hours. Both
blockers are exact necessary conditions, not heuristics, so the output is identical to the
full scan. Verified against a brute-force reference on random subsamples by
`scripts/verify_dedupe_blocking.py`, released with the artefacts.

### 5.1 How step 3 is adjudicated

Step 3 is a two-part loop, because the pairs it flags genuinely cannot be settled by rule.
From the executed run: *Photonic Reservoir Computing* against *Photovoltaic Reservoir
Computing* are two papers, and *conn2res: A toolbox for connectome-based reservoir computing*
against *`<tt>`conn2res`</tt>`: A toolbox for connectome-based reservoir computing* is one
paper and a markup artefact. Both sit above ratio 0.90. That is the threshold working, not
failing.

1. The first run writes `near_duplicates_for_review.csv` carrying, for each pair, the ratio
   and both records' id, title, year, venue, DOI and source, plus empty `decision`,
   `adjudicated_by` and `note` columns.
2. A coder fills `decision` with `same` or `different`.
3. Re-running with `--adjudications <file>` applies it.

**Adjudicated duplicates are marked, not deleted.** The row stays in the corpus and gains
`dup_of` and `dup_basis = manual-adjudication`; screening operates on `dup_of == ""`. A
deleted row is indistinguishable from one that was never retrieved, and this study cannot
afford that ambiguity in its own corpus.

Two guards, because the failure modes here are silent. A completed review file is never
overwritten; a regenerated list is written alongside it as `.new.csv`. And since record ids
are positional, an adjudication file made against a different harvest would point at the
wrong records while looking valid, so titles are re-checked against the corpus before
anything is applied and a mismatch aborts the run.

**Status: 106 pairs flagged, all 106 adjudicated on 2026-09-05; 46 merged, 60 kept apart.**
Every decision was taken against a registry record rather than by rule, and the deciding
field is recorded per pair in `near_duplicates_for_review.csv`: a Crossref work type and
reference count, a Crossref `relation`, a DataCite `resourceTypeGeneral`, or in one case an
HTTP 410 on a withdrawn deposit. Adjudicated under deviation D12 and **signed off by
S. Trajanovski on 2026-09-05**, which is the condition D12 attaches. The adjudication is
therefore closed and the corpus is final for screening.

What the 60 non-merges are is itself a measurement of what a title-similarity threshold
catches at this cut-off: journal cover features carrying the article's title with zero
references, datasets deposited beside their article, errata and retraction notes, conference
abstracts against the full papers that followed them, an author's master's thesis against the
paper drawn from it, and the *Photonic* against *Photovoltaic* pair this section already used
as its worked example. One pair was left unmerged as unresolvable: two HAL deposits of an
invited talk in adjacent years, neither carrying a DOI and no registry record able to
separate or join them. It is marked as such rather than guessed, because a wrongly merged
duplicate silently deletes a work while a wrongly kept one stays visible.

---

## 6. Execution log

Fill on execution. Retrieval date matters: these databases are not static and the counts
must be reproducible to a date, not just to a string.

| Database | Retrieval date | Raw records | Export file |
|---|---|---|---|
| Scopus | superseded (D5) | n/a | `data/raw/scopus_YYYYMMDD.csv` |
| Web of Science | superseded (D5) | n/a | `data/raw/wos_YYYYMMDD.txt` |
| IEEE Xplore | superseded (D5) | n/a | `data/raw/ieee_YYYYMMDD.csv` |
| OpenAlex | **2026-07-31** | **7,062 in window** (3,831 open access) | `data/raw/openalex_20260731.json` |
| arXiv | **2026-07-31** | **1,234 in window** | `data/raw/arxiv_20260731.json` |
| Semantic Scholar | **2026-08-02** | **6,082 in window** (overlap check, not merged) | `data/raw/s2_20260802.json` |
| Crossref | **2026-08-02** | n/a (per-DOI checks, not a harvest) | `data/raw/crossref_*_20260802.json` |
| **Total pre-dedup** | 2026-08-02 | **8,296** | |
| **Total post-dedup** | 2026-08-02 | **6,532** | `data/screening/corpus_deduped.csv` |

### 6.1 Which OpenAlex number is the right one

Three counts for the same harvest are in circulation and they are not interchangeable. For
the record:

| Count | Value | What it is |
|---|---|---|
| `reported_total` | 7,064 | The total the OpenAlex API declares for the query |
| `retrieved` | 7,068 | Rows the harvester actually received |
| **unique works** | **7,062** | Distinct `openalex_id` values, after collapsing 6 rows delivered twice |
| open access | 3,831 | Of the 7,062 unique works |

The delivered set exceeds the declared total because paging is not atomic: a work whose page
boundary shifts between requests arrives twice. Six did. Those repeats are an artefact of
retrieval rather than two records, so they are collapsed on `openalex_id` before dedup and
counted separately, since folding them into the duplicate-removal count would overstate
cross-database overlap.

**7,062 and 3,831 are the figures to use.** They are what the harvest contains, they are what
enters dedup, and they are reproducible from the export file. §1.2 and §1.3 and deviation D6
previously quoted 7,064 and 3,832, which are the API's declared total and its open-access
subcount; those have been corrected. The discrepancy is small, but a paper that audits
reporting accuracy cannot ship a PRISMA diagram whose inputs disagree across three of its own
documents.

### 6.2 Dedup result, 2026-08-02

| Step | Records |
|---|---|
| Pre-dedup total (7,062 OpenAlex + 1,234 arXiv) | 8,296 |
| − exact DOI match | 395 |
| − exact arXiv identifier match (§5 step 1b) | 663 |
| − normalized title match, Levenshtein ≤ 3 | 706 |
| − human adjudication of near-duplicate pairs (2026-09-05) | 46 |
| **= deduped corpus** | **6,486** |
| Near-duplicate pairs at ratio ≥ 0.90, **all adjudicated** | 106 (46 same, 60 different) |

Cross-database overlap is 1,764 records, about 21 percent of the pre-dedup total. All 1,234
arXiv records are accounted for in the corpus: 948 merged with an OpenAlex record and 286
are arXiv-only.

**Open access split of the 6,486.**

| | Records |
|---|---|
| Openly retrievable, eligible for screening under D6 | **3,555** |
| Closed, retained as metadata only | 2,931 |
| Of the open set: no abstract, flagged at Stage 1 | 215 |

*Pre-adjudication these read 3,584 / 2,948 / 222 against a 6,532 corpus, and those are the
figures every document carried until 2026-09-05. The difference is the 46 merges of §5.1.*

`oa_basis` records why each open record qualifies: 2,321 on OpenAlex open-access status alone, 948 on both an OpenAlex flag and an arXiv preprint, 286 on an arXiv preprint alone. (2,350 / 945 / 289 before the adjudication; corrected 2026-09-09.)

The 3,555 is *lower* than the 3,831 open records OpenAlex returned, which looks wrong at a glance and is not. Those 3,831 records collapse to 3,269 distinct works, because a green open-access preprint and its published version were two open records and are one work. The 286 arXiv-only open records bring the total to 3,555.

**Substrate-proxy characterisation of the D6 exclusion (added 2026-08-20, from the internal
review).** Reproducible with `python3 scripts/screen.py oa-substrate`, using the
terminology proxy of `screen.py` (a proxy, never a family assignment). On titles alone,
which avoids the abstract-coverage confound (abstracts present for 93.8% of open records
but only 63.6% of closed ones), the proxy fires on 29.0% of open and 30.0% of closed
records, so the exclusion is roughly even in aggregate. By vocabulary, against the corpus's
45.1% closed share (closed/tagged counts in parentheses, added 2026-08-27 from the round-3
review so no percentage is read with more precision than its base supports):
memristive-ionic 50.5% closed (384/761), photonic 47.1% (526/1,117), analog-electronic
46.4% (154/332), digital-hardware 45.9% (95/207), mechanical-soft 42.9% (72/168),
biological-organic 33.8% (198/585), spintronic-magnetic 31.8% (93/292), quantum 18.1%
(57/315). Reported in manuscript §7.1 and carried into §9;
the family-resolved comparison remains protocol.md §9.2's job.

### 6.2a Coverage and completeness checks, 2026-08-02 (deviation D11)

Neither check contributes a record to the corpus. §1 pre-specifies that additional yield from
an overlap source is reported separately, and it is.

**Semantic Scholar overlap.** 6,082 in-window records for the same query. 5,398 are already in
the corpus, an overlap of **88.8%**: 4,779 matched by DOI, 442 by arXiv identifier, 177 by
title.

The 684 unmatched records are the interesting part, and their year granularity had to be
resolved before they could be interpreted, since the bulk API exposes a publication year while
the window ends 2026-06-30. Crossref supplied exact dates for the 549 that carry a DOI:

| | Records |
|---|---|
| In window | **429** |
| After the 2026-06-30 cutoff, correctly absent | 78 |
| Before the window, correctly absent | 26 |
| Date unresolved | 16 |
| No DOI, unresolvable this way | 135 |

Of the 429 in-window records, **412 carry a core RC phrase** in title or abstract, and **370
of those are dated 2025 or 2026**.

**Read that as indexing lag, not as a broken search string.** The shortfall is overwhelmingly
recent, which is what one expects when a primary index has not yet ingested the last two
years. Against Semantic Scholar's index the search misses roughly **6% of in-window records**,
concentrated at the recent end.

Two consequences, both of which belong in the manuscript rather than here:

1. §3 gains a **quantified** search limitation instead of a qualitative one.
2. Any claim about *recent* trends is weakened, because the corpus under-represents exactly
   the years such a claim would rest on. The corpus-composition-by-year descriptive in
   `protocol.md` §9 must carry this caveat explicitly.

Whether to promote Semantic Scholar from overlap check to source is a scope decision for the
principal investigator and is **open**. It would need a deviation and a re-run of dedup; the
fetcher already exists and the reader would need adding to `dedupe.py`.

**Crossref completeness.** Two checks.

- *Random sample of 300 corpus DOIs.* 283 registered at Crossref, 17 not. Two abstracts we
  lack, one title mismatch, two year mismatches. Metadata agreement is high and no systematic
  gap appeared.
- *Census of the 213 eligible no-abstract records that carry a DOI* (222 have no abstract; 9
  of those have no DOI either). **26 have an abstract at Crossref that OpenAlex lacks**, all 26
  open access. Recovering them would cut the title-only screening set from 222 to 196, about
  12%.

Those 26 are **not** merged into the corpus. Doing so would make `corpus_deduped.csv` no longer
a function of the two harvest exports, which is the property that currently makes it
byte-reproducible. It is a small decision and it is the principal investigator's: the check is
re-runnable with `fetch_crossref.py completeness --only-missing-abstract`.

### 6.3 The yield estimate was exceeded, and that is a pre-registered trigger

§7 records a working estimate of 1,500 to 4,000 records pre-dedup. The actual figures are
**8,296 pre-dedup and 6,532 post-dedup**, both above the top of the range, post-dedup by
roughly 63 percent.

Under §7 this fires a declared trigger: substantially more than expected "suggests polysemy
leakage and a tightening of the Stage-1 rubric", and the response is "a declared amendment
under `protocol.md` §11, not a silent adjustment". Recording that the trigger has fired is
the automatable half. The amendment itself is a principal-investigator decision and is
**open**.

Two candidate readings, and the corpus can distinguish them before anyone decides:

1. *Polysemy leakage.* "Reservoir" is heavily overloaded in petroleum engineering, hydrology
   and pharmacokinetics, and OpenAlex phrase matching is looser than the field-limited Scopus
   search the estimate assumed (§1.1). The estimate was calibrated on the search this study
   no longer runs.
2. *Genuine growth.* The corpus is monotonically increasing across the window, from 492
   records in 2019 to 1,287 in 2025, with 704 already in a half-year 2026. (These read 493,
   1,301 and 705 before the 2026-09-05 near-duplicate adjudication.) An estimate made
   from a scoping scan may simply have been low.

These make opposite recommendations and are separable by inspection: a random sample of
100 titles from the deduped corpus, coded for topical relevance, estimates the leakage rate
directly. That sample is drawn before, not after, the rubric decision.

**Probe run 2026-08-02.** `data/screening/leakage_probe_20260802.json`, n=100, seed 20260802,
drawn from the 6,532 deduped records.

| Code | n | Meaning |
|---|---|---|
| `on-topic` | 62 | Clearly RC, ESN, LSM or physical reservoir |
| `undecidable-from-title` | 18 | Neuromorphic, RNN or device work that may or may not be RC |
| `off-topic` | 20 | No plausible RC connection from the title |

Projected onto the corpus:

| Scenario | Corpus |
|---|---|
| Remove off-topic only | 5,226 |
| Remove off-topic **and** every undecidable record | 4,050 |
| Pre-registered ceiling | 4,000 |

**Polysemy leakage cannot account for the overshoot.** Even the maximally aggressive scenario,
which discards every record that could not be confirmed on-topic from its title alone, lands
at 4,050, still above the ceiling. Reading 1 is therefore insufficient on its own and reading
2, genuine growth, carries most of the excess. The year curve agrees: 492 records in 2019 rising to 1,287 in 2025.

**Count correction, 2026-09-05.** The three year counts above read 517, 1,342 and 628 until
this date. Those are the pre-dedup OpenAlex figures, not the corpus, and this section had
labelled them "the corpus". The deduplicated corpus holds 492 records dated 2019, 1,287 dated 2025 and 704 dated 2026, and its annual counts sum to the 6,486 in §6.2. *Those three counts read 493 / 1,301 / 705 against a 6,532 corpus until 2026-09-09, which was correct only until the near-duplicate adjudication of 2026-09-05 merged 46 pairs;* all three are
reproducible with `python3 scripts/figures.py fig8s`, which reads them from
`corpus_deduped.csv` rather than from any document. The manuscript has used the corpus
figures since 2026-08-02; this document did not, which is the same three-documents-disagree
failure §6.1 records for the OpenAlex harvest totals. Corrected in place with the correction
shown, on the principle stated there.

**What this implies for the response owed,** stated as a recommendation and not as a decision:
tightening the Stage-1 rubric would not bring the corpus into the registered range and would
trade a documented over-yield for an undocumented under-screen. Liberal Stage-1 inclusion
already removes off-topic records by design, and it does so with two coders and an abstract
each rather than one coder and a title. The alternative response, amending the estimate and
recording why it was wrong, matches the evidence better.

**Limits of this probe, which are real.** Single coder, that coder is the assistant, titles
only, no blinding and no reliability statistic. The 18 undecidable cases are the honest signal
of its resolution: a title frequently is not enough, which is precisely why Stage 1 reads
abstracts. It is a diagnostic for a protocol decision, it is labelled exploratory wherever it
appears, and no record was removed on the strength of it.

**arXiv notes (2026-07-31).** 1,234 unique records, all in window; the server-side date
filter returned zero out-of-window and zero undated records, so no manual date adjudication
is needed for this leg. Harvest terminated on consecutive empty pages rather than on the
6,000-record safety ceiling, so the result is the complete set for this query.

The three subscription databases require institutional authentication and must be run by
hand. Until they are, no screening can begin.

---

## 7. Expected yield

From the scoping scan, roughly **1,500-4,000** records pre-dedup is the working estimate,
with Scopus contributing the majority and arXiv adding several hundred unique preprints.

This estimate is recorded so that a large deviation is itself informative: substantially
fewer suggests the string is too narrow and should trigger a review of §3 limitation 1
before screening proceeds; substantially more suggests polysemy leakage and a tightening of
the Stage-1 rubric. **Either response is a declared amendment under `protocol.md` §11, not a
silent adjustment.**

**Interim check against the estimate (2026-07-31).** The scoping note anticipated arXiv
contributing "several hundred unique preprints". It returned 1,234, roughly double the top
of that expectation, while Scopus was expected to supply the majority of the corpus. If
Scopus, Web of Science and IEEE behave as anticipated, the pre-dedup total will land at or
above the upper end of the 1,500 to 4,000 estimate.

No action is triggered yet: the estimate governs the pre-dedup total across all four
sources, not any single leg, and arXiv overlaps heavily with the others. The observation is
recorded now so that if the total does exceed the range, the response is visibly a reaction
to a pre-registered trigger rather than a post-hoc rationalisation.

**Trigger fired (2026-08-02).** Pre-dedup 8,296, post-dedup 6,532. Both exceed the range.
The response owed under this section is open and belongs to the principal investigator; the
options and the test that separates them are set out in §6.3. Note that the estimate was
calibrated for a Scopus-led search that deviation D5 replaced, so the overshoot is partly a
property of the estimate rather than of the corpus, and saying so is not a way of excusing
it: the trigger is recorded as fired either way.
