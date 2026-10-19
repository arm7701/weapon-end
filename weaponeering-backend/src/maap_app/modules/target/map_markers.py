from __future__ import annotations

from maap_app.modules.target.coordinate_products import resolve_coordinate_product_id
from maap_app.modules.target.service import TargetService
from maap_app.modules.weaponeering.jmem_calculator import (
    JmemWeaponInputs,
    apply_selected_product_rank,
    effect_radii_for_map,
    estimate_mae_building_ft2,
    mission_inputs_from_target_card,
    rank_weapons,
)
from maap_app.modules.wing_data.service import WingDataService

_DEFAULT_EFFECT_WEIGHT_LB = 500.0


def enrich_target_markers_with_effect_radii(
    markers: list[dict],
    scenario_id: str,
    target_service: TargetService,
    wing_data_service: WingDataService,
) -> list[dict]:
    products = wing_data_service.list_products(scenario_id)
    weapons = [
        JmemWeaponInputs(
            product_id=product.id,
            product_name=product.product_name,
            weight_pounds=product.weight_pounds,
            mae_building_ft2=estimate_mae_building_ft2(
                product.product_name,
                product.weight_pounds,
            ),
        )
        for product in products
    ]

    enriched: list[dict] = []
    for marker in markers:
        payload = dict(marker)
        weight_lb = _DEFAULT_EFFECT_WEIGHT_LB
        n_required = 1
        effect_product: str | None = None

        detail = target_service.get_target_detail(marker["targetCardId"])
        selected_product_id: str | None = None
        if detail is not None:
            coord_by_id = {coord.id: coord for coord in detail.coordinates}
            coordinate = coord_by_id.get(marker.get("coordinateId"))
            selected_product_id = resolve_coordinate_product_id(
                coordinate,
                detail.card,
            )
        if detail is not None and weapons:
            mission = mission_inputs_from_target_card(detail.card)
            ranked = apply_selected_product_rank(
                rank_weapons(mission, weapons),
                selected_product_id,
            )
            if ranked:
                top = ranked[0]
                weight_lb = top.weight_pounds
                n_required = max(1, top.n_required)
                effect_product = top.product_name

        payload["effectRadii"] = effect_radii_for_map(weight_lb, n_required)
        payload["effectN"] = n_required
        payload["effectWeightLb"] = weight_lb
        if effect_product:
            payload["effectProduct"] = effect_product
        enriched.append(payload)
    return enriched
