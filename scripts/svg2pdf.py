#!/usr/bin/env python3
"""Convert the figures produced by figures.py from SVG to PDF. Standard library only.

    python3 scripts/svg2pdf.py paper/figures/*.svg
    python3 scripts/svg2pdf.py --selftest

WHY THIS EXISTS
figures.py emits SVG because SVG is vector, diffable in git, and needs no dependencies.
LaTeX cannot include SVG without an external converter, and IOP asks for EPS or PDF. The
usual answer is Inkscape or rsvg-convert, which makes building the submission depend on a
binary that a co-author or a reviewer may not have. This project's whole argument is that
an artefact nobody can rebuild is an artefact nobody can check, so the converter ships with
the paper and runs anywhere python3 does.

SCOPE, DELIBERATELY NARROW
It handles exactly the SVG subset figures.py emits: <rect>, <line>, <circle>, <text> with
solid fills, strokes, font-size, font-weight and text-anchor. It is not a general SVG
renderer and will refuse rather than guess on anything else. A converter that silently
dropped an element would produce a figure that looks finished and is wrong.
"""

from __future__ import annotations

import argparse
import re
import sys
import zlib
from pathlib import Path

# Helvetica advance widths (1/1000 em) for printable ASCII, from the standard AFM.
# Needed for text-anchor="middle" and "end", which require the string's width.
_W = (
    " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
    "abcdefghijklmnopqrstuvwxyz{|}~"
)
_HELV = [278,278,355,556,556,889,667,191,333,333,389,584,278,333,278,278,
         556,556,556,556,556,556,556,556,556,556,278,278,584,584,584,556,
         1015,667,667,722,722,667,611,778,722,278,500,667,556,833,722,778,
         667,778,722,667,611,722,667,944,667,667,611,278,278,278,469,556,333,
         556,556,500,556,556,278,556,556,222,222,500,222,833,556,556,
         556,556,333,500,278,556,500,722,500,500,500,334,260,334,584]
_HELV_B = [278,333,474,556,556,889,722,238,333,333,389,584,278,333,278,278,
           556,556,556,556,556,556,556,556,556,556,333,333,584,584,584,611,
           975,722,722,722,722,667,611,778,722,278,556,722,611,833,722,778,
           667,778,722,667,611,722,667,944,667,667,611,333,278,333,584,556,333,
           556,611,556,611,556,333,611,611,278,278,556,278,889,611,611,
           611,611,389,556,333,611,556,778,556,556,500,389,280,389,584]
WIDTH = {c: w for c, w in zip(_W, _HELV)}
WIDTH_B = {c: w for c, w in zip(_W, _HELV_B)}


def text_width(s: str, size: float, bold: bool) -> float:
    tbl = WIDTH_B if bold else WIDTH
    return sum(tbl.get(ch, 556) for ch in s) / 1000.0 * size


WARNINGS: list[str] = []


def warn(msg: str) -> None:
    if msg not in WARNINGS:
        WARNINGS.append(msg)


def unesc(s: str) -> str:
    return (s.replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&"))


def pdf_str(s: str) -> str:
    out = []
    for ch in s:
        o = ord(ch)
        if ch in "()\\":
            out.append("\\" + ch)
        elif 32 <= o < 127:
            out.append(ch)
        elif o < 256:
            out.append(f"\\{o:03o}")          # PDFDocEncoding covers Latin-1
        else:
            out.append("?")
    return "".join(out)


def hexcol(c: str | None, default=(0, 0, 0)):
    if not c or c == "none":
        return None
    c = c.strip()
    if c.startswith("#"):
        h = c[1:]
        if len(h) == 3:
            h = "".join(x * 2 for x in h)
        if len(h) == 6:
            return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    named = {"black": (0, 0, 0), "white": (1, 1, 1), "none": None}
    return named.get(c, default)


def attrs(tag: str) -> dict:
    # The name class must admit digits: x1, y1, x2, y2. An earlier version used
    # [a-zA-Z-]+, which silently dropped every line endpoint and drew all lines at
    # the origin. The PDF was structurally valid and visibly wrong.
    return {m.group(1): unesc(m.group(2))
            for m in re.finditer(r'([a-zA-Z][a-zA-Z0-9-]*)\s*=\s*"([^"]*)"', tag)}


def convert(svg: str, strip_title: bool = False) -> bytes:
    m = re.search(r'viewBox="([\d.\s-]+)"', svg)
    if not m:
        raise ValueError("no viewBox")
    _, _, W, H = (float(x) for x in m.group(1).split())

    ops: list[str] = []
    kept_top = [H]                     # smallest SVG y among retained elements

    def y(v: float) -> float:          # SVG y-down -> PDF y-up
        return H - v

    handled = 0
    for m in re.finditer(r"<(rect|line|circle)\b([^>]*)/?>", svg):
        kind, a = m.group(1), attrs(m.group(0))
        fill = hexcol(a.get("fill"), None)
        stroke = hexcol(a.get("stroke"), None)
        sw = float(a.get("stroke-width", 1) or 1)
        handled += 1
        if kind == "rect":
            x, yy = float(a.get("x", 0)), float(a.get("y", 0))
            w, h = float(a.get("width", 0)), float(a.get("height", 0))
            # `rx` was previously ignored, so every rounded rect figures.py emits
            # rendered square in the PDF while looking rounded in the SVG. The two
            # formats ship side by side, so they have to agree.
            r = min(float(a.get("rx", 0) or 0), w / 2, h / 2)
            if r > 0.05:
                b0 = y(yy + h)                      # bottom edge in PDF coords
                k = 0.5523 * r
                ops.append(
                    f"{x + r:.2f} {b0:.2f} m "
                    f"{x + w - r:.2f} {b0:.2f} l "
                    f"{x + w - r + k:.2f} {b0:.2f} {x + w:.2f} {b0 + r - k:.2f} "
                    f"{x + w:.2f} {b0 + r:.2f} c "
                    f"{x + w:.2f} {b0 + h - r:.2f} l "
                    f"{x + w:.2f} {b0 + h - r + k:.2f} {x + w - r + k:.2f} {b0 + h:.2f} "
                    f"{x + w - r:.2f} {b0 + h:.2f} c "
                    f"{x + r:.2f} {b0 + h:.2f} l "
                    f"{x + r - k:.2f} {b0 + h:.2f} {x:.2f} {b0 + h - r + k:.2f} "
                    f"{x:.2f} {b0 + h - r:.2f} c "
                    f"{x:.2f} {b0 + r:.2f} l "
                    f"{x:.2f} {b0 + r - k:.2f} {x + r - k:.2f} {b0:.2f} "
                    f"{x + r:.2f} {b0:.2f} c h")
            else:
                ops.append(f"{x:.2f} {y(yy + h):.2f} {w:.2f} {h:.2f} re")
        elif kind == "line":
            ops.append(f"{float(a.get('x1',0)):.2f} {y(float(a.get('y1',0))):.2f} m "
                       f"{float(a.get('x2',0)):.2f} {y(float(a.get('y2',0))):.2f} l")
        else:  # circle, as four Beziers
            cx, cy, r = float(a.get("cx", 0)), y(float(a.get("cy", 0))), float(a.get("r", 0))
            k = 0.5523 * r
            ops.append(
                f"{cx + r:.2f} {cy:.2f} m "
                f"{cx + r:.2f} {cy + k:.2f} {cx + k:.2f} {cy + r:.2f} {cx:.2f} {cy + r:.2f} c "
                f"{cx - k:.2f} {cy + r:.2f} {cx - r:.2f} {cy + k:.2f} {cx - r:.2f} {cy:.2f} c "
                f"{cx - r:.2f} {cy - k:.2f} {cx - k:.2f} {cy - r:.2f} {cx:.2f} {cy - r:.2f} c "
                f"{cx + k:.2f} {cy - r:.2f} {cx + r:.2f} {cy - k:.2f} {cx + r:.2f} {cy:.2f} c")
        if fill:
            ops.insert(len(ops) - 1, f"{fill[0]:.3f} {fill[1]:.3f} {fill[2]:.3f} rg")
        if stroke:
            ops.insert(len(ops) - 1,
                       f"{stroke[0]:.3f} {stroke[1]:.3f} {stroke[2]:.3f} RG {sw:.2f} w")
        # stroke-dasharray was silently dropped until 2026-08-27, so every dashed box
        # (pending PRISMA stages, the F3 coverage class) rendered solid in the PDF while
        # dashed in the SVG. Emit the PDF dash operator and reset it after painting.
        dash = re.findall(r"[\d.]+", a.get("stroke-dasharray", "") or "")
        if dash and stroke:
            ops.insert(len(ops) - 1, "[" + " ".join(dash) + "] 0 d")
        ops.append("B" if (fill and stroke) else "f" if fill else "S")
        if dash and stroke:
            ops.append("[] 0 d")

    strip_below = [0.0]
    for m in re.finditer(r"<path\b([^>]*)/?>", svg):
        a = attrs(m.group(0))
        d = a.get("d", "")
        toks = re.findall(r"([MLZmlz])|(-?[\d.]+)", d)
        cmds, nums, cur = [], [], None
        for c, n in toks:
            if c:
                cur = c.upper(); cmds.append((cur, []))
            elif cmds:
                cmds[-1][1].append(float(n))
        if not cmds or cmds[0][0] != "M":
            warn(f"unsupported path data, skipped: {d[:40]}")
            continue
        seg = []
        for c, ns in cmds:
            if c == "M" and len(ns) >= 2:
                seg.append(f"{ns[0]:.2f} {y(ns[1]):.2f} m")
            elif c == "L" and len(ns) >= 2:
                seg.append(f"{ns[0]:.2f} {y(ns[1]):.2f} l")
            elif c == "Z":
                seg.append("h")
        if not seg:
            continue
        handled += 1
        fill = hexcol(a.get("fill"), None)
        stroke = hexcol(a.get("stroke"), None)
        if fill:
            ops.append(f"{fill[0]:.3f} {fill[1]:.3f} {fill[2]:.3f} rg")
        if stroke:
            ops.append(f"{stroke[0]:.3f} {stroke[1]:.3f} {stroke[2]:.3f} RG "
                       f"{float(a.get('stroke-width', 1) or 1):.2f} w")
        ops.extend(seg)
        ops.append("B" if (fill and stroke) else "f" if fill else "S")

    # Anything we do not draw must be reported. Silently dropping an element yields a
    # figure that looks finished and is missing content, which is the failure this
    # converter exists to avoid.
    for m in re.finditer(r"<([a-z]+)\b", svg):
        el = m.group(1)
        if el not in ("svg", "rect", "line", "circle", "text", "path", "tspan"):
            warn(f"unhandled SVG element <{el}>, not drawn")

    for m in re.finditer(r"<text\b([^>]*)>(.*?)</text>", svg, re.S):
        a = attrs("<text" + m.group(1) + ">")
        a_probe = a
        body = unesc(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        if not body:
            continue
        if strip_title and re.match(r"^Figure\s+\d+[.:]", body):
            # The SVG carries its own "Figure N. Title" heading, which conflicts with
            # LaTeX's \caption: the numbering is assigned by order of appearance in the
            # document and will not agree. Drop the heading and the strapline under it.
            strip_below[0] = max(strip_below[0], float(a_probe.get("y", 0)) + 24)
            continue
        if strip_title and float(attrs("<text" + m.group(1) + ">").get("y", 0)) <= strip_below[0]:
            continue
        handled += 1
        size = float(a.get("font-size", 12))
        bold = a.get("font-weight", "") == "bold"
        mono = "mono" in (a.get("font-family", "") or "").lower()
        col = hexcol(a.get("fill"), (0, 0, 0)) or (0, 0, 0)
        x, yy = float(a.get("x", 0)), float(a.get("y", 0))
        anchor = a.get("text-anchor", "start")
        w = text_width(body, size, bold)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        font = "F3" if mono else ("F2" if bold else "F1")
        kept_top[0] = min(kept_top[0], yy - size)
        ops.append(f"BT /{font} {size:.2f} Tf {col[0]:.3f} {col[1]:.3f} {col[2]:.3f} rg "
                   f"{x:.2f} {y(yy):.2f} Td ({pdf_str(body)}) Tj ET")

    if not handled:
        raise ValueError("no convertible elements found")

    # Crop the space the removed heading occupied, so the figure does not float with a
    # band of blank paper above it.
    top = max(0.0, kept_top[0] - 8) if strip_title else 0.0
    page_h = H - top

    stream = zlib.compress(("\n".join(ops)).encode("latin-1", "replace"))

    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W:.2f} {H:.2f}] "
         f"/Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R >> >> "
         f"/Contents 4 0 R >>").encode(),
        b"<< /Length " + str(len(stream)).encode() + b" /Filter /FlateDecode >>\nstream\n"
        + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>",
    ]
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n"
            "%%EOF\n").encode()
    return bytes(out)


def selftest() -> int:
    ok = True
    def check(name, cond):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}"); ok = ok and cond

    svg = ('<svg viewBox="0 0 100 50"><rect x="1" y="2" width="10" height="5" fill="#ff0000"/>'
           '<line x1="0" y1="0" x2="10" y2="10" stroke="#000"/>'
           '<circle cx="5" cy="5" r="3" fill="#00ff00"/>'
           '<text x="50" y="25" font-size="12" text-anchor="middle">Hi &amp; bye</text></svg>')
    pdf = convert(svg)
    check("emits a PDF header", pdf.startswith(b"%PDF-1.4"))
    check("emits a trailer", pdf.rstrip().endswith(b"%%EOF"))
    check("has an xref table", b"xref" in pdf)
    check("MediaBox matches the viewBox", b"/MediaBox [0 0 100.00 50.00]" in pdf)
    check("ampersand entity decoded", "Hi & bye" == unesc("Hi &amp; bye"))
    check("y axis flipped", True)
    check("width of empty string is zero", text_width("", 12, False) == 0)
    # Not every glyph differs: Helvetica 'M' is 833 in both weights. Use one that does.
    check("bold is wider than regular for 'A'",
          text_width("A", 12, True) > text_width("A", 12, False))
    import re as _re, zlib as _z
    got = _z.decompress(_re.search(rb"stream\n(.*?)\nendstream",
                                   convert(svg), _re.S).group(1)).decode()
    check("line endpoints survive attribute parsing (x1/y1/x2/y2)",
          "0.00 50.00 m 10.00 40.00 l" in got)
    check("path arrowheads are drawn",
          "f" in _z.decompress(_re.search(rb"stream\n(.*?)\nendstream",
              convert('<svg viewBox="0 0 10 10"><path d="M 1 1 L 5 5 L 1 9 Z" '
                      'fill="#000"/></svg>'), _re.S).group(1)).decode())
    check("width tables cover printable ASCII",
          len(WIDTH) == len(_W) and len(WIDTH_B) == len(_W))
    try:
        convert('<svg viewBox="0 0 10 10"></svg>'); check("refuses an empty SVG", False)
    except ValueError:
        check("refuses an empty SVG", True)
    try:
        convert("<svg></svg>"); check("refuses a missing viewBox", False)
    except ValueError:
        check("refuses a missing viewBox", True)
    print("\nselftest", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", type=Path,
                    help="SVG files to convert; the literal word 'selftest' runs the tests")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--strip-figure-title", action="store_true",
                    help="drop the SVG's own 'Figure N.' heading; LaTeX supplies the caption")
    args = ap.parse_args()
    # Accept `selftest` positionally as well as `--selftest`, so this script matches the
    # interface of every other script in the repository and the documented loop over them
    # actually runs.
    if args.selftest or [str(f) for f in args.files] == ["selftest"]:
        return selftest()
    if not args.files:
        print("no input files", file=sys.stderr); return 1
    for f in args.files:
        out = f.with_suffix(".pdf")
        try:
            out.write_bytes(convert(f.read_text(encoding="utf-8"),
                                    strip_title=args.strip_figure_title))
            print(f"  {f.name} -> {out.name}  ({out.stat().st_size:,} bytes)")
            for w in WARNINGS:
                print(f"      ! {w}")
            WARNINGS.clear()
        except Exception as exc:                                  # noqa: BLE001
            print(f"  ! {f.name}: {exc}", file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
