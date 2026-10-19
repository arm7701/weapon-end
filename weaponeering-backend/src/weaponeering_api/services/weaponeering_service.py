from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from weaponeering_api.models import Scenario, User
from weaponeering_api.models.weaponeering import (
    AbstractWeaponeeringOption,
    DeploymentAircraftLine,
    DeploymentWaypoint,
    PlanAssignment,
    PlanOption,
    RankingItem,
    RankingRun,
    ScoringProfile,
    TargetDeploymentPlan,
    TargetWeaponeeringAssessment,
)
from weaponeering_api.schemas.weaponeering import (
    AssessmentCreate,
    DeploymentPlanUpsert,
    PlanAssignmentCreate,
    PlanOptionCreate,
    PlanOptionUpdate,
    RankingItemOverride,
    RankingRunCreate,
    ScoringProfileCreate,
    ScoringProfileUpdate,
    WeaponeeringOptionCreate,
    WeaponeeringOptionUpdate,
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


# --- Weaponeering options ---


async def list_options(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None, status: str | None = "active"
) -> list[AbstractWeaponeeringOption]:
    stmt = select(AbstractWeaponeeringOption).order_by(AbstractWeaponeeringOption.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(AbstractWeaponeeringOption.scenario_id == scenario_id)
    if status is not None:
        stmt = stmt.where(AbstractWeaponeeringOption.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_option(
    db: AsyncSession, body: WeaponeeringOptionCreate, user: User
) -> AbstractWeaponeeringOption:
    await _ensure_scenario(db, body.scenario_id)
    row = AbstractWeaponeeringOption(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db, actor=user.username, event_type="weaponeering_option.create",
        entity_type="abstract_weaponeering_option", entity_id=str(row.id),
        details={"scenario_id": str(body.scenario_id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_option(db: AsyncSession, option_id: uuid.UUID) -> AbstractWeaponeeringOption | None:
    return await db.get(AbstractWeaponeeringOption, option_id)


async def update_option(
    db: AsyncSession, row: AbstractWeaponeeringOption, body: WeaponeeringOptionUpdate, user: User
) -> AbstractWeaponeeringOption:
    _apply_update(row, body)
    await write_audit(
        db, actor=user.username, event_type="weaponeering_option.update",
        entity_type="abstract_weaponeering_option", entity_id=str(row.id), details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_option(db: AsyncSession, row: AbstractWeaponeeringOption, user: User) -> None:
    row.status = "archived"
    await write_audit(
        db, actor=user.username, event_type="weaponeering_option.archive",
        entity_type="abstract_weaponeering_option", entity_id=str(row.id), details={},
    )
    await db.commit()


# --- Assessments ---


async def list_assessments(
    db: AsyncSession, *, target_card_id: uuid.UUID | None = None
) -> list[TargetWeaponeeringAssessment]:
    stmt = select(TargetWeaponeeringAssessment).order_by(TargetWeaponeeringAssessment.created_at.desc())
    if target_card_id is not None:
        stmt = stmt.where(TargetWeaponeeringAssessment.target_card_id == target_card_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_assessment(
    db: AsyncSession, body: AssessmentCreate, user: User
) -> TargetWeaponeeringAssessment:
    row = TargetWeaponeeringAssessment(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db, actor=user.username, event_type="assessment.create",
        entity_type="target_weaponeering_assessment", entity_id=str(row.id),
        details={"target_card_id": str(body.target_card_id)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_assessment(db: AsyncSession, assessment_id: uuid.UUID) -> TargetWeaponeeringAssessment | None:
    return await db.get(TargetWeaponeeringAssessment, assessment_id)


async def delete_assessment(db: AsyncSession, row: TargetWeaponeeringAssessment, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db, actor=user.username, event_type="assessment.delete",
        entity_type="target_weaponeering_assessment", entity_id=entity_id, details={},
    )
    await db.commit()


# --- Deployment plans ---


async def get_deployment_plan_by_target(
    db: AsyncSession, target_card_id: uuid.UUID
) -> TargetDeploymentPlan | None:
    result = await db.execute(
        select(TargetDeploymentPlan)
        .options(
            selectinload(TargetDeploymentPlan.aircraft_lines),
            selectinload(TargetDeploymentPlan.waypoints),
        )
        .where(TargetDeploymentPlan.target_card_id == target_card_id)
    )
    return result.scalar_one_or_none()


async def upsert_deployment_plan(
    db: AsyncSession, body: DeploymentPlanUpsert, user: User
) -> TargetDeploymentPlan:
    await _ensure_scenario(db, body.scenario_id)
    existing = await get_deployment_plan_by_target(db, body.target_card_id)

    plan_data = body.model_dump(exclude={"aircraft_lines", "waypoints"})
    if existing:
        for key, value in plan_data.items():
            setattr(existing, key, value)
        existing.aircraft_lines.clear()
        existing.waypoints.clear()
        plan = existing
    else:
        plan = TargetDeploymentPlan(id=uuid.uuid4(), **plan_data)
        db.add(plan)

    for idx, line in enumerate(body.aircraft_lines):
        plan.aircraft_lines.append(
            DeploymentAircraftLine(
                id=uuid.uuid4(),
                plan_id=plan.id,
                aircraft_id=line.aircraft_id,
                aircraft_count=line.aircraft_count,
                sort_order=idx,
            )
        )
    for idx, wp in enumerate(body.waypoints):
        plan.waypoints.append(
            DeploymentWaypoint(
                id=uuid.uuid4(),
                plan_id=plan.id,
                waypoint_type=wp.waypoint_type,
                label=wp.label,
                lat=wp.lat,
                lng=wp.lng,
                sort_order=idx,
                altitude_ft=wp.altitude_ft,
            )
        )

    await write_audit(
        db, actor=user.username, event_type="deployment_plan.upsert",
        entity_type="target_deployment_plan", entity_id=str(plan.id),
        details={"target_card_id": str(body.target_card_id)},
    )
    await db.commit()
    await db.refresh(plan)
    result = await db.execute(
        select(TargetDeploymentPlan)
        .options(
            selectinload(TargetDeploymentPlan.aircraft_lines),
            selectinload(TargetDeploymentPlan.waypoints),
        )
        .where(TargetDeploymentPlan.id == plan.id)
    )
    return result.scalar_one()


async def delete_deployment_plan(db: AsyncSession, plan: TargetDeploymentPlan, user: User) -> None:
    entity_id = str(plan.id)
    await db.delete(plan)
    await write_audit(
        db, actor=user.username, event_type="deployment_plan.delete",
        entity_type="target_deployment_plan", entity_id=entity_id, details={},
    )
    await db.commit()


# --- Scoring profiles ---


async def list_scoring_profiles(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[ScoringProfile]:
    stmt = select(ScoringProfile).order_by(ScoringProfile.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(ScoringProfile.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_scoring_profile(
    db: AsyncSession, body: ScoringProfileCreate, user: User
) -> ScoringProfile:
    await _ensure_scenario(db, body.scenario_id)
    row = ScoringProfile(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db, actor=user.username, event_type="scoring_profile.create",
        entity_type="scoring_profile", entity_id=str(row.id), details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_scoring_profile(db: AsyncSession, profile_id: uuid.UUID) -> ScoringProfile | None:
    return await db.get(ScoringProfile, profile_id)


async def update_scoring_profile(
    db: AsyncSession, row: ScoringProfile, body: ScoringProfileUpdate, user: User
) -> ScoringProfile:
    _apply_update(row, body)
    await write_audit(
        db, actor=user.username, event_type="scoring_profile.update",
        entity_type="scoring_profile", entity_id=str(row.id), details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_scoring_profile(db: AsyncSession, row: ScoringProfile, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db, actor=user.username, event_type="scoring_profile.delete",
        entity_type="scoring_profile", entity_id=entity_id, details={},
    )
    await db.commit()


# --- Ranking runs ---


async def list_ranking_runs(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[RankingRun]:
    stmt = select(RankingRun).order_by(RankingRun.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(RankingRun.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_ranking_run(
    db: AsyncSession, body: RankingRunCreate, user: User
) -> RankingRun:
    await _ensure_scenario(db, body.scenario_id)
    row = RankingRun(
        id=uuid.uuid4(),
        scenario_id=body.scenario_id,
        ruleset_version=body.ruleset_version,
        scoring_profile_id=body.scoring_profile_id,
        generated_by=user.username,
    )
    db.add(row)
    await write_audit(
        db, actor=user.username, event_type="ranking_run.create",
        entity_type="ranking_run", entity_id=str(row.id), details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_ranking_run(db: AsyncSession, run_id: uuid.UUID) -> RankingRun | None:
    result = await db.execute(
        select(RankingRun).options(selectinload(RankingRun.items)).where(RankingRun.id == run_id)
    )
    return result.scalar_one_or_none()


async def delete_ranking_run(db: AsyncSession, row: RankingRun, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db, actor=user.username, event_type="ranking_run.delete",
        entity_type="ranking_run", entity_id=entity_id, details={},
    )
    await db.commit()


async def override_ranking_item(
    db: AsyncSession, item: RankingItem, body: RankingItemOverride, user: User
) -> RankingItem:
    item.override_rank_order = body.new_rank_order
    item.override_notes = body.notes
    item.review_status = "overridden"
    await write_audit(
        db, actor=user.username, event_type="ranking_item.override",
        entity_type="ranking_item", entity_id=str(item.id),
        details={"new_rank_order": body.new_rank_order},
    )
    await db.commit()
    await db.refresh(item)
    return item


async def get_ranking_item(db: AsyncSession, item_id: uuid.UUID) -> RankingItem | None:
    return await db.get(RankingItem, item_id)


# --- Plan options ---


async def list_plan_options(
    db: AsyncSession, *, scenario_id: uuid.UUID | None = None
) -> list[PlanOption]:
    stmt = select(PlanOption).order_by(PlanOption.created_at.desc())
    if scenario_id is not None:
        stmt = stmt.where(PlanOption.scenario_id == scenario_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_plan_option(
    db: AsyncSession, body: PlanOptionCreate, user: User
) -> PlanOption:
    await _ensure_scenario(db, body.scenario_id)
    row = PlanOption(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db, actor=user.username, event_type="plan_option.create",
        entity_type="plan_option", entity_id=str(row.id), details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_plan_option(db: AsyncSession, option_id: uuid.UUID) -> PlanOption | None:
    return await db.get(PlanOption, option_id)


async def update_plan_option(
    db: AsyncSession, row: PlanOption, body: PlanOptionUpdate, user: User
) -> PlanOption:
    _apply_update(row, body)
    await write_audit(
        db, actor=user.username, event_type="plan_option.update",
        entity_type="plan_option", entity_id=str(row.id), details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_plan_option(db: AsyncSession, row: PlanOption, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db, actor=user.username, event_type="plan_option.delete",
        entity_type="plan_option", entity_id=entity_id, details={},
    )
    await db.commit()


# --- Plan assignments ---


async def list_plan_assignments(
    db: AsyncSession, *, plan_option_id: uuid.UUID | None = None
) -> list[PlanAssignment]:
    stmt = select(PlanAssignment).order_by(PlanAssignment.created_at.desc())
    if plan_option_id is not None:
        stmt = stmt.where(PlanAssignment.plan_option_id == plan_option_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_plan_assignment(
    db: AsyncSession, body: PlanAssignmentCreate, user: User
) -> PlanAssignment:
    plan = await get_plan_option(db, body.plan_option_id)
    if plan is None:
        raise ValueError("ไม่พบ plan option")
    row = PlanAssignment(id=uuid.uuid4(), **body.model_dump())
    db.add(row)
    await write_audit(
        db, actor=user.username, event_type="plan_assignment.create",
        entity_type="plan_assignment", entity_id=str(row.id), details={},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def get_plan_assignment(db: AsyncSession, assignment_id: uuid.UUID) -> PlanAssignment | None:
    return await db.get(PlanAssignment, assignment_id)


async def delete_plan_assignment(db: AsyncSession, row: PlanAssignment, user: User) -> None:
    entity_id = str(row.id)
    await db.delete(row)
    await write_audit(
        db, actor=user.username, event_type="plan_assignment.delete",
        entity_type="plan_assignment", entity_id=entity_id, details={},
    )
    await db.commit()
