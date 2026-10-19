from maap_app.modules.weaponeering.weapon_effects import WEAPON_EFFECTS, weapon_effects_info
from weaponeering_api.schemas.jmem import WeaponEffectOut, WeaponEffectsOut


def test_weapon_effects_cover_three_mechanisms() -> None:
    info = weapon_effects_info()
    assert [row.key for row in info.effects] == [
        "overpressure",
        "fragmentation",
        "cratering",
    ]
    assert len(WEAPON_EFFECTS) == 3
    overpressure, fragmentation, cratering = info.effects
    assert "700" in overpressure.summary
    assert "สุญญากาศ" in overpressure.summary
    assert "อวัยวะภายใน" in overpressure.summary
    assert "500" in fragmentation.summary and "600" in fragmentation.summary
    assert "3,000" in fragmentation.summary and "10,000" in fragmentation.summary
    assert "Casing" in fragmentation.summary
    assert "Runway" in cratering.summary or "ทางวิ่ง" in cratering.summary
    assert "4–5" in cratering.summary or "4-5" in cratering.summary


def test_weapon_effects_schema_serializes_doctrine() -> None:
    info = weapon_effects_info()
    payload = WeaponEffectsOut(
        title=info.title,
        intro=info.intro,
        effects=[
            WeaponEffectOut(
                key=row.key,
                label_en=row.label_en,
                label_th=row.label_th,
                summary=row.summary,
            )
            for row in info.effects
        ],
    )
    dumped = payload.model_dump()
    assert dumped["title"] == "กลไกการทำลายล้างของระเบิด (Weapon Effects)"
    assert "3 รูปแบบ" in dumped["intro"]
    assert [row["key"] for row in dumped["effects"]] == [
        "overpressure",
        "fragmentation",
        "cratering",
    ]
