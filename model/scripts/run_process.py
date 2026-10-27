"""Process sheet for one batch: recipe, phases, moisture and water.

    python model/scripts/run_process.py

Prints the phases and the water balance of one tunnel batch, writes
data/model/process.json and figures/process_batch.png. Everything is MODEL.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from compost_energy import plotting as P
from compost_energy.process import Targets, phases, run_batch, summary

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "figures"
OUT = ROOT / "data" / "model" / "process.json"
VIDEO = ROOT / "video" / "src" / "tunnel-data.js"


def main() -> None:
    s = summary()
    m, t = s["mix"], s["totals"]
    print(f"Mix: moisture {m['moisture']:.1%}, C:N {m['cn']:.0f}, batch {s['batch_t']:.0f} t (MODEL)")
    for ph in s["phases"]:
        share = f"{ph['share']:.0%} of the degradable matter" if ph["share"] is not None else ""
        print(f"  {ph['phase']:13s} day {ph['start']:5.1f} - {ph['end']:5.1f}  {ph['temp']:22s} {share}")
    print(f"Water per batch: {t['evaporated_t']:.0f} t evaporated, {t['metabolic_t']:.0f} t formed, "
          f"{t['condensate_t']:.0f} t condensed in the exchanger, {t['sprayed_t']:.0f} t sprayed; "
          f"end moisture {t['end_moisture']:.0%}, mass left {t['mass_left']:.0%}")
    for row in s["sensitivity"]:
        print(f"  fill at {row['fill_moisture']:.0%}: spray {row['sprayed_t']:4.0f} t, end {row['end_moisture']:.0%}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump({
        "note": "MODEL. Literature feedstock values and the batch kinetics of configurations.py; not measured.",
        "mix": {"moisture": m["moisture"], "cn": m["cn"], "parts": m["parts"]},
        "targets": asdict(Targets()),
        "batch_t": s["batch_t"],
        "sanitised_day": s["sanitised_day"],
        "phases": s["phases"],
        "water_per_batch": t,
        "fill_moisture_sensitivity": s["sensitivity"],
    }, OUT.open("w"), indent=1, default=float)
    print("wrote", OUT)

    # ---- the explainer video's tunnel chapter: one batch every 3 h -------------
    b = run_batch()
    ph = {p["phase"]: p for p in s["phases"]}
    k = max(1, round(3 / ((b["day"][1] - b["day"][0]) * 24)))
    VIDEO.write_text("// MODEL: one tunnel batch from model/compost_energy/process.py, every 3 h. "
                     "Written by model/scripts/run_process.py.\nwindow.TUNNEL_DATA = " + json.dumps({
                         "day": [round(float(v), 3) for v in b["day"][::k]],
                         "T": [round(float(v), 1) for v in b["t_bed_c"][::k]],
                         "moisture": [round(float(v), 3) for v in b["moisture"][::k]],
                         "t45": round(ph["mesophilic"]["end"], 2), "hot_from": round(ph["hot hold"]["start"], 2),
                         "sanitised": round(b["sanitised_day"], 2), "cool_from": round(ph["cooling"]["start"], 2),
                         "batch_t": round(s["batch_t"]), "fill_moisture": round(m["moisture"], 4), "cn": round(m["cn"], 1),
                         "evaporated_t": round(t["evaporated_t"]), "condensate_t": round(t["condensate_t"]),
                         "end_moisture": round(t["end_moisture"], 3),
                     }) + ";\n")
    print("wrote", VIDEO)

    # ---- figure: one batch, temperature and moisture, phases shaded ----------
    b = run_batch()
    day = b["day"]
    tg = Targets()
    fig, (a0, a1) = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True, gridspec_kw={"height_ratios": [1.25, 1]})
    for ph in phases(b):
        if ph.get("sub") or ph["where"] != "tunnel":
            continue
        col = P.PHASE_COLORS[ph["phase"]]
        for ax in (a0, a1):
            ax.axvspan(ph["start"], ph["end"], color=col, alpha=0.13, lw=0)
        a0.text((ph["start"] + ph["end"]) / 2, 68, ph["phase"], ha="center", va="top", color=P.INK, fontsize=9.5)
    for ax in (a0, a1):
        ax.axvspan(10, 15, color=P.PHASE_COLORS["cooling"], alpha=0.10, lw=0)
    a0.text(12.5, 64, "cooling", ha="center", va="top", color=P.MUTED, fontsize=8.5)
    a0.plot(day, b["t_bed_c"], color=P.HOT, lw=1.8)
    a0.axhline(tg.sanitise_c, color=P.MUTED, lw=0.8, ls="--")
    sd = b["sanitised_day"]
    hot0 = float(day[np.argmax(b["t_bed_c"] >= tg.sanitise_c)])
    a0.annotate("", xy=(sd, 52), xytext=(hot0, 52), arrowprops=dict(arrowstyle="<->", color=P.INK, lw=0.9))
    a0.text((hot0 + sd) / 2, 50.5, "sanitised: 72 h ≥ 55 °C", ha="center", va="top", fontsize=8.5)
    a0.set_ylim(10, 70)
    a0.set_ylabel("bed temperature, °C")
    a0.set_title("One tunnel batch: phases, temperature and moisture (MODEL)")

    a1.axhspan(0.50, 0.60, color=P.GREEN, alpha=0.08, lw=0)
    a1.text(0.2, 0.595, "preferred 50-60 %", va="top", color=P.GREEN, fontsize=8.5)
    a1.plot(day, b["moisture"], color=P.COOL, lw=1.8, label=f"filled at {b['fill_moisture']:.0%}")
    for f, ls in ((0.55, ":"), (0.70, "--")):
        r = run_batch(fill_moisture=f)
        a1.plot(day, r["moisture"], color=P.COOL, lw=1.1, ls=ls, alpha=0.8, label=f"filled at {f:.0%}")
        idx = np.flatnonzero(r["sprayed_kg"])
        if len(idx):
            a1.scatter(day[idx], r["moisture"][idx], s=14, color=P.WARM, zorder=3)
    a1.scatter([], [], s=14, color=P.WARM, label="spray bars on")
    a1.set_ylim(0.40, 0.72)
    a1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    a1.set_ylabel("bed moisture")
    a1.set_xlabel("days in the tunnel (then 8 weeks of maturation in windrows)")
    a1.set_xlim(0, 15)
    a1.legend(loc="lower left", ncol=4, fontsize=8.5)
    fig.savefig(FIG / "process_batch.png")
    print("wrote", FIG / "process_batch.png")


if __name__ == "__main__":
    main()
