"""Annual energy balance of compost heat recovery at three scales.

Each scenario answers one question: once you subtract the electricity the
system itself needs (fans, pumps, controls, conveyors), how much fossil
heating does the recovered compost heat actually displace, and is it worth
anything?

All energies are kWh, powers W, money EUR.
"""

from __future__ import annotations

from dataclasses import dataclass, field

HOURS_PER_YEAR = 8760.0


@dataclass(frozen=True)
class Scenario:
    name: str
    waste_kg_per_year: float
    # Heat actually recoverable per kg of wet feedstock. Literature on
    # compost heat recovery spans ~0.3-1.4 kWh/kg for food/green waste and
    # ~0.13-0.24 kWh/kg for manure.
    kwh_per_kg: float
    # Fraction of the year's waste that can be stored and used while there
    # is a heat demand (1.0 = perfect storage, no seasonal mismatch).
    usable_fraction: float = 1.0
    # Average electrical draw of the auxiliaries and the hours it runs.
    aux_power_w: float = 0.0
    aux_hours: float = HOURS_PER_YEAR
    # What the recovered heat displaces.
    boiler_efficiency: float = 0.9
    fuel_price_eur_per_kwh: float = 0.12
    electricity_price_eur_per_kwh: float = 0.20
    fixed_opex_eur: float = 0.0
    notes: str = ""


@dataclass(frozen=True)
class Result:
    scenario: Scenario
    heat_kwh: float
    mean_power_w: float
    aux_kwh: float
    fuel_saved_kwh: float
    fuel_saved_eur: float
    aux_cost_eur: float
    net_eur: float
    extra: dict = field(default_factory=dict)


def evaluate(s: Scenario) -> Result:
    heat = s.waste_kg_per_year * s.usable_fraction * s.kwh_per_kg
    aux = s.aux_power_w * s.aux_hours / 1000.0
    fuel_saved = heat / s.boiler_efficiency
    fuel_eur = fuel_saved * s.fuel_price_eur_per_kwh
    aux_eur = aux * s.electricity_price_eur_per_kwh
    return Result(
        scenario=s,
        heat_kwh=heat,
        mean_power_w=heat * 1000.0 / HOURS_PER_YEAR,
        aux_kwh=aux,
        fuel_saved_kwh=fuel_saved,
        fuel_saved_eur=fuel_eur,
        aux_cost_eur=aux_eur,
        net_eur=fuel_eur - aux_eur - s.fixed_opex_eur,
    )


WASTE_KG_PER_PERSON = 130.0  # household food waste, kg/person/year

HOUSE_IDEAL = Scenario(
    "House, 4 people (ideal)",
    waste_kg_per_year=4 * WASTE_KG_PER_PERSON,
    kwh_per_kg=1.0,
    notes="perfect storage, no auxiliaries, high conversion",
)
HOUSE_REALISTIC = Scenario(
    "House, 4 people (realistic)",
    waste_kg_per_year=4 * WASTE_KG_PER_PERSON,
    kwh_per_kg=0.7,
    aux_power_w=50.0,
    notes="moderate conversion, 50 W of fan/pump/controls",
)
BUILDING_IDEAL = Scenario(
    "Apartment block, 48 people (ideal)",
    waste_kg_per_year=48 * WASTE_KG_PER_PERSON,
    kwh_per_kg=1.0,
    boiler_efficiency=0.95,
)
BUILDING_REALISTIC = Scenario(
    "Apartment block, 48 people (realistic)",
    waste_kg_per_year=48 * WASTE_KG_PER_PERSON,
    kwh_per_kg=0.7,
    aux_power_w=200.0,
    boiler_efficiency=0.95,
)
FARM = Scenario(
    "Farm cooperative, 14,279 t/yr",
    # Mixed manure, slurry, silage and straw from a mid-size farm cooperative.
    waste_kg_per_year=14_279_000.0,
    kwh_per_kg=0.24,
    # Heat only sells in the heating season: 5 months of use, fed by
    # 7 months of feedstock (2 months stockpiled before winter).
    usable_fraction=7 / 12,
    aux_power_w=10_000.0,  # conveying ~5 kW + aeration/heating 3-5 kW
    aux_hours=5 * 730.0,
    boiler_efficiency=0.9,
    fixed_opex_eur=100_000.0,
    notes="heat must be used in a short loop (greenhouse, dryer, district heating)",
)

SCENARIOS = [HOUSE_IDEAL, HOUSE_REALISTIC, BUILDING_IDEAL, BUILDING_REALISTIC, FARM]


def farm_sizing(
    feedstock_t_per_year: float = 14_279.0,
    density_t_per_m3: float = 0.85,
    precompost_days: int = 15,
    daily_volume_retention: float = 0.95,
    maturation_weeks: int = 8,
    storage_months: int = 7,
) -> dict:
    """First-pass volumes for a farm-scale plant.

    Feedstock moves through three enclosed reactors (mesophilic, thermophilic
    with heat extraction, mesophilic) over ``precompost_days``, losing volume
    every day, then matures in windrows and is stored until spreading season.
    """
    daily_t = feedstock_t_per_year / 365.0
    daily_m3 = daily_t / density_t_per_m3
    # Material inside the reactors at any moment: sum of a geometric series.
    precompost_m3 = daily_m3 * sum(daily_volume_retention**d for d in range(precompost_days))
    leaving_m3_per_day = daily_m3 * daily_volume_retention**precompost_days
    maturation_m3 = leaving_m3_per_day * maturation_weeks * 7
    return {
        "feedstock_t_per_day": daily_t,
        "feedstock_m3_per_day": daily_m3,
        "precompost_solids_m3": precompost_m3,
        "reactor_volume_m3": 2 * precompost_m3,  # 50% headspace for mixing + air
        "precompost_out_m3_per_day": leaving_m3_per_day,
        "maturation_m3": maturation_m3,
        "maturation_area_m2_at_1m": maturation_m3,  # keep windrows <= 1 m deep
        # Upper bound: ignores further shrinkage during maturation.
        "storage_m3": leaving_m3_per_day * storage_months * 30,
    }


def payback_capex(result: Result, years: float = 10.0) -> float:
    """Capex the net annual saving can repay over ``years`` (no discounting)."""
    return max(result.net_eur, 0.0) * years
