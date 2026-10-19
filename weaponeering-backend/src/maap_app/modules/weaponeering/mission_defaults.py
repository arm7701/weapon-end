from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimFlightDefaults:
    """Default mission profile for realistic fly-through training simulation."""

    mission_id: str = "SIM-FLIGHT-REALISTIC-001"
    takeoff_lat: float = 14.93444
    takeoff_lng: float = 102.07861
    takeoff_alt_ft: int = 0
    cruise_altitude_ft: int = 25000
    ingress_altitude_ft: int = 2000
    fly_through_altitude_ft: int = 2000
    climb_rate_ft_min: int = 3000
    descent_rate_ft_min: int = 2000
    climb_speed_kt: float = 250.0
    cruise_speed_kt: float = 420.0
    descent_speed_kt: float = 300.0
    ingress_speed_kt: float = 250.0
    exit_speed_kt: float = 250.0
    turn_mode: str = "fly_by"
    cruise_bank_deg: float = 20.0
    ingress_bank_deg: float = 25.0
    exit_bank_deg: float = 25.0
    max_bank_deg: float = 30.0
    sample_distance_m: float = 250.0
    smooth_polyline: bool = True
    auto_toc_tod: bool = True
    ingress_enabled: bool = True
    ingress_heading_deg: int = 167
    ingress_distance_m: int = 30000
    objective_name: str = "WP-FLYTHROUGH-01"
    objective_lat: float = 16.81230
    objective_lng: float = 100.0
    objective_speed_kt: float = 250.0
    exit_enabled: bool = True
    exit_heading_deg: int = 167
    exit_distance_m: int = 20000
    rtb_enabled: bool = True
    rtb_name: str = "RTB-BASE"
    rtb_lat: float = 14.93444
    rtb_lng: float = 102.07861
    rtb_alt_ft: int = 0


SIM_FLIGHT_DEFAULTS = SimFlightDefaults()
