# System design

![System schematic](../hardware/drawings/system-schematic.svg)

The "biological boiler" is a composting box that runs each composting phase in its own chamber, and harvests heat from the hottest one through a water loop.

## Process conditions

| Parameter | Working range | Target | How the design holds it |
|---|---|---|---|
| C/N ratio at start | 20-40 : 1 | 25-30 : 1 | feed mix of fresh green waste + dry garden residues, through the intake hatch |
| Moisture | 40-65 % | 50-60 % | solid plastic chamber floors; rainwater drip into chamber B |
| Oxygen | > 5 % | ~10 % | plastic-mesh inner chambers; natural low (VB) and high (VH) vents |
| Temperature | phase-dependent | 55-70 °C in B | closed timber box on stilts (the simulation shows a small box also needs insulation to go thermophilic); probes in B |

## Chambers

| Chamber | Phase | Temperature | Residence | Volume |
|---|---|---|---|---|
| A | mesophilic | 40-45 °C | ~1 week | full |
| B | thermophilic: **heat is extracted here** | 55-70 °C | 3-4 weeks | full |
| C | cooling | back to 40-45 °C | up to 3-4 weeks | half |
| D | maturation | ambient | weeks | half |

C and D are half size because the material loses 20-50% of its volume during the hot phase.

## Heat path

1. Microbes in B release heat (the model in this repo uses 18 MJ per kg of volatile solids degraded).
2. An aluminium coil buried in B's core carries water through the pile.
3. The coil sits in a block of concrete. The concrete is cheap, survives the heat, protects the coil in transport, and its thermal mass keeps delivering heat while B is emptied and restocked.
4. The water loop is plumbed as a by-pass on the return line of an existing wet heating system (60/40 or 70/50 °C). It pre-heats the return water, so the existing boiler burns less.

## Instrumentation

The patent specifies a temperature + humidity probe in each chamber (B is critical) with a front-panel display. The prototype logger in [`hardware/logger`](../hardware/logger) expands this to five temperatures, water flow and headspace humidity, enough to measure the heat actually extracted rather than estimate it.

## Prototypes

Three bench prototypes were specified and costed (~€640 in parts: [BOM](../hardware/bom/prototypes.csv)):

| # | What it tests |
|---|---|
| 1 | Box, moisture tray, drip irrigation and temperature/humidity probes: can a small box hold the right conditions? |
| 2 | Adds a raised frame, plastic-mesh aerobic chambers, access hatches and one 19 mm aluminium tube as the exchanger. |
| 3 | Same as 2 with double the exchanger length, to measure how output scales with surface area. |

The parts were selected to separate the variables: prototype 1 tests the process alone, 2 adds heat extraction, and 3 changes only the exchanger area.
