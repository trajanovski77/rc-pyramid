#!/usr/bin/env python3
"""Build the IOP-format LaTeX submission from the markdown sections.

    python3 scripts/build_latex.py                 # -> paper/PAPER1.tex
    python3 scripts/build_latex.py --check         # report conversion warnings only

Target: Neuromorphic Computing and Engineering (IOP Publishing), article type "Paper".
Uses iopart.cls, which IOP supplies; see paper/latex/README-latex.md for the files needed.

WHY A CONVERTER RATHER THAN A HAND-WRITTEN .TEX
The markdown sections are the source of truth and they are still being edited. A hand-copied
LaTeX file diverges from them within a day, and the divergence is invisible: both files look
finished. This script regenerates the submission from the same sections `assemble_paper1.py`
reads, so a correction made once lands in both.

It is deliberately strict. Anything it cannot convert faithfully is reported as a warning
rather than silently mangled, because a citation that quietly becomes literal text, or a
table that loses a column, is exactly the class of error this paper is about.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_paper1 import (  # noqa: E402  single source for the URL and the end matter
    ACKNOWLEDGEMENTS,
    CONFLICT_OF_INTEREST,
    DATA_AVAILABILITY,
    REPOSITORY_URL,
)

PAPER = Path("paper")
OUT = PAPER / "PAPER1.tex"

# Same order as assemble_paper1.py, minus the front matter, which becomes the IOP preamble.
SECTIONS = [
    "p1-s1-introduction.md",
    "s2-foundations.md",
    "s3-pyramid.md",
    "s4-facets.md",
    "s5-benchmarks.md",
    "s6-methodology.md",
    "s7-corpus-construction.md",
    "s8-results.md",
    "s9-discussion-limitations.md",
    "s10-conclusion.md",
]

# Shared with assemble_paper1.py: paper 2's placeholders render as explicit deferrals.
# The section sources are paper-1-native (see the convention note in assemble_paper1.py),
# so [MEASURE] is the only substitution; the old cross-reference rewriting garbled text
# and was removed.
SUBSTITUTIONS = [
    (r"`?\[MEASURE\]`?", ""),
]

# Captions come from the sources' own "**Table N. ...**" label lines, which the manuscript
# audit already checks for length and sequential numbering. A hard-coded caption dict keyed
# by section-position broke silently when the 2026-08-20 restructure moved a table between
# sections, so position-keyed captions were removed rather than repaired. Derived captions
# remain the fallback for a table that carries no label line.

WARNINGS: list[str] = []


def warn(msg: str) -> None:
    WARNINGS.append(msg)


def submission_bibliography(source: str) -> str:
    """Remove private verification notes while preserving the audited source bibliography."""
    clean: list[str] = []
    skipping = False
    depth = 0
    for line in source.splitlines():
        line = re.sub(r",\s*note\s*=\s*\{.*\}\s*$", "", line, flags=re.I)
        if not skipping and re.match(r"^\s*note\s*=", line, flags=re.I):
            skipping = True
            depth = line.count("{") - line.count("}")
            if depth <= 0:
                skipping = False
            continue
        if skipping:
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                skipping = False
            continue
        clean.append(line)
    return "\n".join(clean) + "\n"


# ------------------------------------------------------------------ escaping

# Unicode the sources use that LaTeX needs told about.
UNICODE = {
    "\u2264": r"$\leq$", "\u2265": r"$\geq$", "\u2260": r"$\neq$",
    "\u00b1": r"$\pm$", "\u00d7": r"$\times$", "\u2248": r"$\approx$",
    "\u2192": r"$\rightarrow$", "\u2190": r"$\leftarrow$",
    "\u03bb": r"$\lambda$", "\u03ba": r"$\kappa$", "\u03c3": r"$\sigma$",
    "\u03b1": r"$\alpha$", "\u03b2": r"$\beta$", "\u03b3": r"$\gamma$",
    "\u03b4": r"$\delta$", "\u0394": r"$\Delta$", "\u03c4": r"$\tau$",
    "\u03c6": r"$\varphi$", "\u00b2": r"$^2$", "\u00b3": r"$^3$",
    "\u2013": "--", "\u2014": "---", "\u2019": "'", "\u2018": "`",
    "\u201c": "``", "\u201d": "''", "\u00a0": "~", "\u2026": r"\ldots{}",
    "\u00e9": r"\'e", "\u00fc": r'\"u', "\u00f6": r'\"o', "\u00e8": r"\`e",
    "\u010d": r"\v{c}", "\u0161": r"\v{s}", "\u00f8": r"\o{}",
    "\u25cf": r"$\bullet$", "\u25cb": r"$\circ$",
}

SPECIAL = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
           "_": r"\_", "{": r"\{", "}": r"\}"}


def esc(t: str) -> str:
    """Escape LaTeX specials. Applied before any markup is introduced."""
    # The backslash is replaced by a sentinel first and expanded last. Substituting
    # \textbackslash{} here would hand its own braces to the "{" and "}" rules below,
    # which turn them into \{ and \}; the result typesets as a backslash followed by a
    # literal brace pair. That defect shipped in Table 15's "Coder A \ Coder B" header
    # and is the reason this is a sentinel and not a direct replacement.
    SENTINEL = "\x00BACKSLASH\x00"
    t = t.replace("\\", SENTINEL)
    for ch, rep in SPECIAL.items():
        t = t.replace(ch, rep)
    t = t.replace("^", r"\textasciicircum{}").replace("~", r"\textasciitilde{}")
    for ch, rep in UNICODE.items():
        t = t.replace(ch, rep)
    return t.replace(SENTINEL, r"\textbackslash{}")


def inline(t: str) -> str:
    """Convert inline markdown on an already-escaped string."""
    # Code spans become \texttt{}, which is unbreakable, and a file path is long enough
    # to matter: `docs/benchmark-thresholds.md` and `docs/prisma-2020-checklist.md` are 28
    # and 29 characters, and in IEEE Access's narrow column TeX preferred a small overfull
    # box to the large hole that moving the whole span to the next line would leave. Both
    # ran into the gutter in the first real ieeeaccess.cls proof, which the IEEEtran shim
    # had not reproduced. A break is therefore permitted after each separator, which is
    # where a reader would break a path anyway. \allowbreak adds an opportunity and no
    # hyphen, so nothing is inserted into the typeset string.
    def code(m):
        # Break after a slash or a hyphen only. Breaking after the dot too was the first
        # attempt and it split "docs/protocol.md" into "docs/protocol." and "md", which
        # reads as a sentence ending mid-path. Slash and hyphen are where a reader would
        # break a path, and they are enough: the two spans that overflowed both carry one.
        s = re.sub(r"([/-])(?=.)", r"\1\\allowbreak{}", m.group(1))
        return r"\texttt{" + s + "}"
    t = re.sub(r"`([^`]+)`", code, t)
    # Straight ASCII quote pairs -> TeX quotes, after code spans so the inserted
    # backticks cannot be mistaken for markdown code. Without this a quotation opens
    # with a closing quote in the typeset paper. All source quotes are balanced within
    # a paragraph (checked 2026-08-02); an unpaired quote is left alone and warned about.
    t = re.sub(r'"([^"]*)"', r"``\1''", t)
    if '"' in t:
        warn(f"unpaired straight quote in: {t[:60]}")
    t = re.sub(r"\*\*([^*]+)\*\*", lambda m: r"\textbf{" + m.group(1) + "}", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", lambda m: r"\textit{" + m.group(1) + "}", t)
    # Citations: [Key] or [Key1, Key2]. Bibtex keys are alphanumeric.
    def cite(m):
        keys = [k.strip() for k in m.group(1).split(",")]
        if all(re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", k) for k in keys):
            return r"\cite{" + ",".join(keys) + "}"
        return m.group(0)
    t = re.sub(r"\[([A-Za-z][A-Za-z0-9]*(?:\s*,\s*[A-Za-z][A-Za-z0-9]*)*)\]", cite, t)
    return t


def conv(t: str) -> str:
    return inline(esc(t))


# ------------------------------------------------------------------ blocks

# Per-table column widths where equal division is wrong, keyed by the manuscript's own
# table number. Same mechanism as build_ieee.py's TABLE_WIDTHS, and needed for the same
# reason: the equal-division default is right for prose tables and wrong for a matrix of
# long headers over short values, where the header word sets the required width and the
# row length does not predict it. Both entries below were identified by compiling.
TABLE_WIDTHS = {
    # Theory applicability: one result column, four family columns.
    2: (0.36, 0.16, 0.16, 0.16, 0.16),
    # Dimension coverage: one wide review column, nine narrow glyph columns.
    4: (0.19,) + (0.09,) * 9,
    # Coder confusion matrix. "Unassignable" is a single unbreakable 12-character word and
    # appears both as a row label and as a bold column header, so neither of those two
    # columns can be sized by equal division and neither can wrap out of trouble. They get
    # the width the word needs; the four family columns and the total hold two digits.
    # Added 2026-09-05, after compiling reported the overflow twice.
    15: (0.185, 0.105, 0.105, 0.105, 0.105, 0.205, 0.11),
    # Table 18 is the pilot's confusion matrix and has the identical shape and the same
    # unbreakable header word, so it takes the same widths.
    18: (0.185, 0.105, 0.105, 0.105, 0.105, 0.205, 0.11),
    # Pilot dispositions. The label column carries unbreakable \texttt{} exclusion codes;
    # the two count columns hold at most "10 (25.0%)". Added 2026-09-09 after compiling.
    19: (0.60, 0.20, 0.20),
    # The three coding runs: six columns whose natural widths differ by a factor of four.
    # Kappa holds five characters, Outcome a sentence.
    # Sums to 0.98, not 1.00: the column spec opens with @{} but not close with it, so
    # one trailing \tabcolsep survives and a spec summing to exactly \linewidth
    # overflows by about 6pt. The other entries here are narrow enough not to notice.
    20: (0.13, 0.12, 0.16, 0.11, 0.18, 0.28),
}


def table(rows: list[str], label: str, caption: str, number: int = 0) -> str:
    """Markdown pipe table -> IOP tabular using \\br and \\mr rules."""
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, body = cells[0], cells[2:]          # cells[1] is the |---| separator
    ncol = len(header)
    for i, r in enumerate(body):
        if len(r) != ncol:
            warn(f"table '{caption[:40]}': row {i+1} has {len(r)} cells, header has {ncol}")
    # Ragged-right p-columns: these tables are prose, not numbers.
    # Exact: divide the text block by the column count, then subtract the padding
    # LaTeX adds on both sides of every column. Guessing a fraction, as an earlier
    # version did, overflows by roughly 2*ncol*\tabcolsep.
    fracs = TABLE_WIDTHS.get(number)
    if fracs and len(fracs) == ncol:
        spec = ("@{}>{\\raggedright\\arraybackslash}p{\\dimexpr" + f"{fracs[0]}"
                + "\\linewidth-2\\tabcolsep\\relax}" + "".join(
                    ">{\\centering\\arraybackslash}p{\\dimexpr" + f"{w}"
                    + "\\linewidth-2\\tabcolsep\\relax}"
                    for w in fracs[1:]))
    else:
        cw = (rf"\dimexpr(\linewidth/{ncol})-2\tabcolsep\relax")
        spec = "@{}" + "".join(f">{{\\raggedright\\arraybackslash}}p{{{cw}}}"
                               for _ in range(ncol))
    # Six or more columns in IOP's single 12pt column leaves too little per column for
    # footnotesize: the dense matrices (the dimension-coverage grid, the two confusion
    # matrices, the coding-run summary) overflow on their header words alone. Same rule
    # and same reason as build_ieee.py's `size`, at the column count this format needs it.
    size = r"\scriptsize" if ncol >= 6 else r"\footnotesize"
    out = [r"\begin{table}[htbp]", rf"\caption{{\label{{{label}}}{conv(caption)}}}",
           size, rf"\begin{{tabular}}{{{spec}}}", r"\br"]
    out.append(" & ".join(rf"\textbf{{{conv(c)}}}" for c in header) + r" \\")
    out.append(r"\mr")
    for r in body:
        r = (r + [""] * ncol)[:ncol]
        out.append(" & ".join(conv(c) for c in r) + r" \\")
    out += [r"\br", r"\end{tabular}", r"\end{table}", ""]
    return "\n".join(out)



def figure_block(cap: str, path: str, lab: str) -> list[str]:
    """Single-column float. IOP's text block is one column, so this is the only shape."""
    return [
        r"\begin{figure}[htbp]",
        r"\centering",
        rf"\includegraphics[width=\linewidth]{{{Path(path).with_suffix('')}}}",
        rf"\caption{{\label{{{lab}}}{conv(cap)}}}",
        r"\end{figure}", ""]


def caption_from(prose: str, secnum: int, tbl: int) -> str:
    """First sentence of the preceding paragraph, stripped of markdown.

    Never derived from already-generated LaTeX: an earlier version took the previous
    output line, which could be a \\subsection command, and produced a caption containing
    a literal backslash and an unbalanced brace.
    """
    t = re.sub(r"[*`_]", "", prose or "").strip()
    t = re.sub(r"\[[A-Za-z][A-Za-z0-9]*(?:\s*,\s*[A-Za-z][A-Za-z0-9]*)*\]", "", t)
    m = re.match(r"(.{20,180}?[.:])(\s|$)", t)
    cap = (m.group(1) if m else t[:150]).strip()
    if not cap or "\\" in cap:
        cap = f"Section {secnum}, table {tbl}."
    return cap


def convert(md: str, secnum: int, table_renderer=None, figure_renderer=None) -> str:
    """Markdown -> LaTeX.

    `table_renderer(rows, label, caption, number)` and `figure_renderer(cap, path, label)`
    are injection points so a second journal format can reuse this converter instead of
    forking it. Defaults reproduce the IOP output unchanged; `build_ieee.py` supplies
    two-column variants. Keeping one converter is the point: a markdown construct that
    converts correctly for one target and silently mangles for the other is exactly the
    divergence this project reports on.
    """
    table_renderer = table_renderer or table
    figure_renderer = figure_renderer or figure_block
    for pat, rep in SUBSTITUTIONS:
        md = re.sub(pat, rep, md, flags=re.M)

    lines = md.split("\n")
    out: list[str] = []
    i = 0
    tbl = 0
    para: list[str] = []
    bullets: list[str] = []
    last_prose = [""]          # raw markdown, for fallback table captions
    pending_caption = [""]     # caption captured from the "**Table N. ...**" label line
    pending_number = [0]       # its number, for renderers that size tables by it

    def flush_para():
        if para:
            last_prose[0] = " ".join(para)
            out.append(conv(" ".join(para)))
            out.append("")
            para.clear()

    def flush_bullets():
        if bullets:
            out.append(r"\begin{itemize}")
            out.extend(r"\item " + conv(b) for b in bullets)
            out.append(r"\end{itemize}")
            out.append("")
            bullets.clear()

    while i < len(lines):
        ln = lines[i]

        if re.match(r"^#\s+", ln):                      # section
            flush_para(); flush_bullets()
            title = re.sub(r"^#\s+[0-9]+\.\s*", "", ln).strip()
            out += [rf"\section{{{conv(title)}}}", ""]
            i += 1; continue

        if re.match(r"^##\s+", ln):                     # subsection
            flush_para(); flush_bullets()
            title = re.sub(r"^##\s+[0-9]+\.[0-9]+[a-z]?\s*", "", ln).strip()
            out += [rf"\subsection{{{conv(title)}}}", ""]
            i += 1; continue

        if re.match(r"^###\s+", ln):
            flush_para(); flush_bullets()
            title = re.sub(r"^###\s+(?:[0-9]+(?:\.[0-9]+)*\.?\s+)?", "", ln).strip()
            out += [rf"\subsubsection{{{conv(title)}}}", ""]
            i += 1; continue

        # Source files carry human-readable Markdown table labels. LaTeX numbers its own
        # captions, so the label line is not emitted as prose (a duplicate caption can be
        # stranded on the page before a floating table); instead its text, minus the
        # "Table N." prefix, becomes the caption of the table that follows it.
        mlab = re.match(r"^\*\*Table\s+(\d+)\.\s+(.+?)\*\*\s*$", ln.strip(), flags=re.I)
        if mlab:
            flush_para(); flush_bullets()
            pending_number[0] = int(mlab.group(1))
            pending_caption[0] = mlab.group(2).strip()
            i += 1; continue
        if re.match(r"^\*\*Table\s+[^*]+\*\*\s*$", ln.strip(), flags=re.I):
            flush_para(); flush_bullets(); i += 1; continue

        if re.match(r"^!\[", ln.strip()):              # figure
            flush_para(); flush_bullets()
            # Captions are wrapped across lines in the sources for readability, so the
            # block is accumulated until the closing paren. An earlier version matched a
            # single line only and silently emitted the rest as body text, which put raw
            # markdown into the typeset paper.
            blk = ln.strip()
            complete_image = r"\]\([^)]+\)\s*(?:\{#[^}]+\})?\s*$"
            while not re.search(complete_image, blk) and i + 1 < len(lines):
                i += 1
                blk += " " + lines[i].strip()
            m = re.match(r"^!\[(.*?)\]\(([^)]+)\)\s*(?:\{(#[^}]+)\})?\s*$", blk)
            if not m:
                warn(f"unconverted image block: {blk[:60]}")
            if m:
                cap, path = m.group(1), m.group(2)
                lab = (m.group(3) or "#fig:" + Path(path).stem).lstrip("#")
                out.extend(figure_renderer(cap, path, lab))
            i += 1; continue

        if ln.strip().startswith("|"):                  # table
            flush_para(); flush_bullets()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i]); i += 1
            if len(rows) >= 2:
                tbl += 1
                cap = pending_caption[0] or caption_from(last_prose[0], secnum, tbl)
                num = pending_number[0]
                pending_caption[0] = ""
                pending_number[0] = 0
                out.append(table_renderer(rows, f"tab:s{secnum}-{tbl}", cap, num))
            continue

        if re.match(r"^\s*[-*]\s+", ln):                # bullet
            flush_para()
            b = re.sub(r"^\s*[-*]\s+", "", ln)
            i += 1
            while i < len(lines) and re.match(r"^\s{2,}\S", lines[i]) and \
                    not re.match(r"^\s*[-*]\s+", lines[i]):
                b += " " + lines[i].strip(); i += 1
            bullets.append(b); continue

        if re.match(r"^\s*[0-9]+\.\s+", ln):            # numbered list
            flush_para(); flush_bullets()
            items = []
            while i < len(lines):
                m = re.match(r"^\s*[0-9]+\.\s+(.*)", lines[i])
                if not m:
                    if not lines[i].strip():
                        j = i
                        while j < len(lines) and not lines[j].strip():
                            j += 1
                        if j < len(lines) and re.match(r"^\s*[0-9]+\.\s+", lines[j]):
                            i = j
                            continue
                    if items and re.match(r"^\s{2,}\S", lines[i]):
                        items[-1] += " " + lines[i].strip(); i += 1; continue
                    break
                items.append(m.group(1)); i += 1
            out.append(r"\begin{enumerate}")
            out += [r"\item " + conv(x) for x in items]
            out += [r"\end{enumerate}", ""]
            continue

        if ln.strip().startswith(">"):                  # blockquote -> framed remark
            flush_para(); flush_bullets()
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
            body = " ".join(x for x in q if x.strip())
            out += [r"\begin{quote}", conv(body), r"\end{quote}", ""]
            continue

        if ln.strip() in ("---", "***"):
            flush_para(); flush_bullets(); i += 1; continue

        if not ln.strip():
            flush_para(); flush_bullets(); i += 1; continue

        para.append(ln.strip()); i += 1

    flush_para(); flush_bullets()
    return "\n".join(out)


def abstract_from_frontmatter() -> str:
    """The abstract, read from paper/paper1-frontmatter.md rather than repeated here.

    Until 2026-09-05 the abstract existed twice: once in the markdown source that
    `assemble_paper1.py` ships and once verbatim inside this file's preamble. Two copies of
    the paper's most-read paragraph is precisely the drift risk this project reports on, so
    the LaTeX build now derives it. Conversion is the same escaper the body uses.
    """
    text = (PAPER / "paper1-frontmatter.md").read_text(encoding="utf-8")
    m = re.search(r"^##\s+Abstract\s*$(.*?)(?=^#|\Z)", text, flags=re.M | re.S)
    if not m:
        raise SystemExit("build_latex: no '## Abstract' section in paper1-frontmatter.md")
    body = " ".join(line.strip() for line in m.group(1).strip().splitlines() if line.strip())
    if len(body.split()) < 80:
        raise SystemExit("build_latex: abstract looks truncated; refusing to build")
    return conv(body)


# ------------------------------------------------------------------ preamble

PREAMBLE = r"""%% Neuromorphic Computing and Engineering (IOP Publishing)
%% Article type: Paper
%%
%% Build:  pdflatex PAPER1 && bibtex PAPER1 && pdflatex PAPER1 && pdflatex PAPER1
%% Requires iopart.cls and iopart-num.bst from IOP's LaTeX template package.
%%
%% GENERATED FILE. Source of truth is paper/*.md; regenerate with
%%   python3 scripts/build_latex.py
%% Edits made here are lost on the next build.

%% ===========================================================================
%% DOCUMENT CLASS -- two modes.
%%
%% [PREPRINT] is the default and compiles anywhere, including Overleaf.
%% [IOP] is the submission format. iopart.cls is distributed by IOP Publishing
%% directly; it is NOT on CTAN and NOT in TeX Live, so it is not available on
%% Overleaf until you upload it yourself.
%%
%% TO SWITCH: download iopart.cls, iopart12.clo, iopams.sty and iopart-num.bst
%% from IOP's author-support pages, put them beside this file, then comment the
%% two [PREPRINT] lines and uncomment the two [IOP] lines. Also switch the
%% bibliography style at the end of this file.
%% ===========================================================================

\documentclass[12pt,a4paper]{article}   %% [PREPRINT]
\usepackage{iopart-shim}                %% [PREPRINT]

%\documentclass[12pt]{iopart}           %% [IOP]
%\usepackage{iopams}                    %% [IOP]

\usepackage{array}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{url}
\usepackage[utf8]{inputenc}

\begin{document}

\title[Reservoir-computing classification schemes reviewed]{A Review of Reservoir Computing Classification Schemes and an Architecture-Based Framework for Evaluating Reported Systems}

\author{Stefan Trajanovski, Ema Pandilova, Marko Petrov, Ivan Kitanovski,\\
Ivan Chorbev, Ivica Dimitrovski, Dimitar Trajanov and Ilinka Ivanoska}

\address{Faculty of Computer Science and Engineering, University Ss.~Cyril and Methodius,
Rudzer Boshkovikj 16, P.O.~393, Skopje 1000, North Macedonia}

\ead{stefan.trajanovski@students.finki.ukim.mk}

\submitto{\textit{Neuromorphic Computing and Engineering}}

\begin{abstract}
__ABSTRACT__
\end{abstract}

\noindent{\it Keywords}: reservoir computing, physical computing, taxonomy, benchmarking,
reproducibility, prospective protocol, neuromorphic computing

\maketitle

"""

# The three end-matter statements come from assemble_paper1.py so that the markdown and
# the two LaTeX builds cannot disagree about them; see the note there. Only the sectioning
# commands are format-specific. `conv()` escapes the plain text, which turns the straight
# quotes in the funding text into proper TeX quotes and the URL into \url{}.
POSTAMBLE_TEMPLATE = r"""
\ack

__ACKNOWLEDGEMENTS__


\section*{Data availability statement}

__DATA_AVAILABILITY__

\section*{Conflict of interest statement}

__CONFLICT_OF_INTEREST__

%\section*{References}          %% [IOP] uncomment; article adds its own heading
\bibliographystyle{unsrt}       %% [PREPRINT]
%\bibliographystyle{iopart-num} %% [IOP]
\bibliography{references-submission}

\end{document}
"""


def postamble() -> str:
    """The end matter, converted from the shared plain-text source."""
    return (POSTAMBLE_TEMPLATE
            .replace("__ACKNOWLEDGEMENTS__", conv(ACKNOWLEDGEMENTS))
            .replace("__DATA_AVAILABILITY__",
                     conv(DATA_AVAILABILITY).replace(
                         conv(REPOSITORY_URL), r"\url{" + REPOSITORY_URL + "}"))
            .replace("__CONFLICT_OF_INTEREST__", conv(CONFLICT_OF_INTEREST)))




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
    args = ap.parse_args()

    missing = [s for s in SECTIONS if not (PAPER / s).exists()]
    if missing:
        print("missing sections: " + ", ".join(missing), file=sys.stderr)
        return 1

    body = []
    for n, name in enumerate(SECTIONS, 1):
        md = (PAPER / name).read_text(encoding="utf-8")
        body.append(convert(md, n))
        print(f"  {name:32s} -> section {n}")

    tex = PREAMBLE.replace("__ABSTRACT__", abstract_from_frontmatter()) \
        + "\n".join(body) + postamble()

    # Sanity checks on the generated file.
    if tex.count(r"\begin{table}") != tex.count(r"\end{table}"):
        warn("unbalanced table environments")
    if tex.count(r"\begin{itemize}") != tex.count(r"\end{itemize}"):
        warn("unbalanced itemize environments")
    for leftover in re.finditer(r"(?<!\\)\[([A-Z][A-Za-z0-9]*)\](?!\()", tex):
        if leftover.group(1) not in ("AUTHOR", "TO", "AFFILIATIONS", "IOP", "PREPRINT",
                                     "CORRESPONDING"):
            warn(f"possible unconverted citation: [{leftover.group(1)}]")

    if WARNINGS:
        print(f"\n{len(WARNINGS)} warning(s):")
        for w in WARNINGS[:25]:
            print(f"  ! {w}")
    else:
        print("\nno conversion warnings")

    if args.check:
        return 1 if WARNINGS else 0

    source_bib = PAPER / "references.bib"
    submission_bib = PAPER / "references-submission.bib"
    submission_bib.write_text(
        submission_bibliography(source_bib.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    args.out.write_text(strip_comments(tex), encoding="utf-8")
    print(f"\n{len(tex.split())} words -> {args.out}")
    print(f"  \\cite commands: {tex.count(chr(92) + 'cite{')}")
    print(f"  tables:         {tex.count(chr(92) + 'begin{table}')}")
    print(f"  sections:       {tex.count(chr(92) + 'section{')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
