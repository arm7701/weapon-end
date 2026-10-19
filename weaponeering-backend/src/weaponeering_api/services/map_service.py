from __future__ import annotations

import uuid
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from maap_app.modules.target.footprint import target_footprint
from maap_app.modules.weaponeering.jmem_calculator import (
    JmemWeaponInputs,
    apply_selected_product_rank,
    build_target_context,
    effect_radii_for_map,
    estimate_mae_building_ft2,
    rank_weapons,
)
from weaponeering_api.models.detection import (
    ScenarioGroundTransport,
    ScenarioTeamMarker,
    TargetMapDetectionRun,
)
from weaponeering_api.models.target import TargetCard
from weaponeering_api.models.wing import AirWing, WingDepot, WingLogisticsVehicle, WingProduct

_DEFAULT_EFFECT_WEIGHT_LB = 500.0


async def build_map_layers(
    db: AsyncSession,
    scenario_id: uuid.UUID,
    *,
    selected_transport_id: uuid.UUID | None = None,
) -> dict:
    """Aggregate layer payloads matching desktop MainWindow._refresh_map_layers shapes."""
    targets = await _target_markers(db, scenario_id)
    await _attach_risk_directions(db, scenario_id, targets)
    wings, depots = await _wing_layers(db, scenario_id)
    detections = await _detection_objects(db, scenario_id)
    teams = await _team_markers(db, scenario_id)
    transports = await _ground_transports(
        db, scenario_id, selected_transport_id=selected_transport_id
    )
    return {
        "scenarioId": str(scenario_id),
        "targets": targets,
        "wings": wings,
        "depots": depots,
        "detections": detections,
        "teamMarkers": teams,
        "groundTransports": transports,
    }


def _card_namespace(card: TargetCard) -> SimpleNamespace:
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


def _effect_payload_for_card(
    card: TargetCard,
    *,
    selected_product_id: str | None,
    weapon_quantity: int | None,
    weapons: list[JmemWeaponInputs],
) -> tuple[list[dict], int, float, str | None]:
    """Match desktop enrich_target_markers_with_effect_radii."""
    weight_lb = _DEFAULT_EFFECT_WEIGHT_LB
    n_required = 1
    effect_product: str | None = None
    if weapons:
        mission = build_target_context(str(card.id), _card_namespace(card)).mission
        ranked = apply_selected_product_rank(
            rank_weapons(mission, weapons),
            selected_product_id,
        )
        if ranked:
            top = ranked[0]
            active = next(
                (row for row in ranked if selected_product_id and row.product_id == selected_product_id),
                top,
            )
            weight_lb = float(active.weight_pounds)
            n_jmem = max(1, int(active.n_required))
            if weapon_quantity is not None:
                n_required = max(1, int(weapon_quantity))
            else:
                n_required = n_jmem
            effect_product = active.product_name
    return effect_radii_for_map(weight_lb, n_required), n_required, weight_lb, effect_product


async def _attach_risk_directions(
    db: AsyncSession, scenario_id: uuid.UUID, targets: list[dict]
) -> None:
    """Attach lowestRiskDirection (entry/exit approach) to target markers with detections."""
    from weaponeering_api.services.detection_inference import build_risk_direction_payload

    result = await db.execute(
        select(TargetMapDetectionRun)
        .options(selectinload(TargetMapDetectionRun.objects))
        .where(TargetMapDetectionRun.scenario_id == scenario_id)
    )
    runs_by_coord: dict[tuple[str, str], TargetMapDetectionRun] = {}
    for run in result.scalars().all():
        key = (str(run.target_card_id), str(run.target_coordinate_id))
        runs_by_coord[key] = run

    for marker in targets:
        key = (marker["targetCardId"], marker["coordinateId"])
        run = runs_by_coord.get(key)
        if run is None or not run.objects:
            continue
        objects = [
            {
                "lat": obj.center_lat,
                "lng": obj.center_lng,
                "risk": obj.risk_level,
                "label": obj.object_label,
            }
            for obj in run.objects
        ]
        marker["lowestRiskDirection"] = build_risk_direction_payload(
            lat=marker["lat"],
            lng=marker["lng"],
            objects=objects,
            scan_radius_m=float(run.radius_m),
        )
        marker["detectionRadiusM"] = run.radius_m
        marker["detectionObjectCount"] = run.object_count


async def _target_markers(db: AsyncSession, scenario_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(TargetCard)
        .options(selectinload(TargetCard.coordinates))
        .where(TargetCard.scenario_id == scenario_id, TargetCard.status == "active")
        .order_by(TargetCard.created_at.asc())
    )
    products_result = await db.execute(
        select(WingProduct).where(
            WingProduct.scenario_id == scenario_id,
            WingProduct.status == "active",
        )
    )
    products = list(products_result.scalars().all())
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

    markers: list[dict] = []
    for card in result.scalars().all():
        coords = sorted(card.coordinates, key=lambda c: (not c.is_primary, c.sort_order))
        if not coords:
            continue
        radius_m = (
            float(card.coordinate_error_m)
            if card.coordinate_error_m is not None and card.coordinate_error_m > 0
            else 0.0
        )
        point_count = len(coords)
        for index, coord in enumerate(coords):
            point_label = (coord.label or "").strip() or f"P{index + 1}"
            display_label = card.label if point_count == 1 else f"{card.label} · {point_label}"
            selected_product_id = coord.selected_product_id or card.selected_product_id
            weapon_quantity = coord.weapon_quantity if coord.weapon_quantity is not None else card.weapon_quantity
            effect_radii, n_required, weight_lb, effect_product = _effect_payload_for_card(
                card,
                selected_product_id=selected_product_id,
                weapon_quantity=weapon_quantity,
                weapons=weapons,
            )
            payload = {
                "targetCardId": str(card.id),
                "coordinateId": str(coord.id),
                "mapNodeId": str(card.map_node_id) if coord.is_primary and card.map_node_id else None,
                "label": display_label,
                "lat": coord.map_lat,
                "lng": coord.map_lng,
                "radiusM": radius_m,
                "isPrimary": coord.is_primary,
                "pointIndex": index,
                "pointCount": point_count,
                "priorityScore": card.priority_score,
                "targetType": card.target_type,
                "effectRadii": effect_radii,
                "effectN": n_required,
                "effectWeightLb": weight_lb,
            }
            if effect_product:
                payload["effectProduct"] = effect_product
            if index == 0:
                footprint = target_footprint(
                    coord.map_lat,
                    coord.map_lng,
                    card.length_m,
                    card.width_m,
                    heading_deg=card.heading_deg,
                    height_m=card.height_m,
                )
                if footprint is not None:
                    payload["footprint"] = footprint.to_payload()
            markers.append(payload)
    return markers


async def _wing_layers(
    db: AsyncSession, scenario_id: uuid.UUID
) -> tuple[list[dict], list[dict]]:
    wings_result = await db.execute(
        select(AirWing).where(AirWing.scenario_id == scenario_id, AirWing.status == "active")
    )
    depots_result = await db.execute(
        select(WingDepot).where(WingDepot.scenario_id == scenario_id, WingDepot.status == "active")
    )
    wings = []
    for wing in wings_result.scalars().all():
        if wing.map_lat is None or wing.map_lng is None:
            continue
        wings.append(
            {
                "entityId": str(wing.id),
                "entityType": "air_wing",
                "label": wing.wing_name,
                "lat": wing.map_lat,
                "lng": wing.map_lng,
            }
        )
    depots = []
    for depot in depots_result.scalars().all():
        if depot.map_lat is None or depot.map_lng is None:
            continue
        depots.append(
            {
                "entityId": str(depot.id),
                "entityType": "wing_depot",
                "label": depot.depot_name,
                "lat": depot.map_lat,
                "lng": depot.map_lng,
                "wingId": str(depot.wing_id),
            }
        )
    return wings, depots


async def _detection_objects(db: AsyncSession, scenario_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(TargetMapDetectionRun)
        .options(selectinload(TargetMapDetectionRun.objects))
        .where(TargetMapDetectionRun.scenario_id == scenario_id)
    )
    items: list[dict] = []
    for run in result.scalars().all():
        for obj in run.objects:
            items.append(
                {
                    "id": str(obj.id),
                    "runId": str(run.id),
                    "targetCardId": str(obj.target_card_id),
                    "targetCoordinateId": str(run.target_coordinate_id),
                    "mapObjectId": obj.map_object_id,
                    "label": obj.object_label,
                    "objectType": obj.object_type,
                    "risk": obj.risk_level,
                    "confidence": obj.confidence,
                    "lat": obj.center_lat,
                    "lng": obj.center_lng,
                    "polygon": obj.polygon_json if isinstance(obj.polygon_json, list) else [],
                }
            )
    return items


async def _team_markers(db: AsyncSession, scenario_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(ScenarioTeamMarker)
        .where(ScenarioTeamMarker.scenario_id == scenario_id)
        .order_by(ScenarioTeamMarker.created_at.asc())
    )
    items: list[dict] = []
    for marker in result.scalars().all():
        payload = {
            "id": str(marker.id),
            "side": marker.side,
            "unitType": marker.unit_type,
            "label": marker.label,
            "lat": marker.map_lat,
            "lng": marker.map_lng,
        }
        if marker.radius_m is not None:
            payload["radiusM"] = marker.radius_m
        items.append(payload)
    return items


async def _ground_transports(
    db: AsyncSession,
    scenario_id: uuid.UUID,
    *,
    selected_transport_id: uuid.UUID | None = None,
) -> list[dict]:
    wings_result = await db.execute(
        select(AirWing).where(AirWing.scenario_id == scenario_id, AirWing.status == "active")
    )
    wings = {w.id: w for w in wings_result.scalars().all()}
    products_result = await db.execute(
        select(WingProduct).where(WingProduct.scenario_id == scenario_id, WingProduct.status == "active")
    )
    products = {p.id: p for p in products_result.scalars().all()}
    vehicles_result = await db.execute(
        select(WingLogisticsVehicle).where(
            WingLogisticsVehicle.scenario_id == scenario_id,
            WingLogisticsVehicle.status == "active",
        )
    )
    vehicles = {v.id: v for v in vehicles_result.scalars().all()}

    stmt = select(ScenarioGroundTransport).where(
        ScenarioGroundTransport.scenario_id == scenario_id,
        ScenarioGroundTransport.status == "active",
    )
    if selected_transport_id is not None:
        stmt = stmt.where(ScenarioGroundTransport.id == selected_transport_id)
    result = await db.execute(stmt.order_by(ScenarioGroundTransport.created_at.desc()))

    routes: list[dict] = []
    for transport in result.scalars().all():
        origin = wings.get(transport.origin_wing_id)
        destination = wings.get(transport.destination_wing_id)
        if (
            origin is None
            or destination is None
            or origin.map_lat is None
            or origin.map_lng is None
            or destination.map_lat is None
            or destination.map_lng is None
        ):
            continue
        product = products.get(transport.product_id) if transport.product_id else None
        vehicle = vehicles.get(transport.vehicle_id) if transport.vehicle_id else None
        path = transport.route_geometry_json if isinstance(transport.route_geometry_json, list) else []
        if len(path) < 2:
            path = [
                [origin.map_lat, origin.map_lng],
                [destination.map_lat, destination.map_lng],
            ]
        routes.append(
            {
                "id": str(transport.id),
                "label": transport.label or f"{origin.wing_name} → {destination.wing_name}",
                "originWingId": str(origin.id),
                "destinationWingId": str(destination.id),
                "originName": origin.wing_name,
                "destinationName": destination.wing_name,
                "origin": {"lat": origin.map_lat, "lng": origin.map_lng},
                "destination": {"lat": destination.map_lat, "lng": destination.map_lng},
                "path": path,
                "distanceM": transport.distance_m,
                "durationMin": transport.duration_min,
                "routeMode": transport.route_mode,
                "productName": product.product_name if product else None,
                "vehicleName": vehicle.vehicle_name if vehicle else None,
                "quantity": transport.quantity,
            }
        )
    return routes
