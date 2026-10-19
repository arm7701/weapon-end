from maap_app.ui.product_images import product_image_path


def test_product_image_path_matches_known_weapons() -> None:
    assert product_image_path("MK-82") == product_image_path("Mk-82 LDGP")
    assert product_image_path("MK-82").name == "mk-82.png"
    assert product_image_path("GBU-84").name == "gbu-84.png"
    assert product_image_path("gbu-82").name == "gbu-82.png"
    assert product_image_path("MK-84").name == "mk-84.png"


def test_product_image_path_matches_aliases() -> None:
    assert product_image_path("GBU-12").name == "gbu-82.png"
    assert product_image_path("GBU-10").name == "gbu-84.png"
    assert product_image_path("MK 81 (250 lb)").name == "mk-82.png"
    assert product_image_path("CBU-49 / CBU-71").name == "mk-82.png"
    assert product_image_path("GBU-16").name == "gbu-84.png"
    assert product_image_path("JDAM (Stand-off Weapon)").name == "gbu-84.png"


def test_product_image_path_unknown_returns_none() -> None:
    assert product_image_path("AGM-65") is None
