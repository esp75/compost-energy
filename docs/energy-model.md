# Energy model: does compost heat pay?

Code: [`model/compost_energy/energy_balance.py`](../model/compost_energy/energy_balance.py) · run `python model/scripts/run_scenarios.py`

## Method

For each scale:

```
heat recovered (kWh/yr)   = waste (kg/yr) x usable fraction x recoverable heat (kWh/kg)
fuel displaced (kWh/yr)   = heat recovered / efficiency of the boiler it replaces
net saving (EUR/yr)       = fuel displaced x fuel price - auxiliary electricity x power price - fixed opex
```

"Auxiliaries" are everything the system needs to run: fans, the circulation pump, controls and, at scale, conveyors. The model counts them because they are what turns small systems net-negative.

## Assumptions

| Input | Value | Note |
|---|---|---|
| Household food waste | 130 kg/person/yr | French average |
| Recoverable heat, food/green waste | 1.0 (ideal) / 0.7 (realistic) kWh/kg | published recovery studies span ~0.3-1.4 |
| Recoverable heat, manure-rich farm feedstock | 0.24 kWh/kg | manure/slurry sit at the low end (0.13-0.24) |
| Gas price | €0.12/kWh | France, Jan 2025 |
| Electricity price | €0.20/kWh | France, Jan 2025 |
| Boiler efficiency | 0.90 (house, farm) / 0.95 (block) | |
| Auxiliaries | 0 / 50 W (house), 0 / 200 W (block), 13 kW for 5 months (farm): 5 kW conveying + 8 kW fans | fans sized in [farm-unit.md](farm-unit.md) |

## Results

![Net value by scale](../figures/scenarios_net_value.png)

| Scenario | Heat (kWh/yr) | Mean power | Net (€/yr) |
|---|---:|---:|---:|
| House, 4 people (ideal) | 520 | 59 W | +69 |
| House, 4 people (realistic) | 364 | 42 W | **−39** |
| Apartment block, 48 people (ideal) | 6,240 | 712 W | +788 |
| Apartment block, 48 people (realistic) | 4,368 | 499 W | +201 |
| Farm cooperative, 14,279 t/yr | 2,000,000 | 228 kW (year mean; 548 kW over the heating season) | **+157,000** |

## Reading the numbers

- **A house produces about 59 W on average**, less than one person at rest (~100 W). Spending 50 W on a fan and controls already makes it net-negative, before the hardware is paid for. Against a heat pump (COP 3) it's worse still, because the heat it displaces was cheap to begin with.
- **An apartment block saves ~€200/yr.** To pay back in 10 years the unit would have to sell for ~€2,000 and cost ~€1,000 to build. A box sized for 6 t/yr of waste can't be built for that.
- **A farm is a different regime.** About 14,000 t/yr of manure, silage and straw yields ~2 GWh of heat over a 5-month heating season. That's roughly €266k/yr of gas, or ~€157k/yr net after electricity and €100k of operating costs, which can repay ~€1.6M of capex over 10 years.

The farm case still has open questions:

- **Who uses the heat?** Farms are in low-density areas, so the heat needs a nearby user (greenhouse, grain or wood drying, a small district loop).
- **CO2:** composting releases the carbon as CO2, with no biogas to sell.
- **Materials handling:** moving 40 t/day of heterogeneous solids through enclosed reactors is a real engineering problem. The largest automated composters today are container-sized; this is hangar-scale.

## Farm sizing (first pass)

From `farm_sizing()`, with 0.85 t/m³ feedstock, 15 days in the reactors losing 5% of volume per day, 8 weeks of maturation and 7 months of storage:

| Quantity | Value |
|---|---:|
| Feedstock | 39 t/day ≈ 46 m³/day |
| Material inside reactors A+B+C | ~490 m³ (≈ 990 m³ of vessel with 50% headspace for mixing) |
| Pre-compost leaving the reactors | 21 m³/day |
| Maturation windrows | ~1,200 m³ → ~1,200 m² at ≤ 1 m depth |
| Finished-compost storage | ~4,500 m³ |

Plant layout: unloading → optional shredding → screw-conveyed reactors A (mesophilic, seeded) → B (adiabatic, thermophilic, air-to-water heat exchanger; the heat also sanitises the compost) → C (mesophilic) → maturation hall → outdoor storage.
