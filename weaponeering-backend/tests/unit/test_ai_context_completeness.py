from __future__ import annotations

from pathlib import Path

from maap_app.config.settings import AppSettings
from maap_app.db.sqlite import SQLiteDatabase
from maap_app.modules.ai.context import ContextBundleBuilder, format_context_as_text
from maap_app.modules.audit.repository import AuditRepository
from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.repository import GuardrailRepository
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateScenarioRequest
from maap_app.modules.scenario.service import ScenarioService
from maap_app.modules.target.profile_fields import TargetProfileFields
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.schemas import CreateTargetCardRequest
from maap_app.modules.target.service import TargetService
from maap_app.modules.weaponeering.repository import WeaponeeringRepository
from maap_app.modules.wing_data.repository import WingDataRepository
from maap_app.modules.wing_data.schemas import CreateWingProductRequest
from maap_app.modules.wing_data.service import WingDataService


def _build_services(tmp_path: Path):
    settings = AppSettings(data_dir=tmp_path, database_path=tmp_path / "test.sqlite3")
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
    target_repository = TargetRepository(database)
    target_service = TargetService(
        repository=target_repository,
        scenario_repository=scenario_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    wing_data_repository = WingDataRepository(database)
    wing_data_service = WingDataService(
        repository=wing_data_repository,
        guardrail_service=guardrail_service,
        audit_service=audit_service,
    )
    builder = ContextBundleBuilder(
        scenario_repository=scenario_repository,
        target_repository=target_repository,
        weaponeering_repository=WeaponeeringRepository(database),
        logistics_repository=LogisticsRepository(database),
        ranking_repository=RankingRepository(database),
        wing_data_repository=wing_data_repository,
    )
    return scenario_service, target_service, wing_data_service, builder


def test_weapon_unit_cost_reaches_ai_context_catalog_and_text(tmp_path: Path) -> None:
    scenario_service, _target_service, wing_data_service, builder = _build_services(
        tmp_path
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Cost Context Scenario")
    )
    wing_data_service.create_product(
        CreateWingProductRequest(
            scenario_id=scenario_id, product_name="MK-82", weight_pounds=500, unit_cost=4500.0
        )
    )
    wing_data_service.create_product(
        CreateWingProductRequest(
            scenario_id=scenario_id, product_name="MK-84", weight_pounds=2000, unit_cost=13000.0
        )
    )

    bundle = builder.build_for_scenario_chat(scenario_id)

    catalog = {p["name"]: p["unit_cost"] for p in bundle.wing_force.get("products", [])}
    assert catalog["MK-82"] == 4500.0
    assert catalog["MK-84"] == 13000.0

    text = format_context_as_text(bundle)
    assert "MK-82" in text and "$4,500.00" in text
    assert "MK-84" in text and "$13,000.00" in text


def test_full_target_profile_reaches_selected_target_context(tmp_path: Path) -> None:
    scenario_service, target_service, _wing_data_service, builder = _build_services(
        tmp_path
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Profile Context Scenario")
    )
    target_id = target_service.create_target_card(
        CreateTargetCardRequest(
            scenario_id=scenario_id,
            label="TGT-PROFILE",
            profile=TargetProfileFields(
                target_type="BUNKER",
                target_subtype="HARDENED BUNKER",
                material_class="REINFORCED CONCRETE",
                target_description="Test hardened bunker",
                floor_count="2",
                width_m=20.0,
                length_m=30.0,
                height_m=8.0,
                cep=5.5,
                target_pk=0.85,
                reference_pk=0.9,
                resistance="High",
                capacity="500 personnel",
                damage_fit="Penetrator",
                model_version="v2",
            ),
        )
    )

    bundle = builder.build(scenario_id, target_card_id=target_id)

    assert bundle.target["target_subtype"] == "HARDENED BUNKER"
    assert bundle.target["material_class"] == "REINFORCED CONCRETE"
    assert bundle.target["width_m"] == 20.0
    assert bundle.target["length_m"] == 30.0
    assert bundle.target["height_m"] == 8.0
    assert bundle.target["cep"] == 5.5
    assert bundle.target["target_pk"] == 0.85
    assert bundle.target["reference_pk"] == 0.9
    assert bundle.target["resistance"] == "High"
    assert bundle.target["capacity"] == "500 personnel"
    assert bundle.target["damage_fit"] == "Penetrator"
    assert bundle.target["model_version"] == "v2"

    text = format_context_as_text(bundle)
    assert "REINFORCED CONCRETE" in text
    assert "Width=20.0m" in text
    assert "High" in text and "500 personnel" in text


def test_full_target_profile_reaches_all_targets_scenario_chat_context(
    tmp_path: Path,
) -> None:
    scenario_service, target_service, _wing_data_service, builder = _build_services(
        tmp_path
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="All Targets Profile Scenario")
    )
    target_service.create_target_card(
        CreateTargetCardRequest(
            scenario_id=scenario_id,
            label="TGT-ALL-01",
            profile=TargetProfileFields(
                material_class="STEEL",
                width_m=12.0,
                resistance="Medium",
            ),
        )
    )

    bundle = builder.build_for_scenario_chat(scenario_id)

    assert len(bundle.all_targets) == 1
    enriched = bundle.all_targets[0]
    assert enriched["material_class"] == "STEEL"
    assert enriched["width_m"] == 12.0
    assert enriched["resistance"] == "Medium"

    text = format_context_as_text(bundle)
    assert "STEEL" in text
    assert "Medium" in text


def test_scenario_chat_includes_full_weapon_ranking_not_just_top_weapon(
    tmp_path: Path,
) -> None:
    """Reproduces: in Scenario Chat (no target selected), the AI could answer
    "what's the best weapon" but not "what's the second best" — only the #1
    ranked weapon's n_required/total_cost ever reached the context, even
    though rank_weapons() already computes every weapon's ranking.
    """
    scenario_service, target_service, wing_data_service, builder = _build_services(
        tmp_path
    )
    scenario_id = scenario_service.create_scenario(
        CreateScenarioRequest(name="Weapon Ranking Scenario")
    )
    target_service.create_target_card(
        CreateTargetCardRequest(scenario_id=scenario_id, label="TGT-007")
    )
    wing_data_service.create_product(
        CreateWingProductRequest(
            scenario_id=scenario_id, product_name="MK-84", weight_pounds=2000, unit_cost=13000.0
        )
    )
    wing_data_service.create_product(
        CreateWingProductRequest(
            scenario_id=scenario_id, product_name="MK-82", weight_pounds=500, unit_cost=4500.0
        )
    )

    bundle = builder.build_for_scenario_chat(scenario_id)

    enriched = bundle.all_targets[0]
    options = enriched.get("weapon_options")
    assert options is not None
    assert len(options) == 2
    by_name = {o["product_name"]: o for o in options}

    # The #2 weapon must have a real, target-specific n_required and total_cost —
    # not just its catalog unit price with no calculation, as the bug reported.
    second = by_name["MK-82"] if by_name["MK-84"]["rank"] == 1 else by_name["MK-84"]
    assert second["rank"] == 2
    assert second["n_required"] >= 1
    assert second["unit_cost"] is not None
    assert second["total_cost"] is not None
    assert second["total_cost"] == round(second["unit_cost"] * second["n_required"], 2)

    text = format_context_as_text(bundle)
    assert "Weapon options (ranked):" in text
    assert "1. " in text and "2. " in text
    assert by_name["MK-82"]["product_name"] in text
    assert by_name["MK-84"]["product_name"] in text
