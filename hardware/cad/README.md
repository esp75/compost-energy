# CAD: farm-scale unit

A parametric model of the unit in [docs/farm-unit.md](../../docs/reference/farm-unit.md), built with [CadQuery](https://cadquery.readthedocs.io). There are no hand-typed dimensions. Every size comes from [`model/compost_energy/industrial.py`](../../model/compost_energy/industrial.py), the same module that draws CE-06 to CE-14. Change an assumption there, and the drawings, the CAD model and the demo video all follow.

```bash
.venv/bin/pip install -e "model[cad]"
.venv/bin/python hardware/cad/farm_unit.py        # writes out/
.venv/bin/python -m pytest hardware/cad           # model and CAD agree
```

| File | What |
|---|---|
| [`out/farm-unit.step`](out/farm-unit.step) | Assembly, one solid per part, for FreeCAD, Fusion, SolidWorks |
| [`out/farm-unit.glb`](out/farm-unit.glb) | The same with colours, for the web viewer and the video |
| [`out/farm-unit.stl`](out/farm-unit.stl) | One merged mesh. GitHub shows it in 3D. |
| [`out/farm-unit.json`](out/farm-unit.json) | Geometry and model numbers that the video and the website read |
| [`out/parts.csv`](out/parts.csv) | 64 parts with material, size and volume |

The model has 4 tunnels (slab, walls, roofs, door frames and sectional doors), spigot-floor channels, the compost beds, 4 supply blowers, exhaust stubs and the Ø560 manifold, plus the heat-recovery skid: exchanger casing and 3 coils, booster fan, biofilter, condensate tank, the 85 m³ buffer tank TK-201 piped to the exchanger, the water and condensate lines, and the irrigation: three roof spray bars per tunnel fed by a header from the condensate tank. Four tunnels were chosen in the [configuration study](../../docs/explanation/configuration-study.md).

The beds are shown in one staggered moment ([CE-11](../drawings/farm-operating-modes.svg)): four batches started 3.75 days apart, so one is heating up, two are hot and one is cooling. Each bed is at the depth it has settled to by that day.

This is a concept model at the level of the drawings. It has no fixings, no reinforcement and no duct fittings, and nothing has been checked against a vendor.
