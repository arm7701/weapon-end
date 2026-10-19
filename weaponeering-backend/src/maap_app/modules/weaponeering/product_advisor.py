from __future__ import annotations

from dataclasses import dataclass

from maap_app.modules.target.models import TargetCard
from maap_app.modules.weaponeering.jmem_calculator import (
    JmemCalculationResult,
    JmemMissionInputs,
)
from maap_app.modules.weaponeering.laser_designation import designation_info_for
from maap_app.modules.weaponeering.weapon_effects import weapon_effects_info
from maap_app.modules.weaponeering.circular_error import circular_error_info
from maap_app.modules.wing_data.models import WingProduct

_HEAVY_PREFERRED_TYPES = frozenset(
    {"BUNKER", "CONCRETE STRUCTURE", "HANGAR", "SPECIAL STRUCTURE"}
)
_LIGHT_PREFERRED_TYPES = frozenset({"TANK", "AIR DEFENSE"})
_MOBILE_TARGET_TYPES = frozenset({"TANK", "AIR DEFENSE"})
_STATIONARY_TARGET_TYPES = frozenset(
    {
        "BUILDING",
        "BUNKER",
        "CONCRETE STRUCTURE",
        "HANGAR",
        "SPECIAL STRUCTURE",
    }
)


def _weapon_family(product_name: str) -> str:
    normalized = product_name.upper().replace(" ", "")
    if "CBU" in normalized or "CLUSTER" in normalized or "ระเบิดพวง" in product_name:
        return "cluster"
    if "GBU" in normalized or "JDAM" in normalized:
        return "gbu"
    if normalized.startswith("MK") or "MK-" in normalized:
        return "mk"
    return "other"


def _target_mobility_profile(target_type: str) -> str:
    normalized = (target_type or "").strip().upper()
    if normalized in _MOBILE_TARGET_TYPES:
        return "mobile"
    if normalized in _STATIONARY_TARGET_TYPES:
        return "stationary"
    return "unknown"


def _mobility_label(target_type: str) -> str:
    profile = _target_mobility_profile(target_type)
    if profile == "mobile":
        return "เป้าเคลื่อนที่ (ต้องการความแม่นยำสูง)"
    if profile == "stationary":
        return "เป้านิ่ง (โครงสร้าง/สิ่งปลูกสร้าง)"
    return "ไม่ระบุลักษณะการเคลื่อนที่"


def _mobility_weapon_bonus(target_type: str, product_name: str) -> tuple[float, str | None]:
    family = _weapon_family(product_name)
    if family == "cluster":
        return (
            -40.0,
            "ระเบิดพวง — ไทยลงนาม Convention on Cluster Munitions แล้ว ไม่ใช้ในภารกิจหลัก",
        )
    profile = _target_mobility_profile(target_type)
    if profile == "mobile":
        if family == "gbu":
            return (
                24.0,
                "เป้าเคลื่อนที่ — GBU นำวิถี แม่นยำสูง เหมาะกับรถถัง/เป้าที่เคลื่อนที่",
            )
        if family == "mk":
            return -20.0, None
    if profile == "stationary":
        if family == "mk":
            return (
                20.0,
                "เป้านิ่ง — MK เหมาะทำลายอาคาร/โครงสร้าง ต้นทุนต่อภารกิจดีกว่า",
            )
        if family == "gbu":
            return -10.0, None
    return 0.0, None


@dataclass(frozen=True)
class ProductRecommendation:
    product_id: str
    product_name: str
    jmem_rank: int
    meets_desired_pk: bool
    confidence: str
    rationale: str
    factors: tuple[str, ...]
    unit_cost: float
    mission_cost: float
    n_required: int
    pk_n: float
    stock_available: int | None


def _format_thb(amount: float) -> str:
    if amount <= 0:
        return "ไม่ระบุราคา"
    return f"{amount:,.0f} บาท"


_STRENGTH_FIELDS = (
    ("fc_mpa", "f'c", "MPa"),
    ("fy_mpa", "fy", "MPa"),
    ("fu_mpa", "Fu", "MPa"),
    ("e_gpa", "E", "GPa"),
    ("fb_mpa", "Fb", "MPa"),
    ("as_mm2_per_m", "As", "mm²/m"),
    ("thickness_mm", "หนา", "มม."),
    ("density_kg_m3", "density", "kg/m³"),
    ("c_kpa", "c", "kPa"),
    ("phi_deg", "φ", "°"),
    ("gamma_kn_m3", "γ", "kN/m³"),
    ("bearing_kpa", "Bearing", "kPa"),
    ("cbr_pct", "CBR", "%"),
    ("strength_mpa", "ความแข็งแรง", "MPa"),
)


def material_strength_label(material_class: str, strength: dict | None) -> str | None:
    """One-line summary of the target's material strength values (f'c, fy, Fy, soil ...)."""
    if not strength:
        return None
    parts: list[str] = []
    for key, label, unit in _STRENGTH_FIELDS:
        value = strength.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if key == "fc_mpa" and material_class == "WOOD":
            label = "Fc"
        parts.append(f"{label} {value:g} {unit}")
    if not parts:
        return None
    kind = "RC" if material_class == "REINFORCED CONCRETE" else (material_class or "วัสดุ")
    return f"ค่าความแข็งแรงวัสดุ ({kind}): " + " · ".join(parts)


def _target_profile_bonus(target_type: str, material_class: str, weight_lb: float) -> float:
    bonus = 0.0
    if target_type in _HEAVY_PREFERRED_TYPES:
        if weight_lb >= 1_800:
            bonus += 18.0
        elif weight_lb >= 1_000:
            bonus += 12.0
        elif weight_lb >= 500:
            bonus += 6.0
    if target_type in _LIGHT_PREFERRED_TYPES:
        if weight_lb <= 500:
            bonus += 14.0
        elif weight_lb <= 750:
            bonus += 8.0
        if weight_lb >= 1_800:
            bonus -= 12.0
    if material_class == "REINFORCED CONCRETE" and weight_lb >= 1_000:
        bonus += 6.0
    if material_class in {"STEEL", "MIXED"} and weight_lb <= 750:
        bonus += 4.0
    return bonus


def _cost_adjustment(
    *,
    unit_cost: float,
    n_required: int,
    pk_n: float,
    pk_desired: float,
    stock_available: int | None,
) -> tuple[float, list[str]]:
    factors: list[str] = []
    adjustment = 0.0
    mission_cost = max(unit_cost, 0.0) * max(n_required, 1)

    if unit_cost > 0:
        factors.append(f"ราคาต่อหน่วย {_format_thb(unit_cost)}")
        factors.append(
            f"ค่าใช้จ่ายภารกิจ (N={n_required}) {_format_thb(mission_cost)}"
        )
        adjustment -= min(mission_cost / 75_000.0 * 5.0, 35.0)
        if pk_n >= pk_desired and mission_cost > 0:
            efficiency = pk_n / mission_cost * 1_000_000.0
            adjustment += min(efficiency * 3.0, 12.0)
            factors.append(f"ประสิทธิภาพต่อล้านบาท {efficiency:.2f}")
    else:
        factors.append("ยังไม่ระบุราคาต่อหน่วยใน Database")

    if stock_available is None:
        factors.append("ยังไม่ตรวจสอบสต็อกคลัง")
    elif stock_available < n_required:
        adjustment -= 35.0
        factors.append(
            f"สต็อกไม่พอ ({stock_available} < N{n_required}) — เสี่ยงด้าน logistics"
        )
    elif stock_available < n_required * 2:
        adjustment -= 8.0
        factors.append(f"สต็อกตึง ({stock_available} ลูก)")
    else:
        factors.append(f"สต็อกคลังรวม {stock_available} ลูก")

    return adjustment, factors


def _score_result(
    result: JmemCalculationResult,
    mission: JmemMissionInputs,
    *,
    target_type: str,
    material_class: str,
    unit_cost: float,
    stock_available: int | None,
) -> float:
    score = result.pd_base * 40.0
    if result.pk_n >= mission.pk_desired:
        score += 60.0
        score -= result.n_required * 1.5
    else:
        score += result.pk_n * 30.0
        score -= result.n_required * 0.5
    score += _target_profile_bonus(target_type, material_class, result.weight_pounds)
    mobility_bonus, _ = _mobility_weapon_bonus(target_type, result.product_name)
    score += mobility_bonus
    score += _cost_adjustment(
        unit_cost=unit_cost,
        n_required=result.n_required,
        pk_n=result.pk_n,
        pk_desired=mission.pk_desired,
        stock_available=stock_available,
    )[0]
    jmem_rank_bonus = max(0.0, (6 - result.rank) * 1.0)
    score += jmem_rank_bonus
    return score


def _confidence_label(score_gap: float, meets_pk: bool) -> str:
    if meets_pk and score_gap >= 8.0:
        return "สูง"
    if meets_pk or score_gap >= 4.0:
        return "ปานกลาง"
    return "ต่ำ"


def recommend_product(
    card: TargetCard,
    mission: JmemMissionInputs,
    results: list[JmemCalculationResult],
    products: list[WingProduct],
    *,
    stock_by_product: dict[str, int] | None = None,
) -> ProductRecommendation | None:
    if not results:
        return None

    product_costs = {product.id: float(product.unit_cost) for product in products}
    stock_map = stock_by_product or {}

    scored: list[tuple[float, JmemCalculationResult, list[str]]] = []
    for result in results:
        cost_factors = _cost_adjustment(
            unit_cost=product_costs.get(result.product_id, 0.0),
            n_required=result.n_required,
            pk_n=result.pk_n,
            pk_desired=mission.pk_desired,
            stock_available=stock_map.get(result.product_id),
        )[1]
        score = _score_result(
            result,
            mission,
            target_type=card.target_type,
            material_class=card.material_class,
            unit_cost=product_costs.get(result.product_id, 0.0),
            stock_available=stock_map.get(result.product_id),
        )
        scored.append((score, result, cost_factors))

    scored.sort(key=lambda row: row[0], reverse=True)
    best_score, best, cost_factors = scored[0]
    runner_up_score = scored[1][0] if len(scored) > 1 else best_score - 10.0
    unit_cost = product_costs.get(best.product_id, 0.0)
    mission_cost = unit_cost * best.n_required
    meets_pk = best.pk_n >= mission.pk_desired

    factors: list[str] = [
        f"JMEM อันดับ #{best.rank}",
        f"Pd {best.pd_base:.3f} · N {best.n_required} · PKₙ {best.pk_n:.3f}",
        f"Desired PK {mission.pk_desired:.2f}"
        + (" · บรรลุ" if meets_pk else " · ยังไม่บรรลุ"),
        *cost_factors,
    ]
    if card.target_type:
        factors.append(f"ประเภทเป้า {card.target_type}")
        factors.append(_mobility_label(card.target_type))
        _, mobility_factor = _mobility_weapon_bonus(card.target_type, best.product_name)
        if mobility_factor:
            factors.append(mobility_factor)
    if card.material_class and card.material_class != "UNKNOWN":
        factors.append(f"วัสดุ {card.material_class}")
    strength_factor = material_strength_label(
        card.material_class, getattr(card, "material_strength", None)
    )
    if strength_factor:
        factors.append(strength_factor)
    designation = designation_info_for(best.product_name)
    if designation is not None and designation.required:
        factors.append(
            "LGB ต้องมีแหล่งชี้เป้าเลเซอร์: อากาศ (Litening/Sniper บน F-16) หรือภาคพื้น (JTAC/CCT)"
        )
        factors.append(designation.weather_limitation)
    effects = weapon_effects_info()
    factors.append(
        f"{effects.title}: Overpressure · Fragmentation · Cratering"
    )
    cep_info = circular_error_info(
        ce50_ft=mission.cep_ft, product_name=best.product_name
    )
    if cep_info.ce50_ft is not None and cep_info.ce90_ft is not None:
        factors.append(
            f"{cep_info.title}: CE50 {cep_info.ce50_ft:.0f} ft · "
            f"CE90 {cep_info.ce90_ft:.0f} ft"
        )
    else:
        factors.append(f"{cep_info.title}: CE50 · CE90")

    mobility = _target_mobility_profile(card.target_type)
    if mobility == "mobile":
        mobility_note = (
            "เป้าหมายเคลื่อนที่ต้องการความแม่นยำสูง — เน้นชุดนำวิถี GBU"
        )
    elif mobility == "stationary":
        mobility_note = "เป้าหมายนิ่ง — เน้นสินค้าตระกูล MK ต่อโครงสร้าง"
    else:
        mobility_note = ""

    rationale = (
        f"แนะนำ {best.product_name} — "
        f"{'บรรลุ' if meets_pk else 'ใกล้เคียง'} Desired PK "
        f"โดยพิจารณา JMEM, โปรไฟล์เป้า และค่าใช้จ่าย"
    )
    if mobility_note:
        rationale += f" · {mobility_note}"
    if unit_cost > 0:
        rationale += f" (ภารกิจ ~{_format_thb(mission_cost)})"

    return ProductRecommendation(
        product_id=best.product_id,
        product_name=best.product_name,
        jmem_rank=best.rank,
        meets_desired_pk=meets_pk,
        confidence=_confidence_label(best_score - runner_up_score, meets_pk),
        rationale=rationale,
        factors=tuple(factors),
        unit_cost=unit_cost,
        mission_cost=mission_cost,
        n_required=best.n_required,
        pk_n=best.pk_n,
        stock_available=stock_map.get(best.product_id),
    )


def product_analysis_prompt(
    recommendation: ProductRecommendation,
    *,
    target_label: str,
    target_type: str = "",
) -> str:
    mobility = _target_mobility_profile(target_type)
    if mobility == "mobile":
        doctrine = (
            "แนวทางฝึก: เป้าเคลื่อนที่ (เช่น รถถัง) ต้องการความแม่นยำสูง "
            "— ให้ความสำคัญกับ GBU มากกว่า MK"
        )
    elif mobility == "stationary":
        doctrine = (
            "แนวทางฝึก: เป้านิ่ง (เช่น อาคาร/โครงสร้าง) "
            "— ให้ความสำคัญกับ MK มากกว่า GBU"
        )
    else:
        doctrine = (
            "แนวทางฝึก: เป้าเคลื่อนที่แนะนำ GBU · เป้านิ่งแนะนำ MK"
        )
    designation = designation_info_for(recommendation.product_name)
    if designation is not None and designation.required:
        doctrine += (
            " · LGB ต้องชี้เป้าเลเซอร์จากอากาศ (Targeting Pod) หรือภาคพื้น (JTAC/CCT) "
            "และเลเซอร์ส่องผ่านเมฆ/หมอก/ฝนไม่ได้"
        )
    effects = weapon_effects_info()
    doctrine += (
        f" · {effects.title}: Overpressure, Fragmentation, Cratering"
    )
    cep_info = circular_error_info()
    doctrine += (
        f" · {cep_info.title}: CE50 คือรัศมีที่ลูกระเบิด 50% ตกในวง, "
        "CE90 ครอบคลุม 90% และใหญ่กว่าเสมอ · ใช้ Pilot CEP หรือความแม่นยำระบบอาวุธแทนคู่มือปี 1998"
    )

    lines = [
        f"เป้าหมายจำลอง: {target_label}",
        f"ประเภทเป้าหมาย: {target_type or 'ไม่ระบุ'}",
        f"ลักษณะเป้า: {_mobility_label(target_type)}",
        doctrine,
        f"product_id: {recommendation.product_id}",
        f"product_name: {recommendation.product_name}",
        recommendation.rationale,
        f"ความมั่นใจ: {recommendation.confidence}",
        "ปัจจัยการพิจารณา:",
        *[f"- {factor}" for factor in recommendation.factors],
        (
            "อธิบายคำแนะนำสินค้าจำลองนี้เชิงฝึก: "
            "ประสิทธิภาพ JMEM, จำนวน N, ค่าใช้จ่ายภารกิจ, สต็อกคลัง, "
            "ลักษณะเป้า (เคลื่อนที่/นิ่ง) และข้อที่ผู้ฝึกควรตรวจสอบก่อนตัดสินใจ"
        ),
    ]
    return "\n".join(lines)
