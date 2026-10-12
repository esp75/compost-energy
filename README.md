<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/white_on_trans.png">
    <img src="assets/brand/black_on_trans.png" width="120" alt="Compost Energy logo">
  </picture>
</p>

# Compost Energy

**Open hardware for recovering heat from compost.** A "biological boiler" composts each phase in its own chamber and draws heat from the thermophilic core through a buried water loop, which pre-heats an existing heating system.

This repo contains the full engineering record: the (now open) patent, the system design, an energy model at three scales, a physics simulation of a prototype run, the data pipeline that will process real logger data, and the logger firmware.

![System schematic](hardware/drawings/system-schematic.svg)

## The short version

1. **2024:** designed a home unit that turns food scraps into heating and fertiliser. Wrote a provisional patent, specified three prototypes (~€640 BOM) and sized the heat exchanger.
2. **The numbers didn't work for homes.** A household's waste is worth **~59 W** of heat on average. A 50 W fan and controller make it net-negative, and the exchanger had been over-estimated ~70× by one wrong assumption ([details](docs/heat-exchanger.md)).
3. **They do work at farm scale.** About 14,000 t/yr of farm feedstock yields **~2 GWh/yr** of heat, worth **~€159k/yr net**. Microbial heat grows with volume while losses grow with surface area. → [pivot.md](docs/pivot.md)

![Net value by scale](figures/scenarios_net_value.png)

## Simulated prototype run

> ⚠️ **Everything in this section is SIMULATED.** Nothing here was measured. The data comes from a physics model of a 200 kg insulated prototype ([`simulate.py`](model/compost_energy/simulate.py)), with realistic sensor faults injected. It shows what the prototype should do if the physics is right, and it exercises the same pipeline that real logger data will go through. Real runs will go in [`data/measured/`](data/measured/).

The model: two microbial populations (mesophilic + thermophilic) with cardinal-temperature kinetics, first-order substrate decay, a lumped energy balance (walls, buoyant ventilation, turning losses) and an effectiveness-NTU exchanger. Energy is conserved to machine precision (tested).

| | |
|---|---|
| ![temperatures](figures/sim_run_01_temperatures.png) | ![heat](figures/sim_run_01_extracted_heat.png) |

- Core reaches **65 °C** by day 3, stays above 55 °C for **8.5 days** (enough for pathogen kill), re-heats after the day-9.5 turning, and matures to ambient.
- The loop recovers **12.4 kWh over 45 days**: about 84 W while pumping, with a 3.4 °C outlet rise at 0.35 L/min.
- **Only ~9% of the microbial heat is recovered.** The rest leaves through the walls and vents:

![heat ledger](figures/sim_run_01_heat_ledger.png)

**Data cleaning.** The raw log includes DS18B20 error codes (−127/85 °C), a sensor stuck for 1.5 days, flow-meter spikes, logger power cuts, duplicate rows and out-of-order timestamps. The pipeline removes them and leaves long gaps empty rather than inventing data. Energy computed from the cleaned noisy log: **12.42 kWh, against 12.41 kWh true** (0.1% error).

![raw vs clean](figures/sim_run_01_raw_vs_clean.png)

## Repository

```
docs/
  patent/            2024 provisional patent: French original + English translation
  system-design.md   chambers, process conditions, heat path, prototypes
  energy-model.md    house / apartment block / farm energy balance
  heat-exchanger.md  the 2024 calculation, what was wrong, design consequences
  pivot.md           why home units were dropped for farm scale
hardware/
  bom/               prototype 1-3 bill of materials
  drawings/          system schematic (more to come)
  logger/            ESP32 + DS18B20 logger firmware and wiring (not yet built)
model/
  compost_energy/    energy_balance, heat_exchanger, simulate, clean
  scripts/           run_scenarios, simulate_run, analyze_run
  tests/             18 tests: scenario numbers, energy conservation, cleaning
data/
  simulated/         raw_run_01.csv (noisy log), clean_run_01.csv, truth, ledger, report
  measured/          real runs go here
figures/             generated
```

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -e "model[test]"
.venv/bin/python model/scripts/run_scenarios.py                 # energy model + exchanger figures
.venv/bin/python model/scripts/simulate_run.py                  # writes data/simulated/raw_run_01.csv
.venv/bin/python model/scripts/analyze_run.py data/simulated/raw_run_01.csv
.venv/bin/python -m pytest model/tests
```

## Roadmap

- [ ] Build prototype 2 and the logger; first measured run in `data/measured/`
- [ ] Prototype 3 (double exchanger length): measure how output scales with area
- [ ] Fit the simulation's kinetic and loss parameters to measured data
- [ ] Dimensioned drawings and coil layout ([drawings/README](hardware/drawings/README.md))
- [ ] Farm-scale concept: reactor and conveyor design, exhaust-air heat recovery

## License

Hardware CERN-OHL-P v2 · docs and data CC-BY-4.0 · code MIT · the logo is not licensed. See [LICENSE.md](LICENSE.md).

Maxime Kadri, physics (Lyon). Designed in 2024; opened in 2026.
