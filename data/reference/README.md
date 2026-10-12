# Reference data: third-party measurements

> **None of this data was collected by Compost Energy.** These are published, openly licensed measurements by other research groups, included unmodified so this repo's model can be checked against reality. Each is redistributed under its CC-BY-4.0 license with the attribution below.

## `collins2021/`: bin composting temperatures (bin scale)

- **Data:** Collins, D. & Stacey, N. (2021). *Biochar-poultry manure compost alters temperature and nitrogen dynamics during composting and improves crop growth following field application* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.4763775. License: CC-BY-4.0.
- **Included files (unmodified):** the three control bins (0% biochar): bins 5, 9 and 2. Also the bin-weights workbook.
- **What it is:** HOBO data-logger exports at 15-minute intervals from 4 probes per bin (°F), 21 May to 24 June 2019. The feedstock is wood shavings and chicken manure, 4:1. Each bin holds about 320-390 kg of material and has an aeration plenum.
- **Used for:** comparing the shape of the simulated temperature curve with real bins of similar mass.
- **Known features:** probe 4 of bin 2 reads a fixed 537 °C (1000 °F, an open-circuit value) for the first ~2 days. The range rule from `clean.py` removes it. The drop to 10-25 °C around day 13-14 matches the bins being re-weighed on 3-4 June (see the weights file).

## `kojima2022/`: farm-scale compost heat recovery

- **Data:** Kojima, Y., Nakakubo, R. & Ishida, M. (2021). *KOJIMAY2101_001* [Data set], v1. Mendeley Data. https://doi.org/10.17632/w79fv5pct7.1. License: CC-BY-4.0. The SHA-256 of the file, `3f7371f4…`, matches the hash Mendeley publishes.
- **Paper:** Kojima, Y., Nakakubo, R. & Ishida, M. (2022). Recovery and utilization of compost heat from an enclosed vertical-type composting facility: development of warmed water supply system using compost heat. *Animal Science Journal*, 93(1), e13703. https://doi.org/10.1111/asj.13703
- **What it is:** an enclosed vertical composting facility for dairy manure on a 150-cow farm in Japan. A stainless plate-fin exchanger (9.2 m²) in the exhaust air warms the cows' drinking water. The workbook holds the data behind the paper's figures and tables: compost and exhaust temperatures, 30-minute water and air records, daily exchanger heat flows (March 2017), and the facility heat balance.
- **Used for:** a measured farm-scale heat balance. Of 61.8 kW of microbial heat, **23.3 kW (38%) reached the water**, while the facility drew 13.3 kW of electricity for aeration and agitation.

## Other datasets found, not included

- Bondeson, F. A., Faulkner, J. W. & Roy, E. D. (2022). *Dataset: Performance of a compost aeration and heat recovery system at a commercial composting facility*. Zenodo. https://doi.org/10.5281/zenodo.6968159 (CC-BY-4.0). Paper: *Journal of Ecological Engineering Design* (2023), https://doi.org/10.21428/f69f093e.769abde7. It contains windrow temperatures (manual readings) and nutrient data for aerated windrows with heat recovery vs conventional ones, but no heat-flow measurements, so it isn't used here.

Code that reads these files: [`model/compost_energy/reference.py`](../../model/compost_energy/reference.py). Comparison: `python model/scripts/compare_reference.py` → `figures/reference_*.png` and `comparison.json`.
