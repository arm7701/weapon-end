from __future__ import annotations

import random
from dataclasses import dataclass

from maap_app.modules.target.constants import (
    DESIRED_MODEL_RESULTS,
    MATERIAL_CLASS_OPTIONS,
    TARGET_TYPES,
    subtypes_for_target_type,
)
from maap_app.modules.target.profile_fields import TargetProfileFields

_BASE_LAT = 16.8123
_BASE_LNG = 100.1234
_FLOOR_COUNT_OPTIONS = ("1", "2", "3", "4", "5", "6", "8", "10", "UNK")
_AUTO_GENERATED_NOTE = (
    "สร้างอัตโนมัติสำหรับทดสอบ/สอน — กรุณาตรวจสอบและแก้ไขก่อนบันทึก"
)


@dataclass(frozen=True)
class RandomTargetSuggestion:
    label: str
    priority_score: int
    complexity_score: int
    profile: TargetProfileFields
    map_lat: float
    map_lng: float


def generate_random_target(existing_count: int) -> RandomTargetSuggestion:
    target_type = random.choice(TARGET_TYPES)
    target_subtype = random.choice(subtypes_for_target_type(target_type))
    profile = TargetProfileFields(
        target_type=target_type,
        target_subtype=target_subtype,
        material_class=random.choice(MATERIAL_CLASS_OPTIONS),
        target_description=_AUTO_GENERATED_NOTE,
        floor_count=random.choice(_FLOOR_COUNT_OPTIONS),
        width_m=random.uniform(5, 80),
        length_m=random.uniform(5, 120),
        height_m=random.uniform(3, 60),
        desired_model_result=random.choice(DESIRED_MODEL_RESULTS),
    )
    return RandomTargetSuggestion(
        label=f"TGT-{existing_count + 1:03d}",
        priority_score=random.randint(1, 5),
        complexity_score=random.randint(1, 5),
        profile=profile,
        map_lat=_BASE_LAT + random.uniform(-0.7, 0.7),
        map_lng=_BASE_LNG + random.uniform(-0.8, 0.8),
    )
