"""Drawings CE-06..CE-10: the farm-scale unit.

Imported by make_drawings.py. Every number comes from
model/compost_energy/industrial.py, so the drawings move with the model.
Tunnel geometry is rounded to buildable sizes; the model values are printed
next to them where it matters.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "model"))

from compost_energy.industrial import enthalpy_kj_per_kg, layout, operating_modes, size  # noqa: E402
from make_drawings import Svg, header  # noqa: E402

M = size()
OPS = operating_modes()

# ---- buildable geometry (m), shared with hardware/cad ----------------------
G = layout()
LAY = G["layout"]
W = G["width_m"]                                # 5.0 inner
H = G["height_m"]                               # 4.0 inner
L = G["length_m"]                               # 16.5 inner, rounded up from the model
FILL = M["fill_depth_m"]                        # 2.0 average bed
T = LAY.wall_m                                  # 200 concrete + 100 PIR
SLAB = LAY.slab_m                               # plenum slab under the spigot floor
N = M["n_tunnels"]
X_ALL = G["overall_x_m"]                        # 16.2 overall
DOOR_W, DOOR_H = LAY.door_w_m, LAY.door_h_m
SPIGOT_PITCH = LAY.spigot_pitch_m


def bay_x(i: int) -> float:
    """Inner left wall of tunnel i (0-based)."""
    return T + i * (W + T)


def fmt(v: float, nd: int = 0) -> str:
    return f"{v:,.{nd}f}"


DUCT_T = 315    # next standard size up from the model
DUCT_M = 500


# ---------------------------------------------------------------------------
# CE-06  isometric cutaway
# ---------------------------------------------------------------------------
def unit_cutaway(p: dict) -> str:
    s = Svg(1600, 1000, p, "Farm-scale unit - isometric cutaway")
    header(s, "Farm-scale unit: isometric cutaway",
           f"Three aerated tunnels, {fmt(M['gross_total_m3'])} m³ in all, with heat recovered from the exhaust air. "
           "Tunnel 3 roof and side wall cut away.")
    ink, mu = p["ink"], p["muted"]
    k, ox, oy = 32.0, 560.0, 270.0
    c30 = math.cos(math.radians(30))

    def P(x, y, z):
        return (ox + (x - y) * c30 * k, oy + (x + y) * 0.5 * k - z * k)

    def box(x0, x1, y0, y1, z0, z1, top, right, left, sw=1.1, stroke=None, op=1.0):
        stroke = stroke or ink
        e = f'fill-opacity="{op}"'
        s.poly([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], left, stroke, sw, e)
        s.poly([P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], right, stroke, sw, e)
        s.poly([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], top, stroke, sw, e)

    def seg(a, b, col=None, w=1.0, extra=""):
        (x1, y1), (x2, y2) = P(*a), P(*b)
        s.line(x1, y1, x2, y2, col or ink, w, extra)

    wall_top = SLAB + H
    roof = wall_top + T
    concrete, side = p["concrete"], p["panel"]

    # ground
    s.poly([P(-1, -1.5, 0), P(27, -1.5, 0), P(27, 18.5, 0), P(-1, 18.5, 0)],
           p["panel"], p["faint"], 1, 'stroke-dasharray="5 5"')

    # back wall of the whole block and slab
    box(0, X_ALL, -T, 0, 0, roof, concrete, side, concrete)
    box(0, X_ALL, 0, L, 0, SLAB, concrete, side, concrete)

    # tunnels 1 and 2: closed
    for i in range(N - 1):
        x0 = bay_x(i)
        box(x0 - T, x0, 0, L, SLAB, roof, concrete, side, concrete)       # left wall
        box(x0, x0 + W, 0, L, wall_top, roof, concrete, side, concrete)   # roof
        # door frame + sectional door on the front face (y = L)
        dx0 = x0 + (W - DOOR_W) / 2
        s.poly([P(x0 - T, L, SLAB), P(x0 + W + T, L, SLAB), P(x0 + W + T, L, roof), P(x0 - T, L, roof)],
               concrete, ink, 1.1)
        s.poly([P(dx0, L, SLAB), P(dx0 + DOOR_W, L, SLAB), P(dx0 + DOOR_W, L, SLAB + DOOR_H), P(dx0, L, SLAB + DOOR_H)],
               p["c"], ink, 1.2)
        for j in range(1, 8):
            z = SLAB + DOOR_H * j / 8
            seg((dx0, L, z), (dx0 + DOOR_W, L, z), mu, 0.6)
        tx, ty = P(x0 + W / 2, L, roof + 0.25)
        s.text(tx, ty, f"T-10{i + 1}", 12, weight="bold", anchor="middle")

    # tunnel 3: cut away
    x0 = bay_x(N - 1)
    x1 = x0 + W
    box(x0 - T, x0, 0, L, SLAB, roof, concrete, side, concrete)           # its left wall (shared)
    # inside faces seen through the cut: back wall face and left wall face
    s.poly([P(x0, 0, SLAB), P(x1, 0, SLAB), P(x1, 0, wall_top), P(x0, 0, wall_top)], p["panel"], ink, 0.9)
    s.poly([P(x0, 0, SLAB), P(x0, L, SLAB), P(x0, L, wall_top), P(x0, 0, wall_top)], side, ink, 0.9)
    # spigot floor: air channels running along the tunnel
    nch = int(W / SPIGOT_PITCH)
    for c in range(1, nch):
        xc = x0 + c * SPIGOT_PITCH
        seg((xc, 0.2, SLAB), (xc, L - 0.2, SLAB), p["cool"], 0.8, 'stroke-dasharray="2 3"')
    # compost bed: rear part only, front part removed to show the floor
    bed_front = L * 0.62
    box(x0, x1, 0, bed_front, SLAB, SLAB + FILL, p["timber_fill"], p["timber_side"], p["timber_fill"], 1.1)
    for j in range(14):
        yy = 0.6 + j * (bed_front - 1.0) / 13
        for xx in (x0 + 0.8, x0 + 2.1, x0 + 3.4, x0 + 4.4):
            cx, cy = P(xx + (j % 3) * 0.15, yy, SLAB + FILL)
            s.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.6" fill="{p["timber"]}" opacity="0.6"/>')
    # air rising through the bed
    for xx in (x0 + 1.2, x0 + 2.5, x0 + 3.8):
        a, b = P(xx, bed_front - 0.05, SLAB + 0.1), P(xx, bed_front - 0.05, SLAB + FILL + 1.0)
        s.line(a[0], a[1], b[0], b[1], p["cool"], 1.6, 'marker-end="url(#arrCool)"')
    # right wall cut down to a stepped section
    cut_z = SLAB + 0.9
    box(x1, x1 + T, 0, L * 0.45, SLAB, roof, concrete, side, concrete)
    box(x1, x1 + T, L * 0.45, L, SLAB, cut_z, concrete, side, concrete)
    # section hatch on the cut face of the wall
    s.poly([P(x1, L * 0.45, cut_z), P(x1 + T, L * 0.45, cut_z), P(x1 + T, L * 0.45, roof), P(x1, L * 0.45, roof)],
           "url(#hatch)", ink, 0.8)
    # tunnel 3: door open, front frame cut with the wall
    tx, ty = P(x0 + W / 2 + 1.0, L + 1.6, 0)
    s.text(tx, ty, "T-103 (door open)", 12, weight="bold", anchor="middle")

    # exhaust stubs and manifold on the roof
    zm = roof + 0.9
    hot = p["hot"]
    for i in range(N):
        xs = bay_x(i) + W / 2
        seg((xs, 1.2, roof), (xs, 1.2, zm), hot, 5)
    seg((bay_x(0) + W / 2, 1.2, zm), (19.6, 1.2, zm), hot, 7)
    seg((19.6, 1.2, zm), (19.6, 1.2, 3.4), hot, 7)

    # heat-recovery skid: exchanger, fan, biofilter
    box(*LAY.hx, p["panel"], p["b"], p["panel"], 1.3, op=0.95)
    for j in range(9):   # fin pack lines on the visible side
        yy = 0.6 + j * 0.42
        seg((21.4, yy, 0.5), (21.4, yy, 2.9), p["hot"], 0.6)
    box(*LAY.fan, p["panel"], p["panel"], p["panel"], 1.2)          # fan housing
    cx, cy = P(23.1, 2.1, 0.8)
    s.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="10" ry="13" fill="{p["bg"]}" stroke="{ink}" stroke-width="1.2"/>')
    seg((21.4, 2.1, 0.8), (21.9, 2.1, 0.8), mu, 3)
    box(*LAY.tank, p["c"], p["c"], p["c"], 1.1)                        # condensate tank
    seg((21.4, 3.9, 0.3), (24.0, 3.9, 0.3), p["cool"], 2, 'stroke-dasharray="4 3"')
    box(*LAY.biofilter, p["d"], p["d"], p["d"], 1.2, op=0.9)               # biofilter
    seg((22.5, 2.8, 0.8), (22.5, 8.0, 0.8), mu, 3)
    # water loop leaving the exchanger
    seg((18.6, 3.6, 1.0), (17.2, 3.6, 1.0), hot, 3)
    seg((18.6, 3.0, 0.6), (17.2, 3.0, 0.6), p["cool"], 3)

    # callouts
    items = [
        (P(x0 - T / 2, 9.0, roof), "Insulated precast tunnel"),
        (P(bay_x(1) + 2.2, L, SLAB + 2.0), "Sectional door"),
        (P(x0 + 2.5, 13.0, SLAB), "Aerated spigot floor"),
        (P(x0 + 2.4, 5.0, SLAB + FILL), "Compost bed"),
        (P(x0 + 1.5, 2.0, SLAB + FILL + 1.0), "Headspace"),
        (P(9.0, 1.2, zm), "Exhaust manifold"),
        (P(21.4, 2.0, 2.0), "Plate-fin exchanger HX-201"),
        (P(24.5, 3.9, 0.9), "Condensate tank TK-401"),
        (P(22.5, 2.8, 1.2), "Exhaust fan"),
        (P(22.5, 12.0, 1.6), f"Biofilter, {fmt(M['biofilter_m2'])} m²"),
        (P(17.6, 3.6, 1.0), "Water loop to heat users"),
        (P(x1 + T, 13.5, cut_z), "Side wall, cut"),
    ]
    balloons = [(200, 220), (360, 760), (600, 800), (1030, 260), (1110, 330), (700, 140),
                (1250, 540), (1300, 720), (1300, 640), (1000, 870), (1060, 400), (720, 830)]
    for n, ((x, y), _), (bx, by) in zip(range(1, 13), items, balloons):
        s.callout(n, x, y, bx, by)

    # key
    kx, ky = 1300, 108
    s.rect(kx - 14, ky - 8, 290 + 14, 26 + 20 * 12 + 120, p["bg"], p["faint"], 1, 'rx="6"')
    s.text(kx, ky + 12, "KEY", 10, mu, extra='letter-spacing="1.5"')
    for n, (_, label) in enumerate(items, 1):
        s.text(kx, ky + 22 + n * 20, f"{n}", 12, weight="bold")
        s.text(kx + 22, ky + 22 + n * 20, label, 12)
    yy = ky + 22 + 13 * 20 + 6
    for line in [f"Duty {fmt(M['duty_kw'])} kW, heating season",
                 f"Air {fmt(M['air_m3_h'], 0)} m³/h at {fmt(M['t_exhaust_c'])} °C, saturated",
                 f"Exchanger ≈ {fmt(M['hx_area_m2'])} m² plate-fin",
                 f"Water {fmt(M['t_supply_c'])}/{fmt(M['t_return_c'])} °C, {fmt(M['water_m3_h'], 1)} m³/h",
                 f"Wall loss {M['wall_loss_share'] * 100:.0f} % of duty"]:
        s.text(kx, yy, line, 11.5, mu)
        yy += 18

    s.text(32, s.h - 30, "Indicative. Sizes from model/compost_energy/industrial.py; nothing at this scale has been built.", 12, mu)
    s.title_block("Farm-scale unit, cutaway", "CE-06")
    return s.render()


# ---------------------------------------------------------------------------
# CE-07  general arrangement
# ---------------------------------------------------------------------------
def general_arrangement(p: dict) -> str:
    s = Svg(1600, 1000, p, "Farm-scale unit - general arrangement")
    header(s, "Farm-scale unit: general arrangement",
           "Plan, cross-section A-A and long section B-B. Dimensions in metres; inner sizes unless marked.")
    ink, mu, hot, cool = p["ink"], p["muted"], p["hot"], p["cool"]
    concrete = "url(#concrete)"

    # ---- plan ---------------------------------------------------------------
    sp, px0, py0 = 20.0, 80.0, 150.0          # px per m, origin = back-left outer corner

    def Pp(x, y):
        return px0 + x * sp, py0 + (y + T) * sp

    s.text(px0, py0 - 18, "PLAN", 12, mu, weight="bold", extra='letter-spacing="1.5"')
    # outer block
    x, y = Pp(0, -T)
    s.rect(x, y, X_ALL * sp, (L + T) * sp, concrete, ink, 1.4)
    for i in range(N):
        bx, by = Pp(bay_x(i), 0)
        s.rect(bx, by, W * sp, L * sp, p["bg"], ink, 1.2)
        for c in range(1, int(W / SPIGOT_PITCH)):
            xc = bx + c * SPIGOT_PITCH * sp
            s.line(xc, by + 6, xc, by + L * sp - 6, cool, 0.6, 'stroke-dasharray="2 3"')
        # door opening on the front wall
        dx = bx + (W - DOOR_W) / 2 * sp
        s.rect(dx, by + L * sp - 1, DOOR_W * sp, 3, p["bg"], p["bg"], 0)
        s.line(dx, by + L * sp + 6, dx + DOOR_W * sp, by + L * sp + 6, ink, 1.2, 'stroke-dasharray="6 3"')
        s.text(bx + W * sp / 2, by + L * sp / 2, f"T-10{i + 1}", 13, weight="bold", anchor="middle")
        s.text(bx + W * sp / 2, by + L * sp / 2 + 17, f"{fmt(W * H * L)} m³", 11, mu, anchor="middle")
        # exhaust stub
        ex, ey = Pp(bay_x(i) + W / 2, 1.2)
        s.add(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="5" fill="none" stroke="{hot}" stroke-width="1.6"/>')
    # manifold and skid
    a, b = Pp(bay_x(0) + W / 2, 1.2), Pp(19.6, 1.2)
    s.line(a[0], a[1], b[0], b[1], hot, 3)
    hx0, hy0 = Pp(18.6, 0.2)
    s.rect(hx0, hy0, 2.8 * sp, 4.0 * sp, p["b"], ink, 1.3, 'fill-opacity="0.6"')
    s.text(hx0 + 1.4 * sp, hy0 + 2.1 * sp, "HX-201", 10, anchor="middle", weight="bold")
    fx, fy = Pp(21.9, 1.4)
    s.rect(fx, fy, 1.2 * sp, 1.4 * sp, p["panel"], ink, 1.2)
    s.text(fx + 0.6 * sp, fy + 0.85 * sp, "K", 10, anchor="middle", weight="bold")
    bfx, bfy = Pp(19.0, 8.0)
    s.rect(bfx, bfy, 7.0 * sp, 8.0 * sp, p["d"], ink, 1.2)
    s.text(bfx + 3.5 * sp, bfy + 4.2 * sp, "Biofilter F-301", 11, anchor="middle", weight="bold")
    # section markers
    ay = Pp(0, L * 0.72)[1]
    s.line(px0 - 22, ay, px0 + X_ALL * sp + 22, ay, ink, 0.9, 'stroke-dasharray="14 4 3 4"')
    s.text(px0 - 30, ay + 4, "A", 13, weight="bold", anchor="end")
    s.text(px0 + X_ALL * sp + 30, ay + 4, "A", 13, weight="bold")
    bxm = Pp(bay_x(2) + W / 2, 0)[0]
    s.line(bxm, py0 - 6, bxm, Pp(0, L + 0.8)[1], ink, 0.9, 'stroke-dasharray="14 4 3 4"')
    s.text(bxm + 8, py0 - 4, "B", 13, weight="bold")
    # dimensions
    l0, l1 = Pp(0, L + T), Pp(X_ALL, L + T)
    s.dim(l0[0], l0[1], l1[0], l1[1], f"{fmt(X_ALL, 1)} overall", 34)
    b0, b1 = Pp(bay_x(0), L), Pp(bay_x(0) + W, L)
    s.dim(b0[0], b0[1], b1[0], b1[1], fmt(W, 1), 18, 11)
    r0, r1 = Pp(0, 0), Pp(0, L)
    s.dim(r0[0], r0[1], r1[0], r1[1], f"{fmt(L, 1)} inner", 30)
    dd0, dd1 = Pp(bay_x(1) + (W - DOOR_W) / 2, L + T), Pp(bay_x(1) + (W + DOOR_W) / 2, L + T)
    s.dim(dd0[0], dd0[1], dd1[0], dd1[1], f"door {fmt(DOOR_W, 1)}", 18, 11)

    # ---- section A-A --------------------------------------------------------
    sa, ax0, ay0 = 32.0, 740.0, 440.0          # ground line at ay0

    def Pa(x, z):
        return ax0 + x * sa, ay0 - z * sa

    s.text(ax0, Pa(0, SLAB + H + T)[1] - 30, "SECTION A-A", 12, mu, weight="bold", extra='letter-spacing="1.5"')
    gx0, gy0 = Pa(-0.6, 0)
    s.line(gx0, gy0, Pa(X_ALL + 0.6, 0)[0], gy0, ink, 1.4)
    x, y = Pa(0, SLAB)
    s.rect(Pa(0, 0)[0], y, X_ALL * sa, SLAB * sa, concrete, ink, 1.2)
    for i in range(N + 1):
        wx, wy = Pa(i * (W + T), SLAB + H)
        s.rect(wx, wy, T * sa, H * sa, concrete, ink, 1.2)
    rx, ry = Pa(0, SLAB + H + T)
    s.rect(rx, ry, X_ALL * sa, T * sa, concrete, ink, 1.2)
    for i in range(N):
        fx, fy = Pa(bay_x(i), SLAB + FILL)
        s.rect(fx, fy, W * sa, FILL * sa, p["timber_fill"], p["timber"], 1)
        for c in range(1, int(W / SPIGOT_PITCH)):
            cx, cy = Pa(bay_x(i) + c * SPIGOT_PITCH, SLAB)
            s.rect(cx - 2.5, cy, 5, 0.18 * sa, p["bg"], cool, 0.8)
        for xx in (1.6, 2.5, 3.4):
            a, b = Pa(bay_x(i) + xx, SLAB + 0.2), Pa(bay_x(i) + xx, SLAB + FILL + 0.7)
            s.line(a[0], a[1], b[0], b[1], cool, 1.2, 'marker-end="url(#arrCool)"')
        ex, ey = Pa(bay_x(i) + W / 2, SLAB + H + T)
        s.line(ex - 4, ey, ex - 4, ey - 26, hot, 1.4)
        s.line(ex + 4, ey, ex + 4, ey - 26, hot, 1.4)
    a, b = Pa(0, 0), Pa(0, SLAB + H + T)
    s.dim(a[0], a[1], b[0], b[1], f"{fmt(SLAB + H + T, 1)}", -30, 11)
    a, b = Pa(bay_x(0), SLAB), Pa(bay_x(0), SLAB + H)
    s.dim(a[0], a[1], b[0], b[1], f"{fmt(H, 1)} clear", 22, 11)
    a, b = Pa(bay_x(1), SLAB), Pa(bay_x(1), SLAB + FILL)
    s.dim(a[0], a[1], b[0], b[1], f"bed {fmt(FILL, 1)} avg", 22, 11)
    a, b = Pa(bay_x(2), 0), Pa(bay_x(2) + W, 0)
    s.dim(a[0], a[1], b[0], b[1], fmt(W, 1), 30, 11)
    s.text(Pa(X_ALL, 0)[0] + 20, Pa(0, SLAB / 2)[1] + 4, "plenum slab, channels at 0.5", 11, mu)
    s.text(Pa(X_ALL, 0)[0] + 20, Pa(0, SLAB + H + T / 2)[1] + 4, "200 concrete + 100 PIR", 11, mu)
    s.text(Pa(X_ALL, 0)[0] + 20, Pa(0, SLAB + H + T / 2)[1] + 20, f"U = {M['u_wall_w_m2k']:.2f} W/m²K", 11, mu)

    # ---- section B-B --------------------------------------------------------
    sb, bx0, by0 = 32.0, 740.0, 790.0

    def Pb(y, z):
        return bx0 + (y + T) * sb, by0 - z * sb

    s.text(bx0, Pb(0, SLAB + H + T + 1.2)[1] - 18, "SECTION B-B  (T-103)", 12, mu, weight="bold", extra='letter-spacing="1.5"')
    s.line(Pb(-T - 0.6, 0)[0], by0, Pb(L + 1.0, 0)[0], by0, ink, 1.4)
    x, y = Pb(-T, SLAB)
    s.rect(x, y, (L + T) * sb, SLAB * sb, concrete, ink, 1.2)
    x, y = Pb(-T, SLAB + H + T)
    s.rect(x, y, T * sb, (H + T) * sb, concrete, ink, 1.2)
    x, y = Pb(-T, SLAB + H + T)
    s.rect(x, y, (L + T) * sb, T * sb, concrete, ink, 1.2)
    x, y = Pb(L - 0.05, SLAB + H)
    s.rect(x, y, 0.1 * sb, (H - DOOR_H) * sb, concrete, ink, 1)
    x, y = Pb(L - 0.05, SLAB + DOOR_H)
    s.rect(x, y, 0.1 * sb, DOOR_H * sb, p["c"], ink, 1)
    x, y = Pb(0, SLAB + FILL)
    s.rect(x, y, L * sb, FILL * sb, p["timber_fill"], p["timber"], 1)
    x, y = Pb(0, SLAB)
    s.line(x, y - 2, x + L * sb, y - 2, cool, 1.2, 'stroke-dasharray="2 4"')
    for depth, label in ((OPS["fill_depth_m"], "fill, day 0"), (OPS["settled_depth_m"], "day 15")):
        lx0, ly0 = Pb(0, SLAB + depth)
        s.line(lx0, ly0, lx0 + L * sb, ly0, p["timber"], 1.2, 'stroke-dasharray="8 4"')
        s.text(lx0 + L * sb * 0.62, ly0 - 5, f"{label}: {depth:.1f} m", 11, p["timber"])
    # recirculation duct along the back and exhaust stub
    ex, ey = Pb(1.2, SLAB + H + T)
    s.rect(ex - 5, ey - 1.0 * sb, 10, 1.0 * sb, hot, hot, 1)
    s.text(ex + 12, ey - 0.7 * sb, f"exhaust Ø{DUCT_T}", 11, hot)
    a, b = Pb(0, SLAB + 0.15), Pb(-T - 0.4, SLAB + 0.15)
    s.line(b[0], b[1], a[0], a[1], cool, 2, 'marker-end="url(#arrCool)"')
    s.text(b[0] - 6, b[1] + 4, f"K-103 {fmt(M['air_per_tunnel_m3_h'], 0)} m³/h", 11, cool, anchor="end")
    a, b = Pb(0, 0), Pb(L, 0)
    s.dim(a[0], a[1], b[0], b[1], f"{fmt(L, 1)}", 30, 11)
    a, b = Pb(L, SLAB), Pb(L, SLAB + DOOR_H)
    s.dim(a[0], a[1], b[0], b[1], f"door {fmt(DOOR_H, 1)}", 18, 11)

    # ---- data table --------------------------------------------------------
    tx, ty = 80, 640
    rows = [
        ("Feedstock", f"{fmt(M['feedstock_t_per_day'], 1)} t/day, 15-day residence"),
        ("Tunnels", f"{N} × {fmt(W, 1)} × {fmt(H, 1)} × {fmt(L, 1)} m inner"),
        ("Material in tunnels", f"{fmt(M['solids_per_tunnel_m3'] * N)} m³ (model {fmt(M['gross_total_m3'])} m³ gross)"),
        ("Aeration", f"{fmt(M['air_m3_h'], 0)} m³/h, {M['air_changes_per_h']:.1f} vol/h"),
        ("Blowers", f"{N} × {M['fan_kw_per_tunnel']:.1f} kW at {fmt(M['fan_pressure_pa'])} Pa"),
        ("Exhaust ducts", f"Ø{DUCT_T} per tunnel, Ø{DUCT_M} manifold"),
        ("Envelope loss", f"{M['wall_loss_kw_per_tunnel']:.1f} kW per tunnel"),
        ("Heat-recovery duty", f"{fmt(M['duty_kw'])} kW, {M['heat_gwh_per_year']:.1f} GWh/yr"),
        ("Operation", f"staggered: one tunnel refilled every {OPS['stage_days']:.0f} days (CE-11)"),
    ]
    s.rect(tx - 12, ty - 22, 520, 30 + 24 * len(rows), p["bg"], p["faint"], 1, 'rx="6"')
    s.text(tx, ty, "DESIGN DATA", 10, mu, extra='letter-spacing="1.5"')
    for n, (kk, vv) in enumerate(rows):
        yy = ty + 24 + n * 24
        s.text(tx, yy, kk, 12, mu)
        s.text(tx + 170, yy, vv, 12)

    s.text(32, s.h - 30, "Indicative. Tunnel length rounded up from the model to the next 0.5 m; doors and slab are typical, not designed.", 12, mu)
    s.title_block("General arrangement", "CE-07")
    return s.render()


# ---------------------------------------------------------------------------
# CE-08  heat-recovery module
# ---------------------------------------------------------------------------
def recovery_module(p: dict) -> str:
    s = Svg(1600, 1000, p, "Exhaust-air heat-recovery module")
    header(s, "Exhaust-air heat-recovery module HX-201",
           "Saturated exhaust cools from 60 to 35 °C on plate-fin coils; most of the heat is the water vapour condensing.")
    ink, mu, hot, cool = p["ink"], p["muted"], p["hot"], p["cool"]

    # housing section
    x0, y0, w, h = 300, 210, 420, 540
    s.rect(x0, y0, w, h, p["panel"], ink, 1.8, 'rx="4"')
    s.rect(x0 - 10, y0 - 10, w + 20, h + 20, "none", ink, 1, 'stroke-dasharray="2 4"')
    s.text(x0 - 14, y0 - 16, "insulated casing", 11, mu, anchor="end")
    # inlet plenum
    s.rect(x0 + 40, y0 - 60, 120, 60, p["b"], ink, 1.4, 'fill-opacity="0.55"')
    s.text(x0 + 172, y0 - 34, f"exhaust in, Ø{DUCT_M}, {fmt(M['t_exhaust_c'])} °C saturated", 12, hot)
    s.path(f"M{x0 + 100},{y0 - 50} L{x0 + 100},{y0 + 26}", hot, 2.2, extra='marker-end="url(#arrHot)"')
    # wash spray bar
    s.line(x0 + 20, y0 + 44, x0 + w - 20, y0 + 44, cool, 2)
    for i in range(7):
        xx = x0 + 45 + i * 55
        s.path(f"M{xx},{y0 + 46} L{xx - 10},{y0 + 64} M{xx},{y0 + 46} L{xx + 10},{y0 + 64}", cool, 0.8)
    s.text(x0 + w + 16, y0 + 48, "wash spray bar (fouling: dust, NH₃ salts)", 11, mu)
    # coil bank: 3 coils in series on the water side
    for c in range(3):
        cy = y0 + 90 + c * 125
        s.rect(x0 + 20, cy, w - 40, 100, p["bg"], ink, 1.3)
        for f in range(60):
            xx = x0 + 26 + f * (w - 52) / 59
            s.line(xx, cy + 4, xx, cy + 96, mu, 0.4)
        for r in range(4):
            yy = cy + 17 + r * 22
            for t in range(8):
                xx = x0 + 50 + t * 46
                s.add(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="5" fill="{p["bg"]}" stroke="{hot}" stroke-width="1.4"/>')
        s.text(x0 + w + 16, cy + 55, f"coil {c + 1}", 12, weight="bold")
        if c < 2:   # series connection on the water side
            s.path(f"M{x0 + w - 20},{cy + 100 + 12} L{x0 + w - 8},{cy + 100 + 12}", hot, 0)
    s.text(x0 + w + 80, y0 + 270, f"{fmt(M['hx_area_m2'])} m² total", 11, mu)
    s.text(x0 + w + 80, y0 + 286, "Al fins on stainless tubes", 11, mu)
    # air leaves at the bottom, to the fan
    s.path(f"M{x0 + w - 60},{y0 + 478} L{x0 + w + 150},{y0 + 478}", cool, 2.2, extra='marker-end="url(#arrCool)"')
    s.text(x0 + w + 30, y0 + 466, f"{fmt(M['t_air_out_c'])} °C saturated → fan → biofilter", 12, cool)
    # condensate tray, trap and drain
    s.rect(x0 + 10, y0 + h - 30, w - 20, 20, p["c"], ink, 1.2)
    xm = x0 + w / 2
    s.path(f"M{xm},{y0 + h - 10} L{xm},{y0 + h + 40} Q{xm},{y0 + h + 70} {xm + 30},{y0 + h + 70} "
           f"Q{xm + 60},{y0 + h + 70} {xm + 60},{y0 + h + 40} L{xm + 60},{y0 + h + 30} L{xm + 140},{y0 + h + 30}",
           cool, 2, extra='marker-end="url(#arrCool)"')
    s.text(xm + 150, y0 + h + 26, f"condensate ≈ {M['condensate_m3_h']:.2f} m³/h", 12, cool)
    s.text(xm + 150, y0 + h + 44, "→ TK-401, re-used to wet the beds", 12, cool)
    s.text(xm - 10, y0 + h + 92, "water-seal trap", 11, mu, anchor="end")
    s.text(x0 + w - 10, y0 + h - 40, "access door", 11, mu, anchor="end")
    # water connections: counterflow, cold in at the bottom coil, hot out at the top
    s.path(f"M{x0 - 110},{y0 + 390} L{x0 + 20},{y0 + 390}", cool, 3, extra='marker-end="url(#arrCool)"')
    s.text(x0 - 114, y0 + 394, f"{fmt(M['t_return_c'])} °C in", 12, cool, anchor="end")
    s.path(f"M{x0 + 20},{y0 + 140} L{x0 - 110},{y0 + 140}", hot, 3, extra='marker-end="url(#arrHot)"')
    s.text(x0 - 114, y0 + 144, f"{fmt(M['t_supply_c'])} °C out", 12, hot, anchor="end")
    s.text(x0 - 40, y0 + 260, f"{fmt(M['water_m3_h'], 1)} m³/h", 12, mu, anchor="end")
    s.text(x0 - 40, y0 + 276, "water counterflow", 12, mu, anchor="end")
    s.path(f"M{x0 - 30},{y0 + 360} L{x0 - 30},{y0 + 170}", mu, 1, extra='marker-end="url(#arr)"')
    s.path(f"M{x0 + 200},{y0 + 70} L{x0 + 200},{y0 + 86}", ink, 1, extra='marker-end="url(#arr)"')
    s.text(x0 + 212, y0 + 82, "air down", 10.5, mu)

    # ---- enthalpy chart -----------------------------------------------------
    cx0, cy0, cw, ch = 1000, 190, 480, 360
    t0, t1, h0, h1 = 20.0, 65.0, 0.0, 600.0

    def C(t, hh):
        return cx0 + (t - t0) / (t1 - t0) * cw, cy0 + ch - (hh - h0) / (h1 - h0) * ch

    s.text(cx0, cy0 - 26, "WHY LATENT HEAT DOMINATES", 11, mu, weight="bold", extra='letter-spacing="1.5"')
    s.rect(cx0, cy0, cw, ch, p["bg"], p["faint"], 1)
    for t in range(20, 66, 5):
        x, _ = C(t, 0)
        s.line(x, cy0, x, cy0 + ch, p["faint"], 0.6)
        s.text(x, cy0 + ch + 18, str(t), 11, mu, anchor="middle")
    for hh in range(0, 601, 100):
        _, y = C(t0, hh)
        s.line(cx0, y, cx0 + cw, y, p["faint"], 0.6)
        s.text(cx0 - 8, y + 4, str(hh), 11, mu, anchor="end")
    s.text(cx0 + cw / 2, cy0 + ch + 40, "air temperature, °C", 12, mu, anchor="middle")
    s.text(cx0 - 46, cy0 + ch / 2, "kJ per kg dry air", 12, mu, anchor="middle",
           extra=f'transform="rotate(-90 {cx0 - 46} {cy0 + ch / 2})"')
    sat = " ".join(f"{'M' if i == 0 else 'L'}{C(t0 + i * 0.5, enthalpy_kj_per_kg(t0 + i * 0.5))[0]:.1f},"
                   f"{C(t0 + i * 0.5, enthalpy_kj_per_kg(t0 + i * 0.5))[1]:.1f}" for i in range(91))
    ta, tb = M["t_air_out_c"], M["t_exhaust_c"]
    ha, hb = enthalpy_kj_per_kg(ta), enthalpy_kj_per_kg(tb)
    s.path(sat, hot, 2.4)
    (dx0, dy0), (dx1, dy1) = C(ta, ha), C(tb, ha + 1.006 * (tb - ta))
    s.line(dx0, dy0, dx1, dy1, mu, 1.4, 'stroke-dasharray="5 4"')
    (xa, ya), (xb, yb) = C(ta, ha), C(tb, hb)
    s.add(f'<circle cx="{xb:.1f}" cy="{yb:.1f}" r="5" fill="{hot}"/>')
    s.add(f'<circle cx="{xa:.1f}" cy="{ya:.1f}" r="5" fill="{cool}"/>')
    s.line(xb + 14, yb, xb + 14, ya, ink, 1.2, 'marker-start="url(#arr)" marker-end="url(#arr)"')
    s.line(xa, ya, xb + 14, ya, ink, 0.6, 'stroke-dasharray="3 3"')
    s.text(xb + 24, (ya + yb) / 2 - 6, f"Δh = {M['enthalpy_drop_kj_kg']:.0f} kJ/kg", 12, weight="bold")
    s.text(xb + 24, (ya + yb) / 2 + 12, f"{M['latent_share'] * 100:.0f} % latent", 12)
    s.text(C(28, 0)[0], C(28, enthalpy_kj_per_kg(50))[1], "saturated air", 12, hot)
    s.text(dx1 - 4, ya + 26, "the same cooling of dry air:", 11.5, mu, anchor="end")
    s.text(dx1 - 4, ya + 42, f"sensible only, {1.006 * (tb - ta):.0f} kJ/kg", 11.5, mu, anchor="end")

    # ---- data ---------------------------------------------------------------
    tx, ty = 1000, 650
    rows = [("Duty", f"{fmt(M['duty_kw'])} kW (heating-season mean)"),
            ("Air", f"{M['air_dry_kg_s']:.2f} kg/s dry, {fmt(M['air_m3_h'], 0)} m³/h"),
            ("Water", f"{fmt(M['t_return_c'])} → {fmt(M['t_supply_c'])} °C, {fmt(M['water_m3_h'], 1)} m³/h"),
            ("Pinch", f"{M['pinch_k']:.1f} K at the cold end"),
            ("Area", f"{fmt(M['hx_area_m2'])} m², scaled from 23.3 kW / 9.2 m²"),
            ("", "measured on a dairy-farm composter (Kojima 2022)")]
    s.text(tx, ty, "DESIGN POINT", 10, mu, extra='letter-spacing="1.5"')
    for n, (kk, vv) in enumerate(rows):
        s.text(tx, ty + 24 + n * 22, kk, 12, mu)
        s.text(tx + 70, ty + 24 + n * 22, vv, 12)

    s.text(32, s.h - 30, "Indicative. Plate-fin area scaled from one measured farm; a vendor selection replaces it at detail design.", 12, mu)
    s.title_block("Heat-recovery module", "CE-08")
    return s.render()


# ---------------------------------------------------------------------------
# CE-09  process P&ID
# ---------------------------------------------------------------------------
def process_pid(p: dict) -> str:
    s = Svg(1600, 1000, p, "Farm-scale P&amp;ID")
    header(s, "Farm-scale process: air and water P&amp;ID",
           "Per-tunnel aeration with recirculation, shared exhaust to heat recovery and biofilter, heat-metered water loop.")
    ink, mu, hot, cool, g = p["ink"], p["muted"], p["hot"], p["cool"], p["green"]

    def inst(x, y, a, b, col=g):
        s.add(f'<circle cx="{x}" cy="{y}" r="20" fill="{p["bg"]}" stroke="{col}" stroke-width="1.4"/>')
        s.line(x - 20, y, x + 20, y, col, 0.8)
        s.text(x, y - 5, a, 10, col, weight="bold", anchor="middle")
        s.text(x, y + 13, b, 10, col, anchor="middle")

    def damper(x, y, tag, lx=0, ly=-14, anchor="middle"):
        s.line(x - 9, y + 9, x + 9, y - 9, ink, 1.6)
        s.add(f'<circle cx="{x}" cy="{y}" r="2.5" fill="{ink}"/>')
        s.text(x + lx, y + ly, tag, 10, mu, anchor=anchor)

    def sig(x1, y1, x2, y2):
        s.line(x1, y1, x2, y2, g, 1, 'stroke-dasharray="3 3"')

    def blower(x, y, tag):
        s.add(f'<circle cx="{x}" cy="{y}" r="18" fill="{p["bg"]}" stroke="{ink}" stroke-width="1.5"/>')
        s.path(f"M{x - 8},{y - 10} L{x + 10},{y} L{x - 8},{y + 10}", ink, 1.4)
        s.text(x, y + 36, tag, 11, weight="bold", anchor="middle")

    # tunnels
    for i in range(N):
        y = 170 + i * 210
        s.rect(220, y, 300, 150, p["b"] if i == 1 else p["a"] if i == 0 else p["c"], ink, 1.6,
               'rx="6" fill-opacity="0.55"')
        s.text(240, y + 26, f"T-10{i + 1}  tunnel", 14, weight="bold")
        s.text(240, y + 46, ["now on day 0-5: heating up", "now on day 5-10: hot, 55-70 °C", "now on day 10-15: cooling"][i], 12, mu)
        s.line(230, y + 128, 510, y + 128, cool, 1.2, 'stroke-dasharray="2 3"')
        s.text(500, y + 120, "spigot floor", 10, cool, anchor="end")
        # supply blower and dampers
        blower(130, y + 128, f"K-10{i + 1}")
        s.path(f"M148,{y + 128} L230,{y + 128}", cool, 2, extra='marker-end="url(#arrCool)"')
        s.path(f"M60,{y + 128} L112,{y + 128}", cool, 2)
        damper(80, y + 128, f"FD-10{i + 1}", 0, 26)
        s.text(40, y + 132, "air", 11, mu, anchor="end")
        # recirculation from the headspace back to the blower
        s.path(f"M220,{y + 30} L170,{y + 30} L170,{y + 80} L130,{y + 80} L130,{y + 110}", mu, 1.6,
               extra='marker-end="url(#arr)" stroke-dasharray="6 4"')
        damper(150, y + 80, f"RD-10{i + 1}", -6, -12, "end")
        # exhaust
        s.path(f"M520,{y + 40} L640,{y + 40}", hot, 2.4)
        damper(580, y + 40, f"XD-10{i + 1}")
        # instruments
        inst(300, y + 80, "TT", f"10{i + 1}")
        inst(370, y + 80, "OT", f"10{i + 1}")
        inst(440, y + 80, "PT", f"10{i + 1}")
        s.text(300, y + 116, "×3 core probes", 9.5, mu, anchor="middle")
    # manifold
    s.path("M640,210 L640,670", hot, 4)
    s.path("M640,440 L720,440", hot, 4, extra='marker-end="url(#arrHot)"')
    inst(690, 380, "TT", "201")
    inst(690, 500, "MT", "201")
    sig(670, 380, 640, 380)
    sig(670, 500, 640, 500)
    # HX-201
    s.rect(724, 360, 160, 170, p["panel"], ink, 1.6, 'rx="4"')
    s.path("M740,380 L868,400 L740,420 L868,440 L740,460 L868,480 L740,500", hot, 1.6)
    s.text(804, 334, "HX-201", 12, weight="bold", anchor="middle")
    s.text(804, 350, f"{fmt(M['hx_area_m2'])} m² plate-fin", 11, mu, anchor="middle")
    # condensate
    s.path("M800,530 L800,600 L780,600", cool, 1.6, extra='stroke-dasharray="5 3" marker-end="url(#arrCool)"')
    s.rect(680, 580, 96, 46, p["c"], ink, 1.3, 'rx="4"')
    s.text(728, 608, "TK-401", 11, weight="bold", anchor="middle")
    s.text(680, 646, "condensate → bed wetting", 10.5, mu)
    # cooled exhaust to biofilter, via the exhaust fan
    s.path("M860,530 L860,640", cool, 2.4)
    s.add(f'<circle cx="860" cy="664" r="18" fill="{p["bg"]}" stroke="{ink}" stroke-width="1.5"/>')
    s.path("M850,654 L870,664 L850,674", ink, 1.4)
    s.text(886, 668, "K-201 booster", 11, weight="bold")
    s.path("M860,682 L860,760", cool, 2.4, extra='marker-end="url(#arrCool)"')
    s.rect(780, 764, 220, 80, p["d"], ink, 1.4, 'rx="4"')
    s.text(890, 800, "F-301 biofilter", 12, weight="bold", anchor="middle")
    s.text(890, 818, f"wood chip, {fmt(M['biofilter_m2'])} m²", 10.5, mu, anchor="middle")
    s.path("M1000,804 L1060,804", mu, 1.4, extra='marker-end="url(#arr)"')
    s.text(1068, 808, "clean air out", 11, mu)
    inst(720, 900, "AT", "301")
    s.text(692, 904, "NH₃", 10.5, mu, anchor="end")
    sig(740, 890, 780, 830)

    # water loop
    s.path("M884,380 L1180,380", hot, 3, extra='marker-end="url(#arrHot)"')
    s.path("M1180,520 L884,520", cool, 3, extra='marker-end="url(#arrCool)"')
    inst(960, 334, "TT", "202")
    inst(960, 574, "TT", "203")
    inst(1040, 574, "FT", "201")
    sig(960, 354, 960, 380)
    sig(960, 554, 960, 520)
    sig(1040, 554, 1040, 520)
    s.add(f'<circle cx="1110" cy="520" r="18" fill="{p["bg"]}" stroke="{ink}" stroke-width="1.5"/>')
    s.poly([(1120, 510), (1100, 520), (1120, 530)], ink, ink, 1)
    s.text(1110, 556, "P-201 VFD", 11, weight="bold", anchor="middle")
    # buffer tank and users
    s.rect(1184, 330, 90, 240, p["panel"], ink, 1.6, 'rx="30"')
    s.text(1229, 450, "TK-201", 11, weight="bold", anchor="middle")
    s.text(1229, 466, "buffer", 10.5, mu, anchor="middle")
    s.path("M1274,380 L1380,380", hot, 3, extra='marker-end="url(#arrHot)"')
    s.path("M1380,520 L1274,520", cool, 3, extra='marker-end="url(#arrCool)"')
    s.poly([(1310, 368), (1330, 380), (1310, 392)], p["bg"], ink, 1.3)
    s.poly([(1350, 368), (1330, 380), (1350, 392)], p["bg"], ink, 1.3)
    s.text(1330, 360, "TV-201", 10.5, anchor="middle", weight="bold")
    s.path("M1330,392 L1330,520", mu, 1.4, extra='stroke-dasharray="6 4"')
    s.rect(1384, 330, 180, 240, p["panel"], ink, 1.6, 'rx="6"')
    s.text(1474, 370, "Farm heat users", 13, weight="bold", anchor="middle")
    for n, t in enumerate(["dairy hot water", "barn / greenhouse", "grain or hay drying", "back-up boiler stays"]):
        s.text(1474, 396 + n * 20, t, 11, mu, anchor="middle")
    s.text(1030, 300, f"{fmt(M['t_supply_c'])}/{fmt(M['t_return_c'])} °C · {fmt(M['water_m3_h'], 1)} m³/h · "
                      f"Q = ṁ·cp·(TT-202 − TT-203)", 11.5, ink)

    # legend
    lx, ly = 1250, 720
    for n, (col, dash, label) in enumerate([(cool, "", "process air in / cooled air"),
                                            (hot, "", "hot exhaust / supply water"),
                                            (mu, "6 4", "recirculation / by-pass"),
                                            (g, "3 3", "instrument signal")]):
        s.line(lx, ly + n * 22, lx + 40, ly + n * 22, col, 2.4 if not dash else 1.4,
               f'stroke-dasharray="{dash}"' if dash else "")
        s.text(lx + 50, ly + n * 22 + 4, label, 11.5)
    s.text(lx, ly + 100, "TT temperature · OT oxygen · PT pressure", 11, mu)
    s.text(lx, ly + 116, "MT humidity · FT flow · AT ammonia", 11, mu)

    s.text(32, s.h - 30, "Indicative. Batches are staggered 5 days apart, so the three tunnels are always in different phases (CE-11). Tags are used by CE-10.", 12, mu)
    s.title_block("Process P&amp;ID", "CE-09")
    return s.render()


# ---------------------------------------------------------------------------
# CE-10  control logic
# ---------------------------------------------------------------------------
def control(p: dict) -> str:
    s = Svg(1600, 1000, p, "Control and instrumentation")
    header(s, "Control and instrumentation",
           "The compost process has priority. Heat recovery takes what the process gives it and never overrides aeration.")
    ink, mu, hot, cool, g = p["ink"], p["muted"], p["hot"], p["cool"], p["green"]

    def card(x, y, w, h, title, lines, fill=None, tcol=None):
        s.rect(x, y, w, h, fill or p["panel"], ink, 1.4, 'rx="8"')
        s.text(x + 16, y + 28, title, 14, tcol or ink, weight="bold")
        for n, t in enumerate(lines):
            s.text(x + 16, y + 52 + n * 19, t, 11.5, mu)

    def arrow(d, col=None):
        s.path(d, col or ink, 1.6, extra='marker-end="url(#arr)"')

    # inputs
    card(60, 130, 330, 230, "Inputs (per tunnel)", [
        "TT-10x a-c   core temperature, 3 probes",
        "OT-10x       O₂ in the headspace",
        "PT-10x       plenum pressure",
        "MT-201       exhaust humidity",
        "TT-201       exhaust temperature",
        "TT-202/203   water out / in",
        "FT-201       water flow",
        "AT-301       NH₃ after the biofilter",
        "door switches, blower faults",
    ])
    card(60, 390, 330, 150, "Outputs", [
        "K-10x       blower speed (VFD)",
        "RD/FD-10x   recirculation / fresh air",
        "XD-10x      exhaust damper",
        "P-201       water pump speed (VFD)",
        "TV-201      by-pass to the heat users",
    ])
    # PLC
    card(470, 130, 280, 416, "PLC", [
        "scan 1 s, log 1 min",
        "",
        "Runs one batch per tunnel:",
        "load → heat-up → sanitise",
        "→ stabilise → cool → unload",
        "tunnels staggered 5 days (CE-11)",
        "",
        "Same CSV schema and cleaning",
        "pipeline as the prototype logger",
        "(model/compost_energy/clean.py)",
    ], p["bg"])
    arrow("M390,245 L466,245")
    arrow("M466,465 L394,465")

    # control loops
    loops = [
        ("1  Temperature", ["core median → blower speed and recirculation", "setpoint 55 → 65 °C over the batch", "more fresh air when T rises: cools by evaporation"], p["b"]),
        ("2  Oxygen floor", ["O₂ &lt; 5 %: open fresh air, override loop 1", "keeps the bed aerobic: no CH₄, less odour"], p["c"]),
        ("3  Sanitisation", ["hold ≥ 55 °C for ≥ 3 days (US EPA PFRP,", "in-vessel); timer resets if any probe drops below"], p["a"]),
        ("4  Heat recovery", [f"pump holds TT-202 ≥ {fmt(M['t_supply_c'])} °C; TV-201 by-passes if lower",
                              "exhaust flow is set by loops 1-3, never by heat demand"], p["d"]),
    ]
    for n, (title, lines, fill) in enumerate(loops):
        y = 130 + n * 106
        s.rect(830, y, 420, 98, fill, ink, 1.4, 'rx="8" fill-opacity="0.45"')
        s.text(846, y + 28, title, 14, weight="bold")
        for m, t in enumerate(lines):
            s.text(846, y + 52 + m * 19, t, 11.5, ink)
        arrow(f"M750,{y + 46} L826,{y + 46}")
    s.path("M1250,176 L1300,176 L1300,282 L1254,282", g, 1.4, extra='stroke-dasharray="4 3" marker-end="url(#arrGreen)"')
    s.text(1310, 232, "loop 2 overrides 1", 11, g)
    s.path("M1250,388 L1300,388 L1300,494 L1254,494", g, 1.4, extra='stroke-dasharray="4 3" marker-end="url(#arrGreen)"')
    s.text(1310, 432, "1-3 set the air", 11, g)
    s.text(1310, 448, "that 4 receives", 11, g)

    # batch profile
    bx, by, bw, bh = 470, 610, 780, 200
    s.text(bx, by - 14, "BATCH SETPOINT, ONE TUNNEL (15 DAYS)", 10, mu, extra='letter-spacing="1.5"')
    s.rect(bx, by, bw, bh, p["bg"], p["faint"], 1)

    def B(day, t):
        return bx + day / 15 * bw, by + bh - (t - 10) / 65 * bh

    for t in (20, 40, 55, 65):
        _, y = B(0, t)
        s.line(bx, y, bx + bw, y, p["faint"], 0.6)
        s.text(bx - 8, y + 4, f"{t}", 10.5, mu, anchor="end")
    for d in range(0, 16, 3):
        x, _ = B(d, 10)
        s.text(x, by + bh + 16, f"d{d}", 10.5, mu, anchor="middle")
    pts = [(0, 20), (1.5, 45), (2.5, 55), (5.5, 55), (6, 62), (11, 62), (13, 45), (15, 32)]
    d = " ".join(f"{'M' if i == 0 else 'L'}{B(*q)[0]:.1f},{B(*q)[1]:.1f}" for i, q in enumerate(pts))
    s.path(d, hot, 2.4)
    x0, _ = B(2.5, 0)
    x1, _ = B(5.5, 0)
    s.rect(x0, by, x1 - x0, bh, p["a"], "none", 0, 'fill-opacity="0.35"')
    s.text((x0 + x1) / 2, by + 18, "sanitise", 11, anchor="middle", weight="bold")
    s.text(B(8.5, 0)[0], B(0, 64)[1] - 8, "stabilise: max heat to HX-201", 11, hot, anchor="middle")
    s.text(B(14, 0)[0], B(0, 40)[1] - 8, "cool, unload", 11, cool, anchor="middle")
    s.text(bx + bw + 10, by + bh / 2, "°C", 11, mu)

    card(60, 570, 330, 175, "Alarms and trips", [
        "probe disagreement > 10 K",
        "O₂ &lt; 3 % for 30 min",
        "plenum ΔP high (blocked floor)",
        "NH₃ high after biofilter",
        "door open: blower to minimum",
        "frost: pump runs, TV-201 to by-pass",
    ])

    s.text(32, s.h - 30, "Setpoints are starting values from composting practice; they are tuned on the pilot. The temperature profile is illustrative, not simulated.", 12, mu)
    s.title_block("Control and instrumentation", "CE-10")
    return s.render()


# ---------------------------------------------------------------------------
# CE-11  operating modes: staggered batches vs transfer between tunnels
# ---------------------------------------------------------------------------
def operating_modes_sheet(p: dict) -> str:
    s = Svg(1600, 1000, p, "Operating modes")
    header(s, "How a batch moves through the phases",
           "A: each tunnel runs the whole cycle in place, staggered 5 days apart (base design). "
           "B: a loader moves each batch from tunnel to tunnel.")
    ink, mu = p["ink"], p["muted"]
    stage = OPS["stage_days"]
    phases = [(p["a"], "heat-up"), (p["b"], "hot: sanitise, max heat"), (p["c"], "cooling")]
    days = 30
    gx, gw, rh = 150, 720, 34

    def X(day):
        return gx + day / days * gw

    def axis(y0):
        for d in range(0, days + 1, 5):
            s.line(X(d), y0 - 8, X(d), y0 + 3 * (rh + 10), p["faint"], 0.8)
            s.text(X(d), y0 + 3 * (rh + 10) + 16, f"d{d}", 11, mu, anchor="middle")

    def block(t, d0, d1, phase, label, y0):
        d0c, d1c = max(d0, 0), min(d1, days)
        if d1c <= d0c:
            return
        y = y0 + t * (rh + 10)
        s.rect(X(d0c), y, X(d1c) - X(d0c), rh, phase[0], ink, 0.9, 'fill-opacity="0.8"')
        if X(d1c) - X(d0c) > 40:
            s.text((X(d0c) + X(d1c)) / 2, y + rh / 2 + 4, label, 11, anchor="middle")

    def rows(y0):
        for t in range(N):
            s.text(gx - 14, y0 + t * (rh + 10) + rh / 2 + 4, f"T-10{t + 1}", 12, weight="bold", anchor="end")

    def loader(x, y, col=None):
        s.poly([(x - 7, y - 12), (x + 7, y - 12), (x, y - 2)], col or ink, col or ink, 1)

    # ---- A: staggered -------------------------------------------------------
    ya = 180
    s.text(60, ya - 34, "A  STAGGERED BATCHES  (base design)", 12, weight="bold", extra='letter-spacing="1"')
    axis(ya)
    rows(ya)
    for k in range(-2, 6):
        t, start = k % N, k * stage
        for j, ph in enumerate(phases):
            block(t, start + j * stage, start + (j + 1) * stage, ph, f"batch {k + 3}" if j == 0 else "", ya)
    for k in range(0, 6):
        loader(X(k * stage), ya + (k % N) * (rh + 10))
    s.text(X(0), ya + 3 * (rh + 10) + 36,
           "▼ loader empties one tunnel to the maturation hall and refills it, every 5 days. The batch never moves inside.",
           11.5, mu)

    # ---- B: transfer --------------------------------------------------------
    yb = 470
    s.text(60, yb - 34, "B  TRANSFER BETWEEN TUNNELS  (one phase per tunnel)", 12, weight="bold", extra='letter-spacing="1"')
    axis(yb)
    rows(yb)
    for k in range(-2, 6):
        for t in range(N):
            start = (k + t) * stage
            block(t, start, start + stage, phases[t], f"batch {k + 3}", yb)
    for k in range(1, 6):
        x = X(k * stage)
        for t in range(N - 1):
            y1 = yb + t * (rh + 10) + rh / 2
            d = f"M{x - 18},{y1} C{x + 2},{y1} {x - 2},{y1 + rh + 10} {x + 16},{y1 + rh + 10}"
            s.path(d, p["bg"], 6)
            s.path(d, p["hot"], 2, extra='marker-end="url(#arrHot)"')
        loader(x, yb)
    s.text(X(0), yb + 3 * (rh + 10) + 36,
           "▼ every 5 days: empty T-103, move T-102 → T-103 and T-101 → T-102 (hot, open-air moves), refill T-101.",
           11.5, mu)

    # legend
    ly = 700
    for n, (col, label) in enumerate(phases):
        s.rect(60 + n * 230, ly, 26, 16, col, ink, 0.9, 'fill-opacity="0.8"')
        s.text(96 + n * 230, ly + 13, label, 12)
    s.text(60, ly + 44, f"Batch = {fmt(OPS['batch_t'])} t ({fmt(OPS['batch_m3'])} m³) of fresh feedstock. "
                        f"In A it fills a tunnel to {OPS['fill_depth_m']:.1f} m and settles to {OPS['settled_depth_m']:.1f} m by day 15.", 12, mu)
    s.text(60, ly + 62, "Phases drawn as 5-day blocks for clarity; the control setpoints are in CE-10.", 12, mu)

    # ---- comparison ---------------------------------------------------------
    a, b = OPS["staggered"], OPS["transfer"]
    tx, ty = 960, 150
    rows_ = [
        ("", "A  staggered", "B  transfer"),
        ("Loader work", f"{fmt(a['t_per_day'])} t/day", f"{fmt(b['t_per_day'])} t/day"),
        ("Loader time", f"{a['loader_h_per_day']:.1f} h/day", f"{b['loader_h_per_day']:.1f} h/day"),
        ("Diesel", f"{fmt(a['diesel_l_per_day'])} L/day", f"{fmt(b['diesel_l_per_day'])} L/day"),
        ("Hot moves per batch", "0", f"{b['hot_transfers_per_batch']}"),
        ("Heat released in moves", "none", f"≈ {fmt(b['released_kw'])} kW ({OPS['transfer_released_share'] * 100:.1f} % of duty)"),
        ("Exhaust to HX-201", "blend of 3 tunnels", "steady from T-102"),
        ("Tunnel design", "3 identical", "can specialise each"),
        ("Remixing", "once, at loading", "at every move"),
        ("Net value", f"€{a['net_eur'] / 1000:,.0f}k/yr", f"€{b['net_eur'] / 1000:,.0f}k/yr"),
    ]
    c1, c2, c3 = tx, tx + 190, tx + 360
    s.rect(tx - 16, ty - 26, 640, 30 * len(rows_) + 12, p["bg"], p["faint"], 1, 'rx="6"')
    for n, (k, va, vb) in enumerate(rows_):
        y = ty + n * 30
        head = n == 0
        last = n == len(rows_) - 1
        if n:
            s.line(tx - 16, y - 20, tx + 624, y - 20, p["faint"], 0.8)
        s.text(c1, y, k, 12, mu)
        s.text(c2, y, va, 12.5, weight="bold" if head or last else "normal")
        s.text(c3, y, vb, 12.5, weight="bold" if head or last else "normal")

    ry = ty + 30 * len(rows_) + 20
    s.rect(tx - 16, ry, 640, 148, p["d"], ink, 1.2, 'rx="6" fill-opacity="0.45"')
    s.text(tx, ry + 28, "Recommendation: A as the base design", 14, weight="bold")
    for n, t in enumerate([
        "Half the loader work, no hot material in the open, identical tunnels.",
        "The patent's one-chamber-per-phase idea survives as a control scheme:",
        "each tunnel passes through the phases in time instead of in space.",
        "B is worth a pilot trial only if remixing at day 5 and 10 proves",
        "to raise the temperature or the heat recovered.",
    ]):
        s.text(tx, ry + 54 + n * 18, t, 12)

    s.text(32, s.h - 30, f"Assumptions in model/compost_energy/industrial.py (Handling): 0.25 L diesel/t, 120 t/h, 10 K lost per hot move, "
                         "30 % mass loss over 15 days. Routine fill/empty is inside the €100k operating cost.", 11.5, mu)
    s.title_block("Operating modes", "CE-11")
    return s.render()


DRAWINGS = {
    "farm-unit-cutaway": unit_cutaway,
    "farm-unit-ga": general_arrangement,
    "heat-recovery-module": recovery_module,
    "farm-process-pid": process_pid,
    "farm-control": control,
    "farm-operating-modes": operating_modes_sheet,
}
