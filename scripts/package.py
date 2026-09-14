#!/usr/bin/env python3
"""Build the Overleaf submission packages from the generated LaTeX.

    python3 scripts/package.py              # both full packages
    python3 scripts/package.py ieee         # IEEE Access only
    python3 scripts/package.py iop          # IOP / NCE only
    python3 scripts/package.py updates      # the two drop-in update packs
    python3 scripts/package.py --check      # verify the zips match the working tree

A FULL package builds an Overleaf project from nothing. An UPDATE pack refreshes one
that already exists: it carries the document, the bibliography, the README and the
figure library, and leaves the class files, the fonts and the author photographs
alone, because no edit to the manuscript can change those. 125 kB against 2.1 MB.
Drop it at the project root and let it overwrite; the paths line up.

WHY THIS IS A SCRIPT
Both zips were assembled by hand until 2026-09-09, and the cost of that showed up
exactly where an unrepeatable step always shows up: `paper/PAPER1-IEEE.pdf` and its
log were left on disk from a superseded `--preprint` generation, 46 minutes older
than the `.tex` beside them and built against a different document class. A reader
opening the PDF named after the submission was not looking at the submission.

So the rule this file enforces is: the package is a function of the working tree,
every member is listed here by name, and a missing member is an error rather than a
quietly smaller zip. `--check` re-derives the manifest and compares it against the
zip on disk, which is the cheap way to notice that a rebuild was skipped.

The zips carry no PDF. The submission PDF is produced by Overleaf from the package,
and shipping a locally-built one invites the reader to trust whichever is newer.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

PAPER = Path("paper")
CLASS = PAPER / "ieee-class"

# Everything each package contains, as (path on disk, name inside the zip).
# Fonts and class files are listed by directory scan because IEEE ships several dozen
# and enumerating them here would rot; everything else is named.


def figures() -> list[tuple[Path, str]]:
    """Every figure the manuscript actually includes, plus the rest of the library.

    The full library ships because the IOP and IEEE builds have historically differed
    in which figures they float, and a package missing a referenced figure fails to
    compile on Overleaf with an error that names a file the author cannot see.
    """
    pdfs = sorted((PAPER / "figures").glob("*.pdf"))
    if not pdfs:
        raise SystemExit("package: paper/figures/*.pdf not found; run svg2pdf.py first")
    return [(p, f"figures/{p.name}") for p in pdfs]


def photos() -> list[tuple[Path, str]]:
    jpgs = sorted((PAPER / "photos").glob("*.jpg"))
    if len(jpgs) != 8:
        raise SystemExit(f"package: expected 8 author photographs, found {len(jpgs)}")
    return [(p, f"photos/{p.name}") for p in jpgs]


def ieee_manifest() -> list[tuple[Path, str]]:
    items: list[tuple[Path, str]] = [
        (PAPER / "PAPER1-IEEE.tex", "PAPER1-IEEE.tex"),
        (PAPER / "references-submission.bib", "references-submission.bib"),
        (PAPER / "IEEE-README.txt", "IEEE-README.txt"),
    ]
    # The IEEE Access class, its bibliography style, its logos and its fonts. These are
    # IEEE's own template files and are shipped so the package compiles in an empty
    # Overleaf project; ieeeaccess.cls is not on CTAN and not in TeX Live.
    for p in sorted(CLASS.iterdir()):
        if p.is_file() and not p.name.startswith("."):
            items.append((p, p.name))
    items += figures() + photos()
    return items


def iop_manifest() -> list[tuple[Path, str]]:
    return [
        (PAPER / "PAPER1.tex", "PAPER1.tex"),
        (PAPER / "iopart-shim.sty", "iopart-shim.sty"),
        (PAPER / "references-submission.bib", "references-submission.bib"),
        (PAPER / "OVERLEAF-README.txt", "OVERLEAF-README.txt"),
    ] + figures()


# The subset that changes when the manuscript changes. Everything NOT here is a static
# template asset -- IEEE's class, its bibliography style, its fonts and logos, and the eight
# author photographs -- which together are 2.0 MB of the 2.1 MB package and which no edit to
# the paper can touch.
#
# WHY THIS EXISTS: re-uploading the full package to a live Overleaf project to change one
# .tex is slow and, worse, it replaces files nobody meant to replace. This pack carries the
# document and the whole figure library and nothing else, so dropping it into an existing
# project overwrites exactly what an edit can have changed. The figure library ships whole
# rather than diffed because it is 71 kB and because a stale figure is the failure mode this
# repository has already had twice; guessing which three PDFs moved is how you keep the
# fourth.
def ieee_update_manifest() -> list[tuple[Path, str]]:
    return [
        (PAPER / "PAPER1-IEEE.tex", "PAPER1-IEEE.tex"),
        (PAPER / "references-submission.bib", "references-submission.bib"),
        (PAPER / "IEEE-README.txt", "IEEE-README.txt"),
    ] + figures()


def iop_update_manifest() -> list[tuple[Path, str]]:
    return [
        (PAPER / "PAPER1.tex", "PAPER1.tex"),
        (PAPER / "references-submission.bib", "references-submission.bib"),
        (PAPER / "OVERLEAF-README.txt", "OVERLEAF-README.txt"),
    ] + figures()


def ieee_short_manifest() -> list[tuple[Path, str]]:
    """The ~20-page variant plus its supplement, as one Overleaf project.

    Carries the class files and photographs, because this is a project you start from
    nothing rather than an update to one that exists.
    """
    items: list[tuple[Path, str]] = [
        (PAPER / "PAPER1-IEEE-short.tex", "PAPER1-IEEE-short.tex"),
        (PAPER / "PAPER1-IEEE-supplement.tex", "PAPER1-IEEE-supplement.tex"),
        (PAPER / "references-submission.bib", "references-submission.bib"),
        (PAPER / "ieeeaccess-shim.sty", "ieeeaccess-shim.sty"),
    ]
    for p in sorted(CLASS.iterdir()):
        if p.is_file() and not p.name.startswith("."):
            items.append((p, p.name))
    return items + figures() + photos()


PACKAGES = {
    "ieee-short": (PAPER / "PAPER1-IEEE-short-overleaf.zip", ieee_short_manifest),
    "ieee": (PAPER / "PAPER1-IEEE-overleaf.zip", ieee_manifest),
    "iop": (PAPER / "PAPER1-overleaf.zip", iop_manifest),
    "ieee-update": (PAPER / "PAPER1-IEEE-overleaf-UPDATE.zip", ieee_update_manifest),
    "iop-update": (PAPER / "PAPER1-overleaf-UPDATE.zip", iop_update_manifest),
}
FULL = ("ieee", "iop")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def build(which: str) -> int:
    out, manifest = PACKAGES[which]
    items = manifest()
    missing = [str(src) for src, _ in items if not src.exists()]
    if missing:
        print(f"package: missing {len(missing)} file(s):", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        return 1
    # Deterministic order and fixed timestamps, so a rebuild with no source change
    # produces an identical archive and `git status` stays honest about what moved.
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, name in sorted(items, key=lambda it: it[1]):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, src.read_bytes())
    size = out.stat().st_size
    print(f"  {out}  {len(items)} files, {size:,} bytes, sha256:{digest(out.read_bytes())}")
    return 0


def check(which: str) -> int:
    out, manifest = PACKAGES[which]
    if not out.exists():
        print(f"  MISSING: {out}", file=sys.stderr)
        return 1
    items = {name: src for src, name in manifest()}
    with zipfile.ZipFile(out) as z:
        inside = set(z.namelist())
        problems = [f"in the tree, absent from the zip: {n}" for n in sorted(set(items) - inside)]
        problems += [f"in the zip, absent from the tree: {n}" for n in sorted(inside - set(items))]
        for name in sorted(set(items) & inside):
            if z.read(name) != items[name].read_bytes():
                problems.append(f"stale in the zip: {name}")
    if problems:
        print(f"  {out}: {len(problems)} problem(s)", file=sys.stderr)
        for p in problems[:12]:
            print(f"    ! {p}", file=sys.stderr)
        if len(problems) > 12:
            print(f"    ... and {len(problems) - 12} more", file=sys.stderr)
        return 1
    print(f"  {out}: current ({len(items)} files)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="?",
                    choices=["ieee", "iop", "both", "ieee-short",
                             "ieee-update", "iop-update", "updates"],
                    default="both",
                    help="'both' builds the two full packages; the '-update' targets build "
                         "the document-and-figures subset for dropping into a live Overleaf "
                         "project without re-uploading the class files, fonts and photographs")
    ap.add_argument("--check", action="store_true",
                    help="verify the zips match the working tree; write nothing")
    args = ap.parse_args()
    targets = ({"both": list(FULL),
                "updates": ["ieee-update", "iop-update"]}
               .get(args.which, [args.which]))
    fn = check if args.check else build
    rc = 0
    for t in targets:
        rc |= fn(t)
    if args.check and rc:
        print("\nRebuild with: python3 scripts/package.py", file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
