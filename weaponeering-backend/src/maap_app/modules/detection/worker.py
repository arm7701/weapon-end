"""Out-of-process runner for :class:`YoloDetectionService`.

``ultralytics``/``torch`` drag in ``triton``, whose bundled LLVM segfaults when
loaded into a process that already hosts a ``QWebEngineView`` (Cesium's
software-rendering LLVM collides with triton's). Running the detection in a
separate process keeps that native library out of the GUI process.

Protocol: a single JSON object is read from stdin with the keys
``data_dir``, ``project_root`` (optional), ``target``, ``model_name``,
``radius_m`` and ``capture_radius_m``. A single JSON object is written to
stdout with ``ok``, ``message``, ``objects``, ``model_path`` and
``source_path`` (the latter two are ``null`` or absolute path strings).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from maap_app.modules.detection.service import YoloDetectionService


def main() -> int:
    request = json.load(sys.stdin)

    data_dir = Path(request["data_dir"])
    project_root = request.get("project_root")
    service = YoloDetectionService(
        data_dir,
        project_root=Path(project_root) if project_root else None,
    )

    result = service.run(
        target=request["target"],
        model_name=request["model_name"],
        radius_m=request["radius_m"],
        capture_radius_m=request.get("capture_radius_m"),
    )

    json.dump(
        {
            "ok": result.ok,
            "message": result.message,
            "objects": result.objects,
            "model_path": str(result.model_path) if result.model_path else None,
            "source_path": str(result.source_path) if result.source_path else None,
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
