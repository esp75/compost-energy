"""Compare this repo's simulation with published MEASURED data (third-party, CC-BY-4.0).

    python model/scripts/compare_reference.py

Needs data/simulated/clean_run_01.csv and ledger_run_01.json
(run simulate_run.py and analyze_run.py first).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from compost_energy import plotting as P
from compost_energy.reference import (
    kojima_heat_balance, load_collins_controls, load_kojima_daily_exchanger, load_kojima_day,
)

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "figures"
SIM = ROOT / "data" / "simulated"

COLLINS_CREDIT = "Measured: Collins & Stacey (2021), Zenodo 10.5281/zenodo.4763775, CC-BY-4.0"
KOJIMA_CREDIT = ("Measured: Kojima, Nakakubo & Ishida (2022), Anim. Sci. J. 93:e13703; "
                 "data: Mendeley 10.17632/w79fv5pct7.1, CC-BY-4.0")


def credit(fig, text):
    fig.text(0.005, 0.005, text, ha="left", va="bottom", fontsize=7, color=P.MUTED)


def days_above(series: pd.Series, threshold: float, step_days: float) -> float:
    return float((series >= threshold).sum() * step_days)


def main() -> None:
    FIG.mkdir(exist_ok=True)
    sim = pd.read_csv(SIM / "clean_run_01.csv", comment="#", parse_dates=["timestamp"]).set_index("timestamp")
    sim_day = (sim.index - sim.index[0]).total_seconds() / 86400
    ledger = json.loads((SIM / "ledger_run_01.json").read_text())["energy_kwh"]
    report = {}

    # ---- 1. Bin-scale temperature curves --------------------------------
    bins = load_collins_controls()
    fig, ax = plt.subplots(figsize=(10, 4.4))
    shades = ["#7c3aed", "#a78bfa", "#c4b5fd"]
    for (name, df), c in zip(bins.items(), shades):
        hourly = df["mean_c"].resample("1h").median()
        d = (hourly.index - df.index[0]).total_seconds() / 86400
        ax.plot(d, hourly, color=c, lw=1.2, label=f"Measured {name}, mean of 4 probes")
        report[name] = {
            "peak_c": round(float(hourly.max()), 1),
            "days_above_55c": round(days_above(hourly, 55, 1 / 24), 1),
            "removed_readings": df.attrs["removed_readings"],
        }
    ax.plot(sim_day, sim["t_core_c"], color=P.HOT, lw=1.6, ls="--", label="This repo's simulation (SIMULATED)")
    ax.axhline(55, color=P.HOT, lw=0.6, ls=":")
    ax.set(xlabel="Day", ylabel="Temperature (C)", xlim=(0, 45),
           title="Measured bin composting vs this repo's simulation")
    ax.legend(loc="upper right", fontsize=8)
    ax.text(0.99, 0.62,
            "Measured: ~320-390 kg wood shavings + chicken manure (4:1),\nbins with an aeration plenum, May-June\n"
            "Simulated: 200 kg food/green waste, passive vents, autumn",
            transform=ax.transAxes, ha="right", va="top", fontsize=8, color=P.MUTED)
    credit(fig, COLLINS_CREDIT)
    fig.savefig(FIG / "reference_bins_vs_simulation.png")
    plt.close(fig)
    report["simulation"] = {
        "peak_c": round(float(sim["t_core_c"].max()), 1),
        "days_above_55c": round(days_above(sim["t_core_c"], 55, 5 / 1440), 1),
    }

    # ---- 2. Farm-scale heat recovery ------------------------------------
    day = load_kojima_day()
    daily = load_kojima_daily_exchanger()
    hb = kojima_heat_balance()
    farm_frac = hb["water_heat_gain_kw"] / hb["microbial_heat_kw"]
    box_frac = ledger["hx"] / ledger["bio"]
    report["kojima"] = {**hb, "fraction_of_microbial_heat_to_water": round(farm_frac, 3),
                        "daily_extracted_from_gas_kw_mean": round(float(daily["extracted_from_gas_kw"].mean()), 1)}
    report["simulation"]["fraction_of_microbial_heat_recovered"] = round(box_frac, 3)

    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(13, 4.2), gridspec_kw={"width_ratios": [1.3, 1.3, 1]})
    hours = (day.index - day.index[0]).total_seconds() / 3600
    a1.plot(hours, day["exhaust_c"], color=P.HOT, label="Compost exhaust air")
    a1.plot(hours, day["warmed_water_c"], color=P.COOL, label="Warmed water")
    a1.plot(hours, day["ambient_c"], color=P.MUTED, label="Outside air")
    a1.set(xlabel="Hour, 17 Mar 2017", ylabel="C", title="One winter day, 30-min data", ylim=(-2, 88))
    a1.legend(fontsize=8, loc="upper center", ncol=3, columnspacing=0.8, handlelength=1.2)

    dd = daily.index.day
    a2.bar(dd, daily["exhaust_out_kw"], color="#fdba74", label="still in gas after exchanger")
    a2.bar(dd, daily["extracted_from_gas_kw"], bottom=daily["exhaust_out_kw"], color=P.COOL,
           label="taken out by exchanger")
    a2.set(xlabel="Day of March 2017", ylabel="kW (daily mean)", title="Exhaust heat at the exchanger", ylim=(0, 68))
    a2.legend(fontsize=8, loc="upper center", ncol=2, columnspacing=0.8, handlelength=1.2)

    labels = ["200 kg box\n(SIMULATED)", "Farm composter\n(MEASURED)"]
    vals = [box_frac * 100, farm_frac * 100]
    a3.bar(labels, vals, color=[P.WARM, P.GREEN], width=0.55)
    for i, v in enumerate(vals):
        a3.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=11, fontweight="bold")
    a3.set(ylabel="% of microbial heat delivered to water", ylim=(0, 50),
           title="Scale is what makes it work")
    a3.grid(axis="x", visible=False)
    fig.suptitle("Measured compost heat recovery on a 150-cow dairy farm (Japan)",
                 x=0.01, ha="left", fontweight="bold", fontsize=12)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    credit(fig, KOJIMA_CREDIT)
    fig.savefig(FIG / "reference_farm_heat_recovery.png")
    plt.close(fig)

    (ROOT / "data" / "reference" / "comparison.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
