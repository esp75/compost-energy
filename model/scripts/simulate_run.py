"""Generate a SIMULATED prototype run: raw logger CSV + ground truth + energy ledger.

    python model/scripts/simulate_run.py [--seed 42] [--out data/simulated]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from compost_energy.simulate import RunConfig, simulate_truth, to_sensor_log, write_log, SIMULATED_BANNER

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "simulated")
    ap.add_argument("--run", default="run_01")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    cfg = RunConfig(seed=args.seed)
    truth, ledger = simulate_truth(cfg=cfg)
    raw = to_sensor_log(truth, cfg)

    write_log(raw, args.out / f"raw_{args.run}.csv", cfg.seed)

    hourly = truth.set_index("timestamp").resample("1h").mean().drop(columns="day")
    with open(args.out / f"truth_{args.run}.csv", "w") as f:
        f.write(f"# {SIMULATED_BANNER}\n# Ground truth from the physics model, hourly means.\n")
        hourly.to_csv(f, float_format="%.4g")

    j_to_kwh = 1 / 3.6e6
    summary = {
        "note": SIMULATED_BANNER,
        "seed": cfg.seed,
        "energy_kwh": {k[:-2]: round(v * j_to_kwh, 3) for k, v in ledger.items() if k.endswith("_j")},
        "degraded_solids_kg": round(ledger["degraded_kg"], 2),
        "injected_faults": raw.attrs["faults"],
    }
    (args.out / f"ledger_{args.run}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
