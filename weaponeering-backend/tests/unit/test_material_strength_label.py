from maap_app.modules.weaponeering.product_advisor import material_strength_label


def test_rc_strength_label_lists_fc_and_fy() -> None:
    label = material_strength_label("REINFORCED CONCRETE", {"fc_mpa": 40, "fy_mpa": 400})
    assert label == "ค่าความแข็งแรงวัสดุ (RC): f'c 40 MPa · fy 400 MPa"


def test_wood_uses_fc_compression_label() -> None:
    label = material_strength_label("WOOD", {"fc_mpa": 12.5})
    assert label == "ค่าความแข็งแรงวัสดุ (WOOD): Fc 12.5 MPa"


def test_soil_params_and_text_values_are_skipped() -> None:
    label = material_strength_label("EARTH", {"c_kpa": 15, "phi_deg": 30, "section": "W12x26"})
    assert label == "ค่าความแข็งแรงวัสดุ (EARTH): c 15 kPa · φ 30 °"


def test_empty_strength_returns_none() -> None:
    assert material_strength_label("STEEL", {}) is None
    assert material_strength_label("STEEL", None) is None
    assert material_strength_label("STEEL", {"section": "W12x26"}) is None
