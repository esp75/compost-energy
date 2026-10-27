# Contributing

Issues and pull requests are welcome, especially:

- **Measured data.** Logs from real compost heat-recovery runs go in `data/measured/`, with a README saying how they were measured. The data pipeline in `model/compost_energy/clean.py` should handle them as they are.
- **Corrections to the model.** If a number is wrong, open an issue with the source. Every figure in this repo is labelled MODEL, SIMULATED or MEASURED, and changes should keep it that way.
- **Drawings and CAD.** Drawings and the CAD model are generated from `model/compost_energy/industrial.py`. Change the numbers there, not in the SVG or STEP files, then run `make_drawings.py` and `hardware/cad/farm_unit.py`.

Before opening a pull request:

```bash
.venv/bin/python -m pytest model/tests hardware/cad
.venv/bin/python hardware/drawings/src/make_drawings.py   # commit the regenerated drawings
```

CI checks both: the tests, and that the drawings in the repo match what the model generates.

By contributing you agree that your contribution is released under the licence of the part you changed (see [LICENSE.md](LICENSE.md)).
