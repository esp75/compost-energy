"""Generate the Compost Energy drawings as SVG.

    python hardware/drawings/src/make_drawings.py

Writes <name>.svg (light, for GitHub) and dark/<name>.svg (dark theme, for
the website) into hardware/drawings/. Every drawing is generated from the
numbers below, so a dimension change is made once here.

Dimensions are indicative: they are derived from the prototype bill of
materials (hardware/bom/prototypes.csv), not from a verified build.
"""

from __future__ import annotations

import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]

# ---- dimensions (mm), derived from the BOM ---------------------------------
WALL = 24            # 120 x 24 decking boards
INNER = 500          # 500 x 500 mesh / PVC dividers cut from 1000 x 495 sheet
OUTER = INNER + 2 * WALL
H_A, H_B, H_C, H_D = 250, 250, 125, 125   # C and D are half volume
FLOOR = 10           # 2 mm PVC floor on battens, drawn 10 mm
BOX_H = H_A + H_B + H_C + H_D + 4 * FLOOR + 2 * WALL   # incl. lid and base
STILT = 520          # 70 x 70 posts, 1800 mm cut to 4 legs of ~1350
POST = 70
TRAY = (600, 400, 420)   # Euro container, rainwater reserve on the lid
TUBE_OD = 19
COIL_PASSES = 6
COIL_PASS_LEN = 450      # 6 x 450 + bends ~= 3 m of tube
BLOCK = (460, 460, 80)   # concrete block holding the coil

PALETTES = {
    "light": dict(
        bg="#ffffff", ink="#1f2328", muted="#6e7781", faint="#d0d7de", panel="#f6f8fa",
        timber="#9a6a3a", timber_fill="#f3e6d6", timber_side="#e6d2bb",
        a="#fde68a", b="#fca5a5", c="#bfdbfe", d="#d9f99d",
        hot="#c2410c", cool="#2563eb", green="#15803d", concrete="#e5e7eb", stone="#9ca3af",
        coil="#c2410c", display="#111827", display_ink="#86efac", accent="#15803d",
    ),
    "dark": dict(
        bg="#050505", ink="#fafafa", muted="#a1a1aa", faint="#27272a", panel="#0d0d0f",
        timber="#c08a55", timber_fill="#1a1510", timber_side="#241c14",
        a="#5c4a17", b="#6b2a22", c="#1f3a57", d="#33501f",
        hot="#f7c72f", cool="#2dd4bf", green="#2dd4bf", concrete="#2a2a2e", stone="#52525b",
        coil="#f59e5b", display="#000000", display_ink="#2dd4bf", accent="#8b5cf6",
    ),
}

FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"


class Svg:
    def __init__(self, w: int, h: int, p: dict, title: str):
        self.w, self.h, self.p = w, h, p
        self.parts: list[str] = []
        self.title = title

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, size=13, fill=None, weight="normal", anchor="start", extra=""):
        fill = fill or self.p["ink"]
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
                 f'font-weight="{weight}" text-anchor="{anchor}" {extra}>{s}</text>')

    def line(self, x1, y1, x2, y2, stroke=None, w=1.2, extra=""):
        stroke = stroke or self.p["ink"]
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{w}" {extra}/>')

    def rect(self, x, y, w, h, fill="none", stroke=None, sw=1.2, extra=""):
        stroke = stroke or self.p["ink"]
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def poly(self, pts, fill="none", stroke=None, sw=1.2, extra=""):
        stroke = stroke or self.p["ink"]
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linejoin="round" {extra}/>')

    def path(self, d, stroke=None, w=1.2, fill="none", extra=""):
        stroke = stroke or self.p["ink"]
        self.add(f'<path d="{d}" stroke="{stroke}" stroke-width="{w}" fill="{fill}" '
                 f'stroke-linejoin="round" stroke-linecap="round" {extra}/>')

    def callout(self, n, x, y, tx, ty):
        """Numbered balloon at (tx, ty) with a leader to the point (x, y)."""
        self.line(tx, ty, x, y, self.p["muted"], 0.9)
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{self.p["ink"]}"/>')
        self.add(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="12" fill="{self.p["bg"]}" '
                 f'stroke="{self.p["ink"]}" stroke-width="1.2"/>')
        self.text(tx, ty + 4.5, str(n), 12, weight="bold", anchor="middle")

    def dim(self, x1, y1, x2, y2, label, off=0.0, size=12):
        """Linear dimension between two points, offset perpendicular by `off` px."""
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L * off, dx / L * off
        a1, b1, a2, b2 = x1 + nx, y1 + ny, x2 + nx, y2 + ny
        m = self.p["muted"]
        self.line(x1, y1, a1 + nx * 0.15, b1 + ny * 0.15, m, 0.7)
        self.line(x2, y2, a2 + nx * 0.15, b2 + ny * 0.15, m, 0.7)
        self.line(a1, b1, a2, b2, m, 0.9, 'marker-start="url(#dimA)" marker-end="url(#dimA)"')
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90 or ang < -90:
            ang += 180
        cx, cy = (a1 + a2) / 2, (b1 + b2) / 2
        self.add(f'<text x="{cx:.1f}" y="{cy - 5:.1f}" font-size="{size}" fill="{self.p["ink"]}" '
                 f'text-anchor="middle" transform="rotate({ang:.1f} {cx:.1f} {cy:.1f})">{label}</text>')

    def title_block(self, title, number, scale="NTS, indicative"):
        p = self.p
        w, h = 430, 104
        x, y = self.w - w - 24, self.h - h - 24
        self.rect(x, y, w, h, p["bg"], p["ink"], 1.4)
        self.line(x, y + 40, x + w, y + 40, p["ink"], 0.8)
        self.line(x, y + 72, x + w, y + 72, p["faint"], 0.8)
        for cx in (x + 150, x + 290):
            self.line(cx, y + 40, cx, y + h, p["faint"], 0.8)
        self.text(x + 14, y + 26, title, 15, weight="bold")
        rows = [("DRAWING", number), ("REV / DATE", "A · 2026-10"), ("SCALE", scale),
                ("AUTHOR", "Maxime Kadri"), ("PROJECT", "Compost Energy"), ("LICENCE", "CERN-OHL-P-2.0")]
        for i, (k, v) in enumerate(rows):
            cx = x + 14 + (i % 3) * (150 if i % 3 < 2 else 140)
            cx = [x + 14, x + 164, x + 304][i % 3]
            cy = y + 54 + (i // 3) * 32
            self.text(cx, cy, k, 8.5, p["muted"], extra='letter-spacing="1"')
            self.text(cx, cy + 13, v, 11.5)

    def render(self) -> str:
        p = self.p
        defs = f"""<defs>
  <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{p['ink']}"/></marker>
  <marker id="arrHot" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{p['hot']}"/></marker>
  <marker id="arrCool" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{p['cool']}"/></marker>
  <marker id="arrGreen" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{p['green']}"/></marker>
  <marker id="dimA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,1.5 L10,5 L0,8.5 z" fill="{p['muted']}"/></marker>
  <pattern id="mesh" width="7" height="7" patternUnits="userSpaceOnUse"><path d="M0,7 L7,0 M0,0 L7,7" stroke="{p['stone']}" stroke-width="0.45" opacity="0.7"/></pattern>
  <pattern id="concrete" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="12" height="12" fill="{p['concrete']}"/><circle cx="3" cy="3" r="1.1" fill="{p['stone']}"/><circle cx="9" cy="8" r="0.9" fill="{p['stone']}"/><circle cx="7" cy="2" r="0.5" fill="{p['stone']}"/></pattern>
  <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="{p['timber']}" stroke-width="1"/></pattern>
  <pattern id="grain" width="40" height="10" patternUnits="userSpaceOnUse"><rect width="40" height="10" fill="{p['timber_fill']}"/><path d="M0,5 C10,3 20,7 40,5" stroke="{p['timber']}" stroke-width="0.4" fill="none" opacity="0.5"/></pattern>
</defs>"""
        body = "\n".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'font-family="{FONT}">\n<title>{self.title}</title>\n{defs}\n'
                f'<rect width="{self.w}" height="{self.h}" fill="{p["bg"]}"/>\n{body}\n</svg>\n')


def header(s: Svg, title: str, sub: str) -> None:
    s.text(32, 46, title, 24, weight="bold")
    s.text(32, 72, sub, 14, s.p["muted"])


# ---------------------------------------------------------------------------
# 1. Isometric cutaway
# ---------------------------------------------------------------------------
def cutaway(p: dict) -> str:
    s = Svg(1600, 1100, p, "Compostito - isometric cutaway")
    header(s, "Compostito: isometric cutaway",
           "The home unit from the 2024 patent, prototype 2 proportions. Front walls removed; chamber A lifted to show the coil in B.")
    k = 0.37                               # px per mm
    ox, oy = 600, 840
    c30 = math.cos(math.radians(30))

    # Exploded view: chamber A, the lid and the tray are lifted by EXPL so the
    # coil in chamber B can be seen.
    EXPL = 300
    z_split = STILT + WALL + FLOOR + H_D + FLOOR + H_C + FLOOR + H_B + 0.5

    def P(x, y, z):
        if z >= z_split:
            z += EXPL
        return (ox + (x - y) * c30 * k, oy + (x + y) * 0.5 * k - z * k)

    def prism(x0, x1, y0, y1, z0, z1, top, right, left, sw=1.1, stroke=None, op=1.0, gid=None):
        stroke = stroke or p["ink"]
        extra = f'fill-opacity="{op}"'
        if gid:
            s.add(f'<g id="{gid}">')
        s.poly([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], left, stroke, sw, extra)
        s.poly([P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], right, stroke, sw, extra)
        s.poly([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], top, stroke, sw, extra)
        if gid:
            s.add("</g>")

    O = OUTER
    base_z = STILT
    # ground shadow
    s.poly([P(-80, -80, 0), P(O + 80, -80, 0), P(O + 80, O + 80, 0), P(-80, O + 80, 0)],
           p["panel"], p["faint"], 1, 'stroke-dasharray="5 5"')

    # legs (back ones first)
    s.add('<g id="legs">')
    for (lx, ly) in [(0, 0), (O - POST, 0), (0, O - POST), (O - POST, O - POST)]:
        top = base_z + BOX_H if (lx, ly) == (0, 0) else base_z
        prism(lx, lx + POST, ly, ly + POST, 0, top, p["timber_fill"], p["timber_side"], p["timber_fill"], 1)
    s.add("</g>")

    # back walls (x = 0 plane and y = 0 plane), drawn as inner faces
    z0, z1 = base_z, base_z + BOX_H
    s.add('<g id="box">')
    for za_, zb_ in ((z0, z_split - 0.5), (z_split, z1)):
        s.poly([P(0, 0, za_), P(0, O, za_), P(0, O, zb_), P(0, 0, zb_)], "url(#grain)", p["timber"], 1.3)
        s.poly([P(0, 0, za_), P(O, 0, za_), P(O, 0, zb_), P(0, 0, zb_)], "url(#grain)", p["timber"], 1.3)
    # board joints on back walls
    for zz in [z for z in range(int(z0), int(z1), 120) if abs(z - z_split) > 30]:
        s.line(*P(0, 0, zz), *P(0, O, zz), p["timber"], 0.4)
        s.line(*P(0, 0, zz), *P(O, 0, zz), p["timber"], 0.4)
    # base plate
    prism(0, O, 0, O, z0, z0 + WALL, p["timber_fill"], p["timber_side"], p["timber_fill"], 1.2, p["timber"])
    s.add("</g>")

    # chambers, bottom (D) to top (A)
    W0, W1 = WALL, WALL + INNER
    zc = z0 + WALL
    chambers = []
    for name, hh, col in [("D", H_D, p["d"]), ("C", H_C, p["c"]), ("B", H_B, p["b"]), ("A", H_A, p["a"])]:
        # solid PVC floor
        prism(W0, W1, W0, W1, zc + (1 if name == "A" else 0), zc + FLOOR, p["concrete"], p["stone"], p["concrete"], 0.8, p["stone"])
        zc += FLOOR
        chambers.append((name, zc, zc + hh, col))
        zc += hh
    lid_z = zc
    # explosion guides at the inner corners
    for (gx, gy) in [(W0, W0), (W1, W0), (W0, W1), (W1, W1)]:
        a_ = P(gx, gy, z_split - 1)
        b_ = P(gx, gy, z_split)
        s.line(a_[0], a_[1], b_[0], b_[1], p["muted"], 0.9, 'stroke-dasharray="2 4"')

    coil_pts = []
    for name, za, zb, col in chambers:
        gid = f"chamber{name}"
        s.add(f'<g id="{gid}">')
        if name == "B":
            # concrete block with the coil, inside B
            bx0 = WALL + (INNER - BLOCK[0]) / 2
            by0 = WALL + (INNER - BLOCK[1]) / 2
            bz0 = za + (H_B - BLOCK[2]) / 2 - 20
            prism(bx0, bx0 + BLOCK[0], by0, by0 + BLOCK[1], bz0, bz0 + BLOCK[2],
                  "url(#concrete)", p["concrete"], p["concrete"], 0.9, p["stone"])
            # serpentine on the block's top
            zt = bz0 + BLOCK[2]
            step = BLOCK[1] / (COIL_PASSES + 1)
            xa, xb = bx0 + 15, bx0 + BLOCK[0] - 15
            pts = [P(O + 140, by0 + step, zt)]
            for i in range(COIL_PASSES):
                y = by0 + step * (i + 1)
                if i % 2 == 0:
                    pts += [P(xb, y, zt), P(xa, y, zt)]
                else:
                    pts += [P(xa, y, zt), P(xb, y, zt)]
            pts.append(P(O + 140, by0 + step * COIL_PASSES, zt))
            coil_pts = pts
            d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            s.add('<g id="coil">')
            s.path(d, p["coil"], 6.5)
            s.path(d, p["bg"], 2.2, extra='opacity="0.55"')
            s.add("</g>")
            prism(W0, W1, W0, W1, za, zb, col, col, col, 1.0, p["ink"], 0.42)
        else:
            prism(W0, W1, W0, W1, za, zb, col, col, col, 1.0, p["ink"], 0.92)
        # mesh basket overlay on the visible faces
        s.poly([P(W1, W0, za), P(W1, W1, za), P(W1, W1, zb), P(W1, W0, zb)], "url(#mesh)", "none", 0)
        s.poly([P(W0, W1, za), P(W1, W1, za), P(W1, W1, zb), P(W0, W1, zb)], "url(#mesh)", "none", 0)
        lx, ly = P(W1, (W0 + W1) / 2, (za + zb) / 2)
        s.text(lx - 2, ly + 2, name, 28, weight="bold", anchor="end",
               extra=f'fill-opacity="0.85" font-family="Georgia, serif"')
        s.add("</g>")

    # lid with intake hatch and rainwater reserve
    s.add('<g id="lid">')
    prism(0, O, 0, O, lid_z, lid_z + WALL, p["timber_fill"], p["timber_side"], p["timber_fill"], 1.3, p["timber"])
    hz = lid_z + WALL
    s.poly([P(O - 230, 120, hz + 2), P(O - 30, 120, hz + 2), P(O - 30, O - 120, hz + 2), P(O - 230, O - 120, hz + 2)],
           p["timber_side"], p["timber"], 1.4)
    s.add("</g>")
    s.add('<g id="tray">')
    tx0, ty0 = 20, 70
    prism(tx0, tx0 + 260, ty0, ty0 + TRAY[1], hz, hz + 200,
          p["panel"], p["faint"], p["panel"], 1.1, p["muted"])
    s.add("</g>")

    # wall thickness section marks at the cut (front-right and front-left edges, dashed phantom)
    s.add('<g id="phantom">')
    for a, b in [((O, 0, z0), (O, 0, lid_z + WALL)), ((0, O, z0), (0, O, lid_z + WALL)),
                 ((O, O, z0), (O, O, lid_z)), ((O, 0, z0), (O, O, z0)), ((0, O, z0), (O, O, z0))]:
        s.line(*P(*a), *P(*b), p["muted"], 0.9, 'stroke-dasharray="6 5"')
    s.add("</g>")

    # drip line from the tray down the back corner into B
    zb_top = chambers[2][2]
    s.add('<g id="drip">')
    s.path("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in
                           [P(tx0 + 120, ty0, hz + 60), P(WALL + 30, WALL + 30, hz - 10),
                            P(WALL + 30, WALL + 30, zb_top - 30), P(WALL + 200, WALL + 30, zb_top - 30)]),
           p["cool"], 2, extra='stroke-dasharray="5 3"')
    s.add("</g>")

    # vents and airflow
    s.add('<g id="air">')
    vx, vy = P(0, O * 0.5, chambers[0][1] + 40)
    s.line(vx - 120, vy + 40, vx - 8, vy + 4, p["cool"], 2.4, 'marker-end="url(#arrCool)"')
    hx, hy = P(O, O * 0.55, chambers[3][2] - 30)
    s.line(hx + 8, hy - 4, hx + 130, hy - 50, p["hot"], 2.4, 'marker-end="url(#arrHot)"')
    # chimney-effect arrows inside
    for i, frac in enumerate([0.3, 0.55, 0.8]):
        x0_, y0_ = P(W1 - 30, INNER * frac, chambers[0][1] + 20)
        x1_, y1_ = P(W1 - 30, INNER * frac, chambers[3][2] - 20)
        s.path(f"M{x0_:.1f},{y0_:.1f} C{x0_ + 18:.1f},{(y0_ * 2 + y1_) / 3:.1f} {x1_ - 18:.1f},{(y0_ + 2 * y1_) / 3:.1f} {x1_:.1f},{y1_:.1f}",
               p["hot"] if i == 1 else p["cool"], 1.3, extra='stroke-dasharray="3 4" marker-end="url(#arrHot)" opacity="0.75"')
    s.add("</g>")

    # waste going into the hatch
    s.add('<g id="intake">')
    ix, iy = P(O - 130, O / 2, hz + 4)
    s.line(ix, iy - 150, ix, iy - 14, p["ink"], 2.2, 'marker-end="url(#arr)"')
    s.text(ix + 10, iy - 140, "food &amp; garden waste", 13, p["muted"])
    s.add("</g>")

    # probe + display
    s.add('<g id="probe">')
    px, py = P(W0, W1, (chambers[2][1] + chambers[2][2]) / 2)
    qx, qy = P(INNER * 0.45, INNER * 0.55, (chambers[2][1] + chambers[2][2]) / 2)
    s.line(px - 70, py, qx, qy, p["green"], 1.6)
    s.add(f'<circle cx="{qx:.1f}" cy="{qy:.1f}" r="4" fill="{p["green"]}"/>')
    s.rect(px - 190, py - 26, 120, 52, p["display"], p["display"], 1, 'rx="7"')
    s.text(px - 130, py - 3, "62.4 °C", 16, p["display_ink"], anchor="middle", extra='font-family="Menlo, monospace"')
    s.text(px - 130, py + 16, "RH 96 %", 12, p["display_ink"], anchor="middle", extra='font-family="Menlo, monospace"')
    s.add("</g>")

    # water connections out of B
    s.add('<g id="water">')
    if coil_pts:
        a, b = coil_pts[0], coil_pts[-1]
        s.line(a[0], a[1], a[0] + 90, a[1], p["cool"], 3, 'marker-start="url(#arrCool)"')
        s.line(b[0], b[1], b[0] + 90, b[1], p["hot"], 3, 'marker-end="url(#arrHot)"')
        s.text(a[0] + 96, a[1] + 5, "in ~40 °C", 12.5, p["cool"])
        s.text(b[0] + 96, b[1] + 5, "out, pre-heated", 12.5, p["hot"])
    s.add("</g>")

    # callouts: balloons in a left and a right column, at the anchor's height
    zA, zB, zC, zD = (chambers[3], chambers[2], chambers[1], chambers[0])
    items = [
        ("Intake hatch on the lid: fresh waste goes in at the top", P(O - 130, O / 2, hz + 4), "R"),
        ("Rainwater reserve (600 × 400 Euro container)", P(tx0 + 130, ty0 + 200, hz + 200), "L"),
        ("A  Mesophilic: 40-45 °C, ~1 week", P(W1, W1 * 0.55, zA[1] + 150), "R"),
        ("B  Thermophilic: 55-70 °C, 3-4 weeks; heat taken here", P(W1, W1 * 0.8, zB[1] + 200), "R"),
        ("Aluminium coil (Ø19 mm, 3 m) cast in a concrete block", coil_pts[3] if coil_pts else P(0, 0, 0), "R"),
        ("C  Cooling, half volume", P(W1, W1 * 0.7, zC[1] + 60), "R"),
        ("D  Maturation, half volume: finished compost", P(W1, W1 * 0.75, zD[1] + 60), "R"),
        ("Plastic-mesh inner chambers keep air moving through", P(W0 + 60, W1, zA[1] + 80), "L"),
        ("Solid PVC floors hold moisture between phases", P(W0 + 80, W1, zC[1] - 4), "L"),
        ("Drip line keeps B at 50-60 % moisture", P(WALL + 30, WALL + 30, zb_top + 60), "L"),
        ("Treated-timber box on 70 × 70 stilts", P(O - POST / 2, O - POST, 200), "L"),
    ]
    cols = {"L": 230, "R": 1040}
    placed = {"L": [], "R": []}
    order = sorted(range(len(items)), key=lambda i: items[i][1][1])
    ty_of = {}
    for i in order:
        side = items[i][2]
        ty = max(items[i][1][1], 150)
        if placed[side]:
            ty = max(ty, placed[side][-1] + 40)
        placed[side].append(ty)
        ty_of[i] = ty
    s.add('<g id="callouts">')
    for i, (label, (x, y), side) in enumerate(items):
        s.callout(i + 1, x, y, cols[side], ty_of[i])
    s.add("</g>")
    # legend
    lx, ly = 1150, 130
    s.text(lx, ly, "PARTS", 11, p["muted"], extra='letter-spacing="2"')
    for i, (label, _, _) in enumerate(items, 1):
        yy = ly + 28 + (i - 1) * 40
        s.add(f'<circle cx="{lx + 10}" cy="{yy - 4}" r="10" fill="none" stroke="{p["ink"]}" stroke-width="1"/>')
        s.text(lx + 10, yy, str(i), 10.5, weight="bold", anchor="middle")
        words = label.split(" ")
        line1, line2 = "", ""
        for w_ in words:
            if len(line1) + len(w_) < 40 and not line2:
                line1 += w_ + " "
            else:
                line2 += w_ + " "
        s.text(lx + 30, yy, line1.strip(), 12.5)
        if line2:
            s.text(lx + 30, yy + 15, line2.strip(), 12.5, p["muted"])
    # air legend
    s.text(lx, 640, "AIR", 11, p["muted"], extra='letter-spacing="2"')
    s.text(lx, 664, "VB low vent: fresh air in", 13, p["cool"])
    s.text(lx, 684, "VH high vent: warm, moist air out", 13, p["hot"])
    s.text(lx, 704, "Warm air rises through the mesh (chimney effect).", 12.5, p["muted"])
    s.text(32, s.h - 30, "Indicative proportions derived from the prototype bill of materials, not a verified build.", 12, p["muted"])
    s.title_block("Compostito: isometric cutaway", "CE-01")
    return s.render()


# ---------------------------------------------------------------------------
# 2. Prototype 2 orthographic build drawing
# ---------------------------------------------------------------------------
def build(p: dict) -> str:
    s = Svg(1600, 1100, p, "Prototype 2 - build drawing")
    header(s, "Prototype 2: build drawing",
           "Third-angle projection. Box with four mesh chambers, access hatches and one Ø19 mm aluminium exchanger tube.")
    k = 0.40
    # front view origin (bottom-left of box at ground)
    fx, fy = 150, 960
    O = OUTER

    def F(x, z):
        return fx + x * k, fy - z * k

    # ground
    s.line(fx - 60, fy, fx + O * k + 60, fy, p["muted"], 1, 'stroke-dasharray="8 5"')
    # legs
    for lx in (0, O - POST):
        x, y = F(lx, STILT + BOX_H)
        s.rect(x, y, POST * k, (STILT + BOX_H) * k, p["timber_fill"], p["timber"], 1.2)
    # box outline
    bx, by = F(0, STILT + BOX_H)
    s.rect(bx, by, O * k, BOX_H * k, "url(#grain)", p["timber"], 1.6)
    # board courses
    for zz in range(STILT + 120, STILT + BOX_H, 120):
        x1, y1 = F(0, zz)
        s.line(x1, y1, x1 + O * k, y1, p["timber"], 0.5)
    # hatches (one per chamber, 2 hinge pins each)
    zc = STILT + WALL
    hatch_info = []
    for name, hh in [("D", H_D), ("C", H_C), ("B", H_B), ("A", H_A)]:
        zc += FLOOR
        hx0, hz0 = F(WALL + 40, zc + hh - 15)
        hw, hhpx = (INNER - 80) * k, (hh - 30) * k
        col = {"A": p["a"], "B": p["b"], "C": p["c"], "D": p["d"]}[name]
        s.rect(hx0, hz0, hw, hhpx, col, p["ink"], 1.1, 'fill-opacity="0.85" rx="2"')
        s.text(hx0 + hw / 2, hz0 + hhpx / 2 + 6, f"hatch {name}", 13, anchor="middle", weight="bold")
        for py_ in (hz0 + 6, hz0 + hhpx - 10):
            s.rect(hx0 - 7, py_, 7, 4, p["stone"], p["ink"], 0.6)
        hatch_info.append((name, zc, hh))
        zc += hh
    # exchanger stubs on the right, at B
    zB = hatch_info[2][1] + H_B / 2
    x1, y1 = F(O, zB + 30)
    x2, y2 = F(O, zB - 30)
    s.line(x1, y1, x1 + 60, y1, p["hot"], 4)
    s.line(x2, y2, x2 + 60, y2, p["cool"], 4)
    s.text(x1 + 66, y1 + 4, "out", 11, p["hot"])
    s.text(x2 + 66, y2 + 4, "in", 11, p["cool"])
    # dims front
    s.dim(*F(0, STILT), *F(0, STILT + BOX_H), f"{BOX_H}", off=-46)
    s.dim(*F(0, 0), *F(0, STILT), f"{STILT}", off=-46)
    z = STILT + WALL
    for name, zz, hh in hatch_info:
        s.dim(*F(O, zz), *F(O, zz + hh), f"{hh}", off=120, size=11)
    s.text(fx + O * k / 2, fy + 40, "FRONT", 13, p["muted"], anchor="middle", weight="bold", extra='letter-spacing="2"')

    # side view (right of front)
    sx = fx + O * k + 300

    def S(y, z):
        return sx + y * k, fy - z * k

    s.line(sx - 40, fy, sx + O * k + 40, fy, p["muted"], 1, 'stroke-dasharray="8 5"')
    for ly in (0, O - POST):
        x, y = S(ly, STILT + BOX_H)
        s.rect(x, y, POST * k, (STILT + BOX_H) * k, p["timber_fill"], p["timber"], 1.2)
    x, y = S(0, STILT + BOX_H)
    s.rect(x, y, O * k, BOX_H * k, "url(#grain)", p["timber"], 1.6)
    # vents
    vx, vy = S(O * 0.5, STILT + WALL + 60)
    s.rect(vx - 40, vy - 8, 80, 16, p["bg"], p["cool"], 1.4, 'rx="8"')
    s.text(vx, vy + 32, "VB vent", 11, p["cool"], anchor="middle")
    vx, vy = S(O * 0.5, STILT + BOX_H - WALL - 50)
    s.rect(vx - 40, vy - 8, 80, 16, p["bg"], p["hot"], 1.4, 'rx="8"')
    s.text(vx, vy - 16, "VH vent", 11, p["hot"], anchor="middle")
    # tray on lid
    tx, ty = S((O - TRAY[1]) / 2, STILT + BOX_H + TRAY[2])
    s.rect(tx, ty, TRAY[1] * k, TRAY[2] * k, p["panel"], p["muted"], 1.1, 'rx="4"')
    s.text(tx + TRAY[1] * k / 2, ty + TRAY[2] * k / 2 + 4, "rainwater reserve", 11, p["muted"], anchor="middle")
    s.dim(*S(0, STILT + BOX_H + TRAY[2]), *S(O, STILT + BOX_H + TRAY[2]), f"{O}", off=-24)
    s.dim(*S(O, STILT + BOX_H), *S(O, STILT + BOX_H + TRAY[2]), f"{TRAY[2]}", off=34)
    s.text(sx + O * k / 2, fy + 40, "SIDE", 13, p["muted"], anchor="middle", weight="bold", extra='letter-spacing="2"')

    # top view (above front)
    ty0 = 140

    def T(x, y):
        return fx + x * k, ty0 + y * k

    x, y = T(0, 0)
    s.rect(x, y, O * k, O * k, p["timber_fill"], p["timber"], 1.6)
    x, y = T(WALL, WALL)
    s.rect(x, y, INNER * k, INNER * k, "url(#mesh)", p["muted"], 0.9, 'stroke-dasharray="4 3"')
    x, y = T((O - TRAY[0]) / 2 if TRAY[0] < O else -26, (O - TRAY[1]) / 2)
    s.rect(x, y, TRAY[0] * k, TRAY[1] * k, p["panel"], p["muted"], 1, 'rx="4" fill-opacity="0.7"')
    s.text(x + TRAY[0] * k / 2, y + TRAY[1] * k / 2 + 4, "Euro container 600 × 400", 11, p["muted"], anchor="middle")
    for (lx, ly) in [(0, 0), (O - POST, 0), (0, O - POST), (O - POST, O - POST)]:
        x, y = T(lx, ly)
        s.rect(x, y, POST * k, POST * k, p["timber_side"], p["timber"], 1)
    s.dim(*T(0, 0), *T(O, 0), f"{O}", off=-22)
    s.dim(*T(O, 0), *T(O, O), f"{O}", off=-22)
    s.text(fx + O * k / 2, ty0 + O * k + 34, "TOP (lid)", 13, p["muted"], anchor="middle", weight="bold", extra='letter-spacing="2"')

    # detail: hinge
    dx, dy = 1060, 170
    s.text(dx, dy - 20, "DETAIL H: HATCH HINGE (2 per hatch)", 11, p["muted"], extra='letter-spacing="1.5"')
    s.rect(dx, dy, 110, 120, "url(#grain)", p["timber"], 1.2)
    s.rect(dx + 110, dy + 10, 110, 100, p["b"], p["ink"], 1.1, 'fill-opacity="0.8"')
    s.add(f'<circle cx="{dx + 110}" cy="{dy + 30}" r="6" fill="{p["stone"]}" stroke="{p["ink"]}"/>')
    s.add(f'<circle cx="{dx + 110}" cy="{dy + 90}" r="6" fill="{p["stone"]}" stroke="{p["ink"]}"/>')
    s.text(dx + 240, dy + 34, "screw-in hinge pin 80 × 6", 11.5)
    s.text(dx + 240, dy + 52, "hatch swings out for unloading", 11.5, p["muted"])
    s.line(dx + 117, dy + 30, dx + 236, dy + 30, p["muted"], 0.8)

    # parts list
    rows = [
        ("1", "Timber decking board 2400 × 120 × 24", "6", "walls, lid, base"),
        ("2", "Treated post 1800 × 70 × 70", "3", "4 stilts"),
        ("3", "Plastic mesh 500 × 500", "1", "aerobic inner chambers"),
        ("4", "Rigid PVC sheet 1000 × 495 × 2", "2", "solid chamber floors"),
        ("5", "Euro container 600 × 400 × 420", "1", "rainwater reserve"),
        ("6", "PE drip tube Ø4 mm + fittings", "1", "irrigation of B"),
        ("7", "Screw-in hinge pin 80 × 6", "8", "4 hatches"),
        ("8", "Corner brackets 30 / 50 mm", "40", "box and frame"),
        ("9", "Fence insulator ring 80 × 6", "25", "mesh stand-offs"),
        ("10", "Aluminium tube Ø19 mm, 3 m", "1", "exchanger in B"),
        ("11", "Concrete casing", "1", "thermal mass for the coil"),
    ]
    px, py = 1060, 420
    s.text(px, py - 16, "PARTS LIST (from hardware/bom/prototypes.csv)", 11, p["muted"], extra='letter-spacing="1.5"')
    colx = [px, px + 34, px + 300, px + 340]
    s.line(px, py, px + 500, py, p["ink"], 1)
    for i, h_ in enumerate(["#", "Item", "Qty", "Use"]):
        s.text(colx[i], py + 18, h_, 11, p["muted"], weight="bold")
    s.line(px, py + 26, px + 500, py + 26, p["faint"], 1)
    for j, r in enumerate(rows):
        yy = py + 48 + j * 24
        for i, v in enumerate(r):
            s.text(colx[i], yy, v, 12, p["ink"] if i < 3 else p["muted"])
        s.line(px, yy + 8, px + 500, yy + 8, p["faint"], 0.6)
    s.text(px, py + 48 + len(rows) * 24 + 10, "Prototype 2 lines ≈ €220 + €50 concrete; reuses the PVC sheet and drip tube from prototype 1.", 11.5, p["muted"])
    s.text(32, s.h - 30, "All dimensions in mm. Indicative: derived from the bill of materials, not from a verified build.", 12, p["muted"])
    s.title_block("Prototype 2: build drawing", "CE-02")
    return s.render()


# ---------------------------------------------------------------------------
# 3. Exchanger coil
# ---------------------------------------------------------------------------
def exchanger(p: dict) -> str:
    s = Svg(1600, 1100, p, "Exchanger coil - prototype 2 vs 3")
    header(s, "Exchanger coil in its concrete block",
           "Prototype 2 has one 3 m tube. Prototype 3 doubles it, to measure how heat output scales with surface area.")
    k = 0.62

    def plan(ox, oy, layers, label):
        bw, bd = BLOCK[0] * k, BLOCK[1] * k
        s.rect(ox, oy, bw, bd, "url(#concrete)", p["stone"], 1.4, 'rx="6"')
        step = BLOCK[1] / (COIL_PASSES + 1) * k
        for li in range(layers):
            off = li * step / 2
            col = p["coil"] if li == 0 else p["hot"]
            xa, xb = ox + 20, ox + bw - 20
            pts = [(ox + bw + 70, oy + step + off)]
            for i in range(COIL_PASSES):
                y = oy + step * (i + 1) + off
                pts += [(xb, y), (xa, y)] if i % 2 == 0 else [(xa, y), (xb, y)]
            pts.append((ox + bw + 70, oy + step * COIL_PASSES + off))
            d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            s.path(d, col, 7, extra='opacity="0.95"' if li == 0 else 'opacity="0.75" stroke-dasharray="1 0"')
            s.path(d, p["bg"], 2, extra='opacity="0.5"')
        s.text(ox, oy - 18, label, 15, weight="bold")
        s.dim(ox, oy + bd, ox + bw, oy + bd, f"{BLOCK[0]}", off=26)
        s.dim(ox, oy, ox, oy + bd, f"{BLOCK[1]}", off=52)
        # section line
        s.line(ox - 30, oy + bd / 2, ox + bw + 30, oy + bd / 2, p["muted"], 1, 'stroke-dasharray="14 4 3 4"')
        s.text(ox - 44, oy + bd / 2 + 5, "A", 13, p["muted"], weight="bold")
        s.text(ox + bw + 34, oy + bd / 2 + 5, "A", 13, p["muted"], weight="bold")

    def section(ox, oy, layers):
        bw, bh = BLOCK[0] * k, BLOCK[2] * k * 2.2   # vertical exaggeration
        s.rect(ox, oy, bw, bh, "url(#concrete)", p["stone"], 1.4)
        step = BLOCK[1] / (COIL_PASSES + 1) * k
        for li in range(layers):
            cy = oy + bh / 2 if layers == 1 else oy + bh * (0.32 + 0.36 * li)
            for i in range(COIL_PASSES):
                cx = ox + step * (i + 1) + li * step / 2
                if cx > ox + bw - 8:
                    continue
                s.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{TUBE_OD * k * 0.55:.1f}" '
                      f'fill="{p["coil"]}" stroke="{p["ink"]}" stroke-width="0.8"/>')
                s.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{TUBE_OD * k * 0.3:.1f}" fill="{p["bg"]}"/>')
        s.text(ox, oy + bh + 22, "SECTION A-A (vertical ×2.2)", 11, p["muted"], extra='letter-spacing="1.5"')
        s.dim(ox + bw, oy, ox + bw, oy + bh, f"{BLOCK[2]}", off=-24)

    plan(110, 170, 1, "Prototype 2: 1 tube")
    plan(640, 170, 2, "Prototype 3: 2 tubes")
    section(110, 520, 1)
    section(640, 520, 2)

    # numbers
    rows = [("Tube (aluminium)", "Ø19, 3 mm wall", "2 × Ø19"),
            ("Length", "3 m", "6 m"),
            ("Surface A = π·d·L", "0.179 m²", "0.358 m²"),
            ("U at h_compost = 15 W/m²K", "14.9 W/m²K", "14.9 W/m²K"),
            ("P at 60 / 40 °C", "≈ 53 W", "≈ 107 W"),
            ("2024 sheet (h = 1512.5)", "3.55 kW", "-")]
    tx, ty = 1130, 190
    s.text(tx, ty - 16, "WHAT EACH PROTOTYPE SHOULD DELIVER", 11, p["muted"], extra='letter-spacing="1.5"')
    s.line(tx, ty, tx + 420, ty, p["ink"], 1)
    s.text(tx + 230, ty + 18, "P2", 12, weight="bold")
    s.text(tx + 340, ty + 18, "P3", 12, weight="bold")
    for i, (a, b, c) in enumerate(rows):
        yy = ty + 46 + i * 28
        s.text(tx, yy, a, 12, p["muted"])
        s.text(tx + 230, yy, b, 12.5)
        s.text(tx + 340, yy, c, 12.5)
        s.line(tx, yy + 9, tx + 420, yy + 9, p["faint"], 0.6)
    s.text(tx, ty + 46 + len(rows) * 28 + 8, "Model: model/compost_energy/heat_exchanger.py", 11, p["muted"])

    # resistance bar
    bx, by, bw = 110, 830, 1000
    s.text(bx, by - 46, "Where the resistance is:  1/U = 1/h_compost + wall/k + 1/h_water", 17, weight="bold")
    s.text(bx, by - 22, "Shares of the total thermal resistance at realistic values (h_compost 15, Al 3 mm, h_water 3000 W/m²K)", 13, p["muted"])
    shares = [("compost side 99.5 %", 0.99484, p["b"]), ("wall 0.02 %", 0.00019, p["stone"]), ("water 0.5 %", 0.00497, p["cool"])]
    x = bx
    for lab, f, col in shares:
        w = max(bw * f, 3)
        s.rect(x, by, w, 46, col, p["ink"], 0.8)
        x += w
    s.text(bx + 20, by + 29, "compost side: 99.5 %", 15, weight="bold")
    s.line(bx + bw - 2, by + 46, bx + bw - 2, by + 74, p["muted"], 0.8)
    s.text(bx + bw, by + 90, "aluminium wall 0.02 % · water film 0.5 %", 12.5, p["muted"], anchor="end")
    s.text(bx, by + 90, "So copper or a thinner wall changes nothing. More contact area, or moving air past the tube, does.", 13)
    s.title_block("Exchanger coil: P2 vs P3", "CE-03")
    return s.render()


# ---------------------------------------------------------------------------
# 4. Water loop P&ID
# ---------------------------------------------------------------------------
def pid(p: dict) -> str:
    s = Svg(1600, 1000, p, "Water loop P&amp;ID")
    header(s, "Water loop and instrumentation (P&amp;ID)",
           "As patented: a by-pass on the return of an existing wet heating system. Tags match the logger firmware.")
    ink, hot, cool, g = p["ink"], p["hot"], p["cool"], p["green"]

    def inst(x, y, tag, sub, col=None, right=False):
        col = col or g
        s.add(f'<circle cx="{x}" cy="{y}" r="26" fill="{p["bg"]}" stroke="{col}" stroke-width="1.6"/>')
        s.line(x - 26, y, x + 26, y, col, 0.9)
        s.text(x, y - 6, tag.split("-")[0], 11, col, weight="bold", anchor="middle")
        s.text(x, y + 16, tag.split("-")[1], 11, col, anchor="middle")
        if right:
            s.text(x + 34, y + 4, sub, 11, p["muted"])
        else:
            s.text(x, y + 44, sub, 11, p["muted"], anchor="middle")

    # compost chamber B with coil (HX-1)
    s.rect(140, 260, 330, 300, p["b"], ink, 1.6, 'fill-opacity="0.55" rx="6"')
    s.text(160, 290, "Chamber B: thermophilic", 15, weight="bold")
    s.text(160, 310, "55-70 °C", 13, p["muted"])
    s.rect(180, 370, 250, 130, "url(#concrete)", p["stone"], 1, 'rx="4"')
    coil = "M470,400 L410,400 L200,400 L200,430 L410,430 L410,460 L200,460 L200,485 L470,485"
    s.path(coil, p["coil"], 5)
    s.text(305, 525, "HX-1  Al coil in concrete", 12, anchor="middle")

    # main pipes
    # return from radiators (cool) along bottom to pump -> FT -> coil in
    s.path("M1290,660 L1290,840 L820,840", cool, 3)
    s.path("M820,840 L560,840 L560,485 L470,485", cool, 3, extra='marker-end="url(#arrCool)"')
    # coil out (hot) -> top line -> 3-way valve -> boiler
    s.path("M470,400 L560,400 L560,200 L1000,200", hot, 3, extra='marker-end="url(#arrHot)"')
    s.path("M1060,200 L1180,200", hot, 3, extra='marker-end="url(#arrHot)"')
    # bypass leg: valve down to return (dashed)
    s.path("M1030,230 L1030,840", p["muted"], 2, extra='stroke-dasharray="7 5"')
    s.text(1018, 520, "by-pass: takes the box out of the loop", 12, p["muted"], anchor="end")
    s.text(1018, 538, "when B is too cool or being emptied", 12, p["muted"], anchor="end")
    # 3-way valve symbol
    s.poly([(1000, 186), (1030, 200), (1000, 214)], p["bg"], ink, 1.4)
    s.poly([(1060, 186), (1030, 200), (1060, 214)], p["bg"], ink, 1.4)
    s.poly([(1016, 230), (1030, 200), (1044, 230)], p["bg"], ink, 1.4)
    s.text(1030, 172, "V-1  3-way valve", 12, anchor="middle", weight="bold")
    # boiler
    s.rect(1180, 150, 220, 110, p["panel"], ink, 1.6, 'rx="8"')
    s.text(1290, 195, "Existing boiler", 15, weight="bold", anchor="middle")
    s.text(1290, 216, "gas / oil / heat pump", 12, p["muted"], anchor="middle")
    s.text(1290, 234, "60/40 or 70/50 °C", 12, p["muted"], anchor="middle")
    s.path("M1400,205 L1460,205 L1460,560 L1400,560", hot, 3, extra='marker-end="url(#arrHot)"')
    s.text(1470, 380, "supply", 12, hot)
    s.rect(1180, 520, 220, 140, p["panel"], ink, 1.6, 'rx="8"')
    s.text(1290, 584, "Radiators / DHW", 15, weight="bold", anchor="middle")
    s.text(1290, 606, "heat demand", 12, p["muted"], anchor="middle")
    # pump P-1 on return
    s.add(f'<circle cx="760" cy="840" r="24" fill="{p["bg"]}" stroke="{ink}" stroke-width="1.6"/>')
    s.poly([(748, 826), (778, 840), (748, 854)], ink, ink, 1)
    s.text(760, 884, "P-1  12 V pump", 12, anchor="middle", weight="bold")
    s.text(760, 900, "GPIO 26, on 09-17 h if T1 > T4 + 8 °C", 11, p["muted"], anchor="middle")
    # flow sensor
    s.rect(640, 826, 50, 28, p["bg"], ink, 1.4, 'rx="4"')
    s.text(665, 845, "FE", 11, anchor="middle", weight="bold")
    # instrument bubbles
    inst(330, 322, "TT-1", "t_core", g, right=True)
    s.line(318, 346, 300, 400, g, 1, 'stroke-dasharray="3 3"')
    inst(410, 610, "TT-2", "t_mid", g)
    s.line(390, 594, 360, 540, g, 1, 'stroke-dasharray="3 3"')
    inst(200, 680, "TT-3", "t_ambient (outside, shaded)", g)
    inst(620, 760, "TT-4", "t_water_in", g, right=True)
    s.line(620, 786, 600, 840, g, 1, 'stroke-dasharray="3 3"')
    inst(660, 330, "TT-5", "t_water_out", g, right=True)
    s.line(640, 346, 560, 380, g, 1, 'stroke-dasharray="3 3"')
    inst(860, 760, "FT-1", "flow, YF-S401", g)
    s.line(840, 778, 690, 836, g, 1, 'stroke-dasharray="3 3"')
    inst(330, 170, "MT-1", "headspace RH, SHT31", g, right=True)
    s.line(330, 196, 330, 262, g, 1, 'stroke-dasharray="3 3"')

    # logger
    s.rect(140, 760 - 60 + 120, 300, 100, p["display"], p["display"], 1, 'rx="10"')
    s.text(160, 850, "ESP32 logger", 15, p["display_ink"], weight="bold")
    s.text(160, 872, "SD card · RTC · every 2 min", 12, p["display_ink"])
    s.text(160, 890, "1-Wire bus GPIO 4 · flow GPIO 27", 12, p["display_ink"])
    # legend
    lx, ly = 1330, 730
    s.line(lx, ly, lx + 40, ly, hot, 3); s.text(lx + 50, ly + 4, "pre-heated water", 12)
    s.line(lx, ly + 22, lx + 40, ly + 22, cool, 3); s.text(lx + 50, ly + 26, "cool return", 12)
    s.line(lx, ly + 44, lx + 40, ly + 44, g, 1, 'stroke-dasharray="3 3"'); s.text(lx + 50, ly + 48, "sensor connection", 12)
    s.text(32, s.h - 30, "Heat recovered Q = ṁ · cp · (T5 − T4) while P-1 runs. Bench prototypes use mains water at 0.35 L/min in place of the heating return.", 12, p["muted"])
    s.title_block("Water loop P&amp;ID", "CE-04")
    return s.render()


# ---------------------------------------------------------------------------
# 5. Farm plant layout
# ---------------------------------------------------------------------------
def farm(p: dict) -> str:
    s = Svg(1600, 1000, p, "Farm-scale plant layout")
    header(s, "Farm-scale plant: layout (first pass)",
           "Where the project went after the home numbers didn't add up. Sizes from farm_sizing() in model/compost_energy/energy_balance.py.")
    ink = p["ink"]

    def block(x, y, w, h, title, lines, fill, sw=1.6):
        s.rect(x, y, w, h, fill, ink, sw, 'rx="10" fill-opacity="0.9"')
        s.text(x + 16, y + 30, title, 15, weight="bold")
        for i, l in enumerate(lines):
            s.text(x + 16, y + 52 + i * 18, l, 12, p["muted"] if i else ink)

    def flow(d, col=None, marker="arr"):
        s.path(d, col or ink, 3, extra=f'marker-end="url(#{marker})"')

    block(60, 170, 220, 120, "1  Reception", ["39 t/day manure, silage,", "straw ≈ 46 m³/day", "optional shredding"], p["panel"])
    # reactors
    s.rect(340, 140, 640, 330, "none", ink, 1.2, 'rx="14" stroke-dasharray="8 6"')
    s.text(360, 166, "Enclosed tunnels · ~490 m³ · phases shown in order (operation: CE-11)", 13, p["muted"])
    block(360, 190, 180, 150, "2  Reactor A", ["mesophilic", "seeded, mixed", "~40-45 °C"], p["a"])
    block(570, 190, 190, 150, "3  Reactor B", ["thermophilic", "55-70 °C, aerated", "sanitises the compost"], p["b"])
    block(790, 190, 170, 150, "4  Reactor C", ["mesophilic", "cooling", "~40 °C"], p["c"])
    flow("M280,230 L356,230")
    flow("M540,265 L566,265")
    flow("M760,265 L786,265")
    # aeration fan
    s.add(f'<circle cx="665" cy="420" r="26" fill="{p["bg"]}" stroke="{ink}" stroke-width="1.5"/>')
    s.path("M650,410 L680,420 L650,430 Z", ink, 1, fill=ink)
    s.text(705, 425, "aeration fans (in the 13 kW auxiliaries)", 12, p["muted"])
    flow("M665,394 L665,344", p["cool"], "arrCool")
    # exhaust air -> exchanger
    flow("M665,190 L665,110 L1060,110 L1060,166", p["hot"], "arrHot")
    s.text(700, 100, "hot, moist exhaust air", 12, p["hot"])
    block(1010, 170, 250, 130, "5  Air-to-water exchanger", ["plate-fin, in the exhaust", "≈ 2.5 kW/m² measured on", "a dairy farm (Kojima 2022)"], p["panel"])
    flow("M1260,235 L1310,235", p["hot"], "arrHot")
    block(1314, 140, 240, 200, "6  Farm heat users", ["dairy hot water", "barn / greenhouse", "grain or hay drying", "548 kW over the heating season", "≈ 2 GWh/yr (model)"], p["panel"])
    flow("M1135,300 L1135,380", p["muted"])
    block(1010, 384, 250, 80, "7  Biofilter", ["cooled air, odour treated"], p["panel"])
    # down to maturation
    flow("M875,340 L875,560")
    s.text(890, 520, "21 m³/day pre-compost", 12, p["muted"])
    block(560, 566, 540, 160, "8  Maturation hall", ["~1,200 m³ windrows, ≤ 1 m deep → ~1,200 m²", "8 weeks, turned; the mesophilic microbes", "and fungi finish the humus"], p["d"])
    flow("M560,646 L420,646")
    block(120, 566, 296, 160, "9  Storage", ["~4,500 m³ finished compost", "7 months, until spreading", "season"], p["panel"])
    flow("M268,726 L268,800")
    block(120, 804, 296, 90, "10  Fields", ["stable, sanitised fertiliser"], p["d"])
    s.text(560, 790, "Measured on a 150-cow dairy farm composter: 38 % of the microbial heat", 13)
    s.text(560, 810, "reached the water (23.3 of 61.8 kW). Kojima et al. 2022, CC-BY-4.0.", 13, p["muted"])
    s.text(32, s.h - 30, "First-pass layout from the energy model. Plant sizes are model outputs, not a site design.", 12, p["muted"])
    s.title_block("Farm-scale plant layout", "CE-05")
    return s.render()


DRAWINGS = {
    "compostito-cutaway": cutaway,
    "prototype-2-build": build,
    "exchanger-coil": exchanger,
    "water-loop-pid": pid,
    "farm-plant-layout": farm,
}


def main() -> None:
    from industrial_drawings import DRAWINGS as FARM_UNIT  # CE-06..CE-10

    (OUT / "dark").mkdir(exist_ok=True)
    for name, fn in {**DRAWINGS, **FARM_UNIT}.items():
        (OUT / f"{name}.svg").write_text(fn(PALETTES["light"]))
        (OUT / "dark" / f"{name}.svg").write_text(fn(PALETTES["dark"]))
        print("wrote", name)


if __name__ == "__main__":
    main()
