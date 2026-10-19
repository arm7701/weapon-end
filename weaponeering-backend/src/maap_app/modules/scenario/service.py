from __future__ import annotations

from uuid import uuid4

from maap_app.modules.audit.service import AuditService
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.models import MapNode, Scenario
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.scenario.schemas import CreateMapNodeRequest, CreateScenarioRequest


class ScenarioService:
    def __init__(
        self,
        repository: ScenarioRepository,
        guardrail_service: GuardrailService,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.guardrail_service = guardrail_service
        self.audit_service = audit_service

    def create_scenario(self, request: CreateScenarioRequest) -> str:
        scenario_id = str(uuid4())
        text = f"{request.name}\n{request.description}"
        if not self.guardrail_service.validate_training_text(
            text=text,
            entity_type="scenario",
            entity_id=scenario_id,
        ):
            raise ValueError("Scenario text was blocked by guardrail validation.")

        self.repository.insert_scenario(
            scenario_id=scenario_id,
            name=request.name,
            description=request.description,
            ruleset_version=request.ruleset_version,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="scenario_created",
            entity_type="scenario",
            entity_id=scenario_id,
            details={"name": request.name},
        )
        return scenario_id

    def list_scenarios(self) -> list[Scenario]:
        return self.repository.list_scenarios()

    def create_map_node(self, request: CreateMapNodeRequest) -> str:
        node_id = str(uuid4())
        if not self.guardrail_service.validate_training_text(
            text=request.label,
            entity_type="map_node",
            entity_id=node_id,
        ):
            raise ValueError("Map node text was blocked by guardrail validation.")

        self.repository.insert_map_node(
            node_id=node_id,
            scenario_id=request.scenario_id,
            label=request.label,
            node_type=request.node_type,
            map_lat=request.map_lat,
            map_lng=request.map_lng,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="map_node_created",
            entity_type="map_node",
            entity_id=node_id,
            details={"scenario_id": request.scenario_id, "label": request.label},
        )
        return node_id

    def list_map_nodes(self, scenario_id: str) -> list[MapNode]:
        return self.repository.list_map_nodes(scenario_id)

