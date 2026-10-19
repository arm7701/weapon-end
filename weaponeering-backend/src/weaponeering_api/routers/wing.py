from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.db import get_db
from weaponeering_api.deps.auth import get_current_user
from weaponeering_api.models import User
from weaponeering_api.schemas.wing import (
    AirWingCreate,
    AirWingOut,
    AirWingUpdate,
    WingAircraftCreate,
    WingAircraftOut,
    WingAircraftUpdate,
    WingDepotCreate,
    WingDepotInventoryDetailOut,
    WingDepotInventoryOut,
    WingDepotInventoryUpsert,
    WingDepotOut,
    WingDepotTransferCreate,
    WingDepotTransferDetailOut,
    WingDepotTransferOut,
    WingDepotUpdate,
    WingFlyingUnitCreate,
    WingFlyingUnitOut,
    WingFlyingUnitUpdate,
    WingLogisticsVehicleCreate,
    WingLogisticsVehicleOut,
    WingLogisticsVehicleUpdate,
    WingMapDetailOut,
    WingPilotCreate,
    WingPilotOut,
    WingPilotUpdate,
    WingProductCreate,
    WingProductOut,
    WingProductUpdate,
    KnownProductOut,
    WingTableSummaryOut,
)
from weaponeering_api.services import wing_service
from maap_app.modules.weaponeering.product_catalog import KNOWN_PRODUCTS

router = APIRouter(tags=["wing-data"])


def _not_found(detail: str = "ไม่พบข้อมูล") -> HTTPException:
    return HTTPException(status_code=404, detail=detail)


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


# --- Air wings ---


@router.get("/wings", response_model=list[AirWingOut])
async def list_wings(
    scenario_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default="active", alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AirWingOut]:
    rows = await wing_service.list_wings(db, scenario_id=scenario_id, status=status_filter)
    return [AirWingOut.model_validate(r) for r in rows]


@router.get("/wings/summaries", response_model=list[WingTableSummaryOut])
async def list_wing_summaries(
    scenario_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WingTableSummaryOut]:
    return await wing_service.list_wing_summaries(db, scenario_id)


@router.post("/wings", response_model=AirWingOut, status_code=status.HTTP_201_CREATED)
async def create_wing(
    body: AirWingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AirWingOut:
    try:
        row = await wing_service.create_wing(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return AirWingOut.model_validate(row)


@router.get("/wings/{wing_id}", response_model=AirWingOut)
async def get_wing(
    wing_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AirWingOut:
    row = await wing_service.get_wing(db, wing_id)
    if row is None:
        raise _not_found("ไม่พบกองบิน")
    return AirWingOut.model_validate(row)


@router.get("/wings/{wing_id}/map-detail", response_model=WingMapDetailOut)
async def get_wing_map_detail(
    wing_id: UUID,
    scenario_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> WingMapDetailOut:
    detail = await wing_service.get_wing_map_detail(db, wing_id, scenario_id)
    if detail is None:
        raise _not_found("ไม่พบกองบิน")
    return detail


@router.patch("/wings/{wing_id}", response_model=AirWingOut)
async def update_wing(
    wing_id: UUID,
    body: AirWingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AirWingOut:
    row = await wing_service.get_wing(db, wing_id)
    if row is None:
        raise _not_found("ไม่พบกองบิน")
    updated = await wing_service.update_wing(db, row, body, user)
    return AirWingOut.model_validate(updated)


@router.delete("/wings/{wing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wing(
    wing_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await wing_service.get_wing(db, wing_id)
    if row is None:
        raise _not_found("ไม่พบกองบิน")
    await wing_service.archive_wing(db, row, user)


# --- Flying units ---


@router.get("/flying-units", response_model=list[WingFlyingUnitOut])
async def list_flying_units(
    scenario_id: UUID | None = Query(default=None),
    wing_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default="active", alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WingFlyingUnitOut]:
    rows = await wing_service.list_flying_units(
        db, scenario_id=scenario_id, wing_id=wing_id, status=status_filter
    )
    return [WingFlyingUnitOut.model_validate(r) for r in rows]


@router.post("/flying-units", response_model=WingFlyingUnitOut, status_code=status.HTTP_201_CREATED)
async def create_flying_unit(
    body: WingFlyingUnitCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingFlyingUnitOut:
    try:
        row = await wing_service.create_flying_unit(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return WingFlyingUnitOut.model_validate(row)


@router.patch("/flying-units/{unit_id}", response_model=WingFlyingUnitOut)
async def update_flying_unit(
    unit_id: UUID,
    body: WingFlyingUnitUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingFlyingUnitOut:
    row = await wing_service.get_flying_unit(db, unit_id)
    if row is None:
        raise _not_found("ไม่พบหน่วยบิน")
    try:
        updated = await wing_service.update_flying_unit(db, row, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return WingFlyingUnitOut.model_validate(updated)


@router.delete("/flying-units/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flying_unit(
    unit_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await wing_service.get_flying_unit(db, unit_id)
    if row is None:
        raise _not_found("ไม่พบหน่วยบิน")
    await wing_service.archive_flying_unit(db, row, user)


# --- Aircraft ---


@router.get("/aircraft", response_model=list[WingAircraftOut])
async def list_aircraft(
    scenario_id: UUID | None = Query(default=None),
    wing_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default="active", alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WingAircraftOut]:
    rows = await wing_service.list_aircraft(
        db, scenario_id=scenario_id, wing_id=wing_id, status=status_filter
    )
    return [WingAircraftOut.model_validate(r) for r in rows]


@router.post("/aircraft", response_model=WingAircraftOut, status_code=status.HTTP_201_CREATED)
async def create_aircraft(
    body: WingAircraftCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingAircraftOut:
    try:
        row = await wing_service.create_aircraft(db, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return WingAircraftOut.model_validate(row)


@router.patch("/aircraft/{aircraft_id}", response_model=WingAircraftOut)
async def update_aircraft(
    aircraft_id: UUID,
    body: WingAircraftUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingAircraftOut:
    row = await wing_service.get_aircraft(db, aircraft_id)
    if row is None:
        raise _not_found("ไม่พบอากาศยาน")
    try:
        updated = await wing_service.update_aircraft(db, row, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return WingAircraftOut.model_validate(updated)


@router.delete("/aircraft/{aircraft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_aircraft(
    aircraft_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await wing_service.get_aircraft(db, aircraft_id)
    if row is None:
        raise _not_found("ไม่พบอากาศยาน")
    await wing_service.archive_aircraft(db, row, user)


# --- Pilots ---


@router.get("/pilots", response_model=list[WingPilotOut])
async def list_pilots(
    scenario_id: UUID | None = Query(default=None),
    wing_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default="active", alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WingPilotOut]:
    rows = await wing_service.list_pilots(
        db, scenario_id=scenario_id, wing_id=wing_id, status=status_filter
    )
    return [WingPilotOut.model_validate(r) for r in rows]


@router.post("/pilots", response_model=WingPilotOut, status_code=status.HTTP_201_CREATED)
async def create_pilot(
    body: WingPilotCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingPilotOut:
    try:
        row = await wing_service.create_pilot(db, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return WingPilotOut.model_validate(row)


@router.patch("/pilots/{pilot_id}", response_model=WingPilotOut)
async def update_pilot(
    pilot_id: UUID,
    body: WingPilotUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingPilotOut:
    row = await wing_service.get_pilot(db, pilot_id)
    if row is None:
        raise _not_found("ไม่พบนักบิน")
    try:
        updated = await wing_service.update_pilot(db, row, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return WingPilotOut.model_validate(updated)


@router.delete("/pilots/{pilot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pilot(
    pilot_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await wing_service.get_pilot(db, pilot_id)
    if row is None:
        raise _not_found("ไม่พบนักบิน")
    await wing_service.archive_pilot(db, row, user)


# --- Wing depots ---


@router.get("/wing-depots", response_model=list[WingDepotOut])
async def list_wing_depots(
    scenario_id: UUID | None = Query(default=None),
    wing_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default="active", alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WingDepotOut]:
    rows = await wing_service.list_depots(
        db, scenario_id=scenario_id, wing_id=wing_id, status=status_filter
    )
    return [WingDepotOut.model_validate(r) for r in rows]


@router.post("/wing-depots", response_model=WingDepotOut, status_code=status.HTTP_201_CREATED)
async def create_wing_depot(
    body: WingDepotCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingDepotOut:
    try:
        row = await wing_service.create_depot(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return WingDepotOut.model_validate(row)


@router.patch("/wing-depots/{depot_id}", response_model=WingDepotOut)
async def update_wing_depot(
    depot_id: UUID,
    body: WingDepotUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingDepotOut:
    row = await wing_service.get_depot(db, depot_id)
    if row is None:
        raise _not_found("ไม่พบคลังกองบิน")
    try:
        updated = await wing_service.update_depot(db, row, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return WingDepotOut.model_validate(updated)


@router.delete("/wing-depots/{depot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wing_depot(
    depot_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await wing_service.get_depot(db, depot_id)
    if row is None:
        raise _not_found("ไม่พบคลังกองบิน")
    await wing_service.archive_depot(db, row, user)


# --- Products ---


@router.get("/wing-products/catalog", response_model=list[KnownProductOut])
async def list_known_wing_products(
    _: User = Depends(get_current_user),
) -> list[KnownProductOut]:
    return [
        KnownProductOut(
            key=item.key,
            product_name=item.product_name,
            weight_pounds=item.weight_pounds,
            unit_cost=item.unit_cost,
            description=item.description,
            delivery=item.delivery,
            guidance=item.guidance,
            category=item.category,
            category_label=item.category_label,
        )
        for item in KNOWN_PRODUCTS
    ]


@router.get("/wing-products", response_model=list[WingProductOut])
async def list_wing_products(
    scenario_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default="active", alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WingProductOut]:
    rows = await wing_service.list_products(db, scenario_id=scenario_id, status=status_filter)
    return [WingProductOut.model_validate(r) for r in rows]


@router.post("/wing-products", response_model=WingProductOut, status_code=status.HTTP_201_CREATED)
async def create_wing_product(
    body: WingProductCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingProductOut:
    try:
        row = await wing_service.create_product(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return WingProductOut.model_validate(row)


@router.patch("/wing-products/{product_id}", response_model=WingProductOut)
async def update_wing_product(
    product_id: UUID,
    body: WingProductUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingProductOut:
    row = await wing_service.get_product(db, product_id)
    if row is None:
        raise _not_found("ไม่พบสินค้า")
    updated = await wing_service.update_product(db, row, body, user)
    return WingProductOut.model_validate(updated)


@router.delete("/wing-products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wing_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await wing_service.get_product(db, product_id)
    if row is None:
        raise _not_found("ไม่พบสินค้า")
    await wing_service.archive_product(db, row, user)


# --- Inventory ---


@router.get("/wing-depot-inventory", response_model=list[WingDepotInventoryOut])
async def list_wing_depot_inventory(
    scenario_id: UUID | None = Query(default=None),
    depot_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WingDepotInventoryOut]:
    rows = await wing_service.list_inventory(db, scenario_id=scenario_id, depot_id=depot_id)
    return [WingDepotInventoryOut.model_validate(r) for r in rows]


@router.get("/wing-depot-inventory/details", response_model=list[WingDepotInventoryDetailOut])
async def list_wing_depot_inventory_details(
    scenario_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WingDepotInventoryDetailOut]:
    return await wing_service.list_inventory_details(db, scenario_id=scenario_id)


@router.put("/wing-depot-inventory", response_model=WingDepotInventoryOut)
async def upsert_wing_depot_inventory(
    body: WingDepotInventoryUpsert,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingDepotInventoryOut:
    try:
        row = await wing_service.upsert_inventory(db, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return WingDepotInventoryOut.model_validate(row)


@router.delete("/wing-depot-inventory/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wing_depot_inventory(
    inventory_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await wing_service.get_inventory(db, inventory_id)
    if row is None:
        raise _not_found("ไม่พบสต็อก")
    await wing_service.archive_inventory(db, row, user)


@router.post(
    "/wing-depot-transfers",
    response_model=WingDepotTransferOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_wing_depot_transfer(
    body: WingDepotTransferCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingDepotTransferOut:
    try:
        row = await wing_service.transfer_inventory(db, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return WingDepotTransferOut.model_validate(row)


@router.get("/wing-depot-transfers", response_model=list[WingDepotTransferDetailOut])
async def list_wing_depot_transfers(
    scenario_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WingDepotTransferDetailOut]:
    return await wing_service.list_transfers(db, scenario_id=scenario_id)


# --- Logistics vehicles ---


@router.get("/wing-vehicles", response_model=list[WingLogisticsVehicleOut])
async def list_wing_vehicles(
    scenario_id: UUID | None = Query(default=None),
    wing_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default="active", alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WingLogisticsVehicleOut]:
    rows = await wing_service.list_vehicles(
        db, scenario_id=scenario_id, wing_id=wing_id, status=status_filter
    )
    return [WingLogisticsVehicleOut.model_validate(r) for r in rows]


@router.post(
    "/wing-vehicles",
    response_model=WingLogisticsVehicleOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_wing_vehicle(
    body: WingLogisticsVehicleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingLogisticsVehicleOut:
    try:
        row = await wing_service.create_vehicle(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return WingLogisticsVehicleOut.model_validate(row)


@router.patch("/wing-vehicles/{vehicle_id}", response_model=WingLogisticsVehicleOut)
async def update_wing_vehicle(
    vehicle_id: UUID,
    body: WingLogisticsVehicleUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WingLogisticsVehicleOut:
    row = await wing_service.get_vehicle(db, vehicle_id)
    if row is None:
        raise _not_found("ไม่พบยานพาหนะ")
    try:
        updated = await wing_service.update_vehicle(db, row, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return WingLogisticsVehicleOut.model_validate(updated)


@router.delete("/wing-vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wing_vehicle(
    vehicle_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await wing_service.get_vehicle(db, vehicle_id)
    if row is None:
        raise _not_found("ไม่พบยานพาหนะ")
    await wing_service.archive_vehicle(db, row, user)
