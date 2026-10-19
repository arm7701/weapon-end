from maap_app.modules.weaponeering.product_catalog import (
    HIGH_DRAG_IMPACT_ANGLE_DEG,
    KNOWN_PRODUCTS,
    catalog_description,
    fingerprint,
    is_cluster_weapon,
    is_high_drag_weapon,
    lookup_known_product,
    missing_known_products,
    weapon_impact_angle_deg,
)


def test_catalog_covers_air_to_ground_families() -> None:
    keys = {item.key for item in KNOWN_PRODUCTS}
    assert keys == {
        "mk-81",
        "mk-82",
        "mk-83",
        "mk-84",
        "mk-15-high-drag",
        "cbu-49-71",
        "gbu-12",
        "gbu-10-16",
        "jdam",
    }


def test_lookup_distinguishes_series() -> None:
    assert lookup_known_product("MK-81").key == "mk-81"
    assert lookup_known_product("MK 82 (500 lb)").key == "mk-82"
    assert lookup_known_product("Mk-82 LDGP").key == "mk-82"
    assert lookup_known_product("MK-83").key == "mk-83"
    assert lookup_known_product("MK-84").key == "mk-84"
    assert lookup_known_product("MK-15").key == "mk-15-high-drag"
    assert lookup_known_product("Mk 15 High-Drag").key == "mk-15-high-drag"
    assert lookup_known_product("GBU-12").key == "gbu-12"
    assert lookup_known_product("GBU-82").key == "gbu-12"
    assert lookup_known_product("GBU-10").key == "gbu-10-16"
    assert lookup_known_product("GBU-16").key == "gbu-10-16"
    assert lookup_known_product("JDAM").key == "jdam"
    assert lookup_known_product("CBU-49").key == "cbu-49-71"
    assert lookup_known_product("CBU-71").key == "cbu-49-71"


def test_gbu12_is_not_classified_as_mk82() -> None:
    assert fingerprint("GBU-12 (Laser-Guided, MK 82)") == "gbu-12"
    assert fingerprint("Mk-82 Snakeye") == "mk-15-high-drag"


def test_high_drag_uses_steep_impact_angle() -> None:
    assert is_high_drag_weapon("MK 15 (High-Drag Bomb)")
    assert is_high_drag_weapon("Mk-82 Snakeye")
    assert not is_high_drag_weapon("Mk-82 LDGP")
    assert weapon_impact_angle_deg("MK-15", 60.0) == HIGH_DRAG_IMPACT_ANGLE_DEG
    assert weapon_impact_angle_deg("MK-82", 60.0) == 60.0


def test_cluster_catalog_notes_convention() -> None:
    assert is_cluster_weapon("CBU-49 / CBU-71 (Cluster Bomb)")
    text = catalog_description("CBU-71")
    assert "300" in text
    assert "Convention on Cluster Munitions" in text
    assert "ภารกิจหลัก" in text


def test_guided_catalog_descriptions() -> None:
    assert "เลเซอร์" in catalog_description("GBU-12")
    assert "JTAC" in catalog_description("GBU-12")
    assert "GPS" in catalog_description("JDAM (Stand-off Weapon)")
    assert "100" in catalog_description("JDAM")
    assert catalog_description("MK-82", "คำอธิบายที่บันทึกไว้") == "คำอธิบายที่บันทึกไว้"


def test_missing_known_products_skips_existing_series() -> None:
    missing = missing_known_products(["MK-82", "MK-84", "MK 15 (High-Drag Bomb)"])
    keys = {item.key for item in missing}
    assert "mk-82" not in keys
    assert "mk-84" not in keys
    assert "mk-15-high-drag" not in keys
    assert "mk-81" in keys
    assert "cbu-49-71" in keys
    assert "jdam" in keys
