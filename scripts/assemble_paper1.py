#!/usr/bin/env python3
"""Assemble paper 1 into a single submittable markdown document.

    python3 scripts/assemble_paper1.py --out paper/PAPER1.md
    python3 scripts/assemble_paper1.py --check

Paper 1 is the instruments paper: taxonomy, facets, evidence ladder, boundary convention,
benchmark discrimination framework, the anchor-verification result, and the pre-registered
audit protocol. It deliberately contains no corpus-audit results, which belong to paper 2.

WHY ASSEMBLY IS A SCRIPT
Sections live in separate files so they can be edited independently. Concatenating them by
hand invites the two failure modes this project cares about: a section silently dropped, and
a stale copy shipped alongside a fresh one. The script fails loudly if a section is missing
and refuses to emit a document that still contains audit-result placeholders, which in paper 1
would be a promise the paper does not keep.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PAPER = Path("paper")

# Order matters. manuscript.md is an archived audit skeleton and is not assembled here.
SECTIONS = [
    ("paper1-frontmatter.md", "front matter and abstract"),
    ("p1-s1-introduction.md", "1. Introduction"),
    ("s2-foundations.md", "2. Background"),
    ("s3-pyramid.md", "3. Classification Framework"),
    ("s4-facets.md", "4. Evaluation Dimensions"),
    ("s5-benchmarks.md", "5. Benchmark Evaluation"),
    ("s6-methodology.md", "6. Classification Validation and Provenance Methodology"),
    ("s7-corpus-construction.md", "7. Corpus Construction"),
    ("s8-results.md", "8. Results"),
    ("s9-discussion-limitations.md", "9. Discussion and Limitations"),
    ("s10-conclusion.md", "10. Conclusion"),
]

# CROSS-REFERENCE CONVENTION (changed 2026-08-02).
# The section sources are written in PAPER-1 numbering: recommendations are Section 8,
# limitations Section 9, and every "Section X.Y" in the sources refers to a section of
# paper 1. References to audit results that do not exist yet name the registered analysis
# (A1-A5, Section 6.3) and say "paper 2" explicitly, in the prose itself. An earlier
# version of this script rewrote paper-2-numbered references with blanket regexes; that
# garbled legitimate internal references, mislabelled analyses, and missed references
# wrapped across line breaks, so the rewriting was removed rather than repaired.
# (archive-paper2-synthesis.md is paper-2-only and keeps paper-2 numbering; not assembled.)
#
# A `[MEASURE]` marker means "a number goes here once the audit runs". In paper 2 that is
# a hole to fill. In paper 1 it is a true statement about the state of the evidence, so it
# renders as an explicit deferral. The substitution is deliberately visible in the output:
# a reader should be able to see exactly which claims are measured and which are owed.
SUBSTITUTIONS = []

# These must not survive into paper 1 under any rendering. Patterns use \s+ so that a
# reference wrapped across a line break is still caught; one shipped draft carried a
# "Section\n11.2" that every single-line regex had missed.
FORBIDDEN = [
    (r"\[CONDITIONAL\]", "unresolved conditional passage"),
    (r"Blocked\s+on\s+data", "paper-2 blocking notice"),
    (r"\[MEASURE\]", "unresolved measurement placeholder"),
    (r"paper\s+2", "obsolete dependency on a second paper"),
]


# The artefact location, defined once. `build_latex.py` imports this constant rather than
# repeating the URL, because a repository address that exists in two files is a repository
# address that will eventually disagree with itself.
REPOSITORY_URL = "https://github.com/trajanovski77/rc-pyramid"

# End matter, defined ONCE and consumed by all three builders.
#
# Until 2026-09-09 the three end-matter statements existed twice: here in markdown and
# again, independently, inside build_latex.py's POSTAMBLE and build_ieee.py's. The two
# copies drifted exactly as this project's own thesis predicts. On 2026-09-05 the
# acknowledgements, funding and conflict-of-interest text were completed in the LaTeX
# postambles and not here, so `PAPER1.md` went on saying that funding "will be finalized
# after confirmation by all authors" and that the conflict-of-interest declaration
# "awaits confirmation" for four days after both had been settled and were rendering,
# completed, in the two PDFs built from the same sources.
#
# This is the same defect, and the same fix, as `abstract_from_frontmatter()` in
# build_latex.py: one source of truth, derived rather than retyped. The strings below are
# plain text with no markup of either flavour; the markdown build uses them verbatim and
# the LaTeX builds run them through their own escaper.

ACKNOWLEDGEMENTS = """The authors gratefully acknowledge the financial support provided by the Ministry of
Education and Science of the Republic of North Macedonia through the project "Utilizing AI
and National Large Language Models to Advance Macedonian Language Capabilities", as well as
the co-funding provided by EC/EuroHPC JU, the Ministry of Digital Transformation of the
Republic of North Macedonia, and the Faculty of Computer Science and Engineering, Ss. Cyril
and Methodius University in Skopje, through the VEZILKA project, Grant Agreement
No. 101263128.

The authors also thank the reviewers of five rounds of internal and referee-style
pre-submission review, whose reports are answered in dated response documents in the project
repository.

Declaration of generative AI use. The authors used a generative artificial intelligence
assistant (Anthropic Claude) during the preparation of this work. It was used for language
editing and drafting of the manuscript text; for implementing the released search,
deduplication, screening, analysis and figure-generation code; for bibliographic
verification of the reference list against Crossref and the arXiv API (Section 8.2); for the
near-duplicate adjudication proposals described in Section 7, each of which was decided
against an authoritative registry record and signed off by an author; and for grouping the
coders' free-text reasons into the categories reported in Tables 16 and 19. In the pilot
reported in Section 8.4, one coder used it to retrieve full texts and to draft reason text;
every classification call is that coder's own. In the earlier pilot attempt recorded in
Table 20, each coder reviewed a pass produced by the assistant rather than coding unaided;
neither coder altered any of its forty calls, that attempt failed its criterion, and the
arrangement was withdrawn before the reported pilot was drawn. The assistant was not used to
design the study, to define the taxonomy or codebook, to make any coding judgement behind
the reported agreement statistics, or to interpret the reported results. The authors
reviewed all AI-assisted output and take full responsibility for the content of this
publication."""

DATA_AVAILABILITY = f"""The versioned project repository is available at {REPOSITORY_URL} and is released
under the MIT Licence for code and the Creative Commons Attribution 4.0 International
Licence for text and data. It contains the taxonomy, protocol, codebook, search strategy,
threshold and deviation records, scripts, dated search exports, candidate corpus, flow
counts, the adjudicated near-duplicate decisions, the audited bibliography, and the complete
pilot coder files and agreement outputs. Near-duplicate adjudication proposals are
stored separately from official decisions. No screening or extraction dataset is claimed to
exist, because neither stage has been run."""

CONFLICT_OF_INTEREST = """The authors declare no conflict of interest. Any
author-affiliated record that later enters the audit will be coded by an investigator who
did not author it and identified in the released audit data."""

END_MATTER = f"""# Acknowledgements

{ACKNOWLEDGEMENTS}

# Data availability statement

{DATA_AVAILABILITY}

# Conflict of interest statement

{CONFLICT_OF_INTEREST}
"""


def check() -> int:
    problems = []
    for name, label in SECTIONS:
        p = PAPER / name
        if not p.exists():
            problems.append(f"MISSING: {name}  ({label})")
            continue
        text = p.read_text(encoding="utf-8")
        for pat, repl in SUBSTITUTIONS:
            text = re.sub(pat, repl, text, flags=re.M)
        for pat, why in FORBIDDEN:
            for m in re.finditer(pat, text):
                line = text[:m.start()].count("\n") + 1
                problems.append(f"{name}:{line}: {why}: {m.group(0)}")
    if problems:
        print("NOT READY TO ASSEMBLE:\n")
        for p in problems:
            print(f"  {p}")
        print(f"\n{len(problems)} problem(s).")
        return 1
    print("All sections present and free of paper-2 placeholders.")
    return 0


def assemble(out: Path) -> int:
    missing = [n for n, _ in SECTIONS if not (PAPER / n).exists()]
    if missing:
        print("cannot assemble, missing: " + ", ".join(missing), file=sys.stderr)
        return 1
    parts, words = [], 0
    for name, label in SECTIONS:
        text = (PAPER / name).read_text(encoding="utf-8").rstrip()
        for pat, repl in SUBSTITUTIONS:
            text = re.sub(pat, repl, text, flags=re.M)
        words += len(text.split())
        parts.append(text)
        print(f"  {name:32s} {len(text.split()):6d} words   {label}")
    body = "\n\n---\n\n".join(parts)
    body += (
        "\n\n---\n\n# References\n\n"
        "*Bibliography in `paper/references.bib`. Every entry carries a note recording "
        "whether its bibliographic details were confirmed against an authoritative record "
        "and what, if anything, remains unconfirmed.*\n"
    )
    body += "\n---\n\n" + END_MATTER
    out.write_text(body, encoding="utf-8")
    print(f"\n{words} words -> {out}")
    print("Estimated typeset length: ~%.0f pages at 650 words/page." % (words / 650))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=PAPER / "PAPER1.md")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    return check() if args.check else assemble(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
