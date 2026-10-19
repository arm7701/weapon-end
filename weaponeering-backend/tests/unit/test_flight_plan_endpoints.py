from __future__ import annotations

from maap_app.modules.flight_route.plan_endpoints import resolve_flight_plan_endpoints
from maap_app.modules.weaponeering.models import (
    TargetDeploymentPlan,
    TargetDeploymentWaypoint,
)


def _sample_plan() -> TargetDeploymentPlan:
    return TargetDeploymentPlan(
        id="plan-1",
        scenario_id="sc-1",
        target_card_id="tgt-1",
        wing_id="wing-1",
        flying_unit_id="unit-1",
        aircraft_lines=(),
        takeoff_lat=14.93,
        takeoff_lng=102.08,
        waypoints=(
            TargetDeploymentWaypoint(
                id="wp-1",
                plan_id="plan-1",
                waypoint_type="return",
                label="RTB-BASE",
                lat=14.95,
                lng=102.10,
                sort_order=0,
                altitude_ft=0,
            ),
        ),
    )


def test_resolve_flight_plan_endpoints_uses_linked_wing_coords() -> None:
    result = resolve_flight_plan_endpoints(
        plan=_sample_plan(),
        wing_lat=14.0,
        wing_lng=101.0,
        wing_name="Wing A",
    )
    assert result["takeoff"] == (14.0, 101.0)
    assert result["landing"] == (14.0, 101.0)
    assert result["has_plan"] is True
    assert "Wing A" in str(result["takeoff_label"])
    assert "RTB" in str(result["landing_label"])


def test_resolve_flight_plan_endpoints_falls_back_to_wing() -> None:
    result = resolve_flight_plan_endpoints(
        plan=None,
        wing_lat=14.0,
        wing_lng=101.0,
        wing_name="Wing A",
    )
    assert result["takeoff"] == (14.0, 101.0)
    assert result["landing"] == (14.0, 101.0)
    assert result["has_plan"] is False
