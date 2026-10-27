"""Configuration study: 2-4 tunnels, loader transfer, automatic transfer, tower.

    python model/scripts/run_configurations.py

Prints the ranking at low, base and high costs, writes
data/model/configurations.json and draws two figures. Everything is MODEL.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from compost_energy import plotting as P
from compost_energy.configurations import (
    DT_H, FINAL, HIGH, LOW, BatchProcess, Costs, all_options, batch_profile, break_even_boost,
    combined_profile, evaluate_option, ranking,
)

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "figures"
OUT = ROOT / "data" / "model" / "configurations.json"


def main() -> None:
    FIG.mkdir(exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cases = {"low": LOW, "base": Costs(), "high": HIGH}
    tables = {name: ranking(c) for name, c in cases.items()}

    for name, rows in tables.items():
        print(f"\n{name.upper()} costs: value after capital, kEUR/yr (MODEL)")
        for r in rows:
            print(f"  {r['code']:14s} {r['value_eur'] / 1e3:7.1f}   capex {r['capex'] / 1e3:6.0f}k   "
                  f"peak/mean {r['peak_to_mean']:.2f}   buffer {r['buffer_m3']:4.0f} m3   {r['title']}")
    boosts = {code: break_even_boost(code, FINAL) for code in ("B-3", "C-3-NW", "C-3-WF", "C-3-WF-daily", "D-3")}
    print("\nExtra heat from remixing needed to match", FINAL, {k: round(v, 3) for k, v in boosts.items()})

    json.dump({
        "note": "MODEL. First-pass capital and operating estimates; nothing here has been built or quoted.",
        "final": FINAL,
        "costs": {name: asdict(c) for name, c in cases.items()},
        "process": asdict(BatchProcess()),
        "ranking": {name: [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in rows]
                    for name, rows in tables.items()},
        "break_even_remix_boost": boosts,
    }, OUT.open("w"), indent=1)
    print("wrote", OUT)

    # ---- figure 1: exhaust heat over one cycle ---------------------------
    shape = batch_profile()
    duty = evaluate_option(all_options()[1]).numbers["duty_kw"]
    days = np.arange(len(shape)) * DT_H / 24
    fig, (a0, a1) = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1, 1.4]})
    a0.fill_between(days, shape * len(shape), color=P.WARM, alpha=0.25, lw=0)
    a0.plot(days, shape * len(shape), color=P.HOT, lw=1.6)
    for x0, x1, name in ((0, 4, "heat-up\n(recirculation)"), (4, 10, "hot phase\n≥ 55 °C"), (10, 15, "cooling")):
        a0.text((x0 + x1) / 2, 0.06, name, ha="center", fontsize=8, color=P.MUTED)
    a0.set_xlim(0, 15)
    a0.set_ylim(0, None)
    a0.set_xlabel("day of the batch")
    a0.set_ylabel("exhaust heat / batch mean")
    a0.set_title("One batch")
    styles = [(2, P.LIME, "2 tunnels"), (3, P.WARM, "3 tunnels"), (4, P.GREEN, "4 tunnels (final)"),
              (15, P.COOL, "daily slices (plug flow)")]
    for n, col, label in styles:
        prof = combined_profile(n, shape) * duty
        a1.plot(days, prof, color=col, lw=2.0 if n == 4 else 1.2, label=f"{label}: peak {prof.max():.0f} kW")
    a1.axhline(duty, color=P.INK, lw=0.7, ls=":")
    a1.text(0.15, duty + 8, f"mean {duty:.0f} kW", ha="left", fontsize=8, color=P.INK)
    a1.set_xlim(0, 15)
    a1.set_xlabel("day")
    a1.set_ylabel("plant exhaust heat, kW")
    a1.set_title("The plant: batches started 15/N days apart")
    a1.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    fig.text(0.995, 0.995, "MODEL", ha="right", va="top", fontsize=8, color=P.HOT)
    fig.tight_layout()
    fig.savefig(FIG / "config_heat_profiles.png")
    plt.close(fig)

    # ---- figure 2: value after capital, with low-high range ----------------
    base = {r["code"]: r for r in tables["base"]}
    low = {r["code"]: r["value_eur"] for r in tables["low"]}
    high = {r["code"]: r["value_eur"] for r in tables["high"]}
    codes = [r["code"] for r in tables["base"]][::-1]
    fig, ax = plt.subplots(figsize=(9, 5.6))
    y = np.arange(len(codes))
    vals = [base[c]["value_eur"] / 1e3 for c in codes]
    fam_col = {"A": P.GREEN, "B": P.WARM, "C": P.COOL, "D": P.MUTED}
    ax.barh(y, vals, color=[fam_col[c[0]] for c in codes], height=0.62)
    for yi, c in zip(y, codes):
        ax.plot([high[c] / 1e3, low[c] / 1e3], [yi, yi], color=P.INK, lw=0.8)
        ax.text(max(low[c] / 1e3, 0) + 3, yi, base[c]["title"], va="center", fontsize=7.5, color=P.MUTED)
    ax.axvline(0, color=P.INK, lw=0.8)
    ax.set_yticks(y, [f"{c}  ◀ final" if c == FINAL else c for c in codes], fontsize=8.5)
    ax.set_xlabel("net value after capital, kEUR per year (bar: base costs, line: low to high)")
    ax.set_title("Which reactor? Value after paying for it over 10 years at 6 %")
    ax.set_xlim(min(high.values()) / 1e3 - 10, max(low.values()) / 1e3 + 120)
    fig.text(0.995, 0.995, "MODEL", ha="right", va="top", fontsize=8, color=P.HOT)
    fig.tight_layout()
    fig.savefig(FIG / "config_comparison.png")
    plt.close(fig)
    print("wrote figures/config_heat_profiles.png, figures/config_comparison.png")


if __name__ == "__main__":
    main()
