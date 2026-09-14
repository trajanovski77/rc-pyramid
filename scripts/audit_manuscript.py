#!/usr/bin/env python3
"""Check manuscript citations, numbering, captions, and style constraints."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PAPER = Path("paper")
SOURCES = [
    "paper1-frontmatter.md", "p1-s1-introduction.md", "s2-foundations.md",
    "s3-pyramid.md", "s4-facets.md", "s5-benchmarks.md", "s6-methodology.md",
    "s7-corpus-construction.md", "s8-results.md", "s9-discussion-limitations.md",
    "s10-conclusion.md",
]
BODY = SOURCES[1:]
MAX_FIGURE_CAPTION_WORDS = 12
MAX_TABLE_CAPTION_WORDS = 12
DISALLOWED = {
    "paper 2": "dependency on a second paper",
    "RC-PYRAMID": "retired branded component name",
    "RC-FACET": "retired branded component name",
    "RC-LADDER": "retired branded component name",
    "RC-BOUND": "retired branded component name",
    "RC-REPORT": "retired branded component name",
    "[MEASURE]": "unresolved prospective placeholder",
    "audited never": "absolute literature claim",
    "an instrument that cannot fail": "rhetorical slogan",
    "These two problems are the same problem": "rhetorical slogan",
}


def bib_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for block in re.split(r"(?=^@)", text, flags=re.M):
        match = re.match(r"@\w+\{([^,]+),", block)
        if match:
            blocks[match.group(1)] = block
    return blocks


def main() -> int:
    problems: list[str] = []
    texts = {name: (PAPER / name).read_text(encoding="utf-8") for name in SOURCES}
    combined = "\n".join(texts[name] for name in BODY)

    bib = bib_blocks((PAPER / "references.bib").read_text(encoding="utf-8"))
    citations = {
        key.strip()
        for group in re.findall(
            r"\[([A-Za-z][A-Za-z0-9_-]*(?:\s*,\s*[A-Za-z][A-Za-z0-9_-]*)*)\]",
            combined,
        )
        for key in group.split(",")
    }
    for key in sorted(citations - set(bib)):
        problems.append(f"missing bibliography entry: {key}")
    for key in sorted(citations & set(bib)):
        if not re.search(r"\bnote\s*=", bib[key], flags=re.I):
            problems.append(f"cited entry lacks provenance note: {key}")

    figures = []
    tables = []
    for name, text in texts.items():
        for line_no, line in enumerate(text.splitlines(), 1):
            image = re.match(r"^!\[(.*?)\]\(", line)
            if image:
                figures.append((name, line_no, image.group(1)))
            table = re.match(r"^\*\*Table\s+(\d+)\.\s+(.*?)\*\*$", line)
            if table:
                tables.append((name, line_no, int(table.group(1)), table.group(2)))
            if re.match(r"^\*\*[^*]+[.:]\*\*", line) and not line.startswith("**Table"):
                problems.append(f"{name}:{line_no}: paragraph-level mini-heading")

    if [n for _, _, n, _ in tables] != list(range(1, len(tables) + 1)):
        problems.append("table captions are not sequentially numbered")
    for name, line_no, caption in figures:
        if len(caption.split()) > MAX_FIGURE_CAPTION_WORDS:
            problems.append(f"{name}:{line_no}: figure caption exceeds {MAX_FIGURE_CAPTION_WORDS} words")
    for name, line_no, _, caption in tables:
        if len(caption.split()) > MAX_TABLE_CAPTION_WORDS:
            problems.append(f"{name}:{line_no}: table caption exceeds {MAX_TABLE_CAPTION_WORDS} words")

    referenced_figures = {int(x) for x in re.findall(r"Figure\s+(\d+)", combined)}
    referenced_tables = {int(x) for x in re.findall(r"Table\s+(\d+)", combined)}
    expected_figures = set(range(1, len(figures) + 1))
    expected_tables = set(range(1, len(tables) + 1))
    if referenced_figures != expected_figures:
        problems.append(f"figure references {sorted(referenced_figures)} != {sorted(expected_figures)}")
    if referenced_tables != expected_tables:
        problems.append(f"table references {sorted(referenced_tables)} != {sorted(expected_tables)}")

    lowered = combined.lower()
    for phrase, reason in DISALLOWED.items():
        if phrase.lower() in lowered:
            problems.append(f"{reason}: {phrase}")

    headings = re.findall(r"^#\s+(\d+)\.\s+(.+)$", combined, flags=re.M)
    if [int(n) for n, _ in headings] != list(range(1, 11)):
        problems.append("main sections are not numbered 1 through 10")

    words = len("\n".join(texts.values()).split())
    print(f"manuscript words: {words:,}")
    print(f"main sections: {len(headings)}")
    print(f"figures: {len(figures)}")
    print(f"tables: {len(tables)}")
    print(f"unique cited sources: {len(citations)} / {len(bib)} bibliography entries")
    if problems:
        print("\nFAILED")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("\nPASS: citations, provenance notes, numbering, captions, and style constraints")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
