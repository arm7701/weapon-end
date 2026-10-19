from __future__ import annotations

DEFAULT_GROUND_SPEED_KMH = 55.0
MIN_GROUND_SPEED_KMH = 20.0
MAX_GROUND_SPEED_KMH = 120.0

OSRM_BASE_URL = "https://router.project-osrm.org"
OSRM_FALLBACK_URLS: tuple[str, ...] = (
    "https://router.project-osrm.org",
    "https://routing.openstreetmap.de/routed-car",
)
OSRM_PROFILE = "driving"
OSRM_TIMEOUT_SEC = 20.0
OSRM_MIN_PATH_POINTS = 3
