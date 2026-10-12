import math

import numpy as np
import pytest

from compost_energy.clean import DS18B20_ERROR_CODES, TEMP_COLUMNS, clean, summarize
from compost_energy.energy_balance import (
    BUILDING_REALISTIC, FARM, HOUSE_IDEAL, HOUSE_REALISTIC, evaluate, farm_sizing,
)
from compost_energy.heat_exchanger import ORIGINAL_2024, PipeExchanger
from compost_energy.simulate import RunConfig, ctmi, simulate_truth, to_sensor_log


# ---- energy balance -------------------------------------------------------

def test_house_ideal_is_about_59_watts():
    r = evaluate(HOUSE_IDEAL)
    assert r.heat_kwh == pytest.approx(520)
    assert r.mean_power_w == pytest.approx(59.4, abs=0.5)
    assert r.net_eur == pytest.approx(69.3, abs=0.5)


def test_house_realistic_loses_money():
    assert evaluate(HOUSE_REALISTIC).net_eur < 0


def test_building_is_marginal():
    assert 0 < evaluate(BUILDING_REALISTIC).net_eur < 300


def test_farm_recovers_about_2_gwh():
    r = evaluate(FARM)
    assert r.heat_kwh / 1e6 == pytest.approx(2.0, abs=0.01)
    assert r.fuel_saved_eur == pytest.approx(266_541, rel=1e-3)
    assert r.net_eur > 100_000


def test_farm_sizing_maturation_volume():
    s = farm_sizing()
    assert s["feedstock_t_per_day"] == pytest.approx(39.12, abs=0.01)
    assert s["maturation_m3"] == pytest.approx(1194, abs=1)


# ---- heat exchanger -------------------------------------------------------

def test_original_2024_design_point_reproduced():
    # The 2024 spreadsheet used pi = 3.14, hence the loose tolerance.
    assert ORIGINAL_2024.area_m2 == pytest.approx(0.17898, rel=1e-3)
    assert ORIGINAL_2024.u_value == pytest.approx(992.9, abs=0.1)
    assert ORIGINAL_2024.power_w(60, 40) == pytest.approx(3554, rel=2e-3)


def test_realistic_exchanger_is_tens_of_watts():
    assert 15 < PipeExchanger(h_compost=5).power_w(60, 40) < 25
    assert 90 < PipeExchanger(h_compost=30).power_w(60, 40) < 120


def test_ntu_outlet_bounded_by_core():
    hx = PipeExchanger()
    t_out = hx.outlet_temperature(60, 15, 0.35)
    assert 15 < t_out < 60


# ---- simulation -----------------------------------------------------------

@pytest.fixture(scope="module")
def sim():
    cfg = RunConfig()
    truth, ledger = simulate_truth(cfg=cfg)
    raw = to_sensor_log(truth, cfg)
    return cfg, truth, ledger, raw


def test_ctmi_shape():
    assert ctmi(58, 25, 58, 71) == pytest.approx(1.0)
    assert ctmi(20, 25, 58, 71) == 0.0
    assert ctmi(75, 25, 58, 71) == 0.0


def test_energy_is_conserved(sim):
    _, _, led, _ = sim
    out = led["walls_j"] + led["vent_j"] + led["hx_j"] + led["turning_j"] + led["stored_j"]
    assert abs(led["bio_j"] - out) / led["bio_j"] < 0.01


def test_run_goes_thermophilic_then_matures(sim):
    _, truth, _, _ = sim
    assert 55 <= truth["t_core_c"].max() <= 68
    assert truth["t_core_c"].iloc[-200:].mean() < 20


def test_heat_yield_within_literature_range(sim):
    _, _, led, _ = sim
    kwh_per_kg = led["bio_j"] / 3.6e6 / 200
    assert 0.3 <= kwh_per_kg <= 1.4


def test_simulation_is_reproducible():
    a, _ = simulate_truth(cfg=RunConfig(days=3))
    b, _ = simulate_truth(cfg=RunConfig(days=3))
    assert np.allclose(a["t_core_c"], b["t_core_c"])


# ---- cleaning -------------------------------------------------------------

@pytest.fixture(scope="module")
def cleaned(sim):
    _, _, _, raw = sim
    import pandas as pd
    raw = raw.copy()
    raw["timestamp"] = pd.to_datetime(raw["timestamp"])
    df, log = clean(raw)
    return raw, df, log


def test_raw_log_contains_injected_faults(cleaned):
    raw, _, _ = cleaned
    assert raw["timestamp"].duplicated().any()
    assert raw["t_core_c"].isin(DS18B20_ERROR_CODES).any()
    assert not raw["timestamp"].is_monotonic_increasing


def test_cleaning_removes_faults(cleaned):
    _, df, log = cleaned
    assert df.index.is_monotonic_increasing and not df.index.duplicated().any()
    for col in TEMP_COLUMNS:
        assert not df[col].isin(DS18B20_ERROR_CODES).any()
        assert df[col].dropna().between(-30, 80).all()
    assert log["duplicates_removed"] > 0
    assert log["stuck_t_mid_c"] >= 1000
    assert log["flow_spikes"] >= 12


def test_long_gap_left_empty(cleaned):
    _, df, _ = cleaned
    # The 6 h logger outage on day 20.5 must not be interpolated.
    start = df.index[0] + np.timedelta64(int(20.55 * 86400), "s")
    assert math.isnan(df["t_core_c"].asof(start)) or df.loc[start:start, "t_core_c"].isna().all()


def test_turning_event_survives_cleaning(cleaned):
    _, df, _ = cleaned
    t0 = df.index[0]
    before = df["t_core_c"][t0 + np.timedelta64(int(9.40 * 86400), "s"):t0 + np.timedelta64(int(9.49 * 86400), "s")].mean()
    after = df["t_core_c"][t0 + np.timedelta64(int(9.52 * 86400), "s"):t0 + np.timedelta64(int(9.56 * 86400), "s")].mean()
    assert before - after > 4


def test_measured_energy_matches_truth(sim, cleaned):
    _, _, led, _ = sim
    _, df, _ = cleaned
    stats = summarize(df)
    true_kwh = led["hx_j"] / 3.6e6
    assert stats["extracted_kwh_estimated"] == pytest.approx(true_kwh, rel=0.05)


# ---- third-party reference data ------------------------------------------

def test_collins_bins_load_and_fault_is_removed():
    from compost_energy.reference import load_collins_controls
    bins = load_collins_controls()
    assert len(bins) == 3
    for df in bins.values():
        assert 70 < df["mean_c"].max() < 80
        assert df[["probe_1", "probe_2", "probe_3", "probe_4"]].max().max() <= 80
    # The 537 C open-circuit run on bin 2, probe 4.
    assert bins["bin 2 (rep 3)"].attrs["removed_readings"]["probe_4"] > 150


def test_kojima_heat_balance():
    from compost_energy.reference import kojima_heat_balance, load_kojima_daily_exchanger
    hb = kojima_heat_balance()
    assert hb["microbial_heat_kw"] == pytest.approx(61.8)
    assert hb["water_heat_gain_kw"] / hb["microbial_heat_kw"] == pytest.approx(0.377, abs=0.002)
    assert load_kojima_daily_exchanger()["extracted_from_gas_kw"].mean() == pytest.approx(22.6, abs=0.1)
