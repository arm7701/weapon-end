from maap_app.modules.weaponeering.laser_designation import (
    LASER_DESIGNATION_WORKFLOWS,
    designation_info_for,
    is_laser_guided_weapon,
)
from maap_app.modules.weaponeering.product_catalog import GUIDANCE_GPS, GUIDANCE_LASER, weapon_guidance


def test_lgb_requires_airborne_and_ground_designation() -> None:
    assert is_laser_guided_weapon("GBU-12")
    assert is_laser_guided_weapon("GBU-10 / GBU-16")
    assert is_laser_guided_weapon("GBU-82")
    assert not is_laser_guided_weapon("JDAM (Stand-off Weapon)")
    assert not is_laser_guided_weapon("MK-82")
    assert weapon_guidance("GBU-12") == GUIDANCE_LASER
    assert weapon_guidance("JDAM") == GUIDANCE_GPS

    info = designation_info_for("GBU-12")
    assert info is not None
    assert info.required is True
    assert [row.key for row in info.workflows] == ["airborne", "ground"]
    assert len(LASER_DESIGNATION_WORKFLOWS) == 2
    airborne = info.workflows[0]
    ground = info.workflows[1]
    assert "Litening" in airborne.summary or "Sniper" in airborne.summary
    assert "F-16" in airborne.summary
    assert "JTAC" in ground.summary or "CCT" in ground.summary
    assert "เมฆ" in info.weather_limitation
    assert "หมอก" in info.weather_limitation
    assert "ฝน" in info.weather_limitation


def test_jdam_does_not_require_laser_designation() -> None:
    info = designation_info_for("JDAM (Stand-off Weapon)")
    assert info is not None
    assert info.required is False
    assert info.workflows == ()
    assert designation_info_for("MK-84") is None
