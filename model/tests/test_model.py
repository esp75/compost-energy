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


# ---- farm-scale unit ------------------------------------------------------

from compost_energy.industrial import enthalpy_kj_per_kg, humidity_ratio, size  # noqa: E402


def test_psychrometrics_match_tables():
    # ASHRAE: saturated air at 60 °C holds 0.1521 kg/kg; at 35 °C, 0.03666 kg/kg
    assert humidity_ratio(60) == pytest.approx(0.1521, rel=0.01)
    assert humidity_ratio(35) == pytest.approx(0.03666, rel=0.01)
    assert enthalpy_kj_per_kg(35) == pytest.approx(129.2, rel=0.01)


def test_tunnels_hold_the_model_volume():
    m = size()
    assert m["n_tunnels"] == 4
    assert m["gross_total_m3"] == pytest.approx(farm_sizing()["reactor_volume_m3"], rel=1e-9)
    assert 11 < m["tunnel_length_m"] < 14


def test_heat_recovery_balances():
    m = size()
    # air side and water side carry the same duty
    air_kw = m["air_dry_kg_s"] * m["enthalpy_drop_kj_kg"]
    water_kw = m["water_kg_s"] * 4.186 * (m["t_supply_c"] - m["t_return_c"])
    assert air_kw == pytest.approx(m["duty_kw"], rel=1e-9)
    assert water_kw == pytest.approx(m["duty_kw"], rel=1e-9)
    # duty x heating hours gives back the farm scenario's 2 GWh
    assert m["duty_kw"] * 5 * 730 / 1e6 == pytest.approx(m["heat_gwh_per_year"], rel=1e-9)


def test_exhaust_heat_is_mostly_latent_and_walls_are_small():
    m = size()
    assert m["latent_share"] > 0.9
    assert m["wall_loss_share"] < 0.05


def test_counterflow_exchanger_is_feasible():
    assert size()["pinch_k"] > 3.0


def test_farm_auxiliaries_include_the_sized_fans():
    from compost_energy.energy_balance import FARM as farm
    assert farm.aux_power_w == pytest.approx(5000 + size()["fan_kw"] * 1000, abs=100)


def test_staggered_batches_fill_and_settle_inside_the_tunnel():
    from compost_energy.industrial import operating_modes
    ops = operating_modes()
    assert ops["fill_depth_m"] < size()["tunnel_height_m"] - 1.0      # headspace left at fill
    assert ops["settled_depth_m"] < ops["fill_depth_m"]
    # one batch is 15/N days of feedstock
    assert ops["batch_t"] == pytest.approx(15 / size()["n_tunnels"] * farm_sizing()["feedstock_t_per_day"])


def test_transfer_mode_multiplies_handling_and_costs_more():
    from compost_energy.industrial import IndustrialDesign, operating_modes
    for n, ratio in ((3, 2.0), (4, 2.5)):        # every extra tunnel adds one hot move per batch
        ops = operating_modes(IndustrialDesign(n_tunnels=n))
        a, b = ops["staggered"], ops["transfer"]
        assert b["t_per_day"] / a["t_per_day"] == pytest.approx(ratio, abs=0.1)
        assert b["net_eur"] < a["net_eur"]


# ---- configuration study ---------------------------------------------------

from compost_energy import configurations as C  # noqa: E402


def test_batch_profile_is_normalised_and_thermophilic():
    shape = C.batch_profile()
    assert shape.sum() == pytest.approx(1.0)
    n = len(shape)
    day = np.arange(n) * C.DT_H / 24
    # little heat leaves while the bed warms up; most leaves in the hot phase
    assert shape[day < 2].sum() < 0.05
    assert shape[(day >= 3) & (day < 10)].sum() > 0.5


def test_combined_profile_keeps_the_mean_and_smooths_with_more_batches():
    shape = C.batch_profile()
    peaks = [C.combined_profile(n, shape).max() for n in (2, 3, 4, 15)]
    assert all(C.combined_profile(n, shape).mean() == pytest.approx(1.0) for n in (2, 3, 4, 15))
    assert peaks == sorted(peaks, reverse=True)


def test_every_option_value_adds_up():
    for r in C.study():
        n = r.numbers
        assert n["value_eur"] == pytest.approx(n["operating_eur"] - n["annuity_eur"])
        assert n["capex"] == pytest.approx(n["capex_civil"] + n["capex_mech"] + n["capex_transfer"])


def test_final_design_wins_at_low_base_and_high_costs():
    for c in (C.LOW, C.Costs(), C.HIGH):
        assert C.final_choice(c) == C.FINAL == "A-4"


def test_design_constants_match_the_study():
    from compost_energy.industrial import IndustrialDesign
    n = C.evaluate_option(next(o for o in C.all_options() if o.code == C.FINAL)).numbers
    d = IndustrialDesign()
    assert d.peak_to_mean == pytest.approx(n["peak_to_mean"], abs=0.01)
    assert d.buffer_m3 == pytest.approx(n["buffer_m3"], abs=1.0)
    assert d.blower_peak_factor == pytest.approx(n["fan_kw_installed"] / n["fan_kw_mean"], abs=0.05)


def test_automatic_transfer_needs_an_implausible_remix_boost():
    assert C.break_even_boost("C-3-NW", C.FINAL) > 0.3


def test_a3_reproduces_the_previous_operating_mode_numbers():
    from compost_energy.industrial import IndustrialDesign, operating_modes
    ops = operating_modes(IndustrialDesign(n_tunnels=3))
    assert ops["staggered"]["t_per_day"] == pytest.approx(66.5, abs=0.1)
    assert ops["staggered"]["net_eur"] == pytest.approx(156_978, abs=1)
    assert ops["transfer"]["net_eur"] == pytest.approx(129_194, abs=1)


# ---- process: recipe, phases, water ------------------------------------------

from compost_energy import process as P  # noqa: E402


def test_recipe_sits_in_the_composting_window():
    m = P.mix()
    tg = P.Targets()
    assert tg.cn[0] <= m["cn"] <= tg.cn[1]
    assert tg.moisture_fill[0] <= m["moisture"] <= tg.moisture_fill[1] + 0.01


def test_batch_is_sanitised_inside_the_hot_hold():
    b = P.run_batch()
    ph = {p["phase"]: p for p in P.phases(b)}
    assert b["sanitised_day"] is not None
    assert ph["hot hold"]["start"] <= b["sanitised_day"] <= ph["hot hold"]["end"]
    assert ph["thermophilic"]["end"] - ph["thermophilic"]["start"] > 10


def test_phase_shares_cover_the_whole_batch():
    ph = {p["phase"]: p for p in P.phases(P.run_batch())}
    total = ph["mesophilic"]["share"] + ph["thermophilic"]["share"] + ph["maturation"]["share"]
    assert total == pytest.approx(1.0, abs=0.01)
    assert 0.2 < ph["maturation"]["share"] < 0.5          # day 15 is not the end of composting


def test_recovered_heat_matches_the_farm_scenario():
    from compost_energy.industrial import operating_modes
    b = P.run_batch()
    assert b["recovered_kwh"].sum() == pytest.approx(operating_modes()["batch_t"] * 1000 * FARM.kwh_per_kg, rel=1e-6)


def test_water_balance_closes_and_moisture_stays_in_band():
    b = P.run_batch()
    t = b["totals"]
    water0 = b["batch_kg"] * b["fill_moisture"] / 1000
    dry0 = b["batch_kg"] * (1 - b["fill_moisture"]) / 1000
    end = water0 - t["evaporated_t"] + t["metabolic_t"] + t["sprayed_t"]
    assert end / (end + dry0 - t["organic_matter_lost_t"]) == pytest.approx(t["end_moisture"], abs=1e-6)
    assert t["condensate_t"] < t["evaporated_t"]
    for row in P.sensitivity():
        assert row["min_moisture"] >= P.Targets().moisture_cool_min - 0.01
