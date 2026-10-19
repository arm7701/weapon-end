from __future__ import annotations

from maap_app.ui.panels.map_targets_list_panel import (
    format_detected_ago,
    priority_tier_from_score,
)


def test_priority_tier_from_score() -> None:
    assert priority_tier_from_score(5) == "high"
    assert priority_tier_from_score(4) == "high"
    assert priority_tier_from_score(3) == "medium"
    assert priority_tier_from_score(2) == "low"


def test_format_detected_ago_without_timestamp() -> None:
    assert format_detected_ago(None) == "Not yet"
