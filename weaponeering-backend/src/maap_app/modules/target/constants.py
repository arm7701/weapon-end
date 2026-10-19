from __future__ import annotations

TARGET_TYPES = (
    "BUILDING",
    "BUNKER",
    "CONCRETE STRUCTURE",
    "HANGAR",
    "SPECIAL STRUCTURE",
    "TANK",
    "AIR DEFENSE",
)

SUBTYPES_BY_TARGET_TYPE: dict[str, tuple[str, ...]] = {
    "BUILDING": ("MULTI-STORY BUILDING", "WAREHOUSE", "COMMAND CENTER"),
    "TANK": ("MAIN BATTLE TANK", "IFV / APC", "ARMORED SAM"),
    "AIR DEFENSE": ("RADAR SITE", "SAM BATTERY", "C2 NODE"),
    "BUNKER": ("HARDENED BUNKER", "UNDERGROUND FACILITY", "COMMAND BUNKER"),
    "CONCRETE STRUCTURE": (
        "REINFORCED CONCRETE",
        "CONCRETE SLAB",
        "MIXED CONCRETE STRUCTURE",
    ),
    "HANGAR": ("AIRCRAFT HANGAR", "MAINTENANCE HANGAR", "STORAGE HANGAR"),
    "SPECIAL STRUCTURE": (
        "SPECIFIC FACILITY",
        "MIXED STRUCTURE",
        "UNKNOWN SPECIAL STRUCTURE",
    ),
}

MATERIAL_CLASS_OPTIONS = (
    "UNKNOWN",
    "REINFORCED CONCRETE",
    "STEEL",
    "EARTH",
    "CONCRETE",
    "MIXED",
)

DESIRED_MODEL_RESULTS = (
    "STRUCTURAL FAILURE",
    "FUNCTIONAL KILL",
    "SUPPRESSION",
    "NEUTRALIZATION",
)

DATA_SOURCE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("กรอกเอง", "manual"),
    ("นำเข้า", "import"),
    ("AI", "ai"),
)


def subtypes_for_target_type(target_type: str) -> list[str]:
    return list(SUBTYPES_BY_TARGET_TYPE.get(target_type, ("GENERIC TARGET",)))
