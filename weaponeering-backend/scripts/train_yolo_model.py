from __future__ import annotations

import argparse
import shutil
from pathlib import Path


APP_DATA_DIR = Path.home() / ".local" / "share" / "maap_wargame_simulation"
MODEL_OUTPUT_NAMES = {
    "building": "building-seg.pt",
    "vehicle": "vehicle-det.pt",
    "structure": "structure-seg.pt",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train/fine-tune a local Ultralytics YOLO model and install best.pt "
            "for the MAAP desktop detection layer."
        )
    )
    parser.add_argument(
        "--data",
        required=True,
        help="Path to dataset data.yaml exported from Roboflow/YOLO format.",
    )
    parser.add_argument(
        "--base",
        default="yolo11n-seg.pt",
        help="Base YOLO model, e.g. yolo11n-seg.pt, yolo11s-seg.pt, yolo11n.pt.",
    )
    parser.add_argument(
        "--target",
        choices=sorted(MODEL_OUTPUT_NAMES),
        default="building",
        help="Which app model slot to install best.pt into.",
    )
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--device", default=None, help="Optional device, e.g. cpu, 0, mps.")
    parser.add_argument(
        "--project",
        default=str(APP_DATA_DIR / "training_runs"),
        help="Ultralytics project directory for training outputs.",
    )
    parser.add_argument("--name", default=None, help="Training run name.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data).expanduser().resolve()
    if not data_path.is_file():
        raise SystemExit(f"data.yaml not found: {data_path}")
    data_path = normalize_dataset_yaml(data_path)

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit(
            'ultralytics is not installed. Run: pip install -e ".[detection]"'
        ) from exc

    run_name = args.name or f"{args.target}-yolo"
    model = YOLO(args.base)
    train_kwargs = {
        "data": str(data_path),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "project": args.project,
        "name": run_name,
    }
    if args.device:
        train_kwargs["device"] = args.device

    result = model.train(**train_kwargs)
    save_dir = Path(result.save_dir)
    best_path = save_dir / "weights" / "best.pt"
    if not best_path.is_file():
        raise SystemExit(f"Training finished but best.pt was not found: {best_path}")

    models_dir = APP_DATA_DIR / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    destination = models_dir / MODEL_OUTPUT_NAMES[args.target]
    shutil.copy2(best_path, destination)
    project_root = Path(__file__).resolve().parents[1]
    project_destination = project_root / MODEL_OUTPUT_NAMES[args.target]
    shutil.copy2(best_path, project_destination)
    print(f"Installed trained model: {destination}")
    print(f"Project model copy: {project_destination}")
    print(f"Training run: {save_dir}")


def normalize_dataset_yaml(data_path: Path) -> Path:
    """Create a YOLO data yaml with usable absolute train/val paths.

    Some Roboflow exports contain only train/ while data.yaml still references
    valid/ and test/. Ultralytics requires val to exist, so this writes a local
    data.maap.yaml that falls back to train/images for validation when needed.
    """

    root = data_path.parent
    raw_lines = data_path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    passthrough: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            passthrough.append(line)
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in {"train", "val", "test"}:
            values[key] = value
        else:
            passthrough.append(line)

    train_images = resolve_dataset_path(root, values.get("train", "train/images"))
    val_images = resolve_dataset_path(root, values.get("val", "valid/images"))
    test_images = resolve_dataset_path(root, values.get("test", "test/images"))
    if not train_images.exists():
        raise SystemExit(f"train images not found: {train_images}")
    if not val_images.exists():
        print(f"Validation images not found: {val_images}")
        print("Using train/images as validation set for this run.")
        val_images = train_images

    output_lines = [
        f"train: {train_images}",
        f"val: {val_images}",
    ]
    if test_images.exists():
        output_lines.append(f"test: {test_images}")
    output_lines.extend(passthrough)

    output_path = root / "data.maap.yaml"
    output_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    print(f"Using normalized dataset yaml: {output_path}")
    return output_path


def resolve_dataset_path(root: Path, value: str) -> Path:
    cleaned = value.strip().strip("'\"")
    path = Path(cleaned)
    if not path.is_absolute():
        path = (root / path).resolve()
    if path.exists():
        return path
    parts = [part for part in Path(cleaned).parts if part not in {"..", "."}]
    if parts:
        sibling_path = root.joinpath(*parts).resolve()
        if sibling_path.exists():
            return sibling_path
    return path


if __name__ == "__main__":
    main()
