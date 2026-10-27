# Add measured data

Use this guide when you have a real logger run from a compost heat-recovery pile and want it in the repository. Measured runs are the thing this project needs most. Each one replaces a SIMULATED or MODEL number with a MEASURED one.

## What you need

- The SD-card file from the logger. The firmware writes a first line that starts `# MEASURED DATA`. If it is missing, the run is not from the logger and should not go in `data/measured/`.
- A short notes file: feedstock mix and mass, turning dates, watering, and anything unusual. The temperature curve cannot be read without it.

## Steps

1. Copy the SD-card file into `data/measured/`, named `raw_<run>.csv`, for example `raw_run_01.csv`.

2. Run the cleaning and analysis from the repository root:

   ```bash
   .venv/bin/python model/scripts/analyze_run.py data/measured/raw_run_01.csv
   ```

   The script writes `clean_<run>.csv` and `report_<run>.json` next to the raw file, and the figures `figures/meas_<run>_*.png`. The cleaning rules are in [`clean.py`](../../model/compost_energy/clean.py). They remove sensor error codes, stuck sensors, spikes and duplicate timestamps, and leave long gaps empty rather than filling them.

3. Write `data/measured/notes_<run>.md` with the feedstock, the turning dates, the watering, and anything that looks odd in the curve.

4. Check the figures against the raw data. If the cleaning removes a real feature (a step change or a turning dip, for example), the rule is too strict for that sensor. Say so in the notes and open an issue.

5. Commit the files. Keep the labels honest: the report and figures are **MEASURED**, and any number you compare with the model should say which model run it came from.

## What not to do

- Do not edit `clean_<run>.csv` by hand. If the cleaning is wrong, change the rules in `clean.py` and rerun the script.
- Do not put simulated or synthetic data in `data/measured/`. Those files live in `data/simulated/`.

Once a measured run is in the repository, the model can be compared with it. See the [Energy model](../explanation/energy-model.md) for what the comparison should show.
