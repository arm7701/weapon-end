from __future__ import annotations

from dataclasses import replace

from maap_app.modules.target.models import TargetCard
from maap_app.modules.weaponeering.jmem_calculator import (
    JmemCalculationResult,
    JmemMissionInputs,
)
from maap_app.modules.weaponeering.product_advisor import (
    product_analysis_prompt,
    recommend_product,
)
from maap_app.modules.wing_data.models import WingProduct


def _mission() -> JmemMissionInputs:
    return JmemMissionInputs(
        cep_ft=50.0,
        tle_ft=10.0,
        impact_angle_deg=90.0,
        burial_pct=0.0,
        target_length_ft=100.0,
        target_width_ft=80.0,
        p_rel=0.9,
        p_wpn=0.95,
        pk_desired=0.9,
    )


def _card() -> TargetCard:
    return TargetCard(
        id="tgt-1",
        scenario_id="scenario-1",
        label="TGT-001",
        priority_score=4,
        complexity_score=3,
        map_node_id=None,
        review_status="draft",
        status="active",
        target_type="BUILDING",
        material_class="REINFORCED CONCRETE",
    )


def _result(
    *,
    product_id: str,
    name: str,
    rank: int,
    n_required: int,
    pk_n: float,
    weight: float = 500.0,
) -> JmemCalculationResult:
    return JmemCalculationResult(
        product_id=product_id,
        product_name=name,
        weight_pounds=weight,
        mae_building_ft2=100.0,
        cep_total_ft=55.0,
        sigma_ft=46.7,
        a_error_ft2=200.0,
        mae_eff_ft2=300.0,
        a_target_ft2=8000.0,
        mae_adjusted_ft2=300.0,
        pd_base=0.35,
        pk_single=0.4,
        n_required=n_required,
        pk_n=pk_n,
        range_red_ft=14.0,
        range_orange_min_ft=14.0,
        range_orange_max_ft=16.0,
        range_yellow_dark_ft=20.0,
        range_yellow_light_ft=30.0,
        rank=rank,
    )


def test_recommend_product_prefers_lower_cost_when_pk_met() -> None:
    recommendation = recommend_product(
        _card(),
        _mission(),
        [
            _result(product_id="p1", name="MK-84", rank=1, n_required=8, pk_n=0.92),
            _result(product_id="p2", name="MK-82", rank=2, n_required=2, pk_n=0.91),
        ],
        [
            WingProduct("p1", "scenario-1", "MK-84", 2000.0, 300_000.0, "active"),
            WingProduct("p2", "scenario-1", "MK-82", 500.0, 50_000.0, "active"),
        ],
        stock_by_product={"p1": 20, "p2": 30},
    )
    assert recommendation is not None
    assert recommendation.product_id == "p2"
    assert recommendation.mission_cost == 100_000.0
    assert any("ค่าใช้จ่ายภารกิจ" in factor for factor in recommendation.factors)


def test_recommend_product_penalizes_insufficient_stock() -> None:
    recommendation = recommend_product(
        _card(),
        _mission(),
        [
            _result(product_id="p1", name="GBU-84", rank=1, n_required=2, pk_n=0.95),
            _result(product_id="p2", name="MK-82", rank=2, n_required=3, pk_n=0.91),
        ],
        [
            WingProduct("p1", "scenario-1", "GBU-84", 2000.0, 400_000.0, "active"),
            WingProduct("p2", "scenario-1", "MK-82", 500.0, 80_000.0, "active"),
        ],
        stock_by_product={"p1": 1, "p2": 20},
    )
    assert recommendation is not None
    assert recommendation.product_id == "p2"


def test_product_analysis_prompt_includes_cost_context() -> None:
    recommendation = recommend_product(
        _card(),
        _mission(),
        [_result(product_id="p1", name="MK-84", rank=1, n_required=2, pk_n=0.93)],
        [WingProduct("p1", "scenario-1", "MK-84", 2000.0, 100_000.0, "active")],
    )
    assert recommendation is not None
    prompt = product_analysis_prompt(
        recommendation,
        target_label="TGT-001",
        target_type="BUILDING",
    )
    assert "TGT-001" in prompt
    assert "product_id: p1" in prompt
    assert "เป้านิ่ง" in prompt
    assert "MK" in prompt
    assert "ค่าใช้จ่าย" in prompt or "ภารกิจ" in recommendation.rationale
    assert "Overpressure" in prompt
    assert "Fragmentation" in prompt
    assert "Cratering" in prompt
    assert "CE50" in prompt
    assert "CE90" in prompt
    assert "Pilot CEP" in prompt
    assert "1998" in prompt


def test_recommend_product_prefers_gbu_for_tank() -> None:
    tank_card = replace(_card(), target_type="TANK", material_class="STEEL")
    recommendation = recommend_product(
        tank_card,
        _mission(),
        [
            _result(product_id="p1", name="GBU-84", rank=2, n_required=2, pk_n=0.91),
            _result(product_id="p2", name="MK-82", rank=1, n_required=2, pk_n=0.93),
        ],
        [
            WingProduct("p1", "scenario-1", "GBU-84", 2000.0, 400_000.0, "active"),
            WingProduct("p2", "scenario-1", "MK-82", 500.0, 80_000.0, "active"),
        ],
        stock_by_product={"p1": 20, "p2": 30},
    )
    assert recommendation is not None
    assert recommendation.product_name == "GBU-84"
    assert any("เคลื่อนที่" in factor for factor in recommendation.factors)


def test_recommend_product_prefers_mk_for_building() -> None:
    recommendation = recommend_product(
        _card(),
        _mission(),
        [
            _result(product_id="p1", name="GBU-84", rank=1, n_required=2, pk_n=0.95),
            _result(product_id="p2", name="MK-82", rank=2, n_required=2, pk_n=0.91),
        ],
        [
            WingProduct("p1", "scenario-1", "GBU-84", 2000.0, 400_000.0, "active"),
            WingProduct("p2", "scenario-1", "MK-82", 500.0, 80_000.0, "active"),
        ],
        stock_by_product={"p1": 20, "p2": 30},
    )
    assert recommendation is not None
    assert recommendation.product_name == "MK-82"
    assert any("นิ่ง" in factor for factor in recommendation.factors)
    assert any("Overpressure" in factor for factor in recommendation.factors)
    assert any("Fragmentation" in factor for factor in recommendation.factors)
    assert any("Cratering" in factor for factor in recommendation.factors)
    assert any("CE50" in factor and "CE90" in factor for factor in recommendation.factors)
