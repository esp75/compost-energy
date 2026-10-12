"""Heat exchanger buried in the compost core.

Series thermal resistances per unit area (thin wall, so the planar form is
fine):

    1/U = 1/h_compost + wall/k_wall + 1/h_water

The original 2024 design calculation used h_compost = 1512.5 W/m2K, which is
the order of magnitude of a *liquid* in forced convection. Compost is a moist
porous solid with little bulk motion: heat reaches the pipe mostly by
conduction (k ~ 0.2-0.7 W/mK) plus slow vapour/air transport, giving an
effective film coefficient of roughly 5-30 W/m2K. That one assumption moves
the answer from kilowatts to tens of watts, and makes the compost side, not
the metal or the water, the limiting resistance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

K_ALUMINIUM = 237.0  # W/mK


@dataclass(frozen=True)
class PipeExchanger:
    outer_diameter_m: float = 0.019
    length_m: float = 3.0
    wall_m: float = 0.003
    k_wall: float = K_ALUMINIUM
    h_compost: float = 15.0  # W/m2K, realistic mid-range
    h_water: float = 3000.0  # W/m2K, flowing water in a small tube

    @property
    def area_m2(self) -> float:
        return math.pi * self.outer_diameter_m * self.length_m

    @property
    def u_value(self) -> float:
        return 1.0 / (1.0 / self.h_compost + self.wall_m / self.k_wall + 1.0 / self.h_water)

    @property
    def ua(self) -> float:
        return self.u_value * self.area_m2

    def power_w(self, t_compost_c: float, t_water_c: float) -> float:
        """Heat flow for a constant temperature difference (the 2024 method)."""
        return self.ua * (t_compost_c - t_water_c)

    def outlet_temperature(self, t_compost_c: float, t_in_c: float, flow_l_min: float) -> float:
        """Outlet water temperature with the effectiveness-NTU method.

        The compost core is treated as an isothermal reservoir (it changes
        over days; water crosses the pipe in seconds).
        """
        if flow_l_min <= 0:
            return t_compost_c
        m_cp = flow_l_min / 60.0 * 4186.0  # W/K, water at ~1 kg/L
        ntu = self.ua / m_cp
        return t_compost_c - (t_compost_c - t_in_c) * math.exp(-ntu)


# The design point from the 2024 spreadsheet, reproduced exactly.
ORIGINAL_2024 = PipeExchanger(h_compost=1512.5)


def sensitivity(h_values, t_compost_c: float = 60.0, t_water_c: float = 40.0, **kw):
    """Exchanger power over a range of compost-side film coefficients."""
    return [(h, PipeExchanger(h_compost=h, **kw).power_w(t_compost_c, t_water_c)) for h in h_values]
