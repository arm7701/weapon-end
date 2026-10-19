from __future__ import annotations

from pathlib import Path

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.target.map_markers import enrich_target_markers_with_effect_radii
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.schemas import (
    CreateTargetCardRequest,
    LinkTargetMapNodeRequest,
)
from maap_app.modules.target.service import TargetService
from maap_app.modules.wing_data.repository import WingDataRepository
from maap_app.modules.wing_data.schemas import CreateWingProductRequest
from maap_app.modules.wing_data.service import WingDataService


def _build_services(tmp_path: Path):
    settings = AppSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.sqlite3",
    )
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    audit_service = AuditService(AuditRepository(database))
    guardrail_service = GuardrailService(GuardrailRepository(database), audit_service)
    scenario_repository = ScenarioRepository(database)
    scenario_service = ScenarioService(
        repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    target_service = TargetService(
        repository=TargetRepository(database),
        scenario_repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    wing_data_service = WingDataService(
        repository=WingDataRepository(database),
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    return scenario_service, target_service, wing_data_service


def test_enrich_target_markers_adds_effect_radii_without_products(
    tmp_path: Path,
) -> None:
    scenario_service, target_service, wing_data_service = _build_services(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Map Marker Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-MAP")
    )
    target_service.link_target_to_map(
        LinkTargetMapNodeRequest(
            target_card_id=target_id,
            scenario_id=scenario_id,
            map_lat=16.81,
            map_lng=100.12,
        )
    )

    markers = enrich_target_markers_with_effect_radii(
        target_service.list_map_markers(scenario_id),
        scenario_id,
        target_service,
        wing_data_service,
    )

    assert len(markers) == 1
    assert len(markers[0]["effectRadii"]) == 4
    assert markers[0]["effectRadii"][0]["zone"] == "red"
    assert "effectProduct" not in markers[0]


def test_enrich_target_markers_uses_best_ranked_product(tmp_path: Path) -> None:
    scenario_service, target_service, wing_data_service = _build_services(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Map Marker Product Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-MAP-2")
    )
    target_service.link_target_to_map(
        LinkTargetMapNodeRequest(
            target_card_id=target_id,
            scenario_id=scenario_id,
            map_lat=16.81,
            map_lng=100.12,
        )
    )
    wing_data_service.create_product(
        CreateWingProductRequest(
            scenario_id=scenario_id,
            product_name="Mk-82",
            weight_pounds=250,
        )
    )
    wing_data_service.create_product(
        CreateWingProductRequest(
            scenario_id=scenario_id,
            product_name="Mk-84",
            weight_pounds=500,
        )
    )

    markers = enrich_target_markers_with_effect_radii(
        target_service.list_map_markers(scenario_id),
        scenario_id,
        target_service,
        wing_data_service,
    )

    assert markers[0]["effectProduct"] == "Mk-84"
    assert markers[0]["effectRadii"][-1]["zone"] == "yellow_light"


def test_enrich_target_markers_uses_selected_product_over_jmem_rank(
    tmp_path: Path,
) -> None:
    scenario_service, target_service, wing_data_service = _build_services(tmp_path)
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Selected Product Scenario")
    )
    mk82_id = wing_data_service.create_product(
        CreateWingProductRequest(
            scenario_id=scenario_id,
            product_name="Mk-82",
            weight_pounds=250,
        )
    )
    wing_data_service.create_product(
        CreateWingProductRequest(
            scenario_id=scenario_id,
            product_name="Mk-84",
            weight_pounds=500,
        )
    )
    from maap_app.modules.target.profile_fields import TargetProfileFields

    target_id = target_service.create_target_card(
        CreateTargetCardRequest(
            scenario_id=scenario_id,
            label="TGT-SELECTED",
            profile=TargetProfileFields(selected_product_id=mk82_id),
        )
    )
    target_service.link_target_to_map(
        LinkTargetMapNodeRequest(
            target_card_id=target_id,
            scenario_id=scenario_id,
            map_lat=16.81,
            map_lng=100.12,
        )
    )

    markers = enrich_target_markers_with_effect_radii(
        target_service.list_map_markers(scenario_id),
        scenario_id,
        target_service,
        wing_data_service,
    )

    assert markers[0]["effectProduct"] == "Mk-82"
