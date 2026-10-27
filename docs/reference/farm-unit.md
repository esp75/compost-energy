# Farm-scale unit

The farm scenario in [Energy model](../explanation/energy-model.md) says there are about 2 GWh/yr of heat in 14,279 t/yr of farm feedstock. This page turns that into hardware: tunnels, fans, an exhaust-air heat exchanger, a buffer tank and the controls. Every number comes from [`industrial.py`](../../model/compost_energy/industrial.py), and the drawings CE-06 to CE-14 are generated from the same module. The composting process itself (recipe, phases, moisture, spray water) is in [Composting process](process.md).

The layout was chosen in a [configuration study](../explanation/configuration-study.md) that compared 2, 3 and 4 tunnels, moving batches between tunnels by loader, an automatic transfer train and the patent's stacked chambers. **Four tunnels, each running the whole cycle in place, came out best.**

Nothing at this scale has been built. These are design estimates for a pilot.

![Farm-scale unit, cutaway](../../hardware/drawings/png/farm-unit-cutaway.png)

## Design point

| | |
|---|---|
| Feedstock | 39.1 t/day (46 m³), manure, silage and straw |
| Tunnels | 4 × 5.0 × 4.0 × 12.5 m inner, 988 m³ in all |
| Cycle | 15 days per batch; a tunnel is emptied and refilled every 3.75 days |
| Walls | 200 mm precast concrete + 100 mm PIR, U = 0.21 W/m²K |
| Aeration | 7,030 m³/h on average through spigot floors; 4 blowers of 4.1 kW at 2.5 kPa, each sized for its own batch's peak |
| Heat recovery | 548 kW mean over the 5-month heating season, 630 kW peak |
| Exchanger | 249 m² plate-fin, sized for the peak; exhaust 60 → 35 °C, water 30 → 50 °C, 5 K pinch |
| Buffer | 85 m³ hot-water tank, so the heat user gets a flat 548 kW |
| Condensate | 0.69 m³/h, re-used to wet the beds through roof spray bars (3 per tunnel, 6 m³/h); surplus to the slurry store |
| Biofilter | 65 m² at 125 m³/m²·h (peak airflow) |
| Capex | about €0.68M (€0.51–0.91M) for tunnels, aeration, recovery, buffer, biofilter, controls. MODEL |

## Where the heat is

Compost exhaust leaves the bed saturated. Cooling saturated air from 60 to 35 °C releases 330 kJ per kg of dry air, and only 25 kJ of that is sensible heat. **92 % of the recovered heat is water vapour condensing on the coils.** The exchanger is therefore sized on moist-air enthalpy, and it needs a condensate drain and a wash bar.

Wall losses are 3.0 kW per tunnel, about 2 % of the duty. In the 200 kg prototype box most of the heat left through the walls. This is the same scale effect, now in numbers.

The exchanger area is scaled from one measured farm composter: 23.3 kW from 9.2 m² (Kojima et al. 2022, [reference data](../../data/reference/README.md)). A coil vendor would size the real unit.

## How a batch moves through the phases

The 2024 patent gives each composting phase its own chamber. At farm scale the phases become a control scheme: each tunnel passes through them in time, not in space ([CE-11](../../hardware/drawings/farm-operating-modes.svg)).

A wheel loader fills a tunnel through its door, and the batch stays there for all 15 days: about 4 days of mesophilic start, then about 11 thermophilic days (60 °C hot hold with the 72 h sanitisation inside it, then cooling to 45 °C). It then matures for 8 weeks in windrows, where the last third of the organic matter breaks down too slowly and too cool to be worth recovering. [Composting process](process.md) explains why the tunnel stage stops at 15 days, and how moisture is held. The phase changes by changing the air: recirculation while it heats up, the hot hold, then fresh air to cool it. The four tunnels start 3.75 days apart, so at any time one is heating up, two are hot and one is cooling. Every 3.75 days one tunnel is emptied into the maturation hall and refilled with 147 t (173 m³) of fresh feedstock. That fills the bed to 2.8 m, and it settles to 1.3 m by day 15.

Staggering four batches keeps the combined exhaust between 0.8 and 1.15 times its mean. Two or three tunnels swing more, and need a bigger exchanger and a much bigger buffer (263 m³ for three tunnels, 440 m³ for two). Moving batches between tunnels, by loader or by an automatic transfer train, costs more than it saves. The [configuration study](../explanation/configuration-study.md) has the numbers and the trade-offs.

## Control

The compost process has priority. Four loops run per tunnel ([CE-10](../../hardware/drawings/farm-control.svg)):

1. **Temperature:** the median core temperature sets blower speed and recirculation.
2. **Oxygen floor:** below 5 % O₂ the fresh-air damper opens and overrides loop 1.
3. **Sanitisation:** at least 55 °C for 3 days (US EPA PFRP for in-vessel systems). The timer restarts if any probe drops below.
4. **Heat recovery:** the pump holds the supply temperature into the buffer tank, and the by-pass opens when it can't. Heat demand never sets the airflow.

## What this changed in the energy model

Sizing the fans showed that the farm scenario had under-counted aeration: 8.1 kW on average, against the 3–5 kW first assumed. The farm auxiliaries are now 13.1 kW, and the net value is €157k a year before capital. The configuration study adds the capital side: about €0.68M, repaid over 10 years at 6 % with upkeep, leaves about €42k a year (MODEL; €2–70k across the cost range). Tests keep these numbers in step.

## Open questions

- **The heat curve of one batch.** The A-3/A-4 choice turns on it. A pilot should log one batch's exhaust heat hour by hour.
- **Winter throughput.** The scenario delivers 7 months of feedstock's heat in 5 months. With stockpiling, the tunnels would need to run faster in winter than the average sizing assumes.
- **Exhaust blending.** The cooling tunnel's exhaust is cooler. Routing it past the exchanger may beat mixing it in.
- **Bulk density.** The tunnels are sized at 0.85 t/m³; a straw-amended mix should be ≤ 0.65 t/m³, which would need 16 m tunnels ([Composting process](process.md)).
- **Loader assumptions.** The diesel, throughput and heat lost per hot move are typical values, not measurements. They are set in `Handling` in `industrial.py`.
