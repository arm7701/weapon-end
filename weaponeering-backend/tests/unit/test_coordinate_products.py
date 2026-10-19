from __future__ import annotations

from maap_app.modules.target.coordinate_products import resolve_coordinate_product_id
from maap_app.modules.target.models import TargetCard, TargetCoordinate


def _card(**kwargs) -> TargetCard:
    return TargetCard(
        id="t1",
        scenario_id="s1",
        label="TGT",
        priority_score=3,
        complexity_score=3,
        map_node_id=None,
        review_status="draft",
        status="active",
        **kwargs,
    )


def test_resolve_coordinate_product_prefers_coordinate_selection() -> None:
    card = _card(selected_product_id="card-product")
    coord = TargetCoordinate(
        id="c1",
        target_card_id="t1",
        label="P1",
        map_lat=1.0,
        map_lng=2.0,
        sort_order=0,
        is_primary=True,
        selected_product_id="point-product",
    )
    assert resolve_coordinate_product_id(coord, card) == "point-product"


def test_resolve_coordinate_product_falls_back_to_card() -> None:
    card = _card(selected_product_id="card-product")
    coord = TargetCoordinate(
        id="c1",
        target_card_id="t1",
        label="P1",
        map_lat=1.0,
        map_lng=2.0,
        sort_order=0,
        is_primary=True,
        selected_product_id=None,
    )
    assert resolve_coordinate_product_id(coord, card) == "card-product"
