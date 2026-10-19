from __future__ import annotations

from dataclasses import dataclass


WEAPON_EFFECTS_TITLE = "กลไกการทำลายล้างของระเบิด (Weapon Effects)"

WEAPON_EFFECTS_INTRO = "เมื่อระเบิดตกกระทบเป้าหมาย จะเกิดพลังทำลายล้างหลัก 3 รูปแบบ"


@dataclass(frozen=True)
class WeaponEffect:
    key: str
    label_en: str
    label_th: str
    summary: str


WEAPON_EFFECTS: tuple[WeaponEffect, ...] = (
    WeaponEffect(
        key="overpressure",
        label_en="Overpressure",
        label_th="แรงดันอากาศสูงยิ่งยวด",
        summary=(
            "แรงอัดมหาศาล (สูงถึง 700 ตันต่อตารางนิ้ว) ผลักอากาศออกอย่างรวดเร็วจนเกิดสภาวะสุญญากาศชั่วคราว "
            "สิ่งมีชีวิตในรัศมีจะเสียชีวิตจากการถูกทำลายอวัยวะภายใน โดยไม่มีบาดแผลภายนอก"
        ),
    ),
    WeaponEffect(
        key="fragmentation",
        label_en="Fragmentation",
        label_th="สะเก็ดระเบิด",
        summary=(
            "ปลอกเหล็กของระเบิด (Casing) จะแตกตัวเป็นชิ้นส่วนขนาดเล็ก 500–600 ชิ้น "
            "ปลิวกระจายด้วยความเร็วสูงมาก (3,000 - 10,000 ฟุต/วินาที)"
        ),
    ),
    WeaponEffect(
        key="cratering",
        label_en="Cratering",
        label_th="การเกิดแอ่งระเบิด",
        summary=(
            "การทำลายพื้นผิวให้เกิดหลุมลึกเพื่อตัดเส้นทางคมนาคม เช่น ทางวิ่งสนามบิน (Runway) หรือถนน "
            "เพื่อประวิงเวลาในการซ่อมแซมอย่างน้อย 4–5 วัน"
        ),
    ),
)


@dataclass(frozen=True)
class WeaponEffectsInfo:
    title: str
    intro: str
    effects: tuple[WeaponEffect, ...]


def weapon_effects_info() -> WeaponEffectsInfo:
    return WeaponEffectsInfo(
        title=WEAPON_EFFECTS_TITLE,
        intro=WEAPON_EFFECTS_INTRO,
        effects=WEAPON_EFFECTS,
    )
