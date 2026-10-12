"""Print the energy balance for each scale and draw the comparison figures.

    python model/scripts/run_scenarios.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from compost_energy import plotting as P
from compost_energy.energy_balance import FARM, SCENARIOS, evaluate, farm_sizing, payback_capex
from compost_energy.heat_exchanger import ORIGINAL_2024, PipeExchanger, sensitivity

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "figures"


def main() -> None:
    FIG.mkdir(exist_ok=True)
    results = [evaluate(s) for s in SCENARIOS]

    print(f"{'Scenario':42s} {'heat kWh/yr':>12s} {'avg W':>9s} {'aux kWh':>9s} {'net EUR/yr':>11s}")
    for r in results:
        print(f"{r.scenario.name:42s} {r.heat_kwh:12,.0f} {r.mean_power_w:9,.0f} {r.aux_kwh:9,.0f} {r.net_eur:11,.0f}")
    farm = evaluate(FARM)
    print(f"\nFarm: capex repayable over 10 years: EUR {payback_capex(farm):,.0f}")
    print("Farm sizing:")
    for k, v in farm_sizing().items():
        print(f"  {k:28s} {v:10,.1f}")

    print("\nExchanger, 19 mm x 3 m aluminium, compost 60 C / water 40 C:")
    print(f"  2024 design assumption (h=1512.5): U={ORIGINAL_2024.u_value:.1f} W/m2K, "
          f"P={ORIGINAL_2024.power_w(60, 40):.0f} W")
    for h, p in sensitivity([5, 15, 30]):
        print(f"  h={h:>4} W/m2K -> P={p:.0f} W")

    # Figure 1: net value per year, on a symmetric log scale so EUR -40 and EUR 166k fit.
    fig, ax = plt.subplots(figsize=(10, 3.8))
    names = [r.scenario.name for r in results]
    nets = [r.net_eur for r in results]
    colors = [P.GREEN if v > 0 else P.HOT for v in nets]
    y = np.arange(len(results))[::-1]
    ax.barh(y, nets, color=colors, height=0.6)
    ax.set_xscale("symlog", linthresh=100)
    ax.set_yticks(y, names)
    ax.axvline(0, color=P.INK, lw=0.8)
    for yi, r in zip(y, results):
        power = f"{r.mean_power_w / 1000:,.0f} kW" if r.mean_power_w >= 1000 else f"{r.mean_power_w:,.0f} W"
        label = f"  EUR {r.net_eur:,.0f}/yr  ({power} avg)"
        ax.text(r.net_eur if r.net_eur > 0 else 0, yi, label, va="center",
                ha="left", fontsize=8, color=P.INK)
    ax.set_xlim(-300, 3e7)
    ax.set(xlabel="Net saving per year after auxiliary electricity (EUR, symlog)",
           title="Compost heat recovery only pays at farm scale")
    ax.grid(axis="y", visible=False)
    fig.savefig(FIG / "scenarios_net_value.png")
    plt.close(fig)

    # Figure 2: exchanger power vs compost-side film coefficient.
    hs = np.logspace(0, np.log10(3000), 200)
    ps = [PipeExchanger(h_compost=h).power_w(60, 40) for h in hs]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(hs, ps, color=P.COOL, lw=1.6)
    ax.axvspan(5, 30, color=P.GREEN, alpha=0.12, lw=0)
    ax.text(12, 2500, "realistic\ncompost\n5-30 W/m2K", ha="center", fontsize=8, color=P.GREEN)
    ax.scatter([1512.5], [ORIGINAL_2024.power_w(60, 40)], color=P.HOT, zorder=3)
    ax.annotate(f"2024 design point\n{ORIGINAL_2024.power_w(60, 40) / 1000:.2f} kW (assumed h=1512)",
                xy=(1512.5, ORIGINAL_2024.power_w(60, 40)), xytext=(60, 2900), fontsize=8, color=P.HOT,
                arrowprops=dict(arrowstyle="->", color=P.HOT, lw=0.8))
    p15 = PipeExchanger(h_compost=15).power_w(60, 40)
    ax.scatter([15], [p15], color=P.GREEN, zorder=3)
    ax.annotate(f"{p15:.0f} W at h=15", xy=(15, p15), xytext=(40, 600), fontsize=8, color=P.GREEN,
                arrowprops=dict(arrowstyle="->", color=P.GREEN, lw=0.8))
    ax.set_xscale("log")
    ax.set(xlabel="Compost-side heat transfer coefficient h (W/m2K, log)", ylabel="Power (W)",
           title="One assumption moved the exchanger from 3.5 kW to ~50 W")
    fig.savefig(FIG / "exchanger_sensitivity.png")
    plt.close(fig)
    print("\nwrote figures/scenarios_net_value.png, figures/exchanger_sensitivity.png")


if __name__ == "__main__":
    main()
