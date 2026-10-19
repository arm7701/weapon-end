from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.db import get_db
from weaponeering_api.deps.auth import get_current_user
from weaponeering_api.models import User
from weaponeering_api.schemas.weaponeering import (
    AssessmentCreate,
    AssessmentOut,
    DeploymentPlanOut,
    DeploymentPlanUpsert,
    PlanAssignmentCreate,
    PlanAssignmentOut,
    PlanOptionCreate,
    PlanOptionOut,
    PlanOptionUpdate,
    RankingItemOut,
    RankingItemOverride,
    RankingRunCreate,
    RankingRunDetailOut,
    RankingRunOut,
    ScoringProfileCreate,
    ScoringProfileOut,
    ScoringProfileUpdate,
    WeaponeeringOptionCreate,
    WeaponeeringOptionOut,
    WeaponeeringOptionUpdate,
)
from weaponeering_api.services import weaponeering_service
from weaponeering_api.services import jmem_service
from weaponeering_api.schemas.jmem import (
    JmemAiAdviceOut,
    JmemSelectProductIn,
    JmemTargetProductsOut,
    JmemWeaponQuantityIn,
    LaserDesignationOut,
    LaserDesignationWorkflowOut,
    CircularErrorMetricOut,
    CircularErrorOut,
    WeaponEffectOut,
    WeaponEffectsOut,
)

router = APIRouter(tags=["weaponeering"])


def _not_found(detail: str = "ไม่พบข้อมูล") -> HTTPException:
    return HTTPException(status_code=404, detail=detail)


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


# --- JMEM product ranking (desktop-compatible) ---


@router.get("/jmem/laser-designation", response_model=LaserDesignationOut)
async def get_laser_designation_doctrine(
    _: User = Depends(get_current_user),
) -> LaserDesignationOut:
    from maap_app.modules.weaponeering.laser_designation import designation_info_for

    info = designation_info_for("GBU-12")
    assert info is not None
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


@router.get("/jmem/weapon-effects", response_model=WeaponEffectsOut)
async def get_weapon_effects_doctrine(
    _: User = Depends(get_current_user),
) -> WeaponEffectsOut:
    from maap_app.modules.weaponeering.weapon_effects import weapon_effects_info

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


@router.get("/jmem/circular-error", response_model=CircularErrorOut)
async def get_circular_error_doctrine(
    _: User = Depends(get_current_user),
) -> CircularErrorOut:
    from maap_app.modules.weaponeering.circular_error import circular_error_info

    info = circular_error_info()
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


@router.get("/jmem/targets/{target_id}", response_model=JmemTargetProductsOut)
async def get_target_jmem_products(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> JmemTargetProductsOut:
    try:
        return await jmem_service.get_target_jmem_products(db, target_id)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc


@router.put("/jmem/targets/{target_id}/selected-product", response_model=JmemTargetProductsOut)
async def select_target_jmem_product(
    target_id: UUID,
    body: JmemSelectProductIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JmemTargetProductsOut:
    try:
        return await jmem_service.select_target_product(
            db,
            target_id,
            product_id=body.product_id,
            coordinate_id=body.coordinate_id,
            user=user,
        )
    except ValueError as exc:
        message = str(exc)
        if "ไม่พบสินค้า" in message or "ไม่พบพิกัด" in message:
            raise _bad_request(message) from exc
        raise _not_found(message) from exc


@router.put("/jmem/targets/{target_id}/weapon-quantity", response_model=JmemTargetProductsOut)
async def set_target_jmem_weapon_quantity(
    target_id: UUID,
    body: JmemWeaponQuantityIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JmemTargetProductsOut:
    try:
        return await jmem_service.set_target_weapon_quantity(
            db,
            target_id,
            quantity=body.quantity,
            coordinate_id=body.coordinate_id,
            user=user,
        )
    except ValueError as exc:
        message = str(exc)
        if "ไม่พบพิกัด" in message:
            raise _bad_request(message) from exc
        raise _not_found(message) from exc


@router.post("/jmem/targets/{target_id}/ai-advise", response_model=JmemAiAdviceOut)
async def ai_advise_target_product(
    target_id: UUID,
    apply: bool = Query(default=False, description="บันทึกสินค้าที่ AI แนะนำลงเป้าหมาย"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JmemAiAdviceOut:
    try:
        return await jmem_service.advise_target_product(
            db,
            target_id,
            apply_recommendation=apply,
            user=user,
        )
    except ValueError as exc:
        message = str(exc)
        if "ไม่มีสินค้า" in message or "ไม่สามารถสร้าง" in message:
            raise _bad_request(message) from exc
        raise _not_found(message) from exc


# --- Weaponeering options ---


@router.get("/weaponeering-options", response_model=list[WeaponeeringOptionOut])
async def list_options(
    scenario_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default="active", alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[WeaponeeringOptionOut]:
    rows = await weaponeering_service.list_options(db, scenario_id=scenario_id, status=status_filter)
    return [WeaponeeringOptionOut.model_validate(r) for r in rows]


@router.post("/weaponeering-options", response_model=WeaponeeringOptionOut, status_code=status.HTTP_201_CREATED)
async def create_option(
    body: WeaponeeringOptionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WeaponeeringOptionOut:
    try:
        row = await weaponeering_service.create_option(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return WeaponeeringOptionOut.model_validate(row)


@router.get("/weaponeering-options/{option_id}", response_model=WeaponeeringOptionOut)
async def get_option(
    option_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> WeaponeeringOptionOut:
    row = await weaponeering_service.get_option(db, option_id)
    if row is None:
        raise _not_found()
    return WeaponeeringOptionOut.model_validate(row)


@router.patch("/weaponeering-options/{option_id}", response_model=WeaponeeringOptionOut)
async def update_option(
    option_id: UUID,
    body: WeaponeeringOptionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WeaponeeringOptionOut:
    row = await weaponeering_service.get_option(db, option_id)
    if row is None:
        raise _not_found()
    updated = await weaponeering_service.update_option(db, row, body, user)
    return WeaponeeringOptionOut.model_validate(updated)


@router.delete("/weaponeering-options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option(
    option_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await weaponeering_service.get_option(db, option_id)
    if row is None:
        raise _not_found()
    await weaponeering_service.delete_option(db, row, user)


# --- Assessments ---


@router.get("/weaponeering-assessments", response_model=list[AssessmentOut])
async def list_assessments(
    target_card_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AssessmentOut]:
    rows = await weaponeering_service.list_assessments(db, target_card_id=target_card_id)
    return [AssessmentOut.model_validate(r) for r in rows]


@router.post("/weaponeering-assessments", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    body: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AssessmentOut:
    row = await weaponeering_service.create_assessment(db, body, user)
    return AssessmentOut.model_validate(row)


@router.delete("/weaponeering-assessments/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await weaponeering_service.get_assessment(db, assessment_id)
    if row is None:
        raise _not_found()
    await weaponeering_service.delete_assessment(db, row, user)


# --- Deployment plans ---


@router.get("/deployment-plans/{target_card_id}", response_model=DeploymentPlanOut)
async def get_deployment_plan(
    target_card_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DeploymentPlanOut:
    plan = await weaponeering_service.get_deployment_plan_by_target(db, target_card_id)
    if plan is None:
        raise _not_found("ไม่พบ deployment plan")
    return DeploymentPlanOut.model_validate(plan)


@router.put("/deployment-plans", response_model=DeploymentPlanOut)
async def upsert_deployment_plan(
    body: DeploymentPlanUpsert,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DeploymentPlanOut:
    try:
        plan = await weaponeering_service.upsert_deployment_plan(db, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return DeploymentPlanOut.model_validate(plan)


@router.delete("/deployment-plans/{target_card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment_plan(
    target_card_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    plan = await weaponeering_service.get_deployment_plan_by_target(db, target_card_id)
    if plan is None:
        raise _not_found("ไม่พบ deployment plan")
    await weaponeering_service.delete_deployment_plan(db, plan, user)


# --- Scoring profiles ---


@router.get("/scoring-profiles", response_model=list[ScoringProfileOut])
async def list_scoring_profiles(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ScoringProfileOut]:
    rows = await weaponeering_service.list_scoring_profiles(db, scenario_id=scenario_id)
    return [ScoringProfileOut.model_validate(r) for r in rows]


@router.post("/scoring-profiles", response_model=ScoringProfileOut, status_code=status.HTTP_201_CREATED)
async def create_scoring_profile(
    body: ScoringProfileCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScoringProfileOut:
    try:
        row = await weaponeering_service.create_scoring_profile(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return ScoringProfileOut.model_validate(row)


@router.patch("/scoring-profiles/{profile_id}", response_model=ScoringProfileOut)
async def update_scoring_profile(
    profile_id: UUID,
    body: ScoringProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScoringProfileOut:
    row = await weaponeering_service.get_scoring_profile(db, profile_id)
    if row is None:
        raise _not_found()
    updated = await weaponeering_service.update_scoring_profile(db, row, body, user)
    return ScoringProfileOut.model_validate(updated)


@router.delete("/scoring-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scoring_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await weaponeering_service.get_scoring_profile(db, profile_id)
    if row is None:
        raise _not_found()
    await weaponeering_service.delete_scoring_profile(db, row, user)


# --- Ranking runs ---


@router.get("/ranking-runs", response_model=list[RankingRunOut])
async def list_ranking_runs(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[RankingRunOut]:
    rows = await weaponeering_service.list_ranking_runs(db, scenario_id=scenario_id)
    return [RankingRunOut.model_validate(r) for r in rows]


@router.post("/ranking-runs", response_model=RankingRunOut, status_code=status.HTTP_201_CREATED)
async def create_ranking_run(
    body: RankingRunCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RankingRunOut:
    try:
        row = await weaponeering_service.create_ranking_run(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return RankingRunOut.model_validate(row)


@router.get("/ranking-runs/{run_id}", response_model=RankingRunDetailOut)
async def get_ranking_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RankingRunDetailOut:
    row = await weaponeering_service.get_ranking_run(db, run_id)
    if row is None:
        raise _not_found()
    return RankingRunDetailOut(
        run=RankingRunOut.model_validate(row),
        items=[RankingItemOut.model_validate(i) for i in row.items],
    )


@router.delete("/ranking-runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ranking_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await weaponeering_service.get_ranking_run(db, run_id)
    if row is None:
        raise _not_found()
    await weaponeering_service.delete_ranking_run(db, row, user)


@router.patch("/ranking-items/{item_id}/override", response_model=RankingItemOut)
async def override_ranking_item(
    item_id: UUID,
    body: RankingItemOverride,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RankingItemOut:
    item = await weaponeering_service.get_ranking_item(db, item_id)
    if item is None:
        raise _not_found()
    updated = await weaponeering_service.override_ranking_item(db, item, body, user)
    return RankingItemOut.model_validate(updated)


# --- Plan options ---


@router.get("/plan-options", response_model=list[PlanOptionOut])
async def list_plan_options(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PlanOptionOut]:
    rows = await weaponeering_service.list_plan_options(db, scenario_id=scenario_id)
    return [PlanOptionOut.model_validate(r) for r in rows]


@router.post("/plan-options", response_model=PlanOptionOut, status_code=status.HTTP_201_CREATED)
async def create_plan_option(
    body: PlanOptionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlanOptionOut:
    try:
        row = await weaponeering_service.create_plan_option(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return PlanOptionOut.model_validate(row)


@router.patch("/plan-options/{option_id}", response_model=PlanOptionOut)
async def update_plan_option(
    option_id: UUID,
    body: PlanOptionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlanOptionOut:
    row = await weaponeering_service.get_plan_option(db, option_id)
    if row is None:
        raise _not_found()
    updated = await weaponeering_service.update_plan_option(db, row, body, user)
    return PlanOptionOut.model_validate(updated)


@router.delete("/plan-options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan_option(
    option_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await weaponeering_service.get_plan_option(db, option_id)
    if row is None:
        raise _not_found()
    await weaponeering_service.delete_plan_option(db, row, user)


# --- Plan assignments ---


@router.get("/plan-assignments", response_model=list[PlanAssignmentOut])
async def list_plan_assignments(
    plan_option_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[PlanAssignmentOut]:
    rows = await weaponeering_service.list_plan_assignments(db, plan_option_id=plan_option_id)
    return [PlanAssignmentOut.model_validate(r) for r in rows]


@router.post("/plan-assignments", response_model=PlanAssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_plan_assignment(
    body: PlanAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlanAssignmentOut:
    try:
        row = await weaponeering_service.create_plan_assignment(db, body, user)
    except ValueError as exc:
        raise _not_found(str(exc)) from exc
    return PlanAssignmentOut.model_validate(row)


@router.delete("/plan-assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await weaponeering_service.get_plan_assignment(db, assignment_id)
    if row is None:
        raise _not_found()
    await weaponeering_service.delete_plan_assignment(db, row, user)
