from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TargetProfileFields:
    target_type: str = "BUILDING"
    target_subtype: str = "MULTI-STORY BUILDING"
    material_class: str = "UNKNOWN"
    target_description: str = ""
    floor_count: str = ""
    width_m: float | None = None
    length_m: float | None = None
    height_m: float | None = None
    desired_model_result: str = "STRUCTURAL FAILURE"
    coordinate_error_m: float | None = None
    data_source: str = "manual"
    cep: float | None = None
    target_pk: float | None = None
    reference_pk: float | None = None
    resistance: str = ""
    capacity: str = ""
    damage_fit: str = ""
    model_version: str = ""
    selected_product_id: str | None = None

    def as_db_tuple(self) -> tuple:
        return (
            self.target_type,
            self.target_subtype,
            self.material_class,
            self.target_description,
            self.floor_count,
            self.width_m,
            self.length_m,
            self.height_m,
            self.desired_model_result,
            self.coordinate_error_m,
            self.data_source,
            self.cep,
            self.target_pk,
            self.reference_pk,
            self.resistance,
            self.capacity,
            self.damage_fit,
            self.model_version,
            self.selected_product_id,
        )

    @classmethod
    def from_card(cls, card) -> "TargetProfileFields":
        return cls(
            target_type=card.target_type,
            target_subtype=card.target_subtype,
            material_class=card.material_class,
            target_description=card.target_description,
            floor_count=card.floor_count,
            width_m=card.width_m,
            length_m=card.length_m,
            height_m=card.height_m,
            desired_model_result=card.desired_model_result,
            coordinate_error_m=card.coordinate_error_m,
            data_source=card.data_source,
            cep=card.cep,
            target_pk=card.target_pk,
            reference_pk=card.reference_pk,
            resistance=card.resistance,
            capacity=card.capacity,
            damage_fit=card.damage_fit,
            model_version=card.model_version,
            selected_product_id=card.selected_product_id,
        )
