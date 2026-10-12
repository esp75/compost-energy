# Drawings

All drawings are generated from one script, so a dimension changes in one place:

```bash
python hardware/drawings/src/make_drawings.py
```

It writes the light SVGs here (for GitHub) and night-theme copies in [`dark/`](dark/) (for the website). PNG exports are in [`png/`](png/) (`rsvg-convert -w 2400 <name>.svg`).

**Dimensions are indicative.** The patent gives no dimensions. They come from the prototype bill of materials ([`bom/prototypes.csv`](../bom/prototypes.csv)): 500 × 500 mesh and PVC dividers, 120 × 24 decking boards, 70 × 70 posts, a 600 × 400 × 420 Euro container. Nothing here has been checked against a physical build.

| No. | File | What |
|---|---|---|
| CE-01 | [`compostito-cutaway.svg`](compostito-cutaway.svg) | Isometric cutaway of the home unit: chambers A-D, mesh baskets, vents and airflow, drip line, coil in concrete, stilts. Chamber A is lifted to show the coil. |
| CE-02 | [`prototype-2-build.svg`](prototype-2-build.svg) | Front, side and top views with dimensions, the hatch hinge detail, and a parts list keyed to the BOM |
| CE-03 | [`exchanger-coil.svg`](exchanger-coil.svg) | Coil in its concrete block: prototype 2 (one 3 m tube) against prototype 3 (two tubes), sections, expected output, and where the thermal resistance sits |
| CE-04 | [`water-loop-pid.svg`](water-loop-pid.svg) | P&ID of the by-pass on the heating return, with sensor tags matching the [logger firmware](../logger/) |
| CE-05 | [`farm-plant-layout.svg`](farm-plant-layout.svg) | First-pass farm plant: reception → reactors A/B/C → exhaust-air exchanger → farm heat users, then maturation → storage → fields |
| - | [`system-schematic.svg`](system-schematic.svg) | The original stacked-chamber schematic from the 2024 patent |

![Compostito cutaway](png/compostito-cutaway.png)

Still to do:

- [ ] Re-dimension CE-02 from the first physical build
- [ ] Source CAD (FreeCAD) for the box and the coil block

Source formats are welcome (FreeCAD, KiCad, SVG). Please export a PNG or SVG alongside, so they render on GitHub.
