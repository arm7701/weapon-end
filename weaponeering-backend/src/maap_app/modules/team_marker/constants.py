from __future__ import annotations

UNIT_TYPES: dict[str, str] = {
    "generic": "ทั่วไป",
    "radar": "เรดาร์",
    "tank": "รถถัง",
    "small_arms": "ปืนเล็ก",
    "artillery": "ปืนใหญ่",
    "anti_air": "ปืนต่อสู้อากาศยาน",
}

UNIT_TYPE_PREFIXES: dict[str, str] = {
    "generic": "",
    "radar": "RADAR",
    "tank": "TANK",
    "small_arms": "SA",
    "artillery": "ARTY",
    "anti_air": "AA",
}

VALID_UNIT_TYPES = frozenset(UNIT_TYPES)

DEFAULT_RADAR_RADIUS_M = 25_000.0
MIN_RADAR_RADIUS_M = 100.0
MAX_RADAR_RADIUS_M = 500_000.0
