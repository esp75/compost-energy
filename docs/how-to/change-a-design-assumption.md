# Change a design assumption

The farm-scale drawings, the CAD model and the demo video are all generated from the Python model. You change a number once, in code, and everything downstream follows. Do not edit the SVG, STEP or video files by hand.

## Where the numbers live

| Change… | Edit | Then regenerate |
|---|---|---|
| Tunnel size, fans, the exchanger, the buffer tank | [`model/compost_energy/industrial.py`](../../model/compost_energy/industrial.py) | drawings, CAD, video |
| Layout choice (number of tunnels, transfer method) | [`model/compost_energy/configurations.py`](../../model/compost_energy/configurations.py) (`FINAL`) | drawings, CAD |
| Process: recipe, phase windows, moisture | [`model/compost_energy/process.py`](../../model/compost_energy/process.py) | drawings, video |
| Heat-exchanger physics | [`model/compost_energy/heat_exchanger.py`](../../model/compost_energy/heat_exchanger.py) | drawings |

## Steps

1. Change the value in the file above. If it is a design assumption from a source, put the source in a comment next to it, and label it MODEL.

2. Run the tests. They check that the sizing still meets the energy model:

   ```bash
   .venv/bin/python -m pytest model/tests hardware/cad -q
   ```

3. Regenerate the drawings. Each run writes the light and dark SVGs, and renders PNGs with headless Chrome:

   ```bash
   .venv/bin/python hardware/drawings/src/make_drawings.py
   ```

   The PNG step needs Node. Run `npm install` in `video/src` once, or pass `--no-png` to skip the PNGs. The SVGs are the source of truth; CI checks only the SVGs.

4. Regenerate the CAD model:

   ```bash
   .venv/bin/python hardware/cad/farm_unit.py
   ```

5. Check the diff. `git diff --stat` should list only the files that really changed. If a drawing changed that you did not expect, the value you changed is used somewhere you did not think of. Look for it with `grep -rn "<name>" model/`.

6. Update the reference page if a number in the text changed: [Farm-scale unit](../reference/farm-unit.md) quotes many of them.

## Why this is strict

CI runs step 3 on every push and fails if the committed drawings are not exactly what the model produces. This is what keeps the drawings honest. If CI fails on the drawings, the committed SVGs are stale: run the script and commit the result.
