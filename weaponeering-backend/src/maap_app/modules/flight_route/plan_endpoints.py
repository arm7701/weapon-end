from __future__ import annotations

from maap_app.modules.weaponeering.models import TargetDeploymentPlan


def _fmt_coords(lat: float, lng: float) -> str:
    return f"{lat:.5f}, {lng:.5f}"


def resolve_flight_plan_endpoints(
    *,
    plan: TargetDeploymentPlan | None,
    wing_lat: float,
    wing_lng: float,
    wing_name: str,
) -> dict[str, object]:
    """Resolve takeoff/landing from the wing linked to the deployment plan."""
    takeoff = (wing_lat, wing_lng)
    takeoff_label = f"{wing_name} · {_fmt_coords(*takeoff)}"
    landing = takeoff
    landing_label = f"RTB · {wing_name} · {_fmt_coords(*landing)}"

    return {
        "takeoff": takeoff,
        "takeoff_label": takeoff_label,
        "landing": landing,
        "landing_label": landing_label,
        "has_plan": plan is not None,
        "landing_altitude_ft": 0,
    }
