from __future__ import annotations

from dataclasses import dataclass, field


REQUEST_TYPES = (
    "chat_with_context",
    "summarize_target",
    "identify_missing_data",
    "suggest_abstract_option",
    "explain_ranking",
    "draft_plan_summary",
    "generate_review_questions",
    "analyze_product_selection",
)

CLASSIFIER_LABELS = (
    "safe_training",
    "needs_reframing",
    "blocked_operational",
)


@dataclass(frozen=True)
class AiRequest:
    scenario_id: str
    request_type: str
    entity_type: str = ""
    entity_id: str = ""
    user_prompt: str = ""


@dataclass
class AiResponsePayload:
    summary: str = ""
    missing_data: list[str] = field(default_factory=list)
    confidence_note: str = ""
    review_required: bool = True
    score_drivers: list[str] = field(default_factory=list)
    instructor_questions: list[str] = field(default_factory=list)
    suggested_option: dict[str, str | int] = field(default_factory=dict)
    suggested_product_id: str = ""
    analysis_factors: list[str] = field(default_factory=list)
    plan_title: str = ""
    simulation_only_label: str = "SIMULATION-ONLY TRAINING OUTPUT"

    def to_text(self) -> str:
        lines = [self.summary]
        if self.missing_data:
            lines.append("Missing data: " + "; ".join(self.missing_data))
        if self.confidence_note:
            lines.append(self.confidence_note)
        if self.score_drivers:
            lines.append("Score drivers: " + "; ".join(self.score_drivers))
        if self.instructor_questions:
            lines.append("Instructor questions:")
            lines.extend(f"- {q}" for q in self.instructor_questions)
        if self.suggested_option:
            lines.append(
                "Suggested option: "
                + ", ".join(f"{k}={v}" for k, v in self.suggested_option.items())
            )
        if self.plan_title:
            lines.append(f"Plan title: {self.plan_title}")
        lines.append(self.simulation_only_label)
        return "\n".join(lines)
