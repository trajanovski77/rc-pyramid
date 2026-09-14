#!/usr/bin/env python3
"""Build the IEEE Access submission from the same markdown sections as the IOP build.

    python3 scripts/build_ieee.py                 # -> paper/PAPER1-IEEE.tex
    python3 scripts/build_ieee.py --check         # conversion warnings only, no write

Target: IEEE Access, a two-column journal. The IOP build (`build_latex.py`) targets a
one-column journal. Everything except page geometry is shared: this module imports the
converter, the escaper, the citation handling, the abstract reader and the bibliography
cleaner from `build_latex.py` and supplies only its own table and figure renderers and its
own preamble. Two builders that each parsed the markdown would drift, and a construct that
converted correctly for one and silently mangled for the other is the failure this project
exists to report.

WHAT IS DIFFERENT IN TWO COLUMNS, AND WHY IT MATTERS HERE
This manuscript is float-dense: 18 tables, most of them prose rather than numbers, and 9
figures, all of them text-dense diagrams. A prose table squeezed into an 88 mm column
becomes unreadable, and so does a 700-px-wide diagram. Each float is therefore placed in
one column or across both by a stated rule (see WIDE_TABLES and `ieee_table`), not by eye.

SECTION NUMBERING, A DELIBERATE DEVIATION
IEEE house style numbers sections with Roman numerals and subsections with letters. The
manuscript's prose contains roughly a hundred hard-coded cross-references of the form
"Section 7.2", written that way because they are shared with the IOP build. Rewriting them
to "Section VII-B" at build time is mechanical and is exactly what this project already
tried once, in `assemble_paper1.py`, where blanket cross-reference rewriting garbled
sentences and was removed rather than repaired. In a paper about references losing their
meaning in transit, a build step that can silently produce a wrong cross-reference is not
worth the house-style points. Arabic numbering is forced instead, every reference stays
exactly as written and verifiable, and the one-line switch back to Roman is in the preamble
for whoever prefers it.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_latex as B  # noqa: E402

PAPER = Path("paper")
OUT = PAPER / "PAPER1-IEEE.tex"

# Tables placed across both columns. The rule, applied to the markdown before conversion:
# a table spans both columns when its widest row exceeds 100 characters or it has 8 or
# more columns. The first catches prose tables, whose cells wrap to unreadable slivers in
# an 88 mm column; the second catches the review-by-dimension matrix, which has ten.
# Computed once here rather than re-derived per build so the choice is reviewable.
WIDE_MIN_ROW_CHARS = 100
WIDE_MIN_COLS = 8

# Tables the character heuristic sizes wrong, identified by compiling rather than by
# counting. Both are narrow-celled comparison matrices whose *header words* do not fit an
# 88 mm column even though their rows are short: Table 2's family headers ("Addressable
# node", "Distributed medium") and its "Conditional" cells, and Table 15's "Unassignable"
# column header. The first compile reported eight overfull boxes, all of them in these
# two tables and nowhere else. The heuristic measures total row length, which is the right
# proxy for prose tables and the wrong one for a matrix of long labels over short values;
# rather than complicate the rule for two cases, the two cases are named.
# Table 19 joins them for the same reason: its row labels carry unbreakable
# \texttt{} exclusion codes (`not-eligible:publication-type`) that no 88 mm column
# can wrap. Added 2026-09-09 after compiling reported one overfull box there.
FORCE_WIDE = {2, 15, 18, 19}

# Per-table column widths where equal division is wrong. Fractions of the float's width.
TABLE_WIDTHS = {
    # Dimension coverage: one wide review column, nine narrow glyph columns.
    4: (0.19,) + (0.09,) * 9,
    # Confusion matrix: one label column, five counts, one total, across the full width.
    # Table 18 is the pilot's matrix and has the identical shape.
    15: (0.22,) + (0.13,) * 6,
    18: (0.22,) + (0.13,) * 6,
    # Pilot result: the quantity names run long ("Unassignable, coder A, eligible-only"),
    # so the first column takes a third and the three short columns share the rest. Value
    # widened from 0.14 on 2026-09-09: the proof PDF broke "22.5% / 25.0%" across three
    # lines, one of them holding only the slash.
    17: (0.34, 0.19, 0.23, 0.24),
    # Theory applicability: one result column, four family columns, across the full width.
    2: (0.28, 0.18, 0.18, 0.18, 0.18),
    # Pilot dispositions: one long label column carrying \texttt{} exclusion codes, two
    # count columns that hold at most "10 (25.0%)".
    19: (0.50, 0.25, 0.25),
    # The three coding runs: six columns whose natural widths differ by a factor of four.
    # Kappa holds five characters; Outcome holds a sentence. Equal division starves the
    # last column and wastes the fifth.
    20: (0.14, 0.13, 0.18, 0.07, 0.15, 0.33),
}


def is_wide(rows: list[str], number: int = 0) -> bool:
    if number in FORCE_WIDE:
        return True
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    ncol = len(cells[0])
    widest = max(sum(len(c) for c in row) for row in cells)
    return widest > WIDE_MIN_ROW_CHARS or ncol >= WIDE_MIN_COLS


def ieee_table(rows: list[str], label: str, caption: str, number: int) -> str:
    """Markdown pipe table -> IEEE table, single- or double-column by the stated rule."""
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, body = cells[0], cells[2:]
    ncol = len(header)
    for i, r in enumerate(body):
        if len(r) != ncol:
            B.warn(f"table '{caption[:40]}': row {i+1} has {len(r)} cells, header has {ncol}")

    wide = is_wide(rows, number)
    env = "table*" if wide else "table"
    total = r"\textwidth" if wide else r"\columnwidth"

    fracs = TABLE_WIDTHS.get(number)
    if fracs and len(fracs) == ncol:
        spec = "@{}" + "".join(
            ">{\\raggedright\\arraybackslash}p{\\dimexpr" + f"{f}" + total
            + "-2\\tabcolsep\\relax}"
            for f in fracs)
    else:
        cw = rf"\dimexpr({total}/{ncol})-2\tabcolsep\relax"
        spec = "@{}" + "".join(f">{{\\raggedright\\arraybackslash}}p{{{cw}}}"
                               for _ in range(ncol))

    size = r"\scriptsize" if (wide and ncol >= 8) else r"\footnotesize"
    out = [
        rf"\begin{{{env}}}[!t]",
        r"\caption{" + B.conv(caption) + "}",
        rf"\label{{{label}}}",
        r"\centering",
        size,
        rf"\begin{{tabular}}{{{spec}}}",
        r"\hline",
    ]
    out.append(" & ".join(rf"\textbf{{{B.conv(c)}}}" for c in header) + r" \\")
    out.append(r"\hline")
    for r in body:
        r = (r + [""] * ncol)[:ncol]
        out.append(" & ".join(B.conv(c) for c in r) + r" \\")
    out += [r"\hline", r"\end{tabular}", rf"\end{{{env}}}", ""]
    return "\n".join(out)


def ieee_figure(cap: str, path: str, lab: str) -> list[str]:
    """All figures span both columns.

    Every figure in this manuscript is a labelled diagram drawn at 700 to 1000 px wide
    with 8 to 16 px type. Reproduced in an 88 mm column the labels fall below about 5 pt
    and stop being readable; across both columns they land near 7 pt, which is better than
    the one-column IOP build achieves. There is no figure here for which the narrow
    placement would be an improvement, so the choice is not made per figure.
    """
    return [
        r"\begin{figure*}[!t]",
        r"\centerline{\includegraphics[width=\textwidth]{"
        + str(Path(path).with_suffix("")) + "}}",
        rf"\caption{{{B.conv(cap)}}}",
        rf"\label{{{lab}}}",
        r"\end{figure*}", ""]



def add_parstart(section_one: str) -> str:
    """Give the Introduction the IEEE drop cap.

    IEEE Access opens the first section with \\PARstart{R}{eservoir}. It is applied here
    rather than written into the markdown because the markdown is shared with the IOP
    build, where the command does not exist. Warns instead of failing silently if the
    first paragraph is not shaped as expected.
    """
    m = re.search(r"(\\section\{[^}]*\}\n\n)([A-Z])([a-z]+)(\s)", section_one)
    if not m:
        B.warn("PARstart not applied: could not find the first Introduction paragraph")
        return section_one
    return (section_one[:m.start()]
            + m.group(1) + r"\PARstart{" + m.group(2) + "}{" + m.group(3) + "}" + m.group(4)
            + section_one[m.end():])


BOLDMATH = r'''

%% Bold-math setup, carried over verbatim from the IEEE Access template. It names the
%% NewLetters symbol font, which ieeeaccess.cls declares and IEEEtran does not, so this
%% block is emitted only for the submission class. --preprint omits it.
\usepackage{bm}
\makeatletter
\AtBeginDocument{\DeclareMathVersion{bold}
\SetSymbolFont{operators}{bold}{T1}{times}{b}{n}
\SetSymbolFont{NewLetters}{bold}{T1}{times}{b}{it}
\SetMathAlphabet{\mathrm}{bold}{T1}{times}{b}{n}
\SetMathAlphabet{\mathit}{bold}{T1}{times}{b}{it}
\SetMathAlphabet{\mathbf}{bold}{T1}{times}{b}{n}
\SetMathAlphabet{\mathtt}{bold}{OT1}{pcr}{b}{n}
\SetSymbolFont{symbols}{bold}{OMS}{cmsy}{b}{n}
\renewcommand\boldmath{\@nomath\boldmath\mathversion{bold}}}
\makeatother'''

PREAMBLE = r"""%% IEEE Access submission
%% GENERATED FILE. Source of truth is paper/*.md; regenerate with
%%   python3 scripts/build_ieee.py
%% Edits made here are lost on the next build.
%%
%% ===========================================================================
%% DOCUMENT CLASS -- this is the SUBMISSION build and uses the real class.
%%
%% ieeeaccess.cls is distributed by IEEE through the Author Center. It is NOT on
%% CTAN and NOT in TeX Live, so it must be beside this file. On Overleaf, start
%% from the official "IEEE Access LaTeX Template" and drop this project's files
%% into it; the class and its support files come with that template.
%%
%% COMPILER: pdfLaTeX. XeLaTeX and LuaLaTeX both FAIL on this class, because
%% ieeeaccess.cls loads spotcolor.sty for the PANTONE 3015 C spot colour and
%% spotcolor.sty uses pdfTeX-only primitives (\pdfobj, \pdfliteral,
%% \pdfpageresources). This is also why a local Tectonic build cannot compile
%% this file: Tectonic is XeTeX-based.
%%
%% FOR A LOCAL PREVIEW without ieeeaccess.cls, regenerate with
%%   python3 scripts/build_ieee.py --preprint
%% which swaps in IEEEtran plus ieeeaccess-shim.sty. The shim APPROXIMATES the
%% layout and is not the submission format: do not send a PDF built that way to
%% IEEE.
%% ===========================================================================

__DOCUMENTCLASS__

\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{array}
\usepackage{url}

%% BIOGRAPHY SPACING. IEEEtran, and ieeeaccess.cls after it, sets the gap above each
%% biography to \vskip \@IEEEBIOskipN plus 1fil minus 0\baselineskip, with
%% \@IEEEBIOskipN at 4\baselineskip. The infinitely stretchable `plus 1fil' lets those
%% gaps soak up all the slack in a short column, which opens a large hole between the
%% end of the references and the first biography and pushes the eight biographies apart.
%% Shrink the nominal gap and drop the stretch; \raggedbottom, set just before the
%% biographies, then collects the leftover space at the foot of the last column instead.
\usepackage{etoolbox}
\makeatletter
\def\@IEEEBIOskipN{1.5\baselineskip}
\expandafter\patchcmd\csname\string\IEEEbiography\endcsname
  {plus 1fil minus 0\baselineskip}{}{}
  {\@latex@warning{Could not remove the 1fil stretch from IEEEbiography}}
\makeatother

%% SECTION NUMBERING. IEEE house style is Roman sections and lettered
%% subsections. The prose carries about a hundred hard-coded references of the
%% form "Section 7.2", shared with the IOP build, so arabic numbering is forced
%% here to keep every one of them correct and checkable. To restore house
%% style, delete the three lines below -- and then verify the cross-references,
%% because they will no longer match the headings.
%% IEEEtran typesets a heading's number from \the<level>dis, NOT from \the<level>:
%% \thesubsectiondis is hard-coded to \Alph{subsection}, so renewing \thesubsection alone
%% changes what \ref prints and leaves the heading reading "A.". Both are set here. The
%% \@ifundefined guards mean the same file still compiles if a class does not define the
%% display macros.
\makeatletter
\renewcommand{\thesection}{\arabic{section}}
\renewcommand{\thesubsection}{\thesection.\arabic{subsection}}
\renewcommand{\thesubsubsection}{\thesubsection.\arabic{subsubsection}}
\@ifundefined{thesubsectiondis}{}{%
  \renewcommand{\thesubsectiondis}{\thesection.\arabic{subsection}.}}
\@ifundefined{thesubsubsectiondis}{}{%
  \renewcommand{\thesubsubsectiondis}{%
    \thesection.\arabic{subsection}.\arabic{subsubsection}.}}
\makeatother

\begin{document}

\history{Date of publication xxxx 00, 0000, date of current version xxxx 00, 0000.}
\doi{10.1109/ACCESS.2026.DOI}

\title{A Review of Reservoir Computing Classification Schemes and an
Architecture-Based Framework for Evaluating Reported Systems}

%% AUTHOR BLOCK.
%% Full given names, which is IEEE's preference and matches the biographies.
%% \uppercase and the capitalised AND before the last author follow the template.
\author{\uppercase{Stefan Trajanovski}\authorrefmark{1},
\uppercase{Ema Pandilova}\authorrefmark{1},
\uppercase{Marko Petrov}\authorrefmark{1},
\uppercase{Ivan Kitanovski}\authorrefmark{1},
\uppercase{Ivan Chorbev}\authorrefmark{1},
\uppercase{Ivica Dimitrovski}\authorrefmark{1},
\uppercase{Dimitar Trajanov}\authorrefmark{1},
AND \uppercase{Ilinka Ivanoska}\authorrefmark{1}}

\address[1]{Faculty of Computer Science and Engineering, Ss. Cyril and Methodius
University in Skopje, Rudzer Boshkovikj 16, P.O. 393, Skopje 1000, North Macedonia
(e-mail: stefan.trajanovski@students.finki.ukim.mk)}

\tfootnote{This work was supported by the Ministry of Education and Science of the Republic
of North Macedonia through the project ``Utilizing AI and National Large Language Models to
Advance Macedonian Language Capabilities'', and co-funded by EC/EuroHPC JU, the Ministry of
Digital Transformation of the Republic of North Macedonia, and the Faculty of Computer
Science and Engineering, Ss. Cyril and Methodius University in Skopje, through the VEZILKA
project, Grant Agreement No. 101263128.}

%% Running head. Shortened from the full title, which overflows the header width:
%% IEEE style permits a shortened form and the full title is 122 characters.
\markboth
{Trajanovski \headeretal: A Review of Reservoir Computing Classification Schemes}
{Trajanovski \headeretal: A Review of Reservoir Computing Classification Schemes}

\corresp{Corresponding author: Stefan Trajanovski (e-mail:
stefan.trajanovski@students.finki.ukim.mk).}

\begin{abstract}
__ABSTRACT__
\end{abstract}

\begin{keywords}
Benchmarking, neuromorphic computing, physical computing, reproducibility, reservoir
computing, research methodology, taxonomy.
\end{keywords}

\titlepgskip=-21pt

\maketitle

"""

# The three end-matter statements come from assemble_paper1.py through build_latex.py, so
# the markdown and the two LaTeX builds cannot disagree about them; see the note there.
# Only the sectioning commands differ between formats.
POSTAMBLE_TEMPLATE = r"""
\section*{Acknowledgements}

__ACKNOWLEDGEMENTS__


\section*{Data Availability Statement}

__DATA_AVAILABILITY__

\section*{Conflict of Interest Statement}

__CONFLICT_OF_INTEREST__

\bibliographystyle{IEEEtran}
\bibliography{references-submission}

%% Collect leftover vertical space at the foot of the column rather than
%% distributing it between the biographies. Pairs with the \@IEEEBIOskipN patch
%% in the preamble; neither half works alone.
\raggedbottom

%% ===========================================================================
%% AUTHOR BIOGRAPHIES
%%
%% IEEE Access requires a photograph and a short biography for every author.
%% paper/biographies.tex is hand-maintained and copied in verbatim; build_ieee.py
%% checks that every author has exactly one entry, that the order matches the
%% author block, and that every referenced photograph exists on disk.
%% ===========================================================================

__BIOGRAPHIES__

\EOD

\end{document}
"""


def postamble() -> str:
    """The end matter and the biographies, from the shared plain-text source."""
    return (POSTAMBLE_TEMPLATE
            .replace("__ACKNOWLEDGEMENTS__", B.conv(B.ACKNOWLEDGEMENTS))
            .replace("__DATA_AVAILABILITY__",
                     B.conv(B.DATA_AVAILABILITY).replace(
                         B.conv(B.REPOSITORY_URL), r"\url{" + B.REPOSITORY_URL + "}"))
            .replace("__CONFLICT_OF_INTEREST__", B.conv(B.CONFLICT_OF_INTEREST))
            .replace("__BIOGRAPHIES__", biographies()))


# Order must match the author block above. Changing one without the other would give an
# author someone else's biography, which no compile-time check would catch.
BIO_NAMES = [
    "S. TRAJANOVSKI",
    "E. PANDILOVA",
    "M. PETROV",
    "I. KITANOVSKI",
    "I. CHORBEV",
    "I. DIMITROVSKI",
    "D. TRAJANOV",
    "I. IVANOSKA",
]

BIOGRAPHIES = PAPER / "biographies.tex"
PHOTO_DIR = PAPER / "photos"


def biographies() -> str:
    """Return paper/biographies.tex verbatim, after checking it against the author block.

    The file is hand-maintained, not generated: a biography is prose about a real person
    and there is nothing for a converter to do to it. What the build owes instead is the
    check that LaTeX cannot make. IEEE prints biographies in sequence and nothing ties one
    to an author, so a list that drifts out of order gives an author someone else's life
    and compiles without a murmur. Three properties are verified here:

      1. one biography per author in the block, none missing, none extra;
      2. the same order as the author block, matched on surname;
      3. every photograph a biography entry references actually exists on disk.

    Surname matching is used rather than full-name matching because the author block
    carries initials ("I. IVANOSKA") and the biographies carry given names
    ("Ilinka Ivanoska"), which is the correct form in each place.
    """
    if not BIOGRAPHIES.exists():
        B.warn(f"{BIOGRAPHIES} is missing; no biographies emitted")
        return ""
    text = BIOGRAPHIES.read_text(encoding="utf-8")
    live = re.sub(r"(?<!\\)%.*$", "", text, flags=re.M)

    # The author's name is the LAST brace group on the \begin line. It cannot be matched
    # with a simple optional-argument pattern, because the photo argument is
    # [{\includegraphics[width=...]{file}}] and contains both ] and } characters; an
    # earlier `[^\]]*` pattern stopped at the first ] and captured the photo path as the
    # author's name. Scanning the line for its final balanced {...} is exact and does not
    # care what the optional argument holds.
    found = []
    for line in live.splitlines():
        if not line.lstrip().startswith("\\begin{IEEEbiography"):
            continue
        depth, start, last = 0, None, None
        for i, ch in enumerate(line):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    last = line[start + 1:i]
        if last is not None:
            found.append(last)
    expected = [n.split()[-1].upper() for n in BIO_NAMES]
    got = [n.split()[-1].upper() for n in found]

    if got != expected:
        missing = [e for e in expected if e not in got]
        extra = [g for g in got if g not in expected]
        if missing:
            B.warn(f"biographies.tex is missing an entry for: {', '.join(missing)}")
        if extra:
            B.warn(f"biographies.tex has an entry with no matching author: {', '.join(extra)}")
        if not missing and not extra:
            B.warn(f"biographies.tex order {got} does not match the author block {expected}; "
                   f"IEEE prints these in sequence, so this would misattribute a biography")

    for env in ("IEEEbiography", "IEEEbiographynophoto"):
        if live.count(rf"\begin{{{env}}}") != live.count(rf"\end{{{env}}}"):
            B.warn(f"biographies.tex has unbalanced {env} environments")

    for photo in re.findall(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", live):
        rel = photo if photo.startswith("photos/") else photo
        hit = any((PAPER / f"{rel}{ext}").exists() for ext in ("", ".jpg", ".jpeg", ".png", ".pdf"))
        if not hit:
            B.warn(f"biographies.tex references a photo that does not exist: {photo}")

    stubs = len(re.findall(r"Biography text to be supplied by the author\.", live))
    photos = len(re.findall(r"\\begin\{IEEEbiography\}", live))

    # `20xx` marks a year the drafter could not source. It is deliberately visible rather
    # than guessed or silently dropped, on the same principle as the [MEASURE] markers in
    # the manuscript sources: a placeholder a reader can see is a true statement about the
    # state of the evidence, and an invented year is not. It must never reach a submission,
    # so it warns, which fails `--check`.
    placeholders = len(re.findall(r"\b20xx\b", live))
    if placeholders:
        B.warn(f"biographies.tex carries {placeholders} unresolved 20xx year "
               f"placeholder(s); these must be filled before submission")

    print(f"  biographies:     {len(found)} entries, {photos} with a photograph, "
          f"{stubs} awaiting author text, {placeholders} unresolved 20xx year(s)")
    return text.rstrip() + "\n"




# =====================================================================================
# SHORT BUILD
# =====================================================================================
# IEEE Access "strongly recommends" under 20 pages and requires the Editor-in-Chief's
# pre-approval above it; the full build is 31. The 20-page count excludes supplementary
# material, so the lever is to move floats out of the main document rather than delete
# them: nothing is lost, and what moves is still peer-reviewed as supplementary material.
#
# WHAT MOVES, AND WHY EACH ONE
# Every float below is either restated by a float that stays, or is secondary to the
# argument. Nothing that carries a headline result moves.
#
#   T4  dimension coverage      a refinement of T3, which stays
#   T5  CHARC comparison        the prose states the four contrasts
#   T9  evidence and efficiency Figure 5 plots it and stays
#   T12 shift-register sources  the prose states all four values and their bases
#   T13 results vs baselines    Figure 9 plots it and stays
#   T15 preliminary matrix      the preliminary check is secondary to the pilot
#   T16 preliminary reasons     same
#   F1  milestones timeline     contextual, carries no result
#   F4  substrate-by-family     Table 6 carries the assignments it visualises
#   F7  corpus landscape        the prose states every percentage in it
#   F8  NARMA lineage           Table 12 moves with it; the prose carries the values
#   F10 valid-prediction-time   the prose narrates the same two-stage sequence
#
# The pilot result, its confusion matrix, the dispositions, the three coding runs, the
# anchor verification, the threats table and the PRISMA flow all stay. So does the
# F3/F4 limitation and everything supporting it.
SHORT_DROP_TABLES = {4, 5, 9, 12, 13, 15, 16}

# Column widths that apply ONLY in the supplement, which is set one column wide. Table 4's
# ten-column grid is sized for a two-column table* in the main build and overflows a
# one-column page: the review-name column needs more room there, not less, because
# "Topological-systems review 2024" no longer has a facing column to borrow from. Kept
# separate from TABLE_WIDTHS so that tuning the supplement cannot move the submission.
SUPPLEMENT_WIDTHS = {4: (0.28,) + (0.078,) * 9}
SHORT_DROP_FIGURES = {"fig18s", "fig20s", "fig22s", "fig19s", "fig21s"}

# Ranges are the only references the generic remapper cannot rewrite, because "Tables 3--6"
# may span kept and moved floats at once. They are listed here and were expanded by hand
# against the map below. Every SINGLE reference is remapped automatically: a kept float
# takes its new number, a moved one becomes S<n> and resolves in the supplement.
SHORT_PROSE = [
    ("Tables 3--6, Figures 2--4; preliminary check in Tables 15--16; pilot result in Tables 17--20",
     "Tables 3--4, Figures 1--2; preliminary check in the supplement; pilot result in Tables 10--13"),
    ("Tables 7--9, Figure 5; the same twelve systems coded for evidence level and efficiency claim",
     "Tables 5--6 and Figure 3; the same twelve systems coded for evidence level and efficiency claim"),
    ("Tables 11--14, Figures 8--10",
     "Tables 8--9 and Figure 5, with the lineage and verdict tables in the supplement"),
    ("Table 10, Figures 6--7; released code and dated search exports",
     "Table 7 and Figure 4; released code and dated search exports"),
    ("Sections 6.1 and 8.4, Tables 18--19", "Sections 6.1 and 8.4, Tables 11--12"),
    # Table 5 (CHARC) carried a label and no prose reference, so moving it left an
    # uncited item in the supplement. The sentence that introduces CHARC now points at it.
    ("CHARC requires access to the device; the present method requires a paper-level "
     "description. The two methods are therefore complementary.",
     "CHARC requires access to the device; the present method requires a paper-level "
     "description. The two methods are therefore complementary, and Table S2 in the "
     "supplementary material sets the two side by side."),
]


def short_maps():
    """(table_map, figure_map): old manuscript number -> new number or 'S<n>'.

    Derived from the drop sets rather than written out, so the two cannot disagree.
    """
    tmap, smap, keep, supp = {}, {}, 0, 0
    for n in range(1, 23):
        if n in SHORT_DROP_TABLES:
            supp += 1
            tmap[n] = f"S{supp}"
        else:
            keep += 1
            tmap[n] = str(keep)
    order = ["fig18s", "fig1", "fig3", "fig20s", "fig24s",
             "fig7s", "fig22s", "fig19s", "fig23s", "fig21s"]
    keep = supp = 0
    for i, name in enumerate(order, 1):
        if name in SHORT_DROP_FIGURES:
            supp += 1
            smap[i] = f"S{supp}"
        else:
            keep += 1
            smap[i] = str(keep)
    return tmap, smap


def shorten(md: str) -> str:
    """Rewrite a section source for the short build: ranges first, then every single ref."""
    import re as _re
    tmap, fmap = short_maps()
    for a, b in SHORT_PROSE:
        pat = _re.compile(r"\s+".join(map(_re.escape, a.split())))
        md = pat.sub(lambda m, b=b: b, md)

    def one(kind, mapping):
        def f(m):
            n = int(m.group(1))
            return f"{kind} {mapping.get(n, m.group(1))}"
        return f

    # Label lines ("**Table 7. ...**") keep their ORIGINAL numbers on purpose. LaTeX
    # numbers captions itself, in document order, so after the moved tables are removed the
    # survivors come out 1..15 -- which is exactly what tmap says. The label number is
    # therefore never printed; it is only the key that TABLE_WIDTHS and FORCE_WIDE look up.
    # Renumbering it broke that lookup and put four overfull boxes into the first short
    # build, because the pilot tables stopped matching their hand-set column widths.
    md = _re.sub(r"(?<!\*)(?<!\*\*)\bTable (\d+)\b(?!\.\*\*)", one("Table", tmap), md)
    md = _re.sub(r"\bFigure (\d+)\b", one("Figure", fmap), md)
    return md


def split_for_short(md: str):
    """(main_md, moved) - pull the moved floats out of a section before conversion.

    Extraction happens BEFORE renumbering, because the drop sets are keyed by the
    manuscript's own numbers. `moved` entries are (kind, original_number_or_name,
    caption, block) and are re-emitted verbatim in the supplement.
    """
    import re as _re
    moved, out, lines, i = [], [], md.split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        m = _re.match(r"^\*\*Table (\d+)\. (.+?)\*\*\s*$", ln.strip())
        if m and int(m.group(1)) in SHORT_DROP_TABLES:
            num, cap = int(m.group(1)), m.group(2)
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("|"):
                j += 1
            k = j
            while k < len(lines) and lines[k].strip().startswith("|"):
                k += 1
            moved.append(("table", num, cap, "\n".join(lines[j:k])))
            i = k
            while i < len(lines) and not lines[i].strip():
                i += 1
            continue
        mi = _re.match(r"^!\[(.*?)\]\((?:figures/)?(\w+)\.pdf\)", ln.strip())
        if mi and mi.group(2) in SHORT_DROP_FIGURES:
            moved.append(("figure", mi.group(2), mi.group(1), ln.strip()))
            i += 1
            continue
        out.append(ln)
        i += 1
    return "\n".join(out), moved


SUPPLEMENT_PREAMBLE = r"""%% Supplementary material for the IEEE Access submission
%% GENERATED FILE. Regenerate with: python3 scripts/build_ieee.py --short
%%
%% This carries the floats moved out of the main document so that it meets the
%% 20-page recommendation. Nothing here was cut: every item is referenced from the
%% main text by its S-number and is peer-reviewed as supplementary material.
%% One column on purpose: several of the moved tables are full-text-width
%% matrices, and in two columns they overflow. A supplement has no house style
%% to honour, so the layout follows the content.
\documentclass[journal,onecolumn,12pt]{IEEEtran}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{array}
\usepackage{url}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\begin{document}
\title{Supplementary Material: A Review of Reservoir Computing Classification
Schemes and an Architecture-Based Framework for Evaluating Reported Systems}
\author{Stefan Trajanovski, Ema Pandilova, Marko Petrov, Ivan Kitanovski, Ivan Chorbev,
Ivica Dimitrovski, Dimitar Trajanov and Ilinka Ivanoska}
\maketitle

This document carries the tables and figures referenced from the main text by their
S-numbers. They were placed here so that the main document meets the IEEE Access
20-page recommendation; none of the material was removed from the study, and each item
is identical to the version the full manuscript carries.

"""


def strip_comments(tex: str) -> str:
    """Drop whole-line LaTeX comments from the generated file.

    The preambles in this module carry a lot of commentary: why a table is forced
    wide, why section numbering is arabic, which lines to switch for the real class.
    That belongs in this script, where it is maintained and version-controlled, not
    in the file a copy-editor opens. A whole-line comment contributes nothing to the
    typeset output, so removing it cannot change the PDF.

    Only lines whose first non-space character is % are removed, and one class of
    comment is kept: anything tagged [IOP] or [PREPRINT]. Those are not documentation,
    they are the commented-out class, package and bibliography-style lines a reader
    uncomments to switch formats, plus the instructions for doing it. Stripping them
    would delete the switching procedure that OVERLEAF-README.txt tells the reader to
    follow. A trailing `%` that suppresses a newline is part of a content line and is
    left alone.
    """
    def drop(ln: str) -> bool:
        s = ln.lstrip()
        if not s.startswith("%"):
            return False
        return "[IOP]" not in ln and "[PREPRINT]" not in ln

    out = [ln for ln in tex.split("\n") if not drop(ln)]
    # collapse the blank runs the removals leave behind
    kept, blanks = [], 0
    for ln in out:
        blanks = blanks + 1 if not ln.strip() else 0
        if blanks < 3:
            kept.append(ln)
    return "\n".join(kept)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--short", action="store_true",
                    help="build the ~20-page variant: seven tables and five figures move "
                         "to a companion supplement, every cross-reference is remapped, and "
                         "paper/PAPER1-IEEE-supplement.tex is written alongside")
    ap.add_argument("--preprint", action="store_true",
                    help="emit IEEEtran + ieeeaccess-shim instead of the real "
                         "ieeeaccess.cls, so the file compiles without the IEEE class "
                         "and under a XeTeX engine such as Tectonic. APPROXIMATES the "
                         "layout; never submit a PDF built this way.")
    args = ap.parse_args()

    missing = [s for s in B.SECTIONS if not (PAPER / s).exists()]
    if missing:
        print("missing sections: " + ", ".join(missing), file=sys.stderr)
        return 1

    B.WARNINGS.clear()
    body, wide_tables, all_tables, moved = [], 0, 0, []
    for n, name in enumerate(B.SECTIONS, 1):
        md = (PAPER / name).read_text(encoding="utf-8")
        if args.short:
            md, m_here = split_for_short(md)
            moved.extend(m_here)
            md = shorten(md)
        for m in re.finditer(r"^\*\*Table (\d+)\.", md, flags=re.M):
            all_tables += 1
        converted = B.convert(md, n, table_renderer=ieee_table, figure_renderer=ieee_figure)
        if n == 1:
            converted = add_parstart(converted)
        wide_tables += converted.count(r"\begin{table*}")
        body.append(converted)
        print(f"  {name:32s} -> section {n}")

    # The class line is the only difference between the submission build and the local
    # preview build. Substituted rather than branched on a second template, because two
    # preambles would drift and the drift would not show up until submission.
    if args.preprint:
        klass = ("\\documentclass[journal]{IEEEtran}     %% [PREPRINT, NOT THE "
                 "SUBMISSION FORMAT]\n\\usepackage{ieeeaccess-shim}          "
                 "%% [PREPRINT, NOT THE SUBMISSION FORMAT]")
        B.warn("built in --preprint mode: IEEEtran + shim, NOT ieeeaccess.cls. "
               "This approximates the layout and must not be submitted.")
    else:
        klass = "\\documentclass{ieeeaccess}" + BOLDMATH

    tex = (PREAMBLE.replace("__DOCUMENTCLASS__", klass)
           .replace("__ABSTRACT__", B.abstract_from_frontmatter())
           + "\n".join(body)
           + postamble())

    # Structural checks run on the file with LaTeX comments stripped. The preamble and
    # the biography block deliberately contain commented-out \begin{...} lines showing
    # how to switch class or add a photo, and counting those as real environments
    # produced a false "unbalanced" warning on the first build.
    live = re.sub(r"(?<!\\)%.*$", "", tex, flags=re.M)
    for env in ("table", "table*", "figure*", "IEEEbiographynophoto", "abstract",
                "keywords", "tabular"):
        if live.count(rf"\begin{{{env}}}") != live.count(rf"\end{{{env}}}"):
            B.warn(f"unbalanced {env} environments")
    for leftover in re.finditer(r"(?<!\\)\[([A-Z][A-Za-z0-9]*)\](?!\()", live):
        if leftover.group(1) not in ("PREPRINT", "ACCESS", "AUTHOR", "TO"):
            B.warn(f"possible unconverted citation: [{leftover.group(1)}]")
    if "__" in live.replace("__pycache__", ""):
        B.warn("an unsubstituted __PLACEHOLDER__ survived into the output")

    if B.WARNINGS:
        print(f"\n{len(B.WARNINGS)} warning(s):")
        for w in B.WARNINGS[:25]:
            print(f"  ! {w}")
    else:
        print("\nno conversion warnings")

    if args.check:
        return 1 if B.WARNINGS else 0

    submission_bib = PAPER / "references-submission.bib"
    submission_bib.write_text(
        B.submission_bibliography((PAPER / "references.bib").read_text(encoding="utf-8")),
        encoding="utf-8")
    if args.short:
        parts = [SUPPLEMENT_PREAMBLE]
        for kind, key, cap, block in moved:
            if kind == "table":
                saved = TABLE_WIDTHS.get(key)
                if key in SUPPLEMENT_WIDTHS:
                    TABLE_WIDTHS[key] = SUPPLEMENT_WIDTHS[key]
                rendered = ieee_table(block.split("\n"), f"tab:supp{key}", cap, key)
                if key in SUPPLEMENT_WIDTHS:
                    if saved is None:
                        TABLE_WIDTHS.pop(key, None)
                    else:
                        TABLE_WIDTHS[key] = saved
                parts.append(rendered
                             .replace(r"\begin{table*}[!t]", r"\begin{table}[!t]")
                             .replace(r"\end{table*}", r"\end{table}"))
            else:
                parts.append("\n".join(ieee_figure(cap, f"figures/{key}.pdf", f"fig:supp{key}"))
                             .replace(r"\begin{figure*}[!t]", r"\begin{figure}[!t]")
                             .replace(r"\end{figure*}", r"\end{figure}"))
        parts.append("\n\\end{document}\n")
        supp = PAPER / "PAPER1-IEEE-supplement.tex"
        supp.write_text(strip_comments("\n".join(parts)), encoding="utf-8")
        n_t = sum(1 for k, *_ in moved if k == "table")
        n_f = sum(1 for k, *_ in moved if k == "figure")
        print(f"  supplement:      {supp}  ({n_t} tables, {n_f} figures)")
    args.out.write_text(strip_comments(tex), encoding="utf-8")
    print(f"\n{len(tex.split())} words -> {args.out}")
    print(f"  \\cite commands:  {tex.count(chr(92) + 'cite{')}")
    print(f"  tables:          {all_tables}  ({wide_tables} spanning both columns, "
          f"{all_tables - wide_tables} single-column)")
    print(f"  figures:         {tex.count(chr(92) + 'begin{figure*}')}  (all full width)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
