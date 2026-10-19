from __future__ import annotations

from maap_app.modules.ground_transport.road_routing import resolve_ground_route


def estimate_ground_route(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    *,
    speed_kmh: float | None = None,
):
    kwargs = {}
    if speed_kmh is not None:
        kwargs["speed_kmh"] = speed_kmh
    result = resolve_ground_route(
        origin_lat,
        origin_lng,
        destination_lat,
        destination_lng,
        **kwargs,
    )
    return result.distance_m, result.duration_min


def format_distance_m(distance_m: float) -> str:
    if distance_m >= 1000:
        return f"{distance_m / 1000:.1f} km"
    return f"{distance_m:.0f} m"


def format_duration_min(duration_min: float) -> str:
    total = max(int(round(duration_min)), 0)
    if total < 60:
        return f"{total} นาที"
    hours = total // 60
    minutes = total % 60
    if minutes == 0:
        return f"{hours} ชม."
    return f"{hours} ชม. {minutes} นาที"
