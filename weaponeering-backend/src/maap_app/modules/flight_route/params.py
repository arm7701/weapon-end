from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RouteStyle(str, Enum):
    LOW_LEVEL = "low_level"
    CRUISE = "cruise"
    VALLEY = "valley"
    HYBRID = "hybrid"


MIN_FLIGHT_ALTITUDE_FT = 500
MAX_FLIGHT_ALTITUDE_FT = 100_000


@dataclass
class AiRoutePlannerParams:
    route_style: RouteStyle = RouteStyle.LOW_LEVEL
    min_agl_m: int = 80
    pref_agl_m: int = 105
    max_agl_m: int = 120
    cruise_pad_m: int = 105
    grid_m: int = 80
    cruise_kts: int = 250
    turn_radius_m: int = 800
    border_standoff_m: int = 22_000
    border_step_m: int = 12_000
    cruise_altitude_ft: int = 25_000
