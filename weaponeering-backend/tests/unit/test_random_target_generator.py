from __future__ import annotations

from maap_app.modules.target.constants import (
    DESIRED_MODEL_RESULTS,
    MATERIAL_CLASS_OPTIONS,
    TARGET_TYPES,
    subtypes_for_target_type,
)
from maap_app.modules.target.random_generator import generate_random_target


def test_label_increments_from_existing_count() -> None:
    suggestion = generate_random_target(existing_count=5)
    assert suggestion.label == "TGT-006"


def test_label_starts_at_one_when_no_targets_exist() -> None:
    suggestion = generate_random_target(existing_count=0)
    assert suggestion.label == "TGT-001"


def test_scores_are_in_valid_range() -> None:
    for _ in range(50):
        suggestion = generate_random_target(existing_count=0)
        assert 1 <= suggestion.priority_score <= 5
        assert 1 <= suggestion.complexity_score <= 5


def test_profile_uses_valid_option_values() -> None:
    for _ in range(50):
        suggestion = generate_random_target(existing_count=0)
        profile = suggestion.profile
        assert profile.target_type in TARGET_TYPES
        assert profile.target_subtype in subtypes_for_target_type(profile.target_type)
        assert profile.material_class in MATERIAL_CLASS_OPTIONS
        assert profile.desired_model_result in DESIRED_MODEL_RESULTS
        assert profile.floor_count in {
            "1", "2", "3", "4", "5", "6", "8", "10", "UNK",
        }


def test_dimensions_are_in_plausible_ranges() -> None:
    for _ in range(50):
        suggestion = generate_random_target(existing_count=0)
        profile = suggestion.profile
        assert 5 <= profile.width_m <= 80
        assert 5 <= profile.length_m <= 120
        assert 3 <= profile.height_m <= 60


def test_coordinates_are_within_expected_box() -> None:
    for _ in range(50):
        suggestion = generate_random_target(existing_count=0)
        assert 16.8123 - 0.7 <= suggestion.map_lat <= 16.8123 + 0.7
        assert 100.1234 - 0.8 <= suggestion.map_lng <= 100.1234 + 0.8


def test_description_contains_auto_generated_note() -> None:
    suggestion = generate_random_target(existing_count=0)
    assert "สร้างอัตโนมัติ" in suggestion.profile.target_description


def test_other_profile_fields_stay_at_defaults() -> None:
    suggestion = generate_random_target(existing_count=0)
    profile = suggestion.profile
    assert profile.data_source == "manual"
    assert profile.cep is None
    assert profile.target_pk is None
    assert profile.reference_pk is None
    assert profile.resistance == ""
    assert profile.capacity == ""
    assert profile.damage_fit == ""
    assert profile.model_version == ""
    assert profile.selected_product_id is None
