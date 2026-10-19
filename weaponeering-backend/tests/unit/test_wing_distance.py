from __future__ import annotations

from maap_app.modules.geo_utils import haversine_distance_km, km_to_nm


def test_haversine_same_point_is_zero() -> None:
    assert haversine_distance_km(13.75, 100.5, 13.75, 100.5) == 0.0


def test_haversine_known_short_distance() -> None:
    # ~1 degree latitude ≈ 111 km
    distance = haversine_distance_km(13.0, 100.0, 14.0, 100.0)
    assert 110 < distance < 112


def test_km_to_nm_conversion() -> None:
    assert abs(km_to_nm(100) - 53.9957) < 0.01
