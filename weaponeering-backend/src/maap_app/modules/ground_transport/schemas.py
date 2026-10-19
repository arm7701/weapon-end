from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateGroundTransportRequest:
    scenario_id: str
    origin_wing_id: str
    destination_wing_id: str
    product_id: str | None = None
    vehicle_id: str | None = None
    quantity: int = 1
    label: str = ""
