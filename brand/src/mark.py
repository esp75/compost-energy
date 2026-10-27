"""Compost Energy logo, generated as vector.

    .venv/bin/python brand/src/mark.py

The mark is two ribbons that close a ring: a leaf (organic matter) that
sweeps up the left side and ends in a pointed tip, and a flame band (heat)
that runs down the right side and tucks under the leaf's stem. Each ribbon is
drawn as fine contour lines across a tapering width, which reads as a curved
surface and keeps the "hundreds of lines" texture of the reference logo.

COMPOST is custom geometry (heavy, extended, rounded-square letters, after the
reference wordmark); ENERGY is Michroma, tracked wide, converted to outlines so
the SVGs need no fonts.
"""

from __future__ import annotations

import base64
import math
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "11_typography" / "fonts"

LEAF = ["#132b0c", "#3a6b21", "#7cc04a", "#d8ec8a"]           # dark → light
EMBER = ["#2e0901", "#9a2606", "#f26a21", "#ffc073"]
GRAD = ["#6fae3c", "#a7b83f", "#e0882a", "#f26a21", "#b5300a"]
NIGHT, MIST, INK, GLOW = "#060a07", "#e3eae5", "#0f1a13", "#e9f07e"


# ---------------------------------------------------------------------------
# mark
# ---------------------------------------------------------------------------

def _ribbon(theta0, theta1, radius, width, bias, n_t=180):
    """Inner/outer edge samples of a ribbon along an arc (degrees, clockwise).

    width(u) and bias(u) shape the ribbon along u in [0, 1]: bias shifts the
    ribbon outwards (+) or inwards (-) so it looks like it rolls.
    """
    pts = []
    for i in range(n_t + 1):
        u = i / n_t
        th = math.radians(theta0 + (theta1 - theta0) * u)
        w = width(u)
        r_mid = radius(u) + bias(u) * w
        pts.append((th, r_mid, w))
    return pts


def _contours(samples, n_lines, cx, cy):
    """Contour lines across a ribbon: cosine spacing makes the edges read as a curve."""
    lines = []
    for k in range(n_lines):
        s = math.sin(math.pi * (k / (n_lines - 1) - 0.5))   # -1..1, dense at edges
        pts = []
        for th, r_mid, w in samples:
            r = r_mid + s * w / 2
            pts.append((cx + r * math.cos(th), cy - r * math.sin(th)))
        lines.append((s, pts))
    return lines


def _outline(samples, cx, cy):
    outer = [(cx + (r + w / 2) * math.cos(th), cy - (r + w / 2) * math.sin(th)) for th, r, w in samples]
    inner = [(cx + (r - w / 2) * math.cos(th), cy - (r - w / 2) * math.sin(th)) for th, r, w in samples]
    return outer + inner[::-1]


def _d(points, close=False):
    d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return d + (" Z" if close else "")


LEAF_SPAN = (238.0, 58.0)      # from lower left, up the left side, tip at top right
OUTER_SPAN = (230.0, 412.0)    # flame band: from the leaf stem along the bottom, up the right side
INNER_SPAN = (76.0, -150.0)    # after the twist: back inside, from the top down to the lower left


def _leaf_samples(cx, cy, R):
    def width(u):
        return 0.66 * R * math.sin(math.pi * u ** 1.1) ** 0.7 * (1 - 0.30 * u)

    def radius(u):
        return R * (0.98 - 0.06 * math.sin(math.pi * u))

    def bias(u):
        return 0.08 * math.sin(2 * math.pi * u)

    return _ribbon(*LEAF_SPAN, radius, width, bias)


def _outer_samples(cx, cy, R):
    def width(u):
        return R * (0.05 + 0.40 * math.sin(math.pi * u ** 1.15) ** 0.8 + 0.12 * u ** 6)

    def radius(u):
        return R * (1.02 + 0.04 * math.sin(math.pi * u))

    def bias(u):
        return 0.0

    return _ribbon(*OUTER_SPAN, radius, width, bias)


def _inner_samples(cx, cy, R):
    def width(u):
        # thin under the leaf tip, widest on the right, tapering into the lower left
        return R * (0.02 + 0.40 * math.sin(math.pi * u ** 0.75) ** 1.2 + 0.15 * (1 - u) ** 6)

    def radius(u):
        return R * (0.66 + 0.10 * math.sin(math.pi * u) - 0.04 * u)

    def bias(u):
        return 0.0

    return _ribbon(*INNER_SPAN, radius, width, bias)


def _fold(outer, inner, cx, cy, R, k, style, light, n=56):
    """The twist: each contour line leaving the outer band re-enters the inner band
    on the opposite edge, so the lines cross like a Möbius strip seen edge-on."""
    oc = _contours(outer, n, cx, cy)
    ic = _contours(inner, n, cx, cy)
    th = math.radians(70)
    paths = []
    for j in range(n):
        p0 = oc[j][1][-1]
        p1 = ic[n - 1 - j][1][0]
        rr = R * (0.97 + 0.18 * j / (n - 1))
        c = (cx + rr * math.cos(th), cy - rr * math.sin(th))
        paths.append((p0, c, p1))
    if style in ("flat", "mono"):
        a, b = paths[0], paths[-1]
        d = (f"M{a[0][0]:.2f},{a[0][1]:.2f} Q{a[1][0]:.2f},{a[1][1]:.2f} {a[2][0]:.2f},{a[2][1]:.2f} "
             f"L{b[2][0]:.2f},{b[2][1]:.2f} Q{b[1][0]:.2f},{b[1][1]:.2f} {b[0][0]:.2f},{b[0][1]:.2f} Z")
        fill = (INK if light else "#eef3ef") if style == "mono" else EMBER[2]
        return f'<path d="{d}" fill="{fill}"/>'
    out = []
    for j, (p0, c, p1) in enumerate(paths):
        t = j / (n - 1)
        col = _mix(EMBER[1], EMBER[3], t ** 1.5)
        out.append(f'<path d="M{p0[0]:.2f},{p0[1]:.2f} Q{c[0]:.2f},{c[1]:.2f} {p1[0]:.2f},{p1[1]:.2f}" '
                   f'fill="none" stroke="{col}" stroke-width="{(0.5 + 0.5 * t ** 3) * k:.2f}" '
                   f'stroke-opacity="{0.45 + 0.5 * t:.2f}"/>')
    return "".join(out)


def _mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def mark_group(cx=120.0, cy=120.0, R=78.0, style="lines", uid="m", light=False, glow=False, particles=False):
    """SVG <g> for the mark. style: lines | flat | mono. Returns (defs, body).

    lines: the full mark, ribbons built from contour lines (use above ~96 px).
    flat:  solid two-tone ribbons (favicons, small sizes).
    mono:  one ink.
    """
    leaf = _leaf_samples(cx, cy, R)
    outer = _outer_samples(cx, cy, R)
    inner = _inner_samples(cx, cy, R)
    leaf_out, outer_out, inner_out = (_outline(x, cx, cy) for x in (leaf, outer, inner))
    flame_out = outer_out
    k = R / 100.0
    # The flame's tail passes over the leaf's stem at the lower left (the twist).
    tail_clip = _d([(cx - 1.6 * R, cy + 0.15 * R), (cx + 0.05 * R, cy + 0.15 * R),
                    (cx + 0.05 * R, cy + 1.6 * R), (cx - 1.6 * R, cy + 1.6 * R)], close=True)

    defs = [
        f'<linearGradient id="{uid}-leaf" x1="0" y1="1" x2="0.7" y2="0">'
        f'<stop offset="0" stop-color="{LEAF[0]}"/><stop offset="0.6" stop-color="{LEAF[1]}"/>'
        f'<stop offset="1" stop-color="{LEAF[2]}"/></linearGradient>',
        f'<linearGradient id="{uid}-flame" x1="0.3" y1="0" x2="0.2" y2="1">'
        f'<stop offset="0" stop-color="{EMBER[2]}"/><stop offset="0.55" stop-color="{EMBER[1]}"/>'
        f'<stop offset="1" stop-color="{EMBER[0]}"/></linearGradient>',
        f'<clipPath id="{uid}-tail"><path d="{tail_clip}"/></clipPath>',
        f'<filter id="{uid}-blur" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur stdDeviation="{14 * k:.1f}"/></filter>',
    ]
    body = []

    if glow and style != "mono":
        body.append(f'<g filter="url(#{uid}-blur)" opacity="0.75">'
                    f'<path d="{_d(leaf_out, True)}" fill="{LEAF[2]}"/>'
                    f'<path d="{_d(outer_out, True)}" fill="{EMBER[2]}"/>'
                    f'<path d="{_d(inner_out, True)}" fill="{EMBER[2]}"/></g>')

    def ribbon(samples, outline, grad, ramp, n_lines, lit_side, vein):
        out = []
        if style == "mono":
            ink = INK if light else "#eef3ef"
            gap = MIST if light else NIGHT
            out.append(f'<path d="{_d(outline, True)}" fill="{ink}" stroke="{gap}" stroke-width="{3 * k:.2f}"/>')
            return out
        if style == "flat":
            out.append(f'<path d="{_d(outline, True)}" fill="url(#{grad})" stroke="{NIGHT if not light else MIST}" '
                       f'stroke-width="{2 * k:.2f}" stroke-opacity="0.6"/>')
            return out
        # dark body, shaded across the width by the contour lines themselves
        out.append(f'<path d="{_d(outline, True)}" fill="{ramp[0]}"/>')
        for s_, pts in _contours(samples, n_lines, cx, cy):
            t = (s_ * lit_side + 1) / 2                     # 0 = shadow edge, 1 = lit edge
            col = _mix(ramp[1], ramp[3], t ** 2.2)
            op = 0.55 + 0.45 * t
            sw = (0.55 + 0.6 * t ** 3) * k
            out.append(f'<path d="{_d(pts)}" fill="none" stroke="{col}" stroke-width="{sw:.2f}" '
                       f'stroke-opacity="{op:.2f}"/>')
        # bright rim on the lit edge
        edge = [(cx + (r + lit_side * w / 2) * math.cos(th), cy - (r + lit_side * w / 2) * math.sin(th))
                for th, r, w in samples]
        out.append(f'<path d="{_d(edge)}" fill="none" stroke="{ramp[3]}" stroke-width="{1.6 * k:.2f}" '
                   'stroke-opacity="0.95" stroke-linecap="round"/>')
        if vein:
            mid = [(cx + (r - 0.08 * w) * math.cos(th), cy - (r - 0.08 * w) * math.sin(th))
                   for th, r, w in samples[18:-6]]
            out.append(f'<path d="{_d(mid)}" fill="none" stroke="{GLOW}" stroke-width="{1.2 * k:.2f}" '
                       'stroke-opacity="0.8" stroke-linecap="round"/>')
            for i in range(34, len(samples) - 22, 13):
                th, r, w = samples[i]
                r0 = r - 0.08 * w
                th2 = th - math.radians(9)
                for side in (-1, 1):
                    x0, y0 = cx + r0 * math.cos(th), cy - r0 * math.sin(th)
                    r2 = r0 + side * w * 0.40
                    x1, y1 = cx + r2 * math.cos(th2), cy - r2 * math.sin(th2)
                    out.append(f'<path d="M{x0:.2f},{y0:.2f} L{x1:.2f},{y1:.2f}" stroke="{GLOW}" '
                               f'stroke-width="{0.7 * k:.2f}" stroke-opacity="0.45" stroke-linecap="round"/>')
        return out

    body += ribbon(outer, outer_out, f"{uid}-flame", EMBER, 56, 1, False)
    body.append(_fold(outer, inner, cx, cy, R, k, style, light))
    body += ribbon(inner, inner_out, f"{uid}-flame", EMBER, 56, 1, False)
    body += ribbon(leaf, leaf_out, f"{uid}-leaf", LEAF, 60, 1, True)

    if particles and style == "lines":
        seed = 11
        def rnd():
            nonlocal seed
            seed = (seed * 16807) % 2147483647
            return seed / 2147483647
        for _ in range(170):
            a = rnd() * 2 * math.pi
            spread = (rnd() - 0.35) * 0.9 * rnd()
            r = R * (1.0 + spread)
            x, y = cx + r * math.cos(a), cy - r * math.sin(a)
            hot = math.cos(a) > -0.1 or math.sin(a) < -0.5
            col = EMBER[3] if hot else LEAF[3]
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{(0.4 + 1.3 * rnd() ** 2) * k:.2f}" '
                        f'fill="{col}" fill-opacity="{0.25 + 0.6 * rnd():.2f}"/>')
    return defs, "".join(body)


# ---------------------------------------------------------------------------
# COMPOST: custom letters, cap height 100, y up
# ---------------------------------------------------------------------------

H, V, HS = 100.0, 24.0, 22.0       # cap height, vertical stroke, horizontal stroke


def rbox(x0, y0, x1, y1, r):
    r = min(r, (x1 - x0) / 2 - 0.01, (y1 - y0) / 2 - 0.01)
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=32)


def pill(x0, y0, x1, y1):
    return rbox(x0, y0, x1, y1, (y1 - y0) / 2)


def letter(ch: str, w: float):
    """Pill-shaped extended capitals: round ends, flat tops, uniform medium stroke."""
    if ch == "O":
        return pill(0, 0, w, H).difference(pill(V, HS, w - V, H - HS))
    if ch == "C":
        ring = letter("O", w)
        return ring.difference(box(w - H * 0.14, -1, w + 1, H + 1)).difference(box(w - H * 0.5, HS, w + 1, H - HS))
    if ch == "P":
        y0 = 0.36 * H
        bowl = pill(0, y0, w, H).union(box(0, y0, H, H))
        bowl = bowl.difference(pill(V, y0 + HS, w - V, H - HS).union(box(V, y0 + HS, H, H - HS)))
        return unary_union([bowl, box(0, 0, V, H)])
    if ch == "S":
        mid = H / 2
        r_top = (H - (mid - HS / 2)) / 2
        top = pill(0, mid - HS / 2, w, H).union(box(w - r_top, mid - HS / 2, w, H))
        top = top.difference(pill(V, mid + HS / 2, w + 2 * r_top, H - HS))
        bot = pill(0, 0, w, mid + HS / 2).union(box(0, 0, r_top, mid + HS / 2))
        bot = bot.difference(pill(-2 * r_top, HS, w - V, mid - HS / 2))
        return unary_union([top, bot])
    if ch == "M":
        yc, tv = 0.20 * H, 0.27 * H                         # V point height, diagonal depth
        top = rbox(0, -40, w, H, 0.18 * H).intersection(box(0, 0, w, H))
        slope = (H - yc) / (w / 2 - V)
        bottom_gap = Polygon([(V, -1), (w - V, -1), (w - V, H - tv * 1.25), (w / 2, yc), (V, H - tv * 1.25)])
        x_top = w / 2 - (H - (yc + tv)) / slope
        top_notch = Polygon([(x_top, H + 1), (w - x_top, H + 1), (w / 2, yc + tv)])
        return top.difference(bottom_gap).difference(top_notch)
    if ch == "T":
        return unary_union([box(0, H - HS, w, H), box(w / 2 - V / 2, 0, w / 2 + V / 2, H - HS + 1)])
    raise ValueError(ch)


WIDTHS = {"C": 190, "O": 218, "M": 206, "P": 165, "S": 194, "T": 176}
GAP = 20.0


def compost_geometry():
    x, parts = 0.0, []
    for ch in "COMPOST":
        w = WIDTHS[ch]
        parts.append(affinity.translate(letter(ch, w), x, 0))
        x += w + GAP
    return unary_union(parts), x - GAP


def geom_to_d(g, sx=1.0, ox=0.0, oy=0.0):
    """Shapely (multi)polygon → SVG path, flipping y (cap height H)."""
    polys = getattr(g, "geoms", [g])
    out = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            pts = [(ox + x * sx, oy + (H - y) * sx) for x, y in ring.coords]
            out.append(_d(pts, close=True))
    return " ".join(out)


# ---------------------------------------------------------------------------
# ENERGY: Michroma outlines
# ---------------------------------------------------------------------------

def energy_font():
    """Lexend Zetta at weight 300, instanced from the variable font (cached)."""
    out = FONTS / "LexendZetta-Light.ttf"
    if not out.exists():
        from fontTools.varLib.instancer import instantiateVariableFont
        instantiateVariableFont(TTFont(FONTS / "LexendZetta.ttf"), {"wght": 300}).save(out)
    return out


def text_d(text, font_file, size, x, y, tracking_em=0.0):
    font = TTFont(font_file)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    s = size / upm
    pen = SVGPathPen(gs)
    cursor = 0.0
    for ch in text:
        g = cmap[ord(ch)]
        tp = TransformPen(pen, (s, 0, 0, -s, x + cursor, y))
        gs[g].draw(tp)
        cursor += gs[g].width * s + tracking_em * size
    return pen.getCommands(), cursor - tracking_em * size


# ---------------------------------------------------------------------------
# lockups
# ---------------------------------------------------------------------------

def svg(w, h, inner, defs=(), bg=None):
    bgr = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<defs>{"".join(defs)}</defs>{bgr}{inner}</svg>\n')


def glow_defs(uid):
    return [f'<radialGradient id="{uid}-halo" cx="0.5" cy="0.5" r="0.5">'
            f'<stop offset="0" stop-color="{EMBER[2]}" stop-opacity="0.30"/>'
            f'<stop offset="0.45" stop-color="{LEAF[2]}" stop-opacity="0.12"/>'
            f'<stop offset="1" stop-color="{NIGHT}" stop-opacity="0"/></radialGradient>']


def wordmark(x0, y0, width, light=False, uid="w"):
    """COMPOST + ENERGY block scaled to `width`, top-left at (x0, y0). Returns (defs, body, height)."""
    g, gw = compost_geometry()
    sx = width / gw
    ink = INK if light else "#eef3ef"
    d = geom_to_d(g, sx, x0, y0)
    cap = H * sx
    size = cap * 0.43
    ey = y0 + cap + cap * 0.30 + size
    ed, ew = text_d("ENERGY", energy_font(), size, 0, 0, tracking_em=1.55)
    ex = x0 + (width - ew) / 2
    rule_w = width * 0.20
    rule_y = ey - size * 0.36
    th = max(cap * 0.055, 1.5)
    lg, eg = f"{uid}-rl", f"{uid}-re"
    defs = [f'<linearGradient id="{lg}"><stop offset="0" stop-color="#3fae2a" stop-opacity="0.2"/>'
            f'<stop offset="0.7" stop-color="#7cc04a"/><stop offset="1" stop-color="#e9f07e"/></linearGradient>',
            f'<linearGradient id="{eg}"><stop offset="0" stop-color="#ffc073"/><stop offset="0.3" stop-color="#f28a21"/>'
            f'<stop offset="1" stop-color="#e2500e" stop-opacity="0.2"/></linearGradient>']
    if light:
        defs = [d.replace("#e9f07e", "#3d6e22").replace("#ffc073", "#b23f0a") for d in defs]
    body = (f'<path d="{d}" fill="{ink}" fill-rule="evenodd"/>'
            f'<g transform="translate({ex:.2f},{ey:.2f})"><path d="{ed}" fill="{ink}"/></g>'
            f'<rect x="{x0:.2f}" y="{rule_y - th / 2:.2f}" width="{rule_w:.2f}" height="{th:.2f}" rx="{th / 2:.2f}" fill="url(#{lg})"/>'
            f'<rect x="{x0 + width - rule_w:.2f}" y="{rule_y - th / 2:.2f}" width="{rule_w:.2f}" height="{th:.2f}" rx="{th / 2:.2f}" '
            f'fill="url(#{eg})"/>')
    return defs, body, ey - y0 + size * 0.1


RING = {"dark": "mark_v2_dark.png", "light": "mark_v2_light.png"}
RING_AR = 730 / 880          # height / width of the extracted ring


def ring_image(x, y, w, light=False, embed=True):
    """<image> of the supplied ring (05_logo_primary/mark_v2_*.png)."""
    f = ROOT / "05_logo_primary" / RING["light" if light else "dark"]
    if embed:
        href = "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode()
    else:
        href = f.name
    return f'<image href="{href}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{w * RING_AR:.1f}"/>'


def stacked(light=False, bg=True, embed=True):
    """Primary lockup: the supplied ring above the vector wordmark, 1200 x 1200."""
    W, Hh = 1200, 1200
    ring = ring_image(600 - 400, 70, 800, light, embed)
    defs, wm, _ = wordmark(90, 820, 1020, light=light)
    return svg(W, Hh, ring + wm, defs, (MIST if light else NIGHT) if bg else None)


def horizontal(light=False, bg=True, embed=True):
    W, Hh = 1600, 400
    ring = ring_image(30, 200 - 170 * RING_AR, 340, light, embed)
    defs, wm, _ = wordmark(420, 150, 1120, light=light)
    return svg(W, Hh, ring + wm, defs, (MIST if light else NIGHT) if bg else None)


def wordmark_only(light=False, bg=False):
    defs, wm, h = wordmark(40, 40, 1520, light=light)
    return svg(1600, 260, wm, defs, (MIST if light else NIGHT) if bg else None)


def mark_only(style="lines", light=False, bg=False, size=512):
    defs, m = mark_group(size / 2, size / 2, size * 0.30, style=style, uid="o", light=light)
    return svg(size, size, m, defs, (MIST if light else NIGHT) if bg else None)


if __name__ == "__main__":
    out = ROOT / "05_logo_primary"
    out.mkdir(exist_ok=True)
    (out / "primary_v2.svg").write_text(stacked())
    (out / "primary_v2_light.svg").write_text(stacked(light=True))
    print("wrote", out / "primary_v2.svg")
