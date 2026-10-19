from __future__ import annotations

import math
from dataclasses import dataclass, replace

from maap_app.modules.weaponeering.product_catalog import (
    lookup_known_product,
    weapon_impact_angle_deg,
)

CEP_TO_SIGMA = 1.1774

K_ANGLE_TABLE: dict[int, float] = {
    90: 1.000,
    60: 0.965,
}

K_BURIAL_TABLE: dict[int, float] = {
    0: 1.000,
    10: 0.734,
    25: 0.602,
    50: 0.400,
}

METERS_TO_FEET = 3.28084
FEET_TO_METERS = 0.3048

# Weapon delivery CEP (ft) for precision-guided munitions — replaces pilot CEP in JMEM.
GUIDED_LASER_CEP_FT = 13.0
GUIDED_GPS_CEP_FT = 13.0


def format_range_m_ft(radius_ft: float) -> str:
    radius_m = radius_ft * FEET_TO_METERS
    return f"{radius_m:.1f} m ({radius_ft:.0f} ft)"


def format_orange_range_m_ft(lo_ft: float, hi_ft: float) -> str:
    lo = min(lo_ft, hi_ft)
    hi = max(lo_ft, hi_ft)
    if abs(lo - hi) < 0.05:
        return format_range_m_ft(lo)
    lo_m = lo * FEET_TO_METERS
    hi_m = hi * FEET_TO_METERS
    return f"{lo_m:.1f}–{hi_m:.1f} m ({lo:.0f}–{hi:.0f} ft)"


EFFECT_ZONE_COLORS = {
    "red": "#991b1b",
    "orange": "#ea580c",
    "yellow_dark": "#a16207",
    "yellow_light": "#facc15",
}

EFFECT_ZONE_LABELS_TH = {
    "red": "แดง",
    "orange": "ส้ม",
    "yellow_dark": "เหลืองเข้ม",
    "yellow_light": "เหลือง",
}

_EFFECT_ZONE_COLORS = EFFECT_ZONE_COLORS

_RANGE_WEIGHT_ANCHORS = (100, 250, 500)
_RANGE_RED_FT: dict[int, float] = {100: 14.0, 250: 18.0, 500: 25.0}
_RANGE_ORANGE_MIN_FT: dict[int, float] = {100: 14.0, 250: 18.0, 500: 25.0}
_RANGE_ORANGE_MAX_FT: dict[int, float] = {100: 16.0, 250: 22.0, 500: 30.0}
_RANGE_YELLOW_DARK_FT: dict[int, float] = {100: 20.0, 250: 25.0, 500: 32.0}
_RANGE_YELLOW_LIGHT_FT: dict[int, float] = {100: 30.0, 250: 40.0, 500: 55.0}


@dataclass(frozen=True)
class EffectRangesFt:
    red_ft: float
    orange_min_ft: float
    orange_max_ft: float
    yellow_dark_ft: float
    yellow_light_ft: float

    @property
    def orange_display(self) -> str:
        lo = min(self.orange_min_ft, self.orange_max_ft)
        hi = max(self.orange_min_ft, self.orange_max_ft)
        if abs(lo - hi) < 0.05:
            return f"{lo:.0f}"
        return f"{lo:.0f}–{hi:.0f}"


@dataclass(frozen=True)
class JmemMissionInputs:
    cep_ft: float
    tle_ft: float
    impact_angle_deg: float
    burial_pct: float
    target_length_ft: float
    target_width_ft: float
    p_rel: float
    p_wpn: float
    pk_desired: float


@dataclass(frozen=True)
class JmemWeaponInputs:
    product_id: str
    product_name: str
    weight_pounds: float
    mae_building_ft2: float


@dataclass(frozen=True)
class JmemCalculationResult:
    product_id: str
    product_name: str
    weight_pounds: float
    mae_building_ft2: float
    cep_total_ft: float
    sigma_ft: float
    a_error_ft2: float
    mae_eff_ft2: float
    a_target_ft2: float
    mae_adjusted_ft2: float
    pd_base: float
    pk_single: float
    n_required: int
    pk_n: float
    range_red_ft: float
    range_orange_min_ft: float
    range_orange_max_ft: float
    range_yellow_dark_ft: float
    range_yellow_light_ft: float
    rank: int = 0

    @property
    def range_orange_display(self) -> str:
        lo = min(self.range_orange_min_ft, self.range_orange_max_ft)
        hi = max(self.range_orange_min_ft, self.range_orange_max_ft)
        if abs(lo - hi) < 0.05:
            return f"{lo:.0f}"
        return f"{lo:.0f}–{hi:.0f}"


@dataclass(frozen=True)
class JmemTargetContext:
    target_id: str
    label: str
    target_element: str
    mission: JmemMissionInputs
    warnings: tuple[str, ...]


def lookup_k_angle(impact_angle_deg: float) -> float:
    angle = int(round(impact_angle_deg))
    if angle in K_ANGLE_TABLE:
        return K_ANGLE_TABLE[angle]
    if angle >= 90:
        return K_ANGLE_TABLE[90]
    if angle <= 60:
        return K_ANGLE_TABLE[60]
    ratio = (angle - 60) / 30
    return K_ANGLE_TABLE[60] + ratio * (K_ANGLE_TABLE[90] - K_ANGLE_TABLE[60])


def lookup_k_burial(burial_pct: float) -> float:
    burial = int(round(burial_pct))
    keys = sorted(K_BURIAL_TABLE)
    if burial <= keys[0]:
        return K_BURIAL_TABLE[keys[0]]
    if burial >= keys[-1]:
        return K_BURIAL_TABLE[keys[-1]]
    for low, high in zip(keys, keys[1:]):
        if low <= burial <= high:
            span = high - low
            if span == 0:
                return K_BURIAL_TABLE[low]
            ratio = (burial - low) / span
            return K_BURIAL_TABLE[low] + ratio * (K_BURIAL_TABLE[high] - K_BURIAL_TABLE[low])
    return K_BURIAL_TABLE[0]


def _interpolate_range_table(weight_pounds: float, table: dict[int, float]) -> float:
    weight = max(float(weight_pounds), 1.0)
    anchors = _RANGE_WEIGHT_ANCHORS
    if weight <= anchors[0]:
        return table[anchors[0]]
    if weight >= anchors[-1]:
        w0, w1 = anchors[-2], anchors[-1]
        v0, v1 = table[w0], table[w1]
        slope = (v1 - v0) / (w1 - w0)
        return v1 + slope * (weight - w1)
    for low, high in zip(anchors, anchors[1:]):
        if low <= weight <= high:
            ratio = (weight - low) / (high - low)
            return table[low] + ratio * (table[high] - table[low])
    return table[anchors[0]]


def calculate_effect_ranges_ft(weight_pounds: float) -> EffectRangesFt:
    return EffectRangesFt(
        red_ft=_interpolate_range_table(weight_pounds, _RANGE_RED_FT),
        orange_min_ft=_interpolate_range_table(weight_pounds, _RANGE_ORANGE_MIN_FT),
        orange_max_ft=_interpolate_range_table(weight_pounds, _RANGE_ORANGE_MAX_FT),
        yellow_dark_ft=_interpolate_range_table(weight_pounds, _RANGE_YELLOW_DARK_FT),
        yellow_light_ft=_interpolate_range_table(weight_pounds, _RANGE_YELLOW_LIGHT_FT),
    )


def effect_radii_for_map(
    weight_pounds: float,
    n_required: int = 1,
) -> list[dict[str, str | float | int]]:
    """Map blast zones from weapon weight (interpolated per lb) scaled by N."""
    ranges = calculate_effect_ranges_ft(weight_pounds)
    scale = max(1, int(n_required))
    return [
        {
            "zone": "red",
            "color": _EFFECT_ZONE_COLORS["red"],
            "radiusFt": ranges.red_ft * scale,
            "radiusM": ranges.red_ft * FEET_TO_METERS * scale,
            "baseRadiusFt": ranges.red_ft,
            "nRequired": scale,
        },
        {
            "zone": "orange",
            "color": _EFFECT_ZONE_COLORS["orange"],
            "radiusFt": ranges.orange_max_ft * scale,
            "radiusM": ranges.orange_max_ft * FEET_TO_METERS * scale,
            "baseRadiusFt": ranges.orange_max_ft,
            "nRequired": scale,
        },
        {
            "zone": "yellow_dark",
            "color": _EFFECT_ZONE_COLORS["yellow_dark"],
            "radiusFt": ranges.yellow_dark_ft * scale,
            "radiusM": ranges.yellow_dark_ft * FEET_TO_METERS * scale,
            "baseRadiusFt": ranges.yellow_dark_ft,
            "nRequired": scale,
        },
        {
            "zone": "yellow_light",
            "color": _EFFECT_ZONE_COLORS["yellow_light"],
            "radiusFt": ranges.yellow_light_ft * scale,
            "radiusM": ranges.yellow_light_ft * FEET_TO_METERS * scale,
            "baseRadiusFt": ranges.yellow_light_ft,
            "nRequired": scale,
        },
    ]


def _normalize_product_name(product_name: str) -> str:
    return product_name.lower().replace(" ", "").replace("-", "")


def is_guided_weapon(product_name: str) -> bool:
    known = lookup_known_product(product_name)
    if known is not None:
        return known.delivery == "guided"
    normalized = _normalize_product_name(product_name)
    return "gbu" in normalized or "jdam" in normalized or "paveway" in normalized


def weapon_delivery_cep_ft(product_name: str, mission_cep_ft: float) -> float:
    """Return delivery CEP used in JMEM error model for this weapon."""
    if not is_guided_weapon(product_name):
        return mission_cep_ft
    normalized = _normalize_product_name(product_name)
    gps_markers = ("gbu31", "gbu32", "gbu38", "gbu39", "gbu54", "jdam")
    if any(marker in normalized for marker in gps_markers):
        return GUIDED_GPS_CEP_FT
    return GUIDED_LASER_CEP_FT


def estimate_mae_building_ft2(product_name: str, weight_pounds: float) -> float:
    name = product_name.lower().replace(" ", "")
    if "mk-15" in name or "mk15" in name or "snakeye" in name or "high-drag" in name or "highdrag" in name:
        return 12_000.0
    if "gbu-12" in name or "gbu12" in name:
        return 12_000.0
    if "gbu-10" in name or "gbu10" in name or "gbu-16" in name or "gbu16" in name:
        return 32_000.0
    if "mk-84" in name or "mk84" in name:
        return 32_000.0
    if "mk-83" in name or "mk83" in name:
        return 18_000.0
    if "mk-82" in name or "mk82" in name:
        return 12_000.0
    if "mk-81" in name or "mk81" in name:
        return 8_000.0
    if "cbu" in name or "cluster" in name:
        return 24_000.0
    if weight_pounds >= 1_800:
        return 32_000.0
    if weight_pounds >= 750:
        return 18_000.0
    if weight_pounds >= 400:
        return 12_000.0
    return max(8_000.0, weight_pounds * 24.0)


def mission_inputs_from_target_card(card) -> JmemMissionInputs:
    cep_ft = float(card.cep) if card.cep is not None else 120.0
    tle_ft = (
        float(card.coordinate_error_m) * METERS_TO_FEET
        if card.coordinate_error_m is not None
        else 50.0
    )
    length_ft = (
        float(card.length_m) * METERS_TO_FEET if card.length_m is not None else 65.6
    )
    width_ft = float(card.width_m) * METERS_TO_FEET if card.width_m is not None else 49.2
    pk_desired = 0.90
    if card.target_pk is not None:
        pk_desired = float(card.target_pk)
    elif card.reference_pk is not None:
        pk_desired = float(card.reference_pk)

    return JmemMissionInputs(
        cep_ft=cep_ft,
        tle_ft=tle_ft,
        impact_angle_deg=60.0,
        burial_pct=0.0,
        target_length_ft=length_ft,
        target_width_ft=width_ft,
        p_rel=0.98,
        p_wpn=0.97,
        pk_desired=min(max(pk_desired, 0.01), 0.99),
    )


def build_target_context(target_id: str, card) -> JmemTargetContext:
    mission = mission_inputs_from_target_card(card)
    warnings: list[str] = []
    if card.cep is None:
        warnings.append("ใช้ CEP ค่าเริ่มต้น 120 ft (กรอกใน Target Stack)")
    if card.coordinate_error_m is None:
        warnings.append("ใช้ TLE ค่าเริ่มต้น 50 ft (กรอก ERR ใน Target Stack)")
    if card.length_m is None or card.width_m is None:
        warnings.append("ใช้ขนาดเป้าหมายเริ่มต้น 20m×15m (กรอก Width/Length ใน Target Stack)")
    if card.target_pk is None and card.reference_pk is None:
        warnings.append("ใช้ Desired PK เริ่มต้น 0.90 (กรอก Pk เป้าหมายใน Target Stack)")

    return JmemTargetContext(
        target_id=target_id,
        label=card.label,
        target_element=f"{card.target_type} / {card.target_subtype}",
        mission=mission,
        warnings=tuple(warnings),
    )


def pk_for_rounds(pk_single: float, n_rounds: int) -> float:
    """Cumulative Pk for N statistically independent rounds."""
    if n_rounds <= 0 or pk_single <= 0:
        return 0.0
    if pk_single >= 1:
        return 1.0
    return 1 - (1 - pk_single) ** n_rounds


def calculate_weapon_effect(
    mission: JmemMissionInputs,
    weapon: JmemWeaponInputs,
) -> JmemCalculationResult:
    delivery_cep_ft = weapon_delivery_cep_ft(weapon.product_name, mission.cep_ft)
    cep_total = math.hypot(delivery_cep_ft, mission.tle_ft)
    sigma = cep_total / CEP_TO_SIGMA
    a_error = 2 * math.pi * (sigma**2)
    k_angle = lookup_k_angle(
        weapon_impact_angle_deg(weapon.product_name, mission.impact_angle_deg)
    )
    k_burial = lookup_k_burial(mission.burial_pct)
    mae_eff = weapon.mae_building_ft2 * k_angle * k_burial
    a_target = mission.target_length_ft * mission.target_width_ft
    mae_adjusted = mae_eff + a_target
    pd_base = mae_adjusted / (a_error + mae_adjusted)
    pk_single = mission.p_rel * mission.p_wpn * pd_base

    if pk_single <= 0:
        n_required = 0
        pk_n = 0.0
    elif pk_single >= 1:
        n_required = 1
        pk_n = 1.0
    else:
        n_required = max(
            1,
            math.ceil(
                math.log(1 - mission.pk_desired) / math.log(1 - pk_single)
            ),
        )
        pk_n = 1 - (1 - pk_single) ** n_required

    ranges = calculate_effect_ranges_ft(weapon.weight_pounds)

    return JmemCalculationResult(
        product_id=weapon.product_id,
        product_name=weapon.product_name,
        weight_pounds=weapon.weight_pounds,
        mae_building_ft2=weapon.mae_building_ft2,
        cep_total_ft=cep_total,
        sigma_ft=sigma,
        a_error_ft2=a_error,
        mae_eff_ft2=mae_eff,
        a_target_ft2=a_target,
        mae_adjusted_ft2=mae_adjusted,
        pd_base=pd_base,
        pk_single=pk_single,
        n_required=n_required,
        pk_n=pk_n,
        range_red_ft=ranges.red_ft,
        range_orange_min_ft=ranges.orange_min_ft,
        range_orange_max_ft=ranges.orange_max_ft,
        range_yellow_dark_ft=ranges.yellow_dark_ft,
        range_yellow_light_ft=ranges.yellow_light_ft,
    )


def rank_weapons(
    mission: JmemMissionInputs,
    weapons: list[JmemWeaponInputs],
) -> list[JmemCalculationResult]:
    results = [calculate_weapon_effect(mission, weapon) for weapon in weapons]
    ranked = sorted(results, key=lambda row: row.pd_base, reverse=True)
    return [replace(row, rank=index) for index, row in enumerate(ranked, start=1)]


def apply_selected_product_rank(
    results: list[JmemCalculationResult],
    selected_product_id: str | None,
) -> list[JmemCalculationResult]:
    if not selected_product_id or not results:
        return results
    selected: JmemCalculationResult | None = None
    others: list[JmemCalculationResult] = []
    for row in results:
        if row.product_id == selected_product_id:
            selected = row
        else:
            others.append(row)
    if selected is None:
        return results
    reordered = [selected, *others]
    return [replace(row, rank=index) for index, row in enumerate(reordered, start=1)]
