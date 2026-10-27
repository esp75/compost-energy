"""Parametric CAD model of the farm-scale unit (drawings CE-06..CE-12).

    .venv/bin/python hardware/cad/farm_unit.py

Writes to hardware/cad/out/:

    farm-unit.step   the assembly, one solid per part, for CAD tools
    farm-unit.glb    the same assembly with colours, for the web viewer and the video
    farm-unit.stl    one merged mesh, for quick viewing
    farm-unit.json   geometry and model numbers for the web viewer and the video
    parts.csv        part list with sizes and volumes

Every dimension comes from model/compost_energy/industrial.py (size, layout,
operating_modes), the same source as the drawings. The model is in
millimetres. Axes: x across the tunnels, y along them (doors at the front,
y = tunnel length), z up.

The beds are shown in the staggered state of CE-11: four batches started
3.75 days apart, each settled to its depth on the day it has reached.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "model"))

from compost_energy.energy_balance import FARM, evaluate  # noqa: E402
from compost_energy.industrial import layout, operating_modes, size  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"
MM = 1000.0

M = size()
G = layout()
OPS = operating_modes()
LAY = G["layout"]

W, H, L = G["width_m"], G["height_m"], G["length_m"]
T, SLAB = LAY.wall_m, LAY.slab_m
N = M["n_tunnels"]
X_ALL = G["overall_x_m"]
ROOF_Z = G["roof_z_m"]
BAYS = G["bay_x_m"]
STAGE = OPS["stage_days"]

def _rgb(hexcode: str, a: float = 1.0) -> tuple:
    h = hexcode.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (a,)


# Colours (RGBA 0-1) from the brand tokens (brand/10_color/tokens.json): ember = heat, teal = cold side.
C = {
    "concrete": _rgb("#c9d1cc"),
    "roof": _rgb("#aeb8b2"),
    "door": _rgb("#cfe0df"),
    "compost": _rgb("#5a4128"),
    "plenum": _rgb("#2f6f73"),
    "duct_hot": _rgb("#b23f0a"),
    "duct_cool": _rgb("#2f6f73"),
    "steel": _rgb("#8f9a94"),
    "hx": _rgb("#e0882a"),
    "coil": _rgb("#c9a06a"),
    "biofilter": _rgb("#7a8f6a"),
    "tank": _rgb("#cfe0df"),
    "buffer": _rgb("#dfe5e1"),
    "pipe_hot": _rgb("#f26a21"),
    "pipe_cool": _rgb("#4fb3b0"),
}


def box(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    """Axis-aligned box from metre coordinates."""
    return (cq.Workplane("XY")
            .box((x1 - x0) * MM, (y1 - y0) * MM, (z1 - z0) * MM, centered=False)
            .translate((x0 * MM, y0 * MM, z0 * MM)))


def cyl(x, y, z0, z1, d) -> cq.Workplane:
    """Vertical cylinder of diameter d (m)."""
    return (cq.Workplane("XY").circle(d * MM / 2).extrude((z1 - z0) * MM)
            .translate((x * MM, y * MM, z0 * MM)))


def pipe_x(x0, x1, y, z, d) -> cq.Workplane:
    return (cq.Workplane("YZ").circle(d * MM / 2).extrude((x1 - x0) * MM)
            .translate((x0 * MM, y * MM, z * MM)))


def pipe_y(y0, y1, x, z, d) -> cq.Workplane:
    return (cq.Workplane("XZ").circle(d * MM / 2).extrude(-(y1 - y0) * MM)
            .translate((x * MM, y0 * MM, z * MM)))


def pipe_run(pts, z, d) -> cq.Workplane:
    """Horizontal pipe through axis-aligned (x, y) points at height z, with elbows."""
    run = None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = pipe_x(min(x0, x1), max(x0, x1), y0, z, d) if y0 == y1 else pipe_y(min(y0, y1), max(y0, y1), x0, z, d)
        run = seg if run is None else run.union(seg)
    for x, y in pts[1:-1]:
        run = run.union(cq.Workplane("XY").sphere(d * MM / 2).translate((x * MM, y * MM, z * MM)))
    return run


def bed_depth(day: float) -> float:
    return OPS["fill_depth_m"] * 0.95 ** day


def build() -> tuple[cq.Assembly, list[dict]]:
    assy = cq.Assembly(name="farm-unit")
    parts: list[dict] = []

    def add(name, shape, colour, material, group):
        assy.add(shape, name=name, color=cq.Color(*C[colour]))
        bb = shape.val().BoundingBox()
        parts.append({
            "part": name, "group": group, "material": material,
            "x_mm": round(bb.xlen), "y_mm": round(bb.ylen), "z_mm": round(bb.zlen),
            "volume_m3": round(shape.val().Volume() / 1e9, 3),
        })

    # ---- civil: slab, walls, roofs, doors --------------------------------
    add("slab", box(0, X_ALL, -T, L + T, 0, SLAB), "concrete", "precast concrete", "civil")
    add("wall-back", box(0, X_ALL, -T, 0, SLAB, ROOF_Z - T), "concrete", "concrete + PIR", "civil")
    for i in range(N + 1):
        x0 = i * (W + T)
        add(f"wall-{i + 1}", box(x0, x0 + T, 0, L, SLAB, ROOF_Z - T), "concrete", "concrete + PIR", "civil")
    for i, bx in enumerate(BAYS):
        tag = f"T-10{i + 1}"
        add(f"{tag}-roof", box(bx - T / 2, bx + W + T / 2, -T, L + T, ROOF_Z - T, ROOF_Z), "roof",
            "concrete + PIR", "civil")
        dx0 = bx + (W - LAY.door_w_m) / 2
        # front wall around the door opening: two jambs and a lintel
        add(f"{tag}-jamb-l", box(bx, dx0, L, L + T, SLAB, ROOF_Z - T), "concrete", "concrete + PIR", "civil")
        add(f"{tag}-jamb-r", box(dx0 + LAY.door_w_m, bx + W, L, L + T, SLAB, ROOF_Z - T), "concrete",
            "concrete + PIR", "civil")
        add(f"{tag}-lintel", box(dx0, dx0 + LAY.door_w_m, L, L + T, SLAB + LAY.door_h_m, ROOF_Z - T),
            "concrete", "concrete + PIR", "civil")
        add(f"{tag}-door", box(dx0, dx0 + LAY.door_w_m, L + 0.05, L + 0.13, SLAB, SLAB + LAY.door_h_m),
            "door", "insulated sectional door", "civil")

    # ---- process: spigot floor channels and compost beds ------------------
    n_ch = int(W / LAY.spigot_pitch_m) - 1
    for i, bx in enumerate(BAYS):
        tag = f"T-10{i + 1}"
        ch = None
        for c in range(1, n_ch + 1):
            xc = bx + c * LAY.spigot_pitch_m
            piece = box(xc - 0.04, xc + 0.04, 0.2, L - 0.2, SLAB - 0.12, SLAB + 0.01)
            ch = piece if ch is None else ch.union(piece)
        add(f"{tag}-spigot-floor", ch, "plenum", "HDPE channels with spigots", "process")
        day = ((N - i) % N + 0.5) * STAGE      # staggered: each tunnel one stage behind the next
        add(f"{tag}-bed", box(bx, bx + W, 0, L, SLAB + 0.01, SLAB + 0.01 + bed_depth(day)), "compost",
            f"compost, day {day:g}", "process")

    # supply blowers behind the back wall, ducted into the plenum
    for i, bx in enumerate(BAYS):
        tag = f"K-10{i + 1}"
        xc = bx + W / 2
        add(f"{tag}-blower", cyl(xc, -1.3, 0.0, 0.9, 0.9), "steel", f"centrifugal blower {M['blower_kw_each']:.1f} kW", "air")
        add(f"{tag}-duct", pipe_y(-0.85, -T, xc, SLAB / 2 + 0.05, M["duct_tunnel_mm"] / 1000 * 0.9),
            "duct_cool", "galvanised duct", "air")

    # ---- exhaust: stubs and manifold -------------------------------------
    zm = ROOF_Z + LAY.manifold_rise_m
    d_t = 0.355      # per tunnel, sized for its blower's peak
    d_m = 0.560
    ey = LAY.exhaust_y_m
    for i, bx in enumerate(BAYS):
        xs = bx + W / 2
        add(f"X-10{i + 1}-stub", cyl(xs, ey, ROOF_Z, zm, d_t), "duct_hot", "PP duct Ø355", "air")
    hx0, hx1, hy0, hy1, hz0, hz1 = LAY.hx
    xd = (hx0 + hx1) / 2
    add("manifold", pipe_x(BAYS[0] + W / 2, xd, ey, zm, d_m), "duct_hot", "PP duct Ø560", "air")
    add("manifold-drop", cyl(xd, ey, hz1, zm + d_m / 2, d_m), "duct_hot", "PP duct Ø560", "air")

    # ---- heat-recovery skid ----------------------------------------------
    add("HX-201-casing", box(hx0, hx1, hy0, hy1, hz0, hz1).shell(-60), "hx",
        "insulated stainless casing", "heat")
    for c in range(3):
        z0 = 0.5 + c * 0.9
        add(f"HX-201-coil-{c + 1}", box(hx0 + 0.2, hx1 - 0.2, hy0 + 0.2, hy1 - 0.2, z0, z0 + 0.7), "coil",
            "Al fins on stainless tubes", "heat")
    fx0, fx1, fy0, fy1, fz0, fz1 = LAY.fan
    add("K-201-fan", box(fx0, fx1, fy0, fy1, fz0, fz1), "steel", "booster fan", "air")
    add("K-201-inlet", pipe_x(hx1, fx0, (fy0 + fy1) / 2, 0.8, 0.45), "duct_cool", "PP duct", "air")
    bf = LAY.biofilter
    xb = (fx0 + fx1) / 2
    add("K-201-to-biofilter", pipe_y(fy1, bf[2], xb, 0.8, 0.45), "duct_cool", "PP duct", "air")
    add("F-301-biofilter", box(*bf), "biofilter", "wood chip bed in concrete bunker", "air")
    tx0, tx1, ty0, ty1, tz0, tz1 = LAY.tank
    add("TK-401-condensate", cyl((tx0 + tx1) / 2, (ty0 + ty1) / 2, tz0, tz1, tx1 - tx0), "tank",
        "PE tank", "heat")
    add("condensate-line", pipe_x(hx1, tx0, (ty0 + ty1) / 2, 0.25, 0.08), "pipe_cool", "PE pipe", "heat")
    # irrigation: TK-401 -> P-401 -> header behind the tunnels -> three roof spray bars per tunnel (CE-09, CE-14)
    zs = ROOF_Z - T - 0.35
    zh = ROOF_Z + 0.25
    for i, bx in enumerate(BAYS):
        bars = None
        for f in (0.2, 0.5, 0.8):
            bar = pipe_y(0.3, L - 0.3, bx + W * f, zs, 0.06)
            bars = bar if bars is None else bars.union(bar)
        feed = pipe_run([(bx + W * 0.2, 0.3), (bx + W * 0.2, -0.5), (bx + W * 0.8, -0.5), (bx + W * 0.8, 0.3)], zs, 0.06)
        add(f"SP-10{i + 1}-spray-bars", bars.union(feed), "pipe_cool", "PE spray bars, flat-fan nozzles", "water")
        add(f"SP-10{i + 1}-drop", cyl(bx + W / 2, -0.5, zs, zh, 0.06), "pipe_cool", "PE pipe", "water")
    tcx, tcy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    add("irrigation-header", pipe_run([(BAYS[0] + W / 2, -0.5), (tcx, -0.5), (tcx, tcy)], zh, 0.08), "pipe_cool",
        "PE DN65 irrigation header", "water")
    add("irrigation-riser", cyl(tcx, tcy, tz1, zh, 0.08), "pipe_cool", "PE DN65, P-401 at the tank", "water")
    # water: exchanger -> buffer tank TK-201 -> farm heat users
    bcx, bcy, bdia = LAY.buffer
    add("TK-201-buffer", cyl(bcx, bcy, 0.0, LAY.buffer_h_m, bdia), "buffer",
        f"insulated steel tank {M['buffer_m3']:.0f} m³", "heat")
    # out of the back of the skid, along behind it, into the side of the tank
    xs, xr = (hx0 + hx1) / 2, (hx0 + hx1) / 2 + 0.6
    tank_in = bcx - bdia / 2 + 0.1
    add("water-supply", pipe_run([(xs, hy0 + 0.1), (xs, bcy + 0.5), (tank_in, bcy + 0.5)], 2.6, 0.11), "pipe_hot",
        "steel DN100, insulated", "heat")
    add("water-return", pipe_run([(xr, hy0 + 0.1), (xr, bcy - 0.5), (tank_in, bcy - 0.5)], 1.2, 0.11), "pipe_cool",
        "steel DN100, insulated", "heat")
    add("users-supply", pipe_x(bcx + bdia / 2 - 0.1, bcx + bdia / 2 + 3.0, bcy, 1.8, 0.11), "pipe_hot",
        "steel DN100 to heat users", "heat")
    add("users-return", pipe_x(bcx + bdia / 2 - 0.1, bcx + bdia / 2 + 3.0, bcy + 0.8, 0.9, 0.11), "pipe_cool",
        "steel DN100 from heat users", "heat")

    return assy, parts


def _process() -> dict:
    """Phase boundaries and water of one batch (process.py), for the video (MODEL)."""
    from compost_energy import process as proc
    b = proc.run_batch()
    ph = {p["phase"]: p for p in proc.phases(b)}
    return {"t45_day": ph["mesophilic"]["end"], "cool_day": ph["cooling"]["start"],
            "sanitised_day": b["sanitised_day"], "fill_moisture": b["fill_moisture"],
            "end_moisture": b["totals"]["end_moisture"], "evaporated_t": b["totals"]["evaporated_t"],
            "spray_m3_h": proc.WaterModel().spray_m3_h}


def _study() -> dict:
    """The configuration study's verdict, for the video's closing numbers (MODEL)."""
    from compost_energy import configurations as cfg
    final = next(o for o in cfg.all_options() if o.code == cfg.FINAL)
    n = cfg.evaluate_option(final).numbers
    return {"final": cfg.FINAL, "capex_eur": n["capex"], "value_after_capital_eur": n["value_eur"],
            "low_capex_eur": cfg.evaluate_option(final, cfg.LOW).numbers["capex"],
            "high_capex_eur": cfg.evaluate_option(final, cfg.HIGH).numbers["capex"]}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    assy, parts = build()
    assy.export(str(OUT / "farm-unit.step"))
    assy.export(str(OUT / "farm-unit.glb"))
    cq.exporters.export(assy.toCompound(), str(OUT / "farm-unit.stl"), tolerance=5, angularTolerance=0.3)
    with open(OUT / "parts.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(parts[0]))
        w.writeheader()
        w.writerows(parts)
    lay = {k: list(getattr(LAY, k)) for k in ("hx", "fan", "tank", "biofilter", "buffer")}
    lay.update({k: getattr(LAY, k) for k in ("wall_m", "slab_m", "door_w_m", "door_h_m", "exhaust_y_m",
                                             "manifold_rise_m", "spigot_pitch_m", "buffer_h_m")})
    meta = {
        "geometry": {"width_m": W, "height_m": H, "length_m": L, "overall_x_m": X_ALL, "roof_z_m": ROOF_Z,
                     "bay_x_m": BAYS, "n_tunnels": N, **lay},
        "model": {k: v for k, v in M.items() if isinstance(v, (int, float))},
        "operations": {k: v for k, v in OPS.items() if isinstance(v, (int, float))}
                      | {"staggered_net_eur": OPS["staggered"]["net_eur"],
                         "transfer_net_eur": OPS["transfer"]["net_eur"]},
        "farm": {"net_eur": evaluate(FARM).net_eur, "heat_kwh": evaluate(FARM).heat_kwh,
                 "feedstock_t_per_year": FARM.waste_kg_per_year / 1000},
        "measured": {"kojima2022_recovery_share": 23.3 / 61.8},
        "study": _study(),
        "process": _process(),
    }
    (OUT / "farm-unit.json").write_text(json.dumps(meta, indent=1))
    beds = sum(p["volume_m3"] for p in parts if p["part"].endswith("-bed"))
    print(f"{len(parts)} parts; compost in the tunnels {beds:.0f} m³ "
          f"(model average {M['solids_per_tunnel_m3'] * N:.0f} m³)")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name:20s} {f.stat().st_size / 1e6:6.2f} MB")


if __name__ == "__main__":
    main()
