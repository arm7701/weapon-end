from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

HIGH_DRAG_IMPACT_ANGLE_DEG = 90.0

CATEGORY_GRAVITY = "gravity"
CATEGORY_CLUSTER = "cluster"
CATEGORY_GUIDED = "guided"

DELIVERY_LOW_DRAG = "low_drag"
DELIVERY_HIGH_DRAG = "high_drag"
DELIVERY_GUIDED = "guided"
DELIVERY_CLUSTER = "cluster"

GUIDANCE_UNGUIDED = "unguided"
GUIDANCE_LASER = "laser"
GUIDANCE_GPS = "gps"

_HIGH_DRAG_MARKERS = ("mk15", "highdrag", "snakeye", "หางเตะ", "หางหน่วง")


def normalize_product_key(product_name: str) -> str:
    return (
        product_name.lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "")
    )


@dataclass(frozen=True)
class KnownProduct:
    key: str
    product_name: str
    weight_pounds: float
    unit_cost: float = 0.0
    description: str = ""
    delivery: str = DELIVERY_LOW_DRAG
    guidance: str = GUIDANCE_UNGUIDED
    category: str = CATEGORY_GRAVITY
    category_label: str = "ระเบิดธรรมดา (Gravity/Iron Bombs)"
    match_tokens: tuple[str, ...] = ()


KNOWN_PRODUCTS: tuple[KnownProduct, ...] = (
    KnownProduct(
        key="mk-81",
        product_name="MK 81 (250 lb)",
        weight_pounds=250.0,
        description="ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 250 ปอนด์",
        match_tokens=("mk81",),
    ),
    KnownProduct(
        key="mk-82",
        product_name="MK 82 (500 lb)",
        weight_pounds=500.0,
        description=(
            "ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 500 ปอนด์ "
            "นิยมใช้งานมากที่สุด"
        ),
        match_tokens=("mk82",),
    ),
    KnownProduct(
        key="mk-83",
        product_name="MK 83 (1,000 lb)",
        weight_pounds=1000.0,
        description=(
            "ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 1,000 ปอนด์ "
            "นิยมใช้งานมากที่สุด"
        ),
        match_tokens=("mk83",),
    ),
    KnownProduct(
        key="mk-84",
        product_name="MK 84 (2,000 lb)",
        weight_pounds=2000.0,
        description="ระเบิดธรรมดา (Gravity/Iron Bomb) ซีรีส์ ขนาด 2,000 ปอนด์",
        match_tokens=("mk84",),
    ),
    KnownProduct(
        key="mk-15-high-drag",
        product_name="MK 15 (High-Drag Bomb)",
        weight_pounds=500.0,
        description=(
            "ระเบิดติดตั้งหางหน่วงแรงกังหัน (หางเตะ) สำหรับการทิ้งระเบิดในระยะต่ำ "
            "เพื่อให้เครื่องบินรบสามารถบินพ้นรัศมีแรงระเบิด โดยระเบิดจะตกทำมุมชันเกือบ 90 องศา"
        ),
        delivery=DELIVERY_HIGH_DRAG,
        match_tokens=("mk15", "highdrag", "snakeye"),
    ),
    KnownProduct(
        key="cbu-49-71",
        product_name="CBU-49 / CBU-71 (Cluster Bomb)",
        weight_pounds=800.0,
        description=(
            "ระเบิดพวง/ระเบิดลูกปู บรรจุลูกระเบิดขนาดเล็ก (ลูกน้อยหน่า/ลูกเกลี้ยง) ประมาณ 300 ลูกอยู่ภายใน "
            "เมื่อปล่อยจากเครื่องบิน ปลอกนอกจะแยกออกเพื่อกระจายลูกระเบิดเล็กครอบคลุมพื้นที่กว้างเกือบ 2 กิโลเมตร "
            "ใช้สำหรับจำกัดการเข้าถึงของข้าศึก (Area Denial) "
            "หมายเหตุสำคัญ: ปัจจุบันประเทศไทยได้ลงนามในสนธิสัญญาห้ามใช้ระเบิดพวง "
            "(Convention on Cluster Munitions) แล้ว จึงไม่มีการนำมาใช้งานในภารกิจหลัก"
        ),
        delivery=DELIVERY_CLUSTER,
        category=CATEGORY_CLUSTER,
        category_label="ระเบิดพวง/ระเบิดลูกปู (Cluster Bombs)",
        match_tokens=("cbu49", "cbu71", "cbu", "clusterbomb", "ระเบิดพวง", "ลูกปู"),
    ),
    KnownProduct(
        key="gbu-12",
        product_name="GBU-12 (Laser-Guided, MK 82)",
        weight_pounds=500.0,
        description=(
            "ระเบิดนำวิถีเลเซอร์ (Laser-Guided Bomb) ฐานจาก MK 82 "
            "ควบคุมการตกด้วยระบบเซ็นเซอร์ตรวจจับลำแสงเลเซอร์ "
            "จำเป็นต้องมีแหล่งชี้เป้าเลเซอร์จากอากาศ (Targeting Pod เช่น Litening/Sniper บน F-16) "
            "หรือจากภาคพื้น (JTAC/CCT) และมีข้อจำกัดเมื่อสภาพอากาศปิด"
        ),
        delivery=DELIVERY_GUIDED,
        guidance=GUIDANCE_LASER,
        category=CATEGORY_GUIDED,
        category_label="ระเบิดนำวิถีและระเบิดอัจฉริยะ (Guided & Smart Bombs)",
        match_tokens=("gbu12", "gbu82"),
    ),
    KnownProduct(
        key="gbu-10-16",
        product_name="GBU-10 / GBU-16 (Laser-Guided, MK 84)",
        weight_pounds=2000.0,
        description=(
            "ระเบิดนำวิถีเลเซอร์ (Laser-Guided Bomb) ฐานจาก MK 84 "
            "เช่น GBU-10 และ GBU-16 ควบคุมการตกด้วยระบบเซ็นเซอร์ตรวจจับลำแสงเลเซอร์ "
            "จำเป็นต้องมีแหล่งชี้เป้าเลเซอร์จากอากาศ (Targeting Pod เช่น Litening/Sniper บน F-16) "
            "หรือจากภาคพื้น (JTAC/CCT) และมีข้อจำกัดเมื่อสภาพอากาศปิด"
        ),
        delivery=DELIVERY_GUIDED,
        guidance=GUIDANCE_LASER,
        category=CATEGORY_GUIDED,
        category_label="ระเบิดนำวิถีและระเบิดอัจฉริยะ (Guided & Smart Bombs)",
        match_tokens=("gbu10", "gbu16", "gbu84"),
    ),
    KnownProduct(
        key="jdam",
        product_name="JDAM (Stand-off Weapon)",
        weight_pounds=2000.0,
        description=(
            "ระเบิดติดตั้งชุดหางนำวิถีด้วย GPS / อาวุธปล่อยร่อน (Stand-off Weapon) "
            "สามารถร่อนไปทำลายเป้าหมายได้เองจากระยะไกลสูงสุดถึง 100 กิโลเมตร "
            "ช่วยให้เครื่องบินปล่อยอาวุธนอกระยะต่อต้านของข้าศึก "
            "มีความสามารถเลี้ยวอ้อมสันเขาได้ถึง 180 องศา"
        ),
        delivery=DELIVERY_GUIDED,
        guidance=GUIDANCE_GPS,
        category=CATEGORY_GUIDED,
        category_label="ระเบิดนำวิถีและระเบิดอัจฉริยะ (Guided & Smart Bombs)",
        match_tokens=("jdam", "standoff", "gbu31", "gbu32", "gbu38", "ปล่อยร่อน"),
    ),
)

_PRODUCTS_BY_KEY = {item.key: item for item in KNOWN_PRODUCTS}
# MK 15 / GBU / JDAM / CBU before MK-82 so "Mk-82 Snakeye" and "GBU-12" stay distinct.
_LOOKUP_ORDER: tuple[KnownProduct, ...] = tuple(
    _PRODUCTS_BY_KEY[key]
    for key in (
        "mk-15-high-drag",
        "gbu-12",
        "gbu-10-16",
        "jdam",
        "cbu-49-71",
        "mk-84",
        "mk-83",
        "mk-82",
        "mk-81",
    )
)


def fingerprint(product_name: str) -> str | None:
    compact = normalize_product_key(product_name)
    if not compact:
        return None
    for item in _LOOKUP_ORDER:
        if any(token in compact for token in item.match_tokens if token.isascii()):
            return item.key
        if any(token in product_name for token in item.match_tokens if not token.isascii()):
            return item.key
    return None


def lookup_known_product(product_name: str) -> KnownProduct | None:
    key = fingerprint(product_name)
    if key is None:
        return None
    return _PRODUCTS_BY_KEY.get(key)


def missing_known_products(existing_names: Iterable[str]) -> list[KnownProduct]:
    present = {fingerprint(name) for name in existing_names}
    present.discard(None)
    return [item for item in KNOWN_PRODUCTS if item.key not in present]


def is_high_drag_weapon(product_name: str) -> bool:
    known = lookup_known_product(product_name)
    if known is not None:
        return known.delivery == DELIVERY_HIGH_DRAG
    compact = normalize_product_key(product_name)
    if any(marker in compact for marker in _HIGH_DRAG_MARKERS):
        return True
    return any(marker in product_name for marker in ("หางเตะ", "หางหน่วง"))


def is_cluster_weapon(product_name: str) -> bool:
    known = lookup_known_product(product_name)
    if known is not None:
        return known.delivery == DELIVERY_CLUSTER
    compact = normalize_product_key(product_name)
    return "cbu" in compact or "cluster" in compact or "ระเบิดพวง" in product_name


def weapon_impact_angle_deg(product_name: str, mission_angle_deg: float) -> float:
    if is_high_drag_weapon(product_name):
        return HIGH_DRAG_IMPACT_ANGLE_DEG
    return mission_angle_deg


def catalog_description(product_name: str, stored: str | None = None) -> str:
    if stored and stored.strip():
        return stored.strip()
    known = lookup_known_product(product_name)
    return known.description if known else ""


def weapon_guidance(product_name: str) -> str:
    known = lookup_known_product(product_name)
    if known is not None:
        return known.guidance
    compact = normalize_product_key(product_name)
    gps_markers = ("jdam", "gbu31", "gbu32", "gbu38", "gbu39", "gbu54")
    if any(marker in compact for marker in gps_markers):
        return GUIDANCE_GPS
    if "gbu" in compact or "paveway" in compact or "lgb" in compact:
        return GUIDANCE_LASER
    return GUIDANCE_UNGUIDED
