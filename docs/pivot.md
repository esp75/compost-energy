# From home units to farm scale

## The original idea (2024)

A box for a house or a shared building: food scraps go in at the top, a water loop pre-heats the home's heating return, and mature compost (enriched fertiliser) comes out at the bottom about six weeks later. Heat and fertiliser from waste the household already produces. I wrote a provisional patent, designed and costed three prototypes, and sized the heat exchanger.

## Running the numbers

Working through the full energy balance at each scale ([energy-model.md](energy-model.md)) and re-checking the exchanger physics ([heat-exchanger.md](heat-exchanger.md)) gave three results that ended the home product:

1. **A household's waste is only ~59 W of heat** on average (520 kg/yr × ~1 kWh/kg ÷ 8760 h).
2. **The auxiliaries cost about as much as the heat is worth.** A 50 W fan/pump/controller turns the balance negative (−€39/yr). A 48-person building nets ~€200/yr, which can't pay back any box you could build.
3. **The exchanger was over-estimated ~70×.** It was sized at 3.5 kW with an unrealistic compost-side film coefficient; the realistic figure is ~50 W.

The value proposition for homes is year-round, controlled composting, not energy. That's a different product, and not this one.

## Why farm scale works

- **Volume beats surface area.** Microbial heat grows with volume, wall losses with surface area. Small boxes lose most of their heat; big reactors keep it.
- **Feedstock is free and huge.** A mid-size farm cooperative handles ~14,000 t/yr of manure, silage and straw.
- **Auxiliaries get diluted.** 10 kW of conveying and aeration against ~230 kW of recovered heat (winter average).
- **Measured elsewhere, too.** On an enclosed farm composter in Japan, 38% of the microbial heat reached the water, against ~9% in a simulated 200 kg box ([reference data](../data/reference/README.md)).
- **Result:** ~2 GWh/yr of heat, ~€159k/yr net, and enough to repay ~€1.6M of capex over 10 years. Mid-size anaerobic digesters cost ~€3.2M, so this sits in a different, cheaper class.

## What is still unproven

| Risk | How to retire it |
|---|---|
| Heat needs a nearby user | site next to a greenhouse, dryer or small heat network |
| CO2 is released, with no biogas revenue | compare carbon accounting against digestion and open windrows |
| Moving 40 t/day of heterogeneous solids through enclosed reactors | conveyor/screw trials at pilot scale |
| Real recovery rate in a big reactor | instrumented pilot, using the same logger and analysis pipeline as this repo |

Suggested path: a funded research project with an engineering lab (~€150-200k), then a pilot installation (~€200-500k).
