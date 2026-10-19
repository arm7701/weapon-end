from __future__ import annotations

import math
from dataclasses import dataclass

from maap_app.modules.detection.border_route import (
    IngressBorderRoute,
    border_route_summary_th,
    calculate_ingress_border_route,
)
from maap_app.modules.weaponeering.flight_path import (
    bearing_deg,
    destination_point,
    distance_m,
    normalize_bearing_deg,
)

RISK_WEIGHTS: dict[str, float] = {
    "high": 3.0,
    "medium": 1.5,
    "low": 0.5,
}

COMPASS_LABELS_TH: tuple[tuple[float, str], ...] = (
    (0.0, "เหนือ"),
    (45.0, "ตะวันออกเฉียงเหนือ"),
    (90.0, "ตะวันออก"),
    (135.0, "ตะวันออกเฉียงใต้"),
    (180.0, "ใต้"),
    (225.0, "ตะวันตกเฉียงใต้"),
    (270.0, "ตะวันตก"),
    (315.0, "ตะวันตกเฉียงเหนือ"),
)

DEFAULT_SECTOR_COUNT = 36
RECOMMENDED_OPTION_COUNT = 3
MIN_OPTION_SEPARATION_DEG = 25.0
ANGULAR_DECAY_DEG = 30.0
RISK_INDEX_MAX = 100.0


@dataclass(frozen=True)
class RiskDirectionObject:
    lat: float
    lng: float
    risk_level: str
    label: str = ""


@dataclass(frozen=True)
class RiskDirectionOption:
    rank: int
    bearing_deg: float
    compass_label: str
    risk_score: float
    ingress_bearing_deg: float = 0.0
    border_route: IngressBorderRoute | None = None


@dataclass(frozen=True)
class RiskDirectionAlternative:
    bearing_deg: float
    compass_label: str
    risk_score: float


@dataclass(frozen=True)
class LowestRiskDirectionResult:
    available: bool
    bearing_deg: float | None = None
    compass_label: str = ""
    risk_score: float | None = None
    arrow_length_m: float = 0.0
    avoid_bearing_deg: float | None = None
    avoid_compass_label: str = ""
    avoid_risk_score: float | None = None
    recommended_options: tuple[RiskDirectionOption, ...] = ()
    alternatives: tuple[RiskDirectionAlternative, ...] = ()
    recommendations: tuple[str, ...] = ()

    def to_map_payload(self) -> dict[str, object]:
        top_border_route: dict[str, object] | None = None
        if self.recommended_options:
            first_route = self.recommended_options[0].border_route
            if first_route is not None:
                top_border_route = first_route.to_map_payload()
        return {
            "available": self.available,
            "bearingDeg": self.bearing_deg,
            "compassLabel": self.compass_label,
            "riskScore": self.risk_score,
            "arrowLengthM": self.arrow_length_m,
            "avoidBearingDeg": self.avoid_bearing_deg,
            "avoidCompassLabel": self.avoid_compass_label,
            "avoidRiskScore": self.avoid_risk_score,
            "ingressBearingDeg": (
                self.recommended_options[0].ingress_bearing_deg
                if self.recommended_options
                else None
            ),
            "borderRoute": top_border_route,
            "recommendedOptions": [
                {
                    "rank": option.rank,
                    "bearingDeg": option.bearing_deg,
                    "compassLabel": option.compass_label,
                    "riskScore": option.risk_score,
                    "ingressBearingDeg": option.ingress_bearing_deg,
                    "borderRoute": (
                        option.border_route.to_map_payload()
                        if option.border_route is not None
                        else None
                    ),
                }
                for option in self.recommended_options
            ],
            "alternatives": [
                {
                    "bearingDeg": alt.bearing_deg,
                    "compassLabel": alt.compass_label,
                    "riskScore": alt.risk_score,
                }
                for alt in self.alternatives
            ],
            "recommendations": list(self.recommendations),
        }


def bearing_to_compass_label_th(bearing: float) -> str:
    normalized = normalize_bearing_deg(bearing)
    best_label = COMPASS_LABELS_TH[0][1]
    best_delta = 360.0
    for anchor, label in COMPASS_LABELS_TH:
        delta = abs(normalized - anchor)
        delta = min(delta, 360.0 - delta)
        if delta < best_delta:
            best_delta = delta
            best_label = label
    return best_label


def _angular_diff_deg(left: float, right: float) -> float:
    delta = abs(normalize_bearing_deg(left) - normalize_bearing_deg(right)) % 360.0
    return min(delta, 360.0 - delta)


def _sector_center_bearing(sector_index: int, sector_count: int) -> float:
    sector_width = 360.0 / sector_count
    return normalize_bearing_deg((sector_index + 0.5) * sector_width)


def _angular_risk_factor(angle_diff_deg: float) -> float:
    return 1.0 / (1.0 + angle_diff_deg / ANGULAR_DECAY_DEG)


def _compute_sector_scores(
    *,
    target_lat: float,
    target_lng: float,
    objects: list[RiskDirectionObject],
    scan_radius_m: float,
    sector_count: int,
) -> list[float]:
    sector_scores = [0.0] * sector_count
    for sector_index in range(sector_count):
        center_bearing = _sector_center_bearing(sector_index, sector_count)
        for obj in objects:
            obj_bearing = bearing_deg(target_lat, target_lng, obj.lat, obj.lng)
            obj_distance = distance_m(target_lat, target_lng, obj.lat, obj.lng)
            if obj_distance > scan_radius_m * 1.05:
                continue

            weight = RISK_WEIGHTS.get(obj.risk_level, 0.5)
            distance_factor = max(0.15, 1.0 - (obj_distance / scan_radius_m))
            angle_diff = _angular_diff_deg(center_bearing, obj_bearing)
            sector_scores[sector_index] += (
                weight * distance_factor * _angular_risk_factor(angle_diff)
            )
    return sector_scores


def _to_risk_index(score: float, worst_score: float) -> float:
    if worst_score <= 1e-9:
        return 0.0
    return round(min(RISK_INDEX_MAX, RISK_INDEX_MAX * score / worst_score), 1)


def _pick_recommended_sectors(
    *,
    ranked_sectors: list[int],
    sector_count: int,
    best_sector: int,
) -> list[int]:
    selected = [best_sector]
    for sector_index in ranked_sectors:
        if len(selected) >= RECOMMENDED_OPTION_COUNT:
            break
        if sector_index in selected:
            continue
        candidate_bearing = _sector_center_bearing(sector_index, sector_count)
        too_close = False
        for chosen in selected:
            chosen_bearing = _sector_center_bearing(chosen, sector_count)
            if _angular_diff_deg(candidate_bearing, chosen_bearing) < MIN_OPTION_SEPARATION_DEG:
                too_close = True
                break
        if too_close:
            continue
        selected.append(sector_index)

    if len(selected) < RECOMMENDED_OPTION_COUNT:
        for sector_index in ranked_sectors:
            if len(selected) >= RECOMMENDED_OPTION_COUNT:
                break
            if sector_index not in selected:
                selected.append(sector_index)
    return selected[:RECOMMENDED_OPTION_COUNT]


def _build_recommended_options(
    sector_indices: list[int],
    sector_scores: list[float],
    sector_count: int,
    worst_score: float,
    *,
    target_lat: float,
    target_lng: float,
) -> list[RiskDirectionOption]:
    options: list[RiskDirectionOption] = []
    for rank, sector_index in enumerate(sector_indices, start=1):
        bearing = _sector_center_bearing(sector_index, sector_count)
        raw_score = sector_scores[sector_index]
        approach_bearing = round(bearing, 1)
        ingress_bearing = round(normalize_bearing_deg(approach_bearing + 180.0), 1)
        border_route = calculate_ingress_border_route(
            target_lat=target_lat,
            target_lng=target_lng,
            approach_bearing_deg=approach_bearing,
        )
        options.append(
            RiskDirectionOption(
                rank=rank,
                bearing_deg=approach_bearing,
                compass_label=bearing_to_compass_label_th(bearing),
                risk_score=_to_risk_index(raw_score, worst_score),
                ingress_bearing_deg=ingress_bearing,
                border_route=border_route,
            )
        )
    return options


def calculate_lowest_risk_direction(
    *,
    target_lat: float,
    target_lng: float,
    objects: list[RiskDirectionObject],
    scan_radius_m: float,
    sector_count: int = DEFAULT_SECTOR_COUNT,
) -> LowestRiskDirectionResult:
    if scan_radius_m <= 0:
        scan_radius_m = 120.0

    if not objects:
        return LowestRiskDirectionResult(
            available=False,
            recommendations=(
                "รัน Object Detection รอบ Target เพื่อประเมินทิศทางความเสี่ยงต่ำสุด",
                "เมื่อมีวัตถุรอบเป้าหมาย ระบบจะคำนวณทิศทางเป็นองศาและแสดงลูกศรบนแผนที่",
            ),
        )

    sector_scores = _compute_sector_scores(
        target_lat=target_lat,
        target_lng=target_lng,
        objects=objects,
        scan_radius_m=scan_radius_m,
        sector_count=sector_count,
    )
    high_risk_bearings: list[float] = []
    for obj in objects:
        obj_distance = distance_m(target_lat, target_lng, obj.lat, obj.lng)
        if obj_distance > scan_radius_m * 1.05:
            continue
        if obj.risk_level == "high":
            high_risk_bearings.append(
                bearing_deg(target_lat, target_lng, obj.lat, obj.lng)
            )

    ranked_sectors = sorted(
        range(sector_count),
        key=lambda index: sector_scores[index],
    )
    worst_sector = max(range(sector_count), key=lambda index: sector_scores[index])
    worst_bearing = _sector_center_bearing(worst_sector, sector_count)
    worst_score = sector_scores[worst_sector]

    min_score = sector_scores[ranked_sectors[0]]
    best_candidates = [
        index
        for index in ranked_sectors
        if math.isclose(sector_scores[index], min_score, rel_tol=0.0, abs_tol=1e-9)
    ]
    if len(best_candidates) > 1:
        best_sector = max(
            best_candidates,
            key=lambda index: _angular_diff_deg(
                _sector_center_bearing(index, sector_count),
                worst_bearing,
            ),
        )
    else:
        best_sector = best_candidates[0]

    best_bearing = _sector_center_bearing(best_sector, sector_count)
    best_score = sector_scores[best_sector]

    recommended_sectors = _pick_recommended_sectors(
        ranked_sectors=ranked_sectors,
        sector_count=sector_count,
        best_sector=best_sector,
    )
    recommended_options = _build_recommended_options(
        recommended_sectors,
        sector_scores,
        sector_count,
        worst_score,
        target_lat=target_lat,
        target_lng=target_lng,
    )

    alternatives: list[RiskDirectionAlternative] = []
    for option in recommended_options[1:]:
        alternatives.append(
            RiskDirectionAlternative(
                bearing_deg=option.bearing_deg,
                compass_label=option.compass_label,
                risk_score=option.risk_score,
            )
        )

    recommendations = _build_recommendations(
        recommended_options=recommended_options,
        worst_bearing=worst_bearing,
        worst_score=worst_score,
        high_risk_bearings=high_risk_bearings,
        object_count=len(objects),
    )

    return LowestRiskDirectionResult(
        available=True,
        bearing_deg=round(best_bearing, 1),
        compass_label=bearing_to_compass_label_th(best_bearing),
        risk_score=_to_risk_index(best_score, worst_score),
        arrow_length_m=round(max(scan_radius_m * 0.75, 40.0), 1),
        avoid_bearing_deg=round(worst_bearing, 1),
        avoid_compass_label=bearing_to_compass_label_th(worst_bearing),
        avoid_risk_score=_to_risk_index(worst_score, worst_score),
        recommended_options=tuple(recommended_options),
        alternatives=tuple(alternatives),
        recommendations=tuple(recommendations),
    )


def _build_recommendations(
    *,
    recommended_options: list[RiskDirectionOption],
    worst_bearing: float,
    worst_score: float,
    high_risk_bearings: list[float],
    object_count: int,
) -> list[str]:
    lines = [
        "ตัวเลือกที่แนะนำ (คะแนน 1-100 · ต่ำ = ความเสี่ยงน้อย):",
    ]
    for option in recommended_options:
        lines.append(
            f"#{option.rank} {option.bearing_deg:.0f}° ({option.compass_label}) "
            f"— คะแนน {option.risk_score:.1f} · Ingress {option.ingress_bearing_deg:.0f}°"
        )
        if option.border_route is not None and option.border_route.available:
            lines.append(border_route_summary_th(option.border_route))
        elif option.border_route is not None and option.border_route.message:
            lines.append(option.border_route.message)

    lines.append(
        f"หลีกเลี่ยงทิศทาง {worst_bearing:.0f}° "
        f"({bearing_to_compass_label_th(worst_bearing)}) "
        f"— คะแนนความเสี่ยงสูงสุด {_to_risk_index(worst_score, worst_score):.1f}"
    )

    if high_risk_bearings:
        avg_high = normalize_bearing_deg(
            sum(high_risk_bearings) / len(high_risk_bearings)
        )
        lines.append(
            f"พบวัตถุเสี่ยงสูง {len(high_risk_bearings)} รายการ "
            f"โดยเฉลี่ยอยู่ทิศ {avg_high:.0f}° "
            f"({bearing_to_compass_label_th(avg_high)})"
        )

    lines.append(
        f"อ้างอิงวัตถุรอบเป้าหมาย {object_count} รายการจาก Object Detection"
    )
    return lines


def risk_direction_tip_coordinates(
    target_lat: float,
    target_lng: float,
    bearing: float,
    arrow_length_m: float,
) -> tuple[float, float]:
    return destination_point(target_lat, target_lng, bearing, arrow_length_m)
