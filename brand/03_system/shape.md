# Shape language

- **Lines:** hairline only (1 px screen, 0.35 mm print), in `text` at 12–20 % opacity for structure, in `leaf` or `ember` when they carry meaning. No drop shadows anywhere.
- **Radius scale:** 0 (drawings, tables) · 8 px (inputs, chips) · 28 px (glass cards) · full (rings, pills, buttons).
- **Glass card:** surface at 70–75 % opacity, `backdrop-filter: blur(18px)`, 1 px inner hairline at 14 % white (dark) or 60 % white (light). Optional notch: a 40 px half-circle cut into one side, as in mood 3, used to hold a ring icon or a progress rail.
- **Ring + crosshair:** thin circles with small `+` markers at points of interest (mood 5). Used to annotate the CAD model and hero imagery.
- **Contour texture:** 40–120 parallel offset curves at 0.5 px, taken from the mark's band. Used as a background texture on dark only, at ≤ 25 % opacity.
- **Particles:** point clouds (≤ 1.5 px dots) for matter; warm particles drift up from heat sources. Procedural only.
- **Motion:** `cubic-bezier(0.22, 1, 0.36, 1)` (out-expo) for entrances, 600–900 ms; nothing bounces. Colour travels leaf → ember to show heat being made.
