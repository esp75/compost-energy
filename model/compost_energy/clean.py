"""Cleaning and analysis of compost-logger CSVs (simulated or measured).

Pipeline: parse -> dedupe/sort -> drop sensor error codes and out-of-range
values -> remove isolated spikes (Hampel) -> blank stuck sensors -> resample
to a regular grid -> fill only short gaps -> heat extracted by the water loop.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CP_WATER = 4186.0
TEMP_COLUMNS = ["t_core_c", "t_mid_c", "t_ambient_c", "t_water_in_c", "t_water_out_c"]
DS18B20_ERROR_CODES = (-127.0, 85.0)
VALID_RANGE_C = (-30.0, 80.0)
RESAMPLE = "5min"
MAX_FILL_BINS = 6  # interpolate gaps up to 30 min; leave longer gaps empty
PUMP_ON_L_MIN = 0.05


def read_log(path) -> pd.DataFrame:
    df = pd.read_csv(path, comment="#")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def _hampel(s: pd.Series, window: int = 15, n_sigmas: float = 4.0, min_dev: float = 1.0) -> pd.Series:
    """Mask points far from the rolling median (robust to real step changes)."""
    med = s.rolling(window, center=True, min_periods=window // 2).median()
    mad = (s - med).abs().rolling(window, center=True, min_periods=window // 2).median()
    dev = (s - med).abs()
    return dev > np.maximum(n_sigmas * 1.4826 * mad, min_dev)


def _stuck(s: pd.Series, min_run: int = 30) -> pd.Series:
    """True where a sensor repeats the exact same value for >= min_run samples.

    Only valid for sensors whose noise exceeds their resolution (DS18B20 at
    12 bit). Coarsely quantised loggers repeat values when healthy; see
    reference.py.
    """
    same = s.diff().eq(0)
    run_id = (~same).cumsum()
    run_len = s.groupby(run_id).transform("size")
    return run_len >= min_run


def _fill_short_gaps(s: pd.Series, max_bins: int) -> pd.Series:
    isna = s.isna()
    run_id = (~isna).cumsum()
    gap_len = isna.groupby(run_id).transform("sum")
    filled = s.interpolate(limit_area="inside")
    return filled.where(~isna | (gap_len <= max_bins))


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    log: dict = {"rows_in": len(raw)}
    df = raw.copy()

    df = df.sort_values("timestamp", kind="stable")
    before = len(df)
    # Duplicate writes carry the same timestamp (to the second) and values.
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="timestamp", keep="first")
    log["duplicates_removed"] = before - len(df)
    df = df.set_index("timestamp")

    for col in TEMP_COLUMNS:
        bad = df[col].isin(DS18B20_ERROR_CODES) | ~df[col].between(*VALID_RANGE_C)
        log[f"error_codes_{col}"] = int(bad.sum())
        df.loc[bad, col] = np.nan

    for col in TEMP_COLUMNS:
        spikes = _hampel(df[col])
        log[f"spikes_{col}"] = int(spikes.sum())
        df.loc[spikes, col] = np.nan

    for col in TEMP_COLUMNS:
        stuck = _stuck(df[col])
        log[f"stuck_{col}"] = int(stuck.sum())
        df.loc[stuck, col] = np.nan

    flow = df["flow_l_min"]
    flow_med = flow.rolling(15, center=True, min_periods=5).median()
    flow_bad = (flow < 0) | (flow > 5) | ((flow_med > PUMP_ON_L_MIN) & (flow > 3 * flow_med))
    log["flow_spikes"] = int(flow_bad.sum())
    df.loc[flow_bad, "flow_l_min"] = np.nan

    df = df.resample(RESAMPLE).mean()
    log["bins"] = len(df)
    log["empty_bins_before_fill"] = int(df["t_core_c"].isna().sum())
    for col in df.columns:
        df[col] = _fill_short_gaps(df[col], MAX_FILL_BINS)
    log["empty_bins_after_fill"] = int(df["t_core_c"].isna().sum())

    # A bin is "pumping" only if the pump ran for the whole bin; partial bins at
    # pump start/stop mix stagnant-water readings with flow and are dropped.
    pumping = df["flow_l_min"] > PUMP_ON_L_MIN
    full = pumping & pumping.shift(1, fill_value=False) & pumping.shift(-1, fill_value=False)
    dT = df["t_water_out_c"] - df["t_water_in_c"]
    df["p_extracted_w"] = np.where(full, df["flow_l_min"] / 60.0 * CP_WATER * dT, np.where(pumping, np.nan, 0.0))
    df["phase"] = classify_phases(df)
    return df, log


def classify_phases(df: pd.DataFrame, thermo_c: float = 45.0, mature_margin_c: float = 8.0) -> pd.Series:
    core = df["t_core_c"].rolling(12, min_periods=1, center=True).median()  # 1 h smoothing
    hot = core >= thermo_c
    phase = pd.Series("mesophilic", index=df.index)
    if hot.any():
        first, last = hot.idxmax(), hot[::-1].idxmax()
        phase[(df.index >= first) & (df.index <= last)] = "thermophilic"
        after = df.index > last
        amb = df["t_ambient_c"].rolling(288, min_periods=1).mean()
        # Hysteresis: once the core first settles near ambient, the pile is maturing.
        settled = after & ((core - amb) <= mature_margin_c)
        phase[after] = "cooling"
        if settled.any():
            phase[df.index >= settled.idxmax()] = "maturation"
    return phase


def summarize(df: pd.DataFrame) -> dict:
    bin_h = pd.Timedelta(RESAMPLE).total_seconds() / 3600
    p = df["p_extracted_w"]
    pumping = df["flow_l_min"] > PUMP_ON_L_MIN
    valid_pumping = pumping & p.notna()
    energy_kwh = (p.fillna(0) * bin_h).sum() / 1000
    # Scale for pump-on bins we could not measure (gaps, start/stop transients).
    coverage = valid_pumping.sum() / max(pumping.sum(), 1)
    out = {
        "duration_days": (df.index[-1] - df.index[0]).total_seconds() / 86400,
        "peak_core_c": float(df["t_core_c"].max()),
        "days_above_45c": float((df["t_core_c"] >= 45).sum() * bin_h / 24),
        "days_above_55c": float((df["t_core_c"] >= 55).sum() * bin_h / 24),
        "mean_power_while_pumping_w": float(p[valid_pumping].mean()),
        "peak_power_w": float(p.max()),
        "extracted_kwh_measured": float(energy_kwh),
        "pump_bin_coverage": float(coverage),
        "extracted_kwh_estimated": float(energy_kwh / coverage) if coverage else float("nan"),
        "mean_outlet_rise_c": float((df["t_water_out_c"] - df["t_water_in_c"])[valid_pumping].mean()),
    }
    out["phase_days"] = (df["phase"].value_counts() * bin_h / 24).round(2).to_dict()
    return out
