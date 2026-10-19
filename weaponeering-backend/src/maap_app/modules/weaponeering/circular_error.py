from __future__ import annotations

import math
from dataclasses import dataclass

from maap_app.modules.weaponeering.jmem_calculator import (
    CEP_TO_SIGMA,
    is_guided_weapon,
    weapon_delivery_cep_ft,
)

CIRCULAR_ERROR_TITLE = "การคำนวณค่าความแม่นยำทางสถิติ (CEP & Circular Error)"

CIRCULAR_ERROR_INTRO = (
    "ในการวางแผนยุทธการทางอากาศ จะใช้ค่าความคลาดเคลื่อนวงกลมเพื่อคำนวณหาจำนวนลูกระเบิดที่ต้องใช้"
)

CIRCULAR_ERROR_APPLICATION = (
    "ในอดีตใช้คู่มือคำนวณแบบเดิม (ตั้งแต่ปี 1998) "
    "ปัจจุบันเปลี่ยนมาใช้โปรแกรมสำเร็จรูปในการคำนวณหาค่าความน่าจะเป็น "
    "เช่น การป้อนค่าเฉลี่ยความแม่นยำของนักบินแต่ละคนในฝูงบิน (Pilot CEP) "
    "หรือค่าความแม่นยำของระบบอาวุธ เพื่อหาผลลัพธ์ที่ดีที่สุด"
)

# Rayleigh 2-D: CEP = CE50 = 1.1774 σ; CE90 = √(-2 ln 0.10) σ ≈ 2.146 σ
CE90_SIGMA = math.sqrt(-2.0 * math.log(0.10))
CE90_OVER_CE50 = CE90_SIGMA / CEP_TO_SIGMA


@dataclass(frozen=True)
class CircularErrorMetric:
    key: str
    label_en: str
    label_th: str
    summary: str


CIRCULAR_ERROR_METRICS: tuple[CircularErrorMetric, ...] = (
    CircularErrorMetric(
        key="ce50",
        label_en="CE50 (Circular Error Probable 50%)",
        label_th="รัศมีวงกลมที่ลูกระเบิด 50% ตกภายใน",
        summary=(
            "รัศมีวงกลมรอบเป้าหมายที่ลูกระเบิดจำนวน 50% มีโอกาสตกภายในวงนี้ "
            "ค่า CEP ในระบบ Weaponeering คือ CE50"
        ),
    ),
    CircularErrorMetric(
        key="ce90",
        label_en="CE90",
        label_th="รัศมีวงกลมที่ครอบคลุมโอกาสตก 90%",
        summary=(
            "รัศมีวงกลมที่ครอบคลุมโอกาสตกของระเบิดถึง 90% "
            "วง CE90 จะมีขนาดใหญ่กว่า CE50 เสมอ"
        ),
    ),
)


@dataclass(frozen=True)
class CircularErrorInfo:
    title: str
    intro: str
    application: str
    metrics: tuple[CircularErrorMetric, ...]
    ce50_ft: float | None = None
    ce90_ft: float | None = None
    cep_source: str = ""


def ce90_from_ce50(ce50_ft: float) -> float:
    return float(ce50_ft) * CE90_OVER_CE50


def circular_error_info(
    *,
    ce50_ft: float | None = None,
    product_name: str = "",
) -> CircularErrorInfo:
    resolved_ce50: float | None = None
    source = ""
    if ce50_ft is not None:
        if product_name:
            resolved_ce50 = weapon_delivery_cep_ft(product_name, float(ce50_ft))
            source = "weapon" if is_guided_weapon(product_name) else "pilot"
        else:
            resolved_ce50 = float(ce50_ft)
            source = "pilot"
    ce90 = ce90_from_ce50(resolved_ce50) if resolved_ce50 is not None else None
    return CircularErrorInfo(
        title=CIRCULAR_ERROR_TITLE,
        intro=CIRCULAR_ERROR_INTRO,
        application=CIRCULAR_ERROR_APPLICATION,
        metrics=CIRCULAR_ERROR_METRICS,
        ce50_ft=resolved_ce50,
        ce90_ft=ce90,
        cep_source=source,
    )
