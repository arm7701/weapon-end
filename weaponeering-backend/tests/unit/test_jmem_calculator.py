from __future__ import annotations

from maap_app.modules.weaponeering.jmem_calculator import (
    FEET_TO_METERS,
    GUIDED_LASER_CEP_FT,
    JmemMissionInputs,
    JmemWeaponInputs,
    apply_selected_product_rank,
    calculate_effect_ranges_ft,
    calculate_weapon_effect,
    effect_radii_for_map,
    estimate_mae_building_ft2,
    is_guided_weapon,
    pk_for_rounds,
    rank_weapons,
    weapon_delivery_cep_ft,
)


def _doc_scenario_mission() -> JmemMissionInputs:
    return JmemMissionInputs(
        cep_ft=120.0,
        tle_ft=50.0,
        impact_angle_deg=60.0,
        burial_pct=0.0,
        target_length_ft=65.6,
        target_width_ft=49.2,
        p_rel=0.98,
        p_wpn=0.97,
        pk_desired=0.90,
    )


def test_mk82_matches_reference_pd_base() -> None:
    mission = _doc_scenario_mission()
    weapon = JmemWeaponInputs(
        product_id="w1",
        product_name="Mk-82 LDGP",
        weight_pounds=500.0,
        mae_building_ft2=12_000.0,
    )
    result = calculate_weapon_effect(mission, weapon)
    assert abs(result.pd_base - 0.1620) < 0.001
    assert abs(result.pk_single - 0.1541) < 0.001
    assert result.n_required == 14


def test_guided_weapon_uses_weapon_cep_not_pilot_cep() -> None:
    assert is_guided_weapon("GBU-12")
    assert is_guided_weapon("GBU-31")
    assert not is_guided_weapon("Mk-82")
    assert weapon_delivery_cep_ft("Mk-82", 120.0) == 120.0
    assert weapon_delivery_cep_ft("GBU-12", 120.0) == GUIDED_LASER_CEP_FT


def test_gbu12_more_accurate_than_mk82_same_weight() -> None:
    mission = _doc_scenario_mission()
    mk82 = calculate_weapon_effect(
        mission,
        JmemWeaponInputs("1", "Mk-82 LDGP", 500.0, 12_000.0),
    )
    gbu12 = calculate_weapon_effect(
        mission,
        JmemWeaponInputs("2", "GBU-12", 500.0, 12_000.0),
    )
    assert gbu12.pd_base > mk82.pd_base
    assert gbu12.pk_single > mk82.pk_single
    assert gbu12.n_required < mk82.n_required
    assert gbu12.n_required == 4
    assert gbu12.pk_n >= mission.pk_desired


def test_gbu31_beats_mk82_on_accuracy_and_rounds() -> None:
    mission = _doc_scenario_mission()
    mk82 = calculate_weapon_effect(
        mission,
        JmemWeaponInputs("1", "Mk-82 LDGP", 500.0, 12_000.0),
    )
    gbu31 = calculate_weapon_effect(
        mission,
        JmemWeaponInputs("2", "GBU-31", 2000.0, 32_000.0),
    )
    assert gbu31.pd_base > mk82.pd_base
    assert gbu31.n_required < mk82.n_required
    assert gbu31.n_required <= 2


def test_pk_for_rounds_matches_weapon_effect() -> None:
    mission = _doc_scenario_mission()
    weapon = JmemWeaponInputs("1", "Mk-82 LDGP", 500.0, 12_000.0)
    result = calculate_weapon_effect(mission, weapon)
    assert abs(pk_for_rounds(result.pk_single, result.n_required) - result.pk_n) < 0.0001
    assert abs(pk_for_rounds(result.pk_single, 1) - result.pk_single) < 0.0001
    assert pk_for_rounds(result.pk_single, result.n_required + 2) > result.pk_n


def test_apply_selected_product_rank_promotes_choice() -> None:
    mission = _doc_scenario_mission()
    weapons = [
        JmemWeaponInputs("1", "Mk-82", 500, 12_000),
        JmemWeaponInputs("2", "Mk-83", 1000, 18_000),
        JmemWeaponInputs("3", "Mk-84", 2000, 32_000),
    ]
    ranked = rank_weapons(mission, weapons)
    promoted = apply_selected_product_rank(ranked, "1")

    assert promoted[0].product_name == "Mk-82"
    assert promoted[0].rank == 1
    assert promoted[1].product_name == "Mk-84"


def test_ranking_orders_by_pd_descending() -> None:
    mission = _doc_scenario_mission()
    weapons = [
        JmemWeaponInputs("1", "Mk-82", 500, 12_000),
        JmemWeaponInputs("2", "Mk-83", 1000, 18_000),
        JmemWeaponInputs("3", "Mk-84", 2000, 32_000),
    ]
    ranked = rank_weapons(mission, weapons)
    assert ranked[0].product_name == "Mk-84"
    assert ranked[0].rank == 1
    assert ranked[-1].product_name == "Mk-82"
    assert ranked[0].pd_base > ranked[-1].pd_base


def test_high_drag_bomb_uses_steeper_impact_than_ldgp() -> None:
    mission = _doc_scenario_mission()
    mk82 = calculate_weapon_effect(
        mission,
        JmemWeaponInputs("1", "Mk-82 LDGP", 500.0, 12_000.0),
    )
    mk15 = calculate_weapon_effect(
        mission,
        JmemWeaponInputs("2", "MK 15 (High-Drag Bomb)", 500.0, 12_000.0),
    )
    assert mk15.pd_base > mk82.pd_base
    assert mk15.mae_eff_ft2 > mk82.mae_eff_ft2


def test_estimate_mae_from_product_name() -> None:
    assert estimate_mae_building_ft2("Mk-84 LDGP", 2000) == 32_000.0
    assert estimate_mae_building_ft2("MK 81 (250 lb)", 250) == 8_000.0
    assert estimate_mae_building_ft2("GBU-12", 500) == 12_000.0
    assert estimate_mae_building_ft2("GBU-10 / GBU-16", 2000) == 32_000.0
    assert estimate_mae_building_ft2("Generic", 500) == 12_000.0


def test_effect_ranges_at_anchor_weights() -> None:
    r100 = calculate_effect_ranges_ft(100)
    assert r100.red_ft == 14.0
    assert r100.orange_display == "14–16"
    assert r100.yellow_dark_ft == 20.0
    assert r100.yellow_light_ft == 30.0

    r250 = calculate_effect_ranges_ft(250)
    assert r250.red_ft == 18.0
    assert r250.orange_display == "18–22"
    assert r250.yellow_dark_ft == 25.0
    assert r250.yellow_light_ft == 40.0

    r500 = calculate_effect_ranges_ft(500)
    assert r500.red_ft == 25.0
    assert r500.orange_display == "25–30"
    assert r500.yellow_dark_ft == 32.0
    assert r500.yellow_light_ft == 55.0


def test_effect_radii_for_map_returns_four_zones() -> None:
    radii = effect_radii_for_map(500)
    assert len(radii) == 4
    assert radii[0]["zone"] == "red"
    assert radii[-1]["zone"] == "yellow_light"
    ranges = calculate_effect_ranges_ft(500)
    assert radii[0]["radiusM"] == ranges.red_ft * FEET_TO_METERS
    assert radii[0]["nRequired"] == 1


def test_effect_radii_for_map_scales_with_n_required() -> None:
    single = effect_radii_for_map(500, 1)
    scaled = effect_radii_for_map(500, 14)
    assert scaled[0]["radiusM"] == single[0]["radiusM"] * 14
    assert scaled[0]["baseRadiusFt"] == single[0]["baseRadiusFt"]
    assert scaled[0]["nRequired"] == 14


def test_effect_ranges_interpolate_between_anchors() -> None:
    ranges = calculate_effect_ranges_ft(175)
    assert 14.0 < ranges.red_ft < 18.0
    assert 16.0 < ranges.orange_max_ft < 22.0
    assert 20.0 < ranges.yellow_dark_ft < 25.0
    assert 30.0 < ranges.yellow_light_ft < 40.0
