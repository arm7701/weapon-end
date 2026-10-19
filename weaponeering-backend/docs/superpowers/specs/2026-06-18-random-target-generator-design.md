# Random Target Generator — Design

## Problem

Filling out a Target Card by hand (type, subtype, material, dimensions, priority/complexity,
coordinates) is slow when a user just wants test/demo data in the Target Stack. We want a
one-click "generate random target" action that pre-fills the existing Target Form with
plausible random values, which the user can review/edit before saving — no new validation
or persistence path is needed.

## Behavior

- Clicking the button populates the Target Form fields with randomized values (does **not**
  create/save anything by itself).
- The user reviews/edits the pre-filled form like any new target, then presses the existing
  "บันทึก" (Save) button to persist it through the normal create path.

## Architecture

A new pure-function module, `src/maap_app/modules/target/random_generator.py`, owns the
randomization logic, decoupled from Qt:

```python
@dataclass(frozen=True)
class RandomTargetSuggestion:
    label: str
    priority_score: int
    complexity_score: int
    profile: TargetProfileFields
    map_lat: float
    map_lng: float

def generate_random_target(existing_count: int) -> RandomTargetSuggestion: ...
```

This isolates randomization from widget code so it can be unit-tested directly (e.g. assert
generated values fall within valid ranges / belong to the option lists in `constants.py`).

## Field randomization ranges

| Field | Source |
|---|---|
| `target_type` | `random.choice(TARGET_TYPES)` |
| `target_subtype` | `random.choice(subtypes_for_target_type(target_type))` |
| `material_class` | `random.choice(MATERIAL_CLASS_OPTIONS)` |
| `floor_count` | `random.choice(["1","2","3","4","5","6","8","10","UNK"])` |
| `width_m` | `random.uniform(5, 80)` |
| `length_m` | `random.uniform(5, 120)` |
| `height_m` | `random.uniform(3, 60)` |
| `desired_model_result` | `random.choice(DESIRED_MODEL_RESULTS)` |
| `priority_score` | `random.randint(1, 5)` |
| `complexity_score` | `random.randint(1, 5)` |
| `label` | `f"TGT-{existing_count + 1:03d}"` |
| `target_description` | fixed note: `"สร้างอัตโนมัติสำหรับทดสอบ/สอน — กรุณาตรวจสอบและแก้ไขก่อนบันทึก"` |
| `map_lat` | base `16.8123` + `random.uniform(-0.7, 0.7)` |
| `map_lng` | base `100.1234` + `random.uniform(-0.8, 0.8)` |

This produces a roughly ±80 km box around the map's existing `DEFAULT_CENTER`
(`src/maap_app/ui/map/assets/leaflet_map.html`), so generated targets are immediately visible
on the default map view.

All other `TargetProfileFields` (`data_source`, `cep`, `target_pk`, `reference_pk`,
`resistance`, `capacity`, `damage_fit`, `model_version`, `coordinate_error_m`,
`selected_product_id`) are left at their dataclass defaults — identical to a normal new
target — since these are meant to come from real analysis, not guessing.

## UI wiring

1. **`TargetSidebar`** (`src/maap_app/ui/panels/target_panel.py`)
   - New signal: `generate_random_target_requested = Signal()`
   - New button `🎲 สุ่มเป้าหมาย` (`objectName="GhostButton"`) added to the footer.
     Footer becomes two rows (sidebar is only 260–320px wide):
     - Row 1: `+ เพิ่มเป้าหมาย` (stretch 1) + `🎲 สุ่มเป้าหมาย` (stretch 1)
     - Row 2: `ลบเป้าหมาย` (full width, unchanged)
   - `_on_generate_random()`: clears `_selected_id` / card selection (mirrors
     `_on_add_target`), then emits `generate_random_target_requested`.

2. **`TargetPanel.__init__`**: wires
   `self.sidebar.generate_random_target_requested.connect(self.form_panel.begin_create_random)`.

3. **`TargetFormPanel.begin_create_random()`** (new method):
   - Calls `self.begin_create()` to reset to create mode and clear the form.
   - Counts existing target cards in the current scenario via
     `self.target_service.list_target_cards(self._scenario_id, TargetFilterParams())` if a
     scenario is set, else uses `0`.
   - Calls `generate_random_target(existing_count)` to get a `suggestion`.
   - Calls `self.profile_form.apply_random_suggestion(suggestion)`.

4. **`TargetProfileFormWidget.apply_random_suggestion(suggestion)`** (new method): sets
   `label_input`, `priority_input`, `complexity_input`, the `target_type` /
   `material_class` / `desired_model_result` combo boxes (repopulating subtypes for the
   chosen `target_type`, preserving the suggested subtype), `target_description`,
   `floor_count`, the three dimension spin fields, then calls
   `self.coordinates_widget.apply_map_coordinate(suggestion.map_lat, suggestion.map_lng)` to
   drop a primary coordinate pin into the (already-empty, from `clear_form()`) first
   coordinate row.

## Edge cases

- **No scenario selected**: `begin_create_random()` treats `existing_count` as `0`
  (label `TGT-001`). Pressing Save still hits the existing scenario guard in
  `TargetFormPanel._on_save` ("เลือกหรือสร้าง scenario ก่อน") — unchanged behavior.
- **Nothing is persisted** by generation itself — only the existing Save path writes to the
  database, so there's no new failure mode to handle for create/update.

## Testing

- Unit tests for `generate_random_target()`: values are within declared ranges, `target_type`
  is in `TARGET_TYPES`, `target_subtype` is valid for the chosen `target_type`,
  `material_class`/`desired_model_result` are in their respective option tuples, label format
  matches `TGT-{n:03d}` for given `existing_count`.
- No new Qt/widget tests planned beyond manual verification — existing panel tests in this
  codebase (e.g. `tests/unit/test_map_targets_list_panel.py`) only cover pure helper
  functions, not actual widget interaction, so this follows the same convention.
