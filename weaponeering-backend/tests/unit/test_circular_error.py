from maap_app.modules.weaponeering.circular_error import (
    CE90_OVER_CE50,
    CIRCULAR_ERROR_METRICS,
    ce90_from_ce50,
    circular_error_info,
)
from maap_app.modules.weaponeering.jmem_calculator import GUIDED_LASER_CEP_FT
from weaponeering_api.schemas.jmem import CircularErrorMetricOut, CircularErrorOut


def test_circular_error_covers_ce50_and_ce90() -> None:
    info = circular_error_info()
    assert [row.key for row in info.metrics] == ["ce50", "ce90"]
    assert len(CIRCULAR_ERROR_METRICS) == 2
    ce50, ce90 = info.metrics
    assert "50%" in ce50.summary
    assert "90%" in ce90.summary
    assert "ใหญ่กว่า" in ce90.summary
    assert "1998" in info.application
    assert "Pilot CEP" in info.application
    assert info.ce50_ft is None
    assert info.ce90_ft is None


def test_ce90_is_always_larger_than_ce50() -> None:
    ce50 = 120.0
    ce90 = ce90_from_ce50(ce50)
    assert ce90 > ce50
    assert CE90_OVER_CE50 > 1.0
    assert abs(ce90 / ce50 - CE90_OVER_CE50) < 1e-9


def test_unguided_uses_pilot_cep_and_guided_uses_weapon_cep() -> None:
    mk = circular_error_info(ce50_ft=120.0, product_name="MK-82")
    assert mk.cep_source == "pilot"
    assert mk.ce50_ft == 120.0
    assert mk.ce90_ft is not None and mk.ce90_ft > mk.ce50_ft

    gbu = circular_error_info(ce50_ft=120.0, product_name="GBU-12")
    assert gbu.cep_source == "weapon"
    assert gbu.ce50_ft == GUIDED_LASER_CEP_FT
    assert gbu.ce90_ft is not None and gbu.ce90_ft > gbu.ce50_ft
    assert gbu.ce50_ft < mk.ce50_ft


def test_circular_error_schema_serializes_doctrine() -> None:
    info = circular_error_info(ce50_ft=120.0)
    payload = CircularErrorOut(
        title=info.title,
        intro=info.intro,
        application=info.application,
        metrics=[
            CircularErrorMetricOut(
                key=row.key,
                label_en=row.label_en,
                label_th=row.label_th,
                summary=row.summary,
            )
            for row in info.metrics
        ],
        ce50_ft=info.ce50_ft,
        ce90_ft=info.ce90_ft,
        cep_source=info.cep_source,
    )
    dumped = payload.model_dump()
    assert dumped["title"] == "การคำนวณค่าความแม่นยำทางสถิติ (CEP & Circular Error)"
    assert "ความคลาดเคลื่อนวงกลม" in dumped["intro"]
    assert [row["key"] for row in dumped["metrics"]] == ["ce50", "ce90"]
    assert dumped["ce50_ft"] == 120.0
    assert dumped["ce90_ft"] > dumped["ce50_ft"]
