from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


MODEL_FILES = {
    "Building Detector": "building-seg.pt",
    "building-seg.pt": "building-seg.pt",
    "Vehicle Detector": "vehicle-det.pt",
    "Structure Segmentation": "structure-seg.pt",
}

BUILDING_MODEL_FILENAME = MODEL_FILES["Building Detector"]

DETECTION_ZOOM_MIN = 1
DETECTION_ZOOM_MAX = 4
DETECTION_ZOOM_DEFAULT = 4


def detection_capture_radius_m(radius_m: int, zoom_level: int = DETECTION_ZOOM_DEFAULT) -> int:
    """Half-span of the captured viewport in meters.

    Higher *zoom_level* zooms the map closer for sharper YOLO input while
    *radius_m* remains the target filter radius.
    """
    zoom = max(DETECTION_ZOOM_MIN, min(DETECTION_ZOOM_MAX, zoom_level))
    margin_factor = 1.0 + (DETECTION_ZOOM_MAX + 1 - zoom) * 0.25
    return max(int(radius_m * margin_factor), radius_m + 20)

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
VEHICLE_CLASS_NAMES = {"car", "truck", "bus", "motorcycle", "vehicle"}
DEFAULT_CONFIDENCE = 0.12
LOW_CONFIDENCE = 0.05
_BUNDLED_MODELS_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class DetectionRunResult:
    objects: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""
    model_path: Path | None = None
    source_path: Path | None = None
    ok: bool = False


class YoloDetectionService:
    """Runs local YOLO detection on local imagery and returns map overlay polygons.

    Source image convention:
    - data_dir/detection_sources/{target_card_id}.png|jpg|tif
    - data_dir/detection_sources/default.png|jpg|tif

    The image is treated as a square crop centered on the target and covering the
    selected radius in every direction. This keeps the first integration local and
    deterministic until a GeoTIFF/orthophoto georeference pipeline is added.
    """

    def __init__(self, data_dir: Path, project_root: Path | None = None) -> None:
        self.data_dir = data_dir
        self.project_root = project_root or _BUNDLED_MODELS_ROOT

    def run(
        self,
        *,
        target: dict,
        model_name: str,
        radius_m: int,
        capture_radius_m: int | None = None,
    ) -> DetectionRunResult:
        model_path = self._resolve_model_path(model_name)
        if model_path is None:
            return DetectionRunResult(
                message=self._missing_model_message(model_name),
            )

        source_path = self._resolve_source_image(str(target.get("targetCardId", "")))
        if source_path is None:
            return DetectionRunResult(
                model_path=model_path,
                message=(
                    "Local source image not found. Put a target crop in "
                    f"{self.data_dir / 'detection_sources'}"
                ),
            )

        try:
            from ultralytics import YOLO
        except ImportError:
            return DetectionRunResult(
                model_path=model_path,
                source_path=source_path,
                message="ultralytics is not installed. Install the detection extra first.",
            )

        scan_radius = capture_radius_m or radius_m
        model = YOLO(str(model_path))
        results = model(str(source_path), verbose=False, conf=DEFAULT_CONFIDENCE)
        candidate_count, objects = self._results_to_objects(
            results=results,
            target=target,
            model_name=model_name,
            radius_m=radius_m,
            capture_radius_m=scan_radius,
        )

        model_label = model_path.name
        if candidate_count == 0:
            results = model(str(source_path), verbose=False, conf=LOW_CONFIDENCE)
            candidate_count, objects = self._results_to_objects(
                results=results,
                target=target,
                model_name=model_name,
                radius_m=radius_m,
                capture_radius_m=scan_radius,
            )
            if candidate_count:
                model_label = f"{model_path.name} (low conf)"

        filtered_note = ""
        if candidate_count and not objects:
            filtered_note = f"; {candidate_count} object(s) were outside {radius_m} m"
        empty_note = ""
        if candidate_count == 0:
            empty_note = (
                ". No objects detected in the captured image — try a larger radius "
                "or fine-tune the YOLO model for satellite imagery"
            )
        return DetectionRunResult(
            objects=objects,
            message=(
                f"{model_name} ({model_label}): detected {len(objects)} object(s) "
                f"from {source_path.name}{filtered_note}{empty_note}"
            ),
            model_path=model_path,
            source_path=source_path,
            ok=True,
        )

    def run_on_image_path(
        self,
        *,
        target: dict,
        model_name: str,
        radius_m: int,
        image_path: Path,
        capture_radius_m: int | None = None,
    ) -> DetectionRunResult:
        """Run YOLO on an explicit image path (web upload / Cesium capture)."""
        model_path = self._resolve_model_path(model_name)
        if model_path is None:
            return DetectionRunResult(
                message=self._missing_model_message(model_name),
            )
        path = Path(image_path)
        if not path.is_file():
            return DetectionRunResult(
                model_path=model_path,
                message=f"Source image not found: {path}",
            )
        try:
            from ultralytics import YOLO
        except ImportError:
            return DetectionRunResult(
                model_path=model_path,
                source_path=path,
                message="ultralytics is not installed. Install the detection extra first.",
            )

        scan_radius = capture_radius_m or radius_m
        model = YOLO(str(model_path))
        results = model(str(path), verbose=False, conf=DEFAULT_CONFIDENCE)
        candidate_count, objects = self._results_to_objects(
            results=results,
            target=target,
            model_name=model_name,
            radius_m=radius_m,
            capture_radius_m=scan_radius,
        )
        model_label = model_path.name
        if candidate_count == 0:
            results = model(str(path), verbose=False, conf=LOW_CONFIDENCE)
            candidate_count, objects = self._results_to_objects(
                results=results,
                target=target,
                model_name=model_name,
                radius_m=radius_m,
                capture_radius_m=scan_radius,
            )
            if candidate_count:
                model_label = f"{model_path.name} (low conf)"

        filtered_note = ""
        if candidate_count and not objects:
            filtered_note = f"; {candidate_count} object(s) were outside {radius_m} m"
        empty_note = ""
        if candidate_count == 0:
            empty_note = (
                ". No objects detected in the captured image — try a larger radius "
                "or fine-tune the YOLO model for satellite imagery"
            )
        return DetectionRunResult(
            objects=objects,
            message=(
                f"{model_name} ({model_label}): detected {len(objects)} object(s) "
                f"from {path.name}{filtered_note}{empty_note}"
            ),
            model_path=model_path,
            source_path=path,
            ok=True,
        )

    def describe_setup(self, model_name: str) -> str:
        model_path = self._resolve_model_path(model_name)
        slot = MODEL_FILES.get(model_name, BUILDING_MODEL_FILENAME)
        lines = [
            f"Model slot: {slot}",
            f"Resolved model: {model_path if model_path else 'not found'}",
            f"Project model: {self.project_root / slot}",
            f"Legacy install path: {self.data_dir / 'models' / slot}",
            f"Source folder: {self.data_dir / 'detection_sources'}",
            f"ultralytics: {'installed' if self._ultralytics_installed() else 'missing'}",
        ]
        return "\n".join(lines)

    def _missing_model_message(self, model_name: str) -> str:
        slot = MODEL_FILES.get(model_name, BUILDING_MODEL_FILENAME)
        return (
            f"YOLO model weight not found for {model_name}.\n"
            f"Place your trained model at {self.project_root / slot}"
        )

    @staticmethod
    def _ultralytics_installed() -> bool:
        try:
            import ultralytics  # noqa: F401
        except ImportError:
            return False
        return True

    def _model_search_roots(self) -> list[Path]:
        roots: list[Path] = []
        for candidate in (
            self.project_root,
            self.project_root / "models",
            self.data_dir / "models",
            Path.cwd(),
            Path.cwd() / "models",
        ):
            resolved = candidate.resolve()
            if resolved not in roots:
                roots.append(resolved)
        return roots

    def _model_file_candidates(self, model_name: str) -> list[Path]:
        slot = MODEL_FILES.get(model_name, "building-seg.pt")
        candidates: list[Path] = []
        seen: set[str] = set()
        for root in self._model_search_roots():
            path = (root / slot).resolve()
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(path)
        return candidates

    def _resolve_model_path(self, model_name: str) -> Path | None:
        return next(
            (path for path in self._model_file_candidates(model_name) if path.is_file()),
            None,
        )

    def _resolve_source_image(self, target_card_id: str) -> Path | None:
        source_dir = self.data_dir / "detection_sources"
        stems = [target_card_id, "default"] if target_card_id else ["default"]
        for stem in stems:
            for extension in IMAGE_EXTENSIONS:
                path = source_dir / f"{stem}{extension}"
                if path.is_file():
                    return path
        return None

    def _results_to_objects(
        self,
        *,
        results,
        target: dict,
        model_name: str,
        radius_m: int,
        capture_radius_m: int,
    ) -> tuple[int, list[dict[str, Any]]]:
        objects: list[dict[str, Any]] = []
        candidate_count = 0
        target_lat = float(target["lat"])
        target_lng = float(target["lng"])
        target_id = str(target.get("targetCardId", "target"))
        model_key = model_name.lower()

        for result in results:
            image_h, image_w = result.orig_shape
            names = result.names or {}
            masks_xy = list(result.masks.xy) if getattr(result, "masks", None) else []
            boxes = result.boxes
            if boxes is None:
                continue
            xyxy_values = boxes.xyxy.cpu().tolist() if boxes.xyxy is not None else []
            cls_values = boxes.cls.cpu().tolist() if boxes.cls is not None else []
            conf_values = boxes.conf.cpu().tolist() if boxes.conf is not None else []

            for index, bbox in enumerate(xyxy_values[:100]):
                class_id = int(cls_values[index]) if index < len(cls_values) else -1
                class_name = str(names.get(class_id, "object"))
                if "vehicle" in model_key and class_name.lower() not in VEHICLE_CLASS_NAMES:
                    continue
                pixel_polygon = (
                    masks_xy[index].tolist()
                    if index < len(masks_xy)
                    else self._bbox_to_pixel_polygon(bbox)
                )
                polygon = self._pixel_polygon_to_lat_lng(
                    pixel_polygon,
                    image_w=image_w,
                    image_h=image_h,
                    center_lat=target_lat,
                    center_lng=target_lng,
                    radius_m=capture_radius_m,
                )
                if len(polygon) < 3:
                    continue
                obj_lat, obj_lng = self._polygon_centroid(polygon)
                distance = self._distance_m(target_lat, target_lng, obj_lat, obj_lng)
                candidate_count += 1
                if self._polygon_min_distance_m(target_lat, target_lng, polygon) > radius_m:
                    continue
                objects.append(
                    {
                        "id": f"{target_id}-yolo-{len(objects) + 1}",
                        "targetCardId": target_id,
                        "label": class_name.title(),
                        "objectType": class_name,
                        "model": model_name,
                        "risk": self._risk_for_distance(distance, radius_m),
                        "confidence": round(float(conf_values[index]), 3)
                        if index < len(conf_values)
                        else 0.0,
                        "lat": obj_lat,
                        "lng": obj_lng,
                        "polygon": polygon,
                    }
                )
        return candidate_count, objects

    @staticmethod
    def _bbox_to_pixel_polygon(bbox: list[float]) -> list[list[float]]:
        x1, y1, x2, y2 = bbox
        return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

    @staticmethod
    def _pixel_polygon_to_lat_lng(
        polygon: list[list[float]],
        *,
        image_w: int,
        image_h: int,
        center_lat: float,
        center_lng: float,
        radius_m: int,
    ) -> list[list[float]]:
        if image_w <= 0 or image_h <= 0:
            return []
        lng_scale = max(math.cos(math.radians(center_lat)), 0.1)
        result: list[list[float]] = []
        for x, y in polygon:
            east_m = (float(x) / image_w - 0.5) * radius_m * 2
            north_m = (0.5 - float(y) / image_h) * radius_m * 2
            lat = center_lat + north_m / 111_320.0
            lng = center_lng + east_m / (111_320.0 * lng_scale)
            result.append([lat, lng])
        return result

    @staticmethod
    def _polygon_centroid(polygon: list[list[float]]) -> tuple[float, float]:
        lat = sum(point[0] for point in polygon) / len(polygon)
        lng = sum(point[1] for point in polygon) / len(polygon)
        return lat, lng

    @staticmethod
    def _distance_m(lat_a: float, lng_a: float, lat_b: float, lng_b: float) -> float:
        mean_lat = math.radians((lat_a + lat_b) / 2)
        d_lat = (lat_b - lat_a) * 111_320.0
        d_lng = (lng_b - lng_a) * 111_320.0 * max(math.cos(mean_lat), 0.1)
        return math.hypot(d_lat, d_lng)

    @classmethod
    def _polygon_min_distance_m(
        cls,
        center_lat: float,
        center_lng: float,
        polygon: list[list[float]],
    ) -> float:
        return min(
            cls._distance_m(center_lat, center_lng, point[0], point[1])
            for point in polygon
        )

    @staticmethod
    def _risk_for_distance(distance_m: float, radius_m: int) -> str:
        if distance_m <= radius_m * 0.35:
            return "high"
        if distance_m <= radius_m * 0.7:
            return "medium"
        return "low"
