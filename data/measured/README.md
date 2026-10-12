# Measured runs

Real logger files go here. Nothing has been measured yet: everything in `data/simulated/` is synthetic.

1. Copy the SD-card file in, named `raw_<run>.csv` (e.g. `raw_run_01.csv`). The first line written by the firmware is `# MEASURED DATA ...`.
2. Run `python model/scripts/analyze_run.py data/measured/raw_run_01.csv`
3. The script writes `clean_<run>.csv` and `report_<run>.json` here, and `figures/meas_<run>_*.png`.

Please also add a short `notes_<run>.md`: feedstock mix and mass, turning dates, watering, anything unusual. The temperature curve can't be interpreted without it.
