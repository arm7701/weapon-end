from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.db import get_db
from weaponeering_api.deps.auth import get_current_user
from weaponeering_api.models import User
from weaponeering_api.schemas.logistics import (
    DepotCreate,
    DepotInventoryCreate,
    DepotInventoryOut,
    DepotInventoryUpdate,
    DepotOut,
    DepotUpdate,
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
    PlanScoreCreate,
    PlanScoreOut,
    PlatformReadinessIn,
    PlatformReadinessOut,
    PlatformTypeCreate,
    PlatformTypeOut,
    PlatformTypeUpdate,
    ResourceTokenCreate,
    ResourceTokenOut,
    ResourceTokenUpdate,
    RouteSegmentCreate,
    RouteSegmentOut,
    RouteSegmentUpdate,
    SimulatedPlatformCreate,
    SimulatedPlatformOut,
    SimulatedPlatformUpdate,
    TransportAssetCreate,
    TransportAssetOut,
    TransportAssetUpdate,
)
from weaponeering_api.services import logistics_service

router = APIRouter(tags=["logistics"])


def _not_found(detail: str = "ไม่พบข้อมูล") -> HTTPException:
    return HTTPException(status_code=404, detail=detail)


# --- Organizations ---


@router.get("/organizations", response_model=list[OrganizationOut])
async def list_organizations(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[OrganizationOut]:
    rows = await logistics_service.list_organizations(db, scenario_id=scenario_id)
    return [OrganizationOut.model_validate(r) for r in rows]


@router.post("/organizations", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrganizationOut:
    try:
        row = await logistics_service.create_organization(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return OrganizationOut.model_validate(row)


@router.get("/organizations/{org_id}", response_model=OrganizationOut)
async def get_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OrganizationOut:
    row = await logistics_service.get_organization(db, org_id)
    if row is None:
        raise _not_found("ไม่พบ organization")
    return OrganizationOut.model_validate(row)


@router.patch("/organizations/{org_id}", response_model=OrganizationOut)
async def update_organization(
    org_id: UUID,
    body: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrganizationOut:
    row = await logistics_service.get_organization(db, org_id)
    if row is None:
        raise _not_found("ไม่พบ organization")
    updated = await logistics_service.update_organization(db, row, body, user)
    return OrganizationOut.model_validate(updated)


@router.delete("/organizations/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await logistics_service.get_organization(db, org_id)
    if row is None:
        raise _not_found("ไม่พบ organization")
    await logistics_service.delete_organization(db, row, user)


# --- Platform types ---


@router.get("/platform-types", response_model=list[PlatformTypeOut])
async def list_platform_types(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PlatformTypeOut]:
    rows = await logistics_service.list_platform_types(db, scenario_id=scenario_id)
    return [PlatformTypeOut.model_validate(r) for r in rows]


@router.post("/platform-types", response_model=PlatformTypeOut, status_code=status.HTTP_201_CREATED)
async def create_platform_type(
    body: PlatformTypeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlatformTypeOut:
    try:
        row = await logistics_service.create_platform_type(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return PlatformTypeOut.model_validate(row)


@router.get("/platform-types/{type_id}", response_model=PlatformTypeOut)
async def get_platform_type(
    type_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PlatformTypeOut:
    row = await logistics_service.get_platform_type(db, type_id)
    if row is None:
        raise _not_found("ไม่พบ platform type")
    return PlatformTypeOut.model_validate(row)


@router.patch("/platform-types/{type_id}", response_model=PlatformTypeOut)
async def update_platform_type(
    type_id: UUID,
    body: PlatformTypeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlatformTypeOut:
    row = await logistics_service.get_platform_type(db, type_id)
    if row is None:
        raise _not_found("ไม่พบ platform type")
    updated = await logistics_service.update_platform_type(db, row, body, user)
    return PlatformTypeOut.model_validate(updated)


@router.delete("/platform-types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform_type(
    type_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await logistics_service.get_platform_type(db, type_id)
    if row is None:
        raise _not_found("ไม่พบ platform type")
    await logistics_service.delete_platform_type(db, row, user)


# --- Simulated platforms ---


@router.get("/platforms", response_model=list[SimulatedPlatformOut])
async def list_platforms(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SimulatedPlatformOut]:
    rows = await logistics_service.list_simulated_platforms(db, scenario_id=scenario_id)
    return [SimulatedPlatformOut.model_validate(r) for r in rows]


@router.post("/platforms", response_model=SimulatedPlatformOut, status_code=status.HTTP_201_CREATED)
async def create_platform(
    body: SimulatedPlatformCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SimulatedPlatformOut:
    try:
        row = await logistics_service.create_simulated_platform(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return SimulatedPlatformOut.model_validate(row)


@router.get("/platforms/{platform_id}", response_model=SimulatedPlatformOut)
async def get_platform(
    platform_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SimulatedPlatformOut:
    row = await logistics_service.get_simulated_platform(db, platform_id)
    if row is None:
        raise _not_found("ไม่พบ platform")
    return SimulatedPlatformOut.model_validate(row)


@router.patch("/platforms/{platform_id}", response_model=SimulatedPlatformOut)
async def update_platform(
    platform_id: UUID,
    body: SimulatedPlatformUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SimulatedPlatformOut:
    row = await logistics_service.get_simulated_platform(db, platform_id)
    if row is None:
        raise _not_found("ไม่พบ platform")
    updated = await logistics_service.update_simulated_platform(db, row, body, user)
    return SimulatedPlatformOut.model_validate(updated)


@router.delete("/platforms/{platform_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform(
    platform_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await logistics_service.get_simulated_platform(db, platform_id)
    if row is None:
        raise _not_found("ไม่พบ platform")
    await logistics_service.delete_simulated_platform(db, row, user)


@router.post(
    "/platforms/{platform_id}/readiness",
    response_model=PlatformReadinessOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_platform_readiness(
    platform_id: UUID,
    body: PlatformReadinessIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlatformReadinessOut:
    row = await logistics_service.get_simulated_platform(db, platform_id)
    if row is None:
        raise _not_found("ไม่พบ platform")
    event = await logistics_service.add_platform_readiness(db, row, body, user)
    return PlatformReadinessOut.model_validate(event)


# --- Depots ---


@router.get("/depots", response_model=list[DepotOut])
async def list_depots(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DepotOut]:
    rows = await logistics_service.list_depots(db, scenario_id=scenario_id)
    return [DepotOut.model_validate(r) for r in rows]


@router.post("/depots", response_model=DepotOut, status_code=status.HTTP_201_CREATED)
async def create_depot(
    body: DepotCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DepotOut:
    try:
        row = await logistics_service.create_depot(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return DepotOut.model_validate(row)


@router.get("/depots/{depot_id}", response_model=DepotOut)
async def get_depot(
    depot_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DepotOut:
    row = await logistics_service.get_depot(db, depot_id)
    if row is None:
        raise _not_found("ไม่พบ depot")
    return DepotOut.model_validate(row)


@router.patch("/depots/{depot_id}", response_model=DepotOut)
async def update_depot(
    depot_id: UUID,
    body: DepotUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DepotOut:
    row = await logistics_service.get_depot(db, depot_id)
    if row is None:
        raise _not_found("ไม่พบ depot")
    updated = await logistics_service.update_depot(db, row, body, user)
    return DepotOut.model_validate(updated)


@router.delete("/depots/{depot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_depot(
    depot_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await logistics_service.get_depot(db, depot_id)
    if row is None:
        raise _not_found("ไม่พบ depot")
    await logistics_service.delete_depot(db, row, user)


# --- Resource tokens ---


@router.get("/resource-tokens", response_model=list[ResourceTokenOut])
async def list_resource_tokens(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ResourceTokenOut]:
    rows = await logistics_service.list_resource_tokens(db, scenario_id=scenario_id)
    return [ResourceTokenOut.model_validate(r) for r in rows]


@router.post("/resource-tokens", response_model=ResourceTokenOut, status_code=status.HTTP_201_CREATED)
async def create_resource_token(
    body: ResourceTokenCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResourceTokenOut:
    try:
        row = await logistics_service.create_resource_token(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return ResourceTokenOut.model_validate(row)


@router.get("/resource-tokens/{token_id}", response_model=ResourceTokenOut)
async def get_resource_token(
    token_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ResourceTokenOut:
    row = await logistics_service.get_resource_token(db, token_id)
    if row is None:
        raise _not_found("ไม่พบ resource token")
    return ResourceTokenOut.model_validate(row)


@router.patch("/resource-tokens/{token_id}", response_model=ResourceTokenOut)
async def update_resource_token(
    token_id: UUID,
    body: ResourceTokenUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResourceTokenOut:
    row = await logistics_service.get_resource_token(db, token_id)
    if row is None:
        raise _not_found("ไม่พบ resource token")
    updated = await logistics_service.update_resource_token(db, row, body, user)
    return ResourceTokenOut.model_validate(updated)


@router.delete("/resource-tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource_token(
    token_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await logistics_service.get_resource_token(db, token_id)
    if row is None:
        raise _not_found("ไม่พบ resource token")
    await logistics_service.delete_resource_token(db, row, user)


# --- Depot inventory ---


@router.get("/depot-inventory", response_model=list[DepotInventoryOut])
async def list_depot_inventory(
    depot_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DepotInventoryOut]:
    rows = await logistics_service.list_depot_inventory(db, depot_id=depot_id)
    return [DepotInventoryOut.model_validate(r) for r in rows]


@router.post("/depot-inventory", response_model=DepotInventoryOut, status_code=status.HTTP_201_CREATED)
async def create_depot_inventory(
    body: DepotInventoryCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DepotInventoryOut:
    try:
        row = await logistics_service.create_depot_inventory(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return DepotInventoryOut.model_validate(row)


@router.patch("/depot-inventory/{item_id}", response_model=DepotInventoryOut)
async def update_depot_inventory(
    item_id: UUID,
    body: DepotInventoryUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DepotInventoryOut:
    row = await logistics_service.get_depot_inventory(db, item_id)
    if row is None:
        raise _not_found("ไม่พบ inventory item")
    updated = await logistics_service.update_depot_inventory(db, row, body, user)
    return DepotInventoryOut.model_validate(updated)


@router.delete("/depot-inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_depot_inventory(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await logistics_service.get_depot_inventory(db, item_id)
    if row is None:
        raise _not_found("ไม่พบ inventory item")
    await logistics_service.delete_depot_inventory(db, row, user)


# --- Transport assets ---


@router.get("/transport-assets", response_model=list[TransportAssetOut])
async def list_transport_assets(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TransportAssetOut]:
    rows = await logistics_service.list_transport_assets(db, scenario_id=scenario_id)
    return [TransportAssetOut.model_validate(r) for r in rows]


@router.post("/transport-assets", response_model=TransportAssetOut, status_code=status.HTTP_201_CREATED)
async def create_transport_asset(
    body: TransportAssetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TransportAssetOut:
    try:
        row = await logistics_service.create_transport_asset(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return TransportAssetOut.model_validate(row)


@router.get("/transport-assets/{asset_id}", response_model=TransportAssetOut)
async def get_transport_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TransportAssetOut:
    row = await logistics_service.get_transport_asset(db, asset_id)
    if row is None:
        raise _not_found("ไม่พบ transport asset")
    return TransportAssetOut.model_validate(row)


@router.patch("/transport-assets/{asset_id}", response_model=TransportAssetOut)
async def update_transport_asset(
    asset_id: UUID,
    body: TransportAssetUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TransportAssetOut:
    row = await logistics_service.get_transport_asset(db, asset_id)
    if row is None:
        raise _not_found("ไม่พบ transport asset")
    updated = await logistics_service.update_transport_asset(db, row, body, user)
    return TransportAssetOut.model_validate(updated)


@router.delete("/transport-assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transport_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await logistics_service.get_transport_asset(db, asset_id)
    if row is None:
        raise _not_found("ไม่พบ transport asset")
    await logistics_service.delete_transport_asset(db, row, user)


# --- Route segments ---


@router.get("/route-segments", response_model=list[RouteSegmentOut])
async def list_route_segments(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[RouteSegmentOut]:
    rows = await logistics_service.list_route_segments(db, scenario_id=scenario_id)
    return [RouteSegmentOut.model_validate(r) for r in rows]


@router.post("/route-segments", response_model=RouteSegmentOut, status_code=status.HTTP_201_CREATED)
async def create_route_segment(
    body: RouteSegmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RouteSegmentOut:
    try:
        row = await logistics_service.create_route_segment(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return RouteSegmentOut.model_validate(row)


@router.get("/route-segments/{segment_id}", response_model=RouteSegmentOut)
async def get_route_segment(
    segment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RouteSegmentOut:
    row = await logistics_service.get_route_segment(db, segment_id)
    if row is None:
        raise _not_found("ไม่พบ route segment")
    return RouteSegmentOut.model_validate(row)


@router.patch("/route-segments/{segment_id}", response_model=RouteSegmentOut)
async def update_route_segment(
    segment_id: UUID,
    body: RouteSegmentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RouteSegmentOut:
    row = await logistics_service.get_route_segment(db, segment_id)
    if row is None:
        raise _not_found("ไม่พบ route segment")
    updated = await logistics_service.update_route_segment(db, row, body, user)
    return RouteSegmentOut.model_validate(updated)


@router.delete("/route-segments/{segment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route_segment(
    segment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await logistics_service.get_route_segment(db, segment_id)
    if row is None:
        raise _not_found("ไม่พบ route segment")
    await logistics_service.delete_route_segment(db, row, user)


# --- Plan scores ---


@router.get("/plan-scores", response_model=list[PlanScoreOut])
async def list_plan_scores(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PlanScoreOut]:
    rows = await logistics_service.list_plan_scores(db, scenario_id=scenario_id)
    return [PlanScoreOut.model_validate(r) for r in rows]


@router.post("/plan-scores", response_model=PlanScoreOut, status_code=status.HTTP_201_CREATED)
async def create_plan_score(
    body: PlanScoreCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlanScoreOut:
    try:
        row = await logistics_service.create_plan_score(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return PlanScoreOut.model_validate(row)


@router.delete("/plan-scores/{score_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan_score(
    score_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await logistics_service.get_plan_score(db, score_id)
    if row is None:
        raise _not_found("ไม่พบ plan score")
    await logistics_service.delete_plan_score(db, row, user)
