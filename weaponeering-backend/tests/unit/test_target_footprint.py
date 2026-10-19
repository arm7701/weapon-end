import math

from maap_app.modules.target.footprint import target_footprint

_M_PER_DEG_LAT = 6378137.0 * math.pi / 180.0


def _local_m(lat0: float, lng0: float, lat: float, lng: float) -> tuple[float, float]:
    east = (lng - lng0) * _M_PER_DEG_LAT * math.cos(math.radians(lat0))
    north = (lat - lat0) * _M_PER_DEG_LAT
    return east, north


def _edge(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def test_footprint_requires_position_and_size() -> None:
    assert target_footprint(None, 100.0, 60.0, 40.0) is None
    assert target_footprint(13.7, 100.5, None, 40.0) is None
    assert target_footprint(13.7, 100.5, 60.0, 0.0) is None


def test_north_aligned_footprint_matches_real_size() -> None:
    lat0, lng0 = 13.7563, 100.5018
    fp = target_footprint(lat0, lng0, 60.0, 40.0)
    assert fp is not None
    assert len(fp.polygon) == 4
    pts = [_local_m(lat0, lng0, lat, lng) for lat, lng in fp.polygon]
    norths = [p[1] for p in pts]
    easts = [p[0] for p in pts]
    assert math.isclose(max(norths) - min(norths), 60.0, abs_tol=0.05)
    assert math.isclose(max(easts) - min(easts), 40.0, abs_tol=0.05)
    assert math.isclose(sum(norths) / 4, 0.0, abs_tol=1e-6)
    assert math.isclose(sum(easts) / 4, 0.0, abs_tol=1e-6)
    assert fp.area_m2 == 2400.0
    assert fp.height_m is None


def test_heading_rotates_length_axis_clockwise_from_north() -> None:
    lat0, lng0 = 13.7563, 100.5018
    fp = target_footprint(lat0, lng0, 100.0, 20.0, heading_deg=90.0, height_m=12.0)
    assert fp is not None
    pts = [_local_m(lat0, lng0, lat, lng) for lat, lng in fp.polygon]
    easts = [p[0] for p in pts]
    norths = [p[1] for p in pts]
    assert math.isclose(max(easts) - min(easts), 100.0, abs_tol=0.05)
    assert math.isclose(max(norths) - min(norths), 20.0, abs_tol=0.05)
    assert fp.height_m == 12.0

    diagonal = target_footprint(lat0, lng0, 100.0, 20.0, heading_deg=45.0)
    assert diagonal is not None
    d = [_local_m(lat0, lng0, lat, lng) for lat, lng in diagonal.polygon]
    sides = sorted(_edge(d[i], d[(i + 1) % 4]) for i in range(4))
    assert math.isclose(sides[0], 20.0, abs_tol=0.05)
    assert math.isclose(sides[-1], 100.0, abs_tol=0.05)


def test_footprint_payload_shape() -> None:
    fp = target_footprint(13.7, 100.5, 60.0, 40.0, heading_deg=370.0, height_m=15.0)
    assert fp is not None
    payload = fp.to_payload()
    assert payload["headingDeg"] == 10.0
    assert payload["lengthM"] == 60.0
    assert payload["widthM"] == 40.0
    assert payload["heightM"] == 15.0
    assert payload["areaM2"] == 2400.0
    assert len(payload["polygon"]) == 4
    assert all(len(corner) == 2 for corner in payload["polygon"])
