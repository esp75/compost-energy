"""Drawings CE-06..CE-14: the farm-scale unit.

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

from compost_energy import configurations as CFG  # noqa: E402
from compost_energy import process as PROC  # noqa: E402
from compost_energy.industrial import enthalpy_kj_per_kg, layout, operating_modes, size  # noqa: E402
from make_drawings import MONO, Svg, header  # noqa: E402

M = size()
OPS = operating_modes()
BATCH = PROC.run_batch()
PH = {ph["phase"]: ph for ph in PROC.phases(BATCH)}
T45 = PH["mesophilic"]["end"]                   # day the bed passes 45 °C
COOL = PH["cooling"]["start"]                   # day the cooling setpoint starts

# ---- buildable geometry (m), shared with hardware/cad ----------------------
G = layout()
LAY = G["layout"]
W = G["width_m"]                                # 5.0 inner
H = G["height_m"]                               # 4.0 inner
L = G["length_m"]                               # 12.5 inner, rounded up from the model
FILL = M["fill_depth_m"]                        # 2.0 average bed
T = LAY.wall_m                                  # 200 concrete + 100 PIR
SLAB = LAY.slab_m                               # plenum slab under the spigot floor
N = M["n_tunnels"]
X_ALL = G["overall_x_m"]                        # 21.5 overall
DOOR_W, DOOR_H = LAY.door_w_m, LAY.door_h_m
SPIGOT_PITCH = LAY.spigot_pitch_m


def bay_x(i: int) -> float:
    """Inner left wall of tunnel i (0-based)."""
    return T + i * (W + T)


def fmt(v: float, nd: int = 0) -> str:
    return f"{v:,.{nd}f}"


def eur(v: float) -> str:
    """k€ per year with a real minus sign."""
    return ("−" if v < 0 else "") + f"€{abs(v) / 1e3:,.0f}k/yr"


DUCT_T = 355    # per tunnel, at its blower's peak (3,570 m³/h, 10 m/s)
DUCT_M = 560    # manifold, at the plant's peak exhaust


# ---------------------------------------------------------------------------
# CE-06  isometric cutaway
# ---------------------------------------------------------------------------
def unit_cutaway(p: dict) -> str:
    s = Svg(1600, 1000, p, "Farm-scale unit - isometric cutaway")
    header(s, "Farm-scale unit: isometric cutaway",
           f"{N} aerated tunnels, {fmt(M['gross_total_m3'])} m³ in all, with heat recovered from the exhaust air. "
           f"T-10{N} roof and side wall cut away.")
    ink, mu = p["ink"], p["muted"]
    k, ox, oy = 25.0, 400.0, 290.0
    c30 = math.cos(math.radians(30))

    def P(x, y, z):
        return (ox + (x - y) * c30 * k, oy + (x + y) * 0.5 * k - z * k)

    def box(x0, x1, y0, y1, z0, z1, top, right, left, sw=1.1, stroke=None, op=1.0):
        stroke = stroke or ink
        e = f'fill-opacity="{op}"'
        s.poly([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], left, stroke, sw, e)
        s.poly([P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], right, stroke, sw, e)
        s.poly([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], top, stroke, sw, e)

    def cylinder(cx, cy, r, z0, z1, fill, stroke=None):
        stroke = stroke or ink
        ring = [(cx + r * math.cos(t / 36 * 2 * math.pi), cy + r * math.sin(t / 36 * 2 * math.pi)) for t in range(36)]
        # silhouette: the two tangents seen in the iso view are at +45 and -135 degrees in plan
        ta, tb = math.radians(45), math.radians(225)
        a0, a1 = P(cx + r * math.cos(ta), cy - r * math.sin(ta), z0), P(cx + r * math.cos(ta), cy - r * math.sin(ta), z1)
        b0, b1 = P(cx + r * math.cos(tb), cy - r * math.sin(tb), z0), P(cx + r * math.cos(tb), cy - r * math.sin(tb), z1)
        bottom = [P(x, y, z0) for x, y in ring]
        s.poly(bottom, fill, stroke, 1.1)
        s.poly([a0, a1, b1, b0], fill, "none", 0)
        s.line(a0[0], a0[1], a1[0], a1[1], stroke, 1.1)
        s.line(b0[0], b0[1], b1[0], b1[1], stroke, 1.1)
        s.poly([P(x, y, z1) for x, y in ring], fill, stroke, 1.1)

    def seg(a, b, col=None, w=1.0, extra=""):
        (x1, y1), (x2, y2) = P(*a), P(*b)
        s.line(x1, y1, x2, y2, col or ink, w, extra)

    wall_top = SLAB + H
    roof = wall_top + T
    concrete, side = p["concrete"], p["panel"]
    hx, fan, tank, bio = LAY.hx, LAY.fan, LAY.tank, LAY.biofilter
    bcx, bcy, bdia = LAY.buffer

    # ground
    s.poly([P(-1, -1.5, 0), P(bio[1] + 1.5, -1.5, 0), P(bio[1] + 1.5, bio[3] + 1.0, 0), P(-1, bio[3] + 1.0, 0)],
           p["panel"], p["faint"], 1, 'stroke-dasharray="5 5"')

    # back wall of the whole block and slab
    box(0, X_ALL, -T, 0, 0, roof, concrete, side, concrete)
    box(0, X_ALL, 0, L, 0, SLAB, concrete, side, concrete)

    # tunnels 1..N-1: closed
    for i in range(N - 1):
        x0 = bay_x(i)
        box(x0 - T, x0, 0, L, SLAB, roof, concrete, side, concrete)       # left wall
        box(x0, x0 + W, 0, L, wall_top, roof, concrete, side, concrete)   # roof
        dx0 = x0 + (W - DOOR_W) / 2
        s.poly([P(x0 - T, L, SLAB), P(x0 + W + T, L, SLAB), P(x0 + W + T, L, roof), P(x0 - T, L, roof)],
               concrete, ink, 1.1)
        s.poly([P(dx0, L, SLAB), P(dx0 + DOOR_W, L, SLAB), P(dx0 + DOOR_W, L, SLAB + DOOR_H), P(dx0, L, SLAB + DOOR_H)],
               p["c"], ink, 1.2)
        for j in range(1, 8):
            z = SLAB + DOOR_H * j / 8
            seg((dx0, L, z), (dx0 + DOOR_W, L, z), mu, 0.6)
        tx, ty = P(x0 + W / 2, L, roof + 0.25)
        s.text(tx, ty, f"T-10{i + 1}", 12, weight="600", anchor="middle")

    # last tunnel: cut away
    x0 = bay_x(N - 1)
    x1 = x0 + W
    box(x0 - T, x0, 0, L, SLAB, roof, concrete, side, concrete)           # its left wall (shared)
    s.poly([P(x0, 0, SLAB), P(x1, 0, SLAB), P(x1, 0, wall_top), P(x0, 0, wall_top)], p["panel"], ink, 0.9)
    s.poly([P(x0, 0, SLAB), P(x0, L, SLAB), P(x0, L, wall_top), P(x0, 0, wall_top)], side, ink, 0.9)
    nch = int(W / SPIGOT_PITCH)
    for c in range(1, nch):
        xc = x0 + c * SPIGOT_PITCH
        seg((xc, 0.2, SLAB), (xc, L - 0.2, SLAB), p["cool"], 0.8, 'stroke-dasharray="2 3"')
    bed_front = L * 0.62
    box(x0, x1, 0, bed_front, SLAB, SLAB + FILL, p["timber_fill"], p["timber_side"], p["timber_fill"], 1.1)
    for j in range(11):
        yy = 0.6 + j * (bed_front - 1.0) / 10
        for xx in (x0 + 0.8, x0 + 2.1, x0 + 3.4, x0 + 4.4):
            cx, cy = P(xx + (j % 3) * 0.15, yy, SLAB + FILL)
            s.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.5" fill="{p["timber"]}" opacity="0.6"/>')
    for xx in (x0 + 1.2, x0 + 2.5, x0 + 3.8):
        a, b = P(xx, bed_front - 0.05, SLAB + 0.1), P(xx, bed_front - 0.05, SLAB + FILL + 1.0)
        s.line(a[0], a[1], b[0], b[1], p["cool"], 1.6, 'marker-end="url(#arrCool)"')
    cut_z = SLAB + 0.9
    box(x1, x1 + T, 0, L * 0.45, SLAB, roof, concrete, side, concrete)
    box(x1, x1 + T, L * 0.45, L, SLAB, cut_z, concrete, side, concrete)
    s.poly([P(x1, L * 0.45, cut_z), P(x1 + T, L * 0.45, cut_z), P(x1 + T, L * 0.45, roof), P(x1, L * 0.45, roof)],
           "url(#hatch)", ink, 0.8)
    tx, ty = P(x0 + W / 2 + 1.0, L + 1.6, 0)
    s.text(tx, ty, f"T-10{N} (door open)", 12, weight="600", anchor="middle")

    # exhaust stubs and manifold on the roof, down to the exchanger
    zm = roof + 0.9
    hot, cool = p["hot"], p["cool"]
    ey = LAY.exhaust_y_m
    xin = hx[0] + 1.0
    for i in range(N):
        xs = bay_x(i) + W / 2
        seg((xs, ey, roof), (xs, ey, zm), hot, 5)
    seg((bay_x(0) + W / 2, ey, zm), (xin, ey, zm), hot, 7)
    seg((xin, ey, zm), (xin, ey, hx[5]), hot, 7)

    # buffer tank stands behind the skid; water: exchanger -> buffer -> heat users
    cylinder(bcx, bcy, bdia / 2, 0, LAY.buffer_h_m, p["panel"])
    tx, ty = P(bcx, bcy, LAY.buffer_h_m + 0.5)
    s.text(tx, ty, f"TK-201 · {fmt(M['buffer_m3'])} m³", 11, weight="600", anchor="middle")
    seg(((hx[0] + hx[1]) / 2, hx[2], 2.6), ((hx[0] + hx[1]) / 2, bcy + 0.4, 2.6), hot, 3)
    seg(((hx[0] + hx[1]) / 2 + 0.6, hx[2], 1.2), ((hx[0] + hx[1]) / 2 + 0.6, bcy + 0.4, 1.2), cool, 3)
    seg((bcx + bdia / 2, bcy, 1.8), (bcx + bdia / 2 + 3.0, bcy, 1.8), hot, 3, 'marker-end="url(#arrHot)"')
    seg((bcx + bdia / 2 + 3.0, bcy + 0.8, 0.9), (bcx + bdia / 2, bcy + 0.8, 0.9), cool, 3, 'marker-end="url(#arrCool)"')

    # heat-recovery skid: exchanger, fan, condensate tank, biofilter
    box(*hx, p["panel"], p["b"], p["panel"], 1.3, op=0.95)
    for j in range(9):
        yy = hx[2] + 0.4 + j * (hx[3] - hx[2] - 0.8) / 8
        seg((hx[1], yy, 0.5), (hx[1], yy, hx[5] - 0.5), hot, 0.6)
    box(*fan, p["panel"], p["panel"], p["panel"], 1.2)
    cx, cy = P(fan[1], (fan[2] + fan[3]) / 2, 0.8)
    s.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="9" ry="12" fill="{p["bg"]}" stroke="{ink}" stroke-width="1.2"/>')
    seg((hx[1], (fan[2] + fan[3]) / 2, 0.8), (fan[0], (fan[2] + fan[3]) / 2, 0.8), mu, 3)
    box(*tank, p["c"], p["c"], p["c"], 1.1)
    seg((hx[1], (tank[2] + tank[3]) / 2, 0.3), (tank[0], (tank[2] + tank[3]) / 2, 0.3), cool, 2, 'stroke-dasharray="4 3"')
    box(*bio, p["d"], p["d"], p["d"], 1.2, op=0.9)
    fy = (fan[2] + fan[3]) / 2
    seg(((fan[0] + fan[1]) / 2, fan[3], 0.8), ((fan[0] + fan[1]) / 2, bio[2], 0.8), mu, 3)
    # callouts: (point, label, balloon offset in px)
    items = [
        (P(bay_x(0) - T / 2, L * 0.55, roof), "Insulated precast tunnel", (-120, -150)),
        (P(bay_x(1) + 2.2, L, SLAB + 2.0), "Sectional door", (-150, 130)),
        (P(x0 + 2.5, L * 0.85, SLAB), "Aerated spigot floor", (-90, 150)),
        (P(x0 + 2.4, bed_front * 0.4, SLAB + FILL), "Compost bed", (140, -120)),
        (P(x0 + 1.5, 1.2, SLAB + FILL + 1.0), "Headspace", (110, -150)),
        (P(bay_x(1) + W / 2, ey, zm), "Exhaust manifold", (-60, -110)),
        (P(hx[1], (hx[2] + hx[3]) / 2, 2.0), "Plate-fin exchanger HX-201", (230, -60)),
        (P(tank[1], (tank[2] + tank[3]) / 2, 0.9), "Condensate tank TK-401", (60, 150)),
        (P((fan[0] + fan[1]) / 2, fan[2], 1.2), "Exhaust fan K-201", (210, 40)),
        (P((bio[0] + bio[1]) / 2, (bio[2] + bio[3]) / 2, 1.6), f"Biofilter, {fmt(M['biofilter_m2'])} m²", (60, 110)),
        (P(bcx, bcy, 4.0), f"Buffer tank TK-201, {fmt(M['buffer_m3'])} m³", (-60, -170)),
        (P(bcx + bdia / 2 + 2.4, bcy, 1.8), "Water loop to heat users", (130, -90)),
        (P(x1 + T, L * 0.8, cut_z), "Side wall, cut", (-20, 200)),
    ]
    for n, ((x, y), _, (dx, dy)) in enumerate(items, 1):
        s.callout(n, x, y, x + dx, y + dy)

    # key
    kx, ky = 1290, 108
    s.rect(kx - 14, ky - 8, 300, 26 + 20 * len(items) + 130, p["bg"], p["faint"], 1, 'rx="6"')
    s.text(kx, ky + 12, "KEY", 10, mu, extra=f'letter-spacing="1.5" font-family="{MONO}"')
    for n, (_, label, _) in enumerate(items, 1):
        s.text(kx, ky + 22 + n * 20, f"{n}", 12, weight="600")
        s.text(kx + 22, ky + 22 + n * 20, label, 12)
    yy = ky + 22 + (len(items) + 1) * 20 + 6
    for line in [f"Duty {fmt(M['duty_kw'])} kW mean, {fmt(M['peak_duty_kw'])} kW peak",
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
    sp, px0, py0 = 19.0, 70.0, 205.0          # px per m, origin = back-left outer corner

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
    hx, fan, tank, bio = LAY.hx, LAY.fan, LAY.tank, LAY.biofilter
    bcx, bcy, bdia = LAY.buffer
    a, b = Pp(bay_x(0) + W / 2, LAY.exhaust_y_m), Pp(hx[0] + 1.0, LAY.exhaust_y_m)
    s.line(a[0], a[1], b[0], b[1], hot, 3)
    hx0, hy0 = Pp(hx[0], hx[2])
    s.rect(hx0, hy0, (hx[1] - hx[0]) * sp, (hx[3] - hx[2]) * sp, p["b"], ink, 1.3, 'fill-opacity="0.6"')
    s.text(hx0 + (hx[1] - hx[0]) / 2 * sp, hy0 + 2.1 * sp, "HX-201", 10, anchor="middle", weight="bold")
    fx, fy = Pp(fan[0], fan[2])
    s.rect(fx, fy, (fan[1] - fan[0]) * sp, (fan[3] - fan[2]) * sp, p["panel"], ink, 1.2)
    s.text(fx + (fan[1] - fan[0]) / 2 * sp, fy + 0.85 * sp, "K", 10, anchor="middle", weight="bold")
    tkx, tky = Pp(tank[0], tank[2])
    s.rect(tkx, tky, (tank[1] - tank[0]) * sp, (tank[3] - tank[2]) * sp, p["c"], ink, 1.1)
    bx_, by_ = Pp(bcx, bcy)
    s.add(f'<circle cx="{bx_:.1f}" cy="{by_:.1f}" r="{bdia / 2 * sp:.1f}" fill="{p["panel"]}" stroke="{ink}" stroke-width="1.3"/>')
    s.text(bx_, by_ + 4, "TK-201", 10, anchor="middle", weight="bold")
    s.text(bx_, by_ + 18, f"{fmt(M['buffer_m3'])} m³", 9.5, mu, anchor="middle")
    bfx, bfy = Pp(bio[0], bio[2])
    s.rect(bfx, bfy, (bio[1] - bio[0]) * sp, (bio[3] - bio[2]) * sp, p["d"], ink, 1.2)
    s.text(bfx + (bio[1] - bio[0]) / 2 * sp, bfy + (bio[3] - bio[2]) / 2 * sp, "Biofilter F-301", 11,
           anchor="middle", weight="bold")
    # section markers
    ay = Pp(0, L * 0.72)[1]
    s.line(px0 - 22, ay, px0 + X_ALL * sp + 22, ay, ink, 0.9, 'stroke-dasharray="14 4 3 4"')
    s.text(px0 - 30, ay + 4, "A", 13, weight="bold", anchor="end")
    s.text(px0 + X_ALL * sp + 30, ay + 4, "A", 13, weight="bold")
    bxm = Pp(bay_x(N - 1) + W / 2, 0)[0]
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
    sa, ax0, ay0 = 24.0, 780.0, 420.0          # ground line at ay0

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
    a, b = Pa(bay_x(N - 1), 0), Pa(bay_x(N - 1) + W, 0)
    s.dim(a[0], a[1], b[0], b[1], fmt(W, 1), 30, 11)
    s.text(Pa(X_ALL, 0)[0] + 20, Pa(0, SLAB / 2)[1] + 4, "plenum slab, channels at 0.5", 11, mu)
    s.text(Pa(X_ALL, 0)[0] + 20, Pa(0, SLAB + H + T / 2)[1] + 4, "200 concrete + 100 PIR", 11, mu)
    s.text(Pa(X_ALL, 0)[0] + 20, Pa(0, SLAB + H + T / 2)[1] + 20, f"U = {M['u_wall_w_m2k']:.2f} W/m²K", 11, mu)

    # ---- section B-B --------------------------------------------------------
    sb, bx0, by0 = 32.0, 780.0, 780.0

    def Pb(y, z):
        return bx0 + (y + T) * sb, by0 - z * sb

    s.text(bx0, Pb(0, SLAB + H + T + 1.2)[1] - 18, f"SECTION B-B  (T-10{N})", 12, mu, weight="bold", extra='letter-spacing="1.5"')
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
        s.text(lx0 + L * sb * 0.55, ly0 - 5, f"{label}: {depth:.1f} m", 11, p["timber"])
    # recirculation duct along the back and exhaust stub
    ex, ey = Pb(1.2, SLAB + H + T)
    s.rect(ex - 5, ey - 1.0 * sb, 10, 1.0 * sb, hot, hot, 1)
    s.text(ex + 12, ey - 0.7 * sb, f"exhaust Ø{DUCT_T}", 11, hot)
    a, b = Pb(0, SLAB + 0.15), Pb(-T - 0.4, SLAB + 0.15)
    s.line(b[0], b[1], a[0], a[1], cool, 2, 'marker-end="url(#arrCool)"')
    s.text(b[0] - 6, b[1] + 4, f"K-10{N} up to {fmt(M['blower_m3_h_each'], 0)} m³/h", 11, cool, anchor="end")
    a, b = Pb(0, 0), Pb(L, 0)
    s.dim(a[0], a[1], b[0], b[1], f"{fmt(L, 1)}", 30, 11)
    a, b = Pb(L, SLAB), Pb(L, SLAB + DOOR_H)
    s.dim(a[0], a[1], b[0], b[1], f"door {fmt(DOOR_H, 1)}", 18, 11)

    # ---- data table --------------------------------------------------------
    tx, ty = 80, 620
    rows = [
        ("Feedstock", f"{fmt(M['feedstock_t_per_day'], 1)} t/day, 15-day residence"),
        ("Tunnels", f"{N} × {fmt(W, 1)} × {fmt(H, 1)} × {fmt(L, 1)} m inner"),
        ("Material in tunnels", f"{fmt(M['solids_per_tunnel_m3'] * N)} m³ (model {fmt(M['gross_total_m3'])} m³ gross)"),
        ("Aeration", f"{fmt(M['air_m3_h'], 0)} m³/h mean, {M['air_changes_per_h']:.1f} vol/h"),
        ("Blowers", f"{N} × {M['blower_kw_each']:.1f} kW at {fmt(M['fan_pressure_pa'])} Pa (batch peak)"),
        ("Exhaust ducts", f"Ø{DUCT_T} per tunnel, Ø{DUCT_M} manifold"),
        ("Envelope loss", f"{M['wall_loss_kw_per_tunnel']:.1f} kW per tunnel"),
        ("Heat recovery", f"{fmt(M['duty_kw'])} kW mean, {fmt(M['peak_duty_kw'])} kW peak, {M['heat_gwh_per_year']:.1f} GWh/yr"),
        ("Buffer", f"TK-201, {fmt(M['buffer_m3'])} m³ hot water"),
        ("Operation", f"one tunnel refilled every {OPS['stage_days']:.2f} days (CE-11)"),
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
    rows = [("Duty", f"{fmt(M['duty_kw'])} kW mean, {fmt(M['peak_duty_kw'])} kW peak (4 staggered batches)"),
            ("Air", f"{M['air_dry_kg_s']:.2f} kg/s dry, {fmt(M['air_m3_h'], 0)} m³/h"),
            ("Water", f"{fmt(M['t_return_c'])} → {fmt(M['t_supply_c'])} °C, {fmt(M['water_m3_h'], 1)} m³/h"),
            ("Pinch", f"{M['pinch_k']:.1f} K at the cold end"),
            ("Area", f"{fmt(M['hx_area_m2'])} m² for the peak, scaled from 23.3 kW / 9.2 m²"),
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
           "Per-tunnel aeration with recirculation and roof spray bars, shared exhaust to heat recovery and biofilter, heat-metered water loop.")
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
    pitch, hh = 690 / N, 690 / N - 34                     # row pitch and tunnel box height
    stage = OPS["stage_days"]
    for i in range(N):
        y = 150 + i * pitch
        d0, d1 = i * stage, (i + 1) * stage
        fill = p["a"] if d1 <= T45 + 0.5 else p["c"] if d0 >= COOL else p["b"]
        s.rect(220, y, 300, hh, fill, ink, 1.6, 'rx="6" fill-opacity="0.55"')
        s.text(240, y + 24, f"T-10{i + 1}  tunnel", 14, weight="bold")
        phase = "mesophilic" if d1 <= T45 + 0.5 else "cooling" if d0 >= COOL else "thermophilic, 60 °C"
        s.text(240, y + 42, f"batch now on day {d0:g}-{d1:g}: {phase}", 11.5, mu)
        yb = y + hh - 18
        s.line(230, yb, 510, yb, cool, 1.2, 'stroke-dasharray="2 3"')
        s.text(500, yb - 6, "spigot floor", 10, cool, anchor="end")
        blower(130, yb, f"K-10{i + 1}")
        s.path(f"M148,{yb} L230,{yb}", cool, 2, extra='marker-end="url(#arrCool)"')
        s.path(f"M60,{yb} L112,{yb}", cool, 2)
        damper(80, yb, f"FD-10{i + 1}", 0, 24)
        s.text(40, yb + 4, "air", 11, mu, anchor="end")
        s.path(f"M220,{y + 26} L170,{y + 26} L170,{yb - 40} L130,{yb - 40} L130,{yb - 18}", mu, 1.6,
               extra='marker-end="url(#arr)" stroke-dasharray="6 4"')
        damper(150, yb - 40, f"RD-10{i + 1}", -6, -12, "end")
        s.path(f"M520,{y + 34} L640,{y + 34}", hot, 2.4)
        damper(580, y + 34, f"XD-10{i + 1}")
        for xi, tag in ((290, "TT"), (350, "OT"), (410, "PT")):
            inst(xi, y + hh / 2 + 6, tag, f"10{i + 1}")
        # roof spray bar SP-10x, fed from the irrigation header through XV-10x
        ys = y + 62
        s.line(456, ys, 512, ys, cool, 1.6)
        for xn in (466, 484, 502):
            s.poly([(xn - 5, ys + 11), (xn + 5, ys + 11), (xn, ys + 2)], "none", cool, 1)
        s.text(484, ys - 6, f"SP-10{i + 1}", 9.5, cool, anchor="middle")
        s.path(f"M560,{ys} L512,{ys}", cool, 1.6, extra='stroke-dasharray="8 3"')
        s.poly([(530, ys - 6), (540, ys), (530, ys + 6)], p["bg"], ink, 1)
        s.poly([(550, ys - 6), (540, ys), (550, ys + 6)], p["bg"], ink, 1)
        s.text(540, ys + 18, f"XV-10{i + 1}", 9.5, mu, anchor="middle")
    # manifold
    s.path(f"M640,{150 + 34} L640,{150 + (N - 1) * pitch + 34}", hot, 4)
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
    s.text(684, 644, "condensate", 10.5, mu)
    # irrigation: TK-401 -> P-401 -> header -> spray bars; farm water after sanitisation
    y_last = 150 + (N - 1) * pitch + 62
    s.path("M680,603 L662,603 L662,880 L560,880 L560,212", cool, 1.6, extra='stroke-dasharray="8 3"')
    s.add(f'<circle cx="612" cy="880" r="14" fill="{p["bg"]}" stroke="{ink}" stroke-width="1.4"/>')
    s.poly([(619, 872), (603, 880), (619, 888)], ink, ink, 1)
    s.text(612, 910, "P-401", 10.5, weight="bold", anchor="middle")
    s.path("M470,930 L560,930 L560,880", cool, 1.6, extra='stroke-dasharray="8 3"')
    s.poly([(500, 924), (510, 930), (500, 936)], p["bg"], ink, 1)
    s.poly([(520, 924), (510, 930), (520, 936)], p["bg"], ink, 1)
    s.text(510, 950, "XV-402", 9.5, mu, anchor="middle")
    s.text(462, 934, "farm water", 10.5, mu, anchor="end")
    inst(590, 840, "FT", "401")
    s.text(320, 880, "spray water: condensate until the batch", 10.5, mu)
    s.text(320, 894, "is sanitised, farm water after (CE-14)", 10.5, mu)
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
    s.text(1229, 466, f"buffer {fmt(M['buffer_m3'])} m³", 10.5, mu, anchor="middle")
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
                                            (cool, "8 3", "spray water to the beds"),
                                            (g, "3 3", "instrument signal")]):
        s.line(lx, ly + n * 22, lx + 40, ly + n * 22, col, 2.4 if not dash else 1.4,
               f'stroke-dasharray="{dash}"' if dash else "")
        s.text(lx + 50, ly + n * 22 + 4, label, 11.5)
    s.text(lx, ly + 122, "TT temperature · OT oxygen · PT pressure", 11, mu)
    s.text(lx, ly + 138, "MT humidity · FT flow · AT ammonia · XV valve", 11, mu)

    s.text(32, s.h - 30, f"Indicative. Batches are staggered {OPS['stage_days']:.2f} days apart, so the {N} tunnels are always at different stages (CE-11). Tags are used by CE-10.", 12, mu)
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
        f"tunnels staggered {OPS['stage_days']:.2f} days (CE-11)",
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
    stage = OPS["stage_days"]
    header(s, "How a batch moves through the phases",
           f"A: each tunnel runs the whole cycle in place, staggered {stage:.2f} days apart (base design). "
           "B: a loader moves each batch from tunnel to tunnel.")
    ink, mu = p["ink"], p["muted"]
    # phase windows of one batch (days), as the controller runs it (CE-10, configurations.py)
    windows = [(0.0, round(T45, 1), p["a"], "mesophilic heat-up"), (round(T45, 1), COOL, p["b"], "thermophilic: sanitise, most heat"),
               (COOL, 15.0, p["c"], "cooling (still ≥ 45 °C)")]
    days = 30
    gx, gw, rh, gap = 150, 720, 30, 8

    def X(day):
        return gx + day / days * gw

    def axis(y0):
        for d in range(0, days + 1, 5):
            s.line(X(d), y0 - 8, X(d), y0 + N * (rh + gap), p["faint"], 0.8)
            s.text(X(d), y0 + N * (rh + gap) + 14, f"d{d}", 11, mu, anchor="middle")

    def block(t, d0, d1, fill, label, y0):
        d0c, d1c = max(d0, 0), min(d1, days)
        if d1c <= d0c:
            return
        y = y0 + t * (rh + gap)
        s.rect(X(d0c), y, X(d1c) - X(d0c), rh, fill, ink, 0.9, 'fill-opacity="0.8"')
        if label and X(d1c) - X(d0c) > 46:
            s.text((X(d0c) + X(d1c)) / 2, y + rh / 2 + 4, label, 10.5, anchor="middle")

    def rows(y0):
        for t in range(N):
            s.text(gx - 14, y0 + t * (rh + gap) + rh / 2 + 4, f"T-10{t + 1}", 12, weight="600", anchor="end")

    def loader(x, y):
        s.poly([(x - 7, y - 12), (x + 7, y - 12), (x, y - 2)], ink, ink, 1)

    def batch(start, t_of_day, y0, label, moves=False):
        """Draw one batch started at `start`; t_of_day(age) gives the tunnel it sits in."""
        for w0, w1, fill, _ in windows:
            # split the phase window where the batch changes tunnel
            cuts = sorted({w0, w1, *[k * stage for k in range(1, N) if moves and w0 < k * stage < w1]})
            for c0, c1 in zip(cuts, cuts[1:]):
                block(t_of_day(c0), start + c0, start + c1, fill, label if c0 == 0 else "", y0)

    # ---- A: staggered -------------------------------------------------------
    ya = 170
    s.text(60, ya - 30, "A  STAGGERED BATCHES  (base design)", 12, weight="600", extra='letter-spacing="1"')
    axis(ya)
    rows(ya)
    for k in range(-N, 9):
        batch(k * stage, lambda age, k=k: k % N, ya, f"batch {k + N}")
    for k in range(0, 9):
        if k * stage <= days:
            loader(X(k * stage), ya + (k % N) * (rh + gap))
    s.text(X(0), ya + N * (rh + gap) + 34,
           f"▼ every {stage:.2f} days the loader empties one tunnel to the maturation hall and refills it. The batch never moves inside.",
           11.5, mu)

    # ---- B: transfer --------------------------------------------------------
    yb = 450
    s.text(60, yb - 30, "B  TRANSFER BETWEEN TUNNELS  (one stage per tunnel)", 12, weight="600", extra='letter-spacing="1"')
    axis(yb)
    rows(yb)
    for k in range(-N, 9):
        batch(k * stage, lambda age: min(int(age // stage + 1e-9), N - 1), yb, f"batch {k + N}", moves=True)
    for k in range(1, 9):
        x = X(k * stage)
        if x > X(days):
            break
        for t in range(N - 1):
            y1 = yb + t * (rh + gap) + rh / 2
            d = f"M{x - 16},{y1} C{x + 2},{y1} {x - 2},{y1 + rh + gap} {x + 14},{y1 + rh + gap}"
            s.path(d, p["bg"], 6)
            s.path(d, p["hot"], 2, extra='marker-end="url(#arrHot)"')
        loader(x, yb)
    s.text(X(0), yb + N * (rh + gap) + 34,
           f"▼ every {stage:.2f} days: empty T-10{N}, move every batch one tunnel along (hot, in the open), refill T-101.",
           11.5, mu)

    # legend
    ly = 740
    for n, (_, _, col, label) in enumerate(windows):
        s.rect(60 + n * 250, ly, 26, 16, col, ink, 0.9, 'fill-opacity="0.8"')
        s.text(96 + n * 250, ly + 13, label, 12)
    s.text(60, ly + 44, f"Batch = {fmt(OPS['batch_t'])} t ({fmt(OPS['batch_m3'])} m³) of fresh feedstock. "
                        f"In A it fills a tunnel to {OPS['fill_depth_m']:.1f} m and settles to {OPS['settled_depth_m']:.1f} m by day 15.", 12, mu)
    s.text(60, ly + 62, "Phase windows from the batch model (process.py); setpoints in CE-10; the whole process sheet in CE-14.", 12, mu)

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
        ("Exhaust to HX-201", f"blend of {N} batches", "same blend, other tunnels"),
        ("Tunnel design", f"{N} identical", "can specialise each"),
        ("Remixing", "once, at loading", "at every move"),
        ("Net value before capital", f"€{a['net_eur'] / 1000:,.0f}k/yr", f"€{b['net_eur'] / 1000:,.0f}k/yr"),
    ]
    c1, c2, c3 = tx, tx + 200, tx + 380
    s.rect(tx - 16, ty - 26, 640, 30 * len(rows_) + 12, p["bg"], p["faint"], 1, 'rx="6"')
    for n, (k, va, vb) in enumerate(rows_):
        y = ty + n * 30
        head = n == 0
        last = n == len(rows_) - 1
        if n:
            s.line(tx - 16, y - 20, tx + 624, y - 20, p["faint"], 0.8)
        s.text(c1, y, k, 12, mu)
        s.text(c2, y, va, 12.5, weight="600" if head or last else "normal")
        s.text(c3, y, vb, 12.5, weight="600" if head or last else "normal")

    ry = ty + 30 * len(rows_) + 20
    s.rect(tx - 16, ry, 640, 166, p["d"], ink, 1.2, 'rx="6" fill-opacity="0.45"')
    s.text(tx, ry + 28, "A is the base design", 14, weight="600")
    for n, t in enumerate([
        f"{b['t_per_day'] / a['t_per_day']:.1f}× less loader work, no hot material in the open, identical tunnels.",
        "The patent's one-chamber-per-phase idea survives as a control scheme:",
        "each tunnel passes through the phases in time instead of in space.",
        "B pays only if remixing at each move raised the heat recovered by ~12 %.",
        "Tunnel count, automatic transfer and a stacked tower: CE-12 and CE-13.",
    ]):
        s.text(tx, ry + 54 + n * 20, t, 12)

    s.text(32, s.h - 30, f"Assumptions in industrial.py (Handling): 0.25 L diesel/t, 120 t/h, 10 K lost per hot move, "
                         "30 % mass loss over 15 days (CE-14: 46 %). Fill/empty is in the €100k opex.", 11.5, mu)
    s.title_block("Operating modes", "CE-11")
    return s.render()


# ---------------------------------------------------------------------------
# CE-12  configuration study
# ---------------------------------------------------------------------------
def configuration_study(p: dict) -> str:
    s = Svg(1600, 1000, p, "Configuration study")
    header(s, "Which reactor? Configuration study",
           "2-4 tunnels, loader transfer, an automatic transfer train and the patent's stacked chambers, "
           "paid for over 10 years at 6 %. MODEL, first-pass costs.")
    ink, mu, hot, cool, g = p["ink"], p["muted"], p["hot"], p["cool"], p["green"]
    mono = f'font-family="{MONO}"'

    # ---- exhaust heat over one cycle ---------------------------------------
    shape = CFG.batch_profile()
    duty = M["duty_kw"]
    cx0, cy0, cw, ch = 110, 150, 600, 300
    k0, k1 = 350.0, 900.0

    def C(day, kw):
        return cx0 + day / 15 * cw, cy0 + ch - (kw - k0) / (k1 - k0) * ch

    s.text(cx0 - 60, cy0 - 22, "PLANT EXHAUST HEAT, ONE 15-DAY CYCLE", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    s.rect(cx0, cy0, cw, ch, p["bg"], p["faint"], 1)
    for kw in range(400, 901, 100):
        _, y = C(0, kw)
        s.line(cx0, y, cx0 + cw, y, p["faint"], 0.6)
        s.text(cx0 - 8, y + 4, str(kw), 10.5, mu, anchor="end")
    for d in range(0, 16, 3):
        x, _ = C(d, k0)
        s.text(x, cy0 + ch + 16, f"d{d}", 10.5, mu, anchor="middle")
    s.text(cx0 - 52, cy0 + ch / 2, "kW", 11, mu, anchor="middle")
    _, ym = C(0, duty)
    s.line(cx0, ym, cx0 + cw, ym, ink, 0.8, 'stroke-dasharray="3 3"')
    s.text(cx0 + 6, ym - 6, f"mean {fmt(duty)} kW", 10.5, ink)
    styles = [(2, p["a"], 1.4, "2 tunnels"), (3, p["b"], 1.4, "3 tunnels"), (15, cool, 1.2, "daily slices"),
              (4, g, 2.6, "4 tunnels (final)")]
    n = len(shape)
    for nb, col, w, label in styles:
        prof = CFG.combined_profile(nb, shape) * duty
        stroke = col if nb not in (2, 3) else ("#a7b83f" if nb == 2 else "#e0882a")
        pts = " ".join(f"{'M' if i == 0 else 'L'}{C(i / n * 15, v)[0]:.1f},{C(i / n * 15, v)[1]:.1f}"
                       for i, v in enumerate(prof) if i % 2 == 0)
        s.path(pts, stroke, w)
    ly = cy0 + ch + 44
    for i, (nb, col, w, label) in enumerate(styles):
        prof = CFG.combined_profile(nb, shape) * duty
        stroke = col if nb not in (2, 3) else ("#a7b83f" if nb == 2 else "#e0882a")
        x = cx0 + (i % 2) * 300
        y = ly + (i // 2) * 22
        s.line(x, y - 4, x + 26, y - 4, stroke, w + 0.4)
        s.text(x + 34, y, f"{label}: peak {fmt(prof.max())} kW", 11.5)

    # ---- A-2 / A-3 / A-4 detail ----------------------------------------------
    base = {r["code"]: r for r in CFG.ranking(CFG.Costs())}
    low = {r["code"]: r["value_eur"] for r in CFG.ranking(CFG.LOW)}
    high = {r["code"]: r["value_eur"] for r in CFG.ranking(CFG.HIGH)}
    tx, ty = 110, 590
    cols = [("", 0), ("A-2", 230), ("A-3", 340), ("A-4", 450)]
    rows = [("Peak / mean", lambda r: f"{r['peak_to_mean']:.2f}"),
            ("Exchanger", lambda r: f"{fmt(r['hx_area_m2'])} m²"),
            ("Buffer tank", lambda r: f"{fmt(r['buffer_m3'])} m³"),
            ("Doors, blowers", lambda r: f"{r['n']}, {r['n']}"),
            ("Capex", lambda r: f"€{r['capex'] / 1e3:,.0f}k"),
            ("Value after capital", lambda r: f"€{r['value_eur'] / 1e3:,.1f}k/yr")]
    s.text(tx - 60, ty - 22, "WHOLE CYCLE IN PLACE: HOW MANY TUNNELS?", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    s.rect(tx - 16, ty - 4, 600, 26 * (len(rows) + 1) + 12, p["bg"], p["faint"], 1, 'rx="6"')
    for name, x in cols[1:]:
        s.text(tx + x, ty + 18, name, 12.5, g if name == CFG.FINAL else ink, weight="600")
    for i, (label, f) in enumerate(rows):
        y = ty + 18 + (i + 1) * 26
        s.line(tx - 16, y - 18, tx + 584, y - 18, p["faint"], 0.7)
        s.text(tx, y, label, 12, mu)
        for name, x in cols[1:]:
            s.text(tx + x, y, f(base[name]), 12, weight="600" if i == len(rows) - 1 else "normal")

    # ---- ranking ---------------------------------------------------------------
    order = [r["code"] for r in CFG.ranking(CFG.Costs())]
    rx0, ry0, rw, rhh = 940, 150, 420, 34
    v0, v1 = -220e3, 80e3

    def V(v):
        return rx0 + (v - v0) / (v1 - v0) * rw

    s.text(rx0 - 120, ry0 - 22, "VALUE AFTER CAPITAL, k€/yr  (bar: base · line: low-high)", 10.5, mu,
           extra=f'letter-spacing="1.4" {mono}')
    for v in range(-200, 81, 50):
        x = V(v * 1e3)
        s.line(x, ry0 - 6, x, ry0 + rhh * len(order), p["faint"], 0.6)
        s.text(x, ry0 + rhh * len(order) + 16, str(v), 10.5, mu, anchor="middle")
    s.line(V(0), ry0 - 6, V(0), ry0 + rhh * len(order), ink, 1)
    fam = {"A": g, "B": "#e0882a", "C": cool, "D": mu}
    for i, code in enumerate(order):
        r = base[code]
        y = ry0 + i * rhh
        v = r["value_eur"]
        x0, x1 = sorted((V(0), V(v)))
        s.rect(x0, y + 7, x1 - x0, rhh - 14, fam[code[0]], "none", 0, 'fill-opacity="0.85"')
        s.line(V(high[code]), y + rhh / 2, V(low[code]), y + rhh / 2, ink, 1)
        s.text(rx0 - 120, y + rhh / 2 + 4, code + ("  ◀ final" if code == CFG.FINAL else ""), 11.5,
               g if code == CFG.FINAL else ink, weight="600" if code == CFG.FINAL else "normal", extra=mono)
        s.text(max(V(low[code]), V(0)) + 8, y + rhh / 2 + 4, r["title"], 10, mu)

    # ---- findings ---------------------------------------------------------------
    fx, fy = 820, 700
    s.rect(fx - 16, fy - 26, 760, 150, p["d"], ink, 1.2, 'rx="6" fill-opacity="0.45"')
    boost_c = CFG.break_even_boost("C-3-NW", CFG.FINAL)
    for i, t in enumerate([
        (f"A-4 is the final design: best at low, base and high costs; A-3 is within €{(base['A-4']['value_eur'] - base['A-3']['value_eur']) / 1e3:.0f}k/yr.", True),
        ("More batches in flight = steadier exhaust = smaller exchanger and buffer tank.", False),
        (f"Moving material costs more than it saves. The automatic train needs ~{boost_c * 100:.0f} % more heat from remixing", False),
        ("to break even (CE-13). The stacked tower is the most expensive option.", False),
        ("A-3 wins if the feedstock composts faster/slower than assumed or arrives warm: a pilot batch decides.", False),
    ]):
        s.text(fx, fy + i * 22, t[0], 12.5 if t[1] else 12, weight="600" if t[1] else "normal")

    s.text(32, s.h - 30, "MODEL. Costs, upkeep and batch kinetics in model/compost_energy/configurations.py; "
                         "all options in docs/explanation/configuration-study.md and data/model/configurations.json.", 12, mu)
    s.title_block("Configuration study", "CE-12")
    return s.render()


# ---------------------------------------------------------------------------
# CE-13  automatic transfer train (studied, not selected)
# ---------------------------------------------------------------------------
def transfer_train(p: dict) -> str:
    s = Svg(1600, 1000, p, "Automatic transfer train")
    header(s, "Automatic transfer train (studied, not selected)",
           "Fill only T-101; the bed moves to the next tunnel inside the building. Engineered and costed in the "
           "configuration study, it loses to A-4 (CE-12).")
    ink, mu, hot, cool, g = p["ink"], p["muted"], p["hot"], p["cool"], p["green"]
    mono = f'font-family="{MONO}"'
    n_t = 3
    Lt = CFG.evaluate_option(next(o for o in CFG.all_options() if o.code == "C-3-NW")).numbers["tunnel_length_m"]

    # ---- long section ---------------------------------------------------------
    sc, x0, y0 = 22.0, 230.0, 330.0           # px per m, ground line
    door = 0.35

    def X(m):
        return x0 + m * sc

    def Z(m):
        return y0 - m * sc

    total = n_t * Lt + (n_t + 1) * door
    s.text(60, 140, "LONG SECTION  (3 tunnels in line, floor-net option)", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    s.line(X(-6), y0, X(total + 6), y0, ink, 1.4)
    s.rect(X(0), Z(SLAB), total * sc, SLAB * sc, "url(#concrete)", ink, 1.1)
    s.rect(X(0), Z(SLAB + H + T), total * sc, T * sc, "url(#concrete)", ink, 1.1)
    phase_fill = [p["a"], p["b"], p["c"]]
    labels = ["T-101  heat-up", "T-102  hot, sanitise", "T-103  cooling"]
    for i in range(n_t):
        xa = door + i * (Lt + door)
        # door (guillotine) at the inlet of each tunnel, and the outlet door
        s.rect(X(xa - door), Z(SLAB + H), door * sc, H * sc, p["c"], ink, 1.1)
        bed = FILL * (1.15 - 0.15 * i)
        s.rect(X(xa), Z(SLAB + bed), Lt * sc, bed * sc, phase_fill[i], p["timber"], 1, 'fill-opacity="0.85"')
        s.line(X(xa), Z(SLAB) - 2, X(xa + Lt), Z(SLAB) - 2, cool, 1.4, 'stroke-dasharray="2 3"')
        s.text(X(xa + Lt / 2), Z(SLAB + H) + 20, labels[i], 12, weight="600", anchor="middle")
        for xx in (0.25, 0.5, 0.75):
            a, b = (X(xa + Lt * xx), Z(SLAB + 0.1)), (X(xa + Lt * xx), Z(SLAB + bed + 0.6))
            s.line(a[0], a[1], b[0], b[1], cool, 1.1, 'marker-end="url(#arrCool)"')
        # remix reel at the internal doors
        if i > 0:
            rx, rz = X(xa - door / 2), Z(SLAB + 0.9)
            s.add(f'<circle cx="{rx:.1f}" cy="{rz:.1f}" r="13" fill="{p["bg"]}" stroke="{ink}" stroke-width="1.4"/>')
            for k in range(6):
                ang = k * math.pi / 3
                s.line(rx, rz, rx + 13 * math.cos(ang), rz + 13 * math.sin(ang), ink, 1)
            s.path(f"M{rx},{rz - 13} L{rx},{rz - 34}", cool, 1, extra='stroke-dasharray="2 2"')
        # winch pulling the floor net to the outlet end
        wx = X(xa + Lt - 0.4)
        s.rect(wx - 8, Z(SLAB + 0.6), 16, 0.6 * sc, p["panel"], ink, 1)
        s.path(f"M{X(xa + 0.3)},{Z(SLAB) - 5} L{wx - 8},{Z(SLAB) - 5}", g, 1.4, extra='marker-end="url(#arrGreen)"')
    s.rect(X(total - door), Z(SLAB + H), door * sc, H * sc, p["c"], ink, 1.1)
    # hopper and feed conveyor
    hx0 = X(-5.5)
    s.poly([(hx0, Z(3.4)), (hx0 + 3.2 * sc, Z(3.4)), (hx0 + 2.2 * sc, Z(1.8)), (hx0 + 1.0 * sc, Z(1.8))], p["panel"], ink, 1.3)
    s.text(hx0 + 1.6 * sc, Z(3.4) - 10, "hopper + mixer", 11, anchor="middle", weight="600")
    s.path(f"M{hx0 + 1.6 * sc},{Z(1.8)} L{X(door + 0.5)},{Z(SLAB + 2.4)}", ink, 4)
    s.text(hx0 + 1.6 * sc, Z(1.0), "loader tips fresh feed", 10.5, mu, anchor="middle")
    # outlet conveyor
    ox = X(total)
    s.path(f"M{ox},{Z(SLAB + 0.4)} L{ox + 5 * sc},{Z(1.6)}", ink, 4, extra='marker-end="url(#arr)"')
    s.text(ox + 5 * sc + 8, Z(1.6) + 4, "to maturation hall", 10.5, mu)
    # exhaust
    for i in range(n_t):
        xa = door + i * (Lt + door) + 1.0
        s.line(X(xa), Z(SLAB + H + T), X(xa), Z(SLAB + H + T + 0.9), hot, 4)
    s.line(X(door + 1.0), Z(SLAB + H + T + 0.9), X(total + 3), Z(SLAB + H + T + 0.9), hot, 5)
    s.text(X(total + 3) + 8, Z(SLAB + H + T + 0.9) + 4, "exhaust → HX-201", 10.5, hot)
    s.dim(X(door), y0, X(door + Lt), y0, f"{fmt(Lt, 1)}", 26, 11)
    s.dim(X(0), y0, X(total), y0, f"{fmt(total, 1)} overall", 48, 11)

    # ---- move sequence ---------------------------------------------------------
    qx, qy = 60, 500
    s.text(qx, qy - 22, "ONE MOVE, EVERY 5 DAYS (OR A SLICE DAILY)", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    steps = ["Open the outlet door; T-103's net pulls its bed onto the outlet conveyor.",
             "Open door 2-3; T-102's bed is pulled through the remix reel into T-103.",
             "Open door 1-2; T-101's bed moves into T-102 the same way.",
             "Fill T-101 from the hopper; close all doors; restart aeration."]
    for i, t in enumerate(steps):
        y = qy + i * 30
        s.add(f'<circle cx="{qx + 11}" cy="{y - 4}" r="11" fill="{p["bg"]}" stroke="{ink}" stroke-width="1.2"/>')
        s.text(qx + 11, y, str(i + 1), 11, weight="600", anchor="middle")
        s.text(qx + 32, y, t, 12)

    ix, iy = 60, 680
    s.text(ix, iy - 22, "INTERLOCKS: A MOVE STARTS ONLY IF", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    for i, t in enumerate(["the downstream tunnel is empty (load cells, door switches)",
                           "the hot batch has held ≥ 55 °C for 3 days (PFRP timer)",
                           "net and door positions agree; no jam on winch current",
                           "it is a low heat-demand hour. If a move fails, batches compost in place (mode A)."]):
        s.text(ix, iy + i * 22, "·  " + t, 12)

    # ---- the numbers -------------------------------------------------------------
    a4 = CFG.evaluate_option(next(o for o in CFG.all_options() if o.code == CFG.FINAL)).numbers
    c3 = CFG.evaluate_option(next(o for o in CFG.all_options() if o.code == "C-3-NW")).numbers
    cd = CFG.evaluate_option(next(o for o in CFG.all_options() if o.code == "C-3-WF-daily")).numbers
    bx, by = 900, 500
    s.rect(bx - 16, by - 30, 690, 230, p["bg"], p["faint"], 1, 'rx="6"')
    s.text(bx, by - 8, "WHY IT LOSES TO A-4 (base costs, MODEL)", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    rows = [("", "A-4", "C-3 net+winch", "C-3 daily"),
            ("Capex", f"€{a4['capex'] / 1e3:,.0f}k", f"€{c3['capex'] / 1e3:,.0f}k", f"€{cd['capex'] / 1e3:,.0f}k"),
            ("of which transfer kit", "–", f"€{c3['capex_transfer'] / 1e3:,.0f}k", f"€{cd['capex_transfer'] / 1e3:,.0f}k"),
            ("Loader work", f"{fmt(a4['loader_t_day'])} t/day", f"{fmt(c3['loader_t_day'])} t/day", f"{fmt(cd['loader_t_day'])} t/day"),
            ("Buffer tank", f"{fmt(a4['buffer_m3'])} m³", f"{fmt(c3['buffer_m3'])} m³", f"{fmt(cd['buffer_m3'])} m³"),
            ("Value after capital", eur(a4['value_eur']), eur(c3['value_eur']), eur(cd['value_eur']))]
    for i, r in enumerate(rows):
        y = by + 22 + i * 26
        for j, (txt, x) in enumerate(zip(r, (0, 210, 330, 490))):
            s.text(bx + x, y, txt, 12, mu if j == 0 else ink, weight="600" if i in (0, len(rows) - 1) and j else "normal")
    s.text(bx, by + 190, "The loader work it replaces costs only ~€19k/yr; €1 of kit costs ~€0.19/yr repaid and maintained.", 11.5, mu)

    s.text(32, s.h - 30, "Concept for the record. Walking-floor and floor-net prices are unquoted assumptions (configurations.Costs).", 12, mu)
    s.title_block("Automatic transfer train", "CE-13")
    return s.render()


# ---------------------------------------------------------------------------
# CE-14  process sheet: phases, recipe, moisture and water
# ---------------------------------------------------------------------------
def process_sheet(p: dict) -> str:
    s = Svg(1600, 1000, p, "Process sheet")
    header(s, "One batch: phases, moisture and water",
           "What a tunnel runs: 15 days in the tunnel, then 8 weeks of maturation in windrows. MODEL, literature feedstock values.")
    ink, mu, hot, cool, g = p["ink"], p["muted"], p["hot"], p["cool"], p["green"]
    mono = f'font-family="{MONO}"'
    tg = PROC.Targets()
    b = BATCH
    day = b["day"]
    mat = PH["maturation"]

    # ---- the whole process on one strip ------------------------------------------
    sx0, sx1, sy = 110, 900, 128
    tunnel_w = (sx1 - sx0) * 0.62

    def SX(d):
        if d <= 15:
            return sx0 + d / 15 * tunnel_w
        return sx0 + tunnel_w + (d - 15) / (mat["end"] - 15) * (sx1 - sx0 - tunnel_w)

    for name, col in (("mesophilic", p["a"]), ("thermophilic", p["b"]), ("maturation", p["d"])):
        ph = PH[name]
        s.rect(SX(ph["start"]), sy, SX(ph["end"]) - SX(ph["start"]), 26, col, ink, 0.9, 'fill-opacity="0.9"')
        share = f" · {ph['share'] * 100:.0f} %" if ph["share"] else ""
        label = {"mesophilic": "mesophilic", "thermophilic": "thermophilic, 45-60 °C",
                 "maturation": "maturation in windrows, 8 weeks"}[name]
        x1 = SX(COOL) if name == "thermophilic" else SX(ph["end"])
        s.text((SX(ph["start"]) + x1) / 2, sy + 17, label + share, 11, anchor="middle")
    s.rect(SX(COOL), sy, SX(15) - SX(COOL), 26, p["c"], ink, 0.9, 'fill-opacity="0.75"')
    s.text((SX(COOL) + SX(15)) / 2, sy + 17, "cooling", 11, anchor="middle")
    s.line(SX(15), sy - 10, SX(15), sy + 36, ink, 1.4)
    s.text(SX(15), sy - 14, "emptied, day 15", 10.5, ink, anchor="middle")
    for d in (0, 5, 10, 15, 29, 43, 57, int(mat["end"])):
        s.text(SX(d), sy + 42, f"d{d}", 10, mu, anchor="middle")
    s.text(sx0 - 14, sy + 17, "TUNNEL", 9.5, mu, anchor="end", extra=f'letter-spacing="1.2" {mono}')
    s.text(sx1 + 8, sy + 17, f"% = share of the degradable matter broken down", 10, mu)

    # ---- temperature and moisture, 15 tunnel days --------------------------------
    cx0, cw = 110, 790
    ty0, th = 210, 170          # temperature panel
    my0, mh = 418, 150          # moisture panel

    def X(d):
        return cx0 + d / 15 * cw

    def YT(t):
        return ty0 + th - (t - 10) / 60 * th

    def YM(m):
        return my0 + mh - (m - 0.40) / 0.32 * mh

    for name, col, d0, d1 in (("mesophilic", p["a"], 0, T45), ("thermophilic", p["b"], T45, COOL),
                              ("cooling", p["c"], COOL, 15)):
        for y0, hh in ((ty0, th), (my0, mh)):
            s.rect(X(d0), y0, X(d1) - X(d0), hh, col, "none", 0, 'fill-opacity="0.35"')
    for y0, hh in ((ty0, th), (my0, mh)):
        s.rect(cx0, y0, cw, hh, "none", p["faint"], 1)
    for t in range(10, 71, 10):
        s.line(cx0, YT(t), cx0 + cw, YT(t), p["faint"], 0.5)
        s.text(cx0 - 8, YT(t) + 4, f"{t}", 10, mu, anchor="end")
    s.text(cx0 - 40, ty0 + th / 2, "°C", 11, mu, anchor="middle")
    s.line(cx0, YT(tg.sanitise_c), cx0 + cw, YT(tg.sanitise_c), mu, 0.8, 'stroke-dasharray="4 3"')
    pts = " ".join(f"{'M' if i == 0 else 'L'}{X(d):.1f},{YT(t):.1f}" for i, (d, t) in enumerate(zip(day, b["t_bed_c"])) if i % 2 == 0)
    s.path(pts, hot, 2.2)
    h0, sd = PH["sanitisation"]["start"], b["sanitised_day"]
    yb = YT(tg.sanitise_c) + 16
    s.line(X(h0), yb, X(sd), yb, ink, 1, 'marker-start="url(#arr)" marker-end="url(#arr)"')
    s.text((X(h0) + X(sd)) / 2, yb + 15, f"sanitised: {tg.sanitise_h:.0f} h ≥ {tg.sanitise_c:.0f} °C (day {h0:.1f}-{sd:.1f})", 10.5, anchor="middle")
    s.text(X(7.5), YT(60) - 8, "hot hold at 60 °C: fastest breakdown, most heat", 10.5, hot, anchor="middle")
    s.text(X(12.6), YT(40), "fresh air cools to 45 °C", 10.5, mu, anchor="middle")
    s.text(X(T45 / 2), YT(32) - 12, "self-heating on", 10.5, mu, anchor="middle")
    s.text(X(T45 / 2), YT(32) + 2, "recirculated air", 10.5, mu, anchor="middle")

    s.rect(cx0, YM(0.60), cw, YM(0.50) - YM(0.60), g, "none", 0, 'fill-opacity="0.10"')
    s.text(cx0 + 8, YM(0.60) + 13, "preferred 50-60 %", 10, g)
    for m in (0.40, 0.50, 0.60, 0.70):
        s.line(cx0, YM(m), cx0 + cw, YM(m), p["faint"], 0.5)
        s.text(cx0 - 8, YM(m) + 4, f"{m * 100:.0f} %", 10, mu, anchor="end")
    s.text(cx0 - 52, my0 + mh / 2, "moisture", 11, mu, anchor="middle")
    for fill, dash, w in ((None, "", 2.2), (0.55, 'stroke-dasharray="2 3"', 1.4), (0.70, 'stroke-dasharray="7 4"', 1.4)):
        r = b if fill is None else PROC.run_batch(fill_moisture=fill)
        pts = " ".join(f"{'M' if i == 0 else 'L'}{X(d):.1f},{YM(m):.1f}" for i, (d, m) in enumerate(zip(day, r["moisture"])) if i % 2 == 0)
        s.path(pts, cool, w, extra=dash)
        if fill is not None:
            for i in [i for i, v in enumerate(r["sprayed_kg"]) if v > 0]:
                s.add(f'<circle cx="{X(day[i]):.1f}" cy="{YM(r["moisture"][i]):.1f}" r="3.6" fill="{p["b"]}" stroke="{hot}" stroke-width="1"/>')
    for d in range(0, 16, 3):
        s.text(X(d), my0 + mh + 16, f"d{d}", 10, mu, anchor="middle")
    lx, lyy = cx0, my0 + mh + 40
    for n, (dash, w, label) in enumerate((("", 2.2, f"this recipe, filled at {b['fill_moisture'] * 100:.0f} %"),
                                          ('stroke-dasharray="2 3"', 1.4, "drier mix, 55 %"),
                                          ('stroke-dasharray="7 4"', 1.4, "wetter mix, 70 %"))):
        x = lx + n * 230
        s.line(x, lyy - 4, x + 28, lyy - 4, cool, w, dash)
        s.text(x + 36, lyy, label, 11)
    s.add(f'<circle cx="{lx + 700:.1f}" cy="{lyy - 4:.1f}" r="3.6" fill="{p["b"]}" stroke="{hot}" stroke-width="1"/>')
    s.text(lx + 710, lyy, "spray bars on", 11)

    # ---- recipe and process window ----------------------------------------------
    rx, ry = 1000, 128
    mix = PROC.mix()
    s.text(rx, ry, "RECIPE, BY MASS", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    rows = [("", "share", "moisture", "C:N")]
    for f, share in PROC.Recipe().parts:
        rows.append((f.name, f"{share * 100:.0f} %", f"{f.moisture * 100:.0f} %", f"{f.c_pct_dm / f.n_pct_dm:.0f}"))
    rows.append(("mix", "", f"{mix['moisture'] * 100:.0f} %", f"{mix['cn']:.0f}"))
    for i, row in enumerate(rows):
        y = ry + 26 + i * 21
        for j, (x, txt) in enumerate(zip((0, 260, 345, 440), row)):
            s.text(rx + x, y, txt, 11.5, mu if i == 0 else ink, weight="600" if i == len(rows) - 1 else "normal")
        if i:
            s.line(rx, y - 15, rx + 560, y - 15, p["faint"], 0.6)

    wy = ry + 26 + len(rows) * 21 + 26
    s.text(rx, wy, "PROCESS WINDOW", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    window = [
        ("C:N ratio", f"{tg.cn[0]:.0f}-{tg.cn[1]:.0f}", "straw share at the mixer"),
        ("Moisture at filling", f"{tg.moisture_fill[0] * 100:.0f}-{tg.moisture_fill[1] * 100:.0f} %", "straw; water at the mixer"),
        ("Moisture, thermophilic", f"≥ {tg.moisture_hot_min * 100:.0f} % → {tg.moisture_hot_set * 100:.0f} %", "spray bars SP-10x"),
        ("Moisture, cooling", f"≥ {tg.moisture_cool_min * 100:.0f} % → {tg.moisture_cool_set * 100:.0f} %", "spray bars, farm water"),
        ("Moisture, maturation", f"{tg.moisture_maturation[0] * 100:.0f}-{tg.moisture_maturation[1] * 100:.0f} %", "water when turning"),
        ("Oxygen in exhaust", f"≥ {tg.o2_min_pct:.0f} %", "fresh-air damper, overrides all"),
        ("Bed temperature", "60 °C, 45 °C to empty", "blower speed, recirculation"),
        ("Sanitisation", f"≥ {tg.sanitise_c:.0f} °C for {tg.sanitise_h:.0f} h", "timer restarts on a dip"),
        ("Bulk density at filling", f"≤ {tg.bulk_max_t_m3:.2f} t/m³", "bucket test at the mixer"),
        ("Particle size", f"{tg.particle_mm[0]:.0f}-{tg.particle_mm[1]:.0f} mm", "shredder"),
        ("pH", f"{tg.ph[0]}-{tg.ph[1]}", "lab, per batch"),
    ]
    for i, (k, v, how) in enumerate(window):
        y = wy + 26 + i * 21
        s.text(rx, y, k, 11.5, mu)
        s.text(rx + 175, y, v, 11.5, weight="600")
        s.text(rx + 345, y, how, 11.5, mu)
        s.line(rx, y + 6, rx + 560, y + 6, p["faint"], 0.5)

    # ---- water per batch ------------------------------------------------------------
    t = b["totals"]
    bx, by = 80, 690
    w0 = b["batch_kg"] * b["fill_moisture"] / 1000
    water_end = w0 - t["evaporated_t"] + t["metabolic_t"] + t["sprayed_t"]
    s.text(bx, by - 26, f"WATER PER {fmt(b['batch_kg'] / 1000)} t BATCH", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    scale = 3.2
    bars = [("in the fresh mix", w0, p["c"], ""), ("evaporated into the exhaust", -t["evaporated_t"], p["b"], ""),
            ("formed by the microbes", t["metabolic_t"], p["a"], ""), ("sprayed back (this recipe)", t["sprayed_t"], p["c"], ""),
            ("left in the bed at day 15", water_end, p["c"], f"{t['end_moisture'] * 100:.0f} % moisture")]
    for i, (label, v, col, note) in enumerate(bars):
        y = by + i * 30
        s.text(bx, y + 13, label, 11.5, mu)
        x0 = bx + 200
        s.rect(x0, y, max(abs(v) * scale, 1.5), 18, col, ink, 0.8)
        sign = "−" if v < 0 else ("+" if 0 < i < 4 else "")
        s.text(x0 + abs(v) * scale + 8, y + 13, f"{sign}{fmt(abs(v))} t {note}", 11.5, weight="600" if i == 4 else "normal")
    s.text(bx, by + 172, f"The exchanger condenses {fmt(t['condensate_t'])} t back out of the exhaust; spare condensate", 11, mu)
    s.text(bx, by + 188, "goes to the slurry store. 92 % of the heat recovered is this water condensing.", 11, mu)

    # ---- spray bars, cross-section ------------------------------------------------
    qx, qy, qw, qh = 690, 688, 240, 150
    s.text(qx - 12, by - 26, "SPRAY BARS, SECTION", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    s.rect(qx - 12, qy - 12, qw + 24, qh + 24, "url(#concrete)", ink, 1.2)
    s.rect(qx, qy, qw, qh, p["bg"], ink, 1)
    s.rect(qx, qy + qh - 80, qw, 80, p["b"], "none", 0, 'fill-opacity="0.75"')
    s.text(qx + qw / 2, qy + qh - 30, "bed", 11, anchor="middle")
    for k in range(1, 6):
        xa = qx + k * qw / 6
        s.line(xa, qy + qh - 6, xa, qy + qh - 60, cool, 1, 'marker-end="url(#arrCool)"')
    for xb_ in (qx + qw * 0.2, qx + qw * 0.5, qx + qw * 0.8):
        s.add(f'<circle cx="{xb_:.1f}" cy="{qy + 14}" r="5" fill="{p["bg"]}" stroke="{cool}" stroke-width="1.6"/>')
        s.path(f"M{xb_ - 22:.1f},{qy + 66} L{xb_:.1f},{qy + 19} L{xb_ + 22:.1f},{qy + 66}", cool, 0.8, extra='stroke-dasharray="2 3"')
    s.text(qx + qw + 22, qy + 18, "SP-10x: 3 bars", 11, weight="600")
    s.text(qx + qw + 22, qy + 34, "flat-fan nozzles", 10.5, mu)
    s.text(qx + qw + 22, qy + 50, f"{PROC.WaterModel().spray_m3_h:.0f} m³/h per tunnel", 10.5, mu)
    s.text(qx + qw + 22, qy + 76, "air up through the", 10.5, mu)
    s.text(qx + qw + 22, qy + 92, "spigot floor carries", 10.5, mu)
    s.text(qx + qw + 22, qy + 108, "water to the drier", 10.5, mu)
    s.text(qx + qw + 22, qy + 124, "bottom layer", 10.5, mu)
    s.text(qx - 12, qy + qh + 34, "TK-401 condensate → P-401 → XV-10x until sanitised;", 10.5, mu)
    s.text(qx - 12, qy + qh + 50, "farm water through XV-402 after (no germs back on).", 10.5, mu)

    # ---- control of the bars ----------------------------------------------------------
    kx, ky = 1100, 590
    s.text(kx, ky, "WHEN THE BARS COME ON", 10.5, mu, extra=f'letter-spacing="1.4" {mono}')
    for i, line in enumerate([
        "The PLC keeps a running water balance per tunnel:",
        "  water in at filling (weighbridge × moisture sample)",
        "  − evaporated (airflow × exhaust − inlet humidity, MT-201)",
        "  + formed (from the heat released) + sprayed (FT-10x).",
        f"Thermophilic: spray below {tg.moisture_hot_min * 100:.0f} % back to {tg.moisture_hot_set * 100:.0f} %.",
        f"Cooling: spray below {tg.moisture_cool_min * 100:.0f} % back to {tg.moisture_cool_set * 100:.0f} %, farm water only.",
        "A grab sample (oven-dry or squeeze test) corrects it daily.",
        "Spray only with the blower at full flow.",
    ]):
        s.text(kx, ky + 24 + i * 19, line, 11.5, ink if i in (0, 4, 5) else mu)

    s.text(32, s.h - 30, "Process model: model/compost_energy/process.py, docs/reference/process.md. Feedstock values are typical, not lab results; "
                         f"tunnels sized at 0.85 t/m³, the mix should be ≤ {tg.bulk_max_t_m3:.2f} (to settle on the pilot).", 11.5, mu)
    s.title_block("Process sheet", "CE-14")
    return s.render()


DRAWINGS = {
    "farm-unit-cutaway": unit_cutaway,
    "farm-unit-ga": general_arrangement,
    "heat-recovery-module": recovery_module,
    "farm-process-pid": process_pid,
    "farm-control": control,
    "farm-operating-modes": operating_modes_sheet,
    "farm-configurations": configuration_study,
    "farm-transfer-train": transfer_train,
    "farm-process-sheet": process_sheet,
}
