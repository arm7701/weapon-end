from __future__ import annotations

from pathlib import Path

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.ai.context import ContextBundleBuilder
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.detection.persistence_service import TargetDetectionService
from maap_app.modules.detection.repository import TargetDetectionRepository
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.schemas import CreateTargetCardRequest
from maap_app.modules.target.service import TargetService
from maap_app.modules.weaponeering.repository import WeaponeeringRepository


def test_ai_context_includes_target_detection_risk_counts(tmp_path: Path) -> None:
    settings = AppSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.sqlite3",
    )
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    audit_service = AuditService(AuditRepository(database))
    guardrail_service = GuardrailService(GuardrailRepository(database), audit_service)
    scenario_repository = ScenarioRepository(database)
    target_repository = TargetRepository(database)
    detection_repository = TargetDetectionRepository(database)
    scenario_service = ScenarioService(
        repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    target_service = TargetService(
        repository=target_repository,
        scenario_repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    detection_service = TargetDetectionService(
        repository=detection_repository,
        target_repository=target_repository,
        audit_service=audit_service,
    )
    builder = ContextBundleBuilder(
        scenario_repository=scenario_repository,
        target_repository=target_repository,
        weaponeering_repository=WeaponeeringRepository(database),
        logistics_repository=LogisticsRepository(database),
        ranking_repository=RankingRepository(database),
        detection_repository=detection_repository,
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Detection Context Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-RISK")
    )
    detection_service.save_detection_run(
        scenario_id=scenario_id,
        target_card_id=target_id,
        target_coordinate_id=f"legacy-{target_id}",
        model_name="Building Detector",
        model_file_name="building-seg.pt",
        radius_m=120,
        capture_radius_m=480,
        source_image_name="source.png",
        detection_message="detected 3 object(s)",
        objects=[
            _object(target_id, "high", 0.91, 16.01, 100.01),
            _object(target_id, "medium", 0.72, 16.02, 100.02),
            _object(target_id, "low", 0.55, 16.03, 100.03),
        ],
    )

    bundle = builder.build(scenario_id, target_card_id=target_id)

    assert bundle.detection["available"] is True
    assert bundle.detection["building_high_count"] == 1
    assert bundle.detection["building_medium_count"] == 1
    assert bundle.detection["building_low_count"] == 1
    assert "ได้รับผลกระทบสูง" in bundle.detection["risk_meaning"]["high"]
    assert bundle.detection["objects"][0]["risk_meaning"] == (
        "Building High คืออาคารหรือวัตถุที่ได้รับผลกระทบสูง"
    )


def _object(
    target_id: str,
    risk: str,
    confidence: float,
    lat: float,
    lng: float,
) -> dict:
    return {
        "id": f"{target_id}-{risk}",
        "targetCardId": target_id,
        "label": "Building",
        "objectType": "building",
        "model": "Building Detector",
        "risk": risk,
        "confidence": confidence,
        "lat": lat,
        "lng": lng,
        "polygon": [[lat, lng], [lat + 0.001, lng], [lat, lng + 0.001]],
    }
