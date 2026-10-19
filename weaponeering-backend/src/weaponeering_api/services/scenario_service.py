from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from weaponeering_api.models import LearningObjective, MapNode, Scenario, User
from weaponeering_api.models.wing import WingProduct
from weaponeering_api.schemas.scenario import ScenarioCreate, ScenarioUpdate
from weaponeering_api.services.auth_persist import write_audit
from maap_app.modules.weaponeering.product_catalog import KNOWN_PRODUCTS


async def list_scenarios(db: AsyncSession) -> list[Scenario]:
    result = await db.execute(select(Scenario).order_by(Scenario.updated_at.desc()))
    return list(result.scalars().all())


async def get_scenario(db: AsyncSession, scenario_id: uuid.UUID) -> Scenario | None:
    result = await db.execute(
        select(Scenario)
        .where(Scenario.id == scenario_id)
        .options(
            selectinload(Scenario.learning_objectives),
            selectinload(Scenario.map_nodes),
        )
    )
    return result.scalar_one_or_none()


async def create_scenario(db: AsyncSession, body: ScenarioCreate, user: User) -> Scenario:
    scenario = Scenario(
        id=uuid.uuid4(),
        name=body.name.strip(),
        description=body.description or "",
        status=body.status,
        ruleset_version=body.ruleset_version,
        created_by=user.id,
    )
    for item in body.learning_objectives:
        scenario.learning_objectives.append(
            LearningObjective(
                id=uuid.uuid4(),
                label=item.label.strip(),
                priority=item.priority,
            )
        )
    for node in body.map_nodes:
        scenario.map_nodes.append(
            MapNode(
                id=uuid.uuid4(),
                label=node.label.strip(),
                node_type=node.node_type,
                map_lat=node.map_lat,
                map_lng=node.map_lng,
                review_status=node.review_status,
            )
        )
    db.add(scenario)
    await write_audit(
        db,
        actor=user.username,
        event_type="scenario.create",
        entity_type="scenario",
        entity_id=str(scenario.id),
        details={"name": scenario.name},
    )
    for item in KNOWN_PRODUCTS:
        db.add(
            WingProduct(
                id=uuid.uuid4(),
                scenario_id=scenario.id,
                product_name=item.product_name,
                weight_pounds=item.weight_pounds,
                unit_cost=item.unit_cost,
                description=item.description,
                status="active",
            )
        )
    await db.commit()
    return await get_scenario(db, scenario.id)  # type: ignore[return-value]


async def update_scenario(
    db: AsyncSession,
    scenario: Scenario,
    body: ScenarioUpdate,
    user: User,
) -> Scenario:
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(scenario, key, value)
    await write_audit(
        db,
        actor=user.username,
        event_type="scenario.update",
        entity_type="scenario",
        entity_id=str(scenario.id),
        details=data,
    )
    await db.commit()
    return await get_scenario(db, scenario.id)  # type: ignore[return-value]


async def delete_scenario(db: AsyncSession, scenario: Scenario, user: User) -> None:
    scenario_id = str(scenario.id)
    await db.delete(scenario)
    await write_audit(
        db,
        actor=user.username,
        event_type="scenario.delete",
        entity_type="scenario",
        entity_id=scenario_id,
        details={},
    )
    await db.commit()
