from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.db import get_db
from weaponeering_api.deps.auth import get_current_user
from weaponeering_api.models import User
from weaponeering_api.schemas.detection import (
    DetectionExecuteOut,
    DetectionMapObjectOut,
    DetectionRunOut,
    DetectionRunUpsert,
    GroundTransportCreate,
    GroundTransportOut,
    GroundTransportUpdate,
    TeamMarkerCreate,
    TeamMarkerOut,
    TeamMarkerUpdate,
)
from weaponeering_api.services import detection_inference, detection_service

router = APIRouter(tags=["detection-map"])


def _not_found(detail: str = "ไม่พบข้อมูล") -> HTTPException:
    return HTTPException(status_code=404, detail=detail)


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


# --- Detection runs ---


@router.get("/detection-runs", response_model=list[DetectionRunOut])
async def list_detection_runs(
    scenario_id: UUID | None = Query(default=None),
    target_card_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DetectionRunOut]:
    rows = await detection_service.list_detection_runs(
        db, scenario_id=scenario_id, target_card_id=target_card_id
    )
    return [DetectionRunOut.model_validate(r) for r in rows]


@router.get("/detection-runs/by-coordinate", response_model=DetectionRunOut)
async def get_detection_run_by_coordinate(
    target_card_id: UUID = Query(...),
    target_coordinate_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DetectionRunOut:
    row = await detection_service.get_detection_run_for_coordinate(
        db, target_card_id, target_coordinate_id
    )
    if row is None:
        raise _not_found("ไม่พบ detection run")
    return DetectionRunOut.model_validate(row)


@router.get("/detection-models")
async def list_detection_models(
    _: User = Depends(get_current_user),
) -> dict:
    return {
        "models": detection_inference.available_model_names(),
        "defaultModel": "Building Detector",
        "zoomMin": 1,
        "zoomMax": 4,
        "zoomDefault": 4,
        "radiusMin": 20,
        "radiusMax": 300,
        "radiusDefault": 120,
    }


@router.post("/detection-runs/execute", response_model=DetectionExecuteOut)
async def execute_detection_run(
    scenario_id: UUID = Form(...),
    target_card_id: UUID = Form(...),
    target_coordinate_id: UUID = Form(...),
    model_name: str = Form(default="Building Detector"),
    radius_m: int = Form(default=120),
    zoom_level: int = Form(default=4),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DetectionExecuteOut:
    if radius_m < 20 or radius_m > 500:
        raise _bad_request("radius_m ต้องอยู่ระหว่าง 20–500")
    if zoom_level < 1 or zoom_level > 4:
        raise _bad_request("zoom_level ต้องอยู่ระหว่าง 1–4")
    content = await image.read()
    if not content:
        raise _bad_request("ไม่พบไฟล์ภาพสำหรับ detection")
    try:
        payload = await detection_inference.execute_detection_run(
            db,
            user=user,
            scenario_id=scenario_id,
            target_card_id=target_card_id,
            target_coordinate_id=target_coordinate_id,
            model_name=model_name,
            radius_m=radius_m,
            zoom_level=zoom_level,
            image_bytes=content,
            image_filename=image.filename or "capture.png",
        )
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    except RuntimeError as exc:
        raise _bad_request(str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Detection ล้มเหลว: {exc}",
        ) from exc
    return DetectionExecuteOut.model_validate(payload)


@router.get("/detection-runs/risk-direction")
async def get_risk_direction(
    target_card_id: UUID = Query(...),
    target_coordinate_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    try:
        return await detection_inference.risk_direction_for_coordinate(
            db,
            target_card_id=target_card_id,
            target_coordinate_id=target_coordinate_id,
        )
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc


@router.get("/detection-runs/{run_id}", response_model=DetectionRunOut)
async def get_detection_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DetectionRunOut:
    row = await detection_service.get_detection_run(db, run_id)
    if row is None:
        raise _not_found("ไม่พบ detection run")
    return DetectionRunOut.model_validate(row)


@router.put("/detection-runs", response_model=DetectionRunOut)
async def upsert_detection_run(
    body: DetectionRunUpsert,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DetectionRunOut:
    try:
        row = await detection_service.upsert_detection_run(db, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return DetectionRunOut.model_validate(row)


@router.delete("/detection-runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await detection_service.get_detection_run(db, run_id)
    if row is None:
        raise _not_found("ไม่พบ detection run")
    await detection_service.delete_detection_run(db, row, user)


@router.delete("/detection-objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection_object(
    object_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await detection_service.get_detection_object(db, object_id)
    if row is None:
        raise _not_found("ไม่พบอาคาร detection")
    await detection_service.delete_detection_object(db, row, user)


@router.get("/detection-map-objects", response_model=list[DetectionMapObjectOut])
async def list_detection_map_objects(
    scenario_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DetectionMapObjectOut]:
    return await detection_service.list_detection_map_objects(db, scenario_id=scenario_id)


# --- Team markers ---


@router.get("/team-markers", response_model=list[TeamMarkerOut])
async def list_team_markers(
    scenario_id: UUID | None = Query(default=None),
    side: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TeamMarkerOut]:
    rows = await detection_service.list_team_markers(db, scenario_id=scenario_id, side=side)
    return [TeamMarkerOut.model_validate(r) for r in rows]


@router.post("/team-markers", response_model=TeamMarkerOut, status_code=status.HTTP_201_CREATED)
async def create_team_marker(
    body: TeamMarkerCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TeamMarkerOut:
    try:
        row = await detection_service.create_team_marker(db, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return TeamMarkerOut.model_validate(row)


@router.patch("/team-markers/{marker_id}", response_model=TeamMarkerOut)
async def update_team_marker(
    marker_id: UUID,
    body: TeamMarkerUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TeamMarkerOut:
    row = await detection_service.get_team_marker(db, marker_id)
    if row is None:
        raise _not_found("ไม่พบ team marker")
    try:
        updated = await detection_service.update_team_marker(db, row, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return TeamMarkerOut.model_validate(updated)


@router.delete("/team-markers/{marker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_marker(
    marker_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await detection_service.get_team_marker(db, marker_id)
    if row is None:
        raise _not_found("ไม่พบ team marker")
    await detection_service.delete_team_marker(db, row, user)


# --- Ground transports ---


@router.get("/ground-transports", response_model=list[GroundTransportOut])
async def list_ground_transports(
    scenario_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[GroundTransportOut]:
    rows = await detection_service.list_ground_transports(db, scenario_id=scenario_id)
    return [GroundTransportOut.model_validate(r) for r in rows]


@router.post(
    "/ground-transports",
    response_model=GroundTransportOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_ground_transport(
    body: GroundTransportCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GroundTransportOut:
    try:
        row = await detection_service.create_ground_transport(db, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return GroundTransportOut.model_validate(row)


@router.patch("/ground-transports/{transport_id}", response_model=GroundTransportOut)
async def update_ground_transport(
    transport_id: UUID,
    body: GroundTransportUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GroundTransportOut:
    row = await detection_service.get_ground_transport(db, transport_id)
    if row is None:
        raise _not_found("ไม่พบ ground transport")
    try:
        updated = await detection_service.update_ground_transport(db, row, body, user)
    except ValueError as exc:
        raise _bad_request(str(exc)) from exc
    return GroundTransportOut.model_validate(updated)


@router.delete("/ground-transports/{transport_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ground_transport(
    transport_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = await detection_service.get_ground_transport(db, transport_id)
    if row is None:
        raise _not_found("ไม่พบ ground transport")
    await detection_service.delete_ground_transport(db, row, user)
