from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from maap_app.modules.ground_transport.constants import (
    DEFAULT_GROUND_SPEED_KMH,
    OSRM_FALLBACK_URLS,
    OSRM_PROFILE,
    OSRM_TIMEOUT_SEC,
)
from maap_app.modules.ground_transport.models import GroundRouteResult
from maap_app.modules.weaponeering.flight_path import distance_m


def fetch_road_route(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    *,
    base_urls: tuple[str, ...] = OSRM_FALLBACK_URLS,
    timeout_sec: float = OSRM_TIMEOUT_SEC,
) -> GroundRouteResult | None:
    for base_url in base_urls:
        result = _fetch_road_route_from_server(
            origin_lat,
            origin_lng,
            destination_lat,
            destination_lng,
            base_url=base_url,
            timeout_sec=timeout_sec,
        )
        if result is not None:
            return result
    return None


def _fetch_road_route_from_server(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    *,
    base_url: str,
    timeout_sec: float,
) -> GroundRouteResult | None:
    coordinates = f"{origin_lng},{origin_lat};{destination_lng},{destination_lat}"
    query = urllib.parse.urlencode(
        {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        }
    )
    url = (
        f"{base_url.rstrip('/')}/route/v1/{OSRM_PROFILE}/"
        f"{coordinates}?{query}"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "MAAP-Wargame/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ):
        return None

    if payload.get("code") != "Ok":
        return None
    routes = payload.get("routes") or []
    if not routes:
        return None
    route = routes[0]
    geometry = route.get("geometry") or {}
    coordinates_list = geometry.get("coordinates") or []
    path: list[tuple[float, float]] = []
    for point in coordinates_list:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        lng = float(point[0])
        lat = float(point[1])
        path.append((lat, lng))
    if len(path) < 2:
        return None

    distance_m_value = float(route.get("distance") or 0)
    duration_sec = float(route.get("duration") or 0)
    if distance_m_value <= 0 or duration_sec <= 0:
        return None

    return GroundRouteResult(
        distance_m=distance_m_value,
        duration_min=duration_sec / 60.0,
        path=tuple(path),
        route_mode="road",
    )


def estimate_direct_route(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    *,
    speed_kmh: float = DEFAULT_GROUND_SPEED_KMH,
) -> GroundRouteResult:
    route_distance_m = distance_m(origin_lat, origin_lng, destination_lat, destination_lng)
    safe_speed = max(speed_kmh, 1.0)
    duration_min = (route_distance_m / 1000.0) / safe_speed * 60.0
    return GroundRouteResult(
        distance_m=route_distance_m,
        duration_min=duration_min,
        path=((origin_lat, origin_lng), (destination_lat, destination_lng)),
        route_mode="direct",
    )


def resolve_ground_route(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    *,
    speed_kmh: float = DEFAULT_GROUND_SPEED_KMH,
) -> GroundRouteResult:
    road_route = fetch_road_route(
        origin_lat,
        origin_lng,
        destination_lat,
        destination_lng,
    )
    if road_route is not None:
        return road_route
    return estimate_direct_route(
        origin_lat,
        origin_lng,
        destination_lat,
        destination_lng,
        speed_kmh=speed_kmh,
    )
