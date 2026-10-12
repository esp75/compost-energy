"""Clean a logger CSV and plot what the compost did and how much heat came out.

Works the same on simulated runs (data/simulated/) and real ones (data/measured/).

    python model/scripts/analyze_run.py data/simulated/raw_run_01.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from compost_energy import plotting as P
from compost_energy.clean import TEMP_COLUMNS, clean, read_log, summarize
from compost_energy.simulate import SIMULATED_BANNER

ROOT = Path(__file__).resolve().parents[2]


def is_simulated(path: Path) -> bool:
    with open(path) as f:
        return "SIMULATED" in f.readline()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", type=Path)
    ap.add_argument("--figures", type=Path, default=ROOT / "figures")
    args = ap.parse_args()

    raw_path = args.raw.resolve()
    run = raw_path.stem.removeprefix("raw_")
    simulated = is_simulated(raw_path)
    prefix = ("sim_" if simulated else "meas_") + run
    tag = " (SIMULATED)" if simulated else ""
    args.figures.mkdir(parents=True, exist_ok=True)

    raw = read_log(raw_path)
    df, log = clean(raw)
    stats = summarize(df)

    truth_path = raw_path.with_name(f"truth_{run}.csv")
    if truth_path.exists():
        truth = pd.read_csv(truth_path, comment="#", parse_dates=["timestamp"])
        stats["extracted_kwh_true"] = float(truth["p_hx_w"].sum() / 1000)  # hourly means x 1 h

    clean_path = raw_path.with_name(f"clean_{run}.csv")
    with open(clean_path, "w") as f:
        if simulated:
            f.write(f"# {SIMULATED_BANNER}\n")
        f.write("# Cleaned by model/compost_energy/clean.py: 5-min means, gaps <=30 min interpolated.\n")
        df.to_csv(f, float_format="%.4g")
    report = {"cleaning": log, "summary": stats}
    raw_path.with_name(f"report_{run}.json").write_text(json.dumps(report, indent=2, default=float))
    print(json.dumps(report, indent=2, default=float))

    days = (df.index - df.index[0]).total_seconds() / 86400
    x = pd.Series(days, index=df.index)

    # 1. Temperatures and composting phases.
    fig, ax = plt.subplots(figsize=(10, 4.2))
    P.shade_phases(ax, df, x)
    ax.plot(days, df["t_core_c"], color=P.HOT, lw=1.4, label="Core")
    ax.plot(days, df["t_mid_c"], color=P.WARM, lw=1.0, label="Mid-depth")
    ax.plot(days, df["t_ambient_c"], color=P.MUTED, lw=0.8, label="Ambient")
    ax.axhline(55, color=P.HOT, lw=0.6, ls=":")
    ax.text(days[-1], 55.5, "55 C sanitisation", ha="right", va="bottom", fontsize=8, color=P.HOT)
    ax.set(xlabel="Day", ylabel="Temperature (C)", title=f"Compost temperatures and phases{tag}")
    handles, labels = ax.get_legend_handles_labels()
    handles += [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.5) for c in P.PHASE_COLORS.values()]
    labels += list(P.PHASE_COLORS)
    ax.legend(handles, labels, ncol=7, loc="upper center", bbox_to_anchor=(0.5, -0.15), fontsize=8)
    if simulated:
        P.simulated_stamp(fig)
    fig.savefig(args.figures / f"{prefix}_temperatures.png")
    plt.close(fig)

    # 2. Heat extracted by the water loop.
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    pumping_only = df["p_extracted_w"].where(df["flow_l_min"] > 0.05)
    a1.plot(days, pumping_only, color=P.COOL, lw=0.7)
    a1.set_ylim(bottom=0)
    a1.set(ylabel="Extracted power (W)",
           title=f"Heat recovered through the buried exchanger{tag}")
    a1.text(0.99, 0.95, f"mean while pumping: {stats['mean_power_while_pumping_w']:.0f} W\n"
            f"mean outlet rise: {stats['mean_outlet_rise_c']:.1f} C",
            transform=a1.transAxes, ha="right", va="top", fontsize=9, color=P.INK)
    cum = (df["p_extracted_w"].fillna(0) * 5 / 60).cumsum() / 1000
    a2.plot(days, cum, color=P.GREEN, lw=1.5)
    a2.set(xlabel="Day", ylabel="Cumulative (kWh)")
    a2.text(days[-1], cum.iloc[-1], f" {cum.iloc[-1]:.1f} kWh", va="center", fontsize=9, color=P.GREEN)
    if simulated:
        P.simulated_stamp(fig)
    fig.savefig(args.figures / f"{prefix}_extracted_heat.png")
    plt.close(fig)

    # 3. Raw vs clean: what the cleaning actually removed.
    raw_sorted = raw.sort_values("timestamp")
    rdays = (raw_sorted["timestamp"] - df.index[0]).dt.total_seconds() / 86400
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
    for ax, col, title in ((axes[0], "t_core_c", "Core probe"), (axes[1], "t_mid_c", "Mid-depth probe")):
        ax.scatter(rdays, raw_sorted[col], s=2, color=P.MUTED, alpha=0.5, label="raw", rasterized=True)
        ax.plot(days, df[col], color=P.HOT, lw=1.0, label="clean")
        ax.set_ylim(-5, 90)
        ax.set(ylabel="C", title=f"{title}: raw log vs cleaned{tag}")
        ax.legend(loc="upper right", markerscale=4)
    axes[0].annotate("DS18B20 85 C reset codes", xy=(0.02, 85), xytext=(0.12, 0.82), textcoords="axes fraction",
                     fontsize=8, color=P.MUTED)
    stuck = df["t_mid_c"].isna() & (x > 16.9) & (x < 18.6)
    if stuck.any():
        axes[1].axvspan(x[stuck].iloc[0], x[stuck].iloc[-1], color=P.HOT, alpha=0.1, lw=0)
        axes[1].text(x[stuck].iloc[0], 80, " stuck sensor removed", fontsize=8, color=P.HOT, va="top")
    axes[1].set_xlabel("Day  (-127 C disconnect codes fall below the axis)")
    if simulated:
        P.simulated_stamp(fig)
    fig.savefig(args.figures / f"{prefix}_raw_vs_clean.png")
    plt.close(fig)

    # 4. Where the microbial heat went (simulation only: needs the model's ledger).
    ledger_path = raw_path.with_name(f"ledger_{run}.json")
    if simulated and ledger_path.exists():
        e = json.loads(ledger_path.read_text())["energy_kwh"]
        parts = [("Through walls", e["walls"], P.MUTED), ("Ventilation + evaporation", e["vent"], P.WARM),
                 ("Lost when turning", e["turning"], "#a8a29e"), ("Recovered by exchanger", e["hx"], P.COOL)]
        fig, ax = plt.subplots(figsize=(10, 2.8))
        left = 0.0
        total = e["bio"]
        for name, v, c in parts:
            ax.barh(0, v, left=left, color=c, height=0.5)
            label = f"{name}\n{v:.0f} kWh ({v / total:.0%})"
            if v / total > 0.15:
                ax.text(left + v / 2, 0, label, ha="center", va="center",
                        fontsize=8, color="white" if c != P.WARM else P.INK)
            elif name.startswith("Recovered"):
                ax.annotate(label, xy=(left + v / 2, 0.25), xytext=(left + v / 2 - total * 0.02, 0.55),
                            ha="right", va="center", fontsize=8, color=c,
                            arrowprops=dict(arrowstyle="->", color=c, lw=0.8))
            left += v
        ax.set(xlim=(0, total * 1.01), ylim=(-0.4, 0.8), yticks=[], xlabel="kWh over the run  (grey sliver: heat lost when turning)",
               title=f"Where {total:.0f} kWh of microbial heat went{tag}")
        ax.grid(axis="y", visible=False)
        P.simulated_stamp(fig)
        fig.savefig(args.figures / f"{prefix}_heat_ledger.png")
        plt.close(fig)

    print(f"\nwrote {clean_path.relative_to(ROOT)} and figures/{prefix}_*.png")


if __name__ == "__main__":
    main()
