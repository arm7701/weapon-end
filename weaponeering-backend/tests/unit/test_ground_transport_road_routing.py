from __future__ import annotations

from unittest.mock import patch

from maap_app.modules.ground_transport.models import GroundRouteResult
from maap_app.modules.ground_transport.road_routing import (
    estimate_direct_route,
    fetch_road_route,
    resolve_ground_route,
)


def test_fetch_road_route_parses_osrm_response() -> None:
    payload = {
        "code": "Ok",
        "routes": [
            {
                "distance": 12500.0,
                "duration": 1800.0,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [100.5, 13.75],
                        [100.6, 13.8],
                        [100.8, 14.1],
                    ],
                },
            }
        ],
    }

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            import json

            return json.dumps(payload).encode("utf-8")

    with patch(
        "maap_app.modules.ground_transport.road_routing.urllib.request.urlopen",
        return_value=_FakeResponse(),
    ):
        result = fetch_road_route(13.75, 100.5, 14.1, 100.8)

    assert result is not None
    assert result.route_mode == "road"
    assert result.distance_m == 12500.0
    assert result.duration_min == 30.0
    assert len(result.path) == 3
    assert result.path[0] == (13.75, 100.5)


def test_resolve_ground_route_falls_back_to_direct() -> None:
    with patch(
        "maap_app.modules.ground_transport.road_routing.fetch_road_route",
        return_value=None,
    ):
        result = resolve_ground_route(13.75, 100.5, 14.1, 100.8)

    direct = estimate_direct_route(13.75, 100.5, 14.1, 100.8)
    assert result.route_mode == "direct"
    assert result.distance_m == direct.distance_m
    assert len(result.path) == 2
