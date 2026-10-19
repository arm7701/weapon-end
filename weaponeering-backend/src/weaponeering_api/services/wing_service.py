from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.models import Scenario, User
from weaponeering_api.models.wing import (
    AirWing,
    WingAircraft,
    WingDepot,
    WingDepotInventory,
    WingDepotTransfer,
    WingFlyingUnit,
    WingLogisticsVehicle,
    WingPilot,
    WingProduct,
)
from weaponeering_api.schemas.wing import (
    AirWingCreate,
    AirWingUpdate,
    WingAircraftCreate,
    WingAircraftUpdate,
    WingDepotCreate,
    WingDepotInventoryDetailOut,
    WingDepotInventoryUpsert,
    WingDepotTransferCreate,
    WingDepotTransferDetailOut,
    WingDepotUpdate,
    WingFlyingUnitCreate,
    WingFlyingUnitUpdate,
    WingLogisticsVehicleCreate,
    WingLogisticsVehicleUpdate,
    WingMapDetailOut,
    WingPilotCreate,
    WingPilotUpdate,
    WingProductCreate,
    WingProductUpdate,
    WingTableSummaryOut,
    AirWingOut,
    WingAircraftOut,
    WingFlyingUnitOut,
    WingPilotOut,
)
from weaponeering_api.services.auth_persist import write_audit
from maap_app.modules.weaponeering.product_catalog import catalog_description


async def _ensure_scenario(db: AsyncSession, scenario_id: uuid.UUID) -> Scenario:
    scenario = await db.get(Scenario, scenario_id)
    if scenario is None:
        raise ValueError("ไม่พบ scenario")
    return scenario


def _apply_update(row: Any, body: BaseModel) -> None:
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)


async def _ensure_wing(db: AsyncSession, wing_id: uuid.UUID) -> AirWing:
    wing = await db.get(AirWing, wing_id)
    if wing is None:
        raise ValueError("ไม่พบกองบิน")
    return wing


async def _validate_flying_unit_for_wing(
    db: AsyncSession,
    *,
    flying_unit_id: uuid.UUID | None,
    wing_id: uuid.UUID | None,
    scenario_id: uuid.UUID,
) -> None:
    if flying_unit_id is None:
        return
    unit = await db.get(WingFlyingUnit, flying_unit_id)
    if unit is None or unit.scenario_id != scenario_id:
        raise ValueError("ไม่พบหน่วยบินที่เลือก")
    if wing_id and unit.wing_id != wing_id:
        raise ValueError("หน่วยบินต้องอยู่ภายใต้กองบินเดียวกัน")


# --- Air wings ---


async def list_wings(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    status: str | None = "active",
) -> list[AirWing]:
    stmt = select(AirWing).order_by(AirWing.created_at.asc())
    if scenario_id is not None:
        stmt = stmt.where(AirWing.scenario_id == scenario_id)
    if status is not None:
        stmt = stmt.where(AirWing.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_wing(db: AsyncSession, body: AirWingCreate, user: User) -> AirWing:
    await _ensure_scenario(db, body.scenario_id)
    row = AirWing(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="air_wing.create",
        entity_type="air_wing",
        entity_id=str(row.id),
        details={"scenario_id": str(body.scenario_id), "wing_name": body.wing_name},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_wing(db: AsyncSession, wing_id: uuid.UUID) -> AirWing | None:
    return await db.get(AirWing, wing_id)


async def update_wing(
    db: AsyncSession, row: AirWing, body: AirWingUpdate, user: User
) -> AirWing:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="air_wing.update",
        entity_type="air_wing",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def archive_wing(db: AsyncSession, row: AirWing, user: User) -> None:
    row.status = "archived"
    await write_audit(
        db,
        actor=user.username,
        event_type="air_wing.archive",
        entity_type="air_wing",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()


async def list_wing_summaries(
    db: AsyncSession, scenario_id: uuid.UUID
) -> list[WingTableSummaryOut]:
    wings = await list_wings(db, scenario_id=scenario_id)
    summaries: dict[uuid.UUID, dict[str, Any]] = {
        w.id: {
            "units": 0,
            "aircraft": 0,
            "pilots": 0,
            "depots": 0,
            "products": {},
        }
        for w in wings
    }

    for unit in await list_flying_units(db, scenario_id=scenario_id):
        if unit.wing_id in summaries:
            summaries[unit.wing_id]["units"] += 1
    for aircraft in await list_aircraft(db, scenario_id=scenario_id):
        if aircraft.wing_id in summaries:
            summaries[aircraft.wing_id]["aircraft"] += 1
    for pilot in await list_pilots(db, scenario_id=scenario_id):
        if pilot.wing_id and pilot.wing_id in summaries:
            summaries[pilot.wing_id]["pilots"] += 1

    depots = await list_depots(db, scenario_id=scenario_id)
    depot_to_wing = {}
    for depot in depots:
        depot_to_wing[depot.id] = depot.wing_id
        if depot.wing_id in summaries:
            summaries[depot.wing_id]["depots"] += 1

    for detail in await list_inventory_details(db, scenario_id=scenario_id):
        wing_id = depot_to_wing.get(detail.depot_id)
        if wing_id not in summaries:
            continue
        products = summaries[wing_id]["products"]
        products[detail.product_name] = products.get(detail.product_name, 0) + detail.quantity

    return [
        WingTableSummaryOut(
            wing_id=wing_id,
            flying_unit_count=int(values["units"]),
            aircraft_count=int(values["aircraft"]),
            pilot_count=int(values["pilots"]),
            depot_count=int(values["depots"]),
            product_stock=sorted(values["products"].items(), key=lambda item: item[0].lower()),
        )
        for wing_id, values in summaries.items()
    ]


async def get_wing_map_detail(
    db: AsyncSession, wing_id: uuid.UUID, scenario_id: uuid.UUID
) -> WingMapDetailOut | None:
    wing = await get_wing(db, wing_id)
    if wing is None or wing.scenario_id != scenario_id:
        return None

    flying_units = [
        u for u in await list_flying_units(db, scenario_id=scenario_id) if u.wing_id == wing_id
    ]
    aircraft = [
        a for a in await list_aircraft(db, scenario_id=scenario_id) if a.wing_id == wing_id
    ]
    pilots = [
        p for p in await list_pilots(db, scenario_id=scenario_id) if p.wing_id == wing_id
    ]
    depot_ids = {
        d.id for d in await list_depots(db, scenario_id=scenario_id) if d.wing_id == wing_id
    }
    inventory = [
        row
        for row in await list_inventory_details(db, scenario_id=scenario_id)
        if row.depot_id in depot_ids
    ]
    ready = sum(1 for a in aircraft if a.mission_ready == "ready")
    return WingMapDetailOut(
        wing=AirWingOut.model_validate(wing),
        flying_units=[WingFlyingUnitOut.model_validate(u) for u in flying_units],
        aircraft=[WingAircraftOut.model_validate(a) for a in aircraft],
        pilots=[WingPilotOut.model_validate(p) for p in pilots],
        inventory=inventory,
        aircraft_ready_count=ready,
        aircraft_not_ready_count=len(aircraft) - ready,
    )


# --- Flying units ---


async def list_flying_units(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    wing_id: uuid.UUID | None = None,
    status: str | None = "active",
) -> list[WingFlyingUnit]:
    stmt = select(WingFlyingUnit).order_by(WingFlyingUnit.created_at.asc())
    if scenario_id is not None:
        stmt = stmt.where(WingFlyingUnit.scenario_id == scenario_id)
    if wing_id is not None:
        stmt = stmt.where(WingFlyingUnit.wing_id == wing_id)
    if status is not None:
        stmt = stmt.where(WingFlyingUnit.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_flying_unit(
    db: AsyncSession, body: WingFlyingUnitCreate, user: User
) -> WingFlyingUnit:
    await _ensure_scenario(db, body.scenario_id)
    await _ensure_wing(db, body.wing_id)
    row = WingFlyingUnit(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_flying_unit.create",
        entity_type="wing_flying_unit",
        entity_id=str(row.id),
        details={"unit_name": body.unit_name},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_flying_unit(db: AsyncSession, unit_id: uuid.UUID) -> WingFlyingUnit | None:
    return await db.get(WingFlyingUnit, unit_id)


async def update_flying_unit(
    db: AsyncSession, row: WingFlyingUnit, body: WingFlyingUnitUpdate, user: User
) -> WingFlyingUnit:
    data = body.model_dump(exclude_unset=True)
    if "wing_id" in data and data["wing_id"] is not None:
        await _ensure_wing(db, data["wing_id"])
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_flying_unit.update",
        entity_type="wing_flying_unit",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def archive_flying_unit(db: AsyncSession, row: WingFlyingUnit, user: User) -> None:
    row.status = "archived"
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_flying_unit.archive",
        entity_type="wing_flying_unit",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()


# --- Aircraft ---


async def list_aircraft(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    wing_id: uuid.UUID | None = None,
    status: str | None = "active",
) -> list[WingAircraft]:
    stmt = select(WingAircraft).order_by(WingAircraft.created_at.asc())
    if scenario_id is not None:
        stmt = stmt.where(WingAircraft.scenario_id == scenario_id)
    if wing_id is not None:
        stmt = stmt.where(WingAircraft.wing_id == wing_id)
    if status is not None:
        stmt = stmt.where(WingAircraft.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_aircraft(
    db: AsyncSession, body: WingAircraftCreate, user: User
) -> WingAircraft:
    await _ensure_scenario(db, body.scenario_id)
    await _ensure_wing(db, body.wing_id)
    await _validate_flying_unit_for_wing(
        db,
        flying_unit_id=body.flying_unit_id,
        wing_id=body.wing_id,
        scenario_id=body.scenario_id,
    )
    row = WingAircraft(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_aircraft.create",
        entity_type="wing_aircraft",
        entity_id=str(row.id),
        details={"aircraft_type": body.aircraft_type},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_aircraft(db: AsyncSession, aircraft_id: uuid.UUID) -> WingAircraft | None:
    return await db.get(WingAircraft, aircraft_id)


async def update_aircraft(
    db: AsyncSession, row: WingAircraft, body: WingAircraftUpdate, user: User
) -> WingAircraft:
    data = body.model_dump(exclude_unset=True)
    wing_id = data.get("wing_id", row.wing_id)
    flying_unit_id = data.get("flying_unit_id", row.flying_unit_id)
    if "wing_id" in data and data["wing_id"] is not None:
        await _ensure_wing(db, data["wing_id"])
    await _validate_flying_unit_for_wing(
        db,
        flying_unit_id=flying_unit_id,
        wing_id=wing_id,
        scenario_id=row.scenario_id,
    )
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_aircraft.update",
        entity_type="wing_aircraft",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def archive_aircraft(db: AsyncSession, row: WingAircraft, user: User) -> None:
    row.status = "archived"
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_aircraft.archive",
        entity_type="wing_aircraft",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()


# --- Pilots ---


async def list_pilots(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    wing_id: uuid.UUID | None = None,
    status: str | None = "active",
) -> list[WingPilot]:
    stmt = select(WingPilot).order_by(WingPilot.created_at.asc())
    if scenario_id is not None:
        stmt = stmt.where(WingPilot.scenario_id == scenario_id)
    if wing_id is not None:
        stmt = stmt.where(WingPilot.wing_id == wing_id)
    if status is not None:
        stmt = stmt.where(WingPilot.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_pilot(db: AsyncSession, body: WingPilotCreate, user: User) -> WingPilot:
    await _ensure_scenario(db, body.scenario_id)
    if body.wing_id is not None:
        await _ensure_wing(db, body.wing_id)
    await _validate_flying_unit_for_wing(
        db,
        flying_unit_id=body.flying_unit_id,
        wing_id=body.wing_id,
        scenario_id=body.scenario_id,
    )
    row = WingPilot(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_pilot.create",
        entity_type="wing_pilot",
        entity_id=str(row.id),
        details={"pilot_name": body.pilot_name},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_pilot(db: AsyncSession, pilot_id: uuid.UUID) -> WingPilot | None:
    return await db.get(WingPilot, pilot_id)


async def update_pilot(
    db: AsyncSession, row: WingPilot, body: WingPilotUpdate, user: User
) -> WingPilot:
    data = body.model_dump(exclude_unset=True)
    wing_id = data.get("wing_id", row.wing_id)
    flying_unit_id = data.get("flying_unit_id", row.flying_unit_id)
    if "wing_id" in data and data["wing_id"] is not None:
        await _ensure_wing(db, data["wing_id"])
    await _validate_flying_unit_for_wing(
        db,
        flying_unit_id=flying_unit_id,
        wing_id=wing_id,
        scenario_id=row.scenario_id,
    )
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_pilot.update",
        entity_type="wing_pilot",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def archive_pilot(db: AsyncSession, row: WingPilot, user: User) -> None:
    row.status = "archived"
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_pilot.archive",
        entity_type="wing_pilot",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()


# --- Depots ---


async def list_depots(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    wing_id: uuid.UUID | None = None,
    status: str | None = "active",
) -> list[WingDepot]:
    stmt = select(WingDepot).order_by(WingDepot.created_at.asc())
    if scenario_id is not None:
        stmt = stmt.where(WingDepot.scenario_id == scenario_id)
    if wing_id is not None:
        stmt = stmt.where(WingDepot.wing_id == wing_id)
    if status is not None:
        stmt = stmt.where(WingDepot.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_depot(db: AsyncSession, body: WingDepotCreate, user: User) -> WingDepot:
    await _ensure_scenario(db, body.scenario_id)
    await _ensure_wing(db, body.wing_id)
    row = WingDepot(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_depot.create",
        entity_type="wing_depot",
        entity_id=str(row.id),
        details={"depot_name": body.depot_name},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_depot(db: AsyncSession, depot_id: uuid.UUID) -> WingDepot | None:
    return await db.get(WingDepot, depot_id)


async def update_depot(
    db: AsyncSession, row: WingDepot, body: WingDepotUpdate, user: User
) -> WingDepot:
    data = body.model_dump(exclude_unset=True)
    if "wing_id" in data and data["wing_id"] is not None:
        await _ensure_wing(db, data["wing_id"])
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_depot.update",
        entity_type="wing_depot",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def archive_depot(db: AsyncSession, row: WingDepot, user: User) -> None:
    row.status = "archived"
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_depot.archive",
        entity_type="wing_depot",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()


# --- Products ---


async def list_products(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    status: str | None = "active",
) -> list[WingProduct]:
    stmt = select(WingProduct).order_by(WingProduct.created_at.asc())
    if scenario_id is not None:
        stmt = stmt.where(WingProduct.scenario_id == scenario_id)
    if status is not None:
        stmt = stmt.where(WingProduct.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_product(
    db: AsyncSession, body: WingProductCreate, user: User
) -> WingProduct:
    await _ensure_scenario(db, body.scenario_id)
    data = body.model_dump()
    if not str(data.get("description") or "").strip():
        data["description"] = catalog_description(data["product_name"])
    row = WingProduct(id=uuid.uuid4(), **data)
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_product.create",
        entity_type="wing_product",
        entity_id=str(row.id),
        details={"product_name": body.product_name},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_product(db: AsyncSession, product_id: uuid.UUID) -> WingProduct | None:
    return await db.get(WingProduct, product_id)


async def update_product(
    db: AsyncSession, row: WingProduct, body: WingProductUpdate, user: User
) -> WingProduct:
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_product.update",
        entity_type="wing_product",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def archive_product(db: AsyncSession, row: WingProduct, user: User) -> None:
    row.status = "archived"
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_product.archive",
        entity_type="wing_product",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()


# --- Inventory ---


async def list_inventory(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    depot_id: uuid.UUID | None = None,
    status: str | None = "active",
) -> list[WingDepotInventory]:
    stmt = select(WingDepotInventory).order_by(WingDepotInventory.created_at.asc())
    if scenario_id is not None:
        stmt = stmt.where(WingDepotInventory.scenario_id == scenario_id)
    if depot_id is not None:
        stmt = stmt.where(WingDepotInventory.depot_id == depot_id)
    if status is not None:
        stmt = stmt.where(WingDepotInventory.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_inventory_details(
    db: AsyncSession, *, scenario_id: uuid.UUID
) -> list[WingDepotInventoryDetailOut]:
    stmt = (
        select(
            WingDepotInventory.id,
            WingDepotInventory.scenario_id,
            WingDepotInventory.depot_id,
            WingDepot.depot_name,
            WingDepotInventory.product_id,
            WingProduct.product_name,
            WingDepotInventory.quantity,
        )
        .join(WingDepot, WingDepot.id == WingDepotInventory.depot_id)
        .join(WingProduct, WingProduct.id == WingDepotInventory.product_id)
        .where(
            WingDepotInventory.scenario_id == scenario_id,
            WingDepotInventory.status == "active",
        )
        .order_by(WingDepot.depot_name.asc(), WingProduct.product_name.asc())
    )
    result = await db.execute(stmt)
    return [
        WingDepotInventoryDetailOut(
            id=row.id,
            scenario_id=row.scenario_id,
            depot_id=row.depot_id,
            depot_name=row.depot_name,
            product_id=row.product_id,
            product_name=row.product_name,
            quantity=row.quantity,
        )
        for row in result.all()
    ]


async def get_inventory_row(
    db: AsyncSession, depot_id: uuid.UUID, product_id: uuid.UUID
) -> WingDepotInventory | None:
    result = await db.execute(
        select(WingDepotInventory).where(
            WingDepotInventory.depot_id == depot_id,
            WingDepotInventory.product_id == product_id,
            WingDepotInventory.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def upsert_inventory(
    db: AsyncSession, body: WingDepotInventoryUpsert, user: User
) -> WingDepotInventory:
    await _ensure_scenario(db, body.scenario_id)
    depot = await get_depot(db, body.depot_id)
    if depot is None or depot.scenario_id != body.scenario_id:
        raise ValueError("ไม่พบคลัง")
    product = await get_product(db, body.product_id)
    if product is None or product.scenario_id != body.scenario_id:
        raise ValueError("ไม่พบสินค้า")

    row = await get_inventory_row(db, body.depot_id, body.product_id)
    if row is None:
        row = WingDepotInventory(
            id=uuid.uuid4(),
            scenario_id=body.scenario_id,
            depot_id=body.depot_id,
            product_id=body.product_id,
            quantity=body.quantity,
        )
        db.add(row)
    else:
        row.quantity = body.quantity

    await write_audit(
        db,
        actor=user.username,
        event_type="wing_depot_inventory.upsert",
        entity_type="wing_depot_inventory",
        entity_id=str(row.id),
        details={
            "depot_id": str(body.depot_id),
            "product_id": str(body.product_id),
            "quantity": body.quantity,
        },
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_inventory(db: AsyncSession, inventory_id: uuid.UUID) -> WingDepotInventory | None:
    return await db.get(WingDepotInventory, inventory_id)


async def archive_inventory(db: AsyncSession, row: WingDepotInventory, user: User) -> None:
    row.status = "archived"
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_depot_inventory.archive",
        entity_type="wing_depot_inventory",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()


async def transfer_inventory(
    db: AsyncSession, body: WingDepotTransferCreate, user: User
) -> WingDepotTransfer:
    if body.from_depot_id == body.to_depot_id:
        raise ValueError("คลังต้นทางและปลายทางต้องไม่ใช่คลังเดียวกัน")
    await _ensure_scenario(db, body.scenario_id)

    source = await get_inventory_row(db, body.from_depot_id, body.product_id)
    if source is None or source.quantity < body.quantity:
        raise ValueError("จำนวนสินค้าในคลังต้นทางไม่เพียงพอ")

    dest = await get_inventory_row(db, body.to_depot_id, body.product_id)
    dest_qty = dest.quantity if dest else 0

    source.quantity -= body.quantity
    if dest is None:
        dest = WingDepotInventory(
            id=uuid.uuid4(),
            scenario_id=body.scenario_id,
            depot_id=body.to_depot_id,
            product_id=body.product_id,
            quantity=dest_qty + body.quantity,
        )
        db.add(dest)
    else:
        dest.quantity = dest_qty + body.quantity

    transfer = WingDepotTransfer(
        id=uuid.uuid4(),
        scenario_id=body.scenario_id,
        product_id=body.product_id,
        from_depot_id=body.from_depot_id,
        to_depot_id=body.to_depot_id,
        quantity=body.quantity,
    )
    db.add(transfer)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_depot_inventory.transfer",
        entity_type="wing_depot_transfer",
        entity_id=str(transfer.id),
        details={
            "from_depot_id": str(body.from_depot_id),
            "to_depot_id": str(body.to_depot_id),
            "product_id": str(body.product_id),
            "quantity": body.quantity,
        },
    )
    await db.commit()
    await db.refresh(transfer)
    return transfer


async def list_transfers(
    db: AsyncSession, *, scenario_id: uuid.UUID
) -> list[WingDepotTransferDetailOut]:
    from_depot = WingDepot.__table__.alias("from_depot")
    to_depot = WingDepot.__table__.alias("to_depot")
    stmt = (
        select(
            WingDepotTransfer.id,
            WingDepotTransfer.scenario_id,
            WingDepotTransfer.from_depot_id,
            from_depot.c.depot_name.label("from_depot_name"),
            WingDepotTransfer.to_depot_id,
            to_depot.c.depot_name.label("to_depot_name"),
            WingDepotTransfer.product_id,
            WingProduct.product_name,
            WingDepotTransfer.quantity,
            WingDepotTransfer.created_at,
        )
        .join(from_depot, from_depot.c.id == WingDepotTransfer.from_depot_id)
        .join(to_depot, to_depot.c.id == WingDepotTransfer.to_depot_id)
        .join(WingProduct, WingProduct.id == WingDepotTransfer.product_id)
        .where(WingDepotTransfer.scenario_id == scenario_id)
        .order_by(WingDepotTransfer.created_at.desc())
    )
    result = await db.execute(stmt)
    return [
        WingDepotTransferDetailOut(
            id=row.id,
            scenario_id=row.scenario_id,
            from_depot_id=row.from_depot_id,
            from_depot_name=row.from_depot_name,
            to_depot_id=row.to_depot_id,
            to_depot_name=row.to_depot_name,
            product_id=row.product_id,
            product_name=row.product_name,
            quantity=row.quantity,
            created_at=row.created_at,
        )
        for row in result.all()
    ]


# --- Logistics vehicles ---


async def list_vehicles(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    wing_id: uuid.UUID | None = None,
    status: str | None = "active",
) -> list[WingLogisticsVehicle]:
    stmt = select(WingLogisticsVehicle).order_by(WingLogisticsVehicle.created_at.asc())
    if scenario_id is not None:
        stmt = stmt.where(WingLogisticsVehicle.scenario_id == scenario_id)
    if wing_id is not None:
        stmt = stmt.where(WingLogisticsVehicle.wing_id == wing_id)
    if status is not None:
        stmt = stmt.where(WingLogisticsVehicle.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_vehicle(
    db: AsyncSession, body: WingLogisticsVehicleCreate, user: User
) -> WingLogisticsVehicle:
    await _ensure_scenario(db, body.scenario_id)
    await _ensure_wing(db, body.wing_id)
    row = WingLogisticsVehicle(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_logistics_vehicle.create",
        entity_type="wing_logistics_vehicle",
        entity_id=str(row.id),
        details={"vehicle_name": body.vehicle_name},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_vehicle(
    db: AsyncSession, vehicle_id: uuid.UUID
) -> WingLogisticsVehicle | None:
    return await db.get(WingLogisticsVehicle, vehicle_id)


async def update_vehicle(
    db: AsyncSession,
    row: WingLogisticsVehicle,
    body: WingLogisticsVehicleUpdate,
    user: User,
) -> WingLogisticsVehicle:
    data = body.model_dump(exclude_unset=True)
    if "wing_id" in data and data["wing_id"] is not None:
        await _ensure_wing(db, data["wing_id"])
    _apply_update(row, body)
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_logistics_vehicle.update",
        entity_type="wing_logistics_vehicle",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def archive_vehicle(db: AsyncSession, row: WingLogisticsVehicle, user: User) -> None:
    row.status = "archived"
    await write_audit(
        db,
        actor=user.username,
        event_type="wing_logistics_vehicle.archive",
        entity_type="wing_logistics_vehicle",
        entity_id=str(row.id),
        details={},
    )
    await db.commit()
