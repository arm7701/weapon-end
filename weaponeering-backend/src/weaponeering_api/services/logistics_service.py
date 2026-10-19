from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.models import Scenario, User
from weaponeering_api.models.logistics import (
    Depot,
    DepotInventoryItem,
    Organization,
    PlanScore,
    PlatformReadinessEvent,
    PlatformType,
    ResourceToken,
    RouteSegment,
    SimulatedPlatform,
    TransportAsset,
)
from weaponeering_api.schemas.logistics import (
    DepotCreate,
    DepotInventoryCreate,
    DepotInventoryUpdate,
    DepotUpdate,
    OrganizationCreate,
    OrganizationUpdate,
    PlanScoreCreate,
    PlatformReadinessIn,
    PlatformTypeCreate,
    PlatformTypeUpdate,
    ResourceTokenCreate,
    ResourceTokenUpdate,
    RouteSegmentCreate,
    RouteSegmentUpdate,
    SimulatedPlatformCreate,
    SimulatedPlatformUpdate,
    TransportAssetCreate,
    TransportAssetUpdate,
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


# --- Organizations ---


async def list_organizations(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[Organization]:
    stmt = select(Organization).order_by(Organization.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(Organization.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_organization(
    db: AsyncSession, body: OrganizationCreate, user: User
) -> Organization:
    await _ensure_scenario(db, body.scenario_id)
    row = Organization(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="organization.create",
        entity_type="organization",
        entity_id=str(row.id),
        details={"scenario_id": str(body.scenario_id), "name": body.name},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_organization(db: AsyncSession, org_id: uuid.UUID) -> Organization | None:
    return await db.get(Organization, org_id)


async def update_organization(
    db: AsyncSession, row: Organization, body: OrganizationUpdate, user: User
) -> Organization:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="organization.update",
        entity_type="organization",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_organization(db: AsyncSession, row: Organization, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="organization.delete",
        entity_type="organization",
        entity_id=entity_id,
        details={},
    )
    await db.commit()


# --- Platform types ---


async def list_platform_types(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[PlatformType]:
    stmt = select(PlatformType).order_by(PlatformType.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(PlatformType.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_platform_type(
    db: AsyncSession, body: PlatformTypeCreate, user: User
) -> PlatformType:
    await _ensure_scenario(db, body.scenario_id)
    row = PlatformType(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="platform_type.create",
        entity_type="platform_type",
        entity_id=str(row.id),
        details={"scenario_id": str(body.scenario_id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_platform_type(db: AsyncSession, type_id: uuid.UUID) -> PlatformType | None:
    return await db.get(PlatformType, type_id)


async def update_platform_type(
    db: AsyncSession, row: PlatformType, body: PlatformTypeUpdate, user: User
) -> PlatformType:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="platform_type.update",
        entity_type="platform_type",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_platform_type(db: AsyncSession, row: PlatformType, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="platform_type.delete",
        entity_type="platform_type",
        entity_id=entity_id,
        details={},
    )
    await db.commit()


# --- Simulated platforms ---


async def list_simulated_platforms(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[SimulatedPlatform]:
    stmt = select(SimulatedPlatform).order_by(SimulatedPlatform.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(SimulatedPlatform.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_simulated_platform(
    db: AsyncSession, body: SimulatedPlatformCreate, user: User
) -> SimulatedPlatform:
    await _ensure_scenario(db, body.scenario_id)
    row = SimulatedPlatform(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="simulated_platform.create",
        entity_type="simulated_platform",
        entity_id=str(row.id),
        details={"scenario_id": str(body.scenario_id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_simulated_platform(
    db: AsyncSession, platform_id: uuid.UUID
) -> SimulatedPlatform | None:
    return await db.get(SimulatedPlatform, platform_id)


async def update_simulated_platform(
    db: AsyncSession, row: SimulatedPlatform, body: SimulatedPlatformUpdate, user: User
) -> SimulatedPlatform:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="simulated_platform.update",
        entity_type="simulated_platform",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_simulated_platform(
    db: AsyncSession, row: SimulatedPlatform, user: User
) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="simulated_platform.delete",
        entity_type="simulated_platform",
        entity_id=entity_id,
        details={},
    )
    await db.commit()


async def add_platform_readiness(
    db: AsyncSession,
    platform: SimulatedPlatform,
    body: PlatformReadinessIn,
    user: User,
) -> PlatformReadinessEvent:
    event = PlatformReadinessEvent(
        id=uuid.uuid4(),
        simulated_platform_id=platform.id,
        status=body.status,
        readiness_score=body.readiness_score,
        reason=body.reason,
    )
    platform.readiness_status = body.status
    platform.readiness_note = body.reason
    db.add(event)
    await write_audit(
        db,
        actor=user.username,
        event_type="platform_readiness.create",
        entity_type="platform_readiness_event",
        entity_id=str(event.id),
        details={"platform_id": str(platform.id), "status": body.status},
    )
    await db.commit()
    await db.refresh(event)
    return event


# --- Depots ---


async def list_depots(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[Depot]:
    stmt = select(Depot).order_by(Depot.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(Depot.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_depot(db: AsyncSession, body: DepotCreate, user: User) -> Depot:
    await _ensure_scenario(db, body.scenario_id)
    row = Depot(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="depot.create",
        entity_type="depot",
        entity_id=str(row.id),
        details={"scenario_id": str(body.scenario_id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_depot(db: AsyncSession, depot_id: uuid.UUID) -> Depot | None:
    return await db.get(Depot, depot_id)


async def update_depot(
    db: AsyncSession, row: Depot, body: DepotUpdate, user: User
) -> Depot:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="depot.update",
        entity_type="depot",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_depot(db: AsyncSession, row: Depot, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="depot.delete",
        entity_type="depot",
        entity_id=entity_id,
        details={},
    )
    await db.commit()


# --- Resource tokens ---


async def list_resource_tokens(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[ResourceToken]:
    stmt = select(ResourceToken).order_by(ResourceToken.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(ResourceToken.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_resource_token(
    db: AsyncSession, body: ResourceTokenCreate, user: User
) -> ResourceToken:
    await _ensure_scenario(db, body.scenario_id)
    row = ResourceToken(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="resource_token.create",
        entity_type="resource_token",
        entity_id=str(row.id),
        details={"scenario_id": str(body.scenario_id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_resource_token(db: AsyncSession, token_id: uuid.UUID) -> ResourceToken | None:
    return await db.get(ResourceToken, token_id)


async def update_resource_token(
    db: AsyncSession, row: ResourceToken, body: ResourceTokenUpdate, user: User
) -> ResourceToken:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="resource_token.update",
        entity_type="resource_token",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_resource_token(db: AsyncSession, row: ResourceToken, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="resource_token.delete",
        entity_type="resource_token",
        entity_id=entity_id,
        details={},
    )
    await db.commit()


# --- Depot inventory ---


async def list_depot_inventory(
    db: AsyncSession, *, depot_id: uuid.UUID | None = None
) -> list[DepotInventoryItem]:
    stmt = select(DepotInventoryItem).order_by(DepotInventoryItem.created_at.desc())
    if depot_id is not None:
        stmt = stmt.where(DepotInventoryItem.depot_id == depot_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_depot_inventory(
    db: AsyncSession, body: DepotInventoryCreate, user: User
) -> DepotInventoryItem:
    depot = await db.get(Depot, body.depot_id)
    if depot is None:
        raise ValueError("ไม่พบ depot")
    row = DepotInventoryItem(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="depot_inventory.create",
        entity_type="depot_inventory",
        entity_id=str(row.id),
        details={"depot_id": str(body.depot_id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_depot_inventory(
    db: AsyncSession, item_id: uuid.UUID
) -> DepotInventoryItem | None:
    return await db.get(DepotInventoryItem, item_id)


async def update_depot_inventory(
    db: AsyncSession, row: DepotInventoryItem, body: DepotInventoryUpdate, user: User
) -> DepotInventoryItem:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="depot_inventory.update",
        entity_type="depot_inventory",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_depot_inventory(
    db: AsyncSession, row: DepotInventoryItem, user: User
) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="depot_inventory.delete",
        entity_type="depot_inventory",
        entity_id=entity_id,
        details={},
    )
    await db.commit()


# --- Transport assets ---


async def list_transport_assets(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[TransportAsset]:
    stmt = select(TransportAsset).order_by(TransportAsset.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(TransportAsset.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_transport_asset(
    db: AsyncSession, body: TransportAssetCreate, user: User
) -> TransportAsset:
    await _ensure_scenario(db, body.scenario_id)
    row = TransportAsset(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="transport_asset.create",
        entity_type="transport_asset",
        entity_id=str(row.id),
        details={"scenario_id": str(body.scenario_id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_transport_asset(
    db: AsyncSession, asset_id: uuid.UUID
) -> TransportAsset | None:
    return await db.get(TransportAsset, asset_id)


async def update_transport_asset(
    db: AsyncSession, row: TransportAsset, body: TransportAssetUpdate, user: User
) -> TransportAsset:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="transport_asset.update",
        entity_type="transport_asset",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_transport_asset(
    db: AsyncSession, row: TransportAsset, user: User
) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="transport_asset.delete",
        entity_type="transport_asset",
        entity_id=entity_id,
        details={},
    )
    await db.commit()


# --- Route segments ---


async def list_route_segments(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[RouteSegment]:
    stmt = select(RouteSegment).order_by(RouteSegment.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(RouteSegment.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_route_segment(
    db: AsyncSession, body: RouteSegmentCreate, user: User
) -> RouteSegment:
    await _ensure_scenario(db, body.scenario_id)
    row = RouteSegment(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="route_segment.create",
        entity_type="route_segment",
        entity_id=str(row.id),
        details={"scenario_id": str(body.scenario_id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_route_segment(db: AsyncSession, segment_id: uuid.UUID) -> RouteSegment | None:
    return await db.get(RouteSegment, segment_id)


async def update_route_segment(
    db: AsyncSession, row: RouteSegment, body: RouteSegmentUpdate, user: User
) -> RouteSegment:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="route_segment.update",
        entity_type="route_segment",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_route_segment(db: AsyncSession, row: RouteSegment, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="route_segment.delete",
        entity_type="route_segment",
        entity_id=entity_id,
        details={},
    )
    await db.commit()


# --- Plan scores ---


async def list_plan_scores(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[PlanScore]:
    stmt = select(PlanScore).order_by(PlanScore.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(PlanScore.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_plan_score(
    db: AsyncSession, body: PlanScoreCreate, user: User
) -> PlanScore:
    await _ensure_scenario(db, body.scenario_id)
    row = PlanScore(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="plan_score.create",
        entity_type="plan_score",
        entity_id=str(row.id),
        details={"scenario_id": str(body.scenario_id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_plan_score(db: AsyncSession, score_id: uuid.UUID) -> PlanScore | None:
    return await db.get(PlanScore, score_id)


async def delete_plan_score(db: AsyncSession, row: PlanScore, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="plan_score.delete",
        entity_type="plan_score",
        entity_id=entity_id,
        details={},
    )
    await db.commit()
