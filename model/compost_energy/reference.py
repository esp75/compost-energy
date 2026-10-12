"""Loaders for third-party MEASURED datasets in data/reference/.

These are other researchers' measurements, used under CC-BY-4.0 to check the
model in this repo against reality. See data/reference/README.md for full
citations. None of this data was collected by Compost Energy.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .clean import VALID_RANGE_C, _hampel

REF = Path(__file__).resolve().parents[2] / "data" / "reference"

COLLINS_CONTROL_BINS = {
    "bin 5 (rep 1)": "9941281 bin5 0bioch rep1 24jun19.csv",
    "bin 9 (rep 2)": "10101120 bin9 0bioch rep2 24jun19.csv",
    "bin 2 (rep 3)": "10095092 bin2 0bioch rep3 24jun19.csv",
}
KOJIMA_FILE = "Applied energy data_Kojima(NARO)210106.xlsx"


def f_to_c(f):
    return (f - 32.0) / 1.8


def load_collins_bin(filename: str) -> pd.DataFrame:
    """HOBO logger export: 15-min readings from 4 probes, in deg F.

    Returns a frame indexed by timestamp with probe_1..probe_4 in deg C,
    their mean, and days since the logger started.
    """
    raw = pd.read_csv(REF / "collins2021" / filename, skiprows=1, encoding="utf-8-sig")
    df = raw.iloc[:, 1:6].copy()
    df.columns = ["timestamp", "probe_1", "probe_2", "probe_3", "probe_4"]
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%m/%d/%y %I:%M:%S %p")
    probes = ["probe_1", "probe_2", "probe_3", "probe_4"]
    df[probes] = f_to_c(df[probes].astype(float))
    df = df.dropna(subset=probes, how="all").set_index("timestamp")
    # Range and spike rules from clean.py. Bin 2's probe 4 reads a fixed
    # 537 C (1000 F, open circuit) for its first ~2 days; the range rule
    # catches it. clean.py's exact-repeat "stuck sensor" rule is NOT used:
    # these loggers quantise coarsely, so ~50% of consecutive readings repeat
    # even when the probe is fine. That rule only suits noisy sensors like
    # the DS18B20.
    removed = {}
    for c in probes:
        bad = (~df[c].between(*VALID_RANGE_C) & df[c].notna()) | _hampel(df[c], window=15, min_dev=3.0)
        removed[c] = int(bad.sum())
        df.loc[bad, c] = float("nan")
    df.attrs["removed_readings"] = removed
    df["mean_c"] = df[probes].mean(axis=1)
    df["day"] = (df.index - df.index[0]).total_seconds() / 86400
    return df


def load_collins_controls() -> dict[str, pd.DataFrame]:
    return {name: load_collins_bin(f) for name, f in COLLINS_CONTROL_BINS.items()}


def _sheet_rows(sheet: str) -> list[tuple]:
    import openpyxl

    wb = openpyxl.load_workbook(REF / "kojima2022" / KOJIMA_FILE, data_only=True, read_only=True)
    return list(wb[sheet].iter_rows(values_only=True))


def load_kojima_day() -> pd.DataFrame:
    """30-min record of 17 March 2017 (paper Fig. 3): temperatures in deg C,
    water supply rate as published."""
    rows = _sheet_rows("Fig3")
    head = next(i for i, r in enumerate(rows) if "Date/Time" in r)
    c0 = rows[head].index("Date/Time")
    data = [r[c0:c0 + 5] for r in rows[head + 1:] if r[c0] is not None]
    df = pd.DataFrame(data, columns=["timestamp", "exhaust_c", "warmed_water_c", "ambient_c", "water_supply_rate"])
    return df.set_index("timestamp")


def load_kojima_daily_exchanger() -> pd.DataFrame:
    """Daily heat carried by the exhaust gas into and out of the heat
    exchanger, March 2017 (paper Table 5 workings), in kW."""
    rows = _sheet_rows("Tab5")
    out = []
    for r in rows:
        if hasattr(r[7], "year") and isinstance(r[9], (int, float)):
            out.append((r[7], r[9], r[11]))
    df = pd.DataFrame(out, columns=["date", "exhaust_in_kw", "exhaust_out_kw"]).set_index("date")
    df["extracted_from_gas_kw"] = df["exhaust_in_kw"] - df["exhaust_out_kw"]
    return df


def kojima_heat_balance() -> dict:
    """Average daily heat balance of the facility (paper Table 5), in kW."""
    rows = _sheet_rows("Tab5")
    table = {}
    label = None
    for r in rows:
        name = " ".join(str(x) for x in r[0:2] if x)
        if name:
            label = name
        if isinstance(r[5], (int, float)) and label:
            table[label] = float(r[5])
    return {
        "electricity_kw": table["EVCF operation*"],
        "microbial_heat_kw": table["heat generation by OMD"],
        "exhaust_at_exchanger_kw": table["Exhaust HE IN"],
        "water_heat_gain_kw": table["Water got by heat"],
    }
