#!/usr/bin/env python3
"""Figure generation for the RC audit paper.

Figures 1-3 are data-free (they draw the taxonomy itself) and render now.
Figures 5-12 consume data/extraction/*.csv and refuse to render until it exists.

    python3 scripts/figures.py all      --out paper/figures
    python3 scripts/figures.py fig1     --out paper/figures
    python3 scripts/figures.py selftest

Output is SVG, which is vector, diffable in git, and convertible to PDF/EPS at
submission without resampling. No external dependencies: the SVG is emitted
directly, so this runs anywhere python3 does.

A data-dependent figure that renders with no data would produce an empty plot
that looks like a finding. Figures 5-12 therefore raise rather than emit.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- style

FONT = "Helvetica, Arial, sans-serif"
MONO = "SFMono-Regular, Menlo, monospace"
INK = "#1f2933"
MUTED = "#52606d"
RULE = "#9aa5b1"
FAMILY_INK = {"F1": "#244a73", "F2": "#426b8f", "F3": "#607f99", "F4": "#385c63"}

# Saturated accents plus generous light fills keep the diagrams lively at page
# size without sacrificing black-and-white legibility. The mapping also upgrades
# legacy colour literals, so all manuscript figures share one palette.
COLOR_MAP = {
    "#8a4b2a": "#6f4e37", "#2f5d7c": "#426b8f",
    "#4f6b2f": "#4f6b58", "#6b4a7c": "#5f5b73",
    "#7a6840": "#71643f", "#8a3b2a": "#7a4a42",
    "#f05a28": "#244a73", "#008bd2": "#426b8f",
    "#22a447": "#607f99", "#9636d8": "#385c63",
    "#d98b00": "#71643f", "#d93a35": "#7a4a42",
}
TINT_BY_STROKE = {RULE: "#f5f7f9", INK: "#f5f7f9"}
FILL_MAP = {
    "#f7f2ee": "#f3f5f7", "#fdf6f2": "#f7f8f9", "#f6ece6": "#eef2f5",
    "#eef4f8": "#edf3f7", "#eef2f5": "#edf3f7", "#e8eef2": "#e8eef3",
    "#eef2e6": "#eef3ef", "#e9f1e5": "#e8f0ea",
    "#f3e8f5": "#f0eff3", "#f7eddc": "#f3f1e9", "#f6e3df": "#f2eceb",
    "#f2efe9": "#f2f3f4", "#f7f5f1": "#f5f6f7", "#f7f5f0": "#f5f6f7",
    "#fdfaf4": "#f8f8f7", "#fdfcfa": "#fafafa", "#fbfaf8": "#f7f8f9",
    "#fbfaf7": "#f5f7f9", "#f5f7f8": "#f2f5f7", "#eeeeeb": "#edf1f3",
}


def color(c: str) -> str:
    return COLOR_MAP.get(c.lower(), c)


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def text(x, y, s, size=11, fill=INK, weight="normal", anchor="start", font=FONT):
    fill = color(fill)
    return (
        f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
        f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>'
    )


def rect(x, y, w, h, fill="none", stroke=RULE, sw=1, rx=4, dash=None):
    stroke = color(stroke)
    fill = FILL_MAP.get(fill.lower(), fill)
    if fill == "#ffffff":
        fill = "#ffffff"
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}"{d}/>'
    )


def line(x1, y1, x2, y2, stroke=RULE, sw=1):
    stroke = color(stroke)
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"/>'


def wrap(s: str, width: int) -> list[str]:
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > width and cur:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out


def svg(width: int, height: int, body: str) -> str:
    for old, new in COLOR_MAP.items():
        body = body.replace(old, new)
    rail = f'<line x1="0" y1="1" x2="{width}" y2="1" stroke="{RULE}" stroke-width="2"/>'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>\n{rail}\n{body}\n</svg>\n'
    )


# ---------------------------------------------------------------- figure 1

FAMILIES = [
    ("F1", "Addressable-node reservoirs",
     "Memory from coupling among, or internal dynamics of, addressable nodes.",
     ["F1.1 Rate-based / analog-state", "F1.2 Spiking / event-driven",
      "F1.3 Hierarchical & multi-timescale", "F1.4 Structured-topology",
      "F1.5 Coupled-oscillator / phase", "F1.6 Uncoupled dynamic nodes"]),
    ("F2", "Delay-embedded reservoirs",
     "Memory from propagation delay; few nodes sampled as virtual nodes.",
     ["F2.1 Single-node time-multiplexed", "F2.2 Multi-delay / multi-loop",
      "F2.3 Frequency / wavelength mux", "F2.4 Deep / cascaded stages"]),
    ("F3", "Explicit-feature reservoirs",
     "No internal state. Memory from an explicit finite input window.",
     ["F3.1 Polynomial-feature (NG-RC)", "F3.2 Random-feature / kernel",
      "F3.3 Orthogonal-basis expansion", "F3.4 Learned-basis hybrid"]),
    ("F4", "Distributed-medium reservoirs",
     "Memory from spatial propagation in a continuum or unengineered mesh.",
     ["F4.1 Random material networks", "F4.2 Wave & field media",
      "F4.3 Lattice & automata", "F4.4 Mechanical / morphological"]),
]


TIER3_EXAMPLES = [
    ("leaky ESN on CPU", "F1.1 + digital-simulated + E0"),
    ("DFB-laser-array deep photonic RC", "F2.4 + photonic + E3"),
    ("Ag-nanowire mesh", "F4.1 + memristive-ionic + E2"),
]


def fig1() -> str:
    """Compact scientific hierarchy: definition, families, and subclasses."""
    W, H = 1000, 390
    b = []

    def arrow_down(x, y1, y2, col=INK):
        return [line(x, y1, x, y2 - 7, col, 1.5),
                f'<path d="M {x-4} {y2-7} L {x} {y2} L {x+4} {y2-7} Z" fill="{col}"/>']

    rx, rw = 230, 540
    b.append(rect(rx, 20, rw, 55, fill="#f7f2ee", stroke=INK, sw=1.5))
    b.append(text(500, 42, "RESERVOIR COMPUTING", 14, INK, "bold", "middle"))
    b.append(text(500, 61, "fixed state-generation map and trained readout", 10.5, MUTED, anchor="middle"))

    colw, gap = 220, 16
    centers = [44 + i * (colw + gap) + colw / 2 for i in range(4)]
    busy, ftop = 92, 112
    b.append(line(500, 75, 500, busy, INK, 1.5))
    b.append(line(centers[0], busy, centers[3], busy, INK, 1.5))
    for cx in centers:
        b += arrow_down(cx, busy, ftop)

    fh = 70
    for i, (code, name, q, subs) in enumerate(FAMILIES):
        x = 44 + i * (colw + gap)
        c = FAMILY_INK[code]
        # F3 is a flagged coverage class outside the strict dynamical-state definition
        # (Section 3.3.3); the dashed border says so without a second hierarchy.
        dash = "6,4" if code == "F3" else None
        b.append(rect(x, ftop, colw, fh, fill="#ffffff", stroke=c, sw=1.8, dash=dash))
        b.append(text(x + colw / 2, ftop + 23, code, 12, c, "bold", "middle", MONO))
        for j, ln in enumerate(wrap(name, 25)):
            b.append(text(x + colw / 2, ftop + 44 + j * 14, ln, 11, INK, "bold", "middle"))

    stop, sh = 220, 130
    for i, (code, name, q, subs) in enumerate(FAMILIES):
        x = 44 + i * (colw + gap)
        c = FAMILY_INK[code]
        b += arrow_down(centers[i], ftop + fh, stop, c)
        b.append(rect(x, stop, colw, sh, fill="#fdfcfa", stroke=c, sw=1.2,
                      dash="6,4" if code == "F3" else None))
        yy = stop + 22
        for s in subs:
            short = s.split(" ", 1)[1] if " " in s else s
            for ln in wrap(short, 27):
                b.append(text(x + colw / 2, yy, ln, 10, INK, "normal", "middle"))
                yy += 13
            yy += 2
    b.append(text(500, 377, "Substrate and evaluation attributes are recorded independently.",
                  10.5, MUTED, anchor="middle"))
    b.append(text(500, 393, "Dashed: F3 is a flagged coverage class outside the strict "
                            "dynamical-state definition (Section 3.3.3).", 10.5, MUTED,
                  anchor="middle"))
    return svg(W, H + 16, "\n".join(b))


# ---------------------------------------------------------------- figure 2

FACETS = [
    ("D1", "Substrate", "digital-simulated · digital-hardware · analog-electronic · photonic · "
                        "spintronic-magnetic · memristive-ionic · mechanical-soft · biological-organic · quantum"),
    ("D2", "Readout & training", "offline-linear · online-recursive · nonlinear-readout · sparse-selected · in-hardware"),
    ("D3", "Reservoir adaptation", "random-fixed · hp-optimized · unsupervised · evolved · physically-tuned"),
    ("D4", "Operating mode", "open-loop · closed-loop · control-in-loop · hybrid-physics-informed"),
    ("D5", "Task class", "imitation · prediction · computation · classification · property-measure"),
    ("D6", "Evidence tier", "E0 simulation · E1 substrate-model · E2 measured-trace · "
                            "E3 benchtop · E4 integrated · E5 field"),
]

FINGERPRINTS = [
    ("Lorenz forecasting with an echo state network, in software",
     "F1.1 · digital-simulated · offline-linear · hp-optimized · closed-loop · prediction · E0"),
    ("Optoelectronic delay line, spoken digit recognition",
     "F2.1 · photonic · offline-linear · random-fixed · open-loop · classification · E3"),
    ("Nanowire network characterised for memory capacity",
     "F4.1 · memristive-ionic · offline-linear · physically-tuned · open-loop · property-measure · E2"),
]


def fig2() -> str:
    W, H = 1000, 640
    b = []
    b.append(text(40, 42, "Evaluation dimensions", 17, INK, "bold"))
    b.append(text(40, 64, "Six orthogonal coding dimensions. These are the properties prior taxonomies "
                          "promoted to hierarchy levels.", 12, MUTED))
    y = 92
    facet_cols = ("#f05a28", "#008bd2", "#22a447", "#9636d8", "#d98b00", "#008bd2")
    for idx, (code, name, vals) in enumerate(FACETS):
        col = facet_cols[idx]
        b.append(rect(40, y, W - 80, 56, fill="#ffffff", stroke=col, dash="4 3"))
        b.append(text(70, y + 22, code, 11, col, "bold", "middle", MONO))
        b.append(text(W / 2, y + 21, name, 11.5, INK, "bold", "middle"))
        vy = y + 40
        for ln in wrap(vals, 118):
            b.append(text(W / 2, vy, ln, 9.5, MUTED, "normal", "middle"))
            vy += 12
        y += 64

    y += 10
    b.append(text(40, y, "Worked fingerprints", 13, INK, "bold"))
    y += 10
    for label, fp in FINGERPRINTS:
        y += 22
        b.append(text(40, y, label, 10.5, MUTED))
        y += 15
        b.append(text(40, y, fp, 10, INK, "normal", font=MONO))
    y += 26
    b.append(text(40, y, "Records 2 and 3 are both physical RC in every prior taxonomy and share exactly one "
                         "coordinate.", 10, INK))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 3

STEPS = [
    ("1", "Does the state depend on any internal variable carried across time steps?",
     "No, the state is a function of an explicit finite input window only", "F3"),
    ("2", "Is the dominant memory mechanism a propagation delay, with the state read by "
          "sampling one or few nodes across a delay interval?", "Yes", "F2"),
    ("3", "Are the state variables individually addressable units with a specified "
          "coupling structure?", "Yes", "F1"),
    ("4", "Otherwise: state sampled at probe positions in a medium whose internal "
          "coupling is not designed or not known", "", "F4"),
]


def fig3() -> str:
    W, H = 1000, 490
    b = []
    y = 26
    for n, q, ans, fam in STEPS:
        c = FAMILY_INK[fam]
        b.append(rect(40, y, W - 220, 78, fill="#ffffff"))
        b.append(f'<circle cx="70" cy="{y + 26}" r="13" fill="none" stroke="{c}" stroke-width="1.5"/>')
        b.append(text(70, y + 30, n, 11, c, "bold", "middle", font=MONO))
        qy = y + 24
        for ln in wrap(q, 74):
            b.append(text(96, qy, ln, 11, INK))
            qy += 14
        if ans:
            b.append(text(96, qy + 6, ans, 9.5, MUTED))
        b.append(rect(W - 165, y + 14, 125, 50, fill="#ffffff", stroke=c, sw=1.5))
        b.append(text(W - 102, y + 45, fam, 17, c, "bold", "middle", font=MONO))
        b.append(line(W - 220 + 40, y + 39, W - 165, y + 39, RULE))
        y += 92

    # The hybrid rule, and it is the rule the manuscript states, not the one it withdrew.
    # This box drew "whichever component generates most of the state dimension" until
    # 2026-09-09, which is the rule deviation D18 replaced on 2026-09-05 precisely because
    # it ranked components by a quantity Section 2.2 says is not comparable across
    # families. The figure therefore contradicted its own Section 3.2 in the built PDF for
    # four days. It also wrote the symmetric label as F2xF1; taxonomy 2.1 requires the
    # codes in ascending order, F1xF2. Fourth instance of a withdrawn value surviving in a
    # figure after the text was corrected, so: when a rule changes, grep figures.py too.
    # Box height is DERIVED from the wrapped line count, not hand-set. The first attempt at
    # this fix hard-coded 86 against text that wraps to five lines, and the last line
    # ("F1xF2.") fell outside the dashed border in the proof PDF. A box sized by hand
    # against text edited by hand drifts the moment either changes, which is the same shape
    # of failure as the rule the box states.
    hybrid_lines = wrap(
        "Primary family is the component whose mechanism dominates state generation, judged "
        "from the reported memory mechanism and never from a reported count: the one whose "
        "removal would end the system's dependence on input history. The other is recorded "
        "as a secondary family. Where the report does not establish dominance, no primary "
        "family is assigned and the record carries a symmetric label, written F1xF2.", 100)
    LINE_H, TOP, BOT = 14, 46, 12
    box_h = TOP + LINE_H * len(hybrid_lines) + BOT
    b.append(rect(40, y + 6, W - 80, box_h, fill="#fbfaf8", dash="4 3"))
    b.append(text(56, y + 28, "Hybrids", 10.5, INK, "bold"))
    hy = y + TOP
    for ln in hybrid_lines:
        b.append(text(56, hy, ln, 10, MUTED))
        hy += LINE_H
    return svg(W, int(y + 6 + box_h + 18), "\n".join(b))


# ---------------------------------------------------------------- data-dependent

DATA_FIGURES = {
    "fig5": ("Corpus composition over time",
             "Two stacked panels, family-by-year and substrate-by-year, side by side to show the "
             "two trends are decoupled.", "records.csv"),
    "fig6": ("Evidence ladder distribution by family",
             "E0-E5 distribution per family with the rhetoric-mismatch overlay from A3.", "records.csv"),
    "fig7": ("Reporting completeness heatmap",
             "Audit items by stratum, percent stated.", "records.csv"),
    "fig8": ("Reproduction outcome Sankey",
             "Sampled to attempted to R0-R4, with failure causes as terminal branches.", "reproduction.csv"),
    "fig9": ("Matched-pair simulated vs physical",
             "Same family, benchmark and metric; paired connectors. Caption must state that this "
             "compares reported values and is not a re-execution.", "benchmarks.csv"),
    "fig10": ("Efficiency re-normalised to B3",
              "Reported vs B3-normalised, log axis, boundary coded by colour, assumption ranges shown.",
              "records.csv"),
    "fig11": ("Benchmark saturation",
              "NARMA-10 usage over time with the discrimination band (0.05 to 0.16 NMSE) shaded.",
              "benchmarks.csv"),
    "fig12": ("Deployment funnel",
              "Claimed-applicable to E4 to E5 by domain, peer-reviewed and vendor claims separated.",
              "records.csv"),
}


def data_figure(name: str, extraction: Path) -> str:
    title, desc, needs = DATA_FIGURES[name]
    path = extraction / needs
    rows = []
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(
            f"{name} ({title}) needs {path}, which is missing or empty.\n"
            f"  Plan: {desc}\n"
            f"  Extraction has not run. Rendering this figure now would produce an empty\n"
            f"  plot that reads as a finding, so it is refused rather than emitted."
        )
    raise SystemExit(
        f"{name}: {len(rows)} rows found in {path}. Renderer not yet implemented.\n"
        f"  Plan: {desc}"
    )


# ---------------------------------------------------------------- driver



# ---------------------------------------------------------------- figure 0
# The orientation figure. A reader who knows nothing about reservoir computing
# should be able to start here and follow the rest of the paper. It draws the
# three invariants of the RC Contract onto the architecture they constrain, so
# the membership test in Section 2 is visual before it is formal.

def fig0() -> str:
    W, H = 1180, 470
    b = [text(40, 42, "Reservoir-computing system", 17, weight="bold"),
         text(40, 66, "The reservoir is never trained. Only the linear readout is fitted. "
                      "Everything else follows from that.", 12, MUTED)]

    # input
    b += [rect(60, 130, 150, 110, fill="#f7f5f0", stroke=RULE),
          text(135, 168, "INPUT", 12, MUTED, "bold", "middle"),
          text(135, 195, "u(t)", 20, INK, "bold", "middle", MONO),
          text(135, 220, "a time series", 10, MUTED, anchor="middle")]

    # reservoir
    b += [rect(280, 100, 380, 170, fill="#fdfaf4", stroke="#8a4b2a", sw=2),
          text(470, 130, "RESERVOIR", 13, "#8a4b2a", "bold", "middle"),
          text(470, 150, "a dynamical system with many state variables", 10, MUTED,
               anchor="middle")]
    import math
    nodes = [(340, 200), (395, 175), (450, 215), (505, 180), (560, 210), (600, 175),
             (370, 240), (480, 245), (545, 250)]
    for (x1, y1) in nodes:
        for (x2, y2) in nodes:
            if (x1, y1) < (x2, y2) and abs(x1 - x2) < 95:
                b.append(line(x1, y1, x2, y2, "#e0d6c8", 1))
    for (x, y) in nodes:
        b.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#8a4b2a" opacity="0.85"/>')
    b.append(text(470, 285, "x(t), the state vector", 11, INK, "bold", "middle", MONO))

    # readout
    b += [rect(730, 130, 160, 110, fill="#eef4f8", stroke="#2f5d7c", sw=2),
          text(810, 165, "READOUT", 12, "#2f5d7c", "bold", "middle"),
          text(810, 192, "W_out", 18, INK, "bold", "middle", MONO),
          text(810, 217, "linear, TRAINED", 10, "#2f5d7c", "bold", "middle")]

    # output
    b += [rect(960, 130, 150, 110, fill="#f7f5f0", stroke=RULE),
          text(1035, 168, "OUTPUT", 12, MUTED, "bold", "middle"),
          text(1035, 195, "y(t)", 20, INK, "bold", "middle", MONO),
          text(1035, 220, "the prediction", 10, MUTED, anchor="middle")]

    for x1, x2 in ((210, 280), (660, 730), (890, 960)):
        b.append(line(x1, 185, x2 - 10, 185, INK, 2))
        b.append(f'<path d="M {x2-10} 180 L {x2} 185 L {x2-10} 190 Z" fill="{INK}"/>')

    # the three invariants, tied to what they constrain
    inv = [(300, "I1", "The state map is high-dimensional, nonlinear and input-driven.",
            "#8a4b2a"),
           (330, "I2", "No task error reaches the reservoir. Its parameters are not "
            "trained.", "#8a4b2a"),
           (360, "I3", "The readout is trained, and it is the only thing that is.",
            "#2f5d7c")]
    b.append(text(60, 325, "THE THREE INVARIANTS  (Section 2: all three must hold, or it "
                           "is not reservoir computing)", 11, INK, "bold"))
    for y, k, txt, col in inv:
        b += [text(60, y + 45, k, 12, col, "bold", font=MONO),
              text(95, y + 45, txt, 12, INK)]

    b.append(text(60, 438, "Why it matters: training only a linear readout is cheap and "
                           "stable, and it lets the reservoir be", 11, MUTED))
    b.append(text(60, 456, "almost any physical system, from a photonic cavity to a soft "
                           "robot limb. That freedom is the subject of this paper.",
                  11, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 4
# The discrimination framework, drawn on a single performance axis. The three
# failures the literature conflates are three regions, not three opinions.

def fig4() -> str:
    W, H = 1180, 430
    b = [text(40, 42, "Benchmark discrimination regions", 17,
              weight="bold"),
         text(40, 66, "Performance regions defined relative to trivial, resolution, and saturation limits.", 12, MUTED)]

    x0, x1, y = 90, 1100, 200
    b.append(line(x0, y, x1, y, INK, 2))
    b.append(text(x0, y + 60, "Perfect", 11, MUTED, anchor="middle"))
    b.append(text(x1, y + 60, "Useless", 11, MUTED, anchor="middle"))
    b.append(text((x0 + x1) // 2, y + 78, "reported error, increasing to the right",
                  11, MUTED, anchor="middle"))

    bands = [
        (x0, 235, "#e8eef2", "#2f5d7c", "SATURATED",
         "Compressed score range.", "Limited method resolution."),
        (235, 420, "#eef2e6", "#4f6b2f", "BELOW THE RESOLUTION FLOOR",
         "Difference below run spread.", "Dispersion required."),
        (420, 830, "#ffffff", RULE, "INFORMATIVE",
         "Differences exceed", "measurement variation."),
        (830, x1, "#f6ece6", "#8a4b2a", "ABOVE THE TRIVIALITY CEILING",
         "At or below trivial performance.", "No reservoir benefit established."),
    ]
    for xa, xb, fill, stroke, label, l1, l2 in bands:
        b.append(rect(xa, y - 55, xb - xa, 55, fill=fill, stroke=stroke, sw=1.5, rx=0))
        b.append(text((xa + xb) // 2, y - 32, label, 11, stroke, "bold", "middle"))
        b.append(text((xa + xb) // 2, y + 22, l1, 9, MUTED, anchor="middle"))
        b.append(text((xa + xb) // 2, y + 38, l2, 9, MUTED, anchor="middle"))

    for xm, name, sym in ((235, "T_sat", "saturation"), (420, "T_res", "resolution floor"),
                          (830, "T_triv", "triviality ceiling")):
        b.append(line(xm, y - 70, xm, y + 8, INK, 1.5))
        b.append(text(xm, y - 80, sym, 11, INK, "bold", "middle", MONO))
        b.append(text(xm, y - 95, name, 10, MUTED, anchor="middle"))

    b.append(text(60, 330, "The regions require different interpretations and corrective actions.", 12, INK))
    for i, (t, r) in enumerate([
            ("A result above the triviality ceiling", "needs a better system."),
            ("A result below the resolution floor", "needs reported dispersion before it "
             "can be read at all."),
            ("A saturated benchmark", "needs replacing.")]):
        b.append(text(80, 360 + i * 22, "-  " + t, 11, INK, "bold"))
        b.append(text(80 + 290, 360 + i * 22, r, 11, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 5s
# The metric collision, as a table. Companion to fig19s, which draws the same
# three sources as a flow. Redrawn 2026-09-05 after deviation D16: the third
# row previously read "~0.4 NMSE, value retained, label changed", which was
# this project's misquotation of a primary that says ~0.434 for a different
# input distribution. A released figure asserting a withdrawn reading is the
# exact failure this paper reports, so it is corrected rather than retired.

def fig5s() -> str:
    W, H = 1180, 440
    b = []

    rows = [("Single-node RC paper", "Primary source", "NRMSE", "0.4", "#4f6b2f"),
            ("Passive-cavity RC paper", "Explicit conversion", "NMSE", "0.16", "#4f6b2f"),
            ("Magnetic-metamaterial paper", "Authors' own baseline, autocorrelated input",
             "NMSE", "~0.434", "#8a4b2a")]
    y = 130
    b.append(rect(60, y - 30, 1060, 30, fill="#f2efe9", stroke=RULE, rx=0))
    for cx, lab in ((220, "SOURCE"), (530, "ROLE"), (780, "METRIC"), (1010, "VALUE")):
        b.append(text(cx, y - 10, lab, 10, MUTED, "bold", "middle"))
    for i, (src, role, metric, val, col) in enumerate(rows):
        yy = y + 26 + i * 52
        b.append(rect(60, yy - 22, 1060, 46, fill="#ffffff", stroke=RULE, rx=0))
        b.append(text(220, yy + 5, src, 11.5, INK, "bold", "middle"))
        b.append(text(530, yy + 5, role, 10.5, MUTED, "normal", "middle"))
        b.append(text(780, yy + 5, metric, 13, col, "bold", "middle", MONO))
        b.append(text(1010, yy + 5, val, 15, col, "bold", "middle", MONO))

    yb = 342
    b.append(rect(60, yb - 28, 500, 76, fill="#eef2e6", stroke="#4f6b2f", sw=1.5))
    b.append(text(80, yb - 6, "Equivalent values", 12, "#4f6b2f", "bold"))
    b.append(text(80, yb + 20, "0.4\u00b2 = 0.16", 20, INK, "bold", font=MONO))
    b.append(text(230, yb + 20, "NRMSE squared is NMSE.", 12, MUTED))

    b.append(rect(600, yb - 28, 520, 76, fill="#f6ece6", stroke="#8a4b2a", sw=1.5))
    b.append(text(620, yb - 6, "A different quantity", 12, "#8a4b2a", "bold"))
    b.append(text(620, yb + 16, "0.434 NMSE is that paper's own shift register on a",
                  11, INK))
    b.append(text(620, yb + 34, "NARMA-N variant, not 0.4 NRMSE relabelled.", 11, INK))

    b.append(text(60, 431, "Read as bare NMSE values the two published baselines differ by a "
                           "factor of 2.7; metric, normalization and input distribution are "
                           "required for comparison.", 11, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 6s
# RC-LADDER, the evidence scale, as an actual ladder.

def fig6s() -> str:
    W, H = 1000, 640
    b = [text(40, 42, "Evidence levels", 17, weight="bold"),
         text(40, 66, "Every claim in the corpus is coded to one rung. The gap that matters "
                      "most is between E2 and E3.", 12, MUTED)]
    rungs = [
        ("E5", "Deployed", "Running in a real application outside the lab.", "#2f5d7c"),
        ("E4", "Integrated", "A packaged system operating in real time.", "#2f5d7c"),
        ("E3", "Live device", "The device processed the input in order, at rate.",
         "#4f6b2f"),
        ("E2", "Assembled traces", "States measured separately, combined offline into a "
         "state matrix.", "#8a4b2a"),
        ("E1", "Device-informed model", "Simulation calibrated to a measured device.",
         "#6b4a7c"),
        ("E0", "Model only", "Numerical simulation.", "#6b4a7c"),
    ]
    for i, (code, name, desc, col) in enumerate(rungs):
        y = 110 + i * 62 + (90 if i >= 3 else 0)
        b.append(rect(70, y, 850, 50, fill="#ffffff", stroke=col, sw=1.5))
        b.append(rect(70, y, 62, 50, fill=col, stroke=col, rx=4))
        b.append(text(101, y + 31, code, 16, "#ffffff", "bold", "middle", MONO))
        b.append(text(150, y + 21, name, 13, INK, "bold"))
        b.append(text(150, y + 39, desc, 11, MUTED))
    ygap = 300
    b.append(line(70, ygap, 920, ygap, "#8a4b2a", 2))
    b.append(rect(70, ygap + 10, 850, 44, fill="#f6ece6", stroke="#8a4b2a", sw=1.5))
    b.append(text(88, ygap + 30, "THE LINE THAT IS ROUTINELY BLURRED", 11, "#8a4b2a",
                  "bold"))
    b.append(text(88, ygap + 47, "Both E2 and E3 are described in abstracts as "
                                 "\"demonstrations\". Only E3 processed a sequence in order "
                                 "at rate.", 11, INK))
    b.append(text(40, 610, "Where a paper does not make this determinable, the audit codes "
                           "E2 and flags it. The rate at which it is indeterminable is "
                           "itself a finding.", 11, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 7s
# The PRISMA 2020 flow, to date. The paper reports per PRISMA, so the flow
# diagram is expected furniture. It reads the released counts file at render
# time and refuses without it; the screening stages are drawn dashed and
# labelled pending, because zero records have been screened and a flow diagram
# that implied otherwise would be a lie in a box.

def _prisma_counts() -> dict:
    p = Path("data/screening/prisma_counts.json")
    if not p.exists():
        raise SystemExit(
            "fig7s needs data/screening/prisma_counts.json, which is missing.\n"
            "  Run scripts/dedupe.py to regenerate it from the frozen exports."
        )
    import json
    return json.loads(p.read_text(encoding="utf-8"))


def fig7s() -> str:
    c = _prisma_counts()
    W, H = 1000, 700
    b = []

    def box(x, y, w, h, lines, stroke=INK, dash=None, fill="#ffffff"):
        out = [rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.5, dash=dash)]
        for i, (s, size, col, wt) in enumerate(lines):
            out.append(text(x + w / 2, y + 22 + i * 18, s, size, col, wt, "middle"))
        return out

    def arrow(x, y1, y2):
        return [line(x, y1, x, y2 - 8, INK, 1.5),
                f'<path d="M {x-4} {y2-8} L {x} {y2} L {x+4} {y2-8} Z" fill="{INK}"/>']

    # identification
    b += box(70, 100, 380, 58, [
        (f"OpenAlex: {c['per_source']['openalex']:,} in-window works", 12, INK, "bold"),
        (f"arXiv: {c['per_source']['arxiv']:,} in-window records", 12, INK, "bold")])
    b += box(530, 100, 380, 58, [
        (f"Total identified: {c['raw_total']:,}", 13, INK, "bold"),
        ("window 2019-01-01 to 2026-06-30, frozen", 10, MUTED, "normal")])
    b.append(line(450, 129, 530, 129, INK, 1.5))
    b += arrow(720, 158, 200)

    # dedup
    removed = (c["removed_doi_exact"] + c["removed_arxiv_id_exact"]
               + c["removed_title_match"] + c["removed_manual_adjudication"])
    b += box(530, 200, 380, 112, [
        (f"Removed as duplicates: {removed:,}", 12, INK, "bold"),
        (f"exact DOI match: {c['removed_doi_exact']}", 11, MUTED, "normal"),
        (f"exact arXiv identifier: {c['removed_arxiv_id_exact']}", 11, MUTED, "normal"),
        (f"normalized title match: {c['removed_title_match']}", 11, MUTED, "normal"),
        # Reads the counts rather than asserting an outcome. Until 2026-09-05 this line
        # said "none merged", which was true only while the adjudication was outstanding
        # and became false the moment it was applied.
        (f"human adjudication: {c['removed_manual_adjudication']} "
         f"(of {c['near_duplicate_pairs_flagged']} pairs flagged)",
         11, "#8a4b2a", "normal")])
    b += arrow(720, 312, 354)

    # corpus
    b += box(530, 354, 380, 50, [
        (f"Corpus: {c['deduped_total']:,} records", 14, INK, "bold")])
    b += arrow(720, 404, 446)

    # eligibility split
    b += box(70, 446, 380, 76, [
        (f"Closed access: {c['closed_excluded_d6']:,}", 12, "#8a4b2a", "bold"),
        ("excluded by the open-access criterion; retained as metadata", 11, MUTED, "normal"),
        ("characterized, not assumed harmless", 11, MUTED, "normal")],
        stroke="#8a4b2a")
    b += box(530, 446, 380, 76, [
        (f"Openly retrievable: {c['open_access_eligible']:,}", 12, "#4f6b2f", "bold"),
        ("eligible for screening", 11, MUTED, "normal"),
        (f"{c['open_without_abstract']} lack an abstract; screened on title, "
         "not dropped", 11, MUTED, "normal")], stroke="#4f6b2f")
    b.append(line(530, 484, 450, 484, "#8a4b2a", 1.5))
    b += arrow(720, 522, 564)

    # pending stages
    b += box(530, 564, 380, 44, [
        ("Stage 1 screening: PENDING, 0 records screened", 11, MUTED, "bold")],
        stroke=MUTED, dash="6,4", fill="#fbfaf7")
    b += arrow(720, 608, 634)
    b += box(530, 634, 380, 44, [
        ("Stage 2, extraction, reproduction: PENDING", 11, MUTED, "bold")],
        stroke=MUTED, dash="6,4", fill="#fbfaf7")

    # The caption follows the adjudication state instead of asserting it, so the figure
    # cannot keep telling a reader that a completed step is outstanding.
    if c.get("near_duplicate_adjudication_complete"):
        b.append(text(70, 560, f"All {c['near_duplicate_pairs_flagged']} near-duplicate "
                               f"pairs are adjudicated.", 11, MUTED))
        b.append(text(70, 578, "Screening starts once the taxonomy freezes at the",
                      11, MUTED))
        b.append(text(70, 596, "pilot gate.", 11, MUTED))
    else:
        b.append(text(70, 560, f"Screening starts only after the "
                               f"{c['near_duplicate_pairs_flagged']} near-duplicate",
                      11, MUTED))
        b.append(text(70, 578, "pairs are adjudicated by hand and the taxonomy", 11, MUTED))
        b.append(text(70, 596, "freezes at the pilot gate.", 11, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 8s
# The corpus by year. This is the evidence that the yield overshoot is growth
# rather than leakage, and a bar chart says it faster than the paragraph does.

def _corpus_years() -> dict[str, int]:
    p = Path("data/screening/corpus_deduped.csv")
    if not p.exists():
        raise SystemExit(
            "fig8s needs data/screening/corpus_deduped.csv, which is missing.\n"
            "  Run scripts/dedupe.py to rebuild it from the frozen exports."
        )
    from collections import Counter
    years: Counter[str] = Counter()
    with p.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if not row.get("dup_of"):
                y = (row.get("year") or "").strip()
                if y.isdigit():
                    years[y] += 1
    return dict(years)


def fig8s() -> str:
    years = _corpus_years()
    order = [str(y) for y in range(2019, 2027)]
    counts = [years.get(y, 0) for y in order]
    W, H = 1000, 460
    b = [text(40, 42, "Candidate corpus by publication year", 17,
              weight="bold"),
         text(40, 66, "The pre-registered yield estimate assumed the field's rate of "
                      "output; the field more than doubled it instead.", 12, MUTED)]
    x0, y0, bw, gap = 90, 360, 92, 20
    peak = max(counts)
    scale = 220 / peak
    for i, (y, n) in enumerate(zip(order, counts)):
        x = x0 + i * (bw + gap)
        h = n * scale
        partial = y == "2026"
        fill = "#d8d2c6" if partial else "#2f5d7c"
        b.append(rect(x, y0 - h, bw, h, fill=fill, stroke="none", rx=2))
        b.append(text(x + bw / 2, y0 - h - 8, f"{n:,}", 12, INK, "bold", "middle"))
        b.append(text(x + bw / 2, y0 + 20, y, 12, MUTED, anchor="middle"))
        if partial:
            b.append(text(x + bw / 2, y0 + 38, "to 30 June", 10, MUTED, anchor="middle"))
    b.append(line(x0 - 10, y0, x0 + 8 * (bw + gap), y0, INK, 1.5))
    first, last_full = counts[0], counts[6]
    footer = (f"{first} records in 2019 to {last_full:,} in 2025, a factor of "
              f"{last_full / first:.1f}. The 100-title probe found leakage cannot account "
              "for the overshoot; growth does. Counts are the deduplicated corpus, not "
              "the raw harvest. The 2026 bar covers half a year and understates 2026 by "
              "roughly the 6% indexing lag of Section 8.1.")
    for j, ln in enumerate(wrap(footer, 118)):
        b.append(text(90, 414 + j * 17, ln, 11, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 9s
# RC-BOUND as nested boundaries. The instrument is a convention about where
# the measurement line is drawn, so it is drawn.

def fig9s() -> str:
    W, H = 1080, 540
    b = [text(40, 42, "Efficiency measurement boundaries",
              19, weight="bold"),
         text(40, 66, "Nested boundaries for energy and throughput claims. A figure of "
                      "merit means nothing until its boundary is stated.", 12, MUTED)]

    frames = [
        ("B3", 70, 100, 660, 360, "#2f5d7c",
         "+ readout computation, pre- and post-processing, amortized calibration"),
        ("B2", 110, 150, 580, 260, "#4f6b2f",
         "+ state acquisition: probes, converters, sampling at task bandwidth"),
        ("B1", 150, 200, 500, 160, "#8a4b2a",
         "+ input encoding, modulation, drive electronics"),
        ("B0", 190, 250, 420, 70, "#6b4a7c",
         "reservoir core: the substrate's own dissipation"),
    ]
    for code, x, y, w, h, col, lab in frames:
        b.append(rect(x, y, w, h, fill="none", stroke=col, sw=2))
        b.append(text(x + 12, y + 22, code, 14, col, "bold", font=MONO))
        b.append(text(x + w / 2, y + 22, lab, 10.5, INK, "normal", "middle"))

    notes = [
        ("B0", "#6b4a7c", "Most headline figures appear to be computed here."),
        ("B1", "#8a4b2a", "In photonic systems this term is often dominant."),
        ("B2", "#4f6b2f", "Frequently exceeds the core; probe and converter count is a "
                          "first-order constraint."),
        ("B3", "#2f5d7c", "The only boundary at which comparison against a digital "
                          "baseline means anything."),
    ]
    for i, (code, col, note) in enumerate(notes):
        y = 120 + i * 64
        b.append(text(770, y, code, 13, col, "bold", font=MONO))
        for j, ln in enumerate(wrap(note, 40)):
            b.append(text(810, y + j * 16, ln, 11, INK))

    b.append(text(70, 500, "Two fields are coded per efficiency claim: the boundary at "
                           "which it was computed, and whether the paper states its "
                           "boundary at all.", 11, MUTED))
    b.append(text(70, 518, "Analysis A2 re-normalizes claims to B3 from each paper's own "
                           "stated components; records that cannot be re-normalized are "
                           "excluded, not estimated.", 11, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 10s
# The instruments composed into one pipeline. A 50-page paper needs a map a
# reader can hold; this is that map, and it is deliberately NOT a topic tree:
# mixing instruments, benchmarks and analyses into one hierarchy is the exact
# error Section 3.3 argues against.

def fig10s() -> str:
    W, H = 1180, 400
    b = [text(40, 42, "Framework components", 17, weight="bold"),
         text(40, 66, "What happens to one published record under this paper's apparatus. "
                      "Each stage is a separate instrument with its own section.",
              12, MUTED)]

    def stage(x, w, title, col, lines, sec):
        out = [rect(x, 110, w, 96, fill="#ffffff", stroke=col, sw=1.8),
               text(x + w / 2, 132, title, 12, col, "bold", "middle")]
        yy = 150
        for ln in lines:
            out.append(text(x + w / 2, yy, ln, 9.5, INK, "normal", "middle"))
            yy += 13
        out.append(text(x + w / 2, 199, sec, 9, MUTED, "normal", "middle", MONO))
        return out

    def arrow_right(x1, x2, y=158):
        return [line(x1, y, x2 - 8, y, INK, 1.5),
                f'<path d="M {x2-8} {y-4} L {x2} {y} L {x2-8} {y+4} Z" fill="{INK}"/>']

    b += [rect(40, 128, 120, 60, fill="#f2efe9", stroke=RULE),
          text(100, 154, "a published", 10.5, INK, "normal", "middle"),
          text(100, 170, "record", 10.5, INK, "normal", "middle")]
    b += arrow_right(160, 186)

    b += stage(186, 176, "RC CONTRACT", "#8a4b2a",
               ["membership test", "three invariants I1 I2 I3"], "Section 2")
    b += arrow_right(362, 388)
    b += stage(388, 176, "RC-PYRAMID", "#2f5d7c",
               ["family F1 to F4 by", "state-generation principle,", "then subclass"],
               "Section 3")
    b += arrow_right(564, 590)
    b += stage(590, 220, "RC-FACET", "#4f6b2f",
               ["six coordinates D1 to D6;", "D6 is RC-LADDER, evidence E0 to E5"],
               "Section 4")
    b += arrow_right(810, 836)
    b += stage(836, 304, "PER-CLAIM CONVENTIONS", "#6b4a7c",
               ["benchmark thresholds: triviality,", "resolution, saturation;",
                "RC-BOUND B0 to B3 for efficiency"], "Sections 4.2 and 5")

    # exclusion branch under the contract
    b += [line(274, 206, 274, 240, "#8a4b2a", 1.2),
          f'<path d="M 270 240 L 274 247 L 278 240 Z" fill="#8a4b2a"/>',
          rect(196, 247, 156, 40, fill="#fdf6f2", stroke="#8a4b2a", sw=1, dash="4 3"),
          text(274, 264, "fails the contract:", 9.5, "#8a4b2a", "normal", "middle"),
          text(274, 278, "excluded, and the ruling recorded", 8.5, MUTED, "normal", "middle")]

    # the product
    b += [line(988, 206, 988, 240, INK, 1.5),
          f'<path d="M 984 240 L 988 247 L 992 240 Z" fill="{INK}"/>',
          rect(560, 247, 580, 60, fill="#eef2f5", stroke="#2f5d7c", sw=1.5),
          text(850, 270, "one fingerprint per record: family + subclass + facet vector",
               11, INK, "bold", "middle"),
          text(850, 290, "the unit on which the registered analyses A1 to A5 (Section 6.3) "
               "operate in paper 2", 10, MUTED, "normal", "middle")]

    b.append(text(40, 350, "Two records are comparable when their fingerprints say so, "
                           "not when their substrates match. That single change is what "
                           "the rest of the paper builds on.", 11, MUTED))
    b.append(text(40, 368, "This is a pipeline, not a taxonomy: the hierarchy itself has "
                           "exactly one axis (Figure 1), and everything else is a "
                           "coordinate.", 11, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 11s
# The field's history on one axis: results above, maps of the field below,
# and the absence the paper exists to fill written where it cannot be missed.
# Every year is the publication year of a verified entry in references.bib.

def fig11s() -> str:
    W, H = 1180, 470
    b = [text(40, 42, "Selected reservoir-computing literature", 17, weight="bold"),
         text(40, 66, "Above the axis, foundational results and architectures. Below it, "
                      "the surveys, tutorials, frameworks and tools that map the field.",
              12, MUTED)]

    x0, x1, ay = 80, 1120, 230
    def X(year): return x0 + (year - 2000) * (x1 - x0) / 27.0

    b.append(line(x0 - 10, ay, x1 + 10, ay, INK, 2))

    results = [  # (year, lines, level 1..2)
        (2001, ["2001 echo state", "network"], 1),
        (2002, ["2002 liquid state machine;", "memory capacity bound"], 2),
        (2004, ["2004 chaotic prediction,", "channel equalization"], 1),
        (2011, ["2011 delay reservoir,", "virtual nodes"], 1),
        (2012, ["2012 information", "processing capacity"], 2),
        (2018, ["2018 universality", "results"], 1),
        (2021, ["2021 NG-RC; NARMA-10", "instability shown"], 2),
    ]
    maps_ = [
        (2009, ["2009 methods", "review"], 1),
        (2019, ["2019 substrate map;", "CHARC"], 2),
        (2020, ["2020 perspective"], 1),
        (2022, ["2022 tutorial"], 3),
        (2023, ["2023 applications", "review"], 1),
        (2024, ["2024 deployment-gap synthesis;", "two substrate reviews"], 2),
        (2025, ["2025 benchmark", "best practice"], 3),
        (2026, ["2026 RCbench;", "two further reviews"], 1),
    ]
    up_y = {1: 176, 2: 122}
    dn_y = {1: 272, 2: 318, 3: 364}
    for year, lines, lv in results:
        x = X(year)
        b.append(line(x, up_y[lv] + 6, x, ay - 5, "#2f5d7c", 1.2))
        b.append(f'<circle cx="{x}" cy="{ay}" r="4" fill="#2f5d7c"/>')
        for j, ln in enumerate(lines):
            b.append(text(x, up_y[lv] - (len(lines) - 1 - j) * 13, ln, 9.5,
                          "#2f5d7c" if j == 0 else INK, "bold" if j == 0 else "normal",
                          "middle"))
    for year, lines, lv in maps_:
        x = X(year)
        b.append(line(x, ay + 5, x, dn_y[lv] - 12, "#8a4b2a", 1.2))
        b.append(f'<circle cx="{x}" cy="{ay}" r="4" fill="#8a4b2a"/>')
        for j, ln in enumerate(lines):
            b.append(text(x, dn_y[lv] + j * 13, ln, 9.5,
                          "#8a4b2a" if j == 0 else INK, "bold" if j == 0 else "normal",
                          "middle"))

    b.append(text(x0 - 14, 150, "RESULTS", 9, "#2f5d7c", "bold"))
    b.append(text(x0 - 14, 296, "MAPS", 9, "#8a4b2a", "bold"))

    b.append(rect(80, 404, 1040, 46, fill="#fdf6f2", stroke="#8a4b2a", sw=1.5))
    b.append(text(600, 424, "Systematic audits of the reservoir computing corpus in this "
                            "period: none.", 12, "#8a4b2a", "bold", "middle"))
    b.append(text(600, 441, "Section 6 specifies the first, before any record is screened.",
                  10.5, INK, "normal", "middle"))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 12s
# The paper's central counterexample in one glance: substrate grouping joins
# unlike architectures, while a state-generation grouping joins like ones.

def fig12s() -> str:
    W, H = 1180, 500
    b = [text(40, 42, "Substrate- and architecture-based classification", 17, weight="bold"),
         text(40, 66, "The same material can implement different memory mechanisms; the same memory mechanism can cross materials.",
              12, MUTED)]

    items = [
        (80, 125, "PHOTONIC", "laser + delayed feedback", "F2  delay-embedded", "#2f5d7c"),
        (80, 285, "PHOTONIC", "coupled waveguide array", "F1  recurrent-network", "#8a4b2a"),
        (700, 125, "DIGITAL", "simulated delayed node", "F2  delay-embedded", "#2f5d7c"),
        (700, 285, "ELECTRONIC", "coupled oscillator array", "F1  recurrent-network", "#8a4b2a"),
    ]
    for x, y, sub, system, family, col in items:
        b += [rect(x, y, 390, 100, fill="#ffffff", stroke=col, sw=1.8),
              text(x + 195, y + 24, sub, 9, MUTED, "bold", "middle", MONO),
              text(x + 195, y + 52, system, 13, INK, "bold", "middle"),
              text(x + 195, y + 78, family, 11, col, "bold", "middle", MONO)]

    # What a substrate-first review does on the left.
    b += [rect(55, 104, 440, 302, fill="none", stroke="#6b4a7c", sw=2, dash="6 4"),
          text(275, 430, "SUBSTRATE GROUPING", 10, "#6b4a7c", "bold", "middle", MONO),
          text(275, 449, "joins unlike architectures", 11, INK, "normal", "middle")]

    # What the proposed architecture axis does across materials.
    for y, col in ((175, "#2f5d7c"), (335, "#8a4b2a")):
        b += [line(470, y, 692, y, col, 2),
              f'<path d="M 684 {y-5} L 694 {y} L 684 {y+5} Z" fill="{col}"/>']
    b += [text(590, 157, "same state-generation principle", 10, "#2f5d7c", "bold", "middle"),
          text(590, 317, "same state-generation principle", 10, "#8a4b2a", "bold", "middle"),
          text(900, 430, "ARCHITECTURE GROUPING", 10, "#4f6b2f", "bold", "middle", MONO),
          text(900, 449, "crosses substrates and preserves comparability", 11, INK, "normal", "middle")]
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 13s
# Visual companion to Table 2.1: it makes the uneven reach of theory visible,
# especially the F3 column, without pretending that partial results are binary.

def fig13s() -> str:
    W, H = 1120, 520
    b = [text(40, 42, "Applicability of theoretical results", 17, weight="bold"),
         text(40, 66, "Applicability by family. The conspicuous gap is F3: explicit finite-window features sit outside most dynamical-state results.",
              12, MUTED)]
    rows = [
        ("Echo state property", ["yes", "yes", "n/a", "yes"]),
        ("Fading memory", ["yes", "yes", "n/a", "yes"]),
        ("Memory-capacity bound", ["yes", "partial", "n/a", "partial"]),
        ("Processing capacity", ["yes", "yes", "yes", "yes"]),
        ("Memory / nonlinearity trade-off", ["yes", "yes", "yes", "yes"]),
        ("Fading-memory universality", ["yes", "yes", "no", "unclear"]),
    ]
    x0, y0, labelw, cw, rh = 40, 112, 350, 165, 50
    headers = [("F1", "recurrent"), ("F2", "delay"), ("F3", "features"), ("F4", "medium")]
    b.append(rect(x0, y0, labelw, 54, fill="#f2efe9", stroke=RULE))
    b.append(text(x0 + 14, y0 + 33, "THEORETICAL RESULT", 11, INK, "bold"))
    for j, (code, lab) in enumerate(headers):
        x = x0 + labelw + j * cw
        col = FAMILY_INK[code]
        b += [rect(x, y0, cw, 54, fill="#f7f5f1", stroke=col, sw=1.2),
              text(x + cw/2, y0 + 22, code, 12, col, "bold", "middle", MONO),
              text(x + cw/2, y0 + 40, lab.upper(), 9.5, MUTED, "bold", "middle")]
    fills = {"yes": "#e9f1e5", "partial": "#f7eddc", "n/a": "#eeeeeb", "no": "#f6e3df", "unclear": "#f3e8f5"}
    inks = {"yes": "#4f6b2f", "partial": "#8a4b2a", "n/a": MUTED, "no": "#8a3b2a", "unclear": "#6b4a7c"}
    for i, (label, vals) in enumerate(rows):
        y = y0 + 54 + i * rh
        b += [rect(x0, y, labelw, rh, fill="#ffffff", stroke=RULE),
              text(x0 + 14, y + 31, label, 10.5, INK)]
        for j, val in enumerate(vals):
            x = x0 + labelw + j * cw
            b += [rect(x, y, cw, rh, fill=fills[val], stroke=RULE),
                  text(x + cw/2, y + 31, val.upper(), 10, inks[val], "bold", "middle", MONO)]
    b += [text(40, 492, "Applicability is not design guidance: several 'yes' cells establish existence or validity without telling a practitioner what to build.",
               10.5, MUTED)]
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 14s
# The prospective audit is easy to misread as complete. This figure makes the
# temporal order and the one-way freeze gate explicit.

def fig14s() -> str:
    W, H = 1180, 420
    b = [text(40, 42, "Prospective validation sequence", 17, weight="bold"),
         text(40, 66, "Completed work is solid; prospective work is dashed. Nothing after the gate begins before the taxonomy and protocol freeze.",
              12, MUTED)]
    stages = [
        ("SEARCH", "8,296 retrieved", True, "#2f5d7c"),
        ("DEDUPLICATE", "6,486 corpus", True, "#2f5d7c"),
        ("PILOT", "40 records", False, "#8a4b2a"),
        ("FREEZE + REGISTER", "hard gate", False, "#8a4b2a"),
        ("SCREEN + EXTRACT", "two coders", False, "#4f6b2f"),
        ("A1-A5 + REPRO", "paper 2", False, "#6b4a7c"),
    ]
    x, y, w, h, gap = 40, 125, 160, 90, 30
    for i, (title, sub, done, col) in enumerate(stages):
        xx = x + i * (w + gap)
        b += [rect(xx, y, w, h, fill="#ffffff" if done else "#fbfaf8", stroke=col,
                   sw=2 if title == "FREEZE + REGISTER" else 1.5, dash=None if done else "5 4"),
              text(xx + w/2, y + 35, title, 10, col, "bold", "middle", MONO),
              text(xx + w/2, y + 60, sub, 10.5, INK, "normal", "middle")]
        if i < len(stages) - 1:
            ax1, ax2, ay = xx + w, xx + w + gap, y + h/2
            b += [line(ax1, ay, ax2 - 8, ay, INK, 1.5),
                  f'<path d="M {ax2-8} {ay-4} L {ax2} {ay} L {ax2-8} {ay+4} Z" fill="{INK}"/>']
    gatex = x + 3 * (w + gap) - 15
    b += [line(gatex, 100, gatex, 255, "#8a4b2a", 3),
          text(gatex, 278, "NO EXTRACTION BEFORE THIS LINE", 10, "#8a4b2a", "bold", "middle", MONO),
          rect(170, 320, 840, 54, fill="#f7f2ee", stroke="#8a4b2a", sw=1.2),
          text(590, 342, "Pilot records are discarded, the taxonomy is frozen, and the protocol receives a time-stamped registration.",
               10.5, INK, "normal", "middle"),
          text(590, 360, "A failed pilot triggers revision and a fresh pilot; it does not permit the gate to be bypassed.",
               10.5, MUTED, "normal", "middle")]
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 15s
# The same reported integer can count fundamentally different objects. This is
# the smallest visual statement of why per-node normalization cannot cross families.

def fig15s() -> str:
    W, H = 1180, 500
    b = [text(40, 42, "Reported counts and state dimension", 17, weight="bold"),
         text(40, 66, "The numeral can match while the object being counted changes. Capacity normalization must follow the family definition.",
              12, MUTED)]
    panels = [
        (40, "F1", "COUPLED VARIABLES", "500 physical nodes", "Bound applies directly", "#8a4b2a"),
        (420, "F2", "VIRTUAL SAMPLES", "500 time samples", "Independence depends on dynamics", "#2f5d7c"),
        (800, "F4", "MEASUREMENT PROBES", "500 probe locations", "Independence depends on correlation", "#6b4a7c"),
    ]
    for x, code, kind, value, note, col in panels:
        b += [rect(x, 104, 340, 300, fill="#ffffff", stroke=col, sw=1.8),
              text(x + 18, 130, code, 13, col, "bold", font=MONO),
              text(x + 322, 130, kind, 9, MUTED, "bold", "end", MONO)]
        if code == "F1":
            for row in range(4):
                for c in range(6):
                    cx, cy = x + 55 + c * 45, 178 + row * 38
                    if c < 5: b.append(line(cx + 6, cy, cx + 39, cy, RULE, 1))
                    if row < 3: b.append(line(cx, cy + 6, cx, cy + 32, RULE, 1))
                    b.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{col}"/>')
        elif code == "F2":
            b += [rect(x + 62, 164, 216, 94, fill="#f7f5f1", stroke=col, sw=1.5, rx=45)]
            for i in range(18):
                xx = x + 72 + i * 11.5
                b.append(line(xx, 251, xx, 263, col, 1))
            b += [text(x + 170, 200, "one delayed trajectory", 10.5, INK, "normal", "middle"),
                  text(x + 170, 222, "sampled many times", 10.5, MUTED, "normal", "middle")]
        else:
            b += [rect(x + 45, 160, 250, 112, fill="#f7f5f1", stroke=col, sw=1.3, rx=30)]
            for row in range(4):
                for c in range(7):
                    cx = x + 68 + c * 34 + (row % 2) * 8
                    cy = 181 + row * 23
                    b.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="{col}"/>')
            b += [line(x + 88, 175, x + 140, 240, RULE, 1), line(x + 140, 240, x + 245, 188, RULE, 1)]
        b += [text(x + 170, 310, value, 14, col, "bold", "middle"),
              text(x + 170, 336, note, 10.5, INK, "normal", "middle"),
              text(x + 170, 372, "Same reported numeral", 9.5, MUTED, "normal", "middle", MONO)]
    b += [line(210, 430, 970, 430, INK, 1.5),
          text(590, 454, "500  !=  500  !=  500", 14, INK, "bold", "middle", MONO),
          text(590, 478, "Compare within a family, or justify the effective independent dimension.", 11, MUTED, "normal", "middle")]
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 16s
# A compact key for the benchmark chapter: two reported scores become comparable
# only after the surrounding qualifiers align.

def fig16s() -> str:
    W, H = 1120, 520
    b = [text(40, 42, "Conditions for quantitative comparison", 17, weight="bold"),
         text(40, 66, "A score is comparable only when the fields that give it meaning align. A matching numeral is not enough.", 12, MUTED)]
    fields = [
        ("ARCHITECTURE", "Family + subclass", "#8a4b2a"),
        ("TASK", "Complete parameterization", "#2f5d7c"),
        ("METRIC", "Definition + normalization", "#4f6b2f"),
        ("STATISTIC", "Mean / best + dispersion", "#6b4a7c"),
        ("BOUNDARY", "System boundary when relevant", "#7a6840"),
    ]
    b += [rect(40, 106, 170, 332, fill="#f7f5f1", stroke=RULE),
          text(125, 136, "RECORD A", 11, INK, "bold", "middle", MONO),
          rect(910, 106, 170, 332, fill="#f7f5f1", stroke=RULE),
          text(995, 136, "RECORD B", 11, INK, "bold", "middle", MONO)]
    for i, (name, meaning, col) in enumerate(fields):
        y = 112 + i * 64
        b += [rect(242, y, 636, 48, fill="#ffffff", stroke=col, sw=1.4),
              text(262, y + 29, name, 10, col, "bold", font=MONO),
              text(660, y + 29, meaning, 11, INK, "normal", "middle"),
              f'<circle cx="{220}" cy="{y+24}" r="5" fill="{col}"/>',
              f'<circle cx="{900}" cy="{y+24}" r="5" fill="{col}"/>',
              line(225, y + 24, 242, y + 24, col, 1.3),
              line(878, y + 24, 895, y + 24, col, 1.3)]
    b += [rect(318, 458, 484, 42, fill="#eef2f5", stroke="#2f5d7c", sw=1.5),
          text(560, 484, "All five align  ->  the difference can describe the systems", 11, INK, "bold", "middle")]
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 17s
# RC-REPORT has a universal core and an additive physical track. Showing the
# conditional branch prevents readers from treating hardware-only items as universal.

def fig17s() -> str:
    W, H = 1140, 560
    b = [text(40, 42, "Reporting requirements by study type", 17, weight="bold"),
         text(40, 66, "Every paper receives the common track. Physical evidence at E2 or above adds a second disclosure layer.", 12, MUTED)]
    b += [rect(70, 108, 680, 384, fill="#f5f7f8", stroke="#2f5d7c", sw=2),
          text(94, 136, "COMMON TRACK  /  EVERY RESERVOIR-COMPUTING PAPER", 11, "#2f5d7c", "bold", font=MONO)]
    common = [
        ("01", "Architecture"), ("02", "State dimension + kind"),
        ("03", "Reservoir specification"), ("04", "Evaluation protocol"),
        ("05", "Dispersion"), ("06", "Fair trivial baseline"),
        ("07", "Benchmark + metric definition"), ("08", "Artefact status"),
    ]
    for i, (num, label) in enumerate(common):
        col, row = i % 2, i // 2
        x, y = 94 + col * 320, 166 + row * 66
        b += [rect(x, y, 292, 48, fill="#ffffff", stroke=RULE),
              text(x + 16, y + 29, num, 9.5, "#2f5d7c", "bold", font=MONO),
              text(x + 162, y + 29, label, 10.5, INK, "normal", "middle")]
    b += [rect(790, 108, 280, 384, fill="#f7f2ee", stroke="#8a4b2a", sw=2),
          text(930, 136, "PHYSICAL TRACK", 11, "#8a4b2a", "bold", "middle", MONO),
          text(930, 154, "Add when evidence >= E2", 9.5, MUTED, "bold", "middle")]
    physical = ["Evidence tier", "Drift + recalibration", "Acquisition chain", "Device variability", "Efficiency boundary"]
    for i, label in enumerate(physical):
        y = 178 + i * 58
        b += [rect(812, y, 236, 42, fill="#ffffff", stroke="#8a4b2a", sw=1),
              text(830, y + 26, f"P{i+1}", 9, "#8a4b2a", "bold", font=MONO),
              text(930, y + 26, label, 10, INK, "normal", "middle")]
    b += [line(750, 300, 782, 300, "#8a4b2a", 2),
          f'<path d="M 782 295 L 790 300 L 782 305 Z" fill="#8a4b2a"/>',
          text(570, 530, "The second track extends the first; it never replaces it.", 11, MUTED, "normal", "middle")]
    return svg(W, H, "\n".join(b))



# ---------------------------------------------------------------- figure 18s
# Breakthroughs timeline. Colour carries the architecture family, so the figure
# doubles as evidence for the paper's own claim: every family recurs across the
# window and across substrates rather than belonging to one era or one material.
#
# EVERY milestone below is keyed to a bibliography entry and its year is the
# year in that entry. Nothing on this figure is dated from memory. A timeline
# with an invented date in a paper about lost provenance would be indefensible,
# so `selftest` re-reads paper/references.bib and fails on any mismatch.

TIMELINE_CATEGORIES = [
    ("T",  "Theory and bounds",        "#4a4a5c"),
    ("F1", "Addressable node",        "#244a73"),
    ("F2", "Delay embedded",           "#426b8f"),
    ("F3", "Explicit feature",         "#55703f"),
    ("F4", "Distributed medium",       "#385c63"),
    ("M",  "Reviews, tools, critique", "#7a5c4a"),
]

# (year, label, category, [bibliography keys the year is taken from])
TIMELINE = [
    (2001, "Echo state network", "T", ["Jaeger2001"]),
    (2002, "Liquid state machine", "T", ["Maass2002"]),
    (2002, "Memory-capacity bound", "T", ["Jaeger2002"]),
    (2003, "Liquid medium", "F4", ["Fernando2003"]),
    (2004, "Chaotic prediction", "T", ["JaegerHaas2004"]),
    (2011, "Single-node delay loop", "F2", ["Appeltant2011"]),
    (2011, "Morphological computation", "F4", ["Hauser2011"]),
    (2012, "Processing capacity", "T", ["Dambre2012"]),
    (2012, "Optoelectronic loops", "F2",
     ["Larger2012", "Paquot2012", "Duport2012"]),
    (2013, "Fast photonic loop", "F2", ["Brunner2013"]),
    (2014, "Waveguide array", "F1", ["Vandoorne2014"]),
    (2015, "Soft-body computing", "F4", ["Nakajima2015"]),
    (2017, "Dynamic memristor array", "F1", ["Du2017"]),
    (2017, "Spintronic oscillators", "F2", ["Torrejon2017"]),
    (2017, "High-speed photonics", "F2", ["Larger2017"]),
    (2018, "Fading-memory universality", "T", ["Grigoryeva2018"]),
    (2018, "Spatiotemporal prediction", "T", ["Pathak2018"]),
    (2019, "Physical reservoir review", "M", ["Tanaka2019"]),
    (2019, "CHARC characterization", "M", ["Dale2019"]),
    (2021, "Next-generation RC", "F3", ["Gauthier2021"]),
    (2021, "NARMA-10 pathology", "T", ["Kubota2021"]),
    (2021, "Organic electrochemical", "F4", ["Cucchi2021"]),
    (2022, "Spin ice, nanowire mesh", "F4",
     ["Gartside2022", "Milano2022"]),
    (2022, "Practical tutorial", "M", ["Cucchi2022"]),
    (2023, "Neurons and organoids", "F4", ["Sumi2023", "Cai2023"]),
    (2024, "Deployment-gap synthesis", "M", ["Yan2024"]),
    (2025, "Benchmark critique", "M", ["Wringe2025"]),
    (2026, "RCbench framework", "M", ["RCbench2026"]),
]

CHAR_W = 0.62          # same estimate check_geometry uses, so layout and check agree


def fig18s() -> str:
    """Milestone timeline, split into two eras so the labels stay readable.

    Canvas geometry is chosen for the PRINTED size, not the screen. LaTeX draws
    this at \\linewidth, about 390pt, so a wide canvas shrinks the type by a
    factor of three and the labels become unreadable on paper. At W=700 the
    reproduction scale is about 0.56, which puts a 13-unit label at ~7pt.

    One axis spanning 2001-2026 was tried first. Descriptive labels are wide
    enough that a pill covered eight years of the axis, so a milestone no longer
    read as belonging to its own date. Two half-length axes give each year twice
    the room and keep the association tight.
    """
    W = 700
    X0, X1 = 58, 672
    FS = 13                                    # pill label size
    PAD, GAP = 11, 8                           # inside pill, between pills
    LANE_H, LANE_1 = 34, 36                    # lane pitch, first lane offset
    SPLIT = 2015                               # first year of the second panel
    top_pad, axis_pad, panel_gap, legend_h = 18, 34, 30, 92

    colours = {c: col for c, _, col in TIMELINE_CATEGORIES}

    def layout(items, lo, hi):
        """Pack one panel; returns placements plus how far they reach each way."""
        def X(year):
            return X0 + (year - lo) * (X1 - X0) / (hi - lo)

        used = {True: [], False: []}
        placed = []
        for i, (year, label, cat, _keys) in enumerate(items):
            lines = wrap(label, 26)
            wpx = max(len(l) for l in lines) * FS * CHAR_W + 2 * PAD
            hpx = 23 + 16 * (len(lines) - 1)
            cx, above = X(year), i % 2 == 0
            lane = 0
            while any(l == lane and not (cx + wpx / 2 + GAP < s or
                                         cx - wpx / 2 - GAP > e)
                      for l, s, e in used[above]):
                lane += 1
            used[above].append((lane, cx - wpx / 2, cx + wpx / 2))
            placed.append((cx, wpx, hpx, lines, colours[cat], above, lane))
        up = max((l * LANE_H + h for _, _, h, _, _, a, l in placed if a), default=0)
        dn = max((l * LANE_H + h for _, _, h, _, _, a, l in placed if not a), default=0)
        return placed, X, up, dn

    early = [m for m in TIMELINE if m[0] < SPLIT]
    late = [m for m in TIMELINE if m[0] >= SPLIT]
    pa, Xa, up_a, dn_a = layout(early, 2000, SPLIT)
    pb, Xb, up_b, dn_b = layout(late, SPLIT - 1, 2027)

    ay_a = top_pad + LANE_1 + up_a
    ay_b = ay_a + axis_pad + LANE_1 + dn_a + panel_gap + LANE_1 + up_b
    H = int(ay_b + axis_pad + LANE_1 + dn_b + legend_h)

    b = []

    def draw(placed, X, ay, lo, hi, up, dn):
        top = ay - LANE_1 - up - 8
        bot = ay + LANE_1 + dn + 8
        for y in range(lo + 1, hi):
            gx = X(y)
            b.append(f'<line x1="{gx:.1f}" y1="{top:.1f}" x2="{gx:.1f}" '
                     f'y2="{bot:.1f}" stroke="#eef1f4" stroke-width="1"/>')
        b.append(line(X0 - 12, ay, X1 + 8, ay, INK, 2.4))
        for y in range(lo + 1, hi):
            gx, major = X(y), y % 5 == 0
            b.append(f'<circle cx="{gx:.1f}" cy="{ay}" r="{3.4 if major else 2.4}" '
                     f'fill="{MUTED if major else RULE}"/>')
            b.append(text(gx, ay + 24, str(y), 12 if major else 10.5,
                          INK if major else MUTED,
                          "bold" if major else "normal", "middle"))
        for cx, wpx, hpx, lines, col, above, lane in placed:
            if above:
                py = ay - LANE_1 - lane * LANE_H - hpx
                leader_y = py + hpx
            else:
                py = ay + LANE_1 + lane * LANE_H
                leader_y = py
            px = min(max(cx - wpx / 2, 4), W - wpx - 4)
            b.append(f'<line x1="{cx:.1f}" y1="{ay}" x2="{cx:.1f}" y2="{leader_y:.1f}" '
                     f'stroke="{col}" stroke-width="1.1"/>')
            b.append(f'<circle cx="{cx:.1f}" cy="{ay}" r="3.8" fill="{col}"/>')
            b.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{wpx:.1f}" '
                     f'height="{hpx:.1f}" rx="{hpx / 2:.1f}" fill="{col}" stroke="none"/>')
            for j, ln in enumerate(lines):
                b.append(text(px + wpx / 2, py + 16 + j * 16, ln, FS, "#ffffff",
                              "bold", "middle"))

    draw(pa, Xa, ay_a, 2000, SPLIT, up_a, dn_a)
    draw(pb, Xb, ay_b, SPLIT - 1, 2027, up_b, dn_b)

    # ---- legend, wrapped onto as many rows as the canvas needs
    entries = []
    for code, name, col in TIMELINE_CATEGORIES:
        lab = name if code in ("T", "M") else f"{code}  {name}"
        entries.append((lab, col, 20 + len(lab) * 12 * CHAR_W + 16))
    rows, cur, cur_w = [], [], 0.0
    for e in entries:
        if cur and cur_w + e[2] > (X1 - X0) + 24:
            rows.append(cur)
            cur, cur_w = [], 0.0
        cur.append(e)
        cur_w += e[2]
    if cur:
        rows.append(cur)

    ly = H - legend_h + 20
    for row in rows:
        lx = X0 - 12
        for lab, col, w in row:
            b.append(f'<rect x="{lx:.1f}" y="{ly - 10:.1f}" width="14" height="14" '
                     f'rx="7" fill="{col}" stroke="none"/>')
            b.append(text(lx + 20, ly + 1.5, lab, 12, INK))
            lx += w
        ly += 20

    b.append(text(X0 - 12, H - 12,
                  "Years are taken from the cited primary sources; colour marks "
                  "the architecture family.", 11, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 19s
# Citation lineage of the NARMA-10 trivial-predictor baseline: the manuscript's
# most concrete provenance failure, drawn as the chain it is. Values and sources
# are those verified in benchmark-thresholds.md anchors 1-2 (D8) and reported in
# Section 8.2; nothing here is dated or valued from memory.

def fig19s() -> str:
    """Three published shift-register baselines for NARMA-10, and this project's record.

    Redrawn 2026-08-27 after the primaries were re-read. Appeltant (2011) and Vinckier
    (2015) state one result in two metrics, and Vinckier performs the conversion
    explicitly. Vidamour et al. (2023) state ~0.434 NMSE for their own shift register
    on a NARMA variant with autocorrelated inputs, with no citation: a different
    quantity, not a relabelling. The earlier version of this figure drew an arrow from
    Vinckier to Vidamour labelled "metric label lost" on the strength of a misquoted
    "~0.4"; that arrow was this project's error and is now the dashed box.
    """
    W, H = 700, 600
    b = []
    bw, bh = 296, 100
    lx, rx = 36, 368

    def box(x, y, title, role, val, col, dash=None, fill="#ffffff"):
        return [rect(x, y, bw, bh, fill=fill, stroke=col, sw=1.8, dash=dash),
                text(x + bw / 2, y + 24, title, 13, INK, "bold", "middle"),
                text(x + bw / 2, y + 42, role[0], 10.5, MUTED, "normal", "middle"),
                text(x + bw / 2, y + 56, role[1], 10.5, MUTED, "normal", "middle"),
                text(x + bw / 2, y + 84, val, 16, col, "bold", "middle", MONO)]

    def arrow_down(x, y1, y2, col):
        return [line(x, y1, x, y2 - 9, col, 1.8),
                f'<path d="M {x-5} {y2-9} L {x} {y2} L {x+5} {y2-9} Z" fill="{col}"/>']

    b += box(lx, 36, "Appeltant et al. 2011",
             ("primary source; NARMA-10,", "independent uniform input"), "0.4 NRMSE", "#244a73")
    b += arrow_down(lx + bw / 2, 136, 196, "#4f6b58")
    b += [text(lx + bw / 2 + 16, 160, "explicit conversion", 11.5, "#4f6b58", "bold"),
          text(lx + bw / 2 + 16, 176, "0.4^2 = 0.16", 11.5, INK, "normal", font=MONO)]
    b += box(lx, 196, "Vinckier et al. 2015",
             ("same result, converted;", "attributes it to Appeltant"), "0.16 NMSE", "#244a73")
    b += box(rx, 116, "Vidamour et al. 2023",
             ("own shift-register baseline; NARMA-N", "with autocorrelated input; no citation"),
             "~0.434 NMSE", "#71643f")
    b += [text(rx + bw / 2, 236, "a different quantity: input distribution and", 10.5, MUTED,
               "normal", "middle"),
          text(rx + bw / 2, 250, "normalization differ; not a conversion of 0.4 NRMSE", 10.5,
               MUTED, "normal", "middle")]

    # this project's record
    ry = 336
    b += [rect(lx, ry, rx + bw - lx, 98, fill="#f2eceb", stroke="#7a4a42", sw=1.5, dash="6,4"),
          text(350, ry + 22, "This project's record, first two verification passes", 12.5, INK,
               "bold", "middle"),
          text(350, ry + 42, "quoted the third value as \"~0.4 NMSE\", read it as Appeltant's "
                             "0.4 relabelled,", 10.5, MUTED, "normal", "middle"),
          text(350, ry + 57, "and merged it with the first statement. Both readings were "
                             "wrong and were found", 10.5, MUTED, "normal", "middle"),
          text(350, ry + 72, "only when the primary was re-read during revision "
                             "(Section 8.2).", 10.5, MUTED, "normal", "middle"),
          text(350, ry + 90, "recorded: ~0.4 \"NMSE\"  |  primary: ~0.434 NMSE", 11.5,
               "#7a4a42", "bold", "middle", MONO)]

    cy = 486
    b += [rect(36, cy - 30, 628, 60, fill="#edf3f7", stroke="#244a73", sw=1.5),
          text(350, cy - 8, "Read as bare NMSE values, two published shift-register baselines "
                            "for", 12, INK, "bold", "middle"),
          text(350, cy + 10, "\"NARMA-10\" differ by a factor of 2.7; the qualifiers that "
                             "separate them do not travel.", 12, INK, "bold", "middle")]
    b.append(text(36, 552, "Values as read in the primary texts (Section 8.2); the record row "
                           "is from this project's deviation log.", 9.5, MUTED))
    b.append(text(36, 567, "Appeltant et al. 2011; Vinckier et al. 2015, section 4.B; Vidamour "
                           "et al. 2023, text accompanying their Fig. 5.", 9.5, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 20s
# Substrate x architecture-family grid of the twelve worked examples in Table 12.
# Rows are the Table 4 substrate vocabulary, columns the four families. The point
# reads without the prose: a row with entries in two columns is one substrate
# producing two architectures; a column spanning several rows is one architecture
# realised in several substrates. Every placement is a Table 12 assignment; nothing
# is classified for the figure. Empty rows are shown because the absence of a
# worked example is information the reader should have.

GRID_ROWS = [
    "Digital simulation", "Digital hardware", "Analogue electronic", "Photonic",
    "Spintronic or magnetic", "Memristive or ionic", "Mechanical",
    "Biological or organic", "Quantum",
]
GRID_COLS = [("F1", "Addressable node"), ("F2", "Delay embedded"),
             ("F3", "Explicit feature"), ("F4", "Distributed medium")]
# (substrate row, family column, system, first author and year, marker)
GRID_ENTRIES = [
    ("Digital simulation", "F1", "Echo state network", "Jaeger 2001", ""),
    ("Digital simulation", "F1", "Liquid state machine", "Maass 2002", ""),
    ("Digital simulation", "F1", "Deep reservoir", "Gallicchio 2017", ""),
    ("Digital simulation", "F3", "Polynomial features", "Gauthier 2021", "flagged"),
    ("Analogue electronic", "F2", "Electronic delay loop", "Appeltant 2011", ""),
    ("Photonic", "F2", "Laser delay loop", "Brunner 2013", ""),
    ("Photonic", "F1", "Waveguide array", "Vandoorne 2014", ""),
    ("Spintronic or magnetic", "F2", "Spin-torque oscillator", "Torrejon 2017", ""),
    ("Memristive or ionic", "F1", "Memristor array", "Du 2017", ""),
    ("Memristive or ionic", "F4", "Nanowire network", "Milano 2022", ""),
    ("Mechanical", "F4", "Soft silicone body", "Nakajima 2015", ""),
    ("Biological or organic", "F4", "Neuronal culture", "Sumi 2023", "subclass gap"),
]


def fig20s() -> str:
    W = 700
    LABEL_W, GX0, COLW = 168, 176, 128          # row-label column, grid origin, column width
    ENTRY_H, PAD = 24, 10
    HEAD_Y, HEAD_H = 26, 46
    GY0 = HEAD_Y + HEAD_H + 6
    FS_ENTRY, FS_SUB = 8.8, 8.2
    cells: dict[tuple[str, str], list] = {}
    for row, col, sysname, ref, marker in GRID_ENTRIES:
        cells.setdefault((row, col), []).append((sysname, ref, marker))
    row_h = {}
    for r in GRID_ROWS:
        n = max([len(cells.get((r, c), [])) for c, _ in GRID_COLS] + [1])
        row_h[r] = n * ENTRY_H + PAD
    split_rows = {r for r in GRID_ROWS
                  if len({c for (rr, c) in cells if rr == r}) > 1}

    b = []
    # column headers
    for i, (code, name) in enumerate(GRID_COLS):
        x = GX0 + i * COLW
        col = FAMILY_INK[code]
        dash = "5,4" if code == "F3" else None
        b.append(rect(x + 3, HEAD_Y, COLW - 6, HEAD_H, fill="#ffffff", stroke=col, sw=1.4,
                      dash=dash))
        b.append(text(x + COLW / 2, HEAD_Y + 18, code, 11, col, "bold", "middle", MONO))
        b.append(text(x + COLW / 2, HEAD_Y + 34, name, 9.5, INK, "bold", "middle"))
    # rows
    y = GY0
    for r in GRID_ROWS:
        h = row_h[r]
        if r in split_rows:
            b.append(rect(12, y, GX0 + 4 * COLW - 12, h, fill="#edf3f7", stroke="none", rx=3))
        b.append(line(12, y, GX0 + 4 * COLW, y, RULE, 0.8))
        b.append(text(LABEL_W, y + h / 2 + 3.5, r, 9.5, INK, "bold", "end"))
        present = [c for c, _ in GRID_COLS if (r, c) in cells]
        if not present:
            b.append(text(GX0 + 2 * COLW, y + h / 2 + 3, "no worked example in Table 6",
                          8.5, MUTED, "normal", "middle"))
        for i, (code, _) in enumerate(GRID_COLS):
            x = GX0 + i * COLW
            entries = cells.get((r, code), [])
            ey = y + PAD / 2 + 10
            for sysname, ref, marker in entries:
                col = FAMILY_INK[code]
                b.append(rect(x + 8, ey - 7.5, 7, 7, fill=col, stroke="none", rx=1.5))
                b.append(text(x + 20, ey, sysname, FS_ENTRY, INK, "bold"))
                tag = {"ambiguous": " *", "subclass gap": " (gap)", "flagged": " (flag)"}.get(marker, "")
                b.append(text(x + 20, ey + 10.5, ref + tag, FS_SUB, MUTED))
                ey += ENTRY_H
        y += h
    b.append(line(12, y, GX0 + 4 * COLW, y, RULE, 0.8))
    for i in range(5):
        x = GX0 + i * COLW
        b.append(line(x, GY0, x, y, RULE, 0.6))

    notes = [
        "Shaded rows hold one substrate in two columns: the photonic and the memristive-ionic "
        "examples realise two architectures each.",
        "The F2 column spans electronic, photonic, and spintronic rows: one architecture across "
        "substrates. F3 is a flagged coverage class (flag).",
        "Placements are the Table 6 assignments. * F2/F4 ambiguity recorded; (gap) no current "
        "subclass fits.",
    ]
    ny = y + 22
    for n in notes:
        for ln in wrap(n, 108):
            b.append(text(12, ny, ln, 9.2, MUTED))
            ny += 13
    H = int(ny + 4)
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 21s
# The valid-prediction-time statement, drawn as the sequence it went through: a
# recorded value, a correction, and the discovery that the correction had been made
# against a misidentified source. Companion to fig19s. Wording follows Section 8.2
# and the deviation log (D10, D15); no date or value here is from memory.

def fig21s() -> str:
    W, H = 700, 560
    b = []
    bx, bw, bh = 110, 480, 96
    boxes = [
        (36, "Recorded during scoping", "secondary attribution; primary not yet read",
         "baseline 2.87 'Lyapunov times'", MUTED),
        (206, "First verification pass", "unit error found in the attributed source",
         "2.87 model time units = about 2.6 Lyapunov times", "#71643f"),
        (376, "Second, independent check", "bibliography entry had fused two papers; "
         "the sentence is in neither", "baseline removed; no value substituted", "#7a4a42"),
    ]
    for by, title, role, val, col in boxes:
        b += [rect(bx, by, bw, bh, fill="#ffffff", stroke=col, sw=1.8),
              text(bx + bw / 2, by + 24, title, 13, INK, "bold", "middle"),
              text(bx + bw / 2, by + 43, role, 10.5, MUTED, "normal", "middle"),
              text(bx + bw / 2, by + 74, val, 13, col, "bold", "middle", MONO)]

    def arrow_down(y1, y2, col):
        x = bx + bw / 2
        return [line(x, y1, x, y2 - 9, col, 1.8),
                f'<path d="M {x-5} {y2-9} L {x} {y2} L {x+5} {y2-9} Z" fill="{col}"/>']

    b += arrow_down(132, 206, "#71643f")
    b += [text(bx + bw / 2 + 18, 160, "unit corrected", 11.5, "#71643f", "bold"),
          text(bx + bw / 2 + 18, 176, "recorded as a completed correction", 10.5, MUTED)]
    b += arrow_down(302, 376, "#7a4a42")
    b += [text(bx + bw / 2 + 18, 330, "source misidentified", 11.5, "#7a4a42", "bold"),
          text(bx + bw / 2 + 18, 346, "found by a reader who had not written the entry",
               10.5, MUTED)]

    cy = 510
    b += [rect(36, cy - 28, 628, 56, fill="#f2eceb", stroke="#7a4a42", sw=1.5),
          text(350, cy - 6, "A value can pass a verification pass, acquire a documented",
               12.5, INK, "bold", "middle"),
          text(350, cy + 12, "correction, and remain unsourced.", 12.5, INK, "bold", "middle")]
    b.append(text(36, 552, "Sequence as recorded in the released deviation log and reported in "
                           "Section 8.2.", 10.5, MUTED))
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 22s
# The candidate corpus as a picture: records per year split by access status, and
# the closed share of each substrate vocabulary against the corpus baseline. Both
# panels are computed from the frozen corpus with the screening script's own
# terminology proxy, so the figure reproduces Section 8.1 rather than restating it.
# It is a candidate corpus before screening, and the caption and notes say so.

CLOSED_INK, OPEN_INK = "#6f4e37", "#4f6b58"
VOCAB_LABELS = {
    "memristive-ionic": "Memristive or ionic", "photonic": "Photonic",
    "analog-electronic": "Analogue electronic", "digital-hardware": "Digital hardware",
    "mechanical-soft": "Mechanical", "biological-organic": "Biological or organic",
    "spintronic-magnetic": "Spintronic or magnetic", "quantum": "Quantum",
}


def _corpus_rows() -> list[dict]:
    p = Path("data/screening/corpus_deduped.csv")
    if not p.exists():
        raise SystemExit(
            "fig22s needs data/screening/corpus_deduped.csv, which is missing.\\n"
            "  Run scripts/dedupe.py to rebuild it from the frozen exports."
        )
    with p.open(newline="", encoding="utf-8-sig") as fh:
        return [r for r in csv.DictReader(fh) if not r.get("dup_of")]


def fig22s() -> str:
    import screen  # scripts/ is on sys.path when this file runs; same proxy as Section 8.1
    from collections import Counter
    rows = _corpus_rows()
    total = len(rows)
    closed_share = sum(1 for r in rows if r.get("is_oa") != "1") / total
    years = [str(y) for y in range(2019, 2027)]
    open_by, closed_by = Counter(), Counter()
    for r in rows:
        y = (r.get("year") or "").strip()
        (open_by if r.get("is_oa") == "1" else closed_by)[y] += 1
    vocab: dict[str, list[int]] = {}
    for r in rows:
        idx = 0 if r.get("is_oa") == "1" else 1
        for lab in screen.substrate_hits(f"{r.get('title','')} {r.get('abstract','')}"):
            vocab.setdefault(lab, [0, 0])[idx] += 1
    shares = sorted(((c / (o + c), lab, o + c) for lab, (o, c) in vocab.items()), reverse=True)

    W, H = 700, 416
    b = []
    # panel a: stacked bars by year
    b.append(text(30, 24, "a", 12, INK, "bold"))
    b.append(text(46, 24, "Candidate records by year and access status", 11, INK, "bold"))
    x0, base, bw, gap = 52, 300, 26, 10
    peak = max(open_by[y] + closed_by[y] for y in years)
    scale = 190 / peak
    for i, y in enumerate(years):
        x = x0 + i * (bw + gap)
        hc, ho = closed_by[y] * scale, open_by[y] * scale
        b.append(rect(x, base - hc, bw, hc, fill=CLOSED_INK, stroke="none", rx=1))
        b.append(rect(x, base - hc - ho, bw, ho, fill=OPEN_INK, stroke="none", rx=1))
        b.append(text(x + bw / 2, base - hc - ho - 5, f"{open_by[y] + closed_by[y]:,}",
                      8.2, INK, "normal", "middle"))
        b.append(text(x + bw / 2, base + 14, y, 9, MUTED, "normal", "middle"))
        if y == "2026":
            b.append(text(x + bw / 2, base + 25, "to June", 7.8, MUTED, "normal", "middle"))
    b.append(line(x0 - 8, base, x0 + 8 * (bw + gap) - gap + 8, base, INK, 1.2))
    n_open = sum(open_by.values()); n_closed = sum(closed_by.values())
    b += [rect(52, 334, 9, 9, fill=OPEN_INK, stroke="none", rx=1),
          text(66, 342, f"openly retrievable ({n_open:,})", 9, INK),
          rect(200, 334, 9, 9, fill=CLOSED_INK, stroke="none", rx=1),
          text(214, 342, f"closed, metadata only ({n_closed:,})", 9, INK)]
    # panel b: closed share by vocabulary
    b.append(text(380, 24, "b", 12, INK, "bold"))
    b.append(text(396, 24, "Closed share by substrate vocabulary", 11, INK, "bold"))
    lx, bx0, blen, pitch = 505, 512, 160, 27
    y = 46
    # The label carries the vocabulary's total tagged-record count, so a share is
    # never read with more precision than its base supports (round-3 review).
    for share, lab, n in shares:
        b.append(text(lx, y + 12, f"{VOCAB_LABELS.get(lab, lab)} ({n:,})",
                      9, INK, "normal", "end"))
        b.append(rect(bx0, y, share * blen, 16, fill=CLOSED_INK, stroke="none", rx=1))
        b.append(text(bx0 + share * blen + 4, y + 12, f"{share:.1%}", 8.5, INK))
        y += pitch
    xb = bx0 + closed_share * blen
    b.append(f'<line x1="{xb}" y1="40" x2="{xb}" y2="{y - 6}" stroke="{INK}" '
             f'stroke-width="1" stroke-dasharray="4,3"/>')
    b.append(text(xb, y + 6, f"corpus {closed_share:.1%} closed", 8.5, INK, "normal", "middle"))
    note_b = ("Title-and-abstract proxy of the screening script; abstracts are present for "
              f"{sum(1 for r in rows if r.get('is_oa') == '1' and r.get('has_abstract') == '1') / n_open:.1%} "
              f"of open and {sum(1 for r in rows if r.get('is_oa') != '1' and r.get('has_abstract') == '1') / n_closed:.1%} "
              "of closed records, so closed shares are lower bounds.")
    ny = y + 24
    for ln in wrap(note_b, 56):
        b.append(text(380, ny, ln, 8.5, MUTED))
        ny += 12
    note_a = (f"Candidate corpus of {total:,} deduplicated records before screening. The Semantic "
              "Scholar coverage check indicates an indexing shortfall concentrated in 2025 and "
              "2026, so the two most recent bars understate those years.")
    ny = 372
    for ln in wrap(note_a, 118):
        b.append(text(30, ny, ln, 8.5, MUTED))
        ny += 12
    return svg(W, H, "\n".join(b))


# ---------------------------------------------------------------- figure 23s
# The manuscript's Table 10 as a picture: four published NARMA-10 results plotted
# against the two published shift-register baselines, so the verdict reversal is
# visible without scanning two ratio columns (round-3 review, suggested figure 3).
# Every value below also appears verbatim in the Section 8.2 source, and selftest
# fails if the two ever diverge; nothing here is valued from memory.

# (label, sublabel, value, plus/minus dispersion or None, admissible baseline key)
FIG23_RESULTS = [
    ("Paquot et al. 2012", "50 variables, experiment and simulation",
     0.168, 0.015, "standard"),
    ("Vinckier et al. 2015", "50 variables, experiment", 0.107, 0.012, "standard"),
    ("Vinckier et al. 2015", "300 variables, experiment", 0.0484, 0.0095, "standard"),
    ("Vidamour et al. 2023", "peak, autocorrelated input; no dispersion reported",
     0.359, None, "variant"),
]
FIG23_BASELINES = {"standard": (0.16, "0.16 NMSE", "shift register,",
                                "independent uniform input", "#244a73"),
                   "variant": (0.434, "~0.434 NMSE", "shift register,",
                               "autocorrelated variant", "#71643f")}


def fig23s() -> str:
    W, H = 700, 470
    X0, X1 = 250, 660                       # plot window
    XMAX = 0.5                              # NMSE axis maximum
    b = []

    def X(v: float) -> float:
        return X0 + v / XMAX * (X1 - X0)

    ay = 330                                # axis line
    # baselines first, so the result rows draw over them
    for key, (v, lab, l1, l2, col) in FIG23_BASELINES.items():
        x = X(v)
        b.append(f'<line x1="{x:.1f}" y1="60" x2="{x:.1f}" y2="{ay}" '
                 f'stroke="{col}" stroke-width="1.4" stroke-dasharray="5,4"/>')
        b.append(text(x, 30, lab, 11, col, "bold", "middle", MONO))
        b.append(text(x, 43, l1, 8.5, col, "normal", "middle"))
        b.append(text(x, 53, l2, 8.5, col, "normal", "middle"))

    # axis
    b.append(line(X0, ay, X1, ay, INK, 1.5))
    for t in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        x = X(t)
        b.append(line(x, ay, x, ay + 5, INK, 1))
        b.append(text(x, ay + 18, f"{t:.1f}", 9.5, MUTED, "normal", "middle"))
    b.append(text((X0 + X1) / 2, ay + 36, "reported NMSE", 10.5, MUTED,
                  "normal", "middle"))

    for i, (label, sub, v, disp, base) in enumerate(FIG23_RESULTS):
        y = 92 + i * 58
        col = FIG23_BASELINES[base][4]
        b.append(text(238, y - 4, label, 10.5, INK, "bold", "end"))
        b.append(text(238, y + 9, sub, 8.5, MUTED, "normal", "end"))
        if disp:
            xa, xb = X(v - disp), X(v + disp)
            b.append(line(xa, y, xb, y, col, 1.6))
            b.append(line(xa, y - 5, xa, y + 5, col, 1.6))
            b.append(line(xb, y - 5, xb, y + 5, col, 1.6))
        b.append(f'<circle cx="{X(v):.1f}" cy="{y}" r="5" fill="{col}"/>')
        b.append(text(X(v), y - 11, f"{v:g}", 9, col, "bold", "middle", MONO))

    notes = [
        "Dashed lines are the two published shift-register baselines; a result is "
        "admissible only against the baseline whose input distribution it shares "
        "(colour).",
        "Read against the wrong line the verdicts reverse: 0.168 is "
        "indistinguishable from the standard level yet would look 2.6 times better "
        "than the variant baseline, and 0.359 lies below the variant baseline yet "
        "above the standard one.",
        "Values and qualifiers as read from the primaries (Section 8.2, Table 12).",
    ]
    ny = 396
    for n in notes:
        for ln in wrap(n, 112):
            b.append(text(36, ny, ln, 9.2, MUTED))
            ny += 12.5
        ny += 3
    return svg(W, H, "\n".join(b))



# ---------------------------------------------------------------- figure 24s
#
# Evidence level and efficiency reporting across the twelve worked examples, drawn
# from the manuscript's Table 9 (Section 4.3). Added 2026-09-09 on a referee request
# for a visual form of the "efficiency reporting is sparse at every boundary" claim.
#
# The rows are the same twelve systems in the same order as the table, and the
# selftest holds them to it: every system name and every level plotted here must
# appear in the Section 4.3 source. A figure that drifted from its own table would
# be an instance of this paper's subject.
#
# `levels` is a list because evidence attaches to CLAIMS, not to papers: two of the
# twelve support one claim experimentally and another numerically, and a single
# marker per row would misstate one claim in each.
FIG24_SYSTEMS = [
    ("Echo state network",       "Jaeger2001",                  [0],    "none"),
    ("Liquid state machine",     "Maass2002",                   [0],    "none"),
    ("Deep reservoir",           "GallicchioMicheliPedrelli2017",[0],   "none"),
    ("Memristor array",          "Du2017",                      [2],    "qualitative"),
    ("Electronic delay loop",    "Appeltant2011",               [0, 3], "none"),
    ("Laser delay loop",         "Brunner2013",                 [3],    "quantified"),
    ("Waveguide array",          "Vandoorne2014",               [2],    "qualitative"),
    ("Polynomial features",      "Gauthier2021",                [0],    "none"),
    ("Spin-torque oscillator",   "Torrejon2017",                [3],    "qualitative"),
    ("Nanowire network",         "Milano2022",                  [1, 3], "qualitative"),
    ("Soft silicone body",       "Nakajima2015",                [3],    "none"),
    ("Cultured neuronal network","Sumi2023",                    [3],    "none"),
]

FIG24_EFF = {
    "none":        ("None reported",                      "#ffffff", RULE),
    "qualitative": ("Stated qualitatively",               "#e8eef3", "#607f99"),
    "quantified":  ("Quantified, partial boundary", "#244a73", "#244a73"),
}


def fig24s() -> str:
    W = 700
    LABEL_W, GX0, COLW = 186, 194, 45
    ROW_H, HEAD_Y, HEAD_H = 22, 26, 34
    GY0 = HEAD_Y + HEAD_H + 4
    EFFX = GX0 + 6 * COLW + 22

    b = []
    for lv in range(6):
        x = GX0 + lv * COLW
        demonstrated = lv <= 3
        b.append(rect(x + 2, HEAD_Y, COLW - 4, HEAD_H, fill="#ffffff",
                      stroke=RULE if demonstrated else "#c9d2da", sw=1.1,
                      dash=None if demonstrated else "4,3"))
        b.append(text(x + COLW / 2, HEAD_Y + 15, f"E{lv}", 10, INK if demonstrated else MUTED,
                      "bold", "middle", MONO))
        b.append(text(x + COLW / 2, HEAD_Y + 28,
                      ["sim.", "device", "traces", "live", "packaged", "field"][lv],
                      7.6, MUTED, "normal", "middle"))
    b.append(text(EFFX + 80, HEAD_Y + 21, "Efficiency claim", 9.5, INK, "bold", "middle"))

    y = GY0
    for i, (name, key, levels, eff) in enumerate(FIG24_SYSTEMS):
        if i % 2 == 0:
            b.append(rect(12, y, EFFX + 176 - 12, ROW_H, fill="#f5f7f9", stroke="none", rx=2))
        b.append(text(LABEL_W, y + ROW_H / 2 + 3.2, name, 9, INK, "normal", "end"))
        for lv in levels:
            x = GX0 + lv * COLW + COLW / 2
            primary = lv == max(levels)
            b.append(f'<circle cx="{x}" cy="{y + ROW_H / 2}" r="{6 if primary else 4.4}" '
                     f'fill="{"#244a73" if primary else "#ffffff"}" '
                     f'stroke="#244a73" stroke-width="1.4"/>')
        label, fill, stroke = FIG24_EFF[eff]
        b.append(rect(EFFX, y + 4.5, 13, 13, fill=fill, stroke=stroke, sw=1.2, rx=2))
        b.append(text(EFFX + 21, y + ROW_H / 2 + 3.2, label, 8.6, MUTED))
        y += ROW_H
    b.append(line(12, GY0, EFFX + 176, GY0, RULE, 0.9))
    b.append(line(12, y, EFFX + 176, y, RULE, 0.9))
    for lv in range(7):
        x = GX0 + lv * COLW
        b.append(line(x, GY0, x, y, RULE, 0.5))

    notes = [
        "Filled circle: the highest level the paper's own reported method demonstrates. "
        "Open circle: a second claim in the same paper supported at a lower level, which is "
        "why evidence is coded per claim and not per paper.",
        "No worked example reaches E4 or E5, the two levels that require sustained or "
        "deployed operation; those columns are drawn dashed and are empty.",
        "Eleven of the twelve report no efficiency figure or only a qualitative one. The one "
        "quantified figure covers the injection stage with the readout offline, so it is not "
        "a complete-system value in the sense of Table 8.",
    ]
    ny = y + 20
    for n in notes:
        for ln in wrap(n, 112):
            b.append(text(12, ny, ln, 8.4, MUTED))
            ny += 11
        ny += 3
    return svg(W, int(ny + 6), "\n".join(b))

STATIC = {"fig0": fig0, "fig1": fig1, "fig2": fig2, "fig3": fig3,
          "fig4": fig4, "fig5s": fig5s, "fig6s": fig6s,
          "fig7s": fig7s, "fig8s": fig8s, "fig9s": fig9s, "fig10s": fig10s,
          "fig11s": fig11s, "fig12s": fig12s, "fig13s": fig13s,
          "fig14s": fig14s, "fig15s": fig15s, "fig16s": fig16s,
          "fig17s": fig17s, "fig18s": fig18s, "fig19s": fig19s,
          "fig20s": fig20s, "fig21s": fig21s, "fig22s": fig22s,
          "fig23s": fig23s, "fig24s": fig24s}


def check_geometry(name: str, s: str) -> list[str]:
    """Catch content escaping the canvas.

    Preview tools scale and crop, so a visual check cannot distinguish a real
    overflow from a renderer artefact. This does, and it runs in CI.
    Text width is estimated conservatively at 0.62em per character.
    """
    import xml.etree.ElementTree as ET

    ns = "{http://www.w3.org/2000/svg}"
    root = ET.fromstring(s)
    W, H = float(root.get("width")), float(root.get("height"))
    bad = []
    for el in root.iter():
        tag = el.tag.replace(ns, "")
        if tag == "rect" and el.get("x") is not None:
            x, y = float(el.get("x")), float(el.get("y"))
            w, h = float(el.get("width")), float(el.get("height"))
            if x + w > W + 0.5:
                bad.append(f"{name}: rect overflows right ({x + w:.0f} > {W:.0f})")
            if y + h > H + 0.5:
                bad.append(f"{name}: rect overflows bottom ({y + h:.0f} > {H:.0f})")
        elif tag == "text":
            x, y = float(el.get("x")), float(el.get("y"))
            size = float(el.get("font-size"))
            est = len(el.text or "") * size * 0.62
            anchor = el.get("text-anchor", "start")
            left = x if anchor == "start" else (x - est / 2 if anchor == "middle" else x - est)
            if left + est > W + 0.5:
                bad.append(f"{name}: text overflows right: {(el.text or '')[:40]!r}")
            if y > H + 0.5:
                bad.append(f"{name}: text below canvas: {(el.text or '')[:40]!r}")
    return bad


# The figures the manuscript actually floats, derived from its own image lines rather than
# listed here, so a figure added to or dropped from the paper cannot leave this set stale.
def _in_manuscript() -> set:
    import re as _re
    d = Path("paper")
    if not (d / "p1-s1-introduction.md").exists():
        return set()
    names = set()
    for f in sorted(d.glob("*.md")):
        for m in _re.finditer(r"^!\[.*?\]\((?:figures/)?(\w+)\.pdf\)", f.read_text(encoding="utf-8"), _re.M):
            names.add(m.group(1))
    return names & set(STATIC)


IN_MANUSCRIPT = _in_manuscript()


def selftest() -> int:
    fails = []
    skipped: list[str] = []
    for name, fn in STATIC.items():
        s = fn()
        fails.extend(check_geometry(name, s))
        if not s.startswith("<svg") or not s.rstrip().endswith("</svg>"):
            fails.append(f"{name}: malformed svg")
        if "&" in s.replace("&amp;", "").replace("&lt;", "").replace("&gt;", ""):
            fails.append(f"{name}: unescaped ampersand")
        if len(s) < 2000:
            fails.append(f"{name}: suspiciously short ({len(s)} bytes)")
    # Every family and subclass in the spec must appear in figure 1. The 2026-08-13
    # redesign prints subclass NAMES without their "F1.1" designators, so the check
    # is on the name; asserting the designator here failed against a correct figure.
    f1 = fig1()
    for code, _, _, subs in FAMILIES:
        if code not in f1:
            fails.append(f"fig1 missing family {code}")
        for s in subs:
            name = s.split(" ", 1)[1] if " " in s else s
            if not all(w in f1 for w in name.replace("/", " ").split()):
                fails.append(f"fig1 missing subclass {s.split()[0]} ({name})")

    # Every timeline milestone year must equal the year in the bibliography entry
    # it cites. A date typed from memory into a paper about lost provenance is the
    # one error this project cannot afford, so it is checked rather than trusted.
    # The artefact repository ships the instruments, the data, the code and the audited
    # bibliography; the manuscript SOURCES are authored elsewhere (see .gitignore). The
    # two figure-versus-table checks below therefore cannot run there, and they are
    # skipped WITH A NOTICE rather than failed: a check that cannot run has not passed,
    # and a reader running the released selftest is entitled to know which is which.
    # The introduction is the marker for "the manuscript is present"; the timeline check
    # is gated separately, on the bibliography, because that file IS released.
    manuscript = Path("paper/p1-s1-introduction.md").exists()
    if not manuscript:
        skipped.append("fig23s value check and fig24s row check "
                       "(the manuscript sources are not in this repository)")
    bib_path = Path("paper/references.bib")
    if not bib_path.exists():
        skipped.append("timeline year check (paper/references.bib is not in this repository)")
    else:
        bib = bib_path.read_text(encoding="utf-8")
        years = {}
        for block in re.split(r"(?=^@)", bib, flags=re.M):
            m = re.match(r"@\w+\{([^,]+),", block)
            if m:
                y = re.search(r"year\s*=\s*\{?(\d{4})", block)
                if y:
                    years[m.group(1)] = int(y.group(1))
        for year, label, cat, keys in TIMELINE:
            if cat not in {c for c, _, _ in TIMELINE_CATEGORIES}:
                fails.append(f"timeline: unknown category {cat!r} for {label!r}")
            for k in keys:
                if k not in years:
                    fails.append(f"timeline: {label!r} cites missing entry {k}")
                elif years[k] != year:
                    fails.append(f"timeline: {label!r} dated {year}, "
                                 f"{k} says {years[k]}")

    # Figure 23 restates the manuscript's Table 12, so every plotted value must
    # appear verbatim in the Section 8.2 source. A figure that drifted from its
    # own table would be an instance of this paper's subject.
    res = Path("paper/s8-results.md")
    if manuscript and not res.exists():
        fails.append("fig23s: paper/s8-results.md not found")
    elif manuscript:
        src = res.read_text(encoding="utf-8")
        needles = [f"{v:g}" for _, _, v, _, _ in FIG23_RESULTS]
        needles += [f"{d:g}" for _, _, _, d, _ in FIG23_RESULTS if d]
        needles += [f"{v:g}" for v, *_ in FIG23_BASELINES.values()]
        for needle in needles:
            if needle not in src:
                fails.append(f"fig23s: value {needle} not found in the "
                             f"Section 8.2 source")

    # Figure 24 restates the manuscript's Table 9, so every system it plots must
    # appear in the Section 4.3 source, and the levels it draws must be the ones
    # that table records. Same rule as fig23s and for the same reason.
    facets = Path("paper/s4-facets.md")
    if manuscript and not facets.exists():
        fails.append("fig24s: paper/s4-facets.md not found")
    elif manuscript:
        src = facets.read_text(encoding="utf-8")
        table = "\n".join(l for l in src.splitlines() if l.startswith("|"))
        for name, key, levels, eff in FIG24_SYSTEMS:
            if f"[{key}]" not in table:
                fails.append(f"fig24s: {name} cites {key}, absent from the Table 9 rows")
            for lv in levels:
                if f"Level {lv}" not in table:
                    fails.append(f"fig24s: Level {lv} not present in the Table 9 rows")
        if max(lv for _, _, lvs, _ in FIG24_SYSTEMS for lv in lvs) > 3:
            fails.append("fig24s: a level above 3 is plotted; the caption says none exist")
        n_eff = sum(1 for *_, e in FIG24_SYSTEMS if e != "quantified")
        if n_eff != 11:
            fails.append(f"fig24s: {n_eff} systems without a quantified efficiency "
                         f"figure, the note says eleven")
    # Figure 3 draws the assignment procedure, including the hybrid rule, and that rule has
    # been revised once (deviation D18) and then drawn wrong for four days afterwards: the
    # figure kept ranking components by "most of the state dimension" while Section 3.2
    # three pages earlier said that rule was withdrawn. A figure contradicting its own text
    # about an instrument rule is the failure this paper reports on, so it is checked. The
    # check is on the RENDERED output, not the source, because the withdrawn phrase was
    # split across two string literals and no grep of this file would have found it.
    f3 = fig3()
    withdrawn = "most of the state dimension"
    if withdrawn in f3:
        fails.append(f"fig3: draws the withdrawn D18 hybrid rule ({withdrawn!r})")
    if "F1xF2" not in f3:
        fails.append("fig3: symmetric hybrid label absent or not in ascending order")
    if "F2xF1" in f3:
        fails.append("fig3: symmetric label written F2xF1; taxonomy 2.1 requires F1xF2")
    # The hybrid box is sized from its own wrapped text, so assert the arithmetic rather
    # than trusting it: every line must sit inside the dashed rectangle. The proof PDF
    # showed the last line outside it, and the existing geometry check only looks at the
    # SVG canvas edges, so nothing caught it.
    import re as _re
    _rects = _re.findall(r'<rect x="40" y="([\d.]+)" width="\d+" height="([\d.]+)"[^>]*stroke-dasharray', f3)
    _texts = [float(m) for m in _re.findall(r'<text x="56" y="([\d.]+)"', f3)]
    if _rects and _texts:
        _top, _h = float(_rects[-1][0]), float(_rects[-1][1])
        _inside = [v for v in _texts if v >= _top]
        if _inside and max(_inside) > _top + _h:
            fails.append(f"fig3: hybrid text at y={max(_inside):.0f} falls outside its box "
                         f"(y={_top:.0f} to {_top + _h:.0f})")

    pyr = Path("paper/s3-pyramid.md")
    if manuscript and pyr.exists():
        src = pyr.read_text(encoding="utf-8")
        if withdrawn in src:
            fails.append(f"s3-pyramid.md: reinstates the withdrawn hybrid rule ({withdrawn!r})")
        if "F1xF2" not in src:
            fails.append("s3-pyramid.md: Section 3.2 no longer states the F1xF2 label fig3 draws")

    # EVERY cross-reference a shipped figure DRAWS must resolve against the manuscript as it
    # currently stands. This check exists because the same failure has now happened four
    # times: a section or table is renumbered, the prose is updated, and the figures keep
    # the old number and ship in the PDF saying it. The 2026-09-09 proof found four figures
    # still pointing at "Section 7.2" after the restructure moved it to 8.2, plus fig23s
    # naming "Table 10" for what is now Table 12.
    #
    # It resolves against the real headings and captions rather than a hard-coded list, so
    # the next renumbering cannot leave this check behind the way it left the figures.
    if manuscript:
        import re as _re
        srcs = ["paper1-frontmatter.md", "p1-s1-introduction.md", "s2-foundations.md",
                "s3-pyramid.md", "s4-facets.md", "s5-benchmarks.md", "s6-methodology.md",
                "s7-corpus-construction.md", "s8-results.md",
                "s9-discussion-limitations.md", "s10-conclusion.md"]
        body = "\n".join((Path("paper") / s).read_text(encoding="utf-8")
                          for s in srcs if (Path("paper") / s).exists())
        heads = {m.group(1) for m in _re.finditer(r"^#{1,3} (\d+(?:\.\d+){0,2})[ .]", body, _re.M)}
        n_tables = len(_re.findall(r"^\*\*Table \d+\.", body, _re.M))
        n_figures = len(_re.findall(r"^!\[", body, _re.M))
        for name in sorted(IN_MANUSCRIPT):
            drawn = STATIC[name]()
            text_only = " ".join(_re.findall(r">([^<]+)<", drawn))
            for kind, num in _re.findall(r"\b(Section|Table|Figure)s?\s+([\d.]+?)\.?(?=[\s,;:)]|$)",
                                         text_only):
                if kind == "Section" and num not in heads:
                    fails.append(f"{name}: draws 'Section {num}', which is not a heading")
                if kind == "Table" and not (num.isdigit() and 1 <= int(num) <= n_tables):
                    fails.append(f"{name}: draws 'Table {num}'; the manuscript has {n_tables}")
                if kind == "Figure" and not (num.isdigit() and 1 <= int(num) <= n_figures):
                    fails.append(f"{name}: draws 'Figure {num}'; the manuscript has {n_figures}")

    if fails:
        print("SELFTEST FAILED", file=sys.stderr)
        for f in fails:
            print("  - " + f, file=sys.stderr)
        return 1
    for s in skipped:
        print(f"  SKIPPED: {s}")
    print(f"selftest passed: {len(STATIC)} static figures, all families and subclasses present")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=sorted(set(STATIC) | set(DATA_FIGURES) | {"all", "static", "selftest"}))
    ap.add_argument("--out", type=Path, default=Path("paper/figures"))
    ap.add_argument("--extraction", type=Path, default=Path("data/extraction"))
    args = ap.parse_args()

    if args.which == "selftest":
        return selftest()

    args.out.mkdir(parents=True, exist_ok=True)

    if args.which in ("all", "static"):
        for name, fn in STATIC.items():
            p = args.out / f"{name}.svg"
            p.write_text(fn(), encoding="utf-8")
            print(f"  {p}")
        if args.which == "static":
            return 0
        print("\nData-dependent figures (5-12) pending extraction:")
        for name, (title, _, needs) in DATA_FIGURES.items():
            print(f"  {name}: {title}  [needs {needs}]")
        return 0

    if args.which in STATIC:
        p = args.out / f"{args.which}.svg"
        p.write_text(STATIC[args.which](), encoding="utf-8")
        print(f"  {p}")
        return 0

    return data_figure(args.which, args.extraction)


if __name__ == "__main__":
    raise SystemExit(main())
