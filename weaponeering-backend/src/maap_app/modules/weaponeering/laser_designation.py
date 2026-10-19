from __future__ import annotations

from dataclasses import dataclass

from maap_app.modules.weaponeering.product_catalog import (
    GUIDANCE_GPS,
    GUIDANCE_LASER,
    weapon_guidance,
)

LASER_DESIGNATION_TITLE = "ยุทธวิธีการชี้เป้าด้วยแสงเลเซอร์ (Laser Designation)"

LASER_DESIGNATION_INTRO = (
    "ระเบิดนำวิถีด้วยเลเซอร์ (LGB) จำเป็นต้องมีแหล่งกำเนิดแสงเลเซอร์เพื่อนำทางหัวระเบิดดวงตา "
    "(Seeker) เข้าสู่เป้าหมาย ซึ่งทำได้ 2 วิธีการปฏิบัติการ"
)

LASER_WEATHER_LIMITATION = (
    "ข้อจำกัดเชิงยุทธวิธี: สภาพอากาศ (เมฆ หมอก ฝน) เป็นอุปสรรคสำคัญ "
    "เนื่องจากแสงเลเซอร์และเซ็นเซอร์หัวระเบิดไม่สามารถส่องผ่านสภาพอากาศที่ปิดได้"
)


@dataclass(frozen=True)
class LaserDesignationWorkflow:
    key: str
    label_en: str
    label_th: str
    summary: str


LASER_DESIGNATION_WORKFLOWS: tuple[LaserDesignationWorkflow, ...] = (
    LaserDesignationWorkflow(
        key="airborne",
        label_en="Airborne Designation",
        label_th="ชี้เป้าจากอากาศ",
        summary=(
            "ใช้เครื่องบินที่ติดตั้งกระเปาะชี้เป้า (Targeting Pod เช่น Litening Pod / Sniper Pod) "
            "บินสาดแสงเลเซอร์ไปยังเป้าหมาย โดยในกองทัพมีเพียงเครื่องบินบางแบบเท่านั้น "
            "(เช่น F-16) ที่ทำหน้าที่เป็นตัวฉายแสงเลเซอร์ได้"
        ),
    ),
    LaserDesignationWorkflow(
        key="ground",
        label_en="Ground Designation",
        label_th="ชี้เป้าจากภาคพื้น",
        summary=(
            "ให้หน่วยควบคุมการรบร่วมภาคพื้นดิน (JTAC/CCT) ใช้เครื่องยิงแสงเลเซอร์ฉายใส่เป้าหมายโดยตรง "
            "เครื่องบินมีหน้าที่เพียงบินมาปลดระเบิดให้ลงมาในสตรีมแสงเลเซอร์เท่านั้น"
        ),
    ),
)


@dataclass(frozen=True)
class LaserDesignationInfo:
    required: bool
    title: str
    intro: str
    weather_limitation: str
    workflows: tuple[LaserDesignationWorkflow, ...]
    guidance: str


def is_laser_guided_weapon(product_name: str) -> bool:
    return weapon_guidance(product_name) == GUIDANCE_LASER


def designation_info_for(product_name: str) -> LaserDesignationInfo | None:
    guidance = weapon_guidance(product_name)
    if guidance == GUIDANCE_LASER:
        return LaserDesignationInfo(
            required=True,
            title=LASER_DESIGNATION_TITLE,
            intro=LASER_DESIGNATION_INTRO,
            weather_limitation=LASER_WEATHER_LIMITATION,
            workflows=LASER_DESIGNATION_WORKFLOWS,
            guidance=guidance,
        )
    if guidance == GUIDANCE_GPS:
        return LaserDesignationInfo(
            required=False,
            title="นำวิถีด้วย GPS (ไม่ต้องชี้เป้าเลเซอร์)",
            intro=(
                "JDAM / อาวุธปล่อยร่อนใช้ชุดหางนำวิถีด้วย GPS "
                "ไม่จำเป็นต้องมีแหล่งกำเนิดแสงเลเซอร์เพื่อนำทางหัวระเบิด"
            ),
            weather_limitation="",
            workflows=(),
            guidance=guidance,
        )
    return None


def designation_warning_lines(product_name: str) -> tuple[str, ...]:
    info = designation_info_for(product_name)
    if info is None or not info.required:
        return ()
    return (info.weather_limitation,)
