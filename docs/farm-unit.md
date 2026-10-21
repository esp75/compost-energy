# Farm-scale unit

The farm scenario in [energy-model.md](energy-model.md) says there are about 2 GWh/yr of heat in 14,279 t/yr of farm feedstock. This page turns that into hardware: tunnels, fans, an exhaust-air heat exchanger and the controls. Every number comes from [`industrial.py`](../model/compost_energy/industrial.py), and the drawings CE-06 to CE-11 are generated from the same module.

Nothing at this scale has been built. These are design estimates for a pilot.

![Farm-scale unit, cutaway](../hardware/drawings/png/farm-unit-cutaway.png)

## Design point

| | |
|---|---|
| Feedstock | 39.1 t/day (46 m³), manure, silage and straw |
| Tunnels | 3 × 5.0 × 4.0 × 16.5 m inner, 988 m³ in all |
| Walls | 200 mm precast concrete + 100 mm PIR, U = 0.21 W/m²K |
| Aeration | 7,030 m³/h through a spigot floor, 3 blowers of 2.7 kW at 2.5 kPa |
| Heat recovery | 548 kW over the 5-month heating season |
| Exchanger | 216 m² plate-fin, exhaust 60 → 35 °C, water 30 → 50 °C, 5 K pinch |
| Condensate | 0.69 m³/h, re-used to wet the beds |
| Biofilter | 56 m² at 125 m³/m²·h |

## Where the heat is

Compost exhaust leaves the bed saturated. Cooling saturated air from 60 to 35 °C releases 330 kJ per kg of dry air, and only 25 kJ of that is sensible heat. **92 % of the recovered heat is water vapour condensing on the coils.** The exchanger is therefore sized on moist-air enthalpy, and it needs a condensate drain and a wash bar.

Wall losses are 3.8 kW per tunnel, about 2 % of the duty. In the 200 kg prototype box most of the heat left through the walls. This is the same scale effect, now in numbers.

The exchanger area is scaled from one measured farm composter: 23.3 kW from 9.2 m² (Kojima et al. 2022, [reference data](../data/reference/README.md)). A coil vendor would size the real unit.

## How a batch moves through the phases

The 2024 patent gives each composting phase its own chamber, and material drops from one chamber to the next. At farm scale there are two ways to do this ([CE-11](../hardware/drawings/farm-operating-modes.svg)).

**A. Staggered batches (base design).** A wheel loader fills a tunnel through its door, and the batch stays there for all 15 days. The phase changes by changing the air: recirculation while it heats up, the hot hold, then fresh air to cool it. The three tunnels start 5 days apart, so one is always heating up, one is hot and one is cooling. The combined exhaust stays fairly steady. Every 5 days one tunnel is emptied into the maturation hall and refilled with 196 t (230 m³) of fresh feedstock. That fills the bed to 2.8 m, and it settles to 1.3 m by day 15.

**B. Transfer between tunnels.** Each tunnel holds one phase for 5 days. Every 5 days the loader empties T-103, moves T-102 into T-103 and T-101 into T-102, then refills T-101.

| | A, staggered | B, transfer |
|---|---|---|
| Loader work | 67 t/day | 132 t/day |
| Diesel | 17 L/day | 33 L/day |
| Hot material moved in the open | never | twice per batch |
| Heat released during moves | none | ≈ 19 kW (upper bound) |
| Net value | **€157k/yr** | **€129k/yr** |

A is the base design. The patent's chamber-per-phase idea becomes a control scheme: each tunnel passes through the phases in time instead of in space. B is worth testing on a pilot only if remixing at day 5 and day 10 turns out to raise the temperature or the heat recovered.

## Control

The compost process has priority. Four loops run per tunnel ([CE-10](../hardware/drawings/farm-control.svg)):

1. **Temperature:** the median core temperature sets blower speed and recirculation.
2. **Oxygen floor:** below 5 % O₂ the fresh-air damper opens and overrides loop 1.
3. **Sanitisation:** at least 55 °C for 3 days (US EPA PFRP for in-vessel systems). The timer restarts if any probe drops below.
4. **Heat recovery:** the pump holds the supply temperature, and the by-pass opens when it can't. Heat demand never sets the airflow.

## What this changed in the energy model

Sizing the fans showed that the farm scenario had under-counted aeration. The fans need 8.1 kW, against the 3-5 kW assumed. The farm auxiliaries are now 13.1 kW, and the net value drops from €159k to €157k a year. A test keeps the two numbers in step.

## Open questions

- **Winter throughput.** The scenario delivers 7 months of feedstock's heat in 5 months. With stockpiling, the tunnels would need to run faster in winter than the average sizing assumes.
- **Exhaust blending.** In mode A the cooling tunnel's exhaust is cooler. Routing it past the exchanger may beat mixing it in.
- **Loader assumptions.** The diesel, throughput and heat lost per hot move are typical values, not measurements. They are set in `Handling` in `industrial.py`.
