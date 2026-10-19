# Random Target Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Generate Random Target" button to the Target Stack sidebar that pre-fills the Target Form with randomized profile values for the user to review and edit before saving.

**Architecture:** A new pure-function module (`random_generator.py`) produces a `RandomTargetSuggestion`. The Target Stack sidebar gets a new button/signal; the Target Form panel and its profile-form widget gain methods to request a suggestion and apply it to the form fields. Nothing is persisted until the user presses the existing Save button.

**Tech Stack:** Python 3.12, PySide6 (Qt widgets), pytest (`pythonpath = ["src"]`, `testpaths = ["tests"]`, configured in `pyproject.toml`). Run tests with `.venv/Scripts/python.exe -m pytest <path> -v`.

## Global Constraints

- No new persistence path — generation only fills form fields; saving still goes through the existing `TargetFormPanel._on_save` → `TargetService.create_target_card` flow.
- Randomized fields are restricted to: `target_type`, `target_subtype`, `material_class`, `floor_count`, `width_m`, `length_m`, `height_m`, `desired_model_result`, `priority_score`, `complexity_score`, `label`, `target_description`, `map_lat`, `map_lng`. All other `TargetProfileFields` stay at dataclass defaults.
- Label format: `f"TGT-{existing_count + 1:03d}"`.
- Description text (verbatim): `"สร้างอัตโนมัติสำหรับทดสอบ/สอน — กรุณาตรวจสอบและแก้ไขก่อนบันทึก"`.
- Coordinate base: lat `16.8123` ± `random.uniform(-0.7, 0.7)`, lng `100.1234` ± `random.uniform(-0.8, 0.8)`.

---

### Task 1: `random_generator.py` — pure randomization function

**Files:**
- Create: `src/maap_app/modules/target/random_generator.py`
- Test: `tests/unit/test_random_target_generator.py`

**Interfaces:**
- Consumes: `maap_app.modules.target.constants.TARGET_TYPES`, `MATERIAL_CLASS_OPTIONS`, `DESIRED_MODEL_RESULTS`, `subtypes_for_target_type`; `maap_app.modules.target.profile_fields.TargetProfileFields`.
- Produces: `RandomTargetSuggestion` dataclass with fields `label: str`, `priority_score: int`, `complexity_score: int`, `profile: TargetProfileFields`, `map_lat: float`, `map_lng: float`. Function `generate_random_target(existing_count: int) -> RandomTargetSuggestion`. Both are imported by Task 3 as `from maap_app.modules.target.random_generator import RandomTargetSuggestion, generate_random_target`.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_random_target_generator.py`:

```python
from __future__ import annotations

from maap_app.modules.target.constants import (
    DESIRED_MODEL_RESULTS,
    MATERIAL_CLASS_OPTIONS,
    TARGET_TYPES,
    subtypes_for_target_type,
)
from maap_app.modules.target.random_generator import generate_random_target


def test_label_increments_from_existing_count() -> None:
    suggestion = generate_random_target(existing_count=5)
    assert suggestion.label == "TGT-006"


def test_label_starts_at_one_when_no_targets_exist() -> None:
    suggestion = generate_random_target(existing_count=0)
    assert suggestion.label == "TGT-001"


def test_scores_are_in_valid_range() -> None:
    for _ in range(50):
        suggestion = generate_random_target(existing_count=0)
        assert 1 <= suggestion.priority_score <= 5
        assert 1 <= suggestion.complexity_score <= 5


def test_profile_uses_valid_option_values() -> None:
    for _ in range(50):
        suggestion = generate_random_target(existing_count=0)
        profile = suggestion.profile
        assert profile.target_type in TARGET_TYPES
        assert profile.target_subtype in subtypes_for_target_type(profile.target_type)
        assert profile.material_class in MATERIAL_CLASS_OPTIONS
        assert profile.desired_model_result in DESIRED_MODEL_RESULTS
        assert profile.floor_count in {
            "1", "2", "3", "4", "5", "6", "8", "10", "UNK",
        }


def test_dimensions_are_in_plausible_ranges() -> None:
    for _ in range(50):
        suggestion = generate_random_target(existing_count=0)
        profile = suggestion.profile
        assert 5 <= profile.width_m <= 80
        assert 5 <= profile.length_m <= 120
        assert 3 <= profile.height_m <= 60


def test_coordinates_are_within_expected_box() -> None:
    for _ in range(50):
        suggestion = generate_random_target(existing_count=0)
        assert 16.8123 - 0.7 <= suggestion.map_lat <= 16.8123 + 0.7
        assert 100.1234 - 0.8 <= suggestion.map_lng <= 100.1234 + 0.8


def test_description_contains_auto_generated_note() -> None:
    suggestion = generate_random_target(existing_count=0)
    assert "สร้างอัตโนมัติ" in suggestion.profile.target_description


def test_other_profile_fields_stay_at_defaults() -> None:
    suggestion = generate_random_target(existing_count=0)
    profile = suggestion.profile
    assert profile.data_source == "manual"
    assert profile.cep is None
    assert profile.target_pk is None
    assert profile.reference_pk is None
    assert profile.resistance == ""
    assert profile.capacity == ""
    assert profile.damage_fit == ""
    assert profile.model_version == ""
    assert profile.selected_product_id is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/unit/test_random_target_generator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'maap_app.modules.target.random_generator'`

- [ ] **Step 3: Write minimal implementation**

Create `src/maap_app/modules/target/random_generator.py`:

```python
from __future__ import annotations

import random
from dataclasses import dataclass

from maap_app.modules.target.constants import (
    DESIRED_MODEL_RESULTS,
    MATERIAL_CLASS_OPTIONS,
    TARGET_TYPES,
    subtypes_for_target_type,
)
from maap_app.modules.target.profile_fields import TargetProfileFields

_BASE_LAT = 16.8123
_BASE_LNG = 100.1234
_FLOOR_COUNT_OPTIONS = ("1", "2", "3", "4", "5", "6", "8", "10", "UNK")
_AUTO_GENERATED_NOTE = (
    "สร้างอัตโนมัติสำหรับทดสอบ/สอน — กรุณาตรวจสอบและแก้ไขก่อนบันทึก"
)


@dataclass(frozen=True)
class RandomTargetSuggestion:
    label: str
    priority_score: int
    complexity_score: int
    profile: TargetProfileFields
    map_lat: float
    map_lng: float


def generate_random_target(existing_count: int) -> RandomTargetSuggestion:
    target_type = random.choice(TARGET_TYPES)
    target_subtype = random.choice(subtypes_for_target_type(target_type))
    profile = TargetProfileFields(
        target_type=target_type,
        target_subtype=target_subtype,
        material_class=random.choice(MATERIAL_CLASS_OPTIONS),
        target_description=_AUTO_GENERATED_NOTE,
        floor_count=random.choice(_FLOOR_COUNT_OPTIONS),
        width_m=random.uniform(5, 80),
        length_m=random.uniform(5, 120),
        height_m=random.uniform(3, 60),
        desired_model_result=random.choice(DESIRED_MODEL_RESULTS),
    )
    return RandomTargetSuggestion(
        label=f"TGT-{existing_count + 1:03d}",
        priority_score=random.randint(1, 5),
        complexity_score=random.randint(1, 5),
        profile=profile,
        map_lat=_BASE_LAT + random.uniform(-0.7, 0.7),
        map_lng=_BASE_LNG + random.uniform(-0.8, 0.8),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/unit/test_random_target_generator.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```bash
git add src/maap_app/modules/target/random_generator.py tests/unit/test_random_target_generator.py
git commit -m "feat: add pure random target profile generator"
```

---

### Task 2: `TargetProfileFormWidget.apply_random_suggestion`

**Files:**
- Modify: `src/maap_app/ui/panels/target_profile_form.py`

**Interfaces:**
- Consumes: `RandomTargetSuggestion` from Task 1 (`from maap_app.modules.target.random_generator import RandomTargetSuggestion`). Existing widget internals: `self.label_input` (`QLineEdit`), `self.priority_input`/`self.complexity_input` (`QSpinBox`), `self.target_type`/`self.material_class`/`self.desired_model_result` (`QComboBox`), `self.target_description` (`QTextEdit`), `self.floor_count` (`QLineEdit`), `self.width_m`/`self.length_m`/`self.height_m` (`_FloatLineEdit`), `self.coordinates_widget` (`TargetCoordinatesWidget`), `self._set_combo_text(combo, value)` (existing static method), `self._populate_subtypes(target_type, preserve=...)` (existing method), `self._set_optional_spin(spin, value)` (existing static method).
- Produces: `apply_random_suggestion(self, suggestion: RandomTargetSuggestion) -> None`, called by Task 3.

There is no isolated unit test for this task since `TargetProfileFormWidget` is a Qt widget and this codebase doesn't unit-test widget interaction (see `tests/unit/test_map_targets_list_panel.py`, which only tests the panel's pure helper functions). Verification happens manually in Task 5.

- [ ] **Step 1: Add the import**

In `src/maap_app/ui/panels/target_profile_form.py`, add to the imports below the existing `from maap_app.modules.target.profile_fields import TargetProfileFields` line:

```python
from maap_app.modules.target.random_generator import RandomTargetSuggestion
```

- [ ] **Step 2: Add the method**

In `src/maap_app/ui/panels/target_profile_form.py`, add this method to `TargetProfileFormWidget`, directly after the existing `clear_form` method (before `values`):

```python
    def apply_random_suggestion(self, suggestion: RandomTargetSuggestion) -> None:
        self.label_input.setText(suggestion.label)
        self.priority_input.setValue(suggestion.priority_score)
        self.complexity_input.setValue(suggestion.complexity_score)
        profile = suggestion.profile
        self._set_combo_text(self.target_type, profile.target_type)
        self._populate_subtypes(profile.target_type, preserve=profile.target_subtype)
        self._set_combo_text(self.material_class, profile.material_class)
        self.target_description.setPlainText(profile.target_description)
        self.floor_count.setText(profile.floor_count)
        self._set_optional_spin(self.width_m, profile.width_m)
        self._set_optional_spin(self.length_m, profile.length_m)
        self._set_optional_spin(self.height_m, profile.height_m)
        self._set_combo_text(self.desired_model_result, profile.desired_model_result)
        self.coordinates_widget.apply_map_coordinate(suggestion.map_lat, suggestion.map_lng)
```

- [ ] **Step 3: Verify the module still imports cleanly**

Run: `.venv/Scripts/python.exe -c "import maap_app.ui.panels.target_profile_form"`
Expected: no output, exit code 0 (confirms no syntax/import errors)

- [ ] **Step 4: Commit**

```bash
git add src/maap_app/ui/panels/target_profile_form.py
git commit -m "feat: apply random target suggestions to the profile form"
```

---

### Task 3: `TargetFormPanel.begin_create_random`

**Files:**
- Modify: `src/maap_app/ui/panels/target_form_panel.py`

**Interfaces:**
- Consumes: `generate_random_target(existing_count: int) -> RandomTargetSuggestion` from Task 1; `self.profile_form.apply_random_suggestion(suggestion)` from Task 2; existing `self.target_service.list_target_cards(scenario_id)` (returns `list[TargetCardListItem]`, filters optional); existing `self.begin_create()` method; existing `self._scenario_id` attribute.
- Produces: `begin_create_random(self) -> None`, connected by Task 4's sidebar signal.

- [ ] **Step 1: Add the import**

In `src/maap_app/ui/panels/target_form_panel.py`, add below the existing `from maap_app.modules.target.service import TargetService` line:

```python
from maap_app.modules.target.random_generator import generate_random_target
```

- [ ] **Step 2: Add the method**

In `src/maap_app/ui/panels/target_form_panel.py`, add this method directly after `begin_create`:

```python
    def begin_create_random(self) -> None:
        self.begin_create()
        existing_count = 0
        if self._scenario_id:
            existing_count = len(self.target_service.list_target_cards(self._scenario_id))
        suggestion = generate_random_target(existing_count)
        self.profile_form.apply_random_suggestion(suggestion)
```

- [ ] **Step 3: Verify the module still imports cleanly**

Run: `.venv/Scripts/python.exe -c "import maap_app.ui.panels.target_form_panel"`
Expected: no output, exit code 0

- [ ] **Step 4: Commit**

```bash
git add src/maap_app/ui/panels/target_form_panel.py
git commit -m "feat: wire random target generation into the target form panel"
```

---

### Task 4: Sidebar button and signal wiring

**Files:**
- Modify: `src/maap_app/ui/panels/target_panel.py`

**Interfaces:**
- Consumes: `TargetFormPanel.begin_create_random()` from Task 3.
- Produces: `TargetSidebar.generate_random_target_requested` signal, connected in `TargetPanel.__init__`.

- [ ] **Step 1: Add the new signal to `TargetSidebar`**

In `src/maap_app/ui/panels/target_panel.py`, change the `TargetSidebar` class's signal declarations (currently `target_selected`, `targets_changed`, `create_target_requested`) to add a fourth signal:

```python
class TargetSidebar(QWidget):
    target_selected = Signal(str)
    targets_changed = Signal()
    create_target_requested = Signal()
    generate_random_target_requested = Signal()
```

- [ ] **Step 2: Replace the footer layout to add the random-generate button**

Replace this existing block in `_build_ui`:

```python
        footer = QHBoxLayout()
        self.add_btn = QPushButton("+ เพิ่มเป้าหมาย")
        self.add_btn.setObjectName("GhostButton")
        self.add_btn.clicked.connect(self._on_add_target)
        self.delete_btn = QPushButton("ลบเป้าหมาย")
        self.delete_btn.setObjectName("DangerButton")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete_target)
        footer.addWidget(self.add_btn, stretch=1)
        footer.addWidget(self.delete_btn)
        outer.addLayout(footer)
```

with:

```python
        footer = QVBoxLayout()
        footer.setSpacing(6)
        top_row = QHBoxLayout()
        self.add_btn = QPushButton("+ เพิ่มเป้าหมาย")
        self.add_btn.setObjectName("GhostButton")
        self.add_btn.clicked.connect(self._on_add_target)
        self.random_btn = QPushButton("🎲 สุ่มเป้าหมาย")
        self.random_btn.setObjectName("GhostButton")
        self.random_btn.clicked.connect(self._on_generate_random)
        top_row.addWidget(self.add_btn, stretch=1)
        top_row.addWidget(self.random_btn, stretch=1)
        footer.addLayout(top_row)
        self.delete_btn = QPushButton("ลบเป้าหมาย")
        self.delete_btn.setObjectName("DangerButton")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete_target)
        footer.addWidget(self.delete_btn)
        outer.addLayout(footer)
```

- [ ] **Step 3: Add the click handler**

In `src/maap_app/ui/panels/target_panel.py`, add this method directly after `_on_add_target`:

```python
    def _on_generate_random(self) -> None:
        self._selected_id = None
        self._update_card_selection()
        self.generate_random_target_requested.emit()
```

- [ ] **Step 4: Wire the signal in `TargetPanel.__init__`**

In `src/maap_app/ui/panels/target_panel.py`, in `TargetPanel.__init__`, directly after the existing line:

```python
        self.sidebar.create_target_requested.connect(self.form_panel.begin_create)
```

add:

```python
        self.sidebar.generate_random_target_requested.connect(self.form_panel.begin_create_random)
```

- [ ] **Step 5: Verify the module still imports cleanly**

Run: `.venv/Scripts/python.exe -c "import maap_app.ui.panels.target_panel"`
Expected: no output, exit code 0

- [ ] **Step 6: Commit**

```bash
git add src/maap_app/ui/panels/target_panel.py
git commit -m "feat: add generate-random-target button to the target sidebar"
```

---

### Task 5: Run full unit test suite and manual smoke test

**Files:** none (verification only)

**Interfaces:** none — this task only verifies Tasks 1–4 together.

- [ ] **Step 1: Run the full unit test suite**

Run: `.venv/Scripts/python.exe -m pytest tests/unit -v`
Expected: all tests pass, including the 8 new tests from Task 1 and all pre-existing tests (no regressions).

- [ ] **Step 2: Launch the app and manually verify the feature**

Use the project's `run` skill (or `.venv/Scripts/python.exe -m maap_app.app` / whatever the project's existing launch entrypoint is — check `src/maap_app/app.py` for the `if __name__ == "__main__":` block if unsure) to start the application. Then:

1. Open or create a scenario.
2. Go to the Target tab.
3. Confirm the Target Stack sidebar footer now shows two rows: `+ เพิ่มเป้าหมาย` / `🎲 สุ่มเป้าหมาย` on top, `ลบเป้าหมาย` below.
4. Click `🎲 สุ่มเป้าหมาย`.
5. Confirm the Target Form (center column) populates with: a label like `TGT-001` (or the next number if targets already exist), random priority/complexity (1–5), a target type/subtype/material combination, a description starting with "สร้างอัตโนมัติ...", floor count, width/length/height values, a desired model result, and a coordinate row with lat/lng filled in and marked primary.
6. Confirm nothing was saved yet — the Target Stack list on the left has NOT gained a new card.
7. Click `บันทึก` (Save). Confirm the new target now appears in the Target Stack list with the generated label.
8. Click `🎲 สุ่มเป้าหมาย` again with no scenario selected (if reachable) to confirm it doesn't crash — Save should show the existing "เลือกหรือสร้าง scenario ก่อน" warning.

- [ ] **Step 3: Report results**

If all checks in Step 2 pass and Step 1's test run is green, the feature is complete — no commit needed for this verification-only task.
