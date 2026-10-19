from __future__ import annotations

from dataclasses import dataclass


READINESS_SCORES = {
    "ready": 90,
    "limited": 65,
    "unavailable": 25,
    "maintenance": 35,
    "unknown": 50,
}

AVAILABILITY_SCORES = {
    "available": 90,
    "constrained": 60,
    "unavailable": 20,
}


@dataclass(frozen=True)
class LogisticsScoreInputs:
    depot_availability_scores: list[int]
    inventory_availability_scores: list[int]
    resource_token_quantities: list[int]
    route_friction_score: int | None
    fuel_stop_score: int | None
    transport_readiness_scores: list[int]
    platform_readiness_scores: list[int]


def calculate_logistics_feasibility(inputs: LogisticsScoreInputs) -> tuple[int, str, list[str]]:
    warnings: list[str] = []
    components: list[tuple[str, int | None]] = []

    if inputs.depot_availability_scores:
        depot_avg = sum(inputs.depot_availability_scores) // len(
            inputs.depot_availability_scores
        )
        components.append(("Depot availability", depot_avg))
    else:
        warnings.append("No depot availability data — depot component omitted.")

    if inputs.inventory_availability_scores:
        inv_avg = sum(inputs.inventory_availability_scores) // len(
            inputs.inventory_availability_scores
        )
        components.append(("Depot inventory", inv_avg))
    else:
        warnings.append("No depot inventory data — inventory component omitted.")

    if inputs.resource_token_quantities:
        token_avg = min(
            100,
            sum(min(100, q * 10) for q in inputs.resource_token_quantities)
            // len(inputs.resource_token_quantities),
        )
        components.append(("Resource tokens", token_avg))
    else:
        warnings.append("No resource tokens defined — token component omitted.")

    if inputs.route_friction_score is not None:
        route_score = max(1, min(100, 100 - inputs.route_friction_score))
        components.append(("Route friction inverse", route_score))
    else:
        warnings.append("No route segment selected — route component omitted.")

    if inputs.fuel_stop_score is not None:
        components.append(("Fuel-stop support", inputs.fuel_stop_score))
    else:
        warnings.append("No fuel-stop score available — fuel component omitted.")

    if inputs.transport_readiness_scores:
        transport_avg = sum(inputs.transport_readiness_scores) // len(
            inputs.transport_readiness_scores
        )
        components.append(("Transport readiness", transport_avg))
    else:
        warnings.append("No transport assets — transport component omitted.")

    if inputs.platform_readiness_scores:
        platform_avg = sum(inputs.platform_readiness_scores) // len(
            inputs.platform_readiness_scores
        )
        components.append(("Platform readiness", platform_avg))
    else:
        warnings.append("No simulated platforms — platform component omitted.")

    if not components:
        return 1, "Insufficient logistics inputs to compute a meaningful score.", warnings

    score = sum(value for _, value in components if value is not None) // len(components)
    score = max(1, min(100, score))
    rationale_parts = [f"{name}: {value}/100" for name, value in components if value is not None]
    rationale = "Abstract logistics feasibility based on " + "; ".join(rationale_parts) + "."
    return score, rationale, warnings
