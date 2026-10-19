from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from weaponeering_api.models import MapNode, Scenario, User
from weaponeering_api.models.target import (
    HumanReviewRecord,
    TargetCard,
    TargetCoordinate,
    TargetRecognitionResult,
)
from weaponeering_api.schemas.target import (
    HumanReviewCreate,
    TargetCardCreate,
    TargetCardUpdate,
    TargetCoordinateIn,
    TargetRecognitionIn,
)
from weaponeering_api.services.auth_persist import write_audit

PROFILE_FIELDS = (
    "target_type",
    "target_subtype",
    "material_class",
    "material_strength",
    "target_description",
    "floor_count",
    "width_m",
    "length_m",
    "height_m",
    "heading_deg",
    "desired_model_result",
    "coordinate_error_m",
    "data_source",
    "cep",
    "target_pk",
    "reference_pk",
    "resistance",
    "capacity",
    "damage_fit",
    "model_version",
    "selected_product_id",
)


async def _ensure_scenario(db: AsyncSession, scenario_id: uuid.UUID) -> Scenario:
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if scenario is None:
        raise ValueError("ไม่พบ scenario")
    return scenario


def _apply_coordinates(card: TargetCard, coordinates: list[TargetCoordinateIn]) -> None:
    card.coordinates.clear()
    if not coordinates:
        return

    has_primary = any(item.is_primary for item in coordinates)
    for index, item in enumerate(coordinates):
        card.coordinates.append(
            TargetCoordinate(
                id=item.id or uuid.uuid4(),
                label=item.label or "",
                map_lat=item.map_lat,
                map_lng=item.map_lng,
                sort_order=index,
                is_primary=item.is_primary if has_primary else index == 0,
                selected_product_id=item.selected_product_id,
            )
        )


async def _sync_primary_map_node(db: AsyncSession, card: TargetCard) -> None:
    primary = next((c for c in card.coordinates if c.is_primary), None)
    if primary is None and card.coordinates:
        primary = card.coordinates[0]
        primary.is_primary = True

    if primary is None:
        if card.map_node_id:
            node = await db.get(MapNode, card.map_node_id)
            if node is not None:
                await db.delete(node)
            card.map_node_id = None
        return

    if card.map_node_id:
        node = await db.get(MapNode, card.map_node_id)
    else:
        node = None

    if node is None:
        node = MapNode(
            id=uuid.uuid4(),
            scenario_id=card.scenario_id,
            label=primary.label or card.label,
            node_type="target",
            map_lat=primary.map_lat,
            map_lng=primary.map_lng,
            review_status=card.review_status,
            linked_entity_type="target_card",
            linked_entity_id=str(card.id),
            is_synthetic_location=True,
        )
        db.add(node)
        await db.flush()
        card.map_node_id = node.id
    else:
        node.label = primary.label or card.label
        node.map_lat = primary.map_lat
        node.map_lng = primary.map_lng
        node.review_status = card.review_status
        node.linked_entity_type = "target_card"
        node.linked_entity_id = str(card.id)


async def get_target(db: AsyncSession, target_id: uuid.UUID) -> TargetCard | None:
    result = await db.execute(
        select(TargetCard)
        .where(TargetCard.id == target_id)
        .options(
            selectinload(TargetCard.coordinates),
            selectinload(TargetCard.recognition_results),
        )
    )
    return result.scalar_one_or_none()


async def list_targets(
    db: AsyncSession,
    *,
    scenario_id: uuid.UUID | None = None,
    status: str | None = None,
    review_status: str | None = None,
) -> list[TargetCard]:
    stmt = select(TargetCard).order_by(TargetCard.updated_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(TargetCard.scenario_id == scenario_id)
    if status:
        stmt = stmt.where(TargetCard.status == status)
    if review_status:
        stmt = stmt.where(TargetCard.review_status == review_status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_target(db: AsyncSession, body: TargetCardCreate, user: User) -> TargetCard:
    await _ensure_scenario(db, body.scenario_id)
    card = TargetCard(
        id=uuid.uuid4(),
        scenario_id=body.scenario_id,
        label=body.label.strip(),
        priority_score=body.priority_score,
        complexity_score=body.complexity_score,
        review_status=body.review_status,
        status=body.status,
    )
    for field in PROFILE_FIELDS:
        setattr(card, field, getattr(body, field))

    _apply_coordinates(card, body.coordinates)
    if body.recognition is not None:
        card.recognition_results.append(_build_recognition(body.recognition))

    db.add(card)
    await db.flush()
    await _sync_primary_map_node(db, card)
    await write_audit(
        db,
        actor=user.username,
        event_type="target.create",
        entity_type="target_card",
        entity_id=str(card.id),
        details={"label": card.label, "scenario_id": str(card.scenario_id)},
    )
    await db.commit()
    return await get_target(db, card.id)  # type: ignore[return-value]


async def update_target(
    db: AsyncSession,
    card: TargetCard,
    body: TargetCardUpdate,
    user: User,
) -> TargetCard:
    data = body.model_dump(exclude_unset=True, exclude={"coordinates"})
    if "material_strength" in data and data["material_strength"] is None:
        data["material_strength"] = {}
    for key, value in data.items():
        setattr(card, key, value)

    if body.coordinates is not None:
        _apply_coordinates(card, body.coordinates)
        await _sync_primary_map_node(db, card)
    elif "label" in data or "review_status" in data:
        await _sync_primary_map_node(db, card)

    await write_audit(
        db,
        actor=user.username,
        event_type="target.update",
        entity_type="target_card",
        entity_id=str(card.id),
        details=data,
    )
    await db.commit()
    return await get_target(db, card.id)  # type: ignore[return-value]


async def delete_target(db: AsyncSession, card: TargetCard, user: User) -> None:
    target_id = str(card.id)
    map_node_id = card.map_node_id
    await db.delete(card)
    if map_node_id:
        node = await db.get(MapNode, map_node_id)
        if node is not None:
            await db.delete(node)
    await write_audit(
        db,
        actor=user.username,
        event_type="target.delete",
        entity_type="target_card",
        entity_id=target_id,
        details={},
    )
    await db.commit()


def _build_recognition(body: TargetRecognitionIn) -> TargetRecognitionResult:
    return TargetRecognitionResult(
        id=uuid.uuid4(),
        source_type=body.source_type,
        recognition_summary=body.recognition_summary,
        recognition_confidence_score=body.recognition_confidence_score,
        missing_data_json=list(body.missing_data_notes),
        generated_by=body.generated_by,
        review_status=body.review_status,
    )


async def add_recognition(
    db: AsyncSession,
    card: TargetCard,
    body: TargetRecognitionIn,
    user: User,
) -> TargetRecognitionResult:
    row = _build_recognition(body)
    row.target_card_id = card.id
    db.add(row)
    await write_audit(
        db,
        actor=user.username,
        event_type="target.recognition.create",
        entity_type="target_recognition_result",
        entity_id=str(row.id),
        details={"target_card_id": str(card.id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def create_review(
    db: AsyncSession,
    body: HumanReviewCreate,
    user: User,
) -> HumanReviewRecord:
    await _ensure_scenario(db, body.scenario_id)
    record = HumanReviewRecord(
        id=uuid.uuid4(),
        scenario_id=body.scenario_id,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        reviewer=user.username,
        decision=body.decision,
        notes=body.notes or "",
    )
    db.add(record)

    if body.entity_type == "target_card" and body.review_status:
        try:
            target_id = uuid.UUID(body.entity_id)
        except ValueError:
            target_id = None
        if target_id:
            card = await db.get(TargetCard, target_id)
            if card is not None:
                card.review_status = body.review_status

    await write_audit(
        db,
        actor=user.username,
        event_type="review.create",
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        details={"decision": body.decision},
    )
    await db.commit()
    await db.refresh(record)
    return record
