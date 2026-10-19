from __future__ import annotations

import uuid
from types import SimpleNamespace

from sqlalchemy.ext.asyncio import AsyncSession

from maap_app.modules.weaponeering.jmem_calculator import (
    EFFECT_ZONE_COLORS,
    EFFECT_ZONE_LABELS_TH,
    FEET_TO_METERS,
    JmemWeaponInputs,
    apply_selected_product_rank,
    build_target_context,
    effect_radii_for_map,
    estimate_mae_building_ft2,
    pk_for_rounds,
    rank_weapons,
)
from maap_app.modules.weaponeering.product_catalog import (
    catalog_description,
    weapon_guidance,
    weapon_impact_angle_deg,
)
from maap_app.modules.weaponeering.laser_designation import (
    designation_info_for,
    designation_warning_lines,
    is_laser_guided_weapon,
)
from maap_app.modules.weaponeering.weapon_effects import weapon_effects_info
from maap_app.modules.weaponeering.circular_error import circular_error_info
from maap_app.modules.weaponeering.product_advisor import (
    product_analysis_prompt,
    recommend_product,
)
from weaponeering_api.models.target import TargetCard, TargetCoordinate
from weaponeering_api.models.wing import WingProduct
from weaponeering_api.models import User
from weaponeering_api.schemas.jmem import (
    JmemAiAdviceOut,
    JmemCatalogItemOut,
    JmemCoordinateProductOut,
    JmemEffectZoneOut,
    JmemMissionOut,
    JmemProductRankOut,
    JmemTargetProductsOut,
    LaserDesignationOut,
    LaserDesignationWorkflowOut,
    CircularErrorMetricOut,
    CircularErrorOut,
    WeaponEffectOut,
    WeaponEffectsOut,
)
from weaponeering_api.services import target_service, wing_service
from weaponeering_api.services.auth_persist import write_audit


def _card_namespace(card: TargetCard) -> SimpleNamespace:
    """jmem_calculator expects attribute access like desktop TargetCard."""
    return SimpleNamespace(
        label=card.label,
        target_type=card.target_type,
        target_subtype=card.target_subtype,
        cep=card.cep,
        coordinate_error_m=card.coordinate_error_m,
        length_m=card.length_m,
        width_m=card.width_m,
        target_pk=card.target_pk,
        reference_pk=card.reference_pk,
    )


def _resolve_selected_product_id(
    card: TargetCard,
    coordinate: TargetCoordinate | None = None,
) -> str | None:
    if coordinate is not None and coordinate.selected_product_id:
        return coordinate.selected_product_id
    return card.selected_product_id


def _resolve_weapon_quantity(
    card: TargetCard,
    coordinate: TargetCoordinate | None = None,
) -> int | None:
    if coordinate is not None and coordinate.weapon_quantity is not None:
        return max(1, int(coordinate.weapon_quantity))
    if card.weapon_quantity is not None:
        return max(1, int(card.weapon_quantity))
    return None


def _applies_quantity_override(
    result,
    *,
    selected_product_id: str | None,
) -> bool:
    if selected_product_id:
        return result.product_id == selected_product_id
    return result.rank == 1


def _effective_weapon_stats(
    result,
    *,
    weapon_quantity: int | None,
    selected_product_id: str | None,
) -> tuple[int, int, float, bool]:
    n_jmem = max(0, int(result.n_required))
    applies = (
        weapon_quantity is not None
        and _applies_quantity_override(result, selected_product_id=selected_product_id)
    )
    if applies:
        n_required = max(1, int(weapon_quantity))
        pk_n = pk_for_rounds(result.pk_single, n_required)
        return n_jmem, n_required, pk_n, n_required != n_jmem
    return n_jmem, n_jmem, result.pk_n, False


def _serialize_result(
    result,
    *,
    selected_product_id: str | None,
    weapon_quantity: int | None = None,
    unit_cost: float = 0.0,
    description: str = "",
    impact_angle_deg: float | None = None,
) -> JmemProductRankOut:
    n_jmem, n_required, pk_n, quantity_overridden = _effective_weapon_stats(
        result,
        weapon_quantity=weapon_quantity,
        selected_product_id=selected_product_id,
    )
    is_selected = bool(
        selected_product_id and result.product_id == selected_product_id
    ) or (not selected_product_id and result.rank == 1)
    return JmemProductRankOut(
        rank=result.rank,
        product_id=result.product_id,
        product_name=result.product_name,
        weight_pounds=result.weight_pounds,
        unit_cost=unit_cost,
        pd_base=result.pd_base,
        pk_single=result.pk_single,
        n_jmem=n_jmem,
        n_required=n_required,
        pk_n=pk_n,
        quantity_overridden=quantity_overridden,
        mae_building_ft2=result.mae_building_ft2,
        impact_angle_deg=impact_angle_deg,
        description=description,
        guidance=weapon_guidance(result.product_name),
        requires_laser_designation=is_laser_guided_weapon(result.product_name),
        range_red_ft=result.range_red_ft,
        range_orange_min_ft=result.range_orange_min_ft,
        range_orange_max_ft=result.range_orange_max_ft,
        range_yellow_dark_ft=result.range_yellow_dark_ft,
        range_yellow_light_ft=result.range_yellow_light_ft,
        range_red_m=result.range_red_ft * FEET_TO_METERS,
        range_orange_m=result.range_orange_max_ft * FEET_TO_METERS,
        range_yellow_dark_m=result.range_yellow_dark_ft * FEET_TO_METERS,
        range_yellow_light_m=result.range_yellow_light_ft * FEET_TO_METERS,
        selected=is_selected,
    )


def _rank_products(
    card: TargetCard,
    products: list[WingProduct],
    *,
    selected_product_id: str | None,
    weapon_quantity: int | None,
    unit_cost_by_id: dict[str, float],
) -> list[JmemProductRankOut]:
    if not products:
        return []
    mission = build_target_context(str(card.id), _card_namespace(card)).mission
    description_by_id = {
        str(product.id): catalog_description(
            product.product_name, getattr(product, "description", "") or ""
        )
        for product in products
    }
    weapons = [
        JmemWeaponInputs(
            product_id=str(product.id),
            product_name=product.product_name,
            weight_pounds=float(product.weight_pounds or 0),
            mae_building_ft2=estimate_mae_building_ft2(
                product.product_name,
                float(product.weight_pounds or 0),
            ),
        )
        for product in products
    ]
    ranked = apply_selected_product_rank(
        rank_weapons(mission, weapons),
        selected_product_id,
    )
    return [
        _serialize_result(
            result,
            selected_product_id=selected_product_id,
            weapon_quantity=weapon_quantity,
            unit_cost=float(unit_cost_by_id.get(result.product_id, 0.0)),
            description=description_by_id.get(result.product_id, ""),
            impact_angle_deg=weapon_impact_angle_deg(
                result.product_name, mission.impact_angle_deg
            ),
        )
        for result in ranked
    ]


def _effect_zones_for_top(products: list[JmemProductRankOut]) -> list[JmemEffectZoneOut]:
    if not products:
        return []
    top = products[0]
    zones = effect_radii_for_map(top.weight_pounds, top.n_required or 1)
    out: list[JmemEffectZoneOut] = []
    for zone in zones:
        key = str(zone["zone"])
        out.append(
            JmemEffectZoneOut(
                zone=key,
                color=str(zone.get("color") or EFFECT_ZONE_COLORS.get(key, "#999")),
                label_th=EFFECT_ZONE_LABELS_TH.get(key, key),
                radius_ft=float(zone["radiusFt"]),
                radius_m=float(zone["radiusM"]),
                n_required=int(zone.get("nRequired") or 1),
            )
        )
    return out


def _serialize_laser_designation(product_name: str) -> LaserDesignationOut | None:
    info = designation_info_for(product_name)
    if info is None:
        return None
    return LaserDesignationOut(
        required=info.required,
        title=info.title,
        intro=info.intro,
        weather_limitation=info.weather_limitation,
        guidance=info.guidance,
        workflows=[
            LaserDesignationWorkflowOut(
                key=row.key,
                label_en=row.label_en,
                label_th=row.label_th,
                summary=row.summary,
            )
            for row in info.workflows
        ],
    )


def _serialize_weapon_effects() -> WeaponEffectsOut:
    info = weapon_effects_info()
    return WeaponEffectsOut(
        title=info.title,
        intro=info.intro,
        effects=[
            WeaponEffectOut(
                key=row.key,
                label_en=row.label_en,
                label_th=row.label_th,
                summary=row.summary,
            )
            for row in info.effects
        ],
    )


def _serialize_circular_error(
    product_name: str = "",
    cep_ft: float | None = None,
) -> CircularErrorOut:
    info = circular_error_info(ce50_ft=cep_ft, product_name=product_name)
    return CircularErrorOut(
        title=info.title,
        intro=info.intro,
        application=info.application,
        metrics=[
            CircularErrorMetricOut(
                key=row.key,
                label_en=row.label_en,
                label_th=row.label_th,
                summary=row.summary,
            )
            for row in info.metrics
        ],
        ce50_ft=info.ce50_ft,
        ce90_ft=info.ce90_ft,
        cep_source=info.cep_source,
    )


async def get_target_jmem_products(
    db: AsyncSession,
    target_id: uuid.UUID,
) -> JmemTargetProductsOut:
    card = await target_service.get_target(db, target_id)
    if card is None:
        raise ValueError("ไม่พบเป้าหมาย")

    products = await wing_service.list_products(
        db,
        scenario_id=card.scenario_id,
        status="active",
    )
    unit_cost_by_id = {str(p.id): float(p.unit_cost or 0) for p in products}
    catalog = [
        JmemCatalogItemOut(
            id=str(p.id),
            name=p.product_name,
            weight_pounds=float(p.weight_pounds or 0),
            unit_cost=float(p.unit_cost or 0),
            description=catalog_description(
                p.product_name, getattr(p, "description", "") or ""
            ),
            guidance=weapon_guidance(p.product_name),
            requires_laser_designation=is_laser_guided_weapon(p.product_name),
        )
        for p in products
    ]

    context = build_target_context(str(card.id), _card_namespace(card))
    selected = _resolve_selected_product_id(card)
    weapon_quantity = _resolve_weapon_quantity(card)
    ranked = _rank_products(
        card,
        products,
        selected_product_id=selected,
        weapon_quantity=weapon_quantity,
        unit_cost_by_id=unit_cost_by_id,
    )

    coordinate_products: list[JmemCoordinateProductOut] = []
    for index, coord in enumerate(card.coordinates or []):
        coord_selected = _resolve_selected_product_id(card, coord)
        coord_quantity = _resolve_weapon_quantity(card, coord)
        coordinate_products.append(
            JmemCoordinateProductOut(
                coordinate_id=str(coord.id),
                label=(coord.label or "").strip() or f"P{index + 1}",
                is_primary=bool(coord.is_primary),
                selected_product_id=coord_selected,
                weapon_quantity=coord_quantity,
                products=_rank_products(
                    card,
                    products,
                    selected_product_id=coord_selected,
                    weapon_quantity=coord_quantity,
                    unit_cost_by_id=unit_cost_by_id,
                )[:5],
            )
        )

    mission = context.mission
    top_name = ranked[0].product_name if ranked else ""
    warnings = list(context.warnings)
    warnings.extend(designation_warning_lines(top_name))
    return JmemTargetProductsOut(
        target_id=card.id,
        label=card.label,
        target_element=context.target_element,
        selected_product_id=selected,
        weapon_quantity=weapon_quantity,
        warnings=warnings,
        mission=JmemMissionOut(
            cep_ft=mission.cep_ft,
            tle_ft=mission.tle_ft,
            impact_angle_deg=mission.impact_angle_deg,
            burial_pct=mission.burial_pct,
            target_length_ft=mission.target_length_ft,
            target_width_ft=mission.target_width_ft,
            p_rel=mission.p_rel,
            p_wpn=mission.p_wpn,
            pk_desired=mission.pk_desired,
        ),
        product_catalog=catalog,
        products=ranked,
        coordinate_products=coordinate_products,
        effect_zones=_effect_zones_for_top(ranked[:1] if ranked else []),
        laser_designation=_serialize_laser_designation(top_name),
        weapon_effects=_serialize_weapon_effects(),
        circular_error=_serialize_circular_error(top_name, mission.cep_ft),
    )


async def select_target_product(
    db: AsyncSession,
    target_id: uuid.UUID,
    *,
    product_id: str | None,
    coordinate_id: uuid.UUID | None,
    user: User,
) -> JmemTargetProductsOut:
    card = await target_service.get_target(db, target_id)
    if card is None:
        raise ValueError("ไม่พบเป้าหมาย")

    if product_id:
        product = await wing_service.get_product(db, uuid.UUID(str(product_id)))
        if product is None or product.scenario_id != card.scenario_id:
            raise ValueError("ไม่พบสินค้าใน scenario นี้")

    if coordinate_id is not None:
        coord = next((c for c in card.coordinates if c.id == coordinate_id), None)
        if coord is None:
            raise ValueError("ไม่พบพิกัดเป้าหมาย")
        coord.selected_product_id = product_id
        coord.weapon_quantity = None
        await write_audit(
            db,
            actor=user.username,
            event_type="target_coordinate.selected_product",
            entity_type="target_coordinate",
            entity_id=str(coordinate_id),
            details={"product_id": product_id},
        )
    else:
        card.selected_product_id = product_id
        card.weapon_quantity = None
        await write_audit(
            db,
            actor=user.username,
            event_type="target_card.selected_product",
            entity_type="target_card",
            entity_id=str(target_id),
            details={"product_id": product_id},
        )

    await db.commit()
    return await get_target_jmem_products(db, target_id)


async def set_target_weapon_quantity(
    db: AsyncSession,
    target_id: uuid.UUID,
    *,
    quantity: int | None,
    coordinate_id: uuid.UUID | None,
    user: User,
) -> JmemTargetProductsOut:
    card = await target_service.get_target(db, target_id)
    if card is None:
        raise ValueError("ไม่พบเป้าหมาย")

    if coordinate_id is not None:
        coord = next((c for c in card.coordinates if c.id == coordinate_id), None)
        if coord is None:
            raise ValueError("ไม่พบพิกัดเป้าหมาย")
        coord.weapon_quantity = quantity
        await write_audit(
            db,
            actor=user.username,
            event_type="target_coordinate.weapon_quantity",
            entity_type="target_coordinate",
            entity_id=str(coordinate_id),
            details={"weapon_quantity": quantity},
        )
    else:
        card.weapon_quantity = quantity
        await write_audit(
            db,
            actor=user.username,
            event_type="target_card.weapon_quantity",
            entity_type="target_card",
            entity_id=str(target_id),
            details={"weapon_quantity": quantity},
        )

    await db.commit()
    return await get_target_jmem_products(db, target_id)


async def _stock_by_product(db: AsyncSession, scenario_id: uuid.UUID) -> dict[str, int]:
    stock: dict[str, int] = {}
    for row in await wing_service.list_inventory_details(db, scenario_id=scenario_id):
        key = str(row.product_id)
        stock[key] = stock.get(key, 0) + int(row.quantity or 0)
    return stock


async def advise_target_product(
    db: AsyncSession,
    target_id: uuid.UUID,
    *,
    apply_recommendation: bool = False,
    user: User,
) -> JmemAiAdviceOut:
    """Rank with JMEM then recommend product like desktop product_advisor."""
    card = await target_service.get_target(db, target_id)
    if card is None:
        raise ValueError("ไม่พบเป้าหมาย")

    products = await wing_service.list_products(
        db,
        scenario_id=card.scenario_id,
        status="active",
    )
    if not products:
        raise ValueError("ไม่มีสินค้าใน scenario ให้วิเคราะห์")

    unit_cost_by_id = {str(p.id): float(p.unit_cost or 0) for p in products}
    selected = _resolve_selected_product_id(card)
    context = build_target_context(str(card.id), _card_namespace(card))
    weapons = [
        JmemWeaponInputs(
            product_id=str(product.id),
            product_name=product.product_name,
            weight_pounds=float(product.weight_pounds or 0),
            mae_building_ft2=estimate_mae_building_ft2(
                product.product_name,
                float(product.weight_pounds or 0),
            ),
        )
        for product in products
    ]
    results = apply_selected_product_rank(
        rank_weapons(context.mission, weapons),
        selected,
    )
    advisor_products = [
        SimpleNamespace(id=str(p.id), unit_cost=float(p.unit_cost or 0))
        for p in products
    ]
    advisor_card = SimpleNamespace(
        label=card.label,
        target_type=card.target_type,
        material_class=card.material_class,
    )
    recommendation = recommend_product(
        advisor_card,
        context.mission,
        results,
        advisor_products,
        stock_by_product=await _stock_by_product(db, card.scenario_id),
    )
    if recommendation is None:
        raise ValueError("ไม่สามารถสร้างคำแนะนำสินค้าได้")

    prompt = product_analysis_prompt(
        recommendation,
        target_label=card.label,
        target_type=card.target_type,
    )
    analysis_text = "\n".join(
        [
            recommendation.rationale,
            f"ความมั่นใจ: {recommendation.confidence}",
            "",
            "ปัจจัยการพิจารณา:",
            *[f"- {factor}" for factor in recommendation.factors],
        ]
    )

    applied_product_id = None
    if apply_recommendation:
        card.selected_product_id = recommendation.product_id
        applied_product_id = recommendation.product_id
        await write_audit(
            db,
            actor=user.username,
            event_type="target_card.ai_product_applied",
            entity_type="target_card",
            entity_id=str(target_id),
            details={"product_id": recommendation.product_id},
        )
        await db.commit()

    jmem = await get_target_jmem_products(db, target_id)
    return JmemAiAdviceOut(
        recommendation={
            "product_id": recommendation.product_id,
            "product_name": recommendation.product_name,
            "jmem_rank": recommendation.jmem_rank,
            "meets_desired_pk": recommendation.meets_desired_pk,
            "confidence": recommendation.confidence,
            "rationale": recommendation.rationale,
            "factors": list(recommendation.factors),
            "unit_cost": recommendation.unit_cost,
            "mission_cost": recommendation.mission_cost,
            "n_required": recommendation.n_required,
            "pk_n": recommendation.pk_n,
            "stock_available": recommendation.stock_available,
            "unit_cost_lookup": unit_cost_by_id.get(recommendation.product_id, 0.0),
        },
        analysis_text=analysis_text,
        prompt=prompt,
        jmem=jmem,
        applied_product_id=applied_product_id,
    )
