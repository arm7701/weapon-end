from __future__ import annotations

import json
from uuid import uuid4

from maap_app.modules.audit.service import AuditService
from maap_app.modules.common import ReviewStatus
from maap_app.modules.guardrail.service import GuardrailService
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.target.coordinate_products import (
    match_existing_coordinate,
    resolve_coordinate_product_id,
)
from maap_app.modules.target.models import TargetCardDetail, TargetCardListItem
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.target.schemas import (
    CreateRecognitionResultRequest,
    CreateReviewRecordRequest,
    CreateTargetCardRequest,
    LinkTargetMapNodeRequest,
    SaveTargetCoordinatesRequest,
    TargetCoordinateInput,
    TargetFilterParams,
    UpdateRecognitionResultRequest,
    UpdateTargetCardRequest,
)

LOW_CONFIDENCE_THRESHOLD = 50


class TargetService:
    def __init__(
        self,
        repository: TargetRepository,
        scenario_repository: ScenarioRepository,
        guardrail_service: GuardrailService,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.scenario_repository = scenario_repository
        self.guardrail_service = guardrail_service
        self.audit_service = audit_service

    def create_target_card(self, request: CreateTargetCardRequest) -> str:
        target_id = str(uuid4())
        text = request.label
        if not self.guardrail_service.validate_training_text(
            text=text,
            entity_type="target_card",
            entity_id=target_id,
        ):
            raise ValueError("Target Card text was blocked by guardrail validation.")

        review_status = ReviewStatus.DRAFT
        self.repository.insert_target_card(
            target_id=target_id,
            scenario_id=request.scenario_id,
            label=request.label,
            priority_score=request.priority_score,
            complexity_score=request.complexity_score,
            review_status=review_status,
            profile=request.profile,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="target_card_created",
            entity_type="target_card",
            entity_id=target_id,
            details={"scenario_id": request.scenario_id, "label": request.label},
        )
        return target_id

    def update_target_card(self, request: UpdateTargetCardRequest) -> None:
        existing = self.repository.get_target_card(request.target_card_id)
        if existing is None:
            raise ValueError("Target Card not found.")

        text = request.label
        if not self.guardrail_service.validate_training_text(
            text=text,
            entity_type="target_card",
            entity_id=request.target_card_id,
        ):
            raise ValueError("Target Card text was blocked by guardrail validation.")

        review_status = request.review_status or existing.review_status
        self.repository.update_target_card(
            target_id=request.target_card_id,
            label=request.label,
            priority_score=request.priority_score,
            complexity_score=request.complexity_score,
            review_status=review_status,
            profile=request.profile,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="target_card_updated",
            entity_type="target_card",
            entity_id=request.target_card_id,
            details={"label": request.label},
        )

    def delete_target_card(self, target_card_id: str) -> None:
        existing = self.repository.get_target_card(target_card_id)
        if existing is None:
            raise ValueError("Target Card not found.")
        if not self.repository.delete_target_card(target_card_id):
            raise ValueError("Target Card not found.")
        self.audit_service.record_event(
            actor="local_user",
            event_type="target_card_deleted",
            entity_type="target_card",
            entity_id=target_card_id,
            details={"scenario_id": existing.scenario_id, "label": existing.label},
        )

    def delete_target_card(self, target_card_id: str) -> str:
        """Permanently delete a target card and all cascade-linked data. Returns scenario_id."""
        existing = self.repository.get_target_card(target_card_id)
        if existing is None:
            raise ValueError("Target Card not found.")
        scenario_id = existing.scenario_id
        self.repository.delete_target_card(target_card_id)
        self.audit_service.record_event(
            actor="local_user",
            event_type="target_card_deleted",
            entity_type="target_card",
            entity_id=target_card_id,
            details={"scenario_id": scenario_id},
        )
        return scenario_id

    def create_recognition_result(self, request: CreateRecognitionResultRequest) -> str:
        result_id = str(uuid4())
        text = request.recognition_summary
        if not self.guardrail_service.validate_training_text(
            text=text,
            entity_type="target_recognition_result",
            entity_id=result_id,
        ):
            raise ValueError("Recognition result was blocked by guardrail validation.")

        missing_json = json.dumps(request.missing_data_notes)
        review_status = ReviewStatus.REQUIRES_REVIEW
        self.repository.insert_recognition_result(
            result_id=result_id,
            target_card_id=request.target_card_id,
            source_type=request.source_type,
            recognition_summary=request.recognition_summary,
            recognition_confidence_score=request.recognition_confidence_score,
            missing_data_json=missing_json,
            generated_by=request.generated_by,
            review_status=review_status,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="recognition_result_created",
            entity_type="target_recognition_result",
            entity_id=result_id,
            details={"target_card_id": request.target_card_id},
        )
        return result_id

    def update_recognition_result(self, request: UpdateRecognitionResultRequest) -> None:
        if not self.guardrail_service.validate_training_text(
            text=request.recognition_summary,
            entity_type="target_recognition_result",
            entity_id=request.recognition_id,
        ):
            raise ValueError("Recognition result was blocked by guardrail validation.")

        existing = self.repository.get_recognition_by_id(request.recognition_id)
        review_status = request.review_status or (
            existing.review_status if existing else ReviewStatus.REQUIRES_REVIEW
        )
        self.repository.update_recognition_result(
            result_id=request.recognition_id,
            recognition_summary=request.recognition_summary,
            recognition_confidence_score=request.recognition_confidence_score,
            missing_data_json=json.dumps(request.missing_data_notes),
            review_status=review_status,
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="recognition_result_updated",
            entity_type="target_recognition_result",
            entity_id=request.recognition_id,
            details={},
        )

    def link_target_to_map(self, request: LinkTargetMapNodeRequest) -> str:
        card = self.repository.get_target_card(request.target_card_id)
        if card is None:
            raise ValueError("Target Card not found.")

        label = request.label or card.label
        if card.map_node_id:
            self.scenario_repository.update_map_node_coords(
                card.map_node_id,
                request.map_lat,
                request.map_lng,
                label=label,
            )
            node_id = card.map_node_id
        else:
            node_id = str(uuid4())
            self.scenario_repository.insert_map_node(
                node_id=node_id,
                scenario_id=request.scenario_id,
                label=label,
                node_type="target",
                map_lat=request.map_lat,
                map_lng=request.map_lng,
                linked_entity_type="target_card",
                linked_entity_id=request.target_card_id,
            )
            self.repository.set_target_map_node(request.target_card_id, node_id)
        self.audit_service.record_event(
            actor="local_user",
            event_type="target_linked_to_map_node",
            entity_type="target_card",
            entity_id=request.target_card_id,
            details={"map_node_id": node_id},
        )
        return node_id

    def save_target_coordinates(self, request: SaveTargetCoordinatesRequest) -> None:
        card = self.repository.get_target_card(request.target_card_id)
        if card is None:
            raise ValueError("Target Card not found.")
        if card.scenario_id != request.scenario_id:
            raise ValueError("Target Card not found in scenario.")

        coordinates = [
            coord
            for coord in request.coordinates
            if coord.map_lat is not None and coord.map_lng is not None
        ]
        if not coordinates:
            self.repository.replace_target_coordinates(request.target_card_id, [])
            return

        primary_count = sum(1 for coord in coordinates if coord.is_primary)
        if primary_count == 0:
            coordinates = [
                TargetCoordinateInput(
                    label=coordinates[0].label,
                    map_lat=coordinates[0].map_lat,
                    map_lng=coordinates[0].map_lng,
                    is_primary=True,
                ),
                *[
                    TargetCoordinateInput(
                        label=coord.label,
                        map_lat=coord.map_lat,
                        map_lng=coord.map_lng,
                        is_primary=False,
                    )
                    for coord in coordinates[1:]
                ],
            ]
        elif primary_count > 1:
            normalized: list[TargetCoordinateInput] = []
            primary_used = False
            for coord in coordinates:
                if coord.is_primary and not primary_used:
                    normalized.append(
                        TargetCoordinateInput(
                            label=coord.label,
                            map_lat=coord.map_lat,
                            map_lng=coord.map_lng,
                            is_primary=True,
                        )
                    )
                    primary_used = True
                else:
                    normalized.append(
                        TargetCoordinateInput(
                            label=coord.label,
                            map_lat=coord.map_lat,
                            map_lng=coord.map_lng,
                            is_primary=False,
                        )
                    )
            coordinates = normalized

        persisted = []
        existing_coords = self.repository.list_target_coordinates(request.target_card_id)
        for index, coord in enumerate(coordinates):
            matched = None
            if coord.id:
                matched = next(
                    (item for item in existing_coords if item.id == coord.id),
                    None,
                )
            if matched is None:
                matched = match_existing_coordinate(
                    coord.label,
                    float(coord.map_lat),
                    float(coord.map_lng),
                    existing_coords,
                )
            coord_id = coord.id or (matched.id if matched else str(uuid4()))
            product_id = coord.selected_product_id
            if product_id is None and matched is not None:
                product_id = matched.selected_product_id
            persisted.append(
                (
                    coord_id,
                    coord.label.strip(),
                    float(coord.map_lat),
                    float(coord.map_lng),
                    index,
                    coord.is_primary,
                    product_id,
                )
            )
        self.repository.replace_target_coordinates(
            request.target_card_id,
            persisted,
        )

        primary = next(
            (coord for coord in coordinates if coord.is_primary),
            coordinates[0],
        )
        self.link_target_to_map(
            LinkTargetMapNodeRequest(
                target_card_id=request.target_card_id,
                scenario_id=request.scenario_id,
                map_lat=primary.map_lat,
                map_lng=primary.map_lng,
                label=primary.label or card.label,
            )
        )
        self.audit_service.record_event(
            actor="local_user",
            event_type="target_coordinates_saved",
            entity_type="target_card",
            entity_id=request.target_card_id,
            details={"coordinate_count": len(coordinates)},
        )

    def create_review_record(self, request: CreateReviewRecordRequest) -> str:
        record_id = str(uuid4())
        self.repository.insert_review_record(
            record_id=record_id,
            scenario_id=request.scenario_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            reviewer=request.reviewer,
            decision=request.decision,
            notes=request.notes,
        )
        if request.entity_type == "target_card":
            card = self.repository.get_target_card(request.entity_id)
            if card:
                self.repository.update_review_status(
                    request.entity_id,
                    request.review_status,
                )
        self.audit_service.record_event(
            actor=request.reviewer,
            event_type="review_status_changed",
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            details={"decision": request.decision},
        )
        return record_id

    def set_coordinate_selected_product(
        self,
        coordinate_id: str,
        product_id: str | None,
    ) -> None:
        coordinate = self.repository.get_target_coordinate(coordinate_id)
        if coordinate is None:
            raise ValueError("Target coordinate not found.")
        self.repository.update_coordinate_product(coordinate_id, product_id)
        self.audit_service.record_event(
            actor="local_user",
            event_type="target_coordinate_product_changed",
            entity_type="target_coordinate",
            entity_id=coordinate_id,
            details={
                "target_card_id": coordinate.target_card_id,
                "selected_product_id": product_id,
            },
        )

    def list_target_cards(
        self,
        scenario_id: str,
        filters: TargetFilterParams | None = None,
    ) -> list[TargetCardListItem]:
        filters = filters or TargetFilterParams()
        items: list[TargetCardListItem] = []
        for card in self.repository.list_active_target_cards(scenario_id):
            recognition = self.repository.get_latest_recognition(card.id)
            confidence = (
                recognition.recognition_confidence_score if recognition else None
            )
            summary = recognition.recognition_summary if recognition else None
            warnings = self._build_warnings(
                has_recognition=recognition is not None,
                confidence=confidence,
                missing_data_json=recognition.missing_data_json if recognition else "[]",
                has_map_node=card.map_node_id is not None,
                review_status=card.review_status,
            )

            if filters.search_text:
                needle = filters.search_text.lower()
                haystack = " ".join(
                    filter(
                        None,
                        [card.label, summary or ""],
                    )
                ).lower()
                if needle not in haystack:
                    continue
            if filters.review_status and card.review_status != filters.review_status:
                continue
            if not (filters.priority_min <= card.priority_score <= filters.priority_max):
                continue
            if not (
                filters.complexity_min <= card.complexity_score <= filters.complexity_max
            ):
                continue
            if confidence is not None:
                if not (filters.confidence_min <= confidence <= filters.confidence_max):
                    continue
            elif filters.confidence_min > 0:
                continue

            items.append(
                TargetCardListItem(
                    card=card,
                    recognition_confidence=confidence,
                    recognition_summary=summary,
                    warning_count=len(warnings),
                )
            )
        return items

    def get_target_detail(self, target_id: str) -> TargetCardDetail | None:
        detail = self.repository.get_target_detail(target_id)
        if detail is None:
            return None
        recognition = detail.recognition
        detail.warnings = self._build_warnings(
            has_recognition=recognition is not None,
            confidence=recognition.recognition_confidence_score if recognition else None,
            missing_data_json=recognition.missing_data_json if recognition else "[]",
            has_map_node=bool(detail.card.map_node_id) or bool(detail.coordinates),
            review_status=detail.card.review_status,
        )
        missing = (
            TargetRepository.parse_missing_data(recognition.missing_data_json)
            if recognition
            else []
        )
        for note in missing:
            detail.warnings.append(f"Missing data note: {note}")
        return detail

    def get_target_by_map_node(self, map_node_id: str):
        return self.repository.get_target_by_map_node(map_node_id)

    def list_map_markers(self, scenario_id: str) -> list[dict]:
        markers: list[dict] = []
        for card in self.repository.list_active_target_cards(scenario_id):
            detail = self.repository.get_target_detail(card.id)
            if detail is None:
                continue

            coordinates = detail.coordinates
            if coordinates:
                point_count = len(coordinates)
                radius_m = (
                    float(card.coordinate_error_m)
                    if card.coordinate_error_m is not None and card.coordinate_error_m > 0
                    else 0.0
                )
                for index, coord in enumerate(coordinates):
                    point_label = coord.label.strip() or f"P{index + 1}"
                    display_label = (
                        card.label
                        if point_count == 1
                        else f"{card.label} · {point_label}"
                    )
                    markers.append(
                        {
                            "targetCardId": card.id,
                            "coordinateId": coord.id,
                            "mapNodeId": card.map_node_id if coord.is_primary else None,
                            "label": display_label,
                            "lat": coord.map_lat,
                            "lng": coord.map_lng,
                            "radiusM": radius_m,
                            "isPrimary": coord.is_primary,
                            "pointIndex": index,
                            "pointCount": point_count,
                        }
                    )
                continue

            if detail.map_lat is None or detail.map_lng is None:
                continue
            radius_m = (
                float(card.coordinate_error_m)
                if card.coordinate_error_m is not None and card.coordinate_error_m > 0
                else 0.0
            )
            markers.append(
                {
                    "targetCardId": card.id,
                    "coordinateId": None,
                    "mapNodeId": card.map_node_id,
                    "label": card.label,
                    "lat": detail.map_lat,
                    "lng": detail.map_lng,
                    "radiusM": radius_m,
                    "isPrimary": True,
                    "pointIndex": 0,
                    "pointCount": 1,
                }
            )
        return markers

    def _build_warnings(
        self,
        *,
        has_recognition: bool,
        confidence: int | None,
        missing_data_json: str,
        has_map_node: bool,
        review_status: str,
    ) -> list[str]:
        warnings: list[str] = []
        if not has_recognition:
            warnings.append("No Target Recognition Result attached yet.")
        if confidence is not None and confidence < LOW_CONFIDENCE_THRESHOLD:
            warnings.append(
                f"Low recognition confidence ({confidence}/100) — training review recommended."
            )
        if not has_map_node:
            warnings.append("No synthetic map node linked to this Target Card.")
        if review_status == ReviewStatus.BLOCKED_BY_GUARDRAIL:
            warnings.append("Target Card is blocked by guardrail and cannot be used as approved data.")
        missing = TargetRepository.parse_missing_data(missing_data_json)
        if missing:
            warnings.append(f"{len(missing)} missing-data note(s) recorded.")
        return warnings
