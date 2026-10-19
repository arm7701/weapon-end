from __future__ import annotations

import math
from dataclasses import dataclass

_EARTH_RADIUS_M = 6378137.0


@dataclass(frozen=True)
class TargetFootprint:
    polygon: tuple[tuple[float, float], ...]
    length_m: float
    width_m: float
    height_m: float | None
    heading_deg: float

    @property
    def area_m2(self) -> float:
        return self.length_m * self.width_m

    def to_payload(self) -> dict:
        return {
            "polygon": [[lat, lng] for lat, lng in self.polygon],
            "lengthM": self.length_m,
            "widthM": self.width_m,
            "heightM": self.height_m,
            "headingDeg": self.heading_deg,
            "areaM2": self.area_m2,
        }


def _offset_degrees(lat: float, lng: float, east_m: float, north_m: float) -> tuple[float, float]:
    d_lat = math.degrees(north_m / _EARTH_RADIUS_M)
    cos_lat = max(math.cos(math.radians(lat)), 1e-6)
    d_lng = math.degrees(east_m / (_EARTH_RADIUS_M * cos_lat))
    return lat + d_lat, lng + d_lng


def target_footprint(
    lat: float | None,
    lng: float | None,
    length_m: float | None,
    width_m: float | None,
    heading_deg: float | None = None,
    height_m: float | None = None,
) -> TargetFootprint | None:
    """Rectangle centred on the aim point; the length axis points along heading (clockwise from north)."""
    if lat is None or lng is None:
        return None
    if not length_m or not width_m or length_m <= 0 or width_m <= 0:
        return None
    heading = float(heading_deg or 0.0) % 360.0
    theta = math.radians(heading)
    half_l = float(length_m) / 2.0
    half_w = float(width_m) / 2.0
    length_axis = (math.sin(theta), math.cos(theta))
    width_axis = (math.cos(theta), -math.sin(theta))
    corners: list[tuple[float, float]] = []
    for sl, sw in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
        east = sl * half_l * length_axis[0] + sw * half_w * width_axis[0]
        north = sl * half_l * length_axis[1] + sw * half_w * width_axis[1]
        corners.append(_offset_degrees(float(lat), float(lng), east, north))
    height = float(height_m) if height_m is not None and height_m > 0 else None
    return TargetFootprint(
        polygon=tuple(corners),
        length_m=float(length_m),
        width_m=float(width_m),
        height_m=height,
        heading_deg=heading,
    )
