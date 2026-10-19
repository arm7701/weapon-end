from __future__ import annotations

from maap_app.modules.target.models import TargetCard, TargetCoordinate


def resolve_coordinate_product_id(
    coordinate: TargetCoordinate | None,
    card: TargetCard,
) -> str | None:
    if coordinate is not None and coordinate.selected_product_id:
        return coordinate.selected_product_id
    return card.selected_product_id


def match_existing_coordinate(
    label: str,
    map_lat: float,
    map_lng: float,
    existing: list[TargetCoordinate],
) -> TargetCoordinate | None:
    needle_label = label.strip()
    for coord in existing:
        if (
            coord.label.strip() == needle_label
            and abs(coord.map_lat - map_lat) < 1e-4
            and abs(coord.map_lng - map_lng) < 1e-4
        ):
            return coord
    return None
