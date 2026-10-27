"""The composting process inside one tunnel: recipe, phases and water.

configurations.py gives the shape of a batch's heat. This module turns the
same batch into a process sheet an operator could run:

    recipe      what goes in: the mix of manure, silage and straw, its
                moisture, C:N ratio and the targets it has to meet
    phases      mesophilic start, thermophilic phase, sanitisation window,
                cooling, then maturation outside the tunnel, with the days
                each one lasts in the controlled tunnel
    water       how much water the exhaust carries off, how much the
                exchanger gives back as condensate, the bed's moisture day by
                day, and when the spray bars have to add water

Why only 15 days in the tunnel: the tunnel is the intensive stage, where the
bed is hot, sanitised and releases most of its heat. Composting is not
finished at day 15. The batch then matures for 8 weeks in windrows
(energy_balance.farm_sizing), where the rest of the degradable matter breaks
down slowly at 25-45 °C, too cool and too spread out to be worth recovering.

Everything here is MODEL output from literature values, not measurement.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .configurations import CYCLE_DAYS, BatchProcess, batch_trace
from .energy_balance import FARM, farm_sizing
from .industrial import humidity_ratio, enthalpy_kj_per_kg, operating_modes

# ---------------------------------------------------------------------------
# recipe
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Feedstock:
    name: str
    moisture: float           # kg water per kg wet
    c_pct_dm: float           # carbon, % of dry matter
    n_pct_dm: float           # nitrogen, % of dry matter
    bulk_t_m3: float          # as delivered


# Typical values (on-farm composting handbooks, NRAES-54 tables); a pilot measures its own.
CATTLE_MANURE = Feedstock("cattle manure with bedding", 0.77, 40.0, 2.2, 0.80)
SILAGE = Feedstock("spoiled grass/maize silage", 0.65, 44.0, 2.0, 0.65)
STRAW = Feedstock("chopped straw", 0.12, 45.0, 0.6, 0.10)


@dataclass(frozen=True)
class Recipe:
    parts: tuple = ((CATTLE_MANURE, 0.70), (SILAGE, 0.15), (STRAW, 0.15))   # mass shares


@dataclass(frozen=True)
class Targets:
    """Process window the controller and the operator hold (NRAES-54 preferred ranges unless noted)."""
    cn: tuple = (25.0, 35.0)
    moisture_fill: tuple = (0.55, 0.65)
    moisture_hot_min: float = 0.52       # below this, spray during the hot phase
    moisture_hot_set: float = 0.56       # spray back up to this
    moisture_cool_min: float = 0.47      # cooling phase: spray (clean water) below this ...
    moisture_cool_set: float = 0.50      # ... back up to this
    moisture_end: tuple = (0.45, 0.55)   # leaving the tunnel for maturation
    moisture_maturation: tuple = (0.40, 0.50)
    bulk_max_t_m3: float = 0.65          # ~1,100 lb/yd³; denser mixes lack free air space
    o2_min_pct: float = 5.0
    particle_mm: tuple = (6.0, 50.0)
    ph: tuple = (6.5, 8.5)
    sanitise_c: float = 55.0
    sanitise_h: float = 72.0             # 55 °C for 72 h: French order of 22 April 2008 (forced aeration), US EPA PFRP


def mix(r: Recipe = Recipe()) -> dict:
    """Moisture, C:N and dry matter of the recipe, per tonne of wet mix."""
    dm = sum(share * (1 - f.moisture) for f, share in r.parts)
    c = sum(share * (1 - f.moisture) * f.c_pct_dm / 100 for f, share in r.parts)
    n = sum(share * (1 - f.moisture) * f.n_pct_dm / 100 for f, share in r.parts)
    return {"moisture": 1 - dm, "dry_matter": dm, "cn": c / n,
            "parts": [(f.name, share) for f, share in r.parts]}


# ---------------------------------------------------------------------------
# one batch: phases and water
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WaterModel:
    t_in_c: float = 5.0                  # fresh air into the floor, heating season
    rh_in: float = 0.85
    t_hx_out_c: float = 35.0             # the exchanger cools the exhaust to this (industrial.py)
    vs_mj_per_kg: float = 20.0           # heat released per kg of organic matter oxidised
    metabolic_water: float = 0.6         # kg water formed per kg of organic matter oxidised
    cp_bed_kj_kgk: float = 2.5
    spray_m3_h: float = 6.0              # spray bar capacity per tunnel


def run_batch(r: Recipe = Recipe(), p: BatchProcess = BatchProcess(), w: WaterModel = WaterModel(),
              tg: Targets = Targets(), fill_moisture: float | None = None) -> dict:
    """Day-by-day state of one batch in its tunnel, with spray control.

    The exhaust heat of configurations.batch_trace is the enthalpy the air
    carries out of the bed above the inlet. It is scaled so that the part the
    exchanger takes (down to 35 °C) is the farm scenario's recoverable heat
    per batch, the same number every other module uses.
    """
    ops = operating_modes()
    batch_kg = ops["batch_t"] * 1000
    m = mix(r)
    moist0 = m["moisture"] if fill_moisture is None else fill_moisture
    tr = batch_trace(p)
    day, t_bed, ex = tr["day"], tr["t_bed_c"], tr["exhaust"]

    h_in, w_in = enthalpy_kj_per_kg(w.t_in_c, w.rh_in), humidity_ratio(w.t_in_c, w.rh_in)
    h_out, w_out = enthalpy_kj_per_kg(w.t_hx_out_c), humidity_ratio(w.t_hx_out_c)
    h_bed = np.array([enthalpy_kj_per_kg(t) for t in t_bed])
    w_bed = np.array([humidity_ratio(t) for t in t_bed])
    recover = np.clip((h_bed - h_out) / (h_bed - h_in), 0.0, None)   # share of exhaust enthalpy above 35 °C

    recoverable_kwh = batch_kg * FARM.kwh_per_kg
    exhaust_kwh = ex * recoverable_kwh / float((ex * recover).sum())
    air_kg = exhaust_kwh * 3600 / (h_bed - h_in)                      # dry air through the bed per step
    evap = air_kg * (w_bed - w_in)
    condensate = air_kg * np.clip(w_bed - w_out, 0.0, None)

    # organic matter oxidised: heat into the air plus heat stored in the bed
    stored_kwh = batch_kg * w.cp_bed_kj_kgk * (t_bed - p.t_fill_c) / 3600
    bio_kwh = np.cumsum(exhaust_kwh) + stored_kwh
    vs_lost = bio_kwh * 3.6 / w.vs_mj_per_kg                          # kg, cumulative

    water0 = batch_kg * moist0
    dry0 = batch_kg - water0
    sanitised_at = _sanitised_day(day, t_bed, tg)
    water = np.zeros_like(day)
    sprayed = np.zeros_like(day)
    from_condensate = 0.0
    added = 0.0
    dt_h = (day[1] - day[0]) * 24
    cum_evap = np.cumsum(evap)
    for i in range(len(day)):
        wtr = water0 - cum_evap[i] + w.metabolic_water * vs_lost[i] + added
        dry = dry0 - vs_lost[i]
        lo, hi = ((tg.moisture_hot_min, tg.moisture_hot_set) if day[i] < p.cool_from_day
                  else (tg.moisture_cool_min, tg.moisture_cool_set))
        if wtr / (wtr + dry) < lo:
            need = (hi * (wtr + dry) - wtr) / (1 - hi)
            dose = min(need, w.spray_m3_h * 1000 * dt_h)
            added += dose
            sprayed[i] = dose
            # condensate only until the batch is sanitised, clean water after
            if sanitised_at is None or day[i] < sanitised_at:
                from_condensate += dose
            wtr += dose
        water[i] = wtr
    dry = dry0 - vs_lost
    moisture = water / (water + dry)
    return {
        "day": day, "t_bed_c": t_bed, "moisture": moisture, "exhaust_kwh": exhaust_kwh,
        "recovered_kwh": exhaust_kwh * recover, "evaporated_kg": evap, "condensate_kg": condensate,
        "sprayed_kg": sprayed, "mass_kg": water + dry, "substrate_left": tr["substrate_left"],
        "batch_kg": batch_kg, "fill_moisture": moist0, "sanitised_day": sanitised_at,
        "totals": {
            "evaporated_t": float(evap.sum()) / 1000,
            "metabolic_t": float(w.metabolic_water * vs_lost[-1]) / 1000,
            "condensate_t": float(condensate.sum()) / 1000,
            "sprayed_t": float(added) / 1000,
            "sprayed_condensate_t": float(from_condensate) / 1000,
            "organic_matter_lost_t": float(vs_lost[-1]) / 1000,
            "mass_left": float((water[-1] + dry[-1]) / batch_kg),
            "end_moisture": float(moisture[-1]),
            "min_moisture": float(moisture.min()),
        },
    }


def _sanitised_day(day: np.ndarray, t: np.ndarray, tg: Targets) -> float | None:
    """Day the bed has been at or above the sanitising temperature for the required hours, unbroken."""
    dt_h = (day[1] - day[0]) * 24
    run = 0.0
    for d, temp in zip(day, t):
        run = run + dt_h if temp >= tg.sanitise_c else 0.0
        if run >= tg.sanitise_h:
            return float(d)
    return None


def phases(b: dict, p: BatchProcess = BatchProcess(), tg: Targets = Targets()) -> list[dict]:
    """Phase windows of one batch, in days from filling, then maturation outside.

    mesophilic    from filling until the bed passes 45 °C
    thermophilic  45 °C and above, until the batch leaves the tunnel. Inside it:
      hot hold      55-60 °C, where the bed is held at its setpoint
      sanitisation  the first unbroken 72 h at 55 °C or more
      cooling       fresh air brings the bed from 60 to 45 °C before emptying
    maturation    8 weeks in windrows, mesophilic again: curing and humification

    ``share`` is the part of the batch's degradable matter broken down in
    each phase (the heat follows the same split).
    """
    day, t = b["day"], b["t_bed_c"]
    t45 = float(day[np.argmax(t >= 45.0)])
    hot = np.flatnonzero(t >= tg.sanitise_c)
    h0, h1 = float(day[hot[0]]), float(day[hot[-1]])
    left = b["substrate_left"]

    def released(d0, d1):
        i0, i1 = int(np.searchsorted(day, d0)), min(int(np.searchsorted(day, d1)), len(day) - 1)
        return float(left[i0] - left[i1])

    fs = farm_sizing()
    mat_days = fs["maturation_m3"] / fs["precompost_out_m3_per_day"]
    return [
        {"phase": "mesophilic", "start": 0.0, "end": t45, "where": "tunnel",
         "temp": f"{p.t_fill_c:.0f} → 45 °C", "air": "mostly recirculated", "share": released(0, t45)},
        {"phase": "thermophilic", "start": t45, "end": CYCLE_DAYS, "where": "tunnel",
         "temp": f"45-{p.t_hot_c:.0f} °C", "air": "temperature loop, O₂ ≥ 5 %",
         "share": released(t45, CYCLE_DAYS)},
        {"phase": "hot hold", "start": h0, "end": h1, "where": "tunnel", "sub": True,
         "temp": f"≥ {tg.sanitise_c:.0f} °C, held at {p.t_hot_c:.0f}", "air": "fresh air as needed",
         "share": released(h0, h1)},
        {"phase": "sanitisation", "start": h0, "end": b["sanitised_day"], "where": "tunnel", "sub": True,
         "temp": f"≥ {tg.sanitise_c:.0f} °C for {tg.sanitise_h:.0f} h", "air": "timer restarts on any dip",
         "share": None},
        {"phase": "cooling", "start": p.cool_from_day, "end": CYCLE_DAYS, "where": "tunnel", "sub": True,
         "temp": f"{p.t_hot_c:.0f} → {p.t_cool_c:.0f} °C", "air": "full fresh air",
         "share": released(p.cool_from_day, CYCLE_DAYS)},
        {"phase": "maturation", "start": CYCLE_DAYS, "end": CYCLE_DAYS + mat_days, "where": "windrows",
         "temp": "45 °C → ambient", "air": "turned weekly", "share": float(left[-1])},
    ]


def sensitivity(fill: tuple = (0.55, 0.60, 0.65, 0.70)) -> list[dict]:
    """Spray water and end moisture for wetter and drier mixes."""
    out = []
    for f in fill:
        t = run_batch(fill_moisture=f)["totals"]
        out.append({"fill_moisture": f, **{k: float(v) for k, v in t.items()}})
    return out


def summary() -> dict:
    b = run_batch()
    return {"mix": mix(), "targets": Targets(), "batch_t": b["batch_kg"] / 1000, "totals": b["totals"],
            "phases": phases(b), "sanitised_day": b["sanitised_day"], "sensitivity": sensitivity()}


if __name__ == "__main__":
    s = summary()
    print("mix", {k: v for k, v in s["mix"].items() if k != "parts"})
    for ph in s["phases"]:
        print(ph)
    print(s["totals"])
    for row in s["sensitivity"]:
        print({k: round(v, 3) for k, v in row.items()})
