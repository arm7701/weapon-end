from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from weaponeering_api.models import Scenario, User
from weaponeering_api.models.detection import (
    ScenarioGroundTransport,
    ScenarioTeamMarker,
    TargetMapDetectionObject,
    TargetMapDetectionRun,
)
from weaponeering_api.models.target import TargetCard, TargetCoordinate
from weaponeering_api.schemas.detection import (
    DetectionMapObjectOut,
    DetectionRunUpsert,
    GroundTransportCreate,
    GroundTransportUpdate,
    TeamMarkerCreate,
    TeamMarkerUpdate,
)
from weaponeering_api.services.auth_persist import write_audit


async def _ensure_scenario(db: AsyncSession, scenario_id: uuid.UUID) -> Scenario:
    scenario = await db.get(Scenario, scenario_id)
    if scenario is None:
        raise ValueError("ไม่พบ scenario")
    return scenario


def _apply_update(row: Any, body: BaseModel) -> None:
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)


async def _load_run(db: AsyncSession, run_id: uuid.UUID) -> TargetMapDetectionRun | None:
    result = await db.execute(
        select(TargetMapDetectionRun)
        .options(selectinload(TargetMapDetectionRun.objects))
        .where(TargetMapDetectionRun.id == run_id)
    )
    return result.scalar_one_or_none()


# --- Detection ---


async def list_detection_runs(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    target_card_id: uuid.UUID | None = None,
) -> list[TargetMapDetectionRun]:
    stmt = (
        select(TargetMapDetectionRun)
        .options(selectinload(TargetMapDetectionRun.objects))
        .order_by(TargetMapDetectionRun.updated_at.desc())
    )
    if scenario_id is not None:
        stmt = stmt.where(TargetMapDetectionRun.scenario_id == scenario_id)
    if target_card_id is not None:
        stmt = stmt.where(TargetMapDetectionRun.target_card_id == target_card_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_detection_run_for_coordinate(
    db: AsyncSession, target_card_id: uuid.UUID, target_coordinate_id: uuid.UUID
) -> TargetMapDetectionRun | None:
    result = await db.execute(
        select(TargetMapDetectionRun)
        .options(selectinload(TargetMapDetectionRun.objects))
        .where(
            TargetMapDetectionRun.target_card_id == target_card_id,
            TargetMapDetectionRun.target_coordinate_id == target_coordinate_id,
        )
    )
    return result.scalar_one_or_none()


async def get_detection_run(db: AsyncSession, run_id: uuid.UUID) -> TargetMapDetectionRun | None:
    return await _load_run(db, run_id)


async def upsert_detection_run(
    db: AsyncSession, body: DetectionRunUpsert, user: User
) -> TargetMapDetectionRun:
    await _ensure_scenario(db, body.scenario_id)

    target = await db.get(TargetCard, body.target_card_id)
    if target is None or target.scenario_id != body.scenario_id:
        raise ValueError("ไม่พบ Target ใน scenario นี้")

    coord = await db.get(TargetCoordinate, body.target_coordinate_id)
    if coord is None or coord.target_card_id != body.target_card_id:
        raise ValueError("ไม่พบพิกัดของเป้าหมาย")

    existing = await get_detection_run_for_coordinate(
        db, body.target_card_id, body.target_coordinate_id
    )

    if existing:
        existing.model_name = body.model_name
        existing.model_file_name = body.model_file_name
        existing.radius_m = body.radius_m
        existing.capture_radius_m = body.capture_radius_m
        existing.source_image_name = body.source_image_name
        existing.detection_message = body.detection_message
        existing.object_count = len(body.objects)
        existing.objects.clear()
        run = existing
    else:
        run = TargetMapDetectionRun(
            id=uuid.uuid4(),
            scenario_id=body.scenario_id,
            target_card_id=body.target_card_id,
            target_coordinate_id=body.target_coordinate_id,
            model_name=body.model_name,
            model_file_name=body.model_file_name,
            radius_m=body.radius_m,
            capture_radius_m=body.capture_radius_m,
            source_image_name=body.source_image_name,
            detection_message=body.detection_message,
            object_count=len(body.objects),
        )
        db.add(run)

    for idx, obj in enumerate(body.objects):
        run.objects.append(
            TargetMapDetectionObject(
                id=uuid.uuid4(),
                run_id=run.id,
                target_card_id=body.target_card_id,
                map_object_id=obj.map_object_id,
                object_label=obj.object_label,
                object_type=obj.object_type,
                risk_level=obj.risk_level,
                confidence=obj.confidence,
                center_lat=obj.center_lat,
                center_lng=obj.center_lng,
                polygon_json=obj.polygon_json,
                sort_order=obj.sort_order if obj.sort_order else idx,
            )
        )

    await write_audit(
        db,
        actor=user.username,
        event_type="detection_run.upsert",
        entity_type="target_map_detection_run",
        entity_id=str(run.id),
        details={
            "target_card_id": str(body.target_card_id),
            "target_coordinate_id": str(body.target_coordinate_id),
            "object_count": len(body.objects),
        },
    )
    await db.commit()
    loaded = await _load_run(db, run.id)
    assert loaded is not None
    return loaded


async def delete_detection_run(db: AsyncSession, run: TargetMapDetectionRun, user: User) -> None:
    entity_id = str(run.id)
    await db.delete(run)
    await write_audit(
        db,
        actor=user.username,
        event_type="detection_run.delete",
        entity_type="target_map_detection_run",
        entity_id=entity_id,
        details={},
    )
    await db.commit()


async def get_detection_object(
    db: AsyncSession, object_id: uuid.UUID
) -> TargetMapDetectionObject | None:
    return await db.get(TargetMapDetectionObject, object_id)


async def delete_detection_object(
    db: AsyncSession, obj: TargetMapDetectionObject, user: User
) -> int:
    """Delete one building-seg object and refresh parent run counts."""
    run_id = obj.run_id
    object_id = str(obj.id)
    map_object_id = obj.map_object_id
    label = obj.object_label
    await db.delete(obj)
    await db.flush()

    run = await _load_run(db, run_id)
    remaining = len(run.objects) if run is not None else 0
    if run is not None:
        run.object_count = remaining
        run.detection_message = (
            f"ลบอาคารแล้ว · เหลือ {remaining} รายการ (คำนวณทิศทางเข้า-ออกใหม่)"
        )

    await write_audit(
        db,
        actor=user.username,
        event_type="detection_object.delete",
        entity_type="target_map_detection_object",
        entity_id=object_id,
        details={
            "map_object_id": map_object_id,
            "label": label,
            "run_id": str(run_id),
            "remaining": remaining,
        },
    )
    await db.commit()
    return remaining


async def list_detection_map_objects(
    db: AsyncSession, *, scenario_id: uuid.UUID
) -> list[DetectionMapObjectOut]:
    runs = await list_detection_runs(db, scenario_id=scenario_id)
    items: list[DetectionMapObjectOut] = []
    for run in runs:
        for obj in run.objects:
            items.append(
                DetectionMapObjectOut(
                    id=obj.id,
                    run_id=run.id,
                    target_card_id=run.target_card_id,
                    target_coordinate_id=run.target_coordinate_id,
                    map_object_id=obj.map_object_id,
                    object_label=obj.object_label,
                    object_type=obj.object_type,
                    risk_level=obj.risk_level,
                    confidence=obj.confidence,
                    center_lat=obj.center_lat,
                    center_lng=obj.center_lng,
                    polygon_json=obj.polygon_json,
                    model_name=run.model_name,
                    radius_m=run.radius_m,
                )
            )
    return items


# --- Team markers ---


async def list_team_markers(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    side: str | None = None,
) -> list[ScenarioTeamMarker]:
    stmt = select(ScenarioTeamMarker).order_by(ScenarioTeamMarker.created_at.asc())
    if scenario_id is not None:
        stmt = stmt.where(ScenarioTeamMarker.scenario_id == scenario_id)
    if side is not None:
        stmt = stmt.where(ScenarioTeamMarker.side == side)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_team_marker(
    db: AsyncSession, body: TeamMarkerCreate, user: User
) -> ScenarioTeamMarker:
    await _ensure_scenario(db, body.scenario_id)
    row = ScenarioTeamMarker(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="team_marker.create",
        entity_type="scenario_team_marker",
        entity_id=str(row.id),
        details={"side": body.side, "label": body.label},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_team_marker(db: AsyncSession, marker_id: uuid.UUID) -> ScenarioTeamMarker | None:
    return await db.get(ScenarioTeamMarker, marker_id)


async def update_team_marker(
    db: AsyncSession, row: ScenarioTeamMarker, body: TeamMarkerUpdate, user: User
) -> ScenarioTeamMarker:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="team_marker.update",
        entity_type="scenario_team_marker",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_team_marker(db: AsyncSession, row: ScenarioTeamMarker, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="team_marker.delete",
        entity_type="scenario_team_marker",
        entity_id=entity_id,
        details={},
    )
    await db.commit()


# --- Ground transports ---


async def list_ground_transports(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    status: str | None = "active",
) -> list[ScenarioGroundTransport]:
    stmt = select(ScenarioGroundTransport).order_by(ScenarioGroundTransport.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(ScenarioGroundTransport.scenario_id == scenario_id)
    if status is not None:
        stmt = stmt.where(ScenarioGroundTransport.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_ground_transport(
    db: AsyncSession, body: GroundTransportCreate, user: User
) -> ScenarioGroundTransport:
    await _ensure_scenario(db, body.scenario_id)
    if body.origin_wing_id == body.destination_wing_id:
        raise ValueError("ต้นทางและปลายทางต้องไม่ใช่กองบินเดียวกัน")
    row = ScenarioGroundTransport(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="ground_transport.create",
        entity_type="scenario_ground_transport",
        entity_id=str(row.id),
        details={"distance_m": body.distance_m},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_ground_transport(
    db: AsyncSession, transport_id: uuid.UUID
) -> ScenarioGroundTransport | None:
    return await db.get(ScenarioGroundTransport, transport_id)


async def update_ground_transport(
    db: AsyncSession,
    row: ScenarioGroundTransport,
    body: GroundTransportUpdate,
    user: User,
) -> ScenarioGroundTransport:
    data = body.model_dump(exclude_unset=True)
    origin = data.get("origin_wing_id", row.origin_wing_id)
    destination = data.get("destination_wing_id", row.destination_wing_id)
    if origin == destination:
        raise ValueError("ต้นทางและปลายทางต้องไม่ใช่กองบินเดียวกัน")
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="ground_transport.update",
        entity_type="scenario_ground_transport",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_ground_transport(
    db: AsyncSession, row: ScenarioGroundTransport, user: User
) -> None:
    row.status = "archived"
    await write_audit(
        db,
        actor=user.username,
        event_type="ground_transport.archive",
        entity_type="scenario_ground_transport",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
