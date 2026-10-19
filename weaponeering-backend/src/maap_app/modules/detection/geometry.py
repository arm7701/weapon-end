from __future__ import annotations

import math


def square_building_polygon(
    lat: float,
    lng: float,
    *,
    half_size_m: float = 12.0,
) -> list[list[float]]:
    """Approximate building footprint as a lat/lng square around a center point."""
    lat_m = 111_320.0
    lng_m = 111_320.0 * max(math.cos(math.radians(lat)), 0.1)
    dlat = half_size_m / lat_m
    dlng = half_size_m / lng_m
    return [
        [lat + dlat, lng - dlng],
        [lat + dlat, lng + dlng],
        [lat - dlat, lng + dlng],
        [lat - dlat, lng - dlng],
    ]
