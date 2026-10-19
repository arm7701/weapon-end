from __future__ import annotations

import json
from dataclasses import dataclass, field

from maap_app.modules.logistics.repository import LogisticsRepository
from maap_app.modules.ranking.repository import RankingRepository
from maap_app.modules.scenario.repository import ScenarioRepository
from maap_app.modules.target.repository import TargetRepository
from maap_app.modules.weaponeering.jmem_calculator import (
    JmemWeaponInputs,
    apply_selected_product_rank,
    estimate_mae_building_ft2,
    mission_inputs_from_target_card,
    rank_weapons,
)
from maap_app.modules.weaponeering.repository import WeaponeeringRepository
from maap_app.modules.wing_data.repository import WingDataRepository
from maap_app.modules.detection.repository import TargetDetectionRepository


@dataclass
class ContextBundle:
    scenario: dict = field(default_factory=dict)
    target: dict = field(default_factory=dict)
    weaponeering: dict = field(default_factory=dict)
    logistics: dict = field(default_factory=dict)
    ranking: dict = field(default_factory=dict)
    detection: dict = field(default_factory=dict)
    all_targets: list[dict] = field(default_factory=list)
    products: list[dict] = field(default_factory=list)
    wing_force: dict = field(default_factory=dict)
    deployment: dict = field(default_factory=dict)
    missing_data: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "scenario": self.scenario,
                "target": self.target,
                "weaponeering": self.weaponeering,
                "logistics": self.logistics,
                "ranking": self.ranking,
                "detection": self.detection,
                "all_targets": self.all_targets,
                "products": self.products,
                "wing_force": self.wing_force,
                "deployment": self.deployment,
                "missing_data": self.missing_data,
            },
            ensure_ascii=True,
        )


class ContextBundleBuilder:
    def __init__(
        self,
        scenario_repository: ScenarioRepository,
        target_repository: TargetRepository,
        weaponeering_repository: WeaponeeringRepository,
        logistics_repository: LogisticsRepository,
        ranking_repository: RankingRepository,
        detection_repository: TargetDetectionRepository | None = None,
        wing_data_repository: WingDataRepository | None = None,
    ) -> None:
        self.scenario_repository = scenario_repository
        self.target_repository = target_repository
        self.weaponeering_repository = weaponeering_repository
        self.logistics_repository = logistics_repository
        self.ranking_repository = ranking_repository
        self.detection_repository = detection_repository
        self.wing_data_repository = wing_data_repository

    def build(
        self,
        scenario_id: str,
        *,
        target_card_id: str | None = None,
        ranking_item_id: str | None = None,
    ) -> ContextBundle:
        bundle = ContextBundle()
        scenario = self.scenario_repository.get_scenario(scenario_id)
        if scenario:
            bundle.scenario = {
                "id": scenario.id,
                "name": scenario.name,
                "ruleset_version": scenario.ruleset_version,
                "description": scenario.description,
            }

        if target_card_id:
            detail = self.target_repository.get_target_detail(target_card_id)
            if detail:
                recognition = detail.recognition
                card = detail.card
                bundle.target = {
                    "id": card.id,
                    "label": card.label,
                    "target_type": card.target_type,
                    "target_subtype": card.target_subtype,
                    "material_class": card.material_class,
                    "target_description": card.target_description,
                    "floor_count": card.floor_count,
                    "width_m": card.width_m,
                    "length_m": card.length_m,
                    "height_m": card.height_m,
                    "desired_model_result": card.desired_model_result,
                    "coordinate_error_m": card.coordinate_error_m,
                    "data_source": card.data_source,
                    "cep": card.cep,
                    "target_pk": card.target_pk,
                    "reference_pk": card.reference_pk,
                    "resistance": card.resistance,
                    "capacity": card.capacity,
                    "damage_fit": card.damage_fit,
                    "model_version": card.model_version,
                    "priority_score": card.priority_score,
                    "complexity_score": card.complexity_score,
                    "review_status": card.review_status,
                    "recognition_confidence": (
                        recognition.recognition_confidence_score if recognition else None
                    ),
                    "recognition_summary": (
                        recognition.recognition_summary if recognition else ""
                    ),
                    "has_map_node": card.map_node_id is not None,
                    "map_lat": detail.map_lat,
                    "map_lng": detail.map_lng,
                    "coordinates": [
                        {
                            "label": c.label,
                            "lat": c.map_lat,
                            "lng": c.map_lng,
                            "is_primary": c.is_primary,
                        }
                        for c in (detail.coordinates or [])
                    ],
                }
                if not recognition:
                    bundle.missing_data.append("No Target Recognition Result attached.")
                elif recognition.recognition_confidence_score < 50:
                    bundle.missing_data.append("Recognition confidence is low.")
                if not card.map_node_id:
                    bundle.missing_data.append("Target Card is not linked to a map node.")

                assessments = self.weaponeering_repository.list_assessments_for_target(
                    target_card_id
                )
                bundle.weaponeering = {
                    "assessment_count": len(assessments),
                    "approved_count": sum(
                        1 for a in assessments if a.review_status == "approved"
                    ),
                }
                if assessments:
                    latest = assessments[0]
                    bundle.weaponeering["latest_suitability_score"] = latest.suitability_score
                    bundle.weaponeering["latest_feasibility_score"] = latest.feasibility_score
                    bundle.weaponeering["latest_risk_score"] = latest.risk_score
                    bundle.weaponeering["latest_rationale"] = latest.rationale
                bundle.detection = self._build_detection_context(target_card_id)
                bundle.products = self._build_product_ranking(scenario_id, detail)
                bundle.deployment = self._build_deployment_context(target_card_id)

        bundle.wing_force = self._build_wing_force_context(scenario_id)

        depots = self.logistics_repository.list_depots(scenario_id)
        platforms = self.logistics_repository.list_simulated_platforms(scenario_id)
        plan_score = self.logistics_repository.get_latest_plan_score(scenario_id)
        bundle.logistics = {
            "depot_count": len(depots),
            "platform_count": len(platforms),
            "logistics_feasibility": (
                plan_score.logistics_feasibility if plan_score else None
            ),
        }
        if plan_score is None:
            bundle.missing_data.append("No logistics feasibility score calculated.")

        if ranking_item_id:
            item = self.ranking_repository.get_ranking_item(ranking_item_id)
            if item:
                breakdown = RankingRepository.loads_breakdown(item.breakdown_json)
                warnings = breakdown.pop("warnings", [])
                bundle.ranking = {
                    "item_id": item.id,
                    "entity_label": item.entity_label or item.entity_id,
                    "rank_order": item.override_rank_order or item.rank_order,
                    "total_score": item.total_score,
                    "confidence_score": item.confidence_score,
                    "breakdown": breakdown,
                    "warnings": warnings,
                    "review_status": item.review_status,
                }
        else:
            run = self.ranking_repository.get_latest_ranking_run(scenario_id)
            if run:
                items = self.ranking_repository.list_ranking_items(run.id)
                bundle.ranking = {
                    "run_id": run.id,
                    "item_count": len(items),
                    "summary": run.summary,
                }
                bundle.all_targets = [
                    {
                        "rank": item.override_rank_order or item.rank_order,
                        "label": item.entity_label or item.entity_id,
                        "total_score": item.total_score,
                        "confidence_score": item.confidence_score,
                    }
                    for item in items
                ]
            else:
                bundle.missing_data.append("No ranking run available.")

        return bundle

    def build_for_scenario_chat(self, scenario_id: str) -> ContextBundle:
        """Build comprehensive Scenario Chat context from live database — no ranking run required."""
        bundle = self.build(scenario_id)

        # Primary source: all active targets directly from the database
        active_cards = self.target_repository.list_active_target_cards(scenario_id)
        if not active_cards:
            return bundle

        # Optional: merge ranking scores if a run exists
        rank_scores: dict[str, dict] = {}
        run = self.ranking_repository.get_latest_ranking_run(scenario_id)
        if run:
            for item in self.ranking_repository.list_ranking_items(run.id):
                if item.entity_id:
                    rank_scores[item.entity_id] = {
                        "rank": item.override_rank_order or item.rank_order,
                        "total_score": item.total_score,
                        "confidence_score": item.confidence_score,
                    }

        products_list = []
        if self.wing_data_repository is not None:
            products_list = self.wing_data_repository.list_products(scenario_id)
        cost_by_id = {p.id: p.unit_cost for p in products_list}

        enriched_targets = []
        for i, card in enumerate(active_cards, start=1):
            scores = rank_scores.get(card.id, {})
            enriched: dict = {
                "rank": scores.get("rank", i),
                "label": card.label,
                "target_type": card.target_type,
                "target_subtype": card.target_subtype,
                "material_class": card.material_class,
                "target_description": card.target_description,
                "floor_count": card.floor_count,
                "width_m": card.width_m,
                "length_m": card.length_m,
                "height_m": card.height_m,
                "desired_model_result": card.desired_model_result,
                "data_source": card.data_source,
                "cep": card.cep,
                "target_pk": card.target_pk,
                "reference_pk": card.reference_pk,
                "resistance": card.resistance,
                "capacity": card.capacity,
                "damage_fit": card.damage_fit,
                "priority_score": card.priority_score,
                "complexity_score": card.complexity_score,
                "total_score": scores.get("total_score"),
                "confidence_score": scores.get("confidence_score"),
            }

            target_missing: list[str] = []

            detail = self.target_repository.get_target_detail(card.id)
            if detail:
                enriched["primary_lat"] = detail.map_lat
                enriched["primary_lng"] = detail.map_lng

                recognition = detail.recognition
                if recognition:
                    enriched["recognition_confidence"] = recognition.recognition_confidence_score
                    if recognition.recognition_summary:
                        enriched["recognition_summary"] = recognition.recognition_summary
                    if recognition.recognition_confidence_score < 50:
                        target_missing.append("Recognition confidence is low.")
                else:
                    target_missing.append("No recognition result.")

                if not detail.card.map_node_id:
                    target_missing.append("Not linked to map node.")

                assessments = self.weaponeering_repository.list_assessments_for_target(card.id)
                enriched["assessment_count"] = len(assessments)
                enriched["approved_count"] = sum(
                    1 for a in assessments if a.review_status == "approved"
                )
                if not assessments:
                    target_missing.append("No weaponeering assessments.")

                detection = self._build_detection_context(card.id)
                if detection.get("available"):
                    enriched["detection_high"] = detection.get("building_high_count", 0)
                    enriched["detection_medium"] = detection.get("building_medium_count", 0)
                    enriched["detection_low"] = detection.get("building_low_count", 0)

                if products_list:
                    try:
                        mission = mission_inputs_from_target_card(detail.card)
                        weapons = [
                            JmemWeaponInputs(
                                product_id=p.id,
                                product_name=p.product_name,
                                weight_pounds=p.weight_pounds,
                                mae_building_ft2=estimate_mae_building_ft2(
                                    p.product_name, p.weight_pounds
                                ),
                            )
                            for p in products_list
                        ]
                        ranked = rank_weapons(mission, weapons)
                        if ranked:
                            top = ranked[0]
                            enriched["top_weapon"] = top.product_name
                            enriched["top_weapon_pd"] = round(top.pd_base, 4)
                            enriched["top_weapon_pk"] = round(top.pk_single, 4)
                            top_cost = cost_by_id.get(top.product_id)
                            if top_cost is not None:
                                enriched["top_weapon_unit_cost"] = top_cost
                                enriched["top_weapon_total_cost"] = round(
                                    top_cost * top.n_required, 2
                                )
                            weapon_options = []
                            for r in ranked[:5]:
                                unit_cost = cost_by_id.get(r.product_id)
                                weapon_options.append(
                                    {
                                        "rank": r.rank,
                                        "product_name": r.product_name,
                                        "pd_base": round(r.pd_base, 4),
                                        "pk_single": round(r.pk_single, 4),
                                        "n_required": r.n_required,
                                        "pk_n": round(r.pk_n, 4),
                                        "unit_cost": unit_cost,
                                        "total_cost": (
                                            round(unit_cost * r.n_required, 2)
                                            if unit_cost is not None
                                            else None
                                        ),
                                    }
                                )
                            enriched["weapon_options"] = weapon_options
                    except Exception:
                        pass

            if target_missing:
                enriched["missing"] = target_missing

            enriched_targets.append(enriched)

        enriched_targets.sort(
            key=lambda t: (t.get("rank") or 999, -(t.get("priority_score") or 0))
        )
        bundle.all_targets = enriched_targets
        return bundle

    def _build_wing_force_context(self, scenario_id: str) -> dict:
        if self.wing_data_repository is None:
            return {}
        repo = self.wing_data_repository

        wings = repo.list_wings(scenario_id)
        products = repo.list_products(scenario_id)
        if not wings and not products:
            return {}
        cost_by_id = {p.id: p.unit_cost for p in products}

        flying_units = repo.list_flying_units(scenario_id)
        aircraft_list = repo.list_aircraft(scenario_id)
        pilots = repo.list_pilots(scenario_id)
        depots = repo.list_depots(scenario_id)
        inventory = repo.list_inventory(scenario_id)
        vehicles = repo.list_vehicles(scenario_id)

        # Index helpers
        unit_by_id = {u.id: u for u in flying_units}
        units_by_wing: dict[str, list] = {}
        for u in flying_units:
            units_by_wing.setdefault(u.wing_id, []).append(u)
        ac_by_wing: dict[str, list] = {}
        for a in aircraft_list:
            ac_by_wing.setdefault(a.wing_id, []).append(a)
        pilots_by_wing: dict[str, list] = {}
        for p in pilots:
            if p.wing_id:
                pilots_by_wing.setdefault(p.wing_id, []).append(p)
        depots_by_wing: dict[str, list] = {}
        for d in depots:
            depots_by_wing.setdefault(d.wing_id, []).append(d)
        stock_by_depot: dict[str, list] = {}
        for inv in inventory:
            stock_by_depot.setdefault(inv.depot_id, []).append(inv)

        # Aircraft type readiness summary
        type_total: dict[str, int] = {}
        type_ready: dict[str, int] = {}
        for a in aircraft_list:
            type_total[a.aircraft_type] = type_total.get(a.aircraft_type, 0) + 1
            if a.mission_ready == "ready":
                type_ready[a.aircraft_type] = type_ready.get(a.aircraft_type, 0) + 1

        # Per-wing detail
        wings_data = []
        for w in wings:
            w_units = units_by_wing.get(w.id, [])
            w_ac = ac_by_wing.get(w.id, [])
            w_pilots = pilots_by_wing.get(w.id, [])
            w_depots = depots_by_wing.get(w.id, [])
            wings_data.append({
                "name": w.wing_name,
                "lat": w.map_lat,
                "lng": w.map_lng,
                "flying_units": [u.unit_name for u in w_units],
                "aircraft_total": len(w_ac),
                "aircraft_ready": sum(1 for a in w_ac if a.mission_ready == "ready"),
                "pilot_count": len(w_pilots),
                "depot_count": len(w_depots),
            })

        # Pilot list (cap at 25 to stay within token budget)
        PILOT_CAP = 25
        pilots_data = []
        for p in pilots[:PILOT_CAP]:
            wing_name = next((w.wing_name for w in wings if w.id == p.wing_id), None)
            unit_name = unit_by_id.get(p.flying_unit_id or "", None)
            pilots_data.append({
                "name": p.pilot_name,
                "callsign": p.callsign,
                "cep_m": round(p.cep_value, 1),
                "wing": wing_name,
                "unit": unit_name.unit_name if unit_name else None,
            })
        pilots_truncated = len(pilots) > PILOT_CAP

        # Depot + stock detail
        depots_data = []
        for d in depots:
            wing_name = next((w.wing_name for w in wings if w.id == d.wing_id), None)
            stock_items = stock_by_depot.get(d.id, [])
            depots_data.append({
                "name": d.depot_name,
                "wing": wing_name,
                "lat": d.map_lat,
                "lng": d.map_lng,
                "stock": [
                    {
                        "product": inv.product_name,
                        "qty": inv.quantity,
                        "unit_cost": cost_by_id.get(inv.product_id),
                    }
                    for inv in stock_items
                ],
            })

        # Vehicle list
        vehicles_data = []
        for v in vehicles:
            wing_name = next((w.wing_name for w in wings if w.id == v.wing_id), None)
            vehicles_data.append({
                "name": v.vehicle_name,
                "wing": wing_name,
                "fuel_rate_l_per_km": v.fuel_consumption_rate,
                "ready": v.mission_ready == "ready",
            })

        return {
            "wings": wings_data,
            "products": [
                {
                    "name": p.product_name,
                    "weight_pounds": p.weight_pounds,
                    "unit_cost": p.unit_cost,
                }
                for p in products
            ],
            "aircraft_by_type": [
                {
                    "type": t,
                    "total": type_total[t],
                    "ready": type_ready.get(t, 0),
                }
                for t in sorted(type_total)
            ],
            "pilots": pilots_data,
            "pilots_total": len(pilots),
            "pilots_truncated": pilots_truncated,
            "depots": depots_data,
            "vehicles": vehicles_data,
        }

    def _build_detection_context(self, target_card_id: str) -> dict:
        if self.detection_repository is None:
            return {
                "available": False,
                "risk_meaning": _DETECTION_RISK_MEANING,
            }
        run = self.detection_repository.get_run_for_target(target_card_id)
        if run is None:
            return {
                "available": False,
                "risk_meaning": _DETECTION_RISK_MEANING,
            }
        counts = {"high": 0, "medium": 0, "low": 0}
        objects = []
        for obj in run.objects:
            if obj.risk_level in counts:
                counts[obj.risk_level] += 1
            objects.append(
                {
                    "label": obj.object_label,
                    "type": obj.object_type,
                    "risk_level": obj.risk_level,
                    "risk_meaning": _DETECTION_RISK_MEANING.get(
                        obj.risk_level,
                        "ไม่ระบุระดับผลกระทบ",
                    ),
                    "confidence": round(obj.confidence, 4),
                    "center": {
                        "lat": round(obj.center_lat, 6),
                        "lng": round(obj.center_lng, 6),
                    },
                }
            )
        return {
            "available": True,
            "model_name": run.model_name,
            "radius_m": run.radius_m,
            "capture_radius_m": run.capture_radius_m,
            "object_count": run.object_count,
            "building_high_count": counts["high"],
            "building_medium_count": counts["medium"],
            "building_low_count": counts["low"],
            "risk_meaning": _DETECTION_RISK_MEANING,
            "objects": objects[:20],
            "message": run.detection_message or "",
        }


    def _build_deployment_context(self, target_card_id: str) -> dict:
        plan = self.weaponeering_repository.get_deployment_plan_for_target(target_card_id)
        if plan is None:
            return {}
        wing_name = None
        unit_name = None
        aircraft_lines: list[dict] = []
        if self.wing_data_repository is not None:
            wing = self.wing_data_repository.get_wing(plan.wing_id)
            wing_name = wing.wing_name if wing else None
            unit = self.wing_data_repository.get_flying_unit(plan.flying_unit_id)
            unit_name = unit.unit_name if unit else None
            for line in plan.aircraft_lines:
                aircraft = self.wing_data_repository.get_aircraft(line.aircraft_id)
                aircraft_lines.append(
                    {
                        "aircraft_type": aircraft.aircraft_type if aircraft else line.aircraft_id,
                        "count": line.aircraft_count,
                    }
                )
        return {
            "wing": wing_name,
            "flying_unit": unit_name,
            "aircraft_lines": aircraft_lines,
            "total_aircraft_count": plan.total_aircraft_count,
            "cruise_altitude_ft": plan.cruise_altitude_ft,
            "ingress_altitude_ft": plan.ingress_altitude_ft,
            "target_altitude_ft": plan.target_altitude_ft,
            "cruise_speed_kt": plan.cruise_speed_kt,
            "ingress_speed_kt": plan.ingress_speed_kt,
            "waypoint_count": len(plan.waypoints),
        }

    def _build_product_ranking(self, scenario_id: str, detail) -> list[dict]:
        if self.wing_data_repository is None:
            return []
        products = self.wing_data_repository.list_products(scenario_id)
        if not products:
            return []
        cost_by_id = {p.id: p.unit_cost for p in products}
        try:
            mission = mission_inputs_from_target_card(detail.card)
            weapons = [
                JmemWeaponInputs(
                    product_id=p.id,
                    product_name=p.product_name,
                    weight_pounds=p.weight_pounds,
                    mae_building_ft2=estimate_mae_building_ft2(
                        p.product_name,
                        p.weight_pounds,
                    ),
                )
                for p in products
            ]
            results = apply_selected_product_rank(
                rank_weapons(mission, weapons),
                detail.card.selected_product_id,
            )
            return [
                {
                    "rank": r.rank,
                    "product_name": r.product_name,
                    "weight_pounds": r.weight_pounds,
                    "unit_cost": cost_by_id.get(r.product_id),
                    "pd_base": round(r.pd_base, 4),
                    "pk_single": round(r.pk_single, 4),
                    "n_required": r.n_required,
                    "pk_n": round(r.pk_n, 4),
                    "total_cost": (
                        round(cost_by_id[r.product_id] * r.n_required, 2)
                        if cost_by_id.get(r.product_id) is not None
                        else None
                    ),
                    "is_selected": detail.card.selected_product_id == r.product_id,
                }
                for r in results[:5]
            ]
        except Exception:
            return []


_DETECTION_RISK_MEANING = {
    "high": "Building High คืออาคารหรือวัตถุที่ได้รับผลกระทบสูง",
    "medium": "Building Medium คืออาคารหรือวัตถุที่ได้รับผลกระทบปานกลาง",
    "low": "Building Low คืออาคารหรือวัตถุที่ได้รับผลกระทบต่ำสุด",
}


def format_context_as_text(bundle: ContextBundle) -> str:
    lines = ["=== MAAP CONTEXT (SIMULATION DATA) ==="]

    scenario = bundle.scenario
    if scenario:
        lines.append(f"\nScenario: {scenario.get('name', 'Unknown')}")
        if scenario.get("description"):
            lines.append(f"Description: {scenario['description']}")

    if bundle.all_targets:
        lines.append(f"\nAll Targets ({len(bundle.all_targets)} total):")
        for t in bundle.all_targets:
            rank = t.get("rank", "?")
            label = t.get("label", "Unknown")
            detail_parts = []
            if t.get("total_score") is not None:
                detail_parts.append(f"Score: {t['total_score']}/100")
            if t.get("confidence_score") is not None:
                detail_parts.append(f"Confidence: {t['confidence_score']}/100")
            if t.get("target_type"):
                detail_parts.append(f"Type: {t['target_type']}")
            if t.get("priority_score") is not None:
                detail_parts.append(f"Priority: {t['priority_score']}/5")
            if t.get("complexity_score") is not None:
                detail_parts.append(f"Complexity: {t['complexity_score']}/5")
            suffix = f" — {' | '.join(detail_parts)}" if detail_parts else ""
            lines.append(f"  {rank}. {label}{suffix}")
            if t.get("primary_lat") is not None and t.get("primary_lng") is not None:
                lines.append(f"     Coords: lat={t['primary_lat']}, lng={t['primary_lng']}")
            if t.get("recognition_confidence") is not None:
                lines.append(f"     Recognition: {t['recognition_confidence']}/100")
            if t.get("recognition_summary"):
                lines.append(f"     Recognition notes: {t['recognition_summary']}")
            if t.get("assessment_count") is not None:
                lines.append(
                    f"     Weaponeering: {t['assessment_count']} assessments"
                    f" ({t.get('approved_count', 0)} approved)"
                )
            if t.get("top_weapon"):
                pd_val = t.get("top_weapon_pd", 0)
                pk_val = t.get("top_weapon_pk", 0)
                cost_suffix = ""
                if t.get("top_weapon_unit_cost") is not None:
                    cost_suffix = (
                        f" | Unit cost: ${t['top_weapon_unit_cost']:,.2f}"
                        f" | Total cost: ${t.get('top_weapon_total_cost', 0):,.2f}"
                    )
                lines.append(
                    f"     Best weapon: {t['top_weapon']}"
                    f" — Pd: {pd_val:.2%} | Pk: {pk_val:.2%}{cost_suffix}"
                )
            weapon_options = t.get("weapon_options") or []
            if len(weapon_options) > 1:
                lines.append("     Weapon options (ranked):")
                for opt in weapon_options:
                    opt_cost = ""
                    if opt.get("unit_cost") is not None:
                        opt_cost = (
                            f" | Unit cost: ${opt['unit_cost']:,.2f}"
                            f" | Total cost: ${opt.get('total_cost', 0):,.2f}"
                        )
                    lines.append(
                        f"       {opt['rank']}. {opt['product_name']}"
                        f" — Pd: {opt['pd_base']:.2%} | Pk(single): {opt['pk_single']:.2%}"
                        f" | N required: {opt['n_required']} | Pk(N): {opt['pk_n']:.2%}"
                        f"{opt_cost}"
                    )
            profile_parts = []
            if t.get("material_class"):
                profile_parts.append(f"Material: {t['material_class']}")
            if t.get("target_subtype"):
                profile_parts.append(f"Subtype: {t['target_subtype']}")
            for key, text_label in (
                ("width_m", "W"),
                ("length_m", "L"),
                ("height_m", "H"),
            ):
                if t.get(key) is not None:
                    profile_parts.append(f"{text_label}={t[key]:.1f}m")
            if profile_parts:
                lines.append(f"     Profile: {' | '.join(profile_parts)}")
            engineering_parts = []
            if t.get("cep") is not None:
                engineering_parts.append(f"CEP={t['cep']}")
            if t.get("target_pk") is not None:
                engineering_parts.append(f"Target Pk={t['target_pk']}")
            if t.get("reference_pk") is not None:
                engineering_parts.append(f"Reference Pk={t['reference_pk']}")
            if t.get("resistance"):
                engineering_parts.append(f"Resistance={t['resistance']}")
            if t.get("capacity"):
                engineering_parts.append(f"Capacity={t['capacity']}")
            if t.get("damage_fit"):
                engineering_parts.append(f"Damage fit={t['damage_fit']}")
            if engineering_parts:
                lines.append(f"     Engineering: {' | '.join(engineering_parts)}")
            if t.get("target_description"):
                lines.append(f"     Notes: {t['target_description']}")
            if t.get("detection_high") is not None:
                lines.append(
                    f"     Detection: High={t['detection_high']}"
                    f" Med={t.get('detection_medium', 0)}"
                    f" Low={t.get('detection_low', 0)}"
                )
            if t.get("missing"):
                lines.append(f"     Missing: {'; '.join(t['missing'])}")

    target = bundle.target
    if target:
        lines.append(f"\nSelected Target: {target.get('label', 'Unknown')}")
        lines.append(f"  Type: {target.get('target_type', '?')}")
        if target.get("target_subtype"):
            lines.append(f"  Subtype: {target['target_subtype']}")
        if target.get("material_class"):
            lines.append(f"  Material: {target['material_class']}")
        dim_parts = []
        for key, text_label in (("width_m", "Width"), ("length_m", "Length"), ("height_m", "Height")):
            if target.get(key) is not None:
                dim_parts.append(f"{text_label}={target[key]:.1f}m")
        if target.get("floor_count"):
            dim_parts.append(f"Floors={target['floor_count']}")
        if dim_parts:
            lines.append(f"  Dimensions: {' | '.join(dim_parts)}")
        if target.get("target_description"):
            lines.append(f"  Description: {target['target_description']}")
        if target.get("desired_model_result"):
            lines.append(f"  Desired model result: {target['desired_model_result']}")
        engineering_parts = []
        if target.get("cep") is not None:
            engineering_parts.append(f"CEP={target['cep']}")
        if target.get("target_pk") is not None:
            engineering_parts.append(f"Target Pk={target['target_pk']}")
        if target.get("reference_pk") is not None:
            engineering_parts.append(f"Reference Pk={target['reference_pk']}")
        if target.get("coordinate_error_m") is not None:
            engineering_parts.append(f"Coordinate error={target['coordinate_error_m']}m")
        if engineering_parts:
            lines.append(f"  Engineering parameters: {' | '.join(engineering_parts)}")
        ref_parts = []
        if target.get("resistance"):
            ref_parts.append(f"Resistance={target['resistance']}")
        if target.get("capacity"):
            ref_parts.append(f"Capacity={target['capacity']}")
        if target.get("damage_fit"):
            ref_parts.append(f"Damage fit={target['damage_fit']}")
        if target.get("model_version"):
            ref_parts.append(f"Model version={target['model_version']}")
        if ref_parts:
            lines.append(f"  Reference model: {' | '.join(ref_parts)}")
        if target.get("data_source"):
            lines.append(f"  Data source: {target['data_source']}")
        lines.append(f"  Priority score: {target.get('priority_score', '?')}/5")
        lines.append(f"  Complexity score: {target.get('complexity_score', '?')}/5")
        if target.get("map_lat") is not None and target.get("map_lng") is not None:
            lines.append(f"  Primary location: lat={target['map_lat']}, lng={target['map_lng']}")
        coords = target.get("coordinates", [])
        if coords:
            lines.append("  Coordinate points:")
            for c in coords:
                primary_tag = " (primary)" if c.get("is_primary") else ""
                lines.append(
                    f"    - {c.get('label', 'Point')}{primary_tag}:"
                    f" lat={c.get('lat')}, lng={c.get('lng')}"
                )
        if target.get("recognition_confidence") is not None:
            lines.append(f"  Recognition confidence: {target['recognition_confidence']}/100")
        if target.get("recognition_summary"):
            lines.append(f"  Recognition notes: {target['recognition_summary']}")

    weaponeering = bundle.weaponeering
    if weaponeering.get("assessment_count") is not None:
        lines.append(
            f"\nWeaponeering Assessments: {weaponeering['assessment_count']} total"
            f" ({weaponeering.get('approved_count', 0)} approved)"
        )
        if weaponeering.get("latest_rationale") is not None:
            lines.append(
                f"  Latest: Suitability={weaponeering.get('latest_suitability_score', '?')}"
                f" | Feasibility={weaponeering.get('latest_feasibility_score', '?')}"
                f" | Risk={weaponeering.get('latest_risk_score', '?')}"
            )
            if weaponeering["latest_rationale"]:
                lines.append(f"  Rationale: {weaponeering['latest_rationale']}")

    deployment = bundle.deployment
    if deployment:
        lines.append("\nDeployment / Mission Plan:")
        if deployment.get("wing"):
            lines.append(
                f"  Wing: {deployment['wing']} | Flying unit: {deployment.get('flying_unit', '?')}"
            )
        for line in deployment.get("aircraft_lines", []):
            lines.append(f"  Aircraft: {line['count']} × {line['aircraft_type']}")
        lines.append(
            f"  Altitudes: cruise={deployment.get('cruise_altitude_ft', '?')}ft"
            f" | ingress={deployment.get('ingress_altitude_ft', '?')}ft"
            f" | target={deployment.get('target_altitude_ft', '?')}ft"
        )
        lines.append(
            f"  Speeds: cruise={deployment.get('cruise_speed_kt', '?')}kt"
            f" | ingress={deployment.get('ingress_speed_kt', '?')}kt"
        )
        lines.append(f"  Route waypoints: {deployment.get('waypoint_count', 0)}")

    detection = bundle.detection
    if detection.get("available"):
        lines.append(f"\nDetection Results (model: {detection.get('model_name', '?')}):")
        lines.append(f"  Total objects detected: {detection.get('object_count', 0)}")
        lines.append(f"  High-impact buildings: {detection.get('building_high_count', 0)}")
        lines.append(f"  Medium-impact buildings: {detection.get('building_medium_count', 0)}")
        lines.append(f"  Low-impact buildings: {detection.get('building_low_count', 0)}")
        if detection.get("message"):
            lines.append(f"  Assessment: {detection['message']}")
        objects = detection.get("objects", [])
        if objects:
            lines.append("  Detected objects:")
            for obj in objects[:10]:
                center = obj.get("center", {})
                lines.append(
                    f"    - {obj.get('label', '?')} ({obj.get('risk_level', '?')} risk)"
                    f" conf={obj.get('confidence', 0):.2f}"
                    f" lat={center.get('lat', '?')} lng={center.get('lng', '?')}"
                )

    ranking = bundle.ranking
    if ranking.get("entity_label"):
        lines.append(f"\nWeapon Ranking — {ranking['entity_label']}:")
        lines.append(f"  Rank: #{ranking.get('rank_order', '?')}")
        lines.append(f"  Total score: {ranking.get('total_score', '?')}/100")
        lines.append(f"  Confidence: {ranking.get('confidence_score', '?')}/100")
        breakdown = ranking.get("breakdown", {})
        if breakdown:
            lines.append("  Score breakdown:")
            for k, v in breakdown.items():
                if v is not None:
                    lines.append(f"    {k.replace('_', ' ')}: {v}")
        if ranking.get("warnings"):
            lines.append("  Warnings: " + "; ".join(ranking["warnings"]))

    logistics = bundle.logistics
    if logistics:
        lines.append(f"\nLogistics:")
        lines.append(f"  Depots: {logistics.get('depot_count', 0)}")
        lines.append(f"  Simulated platforms: {logistics.get('platform_count', 0)}")
        if logistics.get("logistics_feasibility") is not None:
            lines.append(f"  Feasibility score: {logistics['logistics_feasibility']}/100")

    if bundle.products:
        target_label = bundle.target.get("label", "this target")
        lines.append(f"\nWeapon Ranking for {target_label} (top {len(bundle.products)} by effectiveness):")
        for p in bundle.products:
            selected_tag = " ← selected" if p.get("is_selected") else ""
            cost_suffix = ""
            if p.get("unit_cost") is not None:
                cost_suffix = (
                    f" | Unit cost: ${p['unit_cost']:,.2f}"
                    f" | Total cost: ${p.get('total_cost', 0):,.2f}"
                )
            lines.append(
                f"  {p['rank']}. {p['product_name']} ({p['weight_pounds']:.0f} lb)"
                f" — Pd: {p['pd_base']:.2%} | Pk(single): {p['pk_single']:.2%}"
                f" | N required: {p['n_required']} | Pk(N): {p['pk_n']:.2%}"
                f"{cost_suffix}{selected_tag}"
            )

    wf = bundle.wing_force
    if wf:
        total_ac = sum(w.get("aircraft_total", 0) for w in wf.get("wings", []))
        ready_ac = sum(w.get("aircraft_ready", 0) for w in wf.get("wings", []))
        lines.append(
            f"\nWing Force Data"
            f" ({len(wf.get('wings', []))} wings"
            f" | {ready_ac}/{total_ac} aircraft ready"
            f" | {wf.get('pilots_total', 0)} pilots"
            f" | {len(wf.get('depots', []))} depots"
            f" | {len(wf.get('vehicles', []))} vehicles):"
        )

        products_catalog = wf.get("products", [])
        if products_catalog:
            lines.append(f"  Weapon/Product Catalog ({len(products_catalog)}):")
            for prod in products_catalog:
                lines.append(
                    f"    {prod['name']} — {prod['weight_pounds']:.0f} lb"
                    f" | Unit cost: ${prod['unit_cost']:,.2f}"
                )

        for w in wf.get("wings", []):
            loc = ""
            if w.get("lat") is not None and w.get("lng") is not None:
                loc = f" — lat={w['lat']:.5f}, lng={w['lng']:.5f}"
            units_str = ", ".join(w.get("flying_units", [])) or "none"
            lines.append(f"  Wing: {w['name']}{loc}")
            lines.append(f"    Flying units: {units_str}")
            lines.append(
                f"    Aircraft: {w['aircraft_ready']}/{w['aircraft_total']} ready"
                f" | Pilots: {w['pilot_count']}"
                f" | Depots: {w['depot_count']}"
            )

        by_type = wf.get("aircraft_by_type", [])
        if by_type:
            lines.append("  Aircraft by type:")
            for entry in by_type:
                lines.append(
                    f"    {entry['type']}: {entry['ready']}/{entry['total']} ready"
                )

        pilots = wf.get("pilots", [])
        if pilots:
            trunc = wf.get("pilots_truncated", False)
            total_p = wf.get("pilots_total", len(pilots))
            header = f"  Pilots ({total_p} total" + (", showing first 25):" if trunc else "):")
            lines.append(header)
            for p in pilots:
                parts = [f"{p['name']} ({p['callsign']}) — CEP: {p['cep_m']}m"]
                if p.get("wing"):
                    parts.append(p["wing"])
                if p.get("unit"):
                    parts.append(p["unit"])
                lines.append("    " + " | ".join(parts))

        depots = wf.get("depots", [])
        if depots:
            lines.append(f"  Depots ({len(depots)}):")
            for d in depots:
                loc = ""
                if d.get("lat") is not None and d.get("lng") is not None:
                    loc = f" — lat={d['lat']:.5f}, lng={d['lng']:.5f}"
                wing_str = f" [{d['wing']}]" if d.get("wing") else ""
                lines.append(f"    {d['name']}{wing_str}{loc}")
                for s in d.get("stock", []):
                    cost_suffix = (
                        f" (${s['unit_cost']:,.2f}/unit)" if s.get("unit_cost") is not None else ""
                    )
                    lines.append(f"      Stock: {s['product']} × {s['qty']}{cost_suffix}")
                if not d.get("stock"):
                    lines.append("      Stock: (empty)")

        vehicles = wf.get("vehicles", [])
        if vehicles:
            lines.append(f"  Vehicles ({len(vehicles)}):")
            for v in vehicles:
                ready_str = "พร้อม" if v.get("ready") else "ไม่พร้อม"
                wing_str = f" [{v['wing']}]" if v.get("wing") else ""
                lines.append(
                    f"    {v['name']}{wing_str}"
                    f" — {v['fuel_rate_l_per_km']:.2f} L/km — {ready_str}"
                )

    if bundle.missing_data:
        lines.append("\nMissing / Low-confidence data:")
        for m in bundle.missing_data:
            lines.append(f"  - {m}")

    return "\n".join(lines)
