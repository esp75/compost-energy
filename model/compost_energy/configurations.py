"""Configuration study for the farm unit: how many tunnels, and how a batch moves.

The farm scenario fixes how much heat there is (energy_balance.FARM). This
module compares the ways of building the reactor that would recover it:

    A-N        N tunnels side by side, each runs the whole 15-day cycle in place.
               A wheel loader fills and empties one tunnel every 15/N days.
    B-N        N tunnels side by side, one phase per tunnel; the loader moves
               each batch from tunnel to tunnel every 15/N days.
    C-N  ...   N tunnels end to end with insulated doors between them. Only
               tunnel 1 is filled; the bed moves to the next tunnel inside the
               building, on an automatic transfer system:
                 -WF  aerated walking floor (hydraulic slats) in every tunnel
                 -NW  floor net pulled by a winch onto a travelling filling head
                      (the way mushroom-compost tunnels are emptied and filled)
               and either in steps of 15/N days ("step") or a slice every day
               ("daily", plug flow).
    D-3        The 2024 patent taken literally: three stacked chambers in a
               tower, material dropping floor to floor. A rough reference point.

What differs between options is the shape of the exhaust heat over time (it
sets the size of the exchanger and the fans), the building envelope, how much
material a loader moves and how much heat escapes while it does, the
equipment, and the capital cost. The heat itself is the same in every option
unless a remix boost is assumed for options that remix the bed on transfer.

All costs are first-pass assumptions with low/base/high values, listed in
``Costs``. Nothing here has been built or quoted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

from .energy_balance import FARM, evaluate, farm_sizing
from .industrial import Handling, IndustrialDesign, KOJIMA_KW_PER_M2, size
from .simulate import PileParams, rate_factor

CYCLE_DAYS = 15.0
DT_H = 0.5                              # profile resolution, hours


# ---------------------------------------------------------------------------
# heat release of one batch
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BatchProcess:
    """Temperature control of one batch, as the tunnel controller runs it.

    The bed heats on its own heat with the air mostly recirculated, is held at
    the setpoint for the hot phase, then cooled to the cooling setpoint. Heat
    leaves in the exhaust whenever the bed is at its setpoint or cooling.
    """
    t_fill_c: float = 15.0
    t_hot_c: float = 60.0
    t_cool_c: float = 45.0
    cool_from_day: float = 10.0
    recirc_share: float = 0.15           # share of heat-up heat that still leaves while recirculating
    k_max_per_day: float = 0.10          # first-order rate for manure/straw at optimum (lit. ~0.05-0.15 /d)
    lag_days: float = 0.8
    cooling_k_per_day: float = 6.0       # how fast fresh air pulls the bed down to t_cool
    approach_k: float = 8.0              # damper opening band below the setpoint


def batch_trace(p: BatchProcess = BatchProcess(), dt_h: float = DT_H) -> dict:
    """One batch under the tunnel controller, step by step over the 15 days.

    Uses the cardinal-temperature rate model of simulate.py with the
    temperature held by the controller. Returns the day, bed temperature,
    degradable substrate left (1 at fill) and the exhaust heat in the same
    units as the substrate (all of it would be 1).
    """
    pile = PileParams()
    n = int(CYCLE_DAYS * 24 / dt_h)
    dt_d = dt_h / 24
    s = 1.0                                     # remaining degradable substrate
    t = p.t_fill_c
    # All of a batch's degradable heat (0.24 kWh/kg, cp 2.5 kJ/kgK) would warm the bed by ~345 K.
    k_per_unit = 0.24 * 3600 / 2.5
    heat_capacity = 1.0 / k_per_unit            # units of heat per kelvin
    out, temp, left = np.zeros(n), np.zeros(n), np.zeros(n)
    for i in range(n):
        day = i * dt_d
        k = p.k_max_per_day * rate_factor(t, pile) * (1 - math.exp(-day / p.lag_days))
        q_bio = k * s                           # heat released this step per unit substrate
        s -= q_bio * dt_d
        target = p.t_hot_c if day < p.cool_from_day else p.t_cool_c
        if t < target:
            # The damper opens gradually over the last `approach_k` below setpoint.
            x = min(max((t - (target - p.approach_k)) / p.approach_k, 0.0), 1.0)
            share = p.recirc_share + (1 - p.recirc_share) * x * x * (3 - 2 * x)
            t = min(target, t + q_bio * (1 - share) * dt_d / heat_capacity)
            exhaust = q_bio * share
        else:                                   # at or above setpoint: heat goes to the exhaust
            drop = min(t - target, p.cooling_k_per_day * dt_d)
            t -= drop
            exhaust = q_bio + drop * heat_capacity / dt_d
        out[i], temp[i], left[i] = exhaust * dt_d, t, s
    return {"day": np.arange(n) * dt_d, "t_bed_c": temp, "substrate_left": left, "exhaust": out}


def batch_profile(p: BatchProcess = BatchProcess(), dt_h: float = DT_H) -> np.ndarray:
    """Exhaust heat of one batch over the 15-day cycle, normalised to sum to 1."""
    out = batch_trace(p, dt_h)["exhaust"]
    return out / out.sum()


def combined_profile(n_batches: int, shape: np.ndarray) -> np.ndarray:
    """Exhaust heat of a plant that starts a batch every 15/n days, steady state.

    One full cycle, starts evenly spaced; each batch carries 1/n of the 15-day
    feedstock. Normalised so the mean is 1 (multiply by the duty in kW).
    """
    n = len(shape)
    total = np.zeros(n)
    for j in range(n_batches):
        total += np.roll(shape, int(round(j * n / n_batches)))
    return total / total.mean()


def phase_peaks(n_stages: int, shape: np.ndarray, n_batches: int) -> list[float]:
    """Peak exhaust heat of each tunnel when tunnel i holds days [i, i+1]*15/N.

    Relative to the plant mean. Used to size one blower per tunnel when every
    tunnel holds one phase (B, C, D).
    """
    n = len(shape)
    total = np.zeros((n_stages, n))
    for j in range(n_batches):
        rolled = np.roll(shape, int(round(j * n / n_batches)))
        age = (np.arange(n) - int(round(j * n / n_batches))) % n
        stage = np.minimum(age * n_stages // n, n_stages - 1)
        for k in range(n_stages):
            total[k] += np.where(stage == k, rolled, 0.0)
    mean = sum(shape) * n_batches / n
    return [float(row.max() / mean) for row in total]


# ---------------------------------------------------------------------------
# costs (first-pass assumptions, EUR 2026, installed)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Costs:
    wall_eur_m2: float = 250.0           # 200 mm precast + 100 mm PIR, both faces finished
    roof_eur_m2: float = 140.0           # insulated, corrosion-proof
    aerated_floor_eur_m2: float = 350.0  # spigot floor + plenum slab
    door_eur: float = 28_000.0           # insulated, gas-tight, 4.5 x 3.6 m
    service_door_eur: float = 8_000.0
    blower_eur_per_kw: float = 1_400.0   # incl. VFD
    duct_set_eur: float = 14_000.0       # per tunnel: ducts, dampers, recirculation
    instruments_eur: float = 15_000.0    # per tunnel: probes, O2, pressure
    plc_eur: float = 45_000.0            # plant control, base
    exchanger_eur_m2: float = 450.0      # stainless plate-fin, condensing
    biofilter_eur_m2: float = 160.0
    buffer_eur_m3: float = 400.0         # insulated steel hot-water tank, installed
    # automatic transfer
    walking_floor_eur_m2: float = 1_300.0
    hydraulic_pack_eur: float = 35_000.0  # per tunnel
    winch_eur: float = 45_000.0           # per pulling point
    net_eur: float = 9_000.0              # per tunnel, replaced every 3 years (in opex)
    filling_head_eur: float = 140_000.0   # travelling head + transfer conveyors
    hopper_eur: float = 70_000.0          # receiving hopper, mixer, feed conveyor to T-101
    discharge_eur: float = 40_000.0       # outlet conveyor to the maturation hall
    reel_eur: float = 35_000.0            # remix reel + condensate spray, per internal door
    # vertical tower (D)
    tower_civil_factor: float = 2.2       # multi-storey structure carrying 1.7 t/m2 wet load per floor
    drop_floor_eur_m2: float = 1_600.0
    lift_conveyor_eur: float = 120_000.0
    # finance and upkeep
    years: float = 10.0
    rate: float = 0.06
    civil_upkeep: float = 0.01           # share of civil capex per year
    mech_upkeep: float = 0.05            # share of mechanical capex per year
    electricity_eur_kwh: float = 0.20


LOW = Costs(wall_eur_m2=180, roof_eur_m2=100, aerated_floor_eur_m2=250, door_eur=18_000, blower_eur_per_kw=900,
            exchanger_eur_m2=280, buffer_eur_m3=250, walking_floor_eur_m2=800, hydraulic_pack_eur=25_000, winch_eur=30_000,
            filling_head_eur=90_000, hopper_eur=50_000, reel_eur=20_000, drop_floor_eur_m2=1_100,
            tower_civil_factor=1.8)
HIGH = Costs(wall_eur_m2=350, roof_eur_m2=200, aerated_floor_eur_m2=500, door_eur=40_000, blower_eur_per_kw=2_000,
             exchanger_eur_m2=700, buffer_eur_m3=650, walking_floor_eur_m2=2_000, hydraulic_pack_eur=50_000, winch_eur=65_000,
             filling_head_eur=200_000, hopper_eur=120_000, reel_eur=60_000, drop_floor_eur_m2=2_200,
             tower_civil_factor=2.8)


def annuity(capex: float, c: Costs) -> float:
    r, n = c.rate, c.years
    return capex * r / (1 - (1 + r) ** -n)


# ---------------------------------------------------------------------------
# options
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Option:
    code: str
    n: int
    layout: str          # "side" (side by side), "line" (end to end), "tower"
    moves: str           # "loader" (fill/empty), "loader-transfer", "auto", "gravity"
    transfer: str = ""   # "", "WF" walking floor, "NW" net + winch
    daily: bool = False
    remixes: bool = False
    title: str = ""


def all_options() -> list[Option]:
    opts = []
    for n in (2, 3, 4):
        opts.append(Option(f"A-{n}", n, "side", "loader", title=f"{n} tunnels, whole cycle in place"))
    for n in (2, 3, 4):
        opts.append(Option(f"B-{n}", n, "side", "loader-transfer", remixes=True,
                           title=f"{n} tunnels, loader moves each batch"))
    for n in (2, 3, 4):
        for tr in ("WF", "NW"):
            name = "walking floor" if tr == "WF" else "net + winch"
            opts.append(Option(f"C-{n}-{tr}", n, "line", "auto", tr, remixes=True,
                               title=f"{n} tunnels in line, {name}, step every {15 / n:g} d"))
    for tr in ("WF",):
        opts.append(Option("C-3-WF-daily", 3, "line", "auto", tr, daily=True, remixes=True,
                           title="3 tunnels in line, walking floor, a slice every day"))
    opts.append(Option("D-3", 3, "tower", "gravity", remixes=True, title="3 stacked chambers (patent, literal)"))
    return opts


@dataclass
class Result:
    option: Option
    profile: np.ndarray = field(repr=False)
    numbers: dict


def evaluate_option(o: Option, c: Costs = Costs(), h: Handling = Handling(), remix_boost: float = 0.0,
                    process: BatchProcess = BatchProcess()) -> Result:
    d = IndustrialDesign(n_tunnels=o.n)
    m = size(d)
    farm = evaluate(FARM)
    sizing = farm_sizing()
    shape = batch_profile(process)
    stage_days = CYCLE_DAYS / o.n
    n_batches = 15 if o.daily else o.n
    prof = combined_profile(n_batches, shape)
    peak, low = float(prof.max()), float(prof.min())
    duty = m["duty_kw"]                                  # mean kW over the heating season

    # ---- geometry --------------------------------------------------------
    W, Ht, L = d.tunnel_width_m, d.tunnel_height_m, m["tunnel_length_m"]
    floor_m2 = o.n * W * L
    u = m["u_wall_w_m2k"]
    if o.layout == "side":
        ext_walls = 2 * L * Ht + o.n * 2 * W * Ht                 # two outer sides + both ends of every bay
        int_walls = (o.n - 1) * L * Ht                            # shared, between warm tunnels
        doors, service = o.n, 0
        footprint = (o.n * (W + 0.3) + 0.3) * (L + 0.6)
    elif o.layout == "line":
        ext_walls = 2 * (o.n * L) * Ht + 2 * W * Ht               # long sides + two ends
        int_walls = 0.0                                           # partitions are doors
        doors, service = o.n + 1, o.n                             # inlet, internal, outlet; side service doors
        footprint = (W + 0.6) * (o.n * L + (o.n + 1) * 0.3)
    else:  # tower: three floors of the same plan stacked
        ext_walls = 2 * (L + W) * Ht * o.n
        int_walls = 0.0
        doors, service = 1, o.n
        footprint = (W + 0.6) * (L + 0.6)
    roof_m2 = floor_m2 if o.layout != "tower" else W * L
    ground_m2 = roof_m2
    wall_loss_kw = u * (ext_walls + roof_m2 + ground_m2) * (d.t_core_c - d.t_ambient_c) / 1000

    # ---- heat ------------------------------------------------------------
    boost = remix_boost if o.remixes else 0.0
    heat_value_eur_per_kwh = FARM.fuel_price_eur_per_kwh / FARM.boiler_efficiency
    boost_eur = farm.heat_kwh * boost * heat_value_eur_per_kwh

    # ---- air, exchanger, fans --------------------------------------------
    air_mean = m["air_m3_h"]
    fan_kw_mean = m["fan_kw"]
    if o.layout == "side" and o.moves == "loader":
        # every tunnel sees every phase: each blower sized for one batch's peak
        per_tunnel_peak = float(shape.max() * len(shape)) / o.n  # one batch peak, as a share of plant mean
        installed_air = o.n * per_tunnel_peak * air_mean
    else:
        installed_air = sum(phase_peaks(o.n, shape, n_batches)) * air_mean
    fan_kw_installed = installed_air / 3600 * d.fan_pressure_pa / d.fan_efficiency / 1000
    if o.layout == "tower":
        fan_kw_installed *= 1.3                                   # deeper, compacting beds
    hx_area = peak * duty / KOJIMA_KW_PER_M2
    # Buffer that turns the uneven exhaust into a flat supply at the mean duty
    # (water 50/30 C, 23.3 kWh per m3). An upper bound: a user that can follow
    # the swings would need less.
    swing = np.cumsum(prof - 1.0) * duty * DT_H            # kWh above/below the mean
    buffer_kwh = float(swing.max() - swing.min())
    buffer_m3 = buffer_kwh / (4.186 * (d.t_supply_c - d.t_return_c) / 3.6)
    biofilter_m2 = peak * air_mean / d.biofilter_loading_m3_m2_h

    # ---- handling ----------------------------------------------------------
    fresh_t = m["feedstock_t_per_day"] * stage_days

    def mass(day):
        return fresh_t * h.mass_left_day15 ** (day / CYCLE_DAYS)

    if o.moves == "loader":
        loader_t_batch = fresh_t + mass(CYCLE_DAYS)
        hot_moves, released_kw = 0, 0.0
    elif o.moves == "loader-transfer":
        transfer_t = sum(mass(stage_days * k) for k in range(1, o.n))
        loader_t_batch = fresh_t + mass(CYCLE_DAYS) + transfer_t
        hot_moves = o.n - 1
        released_kwh = transfer_t * 1000 * h.cp_compost_kj_kgk * h.transfer_drop_k / 3600
        released_kw = released_kwh / (stage_days * 24)
    else:
        loader_t_batch = fresh_t                                  # loader only tips into the hopper
        hot_moves, released_kw = 0, 0.0
    loader_t_day = loader_t_batch / stage_days
    loader_h_day = loader_t_day / h.loader_t_per_h
    diesel_l_day = loader_t_day * h.diesel_l_per_t
    handling_eur = 365 * (diesel_l_day * h.diesel_eur_per_l + loader_h_day * h.operator_eur_per_h)
    lost_heat_eur = released_kw * d.heating_hours * heat_value_eur_per_kwh

    # transfer machinery energy (runs year-round with the plant)
    if o.moves == "auto":
        moves_per_year = 365 / (1 if o.daily else stage_days)
        run_h = (0.25 if o.daily else 0.6) * o.n                  # hours of hydraulics/winch per move
        mech_kw = 30.0 if o.transfer == "WF" else 22.0
        transfer_kwh = moves_per_year * run_h * (mech_kw + 15.0)  # + conveyors / filling head
        operator_h_day = 0.25                                     # tipping into the hopper, checks
        handling_eur += 365 * operator_h_day * h.operator_eur_per_h
    elif o.moves == "gravity":
        moves_per_year = 365 / stage_days
        transfer_kwh = moves_per_year * 0.5 * o.n * 20.0 + 365 * 0.5 * 20.0     # drop floors + daily lift to the top
    else:
        transfer_kwh = 0.0
    elec_eur = transfer_kwh * c.electricity_eur_kwh

    # ---- capex -------------------------------------------------------------
    civil = (ext_walls + int_walls) * c.wall_eur_m2 + roof_m2 * c.roof_eur_m2 + floor_m2 * c.aerated_floor_eur_m2
    if o.layout == "tower":
        civil *= c.tower_civil_factor
    mech = (doors * c.door_eur + service * c.service_door_eur
            + fan_kw_installed * c.blower_eur_per_kw + o.n * (c.duct_set_eur + c.instruments_eur) + c.plc_eur
            + hx_area * c.exchanger_eur_m2 + biofilter_m2 * c.biofilter_eur_m2 + buffer_m3 * c.buffer_eur_m3)
    transfer_capex = 0.0
    net_opex = 0.0
    if o.moves == "auto":
        transfer_capex += c.hopper_eur + c.discharge_eur + (o.n - 1) * c.reel_eur + 25_000   # + transfer PLC/safety
        if o.transfer == "WF":
            transfer_capex += floor_m2 * c.walking_floor_eur_m2 + o.n * c.hydraulic_pack_eur
        else:
            transfer_capex += o.n * c.winch_eur + c.filling_head_eur + o.n * c.net_eur
            net_opex = o.n * c.net_eur / 3
    elif o.moves == "gravity":
        transfer_capex += o.n * W * L * c.drop_floor_eur_m2 + c.lift_conveyor_eur + c.discharge_eur
    capex = civil + mech + transfer_capex
    upkeep = civil * c.civil_upkeep + (mech + transfer_capex) * c.mech_upkeep + net_opex

    # ---- value -------------------------------------------------------------
    # energy_balance.FARM already carries fixed opex (labour, general upkeep) and
    # the fans at their mean draw. Here we add what differs between options.
    wall_eur = (wall_loss_kw - _reference_wall_loss_kw()) * d.heating_hours * heat_value_eur_per_kwh
    # Routine filling and emptying (A-3) is inside FARM.fixed_opex; options pay or save the difference.
    handling_delta = handling_eur - _reference_handling_eur(m["feedstock_t_per_day"], h)
    operating = (farm.net_eur + boost_eur - handling_delta - lost_heat_eur - elec_eur - upkeep - wall_eur)
    value = operating - annuity(capex, c)

    return Result(o, prof, dict(
        code=o.code, title=o.title, n=o.n, stage_days=stage_days,
        tunnel_length_m=L, footprint_m2=footprint,
        peak_to_mean=peak, min_to_mean=low, cv=float(prof.std() / prof.mean()),
        duty_kw=duty, peak_kw=peak * duty, wall_loss_kw=wall_loss_kw,
        hx_area_m2=hx_area, buffer_kwh=buffer_kwh, buffer_m3=buffer_m3, fan_kw_installed=fan_kw_installed, fan_kw_mean=fan_kw_mean, biofilter_m2=biofilter_m2,
        loader_t_day=loader_t_day, loader_h_day=loader_h_day, diesel_l_day=diesel_l_day,
        hot_moves_per_batch=hot_moves, released_kw=released_kw,
        transfer_kwh=transfer_kwh, boost=boost, boost_eur=boost_eur,
        handling_eur=handling_eur, handling_delta_eur=handling_delta, lost_heat_eur=lost_heat_eur, elec_eur=elec_eur, upkeep_eur=upkeep,
        wall_eur=wall_eur,
        capex_civil=civil, capex_mech=mech, capex_transfer=transfer_capex, capex=capex,
        annuity_eur=annuity(capex, c), operating_eur=operating, value_eur=value,
    ))


def _reference_handling_eur(feed_t_day: float, h: Handling) -> float:
    """Loader cost of the base design: fill with fresh feedstock, empty at day 15."""
    t_day = feed_t_day * (1 + h.mass_left_day15)
    return 365 * (t_day * h.diesel_l_per_t * h.diesel_eur_per_l + t_day / h.loader_t_per_h * h.operator_eur_per_h)


def _reference_wall_loss_kw() -> float:
    """Wall loss already inside the farm scenario (A-3 as sized in industrial.py)."""
    m = size(IndustrialDesign())
    return m["wall_loss_kw_per_tunnel"] * m["n_tunnels"]


def study(c: Costs = Costs(), remix_boost: float = 0.0) -> list[Result]:
    return [evaluate_option(o, c, remix_boost=remix_boost) for o in all_options()]


def ranking(c: Costs = Costs(), remix_boost: float = 0.0) -> list[dict]:
    return sorted((r.numbers for r in study(c, remix_boost)), key=lambda x: -x["value_eur"])


def break_even_boost(code: str, against: str, c: Costs = Costs()) -> float:
    """Extra heat (share) an option that remixes needs to match `against`."""
    opt = next(o for o in all_options() if o.code == code)
    ref = evaluate_option(next(o for o in all_options() if o.code == against), c).numbers["value_eur"]
    lo, hi = 0.0, 1.0
    if evaluate_option(opt, c, remix_boost=0.0).numbers["value_eur"] >= ref:
        return 0.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if evaluate_option(opt, c, remix_boost=mid).numbers["value_eur"] >= ref:
            hi = mid
        else:
            lo = mid
    return hi


FINAL = "A-4"     # chosen 2026-10-21: best at low, base and high costs (see docs/explanation/configuration-study.md)


def final_choice(c: Costs = Costs()) -> str:
    """The option with the highest base-case value."""
    return ranking(c)[0]["code"]
