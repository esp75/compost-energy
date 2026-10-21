"""Parametric CAD model of the farm-scale unit (drawings CE-06..CE-11).

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

The beds are shown in the staggered state of CE-11: T-101 on day 12.5
(cooling), T-102 on day 2.5 (heating up), T-103 on day 7.5 (hot), each
settled to its depth on that day.
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

# Colours (RGBA 0-1), close to the drawing palette.
C = {
    "concrete": (0.80, 0.80, 0.78, 1.0),
    "roof": (0.72, 0.73, 0.72, 1.0),
    "door": (0.55, 0.68, 0.82, 1.0),
    "compost": (0.42, 0.30, 0.20, 1.0),
    "plenum": (0.25, 0.45, 0.85, 1.0),
    "duct_hot": (0.76, 0.25, 0.05, 1.0),
    "duct_cool": (0.15, 0.39, 0.92, 1.0),
    "steel": (0.62, 0.64, 0.66, 1.0),
    "hx": (0.86, 0.45, 0.40, 1.0),
    "coil": (0.82, 0.55, 0.30, 1.0),
    "biofilter": (0.55, 0.62, 0.30, 1.0),
    "tank": (0.70, 0.82, 0.95, 1.0),
    "pipe_hot": (0.85, 0.30, 0.08, 1.0),
    "pipe_cool": (0.20, 0.45, 0.90, 1.0),
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
        day = ((i + 2) % N + 0.5) * STAGE      # staggered: T-101 cooling, T-102 heating up, T-103 hot
        add(f"{tag}-bed", box(bx, bx + W, 0, L, SLAB + 0.01, SLAB + 0.01 + bed_depth(day)), "compost",
            f"compost, day {day:g}", "process")

    # supply blowers behind the back wall, ducted into the plenum
    for i, bx in enumerate(BAYS):
        tag = f"K-10{i + 1}"
        xc = bx + W / 2
        add(f"{tag}-blower", cyl(xc, -1.3, 0.0, 0.9, 0.9), "steel", "centrifugal blower 2.7 kW", "air")
        add(f"{tag}-duct", pipe_y(-0.85, -T, xc, SLAB / 2 + 0.05, M["duct_tunnel_mm"] / 1000 * 0.9),
            "duct_cool", "galvanised duct", "air")

    # ---- exhaust: stubs and manifold -------------------------------------
    zm = ROOF_Z + LAY.manifold_rise_m
    d_t = 0.315
    d_m = 0.500
    ey = LAY.exhaust_y_m
    for i, bx in enumerate(BAYS):
        xs = bx + W / 2
        add(f"X-10{i + 1}-stub", cyl(xs, ey, ROOF_Z, zm, d_t), "duct_hot", "PP duct Ø315", "air")
    hx0, hx1, hy0, hy1, hz0, hz1 = LAY.hx
    xd = (hx0 + hx1) / 2
    add("manifold", pipe_x(BAYS[0] + W / 2, xd, ey, zm, d_m), "duct_hot", "PP duct Ø500", "air")
    add("manifold-drop", cyl(xd, ey, hz1, zm + d_m / 2, d_m), "duct_hot", "PP duct Ø500", "air")

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
    # water loop to the farm heat users, leaving the skid towards the tunnels
    add("water-supply", pipe_x(X_ALL + 0.4, hx0, hy1 - 0.6, 1.0, 0.11), "pipe_hot", "steel DN100, insulated", "heat")
    add("water-return", pipe_x(X_ALL + 0.4, hx0, hy1 - 1.2, 0.6, 0.11), "pipe_cool", "steel DN100, insulated", "heat")

    return assy, parts


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
    lay = {k: list(getattr(LAY, k)) for k in ("hx", "fan", "tank", "biofilter")}
    lay.update({k: getattr(LAY, k) for k in ("wall_m", "slab_m", "door_w_m", "door_h_m", "exhaust_y_m",
                                             "manifold_rise_m", "spigot_pitch_m")})
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
    }
    (OUT / "farm-unit.json").write_text(json.dumps(meta, indent=1))
    beds = sum(p["volume_m3"] for p in parts if p["part"].endswith("-bed"))
    print(f"{len(parts)} parts; compost in the tunnels {beds:.0f} m³ "
          f"(model average {M['solids_per_tunnel_m3'] * N:.0f} m³)")
    for f in sorted(OUT.iterdir()):
        print(f"  {f.name:20s} {f.stat().st_size / 1e6:6.2f} MB")


if __name__ == "__main__":
    main()
