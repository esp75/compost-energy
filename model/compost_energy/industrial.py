"""First-pass sizing of the farm-scale unit: tunnels, aeration, heat recovery.

The farm scenario in energy_balance.py says how much heat there is. This
module turns that into hardware (the final design, A-4 in configurations.py): how big the tunnels are, how much air the
fans move, how much exchanger area that air needs, and what the water loop
looks like. The drawings CE-06..CE-10 read every number from here.

Heat leaves a forced-aeration composter mostly as latent heat in saturated
exhaust air, so the exchanger is sized on moist-air enthalpy, not on sensible
heat alone. Exchanger area is scaled from the specific duty measured on a
dairy-farm composter (Kojima et al. 2022: 23.3 kW from 9.2 m² of plate-fin).

Everything here is a design estimate. Nothing has been built at this scale.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from .energy_balance import FARM, evaluate, farm_sizing

P_ATM_KPA = 101.325
CP_WATER = 4.186  # kJ/kgK
KOJIMA_KW_PER_M2 = 23.3 / 9.2  # measured specific duty of a plate-fin exhaust exchanger


# ---- moist air ------------------------------------------------------------

def p_sat_kpa(t_c: float) -> float:
    """Saturation vapour pressure over water (Buck 1981), kPa."""
    return 0.61121 * math.exp((18.678 - t_c / 234.5) * (t_c / (257.14 + t_c)))


def humidity_ratio(t_c: float, rh: float = 1.0) -> float:
    """kg water per kg dry air."""
    pw = rh * p_sat_kpa(t_c)
    return 0.62198 * pw / (P_ATM_KPA - pw)


def enthalpy_kj_per_kg(t_c: float, rh: float = 1.0) -> float:
    """Moist-air enthalpy per kg of dry air, 0 °C dry air reference."""
    w = humidity_ratio(t_c, rh)
    return 1.006 * t_c + w * (2501.0 + 1.86 * t_c)


def specific_volume_m3_per_kg(t_c: float, rh: float = 1.0) -> float:
    """m³ of moist air per kg of dry air."""
    w = humidity_ratio(t_c, rh)
    return 0.287042 * (t_c + 273.15) * (1 + 1.607858 * w) / P_ATM_KPA


# ---- design ---------------------------------------------------------------

@dataclass(frozen=True)
class IndustrialDesign:
    # Four tunnels, each running the whole 15-day cycle, started 3.75 days apart.
    # Chosen in configurations.py (option A-4) over 2-4 tunnels, loader transfer,
    # automatic transfer and a stacked tower; see docs/configurations.md.
    n_tunnels: int = 4
    tunnel_width_m: float = 5.0
    tunnel_height_m: float = 4.0
    fill_depth_m: float = 2.0
    # 200 mm precast concrete + 100 mm PIR, inside and outside film
    wall_concrete_m: float = 0.20
    wall_insulation_m: float = 0.10
    k_concrete: float = 1.7
    k_insulation: float = 0.022
    t_core_c: float = 60.0
    t_ambient_c: float = 5.0
    # exhaust leaves the compost saturated at roughly core temperature and
    # leaves the exchanger saturated at the cooled temperature
    t_exhaust_c: float = 60.0
    t_air_out_c: float = 35.0
    # hot-water loop to the farm heat users
    t_supply_c: float = 50.0
    t_return_c: float = 30.0
    # fan: spigot floor + compost bed + exchanger + biofilter
    fan_pressure_pa: float = 2500.0
    fan_efficiency: float = 0.6
    duct_velocity_m_s: float = 10.0
    # biofilter surface loading, typical 50-150 m³ of air per m² per hour
    biofilter_loading_m3_m2_h: float = 125.0
    heating_hours: float = 5 * 730.0
    # Exhaust heat of four staggered batches peaks at 1.15x its mean, and a buffer
    # of about 85 m3 flattens it for the heat user (configurations.py, A-4).
    peak_to_mean: float = 1.15
    buffer_m3: float = 85.0
    # Each blower must carry its own batch at that batch's peak, 2.03x the plant's mean airflow / N.
    blower_peak_factor: float = 2.03


def duct_diameter_mm(flow_m3_h: float, velocity_m_s: float) -> float:
    return 2000.0 * math.sqrt(flow_m3_h / 3600.0 / velocity_m_s / math.pi)


def pinch_k(d: IndustrialDesign, m_dry_air: float, m_water: float, n: int = 200) -> float:
    """Smallest air-to-water temperature difference in a counterflow exchanger.

    Air stays saturated as it cools, so its temperature at each point is the
    saturation temperature for its enthalpy. Water enters where air leaves.
    """
    h_out = enthalpy_kj_per_kg(d.t_air_out_c)
    smallest = math.inf
    for i in range(n + 1):
        t_w = d.t_return_c + (d.t_supply_c - d.t_return_c) * i / n
        h_air = h_out + m_water * CP_WATER * (t_w - d.t_return_c) / m_dry_air
        lo, hi = d.t_air_out_c - 1.0, d.t_exhaust_c + 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if enthalpy_kj_per_kg(mid) < h_air else (lo, mid)
        smallest = min(smallest, lo - t_w)
    return smallest


def size(d: IndustrialDesign = IndustrialDesign()) -> dict:
    plant = farm_sizing()
    heat = evaluate(FARM)

    solids_per_tunnel = plant["precompost_solids_m3"] / d.n_tunnels
    length = solids_per_tunnel / (d.tunnel_width_m * d.fill_depth_m)
    gross_per_tunnel = d.tunnel_width_m * d.tunnel_height_m * length

    # Wall losses through the envelope of one tunnel (floor counted as wall).
    area = (2 * length * d.tunnel_height_m + 2 * d.tunnel_width_m * d.tunnel_height_m
            + 2 * d.tunnel_width_m * length)
    u_wall = 1.0 / (0.13 + d.wall_concrete_m / d.k_concrete
                    + d.wall_insulation_m / d.k_insulation + 0.04)
    wall_loss_kw = u_wall * area * (d.t_core_c - d.t_ambient_c) / 1000.0

    # Design duty: the year's recovered heat delivered over the heating season.
    duty_kw = heat.heat_kwh / d.heating_hours

    dh = enthalpy_kj_per_kg(d.t_exhaust_c) - enthalpy_kj_per_kg(d.t_air_out_c)
    m_dry_air = duty_kw / dh  # kg/s
    v_air = m_dry_air * specific_volume_m3_per_kg(d.t_exhaust_c) * 3600.0  # m³/h at exhaust
    fan_kw = v_air / 3600.0 * d.fan_pressure_pa / d.fan_efficiency / 1000.0
    condensate = m_dry_air * (humidity_ratio(d.t_exhaust_c) - humidity_ratio(d.t_air_out_c))
    sensible_share = 1.006 * (d.t_exhaust_c - d.t_air_out_c) / dh

    hx_area = duty_kw * d.peak_to_mean / KOJIMA_KW_PER_M2      # sized for the peak, not the mean
    m_water = duty_kw / (CP_WATER * (d.t_supply_c - d.t_return_c))  # kg/s
    per_tunnel = v_air / d.n_tunnels

    return {
        "n_tunnels": d.n_tunnels,
        "tunnel_width_m": d.tunnel_width_m,
        "tunnel_height_m": d.tunnel_height_m,
        "tunnel_length_m": length,
        "fill_depth_m": d.fill_depth_m,
        "solids_per_tunnel_m3": solids_per_tunnel,
        "gross_per_tunnel_m3": gross_per_tunnel,
        "gross_total_m3": gross_per_tunnel * d.n_tunnels,
        "feedstock_t_per_day": plant["feedstock_t_per_day"],
        "envelope_m2_per_tunnel": area,
        "u_wall_w_m2k": u_wall,
        "wall_loss_kw_per_tunnel": wall_loss_kw,
        "duty_kw": duty_kw,
        "wall_loss_share": wall_loss_kw * d.n_tunnels / duty_kw,
        "air_dry_kg_s": m_dry_air,
        "air_m3_h": v_air,
        "air_per_tunnel_m3_h": per_tunnel,
        "duct_tunnel_mm": duct_diameter_mm(per_tunnel, d.duct_velocity_m_s),
        "duct_manifold_mm": duct_diameter_mm(v_air, d.duct_velocity_m_s),
        "air_changes_per_h": v_air / (gross_per_tunnel * d.n_tunnels),
        "fan_kw": fan_kw,
        "fan_kw_per_tunnel": fan_kw / d.n_tunnels,
        "blower_kw_each": fan_kw * d.blower_peak_factor / d.n_tunnels,
        "blower_m3_h_each": v_air * d.blower_peak_factor / d.n_tunnels,
        "enthalpy_drop_kj_kg": dh,
        "latent_share": 1.0 - sensible_share,
        "condensate_m3_h": condensate * 3.6,
        "hx_area_m2": hx_area,
        "peak_duty_kw": duty_kw * d.peak_to_mean,
        "buffer_m3": d.buffer_m3,
        "biofilter_m2": v_air * d.peak_to_mean / d.biofilter_loading_m3_m2_h,
        "water_kg_s": m_water,
        "water_m3_h": m_water * 3.6,
        "pinch_k": pinch_k(d, m_dry_air, m_water),
        "heat_gwh_per_year": heat.heat_kwh / 1e6,
        "t_exhaust_c": d.t_exhaust_c,
        "t_air_out_c": d.t_air_out_c,
        "t_supply_c": d.t_supply_c,
        "t_return_c": d.t_return_c,
        "fan_pressure_pa": d.fan_pressure_pa,
    }





# ---- buildable layout -----------------------------------------------------

@dataclass(frozen=True)
class Layout:
    """Rounded, buildable geometry shared by the drawings and the CAD model.

    Metres. x runs across the tunnels, y along them (doors at y = length),
    z up from the ground. Boxes are (x0, x1, y0, y1, z0, z1).
    """
    wall_m: float = 0.30            # 200 concrete + 100 PIR
    slab_m: float = 0.30            # plenum slab under the spigot floor
    door_w_m: float = 4.5
    door_h_m: float = 3.6
    spigot_pitch_m: float = 0.5
    exhaust_y_m: float = 1.2        # exhaust stubs sit near the back wall
    manifold_rise_m: float = 0.9    # manifold height above the roof
    # Equipment boxes, x measured from the outer face of the last tunnel wall.
    hx: tuple = (2.4, 5.2, 0.2, 4.2, 0.0, 3.4)
    fan: tuple = (5.7, 6.9, 1.4, 2.8, 0.0, 1.6)
    tank: tuple = (5.6, 6.6, 3.4, 4.4, 0.0, 0.9)     # TK-401 condensate
    buffer: tuple = (8.6, -2.6, 5.5)       # TK-201 hot-water buffer: centre x, centre y, diameter (set from volume)
    buffer_h_m: float = 5.6
    biofilter: tuple = (2.8, 9.8, 6.5, 14.5, 0.0, 1.6)


def layout(d: IndustrialDesign = IndustrialDesign(), lay: Layout = Layout()) -> dict:
    m = size(d)
    length = math.ceil(m["tunnel_length_m"] * 2) / 2           # next 0.5 m
    bays = [lay.wall_m + i * (d.tunnel_width_m + lay.wall_m) for i in range(d.n_tunnels)]
    x_end = lay.wall_m + d.n_tunnels * (d.tunnel_width_m + lay.wall_m)

    def shift(b):
        return (b[0] + x_end, b[1] + x_end, *b[2:])

    lay = replace(lay, hx=shift(lay.hx), fan=shift(lay.fan), tank=shift(lay.tank), biofilter=shift(lay.biofilter),
                  buffer=(lay.buffer[0] + x_end, *lay.buffer[1:]))
    # buffer tank diameter from its volume and height
    dia = math.sqrt(4 * d.buffer_m3 / (math.pi * lay.buffer_h_m))
    lay = replace(lay, buffer=(lay.buffer[0], lay.buffer[1], round(dia, 1)))
    return {
        "length_m": length,
        "width_m": d.tunnel_width_m,
        "height_m": d.tunnel_height_m,
        "overall_x_m": x_end,
        "bay_x_m": bays,
        "roof_z_m": lay.slab_m + d.tunnel_height_m + lay.wall_m,
        "biofilter_m2": (lay.biofilter[1] - lay.biofilter[0]) * (lay.biofilter[3] - lay.biofilter[2]),
        "layout": lay,
    }


# ---- operating modes ------------------------------------------------------

@dataclass(frozen=True)
class Handling:
    """Assumptions for moving material with a wheel loader."""
    # fraction of fresh mass left after the 15 days in the tunnels (water + CO2 lost)
    mass_left_day15: float = 0.7
    diesel_l_per_t: float = 0.25        # one load-carry-tip cycle over a short distance
    loader_t_per_h: float = 120.0
    diesel_eur_per_l: float = 1.6
    operator_eur_per_h: float = 45.0
    # a hot batch moved between tunnels sits in the open for about two hours
    transfer_drop_k: float = 10.0
    cp_compost_kj_kgk: float = 2.5


def operating_modes(d: IndustrialDesign = IndustrialDesign(), h: Handling = Handling()) -> dict:
    """Compare two ways of taking a batch through the three phases.

    A, staggered: each tunnel runs the whole 15-day cycle in place and the
    phases change by changing the air. Tunnels start 15/N days apart, so every
    15/N days one is emptied and refilled.

    B, transfer: each tunnel holds one stage for 15/N days, and at each step
    the loader moves every batch one tunnel along before refilling T-101.

    configurations.py extends this comparison to 2-4 tunnels, automatic
    transfer and a stacked tower, with capital costs.
    """
    m = size(d)
    stage = 15 / d.n_tunnels                     # days per tunnel or per phase
    fresh_t = m["feedstock_t_per_day"] * stage   # one batch
    floor = d.tunnel_width_m * m["tunnel_length_m"]
    fresh_m3 = farm_sizing()["feedstock_m3_per_day"] * stage
    retention_15 = 0.95 ** 15

    def mass(day: float) -> float:
        return fresh_t * h.mass_left_day15 ** (day / 15)

    base_t = fresh_t + mass(15)                              # fill + empty
    transfer_t = sum(mass(stage * k) for k in range(1, d.n_tunnels))
    released_kwh = transfer_t * 1000 * h.cp_compost_kj_kgk * h.transfer_drop_k / 3600

    def costs(tonnes_per_batch: float) -> dict:
        t_day = tonnes_per_batch / stage
        hours = t_day / h.loader_t_per_h
        diesel = t_day * h.diesel_l_per_t
        eur = 365 * (diesel * h.diesel_eur_per_l + hours * h.operator_eur_per_h)
        return {"t_per_day": t_day, "loader_h_per_day": hours, "diesel_l_per_day": diesel,
                "handling_eur_per_year": eur}

    a = costs(base_t)
    b = costs(base_t + transfer_t)
    farm = evaluate(FARM)
    # Heat released while a batch is out of a tunnel, valued as gas not burnt.
    # An upper bound: not all of it would have reached the exchanger.
    released_kw = released_kwh / (stage * 24)
    lost_eur = released_kw * d.heating_hours * FARM.fuel_price_eur_per_kwh / FARM.boiler_efficiency
    # Routine filling and emptying is inside the farm scenario's fixed opex,
    # so A keeps the scenario's net value and B pays for its extra moves.
    a["net_eur"] = farm.net_eur
    b["net_eur"] = farm.net_eur - (b["handling_eur_per_year"] - a["handling_eur_per_year"]) - lost_eur
    a["hot_transfers_per_batch"], b["hot_transfers_per_batch"] = 0, d.n_tunnels - 1
    a["released_kw"], b["released_kw"] = 0.0, released_kw
    return {
        "stage_days": stage,
        "batch_t": fresh_t,
        "batch_m3": fresh_m3,
        "fill_depth_m": fresh_m3 / floor,
        "settled_depth_m": fresh_m3 * retention_15 / floor,
        "transfer_released_share": released_kw / m["duty_kw"],
        "transfer_lost_eur": lost_eur,
        "staggered": a,
        "transfer": b,
    }


if __name__ == "__main__":
    for k, v in size().items():
        print(f"{k:26s} {v:,.3f}" if isinstance(v, float) else f"{k:26s} {v}")
    for k, v in operating_modes().items():
        print(k, v)
