# Run the model

In this tutorial you will install the Python package, run the energy model, simulate a prototype run, and check that the results are the same as the ones in the repository. It takes about 15 minutes. You need Python 3.10 or newer.

## 1. Install

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -e "model[test]"
```

## 2. Run the energy model

```bash
.venv/bin/python model/scripts/run_scenarios.py
```

This prints one row per scenario (heat per year, mean power, auxiliary energy and net value) for the house, the apartment block and the farm, and rebuilds the figures in [`figures/`](../../figures/). The farm row is the one the [Farm-scale unit](../reference/farm-unit.md) is sized from.

Open [`figures/scenarios_net_value.png`](../../figures/scenarios_net_value.png). It shows why the home scale was dropped: the net value per year is negative there, and positive at farm scale.

## 3. Simulate a prototype run

```bash
.venv/bin/python model/scripts/simulate_run.py
.venv/bin/python model/scripts/analyze_run.py data/simulated/raw_run_01.csv
```

The first command writes a **SIMULATED** logger file, with sensor faults added on purpose: error codes, a stuck sensor, flow spikes, power cuts and duplicate rows. The second cleans it and writes the figures for the cleaned run.

Open [`figures/sim_run_01_raw_vs_clean.png`](../../figures/sim_run_01_raw_vs_clean.png) to see the faults and what the cleaning removes.

The simulation has the true answer, so you can check the cleaning. The energy computed from the cleaned log should match the true energy within about 0.1 %. That check is part of the test suite (step 5).

## 4. Compare with published measurements

```bash
.venv/bin/python model/scripts/compare_reference.py
```

This runs the model against two published datasets from other groups (bins and a farm composter) and writes [`figures/reference_bins_vs_simulation.png`](../../figures/reference_bins_vs_simulation.png) and [`figures/reference_farm_heat_recovery.png`](../../figures/reference_farm_heat_recovery.png). The datasets are not Compost Energy measurements. See [reference data](../../data/reference/README.md).

## 5. Run the tests

```bash
.venv/bin/python -m pytest model/tests -q
```

All tests should pass. They check the scenario numbers, energy conservation in the simulation, the cleaning rules, and the reference comparison.

## What you have now

- The energy numbers, reproduced from code.
- A simulated run that you can compare with its own true answer.
- The same figures that appear in the README.

To change an assumption and see it flow through to the drawings and CAD, go to [Change a design assumption](../how-to/change-a-design-assumption.md).
